from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ReportGenerateRequest(BaseModel):
    report_type: str # screening, patient, analytics
    parameters: Optional[Dict[str, Any]] = None

class ReportJobResponse(BaseModel):
    job_id: str
    report_type: str
    status: str
    download_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
