"""
Portfolio-level analysis service
Aggregates risks, forecasts, and resources across multiple projects
OPTIMIZED for performance - bulk queries and efficient processing
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from collections import defaultdict
import time
import json

from .db_service import get_all_projects, get_activities, get_project
from .db_models import Activity, Project
from .risk_pipeline import compute_project_risks
from .features import compute_features
from .risk_model import RuleBasedRiskModel
from sqlalchemy import text


def _has_file_hash_column(db: Session) -> bool:
    """Check if file_hash column exists in projects table"""
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='projects' AND column_name='file_hash'
        """))
        return result.first() is not None
    except Exception:
        return False


def _get_projects_by_ids(db: Session, project_ids: List[str], user_id: int) -> List[Project]:
    """Safely get projects by IDs, handling missing file_hash column"""
    if not _has_file_hash_column(db):
        # Use raw SQL if file_hash doesn't exist
        placeholders = ','.join([f"'{pid}'" for pid in project_ids])
        result = db.execute(text(f"""
            SELECT project_id, user_id, filename, activity_count, created_at, updated_at
            FROM projects 
            WHERE project_id IN ({placeholders}) AND user_id = :user_id
        """), {"user_id": user_id})
        # Convert to Project objects (minimal, without file_hash)
        projects = []
        for row in result:
            project = Project(
                project_id=row[0],
                user_id=row[1],
                filename=row[2],
                activity_count=row[3] or 0
            )
            projects.append(project)
        return projects
    else:
        # Use ORM if file_hash exists
        return db.query(Project).filter(
            and_(
                Project.project_id.in_(project_ids),
                Project.user_id == user_id
            )
        ).all()


def _safe_json_loads(json_str: str) -> List:
    """Safely parse JSON string, return empty list on error"""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        # Try eval as fallback for legacy data
        try:
            return eval(json_str) if json_str else []
        except:
            return []


def _bulk_load_activities(db: Session, project_ids: List[str]) -> Dict[str, List]:
    """
    Bulk load activities for multiple projects in a single query
    Much faster than loading projects one by one
    """
    if not project_ids:
        return {}
    
    # Single query to get all activities for all projects
    db_activities = db.query(Activity).filter(
        Activity.project_id.in_(project_ids)
    ).all()
    
    # Group by project_id
    activities_by_project = defaultdict(list)
    for db_act in db_activities:
        # Convert to ActivityModel format (simplified - only what we need)
        from .models import Activity as ActivityModel
        act = ActivityModel(
            activity_id=db_act.activity_id,
            name=db_act.name,
            planned_start=db_act.planned_start,
            planned_finish=db_act.planned_finish,
            baseline_start=db_act.baseline_start,
            baseline_finish=db_act.baseline_finish,
            planned_duration=db_act.planned_duration,
            baseline_duration=db_act.baseline_duration,
            actual_start=db_act.actual_start,
            actual_finish=db_act.actual_finish,
            remaining_duration=db_act.remaining_duration,
            percent_complete=db_act.percent_complete,
            risk_probability=db_act.risk_probability,
            risk_delay_impact_days=db_act.risk_delay_impact_days,
            predecessors=_safe_json_loads(db_act.predecessors) if db_act.predecessors else [],
            successors=_safe_json_loads(db_act.successors) if db_act.successors else [],
            on_critical_path=db_act.on_critical_path,
            resource_id=db_act.resource_id,
            fte_allocation=db_act.fte_allocation,
            resource_max_fte=db_act.resource_max_fte
        )
        activities_by_project[db_act.project_id].append(act)
    
    return dict(activities_by_project)


def _compute_quick_risk_score(activities: List) -> float:
    """
    Compute a quick risk score without full risk pipeline
    Uses simplified heuristics for portfolio summary
    """
    if not activities:
        return 0.0
    
    risk_scores = []
    for activity in activities:
        # Quick risk estimation based on key factors
        score = 0.0
        
        # Delay factor
        if activity.planned_duration and activity.baseline_duration:
            delay = activity.planned_duration - activity.baseline_duration
            if delay > 0:
                score += min(30, delay / activity.baseline_duration * 30)
        
        # Progress slip
        if activity.percent_complete and activity.planned_duration:
            expected_progress = 100.0  # Simplified
            if activity.percent_complete < expected_progress * 0.8:
                score += 20
        
        # Risk register
        if activity.risk_probability:
            score += activity.risk_probability * 20
        
        # Critical path
        if activity.on_critical_path:
            score += 15
        
        risk_scores.append(min(100, score))
    
    return sum(risk_scores) / len(risk_scores) if risk_scores else 0.0


def get_portfolio_summary(
    db: Session,
    user_id: int,
    project_ids: Optional[List[str]] = None,
    force_recompute: bool = False
) -> Dict:
    """
    Get portfolio-level summary across multiple projects
    OPTIMIZED: Uses cached project metrics for instant aggregation
    """
    start_time = time.time()
    
    # OPTIMIZATION: Check portfolio cache first (only if no project_ids filter and not forcing recompute)
    # This check must happen BEFORE we modify project_ids
    original_project_ids_was_none = (project_ids is None)
    if not force_recompute and original_project_ids_was_none:
        from core.portfolio_cache_service import get_portfolio_cache
        cached = get_portfolio_cache(db, user_id)
        if cached:
            cache_time = (time.time() - start_time) * 1000
            print(f"[PORTFOLIO_CACHE] Portfolio summary served from cache in {cache_time:.3f}ms")
            return {
                **cached,
                "computation_time_ms": round(cache_time, 2)
            }
    
    # Get projects for user
    if project_ids is None:
        projects = get_all_projects(db, user_id=user_id, limit=1000)
        project_ids = [p["project_id"] for p in projects]
        projects_dict = {p["project_id"]: p for p in projects}
    else:
        # Verify ownership - bulk query
        db_projects = _get_projects_by_ids(db, project_ids, user_id)
        projects_dict = {
            p.project_id: {
                "project_id": p.project_id,
                "filename": p.filename or "Untitled Project",
                "activity_count": p.activity_count or 0,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in db_projects
        }
        project_ids = list(projects_dict.keys())
    
    if not project_ids:
        return {
            "total_projects": 0,
            "total_activities": 0,
            "portfolio_risk_score": 0.0,
            "projects_at_risk": 0,
            "high_risk_projects": [],
            "resource_summary": {},
            "computation_time_ms": 0
        }
    
    # OPTIMIZATION: Try to use cached project metrics (much faster than computing from activities)
    from core.portfolio_cache_service import get_all_project_metrics
    project_metrics = get_all_project_metrics(db, user_id, project_ids)
    
    # Identify projects with and without cached metrics
    projects_with_metrics = set(project_metrics.keys())
    projects_without_metrics = [pid for pid in project_ids if pid not in projects_with_metrics]
    
    # Use cached metrics for projects that have them
    if project_metrics:
        # Aggregate from cached metrics (fast path for projects with metrics)
        total_activities = sum(m["activity_count"] for m in project_metrics.values())
        project_risk_scores = [m["risk_score"] for m in project_metrics.values()]
        
        # Build high-risk projects list from cached metrics
        high_risk_projects = []
        for project_id, metrics in project_metrics.items():
            if metrics["risk_score"] >= 60:
                high_risk_projects.append({
                    "project_id": project_id,
                    "filename": projects_dict.get(project_id, {}).get("filename", "Untitled Project"),
                    "risk_score": round(metrics["risk_score"], 1),
                    "activity_count": metrics["activity_count"]
                })
        
        # Aggregate resource summary from project metrics
        resource_allocations = defaultdict(lambda: {"total_fte": 0.0, "max_fte": 0.0, "projects": set()})
        for project_id, metrics in project_metrics.items():
            resource_summary = metrics.get("resource_summary", {})
            for resource_id, data in resource_summary.items():
                resource_allocations[resource_id]["total_fte"] += data.get("total_fte", 0.0)
                resource_allocations[resource_id]["max_fte"] = max(
                    resource_allocations[resource_id]["max_fte"],
                    data.get("max_fte", 0.0)
                )
                resource_allocations[resource_id]["projects"].add(project_id)
        
        # If we have metrics for all projects, we can return early
        if not projects_without_metrics:
            # Format resource summary
            resource_summary = {}
            for resource_id, data in resource_allocations.items():
                utilization = (data["total_fte"] / data["max_fte"] * 100) if data["max_fte"] > 0 else 0
                resource_summary[resource_id] = {
                    "total_fte": round(data["total_fte"], 2),
                    "max_fte": round(data["max_fte"], 2),
                    "utilization_pct": round(utilization, 1),
                    "project_count": len(data["projects"]),
                    "is_overallocated": utilization > 100
                }
            
            portfolio_risk_score = sum(project_risk_scores) / len(project_risk_scores) if project_risk_scores else 0.0
            projects_at_risk = len([s for s in project_risk_scores if s >= 50])
            
            computation_time = (time.time() - start_time) * 1000
            
            result = {
                "total_projects": len(project_ids),
                "total_activities": total_activities,
                "portfolio_risk_score": round(portfolio_risk_score, 1),
                "projects_at_risk": projects_at_risk,
                "high_risk_projects": sorted(high_risk_projects, key=lambda x: x["risk_score"], reverse=True),
                "resource_summary": resource_summary,
                "computation_time_ms": round(computation_time, 2)
            }
            
            # Cache the result for future requests (only if no project_ids filter)
            if original_project_ids_was_none:
                from core.portfolio_cache_service import save_portfolio_cache
                save_portfolio_cache(
                    db,
                    user_id,
                    result["total_projects"],
                    result["total_activities"],
                    result["portfolio_risk_score"],
                    result["projects_at_risk"],
                    result["high_risk_projects"],
                    result["resource_summary"]
                )
            
            print(f"[PORTFOLIO_CACHE] Portfolio summary computed from cached metrics in {computation_time:.3f}ms")
            return result
        
        # We have some projects without metrics - compute for those and merge
        print(f"[PORTFOLIO_CACHE] Using cached metrics for {len(projects_with_metrics)} projects, computing for {len(projects_without_metrics)} projects")
        
        # Compute for projects without metrics
        activities_by_project = _bulk_load_activities(db, projects_without_metrics)
        
        for project_id in projects_without_metrics:
            activities = activities_by_project.get(project_id, [])
            if not activities:
                continue
            
            total_activities += len(activities)
            quick_risk_score = _compute_quick_risk_score(activities)
            project_risk_scores.append(quick_risk_score)
            
            if quick_risk_score >= 60:
                high_risk_projects.append({
                    "project_id": project_id,
                    "filename": projects_dict.get(project_id, {}).get("filename", "Untitled Project"),
                    "risk_score": round(quick_risk_score, 1),
                    "activity_count": len(activities)
                })
            
            # Aggregate resource allocation for projects without metrics
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
                    resource_allocations[resource_id]["projects"].add(project_id)
        
        # Format resource summary
        resource_summary = {}
        for resource_id, data in resource_allocations.items():
            utilization = (data["total_fte"] / data["max_fte"] * 100) if data["max_fte"] > 0 else 0
            resource_summary[resource_id] = {
                "total_fte": round(data["total_fte"], 2),
                "max_fte": round(data["max_fte"], 2),
                "utilization_pct": round(utilization, 1),
                "project_count": len(data["projects"]),
                "is_overallocated": utilization > 100
            }
        
        portfolio_risk_score = sum(project_risk_scores) / len(project_risk_scores) if project_risk_scores else 0.0
        projects_at_risk = len([s for s in project_risk_scores if s >= 50])
        
        computation_time = (time.time() - start_time) * 1000
        
        result = {
            "total_projects": len(project_ids),
            "total_activities": total_activities,
            "portfolio_risk_score": round(portfolio_risk_score, 1),
            "projects_at_risk": projects_at_risk,
            "high_risk_projects": sorted(high_risk_projects, key=lambda x: x["risk_score"], reverse=True),
            "resource_summary": resource_summary,
            "computation_time_ms": round(computation_time, 2)
        }
        
        # Cache the result for future requests (only if no project_ids filter)
        if original_project_ids_was_none:
            from core.portfolio_cache_service import save_portfolio_cache
            save_portfolio_cache(
                db,
                user_id,
                result["total_projects"],
                result["total_activities"],
                result["portfolio_risk_score"],
                result["projects_at_risk"],
                result["high_risk_projects"],
                result["resource_summary"]
            )
        
        print(f"[PORTFOLIO_CACHE] Portfolio summary computed (mixed: cached + computed) in {computation_time:.3f}ms")
        return result
    
    # Fallback: Compute from activities for all projects (slower, but works if metrics not available)
    print("[PORTFOLIO_CACHE] Using fallback computation from activities (project metrics not available)")
    
    # OPTIMIZATION: Bulk load all activities in one query
    activities_by_project = _bulk_load_activities(db, project_ids)
    
    # Aggregate data across projects
    total_activities = 0
    project_risk_scores = []
    high_risk_projects = []
    resource_allocations = defaultdict(lambda: {"total_fte": 0.0, "max_fte": 0.0, "projects": set()})
    
    # Process all projects (now activities are already loaded)
    for project_id in project_ids:
        activities = activities_by_project.get(project_id, [])
        if not activities:
            continue
        
        total_activities += len(activities)
        
        # OPTIMIZATION: Use quick risk score instead of full computation
        quick_risk_score = _compute_quick_risk_score(activities)
        
        project_risk_scores.append({
            "project_id": project_id,
            "risk_score": quick_risk_score,
            "top_risk_count": len([a for a in activities if quick_risk_score >= 70])
        })
        
        # Track high-risk projects
        if quick_risk_score >= 60:
            high_risk_projects.append({
                "project_id": project_id,
                "filename": projects_dict.get(project_id, {}).get("filename"),
                "risk_score": round(quick_risk_score, 1),
                "activity_count": len(activities)
            })
        
        # Aggregate resource allocation
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
                resource_allocations[resource_id]["projects"].add(project_id)
    
    # Calculate portfolio-level metrics
    portfolio_risk_score = 0.0
    if project_risk_scores:
        portfolio_risk_score = sum(p["risk_score"] for p in project_risk_scores) / len(project_risk_scores)
    
    projects_at_risk = len([p for p in project_risk_scores if p["risk_score"] >= 50])
    
    # Format resource summary
    resource_summary = {}
    for resource_id, data in resource_allocations.items():
        utilization = (data["total_fte"] / data["max_fte"] * 100) if data["max_fte"] > 0 else 0
        resource_summary[resource_id] = {
            "total_fte": round(data["total_fte"], 2),
            "max_fte": round(data["max_fte"], 2),
            "utilization_pct": round(utilization, 1),
            "project_count": len(data["projects"]),
            "is_overallocated": utilization > 100
        }
    
    computation_time = (time.time() - start_time) * 1000
    
    result = {
        "total_projects": len(project_ids),
        "total_activities": total_activities,
        "portfolio_risk_score": round(portfolio_risk_score, 1),
        "projects_at_risk": projects_at_risk,
        "high_risk_projects": sorted(high_risk_projects, key=lambda x: x["risk_score"], reverse=True),
        "resource_summary": resource_summary,
        "computation_time_ms": round(computation_time, 2)
    }
    
    # Cache the result for future requests (only if no project_ids filter)
    if original_project_ids_was_none:
        from core.portfolio_cache_service import save_portfolio_cache
        save_portfolio_cache(
            db,
            user_id,
            result["total_projects"],
            result["total_activities"],
            result["portfolio_risk_score"],
            result["projects_at_risk"],
            result["high_risk_projects"],
            result["resource_summary"]
        )
    
    print(f"[PORTFOLIO_CACHE] Portfolio summary computed from activities (fallback) in {computation_time:.3f}ms")
    return result


def get_portfolio_risks(
    db: Session,
    user_id: int,
    project_ids: Optional[List[str]] = None,
    limit: int = 20,
    force_recompute: bool = False
) -> Dict:
    """
    Get top risks across portfolio (aggregated from all projects)
    OPTIMIZED: Uses cached risks from individual projects for instant aggregation
    """
    start_time = time.time()
    
    # Get projects
    projects_dict = {}
    if project_ids is None:
        projects = get_all_projects(db, user_id=user_id, limit=1000)
        project_ids = [p["project_id"] for p in projects]
        projects_dict = {p["project_id"]: p for p in projects}
    else:
        # Verify ownership - bulk query
        db_projects = _get_projects_by_ids(db, project_ids, user_id)
        project_ids = [p.project_id for p in db_projects]
        projects_dict = {
            p.project_id: {
                "project_id": p.project_id,
                "filename": p.filename or "Untitled Project"
            }
            for p in db_projects
        }
    
    if not project_ids:
        return {
            "total_risks": 0,
            "top_risks": [],
            "projects_analyzed": 0,
            "computation_time_ms": 0
        }
    
    # OPTIMIZATION: Try to use cached risks from individual projects
    all_risks = []
    projects_with_cache = 0
    
    if not force_recompute:
        from core.cache_service import get_risks_cache
        for project_id in project_ids:
            try:
                # Get activities count for cache validation
                activities = _bulk_load_activities(db, [project_id]).get(project_id, [])
                activity_count = len(activities)
                
                # Get cached risks
                cached_risks = get_risks_cache(db, project_id, activity_count)
                if cached_risks:
                    top_risks = cached_risks.get("top_risks", [])
                    # Add project context to each risk
                    project_info = projects_dict.get(project_id, {})
                    for risk in top_risks:
                        risk["project_id"] = project_id
                        risk["project_filename"] = project_info.get("filename", project_id)
                    all_risks.extend(top_risks)
                    projects_with_cache += 1
            except Exception as e:
                print(f"[Portfolio] Error getting cached risks for {project_id}: {e}")
                continue
    
    # If we don't have cached risks for all projects, compute missing ones
    if projects_with_cache < len(project_ids):
        print(f"[PORTFOLIO_CACHE] Computing risks for {len(project_ids) - projects_with_cache} projects (cache miss)")
        activities_by_project = _bulk_load_activities(db, project_ids)
        max_risks_per_project = max(50, limit * 2)
        
        for project_id in project_ids:
            # Skip if we already have cached risks for this project
            if any(r.get("project_id") == project_id for r in all_risks):
                continue
            
            try:
                activities = activities_by_project.get(project_id, [])
                if not activities:
                    continue
                
                # Compute risks for this project
                risks = compute_project_risks(project_id, db=db, activities=activities)
                top_project_risks = risks[:max_risks_per_project]
                
                # Add project context
                project_info = projects_dict.get(project_id, {})
                for risk in top_project_risks:
                    risk["project_id"] = project_id
                    risk["project_filename"] = project_info.get("filename", project_id)
                
                all_risks.extend(top_project_risks)
            except Exception as e:
                print(f"[Portfolio] Error getting risks for project {project_id}: {e}")
                continue
    
    # Sort by risk score and return top N
    all_risks.sort(key=lambda x: x["risk_score"], reverse=True)
    top_risks = all_risks[:limit]
    
    computation_time = (time.time() - start_time) * 1000
    
    return {
        "total_risks": len(all_risks),
        "top_risks": top_risks,
        "projects_analyzed": len(project_ids),
        "computation_time_ms": round(computation_time, 2)
    }


def get_cross_project_dependencies(
    db: Session,
    user_id: int,
    project_ids: Optional[List[str]] = None
) -> Dict:
    """
    Analyze cross-project dependencies (activities that depend on other projects)
    
    Note: This is a basic implementation. For full cross-project dependency tracking,
    a separate dependency table would be needed. This function identifies potential
    dependencies based on activity names and dates.
    """
    if project_ids is None:
        projects = get_all_projects(db, user_id=user_id, limit=1000)
        project_ids = [p["project_id"] for p in projects]
    else:
        # Verify ownership - bulk query
        db_projects = _get_projects_by_ids(db, project_ids, user_id)
        project_ids = [p.project_id for p in db_projects]
    
    # OPTIMIZATION: Bulk load activities
    activities_by_project = _bulk_load_activities(db, project_ids)
    
    # Analyze potential dependencies
    dependencies = []
    
    # Simple heuristic: look for activities that reference other project IDs in names
    # or have dates that suggest dependencies
    for project_id, activities in activities_by_project.items():
        for activity in activities:
            # Check if activity name references another project
            activity_name = (activity.name or "").lower()
            
            # Look for references to other projects
            for other_project_id, other_activities in activities_by_project.items():
                if other_project_id == project_id:
                    continue
                
                # Check if this activity's start depends on another project's finish
                if activity.planned_start and activity.predecessors:
                    # This is a simplified check - full implementation would need
                    # explicit cross-project dependency tracking
                    pass
    
    return {
        "total_projects": len(project_ids),
        "potential_dependencies": dependencies,
        "note": "Cross-project dependencies require explicit tracking. This is a basic analysis."
    }


def get_portfolio_resource_allocation(
    db: Session,
    user_id: int,
    project_ids: Optional[List[str]] = None
) -> Dict:
    """
    Get resource allocation across portfolio
    OPTIMIZED: Uses bulk loading
    """
    if project_ids is None:
        projects = get_all_projects(db, user_id=user_id, limit=1000)
        project_ids = [p["project_id"] for p in projects]
    else:
        # Verify ownership - bulk query
        db_projects = _get_projects_by_ids(db, project_ids, user_id)
        project_ids = [p.project_id for p in db_projects]
    
    # OPTIMIZATION: Bulk load activities
    activities_by_project = _bulk_load_activities(db, project_ids)
    
    resource_details = defaultdict(lambda: {
        "allocations": [],
        "total_fte": 0.0,
        "max_fte": 0.0,
        "projects": set()
    })
    
    # Collect resource data from all projects
    for project_id, activities in activities_by_project.items():
        try:
            for activity in activities:
                if hasattr(activity, 'resource_id') and activity.resource_id:
                    resource_id = activity.resource_id
                    fte = activity.fte_allocation or 0.0
                    max_fte = activity.resource_max_fte or 0.0
                    
                    resource_details[resource_id]["allocations"].append({
                        "project_id": project_id,
                        "activity_id": activity.activity_id,
                        "activity_name": activity.name,
                        "fte": fte,
                        "max_fte": max_fte
                    })
                    resource_details[resource_id]["total_fte"] += fte
                    resource_details[resource_id]["max_fte"] = max(
                        resource_details[resource_id]["max_fte"],
                        max_fte
                    )
                    resource_details[resource_id]["projects"].add(project_id)
        
        except Exception as e:
            print(f"[Portfolio] Error processing resources for {project_id}: {e}")
            continue
    
    # Format results
    resource_allocation = {}
    for resource_id, data in resource_details.items():
        utilization = (data["total_fte"] / data["max_fte"] * 100) if data["max_fte"] > 0 else 0
        resource_allocation[resource_id] = {
            "total_fte": round(data["total_fte"], 2),
            "max_fte": round(data["max_fte"], 2),
            "utilization_pct": round(utilization, 1),
            "project_count": len(data["projects"]),
            "activity_count": len(data["allocations"]),
            "is_overallocated": utilization > 100,
            "allocations": data["allocations"][:10]  # Limit to top 10 for response size
        }
    
    return {
        "total_resources": len(resource_allocation),
        "overallocated_resources": len([r for r in resource_allocation.values() if r["is_overallocated"]]),
        "resources": resource_allocation
    }
