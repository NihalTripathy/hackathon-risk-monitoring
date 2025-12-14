"""
Uncertainty Modulator - Layer 4
Combines forensic intelligence to modulate Monte Carlo distributions
"""

from typing import Dict
from .models import Activity


def modulate_uncertainty(
    activity: Activity,
    enriched_features: Dict,
    risk_archetype: Dict,
    topology_metrics: Dict,
    skill_analysis: Dict
) -> Dict:
    """
    Modulate Monte Carlo parameters based on forensic intelligence.
    
    This is where the magic happens - we change the physics of the simulation.
    
    Key Principle:
    - Drift → Shifts mode (most likely duration) to the right
    - Skill Bottleneck → Widens variance (uncertainty)
    - Topology (Centrality) → Widens variance (bridge nodes)
    - High Risk Cluster → All three effects (mode shift, variance, failure prob)
    - CPI → Increases failure probability
    
    Args:
        activity: Activity to modulate
        enriched_features: Features dict with forensic data
        risk_archetype: Cluster archetype characteristics
        topology_metrics: Topology metrics for this activity
        skill_analysis: Skill analysis results
    
    Returns:
        {
            "mode_shift_factor": float,      # How much to shift the mode (most likely duration)
            "variance_multiplier": float,     # How much to widen the distribution
            "failure_probability": float,     # Probability of risk event triggering
            "base_duration": float           # Starting duration for simulation
        }
    """
    activity_id = activity.activity_id
    
    # Start with base duration
    base_duration = activity.remaining_duration or activity.planned_duration or activity.baseline_duration or 1.0
    if base_duration <= 0:
        base_duration = 1.0
    
    # 1. DRIFT → Shifts Mode to the Right
    drift_data = enriched_features.get("drift_velocity", {})
    if isinstance(drift_data, dict):
        drift_mode_shift = drift_data.get("mode_shift_factor", 0.0)
    else:
        drift_mode_shift = 0.0
    
    # 2. SKILL BOTTLENECK → Widens Variance
    variance_increase_map = skill_analysis.get("variance_increase_map", {})
    skill_variance = variance_increase_map.get(activity_id, 1.0)
    
    # 3. TOPOLOGY → Widens Variance (bridge nodes are uncertain)
    activity_topology = topology_metrics.get(activity_id, {})
    topology_variance = activity_topology.get("variance_multiplier", 1.0)
    
    # 4. CLUSTER ARCHETYPE → All three effects
    archetype_mode_shift = risk_archetype.get("mode_shift_factor", 0.0)
    archetype_variance = risk_archetype.get("variance_multiplier", 1.0)
    archetype_failure_prob = risk_archetype.get("failure_probability", 0.0)
    
    # 5. CPI → Increases Failure Probability
    cpi_data = enriched_features.get("cost_performance", {})
    if isinstance(cpi_data, dict):
        cpi_failure_prob = cpi_data.get("risk_event_probability", 0.0)
    else:
        cpi_failure_prob = 0.0
    
    # COMBINE ALL EFFECTS
    
    # Mode shift: Additive (drift + archetype)
    total_mode_shift = drift_mode_shift + archetype_mode_shift
    
    # Variance: Multiplicative (skill * topology * archetype)
    total_variance_multiplier = skill_variance * topology_variance * archetype_variance
    
    # Failure probability: Maximum (archetype or CPI, whichever is higher)
    total_failure_prob = max(archetype_failure_prob, cpi_failure_prob)
    
    return {
        "mode_shift_factor": total_mode_shift,
        "variance_multiplier": total_variance_multiplier,
        "failure_probability": total_failure_prob,
        "base_duration": base_duration
    }
