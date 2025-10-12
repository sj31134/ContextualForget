"""
Visualization tools for the ContextualForget graph system.
"""
from __future__ import annotations
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime


class GraphVisualizer:
    """Visualizes the ContextualForget graph structure."""
    
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.ifc_nodes = []
        self.bcf_nodes = []
        self._categorize_nodes()
    
    def _categorize_nodes(self):
        """Categorize nodes into IFC and BCF types."""
        for node, data in self.graph.nodes(data=True):
            if node[0] == "IFC":
                self.ifc_nodes.append((node, data))
            elif node[0] == "BCF":
                self.bcf_nodes.append((node, data))
    
    def plot_graph(self, 
                   figsize: Tuple[int, int] = (12, 8),
                   node_size: int = 1000,
                   font_size: int = 8,
                   save_path: Optional[str] = None) -> plt.Figure:
        """Plot the entire graph."""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Use spring layout for better visualization
        pos = nx.spring_layout(self.graph, k=3, iterations=50)
        
        # Draw IFC nodes (blue)
        ifc_pos = {node: pos[node] for node, _ in self.ifc_nodes}
        nx.draw_networkx_nodes(self.graph, ifc_pos, 
                              nodelist=[node for node, _ in self.ifc_nodes],
                              node_color='lightblue', 
                              node_size=node_size,
                              alpha=0.8)
        
        # Draw BCF nodes (orange)
        bcf_pos = {node: pos[node] for node, _ in self.bcf_nodes}
        nx.draw_networkx_nodes(self.graph, bcf_pos,
                              nodelist=[node for node, _ in self.bcf_nodes],
                              node_color='orange',
                              node_size=node_size,
                              alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(self.graph, pos, 
                              edge_color='gray',
                              arrows=True,
                              arrowsize=20,
                              alpha=0.6)
        
        # Draw labels
        labels = {}
        for node, data in self.graph.nodes(data=True):
            if node[0] == "IFC":
                labels[node] = f"IFC\n{node[1][:8]}..."
            else:
                labels[node] = f"BCF\n{node[1][:8]}..."
        
        nx.draw_networkx_labels(self.graph, pos, labels, font_size=font_size)
        
        # Add legend
        ifc_patch = mpatches.Patch(color='lightblue', label='IFC Entities')
        bcf_patch = mpatches.Patch(color='orange', label='BCF Topics')
        ax.legend(handles=[ifc_patch, bcf_patch])
        
        ax.set_title("ContextualForget Graph Structure")
        ax.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_subgraph(self, 
                      target_guid: str,
                      figsize: Tuple[int, int] = (10, 6),
                      save_path: Optional[str] = None) -> plt.Figure:
        """Plot subgraph around a specific IFC GUID."""
        # Find all nodes connected to the target GUID
        target_node = ("IFC", target_guid)
        if target_node not in self.graph:
            raise ValueError(f"GUID {target_guid} not found in graph")
        
        # Get all connected nodes
        connected_nodes = set([target_node])
        for neighbor in self.graph.neighbors(target_node):
            connected_nodes.add(neighbor)
        for predecessor in self.graph.predecessors(target_node):
            connected_nodes.add(predecessor)
        
        # Create subgraph
        subgraph = self.graph.subgraph(connected_nodes)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Use circular layout for subgraph
        pos = nx.circular_layout(subgraph)
        
        # Draw nodes
        ifc_nodes = [node for node in subgraph.nodes() if node[0] == "IFC"]
        bcf_nodes = [node for node in subgraph.nodes() if node[0] == "BCF"]
        
        nx.draw_networkx_nodes(subgraph, pos,
                              nodelist=ifc_nodes,
                              node_color='lightblue',
                              node_size=1500,
                              alpha=0.8)
        
        nx.draw_networkx_nodes(subgraph, pos,
                              nodelist=bcf_nodes,
                              node_color='orange',
                              node_size=1500,
                              alpha=0.8)
        
        # Highlight target node
        nx.draw_networkx_nodes(subgraph, pos,
                              nodelist=[target_node],
                              node_color='red',
                              node_size=2000,
                              alpha=0.9)
        
        # Draw edges
        nx.draw_networkx_edges(subgraph, pos,
                              edge_color='gray',
                              arrows=True,
                              arrowsize=20,
                              alpha=0.6)
        
        # Draw labels
        labels = {}
        for node in subgraph.nodes():
            if node[0] == "IFC":
                labels[node] = f"IFC\n{node[1][:8]}..."
            else:
                labels[node] = f"BCF\n{node[1][:8]}..."
        
        nx.draw_networkx_labels(subgraph, pos, labels, font_size=10)
        
        # Add legend
        ifc_patch = mpatches.Patch(color='lightblue', label='IFC Entities')
        bcf_patch = mpatches.Patch(color='orange', label='BCF Topics')
        target_patch = mpatches.Patch(color='red', label='Target GUID')
        ax.legend(handles=[ifc_patch, bcf_patch, target_patch])
        
        ax.set_title(f"Subgraph for GUID: {target_guid}")
        ax.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig


class TimelineVisualizer:
    """Visualizes event timelines and forgetting patterns."""
    
    def __init__(self, events: List[Dict]):
        self.events = events
    
    def plot_timeline(self, 
                      figsize: Tuple[int, int] = (12, 6),
                      save_path: Optional[str] = None) -> plt.Figure:
        """Plot event timeline."""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Parse dates and sort events
        event_dates = []
        event_labels = []
        
        for event in self.events:
            try:
                date_str = event.get("created", "")
                if date_str:
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    event_dates.append(date)
                    event_labels.append(event.get("title", "Unknown")[:30])
            except Exception:
                continue
        
        if not event_dates:
            ax.text(0.5, 0.5, "No valid dates found", 
                   ha='center', va='center', transform=ax.transAxes)
            return fig
        
        # Create timeline
        y_positions = range(len(event_dates))
        
        ax.scatter(event_dates, y_positions, 
                  c='blue', alpha=0.7, s=100)
        
        # Add labels
        for i, (date, label) in enumerate(zip(event_dates, event_labels)):
            ax.annotate(label, (date, i), 
                       xytext=(5, 0), textcoords='offset points',
                       fontsize=8, alpha=0.8)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Event Index')
        ax.set_title('Event Timeline')
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_forgetting_curve(self, 
                             ttl_days: int = 365,
                             figsize: Tuple[int, int] = (10, 6),
                             save_path: Optional[str] = None) -> plt.Figure:
        """Plot forgetting curve based on TTL."""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Calculate retention over time
        days = list(range(0, ttl_days + 1, 30))
        retention_rates = []
        
        for day in days:
            retained = 0
            total = 0
            
            for event in self.events:
                try:
                    date_str = event.get("created", "")
                    if date_str:
                        event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        age_days = (datetime.now() - event_date).days
                        total += 1
                        
                        if age_days <= day:
                            retained += 1
                except Exception:
                    continue
            
            if total > 0:
                retention_rates.append(retained / total)
            else:
                retention_rates.append(0.0)
        
        ax.plot(days, retention_rates, 'b-', linewidth=2, marker='o')
        ax.set_xlabel('Days')
        ax.set_ylabel('Retention Rate')
        ax.set_title(f'Forgetting Curve (TTL: {ttl_days} days)')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.1)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig


def create_visualization_report(graph_path: str, 
                               output_dir: str = "visualizations"):
    """Create a comprehensive visualization report."""
    import os
    import pickle
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load graph
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
    
    # Create graph visualizer
    visualizer = GraphVisualizer(graph)
    
    # Plot full graph
    fig1 = visualizer.plot_graph(save_path=f"{output_dir}/full_graph.png")
    plt.close(fig1)
    
    # Plot subgraph for sample GUID
    try:
        fig2 = visualizer.plot_subgraph(
            "1kTvXnbbzCWw8lcMd1dR4o",
            save_path=f"{output_dir}/subgraph_sample.png"
        )
        plt.close(fig2)
    except ValueError:
        print("Sample GUID not found in graph")
    
    # Create timeline visualizer
    bcf_events = []
    for node, data in graph.nodes(data=True):
        if node[0] == "BCF":
            bcf_events.append(data)
    
    if bcf_events:
        timeline_viz = TimelineVisualizer(bcf_events)
        
        # Plot timeline
        fig3 = timeline_viz.plot_timeline(save_path=f"{output_dir}/timeline.png")
        plt.close(fig3)
        
        # Plot forgetting curve
        fig4 = timeline_viz.plot_forgetting_curve(save_path=f"{output_dir}/forgetting_curve.png")
        plt.close(fig4)
    
    print(f"Visualization report created in {output_dir}/")
    return output_dir
