"""
Data validation for connector activities.
Ensures data safety and integrity.
"""

from typing import List, Optional
from core.models import Activity
from datetime import datetime
import re


class ValidationError(Exception):
    """Raised when activity validation fails"""
    pass


class ActivityValidator:
    """
    Validates Activity objects for data safety and integrity.
    """
    
    def __init__(
        self,
        max_activities: int = 10000,
        allowed_fields: Optional[List[str]] = None
    ):
        self.max_activities = max_activities
        self.allowed_fields = allowed_fields
    
    def validate(self, activity: Activity) -> bool:
        """
        Validate a single activity.
        
        Args:
            activity: Activity to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Required fields
        if not activity.activity_id or not activity.activity_id.strip():
            errors.append("activity_id is required and cannot be empty")
        
        if not activity.name or not activity.name.strip():
            errors.append("name is required and cannot be empty")
        
        # Validate activity_id format (alphanumeric, dash, underscore)
        if activity.activity_id:
            if not re.match(r'^[A-Za-z0-9_-]+$', activity.activity_id):
                errors.append(f"activity_id '{activity.activity_id}' contains invalid characters")
        
        # Validate dates (if provided)
        date_fields = [
            'planned_start', 'planned_finish',
            'baseline_start', 'baseline_finish',
            'actual_start', 'actual_finish',
            'early_start', 'early_finish',
            'late_start', 'late_finish'
        ]
        
        for field in date_fields:
            value = getattr(activity, field, None)
            if value and not self._is_valid_date_format(value):
                errors.append(f"{field} has invalid date format: {value}")
        
        # Validate numeric fields
        numeric_fields = {
            'planned_duration': (0, 10000),
            'baseline_duration': (0, 10000),
            'remaining_duration': (0, 10000),
            'percent_complete': (0, 100),
            'risk_probability': (0, 1),
            'risk_delay_impact_days': (0, 10000),
            'fte_allocation': (0, 100),
            'resource_max_fte': (0, 100),
            'total_float': (None, None),  # No bounds
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            value = getattr(activity, field, None)
            if value is not None:
                try:
                    num_value = float(value)
                    if min_val is not None and num_value < min_val:
                        errors.append(f"{field} must be >= {min_val}")
                    if max_val is not None and num_value > max_val:
                        errors.append(f"{field} must be <= {max_val}")
                except (ValueError, TypeError):
                    errors.append(f"{field} must be a valid number")
        
        # Validate lists
        if activity.predecessors:
            for pred in activity.predecessors:
                if not isinstance(pred, str):
                    errors.append(f"predecessor must be a string: {pred}")
                elif not re.match(r'^[A-Za-z0-9_-]+$', pred):
                    errors.append(f"predecessor '{pred}' contains invalid characters")
        
        if activity.successors:
            for succ in activity.successors:
                if not isinstance(succ, str):
                    errors.append(f"successor must be a string: {succ}")
                elif not re.match(r'^[A-Za-z0-9_-]+$', succ):
                    errors.append(f"successor '{succ}' contains invalid characters")
        
        # Validate string lengths (prevent DoS)
        string_fields = {
            'name': 500,
            'resource_id': 200,
            'role': 200,
            'skill_tags': 500,
        }
        
        for field, max_length in string_fields.items():
            value = getattr(activity, field, None)
            if value and len(str(value)) > max_length:
                errors.append(f"{field} exceeds maximum length of {max_length}")
        
        # Check for SQL injection patterns (basic)
        suspicious_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
            r"(--|/\*|\*/|;|')",
        ]
        
        for field in ['activity_id', 'name', 'resource_id']:
            value = getattr(activity, field, None)
            if value:
                for pattern in suspicious_patterns:
                    if re.search(pattern, str(value), re.IGNORECASE):
                        errors.append(f"{field} contains suspicious SQL-like patterns")
                        break
        
        if errors:
            raise ValidationError(f"Validation failed: {'; '.join(errors)}")
        
        return True
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """
        Check if date string is in a valid format.
        Accepts common date formats: YYYY-MM-DD, MM/DD/YYYY, etc.
        """
        if not date_str or not isinstance(date_str, str):
            return False
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(date_str.strip(), fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def validate_batch(self, activities: List[Activity], max_count: Optional[int] = None) -> tuple[List[Activity], List[str]]:
        """
        Validate a batch of activities.
        
        Args:
            activities: List of activities to validate
            max_count: Maximum number of activities allowed (overrides instance setting)
            
        Returns:
            Tuple of (valid_activities, error_messages)
        """
        max_activities = max_count or self.max_activities
        
        if len(activities) > max_activities:
            return [], [f"Too many activities: {len(activities)} exceeds maximum of {max_activities}"]
        
        valid_activities = []
        errors = []
        
        for activity in activities:
            try:
                if self.validate(activity):
                    valid_activities.append(activity)
            except ValidationError as e:
                errors.append(str(e))
            except Exception as e:
                errors.append(f"Unexpected error validating activity {activity.activity_id}: {str(e)}")
        
        return valid_activities, errors

