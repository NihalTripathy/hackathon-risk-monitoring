"""
Anomaly Explanation Service - Priority 5: Contextual Zombie Task Explanations
SOLID compliant service for generating business-context explanations of anomalies
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import Activity
else:
    # Runtime import to avoid circular dependency
    Activity = None


class AnomalyExplanationService:
    """Service for generating contextual explanations of anomalies"""
    
    def explain_zombie_task(
        self,
        zombie_task: Dict[str, Any],
        activities: List[Any],  # Activity type
        project_id: str
    ) -> Dict[str, Any]:
        """Generate business-context explanation for zombie task"""
        activity_id = zombie_task.get("activity_id")
        days_overdue = zombie_task.get("days_overdue", 0)
        
        # Find the activity
        activity = next((a for a in activities if a.activity_id == activity_id), None)
        if not activity:
            return self._default_explanation(zombie_task)
        
        # Calculate cascade impact
        blocked_tasks = self._count_blocked_successors(activity_id, activities)
        
        # Calculate urgency
        urgency_days = self._calculate_urgency(zombie_task, activity, activities)
        
        # Generate business impact explanation
        business_impact = self._generate_business_impact(
            activity_id,
            days_overdue,
            blocked_tasks,
            urgency_days,
            activity
        )
        
        return {
            "activity_id": activity_id,
            "activity_name": zombie_task.get("name", "Unknown"),
            "days_overdue": days_overdue,
            "business_impact": business_impact,
            "blocked_tasks_count": blocked_tasks,
            "urgency_days": urgency_days,
            "plain_language": self._generate_plain_language(
                activity_id,
                days_overdue,
                blocked_tasks,
                urgency_days
            ),
            "recommended_action": self._generate_recommended_action(
                days_overdue,
                blocked_tasks,
                urgency_days
            )
        }
    
    def _count_blocked_successors(self, activity_id: str, activities: List[Any]) -> int:
        """Count how many tasks are blocked by this zombie task"""
        blocked = set()
        
        def traverse_successors(current_id: str, visited: set):
            if current_id in visited:
                return
            visited.add(current_id)
            
            current_activity = next((a for a in activities if a.activity_id == current_id), None)
            if not current_activity:
                return
            
            # Get successors
            if hasattr(current_activity, 'successors') and current_activity.successors:
                for succ_id in current_activity.successors:
                    if succ_id and succ_id.strip():
                        blocked.add(succ_id.strip())
                        traverse_successors(succ_id.strip(), visited)
        
        traverse_successors(activity_id, set())
        return len(blocked)
    
    def _calculate_urgency(
        self,
        zombie_task: Dict[str, Any],
        activity: Any,  # Activity type
        activities: List[Any]
    ) -> int:
        """Calculate urgency in days (how many days until critical impact)"""
        days_overdue = zombie_task.get("days_overdue", 0)
        
        # If on critical path, urgency is immediate
        if hasattr(activity, 'on_critical_path') and activity.on_critical_path:
            return 0
        
        # Check float days
        float_days = 0
        if hasattr(activity, 'total_float') and activity.total_float is not None:
            float_days = activity.total_float
        
        # Urgency = float_days - days_overdue (negative means already critical)
        urgency = max(0, float_days - days_overdue)
        
        return int(urgency)
    
    def _generate_business_impact(
        self,
        activity_id: str,
        days_overdue: int,
        blocked_tasks: int,
        urgency_days: int,
        activity: Any  # Activity type
    ) -> Dict[str, Any]:
        """Generate business impact analysis"""
        impact = {
            "severity": "critical" if urgency_days == 0 else "high" if urgency_days <= 2 else "medium",
            "cascade_risk": "high" if blocked_tasks > 5 else "medium" if blocked_tasks > 2 else "low",
            "project_delay_risk": days_overdue if hasattr(activity, 'on_critical_path') and activity.on_critical_path else 0,
            "blocked_tasks": blocked_tasks
        }
        
        return impact
    
    def _generate_plain_language(
        self,
        activity_id: str,
        days_overdue: int,
        blocked_tasks: int,
        urgency_days: int
    ) -> str:
        """Generate plain-language explanation"""
        explanation = f"Task {activity_id} is {days_overdue} day{'s' if days_overdue != 1 else ''} overdue and hasn't started yet. "
        
        if blocked_tasks > 0:
            explanation += f"If not started soon, it will block {blocked_tasks} downstream task{'s' if blocked_tasks != 1 else ''}. "
        
        if urgency_days == 0:
            explanation += "This is a critical issue requiring immediate attention. "
        elif urgency_days <= 2:
            explanation += f"Action needed within {urgency_days} day{'s' if urgency_days != 1 else ''} to avoid critical path impact. "
        
        if blocked_tasks > 5:
            explanation += "The high number of blocked tasks means this delay could cascade across multiple project areas. "
        
        return explanation.strip()
    
    def _generate_recommended_action(
        self,
        days_overdue: int,
        blocked_tasks: int,
        urgency_days: int
    ) -> str:
        """Generate recommended action"""
        if urgency_days == 0:
            return "Immediate action required: Assign resources immediately or escalate to project sponsor."
        elif urgency_days <= 2:
            return "Urgent: Review resource allocation and consider adding team members or adjusting scope."
        elif blocked_tasks > 5:
            return "High priority: This task blocks many downstream activities. Consider fast-tracking or parallel work."
        else:
            return "Monitor closely and ensure resources are available to start this task soon."
    
    def _default_explanation(self, zombie_task: Dict[str, Any]) -> Dict[str, Any]:
        """Default explanation if activity not found"""
        return {
            "activity_id": zombie_task.get("activity_id", "Unknown"),
            "activity_name": zombie_task.get("name", "Unknown"),
            "days_overdue": zombie_task.get("days_overdue", 0),
            "business_impact": {
                "severity": "medium",
                "cascade_risk": "unknown",
                "project_delay_risk": 0,
                "blocked_tasks": 0
            },
            "blocked_tasks_count": 0,
            "urgency_days": 0,
            "plain_language": f"Task {zombie_task.get('activity_id', 'Unknown')} is overdue and hasn't started.",
            "recommended_action": "Review task status and resource allocation."
        }


# Global service instance
_anomaly_explanation_service: Optional[AnomalyExplanationService] = None


def get_anomaly_explanation_service() -> AnomalyExplanationService:
    """Get global anomaly explanation service instance"""
    global _anomaly_explanation_service
    if _anomaly_explanation_service is None:
        _anomaly_explanation_service = AnomalyExplanationService()
    return _anomaly_explanation_service

