"""ContextualForget: Digital-twin Graph-RAG with long-term memory and forgetting."""

__version__ = "0.0.1"

# Import main components for easy access
from .cli import app
from .core import (
    ForgettingManager,
    create_default_forgetting_policy,
    expired,
    extract_ifc_entities,
    parse_bcf_zip,
    read_jsonl,
    score,
    write_jsonl,
)
from .llm import LLMQueryEngine, NaturalLanguageProcessor, QueryIntent
from .performance import GraphOptimizer, MemoryOptimizer, optimize_for_production
from .query import AdvancedQueryEngine, QueryBuilder, find_by_guid
from .realtime import FileChangeEvent, FileWatcher, GraphUpdater, RealtimeMonitor
from .visualization import GraphVisualizer, TimelineVisualizer, create_visualization_report

__all__ = [
    # Core functionality
    "expired",
    "score", 
    "ForgettingManager",
    "create_default_forgetting_policy",
    "read_jsonl",
    "write_jsonl",
    "extract_ifc_entities",
    "parse_bcf_zip",
    # Query functionality
    "find_by_guid",
    "AdvancedQueryEngine",
    "QueryBuilder",
    # Visualization
    "GraphVisualizer",
    "TimelineVisualizer",
    "create_visualization_report",
    # Performance
    "GraphOptimizer",
    "MemoryOptimizer", 
    "optimize_for_production",
    # LLM and Natural Language Processing
    "NaturalLanguageProcessor",
    "LLMQueryEngine",
    "QueryIntent",
    # Real-time monitoring
    "FileWatcher",
    "FileChangeEvent",
    "GraphUpdater",
    "RealtimeMonitor",
    # CLI
    "app"
]
