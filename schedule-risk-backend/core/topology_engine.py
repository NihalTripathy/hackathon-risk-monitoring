"""
Topology Engine - Layer 2
Calculates graph centrality metrics to identify bridge nodes
"""

from typing import Dict
import networkx as nx
from .digital_twin import DigitalTwin


def calculate_topology_metrics(twin: DigitalTwin) -> Dict[str, Dict]:
    """
    Calculate centrality metrics for all activities.
    
    Returns:
        {
            activity_id: {
                "betweenness_centrality": float,
                "eigenvector_centrality": float,
                "variance_multiplier": float  # High centrality = more uncertainty
            }
        }
    """
    graph = twin.graph
    
    # Calculate centralities (cache for performance)
    if not hasattr(twin, '_betweenness_cache'):
        try:
            twin._betweenness_cache = nx.betweenness_centrality(graph, normalized=True)
        except:
            twin._betweenness_cache = {}
    
    if not hasattr(twin, '_eigenvector_cache'):
        try:
            twin._eigenvector_cache = nx.eigenvector_centrality(graph, max_iter=1000)
        except:
            # Fallback if convergence fails
            twin._eigenvector_cache = {}
    
    topology_metrics = {}
    
    for activity_id in twin.activities.keys():
        bet = twin._betweenness_cache.get(activity_id, 0.0)
        eig = twin._eigenvector_cache.get(activity_id, 0.0)
        
        # High centrality = bridge node = more uncertainty
        combined_centrality = (bet * 0.7) + (eig * 0.3)
        
        # Variance multiplier: 1.0 (no change) to 1.5 (50% more variance)
        variance_multiplier = 1.0 + (combined_centrality * 0.5)
        
        topology_metrics[activity_id] = {
            "betweenness_centrality": bet,
            "eigenvector_centrality": eig,
            "variance_multiplier": variance_multiplier
        }
    
    return topology_metrics
