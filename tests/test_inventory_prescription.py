
import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, User, Medicine, Inventory, Prescription


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
