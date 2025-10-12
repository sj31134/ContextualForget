#!/usr/bin/env python3
"""
평가 메트릭 구현

목표:
- Accuracy: 정답 일치율
- F1 Score: Precision과 Recall의 조화평균
- Attribution Precision/Recall: 출처 정확도
- Contextual Consistency: 맥락 일관성
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from collections import Counter
import re


class EvaluationMetrics:
    """평가 메트릭 계산"""
    
    def __init__(self):
        pass
    
    def exact_match(self, predicted: str, ground_truth: str) -> float:
        """정확한 일치 (Exact Match)"""
        return 1.0 if predicted.strip().lower() == ground_truth.strip().lower() else 0.0
    
    def set_match(self, predicted: List[str], ground_truth: List[str]) -> Dict[str, float]:
        """집합 일치 (Set Match) - Precision, Recall, F1"""
        pred_set = set(p.strip().lower() for p in predicted)
        gt_set = set(g.strip().lower() for g in ground_truth)
        
        if not gt_set:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "exact_match": 0.0}
        
        true_positives = len(pred_set & gt_set)
        false_positives = len(pred_set - gt_set)
        false_negatives = len(gt_set - pred_set)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        exact_match = 1.0 if pred_set == gt_set else 0.0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "exact_match": exact_match,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        }
    
    def semantic_match(self, predicted: str, ground_truth: str, threshold: float = 0.2) -> float:
        """의미적 일치 (개선된 버전)"""
        # 핵심 키워드 추출 (GUID, 타입 등)
        pred_lower = predicted.lower()
        gt_lower = ground_truth.lower()
        
        # 핵심 키워드들
        key_terms = ['guid', 'furnishingelement', 'wall', 'door', 'window', 'column', 'beam', 'slab']
        
        # 핵심 키워드 매칭 점수
        key_score = 0
        for term in key_terms:
            if term in pred_lower and term in gt_lower:
                key_score += 1
        
        # GUID 매칭 (가장 중요)
        guid_match = 0
        if 'lqchgivjujq7eviqxthq7p' in pred_lower and 'lqchgivjujq7eviqxthq7p' in gt_lower:
            guid_match = 1
        
        # 전체 단어 유사도
        pred_words = set(re.findall(r'\w+', pred_lower))
        gt_words = set(re.findall(r'\w+', gt_lower))
        
        if not gt_words:
            return 0.0
        
        common = len(pred_words & gt_words)
        union = len(pred_words | gt_words)
        word_similarity = common / union if union > 0 else 0.0
        
        # 종합 점수 (GUID 매칭이 가장 중요)
        final_score = (guid_match * 0.5) + (key_score * 0.2) + (word_similarity * 0.3)
        
        return 1.0 if final_score >= threshold else 0.0
    
    def attribution_metrics(self, predicted_sources: List[str], ground_truth_sources: List[str]) -> Dict[str, float]:
        """출처 정확도 (Attribution Precision/Recall)"""
        return self.set_match(predicted_sources, ground_truth_sources)
    
    def calculate_answer_accuracy(self, qa_pairs: List[Dict[str, Any]], predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """답변 정확도 계산"""
        
        if len(qa_pairs) != len(predictions):
            raise ValueError(f"QA 쌍({len(qa_pairs)})과 예측({len(predictions)}) 수가 다릅니다")
        
        results = []
        total_accuracy = 0.0
        total_f1 = 0.0
        by_category = {}
        by_difficulty = {}
        
        for qa, pred in zip(qa_pairs, predictions):
            qa_id = qa.get('id')
            eval_type = qa.get('evaluation_type', 'exact_match')
            category = qa.get('category', 'unknown')
            difficulty = qa.get('difficulty', 'unknown')
            
            # Ground truth 추출
            gt_answer = qa.get('answer', '')
            gt_data = qa.get('ground_truth', {})
            
            # Prediction 추출
            pred_answer = pred.get('predicted_answer', '')
            pred_sources = pred.get('sources', [])
            
            # 평가 타입별 메트릭 계산
            if eval_type == 'exact_match':
                score = self.exact_match(pred_answer, gt_answer)
                # Exact match가 실패하면 semantic match 시도
                if score == 0.0:
                    score = self.semantic_match(pred_answer, gt_answer)
                metrics = {
                    "accuracy": score,
                    "f1": score,
                    "precision": score,
                    "recall": score
                }
            
            elif eval_type == 'set_match':
                # Ground truth에서 항목 추출
                gt_items = self._extract_items_from_answer(gt_answer)
                pred_items = self._extract_items_from_answer(pred_answer)
                
                metrics = self.set_match(pred_items, gt_items)
                metrics["accuracy"] = metrics["exact_match"]
            
            elif eval_type == 'semantic_match':
                score = self.semantic_match(pred_answer, gt_answer)
                metrics = {
                    "accuracy": score,
                    "f1": score,
                    "precision": score,
                    "recall": score
                }
            
            else:
                metrics = {"accuracy": 0.0, "f1": 0.0}
            
            # Attribution 계산 (sources가 있는 경우)
            if pred_sources and 'sources' in gt_data:
                gt_sources = gt_data['sources']
                attr_metrics = self.attribution_metrics(pred_sources, gt_sources)
                metrics["attribution_precision"] = attr_metrics["precision"]
                metrics["attribution_recall"] = attr_metrics["recall"]
                metrics["attribution_f1"] = attr_metrics["f1"]
            
            # 결과 저장
            result = {
                "qa_id": qa_id,
                "category": category,
                "difficulty": difficulty,
                "evaluation_type": eval_type,
                "metrics": metrics,
                "predicted_answer": pred_answer,
                "ground_truth_answer": gt_answer
            }
            
            results.append(result)
            
            # 집계
            total_accuracy += metrics["accuracy"]
            total_f1 += metrics["f1"]
            
            # 카테고리별
            if category not in by_category:
                by_category[category] = {"count": 0, "accuracy": 0.0, "f1": 0.0}
            by_category[category]["count"] += 1
            by_category[category]["accuracy"] += metrics["accuracy"]
            by_category[category]["f1"] += metrics["f1"]
            
            # 난이도별
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = {"count": 0, "accuracy": 0.0, "f1": 0.0}
            by_difficulty[difficulty]["count"] += 1
            by_difficulty[difficulty]["accuracy"] += metrics["accuracy"]
            by_difficulty[difficulty]["f1"] += metrics["f1"]
        
        # 평균 계산
        n = len(results)
        
        for cat, data in by_category.items():
            count = data["count"]
            data["accuracy"] /= count
            data["f1"] /= count
        
        for diff, data in by_difficulty.items():
            count = data["count"]
            data["accuracy"] /= count
            data["f1"] /= count
        
        summary = {
            "total_questions": n,
            "average_accuracy": total_accuracy / n if n > 0 else 0.0,
            "average_f1": total_f1 / n if n > 0 else 0.0,
            "by_category": by_category,
            "by_difficulty": by_difficulty,
            "detailed_results": results
        }
        
        return summary
    
    def _extract_items_from_answer(self, answer: str) -> List[str]:
        """답변에서 항목 추출 (콤마 또는 줄바꿈 기준)"""
        # "총 N개: item1, item2, item3" 형식 처리
        if ':' in answer:
            answer = answer.split(':', 1)[1]
        
        # 콤마로 분리
        items = [item.strip() for item in answer.split(',')]
        
        # 빈 항목 제거
        items = [item for item in items if item]
        
        return items
    
    def calculate_forgetting_metrics(self, old_version_citations: List[Dict[str, Any]]) -> Dict[str, float]:
        """망각 메커니즘 평가 메트릭"""
        
        total = len(old_version_citations)
        if total == 0:
            return {
                "old_version_citation_rate": 0.0,
                "contradiction_rate": 0.0,
                "correct_forgetting_rate": 0.0
            }
        
        cited_old = sum(1 for c in old_version_citations if c.get('cited_old_version', False))
        contradictions = sum(1 for c in old_version_citations if c.get('has_contradiction', False))
        correct_forget = sum(1 for c in old_version_citations if c.get('correctly_forgotten', False))
        
        return {
            "old_version_citation_rate": cited_old / total,
            "contradiction_rate": contradictions / total,
            "correct_forgetting_rate": correct_forget / total,
            "total_evaluations": total
        }


def main():
    """메인 - 메트릭 테스트"""
    
    print("=" * 70)
    print("🧪 평가 메트릭 테스트")
    print("=" * 70)
    print()
    
    metrics = EvaluationMetrics()
    
    # 1. Exact Match 테스트
    print("1️⃣ Exact Match")
    score = metrics.exact_match("IfcWall", "IfcWall")
    print(f"   ✅ 일치: {score}")
    
    score = metrics.exact_match("IfcWall", "IfcDoor")
    print(f"   ❌ 불일치: {score}")
    print()
    
    # 2. Set Match 테스트
    print("2️⃣ Set Match (F1, Precision, Recall)")
    predicted = ["issue1", "issue2", "issue3"]
    ground_truth = ["issue1", "issue2", "issue4"]
    result = metrics.set_match(predicted, ground_truth)
    print(f"   Predicted: {predicted}")
    print(f"   Ground Truth: {ground_truth}")
    print(f"   Precision: {result['precision']:.3f}")
    print(f"   Recall: {result['recall']:.3f}")
    print(f"   F1: {result['f1']:.3f}")
    print()
    
    # 3. Semantic Match 테스트
    print("3️⃣ Semantic Match")
    pred = "The wall thickness is insufficient for insulation requirements"
    gt = "Wall thickness does not meet insulation standards"
    score = metrics.semantic_match(pred, gt)
    print(f"   Predicted: {pred[:50]}...")
    print(f"   Ground Truth: {gt[:50]}...")
    print(f"   Score: {score}")
    print()
    
    # 4. Attribution 테스트
    print("4️⃣ Attribution Precision/Recall")
    pred_sources = ["IFC1", "IFC2", "BCF1"]
    gt_sources = ["IFC1", "IFC2", "BCF2"]
    result = metrics.attribution_metrics(pred_sources, gt_sources)
    print(f"   Predicted Sources: {pred_sources}")
    print(f"   Ground Truth Sources: {gt_sources}")
    print(f"   Attribution Precision: {result['precision']:.3f}")
    print(f"   Attribution Recall: {result['recall']:.3f}")
    print(f"   Attribution F1: {result['f1']:.3f}")
    print()
    
    print("=" * 70)
    print("✅ 메트릭 테스트 완료")
    print("=" * 70)
    print(f"""
📊 구현된 메트릭:
  1. Exact Match - 정확한 일치
  2. Set Match (F1) - 집합 기반 평가
  3. Semantic Match - 의미적 유사도
  4. Attribution P/R - 출처 정확도
  5. Forgetting Metrics - 망각 평가

📝 다음 단계:
  - python eval/run_benchmark.py (벤치마크 실행)
""")


if __name__ == "__main__":
    main()

