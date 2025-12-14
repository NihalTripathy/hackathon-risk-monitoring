"""
Database connection and session management
Infrastructure layer - handles database connectivity
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional
import os


class DatabaseConfig:
    """Database configuration - Single Responsibility Principle"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/schedule_risk_db"
        )
    
    def create_engine(self):
        """Create SQLAlchemy engine"""
        return create_engine(self.database_url, echo=False)


class DatabaseManager:
    """Manages database connection and sessions"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine = None
        self._session_factory = None
    
    @property
    def engine(self):
        """Get or create engine"""
        if self._engine is None:
            self._engine = self.config.create_engine()
        return self._engine
    
    @property
    def session_factory(self):
        """Get or create session factory"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
        return self._session_factory
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session - dependency injection"""
        db = self.session_factory()
        try:
            yield db
        finally:
            db.close()
    
    def init_database(self):
        """Initialize database - create all tables"""
        from infrastructure.database import models
        models.Base.metadata.create_all(bind=self.engine)


# Global database manager instance
_db_manager: DatabaseManager = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager"""
    global _db_manager
    if _db_manager is None:
        config = DatabaseConfig()
        _db_manager = DatabaseManager(config)
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session"""
    manager = get_database_manager()
    yield from manager.get_session()


def init_db():
    """Initialize database tables"""
    from infrastructure.database import models
    manager = get_database_manager()
    models.Base.metadata.create_all(bind=manager.engine)

