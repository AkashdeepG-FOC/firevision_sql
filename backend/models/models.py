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

    cameras = relationship("Camera", back_populates="user", cascade="all, delete-orphan")

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_name = Column(String(100))
    location = Column(String(255))
    ip_address = Column(String(50))
    status = Column(String(20), default="inactive") # active, inactive
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="cameras")
    alerts = relationship("Alert", back_populates="camera", cascade="all, delete-orphan")

class AlertType(str, enum.Enum):
    FIRE = "fire"
    SMOKE = "smoke"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    alert_type = Column(String(50)) # fire, smoke, etc.
    severity = Column(String(50), default="low")
    confidence_score = Column(Float)
    description = Column(String(255))
    status = Column(String(50), default="active") # active, acknowledged, resolved, false_alarm
    footage_path = Column(String(255), nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    camera = relationship("Camera", back_populates="alerts")
