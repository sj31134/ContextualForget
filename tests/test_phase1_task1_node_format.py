"""
Phase 1 - Task 1.1 단위 테스트
그래프 노드 형식이 올바른 튜플 구조인지 검증
"""
import pickle
import sys
from pathlib import Path

import networkx as nx
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.data.build_graph import build_graph_from_files
from contextualforget.core import write_jsonl


class TestPhase1Task1NodeFormat:
    """노드 형식 검증 테스트"""
    
    @pytest.fixture
    def temp_data_files(self, tmp_path):
        """임시 테스트 데이터 생성"""
        # IFC 데이터
        ifc_data = [
            {
                'guid': 'test_guid_001',
                'type': 'IfcWall',
                'name': '테스트 벽체'
            },
            {
                'guid': 'test_guid_002',
                'type': 'IfcDoor',
                'name': '테스트 문'
            }
        ]
        ifc_file = tmp_path / 'test_ifc.jsonl'
        write_jsonl(str(ifc_file), ifc_data)
        
        # BCF 데이터
        bcf_data = [
            {
                'topic_id': 'bcf_topic_001',
                'title': '테스트 이슈 1',
                'description': '벽체 관련 이슈'
            },
            {
                'topic_id': 'bcf_topic_002',
                'title': '테스트 이슈 2',
                'description': '문 관련 이슈'
            }
        ]
        bcf_file = tmp_path / 'test_bcf.jsonl'
        write_jsonl(str(bcf_file), bcf_data)
        
        # 링크 데이터
        links_data = [
            {
                'topic_id': 'bcf_topic_001',
                'guid_matches': ['test_guid_001'],
                'confidence': 0.9,
                'evidence': '벽체'
            },
            {
                'topic_id': 'bcf_topic_002',
                'guid_matches': ['test_guid_002'],
                'confidence': 0.8,
                'evidence': '문'
            }
        ]
        links_file = tmp_path / 'test_links.jsonl'
        write_jsonl(str(links_file), links_data)
        
        return {
            'ifc_files': [str(ifc_file)],
            'bcf_files': [str(bcf_file)],
            'links_file': str(links_file)
        }
    
    def test_node_format_is_tuple(self, temp_data_files):
        """테스트 1: 모든 노드가 튜플 형식인지 확인"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        # 모든 노드가 튜플이어야 함
        for node in G.nodes:
            assert isinstance(node, tuple), f"노드 {node}는 튜플이 아닙니다: {type(node)}"
    
    def test_node_format_is_two_element_tuple(self, temp_data_files):
        """테스트 2: 모든 노드가 2개 요소로 구성된 튜플인지 확인"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        for node in G.nodes:
            assert len(node) == 2, f"노드 {node}는 2개 요소가 아닙니다: {len(node)}개"
    
    def test_node_format_first_element_is_type(self, temp_data_files):
        """테스트 3: 첫 번째 요소가 'IFC' 또는 'BCF'인지 확인"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        for node in G.nodes:
            assert node[0] in ['IFC', 'BCF'], \
                f"노드 {node}의 첫 요소가 'IFC' 또는 'BCF'가 아닙니다: {node[0]}"
    
    def test_node_format_second_element_is_id(self, temp_data_files):
        """테스트 4: 두 번째 요소가 문자열 ID인지 확인"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        for node in G.nodes:
            assert isinstance(node[1], str), \
                f"노드 {node}의 두 번째 요소가 문자열이 아닙니다: {type(node[1])}"
            assert len(node[1]) > 0, \
                f"노드 {node}의 ID가 빈 문자열입니다"
    
    def test_ifc_nodes_count(self, temp_data_files):
        """테스트 5: IFC 노드 수 확인"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        ifc_nodes = [n for n in G.nodes if n[0] == 'IFC']
        assert len(ifc_nodes) == 2, f"IFC 노드가 2개가 아닙니다: {len(ifc_nodes)}개"
    
    def test_bcf_nodes_count(self, temp_data_files):
        """테스트 6: BCF 노드 수 확인"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        bcf_nodes = [n for n in G.nodes if n[0] == 'BCF']
        assert len(bcf_nodes) == 2, f"BCF 노드가 2개가 아닙니다: {len(bcf_nodes)}개"
    
    def test_edges_exist(self, temp_data_files):
        """테스트 7: 엣지가 생성되었는지 확인"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        assert G.number_of_edges() > 0, "엣지가 생성되지 않았습니다"
        assert G.number_of_edges() == 2, f"엣지가 2개가 아닙니다: {G.number_of_edges()}개"
    
    def test_edge_format(self, temp_data_files):
        """테스트 8: 엣지 형식 확인 (BCF → IFC)"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        for source, target in G.edges:
            assert source[0] == 'BCF', f"엣지 소스가 BCF가 아닙니다: {source}"
            assert target[0] == 'IFC', f"엣지 타겟이 IFC가 아닙니다: {target}"
    
    def test_node_attributes(self, temp_data_files):
        """테스트 9: 노드 속성이 보존되었는지 확인"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        # IFC 노드 속성 확인
        ifc_node = ('IFC', 'test_guid_001')
        assert ifc_node in G.nodes, f"IFC 노드 {ifc_node}가 없습니다"
        assert G.nodes[ifc_node]['type'] == 'IfcWall'
        assert G.nodes[ifc_node]['name'] == '테스트 벽체'
        assert G.nodes[ifc_node]['node_type'] == 'IFC'
        
        # BCF 노드 속성 확인
        bcf_node = ('BCF', 'bcf_topic_001')
        assert bcf_node in G.nodes, f"BCF 노드 {bcf_node}가 없습니다"
        assert G.nodes[bcf_node]['title'] == '테스트 이슈 1'
        assert G.nodes[bcf_node]['node_type'] == 'BCF'
    
    def test_edge_attributes(self, temp_data_files):
        """테스트 10: 엣지 속성이 보존되었는지 확인"""
        G = build_graph_from_files(
            temp_data_files['ifc_files'],
            temp_data_files['bcf_files'],
            temp_data_files['links_file']
        )
        
        bcf_node = ('BCF', 'bcf_topic_001')
        ifc_node = ('IFC', 'test_guid_001')
        
        assert G.has_edge(bcf_node, ifc_node), f"엣지 {bcf_node} → {ifc_node}가 없습니다"
        
        edge_data = G.edges[bcf_node, ifc_node]
        assert edge_data['type'] == 'refersTo'
        assert edge_data['confidence'] == 0.9
        assert 'evidence' in edge_data


def test_build_graph_integration():
    """통합 테스트: 실제 파일로 그래프 구축"""
    # 실제 데이터가 있는 경우에만 실행
    data_dir = Path('data/processed')
    
    if not data_dir.exists():
        pytest.skip("data/processed 디렉토리가 없습니다")
    
    ifc_files = list(data_dir.glob('*_ifc.jsonl'))
    bcf_files = list(data_dir.glob('*_bcf.jsonl'))
    
    if not ifc_files or not bcf_files:
        pytest.skip("IFC 또는 BCF 파일이 없습니다")
    
    # 샘플 링크 파일 사용
    links_file = data_dir / 'sample_links.jsonl'
    if not links_file.exists():
        pytest.skip("sample_links.jsonl 파일이 없습니다")
    
    # 처음 5개 파일만 테스트
    G = build_graph_from_files(
        [str(f) for f in ifc_files[:5]],
        [str(f) for f in bcf_files[:5]],
        str(links_file)
    )
    
    # 기본 검증
    assert G.number_of_nodes() > 0, "노드가 생성되지 않았습니다"
    
    # 모든 노드가 튜플 형식인지 확인
    for node in G.nodes:
        assert isinstance(node, tuple), f"노드 {node}는 튜플이 아닙니다"
        assert len(node) == 2, f"노드 {node}는 2개 요소가 아닙니다"
        assert node[0] in ['IFC', 'BCF'], f"노드 {node}의 타입이 올바르지 않습니다"
    
    print(f"✅ 통합 테스트 통과: 노드 {G.number_of_nodes()}개, 엣지 {G.number_of_edges()}개")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

