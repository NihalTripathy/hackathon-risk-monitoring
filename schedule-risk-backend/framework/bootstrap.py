"""
Application bootstrap - Dependency injection setup
Registers all dependencies in the container
"""
from sqlalchemy.orm import Session
from framework.container import get_container
from infrastructure.database.connection import get_database_manager
from application.services.project_service import create_project_service, ProjectService
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.project_repository import ProjectRepository
from infrastructure.repositories.activity_repository import ActivityRepository
from infrastructure.repositories.audit_log_repository import AuditLogRepository
from domain.interfaces import (
    IUserRepository, IProjectRepository, IActivityRepository, IAuditLogRepository
)


def bootstrap_container():
    """Bootstrap dependency injection container"""
    container = get_container()
    
    # Register database manager as singleton
    db_manager = get_database_manager()
    container.register_singleton(type(db_manager), db_manager)
    
    # Register repository factories (transient - new instance per request)
    def create_user_repo(db: Session) -> IUserRepository:
        return UserRepository(db)
    
    def create_project_repo(db: Session) -> IProjectRepository:
        return ProjectRepository(db)
    
    def create_activity_repo(db: Session) -> IActivityRepository:
        return ActivityRepository(db)
    
    def create_audit_repo(db: Session) -> IAuditLogRepository:
        return AuditLogRepository(db)
    
    # Note: Repositories are created per request, so we don't register them as singletons
    # Instead, services that need them will create them with the db session
    
    return container

