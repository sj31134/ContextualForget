#!/usr/bin/env python3
"""추가 BCF 데이터 대량 생성 (재현성 확보)"""

import os
import uuid
import random
import zipfile
import argparse
from pathlib import Path
from datetime import datetime, timedelta


# 재현성을 위한 시드 설정
SYNTHETIC_SEED = int(os.environ.get('SYNTHETIC_SEED', 42))
random.seed(SYNTHETIC_SEED)


class BCFGenerator:
    """BCF 파일 대량 생성기 (재현 가능)"""
    
    def __init__(self, base_dir: Path, seed: int = SYNTHETIC_SEED):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "data" / "raw" / "downloaded"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        
        # 시드 고정
        random.seed(self.seed)
        
        # 생성 메타데이터
        self.metadata = {
            "generation_date": datetime.now().isoformat(),
            "seed": self.seed,
            "version": "1.0",
            "reproducible": True
        }
        
        # 생성할 IFC GUID 목록 (기존 파일에서 추출하거나 랜덤 생성)
        self.available_guids = self.generate_guids(200)
        
        # 다양한 이슈 템플릿
        self.issue_templates = self.load_issue_templates()
    
    def generate_guids(self, count):
        """IFC GUID 생성"""
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
        return [''.join(random.choice(chars) for _ in range(22)) for _ in range(count)]
    
    def load_issue_templates(self):
        """다양한 이슈 템플릿"""
        return [
            # 구조적 문제
            {
                "category": "구조",
                "templates": [
                    ("기둥 단면 부족", "하중 계산 결과 기둥 단면이 부족합니다. 400x400 → 500x500으로 변경 필요."),
                    ("보 처짐 우려", "보의 처짐이 허용치를 초과합니다. 보강 또는 단면 증가 필요."),
                    ("슬라브 두께 확인", "슬라브 두께가 설계 기준에 미달합니다. 재검토 요청."),
                    ("내진 설계 미흡", "내진 벽체 배치가 구조 계산서와 불일치합니다."),
                    ("기초 깊이 변경", "지반 조사 결과 기초 깊이 증가 필요."),
                    ("철근 배근 오류", "철근 배근 상세가 구조 도면과 다릅니다."),
                    ("연결부 상세 누락", "기둥-보 접합부 상세도가 누락되었습니다."),
                ]
            },
            # 건축 문제
            {
                "category": "건축",
                "templates": [
                    ("벽체 두께 불일치", "외벽 두께가 단열 기준을 만족하지 못합니다."),
                    ("창호 위치 간섭", "창호 위치가 구조체와 간섭됩니다. 위치 조정 필요."),
                    ("출입문 폭 부족", "장애인 접근을 위한 출입문 폭이 부족합니다."),
                    ("천장고 부족", "설비 배관 고려 시 순 천장고가 부족합니다."),
                    ("마감재 변경", "마감재 사양이 승인된 내용과 다릅니다."),
                    ("방수층 시공", "방수층 시공 상세가 명확하지 않습니다."),
                    ("발코니 난간", "발코니 난간 높이가 안전 기준 미달입니다."),
                ]
            },
            # 설비 (기계)
            {
                "category": "기계설비",
                "templates": [
                    ("덕트 간섭", "공조 덕트가 구조 보와 간섭합니다."),
                    ("배관 경로 변경", "급수 배관 경로가 건축 벽체와 충돌합니다."),
                    ("기계실 공간 부족", "기계실 기기 배치 시 공간이 부족합니다."),
                    ("환기 용량 부족", "환기 용량이 실내 인원수 대비 부족합니다."),
                    ("보일러 용량", "보일러 용량 재검토 필요합니다."),
                    ("냉방 부하 초과", "냉방 부하가 예상보다 높습니다."),
                ]
            },
            # 전기
            {
                "category": "전기설비",
                "templates": [
                    ("전력 용량 부족", "전력 수용량이 부족합니다. 큐비클 증설 필요."),
                    ("조명 배치 변경", "조명 배치가 실 용도와 맞지 않습니다."),
                    ("콘센트 위치", "콘센트 위치가 가구 배치와 맞지 않습니다."),
                    ("비상등 누락", "비상등 설치가 누락되었습니다."),
                    ("접지 시스템", "접지 시스템 상세 확인 필요."),
                ]
            },
            # 소방
            {
                "category": "소방",
                "templates": [
                    ("스프링클러 헤드 추가", "스프링클러 헤드 설치 간격이 기준 초과합니다."),
                    ("비상구 유도등", "비상구 유도등 위치가 부적절합니다."),
                    ("소화전 접근", "소화전 접근 공간이 확보되지 않았습니다."),
                    ("방화구획 관통", "방화구획 관통부 방화 처리 누락."),
                ]
            },
            # 시공
            {
                "category": "시공",
                "templates": [
                    ("시공 순서 변경", "현장 여건상 시공 순서 변경 필요."),
                    ("자재 반입 경로", "자재 반입 경로 확보 어려움."),
                    ("양중 계획 수정", "타워크레인 양중 계획 재검토 필요."),
                    ("가설 시설 위치", "가설 사무실 위치 변경 요청."),
                ]
            }
        ]
    
    def create_bcf_topic(self, topic_id, title, description, author, creation_date, related_guids, status="Open"):
        """BCF 토픽 XML 생성"""
        markup = f"""<?xml version="1.0" encoding="UTF-8"?>
<Markup>
  <Header>
    <Files></Files>
  </Header>
  <Topic Guid="{topic_id}" TopicType="Issue" TopicStatus="{status}">
    <Title>{title}</Title>
    <CreationDate>{creation_date.isoformat()}</CreationDate>
    <CreationAuthor>{author}</CreationAuthor>
    <Description>{description}</Description>
  </Topic>"""
        
        # 관련 GUID 추가
        if related_guids:
            markup += "\n  <Viewpoints>"
            for guid in related_guids[:3]:  # 최대 3개
                markup += f'\n    <RelatedTopic Guid="{guid}"/>'
            markup += "\n  </Viewpoints>"
        
        markup += "\n</Markup>"
        
        return markup
    
    def generate_bcf_file(self, filename, num_topics=5):
        """BCF ZIP 파일 생성"""
        filepath = self.raw_dir / filename
        
        with zipfile.ZipFile(filepath, 'w') as bcf_zip:
            # bcf.version
            version_content = """<?xml version="1.0" encoding="UTF-8"?>
<Version VersionId="2.1">
  <DetailedVersion>2.1</DetailedVersion>
</Version>"""
            bcf_zip.writestr("bcf.version", version_content)
            
            # 각 토픽 생성
            for i in range(num_topics):
                topic_id = str(uuid.uuid4())
                
                # 랜덤 템플릿 선택
                category_data = random.choice(self.issue_templates)
                title, description = random.choice(category_data["templates"])
                
                # 메타데이터
                authors = ["engineer_kim", "engineer_lee", "engineer_park", 
                          "architect_choi", "architect_jung", "engineer_a", "engineer_b"]
                author = random.choice(authors)
                
                statuses = ["Open", "InProgress", "Resolved", "Closed"]
                status = random.choice(statuses)
                
                # 시간 (과거 90일 ~ 현재)
                days_ago = random.randint(0, 90)
                creation_date = datetime.now() - timedelta(days=days_ago)
                
                # 관련 GUID (1-3개)
                num_guids = random.randint(1, 3)
                related_guids = random.sample(self.available_guids, num_guids)
                
                # 토픽 XML 생성
                markup_content = self.create_bcf_topic(
                    topic_id, title, description, author, 
                    creation_date, related_guids, status
                )
                
                # ZIP에 추가
                bcf_zip.writestr(f"Topics/{topic_id}/markup.bcf", markup_content)
        
        return filepath
    
    def generate_multiple_bcf_files(self, count=50):
        """다수의 BCF 파일 생성"""
        print("=" * 70)
        print(f"🏗️  BCF 파일 {count}개 생성 중...")
        print("=" * 70)
        
        generated = []
        
        for i in range(count):
            # 파일명
            filename = f"synthetic_bcf_{i+1:03d}.bcfzip"
            
            # 토픽 수 (3-10개)
            num_topics = random.randint(3, 10)
            
            # 생성
            filepath = self.generate_bcf_file(filename, num_topics)
            generated.append({
                "filename": filename,
                "path": str(filepath),
                "topics_count": num_topics
            })
            
            if (i + 1) % 10 == 0:
                print(f"  ✅ {i + 1}/{count} 완료...")
        
        print(f"\n✨ 총 {len(generated)}개 BCF 파일 생성 완료!")
        
        return generated


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic BCF data with reproducibility')
    parser.add_argument('--seed', type=int, default=SYNTHETIC_SEED, 
                        help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--count', type=int, default=50,
                        help='Number of BCF files to generate (default: 50)')
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent
    generator = BCFGenerator(base_dir, seed=args.seed)
    
    print("🚀 BCF 데이터 대량 생성 (재현 가능)\n")
    print(f"🎲 시드: {args.seed}")
    print(f"📦 생성 수: {args.count}개\n")
    
    # BCF 파일 생성
    generated = generator.generate_multiple_bcf_files(count=args.count)
    
    # 통계
    total_topics = sum(bcf["topics_count"] for bcf in generated)
    
    # 메타데이터 저장
    metadata_path = base_dir / "data" / "synthetic" / "generation_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    generator.metadata.update({
        "bcf_files_generated": len(generated),
        "total_topics": total_topics,
        "files": generated
    })
    
    import json
    with open(metadata_path, 'w') as f:
        json.dump(generator.metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 생성 통계:")
    print(f"  - BCF 파일: {len(generated)}개")
    print(f"  - 총 이슈: 약 {total_topics}개")
    print(f"  - 저장 위치: data/raw/downloaded/")
    print(f"  - 메타데이터: {metadata_path}")
    
    print(f"\n✅ 재현성 확보:")
    print(f"  - 시드: {args.seed}")
    print(f"  - 버전: {generator.metadata['version']}")
    print(f"  - 재생성 명령:")
    print(f"    python scripts/generate_more_bcf.py --seed {args.seed} --count {args.count}")
    
    print("\n📝 다음 단계:")
    print("   python scripts/analyze_and_classify_data.py")


if __name__ == "__main__":
    main()

