import argparse
import re
from ..core import read_jsonl, write_jsonl

def extract_guid_from_text(text):
    """텍스트에서 GUID 패턴을 추출합니다."""
    # IFC GUID 패턴: 22자리 영숫자 (예: 0xScRe4drECQ4DMSqUjd6d)
    guid_pattern = r'\b[A-Za-z0-9]{22}\b'
    return re.findall(guid_pattern, text)

def semantic_match(bcf_text, ifc_item):
    """의미적 매칭을 수행합니다."""
    bcf_lower = bcf_text.lower()
    ifc_name = ifc_item.get("name", "").lower()
    ifc_type = ifc_item.get("type", "").lower()
    
    # 키워드 매칭
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
    for category, terms in keywords.items():
        if any(term in bcf_lower for term in terms):
            if any(term in ifc_name or term in ifc_type for term in terms):
                score += 1
    
    return score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ifc", required=True)
    ap.add_argument("--bcf", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ifc_map = {r["guid"]: r for r in read_jsonl(a.ifc)}
    out = []
    
    for b in read_jsonl(a.bcf):
        # BCF 텍스트 구성
        bcf_text = " ".join([
            b.get("title", ""),
            b.get("description", ""),
            b.get("ref", "")
        ])
        
        # 1. 직접 GUID 매칭
        direct_matches = extract_guid_from_text(bcf_text)
        direct_matches = [g for g in direct_matches if g in ifc_map]
        
        # 2. 의미적 매칭 (직접 매칭이 없는 경우)
        semantic_matches = []
        if not direct_matches:
            scores = []
            for guid, ifc_item in ifc_map.items():
                score = semantic_match(bcf_text, ifc_item)
                if score > 0:
                    scores.append((guid, score))
            
            # 상위 3개 선택
            scores.sort(key=lambda x: x[1], reverse=True)
            semantic_matches = [guid for guid, score in scores[:3]]
        
        # 최종 매칭 결과
        all_matches = direct_matches + semantic_matches
        confidence = 1.0 if direct_matches else 0.5 if semantic_matches else 0.2
        
        out.append({
            "topic_id": b["topic_id"],
            "guid_matches": all_matches,
            "confidence": confidence,
            "evidence": bcf_text[:100] + "..." if len(bcf_text) > 100 else bcf_text
        })
    
    write_jsonl(a.out, out)

if __name__ == "__main__":
    main()
