from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from app.models import (
    db, Booking, Medicine, Inventory, WaitlistEntry
)
from app.priority import rank_bookings

waitlist_bp = Blueprint("waitlist", __name__)

def update_waitlist_positions(medicine_id):
    """
    Recalculate active waitlist positions for a medicine.
    Highest priority comes first.
    Earlier booking time breaks ties.
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

    bookings = [
        {
            "booking_id": booking.booking_id,
            "priority_score": float(entry.priority_score),
            "created_at": booking.created_at
        }
        for entry, booking in entries
    ]

    ranked = rank_bookings(bookings)

    positions = {
        item["booking_id"]: index
        for index, item in enumerate(ranked, start=1)
    }

    for entry, booking in entries:
        entry.position = positions[booking.booking_id]

    db.session.flush()


def promote_waitlisted_bookings(medicine_id):
    """
    Allocate replenished stock to eligible waitlisted bookings
    in descending priority order.

    Call this after the inventory module updates available stock.
    """

    inventory = Inventory.query.filter_by(
        medicine_id=medicine_id
    ).first()

    if not inventory:
        return []

    medicine = Medicine.query.filter_by(
        medicine_id=medicine_id,
        status="Active"
    ).first()

    if not medicine:
        return []

    # Prescription verification must be integrated before
    # promoting bookings for prescription-required medicines.
    if medicine.prescription_required:
        return []

    entries = (
        db.session.query(WaitlistEntry, Booking)
        .join(
            Booking,
            WaitlistEntry.booking_id == Booking.booking_id
        )
        .filter(
            WaitlistEntry.status == "Active",
            Booking.status == "Waitlisted",
            Booking.medicine_id == medicine_id
        )
        .all()
    )

    ranked = rank_bookings([
        {
            "booking_id": booking.booking_id,
            "priority_score": float(entry.priority_score),
            "created_at": booking.created_at
        }
        for entry, booking in entries
    ])

    entry_map = {
        booking.booking_id: (entry, booking)
        for entry, booking in entries
    }

    promoted = []

    try:
        for item in ranked:
            entry, booking = entry_map[item["booking_id"]]

            # Stop when the next highest-priority booking
            # cannot be fulfilled with the remaining stock.
            if inventory.available_quantity < booking.quantity:
                break

            inventory.available_quantity -= booking.quantity
            inventory.reserved_quantity += booking.quantity

            booking.status = "Allocated"
            booking.allocated_at = datetime.utcnow()

            entry.status = "Promoted"

            promoted.append({
                "booking_id": booking.booking_id,
                "waitlist_id": entry.waitlist_id,
                "quantity": booking.quantity,
                "status": "Allocated"
            })

        # Recalculate positions of remaining active entries.
        update_waitlist_positions(medicine_id)

        db.session.commit()

        return promoted

    except SQLAlchemyError:
        db.session.rollback()
        raise
    
def cancel_waitlist_entry(waitlist_id):
    """
    Cancel an active waitlist entry and update its booking status.
    Recalculate positions for the affected medicine.
    """

    entry = WaitlistEntry.query.filter_by(
        waitlist_id=waitlist_id,
        status="Active"
    ).first()

    if not entry:
        return None, "Active waitlist entry not found"

    booking = Booking.query.filter_by(
        booking_id=entry.booking_id
    ).first()

    if not booking:
        return None, "Associated booking not found"

    try:
        entry.status = "Cancelled"
        booking.status = "Cancelled"

        update_waitlist_positions(booking.medicine_id)

        db.session.commit()

        return {
            "waitlist_id": entry.waitlist_id,
            "booking_id": booking.booking_id,
            "waitlist_status": entry.status,
            "booking_status": booking.status
        }, None

    except SQLAlchemyError:
        db.session.rollback()
        raise

@waitlist_bp.route("/<waitlist_id>/cancel", methods=["PATCH"])
def cancel_waitlist(waitlist_id):
    """API endpoint to cancel an active waitlist entry."""

    try:
        result, error = cancel_waitlist_entry(waitlist_id)

        if error:
            return jsonify({"error": error}), 404

        return jsonify({
            "message": "Waitlist entry cancelled successfully",
            "result": result
        }), 200

    except SQLAlchemyError:
        return jsonify({
            "error": "Database error while cancelling waitlist entry"
        }), 500

@waitlist_bp.route("/", methods=["GET"])
def get_waitlist():
    """
    Retrieve waitlist entries.

    Optional query parameters:
    - medicine_id: Filter by a particular medicine.
    - status: Filter by waitlist status (Active, Promoted,
      Cancelled, Fulfilled).

    Defaults to displaying active entries.
    """

    medicine_id = request.args.get("medicine_id")
    status = request.args.get("status", "Active").strip()

    valid_statuses = ["Active", "Promoted", "Cancelled", "Fulfilled"]

    if status not in valid_statuses:
        return jsonify({
            "error": "Invalid waitlist status",
            "valid_statuses": valid_statuses
        }), 400

    query = (
        db.session.query(WaitlistEntry, Booking, Medicine)
        .join(
            Booking,
            WaitlistEntry.booking_id == Booking.booking_id
        )
        .join(
            Medicine,
            Booking.medicine_id == Medicine.medicine_id
        )
        .filter(WaitlistEntry.status == status)
    )

    if medicine_id:
        query = query.filter(Booking.medicine_id == medicine_id)

    entries = query.order_by(
        WaitlistEntry.position.asc()
    ).all()

    results = []

    for entry, booking, medicine in entries:
        results.append({
            "waitlist_id": entry.waitlist_id,
            "booking_id": booking.booking_id,
            "user_id": booking.user_id,
            "medicine_id": medicine.medicine_id,
            "medicine_name": medicine.medicine_name,
            "quantity": booking.quantity,
            "urgency": booking.urgency,
            "priority_score": float(entry.priority_score),
            "position": entry.position,
            "waitlist_status": entry.status,
            "booking_status": booking.status,
            "created_at": (
                entry.created_at.isoformat()
                if entry.created_at else None
            )
        })

    return jsonify({
        "total_entries": len(results),
        "waitlist": results
    }), 200
    
@waitlist_bp.route("/promote/<medicine_id>", methods=["POST"])
def promote_waitlist(medicine_id):
    """Promote eligible bookings after stock replenishment."""

    try:
        promoted = promote_waitlisted_bookings(medicine_id)

        return jsonify({
            "message": "Waitlist promotion processed",
            "promoted_count": len(promoted),
            "promoted_bookings": promoted
        }), 200

    except SQLAlchemyError:
        return jsonify({
            "error": "Database error during waitlist promotion"
        }), 500
