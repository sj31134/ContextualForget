#!/usr/bin/env python3
"""
실제 데이터 기반 평가 테스트
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.baselines.bm25_engine import BM25QueryEngine
from contextualforget.baselines.vector_engine import VectorQueryEngine
from contextualforget.query.contextual_forget_engine import ContextualForgetEngine
from contextualforget.query.adaptive_retrieval import HybridRetrievalEngine
from contextualforget.core.utils import read_jsonl
import pickle
import networkx as nx


def load_real_data_graph():
    """실제 데이터 기반 그래프 로드"""
    
    graph_file = Path("data/processed/real_graph/real_data_graph.pkl")
    if not graph_file.exists():
        raise FileNotFoundError(f"그래프 파일을 찾을 수 없습니다: {graph_file}")
    
    with open(graph_file, 'rb') as f:
        graph = pickle.load(f)
    
    print(f"✅ 그래프 로드 완료: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 연결")
    return graph


def initialize_engines_with_real_data():
    """실제 데이터로 엔진들 초기화"""
    
    print("🔧 실제 데이터 기반 엔진 초기화 중...")
    
    # 그래프 로드
    graph = load_real_data_graph()
    
    # 그래프 데이터 구조 생성
    graph_data = {
        'graph': graph,
        'nodes': list(graph.nodes(data=True))
    }
    
    engines = {}
    
    try:
        # BM25 엔진 초기화
        print("  🔍 BM25 엔진 초기화...")
        bm25_engine = BM25QueryEngine("BM25")
        bm25_engine.initialize(graph_data)
        engines['BM25'] = bm25_engine
        print("    ✅ BM25 엔진 초기화 완료")
        
    except Exception as e:
        print(f"    ❌ BM25 엔진 초기화 실패: {e}")
    
    try:
        # Vector 엔진 초기화
        print("  🔍 Vector 엔진 초기화...")
        vector_engine = VectorQueryEngine("Vector")
        vector_engine.initialize(graph_data)
        engines['Vector'] = vector_engine
        print("    ✅ Vector 엔진 초기화 완료")
        
    except Exception as e:
        print(f"    ❌ Vector 엔진 초기화 실패: {e}")
    
    try:
        # ContextualForget 엔진 초기화
        print("  🔍 ContextualForget 엔진 초기화...")
        cf_engine = ContextualForgetEngine(graph)
        engines['ContextualForget'] = cf_engine
        print("    ✅ ContextualForget 엔진 초기화 완료")
        
    except Exception as e:
        print(f"    ❌ ContextualForget 엔진 초기화 실패: {e}")
    
    try:
        # Hybrid 엔진 초기화
        print("  🔍 Hybrid 엔진 초기화...")
        if 'ContextualForget' in engines:
            # Hybrid 엔진은 딕셔너리 형태의 base_engines를 기대함
            base_engines = {
                'ContextualForget': engines['ContextualForget']
            }
            # BM25 엔진이 있으면 추가
            if 'BM25' in engines:
                base_engines['BM25'] = engines['BM25']
            
            hybrid_engine = HybridRetrievalEngine(base_engines)
            engines['Hybrid'] = hybrid_engine
            print("    ✅ Hybrid 엔진 초기화 완료")
        
    except Exception as e:
        print(f"    ❌ Hybrid 엔진 초기화 실패: {e}")
    
    print(f"✅ 총 {len(engines)}개 엔진 초기화 완료")
    return engines


def test_engines_with_real_gold_standard():
    """실제 데이터 기반 Gold Standard로 엔진 테스트"""
    
    print("🧪 실제 데이터 기반 Gold Standard 테스트 시작...")
    
    # 1. 엔진 초기화
    engines = initialize_engines_with_real_data()
    
    # 2. Gold Standard 로드
    gold_standard_file = Path("eval/gold_standard_real_data.jsonl")
    if not gold_standard_file.exists():
        print("❌ 실제 데이터 기반 Gold Standard 파일을 찾을 수 없습니다.")
        return
    
    gold_standard = list(read_jsonl(str(gold_standard_file)))
    print(f"📊 로드된 Gold Standard 질문: {len(gold_standard)}개")
    
    # 3. 테스트 실행 (처음 10개만)
    test_questions = gold_standard[:10]
    print(f"🔬 테스트 질문 수: {len(test_questions)}개")
    
    results = {}
    
    for engine_name, engine in engines.items():
        print(f"\n🔍 {engine_name} 엔진 테스트 중...")
        
        engine_results = []
        start_time = time.time()
        
        for i, qa in enumerate(test_questions):
            try:
                question = qa['question']
                print(f"  📝 질문 {i+1}: {question[:50]}...")
                
                # 엔진별 쿼리 처리
                if engine_name == 'ContextualForget':
                    result = engine.contextual_query(question)
                elif engine_name == 'Hybrid':
                    result = engine.query(question)
                else:
                    result = engine.process_query(question)
                
                # 결과 분석
                result_analysis = {
                    'question_id': i,
                    'question': question,
                    'gold_entities': qa.get('gold_entities', []),
                    'result': result,
                    'success': False,
                    'entities_found': len(result.get('entities', [])),
                    'confidence': result.get('confidence', 0.0)
                }
                
                # 성공 여부 판단 (간단한 기준)
                if result.get('entities') and qa.get('gold_entities'):
                    retrieved_entities = set(result.get('entities', []))
                    gold_entities = set(qa.get('gold_entities', []))
                    overlap = len(retrieved_entities.intersection(gold_entities))
                    if overlap > 0:
                        result_analysis['success'] = True
                        result_analysis['overlap_count'] = overlap
                
                engine_results.append(result_analysis)
                
                print(f"    📊 결과: {result_analysis['entities_found']}개 엔티티, 신뢰도 {result_analysis['confidence']:.3f}, 성공: {result_analysis['success']}")
                
            except Exception as e:
                print(f"    ❌ 오류: {e}")
                engine_results.append({
                    'question_id': i,
                    'question': question,
                    'error': str(e),
                    'success': False
                })
        
        end_time = time.time()
        
        # 엔진별 통계 계산
        successful_queries = sum(1 for r in engine_results if r.get('success', False))
        total_queries = len(engine_results)
        success_rate = successful_queries / total_queries if total_queries > 0 else 0
        
        avg_confidence = sum(r.get('confidence', 0) for r in engine_results) / total_queries if total_queries > 0 else 0
        avg_entities = sum(r.get('entities_found', 0) for r in engine_results) / total_queries if total_queries > 0 else 0
        
        results[engine_name] = {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'success_rate': success_rate,
            'avg_confidence': avg_confidence,
            'avg_entities_found': avg_entities,
            'execution_time': end_time - start_time,
            'detailed_results': engine_results
        }
        
        print(f"  📈 {engine_name} 결과:")
        print(f"    성공률: {success_rate:.1%}")
        print(f"    평균 신뢰도: {avg_confidence:.3f}")
        print(f"    평균 엔티티 수: {avg_entities:.1f}")
        print(f"    실행 시간: {end_time - start_time:.2f}초")
    
    # 4. 결과 저장
    results_file = Path("data/analysis/real_data_test_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 테스트 결과 저장: {results_file}")
    
    # 5. 요약 출력
    print("\n" + "="*60)
    print("📊 실제 데이터 기반 테스트 결과 요약")
    print("="*60)
    
    for engine_name, stats in results.items():
        print(f"\n🔍 {engine_name}:")
        print(f"  성공률: {stats['success_rate']:.1%}")
        print(f"  평균 신뢰도: {stats['avg_confidence']:.3f}")
        print(f"  평균 엔티티 수: {stats['avg_entities_found']:.1f}")
        print(f"  실행 시간: {stats['execution_time']:.2f}초")
    
    return results


def main():
    """메인 실행 함수"""
    print("🚀 실제 데이터 기반 평가 테스트 시작")
    print("="*60)
    
    try:
        results = test_engines_with_real_gold_standard()
        
        print("\n" + "="*60)
        print("🎉 실제 데이터 기반 평가 테스트 완료!")
        
        # 주요 개선사항 확인
        print("\n📈 주요 개선사항:")
        for engine_name, stats in results.items():
            if stats['success_rate'] > 0:
                print(f"  ✅ {engine_name}: {stats['success_rate']:.1%} 성공률 달성!")
            else:
                print(f"  ⚠️ {engine_name}: 여전히 0% 성공률")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
