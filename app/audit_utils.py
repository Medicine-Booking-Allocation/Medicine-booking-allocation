from app.models import db, AuditLog


def record_audit(
    actor_id,
    action,
    entity_type,
    entity_id=None,
    details=None
):
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Audit action is required")
    if not isinstance(entity_type, str) or not entity_type.strip():
        raise ValueError("Audit entity type is required")
    if details is not None and not isinstance(details, str):
        raise ValueError("Audit details must be a string")
    audit = AuditLog(
        actor_id=actor_id,
        action=action.strip(),
        entity_type=entity_type.strip(),
        entity_id=entity_id,
        details=details
    )
    db.session.add(audit)
    return audit
