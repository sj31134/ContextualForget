#!/usr/bin/env python3
"""추가 데이터 소스 수집 스크립트"""

import os
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
import urllib.request


class AdditionalDataCollector:
    """추가 데이터 수집"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "data" / "raw" / "downloaded"
        self.external_dir = self.base_dir / "data" / "external"
        
    def download_ifc_tools_samples(self):
        """IFC 도구 샘플 파일들"""
        print("=" * 60)
        print("📥 IFC 도구 샘플 파일 수집")
        print("=" * 60)
        
        repos = [
            {
                "name": "IfcOpenShell-files",
                "url": "https://github.com/IfcOpenShell/IfcOpenShell.git",
                "path": "test/input"
            },
            {
                "name": "xBIM-Samples",
                "url": "https://github.com/xBimTeam/XbimSamples.git",
                "path": "SampleFiles"
            }
        ]
        
        total = 0
        
        for repo in repos:
            target_dir = self.external_dir / "opensource" / repo["name"]
            
            if target_dir.exists():
                print(f"\n  ⚠️  {repo['name']} 이미 존재")
                # IFC 파일만 찾아서 복사
                ifc_files = list(target_dir.rglob("*.ifc"))
            else:
                print(f"\n  📦 클론: {repo['name']}")
                try:
                    subprocess.run(
                        ["git", "clone", "--depth", "1", repo["url"], str(target_dir)],
                        timeout=300,
                        check=True
                    )
                    ifc_files = list(target_dir.rglob("*.ifc"))
                except Exception as e:
                    print(f"    ❌ 실패: {e}")
                    continue
            
            # 복사
            for ifc_file in ifc_files:
                if ifc_file.stat().st_size > 1024:  # 1KB 이상
                    dest = self.raw_dir / f"{repo['name']}_{ifc_file.name}"
                    shutil.copy2(ifc_file, dest)
                    total += 1
                    print(f"    ✅ {ifc_file.name} ({ifc_file.stat().st_size / 1024:.1f} KB)")
        
        return total
    
    def download_bimserver_samples(self):
        """BIMserver 샘플 프로젝트"""
        print("\n" + "=" * 60)
        print("📥 BIMserver 샘플 프로젝트")
        print("=" * 60)
        
        repo_url = "https://github.com/opensourceBIM/BIMserver-JavaScript-API.git"
        target_dir = self.external_dir / "opensource" / "BIMserver-JS"
        
        if not target_dir.exists():
            print(f"  📦 클론: BIMserver-JavaScript-API")
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
                    timeout=300,
                    check=True
                )
            except Exception as e:
                print(f"    ❌ 실패: {e}")
                return 0
        
        # IFC 파일 찾기
        ifc_files = list(target_dir.rglob("*.ifc"))
        total = 0
        
        for ifc_file in ifc_files:
            if ifc_file.stat().st_size > 1024:
                dest = self.raw_dir / f"bimserver_{ifc_file.name}"
                shutil.copy2(ifc_file, dest)
                total += 1
                print(f"    ✅ {ifc_file.name}")
        
        return total
    
    def create_synthetic_bcf_data(self):
        """합성 BCF 데이터 생성 (기존 IFC 기반)"""
        print("\n" + "=" * 60)
        print("🔧 합성 BCF 데이터 생성")
        print("=" * 60)
        
        # 기존 스크립트 활용
        script_path = self.base_dir / "scripts" / "generate_sample_data.py"
        
        if script_path.exists():
            print(f"  🔄 기존 생성 스크립트 실행...")
            subprocess.run(["python", str(script_path)])
            
            # 생성된 BCF 파일 복사
            bcf_files = list((self.base_dir / "data" / "raw").glob("*_issues.bcfzip"))
            for bcf_file in bcf_files:
                dest = self.raw_dir / bcf_file.name
                shutil.copy2(bcf_file, dest)
                print(f"    ✅ {bcf_file.name}")
            
            return len(bcf_files)
        else:
            print("  ⚠️  생성 스크립트를 찾을 수 없습니다")
            return 0
    
    def download_academic_datasets(self):
        """학술 데이터셋 정보 출력"""
        print("\n" + "=" * 60)
        print("📚 학술 데이터셋 안내")
        print("=" * 60)
        
        datasets = [
            {
                "name": "BIMPROVE Dataset",
                "url": "http://www.bimprove.eu",
                "access": "연구 목적 신청 필요",
                "contact": "research@bimprove.eu",
                "data": "5개 실제 건설 프로젝트, 시간별 버전"
            },
            {
                "name": "Stanford Digital Repository",
                "url": "https://purl.stanford.edu/",
                "access": "공개 (검색 필요)",
                "search": "BIM, IFC, Building Information",
                "data": "15+ 건축 아카이브"
            },
            {
                "name": "TU Delft BIM Repository",
                "url": "https://data.4tu.nl/",
                "access": "공개",
                "search": "BIM, IFC",
                "data": "연구용 BIM 모델"
            }
        ]
        
        print("\n📝 아래 학술 데이터셋은 수동 신청이 필요합니다:\n")
        
        for ds in datasets:
            print(f"  📚 {ds['name']}")
            print(f"     URL: {ds['url']}")
            print(f"     접근: {ds['access']}")
            if 'contact' in ds:
                print(f"     연락: {ds['contact']}")
            if 'search' in ds:
                print(f"     검색어: {ds['search']}")
            print(f"     데이터: {ds['data']}")
            print()
        
        # 신청 템플릿 생성
        template_path = self.base_dir / "data" / "analysis" / "academic_request_template.txt"
        with open(template_path, 'w') as f:
            f.write("""Subject: Request for BIM Dataset Access for Research Purpose

Dear [Dataset Manager],

I am writing to request access to [Dataset Name] for academic research purposes.

Research Project: ContextualForget - Long-Term Memory Management for BIM Digital Twins
Institution: [Your Institution]
Supervisor: [Your Supervisor]

Research Objective:
We are developing a Graph-RAG system that integrates IFC and BCF data with 
adaptive forgetting mechanisms to manage long-term memory in BIM digital twins.

Data Usage:
- Academic research only
- Publication in peer-reviewed conferences/journals
- Open-source implementation (code only, not proprietary data)

We will properly cite your dataset and acknowledge your contribution.

Thank you for your consideration.

Best regards,
[Your Name]
[Your Email]
[Your Affiliation]
""")
        
        print(f"✅ 신청 템플릿 생성: {template_path}")


def main():
    base_dir = Path(__file__).parent.parent
    collector = AdditionalDataCollector(base_dir)
    
    print("🚀 추가 데이터 수집 시작\n")
    
    # IFC 도구 샘플
    ifc_count = collector.download_ifc_tools_samples()
    print(f"\n  총 IFC 도구 샘플: {ifc_count}개")
    
    # BIMserver 샘플
    bimserver_count = collector.download_bimserver_samples()
    print(f"\n  총 BIMserver 샘플: {bimserver_count}개")
    
    # 합성 BCF
    bcf_count = collector.create_synthetic_bcf_data()
    print(f"\n  총 합성 BCF: {bcf_count}개")
    
    # 학술 데이터셋 안내
    collector.download_academic_datasets()
    
    print("\n✨ 추가 데이터 수집 완료!")


if __name__ == "__main__":
    main()

