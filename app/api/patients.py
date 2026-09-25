from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.schemas.patient import (
    PatientCreate, PatientResponse, PatientUpdate, PatientJourneyResponse
)
from app.services.patient_service import patient_service
from app.core.permissions import get_current_user, require_roles
from app.utils.audit import log_audit

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED, summary="Create new patient")
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ASHA, UserRole.PHC_DOCTOR, UserRole.ADMIN]))
):
    patient = patient_service.create_patient(db, patient_in, creator_id=current_user.id)
    log_audit(db, user_id=current_user.user_id, action="PATIENT_CREATED", entity_type="Patient", entity_id=patient.patient_id)
    return patient

@router.get("/{patient_id}", response_model=PatientResponse, summary="Get patient details")
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = patient_service.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    return patient

@router.put("/{patient_id}", response_model=PatientResponse, summary="Update patient details")
def update_patient(
    patient_id: str,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ASHA, UserRole.PHC_DOCTOR, UserRole.ADMIN]))
):
    patient = patient_service.update_patient(db, patient_id, patient_in)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    log_audit(db, user_id=current_user.user_id, action="PATIENT_UPDATED", entity_type="Patient", entity_id=patient.patient_id)
    return patient

@router.get("/{patient_id}/history", summary="Get patient screening history")
def get_patient_history(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return patient_service.get_patient_history(db, patient_id)

@router.get("/{patient_id}/journey", response_model=PatientJourneyResponse, summary="Get patient eye health journey stages")
def get_patient_journey(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return patient_service.get_patient_journey(db, patient_id)
