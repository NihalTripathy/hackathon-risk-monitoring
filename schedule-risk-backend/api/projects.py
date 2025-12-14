"""
Project management API endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, BackgroundTasks, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import tempfile
import os
from core.csv_connector import load_activities_from_csv
from core.connectors import ConnectorRegistry, ConnectorConfig, get_connector
from core.database import get_db
from core.db_service import save_activities, get_activities, project_exists, log_event_db, get_audit_logs, get_all_projects, find_project_by_hash, delete_project, delete_projects
from core.file_utils import compute_file_hash
from core.auth_dependencies import get_current_user
from api.auth import UserResponse

router = APIRouter()


# Pydantic models for connector integration
class ConnectorIntegrationRequest(BaseModel):
    """Request model for connector-based project integration"""
    connector_type: str  # e.g., "csv", "rest_api", "jira"
    connection_params: Dict[str, Any]
    project_name: Optional[str] = None
    description: Optional[str] = None
    validate_data: bool = True
    sanitize_input: bool = True
    max_activities: int = 10000


@router.post("/projects/upload")
async def upload_project(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Upload a project CSV file - requires authentication
    
    Detects duplicate uploads by file hash and updates existing project instead of creating duplicate.
    This prevents duplicate projects from polluting ML training data when USE_ML_MODEL=true.
    
    After upload, computes forecast, risks, and anomalies in the background for instant future access.
    """
    # Use tempfile for cross-platform compatibility
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        temp_path = temp_file.name
        content = await file.read()
        temp_file.write(content)
    
    try:
        # Compute file hash for duplicate detection
        file_hash = compute_file_hash(temp_path)
        
        # Check for existing project with same hash (same user)
        existing_project = find_project_by_hash(db, file_hash, current_user.id)
        
        if existing_project:
            # Duplicate detected - update existing project
            project_id = existing_project.project_id
            is_duplicate = True
            
            # Invalidate cache since we're updating the project
            from core.cache_service import invalidate_project_cache
            invalidate_project_cache(db, project_id)
            
            # Log duplicate detection
            log_event_db(
                db,
                project_id,
                "duplicate_upload_detected",
                {
                    "filename": file.filename,
                    "file_hash": file_hash,
                    "action": "updating_existing_project"
                }
            )
        else:
            # New file - create new project
            project_id = str(uuid.uuid4())
            is_duplicate = False
        
        # Load activities from CSV
        activities = load_activities_from_csv(project_id, temp_path)
        activity_count = len(activities)
        
        # Save to database with filename, user_id, and file_hash
        save_activities(
            db, 
            project_id, 
            activities, 
            filename=file.filename, 
            user_id=current_user.id,
            file_hash=file_hash
        )
        
        # Log the upload event to database
        log_event_db(
            db, 
            project_id, 
            "project_upload",
            {
                "activity_count": activity_count,
                "filename": file.filename,
                "is_duplicate": is_duplicate,
                "file_hash": file_hash
            }
        )
        
        # Schedule background computation of forecast, risks, and anomalies
        # This pre-computes results so future API calls are instant
        if background_tasks:
            background_tasks.add_task(
                _compute_project_analytics_background,
                project_id,
                activity_count
            )
        
        return {
            "project_id": project_id, 
            "count": activity_count,
            "is_duplicate": is_duplicate,
            "message": "Project updated" if is_duplicate else "Project created",
            "note": "Analytics are being computed in the background. Results will be cached for instant access."
        }
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/projects/{project_id}/re-analyze")
async def re_analyze_project(
    project_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Manually trigger re-analysis of a project.
    
    This endpoint:
    - Invalidates all cached results (forecast, risks, anomalies)
    - Recomputes all analytics in the background
    - Useful when:
      * Logic/algorithms have been updated
      * You want to force recalculation
      * Data has been updated via API (future feature)
    
    Returns immediately with status, computation happens in background.
    """
    from core.project_auth import verify_project_ownership
    from core.cache_service import invalidate_project_cache
    from core.db_service import get_activities
    
    # Verify ownership
    verify_project_ownership(db, project_id, current_user)
    
    # Get current activity count
    activities = get_activities(db, project_id)
    if not activities:
        raise HTTPException(status_code=404, detail=f"Project {project_id} has no activities")
    
    activity_count = len(activities)
    
    # Invalidate all cache
    invalidate_project_cache(db, project_id)
    
    # Log the re-analysis event
    log_event_db(
        db,
        project_id,
        "re_analysis_triggered",
        {
            "activity_count": activity_count,
            "triggered_by": current_user.email,
            "reason": "manual_recalculation"
        }
    )
    
    # Schedule background recomputation
    if background_tasks:
        background_tasks.add_task(
            _compute_project_analytics_background,
            project_id,
            activity_count
        )
    
    return {
        "project_id": project_id,
        "status": "re_analysis_scheduled",
        "message": "Project re-analysis has been scheduled. Results will be computed in the background.",
        "activity_count": activity_count,
        "note": "Cache has been invalidated. New results will be available shortly."
    }


def _compute_project_analytics_background(project_id: str, activity_count: int):
    """
    Background task to compute forecast, risks, and anomalies for a project.
    This pre-computes results so future API calls are instant.
    """
    from core.database import get_db
    from core.db_service import get_activities
    from core.digital_twin import get_or_build_twin
    from core.mc_forecaster import monte_carlo_forecast
    from core.risk_pipeline import compute_project_risks
    from core.anomalies import detect_anomalies
    from core.cache_service import save_forecast_cache, save_risks_cache, save_anomalies_cache
    from core.llm_adapter import explain_rule_based
    from core.models import Activity as ActivityModel
    
    try:
        # Get a new database session for background task
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Get activities
            activities = get_activities(db, project_id)
            if not activities:
                return
            
            # Compute data hash once for all cache saves
            from core.logic_version import compute_data_hash
            data_hash = compute_data_hash(activities) if activities else None
            
            # 1. Compute and cache forecast
            try:
                twin = get_or_build_twin(project_id, activities)
                forecast = monte_carlo_forecast(twin, num_simulations=2000)
                save_forecast_cache(db, project_id, forecast, activity_count, data_hash=data_hash)
                print(f"[BACKGROUND] Cached forecast for project {project_id}")
            except Exception as e:
                print(f"[BACKGROUND] Failed to compute forecast for {project_id}: {e}")
            
            # 2. Compute and cache risks
            try:
                # Get reference date from project preference
                reference_date = None  # Always use today's date
                risks = compute_project_risks(project_id, db=db, activities=activities, reference_date=reference_date)
                
                # Enhance top 10 risks with explanations (same as API does)
                activity_map = {act.activity_id: act for act in activities}
                enhanced_risks = []
                
                for risk in risks[:10]:  # Top 10
                    activity_id = risk["activity_id"]
                    name = risk["name"]
                    score = risk["risk_score"]
                    features = risk["features"]
                    risk_factors = risk.get("risk_factors", {})
                    
                    # Determine risk level
                    if score >= 70:
                        risk_level = "High"
                    elif score >= 40:
                        risk_level = "Medium"
                    else:
                        risk_level = "Low"
                    
                    # Build explanation
                    explanation_parts = []
                    delay_days = features.get("delay_baseline_days", 0)
                    if delay_days > 0:
                        explanation_parts.append(f"{int(delay_days)}-day delay")
                    if features.get("is_on_critical_path", False):
                        explanation_parts.append("critical path")
                    float_days = features.get("float_days", 999)
                    if float_days <= 2:
                        explanation_parts.append("low float")
                    if features.get("resource_overbooked", False):
                        explanation_parts.append("resource overload")
                    
                    if explanation_parts:
                        explanation = f"Activity {activity_id} at {risk_level} risk (score {int(score)}): {' + '.join(explanation_parts)}."
                    else:
                        explanation = f"Activity {activity_id} at {risk_level} risk (score {int(score)}): moderate risk factors."
                    
                    # Get detailed explanation
                    detailed_explanation = None
                    activity = activity_map.get(activity_id)
                    if activity:
                        activity_obj = ActivityModel(
                            activity_id=activity.activity_id,
                            name=activity.name,
                            planned_start=activity.planned_start,
                            planned_finish=activity.planned_finish,
                            baseline_start=activity.baseline_start,
                            baseline_finish=activity.baseline_finish,
                            planned_duration=activity.planned_duration,
                            baseline_duration=activity.baseline_duration,
                            actual_start=activity.actual_start,
                            actual_finish=activity.actual_finish,
                            remaining_duration=activity.remaining_duration,
                            percent_complete=activity.percent_complete,
                            risk_probability=activity.risk_probability,
                            risk_delay_impact_days=activity.risk_delay_impact_days,
                            predecessors=activity.predecessors if hasattr(activity, 'predecessors') else [],
                            successors=activity.successors if hasattr(activity, 'successors') else [],
                            on_critical_path=activity.on_critical_path if hasattr(activity, 'on_critical_path') else False,
                            resource_id=activity.resource_id if hasattr(activity, 'resource_id') else None,
                            fte_allocation=activity.fte_allocation if hasattr(activity, 'fte_allocation') else None,
                            resource_max_fte=activity.resource_max_fte if hasattr(activity, 'resource_max_fte') else None
                        )
                        detailed = explain_rule_based(activity_obj, features, score)
                        detailed_explanation = {
                            "reasons": detailed.get("reasons", []),
                            "suggestions": detailed.get("suggestions", [])
                        }
                    
                    enhanced_risk = {
                        "activity_id": activity_id,
                        "name": name,
                        "risk_score": round(score, 1),
                        "risk_level": risk_level,
                        "explanation": explanation,
                        "risk_factors": risk_factors,
                        "key_metrics": {
                            "delay_days": int(delay_days),
                            "float_days": round(float_days, 1),
                            "on_critical_path": features.get("is_on_critical_path", False),
                            "resource_overbooked": features.get("resource_overbooked", False),
                            "progress_slip_pct": round(features.get("progress_slip", 0) * 100, 1)
                        },
                        "percent_complete": risk.get("percent_complete", 0),
                        "on_critical_path": features.get("is_on_critical_path", False)
                    }
                    
                    if detailed_explanation:
                        enhanced_risk["detailed_explanation"] = detailed_explanation
                    
                    enhanced_risks.append(enhanced_risk)
                
                save_risks_cache(db, project_id, {
                    "total_risks": len(risks),
                    "top_risks": enhanced_risks
                }, activity_count, data_hash=data_hash)
                print(f"[BACKGROUND] Cached risks for project {project_id}")
            except Exception as e:
                print(f"[BACKGROUND] Failed to compute risks for {project_id}: {e}")
            
            # 3. Compute and cache anomalies
            try:
                anomalies = detect_anomalies(project_id, activities=activities)
                save_anomalies_cache(db, project_id, anomalies, activity_count, data_hash=data_hash)
                print(f"[BACKGROUND] Cached anomalies for project {project_id}")
            except Exception as e:
                print(f"[BACKGROUND] Failed to compute anomalies for {project_id}: {e}")
            
            # 4. Compute and save project metrics for portfolio aggregation
            try:
                from core.portfolio_cache_service import save_project_metrics
                from core.db_service import get_project
                
                # Get user_id from project
                project = get_project(db, project_id)
                if project:
                    # Calculate average risk score from computed risks
                    avg_risk_score = 0.0
                    high_risk_count = 0
                    if risks:
                        risk_scores = [r["risk_score"] for r in risks]
                        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
                        high_risk_count = len([r for r in risks if r["risk_score"] >= 70])
                    
                    # Compute resource summary for this project
                    resource_summary = {}
                    from collections import defaultdict
                    resource_allocations = defaultdict(lambda: {"total_fte": 0.0, "max_fte": 0.0})
                    
                    for activity in activities:
                        if hasattr(activity, 'resource_id') and activity.resource_id:
                            resource_id = activity.resource_id
                            fte = activity.fte_allocation or 0.0
                            max_fte = activity.resource_max_fte or 0.0
                            resource_allocations[resource_id]["total_fte"] += fte
                            resource_allocations[resource_id]["max_fte"] = max(
                                resource_allocations[resource_id]["max_fte"],
                                max_fte
                            )
                    
                    # Format resource summary
                    for resource_id, data in resource_allocations.items():
                        utilization = (data["total_fte"] / data["max_fte"] * 100) if data["max_fte"] > 0 else 0
                        resource_summary[resource_id] = {
                            "total_fte": round(data["total_fte"], 2),
                            "max_fte": round(data["max_fte"], 2),
                            "utilization_pct": round(utilization, 1),
                            "is_overallocated": utilization > 100
                        }
                    
                    # Save project metrics
                    save_project_metrics(
                        db,
                        project_id,
                        project.user_id,
                        avg_risk_score,
                        activity_count,
                        resource_summary,
                        high_risk_count
                    )
                    
                    # Invalidate portfolio cache for this user (will be recomputed on next portfolio request)
                    from core.portfolio_cache_service import invalidate_portfolio_cache
                    invalidate_portfolio_cache(db, project.user_id)
                    
                    print(f"[BACKGROUND] Saved project metrics for {project_id}")
            except Exception as e:
                print(f"[BACKGROUND] Failed to save project metrics for {project_id}: {e}")
            
        finally:
            db.close()
    except Exception as e:
        print(f"[BACKGROUND] Error in background computation for {project_id}: {e}")


@router.get("/projects")
def list_projects(
    db: Session = Depends(get_db), 
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """List projects for the authenticated user - requires authentication"""
    projects = get_all_projects(db, user_id=current_user.id, limit=limit)
    return {
        "total": len(projects),
        "projects": projects
    }


@router.get("/projects/{project_id}/audit")
def get_audit_log(
    project_id: str, 
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get audit log for a specific project - requires authentication and ownership"""
    if not project_exists(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify project ownership
    from core.db_service import get_project
    project = get_project(db, project_id)
    if project and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: This project belongs to another user")
    
    audit_logs = get_audit_logs(db, project_id)
    return {
        "project_id": project_id,
        "total_events": len(audit_logs),
        "events": audit_logs
    }


@router.post("/projects/integrate")
async def integrate_project(
    request: ConnectorIntegrationRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Integrate a project from an external project management system.
    
    This endpoint allows companies to integrate their existing project management
    software (Jira, MS Project, Asana, etc.) with the risk monitoring system.
    
    The connector framework ensures:
    - Data safety and validation
    - Consistent Activity model output
    - Security and sanitization
    - Same core logic as CSV uploads
    
    Example request for REST API:
    {
        "connector_type": "rest_api",
        "connection_params": {
            "endpoint_url": "https://api.example.com/projects/{project_id}/activities",
            "method": "GET",
            "headers": {"Authorization": "Bearer token"},
            "field_mapping": {
                "activity_id": "id",
                "name": "title",
                "planned_start": "start_date"
            }
        },
        "project_name": "My Project",
        "validate_data": true,
        "sanitize_input": true
    }
    """
    try:
        # Create connector configuration
        config = ConnectorConfig(
            connector_type=request.connector_type,
            name=request.project_name or f"Project from {request.connector_type}",
            description=request.description,
            connection_params=request.connection_params,
            validate_data=request.validate_data,
            sanitize_input=request.sanitize_input,
            max_activities=request.max_activities
        )
        
        # Get connector instance
        try:
            connector = get_connector(config)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid connector type: {str(e)}"
            )
        
        # Test connection first
        test_result = connector.test_connection()
        if not test_result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=f"Connection test failed: {test_result.get('error', 'Unknown error')}"
            )
        
        # Generate project ID
        project_id = str(uuid.uuid4())
        
        # Load activities using connector
        result = connector.load_activities(project_id)
        
        if not result.success and len(result.activities) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load activities: {'; '.join(result.errors) if result.errors else 'Unknown error'}"
            )
        
        activity_count = len(result.activities)
        
        # Convert Activity models to database format
        from core.models import Activity as ActivityModel
        activities_for_db = []
        for act in result.activities:
            activities_for_db.append(ActivityModel(**act.dict()))
        
        # Save to database
        save_activities(
            db,
            project_id,
            activities_for_db,
            filename=f"{request.connector_type}_integration",
            user_id=current_user.id,
            file_hash=None  # No file hash for API integrations
        )
        
        # Log the integration event
        log_event_db(
            db,
            project_id,
            "project_integration",
            {
                "connector_type": request.connector_type,
                "activity_count": activity_count,
                "validation_errors": len(result.errors) if result.errors else 0,
                "warnings": len(result.warnings) if result.warnings else 0,
                "metadata": result.metadata
            }
        )
        
        # Schedule background computation
        if background_tasks:
            background_tasks.add_task(
                _compute_project_analytics_background,
                project_id,
                activity_count
            )
        
        return {
            "project_id": project_id,
            "count": activity_count,
            "connector_type": request.connector_type,
            "message": "Project integrated successfully",
            "warnings": result.warnings if result.warnings else [],
            "errors": result.errors if result.errors else [],
            "metadata": result.metadata,
            "note": "Analytics are being computed in the background. Results will be cached for instant access."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Integration failed: {str(e)}"
        )


@router.get("/connectors")
def list_connectors(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    List available connector types for integration.
    
    Returns information about all registered connectors that can be used
    to integrate with external project management systems.
    """
    available_types = ConnectorRegistry.get_available_types()
    
    connectors_info = []
    for connector_type in available_types:
        info = ConnectorRegistry.get_connector_info(connector_type)
        if info:
            connectors_info.append(info)
    
    return {
        "available_connectors": connectors_info,
        "total": len(connectors_info)
    }


@router.post("/connectors/test")
async def test_connector(
    request: ConnectorIntegrationRequest = Body(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Test a connector configuration without creating a project.
    
    Useful for validating connection parameters before integration.
    """
    try:
        config = ConnectorConfig(
            connector_type=request.connector_type,
            name=request.project_name or "Test Connection",
            connection_params=request.connection_params,
            validate_data=request.validate_data,
            sanitize_input=request.sanitize_input,
            max_activities=request.max_activities
        )
        
        connector = get_connector(config)
        test_result = connector.test_connection()
        
        return {
            "success": test_result.get("success", False),
            "connector_type": request.connector_type,
            "test_result": test_result,
            "connector_info": connector.get_connector_info()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


class DeleteSelectedRequest(BaseModel):
    """Request model for deleting selected projects"""
    project_ids: List[str]


@router.delete("/projects/all")
def delete_all_projects(
    confirm: bool = Query(False, description="Set to true to confirm deletion"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete ALL projects for the current user - requires confirmation
    
    WARNING: This permanently deletes all projects and their activities.
    Use with caution. Set confirm=true to proceed.
    
    This is useful for:
    - Starting fresh with duplicate detection enabled
    - Cleaning up test data
    - Resetting the database for ML training
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="This will delete ALL your projects. Set confirm=true to proceed."
        )
    
    from sqlalchemy import text
    
    # Get count before deletion
    project_count_result = db.execute(text("""
        SELECT COUNT(*) FROM projects WHERE user_id = :user_id
    """), {"user_id": current_user.id})
    project_count = project_count_result.scalar() or 0
    
    if project_count == 0:
        return {
            "success": True,
            "message": "No projects to delete",
            "deleted_projects": 0,
            "deleted_activities": 0
        }
    
    # Get all project IDs for this user
    project_ids_result = db.execute(text("""
        SELECT project_id FROM projects WHERE user_id = :user_id
    """), {"user_id": current_user.id})
    project_ids = [row[0] for row in project_ids_result]
    
    # Use delete_projects function for consistency
    result = delete_projects(db, project_ids, current_user.id)
    
    # Log the deletion event
    try:
        log_event_db(
            db,
            "system",
            "all_projects_deleted",
            {
                "user_id": current_user.id,
                "deleted_projects": result["deleted_projects"],
                "deleted_activities": result["deleted_activities"]
            }
        )
    except:
        pass  # Ignore if logging fails
    
    return result


@router.post("/projects/delete-selected")
def delete_selected_projects(
    request: DeleteSelectedRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete multiple selected projects and all their related data.
    
    This permanently deletes:
    - The selected projects
    - All activities in those projects
    - All audit logs for those projects
    - All cached data (forecast, risks, anomalies, metrics)
    
    Requires authentication and ownership of all projects.
    """
    if not request.project_ids:
        raise HTTPException(status_code=400, detail="No project IDs provided")
    
    try:
        result = delete_projects(db, request.project_ids, current_user.id)
        
        # Log the deletion event
        try:
            log_event_db(
                db,
                "system",
                "projects_deleted",
                {
                    "user_id": current_user.id,
                    "project_ids": request.project_ids,
                    "deleted_projects": result["deleted_projects"],
                    "deleted_activities": result["deleted_activities"]
                }
            )
        except:
            pass  # Ignore if logging fails
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete projects: {str(e)}")


@router.delete("/projects/{project_id}")
def delete_single_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a single project and all its related data.
    
    This permanently deletes:
    - The project
    - All activities in the project
    - All audit logs for the project
    - All cached data (forecast, risks, anomalies, metrics)
    
    Requires authentication and project ownership.
    """
    try:
        result = delete_project(db, project_id, current_user.id)
        
        # Log the deletion event
        try:
            log_event_db(
                db,
                "system",
                "project_deleted",
                {
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "deleted_activities": result["deleted_activities"]
                }
            )
        except:
            pass  # Ignore if logging fails
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

