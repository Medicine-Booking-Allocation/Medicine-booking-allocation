
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User

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
        return jsonify({"error": "Email already registered"}), 400

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

    if (
        not user
        or not check_password_hash(user.password_hash, data['password'])
    ):
        return jsonify({"error": "Invalid login credentials"}), 401

    if user.account_status != 'Active':
        return jsonify({"error": "Account is inactive"}), 403

    session.clear()
    session['user_id'] = user.user_id

    return jsonify({
        "message": "Login successful",
        "user_id": user.user_id,
        "role": user.role,
        "full_name": user.full_name
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()

    return jsonify({
        "message": "Logout successful"
    }), 200
