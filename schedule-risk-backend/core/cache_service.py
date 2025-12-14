"""
Cache service layer - handles caching of computed results (forecast, risks, anomalies)
This dramatically improves response times by avoiding expensive recomputation.
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any
from infrastructure.database.models import ForecastCacheModel, RisksCacheModel, AnomaliesCacheModel
from sqlalchemy import text


def get_forecast_cache(db: Session, project_id: str, current_activity_count: int, current_data_hash: Optional[str] = None) -> Optional[Dict]:
    """
    Get cached forecast for a project if it exists and is still valid.
    Automatically invalidates cache if logic version or data hash has changed.
    
    Args:
        db: Database session
        project_id: Project ID
        current_activity_count: Current number of activities (for cache invalidation)
        current_data_hash: Current data hash (optional, computed if not provided)
    
    Returns:
        Forecast dict if cache exists and is valid, None otherwise
    """
    try:
        cache = db.query(ForecastCacheModel).filter(
            ForecastCacheModel.project_id == project_id
        ).first()
        
        if not cache:
            return None
        
        # Check activity count
        if cache.activity_count != current_activity_count:
            return None
        
        # Check data hash (automatic invalidation on CSV data changes)
        if current_data_hash is None:
            from .db_service import get_activities
            from .logic_version import compute_data_hash
            activities = get_activities(db, project_id)
            if activities:
                current_data_hash = compute_data_hash(activities)
        
        if current_data_hash and cache.data_hash and cache.data_hash != current_data_hash:
            print(f"[CACHE] Invalidating forecast cache for {project_id}: Data hash changed (data content modified)")
            db.query(ForecastCacheModel).filter(
                ForecastCacheModel.project_id == project_id
            ).delete()
            db.commit()
            return None
        
        # Cache is valid
        return {
            "p50": cache.p50,
            "p80": cache.p80,
            "p90": cache.p90,
            "p95": cache.p95,
            "current": cache.current,
            "criticality_indices": cache.criticality_indices or {}
        }
    except Exception as e:
        # If table doesn't exist yet or schema mismatch, rollback and return None (graceful degradation)
        db.rollback()
        print(f"[CACHE] Forecast cache table may not exist yet or schema mismatch: {e}")
    
    return None


def save_forecast_cache(db: Session, project_id: str, forecast: Dict, activity_count: int, data_hash: Optional[str] = None):
    """
    Save forecast to cache.
    
    Args:
        db: Database session
        project_id: Project ID
        forecast: Forecast dict with p50, p80, p90, p95, current, criticality_indices
        activity_count: Number of activities when computed (for invalidation)
        data_hash: Hash of activity data when computed (optional, computed if not provided)
    """
    try:
        # Check if table exists
        db.execute(text("SELECT 1 FROM forecast_cache LIMIT 1"))
    except Exception:
        # Table doesn't exist - skip caching (graceful degradation)
        print("[CACHE] Forecast cache table doesn't exist - skipping cache save")
        return
    
    # Get data hash if not provided
    if data_hash is None:
        from .logic_version import compute_data_hash
        from .db_service import get_activities
        activities = get_activities(db, project_id)
        if activities:
            data_hash = compute_data_hash(activities)
    
    try:
        # Use upsert pattern (update if exists, insert if not)
        existing = db.query(ForecastCacheModel).filter(
            ForecastCacheModel.project_id == project_id
        ).first()
        
        if existing:
            existing.p50 = forecast.get("p50")
            existing.p80 = forecast.get("p80")
            existing.p90 = forecast.get("p90")
            existing.p95 = forecast.get("p95")
            existing.current = forecast.get("current", 0)
            existing.criticality_indices = forecast.get("criticality_indices", {})
            existing.activity_count = activity_count
            existing.data_hash = data_hash
        else:
            cache = ForecastCacheModel(
                project_id=project_id,
                p50=forecast.get("p50"),
                p80=forecast.get("p80"),
                p90=forecast.get("p90"),
                p95=forecast.get("p95"),
                current=forecast.get("current", 0),
                criticality_indices=forecast.get("criticality_indices", {}),
                activity_count=activity_count,
                data_hash=data_hash
            )
            db.add(cache)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[CACHE] Failed to save forecast cache: {e}")


def get_risks_cache(db: Session, project_id: str, current_activity_count: int, current_data_hash: Optional[str] = None) -> Optional[Dict]:
    """
    Get cached risks for a project if it exists and is still valid.
    Automatically invalidates cache if logic version, data hash, or USE_ML_MODEL setting has changed.
    
    Args:
        db: Database session
        project_id: Project ID
        current_activity_count: Current number of activities (for cache invalidation)
        current_data_hash: Current data hash (optional, computed if not provided)
    
    Returns:
        Risks dict with total_risks and top_risks if cache exists and is valid, None otherwise
    """
    try:
        cache = db.query(RisksCacheModel).filter(
            RisksCacheModel.project_id == project_id
        ).first()
        
        if not cache:
            return None
        
        # Check activity count
        if cache.activity_count != current_activity_count:
            return None
        
        # Check data hash (automatic invalidation on CSV data changes)
        if current_data_hash is None:
            from .db_service import get_activities
            from .logic_version import compute_data_hash
            activities = get_activities(db, project_id)
            if activities:
                current_data_hash = compute_data_hash(activities)
        
        if current_data_hash and cache.data_hash and cache.data_hash != current_data_hash:
            print(f"[CACHE] Invalidating risks cache for {project_id}: Data hash changed (data content modified)")
            db.query(RisksCacheModel).filter(
                RisksCacheModel.project_id == project_id
            ).delete()
            db.commit()
            return None
        
        # Check if model type matches current USE_ML_MODEL setting
        from .config import USE_ML_MODEL
        
        # Extract prediction_method from cached risks to check model type
        cached_top_risks = cache.top_risks or []
        if cached_top_risks and isinstance(cached_top_risks, list) and len(cached_top_risks) > 0:
            # Get prediction_method from first risk (all should be same)
            first_risk = cached_top_risks[0]
            if isinstance(first_risk, dict):
                risk_factors = first_risk.get("risk_factors", {})
                if isinstance(risk_factors, dict):
                    cached_method = risk_factors.get("prediction_method", "rule")
                    
                    # Determine expected method based on current config
                    # If USE_ML_MODEL=false, should be "rule"
                    # If USE_ML_MODEL=true, should be "ml", "ensemble", or "ml_fallback"
                    if USE_ML_MODEL:
                        # ML enabled - cache should have ML-based method
                        if cached_method == "rule":
                            # Cache was computed with rule-based but now ML is enabled - invalidate
                            print(f"[CACHE] Invalidating risks cache for {project_id}: ML model enabled but cache has rule-based results")
                            db.query(RisksCacheModel).filter(
                                RisksCacheModel.project_id == project_id
                            ).delete()
                            db.commit()
                            return None
                    else:
                        # Rule-based enabled - cache should have rule-based method
                        if cached_method in ["ml", "ensemble", "ml_fallback"]:
                            # Cache was computed with ML but now rule-based is enabled - invalidate
                            print(f"[CACHE] Invalidating risks cache for {project_id}: Rule-based model enabled but cache has ML results")
                            db.query(RisksCacheModel).filter(
                                RisksCacheModel.project_id == project_id
                            ).delete()
                            db.commit()
                            return None
        
        # Cache is valid - return it
        return {
            "total_risks": cache.total_risks,
            "top_risks": cached_top_risks
        }
    except Exception as e:
        # If table doesn't exist yet, return None (graceful degradation)
        print(f"[CACHE] Risks cache table may not exist yet: {e}")
    
    return None


def save_risks_cache(db: Session, project_id: str, risks_data: Dict, activity_count: int, data_hash: Optional[str] = None):
    """
    Save risks to cache.
    
    Args:
        db: Database session
        project_id: Project ID
        risks_data: Risks dict with total_risks and top_risks
        activity_count: Number of activities when computed (for invalidation)
        data_hash: Hash of activity data when computed (optional, computed if not provided)
    """
    try:
        # Check if table exists
        db.execute(text("SELECT 1 FROM risks_cache LIMIT 1"))
    except Exception:
        # Table doesn't exist - skip caching (graceful degradation)
        print("[CACHE] Risks cache table doesn't exist - skipping cache save")
        return
    
    # Get data hash if not provided
    if data_hash is None:
        from .logic_version import compute_data_hash
        from .db_service import get_activities
        activities = get_activities(db, project_id)
        if activities:
            data_hash = compute_data_hash(activities)
    
    try:
        # Use upsert pattern
        existing = db.query(RisksCacheModel).filter(
            RisksCacheModel.project_id == project_id
        ).first()
        
        if existing:
            existing.total_risks = risks_data.get("total_risks", 0)
            existing.top_risks = risks_data.get("top_risks", [])
            existing.activity_count = activity_count
            existing.data_hash = data_hash
        else:
            cache = RisksCacheModel(
                project_id=project_id,
                total_risks=risks_data.get("total_risks", 0),
                top_risks=risks_data.get("top_risks", []),
                activity_count=activity_count,
                data_hash=data_hash
            )
            db.add(cache)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[CACHE] Failed to save risks cache: {e}")


def get_anomalies_cache(db: Session, project_id: str, current_activity_count: int, current_data_hash: Optional[str] = None) -> Optional[Dict]:
    """
    Get cached anomalies for a project if it exists and is still valid.
    Automatically invalidates cache if logic version or data hash has changed.
    
    Args:
        db: Database session
        project_id: Project ID
        current_activity_count: Current number of activities (for cache invalidation)
        current_data_hash: Current data hash (optional, computed if not provided)
    
    Returns:
        Anomalies dict if cache exists and is valid, None otherwise
    """
    try:
        cache = db.query(AnomaliesCacheModel).filter(
            AnomaliesCacheModel.project_id == project_id
        ).first()
        
        if not cache:
            return None
        
        # Check activity count
        if cache.activity_count != current_activity_count:
            return None
        
        # Check data hash (automatic invalidation on CSV data changes)
        if current_data_hash is None:
            from .db_service import get_activities
            from .logic_version import compute_data_hash
            activities = get_activities(db, project_id)
            if activities:
                current_data_hash = compute_data_hash(activities)
        
        if current_data_hash and cache.data_hash and cache.data_hash != current_data_hash:
            print(f"[CACHE] Invalidating anomalies cache for {project_id}: Data hash changed (data content modified)")
            db.query(AnomaliesCacheModel).filter(
                AnomaliesCacheModel.project_id == project_id
            ).delete()
            db.commit()
            return None
        
        # Cache is valid
        return {
            "zombie_tasks": cache.zombie_tasks or [],
            "black_holes": cache.black_holes or [],
            "total_anomalies": cache.total_anomalies
        }
    except Exception as e:
        # If table doesn't exist yet, return None (graceful degradation)
        print(f"[CACHE] Anomalies cache table may not exist yet: {e}")
    
    return None


def save_anomalies_cache(db: Session, project_id: str, anomalies: Dict, activity_count: int, data_hash: Optional[str] = None):
    """
    Save anomalies to cache.
    
    Args:
        db: Database session
        project_id: Project ID
        anomalies: Anomalies dict with zombie_tasks, black_holes, total_anomalies
        activity_count: Number of activities when computed (for invalidation)
        data_hash: Hash of activity data when computed (optional, computed if not provided)
    """
    try:
        # Check if table exists
        db.execute(text("SELECT 1 FROM anomalies_cache LIMIT 1"))
    except Exception:
        # Table doesn't exist - skip caching (graceful degradation)
        print("[CACHE] Anomalies cache table doesn't exist - skipping cache save")
        return
    
    # Get data hash if not provided
    if data_hash is None:
        from .logic_version import compute_data_hash
        from .db_service import get_activities
        activities = get_activities(db, project_id)
        if activities:
            data_hash = compute_data_hash(activities)
    
    try:
        # Use upsert pattern
        existing = db.query(AnomaliesCacheModel).filter(
            AnomaliesCacheModel.project_id == project_id
        ).first()
        
        if existing:
            existing.zombie_tasks = anomalies.get("zombie_tasks", [])
            existing.black_holes = anomalies.get("black_holes", [])
            existing.total_anomalies = anomalies.get("total_anomalies", 0)
            existing.activity_count = activity_count
            existing.data_hash = data_hash
        else:
            cache = AnomaliesCacheModel(
                project_id=project_id,
                zombie_tasks=anomalies.get("zombie_tasks", []),
                black_holes=anomalies.get("black_holes", []),
                total_anomalies=anomalies.get("total_anomalies", 0),
                activity_count=activity_count,
                data_hash=data_hash
            )
            db.add(cache)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[CACHE] Failed to save anomalies cache: {e}")


def invalidate_project_cache(db: Session, project_id: str):
    """
    Invalidate all cache for a project (called when activities are updated).
    
    Args:
        db: Database session
        project_id: Project ID
    """
    try:
        # Delete forecast cache
        db.query(ForecastCacheModel).filter(
            ForecastCacheModel.project_id == project_id
        ).delete()
        
        # Delete risks cache
        db.query(RisksCacheModel).filter(
            RisksCacheModel.project_id == project_id
        ).delete()
        
        # Delete anomalies cache
        db.query(AnomaliesCacheModel).filter(
            AnomaliesCacheModel.project_id == project_id
        ).delete()
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[CACHE] Failed to invalidate cache (tables may not exist): {e}")

