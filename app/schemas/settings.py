from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ClinicalProtocolSettingsResponse(BaseModel):
    version: int
    protocol_mapping: Dict[str, Any]
    updated_by: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClinicalProtocolSettingsUpdate(BaseModel):
    protocol_mapping: Dict[str, Any]
