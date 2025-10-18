#!/usr/bin/env python3
"""
남은 자동 수집 가능한 데이터 수집
- BIMserver 프로젝트 IFC (278개 발견)
- BCF Test Cases IFC (4개)
- OpenBIM IDS 예제 IFC
"""

import shutil
from pathlib import Path
from datetime import datetime
import json


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "downloaded"
EXTERNAL_DIR = DATA_DIR / "external"


class RemainingDataCollector:
    """남은 자동 수집 가능 데이터 수집기"""
    
    def __init__(self):
        self.collected = {
            "bimserver": 0,
            "bcf_test_ifcs": 0,
            "openbim_ids": 0,
            "total_size": 0
        }
    
    def collect_bimserver_ifc(self):
        """BIMserver 오픈소스 프로젝트의 IFC 파일"""
        print("\n" + "="*60)
        print("🖥️  BIMserver 프로젝트 IFC 수집 중...")
        print("="*60)
        
        source_dir = EXTERNAL_DIR / "opensource"
        
        if not source_dir.exists():
            print("   ⚠️  BIMserver 디렉토리 없음")
            return
        
        # IFC 파일 찾기
        ifc_files = list(source_dir.rglob("*.ifc"))
        print(f"   발견: {len(ifc_files)}개 IFC 파일")
        
        # 복사 (중복 제외, 크기 필터)
        copied = 0
        for ifc_file in ifc_files:
            try:
                size = ifc_file.stat().st_size
                
                # 너무 작은 파일 제외 (<1KB)
                if size < 1024:
                    continue
                
                # 너무 큰 파일 제외 (>50MB - 선택적)
                if size > 50 * 1024 * 1024:
                    continue
                
                # 파일명 생성
                # 경로에서 의미있는 부분 추출
                parts = ifc_file.parts
                if "opensource" in parts:
                    idx = parts.index("opensource")
                    project = parts[idx + 1] if idx + 1 < len(parts) else "unknown"
                else:
                    project = "opensource"
                
                new_name = f"{project}_{ifc_file.stem}.ifc"
                dest = RAW_DIR / new_name
                
                # 중복 체크
                if not dest.exists():
                    shutil.copy2(ifc_file, dest)
                    copied += 1
                    self.collected["bimserver"] += 1
                    self.collected["total_size"] += size
                    
                    if copied % 50 == 0:
                        print(f"   진행: {copied}개 복사...")
            
            except Exception as e:
                continue
        
        print(f"   ✅ {copied}개 파일 복사 완료")
        print(f"   📊 총 크기: {self.collected['total_size'] / 1024 / 1024:.1f} MB")
    
    def collect_bcf_test_ifcs(self):
        """BCF Test Cases에 포함된 IFC 파일"""
        print("\n" + "="*60)
        print("📋 BCF Test Cases IFC 수집 중...")
        print("="*60)
        
        source_dir = EXTERNAL_DIR / "buildingsmart" / "BCF-XML" / "Test Cases" / "IFCs"
        
        if not source_dir.exists():
            print("   ⚠️  BCF Test IFCs 디렉토리 없음")
            return
        
        ifc_files = list(source_dir.glob("*.ifc"))
        print(f"   발견: {len(ifc_files)}개")
        
        copied = 0
        for ifc_file in ifc_files:
            try:
                size = ifc_file.stat().st_size
                
                new_name = f"bcf_testcase_{ifc_file.stem}.ifc"
                dest = RAW_DIR / new_name
                
                if not dest.exists():
                    shutil.copy2(ifc_file, dest)
                    copied += 1
                    self.collected["bcf_test_ifcs"] += 1
                    self.collected["total_size"] += size
            
            except Exception as e:
                continue
        
        print(f"   ✅ {copied}개 파일 복사 완료")
    
    def collect_openbim_ids_examples(self):
        """OpenBIM IDS 예제 IFC 파일"""
        print("\n" + "="*60)
        print("📐 OpenBIM IDS 예제 IFC 수집 중...")
        print("="*60)
        
        source_dir = EXTERNAL_DIR / "openbim" / "IDS" / "Documentation"
        
        if not source_dir.exists():
            print("   ⚠️  OpenBIM IDS 디렉토리 없음")
            return
        
        ifc_files = list(source_dir.rglob("*.ifc"))
        print(f"   발견: {len(ifc_files)}개")
        
        copied = 0
        for ifc_file in ifc_files:
            try:
                size = ifc_file.stat().st_size
                
                if size < 100:
                    continue
                
                new_name = f"openbim_ids_{ifc_file.stem}.ifc"
                dest = RAW_DIR / new_name
                
                if not dest.exists():
                    shutil.copy2(ifc_file, dest)
                    copied += 1
                    self.collected["openbim_ids"] += 1
                    self.collected["total_size"] += size
            
            except Exception as e:
                continue
        
        print(f"   ✅ {copied}개 파일 복사 완료")
    
    def save_collection_report(self):
        """수집 보고서 저장"""
        print("\n" + "="*60)
        print("📝 수집 보고서 생성 중...")
        print("="*60)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": "자동 수집 완료 (로그인 불필요)",
            "collected": self.collected,
            "summary": {
                "total_files": sum([
                    self.collected["bimserver"],
                    self.collected["bcf_test_ifcs"],
                    self.collected["openbim_ids"]
                ]),
                "total_size_mb": round(self.collected["total_size"] / 1024 / 1024, 2)
            }
        }
        
        output_file = DATA_DIR / "analysis" / "remaining_data_collection.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ 보고서 저장: {output_file}")
        
        return report


def main():
    """메인 실행"""
    print("\n" + "🎯 " + "="*58)
    print("   자동 수집 가능 데이터 수집 시작")
    print("   (로그인/승인 불필요)")
    print("   " + "="*58)
    
    collector = RemainingDataCollector()
    
    try:
        # 데이터 수집
        collector.collect_bimserver_ifc()
        collector.collect_bcf_test_ifcs()
        collector.collect_openbim_ids_examples()
        
        # 보고서 생성
        report = collector.save_collection_report()
        
        # 최종 요약
        print("\n" + "="*60)
        print("📊 자동 수집 완료 요약")
        print("="*60)
        
        print(f"\n수집된 파일:")
        print(f"  - BIMserver 프로젝트: {collector.collected['bimserver']}개")
        print(f"  - BCF Test IFCs: {collector.collected['bcf_test_ifcs']}개")
        print(f"  - OpenBIM IDS: {collector.collected['openbim_ids']}개")
        print(f"  - 총: {report['summary']['total_files']}개")
        
        print(f"\n총 크기: {report['summary']['total_size_mb']} MB")
        
        # 전체 현황
        print("\n" + "="*60)
        print("🎉 전체 데이터 수집 현황")
        print("="*60)
        
        all_ifc = list(RAW_DIR.glob("*.ifc"))
        all_bcf = list(RAW_DIR.glob("*.bcf*"))
        
        print(f"\n📂 data/raw/downloaded/")
        print(f"  - IFC 파일: {len(all_ifc)}개")
        print(f"  - BCF 파일: {len(all_bcf)}개")
        
        print("\n✅ 로그인/승인 불필요 데이터: 모두 수집 완료!")
        
        print("\n❌ 수동 작업 필요:")
        print("  5. AI-Hub 건설 안전 (로그인 필요)")
        print("  8. BIMPROVE Dataset (학술 승인 필요)")
        print("  9. Stanford CIFE (학술 승인 필요)")
        print("  10. 국토교통부 BIM (수동 다운로드)")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

