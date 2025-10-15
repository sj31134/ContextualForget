# ContextualForget 튜토리얼

이 튜토리얼은 ContextualForget을 처음 사용하는 사용자를 위한 단계별 가이드입니다.

## 목차

1. [설치 및 설정](#설치-및-설정)
2. [기본 사용법](#기본-사용법)
3. [자연어 질의](#자연어-질의)
4. [실시간 모니터링](#실시간-모니터링)
5. [고급 기능](#고급-기능)
6. [문제 해결](#문제-해결)

---

## 설치 및 설정

### 1. 환경 준비

```bash
# 1. 저장소 클론
git clone https://github.com/sj31134/ContextualForget.git
cd ContextualForget

# 2. Conda 환경 생성
conda create -n contextualforget python=3.11 -y
conda activate contextualforget

# 3. 패키지 설치
pip install -e ".[dev,demo]"
```

### 2. LLM 설정 (선택사항)

자연어 질의 기능을 사용하려면 Ollama를 설치하세요:

```bash
# Ollama 설치 (https://ollama.ai)
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# 모델 다운로드
ollama pull qwen2.5:3b
```

### 3. 샘플 데이터 생성

```bash
# 샘플 데이터 생성 (6개 건물, 87개 노드)
python scripts/generate_sample_data.py

# 데이터를 그래프로 통합
python scripts/process_all_data.py
```

---

## 기본 사용법

### 1. CLI 명령어 확인

```bash
# 도움말 확인
ctxf --help

# 사용 가능한 명령어 확인
ctxf --help
```

### 2. 기본 검색

#### GUID로 검색

```bash
# 특정 GUID 검색
ctxf query 1kTvXnbbzCWw8lcMd1dR4o
```

**출력 예시:**
```json
{
  "guid": "1kTvXnbbzCWw8lcMd1dR4o",
  "entity_type": "IfcWall",
  "name": "벽체_001",
  "related_issues": [
    {
      "topic_id": "topic_001",
      "title": "벽체 두께 불일치",
      "created_at": "2024-01-15T10:30:00",
      "confidence": 0.95
    }
  ]
}
```

#### 키워드로 검색

```bash
# 키워드 검색
ctxf search "벽체" "두께" --ttl 30 --topk 5
```

### 3. 고급 검색

```bash
# 복합 조건 검색
ctxf advanced-query \
  --keywords "벽체" "창호" \
  --start-date "2024-01-01" \
  --end-date "2024-01-31" \
  --sort-by confidence
```

---

## 자연어 질의

### 1. 단일 질의

```bash
# 자연어로 질문하기
ctxf ask "그래프에 몇 개의 노드가 있어?"
ctxf ask "GUID 1kTvXnbbzCWw8lcMd1dR4o와 관련된 이슈는?"
ctxf ask "최근 7일 이내에 생성된 BCF 이슈를 보여줘"
```

### 2. 대화형 모드

```bash
# 대화형 모드 시작
ctxf chat
```

**대화 예시:**
```
> 통계 정보를 보여줘
그래프에는 총 87개의 노드가 있습니다:
- IFC 노드: 60개
- BCF 노드: 27개
- 총 엣지: 45개

> GUID 1kTvXnbbzCWw8lcMd1dR4o를 찾아줘
GUID 1kTvXnbbzCWw8lcMd1dR4o는 IfcWall 타입의 벽체_001입니다.
관련된 이슈는 1개입니다:
- 벽체 두께 불일치 (신뢰도: 0.95)

> quit
```

### 3. LLM 모델 정보

```bash
# 사용 중인 LLM 모델 정보 확인
ctxf model-info
```

---

## 실시간 모니터링

### 1. 기본 모니터링

```bash
# 기본 디렉토리 감시 (data/, data/raw/)
ctxf watch
```

### 2. 커스텀 모니터링

```bash
# 특정 디렉토리 감시
ctxf watch -w /path/to/project/ifc -w /path/to/project/bcf -i 5.0
```

**옵션 설명:**
- `-w, --watch`: 감시할 디렉토리 (여러 개 지정 가능)
- `-i, --interval`: 스캔 간격 (초)

### 3. 실시간 데모

두 개의 터미널을 사용하여 실시간 기능을 테스트할 수 있습니다:

**터미널 1 (데모 스크립트):**
```bash
python scripts/demo_realtime.py
```

**터미널 2 (모니터링):**
```bash
ctxf watch -w data/demo -i 2.0
```

---

## 고급 기능

### 1. 시각화

#### Python 스크립트로 시각화

```python
from contextualforget.visualization import GraphVisualizer
import pickle

# 그래프 로드
with open("data/processed/graph.gpickle", 'rb') as f:
    graph = pickle.load(f)

# 시각화 도구 초기화
visualizer = GraphVisualizer(graph)

# 전체 그래프 시각화
visualizer.visualize_full_graph("output/full_graph.png", max_nodes=50)

# 서브그래프 시각화
visualizer.visualize_subgraph(
    target_guid="1kTvXnbbzCWw8lcMd1dR4o",
    output_path="output/subgraph.png",
    max_depth=2
)

# 타임라인 시각화
visualizer.visualize_timeline("output/timeline.png", days=30)
```

### 2. 망각 메커니즘

```python
from contextualforget.core import ForgettingManager, TTLPolicy, WeightedDecayPolicy
from datetime import datetime

# 망각 매니저 초기화
manager = ForgettingManager()

# TTL 정책 추가 (30일 후 만료)
ttl_policy = TTLPolicy(ttl_days=30)
manager.add_policy(ttl_policy)

# 가중치 감쇠 정책 추가
decay_policy = WeightedDecayPolicy(decay_rate=0.1)
manager.add_policy(decay_policy)

# 망각 정책 적용
current_time = datetime.now()
updated_graph = manager.apply_forgetting(graph, current_time)

# 망각 통계 확인
stats = manager.get_forgetting_stats()
print(f"망각된 노드: {stats['forgotten_nodes']}개")
```

### 3. 성능 최적화

```python
from contextualforget.performance import MemoryOptimizer, GraphOptimizer

# 메모리 최적화
memory_optimizer = MemoryOptimizer()
compressed_graph = memory_optimizer.compress_graph(graph)

# 압축된 그래프 저장
memory_optimizer.save_graph_compressed(
    compressed_graph, 
    "data/processed/compressed_graph.gpickle"
)

# 그래프 최적화
optimizer = GraphOptimizer()
optimized_graph = optimizer.optimize_graph(graph)
```

### 4. 배치 처리

```python
from contextualforget.query import AdvancedQueryEngine

# 쿼리 엔진 초기화
engine = AdvancedQueryEngine("data/processed/graph.gpickle")

# 여러 GUID를 한 번에 검색
guids = [
    "1kTvXnbbzCWw8lcMd1dR4o",
    "2mUwYoaa3DXx9mdNe2eR5p",
    "3nVxZpbb4EYy0neOf3fS6q"
]

results = engine.batch_query(guids)
for guid, result in results.items():
    print(f"GUID {guid}: {len(result.get('related_issues', []))}개 관련 이슈")
```

---

## 문제 해결

### 1. 일반적인 문제

#### 그래프 파일이 없음

```bash
❌ 그래프 파일이 없습니다.
```

**해결 방법:**
```bash
# 샘플 데이터 생성
python scripts/generate_sample_data.py
python scripts/process_all_data.py
```

#### LLM 연결 실패

```bash
❌ Ollama 서버에 연결할 수 없습니다.
```

**해결 방법:**
```bash
# Ollama 서버 시작
ollama serve

# 모델 확인
ollama list

# 모델 다운로드
ollama pull qwen2.5:3b
```

#### 권한 오류

```bash
❌ Permission denied
```

**해결 방법:**
```bash
# 파일 권한 확인
ls -la data/processed/

# 권한 수정
chmod 755 data/processed/
```

### 2. 성능 문제

#### 메모리 부족

```bash
❌ Memory error
```

**해결 방법:**
```python
# 그래프 압축 사용
from contextualforget.performance import MemoryOptimizer

optimizer = MemoryOptimizer()
compressed_graph = optimizer.compress_graph(graph)
```

#### 느린 쿼리

**해결 방법:**
```python
# 캐시 사용
from contextualforget.performance import CacheManager

cache = CacheManager()
cache_key = f"query_{hash(question)}"

result = cache.get(cache_key)
if result is None:
    result = engine.query(question)
    cache.set(cache_key, result)
```

### 3. 디버깅

#### 로그 레벨 설정

```python
import logging

# 디버그 로그 활성화
logging.basicConfig(level=logging.DEBUG)
```

#### 상세한 오류 정보

```python
try:
    result = engine.query_by_guid("invalid_guid")
except Exception as e:
    import traceback
    traceback.print_exc()
```

---

## 다음 단계

### 1. 고급 예제

`examples/advanced_usage.py`를 실행하여 더 많은 기능을 확인하세요:

```bash
python examples/advanced_usage.py
```

### 2. API 문서

자세한 API 문서는 [API_REFERENCE.md](API_REFERENCE.md)를 참조하세요.

### 3. 커스터마이징

자신만의 망각 정책이나 쿼리 엔진을 만들어보세요:

```python
from contextualforget.core import ForgettingPolicy

class CustomForgettingPolicy(ForgettingPolicy):
    def should_forget(self, event, current_time):
        # 커스텀 로직 구현
        return False
    
    def apply(self, graph, current_time):
        # 커스텀 적용 로직 구현
        return graph
```

### 4. 확장

ContextualForget을 다른 프로젝트에 통합하거나 새로운 기능을 추가해보세요.

---

## 도움말

- **GitHub Issues**: [버그 리포트 또는 기능 요청](https://github.com/sj31134/ContextualForget/issues)
- **문서**: [docs/](docs/) 디렉토리
- **예제**: [examples/](examples/) 디렉토리

문제가 있거나 질문이 있으시면 언제든지 GitHub Issues를 통해 문의해주세요!