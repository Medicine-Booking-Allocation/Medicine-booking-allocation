
import pytest
from werkzeug.security import generate_password_hash
from datetime import datetime
from app import create_app
from app.models import (
    db,
    User,
    PriorityRule,
    AuditLog,
    Medicine,
    Inventory,
    Booking,
    WaitlistEntry,
    Prescription,
    Notification
)


@pytest.fixture
def admin_data():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'NOTIFICATION_MAX_RETRIES': 3
    })

    with app.app_context():
        db.drop_all()
        db.create_all()

        customer = User(
            full_name='Test Customer',
            email='customer_admin@pes.edu',
            phone='9876500001',
            password_hash=generate_password_hash('customer123'),
            role='Customer'
        )

        staff = User(
            full_name='Test Staff',
            email='staff_admin@pes.edu',
            phone='9876500002',
            password_hash=generate_password_hash('staff123'),
            role='Pharmacy Staff'
        )

        admin = User(
            full_name='Test Admin',
            email='admin_test@pes.edu',
            phone='9876500003',
            password_hash=generate_password_hash('admin123'),
            role='Administrator'
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


def create_rule(client):
    return client.post('/api/admin/priority-rules', json={
        'rule_name': 'Default Priority',
        'version': '1.0',
        'urgency_weight': 0.4,
        'availability_weight': 0.3,
        'patient_history_weight': 0.3,
        'status': 'Active'
    })


# ---------------------------------------------------------
# AUTHENTICATION AND AUTHORIZATION
# ---------------------------------------------------------

def test_unauthenticated_user_cannot_access_admin(admin_data):
    app, ids = admin_data
    client = app.test_client()

    response = client.get('/api/admin/users')

    assert response.status_code == 401


def test_customer_cannot_access_admin(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'customer_admin@pes.edu', 'customer123')

    response = client.get('/api/admin/users')

    assert response.status_code == 403


def test_staff_cannot_access_admin(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'staff_admin@pes.edu', 'staff123')

    response = client.get('/api/admin/users')

    assert response.status_code == 403


# ---------------------------------------------------------
# USER MANAGEMENT
# ---------------------------------------------------------

def test_admin_can_list_users(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/users')

    assert response.status_code == 200
    assert response.json['total_users'] == 3
    assert len(response.json['users']) == 3
    assert 'password_hash' not in response.json['users'][0]


def test_admin_can_filter_users_by_role(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/users?role=Customer')

    assert response.status_code == 200
    assert response.json['total_users'] == 1
    assert response.json['users'][0]['role'] == 'Customer'


def test_admin_rejects_invalid_user_role_filter(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/users?role=Invalid')

    assert response.status_code == 400


def test_admin_can_update_user_role(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.patch(
        f"/api/admin/users/{ids['customer_id']}/role",
        json={'role': 'Pharmacy Staff'}
    )

    assert response.status_code == 200
    assert response.json['new_role'] == 'Pharmacy Staff'

    updated_user = db.session.get(User, ids['customer_id'])
    assert updated_user.role == 'Pharmacy Staff'

    audit = AuditLog.query.filter_by(
        action='UPDATE_USER_ROLE'
    ).first()

    assert audit is not None
    assert audit.actor_id == ids['admin_id']


def test_admin_cannot_assign_invalid_role(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.patch(
        f"/api/admin/users/{ids['customer_id']}/role",
        json={'role': 'Superuser'}
    )

    assert response.status_code == 400


def test_admin_cannot_demote_last_active_admin(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.patch(
        f"/api/admin/users/{ids['admin_id']}/role",
        json={'role': 'Customer'}
    )

    assert response.status_code == 400


def test_admin_cannot_update_nonexistent_user(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.patch(
        '/api/admin/users/nonexistent-user/role',
        json={'role': 'Customer'}
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# PRIORITY RULE MANAGEMENT
# ---------------------------------------------------------

def test_admin_can_create_priority_rule(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = create_rule(client)

    assert response.status_code == 201
    assert response.json['priority_rule']['rule_name'] == 'Default Priority'

    assert PriorityRule.query.count() == 1
    assert AuditLog.query.filter_by(
        action='CREATE_PRIORITY_RULE'
    ).count() == 1


def test_admin_cannot_create_priority_rule_with_invalid_weights(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.post('/api/admin/priority-rules', json={
        'rule_name': 'Invalid Rule',
        'version': '1.0',
        'urgency_weight': 0.5,
        'availability_weight': 0.5,
        'patient_history_weight': 0.5
    })

    assert response.status_code == 400
    assert PriorityRule.query.count() == 0


def test_admin_can_list_priority_rules(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')
    create_rule(client)

    response = client.get('/api/admin/priority-rules')

    assert response.status_code == 200
    assert response.json['total_rules'] == 1


def test_admin_can_deactivate_priority_rule(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')
    create_rule(client)

    rule = PriorityRule.query.first()

    response = client.patch(
        f'/api/admin/priority-rules/{rule.rule_id}',
        json={'status': 'Inactive'}
    )

    assert response.status_code == 200
    assert response.json['priority_rule']['status'] == 'Inactive'

    audit = AuditLog.query.filter_by(
        action='DEACTIVATE_PRIORITY_RULE'
    ).first()

    assert audit is not None


def test_admin_cannot_update_nonexistent_priority_rule(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.patch(
        '/api/admin/priority-rules/nonexistent-rule',
        json={'status': 'Inactive'}
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# AUDIT LOGS
# ---------------------------------------------------------

def test_admin_can_view_audit_logs(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    db.session.add(AuditLog(
        actor_id=ids['admin_id'],
        action='TEST_ACTION',
        entity_type='Test',
        entity_id='test-001',
        details='Test audit entry'
    ))
    db.session.commit()

    response = client.get('/api/admin/audit-logs')

    assert response.status_code == 200
    assert response.json['total_logs_returned'] == 1
    assert response.json['audit_logs'][0]['action'] == 'TEST_ACTION'


def test_admin_audit_log_limit_validation(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/audit-logs?limit=invalid')

    assert response.status_code == 400


def test_admin_cannot_use_excessive_audit_limit(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/audit-logs?limit=501')

    assert response.status_code == 400


# ---------------------------------------------------------
# REPORT ENDPOINT ACCESS
# ---------------------------------------------------------

@pytest.mark.parametrize('endpoint', [
    '/api/admin/reports/bookings',
    '/api/admin/reports/allocations',
    '/api/admin/reports/waitlist',
    '/api/admin/reports/inventory',
    '/api/admin/reports/prescriptions',
    '/api/admin/reports/notifications'
])
def test_reports_require_admin(endpoint, admin_data):
    app, ids = admin_data
    client = app.test_client()

    response = client.get(endpoint)

    assert response.status_code == 401


# ---------------------------------------------------------
# REPORT ENDPOINTS
# ---------------------------------------------------------

def test_booking_report_returns_empty_report(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/reports/bookings')

    assert response.status_code == 200
    assert response.json['total_bookings'] == 0


def test_allocation_report_returns_empty_report(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/reports/allocations')

    assert response.status_code == 200
    assert response.json['total_allocations'] == 0


def test_waitlist_report_returns_empty_report(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/reports/waitlist')

    assert response.status_code == 200
    assert response.json['total_entries'] == 0


def test_inventory_report_returns_empty_report(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/reports/inventory')

    assert response.status_code == 200
    assert response.json['total_inventory_records'] == 0


def test_prescription_report_returns_empty_report(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/reports/prescriptions')

    assert response.status_code == 200
    assert response.json['total_prescriptions'] == 0


def test_notification_report_returns_empty_report(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get('/api/admin/reports/notifications')

    assert response.status_code == 200
    assert response.json['total_notifications'] == 0


def test_report_rejects_invalid_start_date(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    response = client.get(
        '/api/admin/reports/bookings?start_date=not-a-date'
    )

    assert response.status_code == 400
    
# ---------------------------------------------------------
# POPULATED ADMIN REPORT TESTS
# ---------------------------------------------------------

def test_booking_report_returns_actual_booking_data(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    medicine = Medicine(
        medicine_name='Paracetamol',
        category='Pain Relief',
        strength='500mg'
    )
    db.session.add(medicine)
    db.session.flush()

    booking = Booking(
        user_id=ids['customer_id'],
        medicine_id=medicine.medicine_id,
        quantity=5,
        urgency='high',
        priority_score=75,
        status='Requested'
    )
    db.session.add(booking)
    db.session.commit()

    response = client.get('/api/admin/reports/bookings')

    assert response.status_code == 200
    assert response.json['total_bookings'] == 1
    assert response.json['status_summary']['Requested'] == 1
    assert response.json['bookings'][0]['booking_id'] == booking.booking_id
    assert response.json['bookings'][0]['quantity'] == 5
    assert response.json['bookings'][0]['urgency'] == 'high'


def test_allocation_report_returns_actual_allocation_data(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    medicine = Medicine(
        medicine_name='Cetirizine',
        category='Antihistamine',
        strength='10mg'
    )
    db.session.add(medicine)
    db.session.flush()

    booking = Booking(
        user_id=ids['customer_id'],
        medicine_id=medicine.medicine_id,
        quantity=4,
        urgency='medium',
        priority_score=50,
        status='Allocated',
        allocated_at=datetime(2026, 1, 10, 12, 0, 0)
    )
    db.session.add(booking)
    db.session.commit()

    response = client.get('/api/admin/reports/allocations')

    assert response.status_code == 200
    assert response.json['total_allocations'] == 1
    assert response.json['total_quantity_allocated'] == 4
    assert response.json['allocations'][0]['booking_id'] == booking.booking_id
    assert response.json['allocations'][0]['status'] == 'Allocated'


def test_waitlist_report_returns_actual_waitlist_data(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    medicine = Medicine(
        medicine_name='Azithromycin',
        category='Antibiotic',
        strength='250mg'
    )
    db.session.add(medicine)
    db.session.flush()

    booking = Booking(
        user_id=ids['customer_id'],
        medicine_id=medicine.medicine_id,
        quantity=3,
        urgency='high',
        priority_score=75,
        status='Waitlisted'
    )
    db.session.add(booking)
    db.session.flush()

    entry = WaitlistEntry(
        booking_id=booking.booking_id,
        priority_score=75,
        position=1,
        status='Active'
    )
    db.session.add(entry)
    db.session.commit()

    response = client.get('/api/admin/reports/waitlist')

    assert response.status_code == 200
    assert response.json['total_entries'] == 1
    assert response.json['waitlist'][0]['booking_id'] == booking.booking_id
    assert response.json['waitlist'][0]['position'] == 1
    assert response.json['waitlist'][0]['waitlist_status'] == 'Active'
    assert response.json['waitlist'][0]['booking_status'] == 'Waitlisted'


def test_inventory_report_returns_actual_inventory_data(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    medicine = Medicine(
        medicine_name='Amoxicillin',
        category='Antibiotic',
        strength='500mg'
    )
    db.session.add(medicine)
    db.session.flush()

    inventory = Inventory(
        medicine_id=medicine.medicine_id,
        available_quantity=100,
        reserved_quantity=20,
        fulfilled_quantity=10
    )
    db.session.add(inventory)
    db.session.commit()

    response = client.get('/api/admin/reports/inventory')

    assert response.status_code == 200
    assert response.json['total_inventory_records'] == 1
    assert response.json['inventory'][0]['medicine_name'] == 'Amoxicillin'
    assert response.json['inventory'][0]['available_quantity'] == 100
    assert response.json['inventory'][0]['reserved_quantity'] == 20
    assert response.json['inventory'][0]['fulfilled_quantity'] == 10


def test_prescription_report_returns_actual_prescription_data(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    prescription = Prescription(
        user_id=ids['customer_id'],
        prescription_reference='PRIVATE-REF-001',
        prescription_status='Verified',
        verified_at=datetime(2026, 1, 10, 12, 0, 0)
    )
    db.session.add(prescription)
    db.session.commit()

    response = client.get('/api/admin/reports/prescriptions')

    assert response.status_code == 200
    assert response.json['total_prescriptions'] == 1
    assert response.json['status_summary']['Verified'] == 1
    assert response.json['prescriptions'][0]['prescription_id'] == prescription.prescription_id
    assert response.json['prescriptions'][0]['prescription_status'] == 'Verified'

    # Prescription references must not be exposed in the report.
    assert 'prescription_reference' not in response.json['prescriptions'][0]


def test_notification_report_returns_actual_notification_data(admin_data):
    app, ids = admin_data
    client = app.test_client()

    login(client, 'admin_test@pes.edu', 'admin123')

    notification = Notification(
        user_id=ids['customer_id'],
        event_type='Allocation',
        message='Your medicine booking has been allocated.',
        channel='In-app',
        status='Sent',
        retry_count=1,
        max_retries=3
    )
    db.session.add(notification)
    db.session.commit()

    response = client.get('/api/admin/reports/notifications')

    assert response.status_code == 200
    assert response.json['total_notifications'] == 1
    assert response.json['status_summary']['Sent'] == 1
    assert response.json['notifications'][0]['notification_id'] == notification.notification_id
    assert response.json['notifications'][0]['event_type'] == 'Allocation'
    assert response.json['notifications'][0]['status'] == 'Sent'
    assert response.json['notifications'][0]['retry_count'] == 1

    # Notification message contents must not be exposed in the report.
    assert 'message' not in response.json['notifications'][0]

