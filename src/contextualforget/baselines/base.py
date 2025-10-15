"""
Base class for baseline query engines.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaselineQueryEngine(ABC):
    """Abstract base class for baseline query engines."""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
    
    @abstractmethod
    def initialize(self, graph_data: dict[str, Any]) -> None:
        """Initialize the engine with graph data."""
        pass
    
    @abstractmethod
    def process_query(self, question: str, **kwargs) -> dict[str, Any]:
        """
        Process a natural language query.
        
        Returns:
            {
                'answer': str,
                'confidence': float (0.0-1.0),
                'result_count': int,
                'source': str,
                'details': dict
            }
        """
        pass
    
    def get_stats(self) -> dict[str, Any]:
        """Get engine statistics."""
        return {
            "name": self.name,
            "initialized": self.initialized,
            "timestamp": datetime.now().isoformat()
        }
