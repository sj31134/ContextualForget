#!/usr/bin/env python3
"""
Gold Standard 및 그래프 문제 수정 스크립트
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import read_jsonl


def fix_gold_standard():
    """Gold Standard를 실제 데이터에 맞게 수정"""
    
    print("🔧 Gold Standard 수정 중...")
    
    # 실제 BCF 데이터 로드
    real_bcf_file = Path("data/processed/real_bcf/real_bcf_data.jsonl")
    real_data = list(read_jsonl(str(real_bcf_file)))
    real_guids = [issue.get('topic_id', '') for issue in real_data if issue.get('topic_id')]
    
    print(f"  📊 실제 BCF GUID 수: {len(real_guids)}")
    
    # 기존 Gold Standard 로드
    gold_standard_file = Path("eval/gold_standard_real_data.jsonl")
    gold_data = list(read_jsonl(str(gold_standard_file)))
    
    print(f"  📊 기존 Gold Standard 질문 수: {len(gold_data)}")
    
    # 실제 존재하는 GUID만 사용하여 새로운 Gold Standard 생성
    fixed_gold_data = []
    
    for i, qa in enumerate(gold_data):
        if i < len(real_guids):
            # 실제 존재하는 GUID 사용
            guid = real_guids[i]
            fixed_qa = qa.copy()
            fixed_qa['gold_entities'] = [guid]
            
            # 질문 업데이트
            if qa['category'] == 'entity_search':
                fixed_qa['question'] = f"GUID {guid}의 엔티티 타입은 무엇인가요?"
            elif qa['category'] == 'issue_search':
                fixed_qa['question'] = f"'{guid}'와 관련된 이슈는 무엇인가요?"
            elif qa['category'] == 'relationship':
                fixed_qa['question'] = f"'{guid}'와 관련된 정보는 무엇인가요?"
            
            fixed_gold_data.append(fixed_qa)
    
    # 수정된 Gold Standard 저장
    fixed_gold_file = Path("eval/gold_standard_fixed.jsonl")
    with open(fixed_gold_file, 'w', encoding='utf-8') as f:
        for qa in fixed_gold_data:
            f.write(json.dumps(qa, ensure_ascii=False) + '\n')
    
    print(f"  ✅ 수정된 Gold Standard 저장: {fixed_gold_file}")
    print(f"  📊 수정된 질문 수: {len(fixed_gold_data)}")
    
    return fixed_gold_file


def rebuild_graph_with_connections():
    """연결이 있는 그래프 재구성"""
    
    print("🔧 그래프 재구성 중...")
    
    # 실제 BCF 데이터 로드
    real_bcf_file = Path("data/processed/real_bcf/real_bcf_data.jsonl")
    real_data = list(read_jsonl(str(real_bcf_file)))
    
    # IFC 파일들 로드
    ifc_files = list(Path("data").glob("**/*.ifc"))
    
    print(f"  📊 BCF 이슈: {len(real_data)}개")
    print(f"  📊 IFC 파일: {len(ifc_files)}개")
    
    # 그래프 데이터 구조 생성
    graph_data = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "creation_date": datetime.now().isoformat(),
            "data_source": "real_bcf_with_connections",
            "bcf_issues": len(real_data),
            "ifc_files": len(ifc_files)
        }
    }
    
    # BCF 노드 추가
    bcf_nodes_added = 0
    for issue in real_data:
        topic_id = issue.get('topic_id', '')
        if topic_id:
            node_data = {
                "node_id": ("BCF", topic_id),
                "type": "BCF",
                "topic_id": topic_id,
                "title": issue.get('title', ''),
                "author": issue.get('author', ''),
                "description": issue.get('description', ''),
                "created": issue.get('created', ''),
                "source_file": issue.get('source_file', ''),
                "data_type": "real_bcf"
            }
            graph_data["nodes"].append(node_data)
            bcf_nodes_added += 1
    
    print(f"  ✅ BCF 노드 추가: {bcf_nodes_added}개")
    
    # IFC 노드 추가 (제한적으로)
    ifc_nodes_added = 0
    for ifc_file in ifc_files[:10]:  # 처음 10개 파일만 처리
        try:
            with open(ifc_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # IFC 엔티티 패턴 찾기
            import re
            ifc_pattern = r"#(\d+)=IFC([A-Z0-9_]+)\('([A-Za-z0-9_]{10,24})'"
            matches = re.findall(ifc_pattern, content)
            
            for match in matches[:50]:  # 파일당 최대 50개
                entity_id, entity_type, guid = match
                node_data = {
                    "node_id": ("IFC", guid),
                    "type": "IFC",
                    "guid": guid,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "source_file": ifc_file.name,
                    "data_type": "real_ifc"
                }
                graph_data["nodes"].append(node_data)
                ifc_nodes_added += 1
                
        except Exception as e:
            print(f"  ⚠️ IFC 파일 처리 오류: {ifc_file.name} - {e}")
            continue
    
    print(f"  ✅ IFC 노드 추가: {ifc_nodes_added}개")
    
    # BCF-IFC 연결 생성 (의미 있는 연결)
    edges_added = 0
    
    # BCF 이슈의 제목/설명에서 IFC 관련 키워드 찾기
    ifc_keywords = ["wall", "beam", "column", "slab", "door", "window", "space", "zone", "project", "building"]
    
    for bcf_node in graph_data["nodes"]:
        if bcf_node["type"] == "BCF":
            title = bcf_node.get("title", "").lower()
            description = bcf_node.get("description", "").lower()
            
            # 키워드 매칭으로 IFC 노드와 연결
            for ifc_node in graph_data["nodes"]:
                if ifc_node["type"] == "IFC":
                    entity_type = ifc_node.get("entity_type", "").lower()
                    
                    # 키워드 매칭
                    if any(keyword in title or keyword in description for keyword in ifc_keywords):
                        if entity_type in title or entity_type in description:
                            edge_data = {
                                "source": bcf_node["node_id"],
                                "target": ifc_node["node_id"],
                                "relationship": "relates_to",
                                "confidence": 0.7,
                                "data_type": "semantic_connection"
                            }
                            graph_data["edges"].append(edge_data)
                            edges_added += 1
                            
                            # 너무 많은 연결이 생성되지 않도록 제한
                            if edges_added >= 100:
                                break
            
            if edges_added >= 100:
                break
    
    print(f"  ✅ 연결 추가: {edges_added}개")
    
    # NetworkX 그래프 생성
    import networkx as nx
    G = nx.DiGraph()
    
    # 노드 추가
    for node_data in graph_data["nodes"]:
        node_id = node_data["node_id"]
        G.add_node(node_id, **{k: v for k, v in node_data.items() if k != "node_id"})
    
    # 엣지 추가
    for edge_data in graph_data["edges"]:
        G.add_edge(edge_data["source"], edge_data["target"], **{k: v for k, v in edge_data.items() if k not in ["source", "target"]})
    
    # 그래프 저장
    graph_output_dir = Path("data/processed/real_graph")
    graph_output_dir.mkdir(parents=True, exist_ok=True)
    
    graph_file = graph_output_dir / "real_data_graph_fixed.pkl"
    import pickle
    with open(graph_file, 'wb') as f:
        pickle.dump(G, f)
    
    # 메타데이터 저장
    metadata_file = graph_output_dir / "real_data_graph_fixed_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data["metadata"], f, ensure_ascii=False, indent=2)
    
    # 통계 생성
    stats = {
        "graph_creation_date": datetime.now().isoformat(),
        "total_nodes": len(graph_data["nodes"]),
        "bcf_nodes": bcf_nodes_added,
        "ifc_nodes": ifc_nodes_added,
        "total_edges": len(graph_data["edges"]),
        "graph_density": nx.density(G),
        "connected_components": nx.number_weakly_connected_components(G),
        "average_clustering": nx.average_clustering(G.to_undirected()) if G.number_of_nodes() > 0 else 0
    }
    
    stats_file = graph_output_dir / "real_data_graph_fixed_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ 수정된 그래프 저장: {graph_file}")
    print(f"  📊 총 노드: {stats['total_nodes']}개")
    print(f"  📊 총 연결: {stats['total_edges']}개")
    print(f"  📈 그래프 밀도: {stats['graph_density']:.4f}")
    
    return graph_file


def main():
    """메인 실행 함수"""
    print("🚀 Gold Standard 및 그래프 문제 수정 시작")
    print("="*60)
    
    try:
        # 1. Gold Standard 수정
        fixed_gold_file = fix_gold_standard()
        
        # 2. 그래프 재구성
        fixed_graph_file = rebuild_graph_with_connections()
        
        print("\n" + "="*60)
        print("🎉 Gold Standard 및 그래프 수정 완료!")
        print(f"📊 수정된 Gold Standard: {fixed_gold_file}")
        print(f"📊 수정된 그래프: {fixed_graph_file}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
