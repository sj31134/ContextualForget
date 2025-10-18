#!/usr/bin/env python3
"""
학술 데이터셋 검증 스크립트
작성일: 2025-10-15
용도: 다운로드된 학술 데이터셋의 무결성 및 형식 검증
"""

import json
import zipfile
import os
from pathlib import Path
from typing import Dict, List, Tuple
import sys

PROJECT_ROOT = Path(__file__).parent.parent
ACADEMIC_DIR = PROJECT_ROOT / "data" / "external" / "academic"

class AcademicDataValidator:
    """학술 데이터셋 검증 클래스"""
    
    def __init__(self):
        self.slabim_dir = ACADEMIC_DIR / "slabim"
        self.duraark_dir = ACADEMIC_DIR / "duraark"
        self.schependomlaan_dir = ACADEMIC_DIR / "schependomlaan"
        self.results = {
            "slabim": {},
            "duraark": {},
            "schependomlaan": {},
            "summary": {},
            "errors": [],
            "warnings": []
        }
    
    def validate_slabim_data(self) -> Dict:
        """SLABIM 데이터 검증"""
        print("🔍 SLABIM 데이터 검증 중...")
        
        if not self.slabim_dir.exists():
            self.results["errors"].append(
                f"SLABIM 데이터 디렉토리 없음: {self.slabim_dir}"
            )
            return {"status": "not_found", "count": 0}
        
        # SLAM 스캔 데이터 확인
        slam_files = list(self.slabim_dir.rglob("*.ply")) + list(self.slabim_dir.rglob("*.pcd"))
        print(f"  ✅ SLAM 스캔 파일: {len(slam_files)}개")
        
        # BIM 모델 확인
        bim_files = list(self.slabim_dir.rglob("*.ifc")) + list(self.slabim_dir.rglob("*.fbx"))
        print(f"  ✅ BIM 모델 파일: {len(bim_files)}개")
        
        # 시간적 데이터 확인
        temporal_files = list(self.slabim_dir.rglob("*.json")) + list(self.slabim_dir.rglob("*.csv"))
        print(f"  ✅ 시간적 데이터: {len(temporal_files)}개")
        
        # 총 크기
        total_size = sum(f.stat().st_size for f in self.slabim_dir.rglob("*") if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        print(f"  ✅ 총 크기: {total_size_mb:.2f} MB")
        
        result = {
            "status": "ok" if len(slam_files) > 0 or len(bim_files) > 0 else "warning",
            "slam_count": len(slam_files),
            "bim_count": len(bim_files),
            "temporal_count": len(temporal_files),
            "total_size_mb": total_size_mb
        }
        
        self.results["slabim"] = result
        return result
    
    def validate_duraark_data(self) -> Dict:
        """DURAARK 데이터 검증"""
        print("\n🔍 DURAARK 데이터 검증 중...")
        
        if not self.duraark_dir.exists():
            self.results["errors"].append(
                f"DURAARK 데이터 디렉토리 없음: {self.duraark_dir}"
            )
            return {"status": "not_found", "count": 0}
        
        # IFC 파일 확인
        ifc_files = list(self.duraark_dir.rglob("*.ifc"))
        print(f"  ✅ IFC 파일: {len(ifc_files)}개")
        
        # 분야별 분류 확인
        disciplines = {}
        for ifc_file in ifc_files:
            # 파일명에서 분야 추출 (예: structural, architectural, mep)
            filename = ifc_file.name.lower()
            if "structural" in filename or "structure" in filename:
                disciplines["structural"] = disciplines.get("structural", 0) + 1
            elif "architectural" in filename or "arch" in filename:
                disciplines["architectural"] = disciplines.get("architectural", 0) + 1
            elif "mep" in filename or "mechanical" in filename or "electrical" in filename:
                disciplines["mep"] = disciplines.get("mep", 0) + 1
            else:
                disciplines["other"] = disciplines.get("other", 0) + 1
        
        print(f"  ✅ 분야별 분포: {disciplines}")
        
        # 프로젝트 문서 확인
        doc_files = list(self.duraark_dir.rglob("*.pdf")) + list(self.duraark_dir.rglob("*.doc"))
        print(f"  ✅ 프로젝트 문서: {len(doc_files)}개")
        
        # 총 크기
        total_size = sum(f.stat().st_size for f in self.duraark_dir.rglob("*") if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        print(f"  ✅ 총 크기: {total_size_mb:.2f} MB")
        
        result = {
            "status": "ok" if len(ifc_files) > 0 else "warning",
            "ifc_count": len(ifc_files),
            "disciplines": disciplines,
            "doc_count": len(doc_files),
            "total_size_mb": total_size_mb
        }
        
        self.results["duraark"] = result
        return result
    
    def validate_schependomlaan_data(self) -> Dict:
        """Schependomlaan 데이터 검증"""
        print("\n🔍 Schependomlaan 데이터 검증 중...")
        
        if not self.schependomlaan_dir.exists():
            self.results["errors"].append(
                f"Schependomlaan 데이터 디렉토리 없음: {self.schependomlaan_dir}"
            )
            return {"status": "not_found", "count": 0}
        
        # BCF 파일 확인 (가장 중요)
        bcf_files = list(self.schependomlaan_dir.rglob("*.bcf")) + list(self.schependomlaan_dir.rglob("*.bcfzip"))
        print(f"  ✅ BCF 파일: {len(bcf_files)}개")
        
        # 주차별 BIM 모델 확인
        weekly_models = list(self.schependomlaan_dir.rglob("*week*.ifc")) + list(self.schependomlaan_dir.rglob("*week*.fbx"))
        print(f"  ✅ 주차별 모델: {len(weekly_models)}개")
        
        # 이벤트 로그 확인
        event_files = list(self.schependomlaan_dir.rglob("*event*.csv")) + list(self.schependomlaan_dir.rglob("*log*.json"))
        print(f"  ✅ 이벤트 로그: {len(event_files)}개")
        
        # BCF 내용 검증 (샘플)
        bcf_validation = {"valid_bcf": 0, "invalid_bcf": 0}
        for bcf_file in bcf_files[:5]:  # 샘플 5개만 검증
            try:
                if bcf_file.suffix == ".bcfzip":
                    with zipfile.ZipFile(bcf_file, 'r') as zip_ref:
                        # BCF 구조 확인
                        file_list = zip_ref.namelist()
                        if any("markup.bcf" in f for f in file_list):
                            bcf_validation["valid_bcf"] += 1
                        else:
                            bcf_validation["invalid_bcf"] += 1
                else:
                    # .bcf 파일 직접 검증
                    with open(bcf_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "markup" in content and "topic" in content:
                            bcf_validation["valid_bcf"] += 1
                        else:
                            bcf_validation["invalid_bcf"] += 1
            except Exception as e:
                bcf_validation["invalid_bcf"] += 1
                self.results["warnings"].append(
                    f"BCF 파일 검증 오류: {bcf_file.name} - {str(e)}"
                )
        
        if bcf_validation["invalid_bcf"] > 0:
            print(f"  ⚠️  BCF 검증: 유효 {bcf_validation['valid_bcf']}개, 무효 {bcf_validation['invalid_bcf']}개")
        
        # 총 크기
        total_size = sum(f.stat().st_size for f in self.schependomlaan_dir.rglob("*") if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        print(f"  ✅ 총 크기: {total_size_mb:.2f} MB")
        
        result = {
            "status": "ok" if len(bcf_files) > 0 else "warning",
            "bcf_count": len(bcf_files),
            "weekly_models_count": len(weekly_models),
            "event_files_count": len(event_files),
            "bcf_validation": bcf_validation,
            "total_size_mb": total_size_mb
        }
        
        self.results["schependomlaan"] = result
        return result
    
    def generate_summary(self) -> Dict:
        """검증 요약 생성"""
        print("\n📊 검증 요약 생성 중...")
        
        slabim = self.results["slabim"]
        duraark = self.results["duraark"]
        schependomlaan = self.results["schependomlaan"]
        
        summary = {
            "total_datasets": 3,
            "datasets_found": sum(1 for d in [slabim, duraark, schependomlaan] if d.get("status") == "ok"),
            "total_files": (
                slabim.get("slam_count", 0) + slabim.get("bim_count", 0) +
                duraark.get("ifc_count", 0) +
                schependomlaan.get("bcf_count", 0) + schependomlaan.get("weekly_models_count", 0)
            ),
            "total_size_mb": (
                slabim.get("total_size_mb", 0) +
                duraark.get("total_size_mb", 0) +
                schependomlaan.get("total_size_mb", 0)
            ),
            "bcf_files_available": schependomlaan.get("bcf_count", 0),
            "error_count": len(self.results["errors"]),
            "warning_count": len(self.results["warnings"])
        }
        
        self.results["summary"] = summary
        
        print(f"\n{'='*60}")
        print("🎯 검증 결과 요약")
        print(f"{'='*60}")
        print(f"총 데이터셋: {summary['total_datasets']}개")
        print(f"확보된 데이터셋: {summary['datasets_found']}개")
        print(f"총 파일 수: {summary['total_files']}개")
        print(f"총 크기: {summary['total_size_mb']:.2f} MB")
        print(f"BCF 파일: {summary['bcf_files_available']}개")
        print(f"오류: {summary['error_count']}개")
        print(f"경고: {summary['warning_count']}개")
        print(f"{'='*60}")
        
        return summary
    
    def save_report(self, output_path: Path = None):
        """검증 보고서 저장"""
        if output_path is None:
            output_path = ACADEMIC_DIR / "validation_report.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 검증 보고서 저장: {output_path}")
    
    def print_errors_and_warnings(self):
        """오류 및 경고 출력"""
        if self.results["errors"]:
            print(f"\n{'='*60}")
            print("❌ 오류:")
            print(f"{'='*60}")
            for error in self.results["errors"]:
                print(f"  • {error}")
        
        if self.results["warnings"]:
            print(f"\n{'='*60}")
            print("⚠️  경고:")
            print(f"{'='*60}")
            for warning in self.results["warnings"]:
                print(f"  • {warning}")
    
    def validate_all(self) -> bool:
        """전체 검증 수행"""
        print("🚀 학술 데이터셋 검증 시작...\n")
        
        # 각 데이터셋 검증
        self.validate_slabim_data()
        self.validate_duraark_data()
        self.validate_schependomlaan_data()
        
        # 요약 생성
        summary = self.generate_summary()
        
        # 오류 및 경고 출력
        self.print_errors_and_warnings()
        
        # 보고서 저장
        self.save_report()
        
        # 성공 여부 반환
        success = summary["datasets_found"] > 0 and summary["error_count"] == 0
        
        if success:
            print("\n✅ 검증 완료 - 데이터 사용 가능")
            return True
        else:
            print("\n❌ 검증 실패 - 데이터 확인 필요")
            return False

def main():
    """메인 함수"""
    validator = AcademicDataValidator()
    success = validator.validate_all()
    
    if not success:
        print("\n💡 다음 단계:")
        print("  1. 학술 기관에 데이터 요청")
        print("  2. contact_templates/ 디렉토리의 문의 템플릿 사용")
        print("  3. 데이터 수신 후 다시 검증 실행")
        sys.exit(1)
    else:
        print("\n🎉 다음 단계:")
        print("  1. BCF 변환: python scripts/convert_academic_to_bcf.py")
        print("  2. 데이터 통합: python scripts/integrate_academic_data.py")
        sys.exit(0)

if __name__ == "__main__":
    main()
