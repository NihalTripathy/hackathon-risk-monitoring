"""
Webhook API endpoints - Priority 4: Webhook Integration
SOLID compliant webhook management
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
from core.database import get_db
from core.auth_dependencies import get_current_user
from core.webhook_service import get_webhook_service, WebhookType
from api.auth import UserResponse
from infrastructure.database.models import WebhookConfigurationModel, ProjectModel
from sqlalchemy import and_

router = APIRouter()


class WebhookConfigurationRequest(BaseModel):
    """Request model for webhook configuration"""
    name: str
    webhook_url: HttpUrl
    webhook_type: str  # slack, teams, jira, generic
    project_id: Optional[str] = None  # None = all projects
    triggers: Dict[str, bool]  # {risk_alert: bool, daily_digest: bool, anomaly: bool}
    risk_threshold: float = 70.0
    payload_template: Optional[Dict[str, Any]] = None
    secret_key: Optional[str] = None


class WebhookConfigurationResponse(BaseModel):
    """Response model for webhook configuration"""
    id: int
    name: str
    webhook_url: str
    webhook_type: str
    project_id: Optional[str]
    triggers: Dict[str, bool]
    risk_threshold: float
    enabled: bool
    last_triggered: Optional[str]
    failure_count: int


@router.post("/webhooks", response_model=WebhookConfigurationResponse)
def create_webhook(
    request: WebhookConfigurationRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new webhook configuration"""
    # Validate webhook type
    try:
        webhook_type = WebhookType(request.webhook_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid webhook_type. Must be one of: {[wt.value for wt in WebhookType]}"
        )
    
    # Validate project ownership if project_id provided
    if request.project_id:
        project = db.query(ProjectModel).filter(
            and_(
                ProjectModel.project_id == request.project_id,
                ProjectModel.user_id == current_user.id
            )
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Create webhook configuration
    webhook = WebhookConfigurationModel(
        user_id=current_user.id,
        project_id=request.project_id,
        name=request.name,
        webhook_url=str(request.webhook_url),
        webhook_type=request.webhook_type.lower(),
        triggers=request.triggers,
        risk_threshold=request.risk_threshold,
        payload_template=request.payload_template,
        secret_key=request.secret_key,
        enabled=True
    )
    
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    
    return WebhookConfigurationResponse(
        id=webhook.id,
        name=webhook.name,
        webhook_url=webhook.webhook_url,
        webhook_type=webhook.webhook_type,
        project_id=webhook.project_id,
        triggers=webhook.triggers,
        risk_threshold=webhook.risk_threshold,
        enabled=webhook.enabled,
        last_triggered=webhook.last_triggered.isoformat() if webhook.last_triggered else None,
        failure_count=webhook.failure_count
    )


@router.get("/webhooks", response_model=List[WebhookConfigurationResponse])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """List all webhook configurations for user"""
    webhooks = db.query(WebhookConfigurationModel).filter(
        WebhookConfigurationModel.user_id == current_user.id
    ).all()
    
    return [
        WebhookConfigurationResponse(
            id=w.id,
            name=w.name,
            webhook_url=w.webhook_url,
            webhook_type=w.webhook_type,
            project_id=w.project_id,
            triggers=w.triggers,
            risk_threshold=w.risk_threshold,
            enabled=w.enabled,
            last_triggered=w.last_triggered.isoformat() if w.last_triggered else None,
            failure_count=w.failure_count
        )
        for w in webhooks
    ]


@router.put("/webhooks/{webhook_id}", response_model=WebhookConfigurationResponse)
def update_webhook(
    webhook_id: int,
    request: WebhookConfigurationRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update webhook configuration"""
    webhook = db.query(WebhookConfigurationModel).filter(
        and_(
            WebhookConfigurationModel.id == webhook_id,
            WebhookConfigurationModel.user_id == current_user.id
        )
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Update fields
    webhook.name = request.name
    webhook.webhook_url = str(request.webhook_url)
    webhook.webhook_type = request.webhook_type.lower()
    webhook.triggers = request.triggers
    webhook.risk_threshold = request.risk_threshold
    webhook.payload_template = request.payload_template
    if request.secret_key:
        webhook.secret_key = request.secret_key
    
    db.commit()
    db.refresh(webhook)
    
    return WebhookConfigurationResponse(
        id=webhook.id,
        name=webhook.name,
        webhook_url=webhook.webhook_url,
        webhook_type=webhook.webhook_type,
        project_id=webhook.project_id,
        triggers=webhook.triggers,
        risk_threshold=webhook.risk_threshold,
        enabled=webhook.enabled,
        last_triggered=webhook.last_triggered.isoformat() if webhook.last_triggered else None,
        failure_count=webhook.failure_count
    )


@router.delete("/webhooks/{webhook_id}")
def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete webhook configuration"""
    webhook = db.query(WebhookConfigurationModel).filter(
        and_(
            WebhookConfigurationModel.id == webhook_id,
            WebhookConfigurationModel.user_id == current_user.id
        )
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    db.delete(webhook)
    db.commit()
    
    return {"message": "Webhook deleted successfully"}


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Test webhook configuration"""
    webhook = db.query(WebhookConfigurationModel).filter(
        and_(
            WebhookConfigurationModel.id == webhook_id,
            WebhookConfigurationModel.user_id == current_user.id
        )
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Send test webhook
    webhook_service = get_webhook_service()
    test_data = {
        "activity_id": "TEST-001",
        "activity_name": "Test Activity",
        "risk_score": 75.0,
        "explanation": "This is a test webhook from Schedule Risk Monitoring System",
        "project_id": "test-project",
        "action_url": "http://localhost:3000"
    }
    
    try:
        webhook_type = WebhookType(webhook.webhook_type)
        success = await webhook_service.send_webhook(
            webhook_url=webhook.webhook_url,
            webhook_type=webhook_type,
            event_type="test",
            data=test_data,
            config=webhook.payload_template or {},
            secret_key=webhook.secret_key
        )
        
        if success:
            webhook.last_triggered = datetime.now()
            webhook.failure_count = 0
            db.commit()
            return {"message": "Test webhook sent successfully"}
        else:
            webhook.failure_count += 1
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to send test webhook")
    except Exception as e:
        webhook.failure_count += 1
        db.commit()
        raise HTTPException(status_code=500, detail=f"Webhook test failed: {str(e)}")


async def trigger_webhooks_for_risk_alert(
    db: Session,
    user_id: int,
    project_id: str,
    event_data: Dict[str, Any]
):
    """Trigger webhooks for risk alert (called from risk pipeline)"""
    # Get enabled webhooks for user
    webhooks = db.query(WebhookConfigurationModel).filter(
        and_(
            WebhookConfigurationModel.user_id == user_id,
            WebhookConfigurationModel.enabled == True,
            WebhookConfigurationModel.triggers['risk_alert'].astext == 'true'
        )
    ).all()
    
    webhook_service = get_webhook_service()
    
    for webhook in webhooks:
        # Check if webhook applies to this project
        if webhook.project_id and webhook.project_id != project_id:
            continue
        
        # Check risk threshold
        risk_score = event_data.get("risk_score", 0)
        if risk_score < webhook.risk_threshold:
            continue
        
        try:
            webhook_type = WebhookType(webhook.webhook_type)
            success = await webhook_service.send_webhook(
                webhook_url=webhook.webhook_url,
                webhook_type=webhook_type,
                event_type="risk_alert",
                data=event_data,
                config=webhook.payload_template or {},
                secret_key=webhook.secret_key
            )
            
            if success:
                webhook.last_triggered = datetime.now()
                webhook.failure_count = 0
            else:
                webhook.failure_count += 1
        except Exception as e:
            print(f"[Webhook] Failed to trigger webhook {webhook.id}: {e}")
            webhook.failure_count += 1
    
    db.commit()

