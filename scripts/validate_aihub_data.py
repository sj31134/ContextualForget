#!/usr/bin/env python3
"""
AI-Hub 데이터 검증 스크립트
작성일: 2025-10-15
용도: 다운로드된 AI-Hub 데이터의 무결성 및 형식 검증
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import sys

PROJECT_ROOT = Path(__file__).parent.parent
AIHUB_DIR = PROJECT_ROOT / "data" / "external" / "aihub"


class AIHubDataValidator:
    """AI-Hub 데이터 검증 클래스"""
    
    def __init__(self):
        self.daily_life_dir = AIHUB_DIR / "daily_life_spaces"
        self.construction_safety_dir = AIHUB_DIR / "construction_safety"
        self.results = {
            "daily_life_spaces": {},
            "construction_safety": {},
            "summary": {},
            "errors": [],
            "warnings": []
        }
    
    def validate_daily_life_spaces(self) -> Dict:
        """일상생활 공간 데이터 검증"""
        print("🔍 일상생활 공간 데이터 검증 중...")
        
        if not self.daily_life_dir.exists():
            self.results["errors"].append(
                f"일상생활 공간 데이터 디렉토리 없음: {self.daily_life_dir}"
            )
            return {"status": "error", "count": 0}
        
        # FBX 파일 검증
        fbx_files = list(self.daily_life_dir.rglob("*.fbx"))
        print(f"  ✅ FBX 파일: {len(fbx_files)}개")
        
        # JSON 파일 검증
        json_files = list(self.daily_life_dir.rglob("*.json"))
        print(f"  ✅ JSON 파일: {len(json_files)}개")
        
        # JSON 형식 검증
        valid_json = 0
        invalid_json = 0
        for json_file in json_files[:10]:  # 샘플 10개만 검증
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                valid_json += 1
            except Exception as e:
                invalid_json += 1
                self.results["warnings"].append(
                    f"JSON 파싱 오류: {json_file.name} - {str(e)}"
                )
        
        if invalid_json > 0:
            print(f"  ⚠️  JSON 파싱 오류: {invalid_json}개")
        
        # FBX-JSON 매칭 검증
        fbx_stems = {f.stem for f in fbx_files}
        json_stems = {f.stem for f in json_files}
        matched = fbx_stems & json_stems
        
        if len(matched) > 0:
            print(f"  ✅ FBX-JSON 매칭: {len(matched)}개")
        else:
            self.results["warnings"].append(
                "FBX-JSON 파일 이름 매칭 실패 (다른 구조일 수 있음)"
            )
        
        # 총 크기
        total_size = sum(f.stat().st_size for f in self.daily_life_dir.rglob("*") if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        print(f"  ✅ 총 크기: {total_size_mb:.2f} MB")
        
        result = {
            "status": "ok" if len(fbx_files) > 0 else "warning",
            "fbx_count": len(fbx_files),
            "json_count": len(json_files),
            "matched_count": len(matched),
            "total_size_mb": total_size_mb,
            "valid_json": valid_json,
            "invalid_json": invalid_json
        }
        
        self.results["daily_life_spaces"] = result
        return result
    
    def validate_construction_safety(self) -> Dict:
        """건설 안전 데이터 검증"""
        print("\n🔍 건설 안전 데이터 검증 중...")
        
        if not self.construction_safety_dir.exists():
            self.results["errors"].append(
                f"건설 안전 데이터 디렉토리 없음: {self.construction_safety_dir}"
            )
            return {"status": "error", "count": 0}
        
        # 이미지 파일 검증
        image_files = list(self.construction_safety_dir.rglob("*.jpg")) + \
                      list(self.construction_safety_dir.rglob("*.png"))
        print(f"  ✅ 이미지 파일: {len(image_files)}개")
        
        # 어노테이션 파일 검증
        csv_files = list(self.construction_safety_dir.rglob("*.csv"))
        json_files = list(self.construction_safety_dir.rglob("*.json"))
        annotation_count = len(csv_files) + len(json_files)
        print(f"  ✅ 어노테이션 파일: {annotation_count}개 (CSV: {len(csv_files)}, JSON: {len(json_files)})")
        
        # 이미지 형식 검증 (샘플)
        valid_images = 0
        invalid_images = 0
        for img_file in image_files[:10]:  # 샘플 10개만 검증
            try:
                from PIL import Image
                with Image.open(img_file) as img:
                    img.verify()
                valid_images += 1
            except ImportError:
                print("  ⚠️  PIL 라이브러리 없음 - 이미지 검증 스킵")
                break
            except Exception as e:
                invalid_images += 1
                self.results["warnings"].append(
                    f"이미지 손상: {img_file.name} - {str(e)}"
                )
        
        if invalid_images > 0:
            print(f"  ⚠️  손상된 이미지: {invalid_images}개")
        
        # 총 크기
        total_size = sum(f.stat().st_size for f in self.construction_safety_dir.rglob("*") if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        print(f"  ✅ 총 크기: {total_size_mb:.2f} MB")
        
        result = {
            "status": "ok" if len(image_files) > 0 else "warning",
            "image_count": len(image_files),
            "annotation_count": annotation_count,
            "total_size_mb": total_size_mb,
            "valid_images": valid_images,
            "invalid_images": invalid_images
        }
        
        self.results["construction_safety"] = result
        return result
    
    def generate_summary(self) -> Dict:
        """검증 요약 생성"""
        print("\n📊 검증 요약 생성 중...")
        
        daily_life = self.results["daily_life_spaces"]
        safety = self.results["construction_safety"]
        
        summary = {
            "total_files": (
                daily_life.get("fbx_count", 0) + 
                daily_life.get("json_count", 0) +
                safety.get("image_count", 0) +
                safety.get("annotation_count", 0)
            ),
            "total_size_mb": (
                daily_life.get("total_size_mb", 0) +
                safety.get("total_size_mb", 0)
            ),
            "daily_life_ok": daily_life.get("status") == "ok",
            "safety_ok": safety.get("status") == "ok",
            "error_count": len(self.results["errors"]),
            "warning_count": len(self.results["warnings"])
        }
        
        self.results["summary"] = summary
        
        print(f"\n{'='*60}")
        print("🎯 검증 결과 요약")
        print(f"{'='*60}")
        print(f"총 파일 수: {summary['total_files']}개")
        print(f"총 크기: {summary['total_size_mb']:.2f} MB")
        print(f"일상생활 공간 데이터: {'✅ OK' if summary['daily_life_ok'] else '⚠️ WARNING'}")
        print(f"건설 안전 데이터: {'✅ OK' if summary['safety_ok'] else '⚠️ WARNING'}")
        print(f"오류: {summary['error_count']}개")
        print(f"경고: {summary['warning_count']}개")
        print(f"{'='*60}")
        
        return summary
    
    def save_report(self, output_path: Path = None):
        """검증 보고서 저장"""
        if output_path is None:
            output_path = PROJECT_ROOT / "data" / "analysis" / "aihub_validation_report.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
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
        print("🚀 AI-Hub 데이터 검증 시작...\n")
        
        # 일상생활 공간 데이터 검증
        self.validate_daily_life_spaces()
        
        # 건설 안전 데이터 검증
        self.validate_construction_safety()
        
        # 요약 생성
        summary = self.generate_summary()
        
        # 오류 및 경고 출력
        self.print_errors_and_warnings()
        
        # 보고서 저장
        self.save_report()
        
        # 성공 여부 반환
        success = (
            summary["daily_life_ok"] or summary["safety_ok"]
        ) and summary["error_count"] == 0
        
        if success:
            print("\n✅ 검증 완료 - 데이터 사용 가능")
            return True
        else:
            print("\n❌ 검증 실패 - 데이터 확인 필요")
            return False


def main():
    """메인 함수"""
    validator = AIHubDataValidator()
    success = validator.validate_all()
    
    if not success:
        print("\n💡 다음 단계:")
        print("  1. AI-Hub에서 데이터를 다운로드했는지 확인")
        print("  2. scripts/setup_aihub_data.sh 실행")
        print("  3. 다시 검증 실행")
        sys.exit(1)
    else:
        print("\n🎉 다음 단계:")
        print("  1. IFC 변환: python scripts/convert_aihub_to_ifc.py")
        print("  2. BCF 생성: python scripts/generate_bcf_from_aihub.py")
        sys.exit(0)


if __name__ == "__main__":
    main()

