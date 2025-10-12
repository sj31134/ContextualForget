from __future__ import annotations

from datetime import datetime, timezone


def expired(created_iso: str, ttl: int) -> bool:
    if ttl <= 0:
        return False
    try:
        t = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
    except Exception:
        return True  # Invalid dates should be considered expired
    return (datetime.now(timezone.utc) - t).days > ttl

def score(recency_days: float, usage: int, confidence: float, contradiction: int) -> float:
    return 0.6*max(0, 1.0 - recency_days/365.0) + 0.2*(usage/10.0) + 0.2*confidence - 0.1*contradiction
