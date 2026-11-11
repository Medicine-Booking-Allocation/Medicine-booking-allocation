
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
    WaitlistEntry
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


def test_booking_allocation_creates_notifications(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    response = test_client.post(
        '/api/bookings/',
        json={
            "user_id": customer_id,
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
    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "user_id": customer_id,
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
    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "user_id": customer_id,
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
    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "user_id": customer_id,
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

    response = test_client.post(
        '/api/bookings/',
        json={
            "user_id": customer_id,
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

    response = test_client.post(
        '/api/bookings/',
        json={
            "user_id": customer_id,
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

    with test_client.application.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()

    response = test_client.post(
        '/api/bookings/',
        json={
            "user_id": customer_id,
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
    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()
    response = test_client.post(
        '/api/bookings/',
        json={
            "user_id": customer_id,
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
    with app.app_context():
        inventory = Inventory.query.filter_by(
            medicine_id=medicine_id
        ).first()

        inventory.available_quantity = 0
        db.session.commit()
    response = test_client.post(
        '/api/bookings/',
        json={
            "user_id": customer_id,
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
