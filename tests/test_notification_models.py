
import pytest

from app import create_app
from app.models import db, User, Notification, AuditLog


@pytest.fixture
def app_context():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })

    with app.app_context():
        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


def create_test_user():
    user = User(
        full_name="Test Customer",
        email="notification_test@pes.edu",
        phone="9876543210",
        password_hash="test_hash",
        role="Customer"
    )

    db.session.add(user)
    db.session.commit()

    return user


def test_notification_creation(app_context):
    user = create_test_user()

    notification = Notification(
        user_id=user.user_id,
        event_type="Booking",
        message="Your booking has been created."
    )

    db.session.add(notification)
    db.session.commit()

    saved = Notification.query.filter_by(
        user_id=user.user_id
    ).first()

    assert saved is not None
    assert saved.event_type == "Booking"
    assert saved.message == "Your booking has been created."
    assert saved.channel == "In-app"
    assert saved.status == "Pending"
    assert saved.retry_count == 0
    assert saved.max_retries == 3
    assert saved.created_at is not None


def test_notification_custom_channel_and_status(app_context):
    user = create_test_user()

    notification = Notification(
        user_id=user.user_id,
        event_type="Allocation",
        message="Your medicine has been allocated.",
        channel="Email",
        status="Sent"
    )

    db.session.add(notification)
    db.session.commit()

    saved = Notification.query.first()

    assert saved.channel == "Email"
    assert saved.status == "Sent"


def test_audit_log_creation(app_context):
    user = create_test_user()

    audit = AuditLog(
        actor_id=user.user_id,
        action="UPDATE",
        entity_type="PriorityRule",
        entity_id="rule-001",
        details="Priority rule weights updated."
    )

    db.session.add(audit)
    db.session.commit()

    saved = AuditLog.query.first()

    assert saved is not None
    assert saved.actor_id == user.user_id
    assert saved.action == "UPDATE"
    assert saved.entity_type == "PriorityRule"
    assert saved.entity_id == "rule-001"
    assert saved.details == "Priority rule weights updated."
    assert saved.timestamp is not None


def test_system_generated_audit_log(app_context):
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
