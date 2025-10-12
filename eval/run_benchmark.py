#!/usr/bin/env python3
"""
벤치마크 실행 스크립트

목적:
- Graph-RAG 시스템과 Gold Standard QA 연동
- 자동 평가 파이프라인 실행
- 결과 시각화 및 보고서 생성
"""

import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import networkx as nx

from metrics import EvaluationMetrics
from contextualforget.query import AdvancedQueryEngine
from contextualforget.llm import NaturalLanguageProcessor, LLMQueryEngine


class BenchmarkRunner:
    """벤치마크 실행기"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.eval_dir = self.base_dir / "eval"
        self.graph_path = self.base_dir / "data" / "processed" / "graph.gpickle"
        
        # 컴포넌트 초기화
        self.graph = self._load_graph()
        self.query_engine = None
        self.llm_engine = None
        self.metrics = EvaluationMetrics()
        
        # 결과 저장
        self.results = {
            "timestamp": datetime.now().isoformat(),
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
    
    def initialize_engines(self):
        """쿼리 엔진 초기화"""
        print("\n🔧 쿼리 엔진 초기화 중...")
        
        # Graph-RAG 쿼리 엔진
        self.query_engine = AdvancedQueryEngine(self.graph)
        print("  ✅ Graph-RAG 쿼리 엔진 초기화")
        
        # LLM 자연어 처리 엔진
        try:
            nlp_processor = NaturalLanguageProcessor(model_name="qwen2.5:3b", use_llm=True)
            self.llm_engine = LLMQueryEngine(self.query_engine, nlp_processor)
            print("  ✅ LLM 자연어 처리 엔진 초기화")
        except Exception as e:
            print(f"  ⚠️  LLM 엔진 초기화 실패: {e}")
            print("  🔄 정규식 기반 폴백 모드로 전환")
            nlp_processor = NaturalLanguageProcessor(model_name="qwen2.5:3b", use_llm=False)
            self.llm_engine = LLMQueryEngine(self.query_engine, nlp_processor)
    
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
        qa_id = qa.get('id')
        question = qa.get('question', '')
        ground_truth = qa.get('ground_truth', {})
        
        try:
            # LLM 자연어 쿼리 실행
            result = self.llm_engine.process_natural_query(question)
            
            # 결과 추출
            predicted_answer = result.get('natural_response', '')
            query_results = result.get('query_results', {})
            
            # 소스 추출 (가능한 경우)
            sources = []
            if 'results' in query_results:
                for item in query_results['results']:
                    if 'topic_id' in item:
                        sources.append(item['topic_id'])
                    elif 'guid' in item:
                        sources.append(item['guid'])
            
            return {
                "qa_id": qa_id,
                "question": question,
                "predicted_answer": predicted_answer,
                "sources": sources,
                "query_results": query_results,
                "ground_truth": ground_truth,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "qa_id": qa_id,
                "question": question,
                "predicted_answer": f"Error: {str(e)}",
                "sources": [],
                "query_results": {},
                "ground_truth": ground_truth,
                "status": "error",
                "error": str(e)
            }
    
    def run_benchmark(self, qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """전체 벤치마크 실행"""
        print(f"\n🚀 벤치마크 실행 시작 ({len(qa_pairs)}개 QA)")
        
        results = []
        
        for i, qa in enumerate(qa_pairs):
            print(f"  진행률: {i+1}/{len(qa_pairs)} - {qa.get('id', 'unknown')}")
            
            result = self.run_single_qa(qa)
            results.append(result)
        
        print(f"✅ 벤치마크 완료: {len(results)}개 결과")
        return results
    
    def evaluate_results(self, qa_pairs: List[Dict[str, Any]], predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """결과 평가"""
        print("\n📊 결과 평가 중...")
        
        # 성공한 QA만 평가
        successful_pairs = []
        successful_predictions = []
        
        for qa, pred in zip(qa_pairs, predictions):
            if pred.get('status') == 'success':
                successful_pairs.append(qa)
                successful_predictions.append(pred)
        
        print(f"  평가 대상: {len(successful_pairs)}개 (성공한 QA)")
        
        if not successful_pairs:
            return {"error": "평가할 수 있는 성공한 QA가 없습니다."}
        
        # 메트릭 계산
        evaluation = self.metrics.calculate_answer_accuracy(successful_pairs, successful_predictions)
        
        return evaluation
    
    def generate_report(self, qa_pairs: List[Dict[str, Any]], predictions: List[Dict[str, Any]], evaluation: Dict[str, Any]):
        """보고서 생성"""
        print("\n📝 보고서 생성 중...")
        
        # 그래프 통계
        graph_stats = {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "is_directed": self.graph.is_directed()
        }
        
        # QA 통계
        qa_stats = {
            "total_qa": len(qa_pairs),
            "successful_qa": len([p for p in predictions if p.get('status') == 'success']),
            "failed_qa": len([p for p in predictions if p.get('status') == 'error']),
            "by_category": {}
        }
        
        # 카테고리별 통계
        for qa in qa_pairs:
            category = qa.get('category', 'unknown')
            if category not in qa_stats['by_category']:
                qa_stats['by_category'][category] = 0
            qa_stats['by_category'][category] += 1
        
        # 종합 보고서
        report = {
            "timestamp": datetime.now().isoformat(),
            "graph_statistics": graph_stats,
            "qa_statistics": qa_stats,
            "evaluation_results": evaluation,
            "detailed_results": predictions
        }
        
        # JSON 저장
        report_path = self.eval_dir / "benchmark_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ JSON 보고서: {report_path}")
        
        # Markdown 보고서
        md_path = self.eval_dir / "BENCHMARK_REPORT.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"""# 벤치마크 실행 보고서

**실행 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 그래프 통계

- **노드 수**: {graph_stats['nodes']}개
- **엣지 수**: {graph_stats['edges']}개
- **방향성**: {'Directed' if graph_stats['is_directed'] else 'Undirected'}

## 📋 QA 통계

- **총 QA 쌍**: {qa_stats['total_qa']}개
- **성공한 QA**: {qa_stats['successful_qa']}개
- **실패한 QA**: {qa_stats['failed_qa']}개
- **성공률**: {qa_stats['successful_qa']/qa_stats['total_qa']*100:.1f}%

### 카테고리별 분포

""")
            
            for category, count in qa_stats['by_category'].items():
                f.write(f"- **{category}**: {count}개\n")
            
            f.write(f"""

## 🎯 평가 결과

""")
            
            if 'error' in evaluation:
                f.write(f"**오류**: {evaluation['error']}\n")
            else:
                f.write(f"""
- **평균 정확도**: {evaluation.get('average_accuracy', 0):.3f}
- **평균 F1 점수**: {evaluation.get('average_f1', 0):.3f}
- **총 질문 수**: {evaluation.get('total_questions', 0)}개

### 카테고리별 성능

""")
                
                for category, stats in evaluation.get('by_category', {}).items():
                    f.write(f"- **{category}**: 정확도 {stats.get('accuracy', 0):.3f}, F1 {stats.get('f1', 0):.3f}\n")
                
                f.write(f"""

### 난이도별 성능

""")
                
                for difficulty, stats in evaluation.get('by_difficulty', {}).items():
                    f.write(f"- **{difficulty}**: 정확도 {stats.get('accuracy', 0):.3f}, F1 {stats.get('f1', 0):.3f}\n")
            
            f.write(f"""

## 📈 상세 결과

### 성공한 QA 쌍

""")
            
            for pred in predictions:
                if pred.get('status') == 'success':
                    f.write(f"""
#### {pred.get('qa_id', 'unknown')}

**질문**: {pred.get('question', '')}

**예측 답변**: {pred.get('predicted_answer', '')[:200]}...

**상태**: ✅ 성공

""")
            
            f.write(f"""

### 실패한 QA 쌍

""")
            
            for pred in predictions:
                if pred.get('status') == 'error':
                    f.write(f"""
#### {pred.get('qa_id', 'unknown')}

**질문**: {pred.get('question', '')}

**오류**: {pred.get('error', 'Unknown error')}

**상태**: ❌ 실패

""")
            
            f.write(f"""

---

**보고서 생성**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**벤치마크 버전**: 1.0
""")
        
        print(f"  ✅ Markdown 보고서: {md_path}")
        
        return report
    
    def run_full_benchmark(self):
        """전체 벤치마크 실행"""
        print("=" * 70)
        print("🎯 ContextualForget 벤치마크 실행")
        print("=" * 70)
        
        try:
            # 1. 엔진 초기화
            self.initialize_engines()
            
            # 2. Gold Standard 로드
            qa_pairs = self.load_gold_standard()
            
            # 3. 벤치마크 실행
            predictions = self.run_benchmark(qa_pairs)
            
            # 4. 결과 평가
            evaluation = self.evaluate_results(qa_pairs, predictions)
            
            # 5. 보고서 생성
            report = self.generate_report(qa_pairs, predictions, evaluation)
            
            print("\n" + "=" * 70)
            print("✅ 벤치마크 완료!")
            print("=" * 70)
            
            if 'error' not in evaluation:
                print(f"""
📊 최종 결과:
  - 평균 정확도: {evaluation.get('average_accuracy', 0):.3f}
  - 평균 F1 점수: {evaluation.get('average_f1', 0):.3f}
  - 성공한 QA: {len([p for p in predictions if p.get('status') == 'success'])}개
  - 실패한 QA: {len([p for p in predictions if p.get('status') == 'error'])}개

📂 생성된 파일:
  - eval/benchmark_report.json
  - eval/BENCHMARK_REPORT.md
""")
            else:
                print(f"❌ 평가 실패: {evaluation['error']}")
            
        except Exception as e:
            print(f"❌ 벤치마크 실행 실패: {e}")
            import traceback
            traceback.print_exc()


def main():
    """메인 실행"""
    base_dir = Path(__file__).parent.parent
    runner = BenchmarkRunner(base_dir)
    runner.run_full_benchmark()


if __name__ == "__main__":
    main()

