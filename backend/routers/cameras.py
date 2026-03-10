from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core import database
from ..models import models
from ..schemas import schemas
from .users import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.Camera)
def create_camera(camera: schemas.CameraCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    print(f"DEBUG: Received camera create request for user {current_user.email}: {camera.dict()}")
    camera_data = camera.dict()
    # Ensure the camera is linked to the logged-in user
    camera_data["user_id"] = current_user.id
    db_camera = models.Camera(**camera_data)
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.get("/", response_model=List[schemas.Camera])
def read_cameras(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Camera)
    # Admin can see all cameras, others only see theirs
    if current_user.role != "admin":
        query = query.filter(models.Camera.user_id == current_user.id)
    
    cameras = query.offset(skip).limit(limit).all()
    return cameras

@router.get("/{camera_id}", response_model=schemas.Camera)
def read_camera(camera_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Ownership/Admin check
    if current_user.role != "admin" and db_camera.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this camera")
        
    return db_camera

@router.delete("/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Ownership/Admin check
    if current_user.role != "admin" and db_camera.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this camera")
    
    db.delete(db_camera)
    db.commit()
    return {"detail": "Camera deleted"}
