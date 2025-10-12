#!/usr/bin/env python3
"""데이터 신뢰성 및 품질 검증 스크립트"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import hashlib


class DataCredibilityValidator:
    """데이터 신뢰성 검증기"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "data" / "raw" / "downloaded"
        self.data_dir = self.base_dir / "data"
        self.analysis_dir = self.base_dir / "data" / "analysis"
        
        self.validation_report = {
            "timestamp": datetime.now().isoformat(),
            "data_sources": {},
            "quality_metrics": {},
            "credibility_score": 0,
            "issues": [],
            "recommendations": []
        }
    
    def classify_data_sources(self):
        """데이터 출처 분류"""
        print("=" * 70)
        print("📋 데이터 출처 분류 및 신뢰도 평가")
        print("=" * 70)
        
        # IFC 파일 분류
        ifc_files = list(self.raw_dir.glob("*.ifc")) + list(self.data_dir.glob("*.ifc"))
        
        sources = {
            "buildingsmart": {"files": [], "credibility": "HIGH", "description": "Official buildingSMART samples"},
            "ifcopenshell": {"files": [], "credibility": "MEDIUM", "description": "IFC engine test files"},
            "xbim": {"files": [], "credibility": "MEDIUM", "description": "xBIM sample files"},
            "bimserver": {"files": [], "credibility": "MEDIUM", "description": "BIMserver samples"},
            "synthetic": {"files": [], "credibility": "LOW", "description": "Synthetically generated"},
            "unknown": {"files": [], "credibility": "UNKNOWN", "description": "Unknown source"}
        }
        
        for ifc_file in ifc_files:
            name = ifc_file.name.lower()
            classified = False
            
            if "buildingsmart" in name:
                sources["buildingsmart"]["files"].append(str(ifc_file))
                classified = True
            elif "ifcopenshell" in name:
                sources["ifcopenshell"]["files"].append(str(ifc_file))
                classified = True
            elif "xbim" in name:
                sources["xbim"]["files"].append(str(ifc_file))
                classified = True
            elif "bimserver" in name:
                sources["bimserver"]["files"].append(str(ifc_file))
                classified = True
            elif any(x in name for x in ["residential", "office", "industrial", "hospital", "school"]):
                sources["synthetic"]["files"].append(str(ifc_file))
                classified = True
            
            if not classified:
                sources["unknown"]["files"].append(str(ifc_file))
        
        # BCF 파일 분류
        bcf_files = list(self.raw_dir.glob("*.bcf*")) + list((self.data_dir / "raw").glob("*.bcf*"))
        
        bcf_sources = {
            "buildingsmart": [],
            "synthetic": []
        }
        
        for bcf_file in bcf_files:
            name = bcf_file.name.lower()
            if "buildingsmart" in name or "sample.bcf" in name:
                bcf_sources["buildingsmart"].append(str(bcf_file))
            else:
                bcf_sources["synthetic"].append(str(bcf_file))
        
        # 통계 출력
        print(f"\n📐 **IFC 파일 출처 분포**:")
        total_ifc = 0
        for source, data in sources.items():
            count = len(data["files"])
            total_ifc += count
            if count > 0:
                print(f"  {source.upper():15s}: {count:3d}개 - 신뢰도: {data['credibility']:7s} - {data['description']}")
        
        print(f"\n📋 **BCF 파일 출처 분포**:")
        for source, files in bcf_sources.items():
            count = len(files)
            cred = "HIGH" if source == "buildingsmart" else "LOW"
            print(f"  {source.upper():15s}: {count:3d}개 - 신뢰도: {cred}")
        
        # 저장
        self.validation_report["data_sources"] = {
            "ifc": sources,
            "bcf": bcf_sources,
            "ifc_total": total_ifc,
            "bcf_total": len(bcf_files)
        }
        
        # 신뢰도 이슈 체크
        if sources["synthetic"]["files"]:
            self.validation_report["issues"].append({
                "severity": "HIGH",
                "category": "data_source",
                "message": f"{len(sources['synthetic']['files'])} synthetic IFC files require validation",
                "impact": "Paper reviewers may question data authenticity"
            })
        
        if len(bcf_sources["synthetic"]) > len(bcf_sources["buildingsmart"]):
            self.validation_report["issues"].append({
                "severity": "CRITICAL",
                "category": "data_source",
                "message": f"{len(bcf_sources['synthetic'])} synthetic BCF files (vs {len(bcf_sources['buildingsmart'])} real)",
                "impact": "Major concern for paper acceptance"
            })
        
        return sources, bcf_sources
    
    def measure_data_quality(self):
        """데이터 품질 측정"""
        print("\n" + "=" * 70)
        print("🔍 데이터 품질 측정")
        print("=" * 70)
        
        metrics = {
            "ifc_files_checked": 0,
            "ifc_valid": 0,
            "ifc_invalid": 0,
            "bcf_files_checked": 0,
            "bcf_valid": 0,
            "bcf_invalid": 0,
            "duplicates": 0
        }
        
        # IFC 파일 기본 검증
        ifc_files = list(self.raw_dir.glob("*.ifc")) + list(self.data_dir.glob("*.ifc"))
        file_hashes = set()
        
        print(f"\n📐 IFC 파일 검증 중...")
        for ifc_file in ifc_files:
            metrics["ifc_files_checked"] += 1
            
            # 기본 유효성: 파일 읽기 가능 + "IFC" 헤더
            try:
                with open(ifc_file, 'r', encoding='utf-8', errors='ignore') as f:
                    first_line = f.readline()
                    if "ISO-10303-21" in first_line or "IFC" in first_line:
                        metrics["ifc_valid"] += 1
                    else:
                        metrics["ifc_invalid"] += 1
                
                # 중복 체크 (해시)
                with open(ifc_file, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    if file_hash in file_hashes:
                        metrics["duplicates"] += 1
                    file_hashes.add(file_hash)
                
            except Exception as e:
                metrics["ifc_invalid"] += 1
                print(f"  ❌ {ifc_file.name}: {e}")
        
        print(f"  ✅ 유효: {metrics['ifc_valid']}/{metrics['ifc_files_checked']}")
        print(f"  ❌ 무효: {metrics['ifc_invalid']}/{metrics['ifc_files_checked']}")
        print(f"  🔁 중복: {metrics['duplicates']}")
        
        # BCF 파일 검증
        bcf_files = list(self.raw_dir.glob("*.bcf*")) + list((self.data_dir / "raw").glob("*.bcf*"))
        
        print(f"\n📋 BCF 파일 검증 중...")
        for bcf_file in bcf_files:
            metrics["bcf_files_checked"] += 1
            
            # 기본 유효성: ZIP 파일 읽기 가능
            try:
                import zipfile
                with zipfile.ZipFile(bcf_file, 'r') as z:
                    if "bcf.version" in z.namelist():
                        metrics["bcf_valid"] += 1
                    else:
                        metrics["bcf_invalid"] += 1
            except Exception as e:
                metrics["bcf_invalid"] += 1
                print(f"  ❌ {bcf_file.name}: {e}")
        
        print(f"  ✅ 유효: {metrics['bcf_valid']}/{metrics['bcf_files_checked']}")
        print(f"  ❌ 무효: {metrics['bcf_invalid']}/{metrics['bcf_files_checked']}")
        
        self.validation_report["quality_metrics"] = metrics
        
        # 품질 이슈 체크
        if metrics["ifc_invalid"] > 0:
            self.validation_report["issues"].append({
                "severity": "MEDIUM",
                "category": "data_quality",
                "message": f"{metrics['ifc_invalid']} invalid IFC files detected",
                "impact": "Data quality concerns"
            })
        
        if metrics["duplicates"] > 10:
            self.validation_report["issues"].append({
                "severity": "LOW",
                "category": "data_quality",
                "message": f"{metrics['duplicates']} duplicate files found",
                "impact": "Inflated data count"
            })
        
        return metrics
    
    def calculate_credibility_score(self):
        """신뢰도 점수 계산"""
        print("\n" + "=" * 70)
        print("📊 신뢰도 점수 계산")
        print("=" * 70)
        
        score = 100
        
        sources = self.validation_report["data_sources"]
        
        # IFC 출처별 가중치
        ifc_sources = sources["ifc"]
        total_ifc = sources["ifc_total"]
        
        if total_ifc > 0:
            buildingsmart_ratio = len(ifc_sources["buildingsmart"]["files"]) / total_ifc
            synthetic_ratio = len(ifc_sources["synthetic"]["files"]) / total_ifc
            
            # buildingSMART 많을수록 +점수
            score += buildingsmart_ratio * 20
            
            # 합성 데이터 많을수록 -점수
            score -= synthetic_ratio * 30
        
        # BCF 출처별 가중치
        bcf_sources = sources["bcf"]
        total_bcf = sources["bcf_total"]
        
        if total_bcf > 0:
            synthetic_bcf_ratio = len(bcf_sources["synthetic"]) / total_bcf
            
            # 합성 BCF 많을수록 큰 감점
            score -= synthetic_bcf_ratio * 40
        
        # 품질 메트릭
        metrics = self.validation_report["quality_metrics"]
        if metrics["ifc_files_checked"] > 0:
            valid_ratio = metrics["ifc_valid"] / metrics["ifc_files_checked"]
            score *= valid_ratio
        
        # 이슈별 감점
        for issue in self.validation_report["issues"]:
            if issue["severity"] == "CRITICAL":
                score -= 20
            elif issue["severity"] == "HIGH":
                score -= 10
            elif issue["severity"] == "MEDIUM":
                score -= 5
        
        # 0-100 범위로 제한
        score = max(0, min(100, score))
        
        self.validation_report["credibility_score"] = round(score, 1)
        
        # 등급
        if score >= 80:
            grade = "✅ HIGH - Top-tier conference ready"
        elif score >= 60:
            grade = "🟡 MEDIUM - Revision needed"
        elif score >= 40:
            grade = "🟠 LOW - Major revision required"
        else:
            grade = "🔴 CRITICAL - Data collection restart recommended"
        
        print(f"\n🎯 **최종 신뢰도 점수**: {score:.1f}/100")
        print(f"📈 **등급**: {grade}")
        
        return score, grade
    
    def generate_recommendations(self):
        """개선 권장사항 생성"""
        print("\n" + "=" * 70)
        print("💡 개선 권장사항")
        print("=" * 70)
        
        recommendations = []
        score = self.validation_report["credibility_score"]
        
        # 점수별 권장사항
        if score < 60:
            recommendations.append({
                "priority": "CRITICAL",
                "action": "Reduce synthetic data proportion",
                "details": "Replace synthetic BCF files with real project data or academic datasets",
                "timeline": "2-4 weeks"
            })
        
        if score < 80:
            recommendations.append({
                "priority": "HIGH",
                "action": "Expert validation of synthetic data",
                "details": "Have 2-3 BIM domain experts review and validate synthetic BCF issues",
                "timeline": "1 week"
            })
        
        # 합성 데이터 관련
        sources = self.validation_report["data_sources"]
        if len(sources["bcf"]["synthetic"]) > 30:
            recommendations.append({
                "priority": "HIGH",
                "action": "Document synthetic data generation",
                "details": "Write detailed methodology section explaining BCF generation process",
                "timeline": "3 days"
            })
            
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Fix random seed for reproducibility",
                "details": "Regenerate all synthetic data with fixed seed values",
                "timeline": "1 day"
            })
        
        # Ground truth
        recommendations.append({
            "priority": "HIGH",
            "action": "Create gold standard QA dataset",
            "details": "Generate 50-100 question-answer pairs with expert validation",
            "timeline": "1-2 weeks"
        })
        
        # 실제 데이터 확보
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Apply for academic datasets",
            "details": "Submit data access requests to BIMPROVE, TU Delft, Stanford repositories",
            "timeline": "2-4 weeks"
        })
        
        # Limitation 섹션
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Write limitations section",
            "details": "Clearly state data sources, synthetic data rationale, and generalizability",
            "timeline": "2 days"
        })
        
        # 출력
        print()
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟡",
                "MEDIUM": "🟠",
                "LOW": "🟢"
            }
            emoji = priority_emoji.get(rec["priority"], "⚪")
            
            print(f"{emoji} {i}. [{rec['priority']}] {rec['action']}")
            print(f"   설명: {rec['details']}")
            print(f"   예상 소요: {rec['timeline']}")
            print()
        
        self.validation_report["recommendations"] = recommendations
        
        return recommendations
    
    def save_report(self):
        """검증 보고서 저장"""
        report_path = self.analysis_dir / "credibility_validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.validation_report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 검증 보고서 저장: {report_path}")
        
        # Markdown 요약
        md_path = self.analysis_dir / "CREDIBILITY_REPORT.md"
        score = self.validation_report["credibility_score"]
        
        with open(md_path, 'w') as f:
            f.write(f"""# 데이터 신뢰성 검증 보고서

생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 최종 신뢰도 점수: {score}/100

""")
            
            if score >= 80:
                f.write("**등급**: ✅ HIGH - Top-tier 학회 준비 완료\n\n")
            elif score >= 60:
                f.write("**등급**: 🟡 MEDIUM - 보완 작업 필요\n\n")
            elif score >= 40:
                f.write("**등급**: 🟠 LOW - 주요 보완 필요\n\n")
            else:
                f.write("**등급**: 🔴 CRITICAL - 데이터 재수집 권장\n\n")
            
            # 이슈
            if self.validation_report["issues"]:
                f.write("## ⚠️ 발견된 이슈\n\n")
                for issue in self.validation_report["issues"]:
                    f.write(f"- **[{issue['severity']}]** {issue['message']}\n")
                    f.write(f"  - 영향: {issue['impact']}\n\n")
            
            # 권장사항
            f.write("## 💡 권장 조치사항\n\n")
            for i, rec in enumerate(self.validation_report["recommendations"], 1):
                f.write(f"{i}. **[{rec['priority']}]** {rec['action']}\n")
                f.write(f"   - {rec['details']}\n")
                f.write(f"   - 예상 소요: {rec['timeline']}\n\n")
        
        print(f"✅ Markdown 요약 저장: {md_path}")
        
        return report_path


def main():
    base_dir = Path(__file__).parent.parent
    validator = DataCredibilityValidator(base_dir)
    
    print("🔬 ContextualForget 데이터 신뢰성 검증")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 데이터 출처 분류
    sources, bcf_sources = validator.classify_data_sources()
    
    # 2. 데이터 품질 측정
    metrics = validator.measure_data_quality()
    
    # 3. 신뢰도 점수 계산
    score, grade = validator.calculate_credibility_score()
    
    # 4. 권장사항 생성
    recommendations = validator.generate_recommendations()
    
    # 5. 보고서 저장
    validator.save_report()
    
    # 최종 요약
    print("\n" + "=" * 70)
    print("📝 최종 요약")
    print("=" * 70)
    print(f"""
🎯 신뢰도 점수: {score}/100
📈 등급: {grade}
⚠️  발견된 이슈: {len(validator.validation_report['issues'])}개
💡 권장 조치: {len(recommendations)}개

상세 보고서:
  - data/analysis/credibility_validation_report.json
  - data/analysis/CREDIBILITY_REPORT.md
  - docs/DATA_CREDIBILITY_ASSESSMENT.md
""")
    
    # 종료 코드
    if score >= 60:
        print("✅ 논문 진행 가능 (보완 작업 병행)")
        return 0
    else:
        print("⚠️  데이터 신뢰성 보강 후 진행 권장")
        return 1


if __name__ == "__main__":
    sys.exit(main())

