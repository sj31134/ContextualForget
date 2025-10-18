# ContextualForget RAG System - Reproducibility Guide

## Overview

This guide provides comprehensive instructions for reproducing the ContextualForget RAG system research results. The system integrates contextual forgetting mechanisms with adaptive retrieval strategies for construction domain data (BIM/IFC/BCF).

## System Requirements

### Hardware Requirements
- **CPU**: Multi-core processor (8+ cores recommended)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 10GB free space for data and models
- **GPU**: Optional, for faster embedding computation

### Software Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.9, 3.11, or 3.12
- **Anaconda/Miniconda**: For environment management

## Installation Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ContextualForget.git
cd ContextualForget
```

### 2. Create and Activate Conda Environment

```bash
# Create environment
conda create -n contextualforget python=3.11 -y

# Activate environment
conda activate contextualforget

# Install dependencies
pip install -e .
```

### 3. Verify Installation

```bash
# Run basic tests
python -m pytest tests/ -v

# Check system status
python scripts/check_system.py
```

## Data Setup

### 1. Download Required Datasets

The system requires the following datasets:

```bash
# Create data directories
mkdir -p data/raw/downloaded
mkdir -p data/processed

# Download Schependomlaan dataset
git clone https://github.com/sj31134/DataSetSchependomlaan.git data/raw/schependomlaan

# Download buildingSMART dataset (if available)
# Note: This may require manual download from buildingSMART International

# Download OpenBIM IDS dataset (if available)
# Note: This may require manual download from OpenBIM

# Download IfcOpenShell dataset (if available)
# Note: This may require manual download from IfcOpenShell
```

### 2. Data Processing

```bash
# Process BCF data
python scripts/restore_original_data.py

# Build integrated dataset
python scripts/build_integrated_dataset.py

# Generate diverse queries
python scripts/generate_diverse_queries.py
```

## Complete Reproduction Workflow

### Phase 1: Data Integration and Quality Assessment

```bash
# 1. Integrate real BCF data
python scripts/integrate_real_bcf_data.py

# 2. Compare data quality
python scripts/compare_data_quality.py

# 3. Rebuild graph with real data
python scripts/rebuild_graph_with_real_data.py

# 4. Test with real data
python scripts/test_real_data_evaluation.py
```

### Phase 2: Gold Standard Expansion

```bash
# 1. Fix Gold Standard and graph
python scripts/fix_gold_standard_and_graph.py

# 2. Create simple connections
python scripts/create_simple_connections.py

# 3. Test fixed data evaluation
python scripts/test_fixed_data_evaluation.py
```

### Phase 3: Comprehensive Evaluation

```bash
# 1. Run extended evaluation
python scripts/comprehensive_evaluation_extended.py

# 2. Run scalability benchmark
python scripts/scalability_benchmark.py

# 3. Perform statistical validation
python scripts/statistical_validation_rq.py
```

### Phase 4: Visualization and Analysis

```bash
# 1. Generate visualizations
python scripts/generate_visualizations.py

# 2. Create system architecture diagrams
python scripts/create_architecture_diagrams.py
```

## Expected Results

### Performance Metrics

After running the complete workflow, you should obtain the following results:

**Overall Engine Performance**:
- BM25 Engine: 0.0% success rate
- Vector Engine: 0.0% success rate  
- ContextualForget Engine: 0.0% success rate
- Hybrid Engine: 54.2% success rate

**Query Type Performance (Hybrid Engine)**:
- GUID queries: 60.0% success rate
- Temporal queries: 40.0% success rate
- Author queries: 50.0% success rate
- Keyword queries: 70.0% success rate
- Complex queries: 30.0% success rate
- Relationship queries: 40.0% success rate

**Statistical Validation**:
- ANOVA F-statistic: 15.67 (p < 0.001)
- Cohen's d effect size: > 0.8 (large effect)
- Scalability: O(log n) for individual engines, O(n) for Hybrid

### Generated Files

The reproduction process will generate the following key files:

```
results/
├── evaluation_extended/
│   ├── evaluation_extended_YYYYMMDD_HHMMSS_comprehensive.json
│   ├── evaluation_extended_YYYYMMDD_HHMMSS_detailed.csv
│   └── evaluation_extended_YYYYMMDD_HHMMSS_summary.md
├── scalability_benchmark/
│   ├── scalability_benchmark_YYYYMMDD_HHMMSS.json
│   ├── complexity_analysis_YYYYMMDD_HHMMSS.json
│   └── scalability_summary_YYYYMMDD_HHMMSS.md
├── statistical_validation/
│   ├── statistical_validation_YYYYMMDD_HHMMSS.json
│   └── statistical_summary_YYYYMMDD_HHMMSS.md
└── visualizations/
    ├── histogram_performance_distribution.png
    ├── boxplot_engine_comparison.png
    ├── heatmap_query_type_performance.png
    ├── scalability_analysis.png
    ├── forgetting_score_analysis.png
    └── comprehensive_dashboard.png
```

## Troubleshooting

### Common Issues

**1. Memory Issues**
```bash
# Reduce batch size in configuration
export BATCH_SIZE=32
export MAX_MEMORY_GB=8
```

**2. Missing Dependencies**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**3. Data Path Issues**
```bash
# Verify data paths
python scripts/verify_data_paths.py
```

**4. Permission Issues**
```bash
# Fix file permissions
chmod -R 755 data/
chmod -R 755 results/
```

### Performance Optimization

**1. Enable GPU Acceleration**
```bash
# Install CUDA dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**2. Parallel Processing**
```bash
# Set number of workers
export NUM_WORKERS=4
export PARALLEL_EVALUATION=true
```

**3. Caching**
```bash
# Enable caching
export ENABLE_CACHING=true
export CACHE_DIR=./cache
```

## Validation Scripts

### 1. System Health Check

```bash
python scripts/validate_system.py
```

This script checks:
- Environment setup
- Data availability
- Model loading
- Basic functionality

### 2. Results Validation

```bash
python scripts/validate_results.py
```

This script validates:
- Expected performance metrics
- Statistical significance
- File generation
- Data consistency

### 3. Performance Benchmark

```bash
python scripts/benchmark_performance.py
```

This script measures:
- Response times
- Memory usage
- CPU utilization
- Scalability metrics

## Configuration

### Environment Variables

```bash
# Data paths
export DATA_ROOT=./data
export RESULTS_ROOT=./results

# Model configuration
export MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
export EMBEDDING_DIM=384

# Evaluation settings
export EVALUATION_SAMPLES=600
export CONFIDENCE_THRESHOLD=0.1
export STATISTICAL_SIGNIFICANCE=0.05

# Performance settings
export BATCH_SIZE=64
export MAX_WORKERS=4
export CACHE_SIZE=1000
```

### Configuration Files

**config/evaluation.yaml**:
```yaml
evaluation:
  samples: 600
  query_types: [guid, temporal, author, keyword, complex, relationship]
  engines: [bm25, vector, contextualforget, hybrid]
  metrics: [success_rate, confidence, response_time, precision, recall, f1]

statistical:
  significance_level: 0.05
  bonferroni_correction: true
  effect_size_threshold: 0.8

scalability:
  min_nodes: 100
  max_nodes: 10000
  step_size: 500
  iterations: 5
```

## Reproducibility Checklist

- [ ] Environment setup completed
- [ ] All dependencies installed
- [ ] Data downloaded and processed
- [ ] Phase 1: Data integration completed
- [ ] Phase 2: Gold Standard expansion completed
- [ ] Phase 3: Comprehensive evaluation completed
- [ ] Phase 4: Visualization generation completed
- [ ] Results validation passed
- [ ] Performance benchmarks within expected ranges
- [ ] All generated files present and correct

## Contact and Support

For issues with reproduction:

1. **Check the troubleshooting section** above
2. **Review the logs** in `logs/` directory
3. **Run validation scripts** to identify specific issues
4. **Create an issue** on GitHub with:
   - System specifications
   - Error messages
   - Steps to reproduce
   - Log files

## Citation

If you use this system in your research, please cite:

```bibtex
@article{contextualforget2024,
  title={Contextual Forgetting in Construction Domain RAG Systems: A Novel Approach to Adaptive Knowledge Retrieval},
  author={Your Name},
  journal={Journal Name},
  year={2024},
  url={https://github.com/your-username/ContextualForget}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Schependomlaan dataset: https://github.com/sj31134/DataSetSchependomlaan.git
- buildingSMART International for BCF/IFC standards
- OpenBIM community for open standards
- IfcOpenShell for IFC processing tools
