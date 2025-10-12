"""그래프 동적 업데이트 모듈."""

import logging
import pickle
import networkx as nx
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .file_watcher import FileChangeEvent, FileChangeType
from ..core import extract_ifc_entities, parse_bcf_zip, write_jsonl

logger = logging.getLogger(__name__)


class GraphUpdater:
    """그래프 동적 업데이트 관리자."""
    
    def __init__(self, graph_path: Path, processed_dir: Path):
        """
        Args:
            graph_path: 그래프 파일 경로
            processed_dir: 처리된 데이터 저장 디렉토리
        """
        self.graph_path = Path(graph_path)
        self.processed_dir = Path(processed_dir)
        self.graph = None
        
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"GraphUpdater 초기화: {graph_path}")
    
    def load_graph(self) -> nx.DiGraph:
        """그래프 로드."""
        if self.graph is None:
            if self.graph_path.exists():
                with open(self.graph_path, 'rb') as f:
                    self.graph = pickle.load(f)
                logger.info(f"그래프 로드 완료: {self.graph.number_of_nodes()}개 노드")
            else:
                self.graph = nx.DiGraph()
                logger.info("새 그래프 생성")
        
        return self.graph
    
    def save_graph(self):
        """그래프 저장."""
        if self.graph is None:
            logger.warning("저장할 그래프가 없습니다")
            return
        
        with open(self.graph_path, 'wb') as f:
            pickle.dump(self.graph, f)
        
        logger.info(
            f"그래프 저장 완료: {self.graph.number_of_nodes()}개 노드, "
            f"{self.graph.number_of_edges()}개 엣지"
        )
    
    def process_ifc_file(self, ifc_path: Path) -> List[Dict[str, Any]]:
        """IFC 파일 처리."""
        logger.info(f"IFC 파일 처리: {ifc_path.name}")
        
        try:
            entities = extract_ifc_entities(str(ifc_path))
            logger.info(f"IFC 엔티티 추출 완료: {len(entities)}개")
            return entities
        except Exception as e:
            logger.error(f"IFC 파일 처리 오류: {e}", exc_info=True)
            return []
    
    def process_bcf_file(self, bcf_path: Path) -> List[Dict[str, Any]]:
        """BCF 파일 처리."""
        logger.info(f"BCF 파일 처리: {bcf_path.name}")
        
        try:
            topics = parse_bcf_zip(str(bcf_path))
            logger.info(f"BCF 토픽 추출 완료: {len(topics)}개")
            return topics
        except Exception as e:
            logger.error(f"BCF 파일 처리 오류: {e}", exc_info=True)
            return []
    
    def add_ifc_nodes(self, entities: List[Dict[str, Any]]):
        """IFC 엔티티를 그래프에 추가."""
        graph = self.load_graph()
        added_count = 0
        updated_count = 0
        
        for entity in entities:
            guid = entity.get('GlobalId')
            if not guid:
                continue
            
            node_id = f"ifc:{guid}"
            
            if node_id in graph.nodes:
                # 기존 노드 업데이트
                graph.nodes[node_id].update({
                    'type': 'ifc',
                    'name': entity.get('Name', 'Unnamed'),
                    'ifc_type': entity.get('Type', 'Unknown'),
                    'updated_at': datetime.now().isoformat()
                })
                updated_count += 1
            else:
                # 새 노드 추가
                graph.add_node(node_id, **{
                    'type': 'ifc',
                    'guid': guid,
                    'name': entity.get('Name', 'Unnamed'),
                    'ifc_type': entity.get('Type', 'Unknown'),
                    'created_at': datetime.now().isoformat()
                })
                added_count += 1
        
        logger.info(f"IFC 노드 추가/업데이트: +{added_count}, ~{updated_count}")
        return added_count, updated_count
    
    def add_bcf_nodes(self, topics: List[Dict[str, Any]]):
        """BCF 토픽을 그래프에 추가."""
        graph = self.load_graph()
        added_count = 0
        updated_count = 0
        
        for topic in topics:
            topic_id = topic.get('Guid')
            if not topic_id:
                continue
            
            node_id = f"bcf:{topic_id}"
            
            if node_id in graph.nodes:
                # 기존 노드 업데이트
                graph.nodes[node_id].update({
                    'type': 'bcf',
                    'title': topic.get('Title', 'Untitled'),
                    'status': topic.get('TopicStatus', 'Open'),
                    'author': topic.get('CreationAuthor', 'Unknown'),
                    'updated_at': datetime.now().isoformat()
                })
                updated_count += 1
            else:
                # 새 노드 추가
                graph.add_node(node_id, **{
                    'type': 'bcf',
                    'guid': topic_id,
                    'title': topic.get('Title', 'Untitled'),
                    'description': topic.get('Description', ''),
                    'status': topic.get('TopicStatus', 'Open'),
                    'author': topic.get('CreationAuthor', 'Unknown'),
                    'created_at': topic.get('CreationDate', datetime.now().isoformat()),
                    'importance': 0.5
                })
                added_count += 1
            
            # BCF-IFC 링크 생성
            related_guids = topic.get('RelatedTopics', [])
            for related_guid in related_guids:
                ifc_node_id = f"ifc:{related_guid}"
                if ifc_node_id in graph.nodes:
                    if not graph.has_edge(node_id, ifc_node_id):
                        graph.add_edge(node_id, ifc_node_id, 
                                     relation='references',
                                     created_at=datetime.now().isoformat())
        
        logger.info(f"BCF 노드 추가/업데이트: +{added_count}, ~{updated_count}")
        return added_count, updated_count
    
    def remove_file_nodes(self, file_path: Path, file_type: str):
        """파일과 관련된 노드 제거."""
        graph = self.load_graph()
        
        # 파일 경로 기반으로 노드 식별 (실제로는 더 정교한 매핑 필요)
        # 여기서는 간단한 구현으로 진행
        removed_count = 0
        
        logger.info(f"{file_type.upper()} 파일 관련 노드 제거: {file_path.name}")
        logger.warning("파일 삭제 시 노드 제거는 향후 구현 예정")
        
        return removed_count
    
    def handle_file_change(self, event: FileChangeEvent):
        """파일 변경 이벤트 처리."""
        logger.info(f"파일 변경 처리: {event.change_type.value} - {event.path.name}")
        
        try:
            if event.change_type == FileChangeType.DELETED:
                # 삭제된 파일 처리
                self.remove_file_nodes(event.path, event.file_type)
            
            elif event.change_type in [FileChangeType.CREATED, FileChangeType.MODIFIED]:
                # 생성/수정된 파일 처리
                if event.file_type == 'ifc':
                    entities = self.process_ifc_file(event.path)
                    if entities:
                        self.add_ifc_nodes(entities)
                
                elif event.file_type == 'bcf':
                    topics = self.process_bcf_file(event.path)
                    if topics:
                        self.add_bcf_nodes(topics)
            
            # 그래프 저장
            self.save_graph()
            
            logger.info(f"파일 변경 처리 완료: {event.path.name}")
            
        except Exception as e:
            logger.error(f"파일 변경 처리 오류: {e}", exc_info=True)

