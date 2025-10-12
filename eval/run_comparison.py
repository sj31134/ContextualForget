#!/usr/bin/env python3
"""
3개 시스템 비교 실험 스크립트
- Graph-RAG vs BM25 vs Vector RAG
"""

import sys
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from contextualforget.baselines import BM25QueryEngine, VectorQueryEngine
from contextualforget.query import AdvancedQueryEngine
from contextualforget.llm import NaturalLanguageProcessor, LLMQueryEngine
from metrics import EvaluationMetrics


class SystemComparisonRunner:
    """3개 시스템 비교 실험 실행기"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.eval_dir = self.base_dir / "eval"
        self.graph_path = self.base_dir / "data" / "processed" / "graph.gpickle"
        
        # 컴포넌트 초기화
        self.graph = self._load_graph()
        self.graph_rag_engine = None
        self.bm25_engine = None
        self.vector_engine = None
        self.metrics = EvaluationMetrics()
        
        # 결과 저장
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "systems": ["Graph-RAG", "BM25", "Vector"],
            "graph_stats": {},
            "comparison_results": [],
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
    
    def initialize_engines(self):
        """모든 엔진 초기화"""
        print("\n🔧 모든 엔진 초기화 중...")
        
        # Prepare graph data
        graph_data = {"nodes": list(self.graph.nodes(data=True))}
        
        # 1. Graph-RAG 엔진 초기화
        print("  📊 Graph-RAG 엔진 초기화...")
        self.graph_rag_engine = AdvancedQueryEngine(self.graph)
        try:
            nlp_processor = NaturalLanguageProcessor(model_name="qwen2.5:3b", use_llm=True)
            self.graph_rag_engine = LLMQueryEngine(self.graph_rag_engine, nlp_processor)
            print("    ✅ Graph-RAG 엔진 초기화 완료")
        except Exception as e:
            print(f"    ⚠️ Graph-RAG LLM 초기화 실패: {e}")
            print("    🔄 정규식 기반 폴백 모드로 전환")
            nlp_processor = NaturalLanguageProcessor(model_name="qwen2.5:3b", use_llm=False)
            self.graph_rag_engine = LLMQueryEngine(self.graph_rag_engine, nlp_processor)
        
        # 2. BM25 엔진 초기화
        print("  🔍 BM25 엔진 초기화...")
        self.bm25_engine = BM25QueryEngine()
        self.bm25_engine.initialize(graph_data)
        print("    ✅ BM25 엔진 초기화 완료")
        
        # 3. Vector RAG 엔진 초기화
        print("  🧠 Vector RAG 엔진 초기화...")
        self.vector_engine = VectorQueryEngine()
        self.vector_engine.initialize(graph_data)
        print("    ✅ Vector RAG 엔진 초기화 완료")
    
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
    
    def run_single_qa_comparison(self, qa: Dict[str, Any]) -> Dict[str, Any]:
        """단일 QA에 대해 3개 시스템 비교 실행"""
        qa_id = qa.get('qa_id', 'unknown')
        question = qa.get('question', '')
        ground_truth = qa.get('ground_truth', {})
        
        results = {
            "qa_id": qa_id,
            "question": question,
            "ground_truth": ground_truth,
            "systems": {}
        }
        
        # 1. Graph-RAG 실행
        try:
            graph_result = self.graph_rag_engine.process_natural_query(question)
            graph_answer = graph_result.get('answer', '')
            graph_confidence = graph_result.get('confidence', 0.0)
            graph_metrics = self.metrics.calculate_answer_accuracy(graph_answer, ground_truth)
            
            results["systems"]["Graph-RAG"] = {
                "answer": graph_answer,
                "confidence": graph_confidence,
                "metrics": graph_metrics,
                "status": "success"
            }
        except Exception as e:
            results["systems"]["Graph-RAG"] = {
                "answer": "",
                "confidence": 0.0,
                "metrics": {"exact_match": 0.0, "f1_score": 0.0, "semantic_match": 0.0},
                "status": "error",
                "error": str(e)
            }
        
        # 2. BM25 실행
        try:
            bm25_result = self.bm25_engine.process_query(question)
            bm25_answer = bm25_result.get('answer', '')
            bm25_confidence = bm25_result.get('confidence', 0.0)
            bm25_metrics = self._calculate_baseline_metrics(bm25_answer, ground_truth)
            
            results["systems"]["BM25"] = {
                "answer": bm25_answer,
                "confidence": bm25_confidence,
                "metrics": bm25_metrics,
                "status": "success"
            }
        except Exception as e:
            results["systems"]["BM25"] = {
                "answer": "",
                "confidence": 0.0,
                "metrics": {"exact_match": 0.0, "f1_score": 0.0, "semantic_match": 0.0},
                "status": "error",
                "error": str(e)
            }
        
        # 3. Vector RAG 실행
        try:
            vector_result = self.vector_engine.process_query(question)
            vector_answer = vector_result.get('answer', '')
            vector_confidence = vector_result.get('confidence', 0.0)
            vector_metrics = self._calculate_baseline_metrics(vector_answer, ground_truth)
            
            results["systems"]["Vector"] = {
                "answer": vector_answer,
                "confidence": vector_confidence,
                "metrics": vector_metrics,
                "status": "success"
            }
        except Exception as e:
            results["systems"]["Vector"] = {
                "answer": "",
                "confidence": 0.0,
                "metrics": {"exact_match": 0.0, "f1_score": 0.0, "semantic_match": 0.0},
                "status": "error",
                "error": str(e)
            }
        
        return results
    
    def _calculate_baseline_metrics(self, predicted_answer: str, ground_truth: Dict[str, Any]) -> Dict[str, float]:
        """베이스라인 시스템 답변에 대한 메트릭 계산"""
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
    
    def run_comparison(self):
        """비교 실험 실행"""
        print("\n🚀 3개 시스템 비교 실험 시작")
        print("=" * 60)
        
        # Gold Standard 로드
        qa_pairs = self.load_gold_standard()
        
        # 비교 실험 실행
        print(f"\n🎯 비교 실험 실행 시작 ({len(qa_pairs)}개 QA)")
        
        for i, qa in enumerate(qa_pairs, 1):
            print(f"  진행률: {i}/{len(qa_pairs)} - {qa.get('qa_id', 'unknown')}")
            
            result = self.run_single_qa_comparison(qa)
            self.results["comparison_results"].append(result)
        
        print(f"✅ 비교 실험 완료: {len(self.results['comparison_results'])}개 결과")
        
        # 결과 분석
        self._analyze_results()
        
        # 보고서 생성
        self._generate_report()
    
    def _analyze_results(self):
        """결과 분석"""
        print("\n📊 결과 분석 중...")
        
        results = self.results["comparison_results"]
        
        # 시스템별 통계
        system_stats = {
            "Graph-RAG": {"total": 0, "success": 0, "exact_matches": 0, "f1_scores": [], "semantic_scores": []},
            "BM25": {"total": 0, "success": 0, "exact_matches": 0, "f1_scores": [], "semantic_scores": []},
            "Vector": {"total": 0, "success": 0, "exact_matches": 0, "f1_scores": [], "semantic_scores": []}
        }
        
        # 카테고리별 통계
        category_stats = {
            "entity_search": {"Graph-RAG": [], "BM25": [], "Vector": []},
            "temporal": {"Graph-RAG": [], "BM25": [], "Vector": []},
            "forgetting": {"Graph-RAG": [], "BM25": [], "Vector": []},
            "complex": {"Graph-RAG": [], "BM25": [], "Vector": []}
        }
        
        for result in results:
            qa_id = result["qa_id"]
            
            # 카테고리 추출
            category = "unknown"
            if "entity" in qa_id:
                category = "entity_search"
            elif "temporal" in qa_id:
                category = "temporal"
            elif "forgetting" in qa_id:
                category = "forgetting"
            elif "complex" in qa_id:
                category = "complex"
            
            # 각 시스템별 통계 계산
            for system_name in ["Graph-RAG", "BM25", "Vector"]:
                system_result = result["systems"][system_name]
                system_stats[system_name]["total"] += 1
                
                if system_result["status"] == "success":
                    system_stats[system_name]["success"] += 1
                    metrics = system_result["metrics"]
                    
                    if metrics["exact_match"] > 0:
                        system_stats[system_name]["exact_matches"] += 1
                    
                    system_stats[system_name]["f1_scores"].append(metrics["f1_score"])
                    system_stats[system_name]["semantic_scores"].append(metrics["semantic_match"])
                    
                    # 카테고리별 통계
                    if category in category_stats:
                        category_stats[category][system_name].append(metrics["f1_score"])
        
        # 요약 통계 계산
        summary = {
            "total_qa": len(results),
            "systems": {}
        }
        
        for system_name, stats in system_stats.items():
            total = stats["total"]
            success = stats["success"]
            
            summary["systems"][system_name] = {
                "success_rate": success / total if total > 0 else 0,
                "exact_match_rate": stats["exact_matches"] / total if total > 0 else 0,
                "average_f1": sum(stats["f1_scores"]) / len(stats["f1_scores"]) if stats["f1_scores"] else 0,
                "average_semantic": sum(stats["semantic_scores"]) / len(stats["semantic_scores"]) if stats["semantic_scores"] else 0,
                "total_qa": total,
                "successful_qa": success
            }
        
        # 카테고리별 요약
        summary["categories"] = {}
        for category, systems in category_stats.items():
            summary["categories"][category] = {}
            for system_name, scores in systems.items():
                summary["categories"][category][system_name] = {
                    "count": len(scores),
                    "average_f1": sum(scores) / len(scores) if scores else 0
                }
        
        self.results["summary"] = summary
    
    def _generate_report(self):
        """보고서 생성"""
        print("\n📝 보고서 생성 중...")
        
        # JSON 보고서
        json_path = self.eval_dir / "comparison_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"  ✅ JSON 보고서: {json_path}")
        
        # Markdown 보고서
        md_path = self.eval_dir / "COMPARISON_REPORT.md"
        self._generate_markdown_report(md_path)
        print(f"  ✅ Markdown 보고서: {md_path}")
        
        # 최종 결과 출력
        summary = self.results["summary"]
        print(f"\n======================================================================")
        print(f"✅ 3개 시스템 비교 실험 완료!")
        print(f"======================================================================")
        
        print(f"\n📊 최종 결과 요약:")
        for system_name, stats in summary["systems"].items():
            print(f"\n🔹 {system_name}:")
            print(f"  - 성공률: {stats['success_rate']:.3f}")
            print(f"  - 정확도: {stats['exact_match_rate']:.3f}")
            print(f"  - 평균 F1: {stats['average_f1']:.3f}")
            print(f"  - 성공한 QA: {stats['successful_qa']}/{stats['total_qa']}")
        
        print(f"\n📂 생성된 파일:")
        print(f"  - {json_path}")
        print(f"  - {md_path}")
    
    def _generate_markdown_report(self, output_path: Path):
        """Markdown 보고서 생성"""
        summary = self.results["summary"]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 3개 시스템 비교 실험 보고서\n\n")
            f.write(f"**실행 일시**: {self.results['timestamp']}\n\n")
            
            # 그래프 통계
            f.write("## 📊 그래프 통계\n\n")
            f.write(f"- **노드 수**: {self.graph.number_of_nodes()}개\n")
            f.write(f"- **엣지 수**: {self.graph.number_of_edges()}개\n")
            f.write(f"- **방향성**: Directed\n\n")
            
            # QA 통계
            f.write("## 📋 QA 통계\n\n")
            f.write(f"- **총 QA 쌍**: {summary['total_qa']}개\n\n")
            
            # 시스템별 성능 비교
            f.write("## 🎯 시스템별 성능 비교\n\n")
            f.write("| 시스템 | 성공률 | 정확도 | 평균 F1 | 성공한 QA |\n")
            f.write("|--------|--------|--------|---------|----------|\n")
            
            for system_name, stats in summary["systems"].items():
                f.write(f"| {system_name} | {stats['success_rate']:.3f} | {stats['exact_match_rate']:.3f} | {stats['average_f1']:.3f} | {stats['successful_qa']}/{stats['total_qa']} |\n")
            
            # 카테고리별 성능
            f.write("\n## 📈 카테고리별 성능\n\n")
            for category, systems in summary["categories"].items():
                f.write(f"### {category}\n\n")
                f.write("| 시스템 | QA 수 | 평균 F1 |\n")
                f.write("|--------|--------|----------|\n")
                
                for system_name, stats in systems.items():
                    f.write(f"| {system_name} | {stats['count']} | {stats['average_f1']:.3f} |\n")
                f.write("\n")
            
            # 상세 결과 샘플
            f.write("## 📋 상세 결과 샘플\n\n")
            f.write("### 처음 5개 QA 비교\n\n")
            
            for i, result in enumerate(self.results["comparison_results"][:5]):
                f.write(f"#### {result['qa_id']}\n\n")
                f.write(f"**질문**: {result['question']}\n\n")
                
                for system_name, system_result in result["systems"].items():
                    f.write(f"**{system_name}**:\n")
                    f.write(f"- 답변: {system_result['answer']}\n")
                    f.write(f"- 신뢰도: {system_result['confidence']:.3f}\n")
                    f.write(f"- F1 점수: {system_result['metrics']['f1_score']:.3f}\n")
                    f.write(f"- 상태: {'✅ 성공' if system_result['status'] == 'success' else '❌ 실패'}\n\n")
                
                f.write("---\n\n")
            
            f.write("\n---\n")
            f.write(f"**보고서 생성**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("**실험 버전**: 1.0\n")


def main():
    """메인 함수"""
    base_dir = Path(__file__).parent.parent
    runner = SystemComparisonRunner(base_dir)
    
    try:
        runner.initialize_engines()
        runner.run_comparison()
    except Exception as e:
        print(f"❌ 비교 실험 실행 중 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
