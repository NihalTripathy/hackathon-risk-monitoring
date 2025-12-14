"""
Forensic Forecast - Integration of Forensic Intelligence with Monte Carlo
This module provides the complete forecast pipeline with forensic modulation
"""

from typing import Dict, List, Optional
from datetime import date
from .digital_twin import DigitalTwin, get_or_build_twin
from .mc_forecaster import monte_carlo_forecast
from .uncertainty_modulator import modulate_uncertainty
from .risk_clustering import get_risk_archetype_characteristics
from .models import Activity as ActivityModel


def compute_forensic_forecast(
    project_id: str,
    activities: List[ActivityModel],
    enriched_features: Dict[str, Dict],
    risk_archetypes: Dict[str, Dict],
    topology_metrics: Dict[str, Dict],
    skill_analysis: Dict,
    num_simulations: int = 10000
) -> Dict:
    """
    Compute Monte Carlo forecast with forensic intelligence modulation.
    
    This is the complete Layer 4 + Layer 5 integration:
    - Uses Uncertainty Modulator to shape distributions
    - Runs Monte Carlo with modulated parameters
    - Returns forecast with forensic enhancement flag
    
    Args:
        project_id: Project identifier
        activities: List of activities
        enriched_features: Dict[activity_id, features] from compute_features()
        risk_archetypes: Dict[activity_id, archetype_characteristics] from clustering
        topology_metrics: Dict[activity_id, topology_metrics] from topology engine
        skill_analysis: Skill analysis results from skill_analyzer
        num_simulations: Number of Monte Carlo simulations
    
    Returns:
        Forecast dict with P50, P80, P90, P95 and forensic_modulation_applied flag
    """
    # Build digital twin
    twin = get_or_build_twin(project_id, activities)
    
    # Build uncertainty parameters map for all activities
    uncertainty_params_map = {}
    
    for activity in activities:
        activity_id = activity.activity_id
        features = enriched_features.get(activity_id, {})
        archetype = risk_archetypes.get(activity_id, get_risk_archetype_characteristics(0))
        topology = topology_metrics.get(activity_id, {})
        
        # Modulate uncertainty for this activity
        uncertainty_params = modulate_uncertainty(
            activity,
            features,
            archetype,
            topology,
            skill_analysis
        )
        
        uncertainty_params_map[activity_id] = uncertainty_params
    
    # Run Monte Carlo with forensic modulation
    forecast = monte_carlo_forecast(
        twin,
        num_simulations=num_simulations,
        uncertainty_params_map=uncertainty_params_map
    )
    
    return forecast
