"""
Forecasting API endpoints
"""

import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.digital_twin import get_or_build_twin
from core.mc_forecaster import monte_carlo_forecast
from core.database import get_db
from core.db_service import get_activities, log_event_db
from core.project_auth import verify_project_ownership
from core.auth_dependencies import get_current_user
from core.explanation_service import get_explanation_service
from core.forensic_forecast import compute_forensic_forecast
from core.risk_pipeline import compute_project_risks
from core.skill_analyzer import check_skill_overload
from core.topology_engine import calculate_topology_metrics
from core.risk_clustering import cluster_activities, get_risk_archetype_characteristics
# Date selection feature removed - always use today's date
from api.auth import UserResponse

router = APIRouter()


@router.get("/projects/{project_id}/forecast")
def get_forecast(
    project_id: str, 
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    force_recompute: bool = False,
    include_explanation: bool = True
):
    """
    Get Monte Carlo forecast for project completion - requires authentication and ownership
    
    Uses cache if available to provide instant responses. Set force_recompute=true to bypass cache.
    """
    start_time = time.time()
    
    verify_project_ownership(db, project_id, current_user)
    auth_time = time.time()
    
    # Get activities from database
    activities = get_activities(db, project_id)
    activity_count = len(activities) if activities else 0
    db_time = time.time()
    
    # Check cache first (unless force_recompute is True)
    if not force_recompute:
        from core.cache_service import get_forecast_cache
        cached_forecast = get_forecast_cache(db, project_id, activity_count)
        if cached_forecast:
            cache_time = time.time()
            total_time = cache_time - start_time
            print(f"[CACHE] Forecast served from cache in {total_time:.3f}s")
            return cached_forecast
    
    # Cache miss or force recompute - compute forecast
    twin = get_or_build_twin(project_id, activities)
    twin_time = time.time()
    
    # Use fewer simulations for faster API response (2000 instead of 10000)
    # This provides good accuracy while keeping response time under 2-5 seconds
    forecast = monte_carlo_forecast(twin, num_simulations=2000)
    forecast_time = time.time()
    
    # Add cycle warning if present (for PMO visibility)
    if twin.has_cycles and twin.cycle_warning:
        forecast["warnings"] = forecast.get("warnings", [])
        forecast["warnings"].append(twin.cycle_warning)
    
    # Save to cache for future requests
    from core.cache_service import save_forecast_cache
    save_forecast_cache(db, project_id, forecast, activity_count)
    cache_save_time = time.time()
    
    # Log the forecast event to database
    log_event_db(
        db,
        project_id,
        "forecast",
        {
            "p50": forecast["p50"],
            "p80": forecast["p80"],
            "from_cache": False
        }
    )
    
    # Add plain-language explanation if requested (Priority 2: UX Enhancement)
    if include_explanation:
        try:
            from infrastructure.database.models import ProjectModel
            project = db.query(ProjectModel).filter(ProjectModel.project_id == project_id).first()
            baseline_days = None
            if project and activities:
                # Calculate baseline project duration (sum of baseline durations on critical path)
                # This is a simplified calculation - in production, use actual baseline finish date
                baseline_days = sum(
                    (act.baseline_duration or act.planned_duration or 0) 
                    for act in activities if act.on_critical_path
                )
            
            explanation_service = get_explanation_service()
            explanation = explanation_service.explain_forecast(
                forecast,
                baseline_days=baseline_days,
                project_context={"high_risk_activities": len([a for a in activities if a.on_critical_path]) if activities else 0}
            )
            forecast["explanation"] = explanation
        except Exception as e:
            print(f"[Forecast] Failed to generate explanation: {e}")
            # Don't fail the request if explanation fails
    
    total_time = time.time() - start_time
    # Log performance metrics (can be removed in production if not needed)
    if total_time > 1.0:  # Only log if slow
        print(f"[PERF] Forecast endpoint timing - Total: {total_time:.2f}s, Auth: {auth_time-start_time:.2f}s, DB: {db_time-auth_time:.2f}s, Twin: {twin_time-db_time:.2f}s, Forecast: {forecast_time-twin_time:.2f}s, Cache: {cache_save_time-forecast_time:.2f}s")
    
    return forecast


@router.get("/projects/{project_id}/forecast/forensic")
def get_forensic_forecast(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    force_recompute: bool = False,
    num_simulations: int = 2000,
    include_explanation: bool = True
):
    """
    Get Forensic Intelligence-enhanced Monte Carlo forecast for project completion.
    
    This endpoint uses the complete Forensic Intelligence architecture:
    - Layer 1: Drift Velocity, Skill Constraints, Cost Efficiency (CPI)
    - Layer 2: Topology Engine (Centrality metrics)
    - Layer 3: ML Clustering (Risk Archetypes)
    - Layer 4: Uncertainty Modulator (Physics-based distribution shaping)
    - Layer 5: Enhanced Monte Carlo (Modulated distributions)
    
    Key Principle: Rule Score (current state) and Forensic Intelligence (future prediction)
    are separated to avoid double counting. Forensic features modulate the simulation
    physics, not the risk score.
    
    Returns:
        {
            "p50": int,  # Median forecast (50th percentile)
            "p80": int,  # 80th percentile forecast
            "p90": int,  # 90th percentile forecast
            "p95": int,  # 95th percentile forecast
            "forensic_modulation_applied": bool,  # Always true for this endpoint
            "forensic_insights": {
                "drift_activities": int,  # Count of activities with drift
                "skill_bottlenecks": int,  # Count of skill bottlenecks
                "high_risk_clusters": int,  # Count of activities in high-risk clusters
                "bridge_nodes": int  # Count of high-centrality bridge nodes
            },
            "explanation": str  # Optional: Human-readable explanation
        }
    """
    start_time = time.time()
    
    verify_project_ownership(db, project_id, current_user)
    auth_time = time.time()
    
    # Get activities from database
    activities = get_activities(db, project_id)
    activity_count = len(activities) if activities else 0
    db_time = time.time()
    
    if not activities:
        raise HTTPException(status_code=404, detail="Project not found or has no activities")
    
    # Always use today's date (date selection feature removed)
    reference_date = None
    
    # Check cache first (unless force_recompute is True)
    # Cache key includes 'forensic' to differentiate from standard forecast
    if not force_recompute:
        from core.cache_service import get_forecast_cache
        cached_forecast = get_forecast_cache(db, project_id, activity_count)
        if cached_forecast and cached_forecast.get("forensic_modulation_applied"):
            cache_time = time.time()
            total_time = cache_time - start_time
            print(f"[CACHE] Forensic forecast served from cache in {total_time:.3f}s")
            return cached_forecast
    
    # Build digital twin
    twin = get_or_build_twin(project_id, activities)
    twin_time = time.time()
    
    # Layer 1: Forensic Feature Extraction + Skill Analysis
    skill_analysis = check_skill_overload(activities, reference_date=reference_date)
    
    # Layer 2: Topology Engine
    topology_metrics = calculate_topology_metrics(twin)
    
    # Compute enriched features (includes forensic features)
    # Note: We need to compute features to get enriched_features for forensic forecast
    # But we don't need to compute risk scores here (that's separate)
    from core.features import compute_features
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
    
    # Layer 3: ML Clustering
    activity_clusters = cluster_activities(all_features, n_clusters=4)
    
    # Build risk archetype map
    risk_archetypes = {}
    for activity_id, cluster_id in activity_clusters.items():
        risk_archetypes[activity_id] = get_risk_archetype_characteristics(cluster_id)
    
    # Build enriched features map
    enriched_features = {f["activity_id"]: f for f in all_features}
    
    # Layer 4+5: Compute Forensic Forecast
    forecast = compute_forensic_forecast(
        project_id=project_id,
        activities=activities,
        enriched_features=enriched_features,
        risk_archetypes=risk_archetypes,
        topology_metrics=topology_metrics,
        skill_analysis=skill_analysis,
        num_simulations=num_simulations
    )
    forecast_time = time.time()
    
    # Add forensic insights summary
    drift_count = sum(
        1 for f in all_features
        if isinstance(f.get("drift_velocity"), dict) and f["drift_velocity"].get("drift_ratio", 0) > 0.1
    )
    skill_bottleneck_count = len(skill_analysis.get("skill_bottlenecks", []))
    high_risk_cluster_count = sum(
        1 for cluster_id in activity_clusters.values() if cluster_id >= 2
    )
    bridge_node_count = sum(
        1 for metrics in topology_metrics.values()
        if metrics.get("betweenness_centrality", 0) > 0.5
    )
    
    forecast["forensic_insights"] = {
        "drift_activities": drift_count,
        "skill_bottlenecks": skill_bottleneck_count,
        "high_risk_clusters": high_risk_cluster_count,
        "bridge_nodes": bridge_node_count
    }
    
    # Add cycle warning if present
    if twin.has_cycles and twin.cycle_warning:
        forecast["warnings"] = forecast.get("warnings", [])
        forecast["warnings"].append(twin.cycle_warning)
    
    # Save to cache
    from core.cache_service import save_forecast_cache
    save_forecast_cache(db, project_id, forecast, activity_count)
    cache_save_time = time.time()
    
    # Log the forecast event
    log_event_db(
        db,
        project_id,
        "forensic_forecast",
        {
            "p50": forecast["p50"],
            "p80": forecast["p80"],
            "forensic_modulation_applied": True,
            "from_cache": False
        }
    )
    
    # Add explanation if requested
    if include_explanation:
        try:
            from infrastructure.database.models import ProjectModel
            project = db.query(ProjectModel).filter(ProjectModel.project_id == project_id).first()
            baseline_days = None
            if project and activities:
                baseline_days = sum(
                    (act.baseline_duration or act.planned_duration or 0)
                    for act in activities if act.on_critical_path
                )
            
            explanation_service = get_explanation_service()
            explanation = explanation_service.explain_forecast(
                forecast,
                baseline_days=baseline_days,
                project_context={
                    "high_risk_activities": len([a for a in activities if a.on_critical_path]) if activities else 0,
                    "forensic_insights": forecast["forensic_insights"]
                }
            )
            forecast["explanation"] = explanation
        except Exception as e:
            print(f"[Forensic Forecast] Failed to generate explanation: {e}")
            # Don't fail the request if explanation fails
    
    total_time = time.time() - start_time
    if total_time > 1.0:
        print(f"[PERF] Forensic forecast endpoint timing - Total: {total_time:.2f}s, Auth: {auth_time-start_time:.2f}s, DB: {db_time-auth_time:.2f}s, Twin: {twin_time-db_time:.2f}s, Forecast: {forecast_time-twin_time:.2f}s, Cache: {cache_save_time-forecast_time:.2f}s")
    
    return forecast

