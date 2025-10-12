#!/usr/bin/env python3
"""모든 IFC 및 BCF 데이터를 처리하여 그래프를 구축하는 스크립트."""

import sys
import subprocess
from pathlib import Path
import glob


def run_cmd(cmd):
    """명령어 실행."""
    print(f"  실행: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ 실패: {result.stderr}")
        return False
    print(f"  ✅ 완료")
    return True


def main():
    """메인 함수."""
    python_exe = sys.executable
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    processed_dir = data_dir / "processed"
    raw_dir = data_dir / "raw"
    
    print("🚀 ContextualForget 전체 데이터 처리 시작")
    print("=" * 60)
    
    # 1. 모든 IFC 파일 수집
    print("\n📐 IFC 파일 수집 중...")
    ifc_files = list(data_dir.glob("*.ifc"))
    print(f"  발견된 IFC 파일: {len(ifc_files)}개")
    
    # processed 디렉토리 초기화
    if processed_dir.exists():
        for f in processed_dir.glob("*.jsonl"):
            f.unlink()
    
    # 각 IFC 파일 처리
    all_ifc_data = []
    for ifc_file in ifc_files:
        print(f"\n  처리 중: {ifc_file.name}")
        temp_out = processed_dir / f"{ifc_file.stem}_ifc.jsonl"
        
        cmd = f'{python_exe} -m contextualforget.data.ingest_ifc --ifc "{ifc_file}" --out "{temp_out}"'
        if run_cmd(cmd):
            all_ifc_data.append(temp_out)
    
    # 모든 IFC 데이터 병합
    print("\n  IFC 데이터 병합 중...")
    final_ifc = processed_dir / "ifc.jsonl"
    with open(final_ifc, 'w') as outfile:
        for temp_file in all_ifc_data:
            with open(temp_file, 'r') as infile:
                outfile.write(infile.read())
            temp_file.unlink()  # 임시 파일 삭제
    print(f"  ✅ IFC 데이터 병합 완료: {final_ifc}")
    
    # 2. 모든 BCF 파일 수집
    print("\n📋 BCF 파일 수집 중...")
    bcf_files = list(raw_dir.glob("*.bcfzip"))
    print(f"  발견된 BCF 파일: {len(bcf_files)}개")
    
    # 각 BCF 파일 처리
    all_bcf_data = []
    for bcf_file in bcf_files:
        print(f"\n  처리 중: {bcf_file.name}")
        temp_out = processed_dir / f"{bcf_file.stem}_bcf.jsonl"
        
        cmd = f'{python_exe} -m contextualforget.data.ingest_bcf --bcf "{bcf_file}" --out "{temp_out}"'
        if run_cmd(cmd):
            all_bcf_data.append(temp_out)
    
    # 모든 BCF 데이터 병합
    print("\n  BCF 데이터 병합 중...")
    final_bcf = processed_dir / "bcf.jsonl"
    with open(final_bcf, 'w') as outfile:
        for temp_file in all_bcf_data:
            with open(temp_file, 'r') as infile:
                outfile.write(infile.read())
            temp_file.unlink()  # 임시 파일 삭제
    print(f"  ✅ BCF 데이터 병합 완료: {final_bcf}")
    
    # 3. IFC-BCF 연결
    print("\n🔗 IFC-BCF 연결 중...")
    final_links = processed_dir / "links.jsonl"
    cmd = f'{python_exe} -m contextualforget.data.link_ifc_bcf --ifc "{final_ifc}" --bcf "{final_bcf}" --out "{final_links}"'
    if not run_cmd(cmd):
        print("❌ IFC-BCF 연결 실패")
        return False
    
    # 4. 그래프 구축
    print("\n🕸️  그래프 구축 중...")
    final_graph = processed_dir / "graph.gpickle"
    cmd = f'{python_exe} -m contextualforget.data.build_graph --ifc "{final_ifc}" --bcf "{final_bcf}" --links "{final_links}" --out "{final_graph}"'
    if not run_cmd(cmd):
        print("❌ 그래프 구축 실패")
        return False
    
    # 5. 통계 출력
    print("\n📊 처리 완료 통계:")
    print(f"  IFC 파일: {len(ifc_files)}개")
    print(f"  BCF 파일: {len(bcf_files)}개")
    print(f"  그래프 파일: {final_graph}")
    
    # 6. 그래프 통계 확인
    print("\n🔍 그래프 통계 확인...")
    cmd = f'{python_exe} -c "import networkx as nx; G=nx.read_gpickle(\'{final_graph}\'); print(f\'노드: {{G.number_of_nodes()}}개, 엣지: {{G.number_of_edges()}}개\')"'
    run_cmd(cmd)
    
    print("\n✨ 전체 데이터 처리 완료!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

