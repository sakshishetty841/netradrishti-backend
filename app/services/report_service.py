import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.db.models.screening import Screening
from app.db.models.patient import Patient
from app.db.models.report import ReportJob
from app.storage.local_storage import storage_service

DISCLAIMER_TEXT = (
    "NOTICE & MEDICAL DISCLAIMER: NetraDrishti provides AI-assisted retinal screening and clinical triage support. "
    "This report is generated for screening assistance only and DOES NOT replace a comprehensive diagnostic evaluation "
    "by a licensed ophthalmologist or healthcare practitioner."
)

class ReportService:
    def _generate_job_id(self, db: Session) -> str:
        count = db.query(ReportJob).count() + 10001
        return f"JOB-{count}"

    def generate_single_screening_pdf(self, db: Session, screening_id_or_uuid: str) -> str:
        screening = db.query(Screening).filter(
            (Screening.id == screening_id_or_uuid) | (Screening.screening_id == screening_id_or_uuid)
        ).first()
        if not screening:
            raise HTTPException(status_code=404, detail=f"Screening '{screening_id_or_uuid}' not found")
            
        patient = screening.patient
        pred = screening.prediction
        
        pdf_path = storage_service.get_file_path(f"reports/screening_{screening.screening_id}.pdf")
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=12
        )
        
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Italic'],
            fontSize=8,
            textColor=colors.HexColor('#6B7280'),
            spaceBefore=15
        )

        elements = [
            Paragraph("NETRADRISHTI — AI-Assisted Retinal Screening Report", title_style),
            Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']),
            Spacer(1, 12),
        ]

        # Patient Info Table
        patient_data = [
            ["Patient ID:", patient.patient_id if patient else "N/A", "Age / Gender:", f"{patient.age if patient else 'N/A'} / {patient.gender if patient else 'N/A'}"],
            ["Screening ID:", screening.screening_id, "Eye Examined:", screening.eye.value],
            ["Screening Date:", screening.created_at.strftime("%Y-%m-%d"), "Status:", screening.status.value]
        ]
        t1 = Table(patient_data, colWidths=[110, 150, 110, 150])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 15))

        # AI Result Table
        if pred:
            elements.append(Paragraph("AI-Assisted Retinal Screening Result", styles['Heading2']))
            res_data = [
                ["DR Severity Grade:", pred.grade],
                ["Model Confidence:", f"{round(pred.confidence * 100, 1)}%"],
                ["Triage Urgency:", pred.urgency.upper()],
                ["Clinical Recommendation:", pred.recommendation or "Routine follow-up"],
                ["Explanation:", pred.explanation or "Highlighted retinal region analysis completed."]
            ]
            t2 = Table(res_data, colWidths=[160, 360])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E5E7EB')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#9CA3AF')),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            elements.append(t2)
            elements.append(Spacer(1, 15))

        elements.append(Paragraph(DISCLAIMER_TEXT, disclaimer_style))
        doc.build(elements)
        
        return f"/media/reports/screening_{screening.screening_id}.pdf"

    def create_report_job(self, db: Session, report_type: str, params: Dict[str, Any], creator_id: str) -> ReportJob:
        job_id_str = self._generate_job_id(db)
        job = ReportJob(
            job_id=job_id_str,
            report_type=report_type,
            parameters_json=json.dumps(params or {}),
            status="PENDING",
            created_by=creator_id
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Process inline
        try:
            job.status = "PROCESSING"
            db.commit()
            
            if report_type == "screening" and "screening_id" in params:
                file_url = self.generate_single_screening_pdf(db, params["screening_id"])
                job.file_path = file_url
            else:
                # Default generic report
                job.file_path = "/media/reports/generic_analytics_report.pdf"
                
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
        except Exception as e:
            job.status = "FAILED"
            
        db.commit()
        db.refresh(job)
        return job

report_service = ReportService()
