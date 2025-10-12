#!/usr/bin/env python3
"""수집된 데이터 분석 및 분류"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import random
import shutil
import pickle


class DataAnalyzer:
    """데이터 분석 및 분류"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "data" / "raw" / "downloaded"
        self.analysis_dir = self.base_dir / "data" / "analysis"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        self.ifc_files = []
        self.bcf_files = []
    
    def scan_all_data(self):
        """모든 데이터 스캔"""
        print("=" * 70)
        print("🔍 전체 데이터 스캔")
        print("=" * 70)
        
        # Raw 디렉토리
        raw_ifc = list(self.raw_dir.glob("*.ifc"))
        raw_bcf = list(self.raw_dir.glob("*.bcf*"))
        
        # 기존 data 디렉토리
        data_dir = self.base_dir / "data"
        existing_ifc = list(data_dir.glob("*.ifc"))
        existing_bcf = list((data_dir / "raw").glob("*.bcfzip"))
        
        # 합치기
        self.ifc_files = raw_ifc + existing_ifc
        self.bcf_files = raw_bcf + existing_bcf
        
        print(f"\n📐 IFC 파일: {len(self.ifc_files)}개")
        print(f"📋 BCF 파일: {len(self.bcf_files)}개")
        print(f"📊 총 파일: {len(self.ifc_files) + len(self.bcf_files)}개")
    
    def analyze_ifc_files(self):
        """IFC 파일 상세 분석"""
        print("\n" + "=" * 70)
        print("📊 IFC 파일 상세 분석")
        print("=" * 70)
        
        analysis = {
            "total_count": len(self.ifc_files),
            "total_size_mb": 0,
            "size_categories": {
                "small": [],  # < 100 KB
                "medium": [],  # 100 KB ~ 1 MB
                "large": [],  # 1 MB ~ 10 MB
                "xlarge": []  # > 10 MB
            },
            "complexity_estimate": {},
            "files": []
        }
        
        for ifc_file in self.ifc_files:
            size_kb = ifc_file.stat().st_size / 1024
            size_mb = size_kb / 1024
            analysis["total_size_mb"] += size_mb
            
            # 크기 분류
            if size_kb < 100:
                category = "small"
            elif size_kb < 1024:
                category = "medium"
            elif size_mb < 10:
                category = "large"
            else:
                category = "xlarge"
            
            analysis["size_categories"][category].append(ifc_file.name)
            
            # 복잡도 추정 (파일 크기 기반)
            if size_kb < 50:
                complexity = "simple"
            elif size_kb < 500:
                complexity = "moderate"
            elif size_mb < 5:
                complexity = "complex"
            else:
                complexity = "very_complex"
            
            file_info = {
                "name": ifc_file.name,
                "path": str(ifc_file),
                "size_kb": round(size_kb, 2),
                "size_mb": round(size_mb, 2),
                "category": category,
                "complexity": complexity
            }
            
            analysis["files"].append(file_info)
        
        # 통계
        for cat, files in analysis["size_categories"].items():
            print(f"\n  {cat.upper()}: {len(files)}개")
            if files:
                for f in files[:3]:  # 처음 3개만
                    print(f"    - {f}")
                if len(files) > 3:
                    print(f"    ... (+{len(files) - 3}개)")
        
        # 복잡도 통계
        complexity_counts = {}
        for f in analysis["files"]:
            comp = f["complexity"]
            complexity_counts[comp] = complexity_counts.get(comp, 0) + 1
        
        print(f"\n  복잡도 분포:")
        for comp, count in complexity_counts.items():
            print(f"    - {comp}: {count}개")
        
        # 저장
        with open(self.analysis_dir / "ifc_analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        return analysis
    
    def analyze_bcf_files(self):
        """BCF 파일 분석"""
        print("\n" + "=" * 70)
        print("📊 BCF 파일 분석")
        print("=" * 70)
        
        analysis = {
            "total_count": len(self.bcf_files),
            "total_size_mb": sum(f.stat().st_size for f in self.bcf_files) / 1024 / 1024,
            "files": []
        }
        
        for bcf_file in self.bcf_files:
            size_kb = bcf_file.stat().st_size / 1024
            
            file_info = {
                "name": bcf_file.name,
                "path": str(bcf_file),
                "size_kb": round(size_kb, 2)
            }
            
            analysis["files"].append(file_info)
            print(f"  - {bcf_file.name} ({size_kb:.1f} KB)")
        
        # 저장
        with open(self.analysis_dir / "bcf_analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        return analysis
    
    def classify_for_research(self, ifc_analysis):
        """연구 목적별 분류"""
        print("\n" + "=" * 70)
        print("🏷️  연구 목적별 데이터 분류")
        print("=" * 70)
        
        # 훈련/검증/테스트 분할 (70/15/15)
        all_files = ifc_analysis["files"]
        random.shuffle(all_files)
        
        total = len(all_files)
        train_size = int(total * 0.70)
        val_size = int(total * 0.15)
        
        classification = {
            "train": all_files[:train_size],
            "validation": all_files[train_size:train_size + val_size],
            "test": all_files[train_size + val_size:],
            "statistics": {
                "total": total,
                "train": train_size,
                "validation": val_size,
                "test": total - train_size - val_size
            }
        }
        
        print(f"\n  📊 데이터 분할:")
        print(f"    - 훈련 (Train): {classification['statistics']['train']}개 (70%)")
        print(f"    - 검증 (Validation): {classification['statistics']['validation']}개 (15%)")
        print(f"    - 테스트 (Test): {classification['statistics']['test']}개 (15%)")
        
        # 복잡도별 분포 확인
        for split_name, split_data in [("train", classification["train"]), 
                                       ("validation", classification["validation"]),
                                       ("test", classification["test"])]:
            complexity_dist = {}
            for f in split_data:
                comp = f["complexity"]
                complexity_dist[comp] = complexity_dist.get(comp, 0) + 1
            
            print(f"\n  {split_name.upper()} 복잡도 분포:")
            for comp, count in sorted(complexity_dist.items()):
                print(f"    - {comp}: {count}개")
        
        # 저장
        with open(self.analysis_dir / "data_classification.json", 'w') as f:
            json.dump(classification, f, indent=2, ensure_ascii=False)
        
        return classification
    
    def assess_sufficiency(self, ifc_analysis, bcf_analysis):
        """데이터 충분성 평가"""
        print("\n" + "=" * 70)
        print("✅ 데이터 충분성 평가")
        print("=" * 70)
        
        # 기준
        requirements = {
            "minimum": {
                "ifc_count": 15,
                "bcf_count": 30,
                "total_ifc_size_mb": 10,
                "complexity_diversity": 3  # simple, moderate, complex
            },
            "ideal": {
                "ifc_count": 25,
                "bcf_count": 50,
                "total_ifc_size_mb": 50,
                "complexity_diversity": 4  # + very_complex
            }
        }
        
        # 현재 상태
        current = {
            "ifc_count": ifc_analysis["total_count"],
            "bcf_count": bcf_analysis["total_count"],
            "total_ifc_size_mb": ifc_analysis["total_size_mb"],
            "complexity_diversity": len(set(f["complexity"] for f in ifc_analysis["files"]))
        }
        
        # 평가
        assessment = {
            "current": current,
            "requirements": requirements,
            "status": {}
        }
        
        print(f"\n  📊 현재 상태:")
        print(f"    IFC 파일: {current['ifc_count']}개 (목표: 최소 {requirements['minimum']['ifc_count']}개, 이상적 {requirements['ideal']['ifc_count']}개)")
        print(f"    BCF 파일: {current['bcf_count']}개 (목표: 최소 {requirements['minimum']['bcf_count']}개, 이상적 {requirements['ideal']['bcf_count']}개)")
        print(f"    총 크기: {current['total_ifc_size_mb']:.2f} MB")
        print(f"    복잡도 다양성: {current['complexity_diversity']}종류")
        
        # 최소 요구사항 충족 여부
        min_req_met = (
            current["ifc_count"] >= requirements["minimum"]["ifc_count"] and
            current["bcf_count"] >= requirements["minimum"]["bcf_count"]
        )
        
        # 이상적 요구사항 충족 여부
        ideal_req_met = (
            current["ifc_count"] >= requirements["ideal"]["ifc_count"] and
            current["bcf_count"] >= requirements["ideal"]["bcf_count"]
        )
        
        if ideal_req_met:
            status = "✅ IDEAL - Top-tier 학회 목표 가능"
            score = 100
        elif min_req_met:
            status = "✅ SUFFICIENT - 학술 논문 발표 가능"
            score = 80
        else:
            status = "⚠️  INSUFFICIENT - 추가 데이터 필요"
            score = 50
        
        assessment["status"] = {
            "level": status,
            "score": score,
            "minimum_met": min_req_met,
            "ideal_met": ideal_req_met
        }
        
        print(f"\n  🎯 평가 결과: {status}")
        print(f"  📈 점수: {score}/100")
        
        # 권장사항
        if not ideal_req_met:
            needed_ifc = max(0, requirements["ideal"]["ifc_count"] - current["ifc_count"])
            needed_bcf = max(0, requirements["ideal"]["bcf_count"] - current["bcf_count"])
            
            print(f"\n  💡 권장사항:")
            if needed_ifc > 0:
                print(f"    - IFC 파일 {needed_ifc}개 추가 수집")
            if needed_bcf > 0:
                print(f"    - BCF 파일 {needed_bcf}개 추가 생성/수집")
        
        # 저장
        with open(self.analysis_dir / "sufficiency_assessment.json", 'w') as f:
            json.dump(assessment, f, indent=2, ensure_ascii=False)
        
        return assessment
    
    def generate_comprehensive_report(self, ifc_analysis, bcf_analysis, classification, assessment):
        """종합 보고서 생성"""
        print("\n" + "=" * 70)
        print("📝 종합 데이터 보고서 생성")
        print("=" * 70)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_ifc": ifc_analysis["total_count"],
                "total_bcf": bcf_analysis["total_count"],
                "total_size_mb": ifc_analysis["total_size_mb"] + bcf_analysis["total_size_mb"],
                "sufficiency_score": assessment["status"]["score"],
                "sufficiency_level": assessment["status"]["level"]
            },
            "ifc_breakdown": {
                "size_distribution": {
                    k: len(v) for k, v in ifc_analysis["size_categories"].items()
                },
                "complexity_distribution": {}
            },
            "data_splits": classification["statistics"],
            "next_steps": []
        }
        
        # 복잡도 분포
        for f in ifc_analysis["files"]:
            comp = f["complexity"]
            report["ifc_breakdown"]["complexity_distribution"][comp] = \
                report["ifc_breakdown"]["complexity_distribution"].get(comp, 0) + 1
        
        # 다음 단계
        if assessment["status"]["ideal_met"]:
            report["next_steps"] = [
                "✅ 데이터 충분 - Phase 1 시작 가능",
                "시간적 다양성 추가 (3-12개월 분산)",
                "Gold Standard QA 데이터셋 생성"
            ]
        elif assessment["status"]["minimum_met"]:
            report["next_steps"] = [
                "✅ 최소 요구사항 충족",
                "추가 데이터 수집 (이상적 수준)",
                "시간적 다양성 추가",
                "Phase 1 시작 가능 (단, 추가 수집 병행)"
            ]
        else:
            report["next_steps"] = [
                "⚠️  추가 데이터 수집 필수",
                "BCF 파일 생성 스크립트 실행",
                "Academic 데이터셋 신청",
                "Phase 1 시작 전 데이터 보강"
            ]
        
        # 파일로 저장
        report_path = self.analysis_dir / "comprehensive_data_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 마크다운 보고서
        md_path = self.analysis_dir / "DATA_REPORT.md"
        with open(md_path, 'w') as f:
            f.write(f"""# ContextualForget 데이터 수집 보고서

생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 데이터 요약

- **총 IFC 파일**: {report['summary']['total_ifc']}개
- **총 BCF 파일**: {report['summary']['total_bcf']}개
- **총 크기**: {report['summary']['total_size_mb']:.2f} MB
- **충분성 점수**: {report['summary']['sufficiency_score']}/100
- **평가**: {report['summary']['sufficiency_level']}

## 📐 IFC 파일 분포

### 크기별
- Small (< 100 KB): {report['ifc_breakdown']['size_distribution']['small']}개
- Medium (100 KB ~ 1 MB): {report['ifc_breakdown']['size_distribution']['medium']}개
- Large (1 ~ 10 MB): {report['ifc_breakdown']['size_distribution']['large']}개
- XLarge (> 10 MB): {report['ifc_breakdown']['size_distribution']['xlarge']}개

### 복잡도별
""")
            for comp, count in report['ifc_breakdown']['complexity_distribution'].items():
                f.write(f"- {comp}: {count}개\n")
            
            f.write(f"""

## 📋 데이터 분할

- **훈련 (Train)**: {report['data_splits']['train']}개 (70%)
- **검증 (Validation)**: {report['data_splits']['validation']}개 (15%)
- **테스트 (Test)**: {report['data_splits']['test']}개 (15%)

## 🎯 다음 단계

""")
            for step in report['next_steps']:
                f.write(f"{step}\n")
        
        print(f"\n  ✅ JSON 보고서: {report_path}")
        print(f"  ✅ Markdown 보고서: {md_path}")
        
        return report


def main():
    base_dir = Path(__file__).parent.parent
    analyzer = DataAnalyzer(base_dir)
    
    print("🔬 ContextualForget 데이터 분석 & 분류")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 스캔
    analyzer.scan_all_data()
    
    # 2. IFC 분석
    ifc_analysis = analyzer.analyze_ifc_files()
    
    # 3. BCF 분석
    bcf_analysis = analyzer.analyze_bcf_files()
    
    # 4. 연구 목적별 분류
    classification = analyzer.classify_for_research(ifc_analysis)
    
    # 5. 충분성 평가
    assessment = analyzer.assess_sufficiency(ifc_analysis, bcf_analysis)
    
    # 6. 종합 보고서
    report = analyzer.generate_comprehensive_report(
        ifc_analysis, bcf_analysis, classification, assessment
    )
    
    print("\n" + "=" * 70)
    print("✨ 데이터 분석 및 분류 완료!")
    print("=" * 70)
    print(f"\n📊 결과 파일:")
    print(f"  - data/analysis/ifc_analysis.json")
    print(f"  - data/analysis/bcf_analysis.json")
    print(f"  - data/analysis/data_classification.json")
    print(f"  - data/analysis/sufficiency_assessment.json")
    print(f"  - data/analysis/comprehensive_data_report.json")
    print(f"  - data/analysis/DATA_REPORT.md")


if __name__ == "__main__":
    main()

