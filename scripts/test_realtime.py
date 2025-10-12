#!/usr/bin/env python3
"""실시간 모니터링 테스트 스크립트."""

import time
import shutil
from pathlib import Path
from contextualforget.realtime import RealtimeMonitor

def main():
    """메인 함수."""
    print("🧪 실시간 모니터링 테스트")
    print("=" * 60)
    
    # 테스트 환경 설정
    base_dir = Path(__file__).parent.parent
    test_dir = base_dir / "data" / "test_watch"
    test_dir.mkdir(exist_ok=True)
    
    graph_path = base_dir / "data" / "processed" / "graph.gpickle"
    processed_dir = base_dir / "data" / "processed"
    
    print(f"테스트 디렉토리: {test_dir}")
    print(f"그래프 파일: {graph_path}")
    print("")
    
    # 모니터 초기화
    monitor = RealtimeMonitor(
        watch_dirs=[test_dir],
        graph_path=graph_path,
        processed_dir=processed_dir,
        poll_interval=1.0  # 빠른 테스트를 위해 1초
    )
    
    # 모니터링 시작
    print("📡 모니터링 시작...")
    monitor.start()
    
    try:
        print("\n⏱️  5초 후 테스트 파일 생성...")
        time.sleep(5)
        
        # 테스트 파일 생성
        print("\n📝 테스트 IFC 파일 생성 중...")
        source_ifc = base_dir / "data" / "residential_building.ifc"
        test_ifc = test_dir / "test_new_building.ifc"
        shutil.copy(source_ifc, test_ifc)
        print(f"  ✅ {test_ifc.name} 생성 완료")
        
        print("\n⏱️  5초 대기 (자동 감지)...")
        time.sleep(5)
        
        # 통계 확인
        stats = monitor.get_stats()
        print("\n📊 모니터링 통계:")
        print(f"  처리된 파일: {stats['files_processed']}개")
        print(f"  IFC 파일: {stats['ifc_files']}개")
        print(f"  BCF 파일: {stats['bcf_files']}개")
        print(f"  오류: {stats['errors']}개")
        
        print("\n⏱️  5초 후 테스트 종료...")
        time.sleep(5)
        
    finally:
        # 모니터링 중지
        print("\n⏹️  모니터링 중지 중...")
        monitor.stop()
        
        # 테스트 파일 정리
        print("\n🧹 테스트 파일 정리 중...")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        print("  ✅ 정리 완료")
    
    print("\n✨ 테스트 완료!")


if __name__ == "__main__":
    main()

