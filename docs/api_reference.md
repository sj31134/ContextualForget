# ContextualForget API Reference

이 문서는 ContextualForget의 모든 API와 사용법을 설명합니다.

## 목차

1. [Core Modules](#core-modules)
2. [Query Engine](#query-engine)
3. [LLM Integration](#llm-integration)
4. [Visualization](#visualization)
5. [Performance](#performance)
6. [CLI Commands](#cli-commands)

---

## Core Modules

### ForgettingManager

망각 메커니즘을 관리하는 핵심 클래스입니다.

```python
from contextualforget.core import ForgettingManager, create_default_forgetting_policy

# 망각 매니저 초기화
manager = ForgettingManager()

# 기본 망각 정책 생성
policy = create_default_forgetting_policy()

# 망각 정책 적용
updated_graph = manager.apply_forgetting(graph, current_time)
```

#### 주요 메서드

- `apply_forgetting(graph, current_time)`: 망각 정책을 그래프에 적용
- `get_forgetting_stats()`: 망각 통계 반환
- `add_policy(policy)`: 새로운 망각 정책 추가

### Forgetting Policies

#### TTLPolicy

시간 기반 만료 정책입니다.

```python
from contextualforget.core import TTLPolicy

policy = TTLPolicy(ttl_days=30)
```

#### WeightedDecayPolicy

가중치 감쇠 정책입니다.

```python
from contextualforget.core import WeightedDecayPolicy

policy = WeightedDecayPolicy(decay_rate=0.1)
```

#### ImportanceBasedPolicy

중요도 기반 정책입니다.

```python
from contextualforget.core import ImportanceBasedPolicy

policy = ImportanceBasedPolicy(importance_threshold=0.5)
```

#### CompositeForgettingPolicy

여러 정책을 조합하는 정책입니다.

```python
from contextualforget.core import CompositeForgettingPolicy, TTLPolicy, WeightedDecayPolicy

policy = CompositeForgettingPolicy([
    TTLPolicy(ttl_days=30),
    WeightedDecayPolicy(decay_rate=0.1)
])
```

---

## Query Engine

### AdvancedQueryEngine

고급 쿼리 기능을 제공하는 엔진입니다.

```python
from contextualforget.query import AdvancedQueryEngine

# 쿼리 엔진 초기화
engine = AdvancedQueryEngine("data/processed/graph.gpickle")
```

#### 주요 메서드

##### query_by_guid(guid, ttl=0)

특정 GUID와 관련된 정보를 검색합니다.

```python
result = engine.query_by_guid("1kTvXnbbzCWw8lcMd1dR4o")
```

**반환값:**
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

##### search_by_keywords(keywords, ttl=0)

키워드로 BCF 이슈를 검색합니다.

```python
result = engine.search_by_keywords(["벽체", "두께"], ttl=30)
```

##### query_by_author(author, ttl=0)

특정 작성자의 이슈를 검색합니다.

```python
result = engine.query_by_author("김건설", ttl=7)
```

##### query_by_date_range(start_date, end_date, ttl=0)

날짜 범위로 이슈를 검색합니다.

```python
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=7)
result = engine.query_by_date_range(start_date, end_date)
```

##### advanced_query(guid=None, author=None, keywords=None, start_date=None, end_date=None, ttl=365, sort_by="date", ascending=False)

복합 조건으로 검색합니다.

```python
result = engine.advanced_query(
    keywords=["벽체", "창호"],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    sort_by="confidence",
    ascending=False
)
```

---

## LLM Integration

### NaturalLanguageProcessor

자연어 질의를 처리하는 클래스입니다.

```python
from contextualforget.llm import NaturalLanguageProcessor

# 자연어 프로세서 초기화
nlp = NaturalLanguageProcessor()
```

#### 주요 메서드

##### process_query(question)

자연어 질문을 처리합니다.

```python
result = nlp.process_query("GUID 1kTvXnbbzCWw8lcMd1dR4o와 관련된 이슈는?")
```

**지원하는 질문 유형:**
- GUID 검색: "GUID xxx를 찾아줘"
- 키워드 검색: "벽체 관련 이슈를 보여줘"
- 시간 검색: "최근 7일 이내 이슈를 보여줘"
- 통계 질문: "그래프에 몇 개의 노드가 있어?"

### LLMQueryEngine

LLM을 활용한 쿼리 엔진입니다.

```python
from contextualforget.llm import LLMQueryEngine

# LLM 쿼리 엔진 초기화
llm_engine = LLMQueryEngine(
    model_name="qwen2.5:3b",
    graph_path="data/processed/graph.gpickle"
)
```

#### 주요 메서드

##### query(question, context_limit=5)

LLM을 사용한 자연어 질의입니다.

```python
result = llm_engine.query("현재 프로젝트의 주요 이슈는 무엇인가요?")
```

---

## Visualization

### GraphVisualizer

그래프 시각화를 담당하는 클래스입니다.

```python
from contextualforget.visualization import GraphVisualizer
import pickle

# 그래프 로드
with open("data/processed/graph.gpickle", 'rb') as f:
    graph = pickle.load(f)

# 시각화 도구 초기화
visualizer = GraphVisualizer(graph)
```

#### 주요 메서드

##### visualize_full_graph(output_path, max_nodes=100)

전체 그래프를 시각화합니다.

```python
visualizer.visualize_full_graph("output/full_graph.png", max_nodes=50)
```

##### visualize_subgraph(target_guid, output_path, max_depth=2)

특정 GUID 주변의 서브그래프를 시각화합니다.

```python
visualizer.visualize_subgraph(
    target_guid="1kTvXnbbzCWw8lcMd1dR4o",
    output_path="output/subgraph.png",
    max_depth=2
)
```

##### visualize_timeline(output_path, days=30)

시간순 이슈 타임라인을 시각화합니다.

```python
visualizer.visualize_timeline("output/timeline.png", days=30)
```

##### visualize_forgetting_curve(output_path, days=90)

망각 곡선을 시각화합니다.

```python
visualizer.visualize_forgetting_curve("output/forgetting_curve.png", days=90)
```

---

## Performance

### GraphOptimizer

그래프 성능 최적화를 담당하는 클래스입니다.

```python
from contextualforget.performance import GraphOptimizer

optimizer = GraphOptimizer()
```

#### 주요 메서드

##### optimize_graph(graph)

그래프를 최적화합니다.

```python
optimized_graph = optimizer.optimize_graph(graph)
```

### MemoryOptimizer

메모리 사용량 최적화를 담당하는 클래스입니다.

```python
from contextualforget.performance import MemoryOptimizer

memory_optimizer = MemoryOptimizer()
```

#### 주요 메서드

##### compress_graph(graph)

그래프를 압축합니다.

```python
compressed_graph = memory_optimizer.compress_graph(graph)
```

##### save_graph_compressed(graph, filepath)

압축된 그래프를 저장합니다.

```python
memory_optimizer.save_graph_compressed(compressed_graph, "compressed.gpickle")
```

##### load_graph_compressed(filepath)

압축된 그래프를 로드합니다.

```python
graph = memory_optimizer.load_graph_compressed("compressed.gpickle")
```

### CacheManager

캐시 관리를 담당하는 클래스입니다.

```python
from contextualforget.performance import CacheManager

cache = CacheManager()
```

#### 주요 메서드

##### get(key)

캐시에서 데이터를 가져옵니다.

```python
data = cache.get("query_result_123")
```

##### set(key, data)

데이터를 캐시에 저장합니다.

```python
cache.set("query_result_123", result_data)
```

##### clear()

캐시를 초기화합니다.

```python
cache.clear()
```

---

## CLI Commands

ContextualForget는 `ctxf` 명령어를 통해 CLI 인터페이스를 제공합니다.

### 기본 명령어

#### ctxf query

GUID로 검색합니다.

```bash
ctxf query 1kTvXnbbzCWw8lcMd1dR4o
```

#### ctxf search

키워드로 검색합니다.

```bash
ctxf search "벽체" "두께" --ttl 30 --topk 10
```

#### ctxf ask

자연어 질의를 수행합니다.

```bash
ctxf ask "그래프에 몇 개의 노드가 있어?"
```

#### ctxf chat

대화형 모드를 시작합니다.

```bash
ctxf chat
```

#### ctxf watch

실시간 파일 모니터링을 시작합니다.

```bash
# 기본 모니터링
ctxf watch

# 커스텀 디렉토리 감시
ctxf watch -w /path/to/ifc -w /path/to/bcf -i 5.0
```

#### ctxf model-info

LLM 모델 정보를 표시합니다.

```bash
ctxf model-info
```

#### ctxf advanced-query

고급 검색을 수행합니다.

```bash
ctxf advanced-query \
  --keywords "벽체" "창호" \
  --start-date "2024-01-01" \
  --end-date "2024-01-31" \
  --sort-by confidence \
  --ascending false
```

### 옵션

#### 공통 옵션

- `--graph, -g`: 그래프 파일 경로 (기본값: `data/processed/graph.gpickle`)
- `--ttl`: TTL (Time To Live) 일수 (기본값: 365)
- `--topk`: 반환할 최대 결과 수 (기본값: 10)

#### watch 명령어 옵션

- `--watch, -w`: 감시할 디렉토리 (여러 개 지정 가능)
- `--interval, -i`: 스캔 간격 (초) (기본값: 2.0)

#### advanced-query 명령어 옵션

- `--guid`: IFC GUID
- `--author`: 작성자 이름
- `--keywords`: 키워드 목록
- `--start-date`: 시작 날짜 (YYYY-MM-DD)
- `--end-date`: 종료 날짜 (YYYY-MM-DD)
- `--sort-by`: 정렬 기준 (date, confidence)
- `--ascending`: 오름차순 정렬 여부

---

## 에러 처리

### 일반적인 에러

#### FileNotFoundError

그래프 파일이 없을 때 발생합니다.

```python
try:
    engine = AdvancedQueryEngine("nonexistent.gpickle")
except FileNotFoundError:
    print("그래프 파일을 찾을 수 없습니다.")
```

#### ValueError

잘못된 GUID나 날짜 형식일 때 발생합니다.

```python
try:
    result = engine.query_by_guid("invalid_guid")
except ValueError as e:
    print(f"잘못된 GUID: {e}")
```

### LLM 관련 에러

#### ConnectionError

Ollama 서버에 연결할 수 없을 때 발생합니다.

```python
try:
    result = nlp.process_query("질문")
except ConnectionError:
    print("Ollama 서버에 연결할 수 없습니다.")
```

---

## 성능 팁

### 1. 그래프 최적화

대용량 그래프의 경우 압축을 사용하세요:

```python
from contextualforget.performance import MemoryOptimizer

optimizer = MemoryOptimizer()
compressed_graph = optimizer.compress_graph(graph)
```

### 2. 캐시 활용

반복적인 쿼리는 캐시를 활용하세요:

```python
from contextualforget.performance import CacheManager

cache = CacheManager()
cache_key = f"query_{hash(question)}"

# 캐시에서 먼저 확인
result = cache.get(cache_key)
if result is None:
    result = engine.query(question)
    cache.set(cache_key, result)
```

### 3. 배치 처리

여러 GUID를 한 번에 처리하세요:

```python
# 개별 처리 (비효율적)
for guid in guids:
    result = engine.query_by_guid(guid)

# 배치 처리 (효율적)
results = engine.batch_query(guids)
```

---

## 예제 코드

완전한 예제는 `examples/advanced_usage.py`를 참조하세요.

```bash
python examples/advanced_usage.py
```

이 스크립트는 ContextualForget의 모든 주요 기능을 보여주는 예제를 포함하고 있습니다.