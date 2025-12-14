"""
Audit logging functionality
"""

from datetime import datetime
from typing import Dict, List, Optional
from .models import AUDIT_LOG


def log_event(event_type: str, project_id: str, details: Optional[Dict] = None) -> Dict:
    """Log an audit event"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "project_id": project_id,
        "details": details or {}
    }
    AUDIT_LOG.append(log_entry)
    return log_entry


def log_upload(project_id: str, activity_count: int, filename: Optional[str] = None):
    """Log project upload event"""
    return log_event(
        "project_upload",
        project_id,
        {
            "activity_count": activity_count,
            "filename": filename
        }
    )


def log_risk_scan(project_id: str, risk_count: int, top_risk_score: Optional[float] = None):
    """Log risk scan event"""
    return log_event(
        "risk_scan",
        project_id,
        {
            "risk_count": risk_count,
            "top_risk_score": top_risk_score
        }
    )


def log_forecast(project_id: str, p50: int, p80: int):
    """Log forecast event"""
    return log_event(
        "forecast",
        project_id,
        {
            "p50": p50,
            "p80": p80
        }
    )


def log_simulation(project_id: str, activity_id: str, mitigation_type: str, improvement: Dict):
    """Log mitigation simulation event"""
    return log_event(
        "simulation",
        project_id,
        {
            "activity_id": activity_id,
            "mitigation_type": mitigation_type,
            "improvement": improvement
        }
    )


def log_explanation(project_id: str, activity_id: str, use_llm: bool = False):
    """Log explanation request event"""
    return log_event(
        "explanation",
        project_id,
        {
            "activity_id": activity_id,
            "use_llm": use_llm
        }
    )


def get_project_audit_log(project_id: str) -> List[Dict]:
    """Get audit log entries for a specific project"""
    return [entry for entry in AUDIT_LOG if entry.get("project_id") == project_id]


def get_all_audit_logs(limit: Optional[int] = None) -> List[Dict]:
    """Get all audit log entries, optionally limited"""
    logs = AUDIT_LOG.copy()
    if limit:
        logs = logs[-limit:]  # Get most recent entries
    return logs

