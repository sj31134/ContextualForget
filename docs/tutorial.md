# Tutorial: Getting Started with ContextualForget

## Overview

ContextualForget는 IFC(Industry Foundation Classes)와 BCF(BIM Collaboration Format) 데이터를 통합하여 디지털 트윈의 장기 기억을 관리하는 Graph-RAG 시스템입니다.

## Prerequisites

- Python 3.11+
- Conda 또는 pip
- Git LFS (대용량 파일용)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/sj31134/ContextualForget.git
cd ContextualForget
```

### 2. Setup Environment
```bash
# Using conda (recommended)
conda create -n contextualforget python=3.11 -y
conda activate contextualforget
pip install -e ".[dev]"

# Or using make
make setup
```

### 3. Initialize Git LFS
```bash
git lfs install
git lfs track "*.ifc" "*.bcf" "*.bcfzip"
```

## Quick Start

### 1. Generate Sample Data
```bash
make data
```

### 2. Run Complete Pipeline
```bash
make all
```

### 3. Query the System
```bash
# Using CLI command
ctxf 1kTvXnbbzCWw8lcMd1dR4o --ttl 365 --topk 5

# Or using Python module
python -m src.contextualforget.cli 1kTvXnbbzCWw8lcMd1dR4o --ttl 365 --topk 5
```

## Step-by-Step Pipeline

### Step 1: Ingest IFC Data
```bash
python -m src.contextualforget.ingest_ifc --ifc data/raw/sample.ifc --out data/processed/ifc.jsonl
```

### Step 2: Ingest BCF Data
```bash
python -m src.contextualforget.ingest_bcf --bcf data/raw/sample.bcfzip --out data/processed/bcf.jsonl
```

### Step 3: Link IFC and BCF
```bash
python -m src.contextualforget.link_ifc_bcf --ifc data/processed/ifc.jsonl --bcf data/processed/bcf.jsonl --out data/processed/links.jsonl
```

### Step 4: Build Graph
```bash
python -m src.contextualforget.build_graph --ifc data/processed/ifc.jsonl --bcf data/processed/bcf.jsonl --links data/processed/links.jsonl --out data/processed/graph.gpickle
```

### Step 5: Query
```bash
ctxf 1kTvXnbbzCWw8lcMd1dR4o --ttl 365 --topk 5
```

## Understanding the Output

### Query Result Format
```json
[
  {
    "topic_id": "11111111-1111-1111-1111-111111111111",
    "created": "2025-10-05T09:00:00Z",
    "edge": {
      "type": "refersTo",
      "confidence": 1.0
    }
  }
]
```

### Data Files
- `data/processed/ifc.jsonl`: IFC 엔티티 정보
- `data/processed/bcf.jsonl`: BCF 토픽 정보
- `data/processed/links.jsonl`: IFC-BCF 연결 정보
- `data/processed/graph.gpickle`: 통합 그래프

## Advanced Usage

### Custom TTL Settings
```bash
# 30일 이내의 이벤트만 조회
ctxf 1kTvXnbbzCWw8lcMd1dR4o --ttl 30

# 모든 이벤트 조회 (TTL 비활성화)
ctxf 1kTvXnbbzCWw8lcMd1dR4o --ttl 0
```

### Evaluation
```bash
make eval
```

### Development
```bash
# Run tests
pytest

# Code formatting
ruff check .
ruff format .

# Clean up
make clean
```

## Troubleshooting

### Common Issues

1. **Python Version Error**
   - Ensure Python 3.11+ is installed
   - Use conda environment for version management

2. **Git LFS Issues**
   - Run `git lfs install` and `git lfs pull`

3. **Import Errors**
   - Ensure package is installed in editable mode: `pip install -e .`

4. **File Not Found**
   - Run `make data` to generate sample data first

### Getting Help
- Check the [API Reference](api_reference.md)
- Review the [Research Plan](research_plan.md)
- Open an issue on GitHub
