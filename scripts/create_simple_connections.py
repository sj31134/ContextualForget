#!/usr/bin/env python3
"""
간단한 연결을 가진 그래프 생성
"""

import sys
import json
import pickle
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import read_jsonl
import networkx as nx


def create_graph_with_simple_connections():
    """간단한 연결을 가진 그래프 생성"""
    
    print("🔧 간단한 연결을 가진 그래프 생성 중...")
    
    # 실제 BCF 데이터 로드
    real_bcf_file = Path("data/processed/real_bcf/real_bcf_data.jsonl")
    real_data = list(read_jsonl(str(real_bcf_file)))
    
    print(f"  📊 BCF 이슈: {len(real_data)}개")
    
    # NetworkX 그래프 생성
    G = nx.DiGraph()
    
    # BCF 노드 추가
    bcf_nodes = []
    for issue in real_data:
        topic_id = issue.get('topic_id', '')
        if topic_id:
            node_id = ('BCF', topic_id)
            node_data = {
                'topic_id': topic_id,
                'title': issue.get('title', ''),
                'author': issue.get('author', ''),
                'description': issue.get('description', ''),
                'created': issue.get('created', ''),
                'source_file': issue.get('source_file', ''),
                'data_type': 'real_bcf'
            }
            G.add_node(node_id, **node_data)
            bcf_nodes.append(node_id)
    
    print(f"  ✅ BCF 노드 추가: {len(bcf_nodes)}개")
    
    # 가상의 IFC 노드들 생성 (BCF와 연결하기 위해)
    ifc_nodes = []
    ifc_types = ['PROJECT', 'SITE', 'BUILDING', 'COLUMN', 'BEAM', 'WALL', 'SLAB', 'DOOR', 'WINDOW', 'SPACE']
    
    for i, bcf_node in enumerate(bcf_nodes):
        # 각 BCF 노드마다 2-3개의 관련 IFC 노드 생성
        num_related = 2 + (i % 2)  # 2개 또는 3개
        
        for j in range(num_related):
            ifc_type = ifc_types[j % len(ifc_types)]
            ifc_guid = f"ifc_{i}_{j}_{ifc_type.lower()}"
            ifc_node_id = ('IFC', ifc_guid)
            
            ifc_data = {
                'guid': ifc_guid,
                'entity_type': ifc_type,
                'entity_id': f"#{i*10 + j}",
                'source_file': f"model_{i//10 + 1}.ifc",
                'data_type': 'synthetic_ifc',
                'related_bcf': bcf_node[1]  # BCF topic_id 참조
            }
            
            G.add_node(ifc_node_id, **ifc_data)
            ifc_nodes.append(ifc_node_id)
            
            # BCF-IFC 연결 생성
            G.add_edge(bcf_node, ifc_node_id, 
                      relationship='relates_to', 
                      confidence=0.8,
                      data_type='synthetic_connection')
    
    print(f"  ✅ IFC 노드 추가: {len(ifc_nodes)}개")
    
    # BCF 노드들 간의 연결 생성 (같은 파일에서 온 것들)
    file_groups = {}
    for bcf_node in bcf_nodes:
        source_file = G.nodes[bcf_node].get('source_file', '')
        if source_file:
            if source_file not in file_groups:
                file_groups[source_file] = []
            file_groups[source_file].append(bcf_node)
    
    # 같은 파일의 BCF 노드들을 연결
    for file_name, nodes in file_groups.items():
        if len(nodes) > 1:
            # 순차적으로 연결
            for i in range(len(nodes) - 1):
                G.add_edge(nodes[i], nodes[i + 1], 
                          relationship='same_file', 
                          confidence=0.9,
                          data_type='file_connection')
    
    # 통계 계산
    total_edges = G.number_of_edges()
    density = nx.density(G)
    
    print(f"  ✅ 총 연결: {total_edges}개")
    print(f"  📈 그래프 밀도: {density:.4f}")
    
    # 그래프 저장
    graph_output_dir = Path("data/processed/real_graph")
    graph_output_dir.mkdir(parents=True, exist_ok=True)
    
    graph_file = graph_output_dir / "real_data_graph_with_connections.pkl"
    with open(graph_file, 'wb') as f:
        pickle.dump(G, f)
    
    # 통계 저장
    stats = {
        "graph_creation_date": datetime.now().isoformat(),
        "total_nodes": G.number_of_nodes(),
        "bcf_nodes": len(bcf_nodes),
        "ifc_nodes": len(ifc_nodes),
        "total_edges": total_edges,
        "graph_density": density,
        "connected_components": nx.number_weakly_connected_components(G),
        "average_clustering": nx.average_clustering(G.to_undirected()) if G.number_of_nodes() > 0 else 0
    }
    
    stats_file = graph_output_dir / "real_data_graph_with_connections_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ 연결이 있는 그래프 저장: {graph_file}")
    
    return graph_file, stats


def main():
    """메인 실행 함수"""
    print("🚀 연결이 있는 그래프 생성 시작")
    print("="*60)
    
    try:
        graph_file, stats = create_graph_with_simple_connections()
        
        print("\n" + "="*60)
        print("🎉 연결이 있는 그래프 생성 완료!")
        print(f"📊 그래프 파일: {graph_file}")
        print(f"📊 총 노드: {stats['total_nodes']}개")
        print(f"📊 총 연결: {stats['total_edges']}개")
        print(f"📈 그래프 밀도: {stats['graph_density']:.4f}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
