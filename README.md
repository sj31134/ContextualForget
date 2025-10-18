# ContextualForget — Advanced Graph-RAG with Contextual Forgetting & Adaptive Retrieval

**IFC(정적 구조) + BCF(동적 이슈)**를 하나의 그래프로 묶고, **맥락적 망각 메커니즘**과 **적응적 검색 전략**을 적용하여
**BM25, Vector, ContextualForget, Hybrid** 4개 엔진을 통한 **고성능 RAG 시스템**입니다.

## 🎯 연구 목표

- **RQ1**: 맥락적 망각 메커니즘의 효과성 - ContextualForgetting이 기존 RAG(BM25, Vector)보다 우수한가?
- **RQ2**: 적응적 검색 전략의 우수성 - 쿼리 타입별 최적 엔진 선택이 검색 품질을 향상시키는가?
- **RQ3**: 통합 시스템의 범용성 - 다양한 건설 프로젝트 유형과 쿼리 타입에서 효과적인가?

[![CI](https://github.com/sj31134/ContextualForget/workflows/CI/badge.svg)](https://github.com/sj31134/ContextualForget/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 주요 기능

- 🧠 **4개 RAG 엔진**: BM25, Vector, ContextualForget, Hybrid 엔진 비교
- 🔄 **맥락적 망각**: 사용 패턴 기반 동적 가중치 조정
- 🎯 **적응적 검색**: 쿼리 타입별 최적 엔진 자동 선택
- 📊 **종합 평가**: NDCG, F1, Precision, Recall 등 표준 메트릭
- 🕸️ **통합 그래프**: IFC 구조와 BCF 이슈를 하나의 지식 그래프로 통합
- 📈 **통계적 검증**: ANOVA, t-test, Cohen's d를 통한 유의성 검증

## 🚀 Quickstart

```bash
# 1. Clone and setup
git clone https://github.com/sj31134/ContextualForget.git
cd ContextualForget
conda create -n contextualforget python=3.11 -y
conda activate contextualforget
pip install -e ".[dev,demo]"

# 2. 데이터 준비 및 그래프 구축
python scripts/generate_sample_data.py
python scripts/process_all_data.py

# 3. Gold Standard 생성
python scripts/generate_gold_standard_llm.py

# 4. 종합 평가 실행
python scripts/comprehensive_evaluation_v4.py

# 5. 통계적 분석
python scripts/statistical_analysis.py
```

## 📊 주요 결과

### 🎯 성능 지표
- **ContextualForget**: 최고 성능 (F1: 0.85, Recall: 0.82)
- **Hybrid**: 적응적 검색으로 안정적 성능
- **BM25/Vector**: 전통적 RAG 베이스라인

### 📈 통계적 검증
- **ANOVA p < 0.0001**: 엔진 간 유의한 성능 차이
- **Cohen's d > 0.8**: 큰 효과 크기
- **NDCG@10**: ContextualForget이 0.78로 최고

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG 엔진 아키텍처                          │
│  BM25 ←→ Vector ←→ ContextualForget ←→ Hybrid               │
└─────────────────────────────────────────────────────────────┘
                            ↓
IFC Files → IFC Parser → Graph Builder ← BCF Parser ← BCF Files
                ↓                           ↓
            Entity Nodes ←→ Topic Nodes (with Contextual Forgetting)
                ↓
     ┌──────────────────────────────┐
     │     평가 시스템 (Gold Standard) │
     │  NDCG, F1, Precision, Recall  │
     └──────────────────────────────┘
                ↓
            통계적 검증 (ANOVA, t-test)
```

## 📁 Project Structure

```
src/contextualforget/
├── baselines/              # 베이스라인 RAG 엔진
│   ├── base.py            # 기본 엔진 인터페이스
│   ├── bm25_engine.py     # BM25 키워드 검색
│   └── vector_engine.py   # Vector 의미 검색
├── query/                  # 고급 쿼리 엔진
│   ├── contextual_forget_engine.py  # 맥락적 망각 엔진
│   ├── adaptive_retrieval.py        # 적응적 검색
│   └── advanced_query.py  # 고급 쿼리
├── core/                   # 핵심 기능
│   ├── contextual_forgetting.py     # 맥락적 망각 메커니즘
│   ├── forgetting.py      # 기본 망각 메커니즘
│   └── utils.py           # 유틸리티 함수
├── data/                   # 데이터 처리
│   ├── ingest_ifc.py      # IFC 데이터 수집
│   ├── ingest_bcf.py      # BCF 데이터 수집
│   ├── link_ifc_bcf.py    # IFC-BCF 연결
│   └── build_graph.py     # 그래프 구축
└── cli/                    # 명령줄 인터페이스
    └── cli.py             # CLI 명령어

eval/                       # 평가 시스템
├── metrics_v2.py          # 평가 메트릭 (NDCG, F1, etc.)
├── gold_standard_v3_fixed.jsonl  # Gold Standard QA
└── run_*.py               # 평가 실행 스크립트

scripts/                    # 유틸리티 스크립트
├── comprehensive_evaluation_v4.py  # 종합 평가
├── statistical_analysis.py        # 통계적 분석
└── generate_*.py          # 데이터 생성
```

## 📚 Documentation

- [Research Plan](docs/research_plan.md) - 연구 계획 및 방법론
- [Final Research Report](docs/FINAL_RESEARCH_REPORT.md) - 최종 연구 보고서
- [Data Collection Guide](docs/DATA_COLLECTION_GUIDE_5-10.md) - 데이터 수집 가이드
- [API Reference](docs/api_reference.md) - API 문서

## 🔧 주요 기능

### 🧠 RAG 엔진 비교
- **BM25**: 키워드 기반 전통적 검색
- **Vector**: 의미 기반 임베딩 검색  
- **ContextualForget**: 맥락적 망각 메커니즘 적용
- **Hybrid**: 적응적 검색 전략

### 📊 평가 시스템
- **Gold Standard**: 200개 QA 쌍
- **표준 메트릭**: NDCG@10, F1, Precision, Recall
- **통계적 검증**: ANOVA, t-test, Cohen's d

### 🔄 맥락적 망각
- **사용 패턴 기반**: 접근 빈도에 따른 가중치 조정
- **시간 기반**: 최근성에 따른 우선순위
- **관련성 기반**: 쿼리와의 유사도 고려

## 🛠️ Development

```bash
# Run tests
pytest

# Code formatting
ruff check .
ruff format .

# Clean up
make clean
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

- GitHub Issues: [Report bugs or request features](https://github.com/sj31134/ContextualForget/issues)
- Documentation: [docs/](docs/)

---

**Note**: 대형 파일은 Git LFS 규칙을 사용합니다 (`.gitattributes` 참조).