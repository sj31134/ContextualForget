#!/usr/bin/env python3
"""
실제 데이터 vs 합성 데이터 품질 비교 분석
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from collections import Counter
import statistics

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import read_jsonl


def analyze_data_quality():
    """실제 데이터와 합성 데이터의 품질을 비교 분석"""
    
    print("🔍 데이터 품질 비교 분석 시작...")
    
    # 1. 실제 BCF 데이터 분석
    print("\n📊 실제 BCF 데이터 분석...")
    real_bcf_file = Path("data/processed/real_bcf/real_bcf_data.jsonl")
    real_data = list(read_jsonl(str(real_bcf_file)))
    
    real_stats = analyze_bcf_data(real_data, "실제 BCF")
    
    # 2. 기존 합성 데이터 분석
    print("\n📊 기존 합성 데이터 분석...")
    synthetic_files = list(Path("data/processed").glob("bcf_*.jsonl"))
    synthetic_data = []
    
    for file in synthetic_files:
        if file.name.startswith("bcf_"):
            data = list(read_jsonl(str(file)))
            synthetic_data.extend(data)
    
    synthetic_stats = analyze_bcf_data(synthetic_data, "합성 BCF")
    
    # 3. 비교 분석
    print("\n📈 데이터 품질 비교 결과...")
    comparison = compare_data_quality(real_stats, synthetic_stats)
    
    # 4. 결과 저장
    save_comparison_results(real_stats, synthetic_stats, comparison)
    
    return comparison


def analyze_bcf_data(data, data_type):
    """BCF 데이터의 품질 지표 분석"""
    
    stats = {
        "data_type": data_type,
        "total_issues": len(data),
        "unique_topic_ids": len(set(row.get('topic_id', '') for row in data)),
        "title_analysis": {},
        "author_analysis": {},
        "description_analysis": {},
        "date_analysis": {},
        "quality_metrics": {}
    }
    
    # 제목 분석
    titles = [row.get('title', '') for row in data]
    stats["title_analysis"] = {
        "non_empty_titles": len([t for t in titles if t.strip()]),
        "empty_titles": len([t for t in titles if not t.strip()]),
        "unique_titles": len(set(t for t in titles if t.strip())),
        "avg_title_length": statistics.mean([len(t) for t in titles if t.strip()]) if any(t.strip() for t in titles) else 0,
        "most_common_titles": dict(Counter(t for t in titles if t.strip()).most_common(5))
    }
    
    # 작성자 분석
    authors = [row.get('author', '') for row in data]
    stats["author_analysis"] = {
        "non_empty_authors": len([a for a in authors if a.strip()]),
        "empty_authors": len([a for a in authors if not a.strip()]),
        "unique_authors": len(set(a for a in authors if a.strip())),
        "most_common_authors": dict(Counter(a for a in authors if a.strip()).most_common(5))
    }
    
    # 설명 분석
    descriptions = [row.get('description', '') for row in data]
    stats["description_analysis"] = {
        "non_empty_descriptions": len([d for d in descriptions if d.strip()]),
        "empty_descriptions": len([d for d in descriptions if not d.strip()]),
        "avg_description_length": statistics.mean([len(d) for d in descriptions if d.strip()]) if any(d.strip() for d in descriptions) else 0,
        "max_description_length": max([len(d) for d in descriptions if d.strip()]) if any(d.strip() for d in descriptions) else 0
    }
    
    # 날짜 분석
    dates = [row.get('created', '') for row in data]
    stats["date_analysis"] = {
        "non_empty_dates": len([d for d in dates if d.strip()]),
        "empty_dates": len([d for d in dates if not d.strip()]),
        "date_format_consistency": len(set(d for d in dates if d.strip()))
    }
    
    # 품질 지표 계산
    total_issues = len(data)
    stats["quality_metrics"] = {
        "completeness_score": calculate_completeness_score(stats),
        "diversity_score": calculate_diversity_score(stats),
        "consistency_score": calculate_consistency_score(stats),
        "overall_quality_score": 0  # 나중에 계산
    }
    
    # 전체 품질 점수 계산
    quality_metrics = stats["quality_metrics"]
    stats["quality_metrics"]["overall_quality_score"] = (
        quality_metrics["completeness_score"] * 0.4 +
        quality_metrics["diversity_score"] * 0.3 +
        quality_metrics["consistency_score"] * 0.3
    )
    
    print(f"  ✅ {data_type} 분석 완료:")
    print(f"    📋 총 이슈 수: {stats['total_issues']}")
    print(f"    🎯 고유 토픽 ID: {stats['unique_topic_ids']}")
    print(f"    📝 비어있지 않은 제목: {stats['title_analysis']['non_empty_titles']}")
    print(f"    👤 비어있지 않은 작성자: {stats['author_analysis']['non_empty_authors']}")
    print(f"    📄 비어있지 않은 설명: {stats['description_analysis']['non_empty_descriptions']}")
    print(f"    ⭐ 전체 품질 점수: {stats['quality_metrics']['overall_quality_score']:.2f}")
    
    return stats


def calculate_completeness_score(stats):
    """완성도 점수 계산 (0-1)"""
    total_issues = stats["total_issues"]
    if total_issues == 0:
        return 0.0
    
    # 각 필드의 완성도 계산
    title_completeness = stats["title_analysis"]["non_empty_titles"] / total_issues
    author_completeness = stats["author_analysis"]["non_empty_authors"] / total_issues
    description_completeness = stats["description_analysis"]["non_empty_descriptions"] / total_issues
    date_completeness = stats["date_analysis"]["non_empty_dates"] / total_issues
    
    # 가중 평균 (설명이 가장 중요)
    completeness = (
        title_completeness * 0.2 +
        author_completeness * 0.2 +
        description_completeness * 0.4 +
        date_completeness * 0.2
    )
    
    return completeness


def calculate_diversity_score(stats):
    """다양성 점수 계산 (0-1)"""
    total_issues = stats["total_issues"]
    if total_issues == 0:
        return 0.0
    
    # 제목 다양성
    unique_titles = stats["title_analysis"]["unique_titles"]
    title_diversity = min(1.0, unique_titles / total_issues)
    
    # 작성자 다양성
    unique_authors = stats["author_analysis"]["unique_authors"]
    author_diversity = min(1.0, unique_authors / total_issues) if total_issues > 0 else 0.0
    
    # 전체 다양성 (제목과 작성자 평균)
    diversity = (title_diversity + author_diversity) / 2
    
    return diversity


def calculate_consistency_score(stats):
    """일관성 점수 계산 (0-1)"""
    # 날짜 형식 일관성
    date_consistency = 1.0 if stats["date_analysis"]["date_format_consistency"] <= 1 else 0.5
    
    # 제목 길이 일관성 (표준편차가 작을수록 일관성 높음)
    title_lengths = [len(t) for t in [row.get('title', '') for row in []] if t.strip()]
    if len(title_lengths) > 1:
        title_std = statistics.stdev(title_lengths)
        title_consistency = max(0, 1.0 - (title_std / 50))  # 50자 기준으로 정규화
    else:
        title_consistency = 1.0
    
    consistency = (date_consistency + title_consistency) / 2
    
    return consistency


def compare_data_quality(real_stats, synthetic_stats):
    """실제 데이터와 합성 데이터 품질 비교"""
    
    comparison = {
        "comparison_date": datetime.now().isoformat(),
        "data_volume_comparison": {},
        "quality_metrics_comparison": {},
        "field_analysis_comparison": {},
        "recommendations": []
    }
    
    # 데이터 볼륨 비교
    comparison["data_volume_comparison"] = {
        "real_data_issues": real_stats["total_issues"],
        "synthetic_data_issues": synthetic_stats["total_issues"],
        "volume_ratio": real_stats["total_issues"] / synthetic_stats["total_issues"] if synthetic_stats["total_issues"] > 0 else float('inf')
    }
    
    # 품질 지표 비교
    real_quality = real_stats["quality_metrics"]
    synthetic_quality = synthetic_stats["quality_metrics"]
    
    comparison["quality_metrics_comparison"] = {
        "completeness": {
            "real": real_quality["completeness_score"],
            "synthetic": synthetic_quality["completeness_score"],
            "difference": real_quality["completeness_score"] - synthetic_quality["completeness_score"]
        },
        "diversity": {
            "real": real_quality["diversity_score"],
            "synthetic": synthetic_quality["diversity_score"],
            "difference": real_quality["diversity_score"] - synthetic_quality["diversity_score"]
        },
        "consistency": {
            "real": real_quality["consistency_score"],
            "synthetic": synthetic_quality["consistency_score"],
            "difference": real_quality["consistency_score"] - synthetic_quality["consistency_score"]
        },
        "overall": {
            "real": real_quality["overall_quality_score"],
            "synthetic": synthetic_quality["overall_quality_score"],
            "difference": real_quality["overall_quality_score"] - synthetic_quality["overall_quality_score"]
        }
    }
    
    # 필드별 분석 비교
    comparison["field_analysis_comparison"] = {
        "titles": {
            "real_non_empty": real_stats["title_analysis"]["non_empty_titles"],
            "synthetic_non_empty": synthetic_stats["title_analysis"]["non_empty_titles"],
            "real_avg_length": real_stats["title_analysis"]["avg_title_length"],
            "synthetic_avg_length": synthetic_stats["title_analysis"]["avg_title_length"]
        },
        "authors": {
            "real_non_empty": real_stats["author_analysis"]["non_empty_authors"],
            "synthetic_non_empty": synthetic_stats["author_analysis"]["non_empty_authors"],
            "real_unique": real_stats["author_analysis"]["unique_authors"],
            "synthetic_unique": synthetic_stats["author_analysis"]["unique_authors"]
        },
        "descriptions": {
            "real_non_empty": real_stats["description_analysis"]["non_empty_descriptions"],
            "synthetic_non_empty": synthetic_stats["description_analysis"]["non_empty_descriptions"],
            "real_avg_length": real_stats["description_analysis"]["avg_description_length"],
            "synthetic_avg_length": synthetic_stats["description_analysis"]["avg_description_length"]
        }
    }
    
    # 권장사항 생성
    recommendations = []
    
    if real_quality["overall_quality_score"] > synthetic_quality["overall_quality_score"]:
        recommendations.append("실제 데이터가 합성 데이터보다 전반적으로 높은 품질을 보입니다.")
    
    if real_quality["completeness_score"] > synthetic_quality["completeness_score"]:
        recommendations.append("실제 데이터의 완성도가 더 높습니다. 실제 데이터를 주요 훈련 데이터로 사용하세요.")
    
    if real_quality["diversity_score"] > synthetic_quality["diversity_score"]:
        recommendations.append("실제 데이터의 다양성이 더 높습니다. 더 풍부한 패턴 학습이 가능합니다.")
    
    if real_stats["total_issues"] < synthetic_stats["total_issues"]:
        recommendations.append("실제 데이터의 양이 적습니다. 합성 데이터를 보완 데이터로 활용하세요.")
    
    comparison["recommendations"] = recommendations
    
    # 결과 출력
    print("\n" + "="*60)
    print("📊 데이터 품질 비교 결과")
    print("="*60)
    
    print(f"\n📈 품질 지표 비교:")
    print(f"  완성도: 실제 {real_quality['completeness_score']:.3f} vs 합성 {synthetic_quality['completeness_score']:.3f}")
    print(f"  다양성: 실제 {real_quality['diversity_score']:.3f} vs 합성 {synthetic_quality['diversity_score']:.3f}")
    print(f"  일관성: 실제 {real_quality['consistency_score']:.3f} vs 합성 {synthetic_quality['consistency_score']:.3f}")
    print(f"  전체: 실제 {real_quality['overall_quality_score']:.3f} vs 합성 {synthetic_quality['overall_quality_score']:.3f}")
    
    print(f"\n📋 데이터 볼륨:")
    print(f"  실제 데이터: {real_stats['total_issues']}개 이슈")
    print(f"  합성 데이터: {synthetic_stats['total_issues']}개 이슈")
    
    print(f"\n💡 권장사항:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    return comparison


def save_comparison_results(real_stats, synthetic_stats, comparison):
    """비교 결과를 파일로 저장"""
    
    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 전체 결과 저장
    full_results = {
        "real_data_analysis": real_stats,
        "synthetic_data_analysis": synthetic_stats,
        "comparison": comparison
    }
    
    results_file = output_dir / "data_quality_comparison.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 비교 결과 저장 완료: {results_file}")


def main():
    """메인 실행 함수"""
    print("🚀 데이터 품질 비교 분석 시작")
    print("="*60)
    
    try:
        comparison = analyze_data_quality()
        
        print("\n" + "="*60)
        print("🎉 데이터 품질 비교 분석 완료!")
        
        # 주요 결론
        real_score = comparison["quality_metrics_comparison"]["overall"]["real"]
        synthetic_score = comparison["quality_metrics_comparison"]["overall"]["synthetic"]
        
        if real_score > synthetic_score:
            print(f"✅ 실제 데이터가 합성 데이터보다 {real_score - synthetic_score:.3f}점 높은 품질을 보입니다!")
        else:
            print(f"⚠️ 합성 데이터가 실제 데이터보다 {synthetic_score - real_score:.3f}점 높은 품질을 보입니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
