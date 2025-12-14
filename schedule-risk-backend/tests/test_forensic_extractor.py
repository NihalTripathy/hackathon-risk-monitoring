"""
Unit tests for Forensic Feature Extractor (Layer 1)
Tests: Drift Velocity Engine and Cost Efficiency Engine
"""

import pytest
from datetime import date
from core.forensic_extractor import (
    calculate_drift_velocity,
    calculate_cost_performance,
    extract_forensic_features
)
from core.models import Activity


class TestDriftVelocityEngine:
    """Tests for Drift Velocity Engine"""
    
    def test_drift_velocity_positive_drift(self):
        """Test drift calculation when planned > baseline"""
        activity = Activity(
            activity_id="A-001",
            name="Test Activity",
            planned_duration=8.0,
            baseline_duration=5.0,
            remaining_duration=3.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_drift_velocity(activity)
        
        assert result["drift_ratio"] == 0.6  # (8-5)/5 = 0.6
        assert result["drift_adjusted_remaining"] == 4.8  # 3 * 1.6
        assert result["mode_shift_factor"] == 0.6
    
    def test_drift_velocity_no_drift(self):
        """Test drift calculation when planned = baseline"""
        activity = Activity(
            activity_id="A-002",
            name="Test Activity",
            planned_duration=5.0,
            baseline_duration=5.0,
            remaining_duration=2.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_drift_velocity(activity)
        
        assert result["drift_ratio"] == 0.0
        assert result["drift_adjusted_remaining"] == 2.0
        assert result["mode_shift_factor"] == 0.0
    
    def test_drift_velocity_negative_drift(self):
        """Test drift calculation when planned < baseline (ahead of schedule)"""
        activity = Activity(
            activity_id="A-003",
            name="Test Activity",
            planned_duration=4.0,
            baseline_duration=5.0,
            remaining_duration=2.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_drift_velocity(activity)
        
        assert result["drift_ratio"] == -0.2  # (4-5)/5 = -0.2
        assert result["drift_adjusted_remaining"] == 1.6  # 2 * 0.8
        assert result["mode_shift_factor"] == -0.2
    
    def test_drift_velocity_zero_baseline(self):
        """Test drift calculation when baseline is zero"""
        activity = Activity(
            activity_id="A-004",
            name="Test Activity",
            planned_duration=5.0,
            baseline_duration=0.0,
            remaining_duration=3.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_drift_velocity(activity)
        
        assert result["drift_ratio"] == 0.0
        assert result["drift_adjusted_remaining"] == 3.0
        assert result["mode_shift_factor"] == 0.0
    
    def test_drift_velocity_no_remaining_duration(self):
        """Test drift calculation when remaining duration is zero"""
        activity = Activity(
            activity_id="A-005",
            name="Test Activity",
            planned_duration=8.0,
            baseline_duration=5.0,
            remaining_duration=0.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_drift_velocity(activity)
        
        assert result["drift_ratio"] == 0.6
        assert result["drift_adjusted_remaining"] == 0.0
        assert result["mode_shift_factor"] == 0.6


class TestCostEfficiencyEngine:
    """Tests for Cost Efficiency Engine (CPI)"""
    
    def test_cpi_on_budget(self):
        """Test CPI calculation when on budget"""
        activity = Activity(
            activity_id="A-006",
            name="Test Activity",
            planned_cost=1000.0,
            actual_cost_to_date=1000.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_cost_performance(activity)
        
        assert result["cpi_trend"] == 1.0
        assert result["cost_variance"] == 0.0
        assert result["risk_event_probability"] == 0.0
    
    def test_cpi_over_budget(self):
        """Test CPI calculation when over budget"""
        activity = Activity(
            activity_id="A-007",
            name="Test Activity",
            planned_cost=1000.0,
            actual_cost_to_date=1200.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_cost_performance(activity)
        
        assert result["cpi_trend"] == pytest.approx(0.833, abs=0.001)  # 1000/1200
        assert result["cost_variance"] == 200.0
        assert result["risk_event_probability"] > 0.0  # Should be > 0 for CPI < 0.9
    
    def test_cpi_under_budget(self):
        """Test CPI calculation when under budget"""
        activity = Activity(
            activity_id="A-008",
            name="Test Activity",
            planned_cost=1000.0,
            actual_cost_to_date=800.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_cost_performance(activity)
        
        assert result["cpi_trend"] == 1.25  # 1000/800
        assert result["cost_variance"] == -200.0
        assert result["risk_event_probability"] == 0.0  # CPI > 0.9, no risk
    
    def test_cpi_no_cost_data(self):
        """Test CPI calculation when cost data is missing"""
        activity = Activity(
            activity_id="A-009",
            name="Test Activity",
            planned_cost=None,
            actual_cost_to_date=None,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_cost_performance(activity)
        
        assert result["cpi_trend"] == 1.0  # Default to on track
        assert result["cost_variance"] == 0.0
        assert result["risk_event_probability"] == 0.0
    
    def test_cpi_zero_actual_cost(self):
        """Test CPI calculation when actual cost is zero"""
        activity = Activity(
            activity_id="A-010",
            name="Test Activity",
            planned_cost=1000.0,
            actual_cost_to_date=0.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_cost_performance(activity)
        
        assert result["cpi_trend"] == 1.0  # No actual cost = assume on track
        assert result["cost_variance"] == -1000.0
        assert result["risk_event_probability"] == 0.0
    
    def test_cpi_severe_over_budget(self):
        """Test CPI calculation when severely over budget (CPI < 0.9)"""
        activity = Activity(
            activity_id="A-011",
            name="Test Activity",
            planned_cost=1000.0,
            actual_cost_to_date=1500.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = calculate_cost_performance(activity)
        
        assert result["cpi_trend"] == pytest.approx(0.667, abs=0.001)  # 1000/1500
        assert result["risk_event_probability"] > 0.0
        assert result["risk_event_probability"] <= 0.3  # Capped at 30%


class TestForensicExtractor:
    """Tests for main extractor function"""
    
    def test_extract_forensic_features_complete(self):
        """Test extraction of all forensic features"""
        activity = Activity(
            activity_id="A-012",
            name="Test Activity",
            planned_duration=8.0,
            baseline_duration=5.0,
            remaining_duration=3.0,
            planned_cost=1000.0,
            actual_cost_to_date=1100.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = extract_forensic_features(activity)
        
        assert "drift_velocity" in result
        assert "cost_performance" in result
        assert result["drift_velocity"]["drift_ratio"] == 0.6
        assert result["cost_performance"]["cpi_trend"] < 1.0
    
    def test_extract_forensic_features_minimal(self):
        """Test extraction with minimal data"""
        activity = Activity(
            activity_id="A-013",
            name="Test Activity",
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        result = extract_forensic_features(activity)
        
        assert "drift_velocity" in result
        assert "cost_performance" in result
        # Should handle missing data gracefully
        assert result["drift_velocity"]["drift_ratio"] == 0.0
        assert result["cost_performance"]["cpi_trend"] == 1.0
