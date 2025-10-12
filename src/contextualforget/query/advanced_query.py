"""
Advanced query capabilities for the ContextualForget system.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import networkx as nx

from ..core import ForgettingManager, create_default_forgetting_policy, expired


class AdvancedQueryEngine:
    """Advanced query engine with multiple search strategies."""
    
    def __init__(self, graph: nx.DiGraph, forgetting_manager: ForgettingManager | None = None):
        self.graph = graph
        self.forgetting_manager = forgetting_manager or create_default_forgetting_policy()
    
    def get_ifc_element_info(self, guid: str) -> dict[str, Any]:
        """Get IFC element information by GUID."""
        target_node = ("IFC", guid)
        
        if target_node not in self.graph:
            return {"error": f"GUID {guid} not found"}
        
        node_data = self.graph.nodes[target_node]
        return {
            "guid": guid,
            "type": node_data.get("type", "Unknown"),
            "name": node_data.get("name", guid),
            "data": node_data
        }
    
    def find_by_guid(self, guid: str, ttl: int = 0, limit: int = 10) -> list[dict]:
        """Find BCF topics related to a specific IFC GUID."""
        hits = []
        target_node = ("IFC", guid)
        
        if target_node not in self.graph:
            return hits
        
        # Check predecessors (BCF nodes that point to this IFC node)
        for predecessor in self.graph.predecessors(target_node):
            if predecessor[0] == "BCF":
                edge_data = self.graph.get_edge_data(predecessor, target_node, {})
                node_data = self.graph.nodes[predecessor]
                
                # Apply TTL filtering
                if ttl > 0 and expired(node_data.get("created", ""), ttl):
                    continue
                
                hits.append({
                    "topic_id": predecessor[1],
                    "created": node_data.get("created"),
                    "title": node_data.get("title", ""),
                    "author": node_data.get("author", ""),
                    "edge": {
                        "type": edge_data.get("type", "refersTo"),
                        "confidence": edge_data.get("confidence", 1.0)
                    }
                })
                
                # Apply limit
                if len(hits) >= limit:
                    break
        
        return hits
    
    def find_by_author(self, author: str, ttl: int = 0, limit: int = 10) -> list[dict]:
        """Find all BCF topics by a specific author."""
        hits = []
        
        for node, data in self.graph.nodes(data=True):
            if node[0] == "BCF" and data.get("author") == author:
                # Apply TTL filtering
                if ttl > 0 and expired(data.get("created", ""), ttl):
                    continue
                
                # Find related IFC entities
                related_guids = []
                for neighbor in self.graph.neighbors(node):
                    if neighbor[0] == "IFC":
                        related_guids.append(neighbor[1])
                
                hits.append({
                    "topic_id": node[1],
                    "created": data.get("created"),
                    "title": data.get("title", ""),
                    "author": data.get("author", ""),
                    "related_guids": related_guids
                })
                
                # Apply limit
                if len(hits) >= limit:
                    break
        
        return hits
    
    def find_by_time_range(self, start_date: str, end_date: str) -> list[dict]:
        """Find BCF topics within a specific time range."""
        hits = []
        
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except Exception:
            return hits
        
        for node, data in self.graph.nodes(data=True):
            if node[0] == "BCF":
                created_str = data.get("created", "")
                if created_str:
                    try:
                        created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                        if start_dt <= created_dt <= end_dt:
                            # Find related IFC entities
                            related_guids = []
                            for neighbor in self.graph.neighbors(node):
                                if neighbor[0] == "IFC":
                                    related_guids.append(neighbor[1])
                            
                            hits.append({
                                "topic_id": node[1],
                                "created": data.get("created"),
                                "title": data.get("title", ""),
                                "author": data.get("author", ""),
                                "related_guids": related_guids
                            })
                    except Exception:
                        continue
        
        return hits
    
    def find_by_keywords(self, keywords: list[str], ttl: int = 0) -> list[dict]:
        """Find BCF topics containing specific keywords."""
        hits = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for node, data in self.graph.nodes(data=True):
            if node[0] == "BCF":
                # Apply TTL filtering
                if ttl > 0 and expired(data.get("created", ""), ttl):
                    continue
                
                # Check if any keyword matches
                title = data.get("title", "").lower()
                description = data.get("description", "").lower()
                text_content = f"{title} {description}"
                
                if any(kw in text_content for kw in keywords_lower):
                    # Find related IFC entities
                    related_guids = []
                    for neighbor in self.graph.neighbors(node):
                        if neighbor[0] == "IFC":
                            related_guids.append(neighbor[1])
                    
                    hits.append({
                        "topic_id": node[1],
                        "created": data.get("created"),
                        "title": data.get("title", ""),
                        "author": data.get("author", ""),
                        "related_guids": related_guids,
                        "matched_keywords": [kw for kw in keywords_lower if kw in text_content]
                    })
        
        return hits
    
    def find_connected_components(self, guid: str, max_depth: int = 2) -> dict:
        """Find all entities connected to a GUID within max_depth."""
        target_node = ("IFC", guid)
        
        if target_node not in self.graph:
            return {"error": f"GUID {guid} not found"}
        
        # Use BFS to find connected components
        visited = set()
        queue = [(target_node, 0)]
        components = {"ifc_entities": [], "bcf_topics": []}
        
        while queue:
            current_node, depth = queue.pop(0)
            
            if current_node in visited or depth > max_depth:
                continue
            
            visited.add(current_node)
            
            if current_node[0] == "IFC":
                components["ifc_entities"].append({
                    "guid": current_node[1],
                    "depth": depth,
                    "type": self.graph.nodes[current_node].get("type", "unknown")
                })
            else:
                components["bcf_topics"].append({
                    "topic_id": current_node[1],
                    "depth": depth,
                    "title": self.graph.nodes[current_node].get("title", ""),
                    "created": self.graph.nodes[current_node].get("created", "")
                })
            
            # Add neighbors to queue (both predecessors and successors)
            for neighbor in self.graph.neighbors(current_node):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))
            for predecessor in self.graph.predecessors(current_node):
                if predecessor not in visited:
                    queue.append((predecessor, depth + 1))
        
        return components
    
    def get_statistics(self) -> dict:
        """Get graph statistics."""
        ifc_count = sum(1 for node in self.graph.nodes() if node[0] == "IFC")
        bcf_count = sum(1 for node in self.graph.nodes() if node[0] == "BCF")
        edge_count = self.graph.number_of_edges()
        
        # Calculate average degree
        degrees = [self.graph.degree(node) for node in self.graph.nodes()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0
        
        # Get date range
        dates = []
        for node, data in self.graph.nodes(data=True):
            if node[0] == "BCF":
                created = data.get("created", "")
                if created:
                    try:
                        date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        dates.append(date)
                    except Exception:
                        continue
        
        date_range = {}
        if dates:
            date_range = {
                "earliest": min(dates).isoformat(),
                "latest": max(dates).isoformat(),
                "span_days": (max(dates) - min(dates)).days
            }
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "ifc_entities": ifc_count,
            "bcf_topics": bcf_count,
            "total_edges": edge_count,
            "average_degree": round(avg_degree, 2),
            "date_range": date_range,
            "forgetting_stats": self.forgetting_manager.get_forgetting_stats()
        }
    
    def apply_forgetting_policy(self, events: list[dict]) -> list[dict]:
        """Apply forgetting policy to filter events."""
        return self.forgetting_manager.filter_events(events)


class QueryBuilder:
    """Builder pattern for complex queries."""
    
    def __init__(self, engine: AdvancedQueryEngine):
        self.engine = engine
        self.filters = []
        self.sort_by = None
        self.limit = None
    
    def by_guid(self, guid: str) -> QueryBuilder:
        """Filter by IFC GUID."""
        self.filters.append(("guid", guid))
        return self
    
    def by_author(self, author: str) -> QueryBuilder:
        """Filter by author."""
        self.filters.append(("author", author))
        return self
    
    def by_keywords(self, keywords: list[str]) -> QueryBuilder:
        """Filter by keywords."""
        self.filters.append(("keywords", keywords))
        return self
    
    def by_time_range(self, start_date: str, end_date: str) -> QueryBuilder:
        """Filter by time range."""
        self.filters.append(("time_range", (start_date, end_date)))
        return self
    
    def with_ttl(self, ttl_days: int) -> QueryBuilder:
        """Apply TTL filter."""
        self.filters.append(("ttl", ttl_days))
        return self
    
    def sort_by_date(self, ascending: bool = True) -> QueryBuilder:
        """Sort by date."""
        self.sort_by = ("date", ascending)
        return self
    
    def sort_by_confidence(self, ascending: bool = False) -> QueryBuilder:
        """Sort by confidence."""
        self.sort_by = ("confidence", ascending)
        return self
    
    def limit_results(self, limit: int) -> QueryBuilder:
        """Limit number of results."""
        self.limit = limit
        return self
    
    def execute(self) -> list[dict]:
        """Execute the query."""
        results = []
        
        # Apply filters
        for filter_type, filter_value in self.filters:
            if filter_type == "guid":
                results = self.engine.find_by_guid(filter_value)
            elif filter_type == "author":
                results = self.engine.find_by_author(filter_value)
            elif filter_type == "keywords":
                results = self.engine.find_by_keywords(filter_value)
            elif filter_type == "time_range":
                start_date, end_date = filter_value
                results = self.engine.find_by_time_range(start_date, end_date)
            elif filter_type == "ttl":
                # Apply TTL to existing results
                results = [r for r in results if not expired(r.get("created", ""), filter_value)]
        
        # Apply sorting
        if self.sort_by and results:
            sort_key, ascending = self.sort_by
            if sort_key == "date":
                results.sort(key=lambda x: x.get("created", ""), reverse=not ascending)
            elif sort_key == "confidence":
                results.sort(key=lambda x: x.get("edge", {}).get("confidence", 0), reverse=not ascending)
        
        # Apply limit
        if self.limit:
            results = results[:self.limit]
        
        return results
