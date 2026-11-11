import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import (
    db, User, Medicine, Inventory,
    Prescription, Notification, AuditLog
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


def test_add_stock(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "staff@pes.edu", "staff123")

    response = test_client.post('/api/inventory/add', json={
        "medicine_id": medicine_id,
        "quantity": 50
    })

    assert response.status_code == 200
    assert response.json['available_quantity'] == 150


def test_reserve_stock(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "staff@pes.edu", "staff123")

    response = test_client.post('/api/inventory/reserve', json={
        "medicine_id": medicine_id,
        "quantity": 20
    })

    assert response.status_code == 200
    assert response.json['available_quantity'] == 80
    assert response.json['reserved_quantity'] == 20


def test_reserve_insufficient_stock(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "staff@pes.edu", "staff123")

    response = test_client.post('/api/inventory/reserve', json={
        "medicine_id": medicine_id,
        "quantity": 200
    })

    assert response.status_code == 400
    assert b"Insufficient available stock" in response.data


def test_fulfil_stock(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "staff@pes.edu", "staff123")

    test_client.post('/api/inventory/reserve', json={
        "medicine_id": medicine_id,
        "quantity": 20
    })

    response = test_client.post('/api/inventory/fulfil', json={
        "medicine_id": medicine_id,
        "quantity": 10
    })

    assert response.status_code == 200
    assert response.json['reserved_quantity'] == 10
    assert response.json['fulfilled_quantity'] == 10


def test_release_stock(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "staff@pes.edu", "staff123")

    test_client.post('/api/inventory/reserve', json={
        "medicine_id": medicine_id,
        "quantity": 20
    })

    response = test_client.post('/api/inventory/release', json={
        "medicine_id": medicine_id,
        "quantity": 10
    })

    assert response.status_code == 200
    assert response.json['available_quantity'] == 90
    assert response.json['reserved_quantity'] == 10


def test_customer_cannot_add_stock(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "customer@pes.edu", "customer123")

    response = test_client.post('/api/inventory/add', json={
        "medicine_id": medicine_id,
        "quantity": 50
    })

    assert response.status_code == 403


def test_unauthenticated_user_cannot_add_stock(client):
    test_client, customer_id, medicine_id, staff_id = client

    response = test_client.post('/api/inventory/add', json={
        "medicine_id": medicine_id,
        "quantity": 50
    })

    assert response.status_code == 401


def test_submit_prescription(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "customer@pes.edu", "customer123")

    response = test_client.post('/api/prescriptions/submit', json={
        "prescription_reference": "PRESCRIPTION-001"
    })

    assert response.status_code == 201
    assert response.json['prescription_status'] == 'Submitted'


def test_update_prescription_status(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "customer@pes.edu", "customer123")

    submit_response = test_client.post(
        '/api/prescriptions/submit',
        json={"prescription_reference": "PRESCRIPTION-002"}
    )

    assert submit_response.status_code == 201
    prescription_id = submit_response.json['prescription_id']

    login(test_client, "staff@pes.edu", "staff123")

    review_response = test_client.patch(
        f'/api/prescriptions/{prescription_id}/status',
        json={"prescription_status": "Under Review"}
    )

    assert review_response.status_code == 200

    verify_response = test_client.patch(
        f'/api/prescriptions/{prescription_id}/status',
        json={"prescription_status": "Verified"}
    )

    assert verify_response.status_code == 200
    assert verify_response.json['prescription_status'] == 'Verified'
    assert verify_response.json['verified_at'] is not None


def test_invalid_prescription_transition(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "customer@pes.edu", "customer123")

    submit_response = test_client.post(
        '/api/prescriptions/submit',
        json={"prescription_reference": "PRESCRIPTION-003"}
    )

    assert submit_response.status_code == 201
    prescription_id = submit_response.json['prescription_id']

    login(test_client, "staff@pes.edu", "staff123")

    response = test_client.patch(
        f'/api/prescriptions/{prescription_id}/status',
        json={"prescription_status": "Verified"}
    )

    assert response.status_code == 400
    assert b"Invalid status transition" in response.data


def test_customer_cannot_verify_prescription(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "customer@pes.edu", "customer123")

    submit_response = test_client.post(
        '/api/prescriptions/submit',
        json={"prescription_reference": "PRESCRIPTION-004"}
    )

    prescription_id = submit_response.json['prescription_id']

    response = test_client.patch(
        f'/api/prescriptions/{prescription_id}/status',
        json={"prescription_status": "Under Review"}
    )

    assert response.status_code == 403


def test_submit_prescription_notifies_all_active_staff(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    # Add another active staff member and one inactive staff member.
    with app.app_context():
        second_staff = User(
            full_name="Second Pharmacy Staff",
            email="second_staff@pes.edu",
            phone="9876543213",
            password_hash=generate_password_hash("staff123"),
            role="Pharmacy Staff",
            account_status="Active"
        )

        inactive_staff = User(
            full_name="Inactive Pharmacy Staff",
            email="inactive_staff@pes.edu",
            phone="9876543214",
            password_hash=generate_password_hash("staff123"),
            role="Pharmacy Staff",
            account_status="Inactive"
        )

        db.session.add_all([second_staff, inactive_staff])
        db.session.commit()

        second_staff_id = second_staff.user_id
        inactive_staff_id = inactive_staff.user_id

    # Submit a prescription as the customer.
    login(test_client, "customer@pes.edu", "customer123")

    response = test_client.post(
        '/api/prescriptions/submit',
        json={"prescription_reference": "PRESCRIPTION-NOTIFY-001"}
    )

    assert response.status_code == 201

    # Verify that only active staff received notifications.
    with app.app_context():
        notifications = Notification.query.filter_by(
            event_type="Prescription"
        ).all()

        notified_user_ids = {
            notification.user_id for notification in notifications
        }

        assert notified_user_ids == {staff_id, second_staff_id}
        assert inactive_staff_id not in notified_user_ids

        assert all(
            notification.status == "Pending"
            for notification in notifications
        )


def test_submit_prescription_succeeds_without_active_staff(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    # Remove all Pharmacy Staff accounts.
    with app.app_context():
        User.query.filter_by(role="Pharmacy Staff").delete()
        db.session.commit()

    login(test_client, "customer@pes.edu", "customer123")

    response = test_client.post(
        '/api/prescriptions/submit',
        json={"prescription_reference": "PRESCRIPTION-NO-STAFF"}
    )

    assert response.status_code == 201

    with app.app_context():
        prescription = Prescription.query.filter_by(
            prescription_reference="PRESCRIPTION-NO-STAFF"
        ).first()

        assert prescription is not None
        assert prescription.prescription_status == "Submitted"

        notifications = Notification.query.filter_by(
            event_type="Prescription"
        ).all()

        assert len(notifications) == 0


def test_prescription_status_updates_notify_customer(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    # Customer submits a prescription.
    login(test_client, "customer@pes.edu", "customer123")

    submit_response = test_client.post(
        '/api/prescriptions/submit',
        json={"prescription_reference": "PRESCRIPTION-STATUS-001"}
    )

    assert submit_response.status_code == 201
    prescription_id = submit_response.json['prescription_id']

    # Pharmacy Staff updates the prescription to Under Review.
    login(test_client, "staff@pes.edu", "staff123")

    review_response = test_client.patch(
        f'/api/prescriptions/{prescription_id}/status',
        json={"prescription_status": "Under Review"}
    )

    assert review_response.status_code == 200

    # Pharmacy Staff verifies the prescription.
    verify_response = test_client.patch(
        f'/api/prescriptions/{prescription_id}/status',
        json={"prescription_status": "Verified"}
    )

    assert verify_response.status_code == 200

    # Check customer notifications.
    with app.app_context():
        notifications = Notification.query.filter_by(
            user_id=customer_id
        ).order_by(Notification.created_at.asc()).all()

        status_notifications = [
            notification for notification in notifications
            if notification.event_type == "Prescription"
        ]

        assert len(status_notifications) == 2
        assert all(
            notification.status == "Pending"
            for notification in status_notifications
        )


def test_rejected_prescription_notifies_customer(client):
    test_client, customer_id, medicine_id, staff_id = client
    app = test_client.application

    # Customer submits a prescription.
    login(test_client, "customer@pes.edu", "customer123")

    submit_response = test_client.post(
        '/api/prescriptions/submit',
        json={"prescription_reference": "PRESCRIPTION-REJECT-001"}
    )

    assert submit_response.status_code == 201
    prescription_id = submit_response.json['prescription_id']

    # Pharmacy Staff rejects the prescription.
    login(test_client, "staff@pes.edu", "staff123")

    reject_response = test_client.patch(
        f'/api/prescriptions/{prescription_id}/status',
        json={"prescription_status": "Rejected"}
    )

    assert reject_response.status_code == 200
    with app.app_context():
        notification = Notification.query.filter_by(
            user_id=customer_id,
            event_type="Rejection"
        ).first()

        assert notification is not None
        assert notification.status == "Pending"


def test_add_stock_creates_audit_log(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "staff@pes.edu", "staff123")

    response = test_client.post('/api/inventory/add', json={
        "medicine_id": medicine_id,
        "quantity": 10
    })

    assert response.status_code == 200

    with test_client.application.app_context():
        audit = AuditLog.query.filter_by(
            action='INVENTORY_ADDED',
            entity_type='Inventory'
        ).first()

        assert audit is not None
        assert audit.actor_id == staff_id


def test_reserve_stock_creates_audit_log(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "staff@pes.edu", "staff123")

    response = test_client.post('/api/inventory/reserve', json={
        "medicine_id": medicine_id,
        "quantity": 10
    })

    assert response.status_code == 200

    with test_client.application.app_context():
        audit = AuditLog.query.filter_by(
            action='INVENTORY_RESERVED',
            entity_type='Inventory'
        ).first()

        assert audit is not None
        assert audit.actor_id == staff_id


def test_fulfil_stock_creates_audit_log(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "staff@pes.edu", "staff123")

    test_client.post('/api/inventory/reserve', json={
        "medicine_id": medicine_id,
        "quantity": 10
    })

    response = test_client.post('/api/inventory/fulfil', json={
        "medicine_id": medicine_id,
        "quantity": 5
    })

    assert response.status_code == 200

    with test_client.application.app_context():
        audit = AuditLog.query.filter_by(
            action='INVENTORY_FULFILLED',
            entity_type='Inventory'
        ).first()

        assert audit is not None
        assert audit.actor_id == staff_id


def test_release_stock_creates_audit_log(client):
    test_client, customer_id, medicine_id, staff_id = client
    login(test_client, "staff@pes.edu", "staff123")

    test_client.post('/api/inventory/reserve', json={
        "medicine_id": medicine_id,
        "quantity": 10
    })

    response = test_client.post('/api/inventory/release', json={
        "medicine_id": medicine_id,
        "quantity": 5
    })

    assert response.status_code == 200

    with test_client.application.app_context():
        audit = AuditLog.query.filter_by(
            action='INVENTORY_RELEASED',
            entity_type='Inventory'
        ).first()

        assert audit is not None
        assert audit.actor_id == staff_id
