"""
Project service - Application layer
Orchestrates project-related operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from domain.entities import Project, Activity
from domain.interfaces import IProjectRepository, IActivityRepository, IAuditLogRepository
from infrastructure.repositories.project_repository import ProjectRepository
from infrastructure.repositories.activity_repository import ActivityRepository
from infrastructure.repositories.audit_log_repository import AuditLogRepository


class ProjectService:
    """
    Project application service
    Coordinates between repositories and domain logic
    """
    
    def __init__(
        self,
        project_repo: IProjectRepository,
        activity_repo: IActivityRepository,
        audit_repo: IAuditLogRepository
    ):
        self.project_repo = project_repo
        self.activity_repo = activity_repo
        self.audit_repo = audit_repo
    
    def create_project(
        self,
        user_id: int,
        filename: Optional[str] = None,
        activities: Optional[List[Activity]] = None
    ) -> Project:
        """Create a new project with activities"""
        import uuid
        project_id = str(uuid.uuid4())
        
        project = Project(
            project_id=project_id,
            user_id=user_id,
            filename=filename,
            activity_count=len(activities) if activities else 0
        )
        
        project = self.project_repo.create(project)
        
        if activities:
            self.activity_repo.save_all(project_id, activities)
            # Update activity count
            project.activity_count = len(activities)
            project = self.project_repo.update(project)
        
        # Log creation
        from domain.entities import AuditLog
        self.audit_repo.create(AuditLog(
            project_id=project_id,
            event="project_created",
            details={"filename": filename, "activity_count": len(activities) if activities else 0}
        ))
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        return self.project_repo.get_by_id(project_id)
    
    def get_user_projects(self, user_id: int, limit: Optional[int] = None) -> List[Project]:
        """Get all projects for a user"""
        return self.project_repo.get_by_user_id(user_id, limit)
    
    def verify_ownership(self, project_id: str, user_id: int) -> bool:
        """Verify user owns the project"""
        project = self.project_repo.get_by_id(project_id)
        return project is not None and project.user_id == user_id
    
    def get_project_activities(self, project_id: str) -> List[Activity]:
        """Get all activities for a project"""
        return self.activity_repo.get_by_project_id(project_id)
    
    def save_project_activities(
        self,
        project_id: str,
        activities: List[Activity],
        filename: Optional[str] = None
    ) -> None:
        """Save activities for a project"""
        # Ensure project exists
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Save activities
        self.activity_repo.save_all(project_id, activities)
        
        # Update project metadata
        project.activity_count = len(activities)
        if filename:
            project.filename = filename
        self.project_repo.update(project)
        
        # Log update
        from domain.entities import AuditLog
        self.audit_repo.create(AuditLog(
            project_id=project_id,
            event="activities_updated",
            details={"activity_count": len(activities), "filename": filename}
        ))


def create_project_service(db: Session) -> ProjectService:
    """Factory function to create project service with dependencies"""
    project_repo = ProjectRepository(db)
    activity_repo = ActivityRepository(db)
    audit_repo = AuditLogRepository(db)
    return ProjectService(project_repo, activity_repo, audit_repo)

