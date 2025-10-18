"""
IFC-BCF 링크 생성 스크립트 (개선 버전)
GUID 추출 강화 + TF-IDF 의미적 매칭 추가
"""
import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contextualforget.core import read_jsonl, write_jsonl


def extract_guid_from_text(text: str) -> List[str]:
    """
    텍스트에서 GUID 패턴을 추출합니다 (개선 버전).
    
    IFC GUID는 22자 Base64 변형 문자열입니다.
    허용 문자: 0-9, A-Z, a-z, _, $
    """
    # IFC GUID 패턴: 22자 Base64 변형
    # \b는 한국어와 함께 사용 시 문제가 있으므로 더 유연한 패턴 사용
    guid_pattern = r'[0-9A-Za-z_$]{22}(?![0-9A-Za-z_$])'
    guids = re.findall(guid_pattern, text)
    return list(set(guids))  # 중복 제거

def semantic_match_tfidf(bcf_text: str, ifc_items: Dict[str, Dict]) -> List[Tuple[str, float]]:
    """
    TF-IDF 기반 의미적 매칭을 수행합니다.
    
    Args:
        bcf_text: BCF 이슈의 텍스트 (title + description)
        ifc_items: GUID → IFC 엔티티 매핑 딕셔너리
        
    Returns:
        [(guid, similarity_score), ...] 튜플 리스트 (상위 3개)
    """
    if not bcf_text.strip() or not ifc_items:
        return []
    
    # IFC 엔티티 텍스트 생성
    ifc_texts = []
    guids = []
    for guid, item in ifc_items.items():
        text = " ".join([
            str(item.get('name', '')),
            str(item.get('type', '')),
            str(item.get('description', ''))
        ])
        if text.strip():
            ifc_texts.append(text)
            guids.append(guid)
    
    if not ifc_texts:
        return []
    
    # TF-IDF 벡터화
    try:
        # min_df를 작은 데이터셋에서도 작동하도록 조정
        vectorizer = TfidfVectorizer(
            min_df=1,
            max_df=1.0,  # 모든 문서 허용
            ngram_range=(1, 2),
            token_pattern=r'(?u)\b\w+\b'  # 한국어 지원
        )
        documents = [bcf_text] + ifc_texts
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        # 코사인 유사도 계산
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        # 상위 3개 선택 (유사도가 0보다 큰 경우)
        top_indices = similarities.argsort()[-3:][::-1]
        results = [
            (guids[i], float(similarities[i]))
            for i in top_indices
            if similarities[i] > 0.05  # 임계값 더 낮춤 (0.1 → 0.05)
        ]
        
        # 결과가 없으면 최소 1개는 반환 (유사도가 가장 높은 것)
        if not results and len(similarities) > 0:
            best_idx = similarities.argmax()
            if similarities[best_idx] > 0:
                results = [(guids[best_idx], float(similarities[best_idx]))]
        
        return results
    except Exception as e:
        print(f"⚠️  TF-IDF 매칭 실패: {e}")
        return []


def semantic_match_keyword(bcf_text: str, ifc_item: Dict) -> float:
    """
    키워드 기반 의미적 매칭을 수행합니다 (fallback).
    
    Args:
        bcf_text: BCF 이슈의 텍스트
        ifc_item: IFC 엔티티
        
    Returns:
        매칭 점수 (0.0 ~ 1.0)
    """
    bcf_lower = bcf_text.lower()
    ifc_name = str(ifc_item.get("name", "")).lower()
    ifc_type = str(ifc_item.get("type", "")).lower()
    
    # 한영 키워드 매핑
    keywords = {
        "벽": ["wall", "벽체"],
        "문": ["door", "문"],
        "창": ["window", "창문"],
        "바닥": ["slab", "floor", "바닥"],
        "천장": ["ceiling", "천장"],
        "기둥": ["column", "기둥"],
        "보": ["beam", "보"],
        "계단": ["stair", "계단"],
        "엘리베이터": ["elevator", "엘리베이터"],
        "화장실": ["toilet", "restroom", "화장실"],
        "무균실": ["clean", "sterile", "무균"],
        "방화": ["fire", "방화"],
        "피난": ["escape", "exit", "피난"]
    }
    
    score = 0
    for _category, terms in keywords.items():
        if any(term in bcf_lower for term in terms):
            if any(term in ifc_name or term in ifc_type for term in terms):
                score += 1
    
    # 정규화 (최대 10개 키워드 가정)
    return min(score / 10.0, 1.0)


def calculate_confidence(match_type: str, score: float = 1.0) -> float:
    """
    매칭 타입별 신뢰도를 계산합니다.
    
    Args:
        match_type: 'direct_guid', 'tfidf', 'keyword'
        score: 매칭 점수 (TF-IDF 유사도 또는 키워드 점수)
        
    Returns:
        신뢰도 (0.0 ~ 1.0)
    """
    confidence_map = {
        'direct_guid': 1.0,
        'tfidf_high': min(0.7, score * 0.9),  # 높은 TF-IDF 점수
        'tfidf_medium': min(0.5, score * 0.7),  # 중간 TF-IDF 점수
        'keyword': min(0.4, score),  # 키워드 매칭
    }
    
    if match_type == 'tfidf':
        if score >= 0.5:
            return confidence_map['tfidf_high']
        else:
            return confidence_map['tfidf_medium']
    
    return confidence_map.get(match_type, 0.2)

def main():
    ap = argparse.ArgumentParser(description='IFC-BCF 링크 생성 (GUID + TF-IDF 매칭)')
    ap.add_argument("--ifc", required=True, help="IFC JSONL 파일 경로")
    ap.add_argument("--bcf", required=True, help="BCF JSONL 파일 경로")
    ap.add_argument("--out", required=True, help="출력 링크 JSONL 파일 경로")
    ap.add_argument("--use-tfidf", action="store_true", help="TF-IDF 매칭 사용")
    a = ap.parse_args()

    # IFC 데이터 로드
    ifc_map = {r["guid"]: r for r in read_jsonl(a.ifc)}
    print(f"✅ IFC 데이터 로드: {len(ifc_map)}개")
    
    out = []
    bcf_data = list(read_jsonl(a.bcf))
    print(f"✅ BCF 데이터 로드: {len(bcf_data)}개")
    
    for i, b in enumerate(bcf_data):
        if (i + 1) % 10 == 0:
            print(f"   처리 중: {i+1}/{len(bcf_data)}")
        
        # BCF 텍스트 구성
        bcf_text = " ".join([
            str(b.get("title", "")),
            str(b.get("description", "")),
            str(b.get("ref", ""))
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
        elif a.use_tfidf:
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
        
        # 결과 저장
        out.append({
            "topic_id": b["topic_id"],
            "guid_matches": final_matches,
            "confidence": confidence,
            "match_type": match_type,
            "evidence": bcf_text[:100] + "..." if len(bcf_text) > 100 else bcf_text
        })
    
    write_jsonl(a.out, out)
    
    # 통계 출력
    print(f"\n📊 링크 생성 통계:")
    print(f"   총 BCF 이슈: {len(out)}개")
    
    with_matches = [r for r in out if r['guid_matches']]
    print(f"   매칭 성공: {len(with_matches)}개 ({len(with_matches)/len(out)*100:.1f}%)")
    
    avg_confidence = sum(r['confidence'] for r in out) / len(out) if out else 0
    print(f"   평균 신뢰도: {avg_confidence:.3f}")
    
    match_types = {}
    for r in with_matches:
        mt = r.get('match_type', 'unknown')
        match_types[mt] = match_types.get(mt, 0) + 1
    
    print(f"   매칭 타입:")
    for mt, count in sorted(match_types.items(), key=lambda x: x[1], reverse=True):
        print(f"      {mt}: {count}개")
    
    print(f"\n✅ 링크 파일 저장: {a.out}")


if __name__ == "__main__":
    main()
