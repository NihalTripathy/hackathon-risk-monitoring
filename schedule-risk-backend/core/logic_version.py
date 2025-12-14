"""
Logic Version Tracking System
Tracks algorithm/logic versions to automatically invalidate cache when logic changes.
"""

import hashlib
import os
from typing import Dict, Any

# Logic version - increment this when you change algorithms, formulas, or logic
# This should be updated whenever risk calculation, forecast, or anomaly detection logic changes
LOGIC_VERSION = os.getenv("LOGIC_VERSION", "1.0.0")

# Component versions - track individual component changes
COMPONENT_VERSIONS = {
    "risk_calculation": os.getenv("RISK_LOGIC_VERSION", "1.0.0"),
    "forecast_algorithm": os.getenv("FORECAST_LOGIC_VERSION", "1.0.0"),
    "anomaly_detection": os.getenv("ANOMALY_LOGIC_VERSION", "1.0.0"),
    "feature_computation": os.getenv("FEATURE_LOGIC_VERSION", "1.0.0"),
}

# ML model version (if using ML)
ML_MODEL_VERSION = os.getenv("ML_MODEL_VERSION", "1.0.0")


def get_logic_version() -> str:
    """
    Get current logic version string.
    
    Returns:
        Logic version string (e.g., "1.0.0")
    """
    return LOGIC_VERSION


def get_component_versions() -> Dict[str, str]:
    """
    Get versions for all components.
    
    Returns:
        Dict mapping component names to versions
    """
    return COMPONENT_VERSIONS.copy()


def get_full_logic_signature() -> str:
    """
    Get a combined signature of all logic versions.
    This is used to detect any logic changes.
    
    Returns:
        SHA256 hash of all version strings combined
    """
    # Combine all versions into a single string
    version_string = f"{LOGIC_VERSION}|{ML_MODEL_VERSION}|" + "|".join(
        f"{k}:{v}" for k, v in sorted(COMPONENT_VERSIONS.items())
    )
    
    # Return hash for compact storage
    return hashlib.sha256(version_string.encode()).hexdigest()[:16]  # 16 chars is enough


def compute_data_hash(activities: list) -> str:
    """
    Compute hash of activity data content.
    This detects changes in activity data even if activity_count stays the same.
    
    Args:
        activities: List of Activity objects or dicts with activity data
        
    Returns:
        SHA256 hash of data content (first 16 chars for compact storage)
    """
    import json
    from core.models import Activity as ActivityModel
    
    # Extract key fields that affect calculations
    data_fields = []
    
    for act in activities:
        # Use ActivityModel if it's an object, otherwise assume dict
        if isinstance(act, ActivityModel):
            fields = {
                "id": act.activity_id,
                "name": act.name,
                "planned_start": act.planned_start,
                "planned_finish": act.planned_finish,
                "baseline_start": act.baseline_start,
                "baseline_finish": act.baseline_finish,
                "planned_duration": act.planned_duration,
                "baseline_duration": act.baseline_duration,
                "actual_start": act.actual_start,
                "actual_finish": act.actual_finish,
                "remaining_duration": act.remaining_duration,
                "percent_complete": act.percent_complete,
                "risk_probability": act.risk_probability,
                "risk_delay_impact_days": act.risk_delay_impact_days,
                "predecessors": sorted(act.predecessors) if act.predecessors else [],
                "successors": sorted(act.successors) if act.successors else [],
                "on_critical_path": act.on_critical_path,
                "resource_id": act.resource_id,
                "fte_allocation": act.fte_allocation,
                "resource_max_fte": act.resource_max_fte,
            }
        else:
            # Assume dict
            fields = {
                "id": act.get("activity_id") or act.get("id"),
                "name": act.get("name"),
                "planned_start": act.get("planned_start"),
                "planned_finish": act.get("planned_finish"),
                "baseline_start": act.get("baseline_start"),
                "baseline_finish": act.get("baseline_finish"),
                "planned_duration": act.get("planned_duration"),
                "baseline_duration": act.get("baseline_duration"),
                "actual_start": act.get("actual_start"),
                "actual_finish": act.get("actual_finish"),
                "remaining_duration": act.get("remaining_duration"),
                "percent_complete": act.get("percent_complete"),
                "risk_probability": act.get("risk_probability"),
                "risk_delay_impact_days": act.get("risk_delay_impact_days"),
                "predecessors": sorted(act.get("predecessors", [])),
                "successors": sorted(act.get("successors", [])),
                "on_critical_path": act.get("on_critical_path", False),
                "resource_id": act.get("resource_id"),
                "fte_allocation": act.get("fte_allocation"),
                "resource_max_fte": act.get("resource_max_fte"),
            }
        
        # Sort by activity_id for consistent hashing
        data_fields.append(json.dumps(fields, sort_keys=True))
    
    # Sort all activities by ID for consistent hashing
    data_string = "|".join(sorted(data_fields))
    
    # Compute hash
    return hashlib.sha256(data_string.encode()).hexdigest()[:16]  # 16 chars is enough

