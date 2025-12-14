"""
Skill Constraint Engine - Layer 1
Detects skill bottlenecks that generic FTE counts miss
"""

from typing import List, Dict, Optional
from datetime import datetime, date
from .models import Activity
import pandas as pd


def parse_skill_tags(skill_tags_str: Optional[str]) -> List[str]:
    """Parse skill tags string into list of individual skills"""
    if not skill_tags_str:
        return []
    
    # Handle both semicolon and comma separators
    skills = []
    for separator in [';', ',']:
        if separator in skill_tags_str:
            skills = [s.strip().lower() for s in skill_tags_str.split(separator) if s.strip()]
            break
    
    # If no separator found, treat as single skill
    if not skills:
        skills = [skill_tags_str.strip().lower()]
    
    return skills


def check_skill_overload(
    activities: List[Activity],
    reference_date: Optional[date] = None
) -> Dict[str, any]:
    """
    Check for skill-based overloads across all activities.
    
    Returns:
        Dict with structure:
        {
            "skill_bottlenecks": [
                {
                    "skill": "analytics",
                    "resource_id": "R002",
                    "total_fte_demand": 1.5,
                    "max_fte": 1.0,
                    "overload_pct": 150.0,
                    "activities": ["A-001", "A-002"],
                    "time_window": "2026-01-15 to 2026-01-22"
                }
            ],
            "activity_skill_risks": {
                "A-001": ["analytics"],  # Activities with skill bottlenecks
                "A-002": ["analytics"]
            },
            "variance_increase_map": {
                "A-001": 1.4,  # Variance multiplier for this activity
                "A-002": 1.4
            }
        }
    """
    if reference_date is None:
        reference_date = date.today()
    
    # Build skill demand matrix
    skill_demand = {}  # {(skill, resource_id): {"total_fte": float, "activities": [], "time_window": ...}}
    
    for activity in activities:
        if not activity.skill_tags or not activity.resource_id:
            continue
        
        skills = parse_skill_tags(activity.skill_tags)
        if not skills:
            continue
        
        # Get activity time window
        planned_start = _parse_date(activity.planned_start)
        planned_finish = _parse_date(activity.planned_finish)
        
        if not planned_start or not planned_finish:
            continue
        
        fte = activity.fte_allocation or 0.0
        max_fte = activity.resource_max_fte or 1.0
        
        for skill in skills:
            key = (skill, activity.resource_id)
            if key not in skill_demand:
                skill_demand[key] = {
                    "total_fte": 0.0,
                    "max_fte": max_fte,
                    "activities": [],
                    "time_window_start": planned_start,
                    "time_window_end": planned_finish
                }
            
            skill_demand[key]["total_fte"] += fte
            skill_demand[key]["activities"].append({
                "activity_id": activity.activity_id,
                "activity_name": activity.name,
                "fte": fte,
                "start": planned_start,
                "finish": planned_finish
            })
            
            # Update time window to cover all activities
            if planned_start < skill_demand[key]["time_window_start"]:
                skill_demand[key]["time_window_start"] = planned_start
            if planned_finish > skill_demand[key]["time_window_end"]:
                skill_demand[key]["time_window_end"] = planned_finish
    
    # Identify bottlenecks
    bottlenecks = []
    activity_skill_risks = {}
    variance_increase_map = {}
    
    for (skill, resource_id), data in skill_demand.items():
        total_fte = data["total_fte"]
        max_fte = data["max_fte"]
        
        if total_fte > max_fte:
            overload_pct = (total_fte / max_fte) * 100.0
            
            bottleneck = {
                "skill": skill,
                "resource_id": resource_id,
                "total_fte_demand": round(total_fte, 2),
                "max_fte": round(max_fte, 2),
                "overload_pct": round(overload_pct, 1),
                "activities": [a["activity_id"] for a in data["activities"]],
                "activity_details": data["activities"],
                "time_window": f"{data['time_window_start']} to {data['time_window_end']}"
            }
            bottlenecks.append(bottleneck)
            
            # Mark activities as having skill risk
            for activity_detail in data["activities"]:
                act_id = activity_detail["activity_id"]
                if act_id not in activity_skill_risks:
                    activity_skill_risks[act_id] = []
                if skill not in activity_skill_risks[act_id]:
                    activity_skill_risks[act_id].append(skill)
                
                # Calculate variance multiplier for this activity
                # More skills overbooked = higher variance
                num_skills = len(activity_skill_risks[act_id])
                variance_multiplier = 1.0 + (num_skills * 0.2)  # +20% per skill bottleneck
                variance_multiplier = min(2.0, variance_multiplier)  # Cap at 2x
                variance_increase_map[act_id] = variance_multiplier
    
    return {
        "skill_bottlenecks": bottlenecks,
        "activity_skill_risks": activity_skill_risks,
        "variance_increase_map": variance_increase_map
    }


def get_activity_skill_risk(activity_id: str, skill_analysis: Dict) -> bool:
    """Check if an activity has skill-based risk"""
    return activity_id in skill_analysis.get("activity_skill_risks", {})


def _parse_date(date_str):
    """Helper to parse date string"""
    if not date_str:
        return None
    try:
        return pd.to_datetime(date_str, dayfirst=True, errors='coerce').date()
    except:
        return None
