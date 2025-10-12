"""ContextualForget: Digital-twin Graph-RAG with long-term memory and forgetting."""

__version__ = "0.0.1"

# Import main components for easy access
from .core import (
    expired,
    score,
    ForgettingManager,
    create_default_forgetting_policy,
    read_jsonl,
    write_jsonl,
    extract_ifc_entities,
    parse_bcf_zip
)
from .query import (
    find_by_guid,
    AdvancedQueryEngine,
    QueryBuilder
)
from .visualization import (
    GraphVisualizer,
    TimelineVisualizer,
    create_visualization_report
)
from .performance import (
    GraphOptimizer,
    MemoryOptimizer,
    optimize_for_production
)
from .llm import (
    NaturalLanguageProcessor,
    LLMQueryEngine,
    QueryIntent
)
from .realtime import (
    FileWatcher,
    FileChangeEvent,
    GraphUpdater,
    RealtimeMonitor
)
from .cli import app

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
