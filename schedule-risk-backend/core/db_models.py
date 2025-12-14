"""
SQLAlchemy database models
DEPRECATED: Use infrastructure.database.models instead
This file is kept for backward compatibility during migration
"""
import warnings
from infrastructure.database.models import (
    UserModel as User,
    ProjectModel as Project,
    ActivityModel as Activity,
    AuditLogModel as AuditLog,
    Base
)

# Re-export Base for backward compatibility
__all__ = ['User', 'Project', 'Activity', 'AuditLog', 'Base']

warnings.warn(
    "core.db_models is deprecated. Use infrastructure.database.models instead",
    DeprecationWarning,
    stacklevel=2
)

