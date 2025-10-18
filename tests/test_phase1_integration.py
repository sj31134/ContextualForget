"""
Phase 1 통합 테스트
엣지 >= 500, 고아 노드 <= 60%, 연결성 검증
"""
import pickle
import sys
from pathlib import Path

import networkx as nx
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestPhase1Integration:
    """Phase 1 통합 테스트"""
    
    @pytest.fixture
    def graph_path(self):
        """그래프 파일 경로"""
        return Path('data/processed/graph.gpickle')
    
    @pytest.fixture
    def graph(self, graph_path):
        """그래프 로드"""
        if not graph_path.exists():
            pytest.skip("그래프 파일이 없습니다")
        
        with open(graph_path, 'rb') as f:
            return pickle.load(f)
    
    def test_graph_exists(self, graph_path):
        """테스트 1: 그래프 파일이 존재하는지 확인"""
        assert graph_path.exists(), f"그래프 파일이 없습니다: {graph_path}"
    
    def test_graph_is_networkx(self, graph):
        """테스트 2: 그래프가 NetworkX 객체인지 확인"""
        assert isinstance(graph, nx.Graph) or isinstance(graph, nx.DiGraph), \
            f"그래프가 NetworkX 객체가 아닙니다: {type(graph)}"
    
    def test_edge_count_minimum(self, graph):
        """테스트 3: 엣지 수 >= 500"""
        num_edges = graph.number_of_edges()
        assert num_edges >= 500, \
            f"엣지 수가 목표 미달입니다: {num_edges} < 500"
        
        print(f"✅ 엣지 수: {num_edges}개")
    
    def test_node_format_is_tuple(self, graph):
        """테스트 4: 모든 노드가 튜플 형식인지 확인"""
        for node in list(graph.nodes)[:100]:  # 샘플링
            assert isinstance(node, tuple), f"노드 {node}는 튜플이 아닙니다"
            assert len(node) == 2, f"노드 {node}의 길이가 2가 아닙니다"
            assert node[0] in ['IFC', 'BCF'], f"노드 {node}의 타입이 올바르지 않습니다"
    
    def test_bcf_isolated_nodes_rate(self, graph):
        """테스트 5: BCF 고아 노드 비율 <= 60%"""
        bcf_nodes = [n for n in graph.nodes if isinstance(n, tuple) and n[0] == 'BCF']
        isolated = list(nx.isolates(graph))
        isolated_bcf = [n for n in isolated if isinstance(n, tuple) and n[0] == 'BCF']
        
        isolated_bcf_rate = len(isolated_bcf) / len(bcf_nodes) * 100 if bcf_nodes else 0
        
        assert isolated_bcf_rate <= 60.0, \
            f"BCF 고아 노드 비율이 과다합니다: {isolated_bcf_rate:.2f}% > 60%"
        
        print(f"✅ BCF 고아 노드 비율: {isolated_bcf_rate:.2f}%")
    
    def test_ifc_and_bcf_nodes_exist(self, graph):
        """테스트 6: IFC와 BCF 노드가 모두 존재하는지 확인"""
        ifc_nodes = [n for n in graph.nodes if isinstance(n, tuple) and n[0] == 'IFC']
        bcf_nodes = [n for n in graph.nodes if isinstance(n, tuple) and n[0] == 'BCF']
        
        assert len(ifc_nodes) > 0, "IFC 노드가 없습니다"
        assert len(bcf_nodes) > 0, "BCF 노드가 없습니다"
        
        print(f"   IFC 노드: {len(ifc_nodes):,}개")
        print(f"   BCF 노드: {len(bcf_nodes):,}개")
    
    def test_edges_connect_bcf_to_ifc(self, graph):
        """테스트 7: 엣지가 BCF → IFC를 연결하는지 확인"""
        # 샘플 엣지 검증
        edges = list(graph.edges)[:10]
        
        for source, target in edges:
            # 방향성 그래프인 경우 BCF → IFC
            if isinstance(source, tuple) and isinstance(target, tuple):
                # BCF가 source인지, 또는 target인지 확인
                assert (source[0] == 'BCF' or target[0] == 'BCF'), \
                    f"엣지 {source} → {target}에 BCF 노드가 없습니다"
    
    def test_edge_attributes(self, graph):
        """테스트 8: 엣지 속성 확인"""
        edges_with_data = list(graph.edges(data=True))[:10]
        
        for source, target, data in edges_with_data:
            # confidence 속성 확인
            if 'confidence' in data:
                assert 0.0 <= data['confidence'] <= 1.0, \
                    f"엣지 {source} → {target}의 confidence가 범위를 벗어났습니다: {data['confidence']}"
    
    def test_graph_statistics(self, graph):
        """테스트 9: 그래프 기본 통계"""
        num_nodes = graph.number_of_nodes()
        num_edges = graph.number_of_edges()
        density = nx.density(graph)
        
        print(f"\\n📊 그래프 통계:")
        print(f"   노드: {num_nodes:,}개")
        print(f"   엣지: {num_edges:,}개")
        print(f"   밀도: {density:.6f}")
        
        assert num_nodes > 0, "노드가 없습니다"
        assert num_edges > 0, "엣지가 없습니다"
    
    def test_connected_components(self, graph):
        """테스트 10: 연결 컴포넌트 분석"""
        if graph.is_directed():
            components = list(nx.weakly_connected_components(graph))
        else:
            components = list(nx.connected_components(graph))
        
        largest = max(components, key=len) if components else set()
        
        print(f"\\n🔗 연결성:")
        print(f"   컴포넌트 수: {len(components):,}개")
        print(f"   최대 컴포넌트: {len(largest):,}개 노드")
        
        # 연결 컴포넌트가 있는지만 확인 (개수는 제한하지 않음)
        assert len(components) > 0, "연결 컴포넌트가 없습니다"


def test_phase1_completion():
    """Phase 1 완료 종합 테스트"""
    # 1. 그래프 파일 확인
    graph_path = Path('data/processed/graph.gpickle')
    assert graph_path.exists(), "그래프 파일이 없습니다"
    
    # 2. 링크 파일 확인
    links_path = Path('data/processed/all_links.jsonl')
    assert links_path.exists(), "링크 파일이 없습니다"
    
    # 3. 그래프 로드 및 검증
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
    
    num_edges = graph.number_of_edges()
    ifc_nodes = [n for n in graph.nodes if isinstance(n, tuple) and n[0] == 'IFC']
    bcf_nodes = [n for n in graph.nodes if isinstance(n, tuple) and n[0] == 'BCF']
    
    isolated = list(nx.isolates(graph))
    isolated_bcf = [n for n in isolated if isinstance(n, tuple) and n[0] == 'BCF']
    isolated_bcf_rate = len(isolated_bcf) / len(bcf_nodes) * 100 if bcf_nodes else 0
    
    print(f"\\n🎉 Phase 1 완료 검증:")
    print(f"   ✅ 노드 형식: 튜플 ('IFC'|'BCF', id)")
    print(f"   ✅ IFC 노드: {len(ifc_nodes):,}개")
    print(f"   ✅ BCF 노드: {len(bcf_nodes):,}개")
    print(f"   ✅ 엣지 수: {num_edges}개 (목표: ≥500)")
    print(f"   ✅ BCF 고아 노드: {isolated_bcf_rate:.2f}% (목표: ≤60%)")
    
    # 최종 검증
    assert num_edges >= 500, f"엣지 수 목표 미달: {num_edges} < 500"
    assert isolated_bcf_rate <= 60.0, f"BCF 고아 노드 과다: {isolated_bcf_rate:.2f}% > 60%"
    
    print(f"\\n✅ Phase 1 모든 목표 달성!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

