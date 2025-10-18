# 망각 점수 계산 수식 및 적응적 선택 알고리즘

## 1. 망각 점수 계산 수식

### 1.1 기본 망각 점수 공식

```
Forgetting Score = w_u × Usage Score + w_r × Recency Score + w_v × Relevance Score

S_f(d,t) = w_u·S_u(d) + w_r·S_r(d,t) + w_v·S_v(d,q)
```

**여기서:**
- `S_f(d,t)`: 문서 d의 시간 t에서의 망각 점수
- `w_u = 0.3`: 사용 빈도 가중치
- `w_r = 0.4`: 최근성 가중치  
- `w_v = 0.3`: 관련성 가중치

### 1.2 구성 요소별 계산

#### 1.2.1 사용 빈도 점수 (Usage Score)

```
S_u(d) = min(N_access(d) / 10, 1.0)
```

**여기서:**
- `N_access(d)`: 문서 d의 총 접근 횟수
- 최대값 1.0으로 정규화 (10회 이상 접근시 포화)

#### 1.2.2 최근성 점수 (Recency Score)

```
S_r(d,t) = exp(-λ × (t - t_last) / 365)
```

**여기서:**
- `λ = 0.1`: 감쇠율 (decay rate)
- `t`: 현재 시간
- `t_last`: 마지막 접근 시간
- `365`: 정규화 상수 (1년 기준)

#### 1.2.3 관련성 점수 (Relevance Score)

```
S_v(d,q) = cosine_similarity(E(d), E(q))
```

**여기서:**
- `E(d)`: 문서 d의 임베딩 벡터
- `E(q)`: 쿼리 q의 임베딩 벡터
- `cosine_similarity`: 코사인 유사도 계산

### 1.3 망각 점수 적용 알고리즘

```python
def calculate_forgetting_score(document, query, current_time):
    """
    망각 점수 계산 함수
    
    Args:
        document: 문서 객체 (접근 이력, 임베딩 포함)
        query: 쿼리 객체 (임베딩 포함)
        current_time: 현재 시간
    
    Returns:
        float: 망각 점수 (0.0 ~ 1.0)
    """
    
    # 1. 사용 빈도 점수 계산
    access_count = document.get_access_count()
    usage_score = min(access_count / 10.0, 1.0)
    
    # 2. 최근성 점수 계산
    last_access = document.get_last_access_time()
    days_since_access = (current_time - last_access).days
    recency_score = math.exp(-0.1 * days_since_access / 365.0)
    
    # 3. 관련성 점수 계산
    doc_embedding = document.get_embedding()
    query_embedding = query.get_embedding()
    relevance_score = cosine_similarity(doc_embedding, query_embedding)
    
    # 4. 가중합으로 최종 점수 계산
    forgetting_score = (0.3 * usage_score + 
                       0.4 * recency_score + 
                       0.3 * relevance_score)
    
    return forgetting_score
```

## 2. 적응적 엔진 선택 알고리즘

### 2.1 기본 선택 알고리즘

```python
Algorithm: Adaptive Engine Selection
Input: query, performance_history, exploration_rate=0.1
Output: selected_engine

1. query_type ← classify_query(query)
2. candidate_engines ← get_engines_for_type(query_type)
3. recent_performance ← get_recent_performance(query_type, performance_history)
4. 
5. if random() < exploration_rate:
6.     return random_choice(candidate_engines)
7. else:
8.     return argmax(recent_performance)
```

### 2.2 쿼리 타입 분류 알고리즘

```python
def classify_query(query_text):
    """
    쿼리 타입 자동 분류
    
    Args:
        query_text: 입력 쿼리 텍스트
    
    Returns:
        str: 쿼리 타입 ('guid', 'temporal', 'author', 'keyword', 'complex', 'relationship')
    """
    
    # GUID 패턴 검사
    guid_pattern = r'([A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12})'
    if re.search(guid_pattern, query_text):
        return 'guid'
    
    # 시간 관련 키워드 검사
    temporal_keywords = ['최근', '지난', '오늘', '어제', '주일', '달', '년', '분기']
    if any(keyword in query_text for keyword in temporal_keywords):
        return 'temporal'
    
    # 작성자 관련 키워드 검사
    author_keywords = ['작성', '담당', '엔지니어', 'engineer', '작성자']
    if any(keyword in query_text for keyword in author_keywords):
        return 'author'
    
    # 복합 자연어 패턴 검사
    complex_patterns = ['우선순위', '변경', '분석', '패턴', '관련된', '연결된']
    if any(pattern in query_text for pattern in complex_patterns):
        return 'complex'
    
    # 관계 탐색 패턴 검사
    relationship_patterns = ['관련된', '연결된', '의존', '영향', '원인', '결과']
    if any(pattern in query_text for pattern in relationship_patterns):
        return 'relationship'
    
    # 기본값: 키워드 검색
    return 'keyword'
```

### 2.3 성능 이력 관리 알고리즘

```python
def update_performance_history(engine, query_type, performance_metrics):
    """
    성능 이력 업데이트
    
    Args:
        engine: 엔진 이름
        query_type: 쿼리 타입
        performance_metrics: 성능 메트릭 (성공률, 신뢰도, 응답시간)
    """
    
    # 성능 이력 저장소에서 해당 엔진-쿼리타입 조합 찾기
    key = f"{engine}_{query_type}"
    
    if key not in performance_history:
        performance_history[key] = {
            'success_rates': [],
            'confidences': [],
            'response_times': [],
            'last_updated': datetime.now()
        }
    
    # 새로운 성능 데이터 추가
    history = performance_history[key]
    history['success_rates'].append(performance_metrics['success_rate'])
    history['confidences'].append(performance_metrics['confidence'])
    history['response_times'].append(performance_metrics['response_time'])
    history['last_updated'] = datetime.now()
    
    # 최대 100개 기록만 유지 (슬라이딩 윈도우)
    max_records = 100
    for metric in ['success_rates', 'confidences', 'response_times']:
        if len(history[metric]) > max_records:
            history[metric] = history[metric][-max_records:]
```

### 2.4 엔진 가중치 적응 알고리즘

```python
def adapt_engine_weights(performance_history, learning_rate=0.1):
    """
    엔진 가중치 적응적 업데이트
    
    Args:
        performance_history: 성능 이력 데이터
        learning_rate: 학습률 (α = 0.1)
    
    Returns:
        dict: 업데이트된 엔진 가중치
    """
    
    updated_weights = {}
    
    for engine_query_key, history in performance_history.items():
        engine, query_type = engine_query_key.split('_', 1)
        
        if len(history['confidences']) < 5:  # 최소 5개 기록 필요
            continue
        
        # 최근 성능 계산 (지수 이동 평균)
        recent_performance = calculate_exponential_moving_average(
            history['confidences'], alpha=0.3
        )
        
        # 전체 평균 성능 계산
        all_performances = []
        for other_key, other_history in performance_history.items():
            if len(other_history['confidences']) > 0:
                all_performances.extend(other_history['confidences'])
        
        overall_average = np.mean(all_performances) if all_performances else 0.5
        
        # 가중치 업데이트 (기존 가중치 + 학습률 × 성능 차이)
        current_weight = updated_weights.get(engine, 1.0)
        performance_diff = recent_performance - overall_average
        
        new_weight = current_weight + learning_rate * performance_diff
        new_weight = max(0.1, min(2.0, new_weight))  # 0.1 ~ 2.0 범위로 제한
        
        updated_weights[engine] = new_weight
    
    return updated_weights
```

## 3. 하이브리드 융합 알고리즘

### 3.1 기본 융합 (Basic Fusion)

```python
def basic_fusion(engine_results):
    """
    기본 융합 알고리즘
    
    Args:
        engine_results: 각 엔진의 결과 리스트
    
    Returns:
        dict: 융합된 결과
    """
    
    # 모든 결과를 하나의 리스트로 합치기
    all_results = []
    for engine, results in engine_results.items():
        for result in results:
            result['source_engine'] = engine
            all_results.append(result)
    
    # 신뢰도 기준으로 정렬
    all_results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    # 상위 10개 결과 반환
    return {
        'answer': generate_fused_answer(all_results[:10]),
        'confidence': calculate_fused_confidence(all_results[:10]),
        'result_count': len(all_results[:10]),
        'entities': extract_entities(all_results[:10]),
        'source': 'hybrid_basic_fusion'
    }
```

### 3.2 가중 융합 (Weighted Fusion)

```python
def weighted_fusion(engine_results, engine_weights):
    """
    가중 융합 알고리즘
    
    Args:
        engine_results: 각 엔진의 결과 리스트
        engine_weights: 엔진별 가중치
    
    Returns:
        dict: 가중 융합된 결과
    """
    
    # 가중치 적용된 결과 생성
    weighted_results = []
    
    for engine, results in engine_results.items():
        weight = engine_weights.get(engine, 1.0)
        
        for result in results:
            weighted_result = result.copy()
            weighted_result['confidence'] *= weight
            weighted_result['source_engine'] = engine
            weighted_result['original_confidence'] = result.get('confidence', 0)
            weighted_result['applied_weight'] = weight
            
            weighted_results.append(weighted_result)
    
    # 가중 신뢰도 기준으로 정렬
    weighted_results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    # 상위 10개 결과 반환
    return {
        'answer': generate_fused_answer(weighted_results[:10]),
        'confidence': calculate_fused_confidence(weighted_results[:10]),
        'result_count': len(weighted_results[:10]),
        'entities': extract_entities(weighted_results[:10]),
        'source': 'hybrid_weighted_fusion',
        'fusion_details': {
            'engine_weights': engine_weights,
            'fusion_method': 'weighted'
        }
    }
```

## 4. 성능 메트릭 계산 공식

### 4.1 성공률 (Success Rate)

```
Success Rate = (Number of Successful Queries) / (Total Number of Queries)

SR = Σ(I(success_i)) / N

여기서:
- I(success_i): i번째 쿼리의 성공 지시함수 (1 if success, 0 otherwise)
- N: 총 쿼리 수
```

### 4.2 평균 신뢰도 (Average Confidence)

```
Average Confidence = Σ(confidence_i) / N

AC = (1/N) × Σ(confidence_i)

여기서:
- confidence_i: i번째 쿼리의 신뢰도
- N: 총 쿼리 수
```

### 4.3 평균 응답 시간 (Average Response Time)

```
Average Response Time = Σ(response_time_i) / N

ART = (1/N) × Σ(response_time_i)

여기서:
- response_time_i: i번째 쿼리의 응답 시간 (초)
- N: 총 쿼리 수
```

### 4.4 정밀도 (Precision)

```
Precision = (True Positives) / (True Positives + False Positives)

P = TP / (TP + FP)

여기서:
- TP: 올바르게 검색된 관련 문서 수
- FP: 잘못 검색된 비관련 문서 수
```

### 4.5 재현율 (Recall)

```
Recall = (True Positives) / (True Positives + False Negatives)

R = TP / (TP + FN)

여기서:
- TP: 올바르게 검색된 관련 문서 수
- FN: 놓친 관련 문서 수
```

### 4.6 F1 점수

```
F1 Score = 2 × (Precision × Recall) / (Precision + Recall)

F1 = 2PR / (P + R)

여기서:
- P: 정밀도
- R: 재현율
```

## 5. 통계적 검증 공식

### 5.1 t-검정 (t-test)

```
t = (x̄₁ - x̄₂) / √(s²₁/n₁ + s²₂/n₂)

여기서:
- x̄₁, x̄₂: 두 그룹의 표본 평균
- s²₁, s²₂: 두 그룹의 표본 분산
- n₁, n₂: 두 그룹의 표본 크기
```

### 5.2 Cohen's d (효과 크기)

```
Cohen's d = (x̄₁ - x̄₂) / s_pooled

s_pooled = √((n₁-1)s²₁ + (n₂-1)s²₂) / (n₁ + n₂ - 2)

여기서:
- s_pooled: 합동 표준편차
- 효과 크기 해석: 0.2 (작음), 0.5 (중간), 0.8 (큼)
```

### 5.3 ANOVA F-통계량

```
F = MS_between / MS_within

MS_between = SS_between / df_between
MS_within = SS_within / df_within

여기서:
- MS: 평균 제곱 (Mean Square)
- SS: 제곱합 (Sum of Squares)
- df: 자유도 (degrees of freedom)
```

---

## 구현 참고사항

### 1. 수치 안정성
- 지수 함수 계산시 오버플로우 방지
- 분모가 0인 경우 처리
- NaN 값 처리

### 2. 성능 최적화
- 벡터화된 연산 사용 (NumPy)
- 캐싱을 통한 중복 계산 방지
- 배치 처리로 메모리 효율성 향상

### 3. 확장성 고려
- 모듈화된 설계로 새로운 엔진 추가 용이
- 설정 파일을 통한 하이퍼파라미터 조정
- 로깅을 통한 디버깅 및 모니터링
