# API Reference

## Core Modules

### `contextualforget.utils`

#### `read_jsonl(path: str)`
JSONL 파일을 읽어서 각 줄을 JSON 객체로 파싱합니다.

**Parameters:**
- `path`: JSONL 파일 경로

**Returns:**
- Generator yielding JSON objects

#### `write_jsonl(path: str, rows: List[Dict])`
JSON 객체 리스트를 JSONL 파일로 저장합니다.

**Parameters:**
- `path`: 출력 파일 경로
- `rows`: JSON 객체 리스트

#### `extract_ifc_entities(text: str)`
IFC 파일 텍스트에서 엔티티를 추출합니다.

**Parameters:**
- `text`: IFC 파일 내용

**Returns:**
- List of dicts with keys: `guid`, `type`, `name`

#### `parse_bcf_zip(bcf_path: str)`
BCF ZIP 파일을 파싱하여 토픽 정보를 추출합니다.

**Parameters:**
- `bcf_path`: BCF ZIP 파일 경로

**Returns:**
- List of dicts with keys: `topic_id`, `title`, `created`, `author`, `ref`

### `contextualforget.forgetting`

#### `expired(created_iso: str, ttl: int) -> bool`
이벤트가 TTL을 초과했는지 확인합니다.

**Parameters:**
- `created_iso`: ISO 8601 형식의 생성 시간
- `ttl`: Time-to-live (일 단위)

**Returns:**
- `True` if expired, `False` otherwise

#### `score(recency_days: float, usage: int, confidence: float, contradiction: int) -> float`
이벤트의 중요도 점수를 계산합니다.

**Parameters:**
- `recency_days`: 최근성 (일 단위)
- `usage`: 사용 빈도
- `confidence`: 신뢰도
- `contradiction`: 모순 횟수

**Returns:**
- Importance score (0.0 to 1.0)

### `contextualforget.query`

#### `find_by_guid(G: nx.DiGraph, guid: str, ttl: int = 0)`
특정 GUID와 관련된 BCF 토픽을 찾습니다.

**Parameters:**
- `G`: NetworkX 그래프
- `guid`: IFC 엔티티 GUID
- `ttl`: Time-to-live 필터 (0이면 필터링 없음)

**Returns:**
- List of tuples: (node, data, edge_data)

## Command Line Interface

### `ctxf` Command

```bash
ctxf <guid> [OPTIONS]
```

**Arguments:**
- `guid`: IFC 엔티티 GUID

**Options:**
- `--ttl INTEGER`: Time-to-live in days (default: 365)
- `--topk INTEGER`: Maximum number of results (default: 5)
- `--graph TEXT`: Graph file path (default: data/processed/graph.gpickle)

**Example:**
```bash
ctxf 1kTvXnbbzCWw8lcMd1dR4o --ttl 365 --topk 5
```

## Data Pipeline Modules

### `contextualforget.ingest_ifc`
IFC 파일을 파싱하여 엔티티 정보를 추출합니다.

### `contextualforget.ingest_bcf`
BCF ZIP 파일을 파싱하여 토픽 정보를 추출합니다.

### `contextualforget.link_ifc_bcf`
IFC 엔티티와 BCF 토픽을 연결합니다.

### `contextualforget.build_graph`
통합 그래프를 구축합니다.

### `contextualforget.eval_metrics`
평가 메트릭을 계산합니다.
