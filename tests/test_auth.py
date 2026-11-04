import pytest
from app import create_app
from app.models import db

@pytest.fixture
def client():
    app = create_app({
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200

def test_register_user_success(client):
    # This proves FR-AUTH-01 works
    response = client.post('/api/auth/register', json={
        "full_name": "Divyaa Test",
        "email": "divyaa@pes.edu",
        "password": "securepassword",
        "phone": "9876543210",
        "role": "Customer"
    })
    assert response.status_code == 201
    assert b"User registered successfully" in response.data

def test_register_missing_fields(client):
    # This proves negative testing for FR-AUTH-01
    response = client.post('/api/auth/register', json={
        "email": "incomplete@pes.edu"
    })
    assert response.status_code == 400
    assert b"Missing required registration fields" in response.data