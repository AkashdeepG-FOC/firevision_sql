from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core import database
from ..models import models
from ..schemas import schemas
from .users import get_current_user

router = APIRouter()

@router.get("/login", response_model=List[schemas.LoginLog])
def read_login_logs(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    logs = db.query(models.LoginLog).order_by(models.LoginLog.login_time.desc()).offset(skip).limit(limit).all()
    return logs

@router.get("/system", response_model=List[schemas.SystemLog])
def read_system_logs(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    logs = db.query(models.SystemLog).order_by(models.SystemLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs
