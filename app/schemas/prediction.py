from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class PredictionResponse(BaseModel):
    screening_id: str
    grade: str
    confidence: float
    heatmap_url: Optional[str] = None
    explanation: Optional[str] = None
    recommendation: Optional[str] = None
    urgency: str
    image_quality: str = "good"
    eye: str = "RIGHT"
    findings: List[str] = []
    risk_context: Dict[str, Any] = {}
    model_version: str = "prototype-v1"

    model_config = ConfigDict(from_attributes=True)

class LegacyPredictResponse(BaseModel):
    grade: str
    confidence: float
    heatmap_url: str
    explanation: str
    recommendation: str
    urgency: str
    # Extended fields
    screening_id: Optional[str] = None
    image_quality: Optional[str] = "good"
    eye: Optional[str] = "RIGHT"
    findings: Optional[List[str]] = []
    risk_context: Optional[Dict[str, Any]] = {}
    model_version: Optional[str] = "prototype-v1"
