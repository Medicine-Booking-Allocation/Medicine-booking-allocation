import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import (
    db,
    User,
    Medicine,
    Inventory,
    Notification,
    AuditLog,
    WaitlistEntry,
    PriorityEvaluation,
    Booking,
    Prescription
)


@pytest.fixture
def client():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })

    with app.app_context():
        db.drop_all()
        db.create_all()

        customer = User(
            full_name="Test Customer",
            email="customer@pes.edu",
            phone="9876543210",
            password_hash=generate_password_hash("customer123"),
            role="Customer"
        )

        staff = User(
            full_name="Test Pharmacy Staff",
            email="staff@pes.edu",
            phone="9876543211",
            password_hash=generate_password_hash("staff123"),
            role="Pharmacy Staff"
        )

        medicine = Medicine(
            medicine_name="Paracetamol",
            category="Pain Relief",
            strength="500mg",
            prescription_required=False,
            status="Active"
        )

        db.session.add_all([customer, staff, medicine])
        db.session.commit()

        inventory = Inventory(
            medicine_id=medicine.medicine_id,
            available_quantity=100,
            reserved_quantity=0,
            fulfilled_quantity=0
        )

        db.session.add(inventory)
        db.session.commit()

        customer_id = customer.user_id
        medicine_id = medicine.medicine_id
        staff_id = staff.user_id

    with app.test_client() as test_client:
        yield test_client, customer_id, medicine_id, staff_id

    with app.app_context():
        db.session.remove()
        db.drop_all()


def login(test_client, email, password):
    response = test_client.post('/api/auth/login', json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200


def login_customer(test_client):
    login(test_client, "customer@pes.edu", "customer123")


def login_staff(test_client):
    login(test_client, "staff@pes.edu", "staff123")


def test_booking_allocation_creates_notifications(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    login_customer(test_client)

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "high"
        }
    )

    assert response.status_code == 201
    assert response.json["status"] == "Allocated"

    with app.app_context():
        notifications = Notification.query.filter_by(
            user_id=customer_id
        ).all()

        event_types = {
            notification.event_type
            for notification in notifications
        }

        assert "Booking" in event_types
        assert "Allocation" in event_types


def test_waitlisted_booking_creates_notifications(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    login_customer(test_client)

    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "medium"
        }
    )

    assert response.status_code == 201
    assert response.json["status"] == "Waitlisted"

    with app.app_context():
        notifications = Notification.query.filter_by(
            user_id=customer_id
        ).all()

        event_types = {
            notification.event_type
            for notification in notifications
        }

        assert "Booking" in event_types
        assert "Waitlist" in event_types


def test_promoted_waitlist_booking_notifies_customer(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    login_customer(test_client)

    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "high"
        }
    )

    assert response.status_code == 201
    assert response.json["status"] == "Waitlisted"

    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 10
        db.session.commit()

    # Promotion is a Pharmacy Staff operation.
    login_staff(test_client)

    response = test_client.post(
        f'/api/waitlist/promote/{medicine_id}'
    )

    assert response.status_code == 200
    assert response.json["promoted_count"] == 1

    with app.app_context():
        notifications = Notification.query.filter_by(
            user_id=customer_id,
            event_type='Allocation'
        ).all()

        assert len(notifications) == 1


def test_cancelled_waitlist_booking_notifies_customer(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    login_customer(test_client)

    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "medium"
        }
    )

    assert response.status_code == 201
    assert response.json["status"] == "Waitlisted"

    with app.app_context():
        entry = WaitlistEntry.query.filter_by(
            status='Active'
        ).first()

        waitlist_id = entry.waitlist_id

    # The Customer who owns the booking cancels it.
    response = test_client.patch(
        f'/api/waitlist/{waitlist_id}/cancel'
    )

    assert response.status_code == 200

    with app.app_context():
        notifications = Notification.query.filter_by(
            user_id=customer_id,
            event_type='Cancellation'
        ).all()

        assert len(notifications) == 1


def test_booking_creation_creates_audit_log(client):
    test_client, customer_id, medicine_id, staff_id = client

    login_customer(test_client)

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 2,
            "urgency": "high"
        }
    )

    assert response.status_code == 201

    with test_client.application.app_context():
        audit = AuditLog.query.filter_by(
            action='BOOKING_CREATED',
            entity_type='Booking'
        ).first()

        assert audit is not None
        assert audit.entity_id == response.json['booking_id']
        assert 'quantity=2' in audit.details


def test_booking_allocation_creates_audit_log(client):
    test_client, customer_id, medicine_id, staff_id = client

    login_customer(test_client)

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 2,
            "urgency": "high"
        }
    )

    assert response.status_code == 201
    assert response.json['status'] == 'Allocated'

    with test_client.application.app_context():
        audit = AuditLog.query.filter_by(
            action='BOOKING_ALLOCATED',
            entity_type='Booking'
        ).first()

        assert audit is not None
        assert audit.entity_id == response.json['booking_id']


def test_waitlisted_booking_creates_audit_log(client):
    test_client, customer_id, medicine_id, staff_id = client

    login_customer(test_client)

    with test_client.application.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 2,
            "urgency": "medium"
        }
    )

    assert response.status_code == 201
    assert response.json['status'] == 'Waitlisted'

    with test_client.application.app_context():
        audit = AuditLog.query.filter_by(
            action='BOOKING_WAITLISTED',
            entity_type='Booking'
        ).first()

        assert audit is not None
        assert audit.entity_id == response.json['booking_id']


def test_promoted_waitlist_booking_creates_audit_log(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    login_customer(test_client)

    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "high"
        }
    )

    assert response.status_code == 201
    assert response.json["status"] == "Waitlisted"

    booking_id = response.json["booking_id"]

    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 10
        db.session.commit()

    # Promotion is a Pharmacy Staff operation.
    login_staff(test_client)

    response = test_client.post(
        f'/api/waitlist/promote/{medicine_id}'
    )

    assert response.status_code == 200
    assert response.json["promoted_count"] == 1

    with app.app_context():
        audit = AuditLog.query.filter_by(
            action='BOOKING_ALLOCATED',
            entity_type='Booking',
            entity_id=booking_id
        ).first()

        assert audit is not None
        assert 'Waitlisted booking promoted' in audit.details


def test_cancelled_waitlist_booking_creates_audit_log(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    login_customer(test_client)

    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "medium"
        }
    )

    assert response.status_code == 201
    assert response.json["status"] == "Waitlisted"

    with app.app_context():
        entry = WaitlistEntry.query.filter_by(
            status='Active'
        ).first()

        waitlist_id = entry.waitlist_id
        booking_id = entry.booking_id

    response = test_client.patch(
        f'/api/waitlist/{waitlist_id}/cancel'
    )

    assert response.status_code == 200

    with app.app_context():
        audit = AuditLog.query.filter_by(
            action='BOOKING_CANCELLED',
            entity_type='Booking',
            entity_id=booking_id
        ).first()

        assert audit is not None
        assert 'Waitlisted booking cancelled' in audit.details


def test_higher_priority_booking_gets_first_waitlist_position(client):
    test_client, customer_id, medicine_id, staff_id = client

    login_customer(test_client)

    with test_client.application.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()
        inventory.available_quantity = 0
        db.session.commit()

    low_response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 2,
            "urgency": "low"
        }
    )
    assert low_response.status_code == 201

    high_response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 2,
            "urgency": "high"
        }
    )
    assert high_response.status_code == 201

    login_staff(test_client)

    response = test_client.get(
        f'/api/waitlist/?medicine_id={medicine_id}'
    )

    assert response.status_code == 200

    entries = response.json["waitlist"]

    positions = {
        entry["urgency"]: entry["position"]
        for entry in entries
    }

    assert positions["high"] == 1
    assert positions["low"] == 2


def test_waitlist_promotes_higher_priority_booking_first(client):
    test_client, customer_id, medicine_id, staff_id = client

    login_customer(test_client)

    with test_client.application.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()
        inventory.available_quantity = 0
        db.session.commit()

    # Create a low-priority booking first.
    low_response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 2,
            "urgency": "low"
        }
    )
    assert low_response.status_code == 201

    # Create a high-priority booking second.
    high_response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 2,
            "urgency": "high"
        }
    )
    assert high_response.status_code == 201

    # Replenish stock for only one booking.
    with test_client.application.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()
        inventory.available_quantity = 2
        db.session.commit()

    login_staff(test_client)

    response = test_client.post(
        f'/api/waitlist/promote/{medicine_id}'
    )

    assert response.status_code == 200
    assert response.json["promoted_count"] == 1

    promoted_ids = [
        item["booking_id"]
        for item in response.json["promoted_bookings"]
    ]

    assert high_response.json["booking_id"] in promoted_ids
    assert low_response.json["booking_id"] not in promoted_ids


def test_booking_saves_priority_evaluation(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    login_customer(test_client)

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "high"
        }
    )

    assert response.status_code == 201

    booking_id = response.json["booking_id"]

    with app.app_context():
        evaluation = PriorityEvaluation.query.filter_by(
            booking_id=booking_id
        ).first()

        assert evaluation is not None
        assert evaluation.rule_version == "default-1"

        assert float(evaluation.urgency_score) == 75
        assert float(evaluation.availability_score) == 50
        assert float(evaluation.patient_history_score) == 50

        assert float(evaluation.urgency_weight) == 0.4
        assert float(evaluation.availability_weight) == 0.3
        assert float(evaluation.patient_history_weight) == 0.3

        assert float(evaluation.final_score) == 60


def test_new_booking_does_not_bypass_existing_waitlist(client):
    test_client, customer_id, medicine_id, staff_id = client

    login_customer(test_client)

    # First booking: insufficient stock, so it enters waitlist.
    first_response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 150,
            "urgency": "emergency"
        }
    )

    assert first_response.status_code == 201
    assert first_response.json["status"] == "Waitlisted"

    # Record notification counts before the second booking.
    booking_before = Notification.query.filter_by(
        user_id=customer_id,
        event_type="Booking"
    ).count()

    waitlist_before = Notification.query.filter_by(
        user_id=customer_id,
        event_type="Waitlist"
    ).count()

    # Second booking arrives while the first is waiting.
    second_response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "low"
        }
    )

    assert second_response.status_code == 201

    # The lower-priority booking must not bypass the queue.
    assert second_response.json["status"] == "Waitlisted"

    # Verify that the second booking generates both notifications.
    booking_after = Notification.query.filter_by(
        user_id=customer_id,
        event_type="Booking"
    ).count()

    waitlist_after = Notification.query.filter_by(
        user_id=customer_id,
        event_type="Waitlist"
    ).count()

    assert booking_after == booking_before + 1
    assert waitlist_after == waitlist_before + 1


def test_staff_can_fulfil_allocated_booking(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    login_customer(test_client)

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "high"
        }
    )

    assert response.status_code == 201
    booking_id = response.json["booking_id"]

    login_staff(test_client)

    response = test_client.post(
        f'/api/bookings/{booking_id}/fulfil'
    )

    assert response.status_code == 200
    assert response.json["status"] == "Fulfilled"

    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        assert inventory.reserved_quantity == 0
        assert inventory.fulfilled_quantity == 5


def test_fulfilment_requires_verified_prescription(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    with app.app_context():
        medicine = db.session.get(Medicine, medicine_id)
        medicine.prescription_required = True

        prescription = Prescription(
            user_id=customer_id,
            prescription_reference="TEST-PRESCRIPTION-001",
            prescription_status="Submitted"
        )

        db.session.add(prescription)
        db.session.commit()
        prescription_id = prescription.prescription_id

    login_customer(test_client)

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "high",
            "prescription_id": prescription_id
        }
    )

    assert response.status_code == 201
    booking_id = response.json["booking_id"]

    # Simulate an allocated booking to test the prescription safeguard.
    with app.app_context():
        booking = db.session.get(Booking, booking_id)
        booking.status = "Allocated"
        db.session.commit()

    login_staff(test_client)
    response = test_client.post(
        f'/api/bookings/{booking_id}/fulfil'
    )

    assert response.status_code == 403
    assert "verified prescription" in response.json["error"].lower()

    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        assert inventory.available_quantity == 100
        assert inventory.reserved_quantity == 0
        assert inventory.fulfilled_quantity == 0


def test_customer_can_cancel_allocated_booking_and_release_stock(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    login_customer(test_client)

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "high"
        }
    )

    assert response.status_code == 201
    booking_id = response.json["booking_id"]

    response = test_client.patch(
        f'/api/bookings/{booking_id}/cancel'
    )

    assert response.status_code == 200
    assert response.json["status"] == "Cancelled"

    with app.app_context():
        # Verify that the customer receives a cancellation notification.
        notification = Notification.query.filter_by(
            user_id=customer_id,
            event_type="Cancellation"
        ).first()

        assert notification is not None
        assert notification.status == "Pending"

        # Verify that the reserved inventory is released.
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        assert inventory.available_quantity == 100
        assert inventory.reserved_quantity == 0


def test_fulfilled_booking_cannot_be_cancelled_again(client):
    test_client, customer_id, medicine_id, staff_id = client

    login_customer(test_client)

    response = test_client.post(
        '/api/bookings/',
        json={
            "medicine_id": medicine_id,
            "quantity": 5,
            "urgency": "high"
        }
    )

    assert response.status_code == 201
    booking_id = response.json["booking_id"]

    login_staff(test_client)

    response = test_client.post(
        f'/api/bookings/{booking_id}/fulfil'
    )

    assert response.status_code == 200

    login_customer(test_client)

    response = test_client.patch(
        f'/api/bookings/{booking_id}/cancel'
    )

    assert response.status_code == 409

    with test_client.application.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        assert inventory.reserved_quantity == 0
        assert inventory.fulfilled_quantity == 5
