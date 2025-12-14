"""
Data models and schemas
"""

from pydantic import BaseModel
from typing import List, Optional


class Activity(BaseModel):
    activity_id: str
    name: str
    planned_start: Optional[str]
    planned_finish: Optional[str]
    baseline_start: Optional[str]
    baseline_finish: Optional[str]
    planned_duration: Optional[float]
    baseline_duration: Optional[float]
    actual_start: Optional[str]
    actual_finish: Optional[str]
    remaining_duration: Optional[float]
    percent_complete: float
    # Schedule analysis fields (ES, EF, LS, LF, Total_Float)
    early_start: Optional[str] = None  # ES
    early_finish: Optional[str] = None  # EF
    late_start: Optional[str] = None  # LS
    late_finish: Optional[str] = None  # LF
    total_float: Optional[float] = None  # Total_Float
    # Risk fields
    risk_probability: float
    risk_delay_impact_days: float
    cost_impact_of_risk: Optional[float] = None  # Cost_Impact_of_Risk
    # Cost fields for Forensic Intelligence
    planned_cost: Optional[float] = None  # Planned_Cost
    actual_cost_to_date: Optional[float] = None  # Actual_Cost_To_Date
    # Dependency fields
    predecessors: List[str] = []
    successors: List[str] = []
    on_critical_path: bool = False
    # Resource fields
    resource_id: Optional[str] = None
    role: Optional[str] = None  # Role
    fte_allocation: Optional[float] = 0.0
    resource_max_fte: Optional[float] = 1.0
    skill_tags: Optional[str] = None  # Skill_Tags (comma-separated or semicolon-separated)


PROJECTS = {}

DIGITAL_TWINS = {}

AUDIT_LOG = []

