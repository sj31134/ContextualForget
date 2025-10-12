# Troubleshooting Guide

ContextualForget 시스템 사용 중 발생할 수 있는 문제들과 해결 방법을 안내합니다.

## 일반적인 문제

### 1. 설치 관련 문제

#### Python 버전 오류
```bash
# 문제: Python 3.11 미만 버전 사용
ERROR: Package 'contextualforget' requires a different Python: 3.9.6 not in '>=3.11'

# 해결책: Python 3.11+ 설치
conda install python=3.11
# 또는
brew install python@3.11  # macOS
```

#### 패키지 설치 실패
```bash
# 문제: 의존성 충돌
ERROR: pip's dependency resolver does not currently have a strategy to resolve dependency conflicts

# 해결책: 가상환경 재생성
conda remove -n contextualforget --all
conda create -n contextualforget python=3.11 -y
conda activate contextualforget
pip install -e ".[dev]"
```

#### Git LFS 오류
```bash
# 문제: 대용량 파일 다운로드 실패
error: external filter 'git-lfs filter-process' failed

# 해결책: Git LFS 설치 및 설정
git lfs install
git lfs pull
```

### 2. 데이터 처리 문제

#### IFC 파일 파싱 오류
```bash
# 문제: IFC 파일 형식 오류
ERROR: Invalid IFC file format

# 해결책: IFC 파일 검증
python -c "
from contextualforget.core import extract_ifc_entities
with open('data/raw/sample.ifc', 'r') as f:
    content = f.read()
entities = extract_ifc_entities(content)
print(f'Found {len(entities)} entities')
"
```

#### BCF 파일 압축 해제 오류
```bash
# 문제: BCF ZIP 파일 손상
ERROR: BadZipFile: File is not a zip file

# 해결책: BCF 파일 재생성
python -c "
import zipfile
import os
os.makedirs('data/raw/bcf_min/Topics/0001', exist_ok=True)
# BCF 파일 재생성 코드...
"
```

#### 그래프 구축 실패
```bash
# 문제: 메모리 부족
MemoryError: Unable to allocate array

# 해결책: 청크 크기 줄이기
python -c "
from contextualforget.performance import LargeDataProcessor
processor = LargeDataProcessor(chunk_size=100)  # 기본값: 1000
"
```

### 3. 쿼리 실행 문제

#### GUID 검색 실패
```bash
# 문제: GUID를 찾을 수 없음
No results found for GUID: invalid_guid

# 해결책: 유효한 GUID 확인
ctxf stats  # 그래프 통계 확인
python -c "
import pickle
with open('data/processed/graph.gpickle', 'rb') as f:
    graph = pickle.load(f)
print('Available GUIDs:')
for node, data in graph.nodes(data=True):
    if data.get('type') == 'ifc_entity':
        print(f'  {node}')
"
```

#### TTL 필터링 문제
```bash
# 문제: TTL 필터링 후 결과 없음
No recent events found

# 해결책: TTL 값 조정
ctxf query 1kTvXnbbzCWw8lcMd1dR4o --ttl 0  # TTL 비활성화
ctxf query 1kTvXnbbzCWw8lcMd1dR4o --ttl 3650  # 10년으로 확장
```

### 4. 성능 문제

#### 느린 쿼리 성능
```bash
# 문제: 쿼리 실행 시간이 오래 걸림

# 해결책: 그래프 최적화
python -c "
from contextualforget.performance import optimize_for_production
optimize_for_production('data/processed/graph.gpickle', 'data/processed/graph_optimized.gpickle')
"
```

#### 메모리 사용량 과다
```bash
# 문제: 메모리 사용량이 계속 증가

# 해결책: 메모리 최적화
python -c "
from contextualforget.performance import MemoryOptimizer
import pickle
with open('data/processed/graph.gpickle', 'rb') as f:
    graph = pickle.load(f)
compressed_graph = MemoryOptimizer.compress_graph(graph)
with open('data/processed/graph_compressed.gpickle', 'wb') as f:
    pickle.dump(compressed_graph, f)
"
```

## 디버깅 도구

### 1. 로그 활성화

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 또는 환경 변수 설정
export PYTHONPATH=/app/src
export LOG_LEVEL=DEBUG
```

### 2. 그래프 상태 확인

```python
# 그래프 기본 정보
python -c "
import pickle
with open('data/processed/graph.gpickle', 'rb') as f:
    graph = pickle.load(f)
print(f'Nodes: {graph.number_of_nodes()}')
print(f'Edges: {graph.number_of_edges()}')
print(f'Node types: {set(data.get(\"type\", \"unknown\") for _, data in graph.nodes(data=True))}')
"
```

### 3. 데이터 검증

```python
# IFC 데이터 검증
python -c "
from contextualforget.core import read_jsonl
ifc_data = list(read_jsonl('data/processed/ifc.jsonl'))
print(f'IFC entities: {len(ifc_data)}')
for entity in ifc_data[:3]:
    print(f'  {entity[\"guid\"]}: {entity[\"type\"]}')
"

# BCF 데이터 검증
python -c "
from contextualforget.core import read_jsonl
bcf_data = list(read_jsonl('data/processed/bcf.jsonl'))
print(f'BCF topics: {len(bcf_data)}')
for topic in bcf_data[:3]:
    print(f'  {topic[\"topic_id\"]}: {topic[\"title\"]}')
"
```

## 시스템 요구사항 확인

### 1. Python 환경 확인

```bash
# Python 버전
python --version

# 설치된 패키지
pip list | grep contextualforget

# 환경 변수
echo $PYTHONPATH
```

### 2. 시스템 리소스 확인

```bash
# 메모리 사용량
free -h  # Linux
vm_stat  # macOS

# 디스크 공간
df -h

# CPU 사용량
top
```

## 고급 문제 해결

### 1. 커스텀 망각 정책 디버깅

```python
from contextualforget.core import ForgettingManager, TTLPolicy

# 망각 정책 테스트
manager = ForgettingManager()
manager.add_policy(TTLPolicy(ttl_days=365))

# 이벤트 필터링 테스트
test_events = [
    {"created": "2025-01-01T00:00:00Z", "importance": 0.8},
    {"created": "2024-01-01T00:00:00Z", "importance": 0.6}
]

filtered = manager.filter_events(test_events)
print(f"Original: {len(test_events)}, Filtered: {len(filtered)}")
```

### 2. 그래프 연결성 확인

```python
import networkx as nx

# 그래프 연결성 분석
python -c "
import pickle
import networkx as nx
with open('data/processed/graph.gpickle', 'rb') as f:
    graph = pickle.load(f)

# 연결된 컴포넌트 확인
components = list(nx.connected_components(graph.to_undirected()))
print(f'Connected components: {len(components)}')

# 각 컴포넌트 크기
for i, component in enumerate(components):
    print(f'  Component {i}: {len(component)} nodes')
"
```

## 지원 및 커뮤니티

### 1. 문제 보고

GitHub Issues를 통해 문제를 보고하세요:
- [GitHub Issues](https://github.com/sj31134/ContextualForget/issues)

### 2. 로그 수집

문제 보고 시 다음 정보를 포함해주세요:

```bash
# 시스템 정보
python --version
pip list | grep contextualforget
uname -a

# 로그 파일
tail -n 100 /path/to/logfile.log

# 그래프 상태
ctxf stats
```

### 3. 커뮤니티 지원

- **GitHub Discussions**: 일반적인 질문과 토론
- **GitHub Issues**: 버그 리포트와 기능 요청
- **Documentation**: 상세한 사용법과 예제

## 자주 묻는 질문 (FAQ)

### Q: IFC 파일을 어떻게 준비하나요?
A: IFC 파일은 BIM 소프트웨어(Revit, ArchiCAD 등)에서 내보낸 표준 형식이어야 합니다. 샘플 파일은 `data/raw/sample.ifc`를 참조하세요.

### Q: BCF 파일은 어디서 구할 수 있나요?
A: BCF 파일은 BIM 협업 도구(BIM 360, Trimble Connect 등)에서 내보낸 형식입니다. 샘플 파일은 `data/raw/sample.bcfzip`를 참조하세요.

### Q: 대용량 데이터를 처리할 때 주의사항은?
A: 메모리 사용량을 모니터링하고, 청크 크기를 조정하며, 그래프 압축을 사용하세요. 자세한 내용은 [Performance Guide](performance.md)를 참조하세요.

### Q: 쿼리 결과가 없는 이유는?
A: GUID가 올바른지, TTL 설정이 적절한지, 데이터가 제대로 로드되었는지 확인하세요. `ctxf stats` 명령으로 그래프 상태를 확인할 수 있습니다.
