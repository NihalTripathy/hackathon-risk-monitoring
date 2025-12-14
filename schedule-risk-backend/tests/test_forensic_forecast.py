"""
Unit tests for Forensic Forecast (Integration Layer 4+5)
Tests: Complete forecast pipeline with forensic modulation
"""

import pytest
from core.forensic_forecast import compute_forensic_forecast
from core.models import Activity
from core.risk_clustering import get_risk_archetype_characteristics


class TestForensicForecast:
    """Tests for complete forensic forecast pipeline"""
    
    def test_forensic_forecast_basic(self):
        """Test basic forensic forecast"""
        activities = [
            Activity(
                activity_id="A-001",
                name="Task 1",
                remaining_duration=5.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=[]
            ),
            Activity(
                activity_id="A-002",
                name="Task 2",
                remaining_duration=3.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["A-001"],
                successors=[]
            )
        ]
        
        enriched_features = {
            "A-001": {
                "drift_velocity": {"mode_shift_factor": 0.0},
                "cost_performance": {"risk_event_probability": 0.0}
            },
            "A-002": {
                "drift_velocity": {"mode_shift_factor": 0.0},
                "cost_performance": {"risk_event_probability": 0.0}
            }
        }
        
        risk_archetypes = {
            "A-001": get_risk_archetype_characteristics(0),
            "A-002": get_risk_archetype_characteristics(0)
        }
        
        topology_metrics = {
            "A-001": {"variance_multiplier": 1.0},
            "A-002": {"variance_multiplier": 1.0}
        }
        
        skill_analysis = {"variance_increase_map": {}}
        
        forecast = compute_forensic_forecast(
            project_id="test-project",
            activities=activities,
            enriched_features=enriched_features,
            risk_archetypes=risk_archetypes,
            topology_metrics=topology_metrics,
            skill_analysis=skill_analysis,
            num_simulations=1000  # Small number for testing
        )
        
        assert "p50" in forecast
        assert "p80" in forecast
        assert "p90" in forecast
        assert "p95" in forecast
        assert forecast["forensic_modulation_applied"] == True
        assert forecast["p80"] >= forecast["p50"]
        assert forecast["p90"] >= forecast["p80"]
        assert forecast["p95"] >= forecast["p90"]
    
    def test_forensic_forecast_with_drift(self):
        """Test forecast with drift modulation"""
        activities = [
            Activity(
                activity_id="A-001",
                name="Task 1",
                remaining_duration=10.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=[]
            )
        ]
        
        enriched_features = {
            "A-001": {
                "drift_velocity": {"mode_shift_factor": 0.6},  # 60% drift
                "cost_performance": {"risk_event_probability": 0.0}
            }
        }
        
        risk_archetypes = {
            "A-001": get_risk_archetype_characteristics(0)
        }
        
        topology_metrics = {
            "A-001": {"variance_multiplier": 1.0}
        }
        
        skill_analysis = {"variance_increase_map": {}}
        
        forecast = compute_forensic_forecast(
            project_id="test-project",
            activities=activities,
            enriched_features=enriched_features,
            risk_archetypes=risk_archetypes,
            topology_metrics=topology_metrics,
            skill_analysis=skill_analysis,
            num_simulations=1000
        )
        
        # With 60% drift, forecast should be longer
        # Mode shifts from 10 to 16 days
        assert forecast["p50"] > 10  # Should be shifted right
        assert forecast["forensic_modulation_applied"] == True
    
    def test_forensic_forecast_with_high_risk_cluster(self):
        """Test forecast with high-risk cluster"""
        activities = [
            Activity(
                activity_id="A-001",
                name="Task 1",
                remaining_duration=10.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=[]
            )
        ]
        
        enriched_features = {
            "A-001": {
                "drift_velocity": {"mode_shift_factor": 0.0},
                "cost_performance": {"risk_event_probability": 0.0}
            }
        }
        
        # High-risk cluster (Burnout Zone)
        risk_archetypes = {
            "A-001": get_risk_archetype_characteristics(2)
        }
        
        topology_metrics = {
            "A-001": {"variance_multiplier": 1.0}
        }
        
        skill_analysis = {"variance_increase_map": {}}
        
        forecast = compute_forensic_forecast(
            project_id="test-project",
            activities=activities,
            enriched_features=enriched_features,
            risk_archetypes=risk_archetypes,
            topology_metrics=topology_metrics,
            skill_analysis=skill_analysis,
            num_simulations=1000
        )
        
        # High-risk cluster should increase variance and failure probability
        assert forecast["forensic_modulation_applied"] == True
        # Forecast should be wider (higher P95 - P50 spread)
        spread = forecast["p95"] - forecast["p50"]
        assert spread > 0
    
    def test_forensic_forecast_complex_project(self):
        """Test forecast with complex project structure"""
        activities = [
            Activity(
                activity_id="A",
                name="Start",
                remaining_duration=5.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=["B", "C"]
            ),
            Activity(
                activity_id="B",
                name="Parallel 1",
                remaining_duration=3.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["A"],
                successors=["D"]
            ),
            Activity(
                activity_id="C",
                name="Parallel 2",
                remaining_duration=4.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["A"],
                successors=["D"]
            ),
            Activity(
                activity_id="D",
                name="End",
                remaining_duration=2.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["B", "C"],
                successors=[]
            )
        ]
        
        enriched_features = {
            act_id: {
                "drift_velocity": {"mode_shift_factor": 0.0},
                "cost_performance": {"risk_event_probability": 0.0}
            }
            for act_id in ["A", "B", "C", "D"]
        }
        
        risk_archetypes = {
            act_id: get_risk_archetype_characteristics(0)
            for act_id in ["A", "B", "C", "D"]
        }
        
        topology_metrics = {
            act_id: {"variance_multiplier": 1.0}
            for act_id in ["A", "B", "C", "D"]
        }
        
        skill_analysis = {"variance_increase_map": {}}
        
        forecast = compute_forensic_forecast(
            project_id="test-project",
            activities=activities,
            enriched_features=enriched_features,
            risk_archetypes=risk_archetypes,
            topology_metrics=topology_metrics,
            skill_analysis=skill_analysis,
            num_simulations=1000
        )
        
        # Critical path: A -> C -> D = 5 + 4 + 2 = 11 days
        # But with uncertainty, should be higher
        assert forecast["p50"] >= 10
        assert forecast["forensic_modulation_applied"] == True
