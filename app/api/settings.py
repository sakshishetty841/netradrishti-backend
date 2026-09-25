import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.db.models.settings import ClinicalProtocolSettings
from app.schemas.settings import ClinicalProtocolSettingsResponse, ClinicalProtocolSettingsUpdate
from app.services.screening_service import screening_service, DEFAULT_PROTOCOL_MAPPING
from app.core.permissions import require_roles
from app.utils.audit import log_audit

router = APIRouter(prefix="/admin/settings/clinical-protocol", tags=["Clinical Protocol Settings"])

@router.get("", response_model=ClinicalProtocolSettingsResponse, summary="Get active clinical protocol configuration")
def get_clinical_protocol(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    latest = db.query(ClinicalProtocolSettings).order_by(ClinicalProtocolSettings.version.desc()).first()
    if not latest:
        return {
            "version": 1,
            "protocol_mapping": DEFAULT_PROTOCOL_MAPPING,
            "updated_by": "system",
            "updated_at": datetime.utcnow()
        }
    return {
        "version": latest.version,
        "protocol_mapping": json.loads(latest.mapping_json),
        "updated_by": latest.updated_by,
        "updated_at": latest.updated_at
    }

@router.put("", response_model=ClinicalProtocolSettingsResponse, summary="Update clinical protocol configuration")
def update_clinical_protocol(
    req: ClinicalProtocolSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    latest = db.query(ClinicalProtocolSettings).order_by(ClinicalProtocolSettings.version.desc()).first()
    old_version = latest.version if latest else 0
    old_mapping = json.loads(latest.mapping_json) if latest and latest.mapping_json else DEFAULT_PROTOCOL_MAPPING
    
    new_version = old_version + 1
    new_mapping_str = json.dumps(req.protocol_mapping)
    
    new_settings = ClinicalProtocolSettings(
        version=new_version,
        mapping_json=new_mapping_str,
        updated_by=current_user.user_id
    )
    db.add(new_settings)
    db.commit()
    db.refresh(new_settings)
    
    log_audit(
        db,
        user_id=current_user.user_id,
        action="CLINICAL_PROTOCOL_UPDATED",
        entity_type="ClinicalProtocolSettings",
        entity_id=str(new_version),
        metadata={"old_version": old_version, "new_version": new_version, "old_mapping": old_mapping, "new_mapping": req.protocol_mapping}
    )
    
    return {
        "version": new_settings.version,
        "protocol_mapping": req.protocol_mapping,
        "updated_by": new_settings.updated_by,
        "updated_at": new_settings.updated_at
    }
