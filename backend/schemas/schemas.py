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
    assigned_user_id: Optional[int] = None

class CameraUpdate(BaseModel):
    camera_name: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    assigned_user_id: Optional[int] = None

class Camera(CameraBase):
    id: int
    assigned_user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Alert Schemas
class AlertBase(BaseModel):
    camera_id: int
    alert_type: AlertType
    confidence_score: float

class AlertCreate(AlertBase):
    image_path: Optional[str] = None
    video_path: Optional[str] = None

class Alert(AlertBase):
    id: int
    detected_at: datetime
    image_path: Optional[str] = None # Helper for response
    video_path: Optional[str] = None # Helper for response

    class Config:
        from_attributes = True

# Log Schemas
class LoginLogBase(BaseModel):
    user_id: int
    ip_address: str

class LoginLogCreate(LoginLogBase):
    pass

class LoginLog(LoginLogBase):
    id: int
    login_time: datetime
    logout_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class SystemLogBase(BaseModel):
    action_type: str
    description: str
    performed_by: Optional[int] = None

class SystemLogCreate(SystemLogBase):
    pass

class SystemLog(SystemLogBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
