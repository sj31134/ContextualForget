"""
그래프 검증 스크립트
엣지 수, 고아 노드, 연결성 등을 검증
"""
import argparse
import pickle
import sys
from pathlib import Path

import networkx as nx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def validate_graph(graph_path: str) -> dict:
    """
    그래프를 검증하고 통계를 반환합니다.
    
    Args:
        graph_path: 그래프 파일 경로
        
    Returns:
        검증 결과 딕셔너리
    """
    print(f"📊 그래프 검증 시작: {graph_path}")
    
    # 그래프 로드
    with open(graph_path, 'rb') as f:
        G = pickle.load(f)
    
    # 기본 통계
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    density = nx.density(G)
    
    print(f"\\n📈 기본 통계:")
    print(f"   노드 수: {num_nodes:,}개")
    print(f"   엣지 수: {num_edges:,}개")
    print(f"   밀도: {density:.6f}")
    
    # 노드 타입별 집계
    ifc_nodes = [n for n in G.nodes if isinstance(n, tuple) and n[0] == 'IFC']
    bcf_nodes = [n for n in G.nodes if isinstance(n, tuple) and n[0] == 'BCF']
    
    print(f"\\n🏷️  노드 타입:")
    print(f"   IFC 노드: {len(ifc_nodes):,}개 ({len(ifc_nodes)/num_nodes*100:.1f}%)")
    print(f"   BCF 노드: {len(bcf_nodes):,}개 ({len(bcf_nodes)/num_nodes*100:.1f}%)")
    
    # 고아 노드 (isolated nodes)
    isolated = list(nx.isolates(G))
    isolated_rate = len(isolated) / num_nodes * 100
    
    # BCF 노드 중 고아 노드 (더 의미있는 지표)
    isolated_bcf = [n for n in isolated if isinstance(n, tuple) and n[0] == 'BCF']
    isolated_bcf_rate = len(isolated_bcf) / len(bcf_nodes) * 100 if bcf_nodes else 0
    
    print(f"\\n🏝️  고아 노드:")
    print(f"   전체: {len(isolated):,}개 ({isolated_rate:.2f}%)")
    print(f"   BCF 고아: {len(isolated_bcf):,}개 ({isolated_bcf_rate:.2f}%)")
    
    if isolated_bcf_rate > 60:
        print(f"   ⚠️  BCF 고아 노드가 60%를 초과합니다!")
    else:
        print(f"   ✅ BCF 고아 노드 비율이 양호합니다")
    
    # 연결 컴포넌트
    if G.is_directed():
        components = list(nx.weakly_connected_components(G))
        strongly_components = list(nx.strongly_connected_components(G))
        print(f"\\n🔗 연결 컴포넌트:")
        print(f"   약한 연결: {len(components):,}개")
        print(f"   강한 연결: {len(strongly_components):,}개")
        
        # 가장 큰 컴포넌트
        largest = max(components, key=len)
        print(f"   최대 컴포넌트: {len(largest):,}개 노드 ({len(largest)/num_nodes*100:.1f}%)")
    else:
        components = list(nx.connected_components(G))
        print(f"\\n🔗 연결 컴포넌트:")
        print(f"   수: {len(components):,}개")
        
        # 가장 큰 컴포넌트
        largest = max(components, key=len)
        print(f"   최대 컴포넌트: {len(largest):,}개 노드 ({len(largest)/num_nodes*100:.1f}%)")
    
    # Degree 분포
    degrees = [G.degree(n) for n in G.nodes]
    avg_degree = sum(degrees) / len(degrees) if degrees else 0
    max_degree = max(degrees) if degrees else 0
    min_degree = min(degrees) if degrees else 0
    
    print(f"\\n📊 Degree 분포:")
    print(f"   평균: {avg_degree:.2f}")
    print(f"   최대: {max_degree}")
    print(f"   최소: {min_degree}")
    
    # 검증 결과
    results = {
        'num_nodes': num_nodes,
        'num_edges': num_edges,
        'density': density,
        'ifc_nodes': len(ifc_nodes),
        'bcf_nodes': len(bcf_nodes),
        'isolated_nodes': len(isolated),
        'isolated_rate': isolated_rate,
        'isolated_bcf_nodes': len(isolated_bcf),
        'isolated_bcf_rate': isolated_bcf_rate,
        'num_components': len(components),
        'largest_component_size': len(largest),
        'avg_degree': avg_degree,
        'max_degree': max_degree,
        'min_degree': min_degree
    }
    
    # 통과 조건 검증
    print(f"\\n✅ 검증 결과:")
    
    passed = True
    
    # 1. 엣지 수 >= 500
    if num_edges >= 500:
        print(f"   ✅ 엣지 수 목표 달성: {num_edges} >= 500")
    else:
        print(f"   ❌ 엣지 수 목표 미달: {num_edges} < 500")
        passed = False
    
    # 2. BCF 고아 노드 <= 60%
    if isolated_bcf_rate <= 60.0:
        print(f"   ✅ BCF 고아 노드 비율 양호: {isolated_bcf_rate:.2f}% <= 60%")
    else:
        print(f"   ❌ BCF 고아 노드 과다: {isolated_bcf_rate:.2f}% > 60%")
        passed = False
    
    # 3. 연결성 (최대 컴포넌트가 전체의 50% 이상)
    largest_rate = len(largest) / num_nodes * 100
    if largest_rate >= 50:
        print(f"   ✅ 연결성 양호: 최대 컴포넌트 {largest_rate:.1f}% >= 50%")
    else:
        print(f"   ⚠️  연결성 낮음: 최대 컴포넌트 {largest_rate:.1f}% < 50%")
        # 연결성은 경고만 (실패 처리 안 함)
    
    results['passed'] = passed
    results['largest_component_rate'] = largest_rate
    
    return results


def main():
    ap = argparse.ArgumentParser(description='그래프 검증')
    ap.add_argument("--graph", default="data/processed/graph.gpickle", help="그래프 파일 경로")
    ap.add_argument("--output", help="결과를 JSON 파일로 저장")
    a = ap.parse_args()
    
    results = validate_graph(a.graph)
    
    if a.output:
        import json
        with open(a.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\\n💾 결과 저장: {a.output}")
    
    if results['passed']:
        print(f"\\n🎉 모든 검증 통과!")
        return 0
    else:
        print(f"\\n❌ 일부 검증 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())

