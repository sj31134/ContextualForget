"""
Gold Standard 확장: 100개 → 200개
기존 카테고리 분포를 유지하면서 추가 100개 QA 생성
"""

import json
import pickle
import random
from pathlib import Path
from collections import defaultdict
import sys

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import read_jsonl, write_jsonl


def load_graph(graph_path: str):
    """그래프 로드"""
    with open(graph_path, 'rb') as f:
        return pickle.load(f)


def extract_additional_samples(graph, existing_samples: set, target_counts: dict):
    """
    추가 샘플 추출
    
    Args:
        graph: NetworkX 그래프
        existing_samples: 기존에 사용된 샘플 ID 집합
        target_counts: 카테고리별 목표 개수
    
    Returns:
        카테고리별 추가 샘플 리스트
    """
    samples = {
        'entity_search': [],
        'issue_search': [],
        'relationship': []
    }
    
    # IFC 노드 추출 (entity_search용)
    ifc_nodes = [
        (node_id, data) for node_id, data in graph.nodes(data=True)
        if isinstance(node_id, tuple) and node_id[0] == 'IFC' and node_id not in existing_samples
    ]
    random.shuffle(ifc_nodes)
    
    for node_id, data in ifc_nodes[:target_counts['entity_search']]:
        samples['entity_search'].append({
            'node_id': node_id,
            'data': data,
            'type': 'IFC'
        })
        existing_samples.add(node_id)
    
    # BCF 노드 추출 (issue_search용)
    bcf_nodes = [
        (node_id, data) for node_id, data in graph.nodes(data=True)
        if isinstance(node_id, tuple) and node_id[0] == 'BCF' and node_id not in existing_samples
    ]
    random.shuffle(bcf_nodes)
    
    for node_id, data in bcf_nodes[:target_counts['issue_search']]:
        samples['issue_search'].append({
            'node_id': node_id,
            'data': data,
            'type': 'BCF'
        })
        existing_samples.add(node_id)
    
    # 연결된 BCF-IFC 쌍 추출 (relationship용)
    connected_pairs = []
    for bcf_node in bcf_nodes:
        bcf_id = bcf_node[0]
        if bcf_id in existing_samples:
            continue
        
        neighbors = list(graph.neighbors(bcf_id))
        if neighbors:
            for ifc_id in neighbors:
                if ifc_id not in existing_samples:
                    connected_pairs.append({
                        'bcf_node': bcf_id,
                        'bcf_data': bcf_node[1],
                        'ifc_node': ifc_id,
                        'ifc_data': graph.nodes[ifc_id]
                    })
                    break
    
    random.shuffle(connected_pairs)
    for pair in connected_pairs[:target_counts['relationship']]:
        samples['relationship'].append(pair)
        existing_samples.add(pair['bcf_node'])
        existing_samples.add(pair['ifc_node'])
    
    return samples


def generate_qa_with_llm(samples: dict, start_id: int = 100):
    """
    LLM으로 QA 생성 (qwen2.5:3b 사용)
    
    Args:
        samples: 카테고리별 샘플 딕셔너리
        start_id: 시작 ID
    
    Returns:
        생성된 QA 리스트
    """
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        print("⚠️  langchain_ollama를 가져올 수 없습니다. 템플릿 QA를 생성합니다.")
        return generate_template_qa(samples, start_id)
    
    qa_list = []
    current_id = start_id
    
    llm = ChatOllama(model="qwen2.5:3b", temperature=0.3)
    
    # Entity Search QA 생성
    print("\n📝 Entity Search QA 생성 중...")
    for i, sample in enumerate(samples['entity_search']):
        node_id = sample['node_id']
        data = sample['data']
        
        # GUID 추출
        guid = node_id[1] if isinstance(node_id, tuple) else node_id
        entity_type = data.get('type', 'Unknown')
        entity_name = data.get('name', 'Unknown')
        
        prompt = f"""다음 IFC 엔티티에 대한 한국어 질문-답변 쌍을 생성하세요.

GUID: {guid}
타입: {entity_type}
이름: {entity_name}

질문은 이 엔티티의 속성을 묻는 형태로 작성하세요.
답변은 간결하고 정확하게 작성하세요.

형식:
질문: [질문]
답변: [답변]
"""
        
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            # 질문과 답변 추출
            lines = content.split('\n')
            question = ""
            answer = ""
            
            for line in lines:
                if line.startswith('질문:'):
                    question = line.replace('질문:', '').strip()
                elif line.startswith('답변:'):
                    answer = line.replace('답변:', '').strip()
            
            if not question:
                question = f"이 GUID의 엔티티 타입은 무엇인가요?"
            if not answer:
                answer = f"{entity_type}입니다."
            
            qa_list.append({
                'question': question,
                'answer': answer,
                'gold_entities': [guid],
                'id': f'qa_llm_{current_id:03d}',
                'category': 'entity_search',
                'metadata': {
                    'llm_generated': True,
                    'model': 'qwen2.5:3b',
                    'validated': False,
                    'sample_index': i
                }
            })
            current_id += 1
            
            if (i + 1) % 10 == 0:
                print(f"   진행: {i+1}/{len(samples['entity_search'])}")
        
        except Exception as e:
            print(f"   ⚠️  LLM 호출 실패 (샘플 {i}): {e}")
            # Fallback to template
            qa_list.append({
                'question': f"이 GUID의 엔티티 타입은 무엇인가요?",
                'answer': f"{entity_type}입니다.",
                'gold_entities': [guid],
                'id': f'qa_llm_{current_id:03d}',
                'category': 'entity_search',
                'metadata': {
                    'llm_generated': False,
                    'model': 'template',
                    'validated': False,
                    'sample_index': i
                }
            })
            current_id += 1
    
    # Issue Search QA 생성
    print("\n📝 Issue Search QA 생성 중...")
    for i, sample in enumerate(samples['issue_search']):
        node_id = sample['node_id']
        data = sample['data']
        
        topic_id = node_id[1] if isinstance(node_id, tuple) else node_id
        title = data.get('title', 'Unknown Issue')
        description = data.get('description', '')[:200]
        
        prompt = f"""다음 BIM 이슈에 대한 한국어 질문-답변 쌍을 생성하세요.

제목: {title}
설명: {description}

질문은 이 이슈의 내용이나 상태를 묻는 형태로 작성하세요.
답변은 간결하고 정확하게 작성하세요.

형식:
질문: [질문]
답변: [답변]
"""
        
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            lines = content.split('\n')
            question = ""
            answer = ""
            
            for line in lines:
                if line.startswith('질문:'):
                    question = line.replace('질문:', '').strip()
                elif line.startswith('답변:'):
                    answer = line.replace('답변:', '').strip()
            
            if not question:
                question = f"이 이슈의 제목은 무엇인가요?"
            if not answer:
                answer = f"{title}입니다."
            
            qa_list.append({
                'question': question,
                'answer': answer,
                'gold_entities': [topic_id],
                'id': f'qa_llm_{current_id:03d}',
                'category': 'issue_search',
                'metadata': {
                    'llm_generated': True,
                    'model': 'qwen2.5:3b',
                    'validated': False,
                    'sample_index': i
                }
            })
            current_id += 1
            
            if (i + 1) % 10 == 0:
                print(f"   진행: {i+1}/{len(samples['issue_search'])}")
        
        except Exception as e:
            print(f"   ⚠️  LLM 호출 실패 (샘플 {i}): {e}")
            qa_list.append({
                'question': f"이 이슈의 제목은 무엇인가요?",
                'answer': f"{title}입니다.",
                'gold_entities': [topic_id],
                'id': f'qa_llm_{current_id:03d}',
                'category': 'issue_search',
                'metadata': {
                    'llm_generated': False,
                    'model': 'template',
                    'validated': False,
                    'sample_index': i
                }
            })
            current_id += 1
    
    # Relationship QA 생성
    print("\n📝 Relationship QA 생성 중...")
    for i, pair in enumerate(samples['relationship']):
        bcf_id = pair['bcf_node'][1] if isinstance(pair['bcf_node'], tuple) else pair['bcf_node']
        ifc_id = pair['ifc_node'][1] if isinstance(pair['ifc_node'], tuple) else pair['ifc_node']
        
        bcf_title = pair['bcf_data'].get('title', 'Unknown Issue')
        ifc_type = pair['ifc_data'].get('type', 'Unknown')
        
        prompt = f"""다음 BIM 이슈와 IFC 엔티티의 관계에 대한 한국어 질문-답변 쌍을 생성하세요.

이슈: {bcf_title}
엔티티 타입: {ifc_type}

질문은 이슈와 엔티티의 관계를 묻는 형태로 작성하세요.
답변은 간결하고 정확하게 작성하세요.

형식:
질문: [질문]
답변: [답변]
"""
        
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            lines = content.split('\n')
            question = ""
            answer = ""
            
            for line in lines:
                if line.startswith('질문:'):
                    question = line.replace('질문:', '').strip()
                elif line.startswith('답변:'):
                    answer = line.replace('답변:', '').strip()
            
            if not question:
                question = f"이 이슈와 관련된 엔티티는 무엇인가요?"
            if not answer:
                answer = f"{ifc_type} 엔티티가 관련되어 있습니다."
            
            qa_list.append({
                'question': question,
                'answer': answer,
                'gold_entities': [bcf_id, ifc_id],
                'id': f'qa_llm_{current_id:03d}',
                'category': 'relationship',
                'metadata': {
                    'llm_generated': True,
                    'model': 'qwen2.5:3b',
                    'validated': False,
                    'sample_index': i
                }
            })
            current_id += 1
            
            if (i + 1) % 10 == 0:
                print(f"   진행: {i+1}/{len(samples['relationship'])}")
        
        except Exception as e:
            print(f"   ⚠️  LLM 호출 실패 (샘플 {i}): {e}")
            qa_list.append({
                'question': f"이 이슈와 관련된 엔티티는 무엇인가요?",
                'answer': f"{ifc_type} 엔티티가 관련되어 있습니다.",
                'gold_entities': [bcf_id, ifc_id],
                'id': f'qa_llm_{current_id:03d}',
                'category': 'relationship',
                'metadata': {
                    'llm_generated': False,
                    'model': 'template',
                    'validated': False,
                    'sample_index': i
                }
            })
            current_id += 1
    
    return qa_list


def generate_template_qa(samples: dict, start_id: int = 100):
    """템플릿 기반 QA 생성 (LLM 사용 불가 시)"""
    qa_list = []
    current_id = start_id
    
    # Entity Search
    for i, sample in enumerate(samples['entity_search']):
        node_id = sample['node_id']
        data = sample['data']
        guid = node_id[1] if isinstance(node_id, tuple) else node_id
        entity_type = data.get('type', 'Unknown')
        
        qa_list.append({
            'question': f"이 GUID의 엔티티 타입은 무엇인가요?",
            'answer': f"{entity_type}입니다.",
            'gold_entities': [guid],
            'id': f'qa_template_{current_id:03d}',
            'category': 'entity_search',
            'metadata': {
                'llm_generated': False,
                'model': 'template',
                'validated': False,
                'sample_index': i
            }
        })
        current_id += 1
    
    # Issue Search
    for i, sample in enumerate(samples['issue_search']):
        node_id = sample['node_id']
        data = sample['data']
        topic_id = node_id[1] if isinstance(node_id, tuple) else node_id
        title = data.get('title', 'Unknown Issue')
        
        qa_list.append({
            'question': f"이 이슈의 제목은 무엇인가요?",
            'answer': f"{title}입니다.",
            'gold_entities': [topic_id],
            'id': f'qa_template_{current_id:03d}',
            'category': 'issue_search',
            'metadata': {
                'llm_generated': False,
                'model': 'template',
                'validated': False,
                'sample_index': i
            }
        })
        current_id += 1
    
    # Relationship
    for i, pair in enumerate(samples['relationship']):
        bcf_id = pair['bcf_node'][1] if isinstance(pair['bcf_node'], tuple) else pair['bcf_node']
        ifc_id = pair['ifc_node'][1] if isinstance(pair['ifc_node'], tuple) else pair['ifc_node']
        ifc_type = pair['ifc_data'].get('type', 'Unknown')
        
        qa_list.append({
            'question': f"이 이슈와 관련된 엔티티는 무엇인가요?",
            'answer': f"{ifc_type} 엔티티가 관련되어 있습니다.",
            'gold_entities': [bcf_id, ifc_id],
            'id': f'qa_template_{current_id:03d}',
            'category': 'relationship',
            'metadata': {
                'llm_generated': False,
                'model': 'template',
                'validated': False,
                'sample_index': i
            }
        })
        current_id += 1
    
    return qa_list


def main():
    print("📊 Gold Standard 확장: 100개 → 200개\n")
    
    # 그래프 로드
    graph_path = 'data/processed/graph.gpickle'
    print(f"1. 그래프 로드: {graph_path}")
    graph = load_graph(graph_path)
    print(f"   ✅ 노드: {graph.number_of_nodes():,}개, 엣지: {graph.number_of_edges():,}개\n")
    
    # 기존 QA 로드
    existing_qa_path = 'eval/gold_standard_v2.jsonl'
    print(f"2. 기존 Gold Standard 로드: {existing_qa_path}")
    existing_qa = list(read_jsonl(existing_qa_path))
    print(f"   ✅ {len(existing_qa)}개\n")
    
    # 기존 샘플 ID 추출
    existing_samples = set()
    for qa in existing_qa:
        for entity in qa.get('gold_entities', []):
            # 튜플 형식으로 변환
            if not isinstance(entity, tuple):
                # IFC 또는 BCF 타입 추론 필요
                # 일단 문자열로 추가
                existing_samples.add(entity)
    
    # 추가 샘플 추출
    target_counts = {
        'entity_search': 30,  # 30개 추가
        'issue_search': 30,   # 30개 추가
        'relationship': 40    # 40개 추가
    }
    
    print("3. 추가 샘플 추출")
    samples = extract_additional_samples(graph, existing_samples, target_counts)
    print(f"   ✅ Entity Search: {len(samples['entity_search'])}개")
    print(f"   ✅ Issue Search: {len(samples['issue_search'])}개")
    print(f"   ✅ Relationship: {len(samples['relationship'])}개\n")
    
    # QA 생성
    print("4. QA 생성 (LLM 사용)")
    new_qa = generate_qa_with_llm(samples, start_id=100)
    print(f"   ✅ 총 {len(new_qa)}개 생성\n")
    
    # 병합
    print("5. 기존 QA와 병합")
    all_qa = existing_qa + new_qa
    print(f"   ✅ 총 {len(all_qa)}개\n")
    
    # 저장
    output_path = 'eval/gold_standard_v3.jsonl'
    print(f"6. 저장: {output_path}")
    write_jsonl(output_path, all_qa)
    print(f"   ✅ 저장 완료\n")
    
    # 통계
    print("=" * 60)
    print("📈 최종 통계")
    print("=" * 60)
    from collections import Counter
    categories = [qa['category'] for qa in all_qa]
    counter = Counter(categories)
    for cat, count in sorted(counter.items()):
        print(f"  {cat}: {count}개 ({count/len(all_qa)*100:.1f}%)")
    print(f"\n  총 {len(all_qa)}개")
    
    # 검증 보고서
    validation_report = {
        'total_qa': len(all_qa),
        'original_qa': len(existing_qa),
        'new_qa': len(new_qa),
        'category_distribution': dict(counter),
        'balance_check': {
            cat: abs(count / len(all_qa) - 1/3) <= 0.1
            for cat, count in counter.items()
        }
    }
    
    validation_path = 'eval/gold_standard_validation.json'
    with open(validation_path, 'w') as f:
        json.dump(validation_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 검증 보고서 저장: {validation_path}")
    print("\n" + "=" * 60)
    print("✅ Gold Standard 확장 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()

