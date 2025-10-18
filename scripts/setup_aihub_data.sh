#!/bin/bash
# AI-Hub 데이터셋 설정 스크립트
# 작성일: 2025-10-15
# 용도: AI-Hub에서 다운로드한 데이터를 프로젝트에 통합

set -e  # 오류 발생 시 중단

PROJECT_ROOT="/Users/junyonglee/ContextualForget"
AIHUB_DIR="$PROJECT_ROOT/data/external/aihub"

echo "🚀 AI-Hub 데이터셋 설정 시작..."
echo ""

# 1. 디렉토리 생성
echo "📁 디렉토리 생성 중..."
mkdir -p "$AIHUB_DIR/daily_life_spaces"
mkdir -p "$AIHUB_DIR/construction_safety"
mkdir -p "$AIHUB_DIR/indoor_3d"
mkdir -p "$PROJECT_ROOT/data/processed/aihub_spaces"
mkdir -p "$PROJECT_ROOT/data/processed/aihub_bcf"

echo "✅ 디렉토리 생성 완료"
echo ""

# 2. 다운로드 파일 확인
echo "🔍 다운로드 파일 확인 중..."
DOWNLOAD_DIR="$HOME/Downloads"

# 일상생활 공간 데이터 확인
DAILY_LIFE_FILES=$(find "$DOWNLOAD_DIR" -name "*일상생활*" -o -name "*daily_life*" -o -name "*공간*" 2>/dev/null | wc -l)
if [ "$DAILY_LIFE_FILES" -gt 0 ]; then
    echo "✅ 일상생활 공간 데이터 발견: $DAILY_LIFE_FILES 파일"
else
    echo "⚠️  일상생활 공간 데이터 미발견"
    echo "   → https://aihub.or.kr 에서 '일상생활 작업 및 명령 수행 데이터(공간)' 다운로드 필요"
fi

# 건설 안전 데이터 확인
SAFETY_FILES=$(find "$DOWNLOAD_DIR" -name "*건설*안전*" -o -name "*construction*safety*" 2>/dev/null | wc -l)
if [ "$SAFETY_FILES" -gt 0 ]; then
    echo "✅ 건설 안전 데이터 발견: $SAFETY_FILES 파일"
else
    echo "⚠️  건설 안전 데이터 미발견"
    echo "   → https://aihub.or.kr 에서 '건설 현장 안전 이미지 데이터' 다운로드 필요"
fi

echo ""

# 3. 파일 복사 (사용자 확인 필요)
echo "📦 다운로드 파일을 수동으로 복사하세요:"
echo ""
echo "일상생활 공간 데이터:"
echo "  cp ~/Downloads/[파일명].zip $AIHUB_DIR/daily_life_spaces/"
echo ""
echo "건설 안전 데이터:"
echo "  cp ~/Downloads/[파일명].zip $AIHUB_DIR/construction_safety/"
echo ""

read -p "파일 복사를 완료했습니까? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⏸️  스크립트 중단. 파일 복사 후 다시 실행하세요."
    exit 1
fi

# 4. 압축 해제
echo "📂 압축 해제 중..."

# 일상생활 공간 데이터 압축 해제
if [ -n "$(ls -A $AIHUB_DIR/daily_life_spaces/*.zip 2>/dev/null)" ]; then
    echo "  → 일상생활 공간 데이터 압축 해제..."
    cd "$AIHUB_DIR/daily_life_spaces"
    for zip_file in *.zip; do
        if [ -f "$zip_file" ]; then
            unzip -o "$zip_file"
            echo "    ✅ $zip_file 해제 완료"
        fi
    done
    cd "$PROJECT_ROOT"
fi

# 건설 안전 데이터 압축 해제
if [ -n "$(ls -A $AIHUB_DIR/construction_safety/*.zip 2>/dev/null)" ]; then
    echo "  → 건설 안전 데이터 압축 해제..."
    cd "$AIHUB_DIR/construction_safety"
    for zip_file in *.zip; do
        if [ -f "$zip_file" ]; then
            unzip -o "$zip_file"
            echo "    ✅ $zip_file 해제 완료"
        fi
    done
    cd "$PROJECT_ROOT"
fi

echo "✅ 압축 해제 완료"
echo ""

# 5. 데이터 통계
echo "📊 데이터 통계:"
echo ""

# FBX 파일 수
FBX_COUNT=$(find "$AIHUB_DIR/daily_life_spaces" -name "*.fbx" 2>/dev/null | wc -l)
echo "  FBX 파일: $FBX_COUNT 개"

# JSON 파일 수
JSON_COUNT=$(find "$AIHUB_DIR/daily_life_spaces" -name "*.json" 2>/dev/null | wc -l)
echo "  JSON 파일: $JSON_COUNT 개"

# 이미지 파일 수
IMAGE_COUNT=$(find "$AIHUB_DIR/construction_safety" -name "*.jpg" -o -name "*.png" 2>/dev/null | wc -l)
echo "  이미지 파일: $IMAGE_COUNT 개"

# 총 크기
TOTAL_SIZE=$(du -sh "$AIHUB_DIR" 2>/dev/null | cut -f1)
echo "  총 크기: $TOTAL_SIZE"

echo ""

# 6. README 생성
echo "📝 README 파일 생성 중..."

cat > "$AIHUB_DIR/README.md" << 'EOF'
# AI-Hub 데이터셋

**다운로드 날짜**: $(date +%Y-%m-%d)
**출처**: AI-Hub (https://aihub.or.kr)

## 데이터셋 구성

### 1. 일상생활 작업 및 명령 수행 데이터(공간)
- **경로**: `daily_life_spaces/`
- **용도**: IFC 변환, BCF 이슈 생성
- **라이선스**: AI-Hub 이용약관 준수 (학술 연구 목적)

### 2. 건설 현장 안전 이미지 데이터
- **경로**: `construction_safety/`
- **용도**: BCF 이슈 매핑, 안전 QA 생성
- **라이선스**: AI-Hub 이용약관 준수 (학술 연구 목적)

## 다음 단계

1. FBX → IFC 변환:
   ```bash
   python scripts/convert_aihub_to_ifc.py
   ```

2. BCF 이슈 생성:
   ```bash
   python scripts/generate_bcf_from_aihub.py
   ```

3. 데이터 통합:
   ```bash
   python scripts/integrate_aihub_data.py
   ```

## 인용 (Citation)

논문에서 이 데이터를 사용할 경우:

```
한국지능정보사회진흥원 (NIA). (2024). 
일상생활 작업 및 명령 수행 데이터(공간) / 건설 현장 안전 이미지 데이터.
AI-Hub. https://aihub.or.kr
```

## 주의사항

- ✅ 학술 연구 목적으로만 사용
- ✅ 출처 표기 필수
- ✅ 상업적 이용 금지 (별도 승인 필요)
- ✅ 데이터 재배포 금지
EOF

echo "✅ README 생성 완료"
echo ""

# 7. 다음 단계 안내
echo "🎉 AI-Hub 데이터셋 설정 완료!"
echo ""
echo "📋 다음 단계:"
echo ""
echo "1. 데이터 검증:"
echo "   python scripts/validate_aihub_data.py"
echo ""
echo "2. IFC 변환 (Blender 필요):"
echo "   python scripts/convert_aihub_to_ifc.py"
echo ""
echo "3. BCF 생성:"
echo "   python scripts/generate_bcf_from_aihub.py"
echo ""
echo "4. 전체 파이프라인 실행:"
echo "   make aihub-pipeline"
echo ""
echo "📚 상세 가이드: docs/AIHUB_DATASET_ANALYSIS.md"
echo ""
echo "✅ 완료!"

