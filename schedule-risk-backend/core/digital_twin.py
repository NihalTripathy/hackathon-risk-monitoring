"""
Digital twin implementation for project modeling
"""

import networkx as nx
from typing import List, Optional
from .models import Activity as ActivityModel

# In-memory cache for digital twins (computed, not stored in DB)
DIGITAL_TWINS = {}


class DigitalTwin:
    def __init__(self, activities):
        self.activities = {a.activity_id: a for a in activities}
        self.graph = nx.DiGraph()
        self.has_cycles = False
        self.cycle_warning = None
        self._build()

    def _build(self):
        for a in self.activities.values():
            self.graph.add_node(a.activity_id)
            for p in a.predecessors:
                if p.strip():
                    self.graph.add_edge(p, a.activity_id)
        
        # Detect cycles (warn but don't fail - Monte Carlo handles it)
        try:
            # Try topological sort - if it fails, there are cycles
            list(nx.topological_sort(self.graph))
            self.has_cycles = False
        except nx.NetworkXError:
            self.has_cycles = True
            # Find cycles for warning message
            try:
                cycles = list(nx.simple_cycles(self.graph))
                if cycles:
                    cycle_str = " -> ".join(cycles[0][:5])  # Show first 5 nodes
                    if len(cycles[0]) > 5:
                        cycle_str += "..."
                    self.cycle_warning = f"Graph contains cycles (e.g., {cycle_str}). Critical path calculations may be approximate."
                else:
                    self.cycle_warning = "Graph contains cycles. Critical path calculations may be approximate."
            except:
                self.cycle_warning = "Graph contains cycles. Critical path calculations may be approximate."


def get_or_build_twin(project_id: str, activities: Optional[List[ActivityModel]] = None):
    """Get or build digital twin for a project"""
    # Check cache first
    if project_id in DIGITAL_TWINS:
        return DIGITAL_TWINS[project_id]
    
    # Build twin from provided activities
    if activities is None:
        raise ValueError(f"Activities must be provided for project {project_id}")
    
    twin = DigitalTwin(activities)
    DIGITAL_TWINS[project_id] = twin
    return twin

