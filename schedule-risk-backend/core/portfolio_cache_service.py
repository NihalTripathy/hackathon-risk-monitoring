"""
Portfolio cache service - stores and retrieves portfolio-level aggregated data
Optimizes portfolio screen loading by avoiding expensive recomputation
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, List
from sqlalchemy import text

from infrastructure.database.models import ProjectMetricsModel, PortfolioCacheModel


def save_project_metrics(
    db: Session,
    project_id: str,
    user_id: int,
    risk_score: float,
    activity_count: int,
    resource_summary: Optional[Dict] = None,
    high_risk_activities_count: int = 0
):
    """
    Save or update project metrics for portfolio aggregation.
    
    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
        risk_score: Average risk score for the project
        activity_count: Number of activities
        resource_summary: Resource allocation summary for this project
        high_risk_activities_count: Count of activities with risk >= 70
    """
    
    try:
        # Check if table exists
        db.execute(text("SELECT 1 FROM project_metrics LIMIT 1"))
    except Exception:
        # Table doesn't exist - skip caching (graceful degradation)
        print("[PORTFOLIO_CACHE] Project metrics table doesn't exist - skipping cache save")
        return
    
    try:
        # Use upsert pattern
        existing = db.query(ProjectMetricsModel).filter(
            ProjectMetricsModel.project_id == project_id
        ).first()
        
        if existing:
            existing.risk_score = risk_score
            existing.activity_count = activity_count
            existing.resource_summary = resource_summary or {}
            existing.high_risk_activities_count = high_risk_activities_count
        else:
            metrics = ProjectMetricsModel(
                project_id=project_id,
                user_id=user_id,
                risk_score=risk_score,
                activity_count=activity_count,
                resource_summary=resource_summary or {},
                high_risk_activities_count=high_risk_activities_count
            )
            db.add(metrics)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[PORTFOLIO_CACHE] Failed to save project metrics: {e}")


def get_project_metrics(db: Session, project_id: str) -> Optional[Dict]:
    """
    Get cached project metrics.
    
    Args:
        db: Database session
        project_id: Project ID
    
    Returns:
        Project metrics dict if exists, None otherwise
    """
    
    try:
        metrics = db.query(ProjectMetricsModel).filter(
            ProjectMetricsModel.project_id == project_id
        ).first()
        
        if metrics:
            return {
                "project_id": metrics.project_id,
                "risk_score": metrics.risk_score,
                "activity_count": metrics.activity_count,
                "resource_summary": metrics.resource_summary or {},
                "high_risk_activities_count": metrics.high_risk_activities_count
            }
    except Exception as e:
        print(f"[PORTFOLIO_CACHE] Project metrics table may not exist yet: {e}")
    
    return None


def get_all_project_metrics(db: Session, user_id: int, project_ids: Optional[List[str]] = None) -> Dict[str, Dict]:
    """
    Get cached metrics for multiple projects.
    
    Args:
        db: Database session
        user_id: User ID
        project_ids: Optional list of project IDs to filter (None = all user projects)
    
    Returns:
        Dict mapping project_id -> metrics dict
    """
    
    try:
        query = db.query(ProjectMetricsModel).filter(
            ProjectMetricsModel.user_id == user_id
        )
        
        if project_ids:
            query = query.filter(ProjectMetricsModel.project_id.in_(project_ids))
        
        metrics_list = query.all()
        
        return {
            m.project_id: {
                "project_id": m.project_id,
                "risk_score": m.risk_score,
                "activity_count": m.activity_count,
                "resource_summary": m.resource_summary or {},
                "high_risk_activities_count": m.high_risk_activities_count
            }
            for m in metrics_list
        }
    except Exception as e:
        print(f"[PORTFOLIO_CACHE] Failed to get project metrics: {e}")
        return {}


def save_portfolio_cache(
    db: Session,
    user_id: int,
    total_projects: int,
    total_activities: int,
    portfolio_risk_score: float,
    projects_at_risk: int,
    high_risk_projects: List[Dict],
    resource_summary: Dict
):
    """
    Save or update portfolio cache for a user.
    
    Args:
        db: Database session
        user_id: User ID
        total_projects: Total number of projects
        total_activities: Total number of activities
        portfolio_risk_score: Average risk score across portfolio
        projects_at_risk: Number of projects with risk >= 50
        high_risk_projects: List of high-risk project objects
        resource_summary: Aggregated resource summary
    """
    
    try:
        # Check if table exists
        db.execute(text("SELECT 1 FROM portfolio_cache LIMIT 1"))
    except Exception:
        # Table doesn't exist - skip caching (graceful degradation)
        print("[PORTFOLIO_CACHE] Portfolio cache table doesn't exist - skipping cache save")
        return
    
    try:
        # Use upsert pattern
        existing = db.query(PortfolioCacheModel).filter(
            PortfolioCacheModel.user_id == user_id
        ).first()
        
        if existing:
            existing.total_projects = total_projects
            existing.total_activities = total_activities
            existing.portfolio_risk_score = portfolio_risk_score
            existing.projects_at_risk = projects_at_risk
            existing.high_risk_projects = high_risk_projects
            existing.resource_summary = resource_summary
        else:
            cache = PortfolioCacheModel(
                user_id=user_id,
                total_projects=total_projects,
                total_activities=total_activities,
                portfolio_risk_score=portfolio_risk_score,
                projects_at_risk=projects_at_risk,
                high_risk_projects=high_risk_projects,
                resource_summary=resource_summary
            )
            db.add(cache)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[PORTFOLIO_CACHE] Failed to save portfolio cache: {e}")


def get_portfolio_cache(db: Session, user_id: int) -> Optional[Dict]:
    """
    Get cached portfolio data for a user.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        Portfolio cache dict if exists, None otherwise
    """
    
    try:
        cache = db.query(PortfolioCacheModel).filter(
            PortfolioCacheModel.user_id == user_id
        ).first()
        
        if cache:
            return {
                "total_projects": cache.total_projects,
                "total_activities": cache.total_activities,
                "portfolio_risk_score": cache.portfolio_risk_score,
                "projects_at_risk": cache.projects_at_risk,
                "high_risk_projects": cache.high_risk_projects or [],
                "resource_summary": cache.resource_summary or {}
            }
    except Exception as e:
        print(f"[PORTFOLIO_CACHE] Portfolio cache table may not exist yet: {e}")
    
    return None


def invalidate_project_metrics(db: Session, project_id: str):
    """
    Invalidate project metrics (called when project is updated).
    
    Args:
        db: Database session
        project_id: Project ID
    """
    if not MODELS_AVAILABLE or ProjectMetricsModel is None:
        return
    
    try:
        db.query(ProjectMetricsModel).filter(
            ProjectMetricsModel.project_id == project_id
        ).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[PORTFOLIO_CACHE] Failed to invalidate project metrics: {e}")


def invalidate_portfolio_cache(db: Session, user_id: int):
    """
    Invalidate portfolio cache for a user (called when any project is updated).
    
    Args:
        db: Database session
        user_id: User ID
    """
    if not MODELS_AVAILABLE or PortfolioCacheModel is None:
        return
    
    try:
        db.query(PortfolioCacheModel).filter(
            PortfolioCacheModel.user_id == user_id
        ).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[PORTFOLIO_CACHE] Failed to invalidate portfolio cache: {e}")


def invalidate_all_project_metrics_for_user(db: Session, user_id: int):
    """
    Invalidate all project metrics for a user (called during portfolio re-analyze).
    
    Args:
        db: Database session
        user_id: User ID
    """
    if not MODELS_AVAILABLE or ProjectMetricsModel is None:
        return
    
    try:
        db.query(ProjectMetricsModel).filter(
            ProjectMetricsModel.user_id == user_id
        ).delete()
        db.commit()
        print(f"[PORTFOLIO_CACHE] Invalidated all project metrics for user {user_id}")
    except Exception as e:
        db.rollback()
        print(f"[PORTFOLIO_CACHE] Failed to invalidate project metrics for user {user_id}: {e}")
