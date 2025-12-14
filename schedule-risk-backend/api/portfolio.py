"""
Portfolio-level analysis API endpoints
Provides enterprise-level capabilities for managing multiple projects
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from core.auth_dependencies import get_current_user
from core.portfolio_service import (
    get_portfolio_summary,
    get_portfolio_risks,
    get_cross_project_dependencies,
    get_portfolio_resource_allocation
)
from core.portfolio_cache_service import (
    invalidate_portfolio_cache,
    invalidate_all_project_metrics_for_user
)
from core.db_service import get_all_projects
from core.cache_service import invalidate_project_cache
from api.auth import UserResponse
from api.projects import _compute_project_analytics_background

router = APIRouter()


@router.get("/portfolio/summary")
def portfolio_summary(
    project_ids: Optional[str] = Query(None, description="Comma-separated list of project IDs (optional, defaults to all user projects)"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get portfolio-level summary across multiple projects
    
    Returns:
    - Total projects and activities
    - Portfolio risk score (aggregated)
    - Projects at risk
    - Resource allocation summary
    """
    # Parse project IDs if provided
    project_id_list = None
    if project_ids:
        project_id_list = [pid.strip() for pid in project_ids.split(",") if pid.strip()]
    
    try:
        summary = get_portfolio_summary(
            db=db,
            user_id=current_user.id,
            project_ids=project_id_list
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating portfolio summary: {str(e)}")


@router.get("/portfolio/risks")
def portfolio_risks(
    project_ids: Optional[str] = Query(None, description="Comma-separated list of project IDs (optional)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of top risks to return"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get top risks across portfolio (aggregated from all projects)
    
    Returns the highest-risk activities across all projects in the portfolio.
    """
    # Parse project IDs if provided
    project_id_list = None
    if project_ids:
        project_id_list = [pid.strip() for pid in project_ids.split(",") if pid.strip()]
    
    try:
        risks = get_portfolio_risks(
            db=db,
            user_id=current_user.id,
            project_ids=project_id_list,
            limit=limit
        )
        return risks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio risks: {str(e)}")


@router.get("/portfolio/dependencies")
def portfolio_dependencies(
    project_ids: Optional[str] = Query(None, description="Comma-separated list of project IDs (optional)"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Analyze cross-project dependencies
    
    Identifies potential dependencies between projects based on activity relationships.
    Note: Full cross-project dependency tracking requires explicit dependency definitions.
    """
    # Parse project IDs if provided
    project_id_list = None
    if project_ids:
        project_id_list = [pid.strip() for pid in project_ids.split(",") if pid.strip()]
    
    try:
        dependencies = get_cross_project_dependencies(
            db=db,
            user_id=current_user.id,
            project_ids=project_id_list
        )
        return dependencies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing dependencies: {str(e)}")


@router.get("/portfolio/resources")
def portfolio_resources(
    project_ids: Optional[str] = Query(None, description="Comma-separated list of project IDs (optional)"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get resource allocation across portfolio
    
    Shows how resources are allocated across multiple projects, including:
    - Total FTE allocation per resource
    - Utilization percentages
    - Overallocated resources
    - Projects using each resource
    """
    # Parse project IDs if provided
    project_id_list = None
    if project_ids:
        project_id_list = [pid.strip() for pid in project_ids.split(",") if pid.strip()]
    
    try:
        resources = get_portfolio_resource_allocation(
            db=db,
            user_id=current_user.id,
            project_ids=project_id_list
        )
        return resources
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting resource allocation: {str(e)}")


@router.post("/portfolio/re-analyze")
async def re_analyze_portfolio(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Re-analyze entire portfolio - recomputes all project metrics and portfolio cache.
    
    This endpoint:
    - Invalidates portfolio cache
    - Invalidates all project metrics for the user
    - Invalidates all project caches (forecast, risks, anomalies)
    - Triggers re-analysis for all user projects in the background
    - Updates portfolio cache when complete
    
    Useful when:
    - Backend logic/algorithms have been updated
    - You want to force recalculation of all projects
    - Portfolio data seems stale or incorrect
    
    Returns immediately with status. Re-analysis happens in background.
    """
    try:
        # Get all user projects
        projects = get_all_projects(db, user_id=current_user.id, limit=1000)
        project_ids = [p["project_id"] for p in projects]
        
        if not project_ids:
            return {
                "status": "no_projects",
                "message": "No projects found to re-analyze",
                "projects_analyzed": 0
            }
        
        # Invalidate portfolio cache
        invalidate_portfolio_cache(db, current_user.id)
        
        # Invalidate all project metrics
        invalidate_all_project_metrics_for_user(db, current_user.id)
        
        # Invalidate all project caches (forecast, risks, anomalies)
        for project_id in project_ids:
            try:
                invalidate_project_cache(db, project_id)
            except Exception as e:
                print(f"[PORTFOLIO_REANALYZE] Failed to invalidate cache for {project_id}: {e}")
        
        # Schedule background re-analysis for all projects
        for project in projects:
            project_id = project["project_id"]
            activity_count = project.get("activity_count", 0)
            
            if activity_count > 0:
                background_tasks.add_task(
                    _compute_project_analytics_background,
                    project_id,
                    activity_count
                )
        
        return {
            "status": "re_analysis_scheduled",
            "message": f"Portfolio re-analysis scheduled for {len(project_ids)} project(s). Results will be computed in the background.",
            "projects_scheduled": len(project_ids),
            "note": "All caches have been invalidated. New results will be available shortly. Portfolio cache will be updated automatically when all projects finish analyzing."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling portfolio re-analysis: {str(e)}")

