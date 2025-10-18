# 학술 데이터셋 액션 플랜

**작성일**: 2025년 10월 15일  
**상태**: 리서치 완료, 문의 준비 완료  
**목표**: 실제 BCF 데이터 확보로 연구 신뢰도 향상

---

## 📊 **현재 상황 요약**

### **리서치 결과**
```
✅ 3개 데이터셋 적합성 분석 완료
✅ 다운로드 시도 완료 (직접 다운로드 불가)
✅ 문의 템플릿 생성 완료
✅ 검증 스크립트 준비 완료
```

### **우선순위 데이터셋**
```
1순위: Schependomlaan (TU Eindhoven) - 실제 BCF 2.0 파일 포함
2순위: SLABIM (HKUST) - 시간적 변화 추적 우수
3순위: DURAARK (EU FP7) - IFC 모델 다양성
```

---

## 🎯 **즉시 실행 가능한 액션**

### **1. Schependomlaan 데이터셋 (1순위)**

**접근 방법**:
```
기관: TU Eindhoven
부서: Built Environment
웹사이트: https://www.tue.nl/
데이터 포털: https://data.4tu.nl/
```

**문의 템플릿** (이미 생성됨):
```
파일: data/external/academic/contact_templates/schependomlaan_contact_template.txt
수신자: TU Eindhoven Built Environment 부서
예상 응답: 1-2주
```

**문의 내용**:
- 연구 주제: "Contextual Forgetting in Graph-RAG for BIM Domain"
- 필요 데이터: Schependomlaan 프로젝트의 BCF 2.0 파일과 주차별 BIM 모델
- 활용 목적: 학술 연구 및 논문 발표
- 라이선스: 학술 연구 목적

### **2. SLABIM 데이터셋 (2순위)**

**접근 방법**:
```
기관: Hong Kong University of Science and Technology (HKUST)
부서: Visual Graphics and Design Lab
웹사이트: https://www.hkust.edu.hk/
GitHub: https://github.com/hkust-vgd/slabim (접근 불가)
```

**문의 템플릿** (이미 생성됨):
```
파일: data/external/academic/contact_templates/slabim_contact_template.txt
수신자: HKUST VGD Lab
예상 응답: 1-2주
```

**문의 내용**:
- 연구 주제: Graph-RAG with contextual forgetting for BIM
- 필요 데이터: SLAM 스캔 데이터와 BIM 모델의 시간적 변화 데이터
- 활용 목적: 시간적 망각 메커니즘 테스트
- 라이선스: 학술 연구 목적

### **3. DURAARK 데이터셋 (3순위)**

**접근 방법**:
```
기관: European Union FP7 Project
웹사이트: http://duraark.eu/ (접근 가능)
GitHub: https://github.com/DURAARK
```

**문의 템플릿** (이미 생성됨):
```
파일: data/external/academic/contact_templates/duraark_contact_template.txt
수신자: DURAARK 프로젝트 팀
예상 응답: 1-2주
```

**문의 내용**:
- 연구 주제: BIM 도메인 Graph-RAG 연구
- 필요 데이터: Medical Clinic 프로젝트의 다분야 IFC 모델
- 활용 목적: IFC 모델 간 충돌 검출 및 BCF 변환
- 라이선스: EU 프로젝트 - 학술 연구 목적

---

## 📧 **문의 실행 계획**

### **오늘 (즉시 실행)**
```
1. 문의 템플릿 확인 및 수정
   - 개인 정보 입력 (이름, 소속, 이메일)
   - 연구 주제 구체화
   - 예상 완료 시한 명시

2. 이메일 발송
   - Schependomlaan (1순위) - TU Eindhoven
   - SLABIM (2순위) - HKUST
   - DURAARK (3순위) - DURAARK 프로젝트
```

### **1-2주 후 (응답 대기)**
```
1. 응답 확인 및 후속 조치
2. 데이터 접근 방법 안내 수신
3. 데이터 다운로드 및 저장
4. 검증 스크립트 실행
```

### **2-3주 후 (데이터 확보 시)**
```
1. 데이터 검증 및 분석
2. BCF 변환 스크립트 실행
3. 기존 프로젝트와 통합
4. 신뢰도 재평가
```

---

## 🔧 **준비된 도구 및 스크립트**

### **문의 템플릿**
```
위치: data/external/academic/contact_templates/
파일:
- schependomlaan_contact_template.txt
- slabim_contact_template.txt
- duraark_contact_template.txt
```

### **검증 스크립트**
```
파일: scripts/validate_academic_data.py
용도: 다운로드된 데이터 무결성 검증
실행: python scripts/validate_academic_data.py
```

### **BCF 변환 스크립트** (준비 중)
```
파일: scripts/convert_academic_to_bcf.py
용도: 학술 데이터를 BCF 형식으로 변환
상태: 개발 준비 완료
```

### **통합 스크립트** (준비 중)
```
파일: scripts/integrate_academic_data.py
용도: 학술 데이터를 기존 프로젝트와 통합
상태: 개발 준비 완료
```

---

## 📈 **예상 개선 효과**

### **현재 상태**
```
실제 BCF 파일: 2개 (3%)
합성 BCF 파일: 55개 (97%)
신뢰도 점수: 31.7/100
```

### **학술 데이터 확보 후**
```
실제 BCF 파일: 12-22개 (15-20%)
합성 BCF 파일: 55개 (80-85%)
신뢰도 점수: 50-60/100
개선율: +58-89%
```

### **연구 신뢰도 향상**
```
논문 거부 위험: 높음 → 낮음
실제 데이터 비율: 3% → 15-20%
학술적 정당성: 부족 → 충분
```

---

## 🎯 **성공 기준**

### **최소 목표 (Must Have)**
```
✅ Schependomlaan BCF 파일 1개 이상 확보
✅ 실제 BCF 파일 5개 이상 확보
✅ 신뢰도 점수 45/100 이상 달성
```

### **이상적 목표 (Should Have)**
```
✅ 3개 데이터셋 모두 확보
✅ 실제 BCF 파일 10개 이상 확보
✅ 신뢰도 점수 55/100 이상 달성
✅ 시간적 변화 데이터 확보
```

### **추가 목표 (Nice to Have)**
```
✅ 대규모 실제 데이터 확보
✅ 국제 학술 협력 기회
✅ 데이터셋 공동 발표 가능성
```

---

## 📋 **체크리스트**

### **문의 발송 전**
- [ ] 문의 템플릿 개인 정보 입력
- [ ] 연구 주제 구체화
- [ ] 예상 완료 시한 명시
- [ ] 이메일 주소 확인

### **문의 발송**
- [ ] Schependomlaan (1순위) 발송
- [ ] SLABIM (2순위) 발송
- [ ] DURAARK (3순위) 발송
- [ ] 발송 확인 이메일 저장

### **응답 대기 중**
- [ ] 일일 이메일 확인
- [ ] 응답 기록 및 관리
- [ ] 후속 조치 계획 수립

### **데이터 수신 후**
- [ ] 데이터 다운로드 및 저장
- [ ] 검증 스크립트 실행
- [ ] BCF 변환 작업
- [ ] 기존 프로젝트 통합
- [ ] 신뢰도 재평가

---

## 💡 **성공 팁**

### **문의 이메일 작성**
```
1. 명확한 연구 목적 제시
2. 학술적 정당성 강조
3. 데이터 활용 계획 구체화
4. 출처 표기 약속
5. 협력 의지 표현
```

### **응답 관리**
```
1. 정중한 후속 문의
2. 연구 진행 상황 공유
3. 상호 이익 제시
4. 장기적 협력 가능성 언급
```

### **데이터 활용**
```
1. 라이선스 조건 준수
2. 출처 정확히 표기
3. 재배포 금지 준수
4. 연구 결과 공유
```

---

## 🚀 **즉시 실행 명령어**

### **문의 템플릿 확인**
```bash
conda activate contextualforget
cat data/external/academic/contact_templates/schependomlaan_contact_template.txt
```

### **문의 템플릿 수정**
```bash
# 개인 정보 입력 후 이메일 발송
nano data/external/academic/contact_templates/schependomlaan_contact_template.txt
```

### **검증 스크립트 테스트**
```bash
python scripts/validate_academic_data.py
```

---

**지금 바로 문의 템플릿을 확인하고 이메일을 발송하세요!** 📧

1-2주 내에 응답을 받으면 데이터 확보가 가능하고, 연구 신뢰도가 대폭 향상될 것입니다! 🎯
