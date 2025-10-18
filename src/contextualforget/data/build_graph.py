"""
그래프 구축 스크립트 (개선 버전)
IFC와 BCF 데이터를 통합 그래프로 구축하며, 올바른 노드 형식 (튜플) 보장
"""
import argparse
import pickle
import sys
from pathlib import Path
from typing import Dict, Any

import networkx as nx

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contextualforget.core import read_jsonl


def build_graph_from_files(ifc_files: list, bcf_files: list, links_file: str) -> nx.DiGraph:
    """
    여러 IFC/BCF 파일에서 그래프 구축
    
    Args:
        ifc_files: IFC JSONL 파일 경로 리스트
        bcf_files: BCF JSONL 파일 경로 리스트
        links_file: 링크 JSONL 파일 경로
        
    Returns:
        NetworkX DiGraph with proper node format
    """
    G = nx.DiGraph()
    
    # IFC 노드 추가 (명시적 튜플 형식)
    ifc_count = 0
    for ifc_file in ifc_files:
        for entity in read_jsonl(ifc_file):
            node_id = ('IFC', entity['guid'])
            G.add_node(node_id, node_type='IFC', **entity)
            ifc_count += 1
    
    print(f"✅ IFC 노드 추가 완료: {ifc_count}개")
    
    # BCF 노드 추가 (명시적 튜플 형식)
    bcf_count = 0
    for bcf_file in bcf_files:
        for issue in read_jsonl(bcf_file):
            node_id = ('BCF', issue['topic_id'])
            G.add_node(node_id, node_type='BCF', **issue)
            bcf_count += 1
    
    print(f"✅ BCF 노드 추가 완료: {bcf_count}개")
    
    # 링크(엣지) 추가
    edge_count = 0
    if Path(links_file).exists():
        for link in read_jsonl(links_file):
            topic_id = link['topic_id']
            bcf_node = ('BCF', topic_id)
            
            # BCF 노드가 존재하는지 확인
            if bcf_node not in G.nodes:
                continue
            
            for guid in link.get('guid_matches', []):
                ifc_node = ('IFC', guid)
                
                # IFC 노드가 존재하는지 확인
                if ifc_node not in G.nodes:
                    continue
                
                # 엣지 추가
                G.add_edge(
                    bcf_node, ifc_node,
                    type='refersTo',
                    confidence=link.get('confidence', 0.5),
                    evidence=link.get('evidence', '')
                )
                edge_count += 1
    
    print(f"✅ 엣지 추가 완료: {edge_count}개")
    
    return G


def main():
    ap = argparse.ArgumentParser(description='IFC-BCF 통합 그래프 구축')
    ap.add_argument("--ifc", help="IFC JSONL 파일 경로 (또는 디렉토리)")
    ap.add_argument("--bcf", help="BCF JSONL 파일 경로 (또는 디렉토리)")
    ap.add_argument("--links", required=True, help="링크 JSONL 파일 경로")
    ap.add_argument("--out", required=True, help="출력 그래프 파일 경로 (.gpickle)")
    ap.add_argument("--ifc-dir", help="IFC JSONL 파일들이 있는 디렉토리")
    ap.add_argument("--bcf-dir", help="BCF JSONL 파일들이 있는 디렉토리")
    a = ap.parse_args()
    
    # IFC 파일 목록 생성
    ifc_files = []
    if a.ifc:
        ifc_path = Path(a.ifc)
        if ifc_path.is_file():
            ifc_files.append(str(ifc_path))
        elif ifc_path.is_dir():
            ifc_files = [str(f) for f in ifc_path.glob('*_ifc.jsonl')]
    elif a.ifc_dir:
        ifc_dir = Path(a.ifc_dir)
        ifc_files = [str(f) for f in ifc_dir.glob('*_ifc.jsonl')]
    else:
        # 기본: data/processed에서 찾기
        default_dir = Path('data/processed')
        if default_dir.exists():
            ifc_files = [str(f) for f in default_dir.glob('*_ifc.jsonl')]
    
    # BCF 파일 목록 생성
    bcf_files = []
    if a.bcf:
        bcf_path = Path(a.bcf)
        if bcf_path.is_file():
            bcf_files.append(str(bcf_path))
        elif bcf_path.is_dir():
            bcf_files = [str(f) for f in bcf_path.glob('*_bcf.jsonl')]
    elif a.bcf_dir:
        bcf_dir = Path(a.bcf_dir)
        bcf_files = [str(f) for f in bcf_dir.glob('*_bcf.jsonl')]
    else:
        # 기본: data/processed에서 찾기
        default_dir = Path('data/processed')
        if default_dir.exists():
            bcf_files = [str(f) for f in default_dir.glob('*_bcf.jsonl')]
    
    print(f"📊 그래프 구축 시작...")
    print(f"   IFC 파일: {len(ifc_files)}개")
    print(f"   BCF 파일: {len(bcf_files)}개")
    print(f"   링크 파일: {a.links}")
    
    # 그래프 구축
    G = build_graph_from_files(ifc_files, bcf_files, a.links)
    
    # 결과 출력
    print(f"\n📈 그래프 통계:")
    print(f"   총 노드: {G.number_of_nodes():,}개")
    print(f"   총 엣지: {G.number_of_edges():,}개")
    
    # 노드 타입별 집계
    ifc_nodes = [n for n in G.nodes if n[0] == 'IFC']
    bcf_nodes = [n for n in G.nodes if n[0] == 'BCF']
    print(f"   IFC 노드: {len(ifc_nodes):,}개")
    print(f"   BCF 노드: {len(bcf_nodes):,}개")
    
    # 저장
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with Path(a.out).open('wb') as f:
        pickle.dump(G, f)
    
    print(f"\n✅ 그래프 저장 완료: {a.out}")
    
    # 샘플 노드 출력 (검증용)
    print(f"\n🔍 샘플 노드 (처음 3개):")
    for i, node in enumerate(list(G.nodes)[:3]):
        print(f"   {i+1}. {node}")


if __name__ == "__main__":
    main()
