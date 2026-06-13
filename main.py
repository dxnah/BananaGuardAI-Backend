from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import Optional
from auth import verify_user_refresh_token, get_current_user,verify_password, hash_password, create_access_token, create_refresh_token, verify_refresh_token, get_current_admin
from pydantic import BaseModel
from datetime import datetime as dt
 
import os

from database import Base, engine, get_db
import models
import schemas

load_dotenv()

# ── Auto-create all tables on startup ─────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="BananaGuardAI API", version="1.0.0")

# ── CORS — allow the React dev server ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

class RefreshRequest(BaseModel):
    refresh_token: str

@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    admin = db.query(models.Admin).filter(
        models.Admin.username == form_data.username
    ).first()
 
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
 
    # Record last login time
    admin.last_login = dt.utcnow()
    db.commit()
 
    return {
        "access_token":  create_access_token(data={"sub": admin.username}),
        "refresh_token": create_refresh_token(data={"sub": admin.username}),
        "token_type":    "bearer",
    }
 
 
# ── Update profile (full_name, username) ───────────────────────────────────────
@app.put("/auth/profile", response_model=schemas.AdminOut)
def update_profile(
    payload: schemas.AdminUpdateProfile,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    admin = db.query(models.Admin).filter(
        models.Admin.admin_id == current_admin.admin_id
    ).first()
 
    if payload.username and payload.username != admin.username:
        existing = db.query(models.Admin).filter(
            models.Admin.username == payload.username
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        admin.username = payload.username
 
    if payload.full_name is not None:
        admin.full_name = payload.full_name
 
    db.commit()
    db.refresh(admin)
    return admin
 
 
# ── Change password ────────────────────────────────────────────────────────────
@app.put("/auth/change-password")
def change_password(
    payload: schemas.AdminChangePassword,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    admin = db.query(models.Admin).filter(
        models.Admin.admin_id == current_admin.admin_id
    ).first()
 
    if not verify_password(payload.current_password, admin.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
 
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
 
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
 
    admin.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
 
 
@app.post("/auth/refresh")
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    """
    Call this when the access token expires.
    Send the refresh token, get a new access token back.
    """
    admin = verify_refresh_token(body.refresh_token, db)
    return {
        "access_token": create_access_token(data={"sub": admin.username}),
        "token_type":   "bearer",
    }
 
 
@app.get("/auth/me", response_model=schemas.AdminOut)
def get_me(current_admin=Depends(get_current_admin)):
    return current_admin

# ══════════════════════════════════════════════════════════════════════════════
# USERS (Farmers)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/users/login", response_model=schemas.UserLoginResponse)
def user_login(payload: schemas.UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == payload.username
    ).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return {
        "access_token":  create_access_token(data={"sub": user.username, "role": "user"}),
        "refresh_token": create_refresh_token(data={"sub": user.username, "role": "user"}),
        "token_type":    "bearer",
        "user":          user,
    }
 
 
@app.post("/users/refresh", response_model=schemas.UserRefreshResponse)
def user_refresh_token(body: schemas.UserRefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid user refresh token for a new access token."""
    user = verify_user_refresh_token(body.refresh_token, db)
    return {
        "access_token": create_access_token(data={"sub": user.username, "role": "user"}),
        "token_type":   "bearer",
    }
 
 
@app.get("/users/me", response_model=schemas.UserOut)
def get_current_user_me(current_user=Depends(get_current_user)):
    """Get the currently logged-in user from their access token."""
    return current_user
 
 
@app.get("/users", response_model=list[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
 
 
@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
 
 
@app.post("/users", response_model=schemas.UserOut, status_code=201)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if payload.email:
        if db.query(models.User).filter(models.User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
    if payload.phone_number:
        if db.query(models.User).filter(models.User.phone_number == payload.phone_number).first():
            raise HTTPException(status_code=400, detail="Phone number already registered")
 
    user = models.User(
        full_name       = payload.full_name,
        username        = payload.username,
        hashed_password = hash_password(payload.password),
        email           = payload.email,
        phone_number    = payload.phone_number,
        farm_name       = payload.farm_name,
        location        = payload.location,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
 
 
@app.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
 
    if payload.username and payload.username != user.username:
        if db.query(models.User).filter(models.User.username == payload.username).first():
            raise HTTPException(status_code=400, detail="Username already taken")
    if payload.email and payload.email != user.email:
        if db.query(models.User).filter(models.User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
    if payload.phone_number and payload.phone_number != user.phone_number:
        if db.query(models.User).filter(models.User.phone_number == payload.phone_number).first():
            raise HTTPException(status_code=400, detail="Phone number already registered")
 
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
 
    db.commit()
    db.refresh(user)
    return user
 
 
@app.put("/users/{user_id}/change-password")
def change_user_password(
    user_id: int,
    payload: schemas.UserChangePassword,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
 
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
 
 
@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()

# ══════════════════════════════════════════════════════════════════════════════
# SCAN LOGS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/scans", response_model=list[schemas.ScanLogOut])
def get_scans(db: Session = Depends(get_db)):
    return db.query(models.ScanLog).order_by(models.ScanLog.timestamp.desc()).all()


@app.get("/scans/{scan_id}", response_model=schemas.ScanLogOut)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(models.ScanLog).filter(models.ScanLog.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.post("/scans", response_model=schemas.ScanLogOut, status_code=201)
def create_scan(payload: schemas.ScanLogCreate, db: Session = Depends(get_db)):
    scan = models.ScanLog(**payload.model_dump())
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


# ══════════════════════════════════════════════════════════════════════════════
# DISEASE DETECTIONS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/detections", response_model=list[schemas.DiseaseDetectionOut])
def get_detections(
    anomaly_only: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.DiseaseDetection)
    if anomaly_only is not None:
        query = query.filter(models.DiseaseDetection.anomaly_detected == anomaly_only)
    return query.order_by(models.DiseaseDetection.detection_id.desc()).all()


@app.get("/detections/{detection_id}", response_model=schemas.DiseaseDetectionOut)
def get_detection(detection_id: int, db: Session = Depends(get_db)):
    det = db.query(models.DiseaseDetection).filter(
        models.DiseaseDetection.detection_id == detection_id
    ).first()
    if not det:
        raise HTTPException(status_code=404, detail="Detection not found")
    return det


@app.post("/detections", response_model=schemas.DiseaseDetectionOut, status_code=201)
def create_detection(payload: schemas.DiseaseDetectionCreate, db: Session = Depends(get_db)):
    detection = models.DiseaseDetection(**payload.model_dump())
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


# ══════════════════════════════════════════════════════════════════════════════
# ALERTS (Notifications)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/alerts", response_model=list[schemas.AlertOut])
def get_alerts(
    acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Alert)
    if acknowledged is not None:
        query = query.filter(models.Alert.acknowledged == acknowledged)
    return query.order_by(models.Alert.alert_sent_at.desc()).all()


@app.get("/alerts/{alert_id}", response_model=schemas.AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(models.Alert).filter(models.Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.post("/alerts", response_model=schemas.AlertOut, status_code=201)
def create_alert(payload: schemas.AlertCreate, db: Session = Depends(get_db)):
    alert = models.Alert(**payload.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@app.patch("/alerts/{alert_id}/acknowledge", response_model=schemas.AlertOut)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(models.Alert).filter(models.Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    from sqlalchemy import func as sa_func
    from datetime import date

    today = date.today()

    scans_today = db.query(models.ScanLog).filter(
        sa_func.date(models.ScanLog.timestamp) == today
    ).count()

    active_detections = db.query(models.DiseaseDetection).filter(
        models.DiseaseDetection.anomaly_detected == True
    ).count()

    farmers_notified = db.query(models.Alert).filter(
        models.Alert.acknowledged == False
    ).count()

    total_users = db.query(models.User).count()

    latest_detection = (
        db.query(models.DiseaseDetection)
        .order_by(models.DiseaseDetection.detection_id.desc())
        .first()
    )

    return {
        "scans_today": scans_today,
        "active_detections": active_detections,
        "farmers_notified": farmers_notified,
        "total_farmers": total_users,
        "latest_detection": {
            "detection_id": latest_detection.detection_id,
            "detected_class": latest_detection.detected_class,
            "tier2_confidence": latest_detection.tier2_confidence,
            "recommendation": latest_detection.recommendation,
        } if latest_detection else None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)