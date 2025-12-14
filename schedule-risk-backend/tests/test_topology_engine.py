"""
Unit tests for Topology Engine (Layer 2)
Tests: Centrality calculations, variance multipliers
"""

import pytest
import networkx as nx
from core.topology_engine import calculate_topology_metrics
from core.digital_twin import DigitalTwin
from core.models import Activity


class TestTopologyMetrics:
    """Tests for topology metrics calculation"""
    
    def test_simple_chain(self):
        """Test topology metrics for simple chain graph"""
        activities = [
            Activity(
                activity_id="A",
                name="Start",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=[]
            ),
            Activity(
                activity_id="B",
                name="Middle",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["A"],
                successors=[]
            )
        ]
        
        twin = DigitalTwin(activities)
        metrics = calculate_topology_metrics(twin)
        
        assert "A" in metrics
        assert "B" in metrics
        assert "betweenness_centrality" in metrics["A"]
        assert "eigenvector_centrality" in metrics["A"]
        assert "variance_multiplier" in metrics["A"]
        assert metrics["A"]["variance_multiplier"] >= 1.0
        assert metrics["A"]["variance_multiplier"] <= 1.5
    
    def test_bridge_node(self):
        """Test that bridge nodes have high centrality"""
        # Create graph: A -> B -> C, A -> D -> C
        # B and D are bridge nodes
        activities = [
            Activity(
                activity_id="A",
                name="Start",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=["B", "D"]
            ),
            Activity(
                activity_id="B",
                name="Bridge 1",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["A"],
                successors=["C"]
            ),
            Activity(
                activity_id="D",
                name="Bridge 2",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["A"],
                successors=["C"]
            ),
            Activity(
                activity_id="C",
                name="End",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["B", "D"],
                successors=[]
            )
        ]
        
        twin = DigitalTwin(activities)
        metrics = calculate_topology_metrics(twin)
        
        # B and D should have higher centrality than A or C
        assert metrics["B"]["betweenness_centrality"] > metrics["A"]["betweenness_centrality"]
        assert metrics["D"]["betweenness_centrality"] > metrics["A"]["betweenness_centrality"]
        # Variance multiplier should reflect centrality
        assert metrics["B"]["variance_multiplier"] >= metrics["A"]["variance_multiplier"]
    
    def test_isolated_node(self):
        """Test topology metrics for isolated node"""
        activities = [
            Activity(
                activity_id="A",
                name="Isolated",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=[]
            )
        ]
        
        twin = DigitalTwin(activities)
        metrics = calculate_topology_metrics(twin)
        
        assert "A" in metrics
        assert metrics["A"]["betweenness_centrality"] == 0.0
        assert metrics["A"]["variance_multiplier"] == 1.0  # No centrality = no variance increase
    
    def test_star_topology(self):
        """Test star topology (one central node)"""
        activities = [
            Activity(
                activity_id="Center",
                name="Center",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=["A", "B", "C"]
            ),
            Activity(
                activity_id="A",
                name="Spoke",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["Center"],
                successors=[]
            ),
            Activity(
                activity_id="B",
                name="Spoke",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["Center"],
                successors=[]
            ),
            Activity(
                activity_id="C",
                name="Spoke",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["Center"],
                successors=[]
            )
        ]
        
        twin = DigitalTwin(activities)
        metrics = calculate_topology_metrics(twin)
        
        # Center should have high centrality
        assert metrics["Center"]["betweenness_centrality"] > metrics["A"]["betweenness_centrality"]
        assert metrics["Center"]["variance_multiplier"] > metrics["A"]["variance_multiplier"]
    
    def test_caching(self):
        """Test that centrality calculations are cached"""
        activities = [
            Activity(
                activity_id="A",
                name="Start",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=["B"]
            ),
            Activity(
                activity_id="B",
                name="End",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["A"],
                successors=[]
            )
        ]
        
        twin = DigitalTwin(activities)
        
        # First call
        metrics1 = calculate_topology_metrics(twin)
        
        # Second call (should use cache)
        metrics2 = calculate_topology_metrics(twin)
        
        # Results should be identical
        assert metrics1["A"]["betweenness_centrality"] == metrics2["A"]["betweenness_centrality"]
        assert hasattr(twin, '_betweenness_cache')
        assert hasattr(twin, '_eigenvector_cache')
    
    def test_variance_multiplier_range(self):
        """Test that variance multiplier is in expected range"""
        activities = [
            Activity(
                activity_id=f"A{i}",
                name=f"Activity {i}",
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[] if i == 0 else [f"A{i-1}"],
                successors=[]
            )
            for i in range(5)
        ]
        
        twin = DigitalTwin(activities)
        metrics = calculate_topology_metrics(twin)
        
        for activity_id, metric in metrics.items():
            assert 1.0 <= metric["variance_multiplier"] <= 1.5  # Should be in this range
            assert 0.0 <= metric["betweenness_centrality"] <= 1.0
            assert 0.0 <= metric["eigenvector_centrality"] <= 1.0
