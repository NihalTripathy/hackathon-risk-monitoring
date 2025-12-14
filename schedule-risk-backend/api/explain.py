"""
Explanation and interpretability API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import os
from core.llm_adapter import explain, explain_with_llm
from core.features import compute_features
from core.risk_model import RuleBasedRiskModel
from core.database import get_db
from core.db_service import get_activities, log_event_db
from core.project_auth import verify_project_ownership
from core.auth_dependencies import get_current_user
from api.auth import UserResponse

router = APIRouter()


@router.get("/projects/{project_id}/explain/{activity_id}")
async def explain_activity_risk(
    project_id: str, 
    activity_id: str, 
    use_llm: bool = False, 
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get explanation for why an activity has a certain risk score - requires authentication and ownership"""
    verify_project_ownership(db, project_id, current_user)
    
    activities = get_activities(db, project_id)
    activity = None
    
    for act in activities:
        if act.activity_id == activity_id:
            activity = act
            break
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Compute features and risk score (pass activities to build twin if needed)
    features = compute_features(activity, project_id, activities=activities)
    model = RuleBasedRiskModel()
    risk_score = model.predict(features)
    
    # Get criticality index from forecast if available
    criticality_index = None
    try:
        from core.digital_twin import get_or_build_twin
        from core.mc_forecaster import monte_carlo_forecast
        twin = get_or_build_twin(project_id, activities)
        forecast = monte_carlo_forecast(twin, num_simulations=1000)  # Quick forecast for CI
        criticality_indices = forecast.get("criticality_indices", {})
        criticality_index = criticality_indices.get(activity_id)
    except:
        pass
    
    # Check for anomalies
    anomalies = []
    try:
        from core.anomalies import detect_zombie_tasks, detect_black_holes
        from core.models import PROJECTS
        PROJECTS[project_id] = activities
        zombies = detect_zombie_tasks(project_id)
        black_holes = detect_black_holes(project_id)
        if any(z["activity_id"] == activity_id for z in zombies):
            anomalies.append("zombie_task")
        # Check if activity's resource is in black holes
        if activity.resource_id:
            for bh in black_holes:
                if activity.resource_id == bh["resource_id"] and activity_id in bh.get("activities", []):
                    anomalies.append("resource_black_hole")
                    break
    except:
        pass
    
    # Generate explanation
    if use_llm:
        explanation = await explain_with_llm(activity, features, risk_score, 
                                             criticality_index=criticality_index,
                                             anomalies=anomalies if anomalies else None)
    else:
        explanation = explain(activity, features, risk_score, use_llm=False)
    
    # Log the explanation event to database
    log_event_db(
        db,
        project_id,
        "explanation",
        {
            "activity_id": activity_id,
            "use_llm": use_llm
        }
    )
    
    return {
        "activity_id": activity_id,
        "activity_name": activity.name,
        **explanation
    }


@router.get("/llm/status")
async def check_llm_status():
    """Check if LLM (Hugging Face) is configured and available"""
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    hf_model = os.getenv("HUGGINGFACE_MODEL", "Qwen/Qwen2.5-7B-Instruct:together")
    
    status = {
        "configured": hf_api_key is not None and hf_api_key != "",
        "api_key_set": bool(hf_api_key),
        "model": hf_model,
        "api_key_preview": f"{hf_api_key[:10]}..." if hf_api_key else None,
        "message": ""
    }
    
    if not status["configured"]:
        status["message"] = "HUGGINGFACE_API_KEY is not set. Get your free API key at https://huggingface.co/settings/tokens"
        status["setup_instructions"] = {
            "step1": "Go to https://huggingface.co/ and sign up/login",
            "step2": "Navigate to Settings → Access Tokens",
            "step3": "Create a new token (read access is sufficient)",
            "step4": "Set the environment variable: $env:HUGGINGFACE_API_KEY = 'your_token_here'",
            "step5": "Restart your backend server"
        }
    else:
        status["message"] = "LLM is configured and ready to use"
        status["pricing_info"] = {
            "free_tier": "Hugging Face Inference API offers a free tier with limited requests",
            "pricing_url": "https://huggingface.co/pricing",
            "note": "For production use, check current pricing at the URL above"
        }
    
    return status

