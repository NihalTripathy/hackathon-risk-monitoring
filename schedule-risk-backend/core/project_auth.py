"""
Helper functions to verify project ownership
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import TYPE_CHECKING
from .db_service import get_project

if TYPE_CHECKING:
    from api.auth import UserResponse


def verify_project_ownership(db: Session, project_id: str, user: "UserResponse") -> None:
    """Verify that a project belongs to the user. Raises HTTPException if not."""
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, 
            detail="Access denied: This project belongs to another user"
        )

