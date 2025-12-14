"""
Audit log repository implementation
Implements IAuditLogRepository interface
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from domain.interfaces import IAuditLogRepository
from domain.entities import AuditLog
from infrastructure.database.models import AuditLogModel


class AuditLogRepository(IAuditLogRepository):
    """Audit log repository implementation using SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, audit_log: AuditLog) -> AuditLog:
        """Create audit log entry"""
        db_log = AuditLogModel(
            project_id=audit_log.project_id,
            event=audit_log.event,
            details=audit_log.details or {}
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return self._to_domain(db_log)
    
    def get_by_project_id(self, project_id: str, limit: Optional[int] = None) -> List[AuditLog]:
        """Get audit logs for a project"""
        query = self.db.query(AuditLogModel).filter(
            AuditLogModel.project_id == project_id
        ).order_by(AuditLogModel.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        db_logs = query.all()
        return [self._to_domain(log) for log in db_logs]
    
    def _to_domain(self, db_log: AuditLogModel) -> AuditLog:
        """Convert ORM model to domain entity"""
        if db_log is None:
            return None
        return AuditLog(
            id=db_log.id,
            project_id=db_log.project_id,
            timestamp=db_log.timestamp,
            event=db_log.event,
            details=db_log.details or {}
        )

