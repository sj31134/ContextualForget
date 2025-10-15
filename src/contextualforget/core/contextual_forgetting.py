"""
Contextual Forgetting Mechanism for RAG Systems
RQ2: 맥락적 망각 메커니즘 구현
"""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict, deque

from .forgetting import expired, score


class ContextualForgettingManager:
    """맥락적 망각을 관리하는 클래스"""
    
    def __init__(self, 
                 context_window_size: int = 10,
                 forgetting_threshold: float = 0.3,
                 context_decay_rate: float = 0.1,
                 usage_weight: float = 0.3,
                 recency_weight: float = 0.4,
                 relevance_weight: float = 0.3):
        """
        Args:
            context_window_size: 맥락 윈도우 크기
            forgetting_threshold: 망각 임계값
            context_decay_rate: 맥락 감쇠율
            usage_weight: 사용 빈도 가중치
            recency_weight: 최근성 가중치
            relevance_weight: 관련성 가중치
        """
        self.context_window_size = context_window_size
        self.forgetting_threshold = forgetting_threshold
        self.context_decay_rate = context_decay_rate
        self.usage_weight = usage_weight
        self.recency_weight = recency_weight
        self.relevance_weight = relevance_weight
        
        # 맥락 히스토리
        self.context_history: deque = deque(maxlen=context_window_size)
        
        # 문서별 사용 통계
        self.document_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'access_count': 0,
            'last_access': None,
            'context_relevance': 0.0,
            'forgetting_score': 1.0
        })
        
        # 맥락별 관련성 매트릭스
        self.context_relevance_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
        
    def update_context(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> None:
        """맥락 정보 업데이트"""
        current_context = {
            'timestamp': datetime.now(timezone.utc),
            'query': query,
            'retrieved_docs': [doc.get('doc_id', doc.get('guid', '')) for doc in retrieved_docs],
            'context_vector': self._compute_context_vector(query, retrieved_docs)
        }
        
        self.context_history.append(current_context)
        
        # 문서 통계 업데이트
        for doc in retrieved_docs:
            doc_id = doc.get('doc_id', doc.get('guid', ''))
            if doc_id:
                self.document_stats[doc_id]['access_count'] += 1
                self.document_stats[doc_id]['last_access'] = current_context['timestamp']
                
                # 맥락 관련성 업데이트
                relevance = self._compute_document_relevance(doc, current_context)
                self.document_stats[doc_id]['context_relevance'] = relevance
                
    def _compute_context_vector(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> np.ndarray:
        """맥락 벡터 계산"""
        # 간단한 TF-IDF 스타일 맥락 벡터
        context_words = set()
        
        # 쿼리에서 키워드 추출
        query_words = set(query.lower().split())
        context_words.update(query_words)
        
        # 검색된 문서에서 키워드 추출
        for doc in retrieved_docs:
            title = doc.get('title', '').lower()
            description = doc.get('description', '').lower()
            doc_words = set(title.split() + description.split())
            context_words.update(doc_words)
        
        # 벡터화 (실제로는 더 정교한 임베딩 사용 가능)
        context_vector = np.zeros(len(context_words))
        word_to_idx = {word: idx for idx, word in enumerate(context_words)}
        
        for word in query_words:
            if word in word_to_idx:
                context_vector[word_to_idx[word]] += 2.0  # 쿼리 단어에 더 높은 가중치
                
        for doc in retrieved_docs:
            title = doc.get('title', '').lower()
            description = doc.get('description', '').lower()
            doc_words = title.split() + description.split()
            for word in doc_words:
                if word in word_to_idx:
                    context_vector[word_to_idx[word]] += 1.0
                    
        return context_vector
    
    def _compute_document_relevance(self, doc: Dict[str, Any], context: Dict[str, Any]) -> float:
        """문서의 맥락 관련성 계산"""
        doc_content = f"{doc.get('title', '')} {doc.get('description', '')}".lower()
        query = context['query'].lower()
        
        # 간단한 키워드 매칭 기반 관련성
        query_words = set(query.split())
        doc_words = set(doc_content.split())
        
        if not query_words:
            return 0.0
            
        overlap = len(query_words.intersection(doc_words))
        relevance = overlap / len(query_words)
        
        return min(relevance, 1.0)
    
    def compute_forgetting_scores(self) -> Dict[str, float]:
        """망각 점수 계산"""
        current_time = datetime.now(timezone.utc)
        forgetting_scores = {}
        
        for doc_id, stats in self.document_stats.items():
            # 최근성 점수
            if stats['last_access']:
                days_since_access = (current_time - stats['last_access']).days
                recency_score = max(0, 1.0 - (days_since_access / 365.0))
            else:
                recency_score = 0.0
            
            # 사용 빈도 점수
            usage_score = min(1.0, stats['access_count'] / 10.0)
            
            # 맥락 관련성 점수
            relevance_score = stats['context_relevance']
            
            # 망각 점수 계산 (높을수록 망각되지 않음)
            forgetting_score = (
                self.recency_weight * recency_score +
                self.usage_weight * usage_score +
                self.relevance_weight * relevance_score
            )
            
            forgetting_scores[doc_id] = forgetting_score
            stats['forgetting_score'] = forgetting_score
            
        return forgetting_scores
    
    def should_forget(self, doc_id: str) -> bool:
        """문서가 망각되어야 하는지 판단"""
        if doc_id not in self.document_stats:
            return False
            
        forgetting_score = self.document_stats[doc_id]['forgetting_score']
        return forgetting_score < self.forgetting_threshold
    
    def get_contextual_retrieval_weights(self, candidate_docs: List[Dict[str, Any]]) -> Dict[str, float]:
        """맥락적 검색 가중치 계산"""
        forgetting_scores = self.compute_forgetting_scores()
        weights = {}
        
        for doc in candidate_docs:
            doc_id = doc.get('doc_id', doc.get('guid', ''))
            if doc_id:
                # 기본 점수
                base_score = doc.get('score', 0.5)
                
                # 망각 점수 적용
                forgetting_score = forgetting_scores.get(doc_id, 0.5)
                
                # 맥락 관련성 적용
                context_relevance = self.document_stats[doc_id]['context_relevance']
                
                # 최종 가중치 계산
                final_weight = (
                    base_score * 0.4 +
                    forgetting_score * 0.4 +
                    context_relevance * 0.2
                )
                
                weights[doc_id] = final_weight
                
        return weights
    
    def apply_contextual_forgetting(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """맥락적 망각 적용"""
        # 망각 점수 계산
        forgetting_scores = self.compute_forgetting_scores()
        
        # 망각되지 않은 문서만 필터링
        filtered_docs = []
        for doc in retrieved_docs:
            doc_id = doc.get('doc_id', doc.get('topic_id', doc.get('guid', '')))
            if doc_id and not self.should_forget(doc_id):
                # 망각 점수를 점수에 반영
                doc_copy = doc.copy()
                doc_copy['contextual_score'] = forgetting_scores.get(doc_id, 0.5)
                filtered_docs.append(doc_copy)
        
        # 망각 점수로 정렬
        filtered_docs.sort(key=lambda x: x.get('contextual_score', 0), reverse=True)
        
        return filtered_docs
    
    def get_forgetting_statistics(self) -> Dict[str, Any]:
        """망각 통계 반환"""
        forgetting_scores = self.compute_forgetting_scores()
        
        total_docs = len(self.document_stats)
        forgotten_docs = sum(1 for score in forgetting_scores.values() if score < self.forgetting_threshold)
        
        return {
            'total_documents': total_docs,
            'forgotten_documents': forgotten_docs,
            'retention_rate': (total_docs - forgotten_docs) / total_docs if total_docs > 0 else 0,
            'average_forgetting_score': np.mean(list(forgetting_scores.values())) if forgetting_scores else 0,
            'context_history_size': len(self.context_history)
        }
    
    def save_state(self, filepath: str) -> None:
        """상태 저장"""
        state = {
            'context_history': list(self.context_history),
            'document_stats': dict(self.document_stats),
            'context_relevance_matrix': dict(self.context_relevance_matrix),
            'config': {
                'context_window_size': self.context_window_size,
                'forgetting_threshold': self.forgetting_threshold,
                'context_decay_rate': self.context_decay_rate,
                'usage_weight': self.usage_weight,
                'recency_weight': self.recency_weight,
                'relevance_weight': self.relevance_weight
            }
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
    
    def load_state(self, filepath: str) -> None:
        """상태 로드"""
        if not Path(filepath).exists():
            return
            
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        self.context_history = deque(state['context_history'], maxlen=self.context_window_size)
        self.document_stats = defaultdict(lambda: {
            'access_count': 0,
            'last_access': None,
            'context_relevance': 0.0,
            'forgetting_score': 1.0
        }, state['document_stats'])
        self.context_relevance_matrix = defaultdict(dict, state['context_relevance_matrix'])


class AdaptiveForgettingPolicy:
    """적응적 망각 정책"""
    
    def __init__(self, forgetting_manager: ContextualForgettingManager):
        self.forgetting_manager = forgetting_manager
        self.performance_history = deque(maxlen=100)
        
    def adapt_threshold(self, performance_metric: float) -> None:
        """성능에 따라 망각 임계값 적응"""
        self.performance_history.append(performance_metric)
        
        if len(self.performance_history) < 10:
            return
            
        # 최근 성능이 좋지 않으면 임계값 조정
        recent_performance = np.mean(list(self.performance_history)[-10:])
        if recent_performance < 0.5:
            # 성능이 낮으면 더 많은 정보 보존
            self.forgetting_manager.forgetting_threshold = max(0.1, 
                self.forgetting_manager.forgetting_threshold - 0.05)
        elif recent_performance > 0.8:
            # 성능이 높으면 더 적극적으로 망각
            self.forgetting_manager.forgetting_threshold = min(0.9,
                self.forgetting_manager.forgetting_threshold + 0.05)
    
    def get_adaptive_weights(self, query_type: str) -> Dict[str, float]:
        """쿼리 타입에 따른 적응적 가중치"""
        base_weights = {
            'usage_weight': self.forgetting_manager.usage_weight,
            'recency_weight': self.forgetting_manager.recency_weight,
            'relevance_weight': self.forgetting_manager.relevance_weight
        }
        
        # 쿼리 타입별 가중치 조정
        if query_type == 'temporal':
            # 시간 관련 쿼리는 최근성에 더 높은 가중치
            return {
                'usage_weight': 0.2,
                'recency_weight': 0.6,
                'relevance_weight': 0.2
            }
        elif query_type == 'author':
            # 작성자 관련 쿼리는 사용 빈도에 더 높은 가중치
            return {
                'usage_weight': 0.5,
                'recency_weight': 0.3,
                'relevance_weight': 0.2
            }
        else:
            # 일반 쿼리는 기본 가중치 사용
            return base_weights


def create_contextual_forgetting_manager(config: Optional[Dict[str, Any]] = None) -> ContextualForgettingManager:
    """맥락적 망각 관리자 생성"""
    if config is None:
        config = {}
    
    return ContextualForgettingManager(
        context_window_size=config.get('context_window_size', 10),
        forgetting_threshold=config.get('forgetting_threshold', 0.3),
        context_decay_rate=config.get('context_decay_rate', 0.1),
        usage_weight=config.get('usage_weight', 0.3),
        recency_weight=config.get('recency_weight', 0.4),
        relevance_weight=config.get('relevance_weight', 0.3)
    )
