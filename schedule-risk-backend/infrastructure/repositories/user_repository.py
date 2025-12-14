"""
User repository implementation
Implements IUserRepository interface
"""
from sqlalchemy.orm import Session
from typing import Optional
from domain.interfaces import IUserRepository
from domain.entities import User
from infrastructure.database.models import UserModel


class UserRepository(IUserRepository):
    """User repository implementation using SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user: User) -> User:
        """Create a new user"""
        db_user = UserModel(
            email=user.email,
            hashed_password=getattr(user, 'hashed_password', ''),  # Password should be hashed before
            full_name=user.full_name,
            is_active=user.is_active
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_domain(db_user)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_domain(db_user) if db_user else None
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain(db_user) if db_user else None
    
    def _to_domain(self, db_user: UserModel) -> User:
        """Convert ORM model to domain entity"""
        if db_user is None:
            return None
        user = User(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
        # Store hashed password for authentication
        user.hashed_password = db_user.hashed_password
        return user

