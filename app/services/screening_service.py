import json
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models.screening import Screening, RetinalImage, EyeEnum, ScreeningStatusEnum
from app.db.models.patient import Patient
from app.db.models.prediction import Prediction
from app.db.models.settings import ClinicalProtocolSettings
from app.utils.validators import validate_image_file
from app.ai.quality_check import quality_checker
from app.ai.model_adapter import screening_model
from app.ai.explainability import explainability_service
from ml.explainability.gradcam import generate_gradcam_overlay
from app.storage.local_storage import storage_service
from app.core.config import settings

DEFAULT_PROTOCOL_MAPPING = {
    "No DR": {
        "urgency": "routine",
        "recommendation": "No evidence of diabetic retinopathy. Schedule routine annual AI-assisted retinal rescreening."
    },
    "Mild": {
        "urgency": "moderate",
        "recommendation": "Mild non-proliferative DR detected. Recommend clinical review within 3-6 months and blood glucose management."
    },
    "Moderate": {
        "urgency": "high",
        "recommendation": "Moderate non-proliferative DR detected. Recommend PHC doctor clinical evaluation and referral for comprehensive eye examination within 30 days."
    },
    "Severe": {
        "urgency": "urgent",
        "recommendation": "Severe non-proliferative DR detected. Urgent specialist ophthalmology referral required within 1-2 weeks."
    },
    "Proliferative": {
        "urgency": "urgent",
        "recommendation": "Proliferative diabetic retinopathy detected. Immediate specialist ophthalmology evaluation and treatment required."
    }
}

class ScreeningService:
    def _generate_screening_id(self, db: Session) -> str:
        count = db.query(Screening).count() + 10001
        return f"SCR-{count}"

    def get_protocol_mapping(self, db: Session) -> Dict[str, Any]:
        latest_settings = db.query(ClinicalProtocolSettings).order_by(ClinicalProtocolSettings.version.desc()).first()
        if latest_settings and latest_settings.mapping_json:
            try:
                return json.loads(latest_settings.mapping_json)
            except Exception:
                pass
        return DEFAULT_PROTOCOL_MAPPING

    def create_screening_record(
        self,
        db: Session,
        patient_id: str,
        eye: EyeEnum = EyeEnum.RIGHT,
        screening_center_id: Optional[str] = None,
        health_worker_id: Optional[str] = None,
        local_id: Optional[str] = None
    ) -> Screening:
        patient = db.query(Patient).filter((Patient.id == patient_id) | (Patient.patient_id == patient_id)).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
            
        screening_id_str = self._generate_screening_id(db)
        
        screening = Screening(
            screening_id=screening_id_str,
            local_id=local_id,
            patient_id=patient.id,
            eye=eye,
            screening_center_id=screening_center_id or patient.screening_center_id,
            health_worker_id=health_worker_id,
            status=ScreeningStatusEnum.QUEUED
        )
        db.add(screening)
        db.commit()
        db.refresh(screening)
        return screening

    def analyze(
        self,
        db: Session,
        screening: Screening,
        image_bytes: bytes,
        filename: str,
        eye: Optional[EyeEnum] = None
    ) -> Dict[str, Any]:
        if eye:
            screening.eye = eye
            
        # Step 1: File Validation
        valid, err_msg, meta = validate_image_file(image_bytes, filename)
        if not valid:
            screening.status = ScreeningStatusEnum.REJECTED_POOR_QUALITY
            db.commit()
            return {
                "screening_id": screening.screening_id,
                "grade": "Uncertain",
                "confidence": 0.0,
                "heatmap_url": "",
                "explanation": f"Image file validation failed: {err_msg}",
                "recommendation": "Please capture a clear fundus image adhering to scan guidelines.",
                "urgency": "none",
                "image_quality": "poor",
                "usable": False,
                "messages": [err_msg],
                "model_version": settings.MODEL_VERSION
            }

        # Storage
        storage_url = storage_service.save_file(image_bytes, filename, subfolder="fundus_images")
        
        retinal_img = RetinalImage(
            screening_id=screening.id,
            original_filename=filename,
            storage_path=storage_url,
            mime_type=meta.get("mime_type", "image/jpeg"),
            file_size=meta.get("file_size", len(image_bytes)),
            width=meta.get("width"),
            height=meta.get("height"),
            eye=screening.eye,
            quality_status="pending"
        )
        db.add(retinal_img)
        db.flush()
        screening.image_id = retinal_img.id

        # Step 2: Quality Assessment Gating
        quality_res = quality_checker.assess_quality(image_bytes)
        retinal_img.quality_status = quality_res["status"]
        
        if not quality_res["usable"]:
            screening.status = ScreeningStatusEnum.REJECTED_POOR_QUALITY
            db.commit()
            return {
                "screening_id": screening.screening_id,
                "grade": "Poor Quality",
                "confidence": 0.0,
                "heatmap_url": "",
                "explanation": "Image failed automated quality check. AI screening halted.",
                "recommendation": "Rescan required: " + "; ".join(quality_res["messages"]),
                "urgency": "none",
                "image_quality": "poor",
                "usable": False,
                "messages": quality_res["messages"],
                "model_version": settings.MODEL_VERSION
            }

        # Step 3: Run Trained PyTorch Model Inference
        screening.status = ScreeningStatusEnum.PROCESSING
        db.commit()
        
        model_out = screening_model.predict(image_bytes)
        grade = model_out["grade"]
        confidence = model_out["confidence"]
        findings = model_out.get("findings", [])
        probabilities = model_out.get("probabilities", {})
        grade_num = model_out.get("grade_num", 0)

        # Step 4: Run Grad-CAM Explainability
        if screening_model.is_loaded and screening_model.model is not None and "model_tensor" in model_out:
            explain_out = generate_gradcam_overlay(
                screening_model.model,
                model_out["model_tensor"],
                image_bytes,
                target_class=grade_num
            )
        else:
            explain_out = explainability_service.generate(image_bytes, model_out)

        # Step 5: Recommendation Engine (Configurable clinical protocol)
        protocol = self.get_protocol_mapping(db)
        rule = protocol.get(grade, {
            "urgency": "moderate",
            "recommendation": "AI-assisted screening result requires clinical review by a healthcare provider."
        })
        
        urgency = rule.get("urgency", "routine")
        recommendation = rule.get("recommendation", "")

        # Save Prediction record
        pred = db.query(Prediction).filter(Prediction.screening_id == screening.id).first()
        if not pred:
            pred = Prediction(screening_id=screening.id)
            db.add(pred)
            
        pred.grade = grade
        pred.confidence = confidence
        pred.findings = json.dumps(findings)
        pred.heatmap_url = explain_out["heatmap_url"]
        pred.explanation = explain_out["explanation"]
        pred.recommendation = recommendation
        pred.urgency = urgency
        pred.model_name = model_out.get("model_name", settings.MODEL_NAME)
        pred.model_version = settings.MODEL_VERSION
        pred.explainability_version = settings.EXPLAINABILITY_VERSION

        screening.status = ScreeningStatusEnum.COMPLETED if urgency in ["routine", "moderate"] else ScreeningStatusEnum.REQUIRES_REVIEW
        screening.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(pred)

        risk_context = {
            "ai_triage_support": True,
            "probabilities": probabilities,
            "disclaimer": "AI-assisted retinal screening result. Requires clinical review by qualified medical professional.",
            "protocol_version": "v1"
        }

        return {
            "screening_id": screening.screening_id,
            "grade": grade,
            "grade_num": grade_num,
            "confidence": confidence,
            "probabilities": probabilities,
            "heatmap_url": explain_out["heatmap_url"],
            "explanation": explain_out["explanation"],
            "recommendation": recommendation,
            "urgency": urgency,
            "image_quality": "good",
            "eye": screening.eye.value if isinstance(screening.eye, EyeEnum) else str(screening.eye),
            "findings": findings,
            "risk_context": risk_context,
            "model_version": settings.MODEL_VERSION
        }

screening_service = ScreeningService()
