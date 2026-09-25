import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.screening import RetinalImage
from app.storage.local_storage import storage_service
from app.core.permissions import get_current_user

router = APIRouter(tags=["Images & Media"])

@router.get("/images/{image_id}", summary="Get retinal fundus image by ID with permission checks")
def get_retinal_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    img_record = db.query(RetinalImage).filter(
        (RetinalImage.id == image_id) | (RetinalImage.screening_id == image_id)
    ).first()
    
    if not img_record:
        raise HTTPException(status_code=404, detail=f"Image record '{image_id}' not found")
        
    full_path = storage_service.get_file_path(img_record.storage_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Image file not found on storage server")
        
    return FileResponse(full_path, media_type=img_record.mime_type or "image/jpeg")

@router.get("/media/{subfolder}/{filename}", summary="Authorized media access route")
def get_media_file(
    subfolder: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    relative_path = f"{subfolder}/{filename}"
    full_path = storage_service.get_file_path(relative_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Media file not found")
        
    media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
    return FileResponse(full_path, media_type=media_type)
