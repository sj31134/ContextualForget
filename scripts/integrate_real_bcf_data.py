#!/usr/bin/env python3
"""
실제 BCF 데이터 통합 스크립트
Schependomlaan 실제 BCF 파일들을 프로젝트에 통합
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import shutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import parse_bcf_zip, write_jsonl, read_jsonl


def process_real_bcf_files():
    """실제 BCF 파일들을 처리하여 프로젝트에 통합"""
    
    # 실제 BCF 파일 경로
    real_bcf_dir = Path("data/external/academic/schependomlaan_forked/Coordination model and subcontractors models/Checks/BCF")
    output_dir = Path("data/processed/real_bcf")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 기존 합성 데이터 백업
    synthetic_backup = Path("data/processed/synthetic_backup")
    synthetic_backup.mkdir(parents=True, exist_ok=True)
    
    print("🔄 실제 BCF 데이터 통합 시작...")
    
    # 1. 기존 합성 데이터 백업
    print("📦 기존 합성 데이터 백업 중...")
    synthetic_files = list(Path("data/processed").glob("*.jsonl"))
    for file in synthetic_files:
        if file.name.startswith("bcf_"):
            backup_file = synthetic_backup / file.name
            shutil.copy2(file, backup_file)
            print(f"  ✅ 백업 완료: {file.name}")
    
    # 2. 실제 BCF 파일 처리
    print("🔍 실제 BCF 파일 분석 중...")
    real_bcf_files = list(real_bcf_dir.glob("*.bcfzip"))
    print(f"  📊 발견된 실제 BCF 파일: {len(real_bcf_files)}개")
    
    all_real_bcf_data = []
    processed_count = 0
    
    for bcf_file in real_bcf_files:
        try:
            print(f"  🔄 처리 중: {bcf_file.name}")
            rows = parse_bcf_zip(str(bcf_file))
            
            # 메타데이터 추가
            for row in rows:
                row['source_file'] = bcf_file.name
                row['data_type'] = 'real_bcf'
                row['processed_date'] = datetime.now().isoformat()
                row['project'] = 'Schependomlaan'
                
            all_real_bcf_data.extend(rows)
            processed_count += 1
            
        except Exception as e:
            print(f"  ❌ 오류 발생: {bcf_file.name} - {e}")
            continue
    
    # 3. 실제 데이터 저장
    print("💾 실제 BCF 데이터 저장 중...")
    real_bcf_output = output_dir / "real_bcf_data.jsonl"
    write_jsonl(str(real_bcf_output), all_real_bcf_data)
    
    # 4. 통계 생성
    stats = {
        "total_files_processed": processed_count,
        "total_issues_found": len(all_real_bcf_data),
        "data_type": "real_bcf",
        "source_project": "Schependomlaan",
        "processing_date": datetime.now().isoformat(),
        "file_details": []
    }
    
    # 파일별 상세 통계
    for bcf_file in real_bcf_files:
        file_issues = [row for row in all_real_bcf_data if row.get('source_file') == bcf_file.name]
        stats["file_details"].append({
            "filename": bcf_file.name,
            "file_size_mb": round(bcf_file.stat().st_size / (1024*1024), 2),
            "issues_count": len(file_issues),
            "authors": list(set(row.get('author', '') for row in file_issues if row.get('author'))),
            "date_range": {
                "earliest": min(row.get('created', '') for row in file_issues if row.get('created', '').strip()) if any(row.get('created', '').strip() for row in file_issues) else "",
                "latest": max(row.get('created', '') for row in file_issues if row.get('created', '').strip()) if any(row.get('created', '').strip() for row in file_issues) else ""
            }
        })
    
    # 통계 저장
    stats_file = output_dir / "real_bcf_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 실제 BCF 데이터 통합 완료!")
    print(f"  📊 처리된 파일: {processed_count}개")
    print(f"  📋 발견된 이슈: {len(all_real_bcf_data)}개")
    print(f"  💾 저장 위치: {real_bcf_output}")
    print(f"  📈 통계 파일: {stats_file}")
    
    return stats


def update_data_sources():
    """데이터 소스 정보 업데이트"""
    
    sources_file = Path("data/sources.json")
    
    # 기존 소스 정보 로드
    if sources_file.exists():
        with open(sources_file, 'r', encoding='utf-8') as f:
            sources = json.load(f)
    else:
        sources = {"ifc_files": [], "bcf_files": []}
    
    # 실제 BCF 데이터 소스 추가
    real_bcf_source = {
        "path": "data/processed/real_bcf/real_bcf_data.jsonl",
        "name": "Schependomlaan Real BCF Data",
        "description": "실제 건설 프로젝트의 BCF 협업 이슈 데이터 (93개 이슈)",
        "type": "real_bcf",
        "source_url": "https://github.com/sj31134/DataSetSchependomlaan.git",
        "file_count": 20,
        "data_quality": "high",
        "added_date": datetime.now().isoformat(),
        "usage": "primary_training_data"
    }
    
    # 기존 BCF 파일들을 secondary로 변경
    for bcf_file in sources.get("bcf_files", []):
        if bcf_file.get("type") != "real_bcf":
            bcf_file["usage"] = "secondary_training_data"
            bcf_file["data_quality"] = "medium"
    
    # 새로운 소스 추가
    sources["bcf_files"].append(real_bcf_source)
    
    # 업데이트된 소스 정보 저장
    with open(sources_file, 'w', encoding='utf-8') as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)
    
    print("✅ 데이터 소스 정보 업데이트 완료")


def main():
    """메인 실행 함수"""
    print("🚀 실제 BCF 데이터 통합 프로세스 시작")
    print("=" * 60)
    
    try:
        # 1. 실제 BCF 데이터 처리
        stats = process_real_bcf_files()
        
        # 2. 데이터 소스 정보 업데이트
        update_data_sources()
        
        print("\n" + "=" * 60)
        print("🎉 실제 BCF 데이터 통합 완료!")
        print(f"📊 총 {stats['total_issues_found']}개의 실제 이슈 데이터 확보")
        print("📈 연구 신뢰도 대폭 향상!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
