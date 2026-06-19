from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"

class AlertType(str, Enum):
    FIRE = "fire"
    SMOKE = "smoke"

# Token
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    role: UserRole = UserRole.OPERATOR

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Camera Schemas
class CameraBase(BaseModel):
    camera_name: str
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = "inactive"

class CameraCreate(CameraBase):
    user_id: Optional[int] = None

class CameraUpdate(BaseModel):
    camera_name: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None

class Camera(CameraBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Alert Schemas
class AlertBase(BaseModel):
    camera_id: int
    alert_type: str
    severity: str = "low"
    confidence_score: float
    description: Optional[str] = None
    status: str = "active"

class AlertCreate(AlertBase):
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    footage_path: Optional[str] = None

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    footage_path: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class Alert(AlertBase):
    id: int
    detected_at: datetime
    image_path: Optional[str] = None # Helper for response
    video_path: Optional[str] = None # Helper for response

    class Config:
        from_attributes = True

# Log Schemas (Removed)
