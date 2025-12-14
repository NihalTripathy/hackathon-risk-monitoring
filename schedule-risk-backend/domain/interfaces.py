"""
Domain interfaces - Contracts for repositories and services
Following Interface Segregation Principle (SOLID)
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import User, Project, Activity, AuditLog


class IUserRepository(ABC):
    """User repository interface"""
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass


class IProjectRepository(ABC):
    """Project repository interface"""
    
    @abstractmethod
    def create(self, project: Project) -> Project:
        """Create a new project"""
        pass
    
    @abstractmethod
    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int, limit: Optional[int] = None) -> List[Project]:
        """Get projects by user ID"""
        pass
    
    @abstractmethod
    def update(self, project: Project) -> Project:
        """Update project"""
        pass
    
    @abstractmethod
    def exists(self, project_id: str) -> bool:
        """Check if project exists"""
        pass


class IActivityRepository(ABC):
    """Activity repository interface"""
    
    @abstractmethod
    def save_all(self, project_id: str, activities: List[Activity]) -> None:
        """Save all activities for a project"""
        pass
    
    @abstractmethod
    def get_by_project_id(self, project_id: str) -> List[Activity]:
        """Get all activities for a project"""
        pass


class IAuditLogRepository(ABC):
    """Audit log repository interface"""
    
    @abstractmethod
    def create(self, audit_log: AuditLog) -> AuditLog:
        """Create audit log entry"""
        pass
    
    @abstractmethod
    def get_by_project_id(self, project_id: str, limit: Optional[int] = None) -> List[AuditLog]:
        """Get audit logs for a project"""
        pass


class ILLMProvider(ABC):
    """LLM provider interface - Open/Closed Principle"""
    
    @abstractmethod
    async def explain_risk(self, activity: Activity, features: dict, risk_score: float) -> dict:
        """Generate risk explanation"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class IRiskAnalyzer(ABC):
    """Risk analyzer interface"""
    
    @abstractmethod
    def analyze(self, activities: List[Activity]) -> List[dict]:
        """Analyze risks for activities"""
        pass


class IForecaster(ABC):
    """Forecaster interface"""
    
    @abstractmethod
    def forecast(self, activities: List[Activity]) -> dict:
        """Generate forecast"""
        pass


class IMitigationSimulator(ABC):
    """Mitigation simulator interface"""
    
    @abstractmethod
    def simulate(self, activities: List[Activity], activity_id: str, 
                 duration_reduction: float, risk_mitigation: float) -> dict:
        """Simulate mitigation"""
        pass

