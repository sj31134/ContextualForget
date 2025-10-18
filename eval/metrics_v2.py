"""
평가 메트릭 v2 - 개선된 평가 시스템
NDCG, F1, Precision, Recall 등 표준 메트릭 구현
"""
from typing import Dict, List, Set
import numpy as np
from math import log2


class EvaluationMetricsV2:
    """개선된 평가 메트릭 시스템"""
    
    @staticmethod
    def is_success(result: Dict, gold: Dict) -> bool:
        """
        명확한 성공 정의
        
        Args:
            result: 엔진 응답 결과
            gold: Gold Standard QA
            
        Returns:
            성공 여부
        """
        # 1. 결과 존재 확인
        if result.get('result_count', 0) == 0:
            return False
        
        # 2. 신뢰도 임계값 (최소 0.1 이상)
        if result.get('confidence', 0) < 0.1:
            return False
        
        # 3. Gold 엔티티 매칭 확인 (Recall ≥ 10%)
        retrieved = set(result.get('entities', []))
        gold_set = set(gold.get('gold_entities', []))
        
        if not gold_set:
            # Gold가 없으면 결과만 있으면 성공
            return True
        
        recall = len(retrieved & gold_set) / len(gold_set)
        return recall >= 0.1
    
    @staticmethod
    def compute_precision_recall(result: Dict, gold: Dict) -> tuple:
        """
        Precision과 Recall 계산
        
        Args:
            result: 엔진 응답 결과
            gold: Gold Standard QA
            
        Returns:
            (precision, recall) 튜플
        """
        retrieved = set(result.get('entities', []))
        gold_set = set(gold.get('gold_entities', []))
        
        if not gold_set:
            return 0.0, 0.0
        
        if not retrieved:
            return 0.0, 0.0
        
        tp = len(retrieved & gold_set)
        precision = tp / len(retrieved)
        recall = tp / len(gold_set)
        
        return precision, recall
    
    @staticmethod
    def compute_f1(precision: float, recall: float) -> float:
        """
        F1 점수 계산
        
        Args:
            precision: Precision 값
            recall: Recall 값
            
        Returns:
            F1 점수
        """
        if precision + recall == 0:
            return 0.0
        
        return 2 * precision * recall / (precision + recall)
    
    @staticmethod
    def compute_ndcg(result: Dict, gold: Dict, k: int = 10) -> float:
        """
        NDCG@k (Normalized Discounted Cumulative Gain) 계산
        
        Args:
            result: 엔진 응답 결과
            gold: Gold Standard QA
            k: 상위 k개 결과 고려
            
        Returns:
            NDCG@k 점수
        """
        retrieved_ids = result.get('entities', [])[:k]
        gold_ids = set(gold.get('gold_entities', []))
        
        if not gold_ids or not retrieved_ids:
            return 0.0
        
        # DCG 계산
        dcg = sum(
            1.0 / log2(i + 2) if retrieved_ids[i] in gold_ids else 0.0
            for i in range(len(retrieved_ids))
        )
        
        # IDCG 계산 (이상적인 순서)
        idcg = sum(1.0 / log2(i + 2) for i in range(min(len(gold_ids), k)))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def compute_mrr(result: Dict, gold: Dict) -> float:
        """
        MRR (Mean Reciprocal Rank) 계산
        
        Args:
            result: 엔진 응답 결과
            gold: Gold Standard QA
            
        Returns:
            MRR 점수
        """
        retrieved_ids = result.get('entities', [])
        gold_ids = set(gold.get('gold_entities', []))
        
        if not gold_ids or not retrieved_ids:
            return 0.0
        
        # 첫 번째 정답의 위치 찾기
        for i, entity_id in enumerate(retrieved_ids):
            if entity_id in gold_ids:
                return 1.0 / (i + 1)
        
        return 0.0
    
    @staticmethod
    def compute_metrics(result: Dict, gold: Dict) -> Dict:
        """
        종합 메트릭 계산
        
        Args:
            result: 엔진 응답 결과
            gold: Gold Standard QA
            
        Returns:
            메트릭 딕셔너리
        """
        # Precision & Recall
        precision, recall = EvaluationMetricsV2.compute_precision_recall(result, gold)
        
        # F1
        f1 = EvaluationMetricsV2.compute_f1(precision, recall)
        
        # NDCG@10
        ndcg = EvaluationMetricsV2.compute_ndcg(result, gold, k=10)
        
        # MRR
        mrr = EvaluationMetricsV2.compute_mrr(result, gold)
        
        # 성공 여부
        success = EvaluationMetricsV2.is_success(result, gold)
        
        # 신뢰도 및 응답 시간
        confidence = result.get('confidence', 0.0)
        response_time = result.get('details', {}).get('processing_time', 0.0)
        
        return {
            'success': success,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'ndcg@10': ndcg,
            'mrr': mrr,
            'confidence': confidence,
            'response_time': response_time,
            'result_count': result.get('result_count', 0)
        }
    
    @staticmethod
    def aggregate_metrics(metrics_list: List[Dict]) -> Dict:
        """
        여러 메트릭의 평균 계산
        
        Args:
            metrics_list: 메트릭 딕셔너리 리스트
            
        Returns:
            집계된 메트릭
        """
        if not metrics_list:
            return {}
        
        keys = ['success', 'precision', 'recall', 'f1', 'ndcg@10', 'mrr', 
                'confidence', 'response_time', 'result_count']
        
        aggregated = {}
        for key in keys:
            values = [m[key] for m in metrics_list if key in m]
            if values:
                if key == 'success':
                    aggregated[f'{key}_rate'] = sum(values) / len(values)
                else:
                    aggregated[f'avg_{key}'] = np.mean(values)
                    aggregated[f'std_{key}'] = np.std(values)
        
        return aggregated


def validate_response_format(response: Dict) -> bool:
    """
    엔진 응답이 표준 형식을 따르는지 검증
    
    Args:
        response: 엔진 응답
        
    Returns:
        검증 통과 여부
    """
    required_fields = ['answer', 'confidence', 'result_count', 'entities', 'source']
    
    for field in required_fields:
        if field not in response:
            return False
    
    # 타입 검증
    if not isinstance(response['answer'], str):
        return False
    if not isinstance(response['confidence'], (int, float)):
        return False
    if not isinstance(response['result_count'], int):
        return False
    if not isinstance(response['entities'], list):
        return False
    if not isinstance(response['source'], str):
        return False
    
    # 값 범위 검증
    if not (0.0 <= response['confidence'] <= 1.0):
        return False
    if response['result_count'] < 0:
        return False
    
    return True


if __name__ == "__main__":
    # 테스트
    result = {
        'answer': 'Test answer',
        'confidence': 0.8,
        'result_count': 3,
        'entities': ['guid1', 'guid2', 'guid3'],
        'source': 'TestEngine',
        'details': {'processing_time': 0.1}
    }
    
    gold = {
        'question': 'Test question',
        'answer': 'Test gold answer',
        'gold_entities': ['guid1', 'guid4']
    }
    
    metrics = EvaluationMetricsV2.compute_metrics(result, gold)
    print("테스트 메트릭:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    is_valid = validate_response_format(result)
    print(f"\n응답 형식 검증: {'통과' if is_valid else '실패'}")

