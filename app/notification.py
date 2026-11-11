
from flask import Blueprint, request, jsonify, session, current_app

from app.models import db, User, Notification, utc_now
from app.auth_utils import role_required


notification_bp = Blueprint('notifications', __name__)


# Values supported by the project requirements and Excel layout.
VALID_EVENT_TYPES = {
    'Booking',
    'Allocation',
    'Waitlist',
    'Prescription',
    'Fulfilment',
    'Inventory',
    'Rejection',
    'Cancellation'
}

VALID_CHANNELS = {
    'Push',
    'SMS',
    'Email',
    'In-app'
}

VALID_STATUSES = {
    'Pending',
    'Sent',
    'Delivered',
    'Failed'
}


def create_notification(
    user_id,
    event_type,
    message,
    channel='In-app',
    commit=True
):
    """
    Create a notification for an existing user.

    Set commit=False when calling this function as part of
    another business operation that manages its own transaction.
    """

    if not user_id:
        raise ValueError("User ID is required")

    user = db.session.get(User, user_id)

    if not user:
        raise ValueError("Notification recipient does not exist")

    if event_type not in VALID_EVENT_TYPES:
        raise ValueError("Invalid notification event type")

    if channel not in VALID_CHANNELS:
        raise ValueError("Invalid notification channel")

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Notification message is required")

    if len(message) > 500:
        raise ValueError("Notification message cannot exceed 500 characters")

    max_retries = current_app.config.get(
        'NOTIFICATION_MAX_RETRIES',
        3
    )

    if (
        not isinstance(max_retries, int)
        or isinstance(max_retries, bool)
        or max_retries < 0
    ):
        raise ValueError("Invalid notification retry configuration")

    notification = Notification(
        user_id=user_id,
        event_type=event_type,
        message=message.strip(),
        channel=channel,
        status='Pending',
        max_retries=max_retries
    )

    db.session.add(notification)

    if commit:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    return notification


def notification_to_dict(notification):
    """Convert a notification database record into JSON-friendly data."""

    return {
        'notification_id': notification.notification_id,
        'user_id': notification.user_id,
        'event_type': notification.event_type,
        'message': notification.message,
        'channel': notification.channel,
        'status': notification.status,
        'created_at': notification.created_at.isoformat()
        if notification.created_at else None,
        'retry_count': notification.retry_count,
        'max_retries': notification.max_retries,
        'last_attempt_at': notification.last_attempt_at.isoformat()
        if notification.last_attempt_at else None
    }


@notification_bp.route('/mine', methods=['GET'])
@role_required('Customer', 'Pharmacy Staff', 'Administrator')
def get_my_notifications():
    """Return notifications belonging to the logged-in user."""

    user_id = session.get('user_id')

    query = Notification.query.filter_by(user_id=user_id)

    event_type = request.args.get('event_type')
    status = request.args.get('status')

    if event_type:
        if event_type not in VALID_EVENT_TYPES:
            return jsonify({
                'error': 'Invalid notification event type'
            }), 400

        query = query.filter_by(event_type=event_type)

    if status:
        if status not in VALID_STATUSES:
            return jsonify({
                'error': 'Invalid notification status'
            }), 400

        query = query.filter_by(status=status)

    notifications = query.order_by(
        Notification.created_at.desc()
    ).all()

    return jsonify({
        'notifications': [
            notification_to_dict(item)
            for item in notifications
        ]
    }), 200


@notification_bp.route('/<notification_id>', methods=['GET'])
@role_required('Customer', 'Pharmacy Staff', 'Administrator')
def get_notification(notification_id):
    """Retrieve one notification with ownership authorization."""

    notification = db.session.get(Notification, notification_id)

    if not notification:
        return jsonify({
            'error': 'Notification not found'
        }), 404

    user_id = session.get('user_id')
    user = db.session.get(User, user_id)

    if user.role != 'Administrator' and notification.user_id != user_id:
        return jsonify({
            'error': 'You are not authorized to view this notification'
        }), 403

    return jsonify({
        'notification': notification_to_dict(notification)
    }), 200


@notification_bp.route('/<notification_id>/status', methods=['PATCH'])
@role_required('Pharmacy Staff', 'Administrator')
def update_notification_status(notification_id):
    """Allow authorized staff to update a notification's delivery status."""

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')

    if new_status not in {'Sent', 'Delivered', 'Failed'}:
        return jsonify({
            'error': 'Invalid notification status'
        }), 400

    notification = db.session.get(Notification, notification_id)

    if not notification:
        return jsonify({
            'error': 'Notification not found'
        }), 404

    allowed_transitions = {
        'Pending': {'Sent', 'Failed'},
        'Sent': {'Delivered', 'Failed'},
        'Failed': set(),
        'Delivered': set()
    }

    if new_status not in allowed_transitions[notification.status]:
        return jsonify({
            'error': 'Invalid notification status transition'
        }), 400

    notification.status = new_status
    notification.last_attempt_at = utc_now()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            'error': 'Could not update notification status'
        }), 500

    return jsonify({
        'message': 'Notification status updated successfully',
        'notification': notification_to_dict(notification)
    }), 200


@notification_bp.route('/<notification_id>/retry', methods=['POST'])
@role_required('Pharmacy Staff', 'Administrator')
def retry_notification(notification_id):
    """Queue a failed notification for another delivery attempt."""

    notification = db.session.get(Notification, notification_id)

    if not notification:
        return jsonify({
            'error': 'Notification not found'
        }), 404

    if notification.status != 'Failed':
        return jsonify({
            'error': 'Only failed notifications can be retried'
        }), 400

    if notification.retry_count >= notification.max_retries:
        return jsonify({
            'error': 'Maximum notification retry limit reached'
        }), 400

    notification.retry_count += 1
    notification.status = 'Pending'
    notification.last_attempt_at = utc_now()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            'error': 'Could not retry notification'
        }), 500

    return jsonify({
        'message': 'Notification queued for retry',
        'notification': notification_to_dict(notification)
    }), 200
