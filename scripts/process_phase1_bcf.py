#!/usr/bin/env python3
"""
Phase 1에서 수집한 BCF 파일 배치 처리
"""

import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextualforget.core import parse_bcf_zip, write_jsonl


def process_bcf_batch():
    """수집된 모든 BCF 파일 처리"""
    bcf_dir = PROJECT_ROOT / "data" / "raw" / "downloaded"
    out_dir = PROJECT_ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # BCF 파일 찾기
    bcf_files = list(bcf_dir.glob("*.bcf")) + list(bcf_dir.glob("*.bcfzip"))
    print(f"발견된 BCF 파일: {len(bcf_files)}개")
    
    processed = 0
    failed = 0
    
    for bcf_file in bcf_files:
        try:
            # 출력 파일명 생성
            out_file = out_dir / f"{bcf_file.stem}_bcf.jsonl"
            
            # 이미 처리된 파일은 건너뛰기
            if out_file.exists():
                continue
            
            # BCF 파싱
            rows = parse_bcf_zip(str(bcf_file))
            
            if rows:
                write_jsonl(str(out_file), rows)
                processed += 1
                
                if processed % 10 == 0:
                    print(f"  처리 완료: {processed}/{len(bcf_files)}")
            else:
                print(f"  ⚠️  비어있는 BCF: {bcf_file.name}")
                failed += 1
                
        except Exception as e:
            print(f"  ❌ 오류 ({bcf_file.name}): {e}")
            failed += 1
    
    print(f"\n✅ 처리 완료:")
    print(f"   성공: {processed}개")
    print(f"   실패/건너뜀: {failed}개")
    print(f"   출력 디렉토리: {out_dir}")


if __name__ == "__main__":
    process_bcf_batch()

