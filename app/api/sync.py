from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.services.sync_service import sync_service
from app.core.permissions import get_current_user
from app.utils.audit import log_audit

router = APIRouter(prefix="/sync", tags=["Offline Sync"])

@router.post("/screenings", summary="Idempotently synchronize offline screening records")
async def sync_screenings(
    local_id: str = Form(...),
    patient_id: Optional[str] = Form(None),
    patient_name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
    village: Optional[str] = Form(None),
    eye: str = Form("RIGHT"),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image_bytes = await image.read()
    
    res = sync_service.sync_screening(
        db,
        local_id=local_id,
        patient_id=patient_id,
        patient_name=patient_name,
        age=age,
        gender=gender,
        village=village,
        eye_str=eye,
        image_bytes=image_bytes,
        filename=image.filename or "offline_fundus.jpg",
        health_worker_id=current_user.id
    )
    
    log_audit(db, user_id=current_user.user_id, action="OFFLINE_SYNC_EXECUTED", metadata={"local_id": local_id, "status": res["status"]})
    return res
