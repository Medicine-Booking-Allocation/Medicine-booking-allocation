
import time

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.models import db, User, Medicine, Inventory


@pytest.fixture
def performance_client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():
        db.create_all()

        customer = User(
            full_name="Performance Customer",
            email="performance@pes.edu",
            phone="9876543210",
            password_hash=generate_password_hash("customer123"),
            role="Customer"
        )

        medicine = Medicine(
            medicine_name="Performance Medicine",
            category="Testing",
            strength="500mg",
            prescription_required=False,
            status="Active"
        )

        db.session.add_all([customer, medicine])
        db.session.commit()

        inventory = Inventory(
            medicine_id=medicine.medicine_id,
            available_quantity=100,
            reserved_quantity=0,
            fulfilled_quantity=0
        )

        db.session.add(inventory)
        db.session.commit()

        medicine_id = medicine.medicine_id

    with app.test_client() as test_client:
        login_response = test_client.post(
            "/api/auth/login",
            json={
                "email": "performance@pes.edu",
                "password": "customer123"
            }
        )

        assert login_response.status_code == 200

        yield test_client, medicine_id

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_booking_acknowledgement_within_three_seconds(
    performance_client
):
    client, medicine_id = performance_client

    response_times = []

    for _ in range(10):
        start_time = time.perf_counter()

        response = client.post(
            "/api/bookings/",
            json={
                "medicine_id": medicine_id,
                "quantity": 1,
                "urgency": "medium"
            }
        )

        elapsed = time.perf_counter() - start_time
        response_times.append(elapsed)

        assert response.status_code == 201

    average_time = sum(response_times) / len(response_times)
    maximum_time = max(response_times)

    print(
        f"\nAverage response time: "
        f"{average_time:.4f} seconds"
    )
    print(
        f"Maximum response time: "
        f"{maximum_time:.4f} seconds"
    )

    assert maximum_time < 3.0, (
        f"Booking acknowledgement exceeded 3 seconds: "
        f"{maximum_time:.4f}s"
    )
