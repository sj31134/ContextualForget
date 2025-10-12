# 최종 데이터 전략 및 논문 방향

**작성일**: 2025년 10월 9일  
**전략**: Option 3 + Option 1 하이브리드  
**목표**: 합성 데이터 방법론 논문 + 실제 데이터 보강

---

## 📊 **현재 상태 Summary**

### **데이터 현황**

| 항목 | 수량 | 신뢰도 | 상태 |
|------|------|--------|------|
| **IFC (buildingSMART)** | 14개 | ✅ HIGH | 신뢰 가능 |
| **IFC (IfcOpenShell)** | 100개 | 🟡 MEDIUM | 테스트용 |
| **IFC (기타)** | 9개 | 🟡 MEDIUM | 추가 수집 |
| **BCF (실제)** | 2개 | ✅ HIGH | 매우 부족 |
| **BCF (합성)** | 60개 | ⚠️ LOW→MEDIUM | 투명성 확보 필요 |

### **신뢰도 점수**

```
데이터 신뢰도: 31.7/100 🔴
투명성 점수: 90/100 ✅
```

**문제**: 합성 BCF 비율이 97% (60/62) → 논문 Reject 위험

**해결**: 
1. ✅ 투명성 확보 (90/100) - 완료
2. 🔄 실제 데이터 추가 수집 - 진행 중
3. ⏭️ 논문 재구성 - 다음 단계

---

## 🎯 **최종 전략: 3단계 접근**

### **Phase 1: 데이터 보강 (Week 1-2)** ⭐ 현재

#### **목표**: 신뢰 데이터 비율 향상

**실행 항목**:

1. ✅ **출처 증명 시스템 구축**
   - `data/provenance/DATA_PROVENANCE.md` 생성 완료
   - 모든 파일의 라이선스, URL, 출처 문서화
   - BibTeX 인용 형식 제공

2. ✅ **합성 데이터 투명성 확보**
   - `data/synthetic/GENERATION_METHODOLOGY.md` 생성 완료
   - 생성 로직 100% 공개
   - 재현성 확보 (시드 42 고정)
   - 한계 명시

3. 🔄 **추가 실제 데이터 수집** (진행 중)
   - ✅ IDS 프로젝트: 5개 추가
   - 🔄 Academic 데이터셋 신청:
     - BIMPROVE: research@bimprove.eu
     - TU Delft: https://data.4tu.nl/
     - Stanford: https://purl.stanford.edu/
   - 🔄 공공 데이터:
     - 국토교통부 스마트건설
     - 공공데이터포털

4. ⏭️ **전문가 검증**
   - BIM 전문가 2-3명 섭외
   - 합성 BCF 이슈 현실성 평가
   - Inter-rater reliability 측정

**예상 결과**:
- 신뢰도: 31.7 → **55-65/100** 🟡
- 실제 BCF: 2개 → **5-10개** (목표)
- 합성/실제 비율: 97% → **85-90%**

---

### **Phase 2: 논문 재구성 (Week 3-4)** 📝

#### **전략**: "Methodology + Demonstration" 논문으로 재포지셔닝

**새로운 타이틀**:
```
"A Transparent Framework for Synthetic BIM Collaboration Data Generation 
 and Graph-RAG Evaluation in Digital Twins"
```

**핵심 Contribution 재정의**:

1. **Synthetic Data Generation Framework** (30%)
   - Template-based BCF generation methodology
   - Open-source implementation
   - Reproducibility guarantee (fixed seed)
   - Validation protocol

2. **Graph-RAG Architecture** (30%)
   - IFC-BCF integrated graph model
   - Adaptive forgetting mechanisms
   - LLM-enhanced natural language query

3. **Evaluation Framework** (20%)
   - Metrics: Accuracy, Attribution, Consistency
   - Baseline comparisons (Keyword, Vector, Document RAG)
   - Proof-of-concept experiments

4. **Transparency & Reproducibility** (20%)
   - Full methodology disclosure
   - Data provenance documentation
   - Limitation analysis
   - Future work roadmap

**Target Venue 재조정**:

| Venue Type | Conference/Journal | Accept 확률 | 전략 |
|------------|-------------------|-------------|------|
| **Dataset Track** | NeurIPS Datasets, ICLR Workshop | 60% | 데이터 생성 방법론 강조 |
| **Tool/Demo** | ICSE Demo, ASE Tool Demo | 70% | 구현 및 사용성 |
| **Workshop** | ICSE Workshops, MSR Workshop | 75% | 초기 연구 결과 |
| **Main Conference** | ASE, ICSME | 40% | 보수적 전략 |
| **arxiv** | arxiv.org | 100% | 커뮤니티 피드백 |

**권장 전략**: Workshop (ICSE 2025) + arxiv → 실제 데이터 확보 후 Main Conference (ASE 2025)

---

### **Phase 3: 실험 및 검증 (Week 5-6)** 🔬

#### **실험 설계 조정**

**기존 계획**:
- Large-scale evaluation (123 IFC + 322 BCF)
- 통계적 유의성 검증
- Top-tier 학회 목표

**조정된 계획**:
- **Proof-of-concept** evaluation
- buildingSMART 신뢰 데이터 (14-20 IFC)
- 합성 데이터는 **보조적** 사용
- Limitation 명시

**실험 구성**:

1. **RQ1: Graph-RAG vs Baselines** (변경 없음)
   - 데이터: buildingSMART 14개 + 엄선된 IfcOpenShell 10개
   - 메트릭: Accuracy, F1, Attribution P/R
   - 결론: "Promising results on standard examples"

2. **RQ2: Forgetting Mechanisms** (조정)
   - 데이터: 합성 BCF (명시적 표기)
   - 시간 범위: 90일
   - 결론: "Synthetic data suggests potential benefits, validation needed"

3. **RQ3: Change Impact Tracking** (조정)
   - 데이터: IFC-BCF 링크
   - 규모: 소규모 demonstration
   - 결론: "Framework successfully tracks multi-hop changes"

**Limitation 섹션 (필수)**:

```markdown
### Limitations

1. **Data Availability**: Our evaluation primarily uses publicly available 
   buildingSMART examples (n=14) and synthetic BCF issues (n=60). While 
   these demonstrate feasibility, they may not fully represent the complexity 
   of real-world construction projects.

2. **Synthetic Data**: BCF collaboration issues were generated using 
   template-based approach with fixed seed (42) for reproducibility. 
   We document the methodology transparently in [GENERATION_METHODOLOGY.md]. 
   However, synthetic data has inherent limitations in capturing nuanced 
   human collaboration patterns.

3. **Generalizability**: Our findings should be validated with larger-scale 
   real construction project data. We are actively pursuing academic datasets 
   (BIMPROVE, TU Delft) to extend this work.

4. **Expert Validation**: Synthetic BCF issues have been reviewed by [N] 
   BIM domain experts with [X] years of experience (inter-rater agreement: [Y]). 
   While validated for realism, they remain approximations.
```

---

## 📋 **Action Items (우선순위)**

### **Critical (즉시 실행)**

- [x] 데이터 출처 증명 문서 생성
- [x] 합성 데이터 방법론 문서화
- [x] 재현성 확보 (시드 고정)
- [ ] 논문 타이틀 및 Contribution 재정의
- [ ] Limitation 섹션 초안 작성

### **High (Week 1-2)**

- [ ] BIM 전문가 2-3명 섭외 및 검증 의뢰
- [ ] Academic 데이터셋 신청 이메일 발송
- [ ] 공공 데이터 탐색 및 수집
- [ ] Gold Standard QA 50개 생성 (전문가 협업)
- [ ] 논문 구조 재설계

### **Medium (Week 3-4)**

- [ ] 신뢰 데이터만으로 실험 재설계
- [ ] Baseline 구현 (BM25, Vector RAG)
- [ ] 평가 메트릭 구현
- [ ] 초안 작성 (Workshop paper)

### **Low (병행)**

- [ ] arxiv preprint 준비
- [ ] GitHub repository 정리
- [ ] Documentation 업데이트

---

## 🎯 **성공 기준 재정의**

### **최소 목표 (Must Have)**

✅ 달성 가능:
- buildingSMART 신뢰 데이터 14-20개
- 투명한 합성 데이터 방법론
- Proof-of-concept 실험
- Workshop paper acceptance

### **이상적 목표 (Should Have)**

🔄 노력 중:
- 실제 BCF 5-10개 추가
- 전문가 검증 완료
- Academic 데이터셋 1-2개 확보
- Main conference submission

### **추가 목표 (Nice to Have)**

⏭️ 차기:
- BIMPROVE 실제 프로젝트 데이터
- 대규모 실험 (Main conference)
- Top-tier journal (Automation in Construction)

---

## 📊 **예상 Timeline**

```
Week 1-2: 데이터 보강 + 전문가 검증
├─ 신뢰도: 31.7 → 55-65/100
└─ 논문 방향 확정

Week 3-4: 논문 재구성 + 실험 설계
├─ Workshop paper 구조
└─ Proof-of-concept 실험

Week 5-6: 실험 수행 + 초안 작성
├─ RQ1, RQ2, RQ3 실험
└─ Workshop paper 초안

Week 7-8: 리뷰 + 투고
├─ 내부 리뷰
└─ ICSE Workshop 투고

Week 9-12: 피드백 + 확장
├─ arxiv 공개
├─ 실제 데이터 확보
└─ Main conference 확장
```

---

## 🎓 **학술적 정직성 (Academic Integrity)**

### **우리의 원칙**

1. **완전한 투명성**
   - 합성 데이터 명시
   - 방법론 100% 공개
   - 한계 솔직히 서술

2. **재현성 보장**
   - 고정된 시드 (42)
   - 오픈소스 코드
   - 상세한 문서화

3. **검증 노력**
   - 전문가 리뷰
   - 통계적 분석
   - 실제 데이터 추구

4. **기여 명확화**
   - 방법론 기여 강조
   - 데이터 한계 인정
   - 미래 연구 방향 제시

### **리뷰어에게 전달할 메시지**

> "We acknowledge the limitations of synthetic data. However, we believe 
> our transparent methodology, reproducible framework, and proof-of-concept 
> results contribute to the BIM and Graph-RAG research community. 
> We are actively pursuing real-world data to validate and extend our findings."

---

## ✅ **결론**

### **현실적 평가**

**현재 데이터의 신뢰도: 31.7/100 🔴**

이것은 사실입니다. 합성 데이터가 97%를 차지하는 것은 **Top-tier Main Conference에는 부적합**합니다.

### **우리의 전략**

**하지만** 우리는:
1. ✅ 투명성을 확보했습니다 (90/100)
2. ✅ 방법론을 문서화했습니다
3. ✅ 재현성을 보장했습니다
4. 🔄 실제 데이터를 계속 수집하고 있습니다
5. ⏭️ 논문을 재구성할 준비가 되었습니다

### **성공 경로**

**Short-term (6-8주)**:
- Workshop paper + arxiv
- Proof-of-concept demonstration
- 커뮤니티 피드백 수집

**Long-term (3-6개월)**:
- 실제 데이터 확보 (BIMPROVE, 산학협력)
- 대규모 실험
- Main conference (ASE, ICSME)

### **핵심 메시지**

```
우리는 완벽한 데이터를 가진 척하지 않습니다.
대신, 투명하고 재현 가능한 방법론을 제시합니다.
그리고 계속해서 개선하고 있습니다.
```

이것이 **학술적으로 정직하고 실현 가능한 전략**입니다.

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-10-09 23:30  
**다음 검토**: 실제 데이터 확보 시

