"""
Activity repository implementation
Implements IActivityRepository interface
"""
from sqlalchemy.orm import Session
from typing import List
import json
from domain.interfaces import IActivityRepository
from domain.entities import Activity
from infrastructure.database.models import ActivityModel


class ActivityRepository(IActivityRepository):
    """Activity repository implementation using SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_all(self, project_id: str, activities: List[Activity]) -> None:
        """Save all activities for a project"""
        # Delete existing activities
        self.db.query(ActivityModel).filter(
            ActivityModel.project_id == project_id
        ).delete()
        
        # Insert new activities
        for activity in activities:
            db_activity = ActivityModel(
                project_id=project_id,
                activity_id=activity.activity_id,
                name=activity.name,
                planned_start=activity.planned_start,
                planned_finish=activity.planned_finish,
                baseline_start=activity.baseline_start,
                baseline_finish=activity.baseline_finish,
                planned_duration=activity.planned_duration,
                baseline_duration=activity.baseline_duration,
                actual_start=activity.actual_start,
                actual_finish=activity.actual_finish,
                remaining_duration=activity.remaining_duration,
                percent_complete=activity.percent_complete,
                risk_probability=activity.risk_probability,
                risk_delay_impact_days=activity.risk_delay_impact_days,
                predecessors=json.dumps(activity.predecessors) if activity.predecessors else None,
                successors=json.dumps(activity.successors) if activity.successors else None,
                on_critical_path=activity.on_critical_path,
                resource_id=activity.resource_id,
                fte_allocation=activity.fte_allocation,
                resource_max_fte=activity.resource_max_fte
            )
            self.db.add(db_activity)
        
        self.db.commit()
    
    def get_by_project_id(self, project_id: str) -> List[Activity]:
        """Get all activities for a project"""
        db_activities = self.db.query(ActivityModel).filter(
            ActivityModel.project_id == project_id
        ).all()
        
        return [self._to_domain(a) for a in db_activities]
    
    def _to_domain(self, db_activity: ActivityModel) -> Activity:
        """Convert ORM model to domain entity"""
        return Activity(
            activity_id=db_activity.activity_id,
            name=db_activity.name,
            project_id=db_activity.project_id,
            planned_start=db_activity.planned_start,
            planned_finish=db_activity.planned_finish,
            baseline_start=db_activity.baseline_start,
            baseline_finish=db_activity.baseline_finish,
            planned_duration=db_activity.planned_duration,
            baseline_duration=db_activity.baseline_duration,
            actual_start=db_activity.actual_start,
            actual_finish=db_activity.actual_finish,
            remaining_duration=db_activity.remaining_duration,
            percent_complete=db_activity.percent_complete or 0.0,
            risk_probability=db_activity.risk_probability or 0.0,
            risk_delay_impact_days=db_activity.risk_delay_impact_days or 0.0,
            predecessors=json.loads(db_activity.predecessors) if db_activity.predecessors else [],
            successors=json.loads(db_activity.successors) if db_activity.successors else [],
            on_critical_path=db_activity.on_critical_path or False,
            resource_id=db_activity.resource_id,
            fte_allocation=db_activity.fte_allocation or 0.0,
            resource_max_fte=db_activity.resource_max_fte or 1.0
        )

