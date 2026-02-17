from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(String(50), default=UserRole.OPERATOR)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    cameras = relationship("Camera", back_populates="assigned_user")
    login_logs = relationship("LoginLog", back_populates="user")
    system_logs = relationship("SystemLog", back_populates="performer")

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_name = Column(String(100))
    location = Column(String(255))
    ip_address = Column(String(50))
    status = Column(String(20), default="inactive") # active, inactive
    assigned_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assigned_user = relationship("User", back_populates="cameras")
    alerts = relationship("Alert", back_populates="camera")

class AlertType(str, enum.Enum):
    FIRE = "fire"
    SMOKE = "smoke"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    alert_type = Column(String(50)) # fire, smoke
    confidence_score = Column(Float)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

    camera = relationship("Camera", back_populates="alerts")
    media = relationship("Media", back_populates="alert", uselist=False)

class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"))
    image_path = Column(String(255))
    video_path = Column(String(255))
    stored_at = Column(DateTime(timezone=True), server_default=func.now())

    alert = relationship("Alert", back_populates="media")

class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    login_time = Column(DateTime(timezone=True), server_default=func.now())
    logout_time = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(50))

    user = relationship("User", back_populates="login_logs")

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(100))
    description = Column(String(255))
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    performer = relationship("User", back_populates="system_logs")
