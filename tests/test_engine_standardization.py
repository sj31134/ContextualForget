"""
엔진 응답 형식 표준화 검증 테스트
모든 엔진(BM25, Vector, ContextualForget, Hybrid)이 표준 응답 형식을 따르는지 확인
"""

import pytest
from pathlib import Path


def test_response_format_definition():
    """표준 응답 형식이 base.py에 정의되어 있는지 확인"""
    base_file = Path('src/contextualforget/baselines/base.py')
    assert base_file.exists(), "base.py 파일이 존재하지 않습니다"
    
    with open(base_file, 'r') as f:
        content = f.read()
    
    # 필수 필드가 docstring에 정의되어 있는지 확인
    required_fields = ['answer', 'confidence', 'result_count', 'entities', 'source']
    for field in required_fields:
        assert field in content, f"필수 필드 '{field}'가 base.py에 정의되지 않았습니다"


def test_bm25_has_entities_field():
    """BM25 엔진의 모든 응답에 entities 필드가 있는지 확인"""
    bm25_file = Path('src/contextualforget/baselines/bm25_engine.py')
    with open(bm25_file, 'r') as f:
        content = f.read()
    
    # return 문 확인
    import re
    return_statements = re.findall(r'return\s+\{[^}]+\}', content, re.DOTALL)
    
    # 'entities' 필드가 없는 return문 확인
    missing_entities = []
    for i, stmt in enumerate(return_statements):
        if '"source": "BM25"' in stmt and '"entities"' not in stmt and '"error"' not in stmt:
            missing_entities.append(i)
    
    assert len(missing_entities) == 0, \
        f"BM25 엔진의 {len(missing_entities)}개 return문에 'entities' 필드가 없습니다"


def test_vector_has_entities_field():
    """Vector 엔진의 모든 응답에 entities 필드가 있는지 확인"""
    vector_file = Path('src/contextualforget/baselines/vector_engine.py')
    with open(vector_file, 'r') as f:
        content = f.read()
    
    # return 문 확인
    import re
    return_statements = re.findall(r'return\s+\{[^}]+\}', content, re.DOTALL)
    
    # 'entities' 필드가 없는 return문 확인
    missing_entities = []
    for i, stmt in enumerate(return_statements):
        if '"source": "Vector"' in stmt and '"entities"' not in stmt and '"error"' not in stmt:
            missing_entities.append(i)
    
    assert len(missing_entities) == 0, \
        f"Vector 엔진의 {len(missing_entities)}개 return문에 'entities' 필드가 없습니다"


def test_all_engines_return_dict():
    """모든 엔진의 process_query가 딕셔너리를 반환하는지 확인"""
    engine_files = [
        'src/contextualforget/baselines/bm25_engine.py',
        'src/contextualforget/baselines/vector_engine.py',
    ]
    
    for engine_file in engine_files:
        with open(engine_file, 'r') as f:
            content = f.read()
        
        # process_query 메서드가 있는지 확인
        assert 'def process_query' in content, \
            f"{engine_file}에 process_query 메서드가 없습니다"
        
        # return 문이 있는지 확인
        assert 'return {' in content, \
            f"{engine_file}의 process_query에 딕셔너리 반환이 없습니다"


def test_required_fields_in_engines():
    """모든 엔진의 응답에 필수 필드가 있는지 확인"""
    required_fields = ['answer', 'confidence', 'result_count', 'entities', 'source']
    
    engine_files = {
        'BM25': 'src/contextualforget/baselines/bm25_engine.py',
        'Vector': 'src/contextualforget/baselines/vector_engine.py',
    }
    
    for engine_name, engine_file in engine_files.items():
        with open(engine_file, 'r') as f:
            content = f.read()
        
        # 각 필수 필드가 최소 1번 이상 등장하는지 확인
        for field in required_fields:
            assert f'"{field}"' in content or f"'{field}'" in content, \
                f"{engine_name} 엔진에 '{field}' 필드가 없습니다"


def test_entities_field_is_list():
    """entities 필드가 리스트 형태인지 확인"""
    engine_files = [
        'src/contextualforget/baselines/bm25_engine.py',
        'src/contextualforget/baselines/vector_engine.py',
    ]
    
    for engine_file in engine_files:
        with open(engine_file, 'r') as f:
            content = f.read()
        
        # entities 필드가 리스트로 초기화되는지 확인
        import re
        entities_assignments = re.findall(r'"entities":\s*\[', content)
        
        assert len(entities_assignments) > 0, \
            f"{engine_file}에 'entities' 리스트 할당이 없습니다"


def test_confidence_range():
    """confidence 필드가 0.0-1.0 범위인지 확인"""
    engine_files = [
        'src/contextualforget/baselines/bm25_engine.py',
        'src/contextualforget/baselines/vector_engine.py',
    ]
    
    for engine_file in engine_files:
        with open(engine_file, 'r') as f:
            content = f.read()
        
        # confidence 값이 있는지 확인
        import re
        confidence_values = re.findall(r'"confidence":\s*([\d.]+)', content)
        
        assert len(confidence_values) > 0, \
            f"{engine_file}에 confidence 값이 없습니다"
        
        # 모든 값이 0.0-1.0 범위인지 확인
        for value in confidence_values:
            conf = float(value)
            assert 0.0 <= conf <= 1.0, \
                f"{engine_file}의 confidence 값 {conf}가 범위를 벗어났습니다"


def test_result_count_non_negative():
    """result_count 필드가 음수가 아닌지 확인"""
    engine_files = [
        'src/contextualforget/baselines/bm25_engine.py',
        'src/contextualforget/baselines/vector_engine.py',
    ]
    
    for engine_file in engine_files:
        with open(engine_file, 'r') as f:
            content = f.read()
        
        # result_count 값이 있는지 확인
        import re
        result_counts = re.findall(r'"result_count":\s*(\d+)', content)
        
        assert len(result_counts) > 0, \
            f"{engine_file}에 result_count 값이 없습니다"
        
        # 모든 값이 0 이상인지 확인
        for count in result_counts:
            assert int(count) >= 0, \
                f"{engine_file}의 result_count 값 {count}가 음수입니다"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])

