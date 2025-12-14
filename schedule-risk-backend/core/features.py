"""
Feature engineering and extraction
"""

from datetime import datetime, date
from typing import Dict, List, Optional
import pandas as pd
from .models import Activity
from .digital_twin import get_or_build_twin
from .forensic_extractor import extract_forensic_features


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


def compute_features(activity: Activity, project_id: str, activities: Optional[List[Activity]] = None, twin=None, reference_date: Optional[date] = None, skill_analysis: Optional[Dict] = None) -> Dict:
    """
    Compute all features for an activity
    OPTIMIZED: Accepts optional twin parameter to avoid repeated lookups
    
    Args:
        activity: Activity to compute features for
        project_id: Project identifier
        activities: List of all activities (optional)
        twin: Digital twin instance (optional, will be built if not provided)
        reference_date: Reference date for date-dependent calculations (defaults to today if None)
                       This allows using CSV date or custom date instead of current date.
    
    Returns:
        Dictionary of computed features
    """
    # OPTIMIZATION: Use provided twin if available, otherwise build/cache it
    if twin is None:
        twin = get_or_build_twin(project_id, activities)
    graph = twin.graph
    
    # Date parsing
    planned_start = parse_date(activity.planned_start)
    planned_finish = parse_date(activity.planned_finish)
    baseline_start = parse_date(activity.baseline_start)
    baseline_finish = parse_date(activity.baseline_finish)
    actual_start = parse_date(activity.actual_start)
    actual_finish = parse_date(activity.actual_finish)
    
    # Delay calculations
    delay_baseline_days = 0.0
    if baseline_finish and planned_finish:
        delay = (planned_finish - baseline_finish).days
        delay_baseline_days = max(0, delay)
    
    # Float (slack) calculation - compute from graph if Total_Float not available
    float_days = 0.0
    # Check if total_float is available and not None (0.0 is a valid value, so check is not None)
    if activity.total_float is not None:
        # Use Total_Float from CSV if available (most accurate)
        try:
            float_days = float(activity.total_float)
            # Ensure it's not negative
            float_days = max(0.0, float_days)
        except (ValueError, TypeError, AttributeError):
            float_days = 0.0
    # If total_float is None or 0, float_days remains 0.0 (which is correct for 0 float)
    elif planned_start and planned_finish and activities:
        # Compute float from graph using critical path method
        try:
            import networkx as nx
            # Calculate ES, EF, LS, LF for all activities
            activity_map = {a.activity_id: a for a in activities}
            
            # Forward pass: calculate ES and EF
            try:
                topo_order = list(nx.topological_sort(graph))
            except nx.NetworkXError:
                # Graph has cycles, use simple heuristic
                topo_order = list(graph.nodes())
            
            earliest_start = {}
            earliest_finish = {}
            
            for node_id in topo_order:
                if node_id not in activity_map:
                    continue
                node_activity = activity_map[node_id]
                node_duration = node_activity.planned_duration or node_activity.baseline_duration or 1.0
                
                # ES = max of all predecessor finishes
                pred_finishes = []
                for pred_id in graph.predecessors(node_id):
                    if pred_id in earliest_finish:
                        pred_finishes.append(earliest_finish[pred_id])
                
                if pred_finishes:
                    earliest_start[node_id] = max(pred_finishes)
                else:
                    # No predecessors, start at 0
                    earliest_start[node_id] = 0.0
                
                earliest_finish[node_id] = earliest_start[node_id] + node_duration
            
            # Backward pass: calculate LS and LF
            if earliest_finish:
                project_finish = max(earliest_finish.values())
            else:
                project_finish = 0.0
            
            latest_start = {}
            latest_finish = {}
            
            for node_id in reversed(topo_order):
                if node_id not in activity_map:
                    continue
                node_activity = activity_map[node_id]
                node_duration = node_activity.planned_duration or node_activity.baseline_duration or 1.0
                
                # LF = min of all successor starts
                succ_starts = []
                for succ_id in graph.successors(node_id):
                    if succ_id in latest_start:
                        succ_starts.append(latest_start[succ_id])
                
                if succ_starts:
                    latest_finish[node_id] = min(succ_starts)
                else:
                    # No successors, finish at project finish
                    latest_finish[node_id] = project_finish
                
                latest_start[node_id] = latest_finish[node_id] - node_duration
            
            # Calculate float for this activity: Float = LS - ES (or LF - EF)
            if activity.activity_id in earliest_start and activity.activity_id in latest_start:
                float_days = max(0.0, latest_start[activity.activity_id] - earliest_start[activity.activity_id])
        except Exception:
            # Fallback to simple heuristic if calculation fails
            if activity.on_critical_path:
                float_days = 0.0
            else:
                float_days = activity.planned_duration or 0.0
    else:
        # Fallback: use simple heuristic
        if activity.on_critical_path:
            float_days = 0.0
        else:
            float_days = activity.planned_duration or 0.0
    
    # Progress slip - EXACT SPEC FORMULA: expected_progress = (min(reference_date, Planned Finish) - Planned Start) / (Planned Finish - Planned Start)
    progress_slip = 0.0
    if planned_start and planned_finish and activity.percent_complete is not None:
        # Use reference_date if provided, otherwise use today (backward compatible)
        if reference_date is None:
            reference_datetime = datetime.now()
        else:
            # Convert date to datetime for comparison with planned_finish
            reference_datetime = datetime.combine(reference_date, datetime.min.time())
        
        # Calculate expected progress per spec formula
        time_window = (planned_finish - planned_start).total_seconds() / 86400.0  # Total duration in days
        if time_window > 0:
            # min(reference_date, Planned Finish) - Planned Start
            numerator_time = min(reference_datetime, planned_finish)
            elapsed_time = (numerator_time - planned_start).total_seconds() / 86400.0
            elapsed_time = max(0.0, elapsed_time)  # Can't be negative
            
            expected_progress = elapsed_time / time_window
            expected_progress = min(1.0, max(0.0, expected_progress))  # Clamp to [0, 1]
            
            actual_progress = activity.percent_complete / 100.0
            # progress_slip = max(expected_progress - actual_progress, 0)
            progress_slip = max(0.0, expected_progress - actual_progress)
        else:
            # Zero or negative time window - can't calculate progress slip
            progress_slip = 0.0
    
    # Risk register expected delay - EXACT SPEC: Probability(%)/100 * Delay Impact (days)
    # Note: risk_probability is already in 0-1 range (converted from % in CSV), so this is correct
    # But to be explicit per spec: if we had Probability(%) as percentage, it would be: (Probability(%)/100) * Delay_Impact_days
    expected_delay_days = activity.risk_probability * activity.risk_delay_impact_days
    
    # Graph features
    predecessor_count = len(activity.predecessors)
    successor_count = len(activity.successors)
    in_degree = graph.in_degree(activity.activity_id)
    out_degree = graph.out_degree(activity.activity_id)
    
    # Calculate downstream critical depth (how deep the chain of critical successors is)
    downstream_critical_depth = 0
    if activities:
        # Build a map of activity_id -> activity for quick lookup
        activity_map = {a.activity_id: a for a in activities}
        
        def calculate_critical_depth(node_id: str, visited: set, depth: int = 0) -> int:
            """Recursively calculate maximum depth of critical path successors"""
            if node_id in visited or node_id not in activity_map:
                return depth
            
            visited.add(node_id)
            max_depth = depth
            
            # Check all successors
            if node_id in graph:
                for successor_id in graph.successors(node_id):
                    if successor_id in activity_map:
                        successor_activity = activity_map[successor_id]
                        # If successor is on critical path, continue traversing
                        if successor_activity.on_critical_path:
                            successor_depth = calculate_critical_depth(
                                successor_id, visited.copy(), depth + 1
                            )
                            max_depth = max(max_depth, successor_depth)
            
            return max_depth
        
        if activity.on_critical_path:
            downstream_critical_depth = calculate_critical_depth(activity.activity_id, set())
        else:
            # Even if not on critical path, check if successors are
            for successor_id in activity.successors:
                if successor_id in activity_map:
                    successor_activity = activity_map[successor_id]
                    if successor_activity.on_critical_path:
                        depth = calculate_critical_depth(successor_id, set(), 1)
                        downstream_critical_depth = max(downstream_critical_depth, depth)
    
    # Resource features - fte_ratio per spec: FTE_Allocation / Resource_Max_FTE
    fte_ratio = 0.0
    resource_overbooked = False
    if activity.resource_max_fte and activity.resource_max_fte > 0:
        fte_ratio = (activity.fte_allocation or 0.0) / activity.resource_max_fte
        resource_overbooked = fte_ratio > 1.0
    
    # Float score per SPEC: float_score = {1 if ≤0, 1 - Total_Float/5 if 0<Total_Float<5, 0 if ≥5}
    float_score = 0.0
    if float_days <= 0:
        float_score = 1.0
    elif 0 < float_days < 5:
        float_score = 1.0 - (float_days / 5.0)
        float_score = max(0.0, min(1.0, float_score))  # Clamp to [0, 1]
    else:  # float_days >= 5
        float_score = 0.0
    
    # Critical path flag: 1 if total float is zero, 0 otherwise (per spec)
    critical_path_flag = 1.0 if float_days <= 0.0 else 0.0
    
    # Anomaly flags per spec
    zombie_task_flag = 0.0
    if planned_start:
        # Use reference_date if provided, otherwise use today (backward compatible)
        if reference_date is None:
            reference_datetime = datetime.now()
        else:
            # Convert date to datetime for comparison with planned_start
            reference_datetime = datetime.combine(reference_date, datetime.min.time())
        
        # Normalize planned_start to date for comparison
        planned_start_date = planned_start.date() if hasattr(planned_start, 'date') else planned_start
        reference_date_for_compare = reference_date if reference_date else datetime.now().date()
        
        if planned_start_date <= reference_date_for_compare and (activity.percent_complete or 0.0) < 5.0:
            zombie_task_flag = 1.0
    
    # Resource black hole flag (will be computed later in anomalies.py, but we can set a preliminary flag)
    resource_black_hole_flag = 1.0 if resource_overbooked else 0.0
    
    # Extract forensic features (Layer 1: Forensic Intelligence)
    forensic_features = extract_forensic_features(activity)
    
    # Skill constraint risk (from skill analysis if available)
    is_skill_bottleneck = False
    skill_overload_pct = 0.0
    skill_variance_multiplier = 1.0
    
    if skill_analysis:
        from .skill_analyzer import get_activity_skill_risk
        is_skill_bottleneck = get_activity_skill_risk(activity.activity_id, skill_analysis)
        if is_skill_bottleneck:
            # Find the overload percentage for this activity's skills
            bottlenecks = skill_analysis.get("skill_bottlenecks", [])
            variance_map = skill_analysis.get("variance_increase_map", {})
            skill_variance_multiplier = variance_map.get(activity.activity_id, 1.0)
            
            for bottleneck in bottlenecks:
                if activity.activity_id in bottleneck.get("activities", []):
                    skill_overload_pct = max(skill_overload_pct, bottleneck.get("overload_pct", 0.0))
    
    # Build enriched features dict
    base_features = {
        "activity_id": activity.activity_id,
        "delay_baseline_days": delay_baseline_days,
        "float_days": float_days,
        "float_score": float_score,  # NEW: per spec formula
        "progress_slip": progress_slip,
        "expected_delay_days": expected_delay_days,
        "is_on_critical_path": activity.on_critical_path,
        "critical_path_flag": critical_path_flag,  # NEW: per spec (1 if float=0, 0 otherwise)
        "predecessor_count": predecessor_count,
        "successor_count": successor_count,
        "downstream_critical_depth": downstream_critical_depth,
        "in_degree": in_degree,
        "out_degree": out_degree,
        "fte_ratio": fte_ratio,  # NEW: per spec (FTE_Allocation / Resource_Max_FTE)
        "resource_utilization": fte_ratio,  # Keep for backward compatibility
        "resource_overbooked": resource_overbooked,
        "zombie_task_flag": zombie_task_flag,  # NEW: per spec
        "resource_black_hole_flag": resource_black_hole_flag,  # NEW: per spec
        "percent_complete": activity.percent_complete,
        "risk_probability": activity.risk_probability,
        "risk_delay_impact_days": activity.risk_delay_impact_days,
        "cost_impact_of_risk": activity.cost_impact_of_risk or 0.0,
        # Forensic Intelligence features (for Monte Carlo modulation)
        "drift_velocity": forensic_features.get("drift_velocity", {}),
        "cost_performance": forensic_features.get("cost_performance", {}),
        "is_skill_bottleneck": is_skill_bottleneck,
        "skill_overload_pct": skill_overload_pct,
        "skill_variance_multiplier": skill_variance_multiplier,
    }
    
    return base_features

