
from functools import wraps
from flask import session, jsonify
from app.models import User


def role_required(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')

            if not user_id:
                return jsonify({
                    "error": "Authentication required"
                }), 401

            user = User.query.filter_by(user_id=user_id).first()

            if not user or user.account_status != 'Active':
                session.clear()
                return jsonify({
                    "error": "Invalid or inactive account"
                }), 401

            if user.role not in allowed_roles:
                return jsonify({
                    "error": "You do not have permission to perform this action"
                }), 403

            return func(*args, **kwargs)

        return wrapper
    return decorator
