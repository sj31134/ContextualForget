"""
Optimization module for ContextualForget

이 모듈은 그래프 성능 최적화, 인덱싱, 캐싱을 담당합니다.
"""

import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np
from dataclasses import dataclass

from ..core.logging import get_logger

logger = get_logger("contextualforget.optimization")


@dataclass
class OptimizationConfig:
    """최적화 설정"""
    enable_indexing: bool = True
    enable_caching: bool = True
    enable_compression: bool = True
    cache_size: int = 1000
    index_update_interval: int = 300  # 5분
    compression_level: int = 6


class GraphIndexer:
    """그래프 인덱싱 클래스"""
    
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.guid_index = {}
        self.type_index = {}
        self.date_index = {}
        self.author_index = {}
        self.keyword_index = {}
        self._build_indexes()
    
    def _build_indexes(self):
        """모든 인덱스 구축"""
        logger.info("그래프 인덱스 구축 시작...")
        
        for node, data in self.graph.nodes(data=True):
            node_id = node
            
            # GUID 인덱스
            if data.get('type') == 'ifc' and 'guid' in data:
                self.guid_index[data['guid']] = node_id
            
            # 타입 인덱스
            node_type = data.get('type', 'unknown')
            if node_type not in self.type_index:
                self.type_index[node_type] = []
            self.type_index[node_type].append(node_id)
            
            # 날짜 인덱스
            created_at = data.get('created_at')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        date = created_at
                    
                    date_key = date.date()
                    if date_key not in self.date_index:
                        self.date_index[date_key] = []
                    self.date_index[date_key].append(node_id)
                except Exception as e:
                    logger.warning(f"날짜 인덱싱 오류: {created_at} - {e}")
            
            # 작성자 인덱스
            author = data.get('author')
            if author:
                if author not in self.author_index:
                    self.author_index[author] = []
                self.author_index[author].append(node_id)
            
            # 키워드 인덱스
            title = data.get('title', '')
            description = data.get('description', '')
            text = f"{title} {description}".lower()
            
            for word in text.split():
                if len(word) > 2:  # 2글자 이상만 인덱싱
                    if word not in self.keyword_index:
                        self.keyword_index[word] = []
                    self.keyword_index[word].append(node_id)
        
        logger.info(f"인덱스 구축 완료: GUID({len(self.guid_index)}), 타입({len(self.type_index)}), "
                   f"날짜({len(self.date_index)}), 작성자({len(self.author_index)}), 키워드({len(self.keyword_index)})")
    
    def find_by_guid(self, guid: str) -> Optional[Tuple]:
        """GUID로 노드 찾기"""
        return self.guid_index.get(guid)
    
    def find_by_type(self, node_type: str) -> List[Tuple]:
        """타입으로 노드들 찾기"""
        return self.type_index.get(node_type, [])
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Tuple]:
        """날짜 범위로 노드들 찾기"""
        result = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            if current_date in self.date_index:
                result.extend(self.date_index[current_date])
            current_date += timedelta(days=1)
        
        return result
    
    def find_by_author(self, author: str) -> List[Tuple]:
        """작성자로 노드들 찾기"""
        return self.author_index.get(author, [])
    
    def find_by_keywords(self, keywords: List[str]) -> List[Tuple]:
        """키워드로 노드들 찾기"""
        if not keywords:
            return []
        
        # 모든 키워드가 포함된 노드들 찾기
        result_sets = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            matching_nodes = set()
            
            for word, nodes in self.keyword_index.items():
                if keyword_lower in word:
                    matching_nodes.update(nodes)
            
            result_sets.append(matching_nodes)
        
        # 교집합 계산
        if result_sets:
            result = result_sets[0]
            for s in result_sets[1:]:
                result = result.intersection(s)
            return list(result)
        
        return []


class GraphCache:
    """그래프 캐시 클래스"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.access_times = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 가져오기"""
        if key in self.cache:
            self.access_times[key] = time.time()
            self.hit_count += 1
            return self.cache[key]
        
        self.miss_count += 1
        return None
    
    def set(self, key: str, value: Any):
        """캐시에 데이터 저장"""
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def _evict_oldest(self):
        """가장 오래된 항목 제거"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
    
    def clear(self):
        """캐시 초기화"""
        self.cache.clear()
        self.access_times.clear()
        self.hit_count = 0
        self.miss_count = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate
        }


class GraphCompressor:
    """그래프 압축 클래스"""
    
    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level
    
    def compress_graph(self, graph: nx.DiGraph) -> nx.DiGraph:
        """그래프 압축"""
        logger.info("그래프 압축 시작...")
        
        compressed_graph = nx.DiGraph()
        
        # 노드 압축
        for node, data in self.graph.nodes(data=True):
            compressed_data = self._compress_node_data(data)
            compressed_graph.add_node(node, **compressed_data)
        
        # 엣지 압축
        for edge in self.graph.edges(data=True):
            source, target, data = edge
            compressed_data = self._compress_edge_data(data)
            compressed_graph.add_edge(source, target, **compressed_data)
        
        logger.info(f"그래프 압축 완료: {graph.number_of_nodes()} → {compressed_graph.number_of_nodes()} 노드")
        return compressed_graph
    
    def _compress_node_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """노드 데이터 압축"""
        compressed = {}
        
        # 필수 필드만 유지
        essential_fields = ['type', 'guid', 'name', 'title', 'created_at']
        
        for field in essential_fields:
            if field in data:
                compressed[field] = data[field]
        
        # 텍스트 필드 압축
        if 'description' in data and data['description']:
            description = data['description']
            if len(description) > 200:
                compressed['description'] = description[:200] + "..."
            else:
                compressed['description'] = description
        
        return compressed
    
    def _compress_edge_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """엣지 데이터 압축"""
        compressed = {}
        
        # 필수 필드만 유지
        essential_fields = ['type', 'confidence']
        
        for field in essential_fields:
            if field in data:
                compressed[field] = data[field]
        
        return compressed


class GraphOptimizer:
    """그래프 최적화 메인 클래스"""
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self.indexer: Optional[GraphIndexer] = None
        self.cache = GraphCache(self.config.cache_size)
        self.compressor = GraphCompressor(self.config.compression_level)
        self.optimization_stats = {
            "index_build_time": 0,
            "cache_hit_rate": 0,
            "compression_ratio": 0,
            "last_optimization": None
        }
    
    def optimize_graph(self, graph: nx.DiGraph) -> nx.DiGraph:
        """그래프 최적화 수행"""
        logger.info("그래프 최적화 시작...")
        start_time = time.time()
        
        optimized_graph = graph.copy()
        
        # 인덱싱
        if self.config.enable_indexing:
            self._build_indexes(optimized_graph)
        
        # 압축
        if self.config.enable_compression:
            optimized_graph = self.compressor.compress_graph(optimized_graph)
        
        # 통계 업데이트
        optimization_time = time.time() - start_time
        self.optimization_stats.update({
            "index_build_time": optimization_time,
            "last_optimization": datetime.now().isoformat()
        })
        
        logger.info(f"그래프 최적화 완료 (소요시간: {optimization_time:.2f}초)")
        return optimized_graph
    
    def _build_indexes(self, graph: nx.DiGraph):
        """인덱스 구축"""
        start_time = time.time()
        self.indexer = GraphIndexer(graph)
        build_time = time.time() - start_time
        
        self.optimization_stats["index_build_time"] = build_time
        logger.info(f"인덱스 구축 완료 (소요시간: {build_time:.2f}초)")
    
    def query_with_optimization(self, query_func, query_key: str, *args, **kwargs):
        """최적화된 쿼리 실행"""
        # 캐시 확인
        if self.config.enable_caching:
            cached_result = self.cache.get(query_key)
            if cached_result is not None:
                return cached_result
        
        # 쿼리 실행
        result = query_func(*args, **kwargs)
        
        # 결과 캐싱
        if self.config.enable_caching:
            self.cache.set(query_key, result)
        
        return result
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """최적화 통계 반환"""
        cache_stats = self.cache.get_stats()
        
        return {
            **self.optimization_stats,
            "cache_stats": cache_stats,
            "indexer_stats": {
                "guid_index_size": len(self.indexer.guid_index) if self.indexer else 0,
                "type_index_size": len(self.indexer.type_index) if self.indexer else 0,
                "date_index_size": len(self.indexer.date_index) if self.indexer else 0,
                "author_index_size": len(self.indexer.author_index) if self.indexer else 0,
                "keyword_index_size": len(self.indexer.keyword_index) if self.indexer else 0
            }
        }
    
    def save_optimized_graph(self, graph: nx.DiGraph, filepath: str):
        """최적화된 그래프 저장"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with filepath.open('wb') as f:
            pickle.dump(graph, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        logger.info(f"최적화된 그래프 저장 완료: {filepath}")
    
    def load_optimized_graph(self, filepath: str) -> nx.DiGraph:
        """최적화된 그래프 로드"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"그래프 파일을 찾을 수 없습니다: {filepath}")
        
        with filepath.open('rb') as f:
            graph = pickle.load(f)
        
        # 인덱스 재구축
        if self.config.enable_indexing:
            self._build_indexes(graph)
        
        logger.info(f"최적화된 그래프 로드 완료: {filepath}")
        return graph


def optimize_graph_for_production(graph_path: str, output_path: str, config: Optional[OptimizationConfig] = None):
    """프로덕션용 그래프 최적화"""
    logger.info(f"프로덕션용 그래프 최적화 시작: {graph_path}")
    
    # 그래프 로드
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
    
    # 최적화 수행
    optimizer = GraphOptimizer(config)
    optimized_graph = optimizer.optimize_graph(graph)
    
    # 최적화된 그래프 저장
    optimizer.save_optimized_graph(optimized_graph, output_path)
    
    # 통계 출력
    stats = optimizer.get_optimization_stats()
    logger.info(f"최적화 통계: {stats}")
    
    return optimizer


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ContextualForget Graph Optimizer")
    parser.add_argument("--input", required=True, help="Input graph file")
    parser.add_argument("--output", required=True, help="Output graph file")
    parser.add_argument("--config", help="Configuration file (JSON)")
    
    args = parser.parse_args()
    
    # 설정 로드
    config = None
    if args.config:
        import json
        with open(args.config) as f:
            config_data = json.load(f)
            config = OptimizationConfig(**config_data)
    
    # 최적화 수행
    optimizer = optimize_graph_for_production(args.input, args.output, config)
    
    print("✅ 그래프 최적화 완료!")
    print(f"📊 최적화 통계: {optimizer.get_optimization_stats()}")
