
from functools import wraps

from flask import session, jsonify, request

from app.models import db, User
from app.audit_utils import record_audit


def log_security_event(
    action,
    actor_id=None,
    details=None
):
    """
    Record a security-related event.

    The event is committed independently so that denied
    access attempts are retained in the audit log.
    """
    try:
        record_audit(
            actor_id=actor_id,
            action=action,
            entity_type='SECURITY',
            details=details
        )
        db.session.commit()

    except Exception:
        # A logging failure must not grant access.
        db.session.rollback()


def role_required(*allowed_roles):
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            user_id = session.get('user_id')

            endpoint = request.endpoint or 'unknown'
            method = request.method

            # Case 1: No authenticated session.
            if not user_id:
                log_security_event(
                    action='UNAUTHENTICATED_ACCESS',
                    details=(
                        f'endpoint={endpoint}; '
                        f'method={method}'
                    )
                )

                return jsonify({
                    "error": "Authentication required"
                }), 401

            user = User.query.filter_by(
                user_id=user_id
            ).first()

            # Case 2: Invalid or inactive account.
            if not user or user.account_status != 'Active':

                log_security_event(
                    action='INVALID_OR_INACTIVE_ACCOUNT_ACCESS',
                    actor_id=user.user_id if user else None,
                    details=(
                        f'endpoint={endpoint}; '
                        f'method={method}'
                    )
                )

                session.clear()

                return jsonify({
                    "error": "Invalid or inactive account"
                }), 401

            # Case 3: Authenticated user has insufficient permissions.
            if user.role not in allowed_roles:

                log_security_event(
                    action='UNAUTHORIZED_ROLE_ACCESS',
                    actor_id=user.user_id,
                    details=(
                        f'endpoint={endpoint}; '
                        f'method={method}; '
                        f'user_role={user.role}; '
                        f'required_roles={",".join(allowed_roles)}'
                    )
                )

                return jsonify({
                    "error": "You do not have permission to perform this action"
                }), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator
