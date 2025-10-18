"""
전체 IFC-BCF 데이터 재링크 스크립트
84 IFC × 88 BCF = 7,392개 조합을 병렬 처리하여 링크 생성
"""
import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core import read_jsonl, write_jsonl
from contextualforget.data.link_ifc_bcf import (
    extract_guid_from_text,
    semantic_match_tfidf,
    semantic_match_keyword,
    calculate_confidence
)


def process_single_bcf_issue(args: Tuple) -> Dict:
    """
    단일 BCF 이슈 처리 (병렬 처리용)
    
    Args:
        args: (bcf_issue, ifc_map, use_tfidf) 튜플
        
    Returns:
        링크 정보 딕셔너리
    """
    bcf_issue, ifc_map, use_tfidf = args
    
    # BCF 텍스트 구성
    bcf_text = " ".join([
        str(bcf_issue.get("title", "")),
        str(bcf_issue.get("description", "")),
        str(bcf_issue.get("ref", ""))
    ])
    
    # 1. 직접 GUID 매칭
    direct_matches = extract_guid_from_text(bcf_text)
    direct_matches = [g for g in direct_matches if g in ifc_map]
    
    match_type = ''
    confidence = 0.2
    final_matches = []
    
    if direct_matches:
        # 직접 GUID 발견
        final_matches = direct_matches
        match_type = 'direct_guid'
        confidence = calculate_confidence('direct_guid')
    elif use_tfidf:
        # 2. TF-IDF 의미적 매칭
        tfidf_matches = semantic_match_tfidf(bcf_text, ifc_map)
        if tfidf_matches:
            final_matches = [guid for guid, score in tfidf_matches]
            avg_score = sum(score for _, score in tfidf_matches) / len(tfidf_matches)
            match_type = 'tfidf'
            confidence = calculate_confidence('tfidf', avg_score)
        else:
            # 3. 키워드 매칭 (fallback)
            keyword_scores = []
            for guid, ifc_item in ifc_map.items():
                score = semantic_match_keyword(bcf_text, ifc_item)
                if score > 0:
                    keyword_scores.append((guid, score))
            
            if keyword_scores:
                keyword_scores.sort(key=lambda x: x[1], reverse=True)
                final_matches = [guid for guid, score in keyword_scores[:3]]
                avg_score = sum(score for _, score in keyword_scores[:3]) / len(keyword_scores[:3])
                match_type = 'keyword'
                confidence = calculate_confidence('keyword', avg_score)
    else:
        # TF-IDF 미사용: 키워드 매칭만
        keyword_scores = []
        for guid, ifc_item in ifc_map.items():
            score = semantic_match_keyword(bcf_text, ifc_item)
            if score > 0:
                keyword_scores.append((guid, score))
        
        if keyword_scores:
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            final_matches = [guid for guid, score in keyword_scores[:3]]
            avg_score = sum(score for _, score in keyword_scores[:3]) / len(keyword_scores[:3])
            match_type = 'keyword'
            confidence = calculate_confidence('keyword', avg_score)
    
    return {
        "topic_id": bcf_issue["topic_id"],
        "guid_matches": final_matches,
        "confidence": confidence,
        "match_type": match_type,
        "evidence": bcf_text[:100] + "..." if len(bcf_text) > 100 else bcf_text
    }


def main():
    ap = argparse.ArgumentParser(description='전체 IFC-BCF 데이터 재링크')
    ap.add_argument("--data-dir", default="data/processed", help="데이터 디렉토리")
    ap.add_argument("--out", default="data/processed/all_links.jsonl", help="출력 파일")
    ap.add_argument("--use-tfidf", action="store_true", help="TF-IDF 매칭 사용")
    ap.add_argument("--workers", type=int, default=4, help="병렬 워커 수")
    ap.add_argument("--limit-ifc", type=int, help="IFC 파일 수 제한 (테스트용)")
    ap.add_argument("--limit-bcf", type=int, help="BCF 파일 수 제한 (테스트용)")
    a = ap.parse_args()
    
    data_dir = Path(a.data_dir)
    
    # IFC 파일 로드
    print("📂 IFC 파일 로드 중...")
    ifc_files = sorted(data_dir.glob('*_ifc.jsonl'))
    if a.limit_ifc:
        ifc_files = ifc_files[:a.limit_ifc]
    
    all_ifc_data = {}
    for ifc_file in ifc_files:
        for entity in read_jsonl(str(ifc_file)):
            all_ifc_data[entity['guid']] = entity
    
    print(f"✅ IFC 데이터 로드 완료: {len(all_ifc_data):,}개 엔티티")
    
    # BCF 파일 로드
    print("📂 BCF 파일 로드 중...")
    bcf_files = sorted(data_dir.glob('*_bcf.jsonl'))
    if a.limit_bcf:
        bcf_files = bcf_files[:a.limit_bcf]
    
    all_bcf_data = []
    for bcf_file in bcf_files:
        all_bcf_data.extend(read_jsonl(str(bcf_file)))
    
    print(f"✅ BCF 데이터 로드 완료: {len(all_bcf_data):,}개 이슈")
    
    # 병렬 처리 준비
    print(f"\n🔗 링크 생성 시작 ({a.workers}개 워커)...")
    tasks = [
        (bcf_issue, all_ifc_data, a.use_tfidf)
        for bcf_issue in all_bcf_data
    ]
    
    all_links = []
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=a.workers) as executor:
        futures = {
            executor.submit(process_single_bcf_issue, task): i
            for i, task in enumerate(tasks)
        }
        
        completed = 0
        for future in as_completed(futures):
            try:
                link = future.result()
                all_links.append(link)
                completed += 1
                
                if completed % 10 == 0 or completed == len(tasks):
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    remaining = (len(tasks) - completed) / rate if rate > 0 else 0
                    print(f"   진행: {completed}/{len(tasks)} ({completed/len(tasks)*100:.1f}%) "
                          f"- {rate:.1f} 이슈/초, 남은 시간: {remaining:.0f}초", end='\\r')
            except Exception as e:
                print(f"\\n⚠️  처리 실패: {e}")
    
    print()  # 줄바꿈
    
    # 결과 저장
    write_jsonl(a.out, all_links)
    
    # 통계 출력
    elapsed = time.time() - start_time
    print(f"\\n📊 링크 생성 통계:")
    print(f"   처리 시간: {elapsed:.1f}초")
    print(f"   처리 속도: {len(all_links)/elapsed:.1f} 이슈/초")
    print(f"   총 BCF 이슈: {len(all_links):,}개")
    
    with_matches = [r for r in all_links if r['guid_matches']]
    print(f"   매칭 성공: {len(with_matches):,}개 ({len(with_matches)/len(all_links)*100:.1f}%)")
    
    total_links = sum(len(r['guid_matches']) for r in all_links)
    print(f"   총 링크 수: {total_links:,}개")
    
    avg_confidence = sum(r['confidence'] for r in all_links) / len(all_links) if all_links else 0
    print(f"   평균 신뢰도: {avg_confidence:.3f}")
    
    # 신뢰도별 분포
    high_conf = len([r for r in all_links if r['confidence'] >= 0.7])
    medium_conf = len([r for r in all_links if 0.4 <= r['confidence'] < 0.7])
    low_conf = len([r for r in all_links if r['confidence'] < 0.4])
    
    print(f"   신뢰도 분포:")
    print(f"      높음 (≥0.7): {high_conf}개 ({high_conf/len(all_links)*100:.1f}%)")
    print(f"      중간 (0.4-0.7): {medium_conf}개 ({medium_conf/len(all_links)*100:.1f}%)")
    print(f"      낮음 (<0.4): {low_conf}개 ({low_conf/len(all_links)*100:.1f}%)")
    
    # 매칭 타입별 분포
    match_types = {}
    for r in with_matches:
        mt = r.get('match_type', 'unknown')
        match_types[mt] = match_types.get(mt, 0) + 1
    
    print(f"   매칭 타입:")
    for mt, count in sorted(match_types.items(), key=lambda x: x[1], reverse=True):
        print(f"      {mt}: {count}개 ({count/len(with_matches)*100:.1f}%)")
    
    print(f"\\n✅ 링크 파일 저장 완료: {a.out}")
    
    # 검증
    if total_links >= 500:
        print(f"✅ 링크 수 목표 달성: {total_links} >= 500")
    else:
        print(f"⚠️  링크 수 목표 미달: {total_links} < 500")
    
    if avg_confidence >= 0.6:
        print(f"✅ 평균 신뢰도 목표 달성: {avg_confidence:.3f} >= 0.6")
    else:
        print(f"⚠️  평균 신뢰도 목표 미달: {avg_confidence:.3f} < 0.6")


if __name__ == "__main__":
    main()

