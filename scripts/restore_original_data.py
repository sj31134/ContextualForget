#!/usr/bin/env python3
"""
기존 수집 데이터 복구 스크립트
515개 파일 (428 IFC + 87 BCF)을 분석하고 통합 데이터셋 구축을 위한 준비
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import parse_bcf_zip, write_jsonl, read_jsonl


def analyze_downloaded_data():
    """다운로드된 데이터 분석"""
    
    downloaded_dir = Path("data/raw/downloaded")
    if not downloaded_dir.exists():
        print("❌ data/raw/downloaded 디렉토리가 존재하지 않습니다.")
        return None
    
    print("🔍 다운로드된 데이터 분석 중...")
    
    # 파일 타입별 분류
    ifc_files = list(downloaded_dir.glob("*.ifc"))
    bcf_files = list(downloaded_dir.glob("*.bcfzip"))
    
    print(f"  📊 발견된 파일:")
    print(f"    • IFC 파일: {len(ifc_files)}개")
    print(f"    • BCF 파일: {len(bcf_files)}개")
    print(f"    • 총 파일: {len(ifc_files) + len(bcf_files)}개")
    
    # 파일 크기 분석
    total_size = sum(f.stat().st_size for f in ifc_files + bcf_files)
    print(f"  💾 총 크기: {total_size / (1024*1024):.1f} MB")
    
    # BCF 파일별 이슈 수 분석
    bcf_analysis = {}
    total_bcf_issues = 0
    
    for bcf_file in bcf_files[:10]:  # 처음 10개만 샘플 분석
        try:
            issues = parse_bcf_zip(bcf_file)
            bcf_analysis[bcf_file.name] = len(issues)
            total_bcf_issues += len(issues)
        except Exception as e:
            print(f"    ⚠️ {bcf_file.name} 파싱 실패: {e}")
            bcf_analysis[bcf_file.name] = 0
    
    print(f"  📋 BCF 이슈 분석 (샘플 10개):")
    for filename, count in bcf_analysis.items():
        print(f"    • {filename}: {count}개 이슈")
    
    return {
        "ifc_files": len(ifc_files),
        "bcf_files": len(bcf_files),
        "total_files": len(ifc_files) + len(bcf_files),
        "total_size_mb": total_size / (1024*1024),
        "bcf_analysis": bcf_analysis,
        "estimated_total_bcf_issues": total_bcf_issues * len(bcf_files) // 10
    }


def restore_bcf_data():
    """BCF 데이터 복구 및 통합"""
    
    print("🔄 BCF 데이터 복구 중...")
    
    downloaded_dir = Path("data/raw/downloaded")
    output_dir = Path("data/processed/restored_bcf")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # BCF 파일 처리
    bcf_files = list(downloaded_dir.glob("*.bcfzip"))
    all_bcf_data = []
    
    for i, bcf_file in enumerate(bcf_files):
        print(f"  📄 처리 중: {bcf_file.name} ({i+1}/{len(bcf_files)})")
        
        try:
            issues = parse_bcf_zip(bcf_file)
            
            for issue in issues:
                # 메타데이터 추가
                issue["source_file"] = bcf_file.name
                issue["source_type"] = "downloaded"
                issue["restored_date"] = datetime.now().isoformat()
                
                all_bcf_data.append(issue)
                
        except Exception as e:
            print(f"    ⚠️ {bcf_file.name} 처리 실패: {e}")
            continue
    
    # 복구된 BCF 데이터 저장
    output_file = output_dir / "restored_bcf_data.jsonl"
    write_jsonl(str(output_file), all_bcf_data)
    
    print(f"  ✅ 복구 완료: {len(all_bcf_data)}개 BCF 이슈")
    print(f"  📁 저장 위치: {output_file}")
    
    return {
        "total_issues": len(all_bcf_data),
        "output_file": str(output_file),
        "source_files": len(bcf_files)
    }


def restore_ifc_data():
    """IFC 데이터 복구 및 분석"""
    
    print("🔄 IFC 데이터 복구 중...")
    
    downloaded_dir = Path("data/raw/downloaded")
    output_dir = Path("data/processed/restored_ifc")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # IFC 파일 분석
    ifc_files = list(downloaded_dir.glob("*.ifc"))
    ifc_analysis = []
    
    for i, ifc_file in enumerate(ifc_files[:50]):  # 처음 50개만 샘플 분석
        print(f"  📄 분석 중: {ifc_file.name} ({i+1}/50)")
        
        try:
            # 파일 크기와 기본 정보만 수집
            file_info = {
                "filename": ifc_file.name,
                "size_bytes": ifc_file.stat().st_size,
                "size_mb": ifc_file.stat().st_size / (1024*1024),
                "source_type": "downloaded",
                "restored_date": datetime.now().isoformat()
            }
            
            # IFC 파일의 첫 몇 줄을 읽어서 버전 정보 추출
            with open(ifc_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline().strip() for _ in range(10)]
                
            # IFC 버전 추출
            for line in first_lines:
                if line.startswith("ISO-10303-21"):
                    file_info["ifc_version"] = line
                    break
                elif "IFC" in line.upper():
                    file_info["ifc_version"] = line
                    break
            
            ifc_analysis.append(file_info)
            
        except Exception as e:
            print(f"    ⚠️ {ifc_file.name} 분석 실패: {e}")
            continue
    
    # IFC 분석 결과 저장
    output_file = output_dir / "ifc_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ifc_analysis, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ 분석 완료: {len(ifc_analysis)}개 IFC 파일")
    print(f"  📁 저장 위치: {output_file}")
    
    return {
        "analyzed_files": len(ifc_analysis),
        "total_files": len(ifc_files),
        "output_file": str(output_file)
    }


def update_sources_json():
    """sources.json 업데이트"""
    
    print("📝 sources.json 업데이트 중...")
    
    sources_file = Path("data/sources.json")
    
    # 기존 sources.json 읽기
    if sources_file.exists():
        with open(sources_file, 'r', encoding='utf-8') as f:
            sources = json.load(f)
    else:
        sources = {"ifc_files": [], "bcf_files": []}
    
    # 복구된 데이터 정보 추가
    restored_bcf_info = {
        "path": "data/processed/restored_bcf/restored_bcf_data.jsonl",
        "name": "Restored BCF Data",
        "description": "복구된 buildingSMART 및 기타 BCF 테스트 케이스",
        "type": "restored_bcf",
        "source_type": "downloaded",
        "data_quality": "high",
        "added_date": datetime.now().isoformat(),
        "usage": "primary_training_data"
    }
    
    restored_ifc_info = {
        "path": "data/processed/restored_ifc/ifc_analysis.json",
        "name": "Restored IFC Data",
        "description": "복구된 OpenBIM IDS, IfcOpenShell 및 기타 IFC 파일",
        "type": "restored_ifc",
        "source_type": "downloaded",
        "data_quality": "high",
        "added_date": datetime.now().isoformat(),
        "usage": "primary_training_data"
    }
    
    # 기존 항목과 중복되지 않도록 추가
    existing_paths = {item.get("path", "") for item in sources.get("bcf_files", [])}
    
    if restored_bcf_info["path"] not in existing_paths:
        sources["bcf_files"].append(restored_bcf_info)
    
    if restored_ifc_info["path"] not in existing_paths:
        sources["ifc_files"].append(restored_ifc_info)
    
    # 업데이트된 sources.json 저장
    with open(sources_file, 'w', encoding='utf-8') as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ sources.json 업데이트 완료")
    
    return sources


def main():
    """메인 실행 함수"""
    
    print("🚀 기존 수집 데이터 복구 시작")
    print("=" * 50)
    
    # 1. 다운로드된 데이터 분석
    analysis = analyze_downloaded_data()
    if not analysis:
        return
    
    print("\n" + "=" * 50)
    
    # 2. BCF 데이터 복구
    bcf_result = restore_bcf_data()
    
    print("\n" + "=" * 50)
    
    # 3. IFC 데이터 복구
    ifc_result = restore_ifc_data()
    
    print("\n" + "=" * 50)
    
    # 4. sources.json 업데이트
    sources = update_sources_json()
    
    print("\n" + "=" * 50)
    print("🎉 데이터 복구 완료!")
    print("\n📊 복구 결과 요약:")
    print(f"  • BCF 이슈: {bcf_result['total_issues']}개")
    print(f"  • IFC 파일: {ifc_result['total_files']}개 (분석: {ifc_result['analyzed_files']}개)")
    print(f"  • 총 파일: {analysis['total_files']}개")
    print(f"  • 총 크기: {analysis['total_size_mb']:.1f} MB")
    
    # 복구 결과를 JSON으로 저장
    result_summary = {
        "restoration_date": datetime.now().isoformat(),
        "analysis": analysis,
        "bcf_result": bcf_result,
        "ifc_result": ifc_result,
        "sources_updated": True
    }
    
    summary_file = Path("data/analysis/restoration_summary.json")
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(result_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 상세 결과: {summary_file}")


if __name__ == "__main__":
    main()
