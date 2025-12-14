"""
Gantt Chart API endpoints - Priority 3: Gantt Chart Visualization
SOLID compliant Gantt chart data generation
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from core.database import get_db
from core.db_service import get_activities
from core.project_auth import verify_project_ownership
from core.auth_dependencies import get_current_user
from core.risk_pipeline import compute_project_risks
from api.auth import UserResponse
from datetime import datetime
import pandas as pd

router = APIRouter()


def parse_date(date_str):
    """Parse date string to datetime or return None"""
    if not date_str:
        return None
    try:
        if isinstance(date_str, str) and date_str.strip() == "":
            return None
        return pd.to_datetime(date_str, dayfirst=True, errors='coerce')
    except:
        return None


@router.get("/projects/{project_id}/gantt")
def get_gantt_data(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get Gantt chart data for project visualization
    Returns activities with timeline, dependencies, and risk indicators
    """
    verify_project_ownership(db, project_id, current_user)
    
    # Get activities
    activities = get_activities(db, project_id)
    if not activities:
        raise HTTPException(status_code=404, detail="Project not found or has no activities")
    
    # Get risk scores
    # Get reference date from project preference
    # Always use today's date (date selection feature removed)
    reference_date = None
    risks = compute_project_risks(project_id, db=db, activities=activities, reference_date=reference_date)
    risk_map = {r["activity_id"]: r["risk_score"] for r in risks}
    
    # Build Gantt data
    gantt_data = []
    for activity in activities:
        planned_start = parse_date(activity.planned_start)
        planned_finish = parse_date(activity.planned_finish)
        baseline_start = parse_date(activity.baseline_start)
        baseline_finish = parse_date(activity.baseline_finish)
        
        # Calculate duration
        duration = activity.planned_duration or activity.baseline_duration or 1.0
        
        # Get risk score
        risk_score = risk_map.get(activity.activity_id, 0)
        
        # Determine risk color
        if risk_score >= 70:
            risk_color = "#dc2626"  # Red - High
            risk_level = "high"
        elif risk_score >= 40:
            risk_color = "#f59e0b"  # Yellow - Medium
            risk_level = "medium"
        else:
            risk_color = "#10b981"  # Green - Low
            risk_level = "low"
        
        # Build dependency list
        dependencies = []
        if hasattr(activity, 'predecessors') and activity.predecessors:
            # Predecessors can be a list (from ActivityModel) or a string (from database)
            if isinstance(activity.predecessors, list):
                for pred_id in activity.predecessors:
                    if pred_id and str(pred_id).strip():
                        dependencies.append(str(pred_id).strip())
            elif isinstance(activity.predecessors, str):
                # Parse comma-separated or JSON string
                try:
                    import json
                    pred_list = json.loads(activity.predecessors)
                    if isinstance(pred_list, list):
                        dependencies = [str(p).strip() for p in pred_list if p and str(p).strip()]
                    else:
                        # Single value or comma-separated
                        pred_str = activity.predecessors.strip()
                        if pred_str:
                            dependencies = [p.strip() for p in pred_str.split(',') if p.strip()]
                except:
                    # Fallback: treat as comma-separated string
                    pred_str = activity.predecessors.strip()
                    if pred_str:
                        dependencies = [p.strip() for p in pred_str.split(',') if p.strip()]
        
        gantt_item = {
            "id": activity.activity_id,
            "name": activity.name or activity.activity_id,
            "start": planned_start.isoformat() if planned_start else None,
            "end": planned_finish.isoformat() if planned_finish else None,
            "baseline_start": baseline_start.isoformat() if baseline_start else None,
            "baseline_end": baseline_finish.isoformat() if baseline_finish else None,
            "duration": duration,
            "progress": activity.percent_complete or 0,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "on_critical_path": activity.on_critical_path if hasattr(activity, 'on_critical_path') else False,
            "dependencies": dependencies,
            "resource_id": activity.resource_id if hasattr(activity, 'resource_id') else None,
            "fte_allocation": activity.fte_allocation if hasattr(activity, 'fte_allocation') else 0
        }
        
        gantt_data.append(gantt_item)
    
    # Calculate critical path (for highlighting)
    critical_path_activities = [a.activity_id for a in activities if a.on_critical_path]
    
    return {
        "project_id": project_id,
        "activities": gantt_data,
        "critical_path": critical_path_activities,
        "total_activities": len(gantt_data),
        "high_risk_count": len([a for a in gantt_data if a["risk_level"] == "high"]),
        "medium_risk_count": len([a for a in gantt_data if a["risk_level"] == "medium"]),
        "low_risk_count": len([a for a in gantt_data if a["risk_level"] == "low"])
    }

