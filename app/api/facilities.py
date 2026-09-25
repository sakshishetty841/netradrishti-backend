from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.db.models.facility import ScreeningCenter
from app.core.permissions import require_roles
from app.utils.audit import log_audit

router = APIRouter(prefix="/admin/screening-centres", tags=["Admin Facility Management"])

class ScreeningCenterCreate(BaseModel):
    name: str
    facility_type: str # PHC, CHC, Vision Center, Sub-Center
    village: Optional[str] = None
    block: Optional[str] = None
    district: str
    state: str = "Karnataka"
    address: Optional[str] = None

class ScreeningCenterResponse(ScreeningCenterCreate):
    id: str
    active: bool

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[ScreeningCenterResponse], summary="List screening centres")
def list_screening_centres(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return db.query(ScreeningCenter).all()

@router.post("", response_model=ScreeningCenterResponse, status_code=status.HTTP_201_CREATED, summary="Create screening centre")
def create_screening_centre(
    req: ScreeningCenterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    center = ScreeningCenter(
        name=req.name,
        facility_type=req.facility_type,
        village=req.village,
        block=req.block,
        district=req.district,
        state=req.state,
        address=req.address
    )
    db.add(center)
    db.commit()
    db.refresh(center)
    log_audit(db, user_id=current_user.user_id, action="FACILITY_CREATED", entity_type="ScreeningCenter", entity_id=center.id)
    return center
