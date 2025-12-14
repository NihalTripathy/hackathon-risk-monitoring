"""
Anomaly detection functionality
"""

from datetime import datetime, date
from typing import List, Dict, Optional
from .models import Activity, PROJECTS
from .digital_twin import get_or_build_twin
import pandas as pd


def parse_date(date_str):
    """Parse date string to datetime or return None"""
    if not date_str:
        return None
    try:
        if isinstance(date_str, str) and date_str.strip() == "":
            return None
        # Try parsing with dayfirst=True to handle DD-MM-YYYY format, fallback to default
        return pd.to_datetime(date_str, dayfirst=True, errors='coerce')
    except:
        return None


def detect_zombie_tasks(project_id: str, activities: Optional[List] = None, reference_date: Optional[date] = None) -> List[Dict]:
    """
    Detect tasks that should have started but didn't (Zombie tasks).
    Enhanced to check if predecessors are complete before flagging as zombie.
    All date comparisons are normalized to date-only (no time component) for accuracy.
    
    Args:
        project_id: Project identifier
        activities: List of activities (optional, will load from PROJECTS if not provided)
        reference_date: Reference date for comparison (defaults to today if None)
                       This allows using CSV date or custom date instead of current date.
    
    Returns:
        List of zombie task dictionaries
    """
    if activities is None:
        activities = PROJECTS.get(project_id, [])
    zombies = []
    
    # Use reference_date if provided, otherwise use today (backward compatible)
    if reference_date is None:
        reference_date = datetime.now().date()
    else:
        # Ensure reference_date is a date object
        if hasattr(reference_date, 'date'):
            reference_date = reference_date.date()
    
    # Build activity map for quick lookup
    activity_map = {a.activity_id: a for a in activities}
    
    def are_predecessors_complete(activity) -> bool:
        """Check if all predecessors are complete"""
        if not activity.predecessors:
            return True  # No predecessors, so they're "complete"
        
        for pred_id in activity.predecessors:
            if not pred_id or not pred_id.strip():
                continue
            # Handle FS suffix and multiple predecessors (e.g., "1FS", "1 2FS")
            pred_id_clean = pred_id.strip().replace("FS", "").strip()
            pred_ids = [p.strip() for p in pred_id_clean.split() if p.strip()]
            
            for pid in pred_ids:
                pred_activity = activity_map.get(pid)
                if not pred_activity:
                    # Predecessor not found - assume incomplete to be safe
                    return False
                
                # Check if predecessor is complete
                pred_complete = (
                    pred_activity.percent_complete >= 100.0 or
                    (pred_activity.actual_finish is not None and parse_date(pred_activity.actual_finish) is not None)
                )
                if not pred_complete:
                    return False
        
        return True
    
    for activity in activities:
        planned_start = parse_date(activity.planned_start)
        
        # Normalize planned_start to date-only for comparison
        if planned_start:
            planned_start_date = planned_start.date() if hasattr(planned_start, 'date') else planned_start
            # Use <= to catch tasks due on reference date that haven't started
            if planned_start_date <= reference_date:
                # Task should have started
                # Per spec: zombie task if Planned_Start <= reference_date and Percent_Complete < 5%
                percent_complete = activity.percent_complete or 0.0
                if not activity.actual_start and percent_complete < 5.0:
                    # Check if predecessors are complete (or no predecessors)
                    # Format date as DD-MM-YYYY for consistency
                    def format_date_dd_mm_yyyy(dt):
                        if dt is None:
                            return None
                        return dt.strftime("%d-%m-%Y")
                    
                    if are_predecessors_complete(activity):
                        days_overdue = (reference_date - planned_start_date).days
                        zombies.append({
                            "activity_id": activity.activity_id,
                            "name": activity.name,
                            "planned_start": format_date_dd_mm_yyyy(planned_start),
                            "days_overdue": days_overdue,
                            "anomaly_type": "zombie",
                            "predecessors_ready": True
                        })
                    else:
                        # Predecessors not complete - but task is still overdue
                        # Change message to be more accurate and actionable
                        days_overdue = (reference_date - planned_start_date).days
                        if days_overdue > 7:  # More than a week overdue
                            zombies.append({
                                "activity_id": activity.activity_id,
                                "name": activity.name,
                                "planned_start": format_date_dd_mm_yyyy(planned_start),
                                "days_overdue": days_overdue,
                                "anomaly_type": "zombie",
                                "predecessors_ready": False,
                                "note": "Planned start has passed but progress is 0%"
                            })
    
    return zombies


def detect_black_holes(project_id: str, activities: Optional[List] = None) -> List[Dict]:
    """
    Detect overloaded resources (Black Holes) with time-phased overlap analysis.
    Checks for resources where overlapping FTE_Allocation > Resource_Max_FTE,
    especially for tasks that overlap in critical periods.
    """
    if activities is None:
        activities = PROJECTS.get(project_id, [])
    resource_loads = {}
    
    # Group activities by resource and calculate time-phased utilization
    for activity in activities:
        if activity.resource_id:
            if activity.resource_id not in resource_loads:
                resource_loads[activity.resource_id] = {
                    "max_fte": activity.resource_max_fte or 1.0,
                    "activities": [],
                    "time_windows": []  # List of (start, finish, fte) tuples
                }
            
            # Parse activity dates
            planned_start = parse_date(activity.planned_start)
            planned_finish = parse_date(activity.planned_finish)
            actual_start = parse_date(activity.actual_start)
            actual_finish = parse_date(activity.actual_finish)
            
            # Use actual dates if available, otherwise planned
            start_date = actual_start or planned_start
            finish_date = actual_finish or planned_finish
            
            # Validate dates before using
            if start_date and finish_date:
                # Ensure finish is after start
                if finish_date < start_date:
                    # Invalid date range, skip this activity
                    continue
                fte = activity.fte_allocation or 0.0
                act_info = {
                    "activity_id": activity.activity_id,
                    "name": activity.name,
                    "start": start_date,
                    "finish": finish_date,
                    "fte": fte,
                    "on_critical_path": activity.on_critical_path
                }
                resource_loads[activity.resource_id]["activities"].append(act_info)
                # Store activity info with time window for O(1) lookup
                resource_loads[activity.resource_id]["time_windows"].append(
                    (start_date, finish_date, fte, act_info)  # Include act_info for direct access
                )
    
    # Find overloaded resources using time-phased analysis
    black_holes = []
    for resource_id, load_info in resource_loads.items():
        max_fte = load_info["max_fte"]
        time_windows = load_info["time_windows"]
        
        if not time_windows:
            continue
        
        # Find all unique time points (start and finish dates)
        time_points = set()
        for time_window in time_windows:
            start, finish, _, _ = time_window  # Unpack: start, finish, fte, act_info
            time_points.add(start)
            time_points.add(finish)
        time_points = sorted(time_points)
        
        # Check utilization at each time interval
        max_overlap = 0.0
        max_overlap_period = None
        critical_overlaps = []  # Overlaps during critical periods
        
        for i in range(len(time_points) - 1):
            interval_start = time_points[i]
            interval_end = time_points[i + 1]
            
            # Calculate total FTE in this interval
            total_fte_in_interval = 0.0
            overlapping_activities = []
            has_critical = False
            
            # Optimized: use stored act_info from time_windows tuple (4th element)
            for time_window in time_windows:
                start, finish, fte, act_info = time_window
                # Check if activity overlaps with this interval
                if start <= interval_end and finish >= interval_start:
                    total_fte_in_interval += fte
                    overlapping_activities.append(act_info)
                    if act_info["on_critical_path"]:
                        has_critical = True
            
            # Track maximum overlap
            if total_fte_in_interval > max_overlap:
                max_overlap = total_fte_in_interval
                max_overlap_period = (interval_start, interval_end)
            
            # Track critical period overlaps
            if total_fte_in_interval > max_fte and has_critical:
                critical_overlaps.append({
                    "period": (interval_start, interval_end),  # Keep as datetime objects for now
                    "total_fte": total_fte_in_interval,
                    "utilization": total_fte_in_interval / max_fte if max_fte > 0 else 0,
                    "activities": [a["activity_id"] for a in overlapping_activities]
                })
        
        # Check if resource is overloaded
        if max_overlap > max_fte:
            # Calculate overall utilization (simple sum for backward compatibility)
            total_fte_sum = sum(act["fte"] for act in load_info["activities"])
            overall_utilization = total_fte_sum / max_fte if max_fte > 0 else 0
            
            # Format dates as DD-MM-YYYY for consistency
            def format_date_dd_mm_yyyy(dt):
                if dt is None:
                    return None
                return dt.strftime("%d-%m-%Y")
            
            formatted_max_overlap_period = None
            if max_overlap_period:
                formatted_max_overlap_period = (
                    format_date_dd_mm_yyyy(max_overlap_period[0]),
                    format_date_dd_mm_yyyy(max_overlap_period[1])
                )
            
            # Format critical overlaps dates
            formatted_critical_overlaps = []
            for overlap in critical_overlaps:
                formatted_overlap = overlap.copy()
                if "period" in formatted_overlap and formatted_overlap["period"]:
                    formatted_overlap["period"] = (
                        format_date_dd_mm_yyyy(formatted_overlap["period"][0]),
                        format_date_dd_mm_yyyy(formatted_overlap["period"][1])
                    )
                formatted_critical_overlaps.append(formatted_overlap)
            
            black_holes.append({
                "resource_id": resource_id,
                "utilization": overall_utilization,
                "max_overlap_utilization": max_overlap / max_fte if max_fte > 0 else 0,
                "total_fte": total_fte_sum,
                "max_fte": max_fte,
                "max_overlap_fte": max_overlap,
                "max_overlap_period": formatted_max_overlap_period,
                "activity_count": len(load_info["activities"]),
                "activities": [a["activity_id"] for a in load_info["activities"]],
                "critical_overlaps": formatted_critical_overlaps,  # Overlaps during critical periods
                "anomaly_type": "black_hole"
            })
    
    return black_holes


def detect_anomalies(project_id: str, activities: Optional[List] = None, reference_date: Optional[date] = None) -> Dict:
    """
    Detect all anomalies for a project.
    
    Args:
        project_id: Project identifier
        activities: List of activities (optional)
        reference_date: Reference date for comparison (defaults to today if None)
    
    Returns:
        Dictionary with zombie_tasks, black_holes, and total_anomalies
    """
    zombies = detect_zombie_tasks(project_id, activities, reference_date=reference_date)
    black_holes = detect_black_holes(project_id, activities)
    
    return {
        "zombie_tasks": zombies,
        "black_holes": black_holes,
        "total_anomalies": len(zombies) + len(black_holes)
    }

