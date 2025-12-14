"""
Database connection and session management
DEPRECATED: Use infrastructure.database.connection instead
This file is kept for backward compatibility during migration
"""
import warnings
from infrastructure.database.connection import (
    get_db,
    init_db,
    get_database_manager
)
from infrastructure.database.models import Base

# Backward compatibility exports
engine = get_database_manager().engine
SessionLocal = get_database_manager().session_factory

warnings.warn(
    "core.database is deprecated. Use infrastructure.database.connection instead",
    DeprecationWarning,
    stacklevel=2
)

