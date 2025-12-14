"""
Risk mitigation strategies and recommendations
"""

import copy
from typing import Dict, Optional, List
from .models import Activity
from .digital_twin import DigitalTwin, get_or_build_twin
from .mc_forecaster import monte_carlo_forecast
from .risk_pipeline import compute_project_risks


def clone_twin(twin: DigitalTwin) -> DigitalTwin:
    """Create a deep copy of a digital twin"""
    # Create new twin with copied activities
    activities_copy = []
    for activity in twin.activities.values():
        # Create a new Activity with copied values
        activity_dict = activity.model_dump()
        new_activity = Activity(**activity_dict)
        activities_copy.append(new_activity)
    
    return DigitalTwin(activities_copy)


def modify_activity_duration(twin: DigitalTwin, activity_id: str, 
                             new_duration: Optional[float] = None,
                             reduce_risk: bool = False,
                             new_fte: Optional[float] = None,
                             new_cost: Optional[float] = None) -> DigitalTwin:
    """
    Modify an activity in the twin (e.g., reduce duration, risk, add FTE, or change cost).
    Enhanced to properly handle FTE allocation changes and cost modifications.
    """
    if activity_id not in twin.activities:
        raise ValueError(f"Activity {activity_id} not found")
    
    activity = twin.activities[activity_id]
    
    # Create modified activity
    activity_dict = activity.model_dump()
    
    if new_duration is not None:
        activity_dict["planned_duration"] = new_duration
        activity_dict["baseline_duration"] = new_duration
    
    if reduce_risk:
        # Reduce risk probability and impact
        activity_dict["risk_probability"] = activity.risk_probability * 0.5
        activity_dict["risk_delay_impact_days"] = activity.risk_delay_impact_days * 0.5
    
    if new_fte is not None:
        # Update FTE allocation (this affects resource utilization calculations)
        activity_dict["fte_allocation"] = new_fte
        # Note: We don't modify resource_max_fte as that's a resource constraint
    
    if new_cost is not None:
        # Update planned cost (this affects cost performance calculations)
        activity_dict["planned_cost"] = new_cost
    
    modified_activity = Activity(**activity_dict)
    
    # Create new twin with modified activity
    activities_copy = []
    for aid, act in twin.activities.items():
        if aid == activity_id:
            activities_copy.append(modified_activity)
        else:
            activity_dict = act.model_dump()
            activities_copy.append(Activity(**activity_dict))
    
    return DigitalTwin(activities_copy)


def generate_mitigation_actions(activity: Activity) -> List[Dict]:
    """
    Generate candidate mitigation actions for an activity.
    Returns list of action dictionaries with type, parameters, and estimated cost.
    """
    actions = []
    
    current_duration = activity.planned_duration or activity.baseline_duration or 1.0
    current_risk_prob = activity.risk_probability or 0.0
    current_risk_impact = activity.risk_delay_impact_days or 0.0
    current_fte = activity.fte_allocation or 0.0
    
    # Action 1: Reduce duration by X% (crashing)
    for reduction_pct in [10, 20, 30]:
        new_duration = current_duration * (1 - reduction_pct / 100.0)
        actions.append({
            "type": "reduce_duration",
            "description": f"Reduce duration by {reduction_pct}% (crashing)",
            "parameters": {
                "duration_reduction_pct": reduction_pct,
                "new_duration": new_duration
            },
            "estimated_cost_multiplier": 1.0 + (reduction_pct / 100.0) * 0.5,  # 10% reduction = 1.05x cost
            "estimated_ftedays": 0.0  # No FTE change
        })
    
    # Action 2: Add extra FTE
    if current_fte > 0:
        for extra_fte in [0.5, 1.0, 1.5]:
            new_fte = current_fte + extra_fte
            # Estimate duration reduction from adding resources (not always linear)
            duration_reduction = current_duration * (extra_fte / (current_fte + extra_fte)) * 0.7  # 70% efficiency
            actions.append({
                "type": "add_fte",
                "description": f"Add {extra_fte} FTE for {current_duration:.1f} days",
                "parameters": {
                    "extra_fte": extra_fte,
                    "new_fte": new_fte,
                    "estimated_duration_reduction": duration_reduction
                },
                "estimated_cost_multiplier": 1.0 + (extra_fte / current_fte) if current_fte > 0 else 2.0,
                "estimated_ftedays": extra_fte * current_duration
            })
    
    # Action 3: Reduce risk probability and impact
    if current_risk_prob > 0.1:
        for risk_reduction_pct in [25, 50, 75]:
            actions.append({
                "type": "reduce_risk",
                "description": f"Reduce risk probability and impact by {risk_reduction_pct}%",
                "parameters": {
                    "risk_reduction_pct": risk_reduction_pct,
                    "new_probability": current_risk_prob * (1 - risk_reduction_pct / 100.0),
                    "new_impact": current_risk_impact * (1 - risk_reduction_pct / 100.0)
                },
                "estimated_cost_multiplier": 1.0 + (risk_reduction_pct / 100.0) * 0.3,  # Risk mitigation costs
                "estimated_ftedays": 0.0
            })
    
    return actions


def rank_mitigation_actions(actions: List[Dict], baseline_forecast: Dict, 
                           mitigated_forecasts: Dict[str, Dict]) -> List[Dict]:
    """
    Rank mitigation actions by utility score.
    Utility = (improvement in finish date / risk) + (cost / FTE impact)
    """
    ranked = []
    
    for action in actions:
        action_id = action.get("action_id", "")
        if action_id not in mitigated_forecasts:
            continue
        
        mitigated_forecast = mitigated_forecasts[action_id]
        
        # Calculate improvements
        p50_improvement = baseline_forecast["p50"] - mitigated_forecast["p50"]
        p80_improvement = baseline_forecast["p80"] - mitigated_forecast["p80"]
        
        # Round to 1 decimal place for display, but keep precision for calculations
        # Note: P80 improvements may be 0.0 if the worst-case scenario is dominated by other tasks
        # or if the improvement is very small (< 0.1 days) due to simulation variance
        p50_improvement = round(p50_improvement, 1)
        p80_improvement = round(p80_improvement, 1)
        
        # Calculate utility score
        # Higher improvement = better
        # Lower cost = better
        improvement_score = (p80_improvement * 0.7 + p50_improvement * 0.3)  # Weight P80 more
        
        cost_penalty = action.get("estimated_cost_multiplier", 1.0) - 1.0  # 0 = no cost increase
        fte_penalty = action.get("estimated_ftedays", 0.0) * 0.1  # Penalty for FTE days
        
        # Utility = improvement - cost_penalty - fte_penalty
        utility_score = improvement_score - (cost_penalty * 10) - fte_penalty
        
        ranked.append({
            **action,
            "improvement": {
                "p50_improvement": p50_improvement,
                "p80_improvement": p80_improvement,
                "p50_new": mitigated_forecast["p50"],
                "p80_new": mitigated_forecast["p80"]
            },
            "utility_score": utility_score
        })
    
    # Sort by utility score (highest first)
    ranked.sort(key=lambda x: x["utility_score"], reverse=True)
    
    return ranked


def simulate_mitigation(project_id: str, activity_id: str, 
                        new_duration: Optional[float] = None,
                        reduce_risk: bool = False,
                        new_fte: Optional[float] = None,
                        new_cost: Optional[float] = None,
                        activities: Optional[list] = None) -> Dict:
    """Simulate the effect of a mitigation action"""
    if activities is None:
        raise ValueError("Activities must be provided")
    
    original_twin = get_or_build_twin(project_id, activities)
    
    # Get baseline forecast (use 2000 simulations for consistency with API endpoint)
    baseline_forecast = monte_carlo_forecast(original_twin, num_simulations=2000)
    
    # Create modified twin
    modified_twin = modify_activity_duration(original_twin, activity_id, 
                                            new_duration, reduce_risk, new_fte, new_cost)
    
    # Get modified forecast (use 2000 simulations for consistency)
    modified_forecast = monte_carlo_forecast(modified_twin, num_simulations=2000)
    
    # Calculate improvement
    improvement_p50 = baseline_forecast["p50"] - modified_forecast["p50"]
    improvement_p80 = baseline_forecast["p80"] - modified_forecast["p80"]
    
    return {
        "original_forecast": baseline_forecast,
        "new_forecast": modified_forecast,
        "baseline": baseline_forecast,  # Keep for backward compatibility
        "mitigated": modified_forecast,  # Keep for backward compatibility
        "improvement": {
            "p50_improvement": improvement_p50,
            "p80_improvement": improvement_p80,
            "p50_days_saved": improvement_p50,  # Keep for backward compatibility
            "p80_days_saved": improvement_p80,  # Keep for backward compatibility
            "p50_improvement_pct": (improvement_p50 / baseline_forecast["p50"] * 100) if baseline_forecast["p50"] > 0 else 0,
            "p80_improvement_pct": (improvement_p80 / baseline_forecast["p80"] * 100) if baseline_forecast["p80"] > 0 else 0
        },
        "activity_id": activity_id,
        "mitigation_applied": {
            "new_duration": new_duration,
            "risk_reduced": reduce_risk,
            "new_fte": new_fte,
            "new_cost": new_cost
        }
    }


def generate_and_rank_mitigations(project_id: str, activity_id: str,
                                   activities: Optional[list] = None) -> Dict:
    """
    Generate candidate mitigation actions and rank them by utility.
    Returns ranked list of mitigation options with their impact.
    """
    if activities is None:
        raise ValueError("Activities must be provided")
    
    # Find the activity
    activity = None
    for act in activities:
        if act.activity_id == activity_id:
            activity = act
            break
    
    if not activity:
        raise ValueError(f"Activity {activity_id} not found")
    
    # Get baseline forecast (use 2000 simulations for consistency with API endpoint)
    original_twin = get_or_build_twin(project_id, activities)
    baseline_forecast = monte_carlo_forecast(original_twin, num_simulations=2000)
    
    # Generate candidate actions
    actions = generate_mitigation_actions(activity)
    
    # Simulate each action
    mitigated_forecasts = {}
    for i, action in enumerate(actions):
        action_id = f"action_{i}"
        action["action_id"] = action_id
        
        # Apply the mitigation
        params = action["parameters"]
        new_duration = None
        reduce_risk = False
        
        new_duration = None
        reduce_risk = False
        new_fte = None
        
        if action["type"] == "reduce_duration":
            new_duration = params.get("new_duration")
        elif action["type"] == "add_fte":
            # For FTE addition, modify both FTE allocation and duration
            new_fte = params.get("new_fte")
            duration_reduction = params.get("estimated_duration_reduction", 0)
            current_duration = activity.planned_duration or activity.baseline_duration or 1.0
            new_duration = max(0.1, current_duration - duration_reduction)  # Ensure positive duration
        elif action["type"] == "reduce_risk":
            reduce_risk = True
        
        # Simulate
        # Use fewer simulations for ranking (500 instead of 2000) for faster response
        # Ranking doesn't need high precision - we're comparing relative improvements
        modified_twin = modify_activity_duration(original_twin, activity_id, new_duration, reduce_risk, new_fte)
        mitigated_forecast = monte_carlo_forecast(modified_twin, num_simulations=500)
        mitigated_forecasts[action_id] = mitigated_forecast
    
    # Rank actions
    ranked_actions = rank_mitigation_actions(actions, baseline_forecast, mitigated_forecasts)
    
    return {
        "activity_id": activity_id,
        "baseline_forecast": baseline_forecast,
        "ranked_mitigations": ranked_actions,
        "total_options": len(ranked_actions)
    }

