"""
Performance optimization utilities for large-scale data processing.
"""
from __future__ import annotations
import networkx as nx
import pickle
import json
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import lru_cache
import time
import os
from pathlib import Path


class GraphOptimizer:
    """Optimizes graph operations for large datasets."""
    
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self._build_indexes()
    
    def _build_indexes(self):
        """Build indexes for faster lookups."""
        self.ifc_index = {}
        self.bcf_index = {}
        self.author_index = {}
        self.date_index = {}
        
        for node, data in self.graph.nodes(data=True):
            if node[0] == "IFC":
                self.ifc_index[node[1]] = node
            elif node[0] == "BCF":
                self.bcf_index[node[1]] = node
                
                # Index by author
                author = data.get("author", "")
                if author:
                    if author not in self.author_index:
                        self.author_index[author] = []
                    self.author_index[author].append(node)
                
                # Index by date
                created = data.get("created", "")
                if created:
                    try:
                        from datetime import datetime
                        date = datetime.fromisoformat(created.replace("Z", "+00:00")).date()
                        if date not in self.date_index:
                            self.date_index[date] = []
                        self.date_index[date].append(node)
                    except Exception:
                        pass
    
    @lru_cache(maxsize=1000)
    def get_neighbors_cached(self, node: Tuple[str, str]) -> List[Tuple[str, str]]:
        """Cached neighbor lookup."""
        return list(self.graph.neighbors(node))
    
    def batch_query(self, guids: List[str], ttl: int = 0) -> Dict[str, List[Dict]]:
        """Batch query multiple GUIDs efficiently."""
        results = {}
        
        for guid in guids:
            if guid in self.ifc_index:
                node = self.ifc_index[guid]
                neighbors = self.get_neighbors_cached(node)
                
                hits = []
                # Check predecessors (BCF nodes that point to this IFC node)
                for predecessor in self.graph.predecessors(node):
                    if predecessor[0] == "BCF":
                        edge_data = self.graph.get_edge_data(predecessor, node, {})
                        node_data = self.graph.nodes[predecessor]
                        
                        # Apply TTL filtering
                        if ttl > 0:
                            from ..core import expired
                            if expired(node_data.get("created", ""), ttl):
                                continue
                        
                        hits.append({
                            "topic_id": predecessor[1],
                            "created": node_data.get("created"),
                            "title": node_data.get("title", ""),
                            "edge": {
                                "type": edge_data.get("type", "refersTo"),
                                "confidence": edge_data.get("confidence", 1.0)
                            }
                        })
                
                results[guid] = hits
        
        return results


class ParallelProcessor:
    """Parallel processing utilities."""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
    
    def process_files_parallel(self, 
                              file_paths: List[str], 
                              process_func,
                              chunk_size: int = 100) -> List[Any]:
        """Process multiple files in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks in chunks
            for i in range(0, len(file_paths), chunk_size):
                chunk = file_paths[i:i + chunk_size]
                futures = [executor.submit(process_func, path) for path in chunk]
                
                for future in futures:
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        print(f"Error processing file: {e}")
                        results.append(None)
        
        return results
    
    def process_data_parallel(self, 
                             data_items: List[Any], 
                             process_func,
                             chunk_size: int = 100) -> List[Any]:
        """Process data items in parallel."""
        results = []
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks in chunks
            for i in range(0, len(data_items), chunk_size):
                chunk = data_items[i:i + chunk_size]
                futures = [executor.submit(process_func, item) for item in chunk]
                
                for future in futures:
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        print(f"Error processing item: {e}")
                        results.append(None)
        
        return results


class MemoryOptimizer:
    """Memory optimization utilities."""
    
    @staticmethod
    def compress_graph(graph: nx.DiGraph) -> nx.DiGraph:
        """Compress graph by removing redundant data."""
        compressed = nx.DiGraph()
        
        for node, data in graph.nodes(data=True):
            # Keep only essential data
            compressed_data = {
                "type": data.get("type", ""),
                "created": data.get("created", ""),
                "title": data.get("title", ""),
                "author": data.get("author", "")
            }
            compressed.add_node(node, **compressed_data)
        
        for u, v, data in graph.edges(data=True):
            # Keep only essential edge data
            compressed_data = {
                "type": data.get("type", "refersTo"),
                "confidence": data.get("confidence", 1.0)
            }
            compressed.add_edge(u, v, **compressed_data)
        
        return compressed
    
    @staticmethod
    def save_graph_compressed(graph: nx.DiGraph, filepath: str):
        """Save graph in compressed format."""
        compressed = MemoryOptimizer.compress_graph(graph)
        
        with open(filepath, 'wb') as f:
            pickle.dump(compressed, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    @staticmethod
    def load_graph_compressed(filepath: str) -> nx.DiGraph:
        """Load compressed graph."""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


class CacheManager:
    """Cache management for frequently accessed data."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        return self.cache_dir / f"{key}.pkl"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached data."""
        cache_path = self.get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                return None
        return None
    
    def set(self, key: str, data: Any):
        """Cache data."""
        cache_path = self.get_cache_path(key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"Error caching data: {e}")
    
    def clear(self):
        """Clear all cache."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()


class PerformanceProfiler:
    """Performance profiling utilities."""
    
    def __init__(self):
        self.timings = {}
        self.memory_usage = {}
    
    def time_function(self, func_name: str):
        """Decorator to time function execution."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                if func_name not in self.timings:
                    self.timings[func_name] = []
                self.timings[func_name].append(end_time - start_time)
                
                return result
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        
        for func_name, timings in self.timings.items():
            if timings:
                stats[func_name] = {
                    "count": len(timings),
                    "total_time": sum(timings),
                    "avg_time": sum(timings) / len(timings),
                    "min_time": min(timings),
                    "max_time": max(timings)
                }
        
        return stats
    
    def print_report(self):
        """Print performance report."""
        stats = self.get_stats()
        
        print("Performance Report:")
        print("=" * 50)
        
        for func_name, stat in stats.items():
            print(f"{func_name}:")
            print(f"  Count: {stat['count']}")
            print(f"  Total: {stat['total_time']:.4f}s")
            print(f"  Average: {stat['avg_time']:.4f}s")
            print(f"  Min: {stat['min_time']:.4f}s")
            print(f"  Max: {stat['max_time']:.4f}s")
            print()


class LargeDataProcessor:
    """Process large datasets efficiently."""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        self.processor = ParallelProcessor()
        self.cache = CacheManager()
    
    def process_large_jsonl(self, 
                           filepath: str, 
                           process_func,
                           cache_key: Optional[str] = None) -> List[Any]:
        """Process large JSONL files in chunks."""
        
        # Check cache first
        if cache_key:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        results = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            chunk = []
            for line in f:
                chunk.append(json.loads(line.strip()))
                
                if len(chunk) >= self.chunk_size:
                    # Process chunk
                    chunk_results = self.processor.process_data_parallel(
                        chunk, process_func
                    )
                    results.extend(chunk_results)
                    chunk = []
            
            # Process remaining items
            if chunk:
                chunk_results = self.processor.process_data_parallel(
                    chunk, process_func
                )
                results.extend(chunk_results)
        
        # Cache results
        if cache_key:
            self.cache.set(cache_key, results)
        
        return results
    
    def build_graph_incremental(self, 
                               ifc_data: List[Dict], 
                               bcf_data: List[Dict],
                               links_data: List[Dict]) -> nx.DiGraph:
        """Build graph incrementally to save memory."""
        graph = nx.DiGraph()
        
        # Add IFC nodes in batches
        for i in range(0, len(ifc_data), self.chunk_size):
            batch = ifc_data[i:i + self.chunk_size]
            for item in batch:
                graph.add_node(("IFC", item["guid"]), **item)
        
        # Add BCF nodes in batches
        for i in range(0, len(bcf_data), self.chunk_size):
            batch = bcf_data[i:i + self.chunk_size]
            for item in batch:
                graph.add_node(("BCF", item["topic_id"]), **item)
        
        # Add edges in batches
        for i in range(0, len(links_data), self.chunk_size):
            batch = links_data[i:i + self.chunk_size]
            for item in batch:
                for guid in item["guid_matches"]:
                    graph.add_edge(
                        ("BCF", item["topic_id"]), 
                        ("IFC", guid),
                        type="refersTo", 
                        confidence=item["confidence"]
                    )
        
        return graph


def optimize_for_production(graph_path: str, output_path: str):
    """Optimize graph for production use."""
    print("Loading graph...")
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
    
    print("Compressing graph...")
    compressed_graph = MemoryOptimizer.compress_graph(graph)
    
    print("Building indexes...")
    optimizer = GraphOptimizer(compressed_graph)
    
    print("Saving optimized graph...")
    MemoryOptimizer.save_graph_compressed(compressed_graph, output_path)
    
    print(f"Optimized graph saved to {output_path}")
    print(f"Original size: {os.path.getsize(graph_path) / 1024 / 1024:.2f} MB")
    print(f"Optimized size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    
    return optimizer
