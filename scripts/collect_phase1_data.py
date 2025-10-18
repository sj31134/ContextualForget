#!/usr/bin/env python3
"""
Phase 1 데이터 수집 스크립트
우선순위 1-4번 데이터셋 수집 및 통합

데이터셋:
1. buildingSMART BCF Test Cases (v2.1, v3.0)
2. buildingSMART Additional IFC Files
3. BIMserver Test Projects (GitHub clone 필요)
4. 국토교통부 BIM 샘플 (웹 조사 후 수동 다운로드)
"""

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "downloaded"
EXTERNAL_DIR = DATA_DIR / "external"
PROVENANCE_FILE = DATA_DIR / "provenance" / "data_provenance.json"


class Phase1DataCollector:
    """Phase 1 우선순위 데이터 수집기"""
    
    def __init__(self):
        self.collected_files = []
        self.stats = {
            "bcf_count": 0,
            "ifc_count": 0,
            "total_size": 0,
            "sources": {}
        }
        
    def collect_buildingsmart_bcf_testcases(self):
        """1. buildingSMART BCF Test Cases 수집"""
        print("\n" + "="*60)
        print("📋 1. buildingSMART BCF Test Cases 수집 중...")
        print("="*60)
        
        bcf_source_dir = EXTERNAL_DIR / "buildingsmart" / "BCF-XML" / "Test Cases"
        
        if not bcf_source_dir.exists():
            print(f"❌ BCF Test Cases 디렉토리를 찾을 수 없습니다: {bcf_source_dir}")
            return
        
        # v2.1 및 v3.0 BCF 파일 수집
        bcf_files = []
        for version in ["v2.1", "v3.0"]:
            version_dir = bcf_source_dir / version
            if version_dir.exists():
                # .bcf 및 .bcfzip 파일 찾기
                found = list(version_dir.rglob("*.bcf"))
                found.extend(list(version_dir.rglob("*.bcfzip")))
                bcf_files.extend(found)
        
        print(f"   발견된 BCF 파일: {len(bcf_files)}개")
        
        # raw/downloaded 디렉토리로 복사
        copied_count = 0
        for bcf_file in bcf_files:
            # unzipped 디렉토리는 제외
            if "unzipped" in str(bcf_file):
                continue
                
            # 파일 크기 확인 (너무 작은 파일 제외)
            if bcf_file.stat().st_size < 100:
                continue
            
            # 버전과 테스트 케이스 이름 추출
            parts = bcf_file.parts
            version = parts[parts.index("Test Cases") + 1] if "Test Cases" in parts else "unknown"
            
            # 새 파일명 생성
            new_name = f"buildingsmart_bcf_{version}_{bcf_file.stem}.bcfzip"
            dest_file = RAW_DIR / new_name
            
            # 이미 존재하지 않으면 복사
            if not dest_file.exists():
                shutil.copy2(bcf_file, dest_file)
                copied_count += 1
                self.stats["bcf_count"] += 1
                self.stats["total_size"] += dest_file.stat().st_size
                
                self.collected_files.append({
                    "path": str(dest_file.relative_to(PROJECT_ROOT)),
                    "source": "buildingSMART BCF Test Cases",
                    "version": version,
                    "size": dest_file.stat().st_size,
                    "collected_at": datetime.now().isoformat()
                })
        
        print(f"   ✅ {copied_count}개 파일 복사 완료")
        self.stats["sources"]["buildingSMART_BCF"] = copied_count
    
    def collect_buildingsmart_additional_ifc(self):
        """2. buildingSMART Additional IFC 파일 수집"""
        print("\n" + "="*60)
        print("🏗️  2. buildingSMART Additional IFC 파일 수집 중...")
        print("="*60)
        
        # 기존 buildingSMART-samples 확인
        ifc_source_dir = EXTERNAL_DIR / "buildingSMART-samples"
        
        if not ifc_source_dir.exists():
            print(f"❌ buildingSMART-samples 디렉토리를 찾을 수 없습니다: {ifc_source_dir}")
            return
        
        # IFC 파일 찾기
        ifc_files = list(ifc_source_dir.rglob("*.ifc"))
        print(f"   발견된 IFC 파일: {len(ifc_files)}개")
        
        # raw/downloaded로 복사 (이미 복사되지 않은 것만)
        copied_count = 0
        for ifc_file in ifc_files:
            # 파일 크기 확인
            file_size = ifc_file.stat().st_size
            if file_size < 100:
                continue
            
            # IFC 버전 추출
            parts = ifc_file.parts
            version = "IFC4"
            for part in parts:
                if "IFC" in part.upper():
                    version = part.replace(" ", "_")
                    break
            
            # 새 파일명 생성
            new_name = f"buildingsmart_{version}_{ifc_file.stem}.ifc"
            dest_file = RAW_DIR / new_name
            
            # 이미 존재하는지 확인 (파일명으로)
            if not dest_file.exists():
                # 중복 확인 (기존 파일 중 같은 이름)
                existing = list(RAW_DIR.glob(f"buildingsmart_*{ifc_file.stem}*"))
                if not existing:
                    shutil.copy2(ifc_file, dest_file)
                    copied_count += 1
                    self.stats["ifc_count"] += 1
                    self.stats["total_size"] += file_size
                    
                    self.collected_files.append({
                        "path": str(dest_file.relative_to(PROJECT_ROOT)),
                        "source": "buildingSMART Sample-Test-Files",
                        "version": version,
                        "size": file_size,
                        "collected_at": datetime.now().isoformat()
                    })
        
        print(f"   ✅ {copied_count}개 파일 복사 완료")
        self.stats["sources"]["buildingSMART_IFC"] = copied_count
    
    def collect_bimserver_projects(self):
        """3. BIMserver Test Projects 수집"""
        print("\n" + "="*60)
        print("🖥️  3. BIMserver Test Projects 수집 중...")
        print("="*60)
        
        bimserver_dir = EXTERNAL_DIR / "opensource" / "opensourceBIM"
        
        if not bimserver_dir.exists():
            print(f"ℹ️  BIMserver 디렉토리를 찾을 수 없습니다: {bimserver_dir}")
            print(f"   (이 데이터셋은 선택사항입니다)")
            return
        
        # BIMserver 테스트 IFC 파일 찾기
        test_dir = bimserver_dir / "Tests"
        if test_dir.exists():
            ifc_files = list(test_dir.rglob("*.ifc"))
            print(f"   발견된 테스트 IFC 파일: {len(ifc_files)}개")
            
            copied_count = 0
            for ifc_file in ifc_files:
                file_size = ifc_file.stat().st_size
                if file_size < 100:
                    continue
                
                new_name = f"bimserver_test_{ifc_file.stem}.ifc"
                dest_file = RAW_DIR / new_name
                
                if not dest_file.exists():
                    shutil.copy2(ifc_file, dest_file)
                    copied_count += 1
                    self.stats["ifc_count"] += 1
                    self.stats["total_size"] += file_size
                    
                    self.collected_files.append({
                        "path": str(dest_file.relative_to(PROJECT_ROOT)),
                        "source": "BIMserver Test Projects",
                        "size": file_size,
                        "collected_at": datetime.now().isoformat()
                    })
            
            print(f"   ✅ {copied_count}개 파일 복사 완료")
            self.stats["sources"]["BIMserver"] = copied_count
        else:
            print(f"   ℹ️  Tests 디렉토리를 찾을 수 없습니다")
    
    def investigate_korea_molit_data(self):
        """4. 국토교통부 BIM 샘플 조사"""
        print("\n" + "="*60)
        print("🇰🇷 4. 국토교통부 BIM 샘플 조사...")
        print("="*60)
        
        korea_dir = EXTERNAL_DIR / "public_korea"
        
        if not korea_dir.exists():
            korea_dir.mkdir(parents=True, exist_ok=True)
            print(f"   📁 한국 공공데이터 디렉토리 생성: {korea_dir}")
        
        # 기존 파일 확인
        ifc_files = list(korea_dir.rglob("*.ifc"))
        bcf_files = list(korea_dir.rglob("*.bcf*"))
        
        if ifc_files or bcf_files:
            print(f"   발견된 IFC 파일: {len(ifc_files)}개")
            print(f"   발견된 BCF 파일: {len(bcf_files)}개")
            
            copied_count = 0
            for ifc_file in ifc_files:
                file_size = ifc_file.stat().st_size
                if file_size < 100:
                    continue
                
                new_name = f"korea_public_{ifc_file.stem}.ifc"
                dest_file = RAW_DIR / new_name
                
                if not dest_file.exists():
                    shutil.copy2(ifc_file, dest_file)
                    copied_count += 1
                    self.stats["ifc_count"] += 1
                    self.stats["total_size"] += file_size
            
            print(f"   ✅ {copied_count}개 파일 복사 완료")
            self.stats["sources"]["Korea_MOLIT"] = copied_count
        else:
            print(f"   ℹ️  현재 한국 공공데이터가 없습니다")
            print(f"   📝 수동 다운로드 안내:")
            print(f"      1. 공공데이터포털 (data.go.kr) 방문")
            print(f"      2. 'BIM', 'IFC', '건축정보모델' 검색")
            print(f"      3. 다운로드 후 {korea_dir}에 저장")
    
    def update_provenance(self):
        """데이터 출처 정보 업데이트"""
        print("\n" + "="*60)
        print("📝 데이터 출처 정보 업데이트 중...")
        print("="*60)
        
        # 기존 provenance 읽기
        provenance = {}
        if PROVENANCE_FILE.exists():
            with PROVENANCE_FILE.open("r", encoding="utf-8") as f:
                provenance = json.load(f)
        
        # 새 수집 정보 추가
        if "collections" not in provenance:
            provenance["collections"] = []
        
        provenance["collections"].append({
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 1 - Priority Datasets",
            "files_collected": len(self.collected_files),
            "stats": self.stats,
            "files": self.collected_files
        })
        
        # 저장
        PROVENANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PROVENANCE_FILE.open("w", encoding="utf-8") as f:
            json.dump(provenance, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Provenance 파일 업데이트 완료: {PROVENANCE_FILE}")
    
    def print_summary(self):
        """수집 결과 요약 출력"""
        print("\n" + "="*60)
        print("📊 Phase 1 데이터 수집 완료!")
        print("="*60)
        
        print(f"\n총 수집 파일: {len(self.collected_files)}개")
        print(f"  - IFC 파일: {self.stats['ifc_count']}개")
        print(f"  - BCF 파일: {self.stats['bcf_count']}개")
        print(f"  - 총 크기: {self.stats['total_size'] / 1024 / 1024:.2f} MB")
        
        print(f"\n소스별 분포:")
        for source, count in self.stats["sources"].items():
            print(f"  - {source}: {count}개")
        
        print(f"\n저장 위치: {RAW_DIR}")
        print(f"Provenance: {PROVENANCE_FILE}")
        
        # 다음 단계 안내
        print(f"\n" + "="*60)
        print("🚀 다음 단계:")
        print("="*60)
        print("1. 수집된 BCF 파일 처리:")
        print("   python scripts/process_all_data.py")
        print("")
        print("2. 데이터 품질 검증:")
        print("   python scripts/validate_data_credibility.py")
        print("")
        print("3. 그래프 재구축:")
        print("   make build_graph")


def main():
    """메인 실행 함수"""
    print("\n" + "🎯 " + "="*58)
    print("   Phase 1: 우선순위 데이터셋 수집 시작")
    print("   " + "="*58)
    
    # RAW_DIR 생성
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 수집기 초기화
    collector = Phase1DataCollector()
    
    # 데이터 수집 실행
    try:
        collector.collect_buildingsmart_bcf_testcases()
        collector.collect_buildingsmart_additional_ifc()
        collector.collect_bimserver_projects()
        collector.investigate_korea_molit_data()
        
        # Provenance 업데이트
        collector.update_provenance()
        
        # 결과 요약
        collector.print_summary()
        
        print("\n✅ Phase 1 데이터 수집이 성공적으로 완료되었습니다!")
        return 0
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

