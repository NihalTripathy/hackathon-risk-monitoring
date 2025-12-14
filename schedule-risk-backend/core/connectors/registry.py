"""
Connector registry for managing and discovering available connectors.
"""

from typing import Dict, Optional, Type
from .base import BaseConnector, ConnectorConfig


class ConnectorRegistry:
    """
    Registry for managing connector types and instances.
    
    This allows the system to:
    1. Register new connector types
    2. Create connector instances
    3. Discover available connectors
    """
    
    _connector_classes: Dict[str, Type[BaseConnector]] = {}
    _connector_instances: Dict[str, BaseConnector] = {}
    
    @classmethod
    def register(cls, connector_type: str, connector_class: Type[BaseConnector]):
        """
        Register a connector class.
        
        Args:
            connector_type: Unique identifier (e.g., "csv", "jira")
            connector_class: Connector class that extends BaseConnector
        """
        if not issubclass(connector_class, BaseConnector):
            raise ValueError(f"{connector_class.__name__} must extend BaseConnector")
        
        cls._connector_classes[connector_type] = connector_class
    
    @classmethod
    def create(cls, config: ConnectorConfig) -> BaseConnector:
        """
        Create a connector instance from configuration.
        
        Args:
            config: ConnectorConfig with connector_type and connection params
            
        Returns:
            BaseConnector instance
            
        Raises:
            ValueError: If connector type is not registered
        """
        connector_type = config.connector_type
        
        if connector_type not in cls._connector_classes:
            available = ", ".join(cls._connector_classes.keys())
            raise ValueError(
                f"Connector type '{connector_type}' not registered. "
                f"Available types: {available}"
            )
        
        connector_class = cls._connector_classes[connector_type]
        return connector_class(config)
    
    @classmethod
    def get_available_types(cls) -> list[str]:
        """Get list of available connector types"""
        return list(cls._connector_classes.keys())
    
    @classmethod
    def get_connector_info(cls, connector_type: str) -> Optional[Dict]:
        """Get information about a connector type"""
        if connector_type not in cls._connector_classes:
            return None
        
        connector_class = cls._connector_classes[connector_type]
        # Try to get docstring or class attributes
        return {
            "type": connector_type,
            "class_name": connector_class.__name__,
            "docstring": connector_class.__doc__ or "",
        }


def get_connector(config: ConnectorConfig) -> BaseConnector:
    """
    Convenience function to get a connector instance.
    
    Args:
        config: ConnectorConfig
        
    Returns:
        BaseConnector instance
    """
    return ConnectorRegistry.create(config)

