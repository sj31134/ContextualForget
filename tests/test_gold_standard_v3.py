"""
Gold Standard v3 검증 단위 테스트
200개 QA의 품질과 균형 검증
"""

import json
import pytest
from pathlib import Path
from collections import Counter


def test_gold_standard_exists():
    """Gold Standard v3 파일이 존재하는지 확인"""
    path = Path('eval/gold_standard_v3.jsonl')
    assert path.exists(), "gold_standard_v3.jsonl 파일이 존재하지 않습니다"


def test_gold_standard_count():
    """QA 개수가 200개인지 확인"""
    qa_list = []
    with open('eval/gold_standard_v3.jsonl', 'r') as f:
        for line in f:
            qa_list.append(json.loads(line))
    
    assert len(qa_list) == 200, f"QA 개수가 200개가 아닙니다: {len(qa_list)}개"


def test_gold_standard_category_balance():
    """카테고리 분포가 균형 있는지 확인 (각 ±10% 이내)"""
    categories = []
    with open('eval/gold_standard_v3.jsonl', 'r') as f:
        for line in f:
            qa = json.loads(line)
            categories.append(qa.get('category', 'unknown'))
    
    counter = Counter(categories)
    total = len(categories)
    
    # entity_search: 30% ± 10%
    entity_ratio = counter['entity_search'] / total
    assert 0.20 <= entity_ratio <= 0.40, \
        f"entity_search 비율이 범위를 벗어났습니다: {entity_ratio:.2%}"
    
    # issue_search: 30% ± 10%
    issue_ratio = counter['issue_search'] / total
    assert 0.20 <= issue_ratio <= 0.40, \
        f"issue_search 비율이 범위를 벗어났습니다: {issue_ratio:.2%}"
    
    # relationship: 40% ± 10%
    relationship_ratio = counter['relationship'] / total
    assert 0.30 <= relationship_ratio <= 0.50, \
        f"relationship 비율이 범위를 벗어났습니다: {relationship_ratio:.2%}"


def test_gold_standard_required_fields():
    """필수 필드가 모두 있는지 확인"""
    required_fields = ['question', 'answer', 'gold_entities', 'id', 'category']
    
    with open('eval/gold_standard_v3.jsonl', 'r') as f:
        for i, line in enumerate(f):
            qa = json.loads(line)
            
            for field in required_fields:
                assert field in qa, \
                    f"QA {i}에 필수 필드 '{field}'가 없습니다"
            
            assert isinstance(qa['gold_entities'], list), \
                f"QA {i}의 gold_entities가 리스트가 아닙니다"
            
            assert len(qa['gold_entities']) > 0, \
                f"QA {i}의 gold_entities가 비어있습니다"


def test_gold_standard_unique_ids():
    """모든 QA ID가 유일한지 확인"""
    ids = []
    with open('eval/gold_standard_v3.jsonl', 'r') as f:
        for line in f:
            qa = json.loads(line)
            ids.append(qa['id'])
    
    unique_ids = set(ids)
    assert len(ids) == len(unique_ids), \
        f"중복된 ID가 있습니다: {len(ids)} != {len(unique_ids)}"


def test_gold_standard_no_empty_strings():
    """질문과 답변이 비어있지 않은지 확인"""
    with open('eval/gold_standard_v3.jsonl', 'r') as f:
        for i, line in enumerate(f):
            qa = json.loads(line)
            
            assert qa['question'].strip() != "", \
                f"QA {i}의 질문이 비어있습니다"
            
            assert qa['answer'].strip() != "", \
                f"QA {i}의 답변이 비어있습니다"


def test_validation_report_exists():
    """검증 보고서가 존재하는지 확인"""
    path = Path('eval/gold_standard_validation.json')
    assert path.exists(), "gold_standard_validation.json 파일이 존재하지 않습니다"


def test_validation_report_content():
    """검증 보고서 내용이 올바른지 확인"""
    with open('eval/gold_standard_validation.json', 'r') as f:
        report = json.load(f)
    
    assert report['total_qa'] == 200, \
        f"검증 보고서의 total_qa가 200이 아닙니다: {report['total_qa']}"
    
    assert report['original_qa'] == 100, \
        f"검증 보고서의 original_qa가 100이 아닙니다: {report['original_qa']}"
    
    assert report['new_qa'] == 100, \
        f"검증 보고서의 new_qa가 100이 아닙니다: {report['new_qa']}"
    
    assert 'category_distribution' in report, \
        "검증 보고서에 category_distribution이 없습니다"
    
    assert 'balance_check' in report, \
        "검증 보고서에 balance_check가 없습니다"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])

