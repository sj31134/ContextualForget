#!/usr/bin/env python3
"""다양한 IFC 및 BCF 샘플 데이터 생성 스크립트."""

import os
import json
import zipfile
import random
from datetime import datetime, timedelta
from pathlib import Path
import uuid


def generate_guid():
    """IFC GUID 생성 (Base64 인코딩 22자)."""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
    return ''.join(random.choice(chars) for _ in range(22))


def create_ifc_building(filename: str, building_type: str, num_elements: int = 10):
    """다양한 건물 유형의 IFC 파일 생성."""
    guid = generate_guid()
    building_guid = generate_guid()
    project_guid = generate_guid()
    
    ifc_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('{filename}','2025-10-09T12:00:00',('Architect'),('Building Designer'),'IfcOpenShell','IfcOpenShell-0.6.0','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;

DATA;
#1=IFCPROJECT('{project_guid}',$,'{building_type} Project',$,$,$,$,(#2),#3);
#2=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#4,$);
#3=IFCUNITASSIGNMENT((#5));
#4=IFCAXIS2PLACEMENT3D(#6,$,$);
#5=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#6=IFCCARTESIANPOINT((0.,0.,0.));
#7=IFCSITE('{guid}',$,'{building_type} Site',$,$,#8,$,$,.ELEMENT.,(0,0,0),(0,0,0),0.,$,$);
#8=IFCLOCALPLACEMENT($,#9);
#9=IFCAXIS2PLACEMENT3D(#6,$,$);
#10=IFCBUILDING('{building_guid}',$,'{building_type} Building',$,$,#11,$,$,.ELEMENT.,$,$,$);
#11=IFCLOCALPLACEMENT(#8,#12);
#12=IFCAXIS2PLACEMENT3D(#6,$,$);
#13=IFCRELAGGREGATES('{generate_guid()}',$,$,$,#1,(#7));
#14=IFCRELAGGREGATES('{generate_guid()}',$,$,$,#7,(#10));
"""
    
    # 다양한 건물 요소 생성
    elements = []
    element_types = {
        "residential": ["IFCWALL", "IFCSLAB", "IFCDOOR", "IFCWINDOW", "IFCSTAIR"],
        "office": ["IFCWALL", "IFCCOLUMN", "IFCBEAM", "IFCSLAB", "IFCCURTAINWALL"],
        "industrial": ["IFCCOLUMN", "IFCBEAM", "IFCROOF", "IFCMEMBER", "IFCPLATE"],
        "hospital": ["IFCWALL", "IFCDOOR", "IFCWINDOW", "IFCSLAB", "IFCFURNISHINGELEMENT"],
        "school": ["IFCWALL", "IFCDOOR", "IFCWINDOW", "IFCSLAB", "IFCSTAIR"]
    }
    
    element_list = element_types.get(building_type, element_types["residential"])
    
    line_num = 15
    for i in range(num_elements):
        element_type = random.choice(element_list)
        element_guid = generate_guid()
        element_name = f"{element_type.replace('IFC', '')}_{i+1}"
        
        ifc_content += f"#{line_num}={element_type}('{element_guid}',$,'{element_name}',$,$,#11,$,$);\n"
        elements.append(element_guid)
        line_num += 1
    
    ifc_content += "ENDSEC;\nEND-ISO-10303-21;"
    
    return ifc_content, elements, building_guid


def create_bcf_topic(topic_id: str, title: str, description: str, author: str, 
                     creation_date: datetime, related_guids: list, status: str = "Open"):
    """BCF 토픽 생성."""
    markup_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Markup>
  <Topic Guid="{topic_id}" TopicType="Issue" TopicStatus="{status}">
    <Title>{title}</Title>
    <CreationDate>{creation_date.isoformat()}</CreationDate>
    <CreationAuthor>{author}</CreationAuthor>
    <Description>{description}</Description>
  </Topic>
  <Comment Guid="{uuid.uuid4()}">
    <Date>{creation_date.isoformat()}</Date>
    <Author>{author}</Author>
    <Comment>Initial issue report</Comment>
  </Comment>
"""
    
    # 관련 GUID 추가
    if related_guids:
        for guid in related_guids[:3]:  # 최대 3개
            markup_content += f'  <RelatedTopic Guid="{guid}"/>\n'
    
    markup_content += "</Markup>"
    return markup_content


def create_bcf_zip(zip_path: str, topics: list):
    """BCF ZIP 파일 생성."""
    with zipfile.ZipFile(zip_path, 'w') as bcf_zip:
        # bcf.version 파일
        version_content = """<?xml version="1.0" encoding="UTF-8"?>
<Version VersionId="2.1">
  <DetailedVersion>2.1</DetailedVersion>
</Version>"""
        bcf_zip.writestr("bcf.version", version_content)
        
        # 각 토픽 추가
        for topic_id, markup_content in topics:
            bcf_zip.writestr(f"Topics/{topic_id}/markup.bcf", markup_content)


def main():
    """메인 실행 함수."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    
    # 디렉토리 생성
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    print("🏗️  다양한 IFC 샘플 파일 생성 중...")
    
    # 다양한 건물 유형의 IFC 파일 생성
    building_types = [
        ("residential", "주거용 건물", 15),
        ("office", "오피스 빌딩", 20),
        ("industrial", "공장 건물", 12),
        ("hospital", "병원", 18),
        ("school", "학교", 16)
    ]
    
    all_guids = {}
    
    for building_type, korean_name, num_elements in building_types:
        filename = f"{building_type}_building.ifc"
        filepath = data_dir / filename
        
        ifc_content, elements, building_guid = create_ifc_building(
            filename, building_type, num_elements
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ifc_content)
        
        all_guids[building_type] = {
            "building_guid": building_guid,
            "elements": elements,
            "filename": filename,
            "korean_name": korean_name
        }
        
        print(f"  ✅ {filename} 생성 완료 ({num_elements}개 요소)")
    
    print(f"\n📋 BCF 이슈 파일 생성 중...")
    
    # 각 건물에 대한 BCF 이슈 생성
    authors = ["engineer_a", "engineer_b", "engineer_c", "architect_kim", "architect_lee"]
    statuses = ["Open", "InProgress", "Resolved", "Closed"]
    
    base_date = datetime.now() - timedelta(days=90)
    
    for building_type, info in all_guids.items():
        bcf_topics = []
        num_topics = random.randint(3, 7)
        
        for i in range(num_topics):
            topic_id = str(uuid.uuid4())
            creation_date = base_date + timedelta(days=random.randint(0, 90))
            author = random.choice(authors)
            status = random.choice(statuses)
            
            # 건물 유형에 맞는 이슈 생성
            issues = {
                "residential": [
                    ("벽체 두께 불일치", "외벽과 내벽의 두께가 도면과 다릅니다."),
                    ("창호 위치 확인 필요", "창문 위치가 구조와 충돌합니다."),
                    ("계단 치수 오류", "계단 높이가 건축법 기준에 미달합니다."),
                ],
                "office": [
                    ("기둥 간격 재검토", "기둥 배치가 공조 설비와 간섭됩니다."),
                    ("커튼월 설치 위치", "커튼월 프레임이 슬라브와 충돌합니다."),
                    ("바닥 레벨 차이", "층고가 설계 사양과 다릅니다."),
                ],
                "industrial": [
                    ("지붕 구조 보강 필요", "적설하중 계산 재검토가 필요합니다."),
                    ("기둥 단면 확대", "내하력 부족으로 단면 증가 필요합니다."),
                    ("보 연결부 상세", "용접 상세도가 누락되었습니다."),
                ],
                "hospital": [
                    ("방화문 위치 변경", "피난 동선 고려하여 위치 조정 필요합니다."),
                    ("설비 배관 간섭", "천장 배관이 구조체와 간섭됩니다."),
                    ("무균실 마감 사양", "벽체 마감재 변경이 필요합니다."),
                ],
                "school": [
                    ("교실 채광 부족", "창호 크기 확대가 필요합니다."),
                    ("복도 폭원 부족", "건축법 기준 미달입니다."),
                    ("계단실 방화구획", "방화문 추가 설치 필요합니다."),
                ]
            }
            
            title, description = random.choice(issues.get(building_type, issues["residential"]))
            related_guids = random.sample(info["elements"], min(2, len(info["elements"])))
            
            markup_content = create_bcf_topic(
                topic_id, title, description, author, 
                creation_date, related_guids, status
            )
            
            bcf_topics.append((topic_id, markup_content))
        
        # BCF ZIP 파일 생성
        bcf_filename = f"{building_type}_issues.bcfzip"
        bcf_path = raw_dir / bcf_filename
        create_bcf_zip(str(bcf_path), bcf_topics)
        
        print(f"  ✅ {bcf_filename} 생성 완료 ({num_topics}개 이슈)")
    
    # sources.json 업데이트
    sources_data = {
        "ifc_files": [
            {
                "name": info["filename"],
                "type": building_type,
                "korean_name": info["korean_name"],
                "elements_count": len(info["elements"]),
                "building_guid": info["building_guid"]
            }
            for building_type, info in all_guids.items()
        ],
        "bcf_files": [
            f"{building_type}_issues.bcfzip"
            for building_type in all_guids.keys()
        ],
        "generated_at": datetime.now().isoformat()
    }
    
    with open(data_dir / "sources.json", 'w', encoding='utf-8') as f:
        json.dump(sources_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✨ 샘플 데이터 생성 완료!")
    print(f"  📊 IFC 파일: {len(all_guids)}개")
    print(f"  📋 BCF 파일: {len(all_guids)}개")
    print(f"  🏷️  총 건물 요소: {sum(len(info['elements']) for info in all_guids.values())}개")


if __name__ == "__main__":
    main()

