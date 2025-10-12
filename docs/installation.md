# Installation Guide

## 시스템 요구사항

- **Python**: 3.11 이상
- **운영체제**: macOS, Linux, Windows
- **메모리**: 최소 4GB RAM (대용량 데이터 처리 시 8GB 권장)
- **저장공간**: 최소 1GB 여유 공간

## 설치 방법

### 1. Anaconda/Miniconda 사용 (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/sj31134/ContextualForget.git
cd ContextualForget

# 2. 가상환경 생성 및 활성화
conda create -n contextualforget python=3.11 -y
conda activate contextualforget

# 3. 패키지 설치
pip install -e ".[dev,demo]"

# 4. Git LFS 설정 (대용량 파일용)
git lfs install
git lfs track "*.ifc" "*.bcf" "*.bcfzip"
```

### 2. pip 사용

```bash
# 1. 저장소 클론
git clone https://github.com/sj31134/ContextualForget.git
cd ContextualForget

# 2. 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는
venv\Scripts\activate     # Windows

# 3. 패키지 설치
pip install -e ".[dev,demo]"
```

### 3. Docker 사용

```bash
# 1. 저장소 클론
git clone https://github.com/sj31134/ContextualForget.git
cd ContextualForget

# 2. Docker 이미지 빌드
docker build -t contextualforget:latest .

# 3. 컨테이너 실행
docker run -it contextualforget:latest ctxf --help
```

## 설치 확인

```bash
# CLI 명령어 테스트
ctxf --help

# Python 모듈 테스트
python -c "from contextualforget import AdvancedQueryEngine; print('✅ 설치 성공')"

# 테스트 실행
pytest tests/ -v
```

## 문제 해결

### Python 버전 오류
```bash
# Python 버전 확인
python --version

# 올바른 버전이 아닌 경우
conda install python=3.11
```

### 패키지 설치 오류
```bash
# pip 업그레이드
pip install --upgrade pip

# 캐시 클리어 후 재설치
pip cache purge
pip install -e ".[dev,demo]" --force-reinstall
```

### Git LFS 오류
```bash
# Git LFS 설치 확인
git lfs version

# LFS 파일 다운로드
git lfs pull
```

## 개발 환경 설정

### 개발 도구 설치
```bash
# 개발 의존성 설치
pip install -e ".[dev]"

# 코드 포맷팅 도구
pip install ruff black

# 테스트 도구
pip install pytest pytest-cov
```

### IDE 설정 (VS Code)
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black"
}
```

## 다음 단계

설치가 완료되면 [Quick Start Guide](quick_start.md)를 참조하여 첫 번째 파이프라인을 실행해보세요.
