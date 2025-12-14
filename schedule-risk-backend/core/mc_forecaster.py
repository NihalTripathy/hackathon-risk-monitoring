"""
Monte Carlo forecasting implementation
"""

import numpy as np
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from .models import Activity
from .digital_twin import DigitalTwin


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


def simulate_activity_duration(activity: Activity, num_simulations: int = 1000, 
                                uncertainty_params: Optional[Dict] = None) -> np.ndarray:
    """
    Simulate activity duration using triangular/PERT distribution.
    
    Supports both:
    1. Standard mode (backward compatible): Uses risk_register_expected_delay
    2. Forensic mode: Uses uncertainty_params from Uncertainty Modulator
    
    Args:
        activity: Activity to simulate
        num_simulations: Number of simulations
        uncertainty_params: Optional dict from Uncertainty Modulator with:
            - mode_shift_factor: How much to shift mode
            - variance_multiplier: How much to widen variance
            - failure_probability: Probability of risk event
            - base_duration: Starting duration
    
    Returns: Array of simulated durations
    """
    # If forensic modulation params provided, use them
    if uncertainty_params:
        return simulate_activity_duration_forensic(activity, uncertainty_params, num_simulations)
    
    # Otherwise, use standard approach (backward compatible)
    base_duration = activity.remaining_duration or activity.planned_duration or activity.baseline_duration or 1.0
    
    if base_duration <= 0:
        base_duration = 1.0
    
    risk_probability = activity.risk_probability or 0.0
    risk_delay_impact = activity.risk_delay_impact_days or 0.0
    
    # Calculate uncertainty per spec
    # Option 1: Use risk_register_expected_delay if significant
    expected_delay = risk_probability * risk_delay_impact
    if expected_delay > 0 and base_duration > 0:
        # Derive uncertainty from expected delay: uncertainty = expected_delay / base_duration
        # But cap it at reasonable bounds (e.g., 0.5 = 50%)
        uncertainty_from_risk = min(0.5, expected_delay / base_duration)
    else:
        uncertainty_from_risk = 0.0
    
    # Option 2: Use global constant ±20% (0.2)
    global_uncertainty = 0.2
    
    # Use the larger of the two (more conservative)
    uncertainty = max(global_uncertainty, uncertainty_from_risk)
    
    # Per spec: min = Planned_Duration × (1 – uncertainty), mode = Planned_Duration, max = Planned_Duration × (1 + uncertainty)
    min_duration = base_duration * (1.0 - uncertainty)
    mode_duration = base_duration
    max_duration = base_duration * (1.0 + uncertainty)
    
    # Ensure min is positive
    min_duration = max(0.1, min_duration)
    
    # Use triangular distribution (numpy's triangular: left, mode, right)
    # Note: numpy.random.triangular uses (left, mode, right) where left <= mode <= right
    durations = np.random.triangular(min_duration, mode_duration, max_duration, num_simulations)
    
    # Ensure all durations are positive and reasonable
    durations = np.maximum(0.1, durations)
    
    return durations


def simulate_activity_duration_forensic(
    activity: Activity,
    uncertainty_params: Dict,
    num_simulations: int = 1000
) -> np.ndarray:
    """
    Simulate activity duration using forensic-modulated distributions.
    
    This implements the physics-based modulation:
    - Drift shifts mode to the right
    - Skill/topology/cluster widen variance
    - Cluster/CPI increase failure probability
    
    Args:
        activity: Activity to simulate
        uncertainty_params: Output from modulate_uncertainty()
        num_simulations: Number of simulations
    
    Returns: Array of simulated durations
    """
    base_duration = uncertainty_params["base_duration"]
    mode_shift = uncertainty_params["mode_shift_factor"]
    variance_mult = uncertainty_params["variance_multiplier"]
    failure_prob = uncertainty_params["failure_probability"]
    
    # Calculate modulated parameters
    # Mode: Shift to the right based on drift + cluster
    modulated_mode = base_duration * (1.0 + mode_shift)
    
    # Base uncertainty (20% default)
    base_uncertainty = 0.2
    
    # Variance: Widen based on skill + topology + cluster
    modulated_uncertainty = base_uncertainty * variance_mult
    modulated_uncertainty = min(0.5, modulated_uncertainty)  # Cap at 50%
    
    # Triangular distribution parameters
    min_duration = modulated_mode * (1.0 - modulated_uncertainty)
    max_duration = modulated_mode * (1.0 + modulated_uncertainty)
    
    # Ensure min is positive
    min_duration = max(0.1, min_duration)
    
    # Generate simulations
    durations = np.random.triangular(
        min_duration,
        modulated_mode,
        max_duration,
        num_simulations
    )
    
    # Apply failure events (if failure_prob > 0)
    if failure_prob > 0:
        # Randomly trigger failures based on probability
        failure_mask = np.random.random(num_simulations) < failure_prob
        
        if np.any(failure_mask):
            # On failure, add significant delay (e.g., +50% to +100%)
            failure_delays = np.random.uniform(0.5, 1.0, num_simulations)
            durations[failure_mask] *= (1.0 + failure_delays[failure_mask])
    
    # Ensure all durations are positive and reasonable
    durations = np.maximum(0.1, durations)
    
    return durations


def compute_critical_path_length(graph: nx.DiGraph, activities: Dict[str, Activity], 
                                 simulated_durations: Dict[str, float]) -> float:
    """Compute project finish time using critical path method"""
    # Topological sort to process activities in order
    try:
        topo_order = list(nx.topological_sort(graph))
    except nx.NetworkXError:
        # If graph has cycles, use simple max duration
        return max(simulated_durations.values()) if simulated_durations else 0.0
    
    # Calculate earliest start and finish times
    earliest_start = {}
    earliest_finish = {}
    
    for node in topo_order:
        if node not in simulated_durations:
            continue
        
        # Earliest start is max of all predecessor finishes
        pred_finishes = [earliest_finish.get(pred, 0.0) 
                        for pred in graph.predecessors(node)]
        earliest_start[node] = max(pred_finishes) if pred_finishes else 0.0
        earliest_finish[node] = earliest_start[node] + simulated_durations[node]
    
    # Project finish is max of all finish times
    if earliest_finish:
        return max(earliest_finish.values())
    return 0.0


def compute_critical_path_activities(graph: nx.DiGraph, activities: Dict[str, Activity],
                                    simulated_durations: Dict[str, float]) -> set:
    """Compute which activities are on the critical path for a given simulation"""
    try:
        topo_order = list(nx.topological_sort(graph))
    except nx.NetworkXError:
        return set()
    
    # Calculate earliest and latest times
    earliest_start = {}
    earliest_finish = {}
    latest_start = {}
    latest_finish = {}
    
    # Forward pass: calculate earliest times
    for node in topo_order:
        if node not in simulated_durations:
            continue
        pred_finishes = [earliest_finish.get(pred, 0.0) 
                        for pred in graph.predecessors(node)]
        earliest_start[node] = max(pred_finishes) if pred_finishes else 0.0
        earliest_finish[node] = earliest_start[node] + simulated_durations[node]
    
    # Backward pass: calculate latest times
    project_finish = max(earliest_finish.values()) if earliest_finish else 0.0
    for node in reversed(topo_order):
        if node not in simulated_durations:
            continue
        succ_starts = [latest_start.get(succ, project_finish)
                       for succ in graph.successors(node)]
        latest_finish[node] = min(succ_starts) if succ_starts else project_finish
        latest_start[node] = latest_finish[node] - simulated_durations[node]
    
    # Critical path: activities where ES = LS (or EF = LF)
    critical_activities = set()
    for node in topo_order:
        if node not in simulated_durations:
            continue
        es = earliest_start.get(node, 0.0)
        ls = latest_start.get(node, project_finish)
        # Allow small floating point tolerance
        if abs(es - ls) < 0.01:
            critical_activities.add(node)
    
    return critical_activities


def monte_carlo_forecast(twin: DigitalTwin, num_simulations: int = 10000,
                        uncertainty_params_map: Optional[Dict[str, Dict]] = None) -> Dict:
    """
    Run Monte Carlo simulation to forecast project completion.
    Also computes Criticality Index (CI) for each activity.
    """
    activities = twin.activities
    graph = twin.graph
    
    # Validate that all activities have durations before simulation
    missing_durations = []
    for activity_id, activity in activities.items():
        duration = activity.remaining_duration or activity.planned_duration or activity.baseline_duration
        if duration is None or duration <= 0:
            missing_durations.append(activity_id)
    
    if missing_durations:
        # Use default duration of 1.0 for missing durations (log warning but continue)
        import warnings
        warnings.warn(f"Activities with missing/invalid durations will use default 1.0: {missing_durations[:5]}")
    
    project_durations = []
    criticality_counts = {activity_id: 0 for activity_id in activities.keys()}
    
    for _ in range(num_simulations):
        # Simulate durations for all activities
        simulated_durations = {}
        for activity_id, activity in activities.items():
            # Use forensic modulation if available, otherwise use standard
            uncertainty_params = uncertainty_params_map.get(activity_id) if uncertainty_params_map else None
            durations = simulate_activity_duration(activity, num_simulations=1, uncertainty_params=uncertainty_params)
            simulated_durations[activity_id] = durations[0]
        
        # Compute critical path length (project duration)
        project_duration = compute_critical_path_length(graph, activities, simulated_durations)
        project_durations.append(project_duration)
        
        # Track which activities are on critical path in this simulation
        critical_activities = compute_critical_path_activities(graph, activities, simulated_durations)
        for activity_id in critical_activities:
            if activity_id in criticality_counts:
                criticality_counts[activity_id] += 1
    
    project_durations = np.array(project_durations)
    
    # Calculate percentiles
    p50 = int(np.percentile(project_durations, 50))
    p80 = int(np.percentile(project_durations, 80))
    p90 = int(np.percentile(project_durations, 90))
    p95 = int(np.percentile(project_durations, 95))
    
    # Calculate Criticality Index (CI) for each activity
    # CI = % of simulations where activity is on critical path
    criticality_indices = {}
    for activity_id, count in criticality_counts.items():
        ci = count / num_simulations
        criticality_indices[activity_id] = float(ci)
    
    # Calculate overall project progress from activities
    total_weight = 0.0
    weighted_progress = 0.0
    progress_values = []
    
    for activity in activities.values():
        percent_complete = activity.percent_complete or 0.0
        # Clamp percent_complete to [0, 100] to prevent invalid values
        percent_complete = max(0.0, min(100.0, percent_complete))
        progress_values.append(percent_complete)
        
        duration = activity.planned_duration or activity.baseline_duration or 1.0
        if duration > 0:
            total_weight += duration
            # percent_complete is in 0-100 range, convert to 0-1 for calculation
            weighted_progress += (percent_complete / 100.0) * duration
    
    if total_weight > 0:
        current = weighted_progress / total_weight  # Already in 0-1 range
    elif progress_values:
        # Average of percent_complete values, then convert to 0-1
        current = (sum(progress_values) / len(progress_values)) / 100.0
    else:
        current = 0.0
    
    # Ensure current is in [0, 1] range
    current = max(0.0, min(1.0, current))
    
    # Convert to percentage (0-100) for frontend display
    current_percentage = current * 100.0
    
    return {
        "p50": p50,
        "p80": p80,
        "p90": p90,
        "p95": p95,
        "mean": float(np.mean(project_durations)),
        "std": float(np.std(project_durations)),
        "min": float(np.min(project_durations)),
        "max": float(np.max(project_durations)),
        "current": float(current_percentage),
        "criticality_indices": criticality_indices,  # CI for each activity
        "num_simulations": num_simulations,
        "forensic_modulation_applied": uncertainty_params_map is not None  # Flag to indicate forensic enhancement
    }

