"""
Domain entities - Core business objects
Following Single Responsibility Principle
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class User:
    """User domain entity"""
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class Project:
    """Project domain entity"""
    project_id: str
    user_id: int
    filename: Optional[str] = None
    activity_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Activity:
    """Activity domain entity"""
    activity_id: str
    name: str
    project_id: str
    planned_start: Optional[str] = None
    planned_finish: Optional[str] = None
    baseline_start: Optional[str] = None
    baseline_finish: Optional[str] = None
    planned_duration: Optional[float] = None
    baseline_duration: Optional[float] = None
    actual_start: Optional[str] = None
    actual_finish: Optional[str] = None
    remaining_duration: Optional[float] = None
    percent_complete: float = 0.0
    risk_probability: float = 0.0
    risk_delay_impact_days: float = 0.0
    predecessors: List[str] = None
    successors: List[str] = None
    on_critical_path: bool = False
    resource_id: Optional[str] = None
    fte_allocation: float = 0.0
    resource_max_fte: float = 1.0
    
    def __post_init__(self):
        if self.predecessors is None:
            self.predecessors = []
        if self.successors is None:
            self.successors = []


@dataclass
class AuditLog:
    """Audit log domain entity"""
    id: Optional[int] = None
    project_id: Optional[str] = None
    user_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    event: str = ""
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class RiskAnalysis:
    """Risk analysis result"""
    activity_id: str
    activity_name: str
    risk_score: float
    current_duration: float
    forecasted_duration: float
    key_factors: List[str]


@dataclass
class Forecast:
    """Forecast result"""
    p50: float
    p80: float
    current_progress: float
    forecast_data: List[Dict[str, Any]]


@dataclass
class MitigationSimulation:
    """Mitigation simulation result"""
    original_risk_score: float
    new_risk_score: float
    original_forecast: Forecast
    new_forecast: Forecast
    impact: str

