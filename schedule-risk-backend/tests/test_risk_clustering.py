"""
Unit tests for Risk Clustering Engine (Layer 3)
Tests: Feature vector building, K-Means clustering, risk archetypes
"""

import pytest
import numpy as np
from core.risk_clustering import (
    build_clustering_vector,
    cluster_activities,
    get_risk_archetype_characteristics
)


class TestFeatureVectorBuilder:
    """Tests for feature vector construction"""
    
    def test_build_clustering_vector_complete(self):
        """Test building feature vector with all features"""
        enriched_features = {
            "activity_id": "A-001",
            "float_days": 2.0,
            "fte_ratio": 0.8,
            "drift_velocity": {"drift_ratio": 0.3},
            "cost_performance": {"cost_variance": 500.0},
            "predecessor_count": 2,
            "successor_count": 3
        }
        
        vector = build_clustering_vector(enriched_features)
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 5
        assert vector[0] == 2.0  # float_days
        assert vector[1] == 0.8  # fte_ratio
        assert vector[2] == 0.3  # drift_ratio
        assert vector[3] == 500.0  # cost_variance
        assert vector[4] == 5  # dependency_count (2+3)
    
    def test_build_clustering_vector_missing_features(self):
        """Test building vector with missing features"""
        enriched_features = {
            "activity_id": "A-002"
        }
        
        vector = build_clustering_vector(enriched_features)
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 5
        assert all(v == 0.0 for v in vector)  # All defaults to 0
    
    def test_build_clustering_vector_nested_dicts(self):
        """Test building vector with nested dict structures"""
        enriched_features = {
            "activity_id": "A-003",
            "float_days": 5.0,
            "fte_ratio": 1.2,
            "drift_velocity": {"drift_ratio": 0.5},
            "cost_performance": {"cost_variance": -200.0},
            "predecessor_count": 1,
            "successor_count": 0
        }
        
        vector = build_clustering_vector(enriched_features)
        
        assert vector[0] == 5.0
        assert vector[1] == 1.2
        assert vector[2] == 0.5
        assert vector[3] == -200.0
        assert vector[4] == 1


class TestClustering:
    """Tests for K-Means clustering"""
    
    def test_cluster_activities_sufficient_data(self):
        """Test clustering with sufficient activities"""
        all_features = [
            {
                "activity_id": f"A-{i}",
                "float_days": float(i),
                "fte_ratio": 0.5 + (i * 0.1),
                "drift_velocity": {"drift_ratio": 0.1 * i},
                "cost_performance": {"cost_variance": 100.0 * i},
                "predecessor_count": i % 3,
                "successor_count": (i + 1) % 3
            }
            for i in range(10)  # 10 activities, 4 clusters
        ]
        
        clusters = cluster_activities(all_features, n_clusters=4)
        
        assert len(clusters) == 10
        assert all(0 <= cluster_id <= 3 for cluster_id in clusters.values())
    
    def test_cluster_activities_insufficient_data(self):
        """Test clustering with insufficient activities"""
        all_features = [
            {
                "activity_id": f"A-{i}",
                "float_days": float(i),
                "fte_ratio": 0.5,
                "drift_velocity": {},
                "cost_performance": {},
                "predecessor_count": 0,
                "successor_count": 0
            }
            for i in range(2)  # Only 2 activities, but 4 clusters requested
        ]
        
        clusters = cluster_activities(all_features, n_clusters=4)
        
        # Should assign all to cluster 0 when insufficient data
        assert len(clusters) == 2
        assert all(cluster_id == 0 for cluster_id in clusters.values())
    
    def test_cluster_activities_empty(self):
        """Test clustering with empty list"""
        clusters = cluster_activities([], n_clusters=4)
        
        assert clusters == {}
    
    def test_cluster_activities_consistent(self):
        """Test that clustering is consistent (same input = same output)"""
        all_features = [
            {
                "activity_id": f"A-{i}",
                "float_days": float(i),
                "fte_ratio": 0.5,
                "drift_velocity": {"drift_ratio": 0.1},
                "cost_performance": {"cost_variance": 100.0},
                "predecessor_count": 0,
                "successor_count": 0
            }
            for i in range(8)
        ]
        
        clusters1 = cluster_activities(all_features, n_clusters=4)
        clusters2 = cluster_activities(all_features, n_clusters=4)
        
        # Should be identical (random_state=42 ensures reproducibility)
        assert clusters1 == clusters2
    
    def test_cluster_activities_missing_features(self):
        """Test clustering with activities missing features"""
        all_features = [
            {
                "activity_id": "A-001",
                "float_days": 2.0,
                "fte_ratio": 0.8,
                "drift_velocity": {"drift_ratio": 0.3},
                "cost_performance": {"cost_variance": 500.0},
                "predecessor_count": 2,
                "successor_count": 3
            },
            {
                "activity_id": "A-002"
                # Missing all features
            }
        ]
        
        # Should handle gracefully
        clusters = cluster_activities(all_features, n_clusters=4)
        
        # A-001 should be clustered, A-002 might be skipped or defaulted
        assert "A-001" in clusters or len(clusters) == 0


class TestRiskArchetypes:
    """Tests for risk archetype characteristics"""
    
    def test_low_risk_archetype(self):
        """Test low risk cluster characteristics"""
        archetype = get_risk_archetype_characteristics(0)
        
        assert archetype["failure_probability"] == 0.05
        assert archetype["variance_multiplier"] == 1.0
        assert archetype["mode_shift_factor"] == 0.0
    
    def test_medium_risk_archetype(self):
        """Test medium risk cluster characteristics"""
        archetype = get_risk_archetype_characteristics(1)
        
        assert archetype["failure_probability"] == 0.15
        assert archetype["variance_multiplier"] == 1.2
        assert archetype["mode_shift_factor"] == 0.1
    
    def test_high_risk_archetype(self):
        """Test high risk cluster characteristics"""
        archetype = get_risk_archetype_characteristics(2)
        
        assert archetype["failure_probability"] == 0.30
        assert archetype["variance_multiplier"] == 1.5
        assert archetype["mode_shift_factor"] == 0.2
    
    def test_very_high_risk_archetype(self):
        """Test very high risk cluster characteristics"""
        archetype = get_risk_archetype_characteristics(3)
        
        assert archetype["failure_probability"] == 0.50
        assert archetype["variance_multiplier"] == 2.0
        assert archetype["mode_shift_factor"] == 0.3
    
    def test_invalid_cluster_id(self):
        """Test with invalid cluster ID (should default to low risk)"""
        archetype = get_risk_archetype_characteristics(99)
        
        # Should default to cluster 0 (low risk)
        assert archetype["failure_probability"] == 0.05
        assert archetype["variance_multiplier"] == 1.0
        assert archetype["mode_shift_factor"] == 0.0
    
    def test_archetype_progression(self):
        """Test that risk increases with cluster ID"""
        archetypes = [get_risk_archetype_characteristics(i) for i in range(4)]
        
        # Failure probability should increase
        assert archetypes[0]["failure_probability"] < archetypes[1]["failure_probability"]
        assert archetypes[1]["failure_probability"] < archetypes[2]["failure_probability"]
        assert archetypes[2]["failure_probability"] < archetypes[3]["failure_probability"]
        
        # Variance multiplier should increase
        assert archetypes[0]["variance_multiplier"] < archetypes[1]["variance_multiplier"]
        assert archetypes[1]["variance_multiplier"] < archetypes[2]["variance_multiplier"]
        assert archetypes[2]["variance_multiplier"] < archetypes[3]["variance_multiplier"]
        
        # Mode shift should increase
        assert archetypes[0]["mode_shift_factor"] < archetypes[1]["mode_shift_factor"]
        assert archetypes[1]["mode_shift_factor"] < archetypes[2]["mode_shift_factor"]
        assert archetypes[2]["mode_shift_factor"] < archetypes[3]["mode_shift_factor"]
