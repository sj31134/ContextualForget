#!/usr/bin/env python3
"""
Phase 1 수집 데이터 검증 및 통계
"""

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw" / "downloaded"


def analyze_phase1_data():
    """Phase 1 데이터 분석"""
    print("\n" + "="*60)
    print("📊 Phase 1 데이터 분석 및 검증")
    print("="*60)
    
    # IFC 파일 분석
    ifc_files = list(RAW_DIR.glob("*.ifc"))
    ifc_total_size = sum(f.stat().st_size for f in ifc_files)
    
    print(f"\n🏗️  IFC 파일:")
    print(f"   총 파일 수: {len(ifc_files)}개")
    print(f"   총 크기: {ifc_total_size / 1024 / 1024:.2f} MB")
    
    # IFC 소스별 분류
    ifc_sources = Counter()
    for f in ifc_files:
        if "buildingsmart" in f.name.lower():
            ifc_sources["buildingSMART"] += 1
        elif "ifcopenshell" in f.name.lower():
            ifc_sources["IfcOpenShell"] += 1
        elif "xbim" in f.name.lower():
            ifc_sources["xBIM"] += 1
        elif "korea" in f.name.lower():
            ifc_sources["Korea"] += 1
        else:
            ifc_sources["Other"] += 1
    
    print(f"\n   소스별 분포:")
    for source, count in ifc_sources.most_common():
        print(f"     - {source}: {count}개")
    
    # BCF 파일 분석
    bcf_raw_files = list(RAW_DIR.glob("*.bcf*"))
    bcf_processed_files = list(PROCESSED_DIR.glob("*_bcf.jsonl"))
    
    print(f"\n📋 BCF 파일:")
    print(f"   원본 파일: {len(bcf_raw_files)}개")
    print(f"   처리된 파일: {len(bcf_processed_files)}개")
    
    # BCF 이슈 상세 분석
    total_issues = 0
    issues_by_type = Counter()
    issues_by_status = Counter()
    issues_by_priority = Counter()
    authors = set()
    
    for bcf_file in bcf_processed_files:
        try:
            with bcf_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    issue = json.loads(line)
                    total_issues += 1
                    
                    # 이슈 타입
                    topic_type = issue.get("topic_type", "Unknown")
                    issues_by_type[topic_type] += 1
                    
                    # 이슈 상태
                    status = issue.get("topic_status", "Unknown")
                    issues_by_status[status] += 1
                    
                    # 우선순위
                    priority = issue.get("priority", "Unknown")
                    issues_by_priority[priority] += 1
                    
                    # 작성자
                    author = issue.get("creation_author")
                    if author:
                        authors.add(author)
        except Exception as e:
            print(f"     ⚠️  오류 ({bcf_file.name}): {e}")
    
    print(f"\n   총 이슈 수: {total_issues}개")
    print(f"   평균 이슈/파일: {total_issues/len(bcf_processed_files):.1f}개")
    print(f"   작성자 수: {len(authors)}명")
    
    print(f"\n   이슈 타입 (Top 5):")
    for issue_type, count in issues_by_type.most_common(5):
        print(f"     - {issue_type}: {count}개")
    
    print(f"\n   이슈 상태:")
    for status, count in issues_by_status.most_common():
        print(f"     - {status}: {count}개 ({count/total_issues*100:.1f}%)")
    
    # 데이터 품질 검증
    print(f"\n" + "="*60)
    print("✅ 데이터 품질 검증")
    print("="*60)
    
    quality_checks = {
        "IFC 파일 존재": len(ifc_files) > 0,
        "BCF 파일 존재": len(bcf_raw_files) > 0,
        "BCF 처리 성공": len(bcf_processed_files) > 0,
        "충분한 이슈 수 (>100)": total_issues > 100,
        "다양한 이슈 타입": len(issues_by_type) > 3,
        "다양한 소스": len(ifc_sources) > 1,
    }
    
    for check, passed in quality_checks.items():
        icon = "✅" if passed else "❌"
        print(f"   {icon} {check}")
    
    # 이전 대비 증가량
    print(f"\n" + "="*60)
    print("📈 이전 대비 증가량")
    print("="*60)
    
    # 간단한 비교 (이전 데이터 가정)
    previous_ifc = 123  # 이전 보고서 기준
    previous_bcf = 61   # 이전 보고서 기준
    previous_issues = 322  # 이전 보고서 기준
    
    print(f"   IFC 파일: {previous_ifc}개 → {len(ifc_files)}개 (+{len(ifc_files)-previous_ifc}개)")
    print(f"   BCF 파일: {previous_bcf}개 → {len(bcf_raw_files)}개 (+{len(bcf_raw_files)-previous_bcf}개)")
    print(f"   BCF 이슈: {previous_issues}개 → {total_issues}개 (+{total_issues-previous_issues}개)")
    
    if total_issues > previous_issues:
        increase_pct = ((total_issues - previous_issues) / previous_issues * 100)
        print(f"   📊 이슈 증가율: +{increase_pct:.1f}%")
    
    # 연구 목표 달성 여부
    print(f"\n" + "="*60)
    print("🎯 연구 목표 달성 평가")
    print("="*60)
    
    goals = {
        "RQ1: 충분한 IFC 다양성 (>100)": len(ifc_files) > 100,
        "RQ2: 충분한 이슈 수 (>200)": total_issues > 200,
        "RQ3: 다양한 이슈 타입 (>5)": len(issues_by_type) > 5,
        "신뢰할 수 있는 소스": "buildingSMART" in ifc_sources,
    }
    
    for goal, achieved in goals.items():
        icon = "✅" if achieved else "⚠️ "
        print(f"   {icon} {goal}")
    
    # 결과 저장
    result = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 1",
        "ifc": {
            "count": len(ifc_files),
            "size_mb": round(ifc_total_size / 1024 / 1024, 2),
            "sources": dict(ifc_sources)
        },
        "bcf": {
            "raw_count": len(bcf_raw_files),
            "processed_count": len(bcf_processed_files),
            "total_issues": total_issues,
            "avg_issues_per_file": round(total_issues / len(bcf_processed_files), 1),
            "issue_types": dict(issues_by_type.most_common(10)),
            "issue_statuses": dict(issues_by_status),
            "unique_authors": len(authors)
        },
        "quality_checks": {k: "PASS" if v else "FAIL" for k, v in quality_checks.items()},
        "goals": {k: "ACHIEVED" if v else "PENDING" for k, v in goals.items()}
    }
    
    # 결과 저장
    output_file = DATA_DIR / "analysis" / "phase1_validation.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 검증 결과 저장: {output_file}")
    
    return result


def main():
    """메인 실행"""
    result = analyze_phase1_data()
    
    print(f"\n" + "="*60)
    print("✅ Phase 1 데이터 검증 완료!")
    print("="*60)
    
    # 전체 품질 점수
    passed_checks = sum(1 for v in result["quality_checks"].values() if v == "PASS")
    total_checks = len(result["quality_checks"])
    quality_score = (passed_checks / total_checks) * 100
    
    print(f"\n품질 점수: {quality_score:.0f}/100")
    print(f"통과: {passed_checks}/{total_checks} 검증 항목")
    
    if quality_score >= 80:
        print("\n🎉 데이터 품질이 우수합니다! 연구 진행 가능합니다.")
    elif quality_score >= 60:
        print("\n✅ 데이터 품질이 양호합니다. 일부 보완이 필요할 수 있습니다.")
    else:
        print("\n⚠️  데이터 품질 개선이 필요합니다.")


if __name__ == "__main__":
    main()

