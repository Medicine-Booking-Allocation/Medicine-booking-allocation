
from flask import Blueprint, request, jsonify, session

from app.models import (
    db,
    Prescription,
    User,
    Booking,
    Medicine,
    WaitlistEntry,
    utc_now
)

from app.waitlist import (
    promote_waitlisted_bookings,
    update_waitlist_positions
)

from app.notification import create_notification
from app.auth_utils import role_required

prescription_bp = Blueprint('prescription', __name__)

VALID_STATUSES = [
    'Submitted',
    'Under Review',
    'Verified',
    'Rejected'
]


@prescription_bp.route('/submit', methods=['POST'])
@role_required('Customer')
def submit_prescription():
    data = request.get_json()

    if not data or not data.get('prescription_reference'):
        return jsonify({
            "error": "prescription_reference is required"
        }), 400

    user_id = session.get('user_id')
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    prescription_reference = data['prescription_reference'].strip()

    if not prescription_reference:
        return jsonify({
            "error": "Prescription reference cannot be empty"
        }), 400

    if len(prescription_reference) > 150:
        return jsonify({
            "error": "Prescription reference cannot exceed 150 characters"
        }), 400

    prescription = Prescription(
        user_id=user.user_id,
        prescription_reference=prescription_reference,
        prescribed_medicine=(
            (data.get('prescribed_medicine') or '').strip() or None
        ),
        prescribed_dosage=(
            (data.get('prescribed_dosage') or '').strip() or None
        ),
        prescription_status='Submitted'
    )

    db.session.add(prescription)

    # Find all active Pharmacy Staff members.
    active_staff = User.query.filter_by(
        role='Pharmacy Staff',
        account_status='Active'
    ).all()

    # Notify each active Pharmacy Staff member.
    for staff in active_staff:
        create_notification(
            user_id=staff.user_id,
            event_type='Prescription',
            message='A customer has submitted a prescription for review.',
            channel='In-app',
            commit=False
        )

    # Save the prescription and notifications together.
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        "message": "Prescription submitted successfully",
        "prescription_id": prescription.prescription_id,
        "prescription_status": prescription.prescription_status,
        "submitted_at": prescription.submitted_at.isoformat()
    }), 201


@prescription_bp.route('/<prescription_id>', methods=['GET'])
@role_required('Customer', 'Pharmacy Staff', 'Administrator')
def get_prescription(prescription_id):
    prescription = Prescription.query.filter_by(
        prescription_id=prescription_id
    ).first()

    if not prescription:
        return jsonify({"error": "Prescription not found"}), 404

    current_user = db.session.get(User, session.get('user_id'))

    if (
        current_user.role == 'Customer'
        and prescription.user_id != current_user.user_id
    ):
        return jsonify({"error": "Access denied"}), 403

    return jsonify({
        "prescription_id": prescription.prescription_id,
        "user_id": prescription.user_id,
        "prescription_reference": prescription.prescription_reference,
        "prescription_status": prescription.prescription_status,
        "submitted_at": prescription.submitted_at.isoformat(),
        "prescribed_medicine": prescription.prescribed_medicine,
        "prescribed_dosage": prescription.prescribed_dosage,
        "verified_at": (
            prescription.verified_at.isoformat()
            if prescription.verified_at else None
        )
    }), 200


@prescription_bp.route('/<prescription_id>/status', methods=['PATCH'])
@role_required('Pharmacy Staff', 'Administrator')
def update_prescription_status(prescription_id):
    data = request.get_json()

    if not data or not data.get('prescription_status'):
        return jsonify({
            "error": "prescription_status is required"
        }), 400

    new_status = data['prescription_status']

    if new_status not in VALID_STATUSES:
        return jsonify({
            "error": "Invalid status",
            "allowed_statuses": VALID_STATUSES
        }), 400

    prescription = Prescription.query.filter_by(
        prescription_id=prescription_id
    ).first()

    if not prescription:
        return jsonify({"error": "Prescription not found"}), 404

    allowed_transitions = {
        'Submitted': ['Under Review', 'Rejected'],
        'Under Review': ['Verified', 'Rejected'],
        'Verified': [],
        'Rejected': []
    }

    if new_status not in allowed_transitions[prescription.prescription_status]:
        return jsonify({
            "error": "Invalid status transition",
            "current_status": prescription.prescription_status,
            "requested_status": new_status
        }), 400

    prescription.prescription_status = new_status

    if new_status == 'Verified':
        prescription.verified_at = utc_now()

    if new_status == 'Rejected':
        event_type = 'Rejection'
    else:
        event_type = 'Prescription'

    # Notify the customer about the prescription status update.
    create_notification(
        user_id=prescription.user_id,
        event_type=event_type,
        message=f'Your prescription status has been updated to {new_status}.',
        channel='In-app',
        commit=False
    )

    try:
        if new_status == 'Verified':
            # Find pending bookings linked to this prescription.
            pending_bookings = (
                Booking.query
                .join(
                    Medicine,
                    Booking.medicine_id == Medicine.medicine_id
                )
                .filter(
                    Booking.prescription_id == prescription_id,
                    Booking.status == 'Requested',
                    Medicine.prescription_required.is_(True)
                )
                .all()
            )

            affected_medicines = set()

            # Add verified bookings to the existing priority waitlist.
            for booking in pending_bookings:
                booking.status = 'Waitlisted'

                db.session.add(WaitlistEntry(
                    booking_id=booking.booking_id,
                    priority_score=booking.priority_score,
                    position=0,
                    status='Active'
                ))

                affected_medicines.add(booking.medicine_id)

            db.session.flush()

            # Recalculate positions and promote eligible bookings.
            for medicine_id in affected_medicines:
                update_waitlist_positions(medicine_id)
                promote_waitlisted_bookings(medicine_id)

        elif new_status == 'Rejected':
            # Find pending bookings linked to the rejected prescription.
            pending_bookings = (
                Booking.query
                .join(
                    Medicine,
                    Booking.medicine_id == Medicine.medicine_id
                )
                .filter(
                    Booking.prescription_id == prescription_id,
                    Booking.status == 'Requested',
                    Medicine.prescription_required.is_(True)
                )
                .all()
            )

            # Reject pending bookings and notify their customers.
            for booking in pending_bookings:
                booking.status = 'Rejected'

                # FR-NOT-02: Booking rejection notification.
                create_notification(
                    user_id=booking.user_id,
                    event_type='Rejection',
                    message=(
                        f'Your booking {booking.booking_id} has been '
                        'rejected because its prescription was rejected.'
                    ),
                    channel='In-app',
                    commit=False
                )

        # Save status changes and notifications together.
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        "message": "Prescription status updated successfully",
        "prescription_id": prescription.prescription_id,
        "prescription_status": prescription.prescription_status,
        "verified_at": (
            prescription.verified_at.isoformat()
            if prescription.verified_at else None
        )
    }), 200


@prescription_bp.route('/user/<user_id>', methods=['GET'])
@role_required('Customer', 'Pharmacy Staff', 'Administrator')
def get_user_prescriptions(user_id):
    current_user = db.session.get(User, session.get('user_id'))

    if (
        current_user.role == 'Customer'
        and user_id != current_user.user_id
    ):
        return jsonify({"error": "Access denied"}), 403

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    prescriptions = Prescription.query.filter_by(
        user_id=user_id
    ).order_by(Prescription.submitted_at.desc()).all()

    results = []

    for prescription in prescriptions:
        results.append({
            "prescription_id": prescription.prescription_id,
            "prescription_reference": prescription.prescription_reference,
            "prescribed_medicine": prescription.prescribed_medicine,
            "prescribed_dosage": prescription.prescribed_dosage,
            "prescription_status": prescription.prescription_status,
            "submitted_at": prescription.submitted_at.isoformat(),
            "verified_at": (
                prescription.verified_at.isoformat()
                if prescription.verified_at else None
            )
        })

    return jsonify({"prescriptions": results}), 200
