"""
Advanced forgetting policies for long-term memory management.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone


class ForgettingPolicy:
    """Base class for forgetting policies."""
    
    def should_forget(self, event_data: dict, context: dict) -> bool:
        """Determine if an event should be forgotten."""
        raise NotImplementedError


class TTLPolicy(ForgettingPolicy):
    """Time-to-Live based forgetting policy."""
    
    def __init__(self, ttl_days: int = 365):
        self.ttl_days = ttl_days
    
    def should_forget(self, event_data: dict, context: dict) -> bool:
        created_iso = event_data.get("created", "")
        if not created_iso:
            return True
        
        try:
            created_time = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - created_time).days
            return age_days > self.ttl_days
        except Exception:
            return True


class WeightedDecayPolicy(ForgettingPolicy):
    """Weighted decay based forgetting policy."""
    
    def __init__(self, 
                 recency_weight: float = 0.4,
                 usage_weight: float = 0.3,
                 importance_weight: float = 0.3,
                 decay_rate: float = 0.1):
        self.recency_weight = recency_weight
        self.usage_weight = usage_weight
        self.importance_weight = importance_weight
        self.decay_rate = decay_rate
    
    def should_forget(self, event_data: dict, context: dict) -> bool:
        # Calculate recency score
        created_iso = event_data.get("created", "")
        if not created_iso:
            return True
        
        try:
            created_time = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - created_time).days
            recency_score = math.exp(-self.decay_rate * age_days / 365.0)
        except Exception:
            recency_score = 0.0
        
        # Get usage count from context
        usage_count = context.get("usage_count", 0)
        usage_score = min(usage_count / 10.0, 1.0)
        
        # Get importance from event data
        importance = event_data.get("importance", 0.5)
        importance_score = importance
        
        # Calculate weighted score
        total_score = (
            self.recency_weight * recency_score +
            self.usage_weight * usage_score +
            self.importance_weight * importance_score
        )
        
        # Forget if score is below threshold
        return total_score < 0.01


class ImportanceBasedPolicy(ForgettingPolicy):
    """Importance-based forgetting policy."""
    
    def __init__(self, importance_threshold: float = 0.5):
        self.importance_threshold = importance_threshold
    
    def should_forget(self, event_data: dict, context: dict) -> bool:
        importance = event_data.get("importance", 0.5)
        return importance < self.importance_threshold


class ContradictionPolicy(ForgettingPolicy):
    """Contradiction-based forgetting policy."""
    
    def __init__(self, contradiction_threshold: int = 3):
        self.contradiction_threshold = contradiction_threshold
    
    def should_forget(self, event_data: dict, context: dict) -> bool:
        contradiction_count = event_data.get("contradiction_count", 0)
        return contradiction_count >= self.contradiction_threshold


class CompositeForgettingPolicy(ForgettingPolicy):
    """Composite policy combining multiple forgetting strategies."""
    
    def __init__(self, policies: list[ForgettingPolicy], 
                 mode: str = "any"):  # "any" or "all"
        self.policies = policies
        self.mode = mode
    
    def should_forget(self, event_data: dict, context: dict) -> bool:
        results = [policy.should_forget(event_data, context) for policy in self.policies]
        
        if self.mode == "any":
            return any(results)
        else:  # "all"
            return all(results)


class ForgettingManager:
    """Manages forgetting policies and applies them to events."""
    
    def __init__(self, policy: ForgettingPolicy):
        self.policy = policy
        self.usage_stats: dict[str, int] = {}
    
    def update_usage(self, event_id: str):
        """Update usage statistics for an event."""
        self.usage_stats[event_id] = self.usage_stats.get(event_id, 0) + 1
    
    def should_forget_event(self, event_data: dict) -> bool:
        """Check if an event should be forgotten."""
        event_id = event_data.get("topic_id", "")
        context = {
            "usage_count": self.usage_stats.get(event_id, 0)
        }
        return self.policy.should_forget(event_data, context)
    
    def filter_events(self, events: list[dict]) -> list[dict]:
        """Filter events based on forgetting policy."""
        return [event for event in events if not self.should_forget_event(event)]
    
    def get_forgetting_stats(self) -> dict:
        """Get statistics about forgetting decisions."""
        return {
            "total_events_checked": len(self.usage_stats),
            "usage_stats": self.usage_stats.copy()
        }


def create_default_forgetting_policy() -> ForgettingManager:
    """Create a default forgetting policy manager."""
    # Combine TTL, weighted decay, and importance policies
    ttl_policy = TTLPolicy(ttl_days=365)
    decay_policy = WeightedDecayPolicy()
    importance_policy = ImportanceBasedPolicy(importance_threshold=0.3)
    
    composite_policy = CompositeForgettingPolicy(
        [ttl_policy, decay_policy, importance_policy],
        mode="any"
    )
    
    return ForgettingManager(composite_policy)


def calculate_event_importance(event_data: dict) -> float:
    """Calculate importance score for an event."""
    # Base importance from event type
    event_type = event_data.get("type", "unknown")
    type_importance = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.6,
        "low": 0.4,
        "unknown": 0.5
    }.get(event_type, 0.5)
    
    # Adjust based on labels
    labels = event_data.get("labels", [])
    label_boost = 0.0
    if "safety" in labels:
        label_boost += 0.2
    if "structural" in labels:
        label_boost += 0.15
    if "critical" in labels:
        label_boost += 0.1
    
    return min(type_importance + label_boost, 1.0)
