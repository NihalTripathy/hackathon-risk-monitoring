"""
Webhook Service - Priority 4: Webhook Integration
SOLID compliant service for sending webhooks to external systems
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import httpx
import json
import hmac
import hashlib
import time


class WebhookType(Enum):
    """Supported webhook types"""
    SLACK = "slack"
    TEAMS = "teams"
    JIRA = "jira"
    GENERIC = "generic"


class WebhookFormatter(ABC):
    """Abstract base class for webhook formatters (SOLID: Dependency Inversion)"""
    
    @abstractmethod
    def format_payload(self, event_type: str, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Format payload for specific webhook type"""
        pass


class SlackWebhookFormatter(WebhookFormatter):
    """Slack webhook formatter"""
    
    def format_payload(self, event_type: str, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Format payload for Slack"""
        risk_score = data.get("risk_score", 0)
        color = "#dc2626" if risk_score >= 70 else "#ea580c" if risk_score >= 40 else "#10b981"
        
        payload = {
            "text": f"🚨 Risk Alert: {data.get('activity_name', 'Unknown')}",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "Activity",
                            "value": f"{data.get('activity_id', 'N/A')}: {data.get('activity_name', 'N/A')}",
                            "short": True
                        },
                        {
                            "title": "Risk Score",
                            "value": f"{risk_score:.1f}/100",
                            "short": True
                        },
                        {
                            "title": "Project",
                            "value": data.get("project_id", "N/A"),
                            "short": True
                        },
                        {
                            "title": "Explanation",
                            "value": data.get("explanation", "No explanation available"),
                            "short": False
                        }
                    ],
                    "actions": [
                        {
                            "type": "button",
                            "text": "View Details",
                            "url": data.get("action_url", "")
                        }
                    ],
                    "footer": "Schedule Risk Monitoring",
                    "ts": int(time.time())
                }
            ]
        }
        
        return payload


class TeamsWebhookFormatter(WebhookFormatter):
    """Microsoft Teams webhook formatter"""
    
    def format_payload(self, event_type: str, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Format payload for Teams"""
        risk_score = data.get("risk_score", 0)
        theme_color = "FF0000" if risk_score >= 70 else "FF8C00" if risk_score >= 40 else "00FF00"
        
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": theme_color,
            "summary": f"Risk Alert: {data.get('activity_name', 'Unknown')}",
            "sections": [
                {
                    "activityTitle": f"🚨 Risk Alert: {data.get('activity_name', 'Unknown')}",
                    "facts": [
                        {
                            "name": "Activity ID",
                            "value": data.get("activity_id", "N/A")
                        },
                        {
                            "name": "Risk Score",
                            "value": f"{risk_score:.1f}/100"
                        },
                        {
                            "name": "Project",
                            "value": data.get("project_id", "N/A")
                        },
                        {
                            "name": "Explanation",
                            "value": data.get("explanation", "No explanation available")
                        }
                    ]
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Details",
                    "targets": [
                        {
                            "os": "default",
                            "uri": data.get("action_url", "")
                        }
                    ]
                }
            ]
        }
        
        return payload


class JiraWebhookFormatter(WebhookFormatter):
    """Jira webhook formatter"""
    
    def format_payload(self, event_type: str, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Format payload for Jira (creates issue)"""
        risk_score = data.get("risk_score", 0)
        priority = "Highest" if risk_score >= 70 else "High" if risk_score >= 40 else "Medium"
        
        payload = {
            "fields": {
                "project": {"key": config.get("jira_project_key", "RISK")},
                "summary": f"Risk Alert: {data.get('activity_name', 'Unknown')} - Risk Score: {risk_score:.1f}",
                "description": f"""
                *Activity ID:* {data.get('activity_id', 'N/A')}
                *Project:* {data.get('project_id', 'N/A')}
                *Risk Score:* {risk_score:.1f}/100
                
                *Explanation:*
                {data.get('explanation', 'No explanation available')}
                
                *View Details:* {data.get('action_url', '')}
                """,
                "issuetype": {"name": "Task"},
                "priority": {"name": priority},
                "labels": ["risk-alert", "automated"]
            }
        }
        
        return payload


class GenericWebhookFormatter(WebhookFormatter):
    """Generic webhook formatter (uses custom template if provided)"""
    
    def format_payload(self, event_type: str, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Format payload using custom template or default format"""
        template = config.get("payload_template")
        
        if template:
            # Use custom template
            payload = template.copy()
            # Replace placeholders
            for key, value in payload.items():
                if isinstance(value, str):
                    payload[key] = value.format(**data)
        else:
            # Default format
            payload = {
                "event_type": event_type,
                "timestamp": time.time(),
                "data": data
            }
        
        return payload


class WebhookService:
    """Main webhook service (SOLID: Single Responsibility)"""
    
    def __init__(self):
        """Initialize with webhook formatters"""
        self.formatters = {
            WebhookType.SLACK: SlackWebhookFormatter(),
            WebhookType.TEAMS: TeamsWebhookFormatter(),
            WebhookType.JIRA: JiraWebhookFormatter(),
            WebhookType.GENERIC: GenericWebhookFormatter()
        }
    
    def register_formatter(self, webhook_type: WebhookType, formatter: WebhookFormatter):
        """Register a new webhook formatter (SOLID: Open/Closed)"""
        self.formatters[webhook_type] = formatter
    
    async def send_webhook(
        self,
        webhook_url: str,
        webhook_type: WebhookType,
        event_type: str,
        data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        secret_key: Optional[str] = None
    ) -> bool:
        """Send webhook to external system"""
        formatter = self.formatters.get(webhook_type)
        if not formatter:
            print(f"[Webhook] No formatter for type: {webhook_type}")
            return False
        
        try:
            # Format payload
            payload = formatter.format_payload(event_type, data, config or {})
            
            # Add signature if secret key provided
            headers = {"Content-Type": "application/json"}
            if secret_key:
                signature = self._generate_signature(payload, secret_key)
                headers["X-Webhook-Signature"] = signature
            
            # Send webhook
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload, headers=headers)
                response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"[Webhook] Failed to send webhook: {e}")
            return False
    
    def _generate_signature(self, payload: Dict[str, Any], secret_key: str) -> str:
        """Generate HMAC signature for webhook payload"""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret_key.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"


# Global webhook service instance
_webhook_service: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """Get global webhook service instance"""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service

