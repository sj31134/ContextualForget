"""
ContextualForget Engine with Contextual Forgetting
RQ2: 맥락적 망각 메커니즘을 통합한 검색 엔진
"""

from __future__ import annotations

import pickle
from datetime import datetime, timezone
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx

from ..core.contextual_forgetting import ContextualForgettingManager, AdaptiveForgettingPolicy
from ..core.forgetting import expired
from .advanced_query import AdvancedQueryEngine


class ContextualForgetEngine(AdvancedQueryEngine):
    """맥락적 망각을 통합한 ContextualForget 엔진"""
    
    def __init__(self, 
                 graph: nx.DiGraph,
                 forgetting_manager: Optional[ContextualForgettingManager] = None,
                 enable_contextual_forgetting: bool = True):
        """
        Args:
            graph: NetworkX 그래프
            forgetting_manager: 맥락적 망각 관리자
            enable_contextual_forgetting: 맥락적 망각 활성화 여부
        """
        super().__init__(graph)
        
        self.enable_contextual_forgetting = enable_contextual_forgetting
        
        if forgetting_manager is None:
            from ..core.contextual_forgetting import create_contextual_forgetting_manager
            self.forgetting_manager = create_contextual_forgetting_manager()
        else:
            self.forgetting_manager = forgetting_manager
            
        self.adaptive_policy = AdaptiveForgettingPolicy(self.forgetting_manager)
        
        # 성능 추적
        self.query_history = []
        self.performance_metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'average_response_time': 0.0,
            'average_relevance_score': 0.0
        }
    
    def find_by_keywords_with_forgetting(self, 
                                       keywords: List[str], 
                                       ttl: int = 0,
                                       apply_forgetting: bool = True) -> List[Dict[str, Any]]:
        """키워드 검색 with 맥락적 망각"""
        start_time = time.perf_counter()
        
        # 기본 키워드 검색 수행
        results = self.find_by_keywords(keywords, ttl)
        
        if not self.enable_contextual_forgetting or not apply_forgetting:
            return results
        
        # 맥락 정보 업데이트 (문서에 doc_id 추가)
        docs_with_id = []
        for doc in results:
            doc_copy = doc.copy()
            if 'doc_id' not in doc_copy:
                doc_copy['doc_id'] = doc_copy.get('topic_id', doc_copy.get('guid', ''))
            docs_with_id.append(doc_copy)
        
        self.forgetting_manager.update_context(
            query=" ".join(keywords),
            retrieved_docs=docs_with_id
        )
        
        # 맥락적 망각 적용
        filtered_results = self.forgetting_manager.apply_contextual_forgetting(results)
        
        # 성능 메트릭 업데이트
        self._update_performance_metrics(start_time, len(filtered_results), len(results))
        
        return filtered_results
    
    def find_by_guid_with_forgetting(self, 
                                   guid: str, 
                                   ttl: int = 0,
                                   apply_forgetting: bool = True) -> List[Dict[str, Any]]:
        """GUID 검색 with 맥락적 망각"""
        start_time = time.perf_counter()
        
        # BCF 노드에서 직접 GUID 검색
        results = []
        bcf_node = ("BCF", guid)
        
        if bcf_node in self.graph:
            node_data = self.graph.nodes[bcf_node]
            result = {
                "topic_id": guid,
                "title": node_data.get("title", ""),
                "author": node_data.get("author", ""),
                "description": node_data.get("description", ""),
                "created": node_data.get("created", ""),
                "source_file": node_data.get("source_file", ""),
                "data_type": node_data.get("data_type", "real_bcf")
            }
            results.append(result)
        
        # IFC 노드에서도 검색 (기존 로직)
        ifc_results = self.find_by_guid(guid, ttl)
        results.extend(ifc_results)
        
        if not self.enable_contextual_forgetting or not apply_forgetting:
            return results
        
        # 맥락 정보 업데이트 (문서에 doc_id 추가)
        docs_with_id = []
        for doc in results:
            doc_copy = doc.copy()
            if 'doc_id' not in doc_copy:
                doc_copy['doc_id'] = doc_copy.get('topic_id', doc_copy.get('guid', ''))
            docs_with_id.append(doc_copy)
        
        self.forgetting_manager.update_context(
            query=f"GUID: {guid}",
            retrieved_docs=docs_with_id
        )
        
        # 맥락적 망각 적용
        filtered_results = self.forgetting_manager.apply_contextual_forgetting(results)
        
        # 성능 메트릭 업데이트
        self._update_performance_metrics(start_time, len(filtered_results), len(results))
        
        return filtered_results
    
    def find_by_author_with_forgetting(self, 
                                     author: str, 
                                     ttl: int = 0,
                                     apply_forgetting: bool = True) -> List[Dict[str, Any]]:
        """작성자 검색 with 맥락적 망각"""
        start_time = time.perf_counter()
        
        # 기본 작성자 검색 수행
        results = self.find_by_author(author, ttl)
        
        if not self.enable_contextual_forgetting or not apply_forgetting:
            return results
        
        # 맥락 정보 업데이트 (문서에 doc_id 추가)
        docs_with_id = []
        for doc in results:
            doc_copy = doc.copy()
            if 'doc_id' not in doc_copy:
                doc_copy['doc_id'] = doc_copy.get('topic_id', doc_copy.get('guid', ''))
            docs_with_id.append(doc_copy)
        
        self.forgetting_manager.update_context(
            query=f"Author: {author}",
            retrieved_docs=docs_with_id
        )
        
        # 맥락적 망각 적용
        filtered_results = self.forgetting_manager.apply_contextual_forgetting(results)
        
        # 성능 메트릭 업데이트
        self._update_performance_metrics(start_time, len(filtered_results), len(results))
        
        return filtered_results
    
    def _detect_query_type(self, query: str) -> str:
        """쿼리 타입 자동 감지"""
        import re
        
        # GUID 쿼리 감지
        guid_pattern = r'([A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12})'
        if re.search(guid_pattern, query):
            return "guid"
        
        # 시간 관련 쿼리 감지
        temporal_keywords = ['최근', '이전', '생성', '날짜', '일', '주', '월', '년', 'recent', 'ago', 'created', 'date']
        if any(keyword in query.lower() for keyword in temporal_keywords):
            return "temporal"
        
        # 작성자 관련 쿼리 감지
        author_keywords = ['작성', 'author', 'engineer', 'architect']
        if any(keyword in query.lower() for keyword in author_keywords):
            return "author"
        
        # 복잡한 쿼리 감지 (여러 조건이 포함된 경우)
        complex_keywords = ['그리고', '또는', '하지만', 'and', 'or', 'but', 'with', 'without']
        if any(keyword in query.lower() for keyword in complex_keywords):
            return "complex"
        
        # 기본값: 일반 키워드 쿼리
        return "general"
    
    def contextual_query(self, 
                        query: str, 
                        query_type: str = "auto",
                        apply_forgetting: bool = True) -> Dict[str, Any]:
        """맥락적 쿼리 처리"""
        start_time = time.perf_counter()
        
        # 쿼리 타입 자동 감지
        if query_type == "auto":
            query_type = self._detect_query_type(query)
        
        # 쿼리 타입에 따른 적응적 가중치 적용
        if self.enable_contextual_forgetting:
            adaptive_weights = self.adaptive_policy.get_adaptive_weights(query_type)
            self.forgetting_manager.usage_weight = adaptive_weights['usage_weight']
            self.forgetting_manager.recency_weight = adaptive_weights['recency_weight']
            self.forgetting_manager.relevance_weight = adaptive_weights['relevance_weight']
        
        # 쿼리 타입에 따른 검색 수행
        if query_type == "guid":
            # GUID 패턴 추출
            import re
            guid_pattern = r'([A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12})'
            guid_match = re.search(guid_pattern, query)
            if guid_match:
                results = self.find_by_guid_with_forgetting(guid_match.group(), apply_forgetting=apply_forgetting)
            else:
                results = []
        elif query_type == "author":
            # 작성자 추출
            author_keywords = [word for word in query.split() if word.startswith(('engineer_', 'architect_', 'user_'))]
            if author_keywords:
                results = self.find_by_author_with_forgetting(author_keywords[0], apply_forgetting=apply_forgetting)
            else:
                results = []
        else:
            # 일반 키워드 검색
            keywords = query.split()
            results = self.find_by_keywords_with_forgetting(keywords, apply_forgetting=apply_forgetting)
        
        # 응답 시간 계산
        response_time = max(time.perf_counter() - start_time, 0.0001)
        
        # 신뢰도 계산
        contextual_scores = [doc.get('contextual_score', 0.0) for doc in results]
        if contextual_scores and len(results) > 0:
            avg_contextual = sum(contextual_scores) / len(contextual_scores)
            result_ratio = min(1.0, len(results) / 10.0)
            confidence = avg_contextual * 0.7 + result_ratio * 0.3
        else:
            confidence = 0.0

        # entities 리스트 추출
        entities = []
        for doc in results:
            entity_id = doc.get('doc_id') or doc.get('topic_id') or doc.get('guid', '')
            if entity_id:
                entities.append(entity_id)
        
        # 답변 생성 (간단한 요약)
        if results:
            answer = f"{len(results)}개의 관련 항목을 찾았습니다."
        else:
            answer = "관련 정보를 찾을 수 없습니다."
        
        # 결과 정리 (표준 형식)
        response = {
            'answer': answer,
            'confidence': confidence,
            'result_count': len(results),
            'entities': entities,
            'source': 'ContextualForget',
            'details': {
                'query': query,
                'query_type': query_type,
                'results': results,
                'response_time': response_time,
                'forgetting_applied': apply_forgetting and self.enable_contextual_forgetting,
                'contextual_scores': contextual_scores
            }
        }
        
        # 성능 메트릭 업데이트
        self._update_performance_metrics(start_time, len(results), len(results))
        
        return response
    
    def _update_performance_metrics(self, start_time: datetime, filtered_count: int, original_count: int):
        """성능 메트릭 업데이트"""
        response_time = max(time.perf_counter() - start_time, 0.0001)
        
        self.performance_metrics['total_queries'] += 1
        if filtered_count > 0:
            self.performance_metrics['successful_queries'] += 1
        
        # 평균 응답 시간 업데이트
        total_queries = self.performance_metrics['total_queries']
        current_avg = self.performance_metrics['average_response_time']
        self.performance_metrics['average_response_time'] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )
        
        # 평균 관련성 점수 업데이트
        if filtered_count > 0:
            relevance_score = filtered_count / max(original_count, 1)
            current_avg_relevance = self.performance_metrics['average_relevance_score']
            self.performance_metrics['average_relevance_score'] = (
                (current_avg_relevance * (total_queries - 1) + relevance_score) / total_queries
            )
    
    def get_forgetting_statistics(self) -> Dict[str, Any]:
        """망각 통계 반환"""
        if not self.enable_contextual_forgetting:
            return {'forgetting_enabled': False}
        
        stats = self.forgetting_manager.get_forgetting_statistics()
        stats.update({
            'forgetting_enabled': True,
            'performance_metrics': self.performance_metrics,
            'context_window_size': self.forgetting_manager.context_window_size,
            'forgetting_threshold': self.forgetting_manager.forgetting_threshold
        })
        
        return stats
    
    def adapt_forgetting_policy(self, performance_feedback: float):
        """망각 정책 적응"""
        if self.enable_contextual_forgetting:
            self.adaptive_policy.adapt_threshold(performance_feedback)
    
    def save_forgetting_state(self, filepath: str):
        """망각 상태 저장"""
        if self.enable_contextual_forgetting:
            self.forgetting_manager.save_state(filepath)
    
    def load_forgetting_state(self, filepath: str):
        """망각 상태 로드"""
        if self.enable_contextual_forgetting:
            self.forgetting_manager.load_state(filepath)
    
    def reset_forgetting_state(self):
        """망각 상태 초기화"""
        if self.enable_contextual_forgetting:
            from ..core.contextual_forgetting import create_contextual_forgetting_manager
            self.forgetting_manager = create_contextual_forgetting_manager()
            self.adaptive_policy = AdaptiveForgettingPolicy(self.forgetting_manager)
            self.performance_metrics = {
                'total_queries': 0,
                'successful_queries': 0,
                'average_response_time': 0.0,
                'average_relevance_score': 0.0
            }


def create_contextual_forget_engine(graph: nx.DiGraph, 
                                  config: Optional[Dict[str, Any]] = None) -> ContextualForgetEngine:
    """ContextualForget 엔진 생성"""
    if config is None:
        config = {}
    
    from ..core.contextual_forgetting import create_contextual_forgetting_manager
    
    forgetting_manager = create_contextual_forgetting_manager(
        config.get('forgetting_config', {})
    )
    
    return ContextualForgetEngine(
        graph=graph,
        forgetting_manager=forgetting_manager,
        enable_contextual_forgetting=config.get('enable_forgetting', True)
    )
