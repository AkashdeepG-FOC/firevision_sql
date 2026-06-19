from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from ..core import database
from ..core.logger import get_logger
from ..models import models
from ..schemas import schemas
from .users import get_current_user

router = APIRouter()
log = get_logger("firevision.alerts")

@router.post("/", response_model=schemas.Alert)
def create_alert(
    alert: schemas.AlertCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_alert = models.Alert(
        camera_id=alert.camera_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        confidence_score=alert.confidence_score,
        description=alert.description,
        status=alert.status,
        footage_path=alert.footage_path
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    log.warning(
        f"FIRE ALERT created – type={alert.alert_type} severity={alert.severity} "
        f"confidence={alert.confidence_score:.2f} camera_id={alert.camera_id} "
        f"by user={current_user.email}"
    )
    return db_alert

@router.patch("/{alert_id}", response_model=schemas.Alert)
def update_alert(
    alert_id: int, 
    alert_update: schemas.AlertUpdate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not db_alert:
        log.warning(f"Alert update failed – alert_id={alert_id} not found")
        return {"error": "Alert not found"}
    
    update_data = alert_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_alert, key, value)
    
    db.commit()
    db.refresh(db_alert)
    log.info(f"Alert updated – alert_id={alert_id} fields={list(update_data.keys())} by user={current_user.email}")
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
    
    return alerts
