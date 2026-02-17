from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from ..core import database
from ..models import models
from ..schemas import schemas
from .users import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.Alert)
def create_alert(alert: schemas.AlertCreate, db: Session = Depends(database.get_db)):
    # Create Alert
    db_alert = models.Alert(
        camera_id=alert.camera_id,
        alert_type=alert.alert_type,
        confidence_score=alert.confidence_score
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    
    # Create Media if paths provided
    if alert.image_path or alert.video_path:
        db_media = models.Media(
            alert_id=db_alert.id,
            image_path=alert.image_path,
            video_path=alert.video_path
        )
        db.add(db_media)
        db.commit()
        
    return db_alert

@router.get("/", response_model=List[schemas.Alert])
def read_alerts(
    skip: int = 0, 
    limit: int = 100, 
    camera_id: Optional[int] = None,
    alert_type: Optional[str] = None,
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Alert)
    
    if camera_id:
        query = query.filter(models.Alert.camera_id == camera_id)
    if alert_type:
        query = query.filter(models.Alert.alert_type == alert_type)
        
    alerts = query.order_by(models.Alert.detected_at.desc()).offset(skip).limit(limit).all()
    
    # Enrich response with media paths (simplistic approach, cleaner would be to use JOINs or Pydantic relationships)
    for alert in alerts:
        if alert.media:
            alert.image_path = alert.media.image_path
            alert.video_path = alert.media.video_path
            
    return alerts
