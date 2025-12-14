"""
Simulation API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from core.mitigation import simulate_mitigation, generate_and_rank_mitigations
from core.database import get_db
from core.db_service import get_activities, log_event_db
from core.project_auth import verify_project_ownership
from core.auth_dependencies import get_current_user
from api.auth import UserResponse

router = APIRouter()


class MitigationRequest(BaseModel):
    activity_id: str
    new_duration: Optional[float] = None
    reduce_risk: bool = False
    new_fte: Optional[float] = None
    new_cost: Optional[float] = None


@router.post("/projects/{project_id}/simulate")
def simulate_mitigation_action(
    project_id: str, 
    request: MitigationRequest, 
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Simulate the effect of a mitigation action on project completion - requires authentication and ownership"""
    verify_project_ownership(db, project_id, current_user)
    
    if not request.new_duration and not request.reduce_risk and not request.new_fte and not request.new_cost:
        raise HTTPException(
            status_code=400, 
            detail="Either new_duration, reduce_risk, new_fte, or new_cost must be specified"
        )
    
    # Validate parameters
    if request.new_duration is not None and request.new_duration <= 0:
        raise HTTPException(
            status_code=400,
            detail="new_duration must be greater than 0"
        )
    if request.new_fte is not None and request.new_fte < 0:
        raise HTTPException(
            status_code=400,
            detail="new_fte must be greater than or equal to 0"
        )
    if request.new_cost is not None and request.new_cost < 0:
        raise HTTPException(
            status_code=400,
            detail="new_cost must be greater than or equal to 0"
        )
    
    # Get activities from database
    activities = get_activities(db, project_id)
    result = simulate_mitigation(
        project_id,
        request.activity_id,
        request.new_duration,
        request.reduce_risk,
        request.new_fte,
        request.new_cost,
        activities=activities
    )
    
    # Also calculate new risk score after mitigation
    from core.risk_pipeline import compute_project_risks
    from core.features import compute_features
    from core.risk_model import RuleBasedRiskModel
    
    # Find the activity
    activity = None
    for act in activities:
        if act.activity_id == request.activity_id:
            activity = act
            break
    
    original_risk_score = None
    new_risk_score = None
    
    if activity:
        # Calculate original risk score
        features = compute_features(activity, project_id, activities=activities)
        model = RuleBasedRiskModel()
        original_risk_score = model.predict(features)
        
        # Create modified activity for new risk score
        from core.models import Activity as ActivityModel
        activity_dict = activity.__dict__.copy() if hasattr(activity, '__dict__') else {}
        
        if request.new_duration:
            activity_dict["planned_duration"] = request.new_duration
            activity_dict["baseline_duration"] = request.new_duration
        
        if request.reduce_risk:
            activity_dict["risk_probability"] = (activity.risk_probability or 0) * 0.5
            activity_dict["risk_delay_impact_days"] = (activity.risk_delay_impact_days or 0) * 0.5
        
        if request.new_fte is not None:
            activity_dict["fte_allocation"] = request.new_fte
        
        if request.new_cost is not None:
            activity_dict["planned_cost"] = request.new_cost
        
        # Recalculate features and risk score
        modified_activity = ActivityModel(**activity_dict)
        new_features = compute_features(modified_activity, project_id, activities=activities)
        new_risk_score = model.predict(new_features)
    
    # Enhance result with risk score changes
    result["risk_score_impact"] = {
        "original_risk_score": round(original_risk_score, 1) if original_risk_score else None,
        "new_risk_score": round(new_risk_score, 1) if new_risk_score else None,
        "risk_score_improvement": round((original_risk_score - new_risk_score), 1) if (original_risk_score and new_risk_score) else None
    }
    
    # Log the simulation event to database
    if request.new_duration:
        mitigation_type = "duration_reduction"
    elif request.new_fte:
        mitigation_type = "fte_addition"
    elif request.new_cost:
        mitigation_type = "cost_adjustment"
    else:
        mitigation_type = "risk_reduction"
    log_event_db(
        db,
        project_id,
        "simulation",
        {
            "activity_id": request.activity_id,
            "mitigation_type": mitigation_type,
            "improvement": result.get("improvement", {}),
            "risk_score_improvement": result["risk_score_impact"].get("risk_score_improvement")
        }
    )
    
    return result


@router.get("/projects/{project_id}/mitigations/{activity_id}")
def get_mitigation_options(
    project_id: str,
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get ranked mitigation options for an activity - requires authentication and ownership"""
    verify_project_ownership(db, project_id, current_user)
    
    # Get activities from database
    activities = get_activities(db, project_id)
    if not activities:
        raise HTTPException(status_code=404, detail="Project not found or has no activities")
    
    try:
        result = generate_and_rank_mitigations(project_id, activity_id, activities=activities)
        
        # Log the mitigation generation event
        log_event_db(
            db,
            project_id,
            "mitigation_generation",
            {
                "activity_id": activity_id,
                "options_generated": result.get("total_options", 0)
            }
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

