from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.screening import Screening, ScreeningStatusEnum, EyeEnum
from app.db.models.prediction import Prediction
from app.schemas.screening import ScreeningCreate, ScreeningResponse
from app.schemas.prediction import PredictionResponse
from app.services.screening_service import screening_service
from app.core.permissions import get_current_user
from app.utils.audit import log_audit

router = APIRouter(prefix="/screenings", tags=["Screenings"])

@router.post("", response_model=ScreeningResponse, status_code=status.HTTP_201_CREATED, summary="Create screening draft/queued record")
def create_screening(
    req: ScreeningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    screening = screening_service.create_screening_record(
        db,
        patient_id=req.patient_id,
        eye=req.eye,
        screening_center_id=req.screening_center_id,
        health_worker_id=current_user.id,
        local_id=req.local_id
    )
    log_audit(db, user_id=current_user.user_id, action="SCREENING_CREATED", entity_type="Screening", entity_id=screening.screening_id)
    return screening

@router.get("", response_model=List[ScreeningResponse], summary="List screenings with filtering and pagination")
def list_screenings(
    patient_id: Optional[str] = Query(None),
    status: Optional[ScreeningStatusEnum] = Query(None),
    eye: Optional[EyeEnum] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Screening)
    if patient_id:
        query = query.filter(Screening.patient_id == patient_id)
    if status:
        query = query.filter(Screening.status == status)
    if eye:
        query = query.filter(Screening.eye == eye)
    return query.order_by(Screening.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{screening_id}", response_model=ScreeningResponse, summary="Get screening details")
def get_screening(
    screening_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    screening = db.query(Screening).filter(
        (Screening.id == screening_id) | (Screening.screening_id == screening_id)
    ).first()
    if not screening:
        raise HTTPException(status_code=404, detail=f"Screening '{screening_id}' not found")
    return screening

@router.post("/{screening_id}/analyze", response_model=PredictionResponse, summary="Canonical trigger for AI analysis on an existing screening")
async def analyze_screening(
    screening_id: str,
    image: UploadFile = File(...),
    eye: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    screening = db.query(Screening).filter(
        (Screening.id == screening_id) | (Screening.screening_id == screening_id)
    ).first()
    if not screening:
        raise HTTPException(status_code=404, detail=f"Screening '{screening_id}' not found")

    image_bytes = await image.read()
    eye_enum = EyeEnum(eye.upper()) if eye else screening.eye

    res = screening_service.analyze(
        db,
        screening=screening,
        image_bytes=image_bytes,
        filename=image.filename or "fundus_scan.jpg",
        eye=eye_enum
    )
    
    log_audit(db, user_id=current_user.user_id, action="SCREENING_ANALYZED", entity_type="Screening", entity_id=screening.screening_id)
    return res

@router.get("/{screening_id}/result", response_model=PredictionResponse, summary="Get AI prediction result for screening")
def get_screening_result(
    screening_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    screening = db.query(Screening).filter(
        (Screening.id == screening_id) | (Screening.screening_id == screening_id)
    ).first()
    if not screening:
        raise HTTPException(status_code=404, detail=f"Screening '{screening_id}' not found")
        
    pred = screening.prediction
    if not pred:
        raise HTTPException(status_code=404, detail="AI prediction result not found for this screening")
        
    import json
    findings_list = json.loads(pred.findings) if pred.findings else []
    
    return {
        "screening_id": screening.screening_id,
        "grade": pred.grade,
        "confidence": pred.confidence,
        "heatmap_url": pred.heatmap_url,
        "explanation": pred.explanation,
        "recommendation": pred.recommendation,
        "urgency": pred.urgency,
        "image_quality": "good",
        "eye": screening.eye.value,
        "findings": findings_list,
        "risk_context": {"ai_triage_support": True},
        "model_version": pred.model_version
    }
