
import re

from app.models import db, AuditLog


# Redact values assigned to commonly used sensitive field names.
# Values end at whitespace, a comma, a semicolon, or a newline.
SENSITIVE_VALUE_PATTERN = re.compile(
    r'\b(password|passwd|pwd|token|access_token|refresh_token|'
    r'secret|client_secret|api_key|authorization|cookie|session)'
    r'\b\s*([=:])\s*(?:Bearer\s+)?[^\s,;\n]+',
    re.IGNORECASE
)


def _sanitize_audit_details(details):
    """
    Redact explicitly labelled sensitive values from audit details.
    """
    if details is None:
        return None

    return SENSITIVE_VALUE_PATTERN.sub(
        lambda match: f'{match.group(1)}{match.group(2)}[REDACTED]',
        details
    )


def record_audit(
    actor_id,
    action,
    entity_type,
    entity_id=None,
    details=None
):
    """
    Create an audit record in the current database session.

    The caller remains responsible for committing or rolling back
    the transaction.
    """

    # Validate actor and entity identifiers.
    for field_name, value in (
        ('actor_id', actor_id),
        ('entity_id', entity_id)
    ):
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(
                    f'Audit {field_name} must be a string or None'
                )

            if len(value) > 36:
                raise ValueError(
                    f'Audit {field_name} cannot exceed 36 characters'
                )

    # Validate and normalize action.
    if not isinstance(action, str) or not action.strip():
        raise ValueError('Audit action is required')

    action = action.strip()

    if len(action) > 100:
        raise ValueError(
            'Audit action cannot exceed 100 characters'
        )

    # Validate and normalize entity type.
    if not isinstance(entity_type, str) or not entity_type.strip():
        raise ValueError('Audit entity type is required')

    entity_type = entity_type.strip()

    if len(entity_type) > 50:
        raise ValueError(
            'Audit entity type cannot exceed 50 characters'
        )

    # Validate and sanitize details.
    if details is not None and not isinstance(details, str):
        raise ValueError('Audit details must be a string')

    details = _sanitize_audit_details(details)

    audit = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details
    )

    db.session.add(audit)

    return audit
