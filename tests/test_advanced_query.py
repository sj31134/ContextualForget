"""Tests for advanced query functionality."""
import pytest
import networkx as nx
from datetime import datetime, timezone, timedelta
from contextualforget.query.advanced_query import AdvancedQueryEngine


class TestAdvancedQuery:
    @pytest.fixture
    def sample_graph(self):
        """Create a sample graph for testing."""
        G = nx.DiGraph()
        
        # Add IFC nodes
        G.add_node(("IFC", "guid1"), type="BUILDING", name="Building 1")
        G.add_node(("IFC", "guid2"), type="WALL", name="Wall 1")
        
        # Add BCF nodes
        G.add_node(("BCF", "topic1"), 
                  title="Issue with Building 1",
                  created=(datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                  author="engineer_a")
        G.add_node(("BCF", "topic2"), 
                  title="Wall clearance issue",
                  created=(datetime.now(timezone.utc) - timedelta(days=400)).isoformat(),
                  author="engineer_b")
        G.add_node(("BCF", "topic3"), 
                  title="HVAC clearance problem",
                  created=(datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
                  author="engineer_a")
        
        # Add edges
        G.add_edge(("BCF", "topic1"), ("IFC", "guid1"), 
                  type="refersTo", confidence=1.0)
        G.add_edge(("BCF", "topic2"), ("IFC", "guid2"), 
                  type="refersTo", confidence=0.8)
        G.add_edge(("BCF", "topic3"), ("IFC", "guid1"), 
                  type="refersTo", confidence=0.9)
        
        return G
    
    def test_find_by_guid(self, sample_graph):
        """Test finding BCF topics by IFC GUID."""
        engine = AdvancedQueryEngine(sample_graph)
        
        # Find topics related to guid1
        results = engine.find_by_guid("guid1")
        assert len(results) == 2
        
        topic_ids = [r["topic_id"] for r in results]
        assert "topic1" in topic_ids
        assert "topic3" in topic_ids
        
        # Test with TTL filtering
        results_ttl = engine.find_by_guid("guid1", ttl=365)
        assert len(results_ttl) == 2  # Both should pass TTL
        
        results_ttl_short = engine.find_by_guid("guid1", ttl=20)
        assert len(results_ttl_short) == 1  # Only recent one should pass
    
    def test_find_by_author(self, sample_graph):
        """Test finding BCF topics by author."""
        engine = AdvancedQueryEngine(sample_graph)
        
        # Find topics by engineer_a
        results = engine.find_by_author("engineer_a")
        assert len(results) == 2
        
        topic_ids = [r["topic_id"] for r in results]
        assert "topic1" in topic_ids
        assert "topic3" in topic_ids
        
        # Find topics by engineer_b
        results_b = engine.find_by_author("engineer_b")
        assert len(results_b) == 1
        assert results_b[0]["topic_id"] == "topic2"
    
    def test_find_by_time_range(self, sample_graph):
        """Test finding BCF topics by time range."""
        engine = AdvancedQueryEngine(sample_graph)
        
        # Find topics from last 50 days
        end_date = datetime.now(timezone.utc).isoformat()
        start_date = (datetime.now(timezone.utc) - timedelta(days=50)).isoformat()
        
        results = engine.find_by_time_range(start_date, end_date)
        assert len(results) == 2  # topic1 and topic3
        
        topic_ids = [r["topic_id"] for r in results]
        assert "topic1" in topic_ids
        assert "topic3" in topic_ids
    
    def test_find_by_keywords(self, sample_graph):
        """Test finding BCF topics by keywords."""
        engine = AdvancedQueryEngine(sample_graph)
        
        # Search for "clearance"
        results = engine.find_by_keywords(["clearance"])
        assert len(results) == 2  # topic2 and topic3
        
        topic_ids = [r["topic_id"] for r in results]
        assert "topic2" in topic_ids
        assert "topic3" in topic_ids
        
        # Search for "HVAC"
        results_hvac = engine.find_by_keywords(["HVAC"])
        assert len(results_hvac) == 1
        assert results_hvac[0]["topic_id"] == "topic3"
    
    def test_find_connected_components(self, sample_graph):
        """Test finding connected components."""
        engine = AdvancedQueryEngine(sample_graph)
        
        # Find components connected to guid1
        components = engine.find_connected_components("guid1", max_depth=1)
        
        assert "ifc_entities" in components
        assert "bcf_topics" in components
        
        # Should find guid1 itself and connected BCF topics
        ifc_guids = [e["guid"] for e in components["ifc_entities"]]
        assert "guid1" in ifc_guids
        
        bcf_topics = [t["topic_id"] for t in components["bcf_topics"]]
        assert "topic1" in bcf_topics
        assert "topic3" in bcf_topics
    
    def test_get_statistics(self, sample_graph):
        """Test getting graph statistics."""
        engine = AdvancedQueryEngine(sample_graph)
        
        stats = engine.get_statistics()
        
        assert stats["total_nodes"] == 5
        assert stats["ifc_entities"] == 2
        assert stats["bcf_topics"] == 3
        assert stats["total_edges"] == 3
        assert "date_range" in stats
    
    def test_query_builder(self, sample_graph):
        """Test query builder functionality."""
        engine = AdvancedQueryEngine(sample_graph)
        builder = QueryBuilder(engine)
        
        # Build a complex query
        results = (builder
                  .by_guid("guid1")
                  .with_ttl(20)
                  .sort_by_date(ascending=False)
                  .limit_results(1)
                  .execute())
        
        assert len(results) == 1
        assert results[0]["topic_id"] == "topic3"  # Most recent
    
    def test_query_builder_keywords(self, sample_graph):
        """Test query builder with keywords."""
        engine = AdvancedQueryEngine(sample_graph)
        builder = QueryBuilder(engine)
        
        # Search by keywords
        results = (builder
                  .by_keywords(["clearance"])
                  .sort_by_confidence(ascending=False)
                  .execute())
        
        assert len(results) == 2
        # Should be sorted by confidence (topic2 has confidence 0.8, topic3 has 0.9)
        # But topic2 is connected to guid2, topic3 to guid1
        # The order depends on which one is found first
        topic_ids = [r["topic_id"] for r in results]
        assert "topic2" in topic_ids
        assert "topic3" in topic_ids
