from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re

# Philippine mobile numbers: 09XXXXXXXXX, +639XXXXXXXXX or 639XXXXXXXXX
_PH_MOBILE = re.compile(r"^(?:\+?63|0)9\d{9}$")


def normalize_ph_mobile(value: str) -> str:
    """Accepts common ways of typing a PH mobile number and stores it as 09XXXXXXXXX."""
    cleaned = re.sub(r"[\s\-()]", "", value or "")
    if not _PH_MOBILE.match(cleaned):
        raise ValueError("Enter a valid mobile number, e.g. 09171234567")
    return "0" + cleaned[-10:]


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


# ── Users (Farmers) ────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Farmer registration: name, username, mobile number and password."""
    full_name:    str
    username:     str
    phone_number: str
    password:     str

    @field_validator("full_name", "username")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field cannot be empty")
        return v

    @field_validator("username")
    @classmethod
    def _username_len(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("phone_number")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_ph_mobile(v)

    @field_validator("password")
    @classmethod
    def _password_len(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    """Admin edits a farmer (password is changed by the farmer, not here)."""
    full_name:    Optional[str] = None
    username:     Optional[str] = None
    phone_number: Optional[str] = None

    @field_validator("full_name", "username")
    @classmethod
    def _not_blank(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("This field cannot be empty")
        return v

    @field_validator("username")
    @classmethod
    def _username_len(cls, v):
        if v is not None and len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("phone_number")
    @classmethod
    def _phone(cls, v):
        return None if v is None else normalize_ph_mobile(v)


class UserSelfUpdate(BaseModel):
    """A farmer edits their own profile. Username stays fixed because their login token is tied to it."""
    full_name:    Optional[str] = None
    phone_number: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def _name(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be empty")
        return v

    @field_validator("phone_number")
    @classmethod
    def _phone(cls, v):
        return None if v is None else normalize_ph_mobile(v)


class UserChangePassword(BaseModel):
    current_password: str
    new_password:     str
    confirm_password: str


class UserOut(BaseModel):
    user_id:      int
    full_name:    str
    username:     str
    phone_number: Optional[str]
    created_at:   Optional[datetime]

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserLoginResponse(BaseModel):
    """Returned after successful user login — includes tokens + full user data."""
    access_token:  str
    refresh_token: str
    token_type:    str
    user:          UserOut


class UserRefreshRequest(BaseModel):
    refresh_token: str


class UserRefreshResponse(BaseModel):
    access_token: str
    token_type:   str


# ── Scan Logs ──────────────────────────────────────────────────────────────────

class ScanLogCreate(BaseModel):
    image_path:       Optional[str]   = None
    leaf_mask_path:   Optional[str]   = None
    tier1_confidence: Optional[float] = None
    device_id:        Optional[str]   = None


class ScanLogOut(BaseModel):
    scan_id:          int
    image_path:       Optional[str]
    leaf_mask_path:   Optional[str]
    tier1_confidence: Optional[float]
    timestamp:        Optional[datetime]
    device_id:        Optional[str]

    class Config:
        from_attributes = True


# ── Disease Detections ─────────────────────────────────────────────────────────

class DiseaseDetectionCreate(BaseModel):
    scan_id:          Optional[int]   = None
    anomaly_detected: bool            = False
    detected_class:   Optional[str]   = None
    lesion_mask_path: Optional[str]   = None
    tier2_confidence: Optional[float] = None
    lesion_count:     Optional[int]   = None
    recommendation:   Optional[str]   = None


class DiseaseDetectionOut(BaseModel):
    detection_id:     int
    scan_id:          Optional[int]
    anomaly_detected: bool
    detected_class:   Optional[str]
    lesion_mask_path: Optional[str]
    tier2_confidence: Optional[float]
    lesion_count:     Optional[int]
    recommendation:   Optional[str]

    class Config:
        from_attributes = True


# ── Alerts ─────────────────────────────────────────────────────────────────────

class AlertCreate(BaseModel):
    detection_id:  Optional[int] = None
    user_id:       Optional[int] = None
    alert_message: Optional[str] = None


class AlertOut(BaseModel):
    alert_id:      int
    detection_id:  Optional[int]
    user_id:       Optional[int]
    alert_message: Optional[str]
    alert_sent_at: Optional[datetime]
    acknowledged:  bool

    class Config:
        from_attributes = True


# ── Settings ───────────────────────────────────────────────────────────────────

class SettingsOut(BaseModel):
    auto_notify:             bool
    alert_threshold:         int
    alert_cooldown_hours:    int
    farmers_can_acknowledge: bool


class SettingsUpdate(BaseModel):
    auto_notify:             Optional[bool] = None
    alert_threshold:         Optional[int]  = Field(default=None, ge=50, le=100)
    alert_cooldown_hours:    Optional[int]  = Field(default=None, ge=0, le=168)
    farmers_can_acknowledge: Optional[bool] = None