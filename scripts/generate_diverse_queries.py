#!/usr/bin/env python3
"""
다양한 쿼리 타입 Gold Standard 생성 스크립트
6가지 쿼리 타입으로 500개 질의 생성
"""

import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import read_jsonl, write_jsonl


def load_integrated_data():
    """통합 데이터셋 로드"""
    
    print("📂 통합 데이터셋 로드 중...")
    
    # 통합 BCF 데이터 로드
    bcf_file = Path("data/processed/integrated_dataset/integrated_bcf_data.jsonl")
    if not bcf_file.exists():
        print("❌ 통합 BCF 데이터를 찾을 수 없습니다.")
        return None
    
    bcf_data = list(read_jsonl(str(bcf_file)))
    print(f"  ✅ BCF 데이터: {len(bcf_data)}개 이슈")
    
    # GUID, Author, Keyword 추출
    guids = []
    authors = []
    keywords = []
    
    for issue in bcf_data:
        # GUID 추출
        if issue.get("topic_id"):
            guids.append(issue["topic_id"])
        
        # Author 추출
        if issue.get("author"):
            authors.append(issue["author"])
        
        # Keyword 추출 (제목과 설명에서)
        title = issue.get("title", "")
        description = issue.get("description", "")
        text = f"{title} {description}".lower()
        
        # 건설 관련 키워드 추출
        construction_keywords = [
            "구조", "설비", "충돌", "벽", "바닥", "천장", "문", "창문", "계단", "엘리베이터",
            "전기", "조명", "배관", "환기", "난방", "냉방", "소방", "보안", "통신", "네트워크",
            "재료", "콘크리트", "철근", "강재", "목재", "유리", "타일", "페인트", "단열", "방수",
            "설계", "도면", "계획", "일정", "예산", "품질", "안전", "검사", "승인", "변경"
        ]
        
        for keyword in construction_keywords:
            if keyword in text and keyword not in keywords:
                keywords.append(keyword)
    
    print(f"  📊 추출된 데이터:")
    print(f"    • GUID: {len(set(guids))}개")
    print(f"    • Author: {len(set(authors))}개")
    print(f"    • Keywords: {len(keywords)}개")
    
    return {
        "bcf_data": bcf_data,
        "guids": list(set(guids)),
        "authors": list(set(authors)),
        "keywords": keywords
    }


def generate_guid_queries(data, count=100):
    """GUID 검색 쿼리 생성"""
    
    print(f"🔍 GUID 검색 쿼리 생성 중... ({count}개)")
    
    queries = []
    guids = data["guids"]
    
    # GUID 쿼리 템플릿
    templates = [
        "GUID {guid}와 관련된 이슈는 무엇인가요?",
        "{guid}에 대한 상세 정보를 알려주세요.",
        "이슈 {guid}의 내용을 설명해주세요.",
        "{guid} 관련 문제점은 무엇인가요?",
        "GUID {guid}의 해결 상태는 어떻게 되나요?",
        "{guid} 이슈의 우선순위는 무엇인가요?",
        "이슈 {guid}를 담당하는 사람은 누구인가요?",
        "{guid}와 연결된 다른 이슈들이 있나요?",
        "GUID {guid}의 생성 날짜는 언제인가요?",
        "{guid} 이슈의 분류는 무엇인가요?"
    ]
    
    for i in range(count):
        guid = random.choice(guids)
        template = random.choice(templates)
        question = template.format(guid=guid)
        
        queries.append({
            "id": f"guid_{i+1:03d}",
            "question": question,
            "query_type": "guid",
            "expected_guid": guid,
            "difficulty": "easy"
        })
    
    print(f"  ✅ {len(queries)}개 GUID 쿼리 생성 완료")
    return queries


def generate_temporal_queries(data, count=100):
    """Temporal 쿼리 생성"""
    
    print(f"⏰ Temporal 쿼리 생성 중... ({count}개)")
    
    queries = []
    bcf_data = data["bcf_data"]
    
    # 날짜 범위 계산
    dates = []
    for issue in bcf_data:
        if issue.get("created"):
            try:
                # ISO 형식 날짜 파싱
                date_str = issue["created"]
                if date_str.endswith("Z"):
                    date_str = date_str.replace("Z", "+00:00")
                date = datetime.fromisoformat(date_str)
                # timezone 정보 제거하여 naive datetime으로 통일
                if date.tzinfo is not None:
                    date = date.replace(tzinfo=None)
                dates.append(date)
            except Exception as e:
                # 날짜 파싱 실패시 현재 시간으로 대체
                dates.append(datetime.now())
                continue
    
    if dates:
        min_date = min(dates)
        max_date = max(dates)
    else:
        min_date = datetime.now() - timedelta(days=365)
        max_date = datetime.now()
    
    # Temporal 쿼리 템플릿
    templates = [
        "최근 1주일 동안 생성된 이슈들은 무엇인가요?",
        "지난 달에 보고된 문제점들을 알려주세요.",
        "2024년에 생성된 모든 이슈를 보여주세요.",
        "최근 3개월 동안 해결되지 않은 이슈는 무엇인가요?",
        "오늘 생성된 새로운 이슈가 있나요?",
        "지난 주에 업데이트된 이슈들을 찾아주세요.",
        "최근 6개월 동안의 이슈 트렌드를 보여주세요.",
        "작년 이맘때 생성된 이슈와 비교해주세요.",
        "분기별 이슈 발생 현황을 알려주세요.",
        "최근 2주일 동안 우선순위가 높은 이슈는 무엇인가요?"
    ]
    
    for i in range(count):
        template = random.choice(templates)
        
        queries.append({
            "id": f"temporal_{i+1:03d}",
            "question": template,
            "query_type": "temporal",
            "time_range": "recent",
            "difficulty": "medium"
        })
    
    print(f"  ✅ {len(queries)}개 Temporal 쿼리 생성 완료")
    return queries


def generate_author_queries(data, count=100):
    """Author 쿼리 생성"""
    
    print(f"👤 Author 쿼리 생성 중... ({count}개)")
    
    queries = []
    authors = data["authors"]
    
    # Author 쿼리 템플릿
    templates = [
        "{author}이 작성한 이슈들을 보여주세요.",
        "{author}가 담당하고 있는 문제점들은 무엇인가요?",
        "{author}이 보고한 최근 이슈를 알려주세요.",
        "{author}가 해결한 이슈들의 목록을 보여주세요.",
        "{author}이 생성한 이슈 중 아직 해결되지 않은 것은 무엇인가요?",
        "{author}가 담당하는 프로젝트의 이슈 현황은 어떻게 되나요?",
        "{author}이 작성한 이슈 중 우선순위가 높은 것은 무엇인가요?",
        "{author}가 최근에 업데이트한 이슈를 찾아주세요.",
        "{author}이 생성한 이슈들의 통계를 보여주세요.",
        "{author}가 담당하는 이슈 중 지연된 것은 무엇인가요?"
    ]
    
    for i in range(count):
        author = random.choice(authors) if authors else f"engineer_{i%10:03d}"
        template = random.choice(templates)
        question = template.format(author=author)
        
        queries.append({
            "id": f"author_{i+1:03d}",
            "question": question,
            "query_type": "author",
            "expected_author": author,
            "difficulty": "medium"
        })
    
    print(f"  ✅ {len(queries)}개 Author 쿼리 생성 완료")
    return queries


def generate_keyword_queries(data, count=100):
    """Keyword 쿼리 생성"""
    
    print(f"🔑 Keyword 쿼리 생성 중... ({count}개)")
    
    queries = []
    keywords = data["keywords"]
    
    # Keyword 쿼리 템플릿
    templates = [
        "{keyword} 관련 이슈들을 찾아주세요.",
        "{keyword} 문제점이 있는 곳을 알려주세요.",
        "{keyword}와 관련된 모든 이슈를 보여주세요.",
        "{keyword} 관련 해결되지 않은 문제는 무엇인가요?",
        "{keyword} 이슈의 우선순위는 어떻게 되나요?",
        "{keyword} 관련 최근 이슈를 알려주세요.",
        "{keyword} 문제가 발생한 위치를 찾아주세요.",
        "{keyword} 관련 이슈의 해결 방법을 보여주세요.",
        "{keyword}와 연관된 다른 문제점들은 무엇인가요?",
        "{keyword} 이슈의 담당자를 알려주세요."
    ]
    
    for i in range(count):
        keyword = random.choice(keywords) if keywords else f"keyword_{i%20}"
        template = random.choice(templates)
        question = template.format(keyword=keyword)
        
        queries.append({
            "id": f"keyword_{i+1:03d}",
            "question": question,
            "query_type": "keyword",
            "expected_keyword": keyword,
            "difficulty": "medium"
        })
    
    print(f"  ✅ {len(queries)}개 Keyword 쿼리 생성 완료")
    return queries


def generate_complex_queries(data, count=100):
    """Complex 자연어 쿼리 생성"""
    
    print(f"🧠 Complex 자연어 쿼리 생성 중... ({count}개)")
    
    queries = []
    
    # Complex 쿼리 템플릿
    templates = [
        "작업 우선순위를 높여야 할 구조 관련 이슈는 무엇인가요?",
        "지난 달 생성되었지만 아직 해결되지 않은 설비 충돌은 무엇인가요?",
        "특정 층(3층)과 관련된 모든 협업 이슈를 찾아주세요.",
        "동일한 작성자가 보고한 유사 문제들의 패턴은 무엇인가요?",
        "긴급도가 높은 전기 관련 이슈 중 해결이 지연된 것은 무엇인가요?",
        "설계 변경으로 인해 발생한 모든 이슈를 분석해주세요.",
        "품질 검사에서 발견된 주요 문제점들을 우선순위별로 정리해주세요.",
        "예산 초과와 관련된 이슈들의 원인을 분석해주세요.",
        "안전 점검에서 발견된 위험 요소들을 분류해주세요.",
        "일정 지연을 야기하는 주요 이슈들을 찾아주세요.",
        "설비 설치 과정에서 발생한 문제점들을 해결 방법과 함께 보여주세요.",
        "구조적 결함과 관련된 모든 이슈의 심각도를 평가해주세요.",
        "환경 친화적 재료 사용과 관련된 이슈들을 검토해주세요.",
        "접근성 개선을 위한 이슈들의 구현 현황을 알려주세요.",
        "에너지 효율성과 관련된 문제점들을 분석해주세요."
    ]
    
    for i in range(count):
        template = random.choice(templates)
        
        queries.append({
            "id": f"complex_{i+1:03d}",
            "question": template,
            "query_type": "complex",
            "difficulty": "hard",
            "requires_reasoning": True
        })
    
    print(f"  ✅ {len(queries)}개 Complex 쿼리 생성 완료")
    return queries


def generate_relationship_queries(data, count=100):
    """관계 탐색 쿼리 생성"""
    
    print(f"🔗 관계 탐색 쿼리 생성 중... ({count}개)")
    
    queries = []
    bcf_data = data["bcf_data"]
    
    # 관계 탐색 쿼리 템플릿
    templates = [
        "이슈 {guid}와 관련된 다른 이슈들은 무엇인가요?",
        "{guid} 이슈의 원인과 결과를 분석해주세요.",
        "이슈 {guid}와 연관된 모든 문제점을 찾아주세요.",
        "{guid} 이슈가 다른 이슈에 미치는 영향을 보여주세요.",
        "이슈 {guid}의 의존성을 분석해주세요.",
        "{guid} 이슈와 유사한 다른 이슈들을 찾아주세요.",
        "이슈 {guid}의 해결이 다른 이슈에 미치는 영향을 알려주세요.",
        "{guid} 이슈와 동시에 발생한 다른 이슈들을 보여주세요.",
        "이슈 {guid}의 연쇄 반응을 분석해주세요.",
        "{guid} 이슈와 관련된 모든 담당자들의 작업을 정리해주세요."
    ]
    
    # GUID 선택을 위한 리스트
    guids = [issue.get("topic_id") for issue in bcf_data if issue.get("topic_id")]
    
    for i in range(count):
        guid = random.choice(guids) if guids else f"guid_{i%50:03d}"
        template = random.choice(templates)
        question = template.format(guid=guid)
        
        queries.append({
            "id": f"relationship_{i+1:03d}",
            "question": question,
            "query_type": "relationship",
            "expected_guid": guid,
            "difficulty": "hard",
            "requires_graph_traversal": True
        })
    
    print(f"  ✅ {len(queries)}개 관계 탐색 쿼리 생성 완료")
    return queries


def create_comprehensive_gold_standard():
    """종합 Gold Standard 생성"""
    
    print("🚀 종합 Gold Standard 생성 시작")
    print("=" * 50)
    
    # 1. 데이터 로드
    data = load_integrated_data()
    if not data:
        return
    
    print("\n" + "=" * 50)
    
    # 2. 각 쿼리 타입별 생성
    all_queries = []
    
    # GUID 쿼리 (100개)
    guid_queries = generate_guid_queries(data, 100)
    all_queries.extend(guid_queries)
    
    print("\n" + "=" * 50)
    
    # Temporal 쿼리 (100개)
    temporal_queries = generate_temporal_queries(data, 100)
    all_queries.extend(temporal_queries)
    
    print("\n" + "=" * 50)
    
    # Author 쿼리 (100개)
    author_queries = generate_author_queries(data, 100)
    all_queries.extend(author_queries)
    
    print("\n" + "=" * 50)
    
    # Keyword 쿼리 (100개)
    keyword_queries = generate_keyword_queries(data, 100)
    all_queries.extend(keyword_queries)
    
    print("\n" + "=" * 50)
    
    # Complex 쿼리 (100개)
    complex_queries = generate_complex_queries(data, 100)
    all_queries.extend(complex_queries)
    
    print("\n" + "=" * 50)
    
    # Relationship 쿼리 (100개)
    relationship_queries = generate_relationship_queries(data, 100)
    all_queries.extend(relationship_queries)
    
    print("\n" + "=" * 50)
    
    # 3. Gold Standard 저장
    output_file = Path("eval/gold_standard_comprehensive.jsonl")
    write_jsonl(str(output_file), all_queries)
    
    # 4. 통계 생성
    stats = {
        "total_queries": len(all_queries),
        "query_type_distribution": defaultdict(int),
        "difficulty_distribution": defaultdict(int),
        "generation_date": datetime.now().isoformat()
    }
    
    for query in all_queries:
        stats["query_type_distribution"][query["query_type"]] += 1
        stats["difficulty_distribution"][query["difficulty"]] += 1
    
    # 통계 저장
    stats_file = Path("eval/gold_standard_comprehensive_stats.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(dict(stats), f, indent=2, ensure_ascii=False)
    
    print("🎉 종합 Gold Standard 생성 완료!")
    print(f"\n📊 생성 결과:")
    print(f"  • 총 질의: {len(all_queries)}개")
    print(f"  • GUID: {stats['query_type_distribution']['guid']}개")
    print(f"  • Temporal: {stats['query_type_distribution']['temporal']}개")
    print(f"  • Author: {stats['query_type_distribution']['author']}개")
    print(f"  • Keyword: {stats['query_type_distribution']['keyword']}개")
    print(f"  • Complex: {stats['query_type_distribution']['complex']}개")
    print(f"  • Relationship: {stats['query_type_distribution']['relationship']}개")
    print(f"\n📁 저장 위치:")
    print(f"  • Gold Standard: {output_file}")
    print(f"  • 통계: {stats_file}")


if __name__ == "__main__":
    create_comprehensive_gold_standard()
