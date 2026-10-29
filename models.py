from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# ── Admins ─────────────────────────────────────────────────────────────────────

class Admin(Base):
    __tablename__ = "admins"

    admin_id        = Column(Integer, primary_key=True, index=True)
    username        = Column(String(100), unique=True, nullable=False)
    full_name       = Column(String(200), nullable=True)
    hashed_password = Column(String(200), nullable=False)
    created_at      = Column(DateTime, default=func.now(), nullable=True)
    last_login      = Column(DateTime, nullable=True)


# ── Users (Farmers) ────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    user_id         = Column(Integer, primary_key=True, index=True)
    full_name       = Column(String(200), nullable=False)
    username        = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    phone_number    = Column(String(30),  unique=True, nullable=True) 
    created_at      = Column(DateTime, default=func.now(), nullable=True)

    # relationships
    alerts = relationship("Alert", back_populates="user")


# ── Scan Logs ──────────────────────────────────────────────────────────────────
class ScanLog(Base):
    __tablename__ = "scan_logs"

    scan_id          = Column(Integer, primary_key=True, index=True)
    image_path       = Column(String(500), nullable=True)
    leaf_mask_path   = Column(String(500), nullable=True)
    tier1_confidence = Column(Float, nullable=True)
    timestamp        = Column(DateTime, default=func.now(), nullable=True)
    device_id        = Column(String(200), nullable=True)

    detections = relationship("DiseaseDetection", back_populates="scan")


# ── Disease Detections ─────────────────────────────────────────────────────────
class DiseaseDetection(Base):
    __tablename__ = "disease_detections"

    detection_id     = Column(Integer, primary_key=True, index=True)
    scan_id          = Column(Integer, ForeignKey("scan_logs.scan_id"), nullable=True)
    anomaly_detected = Column(Boolean, default=False)
    detected_class   = Column(String(200), nullable=True)
    lesion_mask_path = Column(String(500), nullable=True)
    tier2_confidence = Column(Float, nullable=True)
    lesion_count     = Column(Integer, nullable=True)
    recommendation   = Column(Text, nullable=True)

    scan   = relationship("ScanLog", back_populates="detections")
    alerts = relationship("Alert", back_populates="detection")


# ── Alerts ─────────────────────────────────────────────────────────────────────
class Alert(Base):
    __tablename__ = "alerts"

    alert_id      = Column(Integer, primary_key=True, index=True)
    detection_id  = Column(Integer, ForeignKey("disease_detections.detection_id"), nullable=True)
    user_id       = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    alert_message = Column(Text, nullable=True)
    alert_sent_at = Column(DateTime, default=func.now(), nullable=True)
    acknowledged  = Column(Boolean, default=False)

    detection = relationship("DiseaseDetection", back_populates="alerts")
    user      = relationship("User", back_populates="alerts")


# ── Training Logs ──────────────────────────────────────────────────────────────
class TrainingLog(Base):
    __tablename__ = "training_logs"

    log_id     = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(200), nullable=True)
    epoch      = Column(Integer, nullable=True)
    train_loss = Column(Float, nullable=True)
    val_loss   = Column(Float, nullable=True)
    mAP50      = Column(Float, nullable=True)


# ── App Settings (simple key/value) ────────────────────────────────────────────
class AppSetting(Base):
    __tablename__ = "app_settings"

    key   = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=False)   # saved as JSON text