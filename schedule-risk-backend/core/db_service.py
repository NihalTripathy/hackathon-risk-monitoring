"""
Database service layer - handles all database operations
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date
from .db_models import Project, Activity, AuditLog
from .models import Activity as ActivityModel
import json


# ========== Project Operations ==========

def find_project_by_hash(db: Session, file_hash: str, user_id: int) -> Optional[Project]:
    """
    Find existing project by file hash and user_id
    
    Args:
        db: Database session
        file_hash: SHA256 hash of file content
        user_id: User ID to scope the search
        
    Returns:
        Project if found, None otherwise
    """
    from sqlalchemy import text
    
    # Check if file_hash column exists
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='projects' AND column_name='file_hash'
        """))
        has_file_hash = result.first() is not None
    except Exception:
        has_file_hash = False
    
    if not has_file_hash:
        # Column doesn't exist yet - return None (no duplicates found)
        return None
    
    # Use raw SQL to find project by hash
    result = db.execute(text("""
        SELECT project_id 
        FROM projects 
        WHERE file_hash = :file_hash AND user_id = :user_id
        ORDER BY created_at DESC
        LIMIT 1
    """), {"file_hash": file_hash, "user_id": user_id})
    
    row = result.first()
    if row:
        return get_project(db, row[0])
    return None


def create_project(db: Session, project_id: str, user_id: int, filename: Optional[str] = None, activity_count: int = 0, file_hash: Optional[str] = None):
    """Create a new project"""
    from sqlalchemy import text
    
    # Check if file_hash column exists - use a more reliable check
    has_file_hash = False
    try:
        # Use a direct query that's less likely to be cached
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'projects' 
            AND column_name = 'file_hash'
        """))
        count = result.scalar() or 0
        has_file_hash = count > 0
    except Exception as e:
        # If check fails, assume column doesn't exist (safer)
        has_file_hash = False
    
    # Build column list and values dynamically
    columns = ["project_id", "user_id"]
    values = [":project_id", ":user_id"]
    params = {"project_id": project_id, "user_id": user_id}
    
    if filename:
        columns.append("filename")
        values.append(":filename")
        params["filename"] = filename
    
    columns.append("activity_count")
    values.append(":activity_count")
    params["activity_count"] = activity_count
    
    if has_file_hash and file_hash:
        columns.append("file_hash")
        values.append(":file_hash")
        params["file_hash"] = file_hash
    
    # Execute insert
    db.execute(text(f"""
        INSERT INTO projects ({', '.join(columns)})
        VALUES ({', '.join(values)})
    """), params)
    
    db.commit()
    return get_project(db, project_id)


def update_project_metadata(db: Session, project_id: str, filename: Optional[str] = None, activity_count: Optional[int] = None, file_hash: Optional[str] = None):
    """Update project metadata"""
    from sqlalchemy import text
    from datetime import date
    
    # Check if columns exist
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='projects' AND column_name IN ('filename', 'activity_count', 'file_hash')
        """))
        existing_columns = {row[0] for row in result}
        has_filename = 'filename' in existing_columns
        has_activity_count = 'activity_count' in existing_columns
        has_file_hash = 'file_hash' in existing_columns
    except Exception:
        has_filename = False
        has_activity_count = False
        has_file_hash = False
    
    # Use raw SQL for flexibility
    updates = []
    params = {"project_id": project_id}
    
    if has_filename and filename is not None:
        updates.append("filename = :filename")
        params["filename"] = filename
    if has_activity_count and activity_count is not None:
        updates.append("activity_count = :activity_count")
        params["activity_count"] = activity_count
    if has_file_hash and file_hash is not None:
        updates.append("file_hash = :file_hash")
        params["file_hash"] = file_hash
    
    if updates:
        # Also update updated_at timestamp
        updates.append("updated_at = CURRENT_TIMESTAMP")
        db.execute(text(f"""
            UPDATE projects 
            SET {', '.join(updates)}
            WHERE project_id = :project_id
        """), params)
        db.commit()
    
    return get_project(db, project_id)


def get_all_projects(db: Session, user_id: Optional[int] = None, limit: Optional[int] = None) -> List[Dict]:
    """Get projects with metadata, optionally filtered by user_id"""
    from sqlalchemy import text
    
    # Check if new columns exist (including file_hash)
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='projects' AND column_name IN ('filename', 'activity_count', 'user_id', 'file_hash')
        """))
        existing_columns = {row[0] for row in result}
        has_filename = 'filename' in existing_columns
        has_activity_count = 'activity_count' in existing_columns
        has_user_id = 'user_id' in existing_columns
        has_file_hash = 'file_hash' in existing_columns
    except Exception:
        # If we can't check, assume columns don't exist (safer)
        has_filename = False
        has_activity_count = False
        has_user_id = False
        has_file_hash = False
    
    # Use raw SQL if file_hash doesn't exist (to avoid ORM trying to select it)
    # OR if other required columns don't exist
    if not has_file_hash or not has_filename or not has_activity_count or not has_user_id:
        # Build query based on what columns exist
        select_cols = ["project_id", "created_at", "updated_at"]
        if has_filename:
            select_cols.append("filename")
        if has_activity_count:
            select_cols.append("activity_count")
        if has_user_id:
            select_cols.append("user_id")
        # Note: We don't select file_hash even if it exists (not needed for list)
        
        where_clause = ""
        if user_id and has_user_id:
            where_clause = "WHERE user_id = :user_id"
        
        query_sql = f"""
            SELECT {', '.join(select_cols)}
            FROM projects 
            {where_clause}
            ORDER BY created_at DESC
        """
        if limit:
            query_sql += f" LIMIT {limit}"
        
        params = {}
        if user_id and has_user_id:
            params["user_id"] = user_id
        
        result = db.execute(text(query_sql), params)
        projects_data = result.fetchall()
        
        # Convert to dict format
        projects_list = []
        for row in projects_data:
            proj_dict = {
                "project_id": row[0],
                "created_at": row[1].isoformat() if row[1] else None,
                "updated_at": row[2].isoformat() if len(row) > 2 and row[2] else None,
            }
            
            col_idx = 3
            if has_filename:
                proj_dict["filename"] = row[col_idx] if col_idx < len(row) and row[col_idx] else "Untitled Project"
                col_idx += 1
            else:
                proj_dict["filename"] = "Untitled Project"
            
            if has_activity_count:
                proj_dict["activity_count"] = row[col_idx] if col_idx < len(row) and row[col_idx] else 0
                col_idx += 1
            else:
                # Count activities manually
                count_result = db.execute(text("""
                    SELECT COUNT(*) FROM activities WHERE project_id = :project_id
                """), {"project_id": proj_dict["project_id"]})
                proj_dict["activity_count"] = count_result.scalar() or 0
            
            
            projects_list.append(proj_dict)
        
        return projects_list
    
    # Normal path - all columns exist including file_hash, use ORM
    query = db.query(Project)
    
    # Filter by user_id if provided
    if user_id is not None:
        query = query.filter(Project.user_id == user_id)
    
    query = query.order_by(Project.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    projects = query.all()
    return [
        {
            "project_id": proj.project_id,
            "filename": proj.filename or "Untitled Project",
            "activity_count": proj.activity_count or 0,
            "created_at": proj.created_at.isoformat() if proj.created_at else None,
            "updated_at": proj.updated_at.isoformat() if proj.updated_at else None,
        }
        for proj in projects
    ]


def get_project(db: Session, project_id: str) -> Optional[Project]:
    """Get project by ID"""
    from sqlalchemy import text
    
    # Check if file_hash column exists
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='projects' AND column_name='file_hash'
        """))
        has_file_hash = result.first() is not None
    except Exception:
        has_file_hash = False
    
    # Use raw SQL if file_hash doesn't exist (to avoid ORM trying to select it)
    if not has_file_hash:
        # Build SELECT columns dynamically
        select_cols = ["project_id", "user_id", "filename", "activity_count", "created_at", "updated_at"]
        
        result = db.execute(text(f"""
            SELECT {', '.join(select_cols)}
            FROM projects 
            WHERE project_id = :project_id
        """), {"project_id": project_id})
        row = result.first()
        if not row:
            return None
        
        # Create a minimal Project object
        project = Project(
            project_id=row[0],
            user_id=row[1],
            filename=row[2],
            activity_count=row[3] or 0
        )
        # Note: created_at and updated_at are set by SQLAlchemy, we can't easily set them here
        # But this should work for most use cases
        return project
    
    # Use ORM if file_hash exists
    return db.query(Project).filter(Project.project_id == project_id).first()


def project_exists(db: Session, project_id: str) -> bool:
    """Check if project exists"""
    from sqlalchemy import text
    
    # Check if file_hash column exists
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='projects' AND column_name='file_hash'
        """))
        has_file_hash = result.first() is not None
    except Exception:
        has_file_hash = False
    
    # Use raw SQL if file_hash doesn't exist (to avoid ORM trying to select it)
    if not has_file_hash:
        result = db.execute(text("""
            SELECT project_id FROM projects WHERE project_id = :project_id
        """), {"project_id": project_id})
        return result.first() is not None
    
    # Use ORM if file_hash exists
    return db.query(Project).filter(Project.project_id == project_id).first() is not None


# ========== Activity Operations ==========

def save_activities(db: Session, project_id: str, activities: List[ActivityModel], filename: Optional[str] = None, user_id: Optional[int] = None, file_hash: Optional[str] = None):
    """Save activities to database"""
    # Invalidate cache when activities are updated (cache is based on activity_count)
    # This ensures cache is invalidated if save_activities is called from anywhere
    try:
        from core.cache_service import invalidate_project_cache
        invalidate_project_cache(db, project_id)
    except Exception:
        pass  # Gracefully handle if cache tables don't exist yet
    
    # Invalidate project metrics and portfolio cache
    try:
        from core.portfolio_cache_service import invalidate_project_metrics, invalidate_portfolio_cache
        invalidate_project_metrics(db, project_id)
        # Get user_id to invalidate portfolio cache
        if user_id:
            invalidate_portfolio_cache(db, user_id)
        else:
            # Try to get user_id from project
            project = get_project(db, project_id)
            if project:
                invalidate_portfolio_cache(db, project.user_id)
    except Exception:
        pass  # Gracefully handle if portfolio cache tables don't exist yet
    
    # Ensure project exists
    if not project_exists(db, project_id):
        if user_id is None:
            raise ValueError("user_id is required when creating a new project")
        create_project(db, project_id, user_id=user_id, filename=filename, activity_count=len(activities), file_hash=file_hash)
    else:
        # Update existing project metadata
        update_project_metadata(db, project_id, filename=filename, activity_count=len(activities), file_hash=file_hash)
    
    # Delete existing activities for this project
    db.query(Activity).filter(Activity.project_id == project_id).delete()
    
    # Insert new activities
    for act in activities:
        db_activity = Activity(
            project_id=project_id,
            activity_id=act.activity_id,
            name=act.name,
            planned_start=act.planned_start,
            planned_finish=act.planned_finish,
            baseline_start=act.baseline_start,
            baseline_finish=act.baseline_finish,
            planned_duration=act.planned_duration,
            baseline_duration=act.baseline_duration,
            actual_start=act.actual_start,
            actual_finish=act.actual_finish,
            remaining_duration=act.remaining_duration,
            percent_complete=act.percent_complete,
            # Schedule analysis fields
            early_start=act.early_start,
            early_finish=act.early_finish,
            late_start=act.late_start,
            late_finish=act.late_finish,
            total_float=act.total_float,
            # Risk fields
            risk_probability=act.risk_probability,
            risk_delay_impact_days=act.risk_delay_impact_days,
            predecessors=json.dumps(act.predecessors) if act.predecessors else None,
            successors=json.dumps(act.successors) if act.successors else None,
            on_critical_path=act.on_critical_path,
            resource_id=act.resource_id,
            fte_allocation=act.fte_allocation,
            resource_max_fte=act.resource_max_fte
        )
        db.add(db_activity)
    
    db.commit()


def get_activities(db: Session, project_id: str) -> List[ActivityModel]:
    """Get all activities for a project"""
    db_activities = db.query(Activity).filter(Activity.project_id == project_id).all()
    
    activities = []
    for db_act in db_activities:
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
            # Schedule analysis fields
            early_start=db_act.early_start,
            early_finish=db_act.early_finish,
            late_start=db_act.late_start,
            late_finish=db_act.late_finish,
            total_float=db_act.total_float,
            # Risk fields
            risk_probability=db_act.risk_probability,
            risk_delay_impact_days=db_act.risk_delay_impact_days,
            predecessors=json.loads(db_act.predecessors) if db_act.predecessors else [],
            successors=json.loads(db_act.successors) if db_act.successors else [],
            on_critical_path=db_act.on_critical_path,
            resource_id=db_act.resource_id,
            fte_allocation=db_act.fte_allocation,
            resource_max_fte=db_act.resource_max_fte
        )
        activities.append(act)
    
    return activities


# ========== Audit Log Operations ==========

def log_event_db(db: Session, project_id: str, event: str, details: Optional[Dict] = None):
    """Log an event to database"""
    # Ensure project exists
    if not project_exists(db, project_id):
        create_project(db, project_id)
    
    audit_log = AuditLog(
        project_id=project_id,
        event=event,
        details=details or {}
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def get_audit_logs(db: Session, project_id: str, limit: Optional[int] = None) -> List[Dict]:
    """Get audit logs for a project"""
    query = db.query(AuditLog).filter(AuditLog.project_id == project_id).order_by(AuditLog.timestamp.desc())
    
    if limit:
        query = query.limit(limit)
    
    logs = query.all()
    return [
        {
            "timestamp": log.timestamp.isoformat(),
            "event": log.event,
            "project_id": log.project_id,
            "details": log.details or {}
        }
        for log in logs
    ]


# ========== Delete Operations ==========

def delete_project(db: Session, project_id: str, user_id: int) -> Dict:
    """
    Delete a single project and all related data.
    
    This function:
    1. Verifies project ownership
    2. Deletes all related cache entries (forecast, risks, anomalies, metrics)
    3. Deletes activities (cascade will handle this, but we do it explicitly for clarity)
    4. Deletes audit logs
    5. Deletes the project itself
    6. Invalidates portfolio cache
    
    Returns:
        Dict with deletion summary
    """
    from sqlalchemy import text
    
    # Verify project exists and belongs to user
    project = get_project(db, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")
    
    if project.user_id != user_id:
        raise ValueError(f"Access denied: Project {project_id} belongs to another user")
    
    # Get counts before deletion
    activity_count_result = db.execute(text("""
        SELECT COUNT(*) FROM activities WHERE project_id = :project_id
    """), {"project_id": project_id})
    activity_count = activity_count_result.scalar() or 0
    
    # Delete cache entries (forecast, risks, anomalies, project_metrics)
    try:
        db.execute(text("DELETE FROM forecast_cache WHERE project_id = :project_id"), {"project_id": project_id})
        db.execute(text("DELETE FROM risks_cache WHERE project_id = :project_id"), {"project_id": project_id})
        db.execute(text("DELETE FROM anomalies_cache WHERE project_id = :project_id"), {"project_id": project_id})
        db.execute(text("DELETE FROM project_metrics WHERE project_id = :project_id"), {"project_id": project_id})
    except Exception as e:
        # Cache tables might not exist, continue anyway
        print(f"Warning: Could not delete cache entries: {e}")
    
    # Delete activities (cascade should handle this, but explicit is clearer)
    db.execute(text("DELETE FROM activities WHERE project_id = :project_id"), {"project_id": project_id})
    
    # Delete audit logs
    db.execute(text("DELETE FROM audit_logs WHERE project_id = :project_id"), {"project_id": project_id})
    
    # Delete project
    db.execute(text("DELETE FROM projects WHERE project_id = :project_id"), {"project_id": project_id})
    
    db.commit()
    
    # Invalidate portfolio cache for this user
    try:
        from core.portfolio_cache_service import invalidate_portfolio_cache
        invalidate_portfolio_cache(db, user_id)
    except Exception:
        pass  # Gracefully handle if portfolio cache doesn't exist
    
    return {
        "success": True,
        "project_id": project_id,
        "deleted_activities": activity_count,
        "message": f"Project {project_id} deleted successfully"
    }


def delete_projects(db: Session, project_ids: List[str], user_id: int) -> Dict:
    """
    Delete multiple projects and all related data.
    
    Args:
        db: Database session
        project_ids: List of project IDs to delete
        user_id: User ID to verify ownership
    
    Returns:
        Dict with deletion summary
    """
    from sqlalchemy import text
    
    if not project_ids:
        return {
            "success": True,
            "deleted_projects": 0,
            "deleted_activities": 0,
            "message": "No projects to delete"
        }
    
    # Verify all projects belong to user
    placeholders = ','.join([f':id{i}' for i in range(len(project_ids))])
    params = {f'id{i}': pid for i, pid in enumerate(project_ids)}
    params['user_id'] = user_id
    
    # Check ownership
    ownership_result = db.execute(text(f"""
        SELECT project_id FROM projects 
        WHERE project_id IN ({placeholders}) AND user_id != :user_id
    """), params)
    unauthorized = [row[0] for row in ownership_result]
    
    if unauthorized:
        raise ValueError(f"Access denied: Projects {unauthorized} belong to another user")
    
    # Get counts before deletion
    activity_count_result = db.execute(text(f"""
        SELECT COUNT(*) FROM activities 
        WHERE project_id IN ({placeholders})
    """), params)
    activity_count = activity_count_result.scalar() or 0
    
    project_count_result = db.execute(text(f"""
        SELECT COUNT(*) FROM projects 
        WHERE project_id IN ({placeholders})
    """), params)
    project_count = project_count_result.scalar() or 0
    
    # Delete cache entries
    try:
        db.execute(text(f"DELETE FROM forecast_cache WHERE project_id IN ({placeholders})"), params)
        db.execute(text(f"DELETE FROM risks_cache WHERE project_id IN ({placeholders})"), params)
        db.execute(text(f"DELETE FROM anomalies_cache WHERE project_id IN ({placeholders})"), params)
        db.execute(text(f"DELETE FROM project_metrics WHERE project_id IN ({placeholders})"), params)
    except Exception as e:
        print(f"Warning: Could not delete cache entries: {e}")
    
    # Delete activities
    db.execute(text(f"DELETE FROM activities WHERE project_id IN ({placeholders})"), params)
    
    # Delete audit logs
    db.execute(text(f"DELETE FROM audit_logs WHERE project_id IN ({placeholders})"), params)
    
    # Delete projects
    db.execute(text(f"DELETE FROM projects WHERE project_id IN ({placeholders})"), params)
    
    db.commit()
    
    # Invalidate portfolio cache
    try:
        from core.portfolio_cache_service import invalidate_portfolio_cache
        invalidate_portfolio_cache(db, user_id)
    except Exception:
        pass
    
    return {
        "success": True,
        "deleted_projects": project_count,
        "deleted_activities": activity_count,
        "message": f"Deleted {project_count} projects and {activity_count} activities"
    }
