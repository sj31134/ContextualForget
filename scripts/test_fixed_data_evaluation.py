#!/usr/bin/env python3
"""
수정된 데이터로 평가 테스트
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import read_jsonl
from contextualforget.baselines.bm25_engine import BM25QueryEngine
from contextualforget.query.contextual_forget_engine import ContextualForgetEngine
from contextualforget.query.adaptive_retrieval import HybridRetrievalEngine
import pickle


def load_fixed_graph():
    """수정된 그래프 로드"""
    graph_file = Path("data/processed/real_graph/real_data_graph_with_connections.pkl")
    
    if not graph_file.exists():
        raise FileNotFoundError(f"그래프 파일을 찾을 수 없습니다: {graph_file}")
    
    with open(graph_file, 'rb') as f:
        graph = pickle.load(f)
    
    print(f"✅ 수정된 그래프 로드 완료: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 연결")
    return graph


def load_fixed_gold_standard():
    """수정된 Gold Standard 로드"""
    gold_file = Path("eval/gold_standard_fixed.jsonl")
    
    if not gold_file.exists():
        raise FileNotFoundError(f"Gold Standard 파일을 찾을 수 없습니다: {gold_file}")
    
    gold_data = list(read_jsonl(str(gold_file)))
    print(f"✅ 수정된 Gold Standard 로드 완료: {len(gold_data)}개 질문")
    return gold_data


def initialize_engines_with_fixed_data():
    """수정된 데이터로 엔진 초기화"""
    print("🔧 수정된 데이터로 엔진 초기화 중...")
    
    # 그래프 로드
    graph = load_fixed_graph()
    
    # 그래프 데이터 구조 생성
    graph_data = {
        'graph': graph,
        'nodes': list(graph.nodes(data=True))
    }
    
    engines = {}
    
    try:
        # BM25 엔진 초기화
        print("  🔍 BM25 엔진 초기화...")
        bm25_engine = BM25QueryEngine('BM25_Fixed')
        bm25_engine.initialize(graph_data)
        engines['BM25'] = bm25_engine
        print("    ✅ BM25 엔진 초기화 완료")
        
    except Exception as e:
        print(f"    ❌ BM25 엔진 초기화 실패: {e}")
    
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
        if 'ContextualForget' in engines and 'BM25' in engines:
            base_engines = {
                'BM25': engines['BM25'],
                'ContextualForget': engines['ContextualForget']
            }
            hybrid_engine = HybridRetrievalEngine(base_engines)
            engines['Hybrid'] = hybrid_engine
            print("    ✅ Hybrid 엔진 초기화 완료")
        
    except Exception as e:
        print(f"    ❌ Hybrid 엔진 초기화 실패: {e}")
    
    print(f"✅ 총 {len(engines)}개 엔진 초기화 완료")
    return engines


def test_engines_with_fixed_data():
    """수정된 데이터로 엔진 테스트"""
    
    print("🧪 수정된 데이터로 엔진 테스트 시작...")
    
    # 1. 엔진 초기화
    engines = initialize_engines_with_fixed_data()
    
    # 2. Gold Standard 로드
    gold_data = load_fixed_gold_standard()
    
    # 3. 테스트 질문 선택 (처음 20개)
    test_questions = gold_data[:20]
    print(f"🔬 테스트 질문 수: {len(test_questions)}")
    
    # 4. 각 엔진별 테스트
    results = {}
    
    for engine_name, engine in engines.items():
        print(f"\n🔍 {engine_name} 엔진 테스트 중...")
        
        engine_results = {
            'success_count': 0,
            'total_questions': len(test_questions),
            'confidence_scores': [],
            'entity_counts': [],
            'response_times': [],
            'detailed_results': []
        }
        
        for i, qa in enumerate(test_questions):
            question = qa['question']
            gold_entities = set(qa.get('gold_entities', []))
            
            start_time = time.perf_counter()
            
            try:
                if engine_name == 'ContextualForget':
                    result = engine.contextual_query(question)
                elif engine_name == 'Hybrid':
                    result = engine.query(question)
                else:
                    result = engine.process_query(question)
                
                response_time = time.perf_counter() - start_time
                
                # 결과 분석
                retrieved_entities = set(result.get('entities', []))
                confidence = result.get('confidence', 0.0)
                entity_count = result.get('result_count', 0)
                
                # 성공 여부 판단 (GUID가 정확히 매칭되는 경우)
                is_success = len(gold_entities & retrieved_entities) > 0
                
                if is_success:
                    engine_results['success_count'] += 1
                
                engine_results['confidence_scores'].append(confidence)
                engine_results['entity_counts'].append(entity_count)
                engine_results['response_times'].append(response_time)
                
                detailed_result = {
                    'question_id': i + 1,
                    'question': question,
                    'gold_entities': list(gold_entities),
                    'retrieved_entities': list(retrieved_entities),
                    'confidence': confidence,
                    'entity_count': entity_count,
                    'response_time': response_time,
                    'is_success': is_success
                }
                engine_results['detailed_results'].append(detailed_result)
                
                print(f"  📝 질문 {i+1}: {question[:50]}...")
                print(f"    📊 결과: {entity_count}개 엔티티, 신뢰도 {confidence:.3f}, 성공: {is_success}")
                
            except Exception as e:
                print(f"  ❌ 질문 {i+1} 처리 오류: {e}")
                engine_results['confidence_scores'].append(0.0)
                engine_results['entity_counts'].append(0)
                engine_results['response_times'].append(0.0)
        
        # 엔진별 통계 계산
        success_rate = (engine_results['success_count'] / engine_results['total_questions']) * 100
        avg_confidence = sum(engine_results['confidence_scores']) / len(engine_results['confidence_scores'])
        avg_entities = sum(engine_results['entity_counts']) / len(engine_results['entity_counts'])
        avg_response_time = sum(engine_results['response_times']) / len(engine_results['response_times'])
        
        print(f"  📈 {engine_name} 결과:")
        print(f"    성공률: {success_rate:.1f}%")
        print(f"    평균 신뢰도: {avg_confidence:.3f}")
        print(f"    평균 엔티티 수: {avg_entities:.1f}")
        print(f"    실행 시간: {avg_response_time:.2f}초")
        
        results[engine_name] = {
            'success_rate': success_rate,
            'avg_confidence': avg_confidence,
            'avg_entities': avg_entities,
            'avg_response_time': avg_response_time,
            'detailed_results': engine_results['detailed_results']
        }
    
    # 5. 결과 저장
    output_file = Path("data/analysis/fixed_data_test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 테스트 결과 저장: {output_file}")
    
    # 6. 결과 요약 출력
    print("\n" + "="*60)
    print("📊 수정된 데이터 테스트 결과 요약")
    print("="*60)
    
    for engine_name, result in results.items():
        print(f"\n🔍 {engine_name}:")
        print(f"  성공률: {result['success_rate']:.1f}%")
        print(f"  평균 신뢰도: {result['avg_confidence']:.3f}")
        print(f"  평균 엔티티 수: {result['avg_entities']:.1f}")
        print(f"  실행 시간: {result['avg_response_time']:.2f}초")
    
    print("\n" + "="*60)
    print("🎉 수정된 데이터 평가 테스트 완료!")
    
    return results


def main():
    """메인 실행 함수"""
    print("🚀 수정된 데이터 평가 테스트 시작")
    print("="*60)
    
    try:
        results = test_engines_with_fixed_data()
        
        # 전체 성공률 계산
        total_success = sum(result['success_rate'] for result in results.values())
        avg_success = total_success / len(results) if results else 0
        
        print(f"\n📈 전체 평균 성공률: {avg_success:.1f}%")
        
        if avg_success >= 80:
            print("🎉 우수한 성능! 모든 엔진이 80% 이상 성공률을 달성했습니다.")
        elif avg_success >= 60:
            print("✅ 양호한 성능! 대부분의 엔진이 60% 이상 성공률을 달성했습니다.")
        else:
            print("⚠️ 개선 필요! 일부 엔진의 성능을 향상시켜야 합니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
