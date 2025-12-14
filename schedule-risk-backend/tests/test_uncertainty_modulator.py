"""
Unit tests for Uncertainty Modulator (Layer 4)
Tests: Physics-based distribution modulation
"""

import pytest
from core.uncertainty_modulator import modulate_uncertainty
from core.models import Activity


class TestUncertaintyModulation:
    """Tests for uncertainty parameter modulation"""
    
    def test_no_modulation(self):
        """Test when no forensic features present"""
        activity = Activity(
            activity_id="A-001",
            name="Test",
            remaining_duration=10.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        enriched_features = {}
        risk_archetype = {
            "failure_probability": 0.05,
            "variance_multiplier": 1.0,
            "mode_shift_factor": 0.0
        }
        topology_metrics = {}
        skill_analysis = {"variance_increase_map": {}}
        
        params = modulate_uncertainty(
            activity, enriched_features, risk_archetype, topology_metrics, skill_analysis
        )
        
        assert params["base_duration"] == 10.0
        assert params["mode_shift_factor"] == 0.0
        assert params["variance_multiplier"] == 1.0
        assert params["failure_probability"] == 0.05
    
    def test_drift_modulation(self):
        """Test mode shift from drift"""
        activity = Activity(
            activity_id="A-002",
            name="Test",
            remaining_duration=10.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        enriched_features = {
            "drift_velocity": {
                "mode_shift_factor": 0.6  # 60% drift
            }
        }
        risk_archetype = {
            "failure_probability": 0.05,
            "variance_multiplier": 1.0,
            "mode_shift_factor": 0.0
        }
        topology_metrics = {}
        skill_analysis = {"variance_increase_map": {}}
        
        params = modulate_uncertainty(
            activity, enriched_features, risk_archetype, topology_metrics, skill_analysis
        )
        
        assert params["mode_shift_factor"] == 0.6  # Drift shifts mode
    
    def test_skill_modulation(self):
        """Test variance increase from skill bottleneck"""
        activity = Activity(
            activity_id="A-003",
            name="Test",
            remaining_duration=10.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        enriched_features = {}
        risk_archetype = {
            "failure_probability": 0.05,
            "variance_multiplier": 1.0,
            "mode_shift_factor": 0.0
        }
        topology_metrics = {}
        skill_analysis = {
            "variance_increase_map": {
                "A-003": 1.4  # 40% variance increase
            }
        }
        
        params = modulate_uncertainty(
            activity, enriched_features, risk_archetype, topology_metrics, skill_analysis
        )
        
        assert params["variance_multiplier"] == 1.4  # Skill widens variance
    
    def test_topology_modulation(self):
        """Test variance increase from topology"""
        activity = Activity(
            activity_id="A-004",
            name="Test",
            remaining_duration=10.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        enriched_features = {}
        risk_archetype = {
            "failure_probability": 0.05,
            "variance_multiplier": 1.0,
            "mode_shift_factor": 0.0
        }
        topology_metrics = {
            "A-004": {
                "variance_multiplier": 1.3  # 30% from centrality
            }
        }
        skill_analysis = {"variance_increase_map": {}}
        
        params = modulate_uncertainty(
            activity, enriched_features, risk_archetype, topology_metrics, skill_analysis
        )
        
        assert params["variance_multiplier"] == 1.3  # Topology widens variance
    
    def test_cluster_modulation(self):
        """Test all effects from high-risk cluster"""
        activity = Activity(
            activity_id="A-005",
            name="Test",
            remaining_duration=10.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        enriched_features = {}
        risk_archetype = {
            "failure_probability": 0.30,  # High risk cluster
            "variance_multiplier": 1.5,   # +50% variance
            "mode_shift_factor": 0.2       # +20% mode shift
        }
        topology_metrics = {}
        skill_analysis = {"variance_increase_map": {}}
        
        params = modulate_uncertainty(
            activity, enriched_features, risk_archetype, topology_metrics, skill_analysis
        )
        
        assert params["mode_shift_factor"] == 0.2
        assert params["variance_multiplier"] == 1.5
        assert params["failure_probability"] == 0.30
    
    def test_combined_modulation(self):
        """Test combined effects from all sources"""
        activity = Activity(
            activity_id="A-006",
            name="Test",
            remaining_duration=10.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        enriched_features = {
            "drift_velocity": {"mode_shift_factor": 0.6},
            "cost_performance": {"risk_event_probability": 0.15}
        }
        risk_archetype = {
            "failure_probability": 0.30,
            "variance_multiplier": 1.5,
            "mode_shift_factor": 0.2
        }
        topology_metrics = {
            "A-006": {"variance_multiplier": 1.3}
        }
        skill_analysis = {
            "variance_increase_map": {"A-006": 1.4}
        }
        
        params = modulate_uncertainty(
            activity, enriched_features, risk_archetype, topology_metrics, skill_analysis
        )
        
        # Mode shift: additive (drift + cluster)
        assert params["mode_shift_factor"] == pytest.approx(0.8, abs=0.01)  # 0.6 + 0.2
        
        # Variance: multiplicative (skill * topology * cluster)
        assert params["variance_multiplier"] == pytest.approx(2.73, abs=0.01)  # 1.4 * 1.3 * 1.5
        
        # Failure prob: maximum (cluster or CPI)
        assert params["failure_probability"] == 0.30  # max(0.30, 0.15)
    
    def test_cpi_failure_probability(self):
        """Test CPI increases failure probability"""
        activity = Activity(
            activity_id="A-007",
            name="Test",
            remaining_duration=10.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        enriched_features = {
            "cost_performance": {
                "risk_event_probability": 0.25  # High CPI risk
            }
        }
        risk_archetype = {
            "failure_probability": 0.15,  # Lower than CPI
            "variance_multiplier": 1.0,
            "mode_shift_factor": 0.0
        }
        topology_metrics = {}
        skill_analysis = {"variance_increase_map": {}}
        
        params = modulate_uncertainty(
            activity, enriched_features, risk_archetype, topology_metrics, skill_analysis
        )
        
        # Should use maximum (CPI is higher)
        assert params["failure_probability"] == 0.25
    
    def test_base_duration_fallback(self):
        """Test base duration fallback to planned/baseline"""
        activity = Activity(
            activity_id="A-008",
            name="Test",
            remaining_duration=None,
            planned_duration=15.0,
            baseline_duration=12.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        enriched_features = {}
        risk_archetype = {
            "failure_probability": 0.05,
            "variance_multiplier": 1.0,
            "mode_shift_factor": 0.0
        }
        topology_metrics = {}
        skill_analysis = {"variance_increase_map": {}}
        
        params = modulate_uncertainty(
            activity, enriched_features, risk_archetype, topology_metrics, skill_analysis
        )
        
        # Should use planned_duration (15.0) as fallback
        assert params["base_duration"] == 15.0
    
    def test_base_duration_zero_fallback(self):
        """Test base duration fallback when all are zero"""
        activity = Activity(
            activity_id="A-009",
            name="Test",
            remaining_duration=0.0,
            planned_duration=0.0,
            baseline_duration=0.0,
            percent_complete=0.0,
            risk_probability=0.0,
            risk_delay_impact_days=0.0
        )
        
        enriched_features = {}
        risk_archetype = {
            "failure_probability": 0.05,
            "variance_multiplier": 1.0,
            "mode_shift_factor": 0.0
        }
        topology_metrics = {}
        skill_analysis = {"variance_increase_map": {}}
        
        params = modulate_uncertainty(
            activity, enriched_features, risk_archetype, topology_metrics, skill_analysis
        )
        
        # Should default to 1.0
        assert params["base_duration"] == 1.0
