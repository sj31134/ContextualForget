"""
Adaptive Retrieval Strategy for RAG Systems
RQ3: 적응적 검색 전략 구현
"""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict, deque
import re

from ..core.contextual_forgetting import ContextualForgettingManager
from .contextual_forget_engine import ContextualForgetEngine


class AdaptiveRetrievalStrategy:
    """적응적 검색 전략"""
    
    def __init__(self, 
                 base_engines: Dict[str, Any],
                 performance_window: int = 20,
                 adaptation_threshold: float = 0.1):
        """
        Args:
            base_engines: 기본 검색 엔진들 (BM25, Vector, ContextualForget)
            performance_window: 성능 평가 윈도우 크기
            adaptation_threshold: 적응 임계값
        """
        self.base_engines = base_engines
        self.performance_window = performance_window
        self.adaptation_threshold = adaptation_threshold
        
        # 성능 히스토리
        self.performance_history: deque = deque(maxlen=performance_window)
        
        # 쿼리 타입별 성능 추적
        self.query_type_performance: Dict[str, List[float]] = defaultdict(list)
        
        # 엔진별 성능 추적
        self.engine_performance: Dict[str, List[float]] = defaultdict(list)
        
        # 적응적 가중치
        self.adaptive_weights = {
            'BM25': 0.33,
            'Vector': 0.33,
            'ContextualForget': 0.34
        }
        
        # 쿼리 타입별 최적 엔진 매핑
        self.optimal_engines = {
            'keyword': 'BM25',
            'semantic': 'Vector',
            'contextual': 'ContextualForget',
            'guid': 'ContextualForget',
            'author': 'ContextualForget',
            'temporal': 'ContextualForget'
        }
        
        # 적응 파라미터
        self.learning_rate = 0.1
        self.exploration_rate = 0.1
        
    def classify_query(self, query: str) -> str:
        """쿼리 분류"""
        query_lower = query.lower()
        
        # GUID 쿼리
        if re.search(r'\b[A-Za-z0-9]{22}\b', query):
            return 'guid'
        
        # 시간 관련 쿼리
        temporal_keywords = ['최근', '이전', '생성', '날짜', '일', '주', '월', '년', 'recent', 'ago', 'created', 'date']
        if any(keyword in query_lower for keyword in temporal_keywords):
            return 'temporal'
        
        # 작성자 관련 쿼리
        author_keywords = ['engineer_', 'architect_', 'user_', '작성자', 'author']
        if any(keyword in query_lower for keyword in author_keywords):
            return 'author'
        
        # 의미적 쿼리 (복잡한 문장)
        if len(query.split()) > 3 and any(word in query_lower for word in ['관련', '문제', '이슈', 'related', 'issue', 'problem']):
            return 'semantic'
        
        # 기본적으로 키워드 쿼리
        return 'keyword'
    
    def select_optimal_engine(self, query: str, query_type: str) -> str:
        """최적 엔진 선택"""
        # 기본 엔진 선택
        base_engine = self.optimal_engines.get(query_type, 'ContextualForget')
        
        # 성능 기반 적응
        if query_type in self.query_type_performance:
            performances = self.query_type_performance[query_type]
            if len(performances) >= 5:  # 충분한 데이터가 있을 때
                # 최근 성능이 좋은 엔진 선택
                recent_performance = np.mean(performances[-5:])
                if recent_performance < 0.5:  # 성능이 낮으면 다른 엔진 시도
                    # 탐험적 선택
                    if np.random.random() < self.exploration_rate:
                        engines = list(self.base_engines.keys())
                        return np.random.choice([e for e in engines if e != base_engine])
        
        return base_engine
    
    def execute_adaptive_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """적응적 쿼리 실행"""
        start_time = datetime.now()
        
        # 쿼리 분류
        query_type = self.classify_query(query)
        
        # 최적 엔진 선택
        selected_engine = self.select_optimal_engine(query, query_type)
        
        # 선택된 엔진으로 쿼리 실행
        engine = self.base_engines[selected_engine]
        
        if selected_engine == 'ContextualForget':
            result = engine.contextual_query(query, query_type=query_type)
        elif selected_engine == 'BM25':
            result = engine.process_query(query)
        elif selected_engine == 'Vector':
            result = engine.process_query(query)
        else:
            result = {'answer': 'Unknown engine', 'confidence': 0.0}
        
        # 응답 시간 계산
        response_time = (datetime.now() - start_time).total_seconds()
        
        # 결과 정리
        adaptive_result = {
            'query': query,
            'query_type': query_type,
            'selected_engine': selected_engine,
            'result': result,
            'response_time': response_time,
            'timestamp': datetime.now(timezone.utc)
        }
        
        return adaptive_result
    
    def update_performance(self, query_result: Dict[str, Any], feedback: Optional[float] = None):
        """성능 업데이트"""
        query_type = query_result['query_type']
        selected_engine = query_result['selected_engine']
        
        # 피드백이 없으면 기본 성능 메트릭 사용
        if feedback is None:
            result = query_result['result']
            if isinstance(result, dict):
                confidence = result.get('confidence', 0.0)
                result_count = result.get('result_count', result.get('results_count', 0))
                response_time = query_result['response_time']
                
                # 복합 성능 점수 계산
                performance_score = (
                    confidence * 0.4 +
                    min(1.0, result_count / 10.0) * 0.3 +
                    max(0.0, 1.0 - response_time / 5.0) * 0.3
                )
            else:
                performance_score = 0.0
        else:
            performance_score = feedback
        
        # 성능 히스토리 업데이트
        self.performance_history.append(performance_score)
        
        # 쿼리 타입별 성능 업데이트
        self.query_type_performance[query_type].append(performance_score)
        if len(self.query_type_performance[query_type]) > self.performance_window:
            self.query_type_performance[query_type] = self.query_type_performance[query_type][-self.performance_window:]
        
        # 엔진별 성능 업데이트
        self.engine_performance[selected_engine].append(performance_score)
        if len(self.engine_performance[selected_engine]) > self.performance_window:
            self.engine_performance[selected_engine] = self.engine_performance[selected_engine][-self.performance_window:]
        
        # 적응적 가중치 업데이트
        self._update_adaptive_weights()
    
    def _update_adaptive_weights(self):
        """적응적 가중치 업데이트"""
        if len(self.performance_history) < 5:
            return
        
        # 최근 성능 계산
        recent_performance = np.mean(list(self.performance_history)[-5:])
        
        # 엔진별 최근 성능 계산
        engine_scores = {}
        for engine, performances in self.engine_performance.items():
            if len(performances) >= 3:
                engine_scores[engine] = np.mean(performances[-3:])
        
        if not engine_scores:
            return
        
        # 가중치 업데이트
        total_score = sum(engine_scores.values())
        if total_score > 0:
            for engine in self.adaptive_weights:
                if engine in engine_scores:
                    # 성능에 비례하여 가중치 조정
                    new_weight = engine_scores[engine] / total_score
                    # 점진적 업데이트
                    self.adaptive_weights[engine] = (
                        (1 - self.learning_rate) * self.adaptive_weights[engine] +
                        self.learning_rate * new_weight
                    )
        
        # 가중치 정규화
        total_weight = sum(self.adaptive_weights.values())
        if total_weight > 0:
            for engine in self.adaptive_weights:
                self.adaptive_weights[engine] /= total_weight
    
    def get_adaptive_statistics(self) -> Dict[str, Any]:
        """적응적 통계 반환"""
        stats = {
            'total_queries': len(self.performance_history),
            'average_performance': np.mean(list(self.performance_history)) if self.performance_history else 0,
            'adaptive_weights': self.adaptive_weights.copy(),
            'query_type_performance': {},
            'engine_performance': {}
        }
        
        # 쿼리 타입별 성능
        for query_type, performances in self.query_type_performance.items():
            if performances:
                stats['query_type_performance'][query_type] = {
                    'count': len(performances),
                    'average': np.mean(performances),
                    'recent_average': np.mean(performances[-5:]) if len(performances) >= 5 else np.mean(performances)
                }
        
        # 엔진별 성능
        for engine, performances in self.engine_performance.items():
            if performances:
                stats['engine_performance'][engine] = {
                    'count': len(performances),
                    'average': np.mean(performances),
                    'recent_average': np.mean(performances[-5:]) if len(performances) >= 5 else np.mean(performances)
                    }
        
        return stats
    
    def save_adaptive_state(self, filepath: str):
        """적응적 상태 저장"""
        state = {
            'performance_history': list(self.performance_history),
            'query_type_performance': dict(self.query_type_performance),
            'engine_performance': dict(self.engine_performance),
            'adaptive_weights': self.adaptive_weights,
            'optimal_engines': self.optimal_engines,
            'config': {
                'performance_window': self.performance_window,
                'adaptation_threshold': self.adaptation_threshold,
                'learning_rate': self.learning_rate,
                'exploration_rate': self.exploration_rate
            }
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
    
    def load_adaptive_state(self, filepath: str):
        """적응적 상태 로드"""
        if not Path(filepath).exists():
            return
        
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        self.performance_history = deque(state['performance_history'], maxlen=self.performance_window)
        self.query_type_performance = defaultdict(list, state['query_type_performance'])
        self.engine_performance = defaultdict(list, state['engine_performance'])
        self.adaptive_weights = state['adaptive_weights']
        self.optimal_engines = state['optimal_engines']


class HybridRetrievalEngine:
    """하이브리드 검색 엔진"""
    
    def __init__(self, 
                 base_engines: Dict[str, Any],
                 fusion_strategy: str = 'weighted',
                 enable_adaptation: bool = True):
        """
        Args:
            base_engines: 기본 검색 엔진들
            fusion_strategy: 융합 전략 ('weighted', 'ranked', 'adaptive')
            enable_adaptation: 적응 활성화 여부
        """
        self.base_engines = base_engines
        self.fusion_strategy = fusion_strategy
        self.enable_adaptation = enable_adaptation
        
        if enable_adaptation:
            self.adaptive_strategy = AdaptiveRetrievalStrategy(base_engines)
        else:
            self.adaptive_strategy = None
    
    def query(self, query: str, **kwargs) -> Dict[str, Any]:
        """하이브리드 쿼리"""
        if self.fusion_strategy == 'adaptive' and self.adaptive_strategy:
            # 적응적 전략 사용
            return self.adaptive_strategy.execute_adaptive_query(query, **kwargs)
        elif self.fusion_strategy == 'weighted':
            # 가중치 기반 융합
            return self._weighted_fusion(query, **kwargs)
        elif self.fusion_strategy == 'ranked':
            # 순위 기반 융합
            return self._ranked_fusion(query, **kwargs)
        else:
            # 기본 전략
            return self._basic_fusion(query, **kwargs)
    
    def _weighted_fusion(self, query: str, **kwargs) -> Dict[str, Any]:
        """가중치 기반 융합"""
        results = {}
        
        # 각 엔진에서 결과 수집
        for engine_name, engine in self.base_engines.items():
            try:
                if engine_name == 'ContextualForget':
                    result = engine.contextual_query(query)
                else:
                    result = engine.process_query(query)
                results[engine_name] = result
            except Exception as e:
                results[engine_name] = {'error': str(e), 'confidence': 0.0}
        
        # 가중치 적용
        weights = self.adaptive_strategy.adaptive_weights if self.adaptive_strategy else {
            'BM25': 0.33, 'Vector': 0.33, 'ContextualForget': 0.34
        }
        
        # 융합된 결과 생성
        fused_confidence = sum(
            results[engine].get('confidence', 0.0) * weights.get(engine, 0.33)
            for engine in results
        )
        
        # 표준 형식으로 변환
        fused_result = {
            'answer': self._generate_fused_answer(results),
            'confidence': fused_confidence,
            'result_count': sum(results[engine].get('result_count', 0) for engine in results),
            'entities': self._merge_entities(results),
            'source': 'Hybrid',
            'details': {
                'query': query,
                'strategy': 'weighted_fusion',
                'engine_results': results,
                'fused_confidence': fused_confidence,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        return fused_result
    
    def _generate_fused_answer(self, results: Dict[str, Any]) -> str:
        """융합된 답변 생성"""
        successful_results = [r for r in results.values() if r.get('confidence', 0) > 0]
        
        if not successful_results:
            return "관련 정보를 찾을 수 없습니다."
        
        # 가장 높은 신뢰도의 결과를 기본으로 사용
        best_result = max(successful_results, key=lambda x: x.get('confidence', 0))
        base_answer = best_result.get('answer', '')
        
        # 여러 엔진이 성공한 경우 추가 정보 포함
        if len(successful_results) > 1:
            engine_count = len(successful_results)
            return f"{base_answer} ({engine_count}개 엔진에서 검증됨)"
        
        return base_answer
    
    def _merge_entities(self, results: Dict[str, Any]) -> List[str]:
        """엔티티 리스트 병합"""
        all_entities = []
        for result in results.values():
            entities = result.get('entities', [])
            if isinstance(entities, list):
                all_entities.extend(entities)
        
        # 중복 제거
        return list(set(all_entities))
    
    def _ranked_fusion(self, query: str, **kwargs) -> Dict[str, Any]:
        """순위 기반 융합"""
        results = {}
        
        # 각 엔진에서 결과 수집
        for engine_name, engine in self.base_engines.items():
            try:
                if engine_name == 'ContextualForget':
                    result = engine.contextual_query(query)
                else:
                    result = engine.process_query(query)
                results[engine_name] = result
            except Exception as e:
                results[engine_name] = {'error': str(e), 'confidence': 0.0}
        
        # 신뢰도로 정렬
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].get('confidence', 0.0),
            reverse=True
        )
        
        # 최고 성능 엔진 결과 반환
        best_engine, best_result = sorted_results[0]
        
        fused_result = {
            'query': query,
            'strategy': 'ranked_fusion',
            'best_engine': best_engine,
            'best_result': best_result,
            'all_results': results,
            'timestamp': datetime.now(timezone.utc)
        }
        
        return fused_result
    
    def _basic_fusion(self, query: str, **kwargs) -> Dict[str, Any]:
        """기본 융합 (ContextualForget 우선)"""
        try:
            result = self.base_engines['ContextualForget'].contextual_query(query)
            # 표준 형식 확인 및 추가
            if 'source' not in result:
                result['source'] = 'Hybrid'
            result['strategy'] = 'basic_fusion'
            result['selected_engine'] = 'ContextualForget'
            return result
        except Exception as e:
            return {
                'answer': '검색 중 오류가 발생했습니다.',
                'confidence': 0.0,
                'result_count': 0,
                'entities': [],
                'source': 'Hybrid',
                'details': {
                    'query': query,
                    'strategy': 'basic_fusion',
                    'error': str(e)
                }
            }
    
    def update_performance(self, query_result: Dict[str, Any], feedback: Optional[float] = None):
        """성능 업데이트"""
        if self.adaptive_strategy:
            self.adaptive_strategy.update_performance(query_result, feedback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 반환"""
        stats = {
            'fusion_strategy': self.fusion_strategy,
            'enable_adaptation': self.enable_adaptation
        }
        
        if self.adaptive_strategy:
            stats['adaptive_statistics'] = self.adaptive_strategy.get_adaptive_statistics()
        
        return stats


def create_hybrid_retrieval_engine(base_engines: Dict[str, Any], 
                                 config: Optional[Dict[str, Any]] = None) -> HybridRetrievalEngine:
    """하이브리드 검색 엔진 생성"""
    if config is None:
        config = {}
    
    return HybridRetrievalEngine(
        base_engines=base_engines,
        fusion_strategy=config.get('fusion_strategy', 'adaptive'),
        enable_adaptation=config.get('enable_adaptation', True)
    )
