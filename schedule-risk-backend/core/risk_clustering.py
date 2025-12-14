"""
Risk Clustering Engine - Layer 3
Unsupervised ML (K-Means) to identify risk archetypes
"""

from typing import List, Dict, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def build_clustering_vector(enriched_features: Dict) -> np.ndarray:
    """
    Build feature vector for clustering.
    V = [Float, FTE_Load, Drift_Ratio, Cost_Variance, Dependency_Count]
    
    Args:
        enriched_features: Dict with all features
    
    Returns: Fixed-size numpy array for K-Means
    """
    # Extract key features for clustering
    float_days = enriched_features.get("float_days", 0.0)
    fte_ratio = enriched_features.get("fte_ratio", 0.0)
    
    # Get drift ratio from forensic features
    drift_velocity = enriched_features.get("drift_velocity", {})
    drift_ratio = drift_velocity.get("drift_ratio", 0.0) if isinstance(drift_velocity, dict) else 0.0
    
    # Get cost variance from forensic features
    cost_performance = enriched_features.get("cost_performance", {})
    cost_variance = cost_performance.get("cost_variance", 0.0) if isinstance(cost_performance, dict) else 0.0
    
    # Dependency count
    predecessor_count = enriched_features.get("predecessor_count", 0)
    successor_count = enriched_features.get("successor_count", 0)
    dependency_count = predecessor_count + successor_count
    
    return np.array([
        float_days,
        fte_ratio,
        drift_ratio,
        cost_variance,
        dependency_count
    ])


def cluster_activities(
    all_features: List[Dict],
    n_clusters: int = 4
) -> Dict[str, int]:
    """
    Cluster activities into risk archetypes.
    
    Args:
        all_features: List of feature dicts (one per activity)
        n_clusters: Number of clusters (default: 4)
    
    Returns:
        Dict mapping activity_id to cluster_id
    """
    if len(all_features) < n_clusters:
        # Not enough activities to cluster
        return {f["activity_id"]: 0 for f in all_features}
    
    # Build feature vectors
    feature_vectors = []
    activity_ids = []
    
    for features_dict in all_features:
        try:
            vector = build_clustering_vector(features_dict)
            feature_vectors.append(vector)
            activity_ids.append(features_dict["activity_id"])
        except Exception as e:
            # Skip activities with missing features
            print(f"[Warning] Failed to build clustering vector for {features_dict.get('activity_id', 'unknown')}: {e}")
            continue
    
    if not feature_vectors:
        return {}
    
    feature_vectors = np.array(feature_vectors)
    
    # Normalize features
    scaler = StandardScaler()
    try:
        feature_vectors_scaled = scaler.fit_transform(feature_vectors)
    except Exception as e:
        print(f"[Warning] Failed to scale feature vectors: {e}")
        return {aid: 0 for aid in activity_ids}
    
    # Perform K-Means clustering
    try:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(feature_vectors_scaled)
    except Exception as e:
        print(f"[Warning] K-Means clustering failed: {e}")
        return {aid: 0 for aid in activity_ids}
    
    # Map activity_id to cluster
    activity_clusters = {}
    for i, activity_id in enumerate(activity_ids):
        activity_clusters[activity_id] = int(cluster_labels[i])
    
    return activity_clusters


def get_risk_archetype_characteristics(cluster_id: int) -> Dict:
    """
    Get characteristics of a risk archetype.
    
    Cluster Archetypes:
    - 0: Low Risk (Stable Zone)
    - 1: Medium Risk (Watch Zone)
    - 2: High Risk (Burnout Zone)
    - 3: Very High Risk (Failure Zone)
    
    Returns:
        {
            "failure_probability": float,  # Base failure prob for this cluster
            "variance_multiplier": float,  # How much to increase variance
            "mode_shift_factor": float     # How much to shift mode
        }
    """
    archetypes = {
        0: {  # Low Risk (Stable Zone)
            "failure_probability": 0.05,  # 5% base failure
            "variance_multiplier": 1.0,    # No variance increase
            "mode_shift_factor": 0.0       # No mode shift
        },
        1: {  # Medium Risk (Watch Zone)
            "failure_probability": 0.15,   # 15% base failure
            "variance_multiplier": 1.2,   # +20% variance
            "mode_shift_factor": 0.1       # +10% mode shift
        },
        2: {  # High Risk (Burnout Zone)
            "failure_probability": 0.30,   # 30% base failure
            "variance_multiplier": 1.5,    # +50% variance
            "mode_shift_factor": 0.2       # +20% mode shift
        },
        3: {  # Very High Risk (Failure Zone)
            "failure_probability": 0.50,   # 50% base failure
            "variance_multiplier": 2.0,    # +100% variance
            "mode_shift_factor": 0.3       # +30% mode shift
        }
    }
    
    return archetypes.get(cluster_id, archetypes[0])
