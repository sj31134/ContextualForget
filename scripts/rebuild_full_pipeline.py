#!/usr/bin/env python3
"""
전체 파이프라인 재구축
1. IFC + BCF 링크 생성
2. 그래프 구축
3. 통계 출력
"""

import sys
import pickle
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextualforget.core import read_jsonl, write_jsonl
import networkx as nx


def create_links():
    """IFC와 BCF 링크 생성"""
    print("\n" + "="*60)
    print("🔗 Step 1: IFC-BCF 링크 생성")
    print("="*60)
    
    processed_dir = PROJECT_ROOT / "data" / "processed"
    
    # IFC 데이터 로드
    ifc_map = {}
    for ifc_file in processed_dir.glob("*_ifc.jsonl"):
        try:
            for entity in read_jsonl(str(ifc_file)):
                if "guid" in entity:
                    ifc_map[entity["guid"]] = entity
        except Exception as e:
            print(f"  ⚠️  IFC 로드 오류 ({ifc_file.name}): {e}")
    
    print(f"  IFC 엔티티: {len(ifc_map)}개")
    
    # BCF 이슈 로드 및 링크 생성
    links = []
    bcf_count = 0
    link_count = 0
    
    for bcf_file in processed_dir.glob("*_bcf.jsonl"):
        try:
            for issue in read_jsonl(str(bcf_file)):
                bcf_count += 1
                topic_id = issue.get("topic_id", "")
                
                # GUID 추출 시도
                ref = issue.get("ref", "")
                description = issue.get("description", "")
                
                # 링크 생성 (간단한 휴리스틱)
                linked_guids = []
                
                # ref 필드에서 GUID 찾기
                if ref and ref in ifc_map:
                    linked_guids.append(ref)
                
                # description에서 GUID 패턴 찾기
                import re
                guid_pattern = r'[A-Za-z0-9_]{22}'
                potential_guids = re.findall(guid_pattern, description)
                for guid in potential_guids:
                    if guid in ifc_map and guid not in linked_guids:
                        linked_guids.append(guid)
                
                if linked_guids:
                    links.append({
                        "topic_id": topic_id,
                        "linked_guids": linked_guids
                    })
                    link_count += len(linked_guids)
        
        except Exception as e:
            print(f"  ⚠️  BCF 로드 오류 ({bcf_file.name}): {e}")
    
    print(f"  BCF 이슈: {bcf_count}개")
    print(f"  생성된 링크: {link_count}개")
    
    # 저장
    links_file = processed_dir / "links.jsonl"
    write_jsonl(str(links_file), links)
    print(f"  ✅ 링크 저장: {links_file}")
    
    return ifc_map, bcf_count, links


def build_graph(ifc_map, links):
    """그래프 구축"""
    print("\n" + "="*60)
    print("📊 Step 2: 그래프 구축")
    print("="*60)
    
    G = nx.DiGraph()
    
    # IFC 노드 추가
    for guid, entity in ifc_map.items():
        G.add_node(guid, **entity)
    
    print(f"  IFC 노드: {len(ifc_map)}개 추가")
    
    # BCF 노드 및 엣지 추가
    processed_dir = PROJECT_ROOT / "data" / "processed"
    bcf_nodes = 0
    bcf_edges = 0
    
    for bcf_file in processed_dir.glob("*_bcf.jsonl"):
        try:
            for issue in read_jsonl(str(bcf_file)):
                topic_id = issue.get("topic_id", "")
                if topic_id:
                    G.add_node(topic_id, node_type="bcf_issue", **issue)
                    bcf_nodes += 1
        except:
            continue
    
    print(f"  BCF 노드: {bcf_nodes}개 추가")
    
    # 링크 엣지 추가
    for link in links:
        topic_id = link["topic_id"]
        for guid in link["linked_guids"]:
            if G.has_node(topic_id) and G.has_node(guid):
                G.add_edge(topic_id, guid, relation="references")
                bcf_edges += 1
    
    print(f"  링크 엣지: {bcf_edges}개 추가")
    
    # 그래프 저장
    output_file = processed_dir / "graph.gpickle"
    with output_file.open("wb") as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    print(f"  ✅ 그래프 저장: {output_file}")
    
    return G


def print_statistics(G, ifc_count, bcf_count):
    """통계 출력"""
    print("\n" + "="*60)
    print("📈 Step 3: 그래프 통계")
    print("="*60)
    
    print(f"\n노드:")
    print(f"  총 노드: {G.number_of_nodes()}개")
    
    ifc_nodes = [n for n in G.nodes() if G.nodes[n].get("type")]
    bcf_nodes = [n for n in G.nodes() if G.nodes[n].get("node_type") == "bcf_issue"]
    
    print(f"  - IFC 엔티티: {len(ifc_nodes)}개")
    print(f"  - BCF 이슈: {len(bcf_nodes)}개")
    
    print(f"\n엣지:")
    print(f"  총 엣지: {G.number_of_edges()}개")
    
    print(f"\n연결성:")
    if G.number_of_nodes() > 0:
        density = nx.density(G)
        print(f"  밀도: {density:.4f}")
        
        if G.number_of_edges() > 0:
            print(f"  평균 연결도: {2 * G.number_of_edges() / G.number_of_nodes():.2f}")
    
    print(f"\n구성 요소:")
    weakly_connected = nx.number_weakly_connected_components(G)
    print(f"  약하게 연결된 구성 요소: {weakly_connected}개")
    
    # 가장 큰 구성 요소
    if weakly_connected > 0:
        largest_wcc = max(nx.weakly_connected_components(G), key=len)
        print(f"  가장 큰 구성 요소: {len(largest_wcc)}개 노드")


def main():
    """메인 실행"""
    print("\n" + "🎯 " + "="*58)
    print("   전체 파이프라인 재구축")
    print("   " + "="*58)
    
    start_time = datetime.now()
    
    try:
        # Step 1: 링크 생성
        ifc_map, bcf_count, links = create_links()
        
        # Step 2: 그래프 구축
        G = build_graph(ifc_map, links)
        
        # Step 3: 통계
        print_statistics(G, len(ifc_map), bcf_count)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "="*60)
        print(f"✅ 파이프라인 완료! (소요 시간: {elapsed:.1f}초)")
        print("="*60)
        
        print("\n다음 단계:")
        print("  python scripts/comprehensive_evaluation.py")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

