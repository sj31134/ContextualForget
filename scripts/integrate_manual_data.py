#!/usr/bin/env python3
"""
수동 수집 데이터 자동 통합 스크립트

사용자가 나중에 다음 4개 데이터를 추가할 때 실행:
5. AI-Hub 건설 안전 데이터
8. BIMPROVE Dataset  
9. Stanford CIFE Dataset
10. 국토교통부 BIM 샘플

사용법:
  python scripts/integrate_manual_data.py --check   # 상태 확인
  python scripts/integrate_manual_data.py --process  # 자동 처리
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextualforget.core import extract_ifc_entities, parse_bcf_zip, write_jsonl


# 데이터 경로 정의
MANUAL_DATA_SOURCES = {
    "aihub": {
        "name": "AI-Hub 건설 안전",
        "path": PROJECT_ROOT / "data" / "external" / "aihub",
        "types": ["json", "csv", "images"],
        "priority": "중기"
    },
    "bimprove": {
        "name": "BIMPROVE Academic Dataset",
        "path": PROJECT_ROOT / "data" / "external" / "bimprove",
        "types": ["ifc", "bcfzip"],
        "priority": "장기"
    },
    "stanford": {
        "name": "Stanford CIFE Dataset",
        "path": PROJECT_ROOT / "data" / "external" / "stanford_cife",
        "types": ["ifc", "bcfzip"],
        "priority": "장기"
    },
    "molit": {
        "name": "국토교통부 BIM 샘플",
        "path": PROJECT_ROOT / "data" / "external" / "public_korea" / "molit",
        "types": ["ifc"],
        "priority": "중기"
    }
}


def check_manual_data_status():
    """수동 데이터 수집 상태 확인"""
    print("\n" + "="*60)
    print("📋 수동 수집 데이터 상태 확인")
    print("="*60)
    
    status = {}
    for key, source in MANUAL_DATA_SOURCES.items():
        path = source["path"]
        exists = path.exists()
        
        file_count = 0
        if exists:
            # IFC 파일
            ifc_files = list(path.rglob("*.ifc"))
            # BCF 파일
            bcf_files = list(path.rglob("*.bcf*"))
            # JSON 파일
            json_files = list(path.rglob("*.json"))
            # CSV 파일
            csv_files = list(path.rglob("*.csv"))
            
            file_count = len(ifc_files) + len(bcf_files) + len(json_files) + len(csv_files)
            
            status[key] = {
                "exists": True,
                "file_count": file_count,
                "ifc": len(ifc_files),
                "bcf": len(bcf_files),
                "json": len(json_files),
                "csv": len(csv_files)
            }
        else:
            status[key] = {
                "exists": False,
                "file_count": 0
            }
        
        # 출력
        icon = "✅" if exists and file_count > 0 else "⏳" if exists else "❌"
        print(f"\n{icon} {source['name']}")
        print(f"   경로: {path}")
        print(f"   우선순위: {source['priority']}")
        
        if exists:
            if file_count > 0:
                print(f"   상태: 데이터 발견 ({file_count}개 파일)")
                if status[key].get("ifc", 0) > 0:
                    print(f"     - IFC: {status[key]['ifc']}개")
                if status[key].get("bcf", 0) > 0:
                    print(f"     - BCF: {status[key]['bcf']}개")
                if status[key].get("json", 0) > 0:
                    print(f"     - JSON: {status[key]['json']}개")
                if status[key].get("csv", 0) > 0:
                    print(f"     - CSV: {status[key]['csv']}개")
            else:
                print(f"   상태: 디렉토리 있지만 데이터 없음")
        else:
            print(f"   상태: 아직 수집되지 않음")
    
    # 요약
    print(f"\n" + "="*60)
    print("📊 요약")
    print("="*60)
    
    ready = sum(1 for s in status.values() if s["exists"] and s["file_count"] > 0)
    total = len(MANUAL_DATA_SOURCES)
    
    print(f"\n수집 완료: {ready}/{total}개")
    
    if ready == 0:
        print("\n💡 아직 수동 데이터가 수집되지 않았습니다.")
        print("   가이드: docs/DATA_COLLECTION_GUIDE_5-10.md 참조")
    elif ready < total:
        print(f"\n⏳ {total - ready}개 데이터 수집 대기 중")
        print("   가이드: docs/DATA_COLLECTION_GUIDE_5-10.md 참조")
    else:
        print("\n🎉 모든 수동 데이터 수집 완료!")
        print("   다음: python scripts/integrate_manual_data.py --process")
    
    return status


def process_manual_data(status=None):
    """수동 수집 데이터 처리 및 통합"""
    if status is None:
        status = check_manual_data_status()
    
    print("\n" + "="*60)
    print("🔄 수동 데이터 처리 및 통합")
    print("="*60)
    
    raw_dir = PROJECT_ROOT / "data" / "raw" / "downloaded"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    
    total_processed = 0
    
    for key, source in MANUAL_DATA_SOURCES.items():
        if not status[key]["exists"] or status[key]["file_count"] == 0:
            continue
        
        print(f"\n처리 중: {source['name']}")
        path = source["path"]
        
        # IFC 파일 복사 및 처리
        ifc_files = list(path.rglob("*.ifc"))
        for ifc_file in ifc_files:
            try:
                # raw로 복사
                new_name = f"{key}_{ifc_file.stem}.ifc"
                dest = raw_dir / new_name
                
                if not dest.exists():
                    shutil.copy2(ifc_file, dest)
                    print(f"  ✅ IFC 복사: {new_name}")
                
                # JSONL 처리
                out_file = processed_dir / f"{key}_{ifc_file.stem}_ifc.jsonl"
                if not out_file.exists():
                    entities = extract_ifc_entities(str(dest))
                    if entities:
                        write_jsonl(str(out_file), entities)
                        print(f"  ✅ JSONL 생성: {out_file.name}")
                        total_processed += 1
            
            except Exception as e:
                print(f"  ❌ 오류 ({ifc_file.name}): {e}")
        
        # BCF 파일 복사 및 처리
        bcf_files = list(path.rglob("*.bcf*"))
        for bcf_file in bcf_files:
            try:
                # raw로 복사
                new_name = f"{key}_{bcf_file.stem}.bcfzip"
                dest = raw_dir / new_name
                
                if not dest.exists():
                    shutil.copy2(bcf_file, dest)
                    print(f"  ✅ BCF 복사: {new_name}")
                
                # JSONL 처리
                out_file = processed_dir / f"{key}_{bcf_file.stem}_bcf.jsonl"
                if not out_file.exists():
                    issues = parse_bcf_zip(str(dest))
                    if issues:
                        write_jsonl(str(out_file), issues)
                        print(f"  ✅ JSONL 생성: {out_file.name}")
                        total_processed += 1
            
            except Exception as e:
                print(f"  ❌ 오류 ({bcf_file.name}): {e}")
    
    print(f"\n" + "="*60)
    print(f"✅ 통합 완료: {total_processed}개 파일 처리")
    print("="*60)
    
    if total_processed > 0:
        print("\n다음 단계:")
        print("  1. 그래프 재구축: make build_graph")
        print("  2. 평가 재실행: python scripts/comprehensive_evaluation.py")


def main():
    """메인 실행"""
    parser = argparse.ArgumentParser(description="수동 수집 데이터 통합")
    parser.add_argument("--check", action="store_true", help="상태만 확인")
    parser.add_argument("--process", action="store_true", help="데이터 처리 및 통합")
    
    args = parser.parse_args()
    
    if args.process:
        status = check_manual_data_status()
        process_manual_data(status)
    else:
        # 기본: 상태 확인
        check_manual_data_status()


if __name__ == "__main__":
    main()

