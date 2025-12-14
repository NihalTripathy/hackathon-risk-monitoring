"""
User Preferences API endpoints - Priority 6: User Preferences & Customization
SOLID compliant user preference management
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from core.database import get_db
from core.auth_dependencies import get_current_user
from api.auth import UserResponse
from infrastructure.database.models import UserPreferencesModel

router = APIRouter()


class UserPreferencesRequest(BaseModel):
    """Request model for updating user preferences"""
    risk_threshold_high: Optional[float] = None
    risk_threshold_medium: Optional[float] = None
    risk_threshold_low: Optional[float] = None
    dashboard_layout: Optional[Dict[str, Any]] = None
    default_filters: Optional[Dict[str, Any]] = None
    default_views: Optional[Dict[str, Any]] = None
    show_p50_first: Optional[bool] = None
    show_p80_first: Optional[bool] = None
    show_anomalies_section: Optional[bool] = None
    show_resource_summary: Optional[bool] = None


class UserPreferencesResponse(BaseModel):
    """Response model for user preferences"""
    risk_threshold_high: float
    risk_threshold_medium: float
    risk_threshold_low: float
    dashboard_layout: Dict[str, Any]
    default_filters: Dict[str, Any]
    default_views: Dict[str, Any]
    show_p50_first: bool
    show_p80_first: bool
    show_anomalies_section: bool
    show_resource_summary: bool


@router.get("/user/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user preferences"""
    prefs = db.query(UserPreferencesModel).filter(
        UserPreferencesModel.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create default preferences
        prefs = UserPreferencesModel(
            user_id=current_user.id,
            risk_threshold_high=70.0,
            risk_threshold_medium=40.0,
            risk_threshold_low=0.0,
            dashboard_layout={},
            default_filters={},
            default_views={},
            show_p50_first=False,
            show_p80_first=True,
            show_anomalies_section=True,
            show_resource_summary=False
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return UserPreferencesResponse(
        risk_threshold_high=prefs.risk_threshold_high,
        risk_threshold_medium=prefs.risk_threshold_medium,
        risk_threshold_low=prefs.risk_threshold_low,
        dashboard_layout=prefs.dashboard_layout or {},
        default_filters=prefs.default_filters or {},
        default_views=prefs.default_views or {},
        show_p50_first=prefs.show_p50_first,
        show_p80_first=prefs.show_p80_first,
        show_anomalies_section=prefs.show_anomalies_section,
        show_resource_summary=prefs.show_resource_summary
    )


@router.put("/user/preferences", response_model=UserPreferencesResponse)
def update_user_preferences(
    request: UserPreferencesRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user preferences"""
    prefs = db.query(UserPreferencesModel).filter(
        UserPreferencesModel.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = UserPreferencesModel(user_id=current_user.id)
        db.add(prefs)
    
    # Update only provided fields
    if request.risk_threshold_high is not None:
        if request.risk_threshold_high < 0 or request.risk_threshold_high > 100:
            raise HTTPException(status_code=400, detail="risk_threshold_high must be between 0 and 100")
        prefs.risk_threshold_high = request.risk_threshold_high
    
    if request.risk_threshold_medium is not None:
        if request.risk_threshold_medium < 0 or request.risk_threshold_medium > 100:
            raise HTTPException(status_code=400, detail="risk_threshold_medium must be between 0 and 100")
        prefs.risk_threshold_medium = request.risk_threshold_medium
    
    if request.risk_threshold_low is not None:
        if request.risk_threshold_low < 0 or request.risk_threshold_low > 100:
            raise HTTPException(status_code=400, detail="risk_threshold_low must be between 0 and 100")
        prefs.risk_threshold_low = request.risk_threshold_low
    
    # Validate thresholds are in order
    if prefs.risk_threshold_low >= prefs.risk_threshold_medium:
        raise HTTPException(
            status_code=400,
            detail="risk_threshold_low must be less than risk_threshold_medium"
        )
    if prefs.risk_threshold_medium >= prefs.risk_threshold_high:
        raise HTTPException(
            status_code=400,
            detail="risk_threshold_medium must be less than risk_threshold_high"
        )
    
    if request.dashboard_layout is not None:
        prefs.dashboard_layout = request.dashboard_layout
    
    if request.default_filters is not None:
        prefs.default_filters = request.default_filters
    
    if request.default_views is not None:
        prefs.default_views = request.default_views
    
    if request.show_p50_first is not None:
        prefs.show_p50_first = request.show_p50_first
    
    if request.show_p80_first is not None:
        prefs.show_p80_first = request.show_p80_first
    
    if request.show_anomalies_section is not None:
        prefs.show_anomalies_section = request.show_anomalies_section
    
    if request.show_resource_summary is not None:
        prefs.show_resource_summary = request.show_resource_summary
    
    db.commit()
    db.refresh(prefs)
    
    return UserPreferencesResponse(
        risk_threshold_high=prefs.risk_threshold_high,
        risk_threshold_medium=prefs.risk_threshold_medium,
        risk_threshold_low=prefs.risk_threshold_low,
        dashboard_layout=prefs.dashboard_layout or {},
        default_filters=prefs.default_filters or {},
        default_views=prefs.default_views or {},
        show_p50_first=prefs.show_p50_first,
        show_p80_first=prefs.show_p80_first,
        show_anomalies_section=prefs.show_anomalies_section,
        show_resource_summary=prefs.show_resource_summary
    )

