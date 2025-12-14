"""
Notification Service - SOLID compliant notification system
Handles email, webhook, and future notification channels
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class NotificationChannel(Enum):
    """Supported notification channels"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationProvider(ABC):
    """Abstract base class for notification providers (SOLID: Dependency Inversion)"""
    
    @abstractmethod
    def send(self, recipient: str, subject: str, content: Dict[str, Any], priority: NotificationPriority) -> bool:
        """Send notification to recipient"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate provider configuration"""
        pass


class EmailNotificationProvider(NotificationProvider):
    """Email notification provider implementation"""
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        self.smtp_config = smtp_config or self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default SMTP configuration from environment"""
        import os
        return {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_username": os.getenv("SMTP_USERNAME", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
            "from_email": os.getenv("FROM_EMAIL", "noreply@riskmonitor.com"),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate email configuration"""
        required = ["smtp_server", "smtp_port", "from_email"]
        return all(key in config for key in required)
    
    def send(self, recipient: str, subject: str, content: Dict[str, Any], priority: NotificationPriority) -> bool:
        """Send email notification"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_config["from_email"]
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Create HTML and plain text versions
            html_body = self._format_html_email(content, priority)
            text_body = self._format_text_email(content, priority)
            
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_config["smtp_server"], self.smtp_config["smtp_port"]) as server:
                if self.smtp_config["use_tls"]:
                    server.starttls()
                if self.smtp_config.get("smtp_username"):
                    server.login(self.smtp_config["smtp_username"], self.smtp_config["smtp_password"])
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"[Notification] Email send failed: {e}")
            return False
    
    def _format_html_email(self, content: Dict[str, Any], priority: NotificationPriority) -> str:
        """Format email as HTML"""
        priority_colors = {
            NotificationPriority.CRITICAL: "#dc2626",
            NotificationPriority.HIGH: "#ea580c",
            NotificationPriority.MEDIUM: "#f59e0b",
            NotificationPriority.LOW: "#10b981"
        }
        color = priority_colors.get(priority, "#6b7280")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                .risk-card {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid {color}; border-radius: 4px; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: {color}; color: white; text-decoration: none; border-radius: 4px; margin-top: 10px; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{content.get('title', 'Risk Alert')}</h2>
                </div>
                <div class="content">
                    {content.get('body', '')}
                    {self._format_risk_details(content.get('risk_details', {}))}
                    {self._format_mitigation_options(content.get('mitigation_options', []))}
                    {self._format_action_button(content.get('action_url', ''))}
                </div>
                <div class="footer">
                    <p>This is an automated notification from Schedule Risk Monitoring System</p>
                    <p><a href="{content.get('unsubscribe_url', '#')}">Manage notification preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_text_email(self, content: Dict[str, Any], priority: NotificationPriority) -> str:
        """Format email as plain text"""
        text = f"""
{content.get('title', 'Risk Alert')}

{content.get('body', '')}

{self._format_risk_details_text(content.get('risk_details', {}))}
{self._format_mitigation_options_text(content.get('mitigation_options', []))}

View details: {content.get('action_url', '')}

---
Manage notification preferences: {content.get('unsubscribe_url', '')}
        """
        return text.strip()
    
    def _format_risk_details(self, risk_details: Dict[str, Any]) -> str:
        """Format risk details for HTML"""
        if not risk_details:
            return ""
        
        details_html = "<div class='risk-card'><h3>Risk Details</h3><ul>"
        for key, value in risk_details.items():
            details_html += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        details_html += "</ul></div>"
        return details_html
    
    def _format_risk_details_text(self, risk_details: Dict[str, Any]) -> str:
        """Format risk details for plain text"""
        if not risk_details:
            return ""
        
        text = "Risk Details:\n"
        for key, value in risk_details.items():
            text += f"  - {key.replace('_', ' ').title()}: {value}\n"
        return text
    
    def _format_mitigation_options(self, options: List[Dict[str, Any]]) -> str:
        """Format mitigation options for HTML"""
        if not options:
            return ""
        
        html = "<div class='risk-card'><h3>Recommended Actions</h3><ol>"
        for option in options[:3]:  # Top 3 only
            html += f"<li><strong>{option.get('description', '')}</strong> - Impact: {option.get('impact', 'N/A')}</li>"
        html += "</ol></div>"
        return html
    
    def _format_mitigation_options_text(self, options: List[Dict[str, Any]]) -> str:
        """Format mitigation options for plain text"""
        if not options:
            return ""
        
        text = "Recommended Actions:\n"
        for i, option in enumerate(options[:3], 1):
            text += f"  {i}. {option.get('description', '')} - Impact: {option.get('impact', 'N/A')}\n"
        return text
    
    def _format_action_button(self, url: str) -> str:
        """Format action button for HTML"""
        if not url:
            return ""
        return f'<a href="{url}" class="button">View Details</a>'


class NotificationService:
    """Main notification service (SOLID: Single Responsibility)"""
    
    def __init__(self, providers: Optional[Dict[NotificationChannel, NotificationProvider]] = None):
        """Initialize with notification providers"""
        self.providers = providers or self._get_default_providers()
    
    def _get_default_providers(self) -> Dict[NotificationChannel, NotificationProvider]:
        """Get default notification providers"""
        return {
            NotificationChannel.EMAIL: EmailNotificationProvider()
        }
    
    def register_provider(self, channel: NotificationChannel, provider: NotificationProvider):
        """Register a new notification provider (SOLID: Open/Closed)"""
        self.providers[channel] = provider
    
    def send_notification(
        self,
        channel: NotificationChannel,
        recipient: str,
        subject: str,
        content: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> bool:
        """Send notification via specified channel"""
        provider = self.providers.get(channel)
        if not provider:
            print(f"[Notification] No provider registered for channel: {channel}")
            return False
        
        try:
            return provider.send(recipient, subject, content, priority)
        except Exception as e:
            print(f"[Notification] Failed to send {channel} notification: {e}")
            return False
    
    def send_risk_alert(
        self,
        user_email: str,
        project_id: str,
        activity_id: str,
        activity_name: str,
        risk_score: float,
        explanation: str,
        risk_details: Dict[str, Any],
        mitigation_options: List[Dict[str, Any]],
        base_url: str = "http://localhost:3000"
    ) -> bool:
        """Send high-risk activity alert"""
        priority = NotificationPriority.CRITICAL if risk_score >= 80 else NotificationPriority.HIGH
        
        content = {
            "title": f"🚨 High Risk Alert: {activity_name}",
            "body": f"Activity {activity_id} ({activity_name}) has a risk score of {risk_score:.1f}/100.",
            "risk_details": {
                "Activity ID": activity_id,
                "Activity Name": activity_name,
                "Risk Score": f"{risk_score:.1f}/100",
                "Explanation": explanation,
                **risk_details
            },
            "mitigation_options": mitigation_options,
            "action_url": f"{base_url}/projects/{project_id}/activities/{activity_id}",
            "unsubscribe_url": f"{base_url}/settings/notifications"
        }
        
        subject = f"🚨 High Risk Alert: {activity_name} (Risk Score: {risk_score:.1f})"
        
        return self.send_notification(
            NotificationChannel.EMAIL,
            user_email,
            subject,
            content,
            priority
        )
    
    def send_daily_digest(
        self,
        user_email: str,
        portfolio_summary: Dict[str, Any],
        base_url: str = "http://localhost:3000"
    ) -> bool:
        """Send daily risk digest"""
        high_risk_count = portfolio_summary.get("high_risk_activities", 0)
        new_risks = portfolio_summary.get("new_risks_today", 0)
        
        content = {
            "title": "Daily Risk Digest",
            "body": f"""
            <p>Your portfolio summary for {datetime.now().strftime('%B %d, %Y')}:</p>
            <ul>
                <li><strong>Total Projects:</strong> {portfolio_summary.get('total_projects', 0)}</li>
                <li><strong>High Risk Activities:</strong> {high_risk_count}</li>
                <li><strong>New Risks Today:</strong> {new_risks}</li>
                <li><strong>Portfolio Risk Score:</strong> {portfolio_summary.get('portfolio_risk_score', 0):.1f}</li>
            </ul>
            """,
            "action_url": f"{base_url}/portfolio",
            "unsubscribe_url": f"{base_url}/settings/notifications"
        }
        
        priority = NotificationPriority.HIGH if high_risk_count > 5 else NotificationPriority.MEDIUM
        
        subject = f"Daily Risk Digest: {high_risk_count} High-Risk Activities"
        
        return self.send_notification(
            NotificationChannel.EMAIL,
            user_email,
            subject,
            content,
            priority
        )


# Global notification service instance (can be injected via DI container)
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get global notification service instance (Singleton pattern)"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

