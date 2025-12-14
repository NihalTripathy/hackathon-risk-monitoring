"""
SQLAlchemy ORM models - Infrastructure layer
Maps database tables to domain entities
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json


# Declarative base for models
Base = declarative_base()


class UserModel(Base):
    """User ORM model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    projects = relationship("ProjectModel", back_populates="owner", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreferencesModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    user_preferences = relationship("UserPreferencesModel", back_populates="user", uselist=False, cascade="all, delete-orphan")


class ProjectModel(Base):
    """Project ORM model"""
    __tablename__ = "projects"
    
    project_id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=True)
    activity_count = Column(Integer, default=0)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA256 hash for duplicate detection
    analysis_date_mode = Column(String(20), default='today')  # 'today' or 'csv_date'
    csv_reference_date = Column(Date, nullable=True)  # Auto-detected date from CSV
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("UserModel", back_populates="projects")
    activities = relationship("ActivityModel", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogModel", back_populates="project", cascade="all, delete-orphan")


class ActivityModel(Base):
    """Activity ORM model"""
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False, index=True)
    activity_id = Column(String, nullable=False, index=True)
    name = Column(String)
    planned_start = Column(String, nullable=True)
    planned_finish = Column(String, nullable=True)
    baseline_start = Column(String, nullable=True)
    baseline_finish = Column(String, nullable=True)
    planned_duration = Column(Float, nullable=True)
    baseline_duration = Column(Float, nullable=True)
    actual_start = Column(String, nullable=True)
    actual_finish = Column(String, nullable=True)
    remaining_duration = Column(Float, nullable=True)
    percent_complete = Column(Float, default=0.0)
    # Schedule analysis fields
    early_start = Column(String, nullable=True)
    early_finish = Column(String, nullable=True)
    late_start = Column(String, nullable=True)
    late_finish = Column(String, nullable=True)
    total_float = Column(Float, nullable=True)  # Total_Float from CSV
    # Risk fields
    risk_probability = Column(Float, default=0.0)
    risk_delay_impact_days = Column(Float, default=0.0)
    predecessors = Column(Text, nullable=True)
    successors = Column(Text, nullable=True)
    on_critical_path = Column(Boolean, default=False)
    resource_id = Column(String, nullable=True)
    fte_allocation = Column(Float, default=0.0)
    resource_max_fte = Column(Float, default=1.0)
    
    # Relationship
    project = relationship("ProjectModel", back_populates="activities")


class AuditLogModel(Base):
    """Audit log ORM model"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    event = Column(String, nullable=False, index=True)
    details = Column(JSON, nullable=True)
    
    # Relationship
    project = relationship("ProjectModel", back_populates="audit_logs")


# Cache models
class ForecastCacheModel(Base):
    """Forecast cache model"""
    __tablename__ = "forecast_cache"
    
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True, index=True)
    p50 = Column(Float, nullable=False)
    p80 = Column(Float, nullable=False)
    p90 = Column(Float, nullable=True)
    p95 = Column(Float, nullable=True)
    current = Column(Float, nullable=True)
    criticality_indices = Column(JSON, nullable=True)
    activity_count = Column(Integer, nullable=False)
    data_hash = Column(String(16), nullable=True)
    logic_version = Column(String(16), nullable=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class RisksCacheModel(Base):
    """Risks cache model"""
    __tablename__ = "risks_cache"
    
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True, index=True)
    total_risks = Column(Integer, nullable=False)
    top_risks = Column(JSON, nullable=False)
    activity_count = Column(Integer, nullable=False)
    data_hash = Column(String(16), nullable=True)
    logic_version = Column(String(16), nullable=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AnomaliesCacheModel(Base):
    """Anomalies cache model"""
    __tablename__ = "anomalies_cache"
    
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True, index=True)
    zombie_tasks = Column(JSON, nullable=False)
    black_holes = Column(JSON, nullable=False)
    total_anomalies = Column(Integer, nullable=False)
    activity_count = Column(Integer, nullable=False)
    data_hash = Column(String(16), nullable=True)
    logic_version = Column(String(16), nullable=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# Portfolio cache models
class PortfolioSummaryCacheModel(Base):
    """Portfolio summary cache model"""
    __tablename__ = "portfolio_summary_cache"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cache_key = Column(String, nullable=False, index=True)
    summary_data = Column(JSON, nullable=False)
    project_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)


class PortfolioRisksCacheModel(Base):
    """Portfolio risks cache model"""
    __tablename__ = "portfolio_risks_cache"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cache_key = Column(String, nullable=False, index=True)
    risks_data = Column(JSON, nullable=False)
    project_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)


class PortfolioResourcesCacheModel(Base):
    """Portfolio resources cache model"""
    __tablename__ = "portfolio_resources_cache"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cache_key = Column(String, nullable=False, index=True)
    resources_data = Column(JSON, nullable=False)
    project_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)


# Portfolio optimization models - for fast portfolio aggregation
class ProjectMetricsModel(Base):
    """Project metrics model - stores computed metrics per project for portfolio aggregation"""
    __tablename__ = "project_metrics"
    
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    activity_count = Column(Integer, nullable=False)
    resource_summary = Column(JSON, nullable=True)
    high_risk_activities_count = Column(Integer, default=0)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("ProjectModel")
    user = relationship("UserModel")


class PortfolioCacheModel(Base):
    """Portfolio cache model - stores aggregated portfolio data per user for instant loading"""
    __tablename__ = "portfolio_cache"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    total_projects = Column(Integer, nullable=False)
    total_activities = Column(Integer, nullable=False)
    portfolio_risk_score = Column(Float, nullable=False)
    projects_at_risk = Column(Integer, nullable=False)
    high_risk_projects = Column(JSON, nullable=False)
    resource_summary = Column(JSON, nullable=False)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("UserModel")


# UX Enhancement Models - Priority 1: Notification Preferences
class NotificationPreferencesModel(Base):
    """User notification preferences model"""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Email preferences
    email_enabled = Column(Boolean, default=True)
    email_risk_alerts = Column(Boolean, default=True)
    email_daily_digest = Column(Boolean, default=False)
    email_weekly_summary = Column(Boolean, default=False)
    
    # Risk thresholds for notifications
    risk_alert_threshold = Column(Float, default=70.0)  # Alert if risk >= this
    risk_digest_threshold = Column(Float, default=50.0)  # Include in digest if risk >= this
    
    # Notification frequency
    digest_frequency = Column(String, default="daily")  # daily, weekly, never
    
    # Project-specific preferences (JSON)
    project_preferences = Column(JSON, default=dict)  # {project_id: {enabled: bool, threshold: float}}
    
    # Email status tracking
    last_email_sent = Column(DateTime(timezone=True), nullable=True)  # Last successful email
    last_email_error = Column(DateTime(timezone=True), nullable=True)  # Last email error
    email_error_count = Column(Integer, default=0)  # Consecutive email failures
    email_error_message = Column(Text, nullable=True)  # Last error message
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("UserModel", back_populates="notification_preferences")


# UX Enhancement Models - Priority 6: User Preferences
class UserPreferencesModel(Base):
    """User preferences model for customization"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Risk threshold customization
    risk_threshold_high = Column(Float, default=70.0)
    risk_threshold_medium = Column(Float, default=40.0)
    risk_threshold_low = Column(Float, default=0.0)
    
    # Dashboard layout preferences (JSON)
    dashboard_layout = Column(JSON, default=dict)  # Widget positions, visibility
    
    # Default filters and views (JSON)
    default_filters = Column(JSON, default=dict)  # Saved filter configurations
    default_views = Column(JSON, default=dict)  # Saved view configurations
    
    # Display preferences
    show_p50_first = Column(Boolean, default=False)
    show_p80_first = Column(Boolean, default=True)
    show_anomalies_section = Column(Boolean, default=True)
    show_resource_summary = Column(Boolean, default=False)
    
    # Onboarding tour completion tracking (JSON array of tour IDs)
    completed_tours = Column(JSON, default=list)  # e.g., ["dashboard", "forecast", "risks"]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("UserModel", back_populates="user_preferences")


# UX Enhancement Models - Priority 4: Webhook Configurations
class WebhookConfigurationModel(Base):
    """Webhook configuration model"""
    __tablename__ = "webhook_configurations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=True, index=True)  # None = all projects
    
    # Webhook details
    name = Column(String, nullable=False)  # User-friendly name
    webhook_url = Column(String, nullable=False)
    webhook_type = Column(String, nullable=False)  # slack, teams, jira, generic
    
    # Trigger configuration (JSON)
    triggers = Column(JSON, nullable=False)  # {risk_alert: bool, daily_digest: bool, anomaly: bool}
    risk_threshold = Column(Float, default=70.0)  # Trigger if risk >= this
    
    # Payload customization (JSON)
    payload_template = Column(JSON, nullable=True)  # Custom payload format
    
    # Status
    enabled = Column(Boolean, default=True)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, default=0)
    
    # Security
    secret_key = Column(String, nullable=True)  # For webhook signature validation
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# UX Enhancement Models - Priority 8: User Feedback
class UserFeedbackModel(Base):
    """User feedback model"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for anonymous feedback
    
    # Feedback context
    feedback_type = Column(String, nullable=False)  # explanation, forecast, mitigation, general
    context_id = Column(String, nullable=True)  # activity_id, project_id, etc.
    
    # Feedback content
    was_helpful = Column(Boolean, nullable=True)  # True/False/None
    feedback_text = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 rating
    
    # Metadata
    page_url = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Processing
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
