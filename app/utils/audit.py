import json
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.db.models.audit import AuditLog
from app.core.logging import logger, sanitize_log_data

def log_audit(
    db: Session,
    user_id: Optional[str],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Appends an immutable audit log entry.
    """
    clean_meta = sanitize_log_data(metadata) if metadata else {}
    meta_json = json.dumps(clean_meta) if clean_meta else None
    
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        metadata_json=meta_json
    )
    
    db.add(audit_entry)
    db.commit()
    
    logger.info(f"AUDIT LOG: [{action}] user={user_id} entity={entity_type}:{entity_id}")
    return audit_entry
