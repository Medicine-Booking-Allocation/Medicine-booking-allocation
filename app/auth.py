
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import db, User
from app.audit_utils import record_audit


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if (
        not data
        or not data.get('email')
        or not data.get('password')
        or not data.get('full_name')
    ):
        return jsonify({
            "error": "Missing required registration fields"
        }), 400

    email = data['email'].strip().lower()

    if User.query.filter_by(email=email).first():
        return jsonify({
            "error": "Email already registered"
        }), 400

    hashed_password = generate_password_hash(data['password'])

    new_user = User(
        full_name=data['full_name'].strip(),
        email=email,
        phone=data.get('phone', ''),
        password_hash=hashed_password,
        role='Customer'
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "user_id": new_user.user_id
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({
            "error": "Missing email or password"
        }), 400

    email = data['email'].strip().lower()
    user = User.query.filter_by(email=email).first()

    # Failed login: unknown email or incorrect password
    if (
        not user
        or not check_password_hash(user.password_hash, data['password'])
    ):
        record_audit(
            actor_id=None,
            action='FAILED_LOGIN',
            entity_type='AUTHENTICATION',
            entity_id=None,
            details='Login failed due to invalid credentials'
        )
        db.session.commit()

        return jsonify({
            "error": "Invalid login credentials"
        }), 401

    # Login attempt by an inactive account
    if user.account_status != 'Active':
        record_audit(
            actor_id=user.user_id,
            action='FAILED_LOGIN_INACTIVE_ACCOUNT',
            entity_type='AUTHENTICATION',
            entity_id=user.user_id,
            details='Login attempted using an inactive account'
        )
        db.session.commit()

        return jsonify({
            "error": "Account is inactive"
        }), 403

    # Successful login
    session.clear()
    session['user_id'] = user.user_id

    record_audit(
        actor_id=user.user_id,
        action='SUCCESSFUL_LOGIN',
        entity_type='AUTHENTICATION',
        entity_id=user.user_id,
        details='User logged in successfully'
    )
    db.session.commit()

    return jsonify({
        "message": "Login successful",
        "user_id": user.user_id,
        "role": user.role,
        "full_name": user.full_name
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')

    # Record logout only when a user is authenticated
    if user_id:
        record_audit(
            actor_id=user_id,
            action='LOGOUT',
            entity_type='AUTHENTICATION',
            entity_id=user_id,
            details='User logged out'
        )
        db.session.commit()

    session.clear()

    return jsonify({
        "message": "Logout successful"
    }), 200
