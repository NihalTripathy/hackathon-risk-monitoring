"""
Risk analysis pipeline
"""

from typing import List, Dict, Optional
from datetime import date
from sqlalchemy.orm import Session
from .models import Activity as ActivityModel
from .features import compute_features
from .risk_model import RuleBasedRiskModel
from .db_adapter import get_project_activities
from .config import USE_ML_MODEL, ML_MODEL_PATH, ML_ENSEMBLE_WEIGHT, ML_FALLBACK_TO_RULE_BASED

# Global hybrid model instance (lazy loaded)
_hybrid_model = None
_ml_available = None


def _check_ml_available():
    """Check if ML dependencies are available"""
    global _ml_available
    if _ml_available is None:
        try:
            import joblib
            import sklearn
            _ml_available = True
        except ImportError:
            _ml_available = False
    return _ml_available


def _get_risk_model():
    """Get the appropriate risk model (ML hybrid or rule-based)"""
    global _hybrid_model
    
    if USE_ML_MODEL and _check_ml_available():
        if _hybrid_model is None:
            try:
                from .ml_risk_model import HybridRiskModel
                _hybrid_model = HybridRiskModel(
                    ml_model_path=ML_MODEL_PATH,
                    ml_weight=ML_ENSEMBLE_WEIGHT
                )
            except ImportError:
                # ML dependencies not installed, fallback to rule-based
                return RuleBasedRiskModel()
        return _hybrid_model
    else:
        # Use rule-based model directly
        return RuleBasedRiskModel()


def compute_project_risks(
    project_id: str, 
    db: Optional[Session] = None, 
    activities: Optional[List[ActivityModel]] = None,
    use_ml: Optional[bool] = None,
    reference_date: Optional[date] = None
) -> List[Dict]:
    """
    Compute risk scores for all activities in a project
    OPTIMIZED: Builds digital twin once and reuses for all activities
    
    Args:
        project_id: Project ID
        db: Database session
        activities: Optional pre-loaded activities
        use_ml: Override config to use ML (None = use config setting)
        reference_date: Reference date for date-dependent calculations (defaults to today if None)
                       This allows using CSV date or custom date instead of current date.
    
    Returns:
        List of risk dictionaries with scores and factors
    """
    # Get activities from database if not provided
    if activities is None:
        if db is None:
            return []
        activities = get_project_activities(db, project_id)
    
    if not activities:
        return []
    
    # OPTIMIZATION: Build digital twin once and reuse for all activities
    from .digital_twin import get_or_build_twin
    twin = get_or_build_twin(project_id, activities)
    
    # Layer 1: Forensic Feature Extraction
    from .skill_analyzer import check_skill_overload
    skill_analysis = check_skill_overload(activities, reference_date=reference_date)
    
    # Layer 2: Topology Engine
    from .topology_engine import calculate_topology_metrics
    topology_metrics = calculate_topology_metrics(twin)
    
    # Determine which model to use
    should_use_ml = use_ml if use_ml is not None else USE_ML_MODEL
    model = _get_risk_model() if should_use_ml else RuleBasedRiskModel()
    
    # PER SPEC: Compute all features first for project-wide normalization
    # Include skill_analysis for forensic features
    all_features = []
    for activity in activities:
        features = compute_features(
            activity, 
            project_id, 
            activities=activities, 
            twin=twin, 
            reference_date=reference_date,
            skill_analysis=skill_analysis
        )
        all_features.append(features)
    
    # Layer 3: ML Clustering (for future prediction, not risk score)
    from .risk_clustering import cluster_activities, get_risk_archetype_characteristics
    activity_clusters = cluster_activities(all_features, n_clusters=4)
    
    # Build risk archetype map
    risk_archetypes = {}
    for activity_id, cluster_id in activity_clusters.items():
        risk_archetypes[activity_id] = get_risk_archetype_characteristics(cluster_id)
    
    risks = []
    
    # OPTIMIZATION: Pre-compute rule model if needed (avoid creating multiple instances)
    rule_model = None
    if hasattr(model, 'is_ml_available') and callable(getattr(model, 'is_ml_available', None)):
        rule_model = RuleBasedRiskModel()
    
    # Compute risk scores with project-wide normalization (per spec)
    for i, activity in enumerate(activities):
        features = all_features[i]
        
        # Compute risk score
        # Check if model has predict method that returns tuple (hybrid model)
        if hasattr(model, 'is_ml_available') and callable(getattr(model, 'is_ml_available', None)):
            # Use hybrid model with project-wide normalization
            risk_score, method_used = model.predict(
                features,
                use_ml=should_use_ml,
                fallback_to_rule=ML_FALLBACK_TO_RULE_BASED,
                project_features=all_features
            )
            # Get risk factors from rule-based component (reuse instance)
            if rule_model is None:
                rule_model = RuleBasedRiskModel()
            risk_factors = rule_model.get_risk_factors(features)
            # Add method info
            risk_factors["prediction_method"] = method_used
        else:
            # Use rule-based model with project-wide normalization (per spec)
            risk_score = model.predict(features, project_features=all_features)
            risk_factors = model.get_risk_factors(features)
            risk_factors["prediction_method"] = "rule"
        
        # Get cluster info for this activity (for future use in Monte Carlo)
        cluster_id = activity_clusters.get(activity.activity_id, 0)
        risk_archetype = risk_archetypes.get(activity.activity_id, get_risk_archetype_characteristics(0))
        
        risks.append({
            "activity_id": activity.activity_id,
            "name": activity.name,
            "risk_score": risk_score,  # Base risk score (for UI - current state)
            "risk_factors": risk_factors,  # e.g., {"delay": "high", "critical_path": "medium", "resource": "low", "prediction_method": "ml"}
            "features": features,
            "percent_complete": activity.percent_complete,
            "on_critical_path": activity.on_critical_path,
            # Forensic Intelligence metadata (for Monte Carlo modulation)
            "cluster_id": cluster_id,
            "risk_archetype": risk_archetype,
            "topology_metrics": topology_metrics.get(activity.activity_id, {}),
        })
    
    # Sort by risk score (highest first)
    risks.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return risks

