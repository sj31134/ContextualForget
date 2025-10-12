# ContextualForget Examples

이 폴더는 ContextualForget 시스템의 사용 예제들을 포함합니다.

## 파일 목록

### 📓 Jupyter Notebooks
- **`demo.ipynb`** - 전체 시스템 기능을 시연하는 대화형 노트북
  - 환경 설정 및 데이터 로드
  - 기본 및 고급 쿼리
  - 망각 정책 시연
  - 시각화 및 성능 분석

### 🐍 Python Scripts
- **`quick_start.py`** - 빠른 시작을 위한 간단한 스크립트
  - 기본 쿼리 실행
  - 키워드 및 작성자 검색
  - 그래프 통계 출력
  - 망각 정책 테스트

## 사용 방법

### 1. 환경 설정
```bash
# 가상환경 활성화
conda activate contextualforget

# 프로젝트 디렉토리로 이동
cd /path/to/ContextualForget
```

### 2. 데이터 준비
```bash
# 샘플 데이터 생성 및 파이프라인 실행
make all
```

### 3. 예제 실행

#### Jupyter Notebook
```bash
# Jupyter Lab 또는 Jupyter Notebook 실행
jupyter lab examples/demo.ipynb
# 또는
jupyter notebook examples/demo.ipynb
```

#### Python Script
```bash
# 빠른 시작 스크립트 실행
python examples/quick_start.py
```

## 예제에서 다루는 기능들

### 🔍 쿼리 기능
- **기본 쿼리**: GUID 기반 BCF 토픽 검색
- **키워드 검색**: 텍스트 내용 기반 검색
- **작성자 검색**: 특정 작성자의 이벤트 검색
- **시간 범위 검색**: 특정 기간의 이벤트 검색
- **복합 쿼리**: 여러 조건을 조합한 검색

### 🧠 망각 정책
- **TTL 정책**: 시간 기반 망각
- **가중치 감쇠**: 사용 빈도와 중요도 기반 망각
- **복합 정책**: 여러 정책을 조합한 망각

### 📊 시각화
- **그래프 시각화**: 전체 그래프 구조 표시
- **서브그래프**: 특정 GUID 주변의 연결 표시
- **타임라인**: 이벤트 시간 순서 표시
- **망각 곡선**: TTL에 따른 망각 패턴 표시

### ⚡ 성능 최적화
- **배치 쿼리**: 여러 GUID 동시 검색
- **성능 프로파일링**: 실행 시간 측정
- **메모리 최적화**: 그래프 압축 및 캐싱

## 추가 리소스

- **문서**: [docs/tutorial.md](../docs/tutorial.md)
- **API 참조**: [docs/api_reference.md](../docs/api_reference.md)
- **CLI 도움말**: `ctxf --help`
- **GitHub 저장소**: [https://github.com/sj31134/ContextualForget](https://github.com/sj31134/ContextualForget)

## 문제 해결

### 일반적인 문제들

1. **모듈을 찾을 수 없음**
   ```bash
   # 프로젝트 루트에서 실행
   pip install -e .
   ```

2. **그래프 파일이 없음**
   ```bash
   # 데이터 생성 및 파이프라인 실행
   make all
   ```

3. **Jupyter에서 모듈 import 오류**
   ```python
   # 노트북 첫 번째 셀에 추가
   import sys
   sys.path.append('..')
   ```

4. **시각화가 표시되지 않음**
   ```bash
   # matplotlib 백엔드 설정
   export MPLBACKEND=Agg
   ```

## 기여하기

새로운 예제를 추가하고 싶으시다면:

1. 이 폴더에 새로운 파일 추가
2. 이 README.md에 설명 추가
3. Pull Request 제출

더 많은 예제와 사용 사례를 환영합니다!
