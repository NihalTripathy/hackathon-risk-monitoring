"""
Feedback API endpoints - Priority 8: Feedback Mechanism
SOLID compliant feedback collection and management
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from core.database import get_db
from core.auth_dependencies import get_current_user, get_optional_user
from api.auth import UserResponse
from infrastructure.database.models import UserFeedbackModel
from datetime import datetime

router = APIRouter()


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback"""
    feedback_type: str  # explanation, forecast, mitigation, general
    context_id: Optional[str] = None  # activity_id, project_id, etc.
    was_helpful: Optional[bool] = None
    feedback_text: Optional[str] = None
    rating: Optional[int] = None  # 1-5
    page_url: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    id: int
    message: str


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserResponse] = Depends(get_optional_user),
    http_request: Request = None
):
    """Submit user feedback (can be anonymous)"""
    # Validate feedback type
    valid_types = ["explanation", "forecast", "mitigation", "general"]
    if request.feedback_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"feedback_type must be one of: {valid_types}"
        )
    
    # Validate rating
    if request.rating is not None:
        if request.rating < 1 or request.rating > 5:
            raise HTTPException(
                status_code=400,
                detail="rating must be between 1 and 5"
            )
    
    # Get user agent
    user_agent = None
    if http_request:
        user_agent = http_request.headers.get("user-agent")
    
    # Create feedback record
    feedback = UserFeedbackModel(
        user_id=current_user.id if current_user else None,
        feedback_type=request.feedback_type,
        context_id=request.context_id,
        was_helpful=request.was_helpful,
        feedback_text=request.feedback_text,
        rating=request.rating,
        page_url=request.page_url,
        user_agent=user_agent,
        processed=False
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return FeedbackResponse(
        id=feedback.id,
        message="Thank you for your feedback! It helps us improve the system."
    )


@router.get("/feedback/stats")
def get_feedback_stats(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get feedback statistics (for admin/analytics)"""
    from sqlalchemy import func
    
    # Only allow users to see their own feedback stats
    total_feedback = db.query(func.count(UserFeedbackModel.id)).filter(
        UserFeedbackModel.user_id == current_user.id
    ).scalar()
    
    helpful_count = db.query(func.count(UserFeedbackModel.id)).filter(
        and_(
            UserFeedbackModel.user_id == current_user.id,
            UserFeedbackModel.was_helpful == True
        )
    ).scalar()
    
    avg_rating = db.query(func.avg(UserFeedbackModel.rating)).filter(
        and_(
            UserFeedbackModel.user_id == current_user.id,
            UserFeedbackModel.rating.isnot(None)
        )
    ).scalar()
    
    return {
        "total_feedback": total_feedback or 0,
        "helpful_count": helpful_count or 0,
        "helpful_percentage": (helpful_count / total_feedback * 100) if total_feedback > 0 else 0,
        "average_rating": round(float(avg_rating), 2) if avg_rating else None
    }

