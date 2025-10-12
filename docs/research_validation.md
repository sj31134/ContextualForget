# 연구 가설 검증 보고서

## 📋 연구 가설 & 목표 검증

### **가설 G1 (맥락): IFC-BCF 통합 그래프의 근거성 향상**

**가설**: IFC의 구조적 관계와 BCF 이슈의 시간축을 한 그래프로 통합하면, 순수 문서 RAG 대비 **근거성(Attribution)**과 변경 영향 추적 성능이 향상된다.

#### ✅ **현재 구현 상태**
1. **IFC-BCF 통합 그래프**: ✅ 완전 구현
   - IFC 엔티티 → 구조적 관계 (노드)
   - BCF 이슈 → 시간축 메타데이터 (노드)
   - BCF → IFC 링크 (엣지)
   ```python
   # 구현된 구조
   Graph = {
       nodes: [ifc:GUID, bcf:TopicID],
       edges: [(bcf → ifc, relation='references')]
   }
   ```

2. **근거성(Attribution)**: ✅ 구현됨
   - 모든 BCF 토픽은 관련 IFC GUID로 연결
   - 쿼리 결과에 근거 링크 포함
   ```python
   find_by_guid(guid) → [bcf_topics with evidence links]
   ```

3. **변경 영향 추적**: ⚠️ **부분 구현**
   - `find_connected_components()`: GUID 기반 연결 탐색 ✅
   - 시간축 변경 추적: TTL 필터링으로 가능 ✅
   - **문제점**: 변경 이력 시각화 부족 ❌
   - **문제점**: "무엇이 바뀌었는가" 명시적 추적 부족 ❌

#### 🔴 **검증 가능성 평가: 60%**

**구현된 기능**:
- ✅ IFC-BCF 그래프 통합
- ✅ 근거 링크 제공
- ✅ 연결된 컴포넌트 탐색
- ✅ TTL 기반 시간 필터링

**부족한 기능**:
- ❌ **벤치마크 비교군 없음**: 순수 문서 RAG 구현 없음
- ❌ **정량적 평가 메트릭 없음**: 근거성 정확도 측정 불가
- ❌ **변경 diff 추적 없음**: "무엇이 바뀌었는가" 명시적 추적 부족
- ❌ **평가 데이터셋 없음**: Gold standard QA 쌍 부족 (eval/gold.jsonl 존재하지만 활용 안 됨)

---

### **가설 G2 (망각): TTL/감쇠/요약압축의 효과**

**가설**: TTL/가중치 감쇠/요약압축을 적용하면 구버전 인용과 모순 응답이 유의하게 감소한다.

#### ✅ **현재 구현 상태**

1. **망각 정책**: ✅ 완전 구현
   ```python
   # 구현된 정책들
   - TTLPolicy: 단순 시간 만료
   - WeightedDecayPolicy: 시간 × 중요도 감쇠
   - ImportanceBasedPolicy: 중요도 임계값
   - ContradictionPolicy: 모순 탐지 (키워드 기반)
   - CompositePolicy: 정책 조합
   ```

2. **구버전 필터링**: ✅ 작동
   ```python
   expired(event, ttl_days) → True/False
   find_by_guid(guid, ttl=30)  # 최근 30일만
   ```

3. **요약압축**: ⚠️ **미구현**
   - 코드에 `summarization` 언급은 있으나 실제 구현 없음
   - LLM 통합은 있지만 요약 기능 연결 안 됨

#### 🔴 **검증 가능성 평가: 40%**

**구현된 기능**:
- ✅ TTL 정책
- ✅ 가중치 감쇠 정책
- ✅ 중요도 기반 정책
- ✅ 모순 탐지 (기초)

**부족한 기능**:
- ❌ **요약압축 미구현**: 가설의 핵심 요소 중 하나
- ❌ **구버전 인용률 측정 불가**: 평가 메트릭 없음
- ❌ **모순률 측정 불가**: 정량적 평가 시스템 없음
- ❌ **성능-비용 곡선 없음**: 인덱스 크기, 쿼리 시간 추적 부족
- ❌ **A/B 테스트 불가**: 망각 정책 적용 전후 비교 시스템 없음

---

### **목표: 재현 가능한 벤치마크 & 참조 아키텍처**

#### ✅ **현재 상태**

1. **재현 가능성**: ✅ 높음
   - 모든 코드 오픈소스
   - Conda 환경 정의
   - 샘플 데이터 생성 스크립트
   - Docker 지원

2. **참조 아키텍처**: ✅ 명확함
   ```
   IFC → Parser → Graph ← Parser ← BCF
           ↓              ↓
       Entity Nodes ↔ Topic Nodes
           ↓
       Query Engine (with LLM)
   ```

3. **벤치마크**: ❌ **없음**
   - 평가 스크립트 있지만 실행 안 됨
   - Gold standard 데이터 미비
   - 비교군 (baseline) 없음

#### 🟡 **달성도: 70%**

**강점**:
- ✅ 완전한 코드베이스
- ✅ 재현 가능한 환경
- ✅ 명확한 아키텍처
- ✅ 다양한 샘플 데이터

**약점**:
- ❌ 벤치마크 시스템 부재
- ❌ 평가 메트릭 미흡

---

## 📊 **연구 질문(RQ) 검증**

### **RQ1: Graph-RAG vs 키워드/벡터 RAG 정확도 비교**

**질문**: Graph-RAG(BCF+IFC) → 키워드/벡터 RAG 대비 정답·근거 정확도가 얼마나 개선되는가?

#### 🔴 **검증 가능성: 10%**

**현재 상태**:
- ✅ Graph-RAG 구현됨
- ❌ 키워드 RAG 비교군 없음
- ❌ 벡터 RAG 비교군 없음
- ❌ 정답 정확도 측정 시스템 없음
- ❌ 근거 정확도 측정 시스템 없음
- ❌ 평가 데이터셋 부족

**필요한 작업**:
1. **비교군 구현**
   - 순수 키워드 검색 (BM25 등)
   - 벡터 임베딩 RAG (Sentence Transformers + FAISS)

2. **평가 시스템 구축**
   - Gold standard QA 쌍 (최소 50-100개)
   - 정답 정확도 메트릭 (Accuracy, F1)
   - 근거 정확도 메트릭 (Attribution Recall, Precision)

3. **실험 설계**
   - 동일 질문에 3가지 방법 적용
   - 통계적 유의성 검정 (t-test 등)

**예상 구현 시간**: 2-3주

---

### **RQ2: 망각 정책의 구버전 인용률 & 모순률 감소 효과**

**질문**: 망각정책(요약/TTL/감쇠)을 조합하면 구버전 인용률과 모순률이 얼마나 낮아지나?

#### 🔴 **검증 가능성: 30%**

**현재 상태**:
- ✅ TTL 정책 구현
- ✅ 감쇠 정책 구현
- ❌ 요약 정책 미구현
- ❌ 구버전 인용률 측정 시스템 없음
- ❌ 모순률 측정 시스템 없음
- ❌ 성능-비용 곡선 추적 없음

**필요한 작업**:
1. **요약 정책 구현**
   ```python
   SummarizationPolicy:
       - 오래된 이벤트들을 LLM으로 요약
       - 원본 노드 제거, 요약 노드 생성
       - 압축률 추적
   ```

2. **평가 메트릭 구현**
   ```python
   metrics = {
       'obsolete_citation_rate': count(인용된 구버전) / count(전체 인용),
       'contradiction_rate': count(모순 응답) / count(전체 응답),
       'graph_size': nodes + edges,
       'query_latency': avg(query_time)
   }
   ```

3. **실험 설계**
   - 정책별 A/B 테스트
   - 시간 경과 시뮬레이션 (30일, 60일, 90일)
   - 성능-비용 트레이드오프 분석

**예상 구현 시간**: 2-3주

---

### **RQ3: 변경 영향 질문의 탐색시간/지연 개선**

**질문**: "변경 영향 질문"(예: L3 Corridor 덕트는 최근 뭐가 바뀌었나?)에서 탐색시간/지연이 얼마나 개선되나?

#### 🟡 **검증 가능성: 50%**

**현재 상태**:
- ✅ 연결된 컴포넌트 탐색 (`find_connected_components`)
- ✅ 시간 범위 필터링 (`find_by_time_range`)
- ✅ LLM 자연어 질의
- ⚠️ 탐색시간 측정 (일부 구현)
- ❌ 변경 diff 명시적 추적 없음
- ❌ 비교군 없음

**구현된 기능**:
```python
# 가능한 질의
ctxf ask "GUID 1kTv...와 연결된 최근 이슈는?"
ctxf timeline --start 2024-01-01 --end 2024-12-31
```

**필요한 작업**:
1. **변경 추적 강화**
   ```python
   def track_changes(guid, start_date, end_date):
       """특정 엔티티의 시간별 변경 이력 추출"""
       events = find_by_guid_and_time(guid, start_date, end_date)
       changes = extract_change_diff(events)
       return changes
   ```

2. **성능 측정**
   ```python
   @performance_monitor
   def change_impact_query(entity_name, time_range):
       start = time.time()
       results = execute_query(...)
       latency = time.time() - start
       return results, latency
   ```

3. **비교군 구현**
   - 선형 스캔 (모든 이벤트 순회)
   - 문서 기반 검색 (Elasticsearch 등)

**예상 구현 시간**: 1-2주

---

## 🎯 **전체 연구 검증 가능성 평가**

### **종합 점수: 45/100**

| 항목 | 구현도 | 검증 가능성 | 우선순위 |
|------|--------|-------------|----------|
| **G1: IFC-BCF 통합 그래프** | 80% | 60% | 🔴 높음 |
| **G2: 망각 메커니즘** | 60% | 40% | 🔴 높음 |
| **RQ1: RAG 비교** | 40% | 10% | 🔴 높음 |
| **RQ2: 망각 효과** | 50% | 30% | 🟡 중간 |
| **RQ3: 변경 영향** | 65% | 50% | 🟢 낮음 |
| **벤치마크 시스템** | 30% | 20% | 🔴 높음 |
| **재현 가능성** | 90% | 90% | ✅ 완료 |

---

## 🚨 **주요 누락 요소 (Critical Gaps)**

### **1. 평가 시스템 (Evaluation Framework)** 🔴

**현재**: 
- `eval/gold.jsonl` 존재하지만 미사용
- `src/contextualforget/core/eval_metrics.py` 기초만 구현

**필요**:
```python
class BenchmarkSystem:
    def __init__(self):
        self.gold_qa_pairs = load_gold_standard()
        self.baselines = [KeywordRAG(), VectorRAG(), DocumentRAG()]
        self.graph_rag = GraphRAG()
    
    def evaluate_all(self):
        results = {}
        for method in [*self.baselines, self.graph_rag]:
            results[method.name] = self.evaluate(method)
        return self.compare(results)
    
    def evaluate(self, method):
        metrics = {
            'accuracy': [],
            'attribution_precision': [],
            'attribution_recall': [],
            'latency': []
        }
        for qa in self.gold_qa_pairs:
            answer, evidence, time = method.query(qa.question)
            metrics['accuracy'].append(self.score_answer(answer, qa.gold_answer))
            metrics['attribution_precision'].append(
                self.score_evidence(evidence, qa.gold_evidence)
            )
            # ... 
        return aggregate(metrics)
```

### **2. 비교군 구현 (Baselines)** 🔴

**필요한 비교군**:
1. **키워드 RAG**: BM25 + TF-IDF
2. **벡터 RAG**: Sentence-BERT + FAISS
3. **문서 RAG**: 순수 텍스트 검색

### **3. 요약 압축 (Summarization)** 🔴

**현재**: 언급만 있고 구현 없음

**필요**:
```python
class SummarizationPolicy(ForgettingPolicy):
    def __init__(self, llm, time_window_days=30):
        self.llm = llm
        self.time_window = time_window_days
    
    def apply(self, graph, current_time):
        old_events = self.find_old_events(graph, current_time)
        
        # 유사한 이벤트들을 그룹화
        event_groups = self.group_by_similarity(old_events)
        
        for group in event_groups:
            # LLM으로 요약
            summary = self.llm.summarize(group)
            
            # 요약 노드 생성, 원본 노드 제거
            summary_node = self.create_summary_node(summary, group)
            graph.add_node(summary_node)
            
            for event in group:
                graph.remove_node(event.id)
        
        return graph
```

### **4. 변경 추적 (Change Tracking)** 🟡

**현재**: 간접적으로만 가능

**필요**:
```python
class ChangeTracker:
    def track_entity_changes(self, entity_guid, start_date, end_date):
        """엔티티의 시간별 변경 이력 추출"""
        events = self.get_events_for_entity(entity_guid, start_date, end_date)
        
        changes = []
        for i in range(len(events) - 1):
            diff = self.compute_diff(events[i], events[i+1])
            changes.append({
                'timestamp': events[i+1].date,
                'type': diff.type,  # 'status_change', 'description_update', etc.
                'before': diff.before_value,
                'after': diff.after_value,
                'author': events[i+1].author
            })
        
        return changes
```

### **5. 성능 벤치마킹 (Performance Benchmarking)** 🟡

**필요**:
```python
class PerformanceBenchmark:
    def measure_query_latency(self, method, queries, repetitions=100):
        latencies = []
        for query in queries:
            for _ in range(repetitions):
                start = time.time()
                method.query(query)
                latencies.append(time.time() - start)
        
        return {
            'mean': np.mean(latencies),
            'median': np.median(latencies),
            'p95': np.percentile(latencies, 95),
            'p99': np.percentile(latencies, 99)
        }
    
    def measure_index_size(self, method):
        return {
            'nodes': method.graph.number_of_nodes(),
            'edges': method.graph.number_of_edges(),
            'disk_size_mb': get_file_size(method.graph_path) / 1024 / 1024
        }
```

---

## 📈 **연구 검증을 위한 로드맵**

### **Phase 1: 평가 시스템 구축 (2주)** 🔴

1. Gold standard QA 데이터셋 생성 (50-100쌍)
2. 평가 메트릭 구현 (정확도, 근거 정확도, 지연시간)
3. 자동화된 벤치마크 스크립트

### **Phase 2: 비교군 구현 (2주)** 🔴

1. 키워드 RAG (BM25)
2. 벡터 RAG (Sentence-BERT + FAISS)
3. 통일된 쿼리 인터페이스

### **Phase 3: 망각 정책 완성 (2주)** 🟡

1. 요약 압축 정책 구현
2. 정책 조합 실험
3. 성능-비용 곡선 분석

### **Phase 4: 실험 & 논문 작성 (3-4주)** 🟢

1. 전체 실험 수행
2. 통계적 유의성 검증
3. 결과 분석 및 시각화
4. 논문 작성

**총 예상 기간: 9-10주**

---

## ✅ **현재 프로젝트의 강점**

1. **완전한 기술 스택**: ✅
   - IFC/BCF 파싱
   - 그래프 구축
   - 망각 메커니즘 (기초)
   - LLM 통합
   - 실시간 모니터링

2. **재현 가능성**: ✅
   - 오픈소스
   - 환경 정의
   - 샘플 데이터
   - 문서화

3. **확장 가능한 아키텍처**: ✅
   - 모듈화된 설계
   - 명확한 인터페이스
   - 테스트 커버리지

---

## 🎯 **결론 & 권고사항**

### **현재 상태 요약**

**✅ 잘 구현된 것**:
- 핵심 시스템 아키텍처
- IFC-BCF 통합 그래프
- 기본 망각 메커니즘
- LLM 자연어 질의
- 실시간 모니터링

**❌ 부족한 것**:
- **평가 시스템** (가장 critical)
- 비교군 (baselines)
- 요약 압축
- 정량적 메트릭

### **연구 논문 발표 가능성**

**현재 상태**: ❌ **불가능**
- 정량적 검증 없음
- 비교 실험 없음
- 통계적 유의성 부재

**Phase 1-2 완료 후**: 🟡 **Workshop/Demo 가능**
- 시스템 데모
- 예비 결과

**Phase 1-4 완료 후**: ✅ **Full paper 가능**
- ICSE, ASE, MSR 등 소프트웨어 공학 학회
- 또는 건설 정보학 학회 (ASCE, ECPPM 등)

### **최우선 작업 (다음 3주)**

1. **Week 1: 평가 데이터셋 생성**
   - 50-100개 QA 쌍
   - Gold standard 근거 링크

2. **Week 2: 비교군 구현**
   - 키워드 RAG
   - 벡터 RAG

3. **Week 3: 초기 실험**
   - RQ1 검증
   - 예비 결과 도출

---

## 📊 **최종 평가**

| 측면 | 점수 | 설명 |
|------|------|------|
| **기술 구현** | 85/100 | 핵심 시스템 잘 구현됨 |
| **연구 검증** | 45/100 | 평가 시스템 부족 |
| **논문 준비도** | 30/100 | 정량적 결과 부재 |
| **재현 가능성** | 90/100 | 매우 우수 |
| **혁신성** | 80/100 | BIM + LLM + 망각 융합 |

**종합**: 훌륭한 프로토타입이지만, **연구 논문으로 발표하려면 평가 시스템 구축이 필수**입니다.

