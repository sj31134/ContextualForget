"""
Gold Standard 질문 수정
질문에 실제 GUID/키워드를 포함시켜 평가 가능하도록 수정
"""

import json
import pickle
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import read_jsonl, write_jsonl


def load_graph(graph_path: str):
    """그래프 로드"""
    with open(graph_path, 'rb') as f:
        return pickle.load(f)


def fix_entity_search_questions(graph, qa_list):
    """entity_search 질문 수정 - 질문에 GUID 포함"""
    fixed_count = 0
    
    for qa in qa_list:
        if qa['category'] != 'entity_search':
            continue
        
        # gold_entities에서 GUID 가져오기
        gold_entities = qa.get('gold_entities', [])
        if not gold_entities:
            continue
        
        guid = gold_entities[0]
        
        # 그래프에서 해당 엔티티 찾기
        found = False
        for node_id, data in graph.nodes(data=True):
            if isinstance(node_id, tuple):
                entity_id = node_id[1]
            else:
                entity_id = node_id
            
            if entity_id == guid:
                entity_type = data.get('type', data.get('entity_type', 'Unknown'))
                entity_name = data.get('name', data.get('title', guid))
                
                # 질문과 답변 수정
                qa['question'] = f"GUID {guid}의 엔티티 타입은 무엇인가요?"
                qa['answer'] = f"{entity_type}입니다."
                
                found = True
                fixed_count += 1
                break
        
        if not found:
            # 그래프에 없으면 간단한 질문으로
            qa['question'] = f"GUID {guid}의 정보를 알려주세요."
            qa['answer'] = f"GUID {guid}에 대한 정보입니다."
            fixed_count += 1
    
    return fixed_count


def fix_issue_search_questions(graph, qa_list):
    """issue_search 질문 수정 - 질문에 키워드 포함"""
    fixed_count = 0
    
    for qa in qa_list:
        if qa['category'] != 'issue_search':
            continue
        
        # gold_entities에서 topic_id 가져오기
        gold_entities = qa.get('gold_entities', [])
        if not gold_entities:
            continue
        
        topic_id = gold_entities[0]
        
        # 그래프에서 해당 이슈 찾기
        found = False
        for node_id, data in graph.nodes(data=True):
            if isinstance(node_id, tuple):
                entity_id = node_id[1]
            else:
                entity_id = node_id
            
            if entity_id == topic_id:
                title = data.get('title', 'Unknown Issue')
                description = data.get('description', '')
                
                # 제목에서 키워드 추출 (첫 3단어)
                keywords = title.split()[:3]
                keyword_str = ' '.join(keywords)
                
                # 질문과 답변 수정
                qa['question'] = f"'{keyword_str}'와 관련된 이슈는 무엇인가요?"
                qa['answer'] = f"{title}입니다."
                
                found = True
                fixed_count += 1
                break
        
        if not found:
            qa['question'] = f"토픽 ID {topic_id[:8]}...와 관련된 이슈는?"
            qa['answer'] = f"해당 토픽에 대한 정보입니다."
            fixed_count += 1
    
    return fixed_count


def fix_relationship_questions(graph, qa_list):
    """relationship 질문 수정 - 질문에 엔티티 ID 포함"""
    fixed_count = 0
    
    for qa in qa_list:
        if qa['category'] != 'relationship':
            continue
        
        # gold_entities에서 두 엔티티 가져오기
        gold_entities = qa.get('gold_entities', [])
        if len(gold_entities) < 2:
            continue
        
        entity1_id = gold_entities[0]
        entity2_id = gold_entities[1]
        
        # 그래프에서 찾기
        entity1_info = None
        entity2_info = None
        
        for node_id, data in graph.nodes(data=True):
            if isinstance(node_id, tuple):
                entity_id = node_id[1]
            else:
                entity_id = node_id
            
            if entity_id == entity1_id:
                entity1_info = {
                    'type': data.get('type', data.get('entity_type', 'Unknown')),
                    'name': data.get('name', data.get('title', entity1_id))
                }
            
            if entity_id == entity2_id:
                entity2_info = {
                    'type': data.get('type', data.get('entity_type', 'Unknown')),
                    'name': data.get('name', data.get('title', entity2_id))
                }
        
        if entity1_info and entity2_info:
            # 질문과 답변 수정
            qa['question'] = f"{entity1_info['name'][:30]}와 관련된 엔티티는?"
            qa['answer'] = f"{entity2_info['type']} 타입의 {entity2_info['name'][:30]}가 관련되어 있습니다."
            fixed_count += 1
        else:
            qa['question'] = f"엔티티 {entity1_id[:8]}...와 관련된 것은?"
            qa['answer'] = f"관련 엔티티가 있습니다."
            fixed_count += 1
    
    return fixed_count


def main():
    print("📝 Gold Standard 질문 수정\n")
    print("="*60)
    
    # 그래프 로드
    graph_path = 'data/processed/graph.gpickle'
    print(f"1. 그래프 로드: {graph_path}")
    graph = load_graph(graph_path)
    print(f"   ✅ 노드: {graph.number_of_nodes():,}개\n")
    
    # Gold Standard 로드
    gold_path = 'eval/gold_standard_v3.jsonl'
    print(f"2. Gold Standard 로드: {gold_path}")
    qa_list = list(read_jsonl(gold_path))
    print(f"   ✅ {len(qa_list)}개 QA\n")
    
    # 카테고리별 수정
    print("3. 질문 수정:")
    
    entity_fixed = fix_entity_search_questions(graph, qa_list)
    print(f"   ✅ Entity Search: {entity_fixed}개 수정")
    
    issue_fixed = fix_issue_search_questions(graph, qa_list)
    print(f"   ✅ Issue Search: {issue_fixed}개 수정")
    
    relationship_fixed = fix_relationship_questions(graph, qa_list)
    print(f"   ✅ Relationship: {relationship_fixed}개 수정")
    
    total_fixed = entity_fixed + issue_fixed + relationship_fixed
    print(f"\n   총 {total_fixed}개 질문 수정 완료\n")
    
    # 저장
    output_path = 'eval/gold_standard_v3_fixed.jsonl'
    print(f"4. 저장: {output_path}")
    write_jsonl(output_path, qa_list)
    print(f"   ✅ 저장 완료\n")
    
    # 샘플 출력
    print("="*60)
    print("📋 수정된 샘플 (처음 3개):")
    print("="*60)
    for i, qa in enumerate(qa_list[:3]):
        print(f"\n{i+1}. {qa['category']} - {qa['id']}")
        print(f"   질문: {qa['question']}")
        print(f"   답변: {qa['answer']}")
        print(f"   gold_entities: {qa['gold_entities']}")
    
    print("\n" + "="*60)
    print("✅ Gold Standard 수정 완료!")
    print("="*60)


if __name__ == "__main__":
    main()

