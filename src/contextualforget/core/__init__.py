"""Core functionality for ContextualForget system."""

from .advanced_forgetting import (
    CompositeForgettingPolicy,
    ContradictionPolicy,
    ForgettingManager,
    ForgettingPolicy,
    ImportanceBasedPolicy,
    TTLPolicy,
    WeightedDecayPolicy,
    calculate_event_importance,
    create_default_forgetting_policy,
)
from .eval_metrics import ndcg_at_k
from .forgetting import expired, score
from .logging import (
    DataPipelineLogger,
    PerformanceMonitor,
    QueryLogger,
    get_logger,
    log_execution_time,
    log_graph_operations,
    setup_logging,
)
from .monitoring import (
    HealthChecker,
    MetricsCollector,
    get_health_status,
    get_metrics_summary,
    start_monitoring,
    stop_monitoring,
)
from .utils import extract_ifc_entities, parse_bcf_zip, read_jsonl, write_jsonl

__all__ = [
    # Forgetting
    "expired",
    "score",
    "ForgettingPolicy",
    "TTLPolicy", 
    "WeightedDecayPolicy",
    "ImportanceBasedPolicy",
    "ContradictionPolicy",
    "CompositeForgettingPolicy",
    "ForgettingManager",
    "create_default_forgetting_policy",
    "calculate_event_importance",
    # Utils
    "read_jsonl",
    "write_jsonl", 
    "extract_ifc_entities",
    "parse_bcf_zip",
    # Evaluation
    "ndcg_at_k",
    # Logging
    "setup_logging",
    "get_logger",
    "log_execution_time",
    "log_graph_operations",
    "QueryLogger",
    "DataPipelineLogger",
    "PerformanceMonitor",
    # Monitoring
    "start_monitoring",
    "stop_monitoring",
    "get_health_status",
    "get_metrics_summary",
    "MetricsCollector",
    "HealthChecker"
]
