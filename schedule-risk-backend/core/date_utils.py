"""
Date utility functions for reference date handling
"""

from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from .db_service import get_project


def get_reference_date_for_project(db: Session, project_id: str) -> Optional[date]:
    """
    Get the reference date for a project.
    
    Always returns None (use today's date) - date selection feature has been removed.
    
    Args:
        db: Database session
        project_id: Project identifier
    
    Returns:
        Always None (use today's date)
    """
    # Always use today's date - date selection feature removed
    return None
