"""
Project repository implementation
Implements IProjectRepository interface
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from domain.interfaces import IProjectRepository
from domain.entities import Project
from infrastructure.database.models import ProjectModel


class ProjectRepository(IProjectRepository):
    """Project repository implementation using SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, project: Project) -> Project:
        """Create a new project"""
        db_project = ProjectModel(
            project_id=project.project_id,
            user_id=project.user_id,
            filename=project.filename,
            activity_count=project.activity_count
        )
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)
        return self._to_domain(db_project)
    
    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        db_project = self.db.query(ProjectModel).filter(
            ProjectModel.project_id == project_id
        ).first()
        return self._to_domain(db_project) if db_project else None
    
    def get_by_user_id(self, user_id: int, limit: Optional[int] = None) -> List[Project]:
        """Get projects by user ID"""
        query = self.db.query(ProjectModel).filter(
            ProjectModel.user_id == user_id
        ).order_by(ProjectModel.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        db_projects = query.all()
        return [self._to_domain(p) for p in db_projects]
    
    def update(self, project: Project) -> Project:
        """Update project"""
        db_project = self.db.query(ProjectModel).filter(
            ProjectModel.project_id == project.project_id
        ).first()
        
        if db_project:
            db_project.filename = project.filename
            db_project.activity_count = project.activity_count
            self.db.commit()
            self.db.refresh(db_project)
            return self._to_domain(db_project)
        return project
    
    def exists(self, project_id: str) -> bool:
        """Check if project exists"""
        return self.db.query(ProjectModel).filter(
            ProjectModel.project_id == project_id
        ).first() is not None
    
    def _to_domain(self, db_project: ProjectModel) -> Project:
        """Convert ORM model to domain entity"""
        if db_project is None:
            return None
        return Project(
            project_id=db_project.project_id,
            user_id=db_project.user_id,
            filename=db_project.filename,
            activity_count=db_project.activity_count or 0,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at
        )

