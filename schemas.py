from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Admin ──────────────────────────────────────────────────────────────────────

class AdminOut(BaseModel):
    admin_id:   int
    username:   str
    full_name:  Optional[str]
    created_at: Optional[datetime]
    last_login: Optional[datetime]
 
    class Config:
        from_attributes = True
 
 
class AdminUpdateProfile(BaseModel):
    full_name: Optional[str] = None
    username:  Optional[str] = None
 
 
class AdminChangePassword(BaseModel):
    current_password: str
    new_password:     str
    confirm_password: str


# ── Users ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    farm_name: Optional[str] = None
    location: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    farm_name: Optional[str] = None
    location: Optional[str] = None


class UserOut(BaseModel):
    user_id: int
    username: str
    farm_name: Optional[str]
    location: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Scan Logs ──────────────────────────────────────────────────────────────────

class ScanLogCreate(BaseModel):
    image_path: Optional[str] = None
    leaf_mask_path: Optional[str] = None
    tier1_confidence: Optional[float] = None
    device_id: Optional[str] = None


class ScanLogOut(BaseModel):
    scan_id: int
    image_path: Optional[str]
    leaf_mask_path: Optional[str]
    tier1_confidence: Optional[float]
    timestamp: Optional[datetime]
    device_id: Optional[str]

    class Config:
        from_attributes = True


# ── Disease Detections ─────────────────────────────────────────────────────────

class DiseaseDetectionCreate(BaseModel):
    scan_id: Optional[int] = None
    anomaly_detected: bool = False
    detected_class: Optional[str] = None
    lesion_mask_path: Optional[str] = None
    tier2_confidence: Optional[float] = None
    lesion_count: Optional[int] = None
    recommendation: Optional[str] = None


class DiseaseDetectionOut(BaseModel):
    detection_id: int
    scan_id: Optional[int]
    anomaly_detected: bool
    detected_class: Optional[str]
    lesion_mask_path: Optional[str]
    tier2_confidence: Optional[float]
    lesion_count: Optional[int]
    recommendation: Optional[str]

    class Config:
        from_attributes = True


# ── Alerts ─────────────────────────────────────────────────────────────────────

class AlertCreate(BaseModel):
    detection_id: Optional[int] = None
    user_id: Optional[int] = None
    alert_message: Optional[str] = None


class AlertOut(BaseModel):
    alert_id: int
    detection_id: Optional[int]
    user_id: Optional[int]
    alert_message: Optional[str]
    alert_sent_at: Optional[datetime]
    acknowledged: bool

    class Config:
        from_attributes = True