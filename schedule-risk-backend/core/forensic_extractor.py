"""
Forensic Feature Extractor - Layer 1
Extracts forensic intelligence features that will shape future predictions (Monte Carlo)
"""

from typing import Dict, List, Optional
from datetime import date
from .models import Activity
import pandas as pd


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


def calculate_drift_velocity(activity: Activity) -> Dict:
    """
    Drift Velocity Engine: Calculate historical drift rate.
    
    Returns:
        {
            "drift_ratio": float,  # (Planned - Baseline) / Baseline
            "drift_adjusted_remaining": float,  # Remaining * (1 + drift_ratio)
            "mode_shift_factor": float  # For Monte Carlo: how much to shift mode
        }
    """
    baseline = activity.baseline_duration or 0.0
    planned = activity.planned_duration or 0.0
    remaining = activity.remaining_duration or 0.0
    
    # Calculate drift ratio
    if baseline > 0:
        drift_ratio = (planned - baseline) / baseline
    else:
        drift_ratio = 0.0
    
    # Mode shift: if we've drifted 60%, shift future mode by 60%
    mode_shift_factor = drift_ratio
    
    # Calculate drift-adjusted remaining duration
    if remaining > 0:
        drift_adjusted_remaining = remaining * (1.0 + drift_ratio)
    else:
        drift_adjusted_remaining = remaining
    
    return {
        "drift_ratio": drift_ratio,
        "drift_adjusted_remaining": drift_adjusted_remaining,
        "mode_shift_factor": mode_shift_factor
    }


def calculate_cost_performance(activity: Activity) -> Dict:
    """
    Cost Efficiency Engine (CPI): Calculate Cost Performance Index.
    
    Returns:
        {
            "cpi_trend": float,  # Planned_Cost / Actual_Cost_To_Date
            "cost_variance": float,  # Actual - Planned
            "risk_event_probability": float  # CPI < 0.9 increases failure prob
        }
    """
    planned_cost = activity.planned_cost or 0.0
    actual_cost = activity.actual_cost_to_date or 0.0
    
    # Calculate CPI
    if actual_cost > 0:
        cpi_trend = planned_cost / actual_cost
    else:
        cpi_trend = 1.0  # No cost data = assume on track
    
    # Cost variance
    cost_variance = actual_cost - planned_cost
    
    # CPI < 0.9 = over budget = increases risk event probability
    if cpi_trend < 0.9:
        risk_event_prob = (0.9 - cpi_trend) * 2.0  # 0.9 -> 0.0 = 0.0, 0.8 -> 0.0 = 0.2
        risk_event_prob = min(0.3, risk_event_prob)  # Cap at 30%
    else:
        risk_event_prob = 0.0
    
    return {
        "cpi_trend": cpi_trend,
        "cost_variance": cost_variance,
        "risk_event_probability": risk_event_prob
    }


def extract_forensic_features(activity: Activity) -> Dict:
    """
    Extract all forensic features for an activity.
    
    Returns enriched features dict with forensic intelligence.
    """
    # Drift velocity
    drift_data = calculate_drift_velocity(activity)
    
    # Cost performance
    cost_data = calculate_cost_performance(activity)
    
    return {
        "drift_velocity": drift_data,
        "cost_performance": cost_data
    }
