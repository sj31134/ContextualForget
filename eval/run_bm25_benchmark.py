#!/usr/bin/env python3
"""
BM25 엔진 벤치마크 실행 스크립트
"""

import sys
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from contextualforget.baselines import BM25QueryEngine
from metrics import EvaluationMetrics


class BM25BenchmarkRunner:
    """BM25 엔진 벤치마크 실행기"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.eval_dir = self.base_dir / "eval"
        self.graph_path = self.base_dir / "data" / "processed" / "graph.gpickle"
        
        # 컴포넌트 초기화
        self.graph = self._load_graph()
        self.bm25_engine = None
        self.metrics = EvaluationMetrics()
        
        # 결과 저장
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "engine": "BM25",
            "graph_stats": {},
            "qa_results": [],
            "summary": {}
        }
    
    def _load_graph(self):
        """그래프 로드"""
        if not self.graph_path.exists():
            raise FileNotFoundError(f"그래프 파일이 없습니다: {self.graph_path}")
        
        with open(self.graph_path, 'rb') as f:
            graph = pickle.load(f)
        
        print(f"✅ 그래프 로드: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 엣지")
        return graph
    
    def initialize_engine(self):
        """BM25 엔진 초기화"""
        print("\n🔧 BM25 엔진 초기화 중...")
        
        # Prepare graph data for BM25
        graph_data = {"nodes": list(self.graph.nodes(data=True))}
        
        # Initialize BM25 engine
        self.bm25_engine = BM25QueryEngine()
        self.bm25_engine.initialize(graph_data)
        print("  ✅ BM25 엔진 초기화 완료")
    
    def load_gold_standard(self) -> List[Dict[str, Any]]:
        """Gold Standard QA 로드"""
        gold_path = self.eval_dir / "gold.jsonl"
        
        if not gold_path.exists():
            raise FileNotFoundError(f"Gold Standard 파일이 없습니다: {gold_path}")
        
        qa_pairs = []
        with open(gold_path, 'r', encoding='utf-8') as f:
            for line in f:
                qa_pairs.append(json.loads(line))
        
        print(f"✅ Gold Standard 로드: {len(qa_pairs)}개 QA 쌍")
        return qa_pairs
    
    def run_single_qa(self, qa: Dict[str, Any]) -> Dict[str, Any]:
        """단일 QA 실행"""
        qa_id = qa.get('qa_id', 'unknown')
        question = qa.get('question', '')
        ground_truth = qa.get('ground_truth', {})
        
        try:
            # BM25 쿼리 실행
            result = self.bm25_engine.process_query(question)
            
            # 결과 추출
            predicted_answer = result.get('answer', '')
            confidence = result.get('confidence', 0.0)
            
            # 평가 메트릭 계산 (BM25 답변 형식에 맞게 조정)
            metrics = self._calculate_bm25_metrics(predicted_answer, ground_truth)
            
            return {
                "qa_id": qa_id,
                "question": question,
                "predicted_answer": predicted_answer,
                "ground_truth": ground_truth,
                "confidence": confidence,
                "metrics": metrics,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "qa_id": qa_id,
                "question": question,
                "predicted_answer": "",
                "ground_truth": ground_truth,
                "confidence": 0.0,
                "metrics": {"exact_match": 0.0, "f1_score": 0.0, "semantic_match": 0.0},
                "status": "error",
                "error": str(e)
            }
    
    def _calculate_bm25_metrics(self, predicted_answer: str, ground_truth: Dict[str, Any]) -> Dict[str, float]:
        """BM25 답변에 대한 메트릭 계산"""
        if not predicted_answer or not ground_truth:
            return {"exact_match": 0.0, "f1_score": 0.0, "semantic_match": 0.0}
        
        # Ground truth에서 답변 추출
        gt_answer = ground_truth.get('answer', '')
        if isinstance(gt_answer, list):
            gt_answer = ' '.join(str(item) for item in gt_answer)
        elif isinstance(gt_answer, dict):
            gt_answer = str(gt_answer)
        
        # Exact Match
        exact_match = 1.0 if predicted_answer.strip() == gt_answer.strip() else 0.0
        
        # F1 Score (간단한 토큰 기반)
        pred_tokens = set(predicted_answer.lower().split())
        gt_tokens = set(gt_answer.lower().split())
        
        if not gt_tokens:
            f1_score = 1.0 if not pred_tokens else 0.0
        else:
            intersection = pred_tokens & gt_tokens
            precision = len(intersection) / len(pred_tokens) if pred_tokens else 0.0
            recall = len(intersection) / len(gt_tokens)
            f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Semantic Match (간단한 키워드 기반)
        semantic_score = 0.0
        if pred_tokens and gt_tokens:
            # 공통 키워드 비율
            common_ratio = len(intersection) / len(gt_tokens)
            semantic_score = min(common_ratio, 1.0)
        
        return {
            "exact_match": exact_match,
            "f1_score": f1_score,
            "semantic_match": semantic_score
        }
    
    def run_benchmark(self):
        """벤치마크 실행"""
        print("\n🚀 BM25 벤치마크 실행 시작")
        print("=" * 50)
        
        # Gold Standard 로드
        qa_pairs = self.load_gold_standard()
        
        # 벤치마크 실행
        print(f"\n🎯 벤치마크 실행 시작 ({len(qa_pairs)}개 QA)")
        
        for i, qa in enumerate(qa_pairs, 1):
            print(f"  진행률: {i}/{len(qa_pairs)} - {qa.get('qa_id', 'unknown')}")
            
            result = self.run_single_qa(qa)
            self.results["qa_results"].append(result)
        
        print(f"✅ 벤치마크 완료: {len(self.results['qa_results'])}개 결과")
        
        # 결과 평가
        self._evaluate_results()
        
        # 보고서 생성
        self._generate_report()
    
    def _evaluate_results(self):
        """결과 평가"""
        print("\n📊 결과 평가 중...")
        
        results = self.results["qa_results"]
        successful_results = [r for r in results if r["status"] == "success"]
        
        print(f"  평가 대상: {len(successful_results)}개 (성공한 QA)")
        
        if not successful_results:
            print("  ⚠️ 성공한 QA가 없습니다.")
            return
        
        # 전체 통계
        total_qa = len(successful_results)
        exact_matches = sum(1 for r in successful_results if r["metrics"]["exact_match"] > 0)
        avg_f1 = sum(r["metrics"]["f1_score"] for r in successful_results) / total_qa
        avg_semantic = sum(r["metrics"]["semantic_match"] for r in successful_results) / total_qa
        
        # 카테고리별 통계
        categories = {}
        for result in successful_results:
            # QA ID에서 카테고리 추출 (예: qa_entity_1 -> entity_search)
            qa_id = result["qa_id"]
            if "entity" in qa_id:
                category = "entity_search"
            elif "temporal" in qa_id:
                category = "temporal"
            elif "forgetting" in qa_id:
                category = "forgetting"
            elif "complex" in qa_id:
                category = "complex"
            else:
                category = "unknown"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # 요약 저장
        self.results["summary"] = {
            "total_qa": total_qa,
            "exact_match_count": exact_matches,
            "exact_match_rate": exact_matches / total_qa if total_qa > 0 else 0,
            "average_f1": avg_f1,
            "average_semantic_match": avg_semantic,
            "categories": {}
        }
        
        # 카테고리별 통계
        for category, category_results in categories.items():
            cat_total = len(category_results)
            cat_exact = sum(1 for r in category_results if r["metrics"]["exact_match"] > 0)
            cat_avg_f1 = sum(r["metrics"]["f1_score"] for r in category_results) / cat_total if cat_total > 0 else 0
            
            self.results["summary"]["categories"][category] = {
                "count": cat_total,
                "exact_match_rate": cat_exact / cat_total if cat_total > 0 else 0,
                "average_f1": cat_avg_f1
            }
    
    def _generate_report(self):
        """보고서 생성"""
        print("\n📝 보고서 생성 중...")
        
        # JSON 보고서
        json_path = self.eval_dir / "bm25_benchmark_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"  ✅ JSON 보고서: {json_path}")
        
        # Markdown 보고서
        md_path = self.eval_dir / "BM25_BENCHMARK_REPORT.md"
        self._generate_markdown_report(md_path)
        print(f"  ✅ Markdown 보고서: {md_path}")
        
        # 최종 결과 출력
        summary = self.results["summary"]
        print(f"\n======================================================================")
        print(f"✅ BM25 벤치마크 완료!")
        print(f"======================================================================")
        print(f"\n📊 최종 결과:")
        print(f"  - 평균 정확도: {summary['exact_match_rate']:.3f}")
        print(f"  - 평균 F1 점수: {summary['average_f1']:.3f}")
        print(f"  - 성공한 QA: {summary['total_qa']}개")
        print(f"  - 실패한 QA: {len(self.results['qa_results']) - summary['total_qa']}개")
        
        print(f"\n📂 생성된 파일:")
        print(f"  - {json_path}")
        print(f"  - {md_path}")
    
    def _generate_markdown_report(self, output_path: Path):
        """Markdown 보고서 생성"""
        summary = self.results["summary"]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# BM25 벤치마크 실행 보고서\n\n")
            f.write(f"**실행 일시**: {self.results['timestamp']}\n\n")
            
            # 그래프 통계
            f.write("## 📊 그래프 통계\n\n")
            f.write(f"- **노드 수**: {self.graph.number_of_nodes()}개\n")
            f.write(f"- **엣지 수**: {self.graph.number_of_edges()}개\n")
            f.write(f"- **방향성**: Directed\n\n")
            
            # QA 통계
            f.write("## 📋 QA 통계\n\n")
            f.write(f"- **총 QA 쌍**: {len(self.results['qa_results'])}개\n")
            f.write(f"- **성공한 QA**: {summary['total_qa']}개\n")
            f.write(f"- **실패한 QA**: {len(self.results['qa_results']) - summary['total_qa']}개\n")
            f.write(f"- **성공률**: {summary['total_qa'] / len(self.results['qa_results']) * 100:.1f}%\n\n")
            
            # 카테고리별 분포
            f.write("### 카테고리별 분포\n\n")
            for category, stats in summary["categories"].items():
                f.write(f"- **{category}**: {stats['count']}개\n")
            
            # 평가 결과
            f.write("\n## 🎯 평가 결과\n\n")
            f.write(f"- **평균 정확도**: {summary['exact_match_rate']:.3f}\n")
            f.write(f"- **평균 F1 점수**: {summary['average_f1']:.3f}\n")
            f.write(f"- **총 질문 수**: {summary['total_qa']}개\n\n")
            
            # 카테고리별 성능
            f.write("### 카테고리별 성능\n\n")
            for category, stats in summary["categories"].items():
                f.write(f"- **{category}**: 정확도 {stats['exact_match_rate']:.3f}, F1 {stats['average_f1']:.3f}\n")
            
            # 상세 결과
            f.write("\n## 📈 상세 결과\n\n")
            f.write("### 성공한 QA 쌍\n\n")
            
            successful_results = [r for r in self.results["qa_results"] if r["status"] == "success"]
            for result in successful_results[:10]:  # 처음 10개만
                f.write(f"#### {result['qa_id']}\n\n")
                f.write(f"**질문**: {result['question']}\n\n")
                f.write(f"**예측 답변**: {result['predicted_answer']}\n\n")
                f.write(f"**상태**: ✅ 성공\n\n")
            
            f.write("\n---\n")
            f.write(f"**보고서 생성**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("**벤치마크 버전**: 1.0\n")


def main():
    """메인 함수"""
    base_dir = Path(__file__).parent.parent
    runner = BM25BenchmarkRunner(base_dir)
    
    try:
        runner.initialize_engine()
        runner.run_benchmark()
    except Exception as e:
        print(f"❌ 벤치마크 실행 중 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
