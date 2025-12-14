"""
Database adapter - provides compatibility layer for existing code
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from .db_service import get_activities, project_exists, log_event_db
from .models import Activity as ActivityModel


def get_project_activities(db: Session, project_id: str) -> List[ActivityModel]:
    """Get activities for a project from database"""
    if not project_exists(db, project_id):
        return []
    return get_activities(db, project_id)


def log_to_db(db: Session, project_id: str, event: str, details: Optional[Dict] = None):
    """Log event to database"""
    log_event_db(db, project_id, event, details)

