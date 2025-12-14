"""
Activity adapter - Converts between domain entities and legacy models
"""
from typing import List
from domain.entities import Activity as DomainActivity
from core.models import Activity as LegacyActivity


def to_domain_activity(legacy: LegacyActivity, project_id: str) -> DomainActivity:
    """Convert legacy Activity model to domain entity"""
    return DomainActivity(
        activity_id=legacy.activity_id,
        name=legacy.name,
        project_id=project_id,
        planned_start=legacy.planned_start,
        planned_finish=legacy.planned_finish,
        baseline_start=legacy.baseline_start,
        baseline_finish=legacy.baseline_finish,
        planned_duration=legacy.planned_duration,
        baseline_duration=legacy.baseline_duration,
        actual_start=legacy.actual_start,
        actual_finish=legacy.actual_finish,
        remaining_duration=legacy.remaining_duration,
        percent_complete=legacy.percent_complete or 0.0,
        risk_probability=legacy.risk_probability or 0.0,
        risk_delay_impact_days=legacy.risk_delay_impact_days or 0.0,
        predecessors=legacy.predecessors or [],
        successors=legacy.successors or [],
        on_critical_path=legacy.on_critical_path or False,
        resource_id=legacy.resource_id,
        fte_allocation=legacy.fte_allocation or 0.0,
        resource_max_fte=legacy.resource_max_fte or 1.0
    )


def to_legacy_activity(domain: DomainActivity) -> LegacyActivity:
    """Convert domain entity to legacy Activity model"""
    return LegacyActivity(
        activity_id=domain.activity_id,
        name=domain.name,
        planned_start=domain.planned_start,
        planned_finish=domain.planned_finish,
        baseline_start=domain.baseline_start,
        baseline_finish=domain.baseline_finish,
        planned_duration=domain.planned_duration,
        baseline_duration=domain.baseline_duration,
        actual_start=domain.actual_start,
        actual_finish=domain.actual_finish,
        remaining_duration=domain.remaining_duration,
        percent_complete=domain.percent_complete,
        risk_probability=domain.risk_probability,
        risk_delay_impact_days=domain.risk_delay_impact_days,
        predecessors=domain.predecessors,
        successors=domain.successors,
        on_critical_path=domain.on_critical_path,
        resource_id=domain.resource_id,
        fte_allocation=domain.fte_allocation,
        resource_max_fte=domain.resource_max_fte
    )


def to_domain_activities(legacy_list: List[LegacyActivity], project_id: str) -> List[DomainActivity]:
    """Convert list of legacy activities to domain entities"""
    return [to_domain_activity(legacy, project_id) for legacy in legacy_list]


def to_legacy_activities(domain_list: List[DomainActivity]) -> List[LegacyActivity]:
    """Convert list of domain entities to legacy models"""
    return [to_legacy_activity(domain) for domain in domain_list]

