#!/usr/bin/env python3
"""
종합 데이터 수집 스크립트
- buildingSMART 공식 샘플
- GitHub 오픈소스 저장소
- Academic 데이터셋
- 공공 데이터
"""

import os
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
import urllib.request
import zipfile
import tarfile


class DataCollector:
    """데이터 수집 관리자"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.external_dir = self.base_dir / "data" / "external"
        self.raw_dir = self.base_dir / "data" / "raw" / "downloaded"
        
        # 수집 로그
        self.collection_log = {
            "timestamp": datetime.now().isoformat(),
            "sources": [],
            "statistics": {}
        }
    
    def download_buildingsmart_samples(self):
        """buildingSMART 공식 샘플 다운로드"""
        print("=" * 60)
        print("📥 buildingSMART 공식 샘플 다운로드")
        print("=" * 60)
        
        target_dir = self.external_dir / "buildingsmart"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Sample-Test-Files 저장소 클론
        repo_url = "https://github.com/buildingSMART/Sample-Test-Files.git"
        repo_dir = target_dir / "Sample-Test-Files"
        
        if repo_dir.exists():
            print(f"  ⚠️  {repo_dir} 이미 존재합니다. 업데이트 중...")
            subprocess.run(["git", "pull"], cwd=repo_dir)
        else:
            print(f"  📦 클론 중: {repo_url}")
            subprocess.run(["git", "clone", "--depth", "1", repo_url, str(repo_dir)])
        
        # IFC 파일 복사
        ifc_files = list(repo_dir.rglob("*.ifc"))
        print(f"\n  발견된 IFC 파일: {len(ifc_files)}개")
        
        copied_count = 0
        for ifc_file in ifc_files:
            if ifc_file.stat().st_size > 100:  # 100 바이트 이상만
                dest = self.raw_dir / f"buildingsmart_{ifc_file.name}"
                shutil.copy2(ifc_file, dest)
                copied_count += 1
                print(f"    ✅ {ifc_file.name} ({ifc_file.stat().st_size / 1024:.1f} KB)")
        
        print(f"\n  총 복사: {copied_count}개")
        
        self.collection_log["sources"].append({
            "name": "buildingSMART Sample-Test-Files",
            "url": repo_url,
            "files_count": copied_count,
            "type": "IFC"
        })
        
        return copied_count
    
    def download_bcf_examples(self):
        """BCF 예제 다운로드"""
        print("\n" + "=" * 60)
        print("📥 buildingSMART BCF 예제 다운로드")
        print("=" * 60)
        
        target_dir = self.external_dir / "buildingsmart"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # BCF-XML 저장소 클론
        repo_url = "https://github.com/buildingSMART/BCF-XML.git"
        repo_dir = target_dir / "BCF-XML"
        
        if repo_dir.exists():
            print(f"  ⚠️  {repo_dir} 이미 존재합니다. 업데이트 중...")
            subprocess.run(["git", "pull"], cwd=repo_dir)
        else:
            print(f"  📦 클론 중: {repo_url}")
            subprocess.run(["git", "clone", "--depth", "1", repo_url, str(repo_dir)])
        
        # BCF 파일 복사 (Samples 디렉토리)
        samples_dir = repo_dir / "Samples"
        if not samples_dir.exists():
            # release_2_1 브랜치 시도
            samples_dir = repo_dir / "release_2_1" / "Samples"
        
        bcf_files = []
        if samples_dir.exists():
            bcf_files = list(samples_dir.rglob("*.bcf*"))
        
        print(f"\n  발견된 BCF 파일: {len(bcf_files)}개")
        
        copied_count = 0
        for bcf_file in bcf_files:
            dest = self.raw_dir / f"buildingsmart_{bcf_file.name}"
            shutil.copy2(bcf_file, dest)
            copied_count += 1
            print(f"    ✅ {bcf_file.name} ({bcf_file.stat().st_size / 1024:.1f} KB)")
        
        print(f"\n  총 복사: {copied_count}개")
        
        self.collection_log["sources"].append({
            "name": "buildingSMART BCF-XML Examples",
            "url": repo_url,
            "files_count": copied_count,
            "type": "BCF"
        })
        
        return copied_count
    
    def download_opensource_bim(self):
        """오픈소스 BIM 프로젝트 다운로드"""
        print("\n" + "=" * 60)
        print("📥 GitHub 오픈소스 BIM 프로젝트")
        print("=" * 60)
        
        target_dir = self.external_dir / "opensource"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        repos = [
            {
                "name": "opensourceBIM",
                "url": "https://github.com/opensourceBIM/BIMserver.git",
                "branch": "master"
            },
            {
                "name": "IFC-files-collection",
                "url": "https://github.com/stephensmitchell-forks/IFC-files.git",
                "branch": "master"
            }
        ]
        
        total_files = 0
        
        for repo_info in repos:
            repo_dir = target_dir / repo_info["name"]
            
            if repo_dir.exists():
                print(f"\n  ⚠️  {repo_info['name']} 이미 존재합니다.")
                continue
            
            print(f"\n  📦 클론 중: {repo_info['name']}")
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_info["url"], str(repo_dir)],
                    timeout=300,
                    check=False
                )
                
                # IFC 파일 찾기
                ifc_files = list(repo_dir.rglob("*.ifc"))
                print(f"    발견: {len(ifc_files)}개 IFC 파일")
                
                # 큰 파일만 복사 (1KB 이상)
                for ifc_file in ifc_files[:10]:  # 처음 10개만
                    if ifc_file.stat().st_size > 1024:
                        dest = self.raw_dir / f"{repo_info['name']}_{ifc_file.name}"
                        shutil.copy2(ifc_file, dest)
                        total_files += 1
                
            except Exception as e:
                print(f"    ❌ 오류: {e}")
        
        self.collection_log["sources"].append({
            "name": "GitHub OpenSource BIM Projects",
            "files_count": total_files,
            "type": "IFC"
        })
        
        return total_files
    
    def download_direct_urls(self):
        """직접 URL에서 다운로드"""
        print("\n" + "=" * 60)
        print("📥 직접 URL 다운로드")
        print("=" * 60)
        
        # 알려진 공개 IFC 파일 URL들
        urls = [
            # IFC 공식 예제
            "https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcxml/examples/example-01.ifcXML",
            "https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcxml/examples/example-02.ifcXML",
        ]
        
        downloaded = 0
        
        for url in urls:
            filename = url.split("/")[-1]
            dest = self.raw_dir / filename
            
            try:
                print(f"\n  📥 다운로드: {filename}")
                urllib.request.urlretrieve(url, dest)
                print(f"    ✅ 완료 ({dest.stat().st_size / 1024:.1f} KB)")
                downloaded += 1
            except Exception as e:
                print(f"    ❌ 실패: {e}")
        
        return downloaded
    
    def analyze_collected_data(self):
        """수집된 데이터 분석"""
        print("\n" + "=" * 60)
        print("📊 수집된 데이터 분석")
        print("=" * 60)
        
        ifc_files = list(self.raw_dir.glob("*.ifc*"))
        bcf_files = list(self.raw_dir.glob("*.bcf*"))
        
        # IFC 분석
        ifc_stats = {
            "count": len(ifc_files),
            "total_size_mb": sum(f.stat().st_size for f in ifc_files) / 1024 / 1024,
            "files": []
        }
        
        print(f"\n📐 IFC 파일: {len(ifc_files)}개")
        for ifc_file in sorted(ifc_files, key=lambda x: x.stat().st_size, reverse=True)[:20]:
            size_kb = ifc_file.stat().st_size / 1024
            print(f"  - {ifc_file.name[:50]:<50} {size_kb:>10.1f} KB")
            ifc_stats["files"].append({
                "name": ifc_file.name,
                "size_kb": size_kb
            })
        
        # BCF 분석
        bcf_stats = {
            "count": len(bcf_files),
            "total_size_mb": sum(f.stat().st_size for f in bcf_files) / 1024 / 1024,
            "files": []
        }
        
        print(f"\n📋 BCF 파일: {len(bcf_files)}개")
        for bcf_file in sorted(bcf_files, key=lambda x: x.stat().st_size, reverse=True)[:20]:
            size_kb = bcf_file.stat().st_size / 1024
            print(f"  - {bcf_file.name[:50]:<50} {size_kb:>10.1f} KB")
            bcf_stats["files"].append({
                "name": bcf_file.name,
                "size_kb": size_kb
            })
        
        self.collection_log["statistics"] = {
            "ifc": ifc_stats,
            "bcf": bcf_stats,
            "total_files": len(ifc_files) + len(bcf_files)
        }
        
        # 로그 저장
        log_path = self.base_dir / "data" / "analysis" / "collection_log.json"
        with open(log_path, 'w') as f:
            json.dump(self.collection_log, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 수집 로그 저장: {log_path}")
        
        return ifc_stats, bcf_stats
    
    def create_summary_report(self):
        """요약 보고서 생성"""
        print("\n" + "=" * 60)
        print("📝 데이터 수집 요약 보고서")
        print("=" * 60)
        
        stats = self.collection_log["statistics"]
        
        print(f"""
📊 수집 결과:
  - IFC 파일: {stats['ifc']['count']}개 ({stats['ifc']['total_size_mb']:.2f} MB)
  - BCF 파일: {stats['bcf']['count']}개 ({stats['bcf']['total_size_mb']:.2f} MB)
  - 총 파일: {stats['total_files']}개

📂 데이터 소스: {len(self.collection_log['sources'])}개
""")
        
        for source in self.collection_log["sources"]:
            print(f"  ✅ {source['name']}: {source['files_count']}개 {source['type']} 파일")
        
        # 권장사항
        print(f"""
\n🎯 데이터 충분성 평가:
  - 현재 IFC: {stats['ifc']['count']}개
  - 목표 IFC: 15-25개 (최소 요구)
  - 상태: {"✅ 충족" if stats['ifc']['count'] >= 15 else "⚠️ 추가 필요"}
  
  - 현재 BCF: {stats['bcf']['count']}개
  - 목표 BCF: 30-50개 (최소 요구)
  - 상태: {"✅ 충족" if stats['bcf']['count'] >= 30 else "⚠️ 추가 필요"}
""")


def main():
    """메인 실행"""
    base_dir = Path(__file__).parent.parent
    collector = DataCollector(base_dir)
    
    print("🚀 ContextualForget 데이터 수집 시작")
    print(f"📁 기본 디렉토리: {base_dir}")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Phase 0: buildingSMART 공식
        ifc_count = collector.download_buildingsmart_samples()
        bcf_count = collector.download_bcf_examples()
        
        # Phase 1: GitHub 오픈소스
        opensource_count = collector.download_opensource_bim()
        
        # Phase 2: 직접 URL
        # direct_count = collector.download_direct_urls()
        
        # 분석
        collector.analyze_collected_data()
        
        # 요약
        collector.create_summary_report()
        
        print(f"\n✨ 데이터 수집 완료!")
        print(f"⏰ 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

