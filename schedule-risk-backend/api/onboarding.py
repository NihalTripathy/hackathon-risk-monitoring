"""
Onboarding API endpoints - Priority 7: Onboarding & Guided Tours
SOLID compliant onboarding management
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from core.database import get_db
from core.auth_dependencies import get_current_user
from api.auth import UserResponse
from infrastructure.database.models import UserModel

router = APIRouter()


class OnboardingStep(BaseModel):
    """Onboarding step model"""
    id: str
    title: str
    description: str
    target_element: Optional[str] = None  # CSS selector or element ID
    position: Optional[str] = None  # top, bottom, left, right
    action: Optional[str] = None  # click, hover, etc.


class OnboardingTour(BaseModel):
    """Onboarding tour model"""
    tour_id: str
    name: str
    description: str
    steps: List[OnboardingStep]


class OnboardingStatus(BaseModel):
    """Onboarding status model"""
    completed_tours: List[str]
    current_tour: Optional[str] = None
    current_step: Optional[int] = None


# Predefined onboarding tours
ONBOARDING_TOURS = {
    "dashboard": {
        "tour_id": "dashboard",
        "name": "Dashboard Tour",
        "description": "Learn how to navigate the risk dashboard",
        "steps": [
            {
                "id": "welcome",
                "title": "Welcome to Risk Monitoring",
                "description": "This dashboard shows your project risks at a glance. High-risk activities appear at the top.",
                "target_element": None,
                "position": "center"
            },
            {
                "id": "forecast",
                "title": "Forecast Cards",
                "description": "P50 shows the most likely completion date (50% confidence). P80 shows the worst-case scenario (80% confidence).",
                "target_element": "[data-tour='forecast-cards']",
                "position": "bottom"
            },
            {
                "id": "risks",
                "title": "Top Risks",
                "description": "Activities are ranked by risk score. Click 'View Details' to see mitigation options.",
                "target_element": "[data-tour='top-risks']",
                "position": "top"
            },
            {
                "id": "anomalies",
                "title": "Anomalies",
                "description": "Zombie tasks are overdue but not started. Resource black holes are overloaded resources.",
                "target_element": "[data-tour='anomalies']",
                "position": "top"
            }
        ]
    },
    "forecast": {
        "tour_id": "forecast",
        "name": "Understanding Forecasts",
        "description": "Learn how to interpret P50 and P80 forecasts",
        "steps": [
            {
                "id": "p50",
                "title": "P50 Forecast",
                "description": "P50 (50th percentile) means there's a 50% chance the project will finish on or before this date. This is your most likely completion date.",
                "target_element": "[data-tour='p50-forecast']",
                "position": "right"
            },
            {
                "id": "p80",
                "title": "P80 Forecast",
                "description": "P80 (80th percentile) means there's an 80% chance the project will finish on or before this date. This is your worst-case scenario.",
                "target_element": "[data-tour='p80-forecast']",
                "position": "right"
            },
            {
                "id": "uncertainty",
                "title": "Understanding Uncertainty",
                "description": "The difference between P50 and P80 shows schedule uncertainty. Larger differences mean higher uncertainty.",
                "target_element": "[data-tour='forecast-chart']",
                "position": "top"
            }
        ]
    },
    "risks": {
        "tour_id": "risks",
        "name": "Understanding Risk Scores",
        "description": "Learn how risk scores are calculated and what they mean",
        "steps": [
            {
                "id": "risk-score",
                "title": "Risk Score",
                "description": "Risk scores range from 0-100. Higher scores mean higher risk of project delays.",
                "target_element": "[data-tour='risk-score']",
                "position": "right"
            },
            {
                "id": "risk-factors",
                "title": "Risk Factors",
                "description": "Risk scores consider delays, critical path status, resource overload, and other factors.",
                "target_element": "[data-tour='risk-factors']",
                "position": "bottom"
            },
            {
                "id": "mitigations",
                "title": "Mitigation Options",
                "description": "Click 'View Details' to see ranked mitigation options with quantified impact.",
                "target_element": "[data-tour='mitigations']",
                "position": "top"
            }
        ]
    }
}


@router.get("/onboarding/tours")
def list_onboarding_tours():
    """List all available onboarding tours"""
    return {
        "tours": [
            {
                "tour_id": tour["tour_id"],
                "name": tour["name"],
                "description": tour["description"],
                "step_count": len(tour["steps"])
            }
            for tour in ONBOARDING_TOURS.values()
        ]
    }


@router.get("/onboarding/tours/{tour_id}")
def get_onboarding_tour(tour_id: str):
    """Get specific onboarding tour"""
    tour = ONBOARDING_TOURS.get(tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    return OnboardingTour(**tour)


@router.get("/onboarding/status", response_model=OnboardingStatus)
def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's onboarding status"""
    from infrastructure.database.models import UserPreferencesModel
    
    # Get or create user preferences
    prefs = db.query(UserPreferencesModel).filter(
        UserPreferencesModel.user_id == current_user.id
    ).first()
    
    # Extract completed tours from preferences
    completed_tours = []
    if prefs and hasattr(prefs, 'completed_tours') and prefs.completed_tours:
        # Handle both list and JSON string formats
        if isinstance(prefs.completed_tours, list):
            completed_tours = prefs.completed_tours
        elif isinstance(prefs.completed_tours, str):
            import json
            try:
                completed_tours = json.loads(prefs.completed_tours)
            except:
                completed_tours = []
        else:
            completed_tours = prefs.completed_tours if prefs.completed_tours else []
    
    return OnboardingStatus(
        completed_tours=completed_tours,
        current_tour=None,
        current_step=None
    )


@router.post("/onboarding/complete/{tour_id}")
def complete_onboarding_tour(
    tour_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Mark onboarding tour as completed - persists to database so it never shows again"""
    if tour_id not in ONBOARDING_TOURS:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    from infrastructure.database.models import UserPreferencesModel
    from sqlalchemy import func
    import json
    
    # Get or create user preferences
    prefs = db.query(UserPreferencesModel).filter(
        UserPreferencesModel.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create new preferences record
        prefs = UserPreferencesModel(user_id=current_user.id)
        db.add(prefs)
        completed_tours = []
    else:
        # Get existing completed tours
        if hasattr(prefs, 'completed_tours') and prefs.completed_tours:
            if isinstance(prefs.completed_tours, list):
                completed_tours = list(prefs.completed_tours)
            elif isinstance(prefs.completed_tours, str):
                try:
                    completed_tours = json.loads(prefs.completed_tours)
                except:
                    completed_tours = []
            else:
                completed_tours = list(prefs.completed_tours) if prefs.completed_tours else []
        else:
            completed_tours = []
    
    # Add tour_id if not already in list
    if tour_id not in completed_tours:
        completed_tours.append(tour_id)
        # Update the completed_tours field
        prefs.completed_tours = completed_tours
        prefs.updated_at = func.now()
        db.commit()
    
    return {
        "message": f"Tour '{tour_id}' marked as completed",
        "tour_id": tour_id,
        "completed_tours": completed_tours
    }

