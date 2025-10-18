# 📚 데이터셋 수집 가이드 (5-10번)

**작성일**: 2025년 10월 15일  
**대상**: Phase 2-3 추가 데이터셋  
**난이도**: 중급-고급

---

## 🎯 개요

Phase 1(1-4번)에서 기본 데이터를 수집했습니다. 이제 연구의 깊이와 신뢰성을 높이기 위한 추가 데이터를 수집합니다.

---

## ✅ **5️⃣ AI-Hub 건설 안전 데이터셋**

### 📋 **기본 정보**
- **신뢰도**: ⭐⭐⭐⭐ (공공기관)
- **비용**: 무료
- **소요시간**: 30분 (회원가입 5분 + 다운로드 25분)
- **난이도**: ⭐ 쉬움

### 🔗 **단계별 가이드**

#### **Step 1: 웹사이트 접속 및 회원가입**

1. **브라우저에서 접속**
   ```
   https://aihub.or.kr
   ```

2. **회원가입 (처음 방문 시)**
   - 우측 상단 "회원가입" 클릭
   - 이메일 또는 네이버/카카오 계정으로 간편 가입
   - 약관 동의 및 인증
   - ✅ 완료 시간: 5분

3. **로그인**
   - 이메일/비밀번호 입력

#### **Step 2: 데이터셋 검색**

1. **상단 검색창 클릭**
2. **검색어 입력** (중 하나 선택):
   ```
   "건설 안전"
   "건설 현장"
   "건축 안전"
   "BIM"
   ```

3. **추천 데이터셋**:
   - "건설 현장 안전 이미지 데이터"
   - "건설 작업자 안전관리 AI 데이터"
   - "건축물 안전진단 데이터"

#### **Step 3: 데이터 다운로드**

1. **데이터셋 상세 페이지 이동**
2. **"데이터 신청" 버튼 클릭**
3. **활용 목적 선택**: 
   ```
   ✅ 학술/연구
   ```
4. **"다운로드" 버튼 클릭**
   - 형식: JSON, CSV, 이미지
   - 크기: 보통 500MB-2GB

#### **Step 4: 프로젝트에 저장**

```bash
# 터미널에서 실행
cd /Users/junyonglee/ContextualForget

# 디렉토리 생성
mkdir -p data/external/aihub/construction_safety

# 다운로드 폴더에서 복사 (파일명은 실제 다운로드된 이름으로 변경)
cp ~/Downloads/construction_safety_*.zip data/external/aihub/construction_safety/

# 압축 해제
cd data/external/aihub/construction_safety/
unzip construction_safety_*.zip
```

#### **저장 구조**
```
data/external/aihub/
└── construction_safety/
    ├── metadata.json
    ├── images/
    │   ├── image_001.jpg
    │   └── ...
    └── annotations.csv
```

---

## ✅ **6️⃣ CSI MasterFormat (건설 사양서 분류)**

### 📋 **기본 정보**
- **신뢰도**: ⭐⭐⭐⭐⭐ (산업 표준)
- **비용**: 샘플 무료 / 전체 유료 ($150-500)
- **소요시간**: 15분 (샘플) / 2-3일 (구매)
- **난이도**: ⭐⭐ 보통

### 🔗 **방법 A: 무료 샘플 다운로드 (권장)**

#### **Step 1: 공식 사이트 접속**
```
https://www.csiresources.org/standards/masterformat
```

#### **Step 2: 샘플 다운로드**
1. "Free Resources" 또는 "Sample" 섹션 찾기
2. "Download Sample MasterFormat Divisions" 클릭
3. PDF 또는 Excel 파일 다운로드

#### **Step 3: 저장**
```bash
cd /Users/junyonglee/ContextualForget
mkdir -p data/external/csi_masterformat

cp ~/Downloads/MasterFormat_Sample*.pdf data/external/csi_masterformat/
```

### 🔗 **방법 B: 기존 프로젝트 데이터 활용 (가장 쉬움)**

**✅ 이미 프로젝트에 포함되어 있습니다!**

```bash
# 기존 MasterFormat 데이터 확인
cd /Users/junyonglee/ContextualForget

# 이미 다운로드된 파일
ls -lh data/raw/downloaded/IfcOpenShell-files_MasterFormat2016Edition.ifc
ls -lh data/raw/downloaded/IfcOpenShell-files_Omniclass_OCCS.ifc

# 이 파일들은 건설 분류 체계를 포함하고 있어 바로 사용 가능
```

**권장**: 방법 B를 사용하세요 (추가 다운로드 불필요)

---

## ✅ **7️⃣ KorQuAD + 건설 도메인 확장**

### 📋 **기본 정보**
- **신뢰도**: ⭐⭐⭐⭐⭐ (학술 검증)
- **비용**: 무료
- **소요시간**: 10분 (자동화됨)
- **난이도**: ⭐ 매우 쉬움

### 🔗 **단계별 가이드**

#### **Step 1: 자동 생성 (이미 완료!)**

```bash
# 이미 실행된 스크립트
python scripts/create_construction_qa.py
```

**결과:**
```
✅ 생성 완료: data/external/korquad/construction_qa_korquad_format.json
   - 문서 수: 5개
   - QA 쌍: 11개
```

#### **Step 2: (선택사항) 원본 KorQuAD 다운로드**

```bash
cd /Users/junyonglee/ContextualForget
mkdir -p data/external/korquad

# KorQuAD 1.0 다운로드
curl -L https://korquad.github.io/dataset/KorQuAD_v1.0_train.json \
  -o data/external/korquad/KorQuAD_v1.0_train.json

curl -L https://korquad.github.io/dataset/KorQuAD_v1.0_dev.json \
  -o data/external/korquad/KorQuAD_v1.0_dev.json
```

#### **저장 구조**
```
data/external/korquad/
├── construction_qa_korquad_format.json  (✅ 이미 생성됨)
├── KorQuAD_v1.0_train.json              (선택사항)
└── KorQuAD_v1.0_dev.json                (선택사항)
```

---

## ⚠️ **8️⃣ BIMPROVE Academic Dataset (학술 데이터)**

### 📋 **기본 정보**
- **신뢰도**: ⭐⭐⭐⭐⭐ (학술 검증)
- **비용**: 무료 (학술 목적)
- **소요시간**: 2-4주 (승인 대기)
- **난이도**: ⭐⭐⭐⭐ 어려움

### 🔗 **단계별 가이드**

#### **Step 1: 이메일 작성**

**수신자**: 
```
bimprove@tum.de (TU Munich)
또는 해당 연구실 교수님 이메일
```

**제목**:
```
Request for BIMPROVE Dataset for Academic Research
```

**본문 템플릿**:
```
Dear BIMPROVE Research Team,

My name is [귀하의 이름] from [귀하의 소속 대학/기관].

I am conducting research on "Contextual Forgetting Mechanisms for 
Graph-based Retrieval Augmented Generation in BIM Domain" and would 
like to request access to the BIMPROVE dataset for academic purposes.

Research Overview:
- Topic: Graph-RAG with contextual forgetting for BIM
- Institution: [귀하의 대학/기관]
- Advisor: [지도교수님 이름]
- Expected Publication: [학회명/저널명]

The dataset will be used solely for academic research and will be 
properly cited in all publications.

Could you please provide access to the dataset or guide me through 
the application process?

Thank you for your consideration.

Best regards,
[귀하의 이름]
[귀하의 이메일]
[귀하의 소속]
```

#### **Step 2: 승인 대기**
- ⏱️ 예상 시간: 2-4주
- 승인 시 다운로드 링크 제공

#### **Step 3: 다운로드 및 저장**
```bash
# 승인 후 제공된 링크로 다운로드
cd /Users/junyonglee/ContextualForget
mkdir -p data/external/bimprove

# 다운로드 (예시)
# 실제 링크는 승인 이메일에서 제공됨
```

#### **저장 구조**
```
data/external/bimprove/
├── project_01/
│   ├── model.ifc
│   └── issues.bcfzip
├── project_02/
└── README.md
```

---

## ⚠️ **9️⃣ Stanford CIFE Dataset**

### 📋 **기본 정보**
- **신뢰도**: ⭐⭐⭐⭐⭐ (학술 검증)
- **비용**: 무료 (학술 목적)
- **소요시간**: 2-4주
- **난이도**: ⭐⭐⭐⭐ 어려움

### 🔗 **단계별 가이드**

#### **Step 1: 웹사이트 접속**
```
https://cife.stanford.edu/
```

#### **Step 2: 데이터 요청**

1. **"Research" → "Data Sets" 메뉴 찾기**
2. **"Request Access" 폼 작성**
3. **연구 목적 및 소속 기관 명시**

#### **이메일 요청** (대안):
```
수신자: cife-data@stanford.edu

제목: Request for 4D BIM Dataset for Academic Research

본문: (BIMPROVE와 유사한 템플릿 사용)
```

---

## 📝 **10. 국토교통부 BIM 샘플 (한국 공공데이터)**

### 📋 **기본 정보**
- **신뢰도**: ⭐⭐⭐⭐⭐ (공공기관)
- **비용**: 무료
- **소요시간**: 1-2일
- **난이도**: ⭐⭐⭐ 중간

### 🔗 **방법 A: 공공데이터포털**

#### **Step 1: 포털 접속**
```
https://www.data.go.kr
```

#### **Step 2: 검색**
```
검색어: "BIM" 또는 "건축정보모델" 또는 "IFC"
```

#### **Step 3: 데이터셋 찾기**
- "건축물 BIM 데이터"
- "공공건축물 3차원 모델"
- "스마트건설 BIM 데이터"

#### **Step 4: 다운로드**
1. 데이터셋 상세 페이지 이동
2. "오픈API" 또는 "파일데이터" 탭
3. 다운로드 버튼 클릭

```bash
# 저장
cd /Users/junyonglee/ContextualForget
mkdir -p data/external/public_korea/molit

cp ~/Downloads/bim_public_*.ifc data/external/public_korea/molit/
```

### 🔗 **방법 B: 국토교통부 직접 문의**

#### **Step 1: 웹사이트 접속**
```
https://www.molit.go.kr
```

#### **Step 2: 스마트건설기술 페이지**
- 메뉴: 정책자료 → 스마트건설
- "BIM 가이드라인" 검색

#### **Step 3: 샘플 파일 다운로드**
- 보통 PDF 가이드라인에 샘플 IFC 파일 포함
- 또는 별도 다운로드 링크 제공

---

## 📂 **최종 프로젝트 구조**

```
/Users/junyonglee/ContextualForget/
└── data/
    └── external/
        ├── aihub/
        │   └── construction_safety/
        │       ├── metadata.json
        │       └── images/
        ├── csi_masterformat/
        │   └── (샘플 파일 또는 기존 IFC 활용)
        ├── korquad/
        │   └── construction_qa_korquad_format.json  ✅ 완료
        ├── bimprove/
        │   └── (승인 후 저장)
        ├── stanford_cife/
        │   └── (승인 후 저장)
        └── public_korea/
            └── molit/
                └── (다운로드 후 저장)
```

---

## ✅ **완료 체크리스트**

### **즉시 가능 (무료, 빠름)**
- [x] 7️⃣ KorQuAD 건설 도메인 QA → ✅ **완료!**
- [ ] 5️⃣ AI-Hub 건설 안전 데이터
- [ ] 6️⃣ CSI MasterFormat (기존 데이터 활용)
- [ ] 10. 국토교통부 BIM 샘플

### **중기 (승인 필요)**
- [ ] 8️⃣ BIMPROVE Dataset (이메일 발송 → 2-4주 대기)
- [ ] 9️⃣ Stanford CIFE (이메일 발송 → 2-4주 대기)

---

## 🚀 **다음 단계**

### **지금 바로 할 수 있는 작업**

1. **AI-Hub 데이터 수집 (30분)**
   ```bash
   # 1. https://aihub.or.kr 접속
   # 2. "건설 안전" 검색
   # 3. 다운로드
   # 4. data/external/aihub/에 저장
   ```

2. **KorQuAD 활용 (이미 완료)**
   ```bash
   # ✅ 이미 생성됨
   ls data/external/korquad/construction_qa_korquad_format.json
   ```

3. **기존 MasterFormat 활용 (즉시 가능)**
   ```bash
   # ✅ 이미 있음
   ls data/raw/downloaded/IfcOpenShell-files_MasterFormat2016Edition.ifc
   ```

### **병행 작업 (이메일 발송)**

4. **학술 데이터 신청 이메일 작성**
   - BIMPROVE → bimprove@tum.de
   - Stanford CIFE → cife-data@stanford.edu

---

## 💡 **팁 및 주의사항**

### **데이터 저장 규칙**
1. ✅ 항상 `data/external/` 아래에 저장
2. ✅ 소스별 디렉토리 분리
3. ✅ 원본 파일명 유지 (추적 가능성)
4. ✅ README.txt 함께 저장 (출처, 날짜, 라이선스)

### **라이선스 확인**
- 각 데이터셋의 이용약관 확인
- 학술 연구 목적 명시
- 출처 표기 필수

### **우선순위**
1. **즉시**: KorQuAD (✅ 완료), AI-Hub
2. **1주일**: 국토교통부 BIM
3. **1개월**: BIMPROVE, Stanford (승인 대기)

---

**가이드 작성**: 2025-10-15  
**업데이트**: 필요시 지속 업데이트  
**문의**: 프로젝트 이슈 또는 데이터 제공 기관

