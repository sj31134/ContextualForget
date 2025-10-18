#!/usr/bin/env python3
"""
의미있는 IFC 파일만 우선 처리
크기 기준: >10KB (작은 테스트 케이스 제외)
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextualforget.core import extract_ifc_entities, write_jsonl


def process_meaningful_ifc():
    """의미있는 IFC 파일만 처리 (>10KB)"""
    raw_dir = PROJECT_ROOT / "data" / "raw" / "downloaded"
    out_dir = PROJECT_ROOT / "data" / "processed"
    
    # 모든 IFC
    all_ifc = list(raw_dir.glob("*.ifc"))
    
    # 이미 처리된 파일
    processed_names = {f.name.replace("_ifc.jsonl", "") for f in out_dir.glob("*_ifc.jsonl")}
    
    # 미처리 파일 중 의미있는 파일 (>10KB)
    meaningful = [
        f for f in all_ifc 
        if f.stem not in processed_names and f.stat().st_size > 10*1024
    ]
    
    print(f"\n{'='*60}")
    print(f"📐 의미있는 IFC 파일 처리")
    print(f"{'='*60}")
    print(f"\n전체 IFC: {len(all_ifc)}개")
    print(f"이미 처리: {len(processed_names)}개")
    print(f"처리 대상: {len(meaningful)}개 (>10KB)")
    
    if len(meaningful) == 0:
        print("\n✅ 모든 의미있는 파일이 처리되었습니다!")
        return
    
    print(f"\n처리 시작...\n")
    
    start = datetime.now()
    processed = 0
    failed = 0
    
    for ifc_file in meaningful:
        try:
            out_file = out_dir / f"{ifc_file.stem}_ifc.jsonl"
            
            if out_file.exists():
                continue
            
            # IFC 파일 읽기
            with ifc_file.open('r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            entities = extract_ifc_entities(text)
            
            if not entities or len(entities) == 0:
                continue
            
            write_jsonl(str(out_file), entities)
            processed += 1
            
            if processed % 10 == 0:
                elapsed = (datetime.now() - start).total_seconds()
                rate = processed / elapsed if elapsed > 0 else 0
                print(f"  진행: {processed}/{len(meaningful)} - {rate:.1f}개/초")
        
        except Exception as e:
            failed += 1
            continue
    
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"✅ 처리 완료!")
    print(f"{'='*60}")
    print(f"\n성공: {processed}개")
    print(f"실패: {failed}개")
    print(f"소요 시간: {elapsed:.1f}초")
    
    # 최종 통계
    total = len(list(out_dir.glob("*_ifc.jsonl")))
    print(f"\n📊 전체 처리 현황:")
    print(f"  처리된 JSONL: {total}개")
    print(f"  원본 IFC: {len(all_ifc)}개")


if __name__ == "__main__":
    process_meaningful_ifc()

