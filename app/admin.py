from flask import Blueprint, request, jsonify, session
from sqlalchemy.exc import SQLAlchemyError
from app.models import db,User,PriorityRule,AuditLog,Booking,WaitlistEntry,Inventory,Medicine,Prescription,Notification
from app.auth_utils import role_required
from app.priority import validate_weights
from app.audit_utils import record_audit
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)
VALID_ROLES = {
    'Customer',
    'Pharmacy Staff',
    'Administrator'
}

VALID_RULE_STATUSES = {
    'Active',
    'Inactive'
}


def apply_date_filters(query, date_column):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    try:
        if start_date:
            start = datetime.fromisoformat(
                start_date.replace('Z', '+00:00')
            )
            query = query.filter(date_column >= start)
        if end_date:
            end = datetime.fromisoformat(
                end_date.replace('Z', '+00:00')
            )
            if len(end_date) == 10:
                end += timedelta(days=1)
                query = query.filter(date_column < end)
            else:
                query = query.filter(date_column <= end)
    except ValueError:
        return None, 'Dates must use YYYY-MM-DD or ISO datetime format'
    return query, None


def audit_to_dict(audit):
    return {
        'audit_id': audit.audit_id,
        'actor_id': audit.actor_id,
        'action': audit.action,
        'entity_type': audit.entity_type,
        'entity_id': audit.entity_id,
        'timestamp': (
            audit.timestamp.isoformat()
            if audit.timestamp else None
        ),
        'details': audit.details
    }


def priority_rule_to_dict(rule):
    return {
        'rule_id': rule.rule_id,
        'rule_name': rule.rule_name,
        'urgency_weight': float(rule.urgency_weight),
        'availability_weight': float(rule.availability_weight),
        'patient_history_weight': float(
            rule.patient_history_weight
        ),
        'version': rule.version,
        'status': rule.status,
        'created_at': (
            rule.created_at.isoformat()
            if rule.created_at else None
        )
    }


@admin_bp.route('/users', methods=['GET'])
@role_required('Administrator')
def get_users():
    query = User.query
    role = request.args.get('role')
    account_status = request.args.get('account_status')
    if role:
        if role not in VALID_ROLES:
            return jsonify({'error': 'Invalid user role'}), 400
        query = query.filter_by(role=role)
    if account_status:
        if account_status not in {'Active', 'Inactive'}:
            return jsonify({'error': 'Invalid account status'}), 400
        query = query.filter_by(account_status=account_status)
    users = query.order_by(User.created_at.desc()).all()
    return jsonify({
        'total_users': len(users),
        'users': [
            {
                'user_id': user.user_id,
                'full_name': user.full_name,
                'email': user.email,
                'phone': user.phone,
                'role': user.role,
                'account_status': user.account_status,
                'created_at': (
                    user.created_at.isoformat()
                    if user.created_at else None
                )
            }
            for user in users
        ]
    }), 200


@admin_bp.route('/users/<user_id>/role', methods=['PATCH'])
@role_required('Administrator')
def update_user_role(user_id):
    data = request.get_json(silent=True) or {}
    new_role = data.get('role')
    if not isinstance(new_role, str) or new_role not in VALID_ROLES:
        return jsonify({
            'error': 'Invalid role',
            'allowed_roles': sorted(VALID_ROLES)
        }), 400
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    old_role = user.role
    if old_role == new_role:
        return jsonify({
            'message': 'User already has this role',
            'user_id': user.user_id,
            'role': user.role
        }), 200

    if (
        old_role == 'Administrator'
        and user.account_status == 'Active'
        and new_role != 'Administrator'
    ):
        active_admin_count = User.query.filter_by(
            role='Administrator',
            account_status='Active'
        ).count()
        if active_admin_count <= 1:
            return jsonify({
                'error': 'Cannot remove the last active administrator'
            }), 400
    try:
        user.role = new_role
        record_audit(
            actor_id=session.get('user_id'),
            action='UPDATE_USER_ROLE',
            entity_type='User',
            entity_id=user.user_id,
            details=f'User role changed from {old_role} to {new_role}.'
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            'error': 'Could not update user role'
        }), 500
    return jsonify({
        'message': 'User role updated successfully',
        'user_id': user.user_id,
        'old_role': old_role,
        'new_role': user.role
    }), 200


@admin_bp.route('/priority-rules', methods=['GET'])
@role_required('Administrator')
def get_priority_rules():
    status = request.args.get('status')
    query = PriorityRule.query
    if status:
        if status not in VALID_RULE_STATUSES:
            return jsonify({'error': 'Invalid priority rule status'}), 400
        query = query.filter_by(status=status)
    rules = query.order_by(PriorityRule.created_at.desc()).all()
    return jsonify({
        'total_rules': len(rules),
        'priority_rules': [
            priority_rule_to_dict(rule)
            for rule in rules
        ]
    }), 200


@admin_bp.route('/priority-rules', methods=['POST'])
@role_required('Administrator')
def create_priority_rule():
    data = request.get_json(silent=True) or {}
    rule_name = data.get('rule_name')
    version = data.get('version')
    if not isinstance(rule_name, str) or not rule_name.strip():
        return jsonify({'error': 'Rule name is required'}), 400
    if len(rule_name.strip()) > 100:
        return jsonify({'error': 'Rule name cannot exceed 100 characters'}), 400
    if not isinstance(version, str) or not version.strip():
        return jsonify({'error': 'Rule version is required'}), 400
    if len(version.strip()) > 20:
        return jsonify({'error': 'Rule version cannot exceed 20 characters'}), 400
    status = data.get('status', 'Active')
    if not isinstance(status, str) or status not in VALID_RULE_STATUSES:
        return jsonify({'error': 'Invalid priority rule status'}), 400
    weights = {
        'urgency': data.get('urgency_weight'),
        'availability': data.get('availability_weight'),
        'patient_history': data.get('patient_history_weight')
    }
    try:
        validate_weights(weights)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    rule = PriorityRule(
        rule_name=rule_name.strip(),
        urgency_weight=weights['urgency'],
        availability_weight=weights['availability'],
        patient_history_weight=weights['patient_history'],
        version=version.strip(),
        status=status
    )
    try:
        db.session.add(rule)
        db.session.flush()
        record_audit(
            actor_id=session.get('user_id'),
            action='CREATE_PRIORITY_RULE',
            entity_type='PriorityRule',
            entity_id=rule.rule_id,
            details=f'Created priority rule {rule.rule_name}, version {rule.version}.'
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            'error': 'Could not create priority rule'
        }), 500
    return jsonify({
        'message': 'Priority rule created successfully',
        'priority_rule': priority_rule_to_dict(rule)
    }), 201


@admin_bp.route('/priority-rules/<rule_id>', methods=['PATCH'])
@role_required('Administrator')
def update_priority_rule(rule_id):
    rule = db.session.get(PriorityRule, rule_id)
    if not rule:
        return jsonify({'error': 'Priority rule not found'}), 404
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    new_name = data.get('rule_name', rule.rule_name)
    new_version = data.get('version', rule.version)
    new_status = data.get('status', rule.status)
    if not isinstance(new_name, str) or not new_name.strip():
        return jsonify({'error': 'Rule name cannot be empty'}), 400
    if len(new_name.strip()) > 100:
        return jsonify({'error': 'Rule name cannot exceed 100 characters'}), 400
    if not isinstance(new_version, str) or not new_version.strip():
        return jsonify({'error': 'Rule version cannot be empty'}), 400
    if len(new_version.strip()) > 20:
        return jsonify({'error': 'Rule version cannot exceed 20 characters'}), 400
    if not isinstance(new_status, str) or new_status not in VALID_RULE_STATUSES:
        return jsonify({'error': 'Invalid priority rule status'}), 400
    weights = {
        'urgency': data.get(
            'urgency_weight',
            float(rule.urgency_weight)
        ),
        'availability': data.get(
            'availability_weight',
            float(rule.availability_weight)
        ),
        'patient_history': data.get(
            'patient_history_weight',
            float(rule.patient_history_weight)
        )
    }
    try:
        validate_weights(weights)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    old_status = rule.status
    try:
        rule.rule_name = new_name.strip()
        rule.version = new_version.strip()
        rule.status = new_status
        rule.urgency_weight = weights['urgency']
        rule.availability_weight = weights['availability']
        rule.patient_history_weight = weights['patient_history']
        action = (
            'DEACTIVATE_PRIORITY_RULE'
            if old_status == 'Active' and new_status == 'Inactive'
            else 'UPDATE_PRIORITY_RULE'
        )
        record_audit(
            actor_id=session.get('user_id'),
            action=action,
            entity_type='PriorityRule',
            entity_id=rule.rule_id,
            details=f'Updated priority rule {rule.rule_name}, version {rule.version}.'
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            'error': 'Could not update priority rule'
        }), 500
    return jsonify({
        'message': 'Priority rule updated successfully',
        'priority_rule': priority_rule_to_dict(rule)
    }), 200


@admin_bp.route('/audit-logs', methods=['GET'])
@role_required('Administrator')
def get_audit_logs():
    query = AuditLog.query
    actor_id = request.args.get('actor_id')
    action = request.args.get('action')
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id')
    if actor_id:
        query = query.filter_by(actor_id=actor_id)
    if action:
        query = query.filter_by(action=action)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if entity_id:
        query = query.filter_by(entity_id=entity_id)
    try:
        limit = int(request.args.get('limit', 100))
    except ValueError:
        return jsonify({'error': 'Limit must be an integer'}), 400
    if not 1 <= limit <= 500:
        return jsonify({'error': 'Limit must be between 1 and 500'}), 400
    logs = (
        query.order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return jsonify({
        'total_logs_returned': len(logs),
        'audit_logs': [
            audit_to_dict(log)
            for log in logs
        ]
    }), 200


# ---------------------------------------------------------
# ADMIN REPORTS
# ---------------------------------------------------------


@admin_bp.route('/reports/bookings', methods=['GET'])
@role_required('Administrator')
def booking_report():
    """Provide booking counts and booking details."""

    query = Booking.query

    status = request.args.get('status')
    medicine_id = request.args.get('medicine_id')

    if status:
        query = query.filter_by(status=status)

    if medicine_id:
        query = query.filter_by(medicine_id=medicine_id)

    query, error = apply_date_filters(query, Booking.created_at)

    if error:
        return jsonify({'error': error}), 400

    bookings = query.order_by(Booking.created_at.desc()).all()

    status_summary = {}

    for booking in bookings:
        status_summary[booking.status] = (
            status_summary.get(booking.status, 0) + 1
        )

    return jsonify({
        'total_bookings': len(bookings),
        'status_summary': status_summary,
        'bookings': [
            {
                'booking_id': booking.booking_id,
                'user_id': booking.user_id,
                'medicine_id': booking.medicine_id,
                'quantity': booking.quantity,
                'urgency': booking.urgency,
                'priority_score': float(booking.priority_score),
                'status': booking.status,
                'created_at': (
                    booking.created_at.isoformat()
                    if booking.created_at else None
                )
            }
            for booking in bookings
        ]
    }), 200


@admin_bp.route('/reports/allocations', methods=['GET'])
@role_required('Administrator')
def allocation_report():
    """Provide details of allocated bookings."""

    query = Booking.query.filter(
        Booking.allocated_at.isnot(None)
    )

    medicine_id = request.args.get('medicine_id')

    if medicine_id:
        query = query.filter_by(medicine_id=medicine_id)

    status = request.args.get('status', 'Allocated')
    query = query.filter_by(status=status)

    query, error = apply_date_filters(query, Booking.allocated_at)

    if error:
        return jsonify({'error': error}), 400

    bookings = query.order_by(Booking.allocated_at.desc()).all()

    return jsonify({
        'total_allocations': len(bookings),
        'total_quantity_allocated': sum(
            booking.quantity for booking in bookings
        ),
        'allocations': [
            {
                'booking_id': booking.booking_id,
                'medicine_id': booking.medicine_id,
                'quantity': booking.quantity,
                'urgency': booking.urgency,
                'priority_score': float(booking.priority_score),
                'status': booking.status,
                'allocated_at': booking.allocated_at.isoformat()
            }
            for booking in bookings
        ]
    }), 200


@admin_bp.route('/reports/waitlist', methods=['GET'])
@role_required('Administrator')
def waitlist_report():
    """Provide waitlist entries and their current statuses."""

    query = (
        db.session.query(WaitlistEntry, Booking)
        .join(
            Booking,
            WaitlistEntry.booking_id == Booking.booking_id
        )
    )

    status = request.args.get('status')
    medicine_id = request.args.get('medicine_id')

    if status:
        query = query.filter(WaitlistEntry.status == status)

    if medicine_id:
        query = query.filter(Booking.medicine_id == medicine_id)

    query, error = apply_date_filters(
        query,
        WaitlistEntry.created_at
    )

    if error:
        return jsonify({'error': error}), 400

    entries = query.order_by(
        WaitlistEntry.created_at.desc()
    ).all()

    return jsonify({
        'total_entries': len(entries),
        'waitlist': [
            {
                'waitlist_id': entry.waitlist_id,
                'booking_id': booking.booking_id,
                'medicine_id': booking.medicine_id,
                'quantity': booking.quantity,
                'priority_score': float(entry.priority_score),
                'position': entry.position,
                'waitlist_status': entry.status,
                'booking_status': booking.status,
                'created_at': (
                    entry.created_at.isoformat()
                    if entry.created_at else None
                )
            }
            for entry, booking in entries
        ]
    }), 200


@admin_bp.route('/reports/inventory', methods=['GET'])
@role_required('Administrator')
def inventory_report():
    """Provide inventory quantities for each medicine."""

    query = (
        db.session.query(Inventory, Medicine)
        .join(
            Medicine,
            Inventory.medicine_id == Medicine.medicine_id
        )
    )

    medicine_id = request.args.get('medicine_id')

    if medicine_id:
        query = query.filter(Inventory.medicine_id == medicine_id)

    records = query.order_by(Medicine.medicine_name.asc()).all()

    return jsonify({
        'total_inventory_records': len(records),
        'inventory': [
            {
                'inventory_id': inventory.inventory_id,
                'medicine_id': medicine.medicine_id,
                'medicine_name': medicine.medicine_name,
                'available_quantity': inventory.available_quantity,
                'reserved_quantity': inventory.reserved_quantity,
                'fulfilled_quantity': inventory.fulfilled_quantity,
                'last_updated_at': (
                    inventory.last_updated_at.isoformat()
                    if inventory.last_updated_at else None
                )
            }
            for inventory, medicine in records
        ]
    }), 200


@admin_bp.route('/reports/prescriptions', methods=['GET'])
@role_required('Administrator')
def prescription_report():
    """Provide prescription status information without references."""

    query = Prescription.query

    status = request.args.get('status')
    if status:
        query = query.filter_by(prescription_status=status)

    query, error = apply_date_filters(
        query,
        Prescription.submitted_at
    )

    if error:
        return jsonify({'error': error}), 400

    prescriptions = query.order_by(
        Prescription.submitted_at.desc()
    ).all()

    status_summary = {}

    for prescription in prescriptions:
        current_status = prescription.prescription_status
        status_summary[current_status] = (
            status_summary.get(current_status, 0) + 1
        )

    return jsonify({
        'total_prescriptions': len(prescriptions),
        'status_summary': status_summary,
        'prescriptions': [
            {
                'prescription_id': prescription.prescription_id,
                'user_id': prescription.user_id,
                'prescription_status': prescription.prescription_status,
                'submitted_at': (
                    prescription.submitted_at.isoformat()
                    if prescription.submitted_at else None
                ),
                'verified_at': (
                    prescription.verified_at.isoformat()
                    if prescription.verified_at else None
                )
            }
            for prescription in prescriptions
        ]
    }), 200


@admin_bp.route('/reports/notifications', methods=['GET'])
@role_required('Administrator')
def notification_report():
    """Provide notification delivery and status information."""
    query = Notification.query

    status = request.args.get('status')
    event_type = request.args.get('event_type')
    channel = request.args.get('channel')

    if status:
        query = query.filter_by(status=status)

    if event_type:
        query = query.filter_by(event_type=event_type)

    if channel:
        query = query.filter_by(channel=channel)

    query, error = apply_date_filters(
        query,
        Notification.created_at
    )

    if error:
        return jsonify({'error': error}), 400

    notifications = query.order_by(
        Notification.created_at.desc()
    ).all()

    status_summary = {}

    for notification in notifications:
        current_status = notification.status
        status_summary[current_status] = (
            status_summary.get(current_status, 0) + 1
        )

    return jsonify({
        'total_notifications': len(notifications),
        'status_summary': status_summary,
        'notifications': [
            {
                'notification_id': notification.notification_id,
                'user_id': notification.user_id,
                'event_type': notification.event_type,
                'channel': notification.channel,
                'status': notification.status,
                'retry_count': notification.retry_count,
                'max_retries': notification.max_retries,
                'created_at': (
                    notification.created_at.isoformat()
                    if notification.created_at else None
                )
            }
            for notification in notifications
        ]
    }), 200
