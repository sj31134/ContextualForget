# Quick Start Guide

이 가이드는 ContextualForget 시스템을 처음 사용하는 사용자를 위한 빠른 시작 가이드입니다.

## 1. 기본 파이프라인 실행

### 샘플 데이터 생성 및 처리

```bash
# 환경 활성화
conda activate contextualforget

# 샘플 데이터 생성
python -c "
import os
os.makedirs('data/raw', exist_ok=True)
with open('data/raw/sample.ifc', 'w') as f:
    f.write('''ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [notYetAssigned]'),'2;1');
FILE_NAME('sample.ifc','2025-10-05T00:00:00',('author'),('org'),'ifc text','ifc text','ref');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#100= IFCPROJECT('0xScRe4drECQ4DMSqUjd6d',$,'Sample',$,$,$,$,$,$);
#500= IFCBUILDING('2FCZDorxHDT8NI01kdXi8P',$,'Test Building',$,$,$,$,$,.ELEMENT.,$,$,$);
#1000= IFCBUILDINGELEMENTPROXY('1kTvXnbbzCWw8lcMd1dR4o',$,'P-1','sample',$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;''')
print('✅ Sample IFC file created')
"
```

### 데이터 파이프라인 실행

```bash
# 1. IFC 데이터 수집
python -m contextualforget.data.ingest_ifc --ifc data/raw/sample.ifc --out data/processed/ifc.jsonl

# 2. BCF 데이터 수집
python -m contextualforget.data.ingest_bcf --bcf data/raw/sample.bcfzip --out data/processed/bcf.jsonl

# 3. IFC-BCF 연결
python -m contextualforget.data.link_ifc_bcf --ifc data/processed/ifc.jsonl --bcf data/processed/bcf.jsonl --out data/processed/links.jsonl

# 4. 그래프 구축
python -m contextualforget.data.build_graph --ifc data/processed/ifc.jsonl --bcf data/processed/bcf.jsonl --links data/processed/links.jsonl --out data/processed/graph.gpickle
```

## 2. 쿼리 시스템 사용

### 기본 쿼리

```bash
# GUID로 관련 이슈 검색
ctxf query 1kTvXnbbzCWw8lcMd1dR4o --ttl 365 --topk 5

# 키워드 검색
ctxf search "clearance" --topk 5

# 작성자별 검색
ctxf author "engineer_a" --topk 5

# 시간 범위 검색
ctxf timeline "2025-01-01" "2025-12-31"

# 연결된 컴포넌트 분석
ctxf connected 1kTvXnbbzCWw8lcMd1dR4o --max-depth 2

# 그래프 통계
ctxf stats
```

### 고급 쿼리

```bash
# 복합 조건 검색
ctxf advanced-query \
  --guid 1kTvXnbbzCWw8lcMd1dR4o \
  --author "engineer_a" \
  --keywords "clearance" "HVAC" \
  --start-date "2025-01-01" \
  --end-date "2025-12-31" \
  --ttl 365 \
  --sort-by confidence \
  --limit 10
```

## 3. 시각화

```bash
# 전체 그래프 시각화
ctxf visualize --output-dir visualizations

# 특정 GUID 서브그래프 시각화
ctxf visualize --guid 1kTvXnbbzCWw8lcMd1dR4o --output-dir visualizations
```

## 4. Python API 사용

### 기본 사용법

```python
from contextualforget import AdvancedQueryEngine, GraphVisualizer
import pickle

# 그래프 로드
with open('data/processed/graph.gpickle', 'rb') as f:
    graph = pickle.load(f)

# 쿼리 엔진 초기화
engine = AdvancedQueryEngine(graph)

# GUID로 검색
results = engine.find_by_guid("1kTvXnbbzCWw8lcMd1dR4o")
print(f"Found {len(results)} related topics")

# 키워드 검색
keyword_results = engine.find_by_keywords(["clearance"])
for result in keyword_results:
    print(f"- {result['title']} (by {result['author']})")

# 통계 조회
stats = engine.get_statistics()
print(f"Total nodes: {stats['total_nodes']}")
print(f"IFC entities: {stats['ifc_entities']}")
print(f"BCF topics: {stats['bcf_topics']}")
```

### 망각 정책 사용

```python
from contextualforget import create_default_forgetting_policy

# 망각 정책 생성
forgetting_manager = create_default_forgetting_policy()

# 이벤트 필터링
filtered_events = forgetting_manager.filter_events(events)
print(f"Original: {len(events)}, Filtered: {len(filtered_events)}")
```

## 5. 성능 최적화

```bash
# 그래프 최적화
python -c "
from contextualforget.performance import optimize_for_production
optimize_for_production('data/processed/graph.gpickle', 'data/processed/graph_optimized.gpickle')
"
```

## 6. 예제 실행

```bash
# Jupyter 노트북 실행
jupyter lab examples/demo.ipynb

# Python 스크립트 실행
python examples/quick_start.py
```

## 7. 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 특정 테스트
pytest tests/test_advanced_query.py -v

# 커버리지 포함 테스트
pytest tests/ --cov=contextualforget --cov-report=html
```

## 다음 단계

- [API Reference](api_reference.md) - 상세한 API 문서
- [Tutorial](tutorial.md) - 단계별 튜토리얼
- [Performance Guide](performance.md) - 성능 최적화 가이드
- [Troubleshooting](troubleshooting.md) - 문제 해결 가이드
