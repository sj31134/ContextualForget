#!/usr/bin/env python3
"""
ContextualForget Quick Start Example

이 스크립트는 ContextualForget 시스템의 기본 사용법을 보여줍니다.
"""

import sys
import os
sys.path.append('..')

from contextualforget.query import AdvancedQueryEngine
from contextualforget.visualization import GraphVisualizer
from contextualforget.core import create_default_forgetting_policy
import pickle


def main():
    print("🚀 ContextualForget Quick Start")
    print("=" * 50)
    
    # 1. 그래프 로드
    graph_path = "data/processed/graph.gpickle"
    if not os.path.exists(graph_path):
        print("❌ 그래프 파일이 없습니다. 먼저 파이프라인을 실행하세요.")
        print("   python run_pipeline.py pipeline")
        return
    
    print("📁 그래프 로드 중...")
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
    
    print(f"✅ 그래프 로드 완료: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 엣지")
    
    # 2. 고급 쿼리 엔진 초기화
    print("\n🔍 쿼리 엔진 초기화...")
    engine = AdvancedQueryEngine(graph)
    
    # 3. 기본 쿼리 실행
    print("\n📋 기본 쿼리 실행:")
    target_guid = "1kTvXnbbzCWw8lcMd1dR4o"
    results = engine.find_by_guid(target_guid)
    
    print(f"GUID '{target_guid}'와 관련된 BCF 토픽:")
    for result in results:
        print(f"  - {result['title']} (생성: {result['created']})")
        print(f"    신뢰도: {result['edge']['confidence']}")
    
    # 4. 키워드 검색
    print("\n🔍 키워드 검색:")
    keyword_results = engine.find_by_keywords(["clearance"])
    print(f"'clearance' 키워드 검색 결과: {len(keyword_results)}개")
    for result in keyword_results:
        print(f"  - {result['title']} (작성자: {result['author']})")
    
    # 5. 작성자 검색
    print("\n👤 작성자 검색:")
    author_results = engine.find_by_author("engineer_a")
    print(f"'engineer_a' 작성자 검색 결과: {len(author_results)}개")
    for result in author_results:
        print(f"  - {result['title']} (생성: {result['created']})")
    
    # 6. 그래프 통계
    print("\n📊 그래프 통계:")
    stats = engine.get_statistics()
    print(f"  - 총 노드: {stats['total_nodes']}")
    print(f"  - IFC 엔티티: {stats['ifc_entities']}")
    print(f"  - BCF 토픽: {stats['bcf_topics']}")
    print(f"  - 총 엣지: {stats['total_edges']}")
    print(f"  - 평균 차수: {stats['average_degree']}")
    
    # 7. 망각 정책 테스트
    print("\n🧠 망각 정책 테스트:")
    forgetting_manager = create_default_forgetting_policy()
    
    # BCF 이벤트 수집
    bcf_events = []
    for node, data in graph.nodes(data=True):
        if node[0] == "BCF":
            bcf_events.append(data)
    
    print(f"총 {len(bcf_events)}개의 BCF 이벤트")
    
    # 망각 정책 적용
    filtered_events = forgetting_manager.filter_events(bcf_events)
    print(f"망각 정책 적용 후: {len(filtered_events)}개의 이벤트 유지")
    print(f"망각률: {(1 - len(filtered_events)/len(bcf_events))*100:.1f}%")
    
    # 8. 연결된 컴포넌트 분석
    print("\n🔗 연결된 컴포넌트 분석:")
    components = engine.find_connected_components(target_guid, max_depth=2)
    
    print(f"GUID '{target_guid}'의 연결된 컴포넌트:")
    print(f"  - IFC 엔티티: {len(components['ifc_entities'])}개")
    print(f"  - BCF 토픽: {len(components['bcf_topics'])}개")
    
    for entity in components['ifc_entities']:
        print(f"    IFC: {entity['guid']} (타입: {entity['type']})")
    
    for topic in components['bcf_topics']:
        print(f"    BCF: {topic['title']}")
    
    print("\n✅ Quick Start 완료!")
    print("\n더 많은 기능을 보려면:")
    print("  - Jupyter 노트북: examples/demo.ipynb")
    print("  - CLI 명령어: ctxf --help")
    print("  - 문서: docs/tutorial.md")


if __name__ == "__main__":
    main()
