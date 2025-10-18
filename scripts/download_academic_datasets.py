#!/usr/bin/env python3
"""
학술 BIM 데이터셋 다운로드 스크립트
작성일: 2025-10-15
용도: SLABIM, DURAARK, Schependomlaan 데이터셋 다운로드 시도
"""

import requests
import json
import time
import zipfile
import os
from pathlib import Path
from typing import Dict, List, Optional
import urllib.parse

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "external" / "academic"

class AcademicDatasetDownloader:
    """학술 BIM 데이터셋 다운로더"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.download_results = {
            "slabim": {"status": "pending", "details": {}},
            "duraark": {"status": "pending", "details": {}},
            "schependomlaan": {"status": "pending", "details": {}}
        }
    
    def setup_directories(self):
        """디렉토리 설정"""
        directories = [
            DATA_DIR / "slabim",
            DATA_DIR / "duraark", 
            DATA_DIR / "schependomlaan"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"📁 디렉토리 생성: {directory}")
    
    def download_slabim_dataset(self) -> Dict:
        """SLABIM 데이터셋 다운로드 시도"""
        print("🔍 SLABIM 데이터셋 다운로드 시도...")
        
        result = {
            "status": "failed",
            "message": "",
            "files_downloaded": [],
            "access_method": "manual_contact_required"
        }
        
        # GitHub 리포지토리 확인
        github_urls = [
            "https://github.com/hkust-vgd/slabim",
            "https://github.com/hkust-vgd/SLABIM",
            "https://api.github.com/repos/hkust-vgd/slabim"
        ]
        
        for url in github_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    if "api.github.com" in url:
                        repo_data = response.json()
                        result["github_info"] = {
                            "stars": repo_data.get("stargazers_count", 0),
                            "forks": repo_data.get("forks_count", 0),
                            "description": repo_data.get("description", "")
                        }
                    result["status"] = "github_accessible"
                    result["message"] = "GitHub 리포지토리 접근 가능, 수동 다운로드 필요"
                    break
            except Exception as e:
                continue
        
        if result["status"] == "failed":
            result["message"] = "GitHub 리포지토리 접근 불가, 학술 기관 직접 문의 필요"
        
        # HKUST 웹사이트 확인
        try:
            hkust_response = self.session.get("https://www.hkust.edu.hk/", timeout=10)
            if hkust_response.status_code == 200:
                result["institution_accessible"] = True
                result["contact_info"] = "HKUST 학술 기관에 직접 문의 필요"
        except:
            result["institution_accessible"] = False
        
        self.download_results["slabim"] = result
        return result
    
    def download_duraark_dataset(self) -> Dict:
        """DURAARK 데이터셋 다운로드 시도"""
        print("🔍 DURAARK 데이터셋 다운로드 시도...")
        
        result = {
            "status": "failed",
            "message": "",
            "files_downloaded": [],
            "access_method": "project_website"
        }
        
        # DURAARK 프로젝트 웹사이트 확인
        duraark_urls = [
            "http://duraark.eu/",
            "https://duraark.eu/",
            "http://www.duraark.eu/",
            "https://github.com/DURAARK"
        ]
        
        for url in duraark_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    result["status"] = "website_accessible"
                    result["message"] = "프로젝트 웹사이트 접근 가능"
                    result["accessible_url"] = url
                    
                    # 데이터 다운로드 링크 찾기 시도
                    if "github.com" in url:
                        # GitHub API로 리포지토리 정보 확인
                        api_url = url.replace("github.com", "api.github.com/repos")
                        api_response = self.session.get(api_url, timeout=10)
                        if api_response.status_code == 200:
                            repo_data = api_response.json()
                            result["github_info"] = {
                                "stars": repo_data.get("stargazers_count", 0),
                                "forks": repo_data.get("forks_count", 0),
                                "description": repo_data.get("description", "")
                            }
                    break
            except Exception as e:
                continue
        
        if result["status"] == "failed":
            result["message"] = "프로젝트 웹사이트 접근 불가"
        
        self.download_results["duraark"] = result
        return result
    
    def download_schependomlaan_dataset(self) -> Dict:
        """Schependomlaan 데이터셋 다운로드 시도"""
        print("🔍 Schependomlaan 데이터셋 다운로드 시도...")
        
        result = {
            "status": "failed",
            "message": "",
            "files_downloaded": [],
            "access_method": "academic_inquiry"
        }
        
        # TU Eindhoven 웹사이트 확인
        tue_urls = [
            "https://www.tue.nl/",
            "https://research.tue.nl/",
            "https://pure.tue.nl/",
            "https://data.4tu.nl/"
        ]
        
        for url in tue_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    result["status"] = "institution_accessible"
                    result["message"] = "TU Eindhoven 웹사이트 접근 가능"
                    result["accessible_url"] = url
                    
                    if "data.4tu.nl" in url:
                        result["data_portal"] = "4TU 데이터 포털 접근 가능"
                    break
            except Exception as e:
                continue
        
        if result["status"] == "failed":
            result["message"] = "TU Eindhoven 웹사이트 접근 불가"
        
        # 학술 문의 정보 추가
        result["contact_info"] = {
            "institution": "TU Eindhoven",
            "department": "Built Environment",
            "contact_method": "학술 연구 문의 필요",
            "expected_response_time": "1-2주"
        }
        
        self.download_results["schependomlaan"] = result
        return result
    
    def generate_contact_templates(self):
        """학술 기관 문의 템플릿 생성"""
        templates_dir = DATA_DIR / "contact_templates"
        templates_dir.mkdir(exist_ok=True)
        
        # SLABIM 문의 템플릿
        slabim_template = """Subject: Request for SLABIM Dataset Access for Academic Research

Dear HKUST Research Team,

I am conducting research on "Contextual Forgetting Mechanisms for Graph-based Retrieval Augmented Generation in BIM Domain" and would like to request access to the SLABIM dataset for academic purposes.

Research Overview:
- Topic: Graph-RAG with contextual forgetting for BIM
- Institution: [Your Institution]
- Advisor: [Your Advisor]
- Expected Publication: [Conference/Journal]

The dataset will be used solely for academic research and will be properly cited in all publications.

Could you please provide access to the SLABIM dataset or guide me through the application process?

Thank you for your consideration.

Best regards,
[Your Name]
[Your Email]
[Your Institution]
"""
        
        # DURAARK 문의 템플릿
        duraark_template = """Subject: Request for DURAARK Dataset Access for Academic Research

Dear DURAARK Project Team,

I am conducting research on "Contextual Forgetting Mechanisms for Graph-based Retrieval Augmented Generation in BIM Domain" and would like to request access to the DURAARK dataset for academic purposes.

Research Overview:
- Topic: Graph-RAG with contextual forgetting for BIM
- Institution: [Your Institution]
- Advisor: [Your Advisor]
- Expected Publication: [Conference/Journal]

The dataset will be used solely for academic research and will be properly cited in all publications.

Could you please provide access to the DURAARK dataset or guide me through the application process?

Thank you for your consideration.

Best regards,
[Your Name]
[Your Email]
[Your Institution]
"""
        
        # Schependomlaan 문의 템플릿
        schependomlaan_template = """Subject: Request for Schependomlaan Dataset Access for Academic Research

Dear TU Eindhoven Research Team,

I am conducting research on "Contextual Forgetting Mechanisms for Graph-based Retrieval Augmented Generation in BIM Domain" and would like to request access to the Schependomlaan dataset for academic purposes.

Research Overview:
- Topic: Graph-RAG with contextual forgetting for BIM
- Institution: [Your Institution]
- Advisor: [Your Advisor]
- Expected Publication: [Conference/Journal]

The dataset will be used solely for academic research and will be properly cited in all publications.

Could you please provide access to the Schependomlaan dataset or guide me through the application process?

Thank you for your consideration.

Best regards,
[Your Name]
[Your Email]
[Your Institution]
"""
        
        # 템플릿 저장
        with open(templates_dir / "slabim_contact_template.txt", 'w', encoding='utf-8') as f:
            f.write(slabim_template)
        
        with open(templates_dir / "duraark_contact_template.txt", 'w', encoding='utf-8') as f:
            f.write(duraark_template)
        
        with open(templates_dir / "schependomlaan_contact_template.txt", 'w', encoding='utf-8') as f:
            f.write(schependomlaan_template)
        
        print(f"📧 문의 템플릿 생성: {templates_dir}")
    
    def save_download_results(self):
        """다운로드 결과 저장"""
        results_file = DATA_DIR / "download_results.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.download_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 다운로드 결과 저장: {results_file}")
        
        # 요약 보고서 생성
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """요약 보고서 생성"""
        report_file = DATA_DIR / "DOWNLOAD_SUMMARY.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 학술 데이터셋 다운로드 요약 보고서\n\n")
            f.write("**작성일**: 2025년 10월 15일\n\n")
            
            f.write("## 다운로드 결과\n\n")
            
            for dataset, result in self.download_results.items():
                f.write(f"### {dataset.upper()}\n")
                f.write(f"- **상태**: {result['status']}\n")
                f.write(f"- **메시지**: {result['message']}\n")
                f.write(f"- **접근 방법**: {result['access_method']}\n")
                if 'accessible_url' in result:
                    f.write(f"- **접근 가능 URL**: {result['accessible_url']}\n")
                f.write("\n")
            
            f.write("## 다음 단계\n\n")
            f.write("1. **Schependomlaan 데이터셋** (1순위): TU Eindhoven에 학술 문의\n")
            f.write("2. **SLABIM 데이터셋** (2순위): HKUST에 학술 문의\n")
            f.write("3. **DURAARK 데이터셋** (3순위): 프로젝트 웹사이트 확인\n")
            f.write("4. 문의 템플릿 사용하여 각 기관에 이메일 발송\n")
            f.write("5. 승인 대기 (1-2주 예상)\n")
            f.write("6. 데이터 수신 후 프로젝트 통합\n\n")
            
            f.write("## 문의 템플릿 위치\n\n")
            f.write("- `data/external/academic/contact_templates/` 디렉토리에 문의 템플릿 저장됨\n")
            f.write("- 각 데이터셋별로 맞춤형 문의 템플릿 제공\n")
        
        print(f"📄 요약 보고서 생성: {report_file}")
    
    def run_download_attempt(self):
        """다운로드 시도 실행"""
        print("🚀 학술 데이터셋 다운로드 시도 시작...\n")
        
        # 디렉토리 설정
        self.setup_directories()
        
        # 각 데이터셋 다운로드 시도
        self.download_slabim_dataset()
        self.download_duraark_dataset()
        self.download_schependomlaan_dataset()
        
        # 문의 템플릿 생성
        self.generate_contact_templates()
        
        # 결과 저장
        self.save_download_results()
        
        print("\n✅ 다운로드 시도 완료!")
        print("📊 결과 요약:")
        for dataset, result in self.download_results.items():
            print(f"   - {dataset}: {result['status']} - {result['message']}")
        
        print("\n📧 다음 단계:")
        print("   1. contact_templates/ 디렉토리의 문의 템플릿 확인")
        print("   2. 각 학술 기관에 이메일 발송")
        print("   3. 승인 대기 (1-2주)")
        print("   4. 데이터 수신 후 통합 작업")

def main():
    """메인 함수"""
    downloader = AcademicDatasetDownloader()
    downloader.run_download_attempt()

if __name__ == "__main__":
    main()
