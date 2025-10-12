#!/usr/bin/env python3
"""
Gold Standard QA 템플릿을 실제 데이터로 채우기

실제 그래프 데이터를 기반으로 QA 쌍의 변수를 채움
"""

import json
import networkx as nx
from pathlib import Path
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any


class GoldStandardFiller:
    """Gold Standard 템플릿 채우기"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.eval_dir = self.base_dir / "eval"
        self.graph_path = self.base_dir / "data" / "processed" / "graph.gpickle"
        
        # 그래프 로드
        self.graph = self._load_graph()
        
        # 실제 데이터 추출
        self.ifc_nodes = []
        self.bcf_nodes = []
        self.extract_graph_data()
    
    def _load_graph(self):
        """그래프 로드"""
        if not self.graph_path.exists():
            print(f"⚠️  그래프 파일이 없습니다: {self.graph_path}")
            print(f"먼저 그래프를 생성하세요: python run_pipeline.py pipeline")
            return None
        
        import pickle
        with open(self.graph_path, 'rb') as f:
            graph = pickle.load(f)
        
        print(f"✅ 그래프 로드: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 엣지")
        return graph
    
    def extract_graph_data(self):
        """그래프에서 실제 데이터 추출"""
        if not self.graph:
            return
        
        for node, data in self.graph.nodes(data=True):
            # 노드 ID가 튜플 형태일 수 있음: ('IFC', 'guid') 또는 ('BCF', 'topic_id')
            if isinstance(node, tuple) and len(node) == 2:
                node_type, node_id = node
            else:
                node_type = data.get('type', '')
                node_id = node
            
            if node_type == 'IFC':
                self.ifc_nodes.append({
                    'node_id': node,  # 튜플 전체를 저장
                    'guid': data.get('guid', node_id),
                    'entity_type': data.get('type', 'Unknown'),  # IFC 노드의 type 필드 사용
                    'name': data.get('name', 'Unnamed'),
                    'data': data
                })
            elif node_type == 'BCF':
                self.bcf_nodes.append({
                    'node_id': node,  # 튜플 전체를 저장
                    'topic_id': node_id,
                    'title': data.get('title', 'No title'),
                    'author': data.get('author', 'Unknown'),
                    'status': data.get('status', 'Open'),
                    'creation_date': data.get('created', data.get('creation_date', '')),  # 'created' 필드도 확인
                    'data': data
                })
        
        print(f"  📐 IFC 노드: {len(self.ifc_nodes)}개")
        print(f"  📋 BCF 노드: {len(self.bcf_nodes)}개")
    
    def fill_qa_templates(self, qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """QA 템플릿을 실제 데이터로 채우기"""
        
        if not self.graph:
            print("⚠️  그래프 데이터가 없어 템플릿을 채울 수 없습니다.")
            return qa_pairs
        
        print(f"\n🔨 {len(qa_pairs)}개 QA 템플릿 채우기 중...")
        
        filled_qa = []
        
        for qa in qa_pairs:
            try:
                filled = self._fill_single_qa(qa)
                if filled:
                    filled_qa.append(filled)
            except Exception as e:
                print(f"  ⚠️  {qa['id']} 처리 실패: {e}")
        
        print(f"  ✅ {len(filled_qa)}개 QA 쌍 채우기 완료")
        
        return filled_qa
    
    def _fill_single_qa(self, qa: Dict[str, Any]) -> Dict[str, Any]:
        """단일 QA 쌍 채우기"""
        
        category = qa['category']
        subcategory = qa['subcategory']
        
        # 카테고리별 처리
        if category == 'entity_search':
            return self._fill_entity_search(qa, subcategory)
        elif category == 'relationship':
            return self._fill_relationship(qa, subcategory)
        elif category == 'temporal':
            return self._fill_temporal(qa, subcategory)
        elif category == 'forgetting':
            return self._fill_forgetting(qa, subcategory)
        elif category == 'change_impact':
            return self._fill_change_impact(qa, subcategory)
        elif category == 'complex':
            return self._fill_complex(qa, subcategory)
        
        return None
    
    def _fill_entity_search(self, qa: Dict[str, Any], subcategory: str) -> Dict[str, Any]:
        """Entity search QA 채우기"""
        
        if subcategory == 'ifc_lookup' and self.ifc_nodes:
            node = random.choice(self.ifc_nodes)
            question = qa['question'].format(guid=node['guid'])
            answer = qa['answer'].format(
                guid=node['guid'],
                entity_type=node['entity_type'],
                name=node['name']
            )
            
            qa_filled = qa.copy()
            qa_filled['question'] = question
            qa_filled['answer'] = answer
            qa_filled['status'] = 'filled'
            qa_filled['ground_truth'] = {
                'guid': node['guid'],
                'entity_type': node['entity_type'],
                'name': node['name']
            }
            return qa_filled
        
        elif subcategory == 'bcf_issue_lookup' and self.ifc_nodes:
            node = random.choice(self.ifc_nodes)
            guid = node['guid']
            
            # 연결된 BCF 이슈 찾기
            related_issues = []
            if self.graph.has_node(guid):
                for predecessor in self.graph.predecessors(guid):
                    pred_data = self.graph.nodes[predecessor]
                    if pred_data.get('type') == 'BCF':
                        related_issues.append(pred_data.get('title', predecessor))
            
            if related_issues:
                question = qa['question'].format(guid=guid)
                answer = qa['answer'].format(
                    count=len(related_issues),
                    issue_list=', '.join(related_issues[:3])  # 처음 3개만
                )
                
                qa_filled = qa.copy()
                qa_filled['question'] = question
                qa_filled['answer'] = answer
                qa_filled['status'] = 'filled'
                qa_filled['ground_truth'] = {
                    'guid': guid,
                    'issues': related_issues
                }
                return qa_filled
        
        return None
    
    def _fill_relationship(self, qa: Dict[str, Any], subcategory: str) -> Dict[str, Any]:
        """Relationship QA 채우기"""
        
        if subcategory == 'connected_components' and self.ifc_nodes:
            node = random.choice(self.ifc_nodes)
            name = node['name']
            node_id = node['node_id']  # 튜플 형태의 노드 ID 사용
            
            # 연결된 노드 찾기 (Directed Graph 고려)
            connected = []
            if self.graph.has_node(node_id):
                # successors (나가는 방향)
                for neighbor in self.graph.neighbors(node_id):
                    neighbor_data = self.graph.nodes[neighbor]
                    if isinstance(neighbor, tuple) and len(neighbor) == 2:
                        neighbor_type, neighbor_id = neighbor
                        if neighbor_type == 'IFC':
                            connected.append(neighbor_data.get('name', neighbor_id))
                        elif neighbor_type == 'BCF':
                            connected.append(neighbor_data.get('title', neighbor_id))
                
                # predecessors (들어오는 방향)
                for predecessor in self.graph.predecessors(node_id):
                    pred_data = self.graph.nodes[predecessor]
                    if isinstance(predecessor, tuple) and len(predecessor) == 2:
                        pred_type, pred_id = predecessor
                        if pred_type == 'IFC':
                            connected.append(pred_data.get('name', pred_id))
                        elif pred_type == 'BCF':
                            connected.append(pred_data.get('title', pred_id))
            
            if connected:
                question = qa['question'].format(entity_name=name)
                answer = qa['answer'].format(
                    entity_name=name,
                    connected_list=', '.join(connected[:5])  # 처음 5개만
                )
                
                qa_filled = qa.copy()
                qa_filled['question'] = question
                qa_filled['answer'] = answer
                qa_filled['status'] = 'filled'
                qa_filled['ground_truth'] = {
                    'entity_name': name,
                    'connected': connected
                }
                return qa_filled
        
        return None
    
    def _fill_temporal(self, qa: Dict[str, Any], subcategory: str) -> Dict[str, Any]:
        """Temporal QA 채우기"""
        
        days = random.choice([7, 14, 30, 60, 90])
        
        if subcategory == 'recent_issues' and self.bcf_nodes:
            # 날짜가 있는 BCF 노드 필터링
            now = datetime.now()
            recent_issues = []
            
            for bcf in self.bcf_nodes:
                creation_date = bcf.get('creation_date', '')
                if creation_date:
                    try:
                        date = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                        if (now - date).days <= days:
                            recent_issues.append(bcf['title'])
                    except:
                        pass
            
            if recent_issues:
                question = qa['question'].format(days=days)
                answer = qa['answer'].format(
                    days=days,
                    count=len(recent_issues),
                    issue_list=', '.join(recent_issues[:5])
                )
                
                qa_filled = qa.copy()
                qa_filled['question'] = question
                qa_filled['answer'] = answer
                qa_filled['status'] = 'filled'
                qa_filled['ground_truth'] = {
                    'days': days,
                    'issues': recent_issues
                }
                return qa_filled
        
        elif subcategory == 'old_issues' and self.bcf_nodes:
            now = datetime.now()
            old_issues = []
            
            for bcf in self.bcf_nodes:
                creation_date = bcf.get('creation_date', '')
                if creation_date:
                    try:
                        date = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                        if (now - date).days > days:
                            old_issues.append(bcf['title'])
                    except:
                        pass
            
            if old_issues:
                question = qa['question'].format(days=days)
                answer = qa['answer'].format(
                    days=days,
                    count=len(old_issues),
                    issue_list=', '.join(old_issues[:5])
                )
                
                qa_filled = qa.copy()
                qa_filled['question'] = question
                qa_filled['answer'] = answer
                qa_filled['status'] = 'filled'
                qa_filled['ground_truth'] = {
                    'days': days,
                    'issues': old_issues
                }
                return qa_filled
        
        return None
    
    def _fill_forgetting(self, qa: Dict[str, Any], subcategory: str) -> Dict[str, Any]:
        """Forgetting QA 채우기"""
        
        if subcategory == 'ttl_filter' and self.bcf_nodes:
            ttl = random.choice([30, 60, 90])
            now = datetime.now()
            valid_issues = []
            
            for bcf in self.bcf_nodes:
                creation_date = bcf.get('creation_date', '')
                if creation_date:
                    try:
                        date = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                        if (now - date).days <= ttl:
                            valid_issues.append(bcf['title'])
                    except:
                        pass
            
            if valid_issues:
                question = qa['question'].format(ttl=ttl)
                answer = qa['answer'].format(
                    ttl=ttl,
                    count=len(valid_issues),
                    issue_list=', '.join(valid_issues[:5])
                )
                
                qa_filled = qa.copy()
                qa_filled['question'] = question
                qa_filled['answer'] = answer
                qa_filled['status'] = 'filled'
                qa_filled['ground_truth'] = {
                    'ttl': ttl,
                    'valid_issues': valid_issues
                }
                return qa_filled
        
        return None
    
    def _fill_change_impact(self, qa: Dict[str, Any], subcategory: str) -> Dict[str, Any]:
        """Change impact QA 채우기 (간단한 버전)"""
        
        if subcategory == 'multi_hop' and self.ifc_nodes:
            node = random.choice(self.ifc_nodes)
            name = node['name']
            node_id = node['node_id']  # 튜플 형태의 노드 ID 사용
            
            # 2-hop 이웃 찾기 (Directed Graph 고려)
            affected = set()
            if self.graph.has_node(node_id):
                # 1-hop: successors + predecessors
                for neighbor in self.graph.neighbors(node_id):
                    affected.add(neighbor)
                for predecessor in self.graph.predecessors(node_id):
                    affected.add(predecessor)
                
                # 2-hop: 각 이웃의 이웃들
                for neighbor in list(affected):
                    for second_neighbor in self.graph.neighbors(neighbor):
                        affected.add(second_neighbor)
                    for second_predecessor in self.graph.predecessors(neighbor):
                        affected.add(second_predecessor)
            
            if affected:
                affected_names = []
                for aff_node in list(affected)[:5]:
                    aff_data = self.graph.nodes.get(aff_node, {})
                    if isinstance(aff_node, tuple) and len(aff_node) == 2:
                        aff_type, aff_id = aff_node
                        if aff_type == 'IFC':
                            affected_names.append(aff_data.get('name', aff_id))
                        elif aff_type == 'BCF':
                            affected_names.append(aff_data.get('title', aff_id))
                    else:
                        affected_names.append(str(aff_node))
                
                question = qa['question'].format(entity_name=name)
                answer = qa['answer'].format(
                    entity_name=name,
                    affected_list=', '.join(affected_names)
                )
                
                qa_filled = qa.copy()
                qa_filled['question'] = question
                qa_filled['answer'] = answer
                qa_filled['status'] = 'filled'
                qa_filled['ground_truth'] = {
                    'entity_name': name,
                    'affected': list(affected)
                }
                return qa_filled
        
        return None
    
    def _fill_complex(self, qa: Dict[str, Any], subcategory: str) -> Dict[str, Any]:
        """Complex QA 채우기"""
        
        if subcategory == 'statistics':
            ifc_count = len(self.ifc_nodes)
            bcf_count = len(self.bcf_nodes)
            resolved_count = len([b for b in self.bcf_nodes if b['status'] in ['Resolved', 'Closed']])
            
            question = qa['question']
            answer = qa['answer'].format(
                ifc_count=ifc_count,
                bcf_count=bcf_count,
                resolved_count=resolved_count
            )
            
            qa_filled = qa.copy()
            qa_filled['question'] = question
            qa_filled['answer'] = answer
            qa_filled['status'] = 'filled'
            qa_filled['ground_truth'] = {
                'ifc_count': ifc_count,
                'bcf_count': bcf_count,
                'resolved_count': resolved_count
            }
            return qa_filled
        
        elif subcategory == 'author_activity' and self.bcf_nodes:
            # 작성자별 그룹화
            authors = {}
            for bcf in self.bcf_nodes:
                author = bcf['author']
                if author not in authors:
                    authors[author] = []
                authors[author].append(bcf['title'])
            
            if authors:
                author = random.choice(list(authors.keys()))
                issues = authors[author]
                
                question = qa['question'].format(author=author)
                answer = qa['answer'].format(
                    author=author,
                    count=len(issues),
                    issue_list=', '.join(issues[:5])
                )
                
                qa_filled = qa.copy()
                qa_filled['question'] = question
                qa_filled['answer'] = answer
                qa_filled['status'] = 'filled'
                qa_filled['ground_truth'] = {
                    'author': author,
                    'issues': issues
                }
                return qa_filled
        
        return None


def main():
    """메인 실행"""
    
    base_dir = Path(__file__).parent.parent
    filler = GoldStandardFiller(base_dir)
    
    print("=" * 70)
    print("📝 Gold Standard QA 템플릿 채우기")
    print("=" * 70)
    print()
    
    # 1. 기존 템플릿 로드
    gold_path = base_dir / "eval" / "gold_standard.jsonl"
    
    if not gold_path.exists():
        print(f"❌ Gold Standard 파일이 없습니다: {gold_path}")
        print("먼저 생성하세요: python eval/gold_standard_generator.py")
        return
    
    qa_pairs = []
    with open(gold_path, 'r', encoding='utf-8') as f:
        for line in f:
            qa_pairs.append(json.loads(line))
    
    print(f"✅ {len(qa_pairs)}개 QA 템플릿 로드")
    
    # 2. 실제 데이터로 채우기
    filled_qa = filler.fill_qa_templates(qa_pairs)
    
    # 3. 저장
    filled_path = base_dir / "eval" / "gold.jsonl"
    with open(filled_path, 'w', encoding='utf-8') as f:
        for qa in filled_qa:
            f.write(json.dumps(qa, ensure_ascii=False) + '\n')
    
    print(f"\n💾 저장 완료: {filled_path}")
    
    # 통계
    filled_count = len([qa for qa in filled_qa if qa['status'] == 'filled'])
    
    print()
    print("=" * 70)
    print("✅ Gold Standard 채우기 완료")
    print("=" * 70)
    print(f"""
📊 결과:
  - 템플릿: {len(qa_pairs)}개
  - 채워진 QA: {filled_count}개
  - 성공률: {filled_count/len(qa_pairs)*100:.1f}%

📂 파일:
  - {filled_path}

📝 다음 단계:
  1. 평가 메트릭 구현
     → python eval/metrics.py
  
  2. 벤치마크 실행
     → python eval/run_benchmark.py
""")


if __name__ == "__main__":
    main()

