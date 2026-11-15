from flask import Blueprint, request, jsonify, session
from sqlalchemy.exc import SQLAlchemyError
from app.waitlist import promote_waitlisted_bookings

from app.models import (
    db,
    User,
    Medicine,
    Inventory,
    Booking,
    WaitlistEntry,
    PriorityRule,
    PriorityEvaluation,
    utc_now
)

from app.auth_utils import role_required
from app.notification import create_notification
from app.priority import (calculate_priority_score,rank_bookings,DEFAULT_WEIGHTS)
from app.audit_utils import record_audit

booking_bp = Blueprint("booking", __name__)

URGENCY_SCORES = {
    "emergency": 100,
    "high": 75,
    "medium": 50,
    "low": 25
}

def update_waitlist_positions(medicine_id):
    """
    Recalculate active waitlist positions for a particular medicine.

    Higher priority scores come first.
    Earlier booking timestamps break priority ties.
    """

    entries = (
        db.session.query(WaitlistEntry, Booking)
        .join(
            Booking,
            WaitlistEntry.booking_id == Booking.booking_id
        )
        .filter(
            WaitlistEntry.status == "Active",
            Booking.medicine_id == medicine_id
        )
        .all()
    )

    bookings_to_rank = [
        {
            "booking_id": booking.booking_id,
            "priority_score": float(entry.priority_score),
            "created_at": booking.created_at
        }
        for entry, booking in entries
    ]

    ranked_bookings = rank_bookings(bookings_to_rank)

    positions = {
        booking["booking_id"]: position
        for position, booking in enumerate(ranked_bookings, start=1)
    }

    for entry, booking in entries:
        entry.position = positions[booking.booking_id]


@booking_bp.route("/", methods=["POST"])
@role_required('Customer')
def create_booking():
    """
    Create a medicine booking.

    If sufficient stock is available, allocate it.
    Otherwise, add the booking to the medicine's waitlist.

    Prescription-required medicines remain Requested until
    prescription verification is integrated.
    """

    data = request.get_json(silent=True) or {}

    # Always use the authenticated user's ID.
    # Do not trust user_id supplied in the request body.
    user_id = session.get('user_id')

    medicine_id = data.get("medicine_id")
    quantity = data.get("quantity")
    urgency = str(data.get("urgency", "")).strip().lower()
    prescription_id = data.get("prescription_id")

    # Validate required fields.
    if not medicine_id or quantity is None or not urgency:
        return jsonify({
            "error": (
                "medicine_id, quantity and urgency "
                "are required"
            )
        }), 400

    # Validate quantity.
    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or quantity <= 0
    ):
        return jsonify({
            "error": "Quantity must be a positive integer"
        }), 400

    # Validate urgency.
    if urgency not in URGENCY_SCORES:
        return jsonify({
            "error": (
                "Urgency must be emergency, high, medium or low"
            )
        }), 400

    # Verify that the authenticated user exists.
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        session.clear()
        return jsonify({
            "error": "User not found"
        }), 401

    # Check whether the medicine exists and is active.
    medicine = Medicine.query.filter_by(
        medicine_id=medicine_id,
        status="Active"
    ).first()

    if not medicine:
        return jsonify({
            "error": "Medicine not found or inactive"
        }), 404

    # Prescription-required medicines need a prescription ID.
    if medicine.prescription_required and not prescription_id:
        return jsonify({
            "error": "A prescription is required for this medicine"
        }), 400

    try:
        # Get the medicine's inventory record.
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        # Load the latest active priority rule.
        active_rule = PriorityRule.query.filter_by(
            status="Active"
        ).order_by(
            PriorityRule.created_at.desc()
        ).first()

        if active_rule:
            weights = {
                "urgency": float(active_rule.urgency_weight),
                "availability": float(active_rule.availability_weight),
                "patient_history": float(
                    active_rule.patient_history_weight
                )
            }

            rule_id = active_rule.rule_id
            rule_version = active_rule.version

        else:
            # Use provisional defaults if no active rule exists.
            weights = DEFAULT_WEIGHTS.copy()
            rule_id = None
            rule_version = "default-1"

        # These two scores remain provisional until the team
        # finalizes their calculation policies.
        factor_scores = {
            "urgency": URGENCY_SCORES[urgency],
            "availability": 50,
            "patient_history": 50
        }

        priority_score = calculate_priority_score(
            urgency_score=factor_scores["urgency"],
            availability_score=factor_scores["availability"],
            patient_history_score=factor_scores["patient_history"],
            weights=weights
        )

        booking = Booking(
            user_id=user_id,
            medicine_id=medicine_id,
            prescription_id=prescription_id,
            quantity=quantity,
            urgency=urgency,
            priority_score=priority_score,
            status="Requested"
        )
        
        # Save booking first so its ID is generated.
        db.session.add(booking)
        db.session.flush()
        
        # Save the exact priority factors and rule version
        # used to calculate this booking's priority score.
        priority_evaluation = PriorityEvaluation(
            booking_id=booking.booking_id,
            rule_id=rule_id,
            rule_version=rule_version,
            urgency_score=factor_scores["urgency"],
            availability_score=factor_scores["availability"],
            patient_history_score=factor_scores["patient_history"],
            urgency_weight=weights["urgency"],
            availability_weight=weights["availability"],
            patient_history_weight=weights["patient_history"],
            final_score=priority_score
        )

        db.session.add(priority_evaluation)

        record_audit(
            actor_id=user_id,
            action='BOOKING_CREATED',
            entity_type='Booking',
            entity_id=booking.booking_id,
            details=(
                f"Booking created; quantity={quantity}; "
                f"medicine_id={medicine_id}; urgency={urgency}"
            )
        )

        # Do not allocate stock before prescription verification.
        if medicine.prescription_required:
            create_notification(
                user_id=user_id,
                event_type='Booking',
                message=(
                    'Your booking has been created and is '
                    'awaiting prescription verification.'
                ),
                channel='In-app',
                commit=False
            )

            db.session.commit()

            return jsonify({
                "message": (
                    "Booking created. Prescription verification "
                    "is pending."
                ),
                "booking_id": booking.booking_id,
                "priority_score": priority_score,
                "status": booking.status
            }), 201
        # Check whether older active waitlist entries exist.
        existing_waitlist = (
            db.session.query(WaitlistEntry)
            .join(
                Booking,
                WaitlistEntry.booking_id == Booking.booking_id
            )
            .filter(
                WaitlistEntry.status == "Active",
                Booking.status == "Waitlisted",
                Booking.medicine_id == medicine_id
            )
            .first()
        )

        # If a queue already exists, join it instead of bypassing it.
        if existing_waitlist:
            booking.status = "Waitlisted"

            db.session.add(WaitlistEntry(
                booking_id=booking.booking_id,
                priority_score=priority_score,
                position=0,
                status="Active"
            ))
            db.session.flush()

            update_waitlist_positions(medicine_id)

            create_notification(
                user_id=user_id,
                event_type="Waitlist",
                message="Your booking has been added to the waitlist.",
                channel="In-app",
                commit=False
            )

            record_audit(
                actor_id=user_id,
                action="BOOKING_WAITLISTED",
                entity_type="Booking",
                entity_id=booking.booking_id,
                details="Booking joined the existing priority queue."
            )

            promoted = promote_waitlisted_bookings(medicine_id)

            db.session.refresh(booking)

            return jsonify({
                "message": "Booking processed using priority order.",
                "booking_id": booking.booking_id,
                "priority_score": priority_score,
                "status": booking.status,
                "promoted_count": len(promoted)
            }), 201
        # Atomically reserve stock only if sufficient quantity exists.
        allocated_rows = 0

        if inventory:
            allocated_rows = Inventory.query.filter(
                Inventory.inventory_id == inventory.inventory_id,
                Inventory.available_quantity >= quantity
            ).update(
                {
                    Inventory.available_quantity:
                        Inventory.available_quantity - quantity,
                    Inventory.reserved_quantity:
                        Inventory.reserved_quantity + quantity
                },
                synchronize_session=False
            )

        if allocated_rows == 1:

            booking.status = "Allocated"
            booking.allocated_at = utc_now()

            record_audit(
                actor_id=user_id,
                action='BOOKING_ALLOCATED',
                entity_type='Booking',
                entity_id=booking.booking_id,
                details=(
                    f"Booking allocated; quantity={quantity}; "
                    f"medicine_id={medicine_id}"
                )
            )

            create_notification(
                user_id=user_id,
                event_type='Booking',
                message='Your booking has been created.',
                channel='In-app',
                commit=False
            )

            create_notification(
                user_id=user_id,
                event_type='Allocation',
                message='Your booking has been successfully allocated.',
                channel='In-app',
                commit=False
            )

            db.session.commit()

            return jsonify({
                "message": "Booking allocated successfully",
                "booking_id": booking.booking_id,
                "priority_score": priority_score,
                "status": booking.status
            }), 201

        # Insufficient stock: add the booking to the waitlist.
        booking.status = "Waitlisted"

        record_audit(
            actor_id=user_id,
            action='BOOKING_WAITLISTED',
            entity_type='Booking',
            entity_id=booking.booking_id,
            details=(
                f"Booking added to waitlist; quantity={quantity}; "
                f"medicine_id={medicine_id}"
            )
        )

        waitlist_entry = WaitlistEntry(
            booking_id=booking.booking_id,
            priority_score=priority_score,
            position=0,
            status="Active"
        )

        db.session.add(waitlist_entry)
        db.session.flush()

        # Update positions according to priority.
        update_waitlist_positions(medicine_id)

        create_notification(
            user_id=user_id,
            event_type='Booking',
            message='Your booking has been created.',
            channel='In-app',
            commit=False
        )

        create_notification(
            user_id=user_id,
            event_type='Waitlist',
            message='Your booking has been added to the waitlist.',
            channel='In-app',
            commit=False
        )

        db.session.commit()

        # Fetch the final position after ranking.
        db.session.refresh(waitlist_entry)

        return jsonify({
            "message": (
                "Insufficient stock. Booking added to waitlist."
            ),
            "booking_id": booking.booking_id,
            "priority_score": priority_score,
            "waitlist_position": waitlist_entry.position,
            "status": booking.status
        }), 201

    except SQLAlchemyError:
        db.session.rollback()

        return jsonify({
            "error": "Database error while creating booking"
        }), 500

    except ValueError as error:
        db.session.rollback()

        return jsonify({
            "error": str(error)
        }), 400


@booking_bp.route("/<booking_id>", methods=["GET"])
@role_required('Customer', 'Pharmacy Staff', 'Administrator')
def get_booking(booking_id):
    """Retrieve booking details using the booking ID."""

    booking = Booking.query.filter_by(
        booking_id=booking_id
    ).first()

    if not booking:
        return jsonify({
            "error": "Booking not found"
        }), 404

    # Customers can only access their own bookings.
    current_user_id = session.get('user_id')
    current_user = User.query.filter_by(
        user_id=current_user_id
    ).first()

    if current_user and current_user.role == 'Customer':
        if booking.user_id != current_user_id:
            return jsonify({
                "error": "You are not authorized to view this booking"
            }), 403

    return jsonify({
        "booking_id": booking.booking_id,
        "user_id": booking.user_id,
        "medicine_id": booking.medicine_id,
        "prescription_id": booking.prescription_id,
        "quantity": booking.quantity,
        "urgency": booking.urgency,
        "priority_score": float(booking.priority_score),
        "status": booking.status,
        "created_at": (
            booking.created_at.isoformat()
            if booking.created_at else None
        ),
        "allocated_at": (
            booking.allocated_at.isoformat()
            if booking.allocated_at else None
        )
    }), 200
