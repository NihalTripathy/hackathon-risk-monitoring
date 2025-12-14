"""
Risk analysis API endpoints
"""

import time
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from core.risk_pipeline import compute_project_risks
from core.anomalies import detect_anomalies
from core.database import get_db
from core.db_service import log_event_db, get_activities
from core.project_auth import verify_project_ownership
from core.auth_dependencies import get_current_user
from api.auth import UserResponse
from core.models import PROJECTS

router = APIRouter()


@router.get("/projects/{project_id}/risks/top")
def get_risks(
    project_id: str, 
    limit: int = 10,
    include_explanations: bool = True,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    force_recompute: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Get top risks for a project with explanations.
    Returns format: "Activity A-142 at high risk (score 78): 9-day delay + critical path + low float."
    
    Uses cache if available to provide instant responses. Set force_recompute=true to bypass cache.
    """
    start_time = time.time()
    
    verify_project_ownership(db, project_id, current_user)
    auth_time = time.time()
    
    # Get activities once and reuse (avoid multiple DB queries)
    activities = get_activities(db, project_id)
    activity_count = len(activities) if activities else 0
    db_time = time.time()
    
    # Always use today's date (date selection feature removed)
    reference_date = None
    
    # Check cache first (unless force_recompute is True)
    # Note: Cache key should include reference_date, but for backward compatibility,
    # we'll use existing cache if reference_date is None (today mode)
    cached_risks_data = None
    if not force_recompute and reference_date is None:
        from core.cache_service import get_risks_cache
        cached_risks_data = get_risks_cache(db, project_id, activity_count)
    
    if cached_risks_data:
        # Use cached risks - they're already enhanced with explanations
        total_risks = cached_risks_data.get("total_risks", 0)
        cached_top_risks = cached_risks_data.get("top_risks", [])
        
        # Cached risks are already in the enhanced format (with explanations, risk_level, etc.)
        # Just return them directly, limiting to requested limit
        enhanced_risks = cached_top_risks[:limit]
        
        cache_time = time.time()
        total_time = cache_time - start_time
        print(f"[CACHE] Risks served from cache in {total_time:.3f}s")
        
        return {
            "total_risks": total_risks,
            "top_risks": enhanced_risks
        }
    
    # Cache miss or force recompute - compute risks with reference_date
    risks = compute_project_risks(project_id, db=db, activities=activities, reference_date=reference_date)
    risks_time = time.time()
    
    top_risks = risks[:limit]
    
    # Enhance risks with explanations
    enhanced_risks = _enhance_risks_with_explanations(top_risks, activities, include_explanations)
    
    # Save to cache for future requests (save all risks, not just top)
    from core.cache_service import save_risks_cache
    save_risks_cache(db, project_id, {
        "total_risks": len(risks),
        "top_risks": enhanced_risks  # Save enhanced risks for faster retrieval
    }, activity_count)
    cache_save_time = time.time()
    
    # Log the risk scan event to database
    top_risk_score = enhanced_risks[0]["risk_score"] if enhanced_risks else None
    log_event_db(
        db,
        project_id,
        "risk_scan",
        {
            "risk_count": len(risks),
            "top_risk_score": top_risk_score,
            "top_risks_returned": len(enhanced_risks),
            "from_cache": False
        }
    )
    
    # Priority 1: Send email notifications for high-risk activities (non-blocking)
    # Use background tasks to avoid blocking the response
    try:
        from api.notifications import check_and_send_risk_alert_async
        from api.webhooks import trigger_webhooks_for_risk_alert
        
        # Schedule notifications in background (non-blocking)
        for risk in enhanced_risks[:5]:  # Top 5 only
            if risk["risk_score"] >= 70:  # High risk threshold
                # Schedule email notification in background (non-blocking)
                background_tasks.add_task(
                    check_and_send_risk_alert_async,
                    user_id=current_user.id,
                    project_id=project_id,
                    activity_id=risk["activity_id"],
                    activity_name=risk["name"],
                    risk_score=risk["risk_score"],
                    explanation=risk.get("explanation", ""),
                    risk_details=risk.get("key_metrics", {}),
                    mitigation_options=[]  # Can be populated from mitigation endpoint
                )
                
                # Schedule webhooks in background (non-blocking)
                event_data = {
                    "activity_id": risk["activity_id"],
                    "activity_name": risk["name"],
                    "risk_score": risk["risk_score"],
                    "explanation": risk.get("explanation", ""),
                    "project_id": project_id,
                    "action_url": f"http://localhost:3000/projects/{project_id}/activities/{risk['activity_id']}"
                }
                background_tasks.add_task(
                    trigger_webhooks_for_risk_alert,
                    user_id=current_user.id,
                    project_id=project_id,
                    event_data=event_data
                )
    except Exception as e:
        print(f"[Notification] Failed to schedule notifications: {e}")
        # Don't fail the request if notification scheduling fails
    
    total_time = time.time() - start_time
    # Log performance metrics (can be removed in production if not needed)
    if total_time > 1.0:  # Only log if slow
        print(f"[PERF] Risks endpoint timing - Total: {total_time:.2f}s, Auth: {auth_time-start_time:.2f}s, DB: {db_time-auth_time:.2f}s, Risks: {risks_time-db_time:.2f}s, Enhance: {cache_save_time-risks_time:.2f}s, Cache: {time.time()-cache_save_time:.2f}s")
    
    return {
        "total_risks": len(risks),
        "top_risks": enhanced_risks
    }


def _enhance_risks_with_explanations(top_risks, activities, include_explanations):
    """Helper function to enhance risks with explanations"""
    # Create activity lookup map for O(1) access instead of O(n) loop
    activity_map = {act.activity_id: act for act in activities}
    
    # Enhance with human-readable explanations
    from core.llm_adapter import explain_rule_based
    
    enhanced_risks = []
    for risk in top_risks:
        # Build explanation string matching problem statement format
        activity_id = risk["activity_id"]
        name = risk["name"]
        score = risk["risk_score"]
        features = risk["features"]
        risk_factors = risk.get("risk_factors", {})
        
        # Determine risk level (capitalized for frontend consistency)
        if score >= 70:
            risk_level = "High"
        elif score >= 40:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # Build explanation components
        explanation_parts = []
        
        delay_days = features.get("delay_baseline_days", 0)
        if delay_days > 0:
            explanation_parts.append(f"{int(delay_days)}-day delay (relative to baseline)")
        
        if features.get("is_on_critical_path", False):
            explanation_parts.append("critical path")
        
        float_days = features.get("float_days", 999)
        if float_days <= 2:
            explanation_parts.append("low float")
        
        if features.get("resource_overbooked", False):
            explanation_parts.append("resource overload")
        
        if features.get("progress_slip", 0) > 0.2:
            slip_pct = int(features["progress_slip"] * 100)
            explanation_parts.append(f"{slip_pct}% progress slip")
        
        # Build the explanation string (matching problem statement format)
        if explanation_parts:
            explanation = f"Activity {activity_id} at {risk_level} risk (score {int(score)}): {' + '.join(explanation_parts)}."
        else:
            explanation = f"Activity {activity_id} at {risk_level} risk (score {int(score)}): moderate risk factors."
        
        # Get detailed explanation if requested
        detailed_explanation = None
        if include_explanations:
            # Use rule-based explanation (fast, no LLM needed)
            from core.models import Activity as ActivityModel
            # Use cached activity map instead of querying database again
            activity = activity_map.get(activity_id)
            
            if activity:
                # Create activity object for explanation
                activity_obj = ActivityModel(
                    activity_id=activity.activity_id,
                    name=activity.name,
                    planned_start=activity.planned_start,
                    planned_finish=activity.planned_finish,
                    baseline_start=activity.baseline_start,
                    baseline_finish=activity.baseline_finish,
                    planned_duration=activity.planned_duration,
                    baseline_duration=activity.baseline_duration,
                    actual_start=activity.actual_start,
                    actual_finish=activity.actual_finish,
                    remaining_duration=activity.remaining_duration,
                    percent_complete=activity.percent_complete,
                    risk_probability=activity.risk_probability,
                    risk_delay_impact_days=activity.risk_delay_impact_days,
                    predecessors=activity.predecessors if hasattr(activity, 'predecessors') else [],
                    successors=activity.successors if hasattr(activity, 'successors') else [],
                    on_critical_path=activity.on_critical_path if hasattr(activity, 'on_critical_path') else False,
                    resource_id=activity.resource_id if hasattr(activity, 'resource_id') else None,
                    fte_allocation=activity.fte_allocation if hasattr(activity, 'fte_allocation') else None,
                    resource_max_fte=activity.resource_max_fte if hasattr(activity, 'resource_max_fte') else None
                )
            detailed = explain_rule_based(activity_obj, features, score)
            detailed_explanation = {
                "reasons": detailed.get("reasons", []),
                "suggestions": detailed.get("suggestions", [])
            }
        
        enhanced_risk = {
            "activity_id": activity_id,
            "name": name,
            "risk_score": round(score, 1),
            "risk_level": risk_level,
            "explanation": explanation,  # Human-readable summary
            "risk_factors": risk_factors,
            "key_metrics": {
                "delay_days": int(delay_days),
                "float_days": round(float_days, 1),
                "on_critical_path": features.get("is_on_critical_path", False),
                "resource_overbooked": features.get("resource_overbooked", False),
                "progress_slip_pct": round(features.get("progress_slip", 0) * 100, 1),
                "baseline_finish": activity.baseline_finish if hasattr(activity, 'baseline_finish') else None,
                "planned_finish": activity.planned_finish if hasattr(activity, 'planned_finish') else None
            },
            "percent_complete": risk.get("percent_complete", 0),
            "on_critical_path": features.get("is_on_critical_path", False)
        }
        
        if detailed_explanation:
            enhanced_risk["detailed_explanation"] = detailed_explanation
        
        enhanced_risks.append(enhanced_risk)
    
    return enhanced_risks


@router.get("/projects/{project_id}/anomalies")
def get_anomalies(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    force_recompute: bool = False
):
    """
    Get anomalies (zombie tasks and resource black holes) for a project - requires authentication and ownership
    
    Uses cache if available to provide instant responses. Set force_recompute=true to bypass cache.
    """
    start_time = time.time()
    
    verify_project_ownership(db, project_id, current_user)
    auth_time = time.time()
    
    # Load activities from database
    activities = get_activities(db, project_id)
    activity_count = len(activities) if activities else 0
    db_time = time.time()
    
    if not activities:
        raise HTTPException(status_code=404, detail="Project not found or has no activities")
    
    # Always use today's date (date selection feature removed)
    reference_date = None
    
    # Check cache first (unless force_recompute is True)
    # Note: Cache key should include reference_date, but for backward compatibility,
    # we'll use existing cache if reference_date is None (today mode)
    if not force_recompute and reference_date is None:
        from core.cache_service import get_anomalies_cache
        cached_anomalies = get_anomalies_cache(db, project_id, activity_count)
        if cached_anomalies:
            cache_time = time.time()
            total_time = cache_time - start_time
            print(f"[CACHE] Anomalies served from cache in {total_time:.3f}s")
            return cached_anomalies
    
    # Cache miss or force recompute - compute anomalies with reference_date
    try:
        # Pass activities directly to avoid PROJECTS dict dependency
        anomalies = detect_anomalies(project_id, activities=activities, reference_date=reference_date)
        detection_time = time.time()
        
        # Priority 5: Add contextual explanations to zombie tasks
        try:
            from core.anomaly_explanation_service import get_anomaly_explanation_service
            explanation_service = get_anomaly_explanation_service()
            
            # Enhance zombie tasks with business context
            enhanced_zombies = []
            for zombie in anomalies.get("zombie_tasks", []):
                enhanced = explanation_service.explain_zombie_task(
                    zombie,
                    activities,
                    project_id
                )
                enhanced_zombies.append(enhanced)
            
            if enhanced_zombies:
                anomalies["zombie_tasks"] = enhanced_zombies
        except Exception as e:
            print(f"[Anomaly] Failed to generate explanations: {e}")
            # Don't fail the request if explanation fails
        
        # Save to cache for future requests
        from core.cache_service import save_anomalies_cache
        save_anomalies_cache(db, project_id, anomalies, activity_count)
        cache_save_time = time.time()
        
        # Log the anomaly detection event
        log_event_db(
            db,
            project_id,
            "anomaly_detection",
            {
                "zombie_count": len(anomalies.get("zombie_tasks", [])),
                "black_hole_count": len(anomalies.get("black_holes", [])),
                "total_anomalies": anomalies.get("total_anomalies", 0),
                "from_cache": False
            }
        )
        
        total_time = time.time() - start_time
        # Log performance metrics (can be removed in production if not needed)
        if total_time > 1.0:  # Only log if slow
            print(f"[PERF] Anomalies endpoint timing - Total: {total_time:.2f}s, Auth: {auth_time-start_time:.2f}s, DB: {db_time-auth_time:.2f}s, Detection: {detection_time-db_time:.2f}s, Cache: {cache_save_time-detection_time:.2f}s")
        
        return anomalies
    finally:
        # Clean up PROJECTS dict if needed (optional, for memory management)
        pass

