"""
종합 평가 시스템 v3
200개 Gold Standard QA로 4개 엔진 800회 평가
"""

import json
import pickle
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
from tqdm import tqdm

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.query.contextual_forget_engine import ContextualForgetEngine
from contextualforget.query.adaptive_retrieval import HybridRetrievalEngine
from contextualforget.baselines.bm25_engine import BM25QueryEngine
from contextualforget.baselines.vector_engine import VectorQueryEngine
from contextualforget.core.utils import read_jsonl

# metrics_v2 임포트
sys.path.insert(0, str(Path(__file__).parent.parent / 'eval'))
from metrics_v2 import EvaluationMetricsV2


class ComprehensiveEvaluatorV3:
    """종합 RAG 시스템 평가자 v3"""
    
    def __init__(self, graph_path: str, gold_standard_path: str):
        self.graph_path = graph_path
        self.gold_standard_path = gold_standard_path
        self.graph = None
        self.engines = {}
        self.gold_standard = []
        self.results = []
        
    def load_graph(self):
        """그래프 로드"""
        print("📊 그래프 로드 중...")
        with open(self.graph_path, 'rb') as f:
            self.graph = pickle.load(f)
        print(f"✅ 그래프 로드 완료: {self.graph.number_of_nodes():,}개 노드, {self.graph.number_of_edges():,}개 엣지")
    
    def load_gold_standard(self):
        """Gold Standard 로드"""
        print("\n📋 Gold Standard 로드 중...")
        self.gold_standard = list(read_jsonl(self.gold_standard_path))
        print(f"✅ Gold Standard 로드 완료: {len(self.gold_standard)}개 QA")
    
    def initialize_engines(self):
        """모든 엔진 초기화"""
        print("\n🔧 엔진들 초기화 중...")
        
        # 데이터 추출
        bcf_data = []
        ifc_data = []
        for node, data in self.graph.nodes(data=True):
            if isinstance(node, tuple):
                if node[0] == 'BCF':
                    bcf_data.append(data)
                elif node[0] == 'IFC':
                    ifc_data.append(data)
        
        print(f"   📋 BCF 데이터: {len(bcf_data)}개")
        print(f"   📋 IFC 데이터: {len(ifc_data)}개")
        
        # BM25 엔진
        print("   🔍 BM25 엔진 초기화...")
        bm25_engine = BM25QueryEngine()
        bm25_engine.initialize({'bcf_data': bcf_data, 'ifc_data': ifc_data, 'graph': self.graph})
        self.engines['BM25'] = bm25_engine
        
        # Vector 엔진
        print("   🔍 Vector 엔진 초기화...")
        vector_engine = VectorQueryEngine()
        vector_engine.initialize({
            'bcf_data': bcf_data,
            'ifc_data': ifc_data,
            'graph': self.graph
        })
        self.engines['Vector'] = vector_engine
        
        # ContextualForget 엔진
        print("   🔍 ContextualForget 엔진 초기화...")
        contextual_engine = ContextualForgetEngine(
            self.graph, 
            enable_contextual_forgetting=True
        )
        self.engines['ContextualForget'] = contextual_engine
        
        # 하이브리드 엔진
        print("   🔍 하이브리드 엔진 초기화...")
        hybrid_engine = HybridRetrievalEngine(
            base_engines={
                'BM25': bm25_engine,
                'Vector': vector_engine,
                'ContextualForget': contextual_engine
            },
            fusion_strategy='basic',
            enable_adaptation=False
        )
        self.engines['Hybrid'] = hybrid_engine
        
        print("✅ 모든 엔진 초기화 완료")
    
    def evaluate_single_query(self, engine_name: str, qa: Dict[str, Any]) -> Dict[str, Any]:
        """단일 쿼리 평가"""
        engine = self.engines[engine_name]
        question = qa['question']
        
        try:
            # 쿼리 실행
            start_time = time.perf_counter()
            
            if engine_name == 'ContextualForget':
                result = engine.contextual_query(question)
            elif engine_name == 'Hybrid':
                result = engine.query(question)
            else:
                result = engine.process_query(question)
            
            response_time = max(time.perf_counter() - start_time, 0.0001)
            
            # 표준 형식 검증 및 보정
            if 'entities' not in result:
                # details나 results에서 entities 추출 시도
                result['entities'] = []
                if 'details' in result and 'results' in result['details']:
                    for doc in result['details']['results']:
                        entity_id = doc.get('doc_id') or doc.get('topic_id') or doc.get('guid', '')
                        if entity_id:
                            result['entities'].append(entity_id)
            
            if 'result_count' not in result:
                result['result_count'] = len(result.get('entities', []))
            
            if 'confidence' not in result:
                result['confidence'] = 0.0
            
            # 메트릭 계산
            metrics = EvaluationMetricsV2.compute_metrics(result, qa)
            metrics['response_time'] = response_time
            
            return {
                'qa_id': qa.get('id', ''),
                'question': question,
                'category': qa.get('category', 'unknown'),
                'engine': engine_name,
                'result': result,
                'metrics': metrics,
                'status': 'success'
            }
            
        except Exception as e:
            print(f"      ⚠️  {engine_name} 오류: {str(e)[:50]}")
            return {
                'qa_id': qa.get('id', ''),
                'question': question,
                'category': qa.get('category', 'unknown'),
                'engine': engine_name,
                'result': {},
                'metrics': {
                    'success': False,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1': 0.0,
                    'ndcg@10': 0.0,
                    'mrr': 0.0,
                    'confidence': 0.0,
                    'response_time': 0.0,
                    'result_count': 0
                },
                'status': 'error',
                'error': str(e)
            }
    
    def evaluate_all(self):
        """전체 평가 실행"""
        print("\n" + "="*60)
        print("📊 전체 평가 시작")
        print("="*60)
        print(f"   Gold Standard: {len(self.gold_standard)}개")
        print(f"   엔진: {len(self.engines)}개")
        print(f"   총 평가 횟수: {len(self.gold_standard) * len(self.engines)}회")
        print()
        
        total_evaluations = len(self.gold_standard) * len(self.engines)
        
        with tqdm(total=total_evaluations, desc="평가 진행") as pbar:
            for qa in self.gold_standard:
                for engine_name in self.engines.keys():
                    result = self.evaluate_single_query(engine_name, qa)
                    self.results.append(result)
                    pbar.update(1)
        
        print("\n✅ 전체 평가 완료")
    
    def analyze_results(self):
        """결과 분석"""
        print("\n" + "="*60)
        print("📈 결과 분석")
        print("="*60)
        
        # 엔진별 집계
        engine_stats = {}
        
        for engine_name in self.engines.keys():
            engine_results = [r for r in self.results if r['engine'] == engine_name]
            
            if not engine_results:
                continue
            
            # 메트릭 집계
            metrics_list = [r['metrics'] for r in engine_results]
            aggregated = EvaluationMetricsV2.aggregate_metrics(metrics_list)
            
            # 성공/실패 카운트
            success_count = sum(1 for r in engine_results if r['status'] == 'success')
            error_count = sum(1 for r in engine_results if r['status'] == 'error')
            
            engine_stats[engine_name] = {
                'total_queries': len(engine_results),
                'success_count': success_count,
                'error_count': error_count,
                'aggregated_metrics': aggregated
            }
        
        # 출력
        print("\n엔진별 성능:")
        print("-" * 60)
        
        for engine_name, stats in engine_stats.items():
            print(f"\n{engine_name}:")
            print(f"  성공: {stats['success_count']}/{stats['total_queries']}")
            print(f"  오류: {stats['error_count']}/{stats['total_queries']}")
            
            if 'aggregated_metrics' in stats and stats['aggregated_metrics']:
                agg = stats['aggregated_metrics']
                print(f"  성공률: {agg.get('success_rate_rate', 0.0):.2%}")
                print(f"  평균 F1: {agg.get('avg_f1', 0.0):.3f}")
                print(f"  평균 Precision: {agg.get('avg_precision', 0.0):.3f}")
                print(f"  평균 Recall: {agg.get('avg_recall', 0.0):.3f}")
                print(f"  평균 NDCG@10: {agg.get('avg_ndcg@10', 0.0):.3f}")
                print(f"  평균 MRR: {agg.get('avg_mrr', 0.0):.3f}")
                print(f"  평균 신뢰도: {agg.get('avg_confidence', 0.0):.3f}")
                print(f"  평균 응답시간: {agg.get('avg_response_time', 0.0):.4f}초")
        
        return engine_stats
    
    def save_results(self, output_dir: str):
        """결과 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n💾 결과 저장 중: {output_dir}")
        
        # 상세 결과 저장
        detailed_file = output_path / 'evaluation_v3_detailed.json'
        with open(detailed_file, 'w') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        print(f"   ✅ 상세 결과: {detailed_file}")
        
        # 요약 결과
        engine_stats = self.analyze_results()
        summary_file = output_path / 'evaluation_v3_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(engine_stats, f, indent=2, ensure_ascii=False, default=str)
        print(f"   ✅ 요약 결과: {summary_file}")
        
        # CSV 비교 테이블
        import csv
        csv_file = output_path / 'evaluation_v3_comparison.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Engine', 'Success Rate', 'F1', 'Precision', 'Recall', 
                           'NDCG@10', 'MRR', 'Confidence', 'Response Time (s)'])
            
            for engine_name, stats in engine_stats.items():
                if 'aggregated_metrics' in stats and stats['aggregated_metrics']:
                    agg = stats['aggregated_metrics']
                    writer.writerow([
                        engine_name,
                        f"{agg.get('success_rate_rate', 0.0):.2%}",
                        f"{agg.get('avg_f1', 0.0):.3f}",
                        f"{agg.get('avg_precision', 0.0):.3f}",
                        f"{agg.get('avg_recall', 0.0):.3f}",
                        f"{agg.get('avg_ndcg@10', 0.0):.3f}",
                        f"{agg.get('avg_mrr', 0.0):.3f}",
                        f"{agg.get('avg_confidence', 0.0):.3f}",
                        f"{agg.get('avg_response_time', 0.0):.4f}"
                    ])
        print(f"   ✅ CSV 비교: {csv_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='종합 평가 시스템 v3')
    parser.add_argument('--graph', default='data/processed/graph.gpickle', help='그래프 파일')
    parser.add_argument('--gold-standard', default='eval/gold_standard_v3.jsonl', help='Gold Standard 파일')
    parser.add_argument('--output', default='results/evaluation_v3', help='출력 디렉토리')
    args = parser.parse_args()
    
    print("\n" + "🎯 " + "="*58)
    print("   종합 평가 시스템 v3")
    print("="*60)
    
    # 평가자 초기화
    evaluator = ComprehensiveEvaluatorV3(args.graph, args.gold_standard)
    
    # 데이터 로드
    evaluator.load_graph()
    evaluator.load_gold_standard()
    
    # 엔진 초기화
    evaluator.initialize_engines()
    
    # 평가 실행
    evaluator.evaluate_all()
    
    # 결과 분석 및 저장
    evaluator.save_results(args.output)
    
    print("\n" + "="*60)
    print("✅ 종합 평가 v3 완료!")
    print("="*60)


if __name__ == "__main__":
    main()

