import time

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.models import (
    db,
    User,
    Medicine,
    Inventory,
    Booking,
    WaitlistEntry
)

@pytest.fixture
def workload_client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():
        db.create_all()

        customer = User(
            full_name="Workload Customer",
            email="workload@pes.edu",
            phone="9876543210",
            password_hash=generate_password_hash("customer123"),
            role="Customer"
        )

        staff = User(
            full_name="Workload Staff",
            email="workloadstaff@pes.edu",
            phone="9876543211",
            password_hash=generate_password_hash("staff123"),
            role="Pharmacy Staff"
        )

        medicine = Medicine(
            medicine_name="Workload Medicine",
            category="Testing",
            strength="500mg",
            prescription_required=False,
            status="Active"
        )

        db.session.add_all([customer, staff, medicine])
        db.session.commit()

        inventory = Inventory(
            medicine_id=medicine.medicine_id,
            available_quantity=20,
            reserved_quantity=0,
            fulfilled_quantity=0
        )

        db.session.add(inventory)
        db.session.commit()

        medicine_id = medicine.medicine_id

    with app.test_client() as client:
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "workload@pes.edu",
                "password": "customer123"
            }
        )

        assert login_response.status_code == 200

        yield client, medicine_id

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_booking_priority_allocation_waitlist_workload(
    workload_client
):
    client, medicine_id = workload_client

    # Each request uses the same medicine and customer.
    # Initial stock is 20 units.
    booking_requests = [
        {"quantity": 5, "urgency": "low"},
        {"quantity": 5, "urgency": "high"},
        {"quantity": 5, "urgency": "medium"},
        {"quantity": 5, "urgency": "emergency"},
        {"quantity": 5, "urgency": "high"},
        {"quantity": 5, "urgency": "low"},
        {"quantity": 5, "urgency": "emergency"},
        {"quantity": 5, "urgency": "medium"}
    ]

    response_times = []
    booking_ids = []

    start_time = time.perf_counter()

    # Submit the booking workload.
    for request_data in booking_requests:
        request_start = time.perf_counter()

        response = client.post(
            "/api/bookings/",
            json={
                "medicine_id": medicine_id,
                "quantity": request_data["quantity"],
                "urgency": request_data["urgency"]
            }
        )

        elapsed = time.perf_counter() - request_start
        response_times.append(elapsed)

        assert response.status_code == 201, response.json

        booking_ids.append(response.json["booking_id"])

    booking_phase_time = time.perf_counter() - start_time

    with client.application.app_context():
        allocated_before = Booking.query.filter_by(
            medicine_id=medicine_id,
            status="Allocated"
        ).count()

        waitlisted_before = Booking.query.filter_by(
            medicine_id=medicine_id,
            status="Waitlisted"
        ).count()

        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        assert allocated_before == 4
        assert waitlisted_before == 4
        assert inventory.available_quantity == 0
        assert inventory.reserved_quantity == 20

        active_entries = WaitlistEntry.query.filter_by(
            status="Active"
        ).all()

        assert len(active_entries) == 4

    # Replenish stock to test waitlist promotion.
    with client.application.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 10
        db.session.commit()

    staff_login = client.post(
        "/api/auth/login",
        json={
            "email": "workloadstaff@pes.edu",
            "password": "staff123"
        }
    )

    assert staff_login.status_code == 200

    promotion_start = time.perf_counter()

    promotion_response = client.post(
        f"/api/waitlist/promote/{medicine_id}"
    )

    promotion_time = time.perf_counter() - promotion_start

    assert promotion_response.status_code == 200
    assert promotion_response.json["promoted_count"] == 2

    total_time = booking_phase_time + promotion_time

    with client.application.app_context():
        allocated_after = Booking.query.filter_by(
            medicine_id=medicine_id,
            status="Allocated"
        ).count()

        waitlisted_after = Booking.query.filter_by(
            medicine_id=medicine_id,
            status="Waitlisted"
        ).count()

        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        promoted_entries = WaitlistEntry.query.filter_by(
            status="Promoted"
        ).count()

        active_entries_after = WaitlistEntry.query.filter_by(
            status="Active"
        ).count()

        assert allocated_after == 6
        assert waitlisted_after == 2
        assert inventory.available_quantity == 0
        assert inventory.reserved_quantity == 30
        assert promoted_entries == 2
        assert active_entries_after == 2

        assert (
            inventory.available_quantity
            + inventory.reserved_quantity
            == 30
        )

    average_time = sum(response_times) / len(response_times)
    maximum_time = max(response_times)

    print("\n--- Booking Workload Results ---")
    print(f"Total booking requests: {len(booking_requests)}")
    print(f"Allocated before replenishment: {allocated_before}")
    print(f"Waitlisted before replenishment: {waitlisted_before}")
    print(f"Promoted after replenishment: {promoted_entries}")
    print(f"Remaining waitlisted: {waitlisted_after}")
    print(f"Average booking response: {average_time:.4f} seconds")
    print(f"Maximum booking response: {maximum_time:.4f} seconds")
    print(f"Booking phase time: {booking_phase_time:.4f} seconds")
    print(f"Promotion time: {promotion_time:.4f} seconds")
    print(f"Total workflow time: {total_time:.4f} seconds")

    assert len(booking_ids) == len(booking_requests)
    assert all(response_time > 0 for response_time in response_times)
