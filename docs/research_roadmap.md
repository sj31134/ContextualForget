# ContextualForget 연구 논문 작성 로드맵

## 🎯 목표: Top-tier 학회 Full Paper 투고 (ICSE, ASE, MSR, ECPPM)

**총 기간**: 9-10주 (2025년 10월 9일 ~ 12월 15일)  
**투고 목표**: ICSE 2026 (Research Track) 또는 ASE 2025

---

## 📅 전체 일정 개요

```
Week 1-2  : Phase 1 - 평가 시스템 구축
Week 3-4  : Phase 2 - 비교군 구현
Week 5-6  : Phase 3 - 망각 정책 완성
Week 7-9  : Phase 4 - 실험 & 분석
Week 10   : Phase 4 - 논문 작성 & 투고
```

---

## 📋 Phase 1: 평가 시스템 구축 (Week 1-2)

**목표**: Gold standard 데이터셋과 자동화된 벤치마크 시스템 구축

### Week 1 (Oct 9-15)

#### ✅ Task 1.1: Gold Standard QA 데이터셋 생성
**예상 시간**: 3-4일

**세부 작업**:
1. **QA 쌍 설계 (30개)**
   ```yaml
   카테고리별 분포:
   - 단순 사실 질의 (10개): "GUID xxx의 이름은?"
   - 관계 질의 (10개): "GUID xxx와 연결된 BCF 이슈는?"
   - 시간 질의 (5개): "최근 30일 이내 생성된 이슈는?"
   - 변경 영향 질의 (5개): "L3 Corridor에서 무엇이 바뀌었나?"
   ```

2. **각 QA에 대한 Gold Answer 작성**
   ```json
   {
     "question": "GUID 1kTvXnbbzCWw8lcMd1dR4o와 관련된 최근 이슈는?",
     "gold_answer": "총 2개의 이슈: 벽체 두께 불일치, 창호 위치 확인 필요",
     "gold_evidence": [
       {"type": "bcf", "id": "topic-001", "guid": "..."},
       {"type": "bcf", "id": "topic-002", "guid": "..."}
     ],
     "difficulty": "medium",
     "category": "relationship"
   }
   ```

3. **복잡도별 추가 생성 (20개)**
   - Easy (10개): 단일 노드 검색
   - Medium (5개): 1-hop 관계
   - Hard (5개): Multi-hop 추론

4. **데이터셋 검증**
   - 독립적인 검증자가 답변 확인
   - 모호한 질문 제거/수정

**산출물**:
- `eval/gold_standard_qa.jsonl` (50개 QA 쌍)
- `eval/dataset_statistics.json` (통계 정보)

---

#### ✅ Task 1.2: 평가 메트릭 구현
**예상 시간**: 3-4일

**세부 작업**:
1. **정답 정확도 메트릭**
   ```python
   # eval/metrics/answer_metrics.py
   
   def exact_match(predicted: str, gold: str) -> float:
       """완전 일치"""
       return 1.0 if predicted.strip() == gold.strip() else 0.0
   
   def f1_score(predicted: str, gold: str) -> float:
       """Token-level F1"""
       pred_tokens = set(tokenize(predicted))
       gold_tokens = set(tokenize(gold))
       
       if not pred_tokens or not gold_tokens:
           return 0.0
       
       precision = len(pred_tokens & gold_tokens) / len(pred_tokens)
       recall = len(pred_tokens & gold_tokens) / len(gold_tokens)
       
       if precision + recall == 0:
           return 0.0
       
       return 2 * precision * recall / (precision + recall)
   
   def bleu_score(predicted: str, gold: str) -> float:
       """BLEU score for answer quality"""
       from nltk.translate.bleu_score import sentence_bleu
       return sentence_bleu([tokenize(gold)], tokenize(predicted))
   ```

2. **근거 정확도 메트릭**
   ```python
   # eval/metrics/attribution_metrics.py
   
   def attribution_precision(predicted_evidence: List[str], 
                            gold_evidence: List[str]) -> float:
       """예측된 근거 중 정답 근거의 비율"""
       if not predicted_evidence:
           return 0.0
       
       correct = len(set(predicted_evidence) & set(gold_evidence))
       return correct / len(predicted_evidence)
   
   def attribution_recall(predicted_evidence: List[str], 
                         gold_evidence: List[str]) -> float:
       """정답 근거 중 예측된 근거의 비율"""
       if not gold_evidence:
           return 1.0  # No evidence required
       
       correct = len(set(predicted_evidence) & set(gold_evidence))
       return correct / len(gold_evidence)
   
   def attribution_f1(predicted_evidence: List[str], 
                     gold_evidence: List[str]) -> float:
       """Attribution F1 score"""
       precision = attribution_precision(predicted_evidence, gold_evidence)
       recall = attribution_recall(predicted_evidence, gold_evidence)
       
       if precision + recall == 0:
           return 0.0
       
       return 2 * precision * recall / (precision + recall)
   ```

3. **성능 메트릭**
   ```python
   # eval/metrics/performance_metrics.py
   
   def measure_latency(query_func: Callable, 
                      query: str, 
                      repetitions: int = 10) -> Dict[str, float]:
       """쿼리 지연 시간 측정"""
       latencies = []
       for _ in range(repetitions):
           start = time.time()
           query_func(query)
           latencies.append(time.time() - start)
       
       return {
           'mean': np.mean(latencies),
           'median': np.median(latencies),
           'std': np.std(latencies),
           'p95': np.percentile(latencies, 95),
           'p99': np.percentile(latencies, 99)
       }
   
   def measure_index_size(graph_path: str) -> Dict[str, Any]:
       """인덱스 크기 측정"""
       import pickle
       with open(graph_path, 'rb') as f:
           graph = pickle.load(f)
       
       return {
           'nodes': graph.number_of_nodes(),
           'edges': graph.number_of_edges(),
           'disk_size_mb': os.path.getsize(graph_path) / 1024 / 1024
       }
   ```

**산출물**:
- `src/contextualforget/eval/metrics/__init__.py`
- `src/contextualforget/eval/metrics/answer_metrics.py`
- `src/contextualforget/eval/metrics/attribution_metrics.py`
- `src/contextualforget/eval/metrics/performance_metrics.py`
- 단위 테스트 (`tests/test_eval_metrics.py`)

---

### Week 2 (Oct 16-22)

#### ✅ Task 1.3: 자동화 벤치마크 스크립트
**예상 시간**: 5-7일

**세부 작업**:
1. **통합 벤치마크 클래스**
   ```python
   # eval/benchmark.py
   
   class RAGBenchmark:
       """통합 RAG 벤치마크 시스템"""
       
       def __init__(self, 
                    gold_qa_path: str,
                    output_dir: str = "results/benchmark"):
           self.qa_pairs = self.load_gold_qa(gold_qa_path)
           self.output_dir = Path(output_dir)
           self.output_dir.mkdir(parents=True, exist_ok=True)
       
       def evaluate_method(self, 
                          method_name: str,
                          query_func: Callable,
                          evidence_func: Callable) -> Dict[str, Any]:
           """단일 RAG 방법 평가"""
           
           results = {
               'method': method_name,
               'timestamp': datetime.now().isoformat(),
               'qa_results': [],
               'aggregate_metrics': {}
           }
           
           answer_scores = []
           attribution_scores = []
           latencies = []
           
           for qa in tqdm(self.qa_pairs, desc=f"Evaluating {method_name}"):
               # 쿼리 실행
               start_time = time.time()
               predicted_answer = query_func(qa['question'])
               predicted_evidence = evidence_func(qa['question'])
               latency = time.time() - start_time
               
               # 정답 평가
               em = exact_match(predicted_answer, qa['gold_answer'])
               f1 = f1_score(predicted_answer, qa['gold_answer'])
               bleu = bleu_score(predicted_answer, qa['gold_answer'])
               
               # 근거 평가
               attr_p = attribution_precision(
                   predicted_evidence, qa['gold_evidence']
               )
               attr_r = attribution_recall(
                   predicted_evidence, qa['gold_evidence']
               )
               attr_f1 = attribution_f1(
                   predicted_evidence, qa['gold_evidence']
               )
               
               # 결과 저장
               qa_result = {
                   'question_id': qa['id'],
                   'question': qa['question'],
                   'predicted_answer': predicted_answer,
                   'gold_answer': qa['gold_answer'],
                   'metrics': {
                       'exact_match': em,
                       'f1': f1,
                       'bleu': bleu,
                       'attribution_precision': attr_p,
                       'attribution_recall': attr_r,
                       'attribution_f1': attr_f1,
                       'latency_ms': latency * 1000
                   }
               }
               results['qa_results'].append(qa_result)
               
               answer_scores.append(f1)
               attribution_scores.append(attr_f1)
               latencies.append(latency)
           
           # 집계 메트릭
           results['aggregate_metrics'] = {
               'mean_f1': np.mean(answer_scores),
               'mean_attribution_f1': np.mean(attribution_scores),
               'mean_latency_ms': np.mean(latencies) * 1000,
               'median_latency_ms': np.median(latencies) * 1000,
               'p95_latency_ms': np.percentile(latencies, 95) * 1000
           }
           
           # 결과 저장
           output_file = self.output_dir / f"{method_name}_results.json"
           with open(output_file, 'w') as f:
               json.dump(results, f, indent=2, ensure_ascii=False)
           
           return results
       
       def compare_methods(self, results_list: List[Dict]) -> pd.DataFrame:
           """여러 방법 비교"""
           comparison = []
           
           for result in results_list:
               comparison.append({
                   'Method': result['method'],
                   'F1 Score': result['aggregate_metrics']['mean_f1'],
                   'Attribution F1': result['aggregate_metrics']['mean_attribution_f1'],
                   'Latency (ms)': result['aggregate_metrics']['mean_latency_ms']
               })
           
           df = pd.DataFrame(comparison)
           
           # 시각화
           self.plot_comparison(df)
           
           return df
       
       def plot_comparison(self, df: pd.DataFrame):
           """결과 시각화"""
           fig, axes = plt.subplots(1, 3, figsize=(15, 5))
           
           # F1 Score
           df.plot(x='Method', y='F1 Score', kind='bar', ax=axes[0])
           axes[0].set_title('Answer F1 Score')
           axes[0].set_ylim(0, 1)
           
           # Attribution F1
           df.plot(x='Method', y='Attribution F1', kind='bar', ax=axes[1])
           axes[1].set_title('Attribution F1 Score')
           axes[1].set_ylim(0, 1)
           
           # Latency
           df.plot(x='Method', y='Latency (ms)', kind='bar', ax=axes[2])
           axes[2].set_title('Query Latency')
           
           plt.tight_layout()
           plt.savefig(self.output_dir / 'comparison.png', dpi=300)
   ```

2. **실행 스크립트**
   ```python
   # scripts/run_benchmark.py
   
   def main():
       # 벤치마크 초기화
       benchmark = RAGBenchmark('eval/gold_standard_qa.jsonl')
       
       # 현재 Graph-RAG 평가
       print("Evaluating Graph-RAG...")
       graph_rag_results = benchmark.evaluate_method(
           method_name='Graph-RAG',
           query_func=graph_rag_query,
           evidence_func=graph_rag_evidence
       )
       
       # 결과 출력
       print("\n=== Graph-RAG Results ===")
       print(f"F1 Score: {graph_rag_results['aggregate_metrics']['mean_f1']:.3f}")
       print(f"Attribution F1: {graph_rag_results['aggregate_metrics']['mean_attribution_f1']:.3f}")
       print(f"Latency: {graph_rag_results['aggregate_metrics']['mean_latency_ms']:.2f} ms")
   ```

**산출물**:
- `eval/benchmark.py`
- `scripts/run_benchmark.py`
- `results/benchmark/` (결과 디렉토리)
- 실행 문서 (`docs/benchmark_guide.md`)

---

## 📋 Phase 2: 비교군 구현 (Week 3-4)

**목표**: 키워드 RAG 및 벡터 RAG 비교군 구현

### Week 3 (Oct 23-29)

#### ✅ Task 2.1: 키워드 RAG (BM25) 구현
**예상 시간**: 5-7일

**세부 작업**:
1. **BM25 인덱스 구축**
   ```python
   # src/contextualforget/baselines/keyword_rag.py
   
   from rank_bm25 import BM25Okapi
   import nltk
   
   class KeywordRAG:
       """BM25 기반 키워드 RAG"""
       
       def __init__(self, graph_path: str):
           self.graph = self.load_graph(graph_path)
           self.documents = self.extract_documents()
           self.bm25 = self.build_index()
       
       def extract_documents(self) -> List[Dict]:
           """그래프에서 문서 추출"""
           documents = []
           
           for node_id, data in self.graph.nodes(data=True):
               if data.get('type') == 'ifc':
                   doc = {
                       'id': node_id,
                       'text': f"{data.get('name', '')} {data.get('ifc_type', '')}",
                       'type': 'ifc',
                       'data': data
                   }
               elif data.get('type') == 'bcf':
                   doc = {
                       'id': node_id,
                       'text': f"{data.get('title', '')} {data.get('description', '')}",
                       'type': 'bcf',
                       'data': data
                   }
               else:
                   continue
               
               documents.append(doc)
           
           return documents
       
       def build_index(self) -> BM25Okapi:
           """BM25 인덱스 구축"""
           tokenized_docs = [
               self.tokenize(doc['text']) 
               for doc in self.documents
           ]
           return BM25Okapi(tokenized_docs)
       
       def tokenize(self, text: str) -> List[str]:
           """텍스트 토큰화"""
           return nltk.word_tokenize(text.lower())
       
       def query(self, question: str, top_k: int = 5) -> str:
           """질의 처리"""
           # 토큰화
           query_tokens = self.tokenize(question)
           
           # BM25 검색
           scores = self.bm25.get_scores(query_tokens)
           top_indices = np.argsort(scores)[::-1][:top_k]
           
           # 결과 조합
           retrieved_docs = [self.documents[i] for i in top_indices]
           
           # 답변 생성 (간단한 추출)
           answer = self.generate_answer(question, retrieved_docs)
           
           return answer
       
       def get_evidence(self, question: str, top_k: int = 5) -> List[str]:
           """근거 문서 반환"""
           query_tokens = self.tokenize(question)
           scores = self.bm25.get_scores(query_tokens)
           top_indices = np.argsort(scores)[::-1][:top_k]
           
           return [self.documents[i]['id'] for i in top_indices]
       
       def generate_answer(self, question: str, docs: List[Dict]) -> str:
           """검색된 문서로부터 답변 생성"""
           # 간단한 추출식 답변
           if 'guid' in question.lower() or '관련' in question:
               # BCF 토픽 추출
               topics = [d for d in docs if d['type'] == 'bcf']
               if topics:
                   titles = [t['data'].get('title', '') for t in topics]
                   return f"총 {len(titles)}개의 이슈: " + ", ".join(titles[:3])
           
           # 기본 답변
           return docs[0]['text'] if docs else "답변을 찾을 수 없습니다."
   ```

2. **벤치마크 통합**
   ```python
   # scripts/run_benchmark.py 업데이트
   
   # BM25 평가 추가
   print("\nEvaluating BM25 Keyword RAG...")
   keyword_rag = KeywordRAG('data/processed/graph.gpickle')
   keyword_results = benchmark.evaluate_method(
       method_name='Keyword-RAG (BM25)',
       query_func=keyword_rag.query,
       evidence_func=keyword_rag.get_evidence
   )
   ```

**산출물**:
- `src/contextualforget/baselines/keyword_rag.py`
- `tests/test_keyword_rag.py`
- `results/benchmark/keyword_rag_results.json`

---

### Week 4 (Oct 30 - Nov 5)

#### ✅ Task 2.2: 벡터 RAG (Sentence-BERT + FAISS) 구현
**예상 시간**: 5-7일

**세부 작업**:
1. **임베딩 및 FAISS 인덱스**
   ```python
   # src/contextualforget/baselines/vector_rag.py
   
   from sentence_transformers import SentenceTransformer
   import faiss
   
   class VectorRAG:
       """Sentence-BERT + FAISS 기반 벡터 RAG"""
       
       def __init__(self, 
                    graph_path: str,
                    model_name: str = 'paraphrase-multilingual-mpnet-base-v2'):
           self.graph = self.load_graph(graph_path)
           self.model = SentenceTransformer(model_name)
           self.documents = self.extract_documents()
           self.embeddings = None
           self.index = None
           self.build_index()
       
       def extract_documents(self) -> List[Dict]:
           """그래프에서 문서 추출 (KeywordRAG와 동일)"""
           # ... (KeywordRAG와 동일한 로직)
       
       def build_index(self):
           """FAISS 인덱스 구축"""
           print("Building vector embeddings...")
           texts = [doc['text'] for doc in self.documents]
           self.embeddings = self.model.encode(texts, show_progress_bar=True)
           
           print("Building FAISS index...")
           dimension = self.embeddings.shape[1]
           self.index = faiss.IndexFlatL2(dimension)
           self.index.add(self.embeddings.astype('float32'))
           
           print(f"Index built: {len(self.documents)} documents, {dimension}D")
       
       def query(self, question: str, top_k: int = 5) -> str:
           """질의 처리"""
           # 질문 임베딩
           query_embedding = self.model.encode([question])
           
           # FAISS 검색
           distances, indices = self.index.search(
               query_embedding.astype('float32'), top_k
           )
           
           # 결과 조합
           retrieved_docs = [self.documents[i] for i in indices[0]]
           
           # 답변 생성
           answer = self.generate_answer(question, retrieved_docs)
           
           return answer
       
       def get_evidence(self, question: str, top_k: int = 5) -> List[str]:
           """근거 문서 반환"""
           query_embedding = self.model.encode([question])
           distances, indices = self.index.search(
               query_embedding.astype('float32'), top_k
           )
           
           return [self.documents[i]['id'] for i in indices[0]]
       
       def generate_answer(self, question: str, docs: List[Dict]) -> str:
           """검색된 문서로부터 답변 생성 (KeywordRAG와 동일)"""
           # ... (KeywordRAG와 동일한 로직)
   ```

2. **벤치마크 통합**
   ```python
   # scripts/run_benchmark.py 업데이트
   
   # Vector RAG 평가 추가
   print("\nEvaluating Vector RAG...")
   vector_rag = VectorRAG('data/processed/graph.gpickle')
   vector_results = benchmark.evaluate_method(
       method_name='Vector-RAG (SBERT+FAISS)',
       query_func=vector_rag.query,
       evidence_func=vector_rag.get_evidence
   )
   
   # 전체 비교
   print("\n=== Comparison ===")
   comparison_df = benchmark.compare_methods([
       graph_rag_results,
       keyword_results,
       vector_results
   ])
   print(comparison_df)
   ```

**산출물**:
- `src/contextualforget/baselines/vector_rag.py`
- `tests/test_vector_rag.py`
- `results/benchmark/vector_rag_results.json`
- `results/benchmark/comparison.png`

---

#### ✅ Task 2.3: RQ1 초기 실험
**예상 시간**: 2-3일

**세부 작업**:
1. **3가지 방법 비교 실험**
2. **통계적 유의성 검정 (t-test)**
3. **결과 분석 및 시각화**
4. **예비 논문 Results 섹션 작성**

**산출물**:
- `results/rq1_preliminary_results.pdf`
- `docs/rq1_analysis.md`

---

## 📋 Phase 3: 망각 정책 완성 (Week 5-6)

**목표**: 요약 압축 정책 구현 및 망각 효과 측정

### Week 5 (Nov 6-12)

#### ✅ Task 3.1: LLM 요약 압축 정책 구현
**예상 시간**: 5-7일

**세부 작업**:
1. **요약 정책 클래스**
   ```python
   # src/contextualforget/core/summarization_policy.py
   
   from langchain_ollama import ChatOllama
   
   class SummarizationPolicy(ForgettingPolicy):
       """LLM 기반 이벤트 요약 압축 정책"""
       
       def __init__(self, 
                    model_name: str = "qwen2.5:3b",
                    time_window_days: int = 30,
                    min_events_for_summary: int = 3):
           self.llm = ChatOllama(model=model_name, temperature=0.3)
           self.time_window = time_window_days
           self.min_events = min_events_for_summary
       
       def should_forget(self, event: Dict, current_time: datetime) -> bool:
           """개별 이벤트는 삭제하지 않음 (그룹 단위 요약)"""
           return False
       
       def apply(self, graph: nx.DiGraph, current_time: datetime) -> nx.DiGraph:
           """오래된 이벤트들을 요약하여 압축"""
           
           # 오래된 이벤트 추출
           old_events = self.find_old_events(graph, current_time)
           
           if len(old_events) < self.min_events:
               logger.info("요약할 이벤트가 부족합니다")
               return graph
           
           # 유사한 이벤트 그룹화
           event_groups = self.group_by_similarity(old_events)
           
           compression_stats = {
               'original_nodes': len(old_events),
               'summary_nodes': 0,
               'compression_ratio': 0
           }
           
           for group in event_groups:
               if len(group) < self.min_events:
                   continue
               
               # LLM으로 요약 생성
               summary = self.summarize_events(group)
               
               # 요약 노드 생성
               summary_node_id = self.create_summary_node(graph, summary, group)
               compression_stats['summary_nodes'] += 1
               
               # 원본 노드 제거 및 엣지 재연결
               self.replace_nodes_with_summary(graph, group, summary_node_id)
           
           # 압축률 계산
           compression_stats['compression_ratio'] = (
               1 - compression_stats['summary_nodes'] / 
               compression_stats['original_nodes']
           )
           
           logger.info(f"요약 압축 완료: {compression_stats}")
           return graph
       
       def find_old_events(self, 
                          graph: nx.DiGraph, 
                          current_time: datetime) -> List[tuple]:
           """오래된 BCF 이벤트 찾기"""
           cutoff_date = current_time - timedelta(days=self.time_window)
           old_events = []
           
           for node_id, data in graph.nodes(data=True):
               if data.get('type') != 'bcf':
                   continue
               
               created_date = datetime.fromisoformat(
                   data.get('created_at', current_time.isoformat())
               )
               
               if created_date < cutoff_date:
                   old_events.append((node_id, data))
           
           return old_events
       
       def group_by_similarity(self, 
                              events: List[tuple]) -> List[List[tuple]]:
           """유사한 이벤트들을 그룹화"""
           # 간단한 구현: GUID 기반 그룹화
           # 실제로는 임베딩 유사도 기반 클러스터링
           
           groups_dict = {}
           
           for node_id, data in events:
               # 연결된 IFC GUID 기반 그룹화
               connected_guids = tuple(sorted(data.get('related_guids', [])))
               
               if connected_guids not in groups_dict:
                   groups_dict[connected_guids] = []
               
               groups_dict[connected_guids].append((node_id, data))
           
           return list(groups_dict.values())
       
       def summarize_events(self, event_group: List[tuple]) -> str:
           """LLM으로 이벤트 그룹 요약"""
           # 이벤트 텍스트 추출
           event_texts = []
           for node_id, data in event_group:
               text = f"- [{data.get('created_at', '')}] {data.get('title', '')}: {data.get('description', '')}"
               event_texts.append(text)
           
           # LLM 프롬프트
           prompt = f"""다음 BIM 프로젝트 이슈들을 하나의 요약문으로 통합하세요.
핵심 정보(날짜 범위, 주요 문제, 관련 부재)를 유지하되 간결하게 작성하세요.

이벤트들:
{chr(10).join(event_texts)}

요약 (50단어 이내):"""
           
           # LLM 호출
           response = self.llm.invoke(prompt)
           summary = response.content.strip()
           
           return summary
       
       def create_summary_node(self, 
                              graph: nx.DiGraph, 
                              summary: str, 
                              original_events: List[tuple]) -> str:
           """요약 노드 생성"""
           import uuid
           summary_node_id = f"summary:{uuid.uuid4()}"
           
           # 메타데이터 통합
           start_date = min(
               datetime.fromisoformat(data.get('created_at', ''))
               for _, data in original_events
           )
           end_date = max(
               datetime.fromisoformat(data.get('created_at', ''))
               for _, data in original_events
           )
           
           graph.add_node(summary_node_id, **{
               'type': 'summary',
               'text': summary,
               'original_count': len(original_events),
               'date_range_start': start_date.isoformat(),
               'date_range_end': end_date.isoformat(),
               'created_at': datetime.now().isoformat()
           })
           
           return summary_node_id
       
       def replace_nodes_with_summary(self, 
                                     graph: nx.DiGraph, 
                                     original_nodes: List[tuple], 
                                     summary_node_id: str):
           """원본 노드를 요약 노드로 교체하고 엣지 재연결"""
           # 모든 원본 노드의 이웃 수집
           all_neighbors = set()
           
           for node_id, _ in original_nodes:
               # 선행자 (predecessors)
               all_neighbors.update(graph.predecessors(node_id))
               # 후속자 (successors)
               all_neighbors.update(graph.successors(node_id))
           
           # 요약 노드와 이웃들 연결
           for neighbor in all_neighbors:
               if neighbor not in [n[0] for n in original_nodes]:
                   graph.add_edge(summary_node_id, neighbor, 
                                relation='summarized')
           
           # 원본 노드 제거
           for node_id, _ in original_nodes:
               graph.remove_node(node_id)
   ```

2. **통합 및 테스트**
   ```python
   # tests/test_summarization_policy.py
   
   def test_summarization_policy():
       # 테스트 그래프 생성
       graph = create_test_graph_with_old_events()
       
       # 요약 정책 적용
       policy = SummarizationPolicy(time_window_days=30)
       compressed_graph = policy.apply(graph, datetime.now())
       
       # 검증
       assert compressed_graph.number_of_nodes() < graph.number_of_nodes()
       
       # 요약 노드 확인
       summary_nodes = [
           n for n, d in compressed_graph.nodes(data=True) 
           if d.get('type') == 'summary'
       ]
       assert len(summary_nodes) > 0
   ```

**산출물**:
- `src/contextualforget/core/summarization_policy.py`
- `tests/test_summarization_policy.py`
- `docs/summarization_guide.md`

---

### Week 6 (Nov 13-19)

#### ✅ Task 3.2: 구버전 인용률/모순률 측정 시스템
**예상 시간**: 3-4일

**세부 작업**:
1. **구버전 인용률 측정**
   ```python
   # eval/metrics/forgetting_metrics.py
   
   def measure_obsolete_citation_rate(graph: nx.DiGraph,
                                      query_results: List[Dict],
                                      current_time: datetime,
                                      ttl_days: int) -> float:
       """구버전 인용률 측정"""
       cutoff_date = current_time - timedelta(days=ttl_days)
       
       total_citations = 0
       obsolete_citations = 0
       
       for result in query_results:
           for evidence_id in result.get('evidence', []):
               total_citations += 1
               
               # 노드 날짜 확인
               node_data = graph.nodes[evidence_id]
               created_date = datetime.fromisoformat(
                   node_data.get('created_at', '')
               )
               
               if created_date < cutoff_date:
                   obsolete_citations += 1
       
       return obsolete_citations / total_citations if total_citations > 0 else 0.0
   
   def measure_contradiction_rate(query_results: List[Dict],
                                 llm_checker: Callable) -> float:
       """모순률 측정 (LLM 기반)"""
       total_pairs = 0
       contradictions = 0
       
       # 동일 GUID에 대한 여러 답변 비교
       guid_answers = {}
       for result in query_results:
           guid = result.get('guid')
           answer = result.get('answer')
           
           if guid not in guid_answers:
               guid_answers[guid] = []
           guid_answers[guid].append(answer)
       
       # 쌍별 모순 검사
       for guid, answers in guid_answers.items():
           for i in range(len(answers)):
               for j in range(i + 1, len(answers)):
                   total_pairs += 1
                   if llm_checker(answers[i], answers[j]):
                       contradictions += 1
       
       return contradictions / total_pairs if total_pairs > 0 else 0.0
   ```

2. **LLM 기반 모순 검사기**
   ```python
   class ContradictionChecker:
       """LLM 기반 모순 검사"""
       
       def __init__(self, model_name: str = "qwen2.5:3b"):
           self.llm = ChatOllama(model=model_name, temperature=0.1)
       
       def check_contradiction(self, answer1: str, answer2: str) -> bool:
           """두 답변이 모순되는지 확인"""
           prompt = f"""다음 두 답변이 서로 모순되는지 판단하세요.

답변 1: {answer1}
답변 2: {answer2}

모순 여부 (yes/no):"""
           
           response = self.llm.invoke(prompt)
           return 'yes' in response.content.lower()
   ```

**산출물**:
- `eval/metrics/forgetting_metrics.py`
- `tests/test_forgetting_metrics.py`

---

#### ✅ Task 3.3: 망각 정책 조합 실험
**예상 시간**: 2-3일

**세부 작업**:
1. **정책 조합 실험 설계**
   ```python
   # scripts/forgetting_experiments.py
   
   def run_forgetting_experiments():
       """다양한 망각 정책 조합 실험"""
       
       policies = {
           'None': None,
           'TTL-30': TTLPolicy(ttl_days=30),
           'TTL-60': TTLPolicy(ttl_days=60),
           'Decay': WeightedDecayPolicy(decay_rate=0.1),
           'Summary-30': SummarizationPolicy(time_window_days=30),
           'TTL+Decay': CompositePolicy([
               TTLPolicy(ttl_days=30),
               WeightedDecayPolicy(decay_rate=0.1)
           ]),
           'TTL+Summary': CompositePolicy([
               TTLPolicy(ttl_days=60),
               SummarizationPolicy(time_window_days=30)
           ])
       }
       
       results = []
       
       for policy_name, policy in policies.items():
           print(f"\nTesting {policy_name}...")
           
           # 그래프 로드
           graph = load_base_graph()
           
           # 정책 적용
           if policy:
               graph = policy.apply(graph, datetime.now())
           
           # 측정
           obsolete_rate = measure_obsolete_citation_rate(graph, ...)
           contradiction_rate = measure_contradiction_rate(...)
           graph_size = graph.number_of_nodes()
           query_latency = measure_average_latency(graph, ...)
           
           results.append({
               'policy': policy_name,
               'obsolete_rate': obsolete_rate,
               'contradiction_rate': contradiction_rate,
               'graph_size': graph_size,
               'query_latency_ms': query_latency
           })
       
       # 결과 저장 및 시각화
       df = pd.DataFrame(results)
       df.to_csv('results/forgetting_experiments.csv', index=False)
       plot_performance_cost_curve(df)
   ```

2. **성능-비용 곡선 시각화**
   ```python
   def plot_performance_cost_curve(df: pd.DataFrame):
       """성능-비용 트레이드오프 시각화"""
       fig, axes = plt.subplots(2, 2, figsize=(12, 10))
       
       # 구버전 인용률
       df.plot(x='policy', y='obsolete_rate', kind='bar', ax=axes[0,0])
       axes[0,0].set_title('Obsolete Citation Rate')
       
       # 모순률
       df.plot(x='policy', y='contradiction_rate', kind='bar', ax=axes[0,1])
       axes[0,1].set_title('Contradiction Rate')
       
       # 그래프 크기
       df.plot(x='policy', y='graph_size', kind='bar', ax=axes[1,0])
       axes[1,0].set_title('Graph Size (nodes)')
       
       # 쿼리 지연
       df.plot(x='policy', y='query_latency_ms', kind='bar', ax=axes[1,1])
       axes[1,1].set_title('Query Latency (ms)')
       
       plt.tight_layout()
       plt.savefig('results/performance_cost_curve.png', dpi=300)
   ```

**산출물**:
- `scripts/forgetting_experiments.py`
- `results/forgetting_experiments.csv`
- `results/performance_cost_curve.png`
- `docs/rq2_analysis.md`

---

## 📋 Phase 4: 실험 & 논문 작성 (Week 7-10)

### Week 7-8 (Nov 20 - Dec 3)

#### ✅ Task 4.1: 전체 실험 수행
**예상 시간**: 10-14일

**세부 작업**:
1. **RQ1 전체 실험** (3일)
   - 3가지 RAG 방법 완전 비교
   - 난이도별, 카테고리별 분석
   - 통계적 유의성 검정

2. **RQ2 전체 실험** (4일)
   - 7가지 망각 정책 조합 비교
   - 시간 경과 시뮬레이션 (30/60/90일)
   - 성능-비용 트레이드오프 분석

3. **RQ3 전체 실험** (3일)
   - 변경 영향 질의 실험
   - 탐색 시간 비교 (Graph vs Linear scan)
   - 다양한 홉 수 실험 (1-hop, 2-hop, 3-hop)

4. **추가 분석** (2-3일)
   - 오류 분석 (Error Analysis)
   - Ablation Study
   - 스케일러빌리티 테스트

**산출물**:
- `results/rq1_full_results.json`
- `results/rq2_full_results.json`
- `results/rq3_full_results.json`
- 모든 시각화 자료 (`.png`, `.pdf`)

---

### Week 9 (Dec 4-10)

#### ✅ Task 4.2: 통계 분석 및 시각화
**예상 시간**: 5-7일

**세부 작업**:
1. **통계적 유의성 검정**
   ```python
   # scripts/statistical_analysis.py
   
   from scipy import stats
   
   def perform_statistical_tests(results: Dict):
       """통계적 유의성 검정"""
       
       # RQ1: Graph-RAG vs Baselines
       graph_rag_f1 = results['graph_rag']['f1_scores']
       keyword_rag_f1 = results['keyword_rag']['f1_scores']
       vector_rag_f1 = results['vector_rag']['f1_scores']
       
       # t-test
       t_stat_kw, p_value_kw = stats.ttest_ind(graph_rag_f1, keyword_rag_f1)
       t_stat_vec, p_value_vec = stats.ttest_ind(graph_rag_f1, vector_rag_f1)
       
       print(f"Graph-RAG vs Keyword-RAG: t={t_stat_kw:.3f}, p={p_value_kw:.4f}")
       print(f"Graph-RAG vs Vector-RAG: t={t_stat_vec:.3f}, p={p_value_vec:.4f}")
       
       # Effect size (Cohen's d)
       cohens_d_kw = calculate_cohens_d(graph_rag_f1, keyword_rag_f1)
       cohens_d_vec = calculate_cohens_d(graph_rag_f1, vector_rag_f1)
       
       print(f"Effect size (Keyword): d={cohens_d_kw:.3f}")
       print(f"Effect size (Vector): d={cohens_d_vec:.3f}")
   ```

2. **논문 품질 Figure 생성**
   - Publication-ready plots (LaTeX 호환)
   - 색상 팔레트 일관성
   - 높은 해상도 (300+ DPI)

3. **표 생성**
   - LaTeX 형식 표
   - 주요 결과 요약 표

**산출물**:
- `results/statistical_analysis.pdf`
- `paper/figures/` (모든 논문용 그림)
- `paper/tables/` (모든 논문용 표)

---

### Week 10 (Dec 11-15)

#### ✅ Task 4.3: 논문 작성 & 투고
**예상 시간**: 5-7일

**세부 작업**:
1. **논문 구조** (ACM/IEEE 형식)
   ```
   1. Abstract (150-200 words)
   2. Introduction (2 pages)
      - Motivation
      - Problem Statement
      - Contributions
   3. Background & Related Work (2-3 pages)
      - IFC/BCF in BIM
      - RAG Systems
      - Long-term Memory in AI
   4. Approach (3-4 pages)
      - System Architecture
      - Graph-based Integration
      - Forgetting Mechanisms
      - LLM Integration
   5. Implementation (1-2 pages)
      - Tech Stack
      - Data Processing
      - Real-time Monitoring
   6. Evaluation (4-5 pages)
      - Experimental Setup
      - RQ1 Results: Graph-RAG vs Baselines
      - RQ2 Results: Forgetting Policies
      - RQ3 Results: Change Impact Tracking
      - Discussion
   7. Threats to Validity (0.5-1 page)
   8. Related Work (1-2 pages)
   9. Conclusion & Future Work (0.5-1 page)
   10. References
   
   Total: ~12-15 pages (ACM double column)
   ```

2. **집필 일정**
   - Day 1-2: Abstract, Introduction, Approach 초안
   - Day 3-4: Evaluation, Results 작성
   - Day 5: Background, Related Work, Conclusion
   - Day 6: 전체 편집 및 교정
   - Day 7: 최종 검토 및 투고 준비

3. **Artifact 준비**
   - GitHub 저장소 정리
   - README 최종 업데이트
   - Replication Package
   - Zenodo DOI 발급

**산출물**:
- `paper/contextualforget_paper.pdf`
- `paper/contextualforget_paper.tex`
- Artifact 패키지
- 투고 완료!

---

## 📊 주차별 체크리스트

### Week 1 체크리스트
- [ ] Gold QA 데이터셋 50개 생성
- [ ] 정답 정확도 메트릭 구현
- [ ] 근거 정확도 메트릭 구현
- [ ] 성능 메트릭 구현
- [ ] 단위 테스트 작성

### Week 2 체크리스트
- [ ] 벤치마크 클래스 구현
- [ ] 실행 스크립트 작성
- [ ] Graph-RAG 평가 완료
- [ ] 결과 시각화
- [ ] 문서 작성

### Week 3 체크리스트
- [ ] BM25 인덱스 구현
- [ ] 키워드 RAG 쿼리 로직
- [ ] 벤치마크 통합
- [ ] 테스트 작성
- [ ] 결과 분석

### Week 4 체크리스트
- [ ] Sentence-BERT 임베딩
- [ ] FAISS 인덱스 구축
- [ ] 벡터 RAG 쿼리 로직
- [ ] 3가지 방법 비교
- [ ] RQ1 예비 결과

### Week 5 체크리스트
- [ ] 요약 정책 클래스 구현
- [ ] LLM 요약 로직
- [ ] 노드 교체 로직
- [ ] 통합 테스트
- [ ] 문서 작성

### Week 6 체크리스트
- [ ] 구버전 인용률 측정
- [ ] 모순률 측정
- [ ] 정책 조합 실험
- [ ] 성능-비용 곡선 생성
- [ ] RQ2 결과 분석

### Week 7-8 체크리스트
- [ ] RQ1 전체 실험
- [ ] RQ2 전체 실험
- [ ] RQ3 전체 실험
- [ ] 오류 분석
- [ ] Ablation Study

### Week 9 체크리스트
- [ ] 통계적 유의성 검정
- [ ] Publication figure 생성
- [ ] LaTeX 표 생성
- [ ] 결과 문서 작성

### Week 10 체크리스트
- [ ] 논문 초안 작성
- [ ] 전체 편집
- [ ] Artifact 준비
- [ ] 최종 검토
- [ ] 투고!

---

## 🎯 성공 기준 (Success Criteria)

### Phase 1 완료 기준
- ✅ 50개 이상의 Gold QA 쌍
- ✅ 5개 이상의 평가 메트릭 구현
- ✅ 자동화된 벤치마크 실행 가능
- ✅ Graph-RAG 베이스라인 결과

### Phase 2 완료 기준
- ✅ 2개 이상의 비교군 구현
- ✅ 3가지 방법 비교 완료
- ✅ 통계적 유의성 확인 (p < 0.05)
- ✅ RQ1 예비 답변 가능

### Phase 3 완료 기준
- ✅ 요약 압축 정책 작동
- ✅ 구버전 인용률 측정 가능
- ✅ 7가지 정책 조합 비교
- ✅ 성능-비용 곡선 도출

### Phase 4 완료 기준
- ✅ 3개 RQ 모두 답변 가능
- ✅ 통계적으로 유의미한 결과
- ✅ 12-15페이지 논문 완성
- ✅ Replication package 준비

---

## 📚 필요 리소스

### 소프트웨어
- Python 3.11+
- 추가 패키지:
  ```bash
  pip install rank-bm25 sentence-transformers faiss-cpu nltk scipy pandas matplotlib seaborn
  ```

### 하드웨어
- 현재 M4 Pro (24GB RAM) 충분
- FAISS 인덱싱 시 메모리 모니터링 필요

### 데이터
- 현재 6개 건물, 87개 노드로 시작
- Phase 1에서 더 많은 샘플 필요 시 추가 생성

### 시간
- 주당 30-40시간 작업 필요
- 총 270-360시간 (9-10주 × 30-40시간)

---

## 🚨 위험 요소 및 대응책

### 위험 1: 평가 데이터셋 품질
**위험**: Gold QA가 너무 쉽거나 편향됨
**대응**: 
- 독립 검증자 확보
- 다양한 난이도 균형
- Pilot study로 사전 검증

### 위험 2: 비교군 성능 저조
**위험**: 모든 방법이 비슷한 성능
**대응**:
- 난이도 높은 질문 추가
- Multi-hop 추론 질문 포함
- 실제 BIM 전문가 질문 수집

### 위험 3: 요약 압축 품질
**위험**: LLM 요약이 정보 손실
**대응**:
- 요약 품질 메트릭 추가
- 사람 평가 (Human Evaluation)
- 여러 LLM 모델 비교

### 위험 4: 시간 부족
**위험**: 10주 내 완료 불가
**대응**:
- 주차별 마일스톤 엄격 관리
- 필요 시 Phase 4 축소
- Workshop 먼저, Full paper 이후

---

## 📈 진행 상황 추적

**현재 상태**: Phase 0 완료 (시스템 프로토타입)
**다음 단계**: Phase 1 Task 1.1 시작

### 주간 보고 형식
```markdown
## Week X 진행 보고 (MM/DD - MM/DD)

### 완료한 작업
- [ ] Task X.Y: ...

### 진행 중인 작업
- [ ] Task X.Z: ...

### 다음 주 계획
- [ ] Task A.B: ...

### 이슈 및 차단 요소
- 없음 / [이슈 설명]

### 일정 상태
- ✅ 일정 준수 / ⚠️ 1-2일 지연 / 🚨 3일+ 지연
```

---

## ✅ 즉시 시작 가능한 작업

### 내일 (Oct 10) 시작:
1. **QA 데이터셋 설계 문서 작성**
   - 카테고리 정의
   - 질문 템플릿 작성
   - 첫 10개 QA 쌍 작성

2. **평가 메트릭 기본 구조 코딩**
   - `eval/metrics/__init__.py` 생성
   - `answer_metrics.py` 스켈레톤 코드

3. **프로젝트 구조 정리**
   ```bash
   mkdir -p eval/metrics
   mkdir -p src/contextualforget/baselines
   mkdir -p paper/figures
   mkdir -p paper/tables
   ```

**첫 주 목표**: Gold QA 30개 + 평가 메트릭 2개 구현 완료!

---

모든 계획이 수립되었습니다! 🚀 
내일부터 Phase 1.1을 시작하시겠습니까?

