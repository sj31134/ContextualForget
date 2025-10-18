#!/usr/bin/env python3
"""
RQ 검증을 위한 통계적 분석 스크립트
t-test, ANOVA, Cohen's d, 히스토그램, Box-Whisker 플롯 생성
"""

import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import seaborn as sns  # seaborn 없이 실행
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from scipy import stats
from scipy.stats import ttest_ind, f_oneway, levene, shapiro
import warnings
warnings.filterwarnings('ignore')

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def load_evaluation_results():
    """평가 결과 로드"""
    
    print("📂 평가 결과 로드 중...")
    
    # 최신 평가 결과 파일 찾기
    results_dir = Path("results/evaluation_extended")
    if not results_dir.exists():
        print("❌ 평가 결과 디렉토리를 찾을 수 없습니다.")
        return None
    
    # 가장 최근 파일 찾기
    result_files = list(results_dir.glob("evaluation_extended_*_comprehensive.json"))
    if not result_files:
        print("❌ 평가 결과 파일을 찾을 수 없습니다.")
        return None
    
    latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
    print(f"  📁 로드 중: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print(f"  ✅ 평가 결과 로드 완료: {results['total_queries']}개 질의")
    return results


def prepare_data_for_analysis(results):
    """통계 분석을 위한 데이터 준비"""
    
    print("📊 통계 분석용 데이터 준비 중...")
    
    # 데이터프레임 생성
    data_rows = []
    
    for engine_name, engine_data in results["engine_results"].items():
        for qtype, query_results in engine_data.items():
            for result in query_results:
                data_rows.append({
                    'engine': engine_name,
                    'query_type': qtype,
                    'query_id': result['query_id'],
                    'success': result['success'],
                    'confidence': result['confidence'],
                    'response_time': result['response_time'],
                    'memory_delta_mb': result['memory_delta_mb'],
                    'cpu_delta_percent': result['cpu_delta_percent']
                })
    
    df = pd.DataFrame(data_rows)
    
    print(f"  ✅ 데이터 준비 완료: {len(df)}개 레코드")
    print(f"  📊 엔진별 분포:")
    for engine in df['engine'].unique():
        count = len(df[df['engine'] == engine])
        print(f"    • {engine}: {count}개")
    
    return df


def rq1_contextual_forgetting_effectiveness(df):
    """RQ1: 맥락적 망각 메커니즘의 효과성 검증"""
    
    print("🔬 RQ1: 맥락적 망각 메커니즘의 효과성 검증 중...")
    
    # ContextualForget vs BM25, Vector 비교
    contextualforget = df[df['engine'] == 'ContextualForget']
    bm25 = df[df['engine'] == 'BM25']
    vector = df[df['engine'] == 'Vector']
    
    rq1_results = {
        "hypothesis": "ContextualForget이 BM25, Vector보다 우수한 성능을 보일 것이다",
        "comparisons": {}
    }
    
    # ContextualForget vs BM25
    if len(contextualforget) > 0 and len(bm25) > 0:
        # 성공률 비교
        cf_success_rate = contextualforget['success'].mean()
        bm25_success_rate = bm25['success'].mean()
        
        # 신뢰도 비교
        cf_confidence = contextualforget['confidence'].mean()
        bm25_confidence = bm25['confidence'].mean()
        
        # t-test (신뢰도)
        t_stat_cf_bm25, p_val_cf_bm25 = ttest_ind(
            contextualforget['confidence'], 
            bm25['confidence']
        )
        
        # Cohen's d (효과 크기)
        pooled_std = np.sqrt(((len(contextualforget)-1) * contextualforget['confidence'].std()**2 + 
                             (len(bm25)-1) * bm25['confidence'].std()**2) / 
                            (len(contextualforget) + len(bm25) - 2))
        cohens_d_cf_bm25 = (cf_confidence - bm25_confidence) / pooled_std if pooled_std > 0 else 0
        
        rq1_results["comparisons"]["ContextualForget_vs_BM25"] = {
            "success_rate": {
                "ContextualForget": cf_success_rate,
                "BM25": bm25_success_rate,
                "difference": cf_success_rate - bm25_success_rate
            },
            "confidence": {
                "ContextualForget": cf_confidence,
                "BM25": bm25_confidence,
                "difference": cf_confidence - bm25_confidence
            },
            "t_test": {
                "t_statistic": t_stat_cf_bm25,
                "p_value": p_val_cf_bm25,
                "significant": bool(p_val_cf_bm25 < 0.01)
            },
            "effect_size": {
                "cohens_d": cohens_d_cf_bm25,
                "interpretation": "large" if abs(cohens_d_cf_bm25) > 0.8 else "medium" if abs(cohens_d_cf_bm25) > 0.5 else "small"
            }
        }
    
    # ContextualForget vs Vector
    if len(contextualforget) > 0 and len(vector) > 0:
        vector_success_rate = vector['success'].mean()
        vector_confidence = vector['confidence'].mean()
        
        t_stat_cf_vector, p_val_cf_vector = ttest_ind(
            contextualforget['confidence'], 
            vector['confidence']
        )
        
        pooled_std = np.sqrt(((len(contextualforget)-1) * contextualforget['confidence'].std()**2 + 
                             (len(vector)-1) * vector['confidence'].std()**2) / 
                            (len(contextualforget) + len(vector) - 2))
        cohens_d_cf_vector = (cf_confidence - vector_confidence) / pooled_std if pooled_std > 0 else 0
        
        rq1_results["comparisons"]["ContextualForget_vs_Vector"] = {
            "success_rate": {
                "ContextualForget": cf_success_rate,
                "Vector": vector_success_rate,
                "difference": cf_success_rate - vector_success_rate
            },
            "confidence": {
                "ContextualForget": cf_confidence,
                "Vector": vector_confidence,
                "difference": cf_confidence - vector_confidence
            },
            "t_test": {
                "t_statistic": t_stat_cf_vector,
                "p_value": p_val_cf_vector,
                "significant": bool(p_val_cf_vector < 0.01)
            },
            "effect_size": {
                "cohens_d": cohens_d_cf_vector,
                "interpretation": "large" if abs(cohens_d_cf_vector) > 0.8 else "medium" if abs(cohens_d_cf_vector) > 0.5 else "small"
            }
        }
    
    print(f"  ✅ RQ1 검증 완료")
    return rq1_results


def rq2_adaptive_retrieval_superiority(df):
    """RQ2: 적응적 검색 전략의 우수성 검증"""
    
    print("🔬 RQ2: 적응적 검색 전략의 우수성 검증 중...")
    
    # 쿼리 타입별 성능 분석
    query_types = df['query_type'].unique()
    
    rq2_results = {
        "hypothesis": "적응적 검색 전략이 쿼리 타입별로 최적의 성능을 보일 것이다",
        "query_type_analysis": {},
        "anova_results": {}
    }
    
    # 각 쿼리 타입별로 엔진 성능 비교
    for qtype in query_types:
        qtype_data = df[df['query_type'] == qtype]
        
        if len(qtype_data) == 0:
            continue
        
        # 엔진별 성능
        engine_performance = {}
        for engine in qtype_data['engine'].unique():
            engine_data = qtype_data[qtype_data['engine'] == engine]
            engine_performance[engine] = {
                "success_rate": engine_data['success'].mean(),
                "avg_confidence": engine_data['confidence'].mean(),
                "avg_response_time": engine_data['response_time'].mean(),
                "count": len(engine_data)
            }
        
        rq2_results["query_type_analysis"][qtype] = engine_performance
    
    # ANOVA: 쿼리 타입별 적응적 전략 효과
    if len(query_types) > 1:
        # 각 쿼리 타입별로 Hybrid 엔진의 성능
        hybrid_performance_by_type = []
        for qtype in query_types:
            qtype_hybrid = df[(df['query_type'] == qtype) & (df['engine'] == 'Hybrid')]
            if len(qtype_hybrid) > 0:
                hybrid_performance_by_type.append(qtype_hybrid['confidence'].values)
        
        if len(hybrid_performance_by_type) > 1:
            # ANOVA 수행
            f_stat, p_val = f_oneway(*hybrid_performance_by_type)
            
            rq2_results["anova_results"] = {
                "f_statistic": f_stat,
                "p_value": p_val,
                "significant": bool(p_val < 0.01),
                "interpretation": "쿼리 타입별 적응적 전략 효과가 통계적으로 유의함" if p_val < 0.01 else "쿼리 타입별 효과가 통계적으로 유의하지 않음"
            }
    
    print(f"  ✅ RQ2 검증 완료")
    return rq2_results


def rq3_system_universality(df):
    """RQ3: 통합 시스템의 범용성 검증"""
    
    print("🔬 RQ3: 통합 시스템의 범용성 검증 중...")
    
    rq3_results = {
        "hypothesis": "통합 시스템이 다양한 쿼리 타입과 엔진에서 일관되게 우수한 성능을 보일 것이다",
        "universality_analysis": {}
    }
    
    # 엔진별 전체 성능
    engine_performance = {}
    for engine in df['engine'].unique():
        engine_data = df[df['engine'] == engine]
        engine_performance[engine] = {
            "success_rate": engine_data['success'].mean(),
            "avg_confidence": engine_data['confidence'].mean(),
            "avg_response_time": engine_data['response_time'].mean(),
            "total_queries": len(engine_data)
        }
    
    rq3_results["universality_analysis"]["engine_performance"] = engine_performance
    
    # 쿼리 타입별 성능 일관성
    query_type_consistency = {}
    for qtype in df['query_type'].unique():
        qtype_data = df[df['query_type'] == qtype]
        
        # 각 엔진의 성능
        engine_scores = []
        for engine in qtype_data['engine'].unique():
            engine_data = qtype_data[qtype_data['engine'] == engine]
            if len(engine_data) > 0:
                engine_scores.append(engine_data['confidence'].mean())
        
        if len(engine_scores) > 1:
            query_type_consistency[qtype] = {
                "mean_performance": np.mean(engine_scores),
                "std_performance": np.std(engine_scores),
                "coefficient_of_variation": np.std(engine_scores) / np.mean(engine_scores) if np.mean(engine_scores) > 0 else 0,
                "performance_range": max(engine_scores) - min(engine_scores)
            }
    
    rq3_results["universality_analysis"]["query_type_consistency"] = query_type_consistency
    
    # 전체 시스템 안정성 (모든 엔진의 성능 변동성)
    all_confidences = df['confidence'].values
    rq3_results["universality_analysis"]["system_stability"] = {
        "overall_mean_confidence": np.mean(all_confidences),
        "overall_std_confidence": np.std(all_confidences),
        "confidence_range": max(all_confidences) - min(all_confidences),
        "coefficient_of_variation": np.std(all_confidences) / np.mean(all_confidences) if np.mean(all_confidences) > 0 else 0
    }
    
    print(f"  ✅ RQ3 검증 완료")
    return rq3_results


def create_visualizations(df, rq1_results, rq2_results, rq3_results):
    """시각화 생성"""
    
    print("📊 시각화 생성 중...")
    
    # 결과 디렉토리 생성
    viz_dir = Path("visualizations/statistical_analysis")
    viz_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 신뢰도 분포 히스토그램
    plt.figure(figsize=(12, 8))
    for i, engine in enumerate(df['engine'].unique()):
        plt.subplot(2, 2, i+1)
        engine_data = df[df['engine'] == engine]['confidence']
        plt.hist(engine_data, bins=20, alpha=0.7, edgecolor='black')
        plt.title(f'{engine} - Confidence Distribution')
        plt.xlabel('Confidence')
        plt.ylabel('Frequency')
        plt.axvline(engine_data.mean(), color='red', linestyle='--', label=f'Mean: {engine_data.mean():.3f}')
        plt.legend()
    
    plt.tight_layout()
    plt.savefig(viz_dir / 'confidence_distribution_histogram.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Box-Whisker 플롯 (엔진별 성능)
    plt.figure(figsize=(10, 6))
    df_melted = df.melt(id_vars=['engine'], value_vars=['confidence', 'response_time'], 
                       var_name='metric', value_name='value')
    
    # sns.boxplot(data=df_melted, x='engine', y='value', hue='metric')  # seaborn 대신 matplotlib 사용
    df_melted.boxplot(column='value', by=['engine', 'metric'], ax=plt.gca())
    plt.title('Engine Performance Comparison (Box-Whisker Plot)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(viz_dir / 'engine_performance_boxplot.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. 쿼리 타입별 성능 히트맵
    plt.figure(figsize=(12, 8))
    
    # 성공률 히트맵
    plt.subplot(1, 2, 1)
    success_pivot = df.groupby(['engine', 'query_type'])['success'].mean().unstack()
    # sns.heatmap(success_pivot, annot=True, fmt='.2f', cmap='YlOrRd')  # matplotlib으로 대체
    plt.imshow(success_pivot.values, cmap='YlOrRd', aspect='auto')
    plt.colorbar()
    plt.xticks(range(len(success_pivot.columns)), success_pivot.columns)
    plt.yticks(range(len(success_pivot.index)), success_pivot.index)
    plt.title('Success Rate by Engine and Query Type')
    
    # 신뢰도 히트맵
    plt.subplot(1, 2, 2)
    confidence_pivot = df.groupby(['engine', 'query_type'])['confidence'].mean().unstack()
    # sns.heatmap(confidence_pivot, annot=True, fmt='.3f', cmap='Blues')  # matplotlib으로 대체
    plt.imshow(confidence_pivot.values, cmap='Blues', aspect='auto')
    plt.colorbar()
    plt.xticks(range(len(confidence_pivot.columns)), confidence_pivot.columns)
    plt.yticks(range(len(confidence_pivot.index)), confidence_pivot.index)
    plt.title('Confidence by Engine and Query Type')
    
    plt.tight_layout()
    plt.savefig(viz_dir / 'performance_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. 확장성 그래프 (응답 시간 vs 엔진)
    plt.figure(figsize=(10, 6))
    # sns.boxplot(data=df, x='engine', y='response_time')  # matplotlib으로 대체
    df.boxplot(column='response_time', by='engine', ax=plt.gca())
    plt.title('Response Time Distribution by Engine')
    plt.ylabel('Response Time (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(viz_dir / 'response_time_scalability.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. 망각 점수 시뮬레이션 (시간 경과별)
    plt.figure(figsize=(10, 6))
    
    # 망각 점수 시뮬레이션
    time_points = np.linspace(0, 365, 100)  # 1년간
    forgetting_scores = np.exp(-0.1 * time_points / 365)  # 지수적 감소
    
    plt.plot(time_points, forgetting_scores, linewidth=2, color='red')
    plt.title('Simulated Forgetting Score Over Time')
    plt.xlabel('Days Since Last Access')
    plt.ylabel('Forgetting Score')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.7, label='Threshold (0.5)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(viz_dir / 'forgetting_score_timeline.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ 시각화 생성 완료: {viz_dir}")
    return viz_dir


def save_statistical_results(rq1_results, rq2_results, rq3_results, viz_dir):
    """통계적 결과 저장"""
    
    print("💾 통계적 결과 저장 중...")
    
    # 결과 디렉토리 생성
    results_dir = Path("results/statistical_validation")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 통합 결과
    statistical_results = {
        "analysis_date": datetime.now().isoformat(),
        "rq1_contextual_forgetting": rq1_results,
        "rq2_adaptive_retrieval": rq2_results,
        "rq3_system_universality": rq3_results,
        "visualization_directory": str(viz_dir)
    }
    
    # JSON 저장
    results_file = results_dir / f"statistical_validation_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(statistical_results, f, indent=2, ensure_ascii=False)
    
    # 요약 보고서 생성
    summary_file = results_dir / f"statistical_summary_{timestamp}.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# 통계적 검증 결과 요약\n\n")
        f.write(f"**분석 일시**: {statistical_results['analysis_date']}\n\n")
        
        f.write("## RQ1: 맥락적 망각 메커니즘의 효과성\n\n")
        f.write(f"**가설**: {rq1_results['hypothesis']}\n\n")
        
        for comparison, data in rq1_results['comparisons'].items():
            f.write(f"### {comparison}\n\n")
            f.write(f"- **성공률 차이**: {data['success_rate']['difference']:.3f}\n")
            f.write(f"- **신뢰도 차이**: {data['confidence']['difference']:.3f}\n")
            f.write(f"- **t-test p-value**: {data['t_test']['p_value']:.6f}\n")
            f.write(f"- **통계적 유의성**: {'유의함' if data['t_test']['significant'] else '유의하지 않음'}\n")
            f.write(f"- **효과 크기 (Cohen's d)**: {data['effect_size']['cohens_d']:.3f} ({data['effect_size']['interpretation']})\n\n")
        
        f.write("## RQ2: 적응적 검색 전략의 우수성\n\n")
        f.write(f"**가설**: {rq2_results['hypothesis']}\n\n")
        
        if rq2_results['anova_results']:
            f.write("### ANOVA 결과\n\n")
            f.write(f"- **F-statistic**: {rq2_results['anova_results']['f_statistic']:.3f}\n")
            f.write(f"- **p-value**: {rq2_results['anova_results']['p_value']:.6f}\n")
            f.write(f"- **해석**: {rq2_results['anova_results']['interpretation']}\n\n")
        
        f.write("## RQ3: 통합 시스템의 범용성\n\n")
        f.write(f"**가설**: {rq3_results['hypothesis']}\n\n")
        
        f.write("### 엔진별 성능\n\n")
        for engine, perf in rq3_results['universality_analysis']['engine_performance'].items():
            f.write(f"- **{engine}**: 성공률 {perf['success_rate']:.1%}, 신뢰도 {perf['avg_confidence']:.3f}\n")
        
        f.write(f"\n### 시스템 안정성\n\n")
        stability = rq3_results['universality_analysis']['system_stability']
        f.write(f"- **전체 평균 신뢰도**: {stability['overall_mean_confidence']:.3f}\n")
        f.write(f"- **신뢰도 표준편차**: {stability['overall_std_confidence']:.3f}\n")
        f.write(f"- **변동계수**: {stability['coefficient_of_variation']:.3f}\n")
    
    print(f"  ✅ 결과 저장 완료:")
    print(f"    • 통계 결과: {results_file}")
    print(f"    • 요약 보고서: {summary_file}")
    
    return {
        "results_file": str(results_file),
        "summary_file": str(summary_file)
    }


def main():
    """메인 실행 함수"""
    
    print("🚀 통계적 검증 시작")
    print("=" * 60)
    
    # 1. 평가 결과 로드
    results = load_evaluation_results()
    if not results:
        return
    
    print("\n" + "=" * 60)
    
    # 2. 데이터 준비
    df = prepare_data_for_analysis(results)
    
    print("\n" + "=" * 60)
    
    # 3. RQ1 검증
    rq1_results = rq1_contextual_forgetting_effectiveness(df)
    
    print("\n" + "=" * 60)
    
    # 4. RQ2 검증
    rq2_results = rq2_adaptive_retrieval_superiority(df)
    
    print("\n" + "=" * 60)
    
    # 5. RQ3 검증
    rq3_results = rq3_system_universality(df)
    
    print("\n" + "=" * 60)
    
    # 6. 시각화 생성
    viz_dir = create_visualizations(df, rq1_results, rq2_results, rq3_results)
    
    print("\n" + "=" * 60)
    
    # 7. 결과 저장
    saved_files = save_statistical_results(rq1_results, rq2_results, rq3_results, viz_dir)
    
    print("\n" + "=" * 60)
    print("🎉 통계적 검증 완료!")
    print(f"\n📊 주요 결과:")
    
    # RQ1 요약
    if rq1_results['comparisons']:
        for comparison, data in rq1_results['comparisons'].items():
            print(f"  • {comparison}: p={data['t_test']['p_value']:.6f}, Cohen's d={data['effect_size']['cohens_d']:.3f}")
    
    # RQ2 요약
    if rq2_results['anova_results']:
        print(f"  • RQ2 ANOVA: F={rq2_results['anova_results']['f_statistic']:.3f}, p={rq2_results['anova_results']['p_value']:.6f}")
    
    # RQ3 요약
    stability = rq3_results['universality_analysis']['system_stability']
    print(f"  • RQ3 시스템 안정성: 평균 신뢰도 {stability['overall_mean_confidence']:.3f}, 변동계수 {stability['coefficient_of_variation']:.3f}")
    
    print(f"\n📁 결과 파일:")
    for file_type, file_path in saved_files.items():
        print(f"  • {file_type}: {file_path}")


if __name__ == "__main__":
    main()
