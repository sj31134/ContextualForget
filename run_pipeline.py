#!/usr/bin/env python3
"""
ContextualForget 파이프라인 실행 스크립트
Makefile 대신 사용하는 Python 기반 파이프라인 실행기
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """명령어 실행"""
    if description:
        print(f"🔄 {description}")
    
    print(f"   실행: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ 성공")
        if result.stdout:
            print(f"   출력: {result.stdout.strip()}")
    else:
        print(f"   ❌ 실패 (코드: {result.returncode})")
        if result.stderr:
            print(f"   오류: {result.stderr.strip()}")
        return False
    
    return True


def setup_environment():
    """환경 설정"""
    print("🔧 환경 설정 중...")
    
    # conda 환경 생성
    if not run_command("conda create -n contextualforget python=3.11 -y", "Conda 환경 생성"):
        print("   환경이 이미 존재하거나 생성 실패")
    
    # pip 업그레이드
    run_command("conda activate contextualforget && pip install -U pip", "Pip 업그레이드")
    
    # 패키지 설치
    return run_command("conda activate contextualforget && pip install -e \".[dev]\"", "패키지 설치")


def create_sample_data():
    """샘플 데이터 생성"""
    print("📁 샘플 데이터 생성 중...")
    
    # 디렉토리 생성
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/raw/bcf_min/Topics/0001", exist_ok=True)
    
    # IFC 파일 생성
    ifc_content = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [notYetAssigned]'),'2;1');
FILE_NAME('sample.ifc','2025-10-05T00:00:00',('author'),('org'),'ifc text','ifc text','ref');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#100= IFCPROJECT('0xScRe4drECQ4DMSqUjd6d',$,'Sample',$,$,$,$,$,$);
#500= IFCBUILDING('2FCZDorxHDT8NI01kdXi8P',$,'Test Building',$,$,$,$,$,.ELEMENT.,$,$,$);
#1000= IFCBUILDINGELEMENTPROXY('1kTvXnbbzCWw8lcMd1dR4o',$,'P-1','sample',$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;"""
    
    with open("data/raw/sample.ifc", "w") as f:
        f.write(ifc_content)
    print("   ✅ IFC 파일 생성")
    
    # BCF 파일 생성
    bcf_content = """<?xml version="1.0" encoding="UTF-8"?>
<Topic Guid="11111111-1111-1111-1111-111111111111" TopicType="Issue" TopicStatus="Open">
  <Title>Increase clearance of proxy element</Title>
  <CreationDate>2025-10-05T09:00:00Z</CreationDate>
  <CreationAuthor>engineer_a</CreationAuthor>
  <ReferenceLink>ifc://1kTvXnbbzCWw8lcMd1dR4o</ReferenceLink>
  <Description>Adjust dimensions of GUID 1kTvXnbbzCWw8lcMd1dR4o at Level 1</Description>
  <Labels><Label>HVAC</Label><Label>Clearance</Label></Labels>
</Topic>"""
    
    with open("data/raw/bcf_min/Topics/0001/markup.bcf", "w") as f:
        f.write(bcf_content)
    print("   ✅ BCF markup 파일 생성")
    
    # BCF version 파일 생성
    version_content = """<?xml version="1.0" encoding="UTF-8"?>
<Version VersionId="2.1" DetailedVersion="2.1"/>"""
    
    with open("data/raw/bcf_min/bcf.version", "w") as f:
        f.write(version_content)
    print("   ✅ BCF version 파일 생성")
    
    # BCF ZIP 파일 생성
    import zipfile
    with zipfile.ZipFile("data/raw/sample.bcfzip", "w") as zf:
        zf.write("data/raw/bcf_min/Topics/0001/markup.bcf", "Topics/0001/markup.bcf")
        zf.write("data/raw/bcf_min/bcf.version", "bcf.version")
    print("   ✅ BCF ZIP 파일 생성")
    
    # sources.json 생성
    import json
    import hashlib
    
    def sha256_file(filepath):
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    sources = {
        "sample.ifc": {
            "path": "data/raw/sample.ifc",
            "sha256": sha256_file("data/raw/sample.ifc"),
            "size": os.path.getsize("data/raw/sample.ifc"),
            "source": "synthetic"
        },
        "sample.bcfzip": {
            "path": "data/raw/sample.bcfzip",
            "sha256": sha256_file("data/raw/sample.bcfzip"),
            "size": os.path.getsize("data/raw/sample.bcfzip"),
            "source": "synthetic"
        }
    }
    
    with open("data/sources.json", "w") as f:
        json.dump(sources, f, indent=2)
    print("   ✅ sources.json 생성")


def run_pipeline():
    """전체 파이프라인 실행"""
    print("🚀 ContextualForget 파이프라인 실행")
    print("=" * 50)
    
    python_exe = sys.executable
    
    # 1. IFC 데이터 수집
    if not run_command(
        f"{python_exe} -m contextualforget.data.ingest_ifc --ifc data/raw/sample.ifc --out data/processed/ifc.jsonl",
        "IFC 데이터 수집"
    ):
        return False
    
    # 2. BCF 데이터 수집
    if not run_command(
        f"{python_exe} -m contextualforget.data.ingest_bcf --bcf data/raw/sample.bcfzip --out data/processed/bcf.jsonl",
        "BCF 데이터 수집"
    ):
        return False
    
    # 3. IFC-BCF 연결
    if not run_command(
        f"{python_exe} -m contextualforget.data.link_ifc_bcf --ifc data/processed/ifc.jsonl --bcf data/processed/bcf.jsonl --out data/processed/links.jsonl",
        "IFC-BCF 연결"
    ):
        return False
    
    # 4. 그래프 구축
    if not run_command(
        f"{python_exe} -m contextualforget.data.build_graph --ifc data/processed/ifc.jsonl --bcf data/processed/bcf.jsonl --links data/processed/links.jsonl --out data/processed/graph.gpickle",
        "그래프 구축"
    ):
        return False
    
    # 5. 쿼리 테스트
    if not run_command(
        f"{python_exe} -m contextualforget.cli.cli query 1kTvXnbbzCWw8lcMd1dR4o --ttl 365 --topk 5",
        "쿼리 테스트"
    ):
        return False
    
    print("🎉 파이프라인 실행 완료!")
    return True


def run_tests():
    """테스트 실행"""
    print("🧪 테스트 실행 중...")
    
    commands = [
        ("conda activate contextualforget && ctxf stats", "그래프 통계"),
        ("conda activate contextualforget && ctxf search \"clearance\" --topk 5", "키워드 검색"),
        ("conda activate contextualforget && ctxf author \"engineer_a\" --topk 5", "작성자 검색"),
        ("conda activate contextualforget && ctxf health", "시스템 상태"),
        ("conda activate contextualforget && ctxf metrics", "시스템 메트릭")
    ]
    
    for cmd, desc in commands:
        run_command(cmd, desc)


def main():
    parser = argparse.ArgumentParser(description="ContextualForget 파이프라인 실행기")
    parser.add_argument("command", nargs="?", default="all", 
                       choices=["setup", "data", "pipeline", "test", "all"],
                       help="실행할 명령어")
    
    args = parser.parse_args()
    
    if args.command in ["setup", "all"]:
        if not setup_environment():
            print("❌ 환경 설정 실패")
            sys.exit(1)
    
    if args.command in ["data", "all"]:
        create_sample_data()
    
    if args.command in ["pipeline", "all"]:
        if not run_pipeline():
            print("❌ 파이프라인 실행 실패")
            sys.exit(1)
    
    if args.command in ["test", "all"]:
        run_tests()
    
    print("✅ 모든 작업 완료!")


if __name__ == "__main__":
    main()
