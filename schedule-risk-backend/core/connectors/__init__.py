"""
Data connector framework for integrating with external project management systems.

This module provides a pluggable architecture for connecting to various
project management software (CSV, Jira, MS Project, Asana, etc.) while
maintaining a consistent interface and data model.
"""

from .base import BaseConnector, ConnectorConfig, ConnectorResult
from .registry import ConnectorRegistry, get_connector
from .validators import ActivityValidator, ValidationError

# Import and register built-in connectors
from .csv_connector import CSVConnector
from .rest_api_connector import RESTAPIConnector

# Register built-in connectors
ConnectorRegistry.register("csv", CSVConnector)
ConnectorRegistry.register("rest_api", RESTAPIConnector)

__all__ = [
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorResult",
    "ConnectorRegistry",
    "get_connector",
    "ActivityValidator",
    "ValidationError",
    "CSVConnector",
    "RESTAPIConnector",
]
