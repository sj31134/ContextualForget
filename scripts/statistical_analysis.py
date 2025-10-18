"""
통계적 유의성 검정
엔진 간 성능 차이의 통계적 유의성 검증
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt


class StatisticalAnalyzer:
    """통계 분석기"""
    
    def __init__(self, detailed_results_path: str):
        self.detailed_results_path = detailed_results_path
        self.results = []
        self.engine_metrics = {}
        
    def load_results(self):
        """평가 결과 로드"""
        print("📊 평가 결과 로드 중...")
        with open(self.detailed_results_path, 'r') as f:
            self.results = json.load(f)
        print(f"✅ {len(self.results)}개 결과 로드 완료")
        
    def extract_engine_metrics(self, metric_name: str = 'f1'):
        """엔진별 메트릭 추출"""
        self.engine_metrics = {}
        
        for result in self.results:
            engine = result['engine']
            metric_value = result['metrics'].get(metric_name, 0.0)
            
            if engine not in self.engine_metrics:
                self.engine_metrics[engine] = []
            
            self.engine_metrics[engine].append(metric_value)
        
        # NumPy 배열로 변환
        for engine in self.engine_metrics:
            self.engine_metrics[engine] = np.array(self.engine_metrics[engine])
        
        print(f"\n엔진별 {metric_name} 샘플 수:")
        for engine, values in self.engine_metrics.items():
            print(f"  {engine}: {len(values)}개")
    
    def compute_paired_ttest(self, engine1: str, engine2: str, metric_name: str = 'f1'):
        """Paired t-test 수행"""
        values1 = self.engine_metrics[engine1]
        values2 = self.engine_metrics[engine2]
        
        # Paired t-test
        t_stat, p_value = stats.ttest_rel(values1, values2)
        
        # Cohen's d 계산 (effect size)
        diff = values1 - values2
        cohens_d = np.mean(diff) / np.std(diff, ddof=1)
        
        # Effect size 해석
        if abs(cohens_d) < 0.2:
            effect_size = "negligible"
        elif abs(cohens_d) < 0.5:
            effect_size = "small"
        elif abs(cohens_d) < 0.8:
            effect_size = "medium"
        else:
            effect_size = "large"
        
        return {
            'method1': engine1,
            'method2': engine2,
            'metric': metric_name,
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'cohens_d': float(cohens_d) if not np.isnan(cohens_d) else 0.0,
            'significant': bool(p_value < 0.05),
            'effect_size': effect_size,
            'mean1': float(np.mean(values1)),
            'mean2': float(np.mean(values2)),
            'std1': float(np.std(values1)),
            'std2': float(np.std(values2))
        }
    
    def compute_anova(self, metric_name: str = 'f1'):
        """ANOVA 수행 (4개 엔진 전체 비교)"""
        engine_names = list(self.engine_metrics.keys())
        engine_values = [self.engine_metrics[name] for name in engine_names]
        
        # One-way ANOVA
        f_stat, p_value = stats.f_oneway(*engine_values)
        
        return {
            'metric': metric_name,
            'engines': engine_names,
            'f_statistic': float(f_stat),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05)
        }
    
    def bonferroni_correction(self, comparisons: List[Dict], alpha: float = 0.05):
        """Bonferroni 다중 비교 보정"""
        n_comparisons = len(comparisons)
        corrected_alpha = alpha / n_comparisons
        
        for comp in comparisons:
            comp['bonferroni_corrected_alpha'] = corrected_alpha
            comp['significant_after_bonferroni'] = comp['p_value'] < corrected_alpha
        
        return comparisons
    
    def analyze_all_metrics(self):
        """모든 메트릭에 대해 통계 분석"""
        metrics = ['f1', 'precision', 'recall', 'ndcg@10', 'mrr', 'confidence']
        
        all_results = {
            'comparisons': [],
            'anova': []
        }
        
        for metric in metrics:
            print(f"\n📊 {metric.upper()} 분석 중...")
            
            # 엔진별 메트릭 추출
            self.extract_engine_metrics(metric)
            
            # ANOVA
            anova_result = self.compute_anova(metric)
            all_results['anova'].append(anova_result)
            print(f"  ANOVA: F={anova_result['f_statistic']:.3f}, p={anova_result['p_value']:.4f}, significant={anova_result['significant']}")
            
            # Pairwise t-tests
            engines = list(self.engine_metrics.keys())
            for i in range(len(engines)):
                for j in range(i+1, len(engines)):
                    comp = self.compute_paired_ttest(engines[i], engines[j], metric)
                    all_results['comparisons'].append(comp)
                    
                    if comp['significant']:
                        print(f"  ✅ {engines[i]} vs {engines[j]}: t={comp['t_statistic']:.3f}, p={comp['p_value']:.4f}, d={comp['cohens_d']:.3f} ({comp['effect_size']})")
        
        # Bonferroni correction
        all_results['comparisons'] = self.bonferroni_correction(all_results['comparisons'])
        
        return all_results
    
    def generate_visualization(self, output_path: str):
        """통계 분석 시각화"""
        print(f"\n📊 시각화 생성 중: {output_path}")
        
        # F1 메트릭 기준으로 시각화
        self.extract_engine_metrics('f1')
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Box plot
        ax1 = axes[0]
        data_for_plot = [self.engine_metrics[engine] for engine in self.engine_metrics.keys()]
        labels = list(self.engine_metrics.keys())
        
        bp = ax1.boxplot(data_for_plot, labels=labels, patch_artist=True)
        for patch, color in zip(bp['boxes'], ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow']):
            patch.set_facecolor(color)
        
        ax1.set_ylabel('F1 Score')
        ax1.set_title('F1 Score Distribution by Engine')
        ax1.grid(True, alpha=0.3)
        
        # Violin plot
        ax2 = axes[1]
        positions = range(1, len(labels) + 1)
        parts = ax2.violinplot(data_for_plot, positions=positions, showmeans=True, showmedians=True)
        
        ax2.set_xticks(positions)
        ax2.set_xticklabels(labels)
        ax2.set_ylabel('F1 Score')
        ax2.set_title('F1 Score Violin Plot by Engine')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 시각화 저장: {output_path}")
    
    def save_results(self, output_path: str, results: Dict):
        """결과 저장"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 통계 결과 저장: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='통계적 유의성 검정')
    parser.add_argument('--detailed-results', default='results/evaluation_v3_final/evaluation_v3_detailed.json', help='상세 평가 결과')
    parser.add_argument('--output', default='results/statistical_analysis_v3.json', help='출력 파일')
    parser.add_argument('--viz-output', default='results/statistical_analysis_v3.pdf', help='시각화 출력')
    args = parser.parse_args()
    
    print("\n" + "🎯 " + "="*58)
    print("   통계적 유의성 검정")
    print("="*60)
    
    # 분석기 초기화
    analyzer = StatisticalAnalyzer(args.detailed_results)
    
    # 결과 로드
    analyzer.load_results()
    
    # 통계 분석 수행
    results = analyzer.analyze_all_metrics()
    
    # 결과 저장
    analyzer.save_results(args.output, results)
    
    # 시각화 생성
    analyzer.generate_visualization(args.viz_output)
    
    # 요약 출력
    print("\n" + "="*60)
    print("📊 통계 분석 요약")
    print("="*60)
    
    # ANOVA 요약
    print("\n🔬 ANOVA 결과:")
    for anova in results['anova']:
        sig_mark = "✅" if anova['significant'] else "❌"
        print(f"  {sig_mark} {anova['metric']}: F={anova['f_statistic']:.3f}, p={anova['p_value']:.4f}")
    
    # 유의한 비교 요약
    significant_comps = [c for c in results['comparisons'] if c['significant_after_bonferroni']]
    print(f"\n✅ Bonferroni 보정 후 유의한 비교: {len(significant_comps)}개")
    
    for comp in significant_comps[:10]:  # 상위 10개만 출력
        print(f"  • {comp['method1']} vs {comp['method2']} ({comp['metric']}): p={comp['p_value']:.4f}, d={comp['cohens_d']:.3f}")
    
    print("\n" + "="*60)
    print("✅ 통계적 유의성 검정 완료!")
    print("="*60)


if __name__ == "__main__":
    main()

