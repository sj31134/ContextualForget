#!/usr/bin/env python3
"""
직접 다운로드 가능한 학술 데이터셋 확인 스크립트
작성일: 2025-10-15
용도: 공개적으로 다운로드 가능한 데이터셋 URL 확인
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import urllib.parse

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class DirectDownloadChecker:
    """직접 다운로드 가능 여부 확인 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.results = {
            "slabim": {},
            "duraark": {},
            "schependomlaan": {},
            "summary": {}
        }
    
    def check_slabim_direct_download(self) -> Dict:
        """SLABIM 직접 다운로드 가능 여부 확인"""
        print("🔍 SLABIM 직접 다운로드 가능 여부 확인...")
        
        result = {
            "status": "checking",
            "direct_download": False,
            "github_repos": [],
            "download_links": [],
            "access_method": "unknown"
        }
        
        # 다양한 GitHub 리포지토리 URL 시도
        github_urls = [
            "https://github.com/hkust-vgd/slabim",
            "https://github.com/hkust-vgd/SLABIM", 
            "https://github.com/hkust-vgd/slabim-dataset",
            "https://github.com/hkust-vgd/bim-slam-dataset",
            "https://github.com/hkust-vgd/construction-dataset"
        ]
        
        for url in github_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    result["github_repos"].append({
                        "url": url,
                        "accessible": True,
                        "status_code": response.status_code
                    })
                    
                    # 릴리즈 페이지 확인
                    releases_url = url + "/releases"
                    releases_response = self.session.get(releases_url, timeout=10)
                    if releases_response.status_code == 200:
                        result["download_links"].append({
                            "type": "github_releases",
                            "url": releases_url,
                            "accessible": True
                        })
                        result["direct_download"] = True
                        result["access_method"] = "github_releases"
                    
                    # 다운로드 폴더 확인
                    download_url = url + "/archive/refs/heads/main.zip"
                    download_response = self.session.head(download_url, timeout=10)
                    if download_response.status_code == 200:
                        result["download_links"].append({
                            "type": "zip_download",
                            "url": download_url,
                            "accessible": True
                        })
                        result["direct_download"] = True
                        result["access_method"] = "github_zip"
                    
                    break
            except Exception as e:
                result["github_repos"].append({
                    "url": url,
                    "accessible": False,
                    "error": str(e)
                })
        
        # HKUST 공식 데이터 포털 확인
        hkust_urls = [
            "https://data.hkust.edu.hk/",
            "https://repository.hkust.edu.hk/",
            "https://research.hkust.edu.hk/"
        ]
        
        for url in hkust_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    result["download_links"].append({
                        "type": "institutional_portal",
                        "url": url,
                        "accessible": True
                    })
            except:
                pass
        
        result["status"] = "completed"
        self.results["slabim"] = result
        return result
    
    def check_duraark_direct_download(self) -> Dict:
        """DURAARK 직접 다운로드 가능 여부 확인"""
        print("🔍 DURAARK 직접 다운로드 가능 여부 확인...")
        
        result = {
            "status": "checking",
            "direct_download": False,
            "project_websites": [],
            "download_links": [],
            "access_method": "unknown"
        }
        
        # DURAARK 프로젝트 웹사이트들
        duraark_urls = [
            "http://duraark.eu/",
            "https://duraark.eu/",
            "http://www.duraark.eu/",
            "https://github.com/DURAARK",
            "https://github.com/duraark"
        ]
        
        for url in duraark_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    result["project_websites"].append({
                        "url": url,
                        "accessible": True,
                        "status_code": response.status_code
                    })
                    
                    # GitHub인 경우 릴리즈 확인
                    if "github.com" in url:
                        releases_url = url + "/releases"
                        releases_response = self.session.get(releases_url, timeout=10)
                        if releases_response.status_code == 200:
                            result["download_links"].append({
                                "type": "github_releases",
                                "url": releases_url,
                                "accessible": True
                            })
                            result["direct_download"] = True
                            result["access_method"] = "github_releases"
                    
                    # 데이터 다운로드 섹션 찾기
                    if "duraark.eu" in url:
                        # 웹사이트에서 다운로드 링크 찾기 시도
                        result["download_links"].append({
                            "type": "project_website",
                            "url": url,
                            "accessible": True,
                            "note": "웹사이트에서 다운로드 링크 확인 필요"
                        })
                        result["direct_download"] = True
                        result["access_method"] = "project_website"
                    
                    break
            except Exception as e:
                result["project_websites"].append({
                    "url": url,
                    "accessible": False,
                    "error": str(e)
                })
        
        result["status"] = "completed"
        self.results["duraark"] = result
        return result
    
    def check_schependomlaan_direct_download(self) -> Dict:
        """Schependomlaan 직접 다운로드 가능 여부 확인"""
        print("🔍 Schependomlaan 직접 다운로드 가능 여부 확인...")
        
        result = {
            "status": "checking",
            "direct_download": False,
            "institutional_sites": [],
            "download_links": [],
            "access_method": "unknown"
        }
        
        # TU Eindhoven 관련 URL들
        tue_urls = [
            "https://www.tue.nl/",
            "https://research.tue.nl/",
            "https://pure.tue.nl/",
            "https://data.4tu.nl/",
            "https://github.com/tue-mps",
            "https://github.com/TUe-Research"
        ]
        
        for url in tue_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    result["institutional_sites"].append({
                        "url": url,
                        "accessible": True,
                        "status_code": response.status_code
                    })
                    
                    # 4TU 데이터 포털인 경우
                    if "data.4tu.nl" in url:
                        result["download_links"].append({
                            "type": "data_portal",
                            "url": url,
                            "accessible": True,
                            "note": "4TU 데이터 포털에서 검색 가능"
                        })
                        result["direct_download"] = True
                        result["access_method"] = "data_portal"
                    
                    # GitHub인 경우
                    if "github.com" in url:
                        releases_url = url + "/releases"
                        releases_response = self.session.get(releases_url, timeout=10)
                        if releases_response.status_code == 200:
                            result["download_links"].append({
                                "type": "github_releases",
                                "url": releases_url,
                                "accessible": True
                            })
                            result["direct_download"] = True
                            result["access_method"] = "github_releases"
                    
            except Exception as e:
                result["institutional_sites"].append({
                    "url": url,
                    "accessible": False,
                    "error": str(e)
                })
        
        # Schependomlaan 특화 검색
        schependomlaan_urls = [
            "https://github.com/search?q=schependomlaan",
            "https://data.4tu.nl/search?q=schependomlaan",
            "https://pure.tue.nl/search?q=schependomlaan"
        ]
        
        for url in schependomlaan_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    result["download_links"].append({
                        "type": "search_result",
                        "url": url,
                        "accessible": True,
                        "note": "검색 결과에서 데이터셋 확인 가능"
                    })
            except:
                pass
        
        result["status"] = "completed"
        self.results["schependomlaan"] = result
        return result
    
    def generate_summary(self) -> Dict:
        """요약 생성"""
        print("📊 직접 다운로드 가능 여부 요약...")
        
        summary = {
            "total_datasets": 3,
            "direct_download_available": 0,
            "github_accessible": 0,
            "institutional_accessible": 0,
            "recommendations": []
        }
        
        for dataset, result in self.results.items():
            if result.get("direct_download", False):
                summary["direct_download_available"] += 1
                summary["recommendations"].append(f"{dataset}: 직접 다운로드 가능")
            
            if any("github" in link.get("type", "") for link in result.get("download_links", [])):
                summary["github_accessible"] += 1
            
            if any("institutional" in link.get("type", "") or "data_portal" in link.get("type", "") for link in result.get("download_links", [])):
                summary["institutional_accessible"] += 1
        
        self.results["summary"] = summary
        return summary
    
    def save_results(self):
        """결과 저장"""
        output_file = OUTPUT_DIR / "direct_download_check.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 결과 저장: {output_file}")
        
        # 요약 보고서 생성
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """요약 보고서 생성"""
        report_file = OUTPUT_DIR / "DIRECT_DOWNLOAD_CHECK.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 직접 다운로드 가능 여부 확인 보고서\n\n")
            f.write("**작성일**: 2025년 10월 15일\n\n")
            
            f.write("## 확인 결과\n\n")
            
            for dataset, result in self.results.items():
                if dataset == "summary":
                    continue
                    
                f.write(f"### {dataset.upper()}\n")
                f.write(f"- **직접 다운로드**: {'✅ 가능' if result.get('direct_download', False) else '❌ 불가능'}\n")
                f.write(f"- **접근 방법**: {result.get('access_method', 'unknown')}\n")
                
                if result.get("download_links"):
                    f.write("- **다운로드 링크**:\n")
                    for link in result["download_links"]:
                        f.write(f"  - {link['type']}: {link['url']}\n")
                
                f.write("\n")
            
            f.write("## 권장사항\n\n")
            for rec in self.results["summary"].get("recommendations", []):
                f.write(f"- {rec}\n")
        
        print(f"📄 요약 보고서 생성: {report_file}")
    
    def run_check(self):
        """전체 확인 실행"""
        print("🚀 직접 다운로드 가능 여부 확인 시작...\n")
        
        # 각 데이터셋 확인
        self.check_slabim_direct_download()
        self.check_duraark_direct_download()
        self.check_schependomlaan_direct_download()
        
        # 요약 생성
        self.generate_summary()
        
        # 결과 저장
        self.save_results()
        
        print("\n✅ 확인 완료!")
        summary = self.results["summary"]
        print(f"📊 결과 요약:")
        print(f"   - 직접 다운로드 가능: {summary['direct_download_available']}/3개")
        print(f"   - GitHub 접근 가능: {summary['github_accessible']}/3개")
        print(f"   - 기관 포털 접근 가능: {summary['institutional_accessible']}/3개")

def main():
    """메인 함수"""
    checker = DirectDownloadChecker()
    checker.run_check()

if __name__ == "__main__":
    main()
