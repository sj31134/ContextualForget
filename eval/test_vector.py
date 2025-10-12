#!/usr/bin/env python3
"""
Vector RAG 엔진 테스트 스크립트
"""

import sys
import pickle
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from contextualforget.baselines import VectorQueryEngine


def test_vector_engine():
    """Test Vector RAG engine with sample queries."""
    
    print("🧪 Vector RAG 엔진 테스트 시작")
    print("=" * 50)
    
    # Load graph data
    graph_path = Path("data/processed/graph.gpickle")
    if not graph_path.exists():
        print(f"❌ 그래프 파일이 없습니다: {graph_path}")
        return
    
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
    
    print(f"✅ 그래프 로드: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 엣지")
    
    # Prepare graph data for Vector RAG
    graph_data = {"nodes": list(graph.nodes(data=True))}
    
    # Initialize Vector RAG engine
    vector_engine = VectorQueryEngine()
    vector_engine.initialize(graph_data)
    
    # Test queries
    test_queries = [
        "GUID 3oJ823HYX3TgOV10vGIMAW는 어떤 IFC 요소인가요?",
        "최근 30일 이내에 생성된 이슈는 무엇인가요?",
        "engineer_a가 작성한 이슈는 무엇인가요?",
        "무균실 마감 사양 관련 이슈는?",
        "방화문 위치 변경 이슈는?",
        "현재 프로젝트의 전체 통계를 보여주세요."
    ]
    
    print(f"\n🔍 테스트 쿼리 실행 ({len(test_queries)}개)")
    print("-" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 질문: {query}")
        
        try:
            result = vector_engine.process_query(query)
            
            print(f"   답변: {result.get('answer', 'N/A')}")
            print(f"   신뢰도: {result.get('confidence', 0.0):.2f}")
            print(f"   소스: {result.get('source', 'N/A')}")
            
            if 'details' in result:
                print(f"   상세: {result['details']}")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
    
    # Test engine stats
    print(f"\n📊 엔진 통계")
    print("-" * 30)
    stats = vector_engine.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ Vector RAG 엔진 테스트 완료")


if __name__ == "__main__":
    test_vector_engine()
