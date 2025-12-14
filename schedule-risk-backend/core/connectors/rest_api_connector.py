"""
REST API connector for integrating with external project management systems.

This connector allows integration with any REST API that can provide
project activity data. It's a generic connector that can be configured
for different APIs (Jira, Asana, Monday.com, etc.).
"""

import httpx
from typing import List, Dict, Any, Optional
from .base import BaseConnector, ConnectorConfig, ConnectorResult
from core.models import Activity


class RESTAPIConnector(BaseConnector):
    """
    Generic REST API connector for project management systems.
    
    Configuration example:
    {
        "endpoint_url": "https://api.example.com/projects/{project_id}/activities",
        "method": "GET",
        "headers": {"Authorization": "Bearer {token}"},
        "field_mapping": {
            "activity_id": "id",
            "name": "title",
            "planned_start": "start_date",
            ...
        }
    }
    """
    
    def connect(self) -> bool:
        """Test connection to REST API"""
        try:
            result = self.test_connection()
            return result.get("success", False)
        except Exception:
            return False
    
    def load_activities(self, project_id: str) -> ConnectorResult:
        """
        Load activities from REST API.
        
        Args:
            project_id: Project ID to load activities for
            
        Returns:
            ConnectorResult with activities
        """
        errors = []
        warnings = []
        
        try:
            endpoint_url = self.config.connection_params.get("endpoint_url")
            if not endpoint_url:
                return ConnectorResult(
                    success=False,
                    activities=[],
                    errors=["endpoint_url is required in connection_params"]
                )
            
            # Replace {project_id} placeholder if present
            endpoint_url = endpoint_url.replace("{project_id}", project_id)
            
            # Prepare request
            method = self.config.connection_params.get("method", "GET").upper()
            headers = self._prepare_headers()
            params = self.config.connection_params.get("params", {})
            
            # Make API request
            with httpx.Client(timeout=30.0) as client:
                if method == "GET":
                    response = client.get(endpoint_url, headers=headers, params=params)
                elif method == "POST":
                    body = self.config.connection_params.get("body", {})
                    response = client.post(endpoint_url, headers=headers, json=body, params=params)
                else:
                    return ConnectorResult(
                        success=False,
                        activities=[],
                        errors=[f"Unsupported HTTP method: {method}"]
                    )
                
                response.raise_for_status()
                data = response.json()
            
            # Extract activities from response
            # Support different response structures
            activities_data = self._extract_activities_data(data)
            
            # Convert to Activity models
            activities = []
            field_mapping = self.config.connection_params.get("field_mapping", {})
            
            for item in activities_data:
                try:
                    activity = self._map_to_activity(item, project_id, field_mapping)
                    activity = self.sanitize_activity(activity)
                    activities.append(activity)
                except Exception as e:
                    errors.append(f"Failed to map activity: {str(e)}")
                    continue
            
            # Validate activities
            if self.config.validate_data:
                valid_activities, validation_errors = self.validate_activities(activities)
                errors.extend(validation_errors)
                activities = valid_activities
            
            metadata = {
                "source": "rest_api",
                "endpoint": endpoint_url,
                "total_items": len(activities_data),
                "valid_activities": len(activities),
                "invalid_items": len(errors)
            }
            
            return ConnectorResult(
                success=len(errors) == 0 or len(activities) > 0,
                activities=activities,
                metadata=metadata,
                errors=errors if errors else None,
                warnings=warnings if warnings else None
            )
            
        except httpx.HTTPError as e:
            return ConnectorResult(
                success=False,
                activities=[],
                errors=[f"HTTP error: {str(e)}"]
            )
        except Exception as e:
            return ConnectorResult(
                success=False,
                activities=[],
                errors=[f"Unexpected error: {str(e)}"]
            )
    
    def test_connection(self) -> Dict[str, Any]:
        """Test REST API connection"""
        try:
            endpoint_url = self.config.connection_params.get("endpoint_url")
            if not endpoint_url:
                return {
                    "success": False,
                    "error": "endpoint_url not provided"
                }
            
            # Try a simple health check or test endpoint
            test_url = endpoint_url.replace("/activities", "/health").replace("/{project_id}", "")
            if test_url == endpoint_url:
                # If no health endpoint, try the main endpoint with a test project_id
                test_url = endpoint_url.replace("{project_id}", "test")
            
            headers = self._prepare_headers()
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(test_url, headers=headers)
                response.raise_for_status()
            
            return {
                "success": True,
                "endpoint": endpoint_url,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare HTTP headers with authentication"""
        headers = self.config.connection_params.get("headers", {}).copy()
        
        # Add authentication if configured
        if self.config.credentials:
            auth_type = self.config.auth_type or "bearer"
            
            if auth_type == "bearer" and "token" in self.config.credentials:
                headers["Authorization"] = f"Bearer {self.config.credentials['token']}"
            elif auth_type == "api_key" and "api_key" in self.config.credentials:
                api_key_name = self.config.connection_params.get("api_key_header", "X-API-Key")
                headers[api_key_name] = self.config.credentials["api_key"]
            elif auth_type == "basic" and "username" in self.config.credentials:
                import base64
                creds = f"{self.config.credentials['username']}:{self.config.credentials.get('password', '')}"
                encoded = base64.b64encode(creds.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
        
        return headers
    
    def _extract_activities_data(self, response_data: Any) -> List[Dict]:
        """
        Extract activities array from API response.
        Supports different response structures.
        """
        if isinstance(response_data, list):
            return response_data
        elif isinstance(response_data, dict):
            # Try common keys
            for key in ["activities", "items", "data", "results", "tasks"]:
                if key in response_data and isinstance(response_data[key], list):
                    return response_data[key]
            # If no list found, return empty
            return []
        else:
            return []
    
    def _map_to_activity(self, item: Dict, project_id: str, field_mapping: Dict[str, str]) -> Activity:
        """
        Map API response item to Activity model.
        
        Args:
            item: Raw API response item
            project_id: Project ID
            field_mapping: Mapping from Activity fields to API fields
        """
        def get_value(field_name: str, default=None):
            # First try mapped field name
            mapped_name = field_mapping.get(field_name, field_name)
            
            # Try different variations
            variations = [
                mapped_name,
                mapped_name.lower(),
                mapped_name.replace("_", ""),
                mapped_name.replace("_", "-"),
            ]
            
            for var in variations:
                if var in item:
                    return item[var]
            
            return default
        
        def get_list_value(field_name: str, separator: str = ",") -> List[str]:
            value = get_value(field_name)
            if value is None:
                return []
            if isinstance(value, list):
                return [str(v) for v in value]
            if isinstance(value, str):
                return [v.strip() for v in value.split(separator) if v.strip()]
            return []
        
        def get_float_value(field_name: str, default: float = 0.0) -> float:
            value = get_value(field_name, default)
            try:
                return float(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        def get_bool_value(field_name: str, default: bool = False) -> bool:
            value = get_value(field_name, default)
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "y", "on")
            return default
        
        return Activity(
            activity_id=str(get_value("activity_id", "")),
            name=str(get_value("name", "")),
            planned_start=get_value("planned_start"),
            planned_finish=get_value("planned_finish"),
            baseline_start=get_value("baseline_start"),
            baseline_finish=get_value("baseline_finish"),
            planned_duration=get_float_value("planned_duration"),
            baseline_duration=get_float_value("baseline_duration"),
            actual_start=get_value("actual_start"),
            actual_finish=get_value("actual_finish"),
            remaining_duration=get_float_value("remaining_duration"),
            percent_complete=get_float_value("percent_complete", 0.0),
            early_start=get_value("early_start"),
            early_finish=get_value("early_finish"),
            late_start=get_value("late_start"),
            late_finish=get_value("late_finish"),
            total_float=get_float_value("total_float"),
            risk_probability=get_float_value("risk_probability", 0.0),
            risk_delay_impact_days=get_float_value("risk_delay_impact_days", 0.0),
            cost_impact_of_risk=get_float_value("cost_impact_of_risk"),
            predecessors=get_list_value("predecessors", separator=","),
            successors=get_list_value("successors", separator=","),
            on_critical_path=get_bool_value("on_critical_path", False),
            resource_id=get_value("resource_id"),
            role=get_value("role"),
            fte_allocation=get_float_value("fte_allocation", 0.0),
            resource_max_fte=get_float_value("resource_max_fte", 1.0),
            skill_tags=get_value("skill_tags")
        )

