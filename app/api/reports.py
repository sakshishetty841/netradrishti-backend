from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.report import ReportJob
from app.schemas.report import ReportGenerateRequest, ReportJobResponse
from app.services.report_service import report_service
from app.storage.local_storage import storage_service
from app.core.permissions import get_current_user
from app.utils.audit import log_audit

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/screening/{screening_id}", summary="Download single-screening PDF report")
def download_screening_report(
    screening_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pdf_url = report_service.generate_single_screening_pdf(db, screening_id)
    full_path = storage_service.get_file_path(pdf_url)
    log_audit(db, user_id=current_user.user_id, action="SCREENING_REPORT_GENERATED", entity_type="Screening", entity_id=screening_id)
    return FileResponse(full_path, media_type="application/pdf", filename=f"screening_{screening_id}.pdf")

@router.post("/generate", response_model=ReportJobResponse, summary="Submit asynchronous report export job")
def generate_report_job(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = report_service.create_report_job(db, req.report_type, req.parameters or {}, current_user.user_id)
    log_audit(db, user_id=current_user.user_id, action="REPORT_JOB_SUBMITTED", entity_type="ReportJob", entity_id=job.job_id)
    return {
        "job_id": job.job_id,
        "report_type": job.report_type,
        "status": job.status,
        "download_url": f"/reports/jobs/{job.job_id}/download" if job.status == "COMPLETED" else None,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }

@router.get("/jobs/{job_id}", response_model=ReportJobResponse, summary="Poll report job status")
def get_report_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(ReportJob).filter((ReportJob.id == job_id) | (ReportJob.job_id == job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Report job '{job_id}' not found")
    return {
        "job_id": job.job_id,
        "report_type": job.report_type,
        "status": job.status,
        "download_url": f"/reports/jobs/{job.job_id}/download" if job.status == "COMPLETED" else None,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }

@router.get("/jobs/{job_id}/download", summary="Download completed report file")
def download_report_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(ReportJob).filter((ReportJob.id == job_id) | (ReportJob.job_id == job_id)).first()
    if not job or job.status != "COMPLETED" or not job.file_path:
        raise HTTPException(status_code=400, detail=f"Report job '{job_id}' is not ready for download")
        
    full_path = storage_service.get_file_path(job.file_path)
    log_audit(db, user_id=current_user.user_id, action="REPORT_DOWNLOADED", entity_type="ReportJob", entity_id=job.job_id)
    return FileResponse(full_path, media_type="application/pdf", filename=f"report_{job.job_id}.pdf")
