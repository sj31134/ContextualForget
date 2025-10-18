#!/usr/bin/env python3
"""
모든 IFC 파일 배치 처리
428개 IFC → JSONL 변환
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextualforget.core import extract_ifc_entities, write_jsonl


def process_all_ifc():
    """모든 IFC 파일 처리"""
    raw_dir = PROJECT_ROOT / "data" / "raw" / "downloaded"
    out_dir = PROJECT_ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 모든 IFC 파일
    all_ifc = list(raw_dir.glob("*.ifc"))
    
    # 이미 처리된 파일 (파일명 기반)
    processed_names = set()
    for f in out_dir.glob("*_ifc.jsonl"):
        # _ifc.jsonl 제거하여 원본 파일명 추출
        original_name = f.name.replace("_ifc.jsonl", "")
        processed_names.add(original_name)
    
    # 새로 처리할 파일
    new_ifc = [f for f in all_ifc if f.stem not in processed_names]
    
    print(f"\n{'='*60}")
    print(f"📐 IFC 파일 배치 처리")
    print(f"{'='*60}")
    print(f"\n전체 IFC: {len(all_ifc)}개")
    print(f"이미 처리됨: {len(processed_names)}개")
    print(f"새로 처리: {len(new_ifc)}개")
    
    if len(new_ifc) == 0:
        print("\n✅ 모든 IFC 파일이 이미 처리되었습니다!")
        return
    
    print(f"\n예상 시간: {len(new_ifc) * 0.5:.0f}초")
    print(f"처리 시작...\n")
    
    start_time = datetime.now()
    processed = 0
    failed = 0
    skipped = 0
    
    for ifc_file in new_ifc:
        try:
            # 출력 파일
            out_file = out_dir / f"{ifc_file.stem}_ifc.jsonl"
            
            # 이미 존재하면 건너뛰기
            if out_file.exists():
                skipped += 1
                continue
            
            # IFC 파싱
            entities = extract_ifc_entities(str(ifc_file))
            
            # 엔티티가 없으면 건너뛰기
            if not entities or len(entities) == 0:
                skipped += 1
                continue
            
            # JSONL 저장
            write_jsonl(str(out_file), entities)
            processed += 1
            
            # 진행 상황 출력
            if processed % 50 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (len(new_ifc) - processed - failed - skipped) / rate if rate > 0 else 0
                print(f"  처리: {processed}/{len(new_ifc)} ({processed/len(new_ifc)*100:.1f}%) "
                      f"- 속도: {rate:.1f}개/초, 남은 시간: {remaining:.0f}초")
        
        except Exception as e:
            print(f"  ❌ 실패 ({ifc_file.name}): {str(e)[:50]}")
            failed += 1
            continue
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"✅ IFC 처리 완료!")
    print(f"{'='*60}")
    print(f"\n결과:")
    print(f"  성공: {processed}개")
    print(f"  실패: {failed}개")
    print(f"  건너뜀: {skipped}개")
    print(f"  소요 시간: {elapsed:.1f}초")
    
    if processed > 0:
        print(f"  평균 속도: {processed/elapsed:.2f}개/초")
    
    print(f"\n출력 디렉토리: {out_dir}")
    
    # 최종 통계
    total_processed = len(list(out_dir.glob("*_ifc.jsonl")))
    print(f"\n📊 전체 처리 현황:")
    print(f"  처리된 IFC JSONL: {total_processed}개")
    print(f"  원본 IFC: {len(all_ifc)}개")
    print(f"  처리율: {total_processed/len(all_ifc)*100:.1f}%")


if __name__ == "__main__":
    process_all_ifc()

