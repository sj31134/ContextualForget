#!/usr/bin/env python3
"""
직접 다운로드 가능한 학술 데이터셋 다운로드 스크립트
작성일: 2025-10-15
용도: DURAARK, Schependomlaan 데이터셋 직접 다운로드
"""

import requests
import json
import time
import os
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
import urllib.parse
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "external" / "academic"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class DatasetDownloader:
    """데이터셋 다운로더 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.download_results = {}
    
    def download_duraark_dataset(self) -> Dict:
        """DURAARK 데이터셋 다운로드"""
        print("📥 DURAARK 데이터셋 다운로드 시작...")
        
        result = {
            "status": "downloading",
            "downloaded_files": [],
            "total_size": 0,
            "errors": []
        }
        
        duraark_dir = DATA_DIR / "duraark"
        duraark_dir.mkdir(exist_ok=True)
        
        # DURAARK 웹사이트에서 다운로드 링크 찾기
        try:
            response = self.session.get("http://duraark.eu/", timeout=30)
            if response.status_code == 200:
                # 웹사이트 내용에서 다운로드 링크 찾기
                content = response.text.lower()
                
                # 일반적인 다운로드 키워드 찾기
                download_keywords = [
                    "download", "data", "dataset", "ifc", "bim", 
                    "medical clinic", "duraark", "zip", "tar.gz"
                ]
                
                # 웹사이트에서 직접 링크 찾기 시도
                import re
                links = re.findall(r'href="([^"]*)"', response.text)
                
                for link in links:
                    if any(keyword in link.lower() for keyword in download_keywords):
                        if link.startswith('/'):
                            full_url = "http://duraark.eu" + link
                        elif link.startswith('http'):
                            full_url = link
                        else:
                            continue
                        
                        try:
                            print(f"🔗 다운로드 시도: {full_url}")
                            file_response = self.session.get(full_url, timeout=60, stream=True)
                            
                            if file_response.status_code == 200:
                                # 파일명 추출
                                filename = os.path.basename(urllib.parse.urlparse(full_url).path)
                                if not filename or '.' not in filename:
                                    filename = f"duraark_data_{int(time.time())}.zip"
                                
                                filepath = duraark_dir / filename
                                
                                # 파일 다운로드
                                with open(filepath, 'wb') as f:
                                    for chunk in tqdm(file_response.iter_content(chunk_size=8192), 
                                                    desc=f"다운로드 {filename}"):
                                        if chunk:
                                            f.write(chunk)
                                
                                result["downloaded_files"].append(str(filepath))
                                result["total_size"] += filepath.stat().st_size
                                print(f"✅ 다운로드 완료: {filename}")
                                
                        except Exception as e:
                            result["errors"].append(f"링크 {full_url}: {str(e)}")
                
                # GitHub 리포지토리 확인
                github_urls = [
                    "https://github.com/DURAARK",
                    "https://github.com/duraark"
                ]
                
                for github_url in github_urls:
                    try:
                        response = self.session.get(github_url, timeout=30)
                        if response.status_code == 200:
                            # GitHub에서 리포지토리 목록 찾기
                            repos = re.findall(r'href="([^"]*)"', response.text)
                            for repo in repos:
                                if "/DURAARK/" in repo and repo.endswith('"'):
                                    repo_url = "https://github.com" + repo.replace('"', '')
                                    print(f"🔗 GitHub 리포지토리 발견: {repo_url}")
                                    
                                    # 리포지토리에서 릴리즈 확인
                                    releases_url = repo_url + "/releases"
                                    releases_response = self.session.get(releases_url, timeout=30)
                                    
                                    if releases_response.status_code == 200:
                                        # 릴리즈에서 다운로드 링크 찾기
                                        release_links = re.findall(r'href="([^"]*\.(?:zip|tar\.gz|tar\.bz2))"', releases_response.text)
                                        for release_link in release_links:
                                            if release_link.startswith('/'):
                                                download_url = "https://github.com" + release_link
                                            else:
                                                download_url = release_link
                                            
                                            try:
                                                print(f"📦 릴리즈 다운로드: {download_url}")
                                                file_response = self.session.get(download_url, timeout=120, stream=True)
                                                
                                                if file_response.status_code == 200:
                                                    filename = os.path.basename(urllib.parse.urlparse(download_url).path)
                                                    filepath = duraark_dir / filename
                                                    
                                                    with open(filepath, 'wb') as f:
                                                        for chunk in tqdm(file_response.iter_content(chunk_size=8192), 
                                                                        desc=f"다운로드 {filename}"):
                                                            if chunk:
                                                                f.write(chunk)
                                                    
                                                    result["downloaded_files"].append(str(filepath))
                                                    result["total_size"] += filepath.stat().st_size
                                                    print(f"✅ 릴리즈 다운로드 완료: {filename}")
                                                    
                                            except Exception as e:
                                                result["errors"].append(f"릴리즈 {download_url}: {str(e)}")
                                    
                                    break
                    except Exception as e:
                        result["errors"].append(f"GitHub {github_url}: {str(e)}")
            
        except Exception as e:
            result["errors"].append(f"DURAARK 웹사이트 접근 오류: {str(e)}")
        
        result["status"] = "completed"
        self.download_results["duraark"] = result
        return result
    
    def download_schependomlaan_dataset(self) -> Dict:
        """Schependomlaan 데이터셋 다운로드"""
        print("📥 Schependomlaan 데이터셋 다운로드 시작...")
        
        result = {
            "status": "downloading",
            "downloaded_files": [],
            "total_size": 0,
            "errors": []
        }
        
        schependomlaan_dir = DATA_DIR / "schependomlaan"
        schependomlaan_dir.mkdir(exist_ok=True)
        
        # 4TU 데이터 포털에서 검색
        try:
            search_url = "https://data.4tu.nl/search?q=schependomlaan"
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                print("🔍 4TU 데이터 포털에서 Schependomlaan 검색...")
                
                # 검색 결과에서 다운로드 링크 찾기
                import re
                links = re.findall(r'href="([^"]*)"', response.text)
                
                for link in links:
                    if "schependomlaan" in link.lower() or "bim" in link.lower():
                        if link.startswith('/'):
                            full_url = "https://data.4tu.nl" + link
                        elif link.startswith('http'):
                            full_url = link
                        else:
                            continue
                        
                        try:
                            print(f"🔗 데이터셋 페이지 확인: {full_url}")
                            page_response = self.session.get(full_url, timeout=30)
                            
                            if page_response.status_code == 200:
                                # 페이지에서 다운로드 링크 찾기
                                download_links = re.findall(r'href="([^"]*\.(?:zip|tar\.gz|bcf|ifc))"', page_response.text)
                                
                                for download_link in download_links:
                                    if download_link.startswith('/'):
                                        download_url = "https://data.4tu.nl" + download_link
                                    else:
                                        download_url = download_link
                                    
                                    try:
                                        print(f"📦 다운로드 시도: {download_url}")
                                        file_response = self.session.get(download_url, timeout=120, stream=True)
                                        
                                        if file_response.status_code == 200:
                                            filename = os.path.basename(urllib.parse.urlparse(download_url).path)
                                            if not filename or '.' not in filename:
                                                filename = f"schependomlaan_data_{int(time.time())}.zip"
                                            
                                            filepath = schependomlaan_dir / filename
                                            
                                            with open(filepath, 'wb') as f:
                                                for chunk in tqdm(file_response.iter_content(chunk_size=8192), 
                                                                desc=f"다운로드 {filename}"):
                                                    if chunk:
                                                        f.write(chunk)
                                            
                                            result["downloaded_files"].append(str(filepath))
                                            result["total_size"] += filepath.stat().st_size
                                            print(f"✅ 다운로드 완료: {filename}")
                                            
                                    except Exception as e:
                                        result["errors"].append(f"다운로드 {download_url}: {str(e)}")
                                
                                break
                        except Exception as e:
                            result["errors"].append(f"페이지 {full_url}: {str(e)}")
            
        except Exception as e:
            result["errors"].append(f"4TU 데이터 포털 접근 오류: {str(e)}")
        
        # GitHub에서도 검색
        try:
            github_search_url = "https://github.com/search?q=schependomlaan"
            response = self.session.get(github_search_url, timeout=30)
            
            if response.status_code == 200:
                print("🔍 GitHub에서 Schependomlaan 검색...")
                
                import re
                repo_links = re.findall(r'href="([^"]*)"', response.text)
                
                for repo_link in repo_links:
                    if "/schependomlaan" in repo_link and repo_link.endswith('"'):
                        repo_url = "https://github.com" + repo_link.replace('"', '')
                        print(f"🔗 GitHub 리포지토리 발견: {repo_url}")
                        
                        try:
                            # 리포지토리에서 릴리즈 확인
                            releases_url = repo_url + "/releases"
                            releases_response = self.session.get(releases_url, timeout=30)
                            
                            if releases_response.status_code == 200:
                                release_links = re.findall(r'href="([^"]*\.(?:zip|tar\.gz))"', releases_response.text)
                                for release_link in release_links:
                                    if release_link.startswith('/'):
                                        download_url = "https://github.com" + release_link
                                    else:
                                        download_url = release_link
                                    
                                    try:
                                        print(f"📦 GitHub 릴리즈 다운로드: {download_url}")
                                        file_response = self.session.get(download_url, timeout=120, stream=True)
                                        
                                        if file_response.status_code == 200:
                                            filename = os.path.basename(urllib.parse.urlparse(download_url).path)
                                            filepath = schependomlaan_dir / filename
                                            
                                            with open(filepath, 'wb') as f:
                                                for chunk in tqdm(file_response.iter_content(chunk_size=8192), 
                                                                desc=f"다운로드 {filename}"):
                                                    if chunk:
                                                        f.write(chunk)
                                            
                                            result["downloaded_files"].append(str(filepath))
                                            result["total_size"] += filepath.stat().st_size
                                            print(f"✅ GitHub 릴리즈 다운로드 완료: {filename}")
                                            
                                    except Exception as e:
                                        result["errors"].append(f"GitHub 릴리즈 {download_url}: {str(e)}")
                            
                        except Exception as e:
                            result["errors"].append(f"GitHub 리포지토리 {repo_url}: {str(e)}")
                        
                        break
        except Exception as e:
            result["errors"].append(f"GitHub 검색 오류: {str(e)}")
        
        result["status"] = "completed"
        self.download_results["schependomlaan"] = result
        return result
    
    def extract_downloaded_files(self):
        """다운로드된 파일 압축 해제"""
        print("📦 다운로드된 파일 압축 해제...")
        
        for dataset, result in self.download_results.items():
            if not result.get("downloaded_files"):
                continue
            
            dataset_dir = DATA_DIR / dataset
            extracted_dir = dataset_dir / "extracted"
            extracted_dir.mkdir(exist_ok=True)
            
            for filepath in result["downloaded_files"]:
                file_path = Path(filepath)
                
                if file_path.suffix.lower() in ['.zip']:
                    try:
                        print(f"📂 압축 해제: {file_path.name}")
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(extracted_dir)
                        print(f"✅ 압축 해제 완료: {file_path.name}")
                    except Exception as e:
                        print(f"❌ 압축 해제 실패: {file_path.name} - {str(e)}")
    
    def generate_download_report(self):
        """다운로드 결과 보고서 생성"""
        report_file = DATA_DIR / "DOWNLOAD_RESULTS.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 직접 다운로드 결과 보고서\n\n")
            f.write("**작성일**: 2025년 10월 15일\n\n")
            
            f.write("## 다운로드 결과\n\n")
            
            for dataset, result in self.download_results.items():
                f.write(f"### {dataset.upper()}\n")
                f.write(f"- **상태**: {result['status']}\n")
                f.write(f"- **다운로드된 파일 수**: {len(result['downloaded_files'])}\n")
                f.write(f"- **총 크기**: {result['total_size'] / (1024*1024):.2f} MB\n")
                
                if result["downloaded_files"]:
                    f.write("- **다운로드된 파일**:\n")
                    for filepath in result["downloaded_files"]:
                        f.write(f"  - {filepath}\n")
                
                if result["errors"]:
                    f.write("- **오류**:\n")
                    for error in result["errors"]:
                        f.write(f"  - {error}\n")
                
                f.write("\n")
            
            f.write("## 다음 단계\n\n")
            f.write("1. 다운로드된 파일 검증\n")
            f.write("2. IFC/BCF 파일 추출\n")
            f.write("3. 데이터 품질 평가\n")
            f.write("4. 프로젝트 통합\n")
        
        print(f"📄 다운로드 결과 보고서 생성: {report_file}")
    
    def run_download(self):
        """전체 다운로드 실행"""
        print("🚀 직접 다운로드 가능한 데이터셋 다운로드 시작...\n")
        
        # DURAARK 다운로드
        self.download_duraark_dataset()
        
        # Schependomlaan 다운로드
        self.download_schependomlaan_dataset()
        
        # 압축 해제
        self.extract_downloaded_files()
        
        # 결과 보고서 생성
        self.generate_download_report()
        
        print("\n✅ 다운로드 완료!")
        
        # 요약 출력
        total_files = sum(len(result.get("downloaded_files", [])) for result in self.download_results.values())
        total_size = sum(result.get("total_size", 0) for result in self.download_results.values())
        
        print(f"📊 다운로드 요약:")
        print(f"   - 총 다운로드된 파일: {total_files}개")
        print(f"   - 총 크기: {total_size / (1024*1024):.2f} MB")
        
        for dataset, result in self.download_results.items():
            print(f"   - {dataset}: {len(result.get('downloaded_files', []))}개 파일")

def main():
    """메인 함수"""
    downloader = DatasetDownloader()
    downloader.run_download()

if __name__ == "__main__":
    main()
