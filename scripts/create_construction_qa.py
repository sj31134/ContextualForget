#!/usr/bin/env python3
"""
건설 도메인 질의응답(QA) 데이터셋 생성
KorQuAD 형식으로 건설 관련 QA 쌍 생성
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# 건설 도메인 QA 템플릿
CONSTRUCTION_QA_TEMPLATES = [
    {
        "context": "BIM(Building Information Modeling)은 건축물의 생애주기 동안 발생하는 모든 정보를 통합하여 관리하는 프로세스입니다. IFC(Industry Foundation Classes)는 BIM 데이터를 교환하기 위한 국제 표준 파일 형식으로, buildingSMART에서 개발하고 관리합니다. BCF(BIM Collaboration Format)는 BIM 모델에서 발견된 이슈를 문서화하고 공유하기 위한 개방형 파일 형식입니다.",
        "qas": [
            {
                "question": "BIM은 무엇의 약자인가요?",
                "answers": [{"text": "Building Information Modeling", "answer_start": 4}],
                "id": "construction_001"
            },
            {
                "question": "IFC 표준을 관리하는 기관은 어디인가요?",
                "answers": [{"text": "buildingSMART", "answer_start": 150}],
                "id": "construction_002"
            },
            {
                "question": "BCF는 어떤 용도로 사용되나요?",
                "answers": [{"text": "BIM 모델에서 발견된 이슈를 문서화하고 공유", "answer_start": 190}],
                "id": "construction_003"
            }
        ]
    },
    {
        "context": "건설 프로젝트에서 충돌 감지(Clash Detection)는 설계 단계에서 서로 다른 분야의 요소들이 물리적으로 겹치는 부분을 찾아내는 프로세스입니다. 예를 들어, 구조 기둥과 기계설비 덕트가 같은 공간을 차지하는 경우를 사전에 발견하여 시공 오류를 방지할 수 있습니다. 이는 공사 비용 절감과 일정 단축에 크게 기여합니다.",
        "qas": [
            {
                "question": "충돌 감지는 언제 수행되나요?",
                "answers": [{"text": "설계 단계", "answer_start": 45}],
                "id": "construction_004"
            },
            {
                "question": "충돌 감지의 주요 목적은 무엇인가요?",
                "answers": [{"text": "시공 오류를 방지", "answer_start": 140}],
                "id": "construction_005"
            }
        ]
    },
    {
        "context": "IfcWall, IfcColumn, IfcBeam은 IFC 표준에서 정의하는 건축 요소입니다. IfcWall은 벽체를, IfcColumn은 기둥을, IfcBeam은 보를 나타냅니다. 각 요소는 형상 정보, 재료 속성, 위치 정보 등을 포함합니다. IFC4 버전에서는 IfcRelConnectsElements를 통해 요소 간의 연결 관계를 표현할 수 있습니다.",
        "qas": [
            {
                "question": "IfcColumn은 무엇을 나타내나요?",
                "answers": [{"text": "기둥", "answer_start": 65}],
                "id": "construction_006"
            },
            {
                "question": "IFC 요소가 포함하는 정보는 무엇인가요?",
                "answers": [{"text": "형상 정보, 재료 속성, 위치 정보", "answer_start": 95}],
                "id": "construction_007"
            }
        ]
    },
    {
        "context": "BCF 이슈는 여러 상태를 가질 수 있습니다. Open은 새로 생성된 이슈, InProgress는 해결 중인 이슈, Resolved는 해결이 완료되어 검토 대기 중인 이슈, Closed는 최종 승인된 이슈를 의미합니다. 각 이슈는 작성자, 담당자, 우선순위, 마감일 등의 메타데이터를 포함합니다.",
        "qas": [
            {
                "question": "BCF 이슈의 상태 중 해결 완료 후 검토 대기 상태는?",
                "answers": [{"text": "Resolved", "answer_start": 85}],
                "id": "construction_008"
            },
            {
                "question": "BCF 이슈에 포함되는 메타데이터는?",
                "answers": [{"text": "작성자, 담당자, 우선순위, 마감일", "answer_start": 150}],
                "id": "construction_009"
            }
        ]
    },
    {
        "context": "LOD(Level of Development)는 BIM 모델의 상세도를 나타내는 지표입니다. LOD 100은 개념 설계, LOD 200은 기본 설계, LOD 300은 실시 설계, LOD 400은 제작 설계, LOD 500은 준공 모델을 의미합니다. 프로젝트 단계에 따라 적절한 LOD를 적용하여 불필요한 모델링 작업을 줄일 수 있습니다.",
        "qas": [
            {
                "question": "LOD 300은 어떤 설계 단계를 의미하나요?",
                "answers": [{"text": "실시 설계", "answer_start": 105}],
                "id": "construction_010"
            },
            {
                "question": "준공 모델에 해당하는 LOD는?",
                "answers": [{"text": "LOD 500", "answer_start": 140}],
                "id": "construction_011"
            }
        ]
    }
]


def create_korquad_format_construction_qa():
    """건설 도메인 QA를 KorQuAD 형식으로 생성"""
    print("\n" + "="*60)
    print("📝 건설 도메인 QA 데이터셋 생성 (KorQuAD 형식)")
    print("="*60)
    
    # KorQuAD 형식 데이터 생성
    dataset = {
        "version": "construction-qa-v1.0",
        "data": []
    }
    
    for idx, template in enumerate(CONSTRUCTION_QA_TEMPLATES):
        paragraph = {
            "context": template["context"],
            "qas": template["qas"]
        }
        
        article = {
            "title": f"건설_BIM_문서_{idx+1}",
            "paragraphs": [paragraph]
        }
        
        dataset["data"].append(article)
    
    # 저장
    output_dir = PROJECT_ROOT / "data" / "external" / "korquad"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "construction_qa_korquad_format.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 생성 완료:")
    print(f"   파일: {output_file}")
    print(f"   문서 수: {len(dataset['data'])}개")
    
    total_qas = sum(len(d["paragraphs"][0]["qas"]) for d in dataset["data"])
    print(f"   QA 쌍: {total_qas}개")
    
    # 통계
    print(f"\n📊 데이터셋 통계:")
    print(f"   평균 문맥 길이: {sum(len(d['paragraphs'][0]['context']) for d in dataset['data']) / len(dataset['data']):.0f}자")
    print(f"   평균 질문 길이: {sum(len(qa['question']) for d in dataset['data'] for qa in d['paragraphs'][0]['qas']) / total_qas:.0f}자")
    
    return dataset


def main():
    """메인 실행"""
    dataset = create_korquad_format_construction_qa()
    
    print("\n" + "="*60)
    print("✅ 건설 도메인 QA 데이터셋 생성 완료!")
    print("="*60)
    
    print("\n📍 다음 단계:")
    print("   1. 평가 시스템에 QA 데이터 통합")
    print("   2. RAG 시스템 질의응답 성능 평가")
    print("   3. 한국어 처리 성능 검증")


if __name__ == "__main__":
    main()

