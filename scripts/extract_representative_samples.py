"""
대표 샘플 추출 스크립트
그래프에서 IFC/BCF 대표 노드 100개 추출 (LLM QA 생성용)
"""
import argparse
import json
import pickle
import sys
from collections import Counter
from pathlib import Path

import networkx as nx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def extract_representative_samples(graph_path: str, output_path: str):
    """
    그래프에서 대표 샘플을 추출합니다.
    
    목표:
    - IFC 엔티티 샘플: 30개
    - BCF 이슈 샘플: 30개
    - 연결된 쌍 (BCF-IFC): 40개
    
    총 100개 샘플 생성
    """
    print(f"📊 그래프 로드 중: {graph_path}")
    with open(graph_path, 'rb') as f:
        G = pickle.load(f)
    
    print(f"   노드: {G.number_of_nodes():,}개")
    print(f"   엣지: {G.number_of_edges():,}개")
    
    # IFC 노드 추출
    ifc_nodes = [n for n in G.nodes if isinstance(n, tuple) and n[0] == 'IFC']
    bcf_nodes = [n for n in G.nodes if isinstance(n, tuple) and n[0] == 'BCF']
    
    print(f"\n🏷️  노드 타입:")
    print(f"   IFC: {len(ifc_nodes):,}개")
    print(f"   BCF: {len(bcf_nodes):,}개")
    
    # 1. IFC 타입별 대표 노드 (30개)
    print(f"\n📦 IFC 타입별 대표 샘플 추출 중...")
    ifc_types = Counter([
        G.nodes[n].get('type', 'Unknown')
        for n in ifc_nodes
    ])
    
    ifc_samples = []
    for ifc_type, count in ifc_types.most_common(10):
        nodes = [n for n in ifc_nodes if G.nodes[n].get('type') == ifc_type]
        # 타입당 최대 3개
        for node in nodes[:3]:
            node_data = G.nodes[node]
            ifc_samples.append({
                'node_id': node,
                'guid': node[1],
                'type': node_data.get('type', 'Unknown'),
                'name': node_data.get('name', ''),
                'description': node_data.get('description', ''),
                'sample_type': 'entity_search'
            })
    
    print(f"   ✅ IFC 샘플: {len(ifc_samples)}개")
    
    # 2. BCF 이슈 샘플 (30개)
    print(f"\n📋 BCF 이슈 샘플 추출 중...")
    
    # 우선순위별로 추출
    priorities = ['critical', 'major', 'high', 'medium', 'normal', 'minor', 'low']
    bcf_by_priority = {p: [] for p in priorities}
    bcf_no_priority = []
    
    for node in bcf_nodes:
        node_data = G.nodes[node]
        priority = node_data.get('priority', '').lower()
        
        if priority in bcf_by_priority:
            bcf_by_priority[priority].append(node)
        else:
            bcf_no_priority.append(node)
    
    bcf_samples = []
    
    # 각 우선순위별로 5개씩
    for priority in priorities:
        for node in bcf_by_priority[priority][:5]:
            node_data = G.nodes[node]
            bcf_samples.append({
                'node_id': node,
                'topic_id': node[1],
                'title': node_data.get('title', ''),
                'description': node_data.get('description', ''),
                'priority': node_data.get('priority', ''),
                'author': node_data.get('author', ''),
                'created': node_data.get('created', ''),
                'sample_type': 'issue_search'
            })
    
    # 부족하면 우선순위 없는 것에서 채우기
    if len(bcf_samples) < 30:
        for node in bcf_no_priority[:30 - len(bcf_samples)]:
            node_data = G.nodes[node]
            bcf_samples.append({
                'node_id': node,
                'topic_id': node[1],
                'title': node_data.get('title', ''),
                'description': node_data.get('description', ''),
                'priority': node_data.get('priority', 'normal'),
                'author': node_data.get('author', ''),
                'created': node_data.get('created', ''),
                'sample_type': 'issue_search'
            })
    
    print(f"   ✅ BCF 샘플: {len(bcf_samples)}개")
    
    # 3. 연결된 쌍 (BCF → IFC) (40개)
    print(f"\n🔗 연결된 BCF-IFC 쌍 추출 중...")
    connected_pairs = []
    
    for bcf_node in bcf_nodes[:200]:  # 처음 200개 BCF 노드 검사
        successors = list(G.successors(bcf_node))
        
        if successors:
            # 첫 번째 연결된 IFC 노드
            ifc_node = successors[0]
            edge_data = G.edges.get((bcf_node, ifc_node), {})
            
            bcf_data = G.nodes[bcf_node]
            ifc_data = G.nodes[ifc_node]
            
            connected_pairs.append({
                'bcf_node_id': bcf_node,
                'ifc_node_id': ifc_node,
                'bcf_topic_id': bcf_node[1],
                'bcf_title': bcf_data.get('title', ''),
                'bcf_description': bcf_data.get('description', ''),
                'ifc_guid': ifc_node[1],
                'ifc_type': ifc_data.get('type', ''),
                'ifc_name': ifc_data.get('name', ''),
                'confidence': edge_data.get('confidence', 0.5),
                'sample_type': 'relationship'
            })
            
            if len(connected_pairs) >= 40:
                break
    
    print(f"   ✅ 연결 쌍: {len(connected_pairs)}개")
    
    # 결과 통합
    samples = {
        'ifc_samples': ifc_samples[:30],
        'bcf_samples': bcf_samples[:30],
        'connected_pairs': connected_pairs[:40],
        'metadata': {
            'total_samples': len(ifc_samples[:30]) + len(bcf_samples[:30]) + len(connected_pairs[:40]),
            'graph_nodes': G.number_of_nodes(),
            'graph_edges': G.number_of_edges(),
            'ifc_node_count': len(ifc_nodes),
            'bcf_node_count': len(bcf_nodes)
        }
    }
    
    # 저장
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    # 통계 출력
    total = samples['metadata']['total_samples']
    print(f"\n📊 추출 완료:")
    print(f"   IFC 샘플: {len(samples['ifc_samples'])}개")
    print(f"   BCF 샘플: {len(samples['bcf_samples'])}개")
    print(f"   연결 쌍: {len(samples['connected_pairs'])}개")
    print(f"   총 샘플: {total}개")
    
    print(f"\n✅ 샘플 저장: {output_path}")
    
    return samples


def main():
    ap = argparse.ArgumentParser(description='대표 샘플 추출')
    ap.add_argument("--graph", default="data/processed/graph.gpickle", help="그래프 파일 경로")
    ap.add_argument("--output", default="data/processed/representative_samples.json", help="출력 파일 경로")
    a = ap.parse_args()
    
    samples = extract_representative_samples(a.graph, a.output)
    
    if samples['metadata']['total_samples'] >= 100:
        print(f"\n🎉 목표 달성: {samples['metadata']['total_samples']}개 >= 100개")
    else:
        print(f"\n⚠️  목표 미달: {samples['metadata']['total_samples']}개 < 100개")


if __name__ == "__main__":
    main()

