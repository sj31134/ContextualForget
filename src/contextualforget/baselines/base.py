"""
Base class for baseline query engines.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BaselineQueryEngine(ABC):
    """Abstract base class for baseline query engines."""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
    
    @abstractmethod
    def initialize(self, graph_data: Dict[str, Any]) -> None:
        """Initialize the engine with graph data."""
        pass
    
    @abstractmethod
    def process_query(self, question: str, **kwargs) -> Dict[str, Any]:
        """Process a natural language query."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "name": self.name,
            "initialized": self.initialized,
            "timestamp": datetime.now().isoformat()
        }
