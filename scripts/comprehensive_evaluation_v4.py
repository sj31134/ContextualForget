"""
종합 평가 시스템 v4 - 개선 버전
- 중간 저장 기능
- 진행 상황 로깅
- 재개 기능
- 예상 완료 시간 표시
"""

import json
import pickle
import sys
import time
from datetime import datetime, timedelta
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


class ComprehensiveEvaluatorV4:
    """종합 RAG 시스템 평가자 v4 - 개선 버전"""
    
    def __init__(self, graph_path: str, gold_standard_path: str, output_dir: str):
        self.graph_path = graph_path
        self.gold_standard_path = gold_standard_path
        self.output_dir = Path(output_dir)
        self.graph = None
        self.engines = {}
        self.gold_standard = []
        self.results = []
        
        # 중간 저장 설정
        self.checkpoint_interval = 10  # 10번마다 저장
        self.checkpoint_file = self.output_dir / 'checkpoint.json'
        self.progress_file = self.output_dir / 'progress.log'
        
        # 성능 추적
        self.start_time = None
        self.evaluation_times = []
        
    def load_graph(self):
        """그래프 로드"""
        print("📊 그래프 로드 중...")
        with open(self.graph_path, 'rb') as f:
            self.graph = pickle.load(f)
        print(f"✅ 그래프 로드 완료: {self.graph.number_of_nodes():,}개 노드, {self.graph.number_of_edges():,}개 엣지")
    
    def load_gold_standard(self, limit: int = None):
        """Gold Standard 로드"""
        print("\n📋 Gold Standard 로드 중...")
        all_data = list(read_jsonl(self.gold_standard_path))
        
        if limit and limit > 0:
            self.gold_standard = all_data[:limit]
            print(f"✅ Gold Standard 로드 완료: {len(self.gold_standard)}개 QA (전체 {len(all_data)}개 중 샘플)")
        else:
            self.gold_standard = all_data
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
    
    def save_checkpoint(self):
        """중간 저장"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_data = {
            'results': self.results,
            'completed_evaluations': len(self.results),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False, default=str)
    
    def load_checkpoint(self) -> bool:
        """체크포인트 로드"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                self.results = checkpoint_data['results']
                print(f"📂 체크포인트 로드: {len(self.results)}개 평가 완료됨")
                return True
        return False
    
    def log_progress(self, current: int, total: int, avg_time: float):
        """진행 상황 로깅"""
        remaining = total - current
        eta_seconds = remaining * avg_time
        eta = timedelta(seconds=int(eta_seconds))
        
        log_message = (
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"진행: {current}/{total} ({current/total*100:.1f}%) | "
            f"평균 속도: {avg_time:.2f}초/평가 | "
            f"예상 완료: {eta}\n"
        )
        
        print(log_message.strip())
        
        # 파일에도 저장
        with open(self.progress_file, 'a') as f:
            f.write(log_message)
    
    def evaluate_all(self, resume: bool = False):
        """전체 평가 실행"""
        print("\n" + "="*60)
        print("📊 전체 평가 시작")
        print("="*60)
        print(f"   Gold Standard: {len(self.gold_standard)}개")
        print(f"   엔진: {len(self.engines)}개")
        print(f"   총 평가 횟수: {len(self.gold_standard) * len(self.engines)}회")
        
        # 재개 여부 확인
        start_idx = 0
        if resume and self.load_checkpoint():
            start_idx = len(self.results) // len(self.engines)
            print(f"   ▶️  {start_idx}번째 질문부터 재개")
        
        print()
        
        total_evaluations = len(self.gold_standard) * len(self.engines)
        self.start_time = time.time()
        self.evaluation_times = []
        
        with tqdm(total=total_evaluations, initial=len(self.results), desc="평가 진행") as pbar:
            for qa_idx, qa in enumerate(self.gold_standard[start_idx:], start=start_idx):
                for engine_name in self.engines.keys():
                    eval_start = time.time()
                    
                    result = self.evaluate_single_query(engine_name, qa)
                    self.results.append(result)
                    
                    # 시간 추적
                    eval_time = time.time() - eval_start
                    self.evaluation_times.append(eval_time)
                    
                    pbar.update(1)
                    
                    # 중간 저장
                    if len(self.results) % self.checkpoint_interval == 0:
                        self.save_checkpoint()
                
                # 진행 상황 로깅 (매 5개 QA마다)
                if (qa_idx + 1) % 5 == 0:
                    avg_time = np.mean(self.evaluation_times[-20:]) if self.evaluation_times else 0
                    self.log_progress(len(self.results), total_evaluations, avg_time)
        
        # 최종 저장
        self.save_checkpoint()
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
    
    def save_results(self):
        """결과 저장"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n💾 결과 저장 중: {self.output_dir}")
        
        # 상세 결과 저장
        detailed_file = self.output_dir / 'evaluation_v4_detailed.json'
        with open(detailed_file, 'w') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        print(f"   ✅ 상세 결과: {detailed_file}")
        
        # 요약 결과
        engine_stats = self.analyze_results()
        summary_file = self.output_dir / 'evaluation_v4_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(engine_stats, f, indent=2, ensure_ascii=False, default=str)
        print(f"   ✅ 요약 결과: {summary_file}")
        
        # CSV 비교 테이블
        import csv
        csv_file = self.output_dir / 'evaluation_v4_comparison.csv'
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
        
        # 체크포인트 삭제
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            print(f"   🗑️  체크포인트 삭제")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='종합 평가 시스템 v4 - 개선 버전')
    parser.add_argument('--graph', default='data/processed/graph.gpickle', help='그래프 파일')
    parser.add_argument('--gold-standard', default='eval/gold_standard_v3.jsonl', help='Gold Standard 파일')
    parser.add_argument('--output', default='results/evaluation_v4', help='출력 디렉토리')
    parser.add_argument('--limit', type=int, default=None, help='샘플 크기 제한 (테스트용)')
    parser.add_argument('--resume', action='store_true', help='중단된 평가 재개')
    args = parser.parse_args()
    
    print("\n" + "🎯 " + "="*58)
    print("   종합 평가 시스템 v4 - 개선 버전")
    print("="*60)
    
    # 평가자 초기화
    evaluator = ComprehensiveEvaluatorV4(args.graph, args.gold_standard, args.output)
    
    # 데이터 로드
    evaluator.load_graph()
    evaluator.load_gold_standard(limit=args.limit)
    
    # 엔진 초기화
    evaluator.initialize_engines()
    
    # 평가 실행
    evaluator.evaluate_all(resume=args.resume)
    
    # 결과 분석 및 저장
    evaluator.save_results()
    
    total_time = time.time() - evaluator.start_time
    print("\n" + "="*60)
    print(f"✅ 종합 평가 v4 완료!")
    print(f"   총 소요 시간: {timedelta(seconds=int(total_time))}")
    print("="*60)


if __name__ == "__main__":
    main()

