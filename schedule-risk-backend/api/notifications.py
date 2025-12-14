"""
Notification API endpoints - Priority 1: Email Notifications
SOLID compliant, extensible for future notification channels
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from core.database import get_db
from core.auth_dependencies import get_current_user
from core.notification_service import get_notification_service, NotificationPriority, NotificationChannel
from api.auth import UserResponse
from infrastructure.database.models import NotificationPreferencesModel, UserModel
from sqlalchemy import and_

router = APIRouter()


class NotificationPreferencesRequest(BaseModel):
    """Request model for updating notification preferences"""
    email_enabled: Optional[bool] = None
    email_risk_alerts: Optional[bool] = None
    email_daily_digest: Optional[bool] = None
    email_weekly_summary: Optional[bool] = None
    risk_alert_threshold: Optional[float] = None
    risk_digest_threshold: Optional[float] = None
    digest_frequency: Optional[str] = None  # daily, weekly, never
    project_preferences: Optional[Dict[str, Any]] = None


class NotificationPreferencesResponse(BaseModel):
    """Response model for notification preferences"""
    email_enabled: bool
    email_risk_alerts: bool
    email_daily_digest: bool
    email_weekly_summary: bool
    risk_alert_threshold: float
    risk_digest_threshold: float
    digest_frequency: str
    project_preferences: Dict[str, Any]


@router.get("/notifications/preferences", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's notification preferences"""
    prefs = db.query(NotificationPreferencesModel).filter(
        NotificationPreferencesModel.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create default preferences
        prefs = NotificationPreferencesModel(
            user_id=current_user.id,
            email_enabled=True,
            email_risk_alerts=True,
            email_daily_digest=False,
            email_weekly_summary=False,
            risk_alert_threshold=70.0,
            risk_digest_threshold=50.0,
            digest_frequency="daily"
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return NotificationPreferencesResponse(
        email_enabled=prefs.email_enabled,
        email_risk_alerts=prefs.email_risk_alerts,
        email_daily_digest=prefs.email_daily_digest,
        email_weekly_summary=prefs.email_weekly_summary,
        risk_alert_threshold=prefs.risk_alert_threshold,
        risk_digest_threshold=prefs.risk_digest_threshold,
        digest_frequency=prefs.digest_frequency,
        project_preferences=prefs.project_preferences or {}
    )


@router.put("/notifications/preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    request: NotificationPreferencesRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user's notification preferences"""
    prefs = db.query(NotificationPreferencesModel).filter(
        NotificationPreferencesModel.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = NotificationPreferencesModel(user_id=current_user.id)
        db.add(prefs)
    
    # Update only provided fields
    if request.email_enabled is not None:
        prefs.email_enabled = request.email_enabled
    if request.email_risk_alerts is not None:
        prefs.email_risk_alerts = request.email_risk_alerts
    if request.email_daily_digest is not None:
        prefs.email_daily_digest = request.email_daily_digest
    if request.email_weekly_summary is not None:
        prefs.email_weekly_summary = request.email_weekly_summary
    if request.risk_alert_threshold is not None:
        prefs.risk_alert_threshold = request.risk_alert_threshold
    if request.risk_digest_threshold is not None:
        prefs.risk_digest_threshold = request.risk_digest_threshold
    if request.digest_frequency is not None:
        if request.digest_frequency not in ["daily", "weekly", "never"]:
            raise HTTPException(status_code=400, detail="digest_frequency must be 'daily', 'weekly', or 'never'")
        prefs.digest_frequency = request.digest_frequency
    if request.project_preferences is not None:
        prefs.project_preferences = request.project_preferences
    
    db.commit()
    db.refresh(prefs)
    
    return NotificationPreferencesResponse(
        email_enabled=prefs.email_enabled,
        email_risk_alerts=prefs.email_risk_alerts,
        email_daily_digest=prefs.email_daily_digest,
        email_weekly_summary=prefs.email_weekly_summary,
        risk_alert_threshold=prefs.risk_alert_threshold,
        risk_digest_threshold=prefs.risk_digest_threshold,
        digest_frequency=prefs.digest_frequency,
        project_preferences=prefs.project_preferences or {}
    )


@router.post("/notifications/test")
def test_notification(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Send a test notification to verify email configuration"""
    user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    notification_service = get_notification_service()
    
    # Send test email
    content = {
        "title": "Test Notification",
        "body": "This is a test notification from Schedule Risk Monitoring System. If you received this, your email configuration is working correctly.",
        "action_url": "http://localhost:3000",
        "unsubscribe_url": "http://localhost:3000/settings/notifications"
    }
    
    success = notification_service.send_notification(
        channel=NotificationChannel.EMAIL,
        recipient=user.email,
        subject="Test Notification - Schedule Risk Monitoring",
        content=content,
        priority=NotificationPriority.MEDIUM
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send test notification. Check SMTP configuration.")
    
    return {"message": "Test notification sent successfully", "email": user.email}


def check_and_send_risk_alert(
    db: Session,
    user_id: int,
    project_id: str,
    activity_id: str,
    activity_name: str,
    risk_score: float,
    explanation: str,
    risk_details: Dict[str, Any],
    mitigation_options: List[Dict[str, Any]],
    base_url: str = "http://localhost:3000"
):
    """Check user preferences and send risk alert if enabled (called from risk pipeline)"""
    # Get user preferences
    prefs = db.query(NotificationPreferencesModel).filter(
        NotificationPreferencesModel.user_id == user_id
    ).first()
    
    if not prefs or not prefs.email_enabled or not prefs.email_risk_alerts:
        return False
    
    # Check risk threshold
    if risk_score < prefs.risk_alert_threshold:
        return False
    
    # Check project-specific preferences
    project_prefs = prefs.project_preferences.get(project_id, {})
    if project_prefs.get("enabled", True) is False:
        return False
    
    project_threshold = project_prefs.get("threshold", prefs.risk_alert_threshold)
    if risk_score < project_threshold:
        return False
    
    # Get user email
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        return False
    
    # Send notification
    notification_service = get_notification_service()
    return notification_service.send_risk_alert(
        user_email=user.email,
        project_id=project_id,
        activity_id=activity_id,
        activity_name=activity_name,
        risk_score=risk_score,
        explanation=explanation,
        risk_details=risk_details,
        mitigation_options=mitigation_options,
        base_url=base_url
    )


async def check_and_send_risk_alert_async(
    user_id: int,
    project_id: str,
    activity_id: str,
    activity_name: str,
    risk_score: float,
    explanation: str,
    risk_details: Dict[str, Any],
    mitigation_options: List[Dict[str, Any]],
    base_url: str = "http://localhost:3000"
):
    """Async version for background tasks - creates its own DB session"""
    from core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get user preferences
        prefs = db.query(NotificationPreferencesModel).filter(
            NotificationPreferencesModel.user_id == user_id
        ).first()
        
        if not prefs or not prefs.email_enabled or not prefs.email_risk_alerts:
            return False
        
        # Check risk threshold
        if risk_score < prefs.risk_alert_threshold:
            return False
        
        # Check project-specific preferences
        project_prefs = prefs.project_preferences.get(project_id, {})
        if project_prefs.get("enabled", True) is False:
            return False
        
        project_threshold = project_prefs.get("threshold", prefs.risk_alert_threshold)
        if risk_score < project_threshold:
            return False
        
        # Get user email
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return False
        
        # Send notification
        notification_service = get_notification_service()
        try:
            success = notification_service.send_risk_alert(
                user_email=user.email,
                project_id=project_id,
                activity_id=activity_id,
                activity_name=activity_name,
                risk_score=risk_score,
                explanation=explanation,
                risk_details=risk_details,
                mitigation_options=mitigation_options,
                base_url=base_url
            )
            
            # Update notification status in preferences
            if success:
                prefs.last_email_sent = func.now()
                prefs.email_error_count = 0
                prefs.email_error_message = None
            else:
                prefs.last_email_error = func.now()
                prefs.email_error_count = (prefs.email_error_count or 0) + 1
                prefs.email_error_message = "Failed to send email (check SMTP configuration)"
            
            db.commit()
        except Exception as e:
            # Log failure and update status
            error_msg = str(e)[:500]  # Limit error message length
            prefs.last_email_error = func.now()
            prefs.email_error_count = (prefs.email_error_count or 0) + 1
            prefs.email_error_message = error_msg
            db.commit()
            print(f"[Notification] Error sending email to {user.email}: {e}")
            success = False
        
        return success
    except Exception as e:
        print(f"[Notification] Error in async notification: {e}")
        return False
    finally:
        db.close()

