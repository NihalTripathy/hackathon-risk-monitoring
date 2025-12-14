"""
Base connector interface and data models for project management integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from core.models import Activity


@dataclass
class ConnectorConfig:
    """Configuration for a connector instance"""
    connector_type: str  # e.g., "csv", "jira", "ms_project", "rest_api"
    name: str  # Human-readable name
    description: Optional[str] = None
    
    # Connection parameters (varies by connector type)
    # For CSV: file_path
    # For Jira: base_url, api_token, project_key
    # For REST API: endpoint_url, api_key, headers
    connection_params: Dict[str, Any] = None
    
    # Security settings
    requires_auth: bool = True
    auth_type: Optional[str] = None  # "api_key", "oauth2", "basic", "token"
    credentials: Optional[Dict[str, str]] = None  # Encrypted/stored securely
    
    # Data safety settings
    validate_data: bool = True
    sanitize_input: bool = True
    max_activities: int = 10000  # Safety limit
    allowed_fields: Optional[List[str]] = None  # Whitelist of allowed fields
    
    def __post_init__(self):
        if self.connection_params is None:
            self.connection_params = {}


@dataclass
class ConnectorResult:
    """Result from a connector operation"""
    success: bool
    activities: List[Activity]
    metadata: Dict[str, Any] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class BaseConnector(ABC):
    """
    Base class for all project management system connectors.
    
    All connectors must implement this interface to ensure:
    1. Consistent data output (Activity model)
    2. Security and validation
    3. Error handling
    4. Data safety
    """
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._validate_config()
    
    def _validate_config(self):
        """Validate connector configuration"""
        if not self.config.connector_type:
            raise ValueError("connector_type is required")
        if not self.config.name:
            raise ValueError("name is required")
        if self.config.max_activities <= 0:
            raise ValueError("max_activities must be positive")
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the external system.
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    def load_activities(self, project_id: str) -> ConnectorResult:
        """
        Load activities from the external system.
        
        This is the main method that all connectors must implement.
        It should:
        1. Fetch data from the external system
        2. Transform it to Activity model
        3. Validate the data
        4. Return ConnectorResult
        
        Args:
            project_id: The project ID to load activities for
            
        Returns:
            ConnectorResult: Contains activities and metadata
            
        Raises:
            ValueError: If data is invalid
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the external system.
        
        Returns:
            Dict with connection status and details
        """
        pass
    
    def validate_activities(self, activities: List[Activity]) -> tuple[List[Activity], List[str]]:
        """
        Validate activities according to connector configuration.
        
        Args:
            activities: List of activities to validate
            
        Returns:
            Tuple of (valid_activities, error_messages)
        """
        from .validators import ActivityValidator
        
        validator = ActivityValidator(
            max_activities=self.config.max_activities,
            allowed_fields=self.config.allowed_fields
        )
        
        valid_activities = []
        errors = []
        
        for activity in activities:
            try:
                if validator.validate(activity):
                    valid_activities.append(activity)
            except Exception as e:
                errors.append(f"Activity {activity.activity_id}: {str(e)}")
        
        return valid_activities, errors
    
    def sanitize_activity(self, activity: Activity) -> Activity:
        """
        Sanitize activity data to prevent injection attacks.
        
        Args:
            activity: Activity to sanitize
            
        Returns:
            Sanitized Activity
        """
        if not self.config.sanitize_input:
            return activity
        
        # Sanitize string fields
        def sanitize_string(value: Optional[str]) -> Optional[str]:
            if value is None:
                return None
            # Remove null bytes and control characters
            sanitized = value.replace('\x00', '').replace('\r', '')
            # Limit length to prevent DoS
            if len(sanitized) > 1000:
                sanitized = sanitized[:1000]
            return sanitized
        
        # Create sanitized copy
        activity_dict = activity.dict()
        for key, value in activity_dict.items():
            if isinstance(value, str):
                activity_dict[key] = sanitize_string(value)
            elif isinstance(value, list):
                activity_dict[key] = [sanitize_string(str(v)) if isinstance(v, str) else v for v in value]
        
        return Activity(**activity_dict)
    
    def get_connector_info(self) -> Dict[str, Any]:
        """Get information about this connector"""
        return {
            "type": self.config.connector_type,
            "name": self.config.name,
            "description": self.config.description,
            "requires_auth": self.config.requires_auth,
            "auth_type": self.config.auth_type,
            "max_activities": self.config.max_activities,
        }

