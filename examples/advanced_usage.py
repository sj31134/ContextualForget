#!/usr/bin/env python3
"""
ContextualForget 고급 사용 예제

이 스크립트는 ContextualForget의 다양한 기능을 보여주는 예제입니다.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

# ContextualForget 모듈 import
from contextualforget.core import ForgettingManager, create_default_forgetting_policy
from contextualforget.query import AdvancedQueryEngine
from contextualforget.llm import NaturalLanguageProcessor
from contextualforget.visualization import GraphVisualizer
from contextualforget.performance import GraphOptimizer, MemoryOptimizer


def example_1_basic_query():
    """예제 1: 기본 쿼리 사용법"""
    print("=== 예제 1: 기본 쿼리 ===")
    
    # 그래프 로드
    graph_path = "data/processed/graph.gpickle"
    if not Path(graph_path).exists():
        print("❌ 그래프 파일이 없습니다. 먼저 데이터를 생성하세요:")
        print("   python scripts/generate_sample_data.py")
        print("   python scripts/process_all_data.py")
        return
    
    # 고급 쿼리 엔진 초기화
    query_engine = AdvancedQueryEngine(graph_path)
    
    # GUID로 검색
    print("\n1. GUID 검색:")
    result = query_engine.query_by_guid("1kTvXnbbzCWw8lcMd1dR4o")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 키워드 검색
    print("\n2. 키워드 검색:")
    result = query_engine.search_by_keywords(["벽체", "두께"], ttl=30)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 시간 범위 검색
    print("\n3. 시간 범위 검색:")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    result = query_engine.query_by_date_range(
        start_date=start_date,
        end_date=end_date
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_2_forgetting_mechanisms():
    """예제 2: 망각 메커니즘 사용법"""
    print("\n=== 예제 2: 망각 메커니즘 ===")
    
    # 망각 매니저 초기화
    forgetting_manager = ForgettingManager()
    
    # 기본 망각 정책 생성
    policy = create_default_forgetting_policy()
    
    # 그래프 로드
    graph_path = "data/processed/graph.gpickle"
    if not Path(graph_path).exists():
        print("❌ 그래프 파일이 없습니다.")
        return
    
    import pickle
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
    
    print(f"원본 그래프: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 엣지")
    
    # 망각 정책 적용
    current_time = datetime.now()
    updated_graph = forgetting_manager.apply_forgetting(graph, current_time)
    
    print(f"망각 적용 후: {updated_graph.number_of_nodes()}개 노드, {updated_graph.number_of_edges()}개 엣지")
    
    # 망각 통계
    stats = forgetting_manager.get_forgetting_stats()
    print(f"망각 통계: {stats}")


def example_3_natural_language_processing():
    """예제 3: 자연어 처리 사용법"""
    print("\n=== 예제 3: 자연어 처리 ===")
    
    # 자연어 프로세서 초기화
    nlp = NaturalLanguageProcessor()
    
    # 다양한 질문 예제
    questions = [
        "그래프에 몇 개의 노드가 있어?",
        "GUID 1kTvXnbbzCWw8lcMd1dR4o와 관련된 이슈는?",
        "최근 7일 이내에 생성된 BCF 이슈를 보여줘",
        "벽체와 관련된 모든 이슈를 찾아줘"
    ]
    
    for question in questions:
        print(f"\n질문: {question}")
        try:
            result = nlp.process_query(question)
            print(f"답변: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"❌ 오류: {e}")


def example_4_visualization():
    """예제 4: 시각화 사용법"""
    print("\n=== 예제 4: 시각화 ===")
    
    graph_path = "data/processed/graph.gpickle"
    if not Path(graph_path).exists():
        print("❌ 그래프 파일이 없습니다.")
        return
    
    import pickle
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
    
    # 그래프 시각화
    visualizer = GraphVisualizer(graph)
    
    # 전체 그래프 시각화
    print("전체 그래프 시각화 중...")
    visualizer.visualize_full_graph(
        output_path="examples/full_graph.png",
        max_nodes=50  # 너무 많은 노드가 있으면 일부만 표시
    )
    print("✅ 전체 그래프 저장: examples/full_graph.png")
    
    # 특정 GUID 주변 서브그래프 시각화
    print("서브그래프 시각화 중...")
    try:
        visualizer.visualize_subgraph(
            target_guid="1kTvXnbbzCWw8lcMd1dR4o",
            output_path="examples/subgraph.png",
            max_depth=2
        )
        print("✅ 서브그래프 저장: examples/subgraph.png")
    except ValueError as e:
        print(f"⚠️ 서브그래프 시각화 실패: {e}")
    
    # 타임라인 시각화
    print("타임라인 시각화 중...")
    visualizer.visualize_timeline(
        output_path="examples/timeline.png",
        days=30
    )
    print("✅ 타임라인 저장: examples/timeline.png")


def example_5_performance_optimization():
    """예제 5: 성능 최적화 사용법"""
    print("\n=== 예제 5: 성능 최적화 ===")
    
    graph_path = "data/processed/graph.gpickle"
    if not Path(graph_path).exists():
        print("❌ 그래프 파일이 없습니다.")
        return
    
    # 그래프 최적화
    optimizer = GraphOptimizer()
    
    # 메모리 최적화
    print("메모리 최적화 중...")
    memory_optimizer = MemoryOptimizer()
    
    import pickle
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
    
    # 압축된 그래프 생성
    compressed_graph = memory_optimizer.compress_graph(graph)
    
    print(f"원본 그래프 크기: {graph.number_of_nodes()}개 노드")
    print(f"압축된 그래프 크기: {compressed_graph.number_of_nodes()}개 노드")
    
    # 압축된 그래프 저장
    compressed_path = "examples/compressed_graph.gpickle"
    memory_optimizer.save_graph_compressed(compressed_graph, compressed_path)
    print(f"✅ 압축된 그래프 저장: {compressed_path}")


def example_6_batch_operations():
    """예제 6: 배치 작업 사용법"""
    print("\n=== 예제 6: 배치 작업 ===")
    
    graph_path = "data/processed/graph.gpickle"
    if not Path(graph_path).exists():
        print("❌ 그래프 파일이 없습니다.")
        return
    
    # 배치 쿼리
    query_engine = AdvancedQueryEngine(graph_path)
    
    # 여러 GUID를 한 번에 검색
    guids = [
        "1kTvXnbbzCWw8lcMd1dR4o",
        "2mUwYoaa3DXx9mdNe2eR5p",
        "3nVxZpbb4EYy0neOf3fS6q"
    ]
    
    print("배치 GUID 검색:")
    for guid in guids:
        try:
            result = query_engine.query_by_guid(guid)
            print(f"GUID {guid}: {len(result.get('related_issues', []))}개 관련 이슈")
        except Exception as e:
            print(f"GUID {guid}: 검색 실패 - {e}")


def main():
    """메인 함수"""
    print("🚀 ContextualForget 고급 사용 예제")
    print("=" * 50)
    
    # 예제 디렉토리 생성
    Path("examples").mkdir(exist_ok=True)
    
    # 각 예제 실행
    try:
        example_1_basic_query()
        example_2_forgetting_mechanisms()
        example_3_natural_language_processing()
        example_4_visualization()
        example_5_performance_optimization()
        example_6_batch_operations()
        
        print("\n✅ 모든 예제가 완료되었습니다!")
        print("\n생성된 파일들:")
        print("- examples/full_graph.png")
        print("- examples/subgraph.png")
        print("- examples/timeline.png")
        print("- examples/compressed_graph.gpickle")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
