import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, User, Notification, AuditLog
from app.notification import create_notification


@pytest.fixture
def app_data():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'NOTIFICATION_MAX_RETRIES': 3
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
        customer = User(
            full_name="Test Customer",
            email="customer_notification@pes.edu",
            phone="9876543210",
            password_hash=generate_password_hash("customer123"),
            role="Customer"
        )
        staff = User(
            full_name="Test Staff",
            email="staff_notification@pes.edu",
            phone="9876543211",
            password_hash=generate_password_hash("staff123"),
            role="Pharmacy Staff"
        )
        admin = User(
            full_name="Test Admin",
            email="admin_notification@pes.edu",
            phone="9876543212",
            password_hash=generate_password_hash("admin123"),
            role="Administrator"
        )
        db.session.add_all([customer, staff, admin])
        db.session.commit()
        ids = {
            'customer_id': customer.user_id,
            'staff_id': staff.user_id,
            'admin_id': admin.user_id
        }
        yield app, ids
        db.session.remove()
        db.drop_all()


def login(client, email, password):
    response = client.post('/api/auth/login', json={
        'email': email,
        'password': password
    })
    assert response.status_code == 200


def test_create_notification(app_data):
    app, ids = app_data
    notification = create_notification(
        ids['customer_id'],
        'Booking',
        'Your booking has been created.'
    )
    assert notification.notification_id is not None
    assert notification.user_id == ids['customer_id']
    assert notification.event_type == 'Booking'
    assert notification.status == 'Pending'
    assert notification.channel == 'In-app'
    assert notification.retry_count == 0
    assert notification.max_retries == 3


def test_create_notification_invalid_event(app_data):
    app, ids = app_data
    with pytest.raises(ValueError):
        create_notification(
            ids['customer_id'],
            'InvalidEvent',
            'Test message'
        )


def test_create_notification_invalid_user(app_data):
    app, ids = app_data
    with pytest.raises(ValueError):
        create_notification(
            'nonexistent-user',
            'Booking',
            'Test message'
        )


def test_unauthenticated_user_cannot_view_notifications(app_data):
    app, ids = app_data
    client = app.test_client()
    response = client.get('/api/notifications/mine')
    assert response.status_code == 401


def test_customer_can_view_own_notifications(app_data):
    app, ids = app_data
    client = app.test_client()
    create_notification(
        ids['customer_id'],
        'Booking',
        'Booking created'
    )
    create_notification(
        ids['staff_id'],
        'Prescription',
        'Prescription requires review'
    )
    login(
        client,
        'customer_notification@pes.edu',
        'customer123'
    )
    response = client.get('/api/notifications/mine')
    assert response.status_code == 200
    assert len(response.json['notifications']) == 1
    assert (
        response.json['notifications'][0]['user_id']
        == ids['customer_id']
    )


def test_customer_cannot_view_another_users_notification(app_data):
    app, ids = app_data
    client = app.test_client()
    notification = create_notification(
        ids['staff_id'],
        'Prescription',
        'Prescription requires review'
    )
    login(
        client,
        'customer_notification@pes.edu',
        'customer123'
    )
    response = client.get(
        f'/api/notifications/{notification.notification_id}'
    )
    assert response.status_code == 403


def test_admin_can_view_another_users_notification(app_data):
    app, ids = app_data
    client = app.test_client()
    notification = create_notification(
        ids['customer_id'],
        'Booking',
        'Booking created'
    )
    login(
        client,
        'admin_notification@pes.edu',
        'admin123'
    )
    response = client.get(
        f'/api/notifications/{notification.notification_id}'
    )
    assert response.status_code == 200


def test_customer_cannot_update_notification_status(app_data):
    app, ids = app_data
    client = app.test_client()
    notification = create_notification(
        ids['customer_id'],
        'Booking',
        'Booking created'
    )
    login(
        client,
        'customer_notification@pes.edu',
        'customer123'
    )
    response = client.patch(
        f'/api/notifications/{notification.notification_id}/status',
        json={'status': 'Sent'}
    )
    assert response.status_code == 403


def test_staff_can_update_notification_status(app_data):
    app, ids = app_data
    client = app.test_client()
    notification = create_notification(
        ids['customer_id'],
        'Booking',
        'Booking created'
    )
    login(
        client,
        'staff_notification@pes.edu',
        'staff123'
    )
    response = client.patch(
        f'/api/notifications/{notification.notification_id}/status',
        json={'status': 'Sent'}
    )
    assert response.status_code == 200
    assert response.json['notification']['status'] == 'Sent'


def test_invalid_notification_status_transition(app_data):
    app, ids = app_data
    client = app.test_client()
    notification = create_notification(
        ids['customer_id'],
        'Booking',
        'Booking created'
    )
    login(
        client,
        'staff_notification@pes.edu',
        'staff123'
    )
    response = client.patch(
        f'/api/notifications/{notification.notification_id}/status',
        json={'status': 'Delivered'}
    )
    assert response.status_code == 400


def test_failed_notification_can_be_retried(app_data):
    app, ids = app_data
    client = app.test_client()
    notification = create_notification(
        ids['customer_id'],
        'Booking',
        'Booking created'
    )
    notification.status = 'Failed'
    db.session.commit()
    login(
        client,
        'staff_notification@pes.edu',
        'staff123'
    )
    response = client.post(
        f'/api/notifications/{notification.notification_id}/retry'
    )
    assert response.status_code == 200
    assert response.json['notification']['status'] == 'Pending'
    assert response.json['notification']['retry_count'] == 1
    

def test_notification_cannot_exceed_retry_limit(app_data):
    app, ids = app_data
    client = app.test_client()
    notification = create_notification(
        ids['customer_id'],
        'Booking',
        'Booking created'
    )
    login(
        client,
        'staff_notification@pes.edu',
        'staff123'
    )
    for attempt in range(3):
        notification.status = 'Failed'
        db.session.commit()
        response = client.post(
            f'/api/notifications/{notification.notification_id}/retry'
        )
        assert response.status_code == 200
        assert response.json['notification']['retry_count'] == attempt + 1
    notification.status = 'Failed'
    db.session.commit()
    response = client.post(
        f'/api/notifications/{notification.notification_id}/retry'
    )
    assert response.status_code == 400
    assert b'Maximum notification retry limit reached' in response.data
    

def test_notification_model_creation(app_data):
    app, ids = app_data

    notification = Notification(
        user_id=ids['customer_id'],
        event_type="Booking",
        message="Your booking has been created."
    )

    db.session.add(notification)
    db.session.commit()

    saved = Notification.query.filter_by(
        user_id=ids['customer_id']
    ).first()

    assert saved is not None
    assert saved.event_type == "Booking"
    assert saved.message == "Your booking has been created."
    assert saved.channel == "In-app"
    assert saved.status == "Pending"
    assert saved.retry_count == 0
    assert saved.max_retries == 3
    assert saved.created_at is not None


def test_notification_model_custom_values(app_data):
    app, ids = app_data

    notification = Notification(
        user_id=ids['customer_id'],
        event_type="Allocation",
        message="Your medicine has been allocated.",
        channel="Email",
        status="Sent"
    )

    db.session.add(notification)
    db.session.commit()

    saved = Notification.query.filter_by(
        user_id=ids['customer_id']
    ).first()

    assert saved.channel == "Email"
    assert saved.status == "Sent"


def test_audit_log_model_creation(app_data):
    app, ids = app_data

    audit = AuditLog(
        actor_id=ids['customer_id'],
        action="UPDATE",
        entity_type="PriorityRule",
        entity_id="rule-001",
        details="Priority rule weights updated."
    )

    db.session.add(audit)
    db.session.commit()

    saved = AuditLog.query.first()

    assert saved is not None
    assert saved.actor_id == ids['customer_id']
    assert saved.action == "UPDATE"
    assert saved.entity_type == "PriorityRule"
    assert saved.entity_id == "rule-001"
    assert saved.details == "Priority rule weights updated."
    assert saved.timestamp is not None


def test_system_generated_audit_log(app_data):
    app, ids = app_data

    audit = AuditLog(
        actor_id="SYSTEM",
        action="AUTO_PROMOTION",
        entity_type="Booking",
        entity_id="booking-001",
        details="System promoted a waitlisted booking."
    )

    db.session.add(audit)
    db.session.commit()

    saved = AuditLog.query.first()

    assert saved is not None
    assert saved.actor_id == "SYSTEM"
    assert saved.action == "AUTO_PROMOTION"
    assert saved.timestamp is not None

