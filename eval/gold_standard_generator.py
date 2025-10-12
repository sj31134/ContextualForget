#!/usr/bin/env python3
"""
Gold Standard QA 데이터셋 생성기

목적:
- 연구 평가를 위한 고품질 Question-Answer 쌍 생성
- BIM 전문가가 검증 가능한 구조
- Graph-RAG, Forgetting 메커니즘 평가용
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class GoldStandardGenerator:
    """Gold Standard QA 생성기"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.eval_dir = self.base_dir / "eval"
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        
        # QA 템플릿
        self.qa_templates = self._load_qa_templates()
    
    def _load_qa_templates(self) -> List[Dict[str, Any]]:
        """QA 템플릿 정의"""
        
        return [
            # === RQ1: Graph-RAG 검색 성능 ===
            {
                "category": "entity_search",
                "subcategory": "ifc_lookup",
                "question_template": "GUID {guid}는 어떤 IFC 요소인가요?",
                "answer_template": "GUID {guid}는 {entity_type}입니다. 이름: {name}",
                "difficulty": "easy",
                "requires": ["guid", "entity_type", "name"],
                "evaluation_type": "exact_match"
            },
            {
                "category": "entity_search",
                "subcategory": "bcf_issue_lookup",
                "question_template": "{guid}와 관련된 BCF 이슈는 무엇인가요?",
                "answer_template": "총 {count}개의 이슈가 있습니다: {issue_list}",
                "difficulty": "medium",
                "requires": ["guid", "issue_list", "count"],
                "evaluation_type": "set_match"
            },
            {
                "category": "relationship",
                "subcategory": "connected_components",
                "question_template": "{entity_name}와 연결된 다른 요소들은 무엇인가요?",
                "answer_template": "{entity_name}는 다음과 연결되어 있습니다: {connected_list}",
                "difficulty": "medium",
                "requires": ["entity_name", "connected_list"],
                "evaluation_type": "set_match"
            },
            {
                "category": "temporal",
                "subcategory": "recent_issues",
                "question_template": "최근 {days}일 이내에 생성된 이슈는 무엇인가요?",
                "answer_template": "최근 {days}일 내 {count}개 이슈: {issue_list}",
                "difficulty": "easy",
                "requires": ["days", "count", "issue_list"],
                "evaluation_type": "set_match"
            },
            {
                "category": "temporal",
                "subcategory": "old_issues",
                "question_template": "{days}일 이전에 생성된 오래된 이슈는?",
                "answer_template": "{days}일 이전 {count}개 이슈: {issue_list}",
                "difficulty": "easy",
                "requires": ["days", "count", "issue_list"],
                "evaluation_type": "set_match"
            },
            
            # === RQ2: 망각 메커니즘 평가 ===
            {
                "category": "forgetting",
                "subcategory": "ttl_filter",
                "question_template": "TTL {ttl}일 기준으로 유효한 이슈만 보여주세요.",
                "answer_template": "TTL {ttl}일 기준 {count}개 이슈가 유효합니다: {issue_list}",
                "difficulty": "medium",
                "requires": ["ttl", "count", "issue_list"],
                "evaluation_type": "set_match"
            },
            {
                "category": "forgetting",
                "subcategory": "old_version_citation",
                "question_template": "{guid}의 이전 버전 정보가 포함되어 있나요?",
                "answer_template": "망각 정책에 따라 {status}. 이유: {reason}",
                "difficulty": "hard",
                "requires": ["guid", "status", "reason"],
                "evaluation_type": "semantic_match"
            },
            {
                "category": "forgetting",
                "subcategory": "contradiction_detection",
                "question_template": "{entity_name}에 대한 모순된 정보가 있나요?",
                "answer_template": "{status}. 세부사항: {details}",
                "difficulty": "hard",
                "requires": ["entity_name", "status", "details"],
                "evaluation_type": "semantic_match"
            },
            
            # === RQ3: 변경 영향 추적 ===
            {
                "category": "change_impact",
                "subcategory": "multi_hop",
                "question_template": "{entity_name}을 변경하면 어떤 요소들에 영향을 주나요?",
                "answer_template": "{entity_name} 변경 시 영향 받는 요소: {affected_list}",
                "difficulty": "hard",
                "requires": ["entity_name", "affected_list"],
                "evaluation_type": "set_match"
            },
            {
                "category": "change_impact",
                "subcategory": "issue_propagation",
                "question_template": "이슈 '{issue_title}'이 해결되지 않으면 어떤 작업이 막히나요?",
                "answer_template": "막히는 작업: {blocked_tasks}. 이유: {reason}",
                "difficulty": "hard",
                "requires": ["issue_title", "blocked_tasks", "reason"],
                "evaluation_type": "semantic_match"
            },
            
            # === 통합 질의 ===
            {
                "category": "complex",
                "subcategory": "statistics",
                "question_template": "현재 프로젝트의 전체 통계를 보여주세요.",
                "answer_template": "총 IFC 요소: {ifc_count}개, BCF 이슈: {bcf_count}개, 해결됨: {resolved_count}개",
                "difficulty": "easy",
                "requires": ["ifc_count", "bcf_count", "resolved_count"],
                "evaluation_type": "exact_match"
            },
            {
                "category": "complex",
                "subcategory": "author_activity",
                "question_template": "{author}가 작성한 이슈는 무엇인가요?",
                "answer_template": "{author} 작성 {count}개: {issue_list}",
                "difficulty": "easy",
                "requires": ["author", "count", "issue_list"],
                "evaluation_type": "set_match"
            },
        ]
    
    def generate_gold_standard(self, count: int = 50) -> List[Dict[str, Any]]:
        """Gold Standard QA 쌍 생성"""
        
        print(f"🔨 Gold Standard QA 데이터셋 생성 중 ({count}개)...")
        
        qa_pairs = []
        
        # 카테고리별 분배
        categories = {
            "entity_search": int(count * 0.25),      # 25%
            "relationship": int(count * 0.15),       # 15%
            "temporal": int(count * 0.15),           # 15%
            "forgetting": int(count * 0.20),         # 20%
            "change_impact": int(count * 0.15),      # 15%
            "complex": int(count * 0.10)             # 10%
        }
        
        qa_id = 1
        
        for category, target_count in categories.items():
            templates = [t for t in self.qa_templates if t["category"] == category]
            
            for i in range(target_count):
                template = templates[i % len(templates)]
                
                # QA 쌍 생성
                qa_pair = {
                    "id": f"qa_{qa_id:03d}",
                    "category": template["category"],
                    "subcategory": template["subcategory"],
                    "difficulty": template["difficulty"],
                    "question": template["question_template"],
                    "answer": template["answer_template"],
                    "requires": template["requires"],
                    "evaluation_type": template["evaluation_type"],
                    "status": "template",  # 실제 데이터로 채워야 함
                    "metadata": {
                        "created": datetime.now().isoformat(),
                        "validated": False,
                        "expert_reviewed": False
                    }
                }
                
                qa_pairs.append(qa_pair)
                qa_id += 1
        
        print(f"  ✅ {len(qa_pairs)}개 QA 템플릿 생성 완료")
        
        return qa_pairs
    
    def save_gold_standard(self, qa_pairs: List[Dict[str, Any]], filename: str = "gold_standard.jsonl"):
        """Gold Standard 저장"""
        
        output_path = self.eval_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for qa in qa_pairs:
                f.write(json.dumps(qa, ensure_ascii=False) + '\n')
        
        print(f"  💾 저장 완료: {output_path}")
        
        # 통계 생성
        stats = self._generate_statistics(qa_pairs)
        stats_path = self.eval_dir / "gold_standard_stats.json"
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"  📊 통계 저장: {stats_path}")
        
        return output_path
    
    def _generate_statistics(self, qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """QA 데이터셋 통계"""
        
        from collections import Counter
        
        stats = {
            "total_count": len(qa_pairs),
            "by_category": dict(Counter(qa["category"] for qa in qa_pairs)),
            "by_difficulty": dict(Counter(qa["difficulty"] for qa in qa_pairs)),
            "by_evaluation_type": dict(Counter(qa["evaluation_type"] for qa in qa_pairs)),
            "status": {
                "template": len([qa for qa in qa_pairs if qa["status"] == "template"]),
                "filled": len([qa for qa in qa_pairs if qa["status"] == "filled"]),
                "validated": len([qa for qa in qa_pairs if qa["metadata"]["validated"]])
            }
        }
        
        return stats
    
    def create_expert_validation_form(self, qa_pairs: List[Dict[str, Any]]):
        """전문가 검증 양식 생성"""
        
        form_path = self.eval_dir / "EXPERT_VALIDATION_FORM.md"
        
        with open(form_path, 'w', encoding='utf-8') as f:
            f.write(f"""# Gold Standard QA 전문가 검증 양식

**생성일**: {datetime.now().strftime('%Y-%m-%d')}  
**총 QA 쌍**: {len(qa_pairs)}개  
**검증자**: [전문가 이름]  
**검증일**: [날짜]

---

## 검증 기준

각 QA 쌍에 대해 다음을 평가해주세요:

1. **정확성 (Accuracy)**: 답변이 정확한가?
   - ✅ 정확함
   - ⚠️ 부분적으로 정확
   - ❌ 부정확

2. **완전성 (Completeness)**: 답변이 완전한가?
   - ✅ 완전함
   - ⚠️ 추가 정보 필요
   - ❌ 불완전

3. **현실성 (Realism)**: 실제 BIM 프로젝트에서 발생할 법한 질문인가?
   - ✅ 현실적
   - ⚠️ 가능하지만 드묾
   - ❌ 비현실적

4. **난이도 (Difficulty)**: 설정된 난이도가 적절한가?
   - ✅ 적절함
   - ⚠️ 조정 필요
   - ❌ 부적절

---

## QA 쌍 리스트

""")
            
            # 카테고리별로 정리
            by_category = {}
            for qa in qa_pairs:
                cat = qa["category"]
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(qa)
            
            for category, qas in sorted(by_category.items()):
                f.write(f"\n### {category.replace('_', ' ').title()} ({len(qas)}개)\n\n")
                
                for i, qa in enumerate(qas[:5], 1):  # 샘플로 5개만
                    f.write(f"#### {qa['id']}\n\n")
                    f.write(f"**질문**: {qa['question']}\n\n")
                    f.write(f"**답변**: {qa['answer']}\n\n")
                    f.write(f"**난이도**: {qa['difficulty']}\n\n")
                    f.write(f"**검증**:\n")
                    f.write(f"- [ ] 정확성: ___\n")
                    f.write(f"- [ ] 완전성: ___\n")
                    f.write(f"- [ ] 현실성: ___\n")
                    f.write(f"- [ ] 난이도: ___\n")
                    f.write(f"- 코멘트: ___\n\n")
                    f.write("---\n\n")
                
                if len(qas) > 5:
                    f.write(f"_(... 나머지 {len(qas) - 5}개 QA 쌍 생략)_\n\n")
            
            f.write(f"""
---

## 전체 평가

### 데이터셋 품질

1. 전반적인 품질: [ ] 우수 [ ] 양호 [ ] 보통 [ ] 개선 필요

2. 주요 강점:
   - 
   - 

3. 개선이 필요한 부분:
   - 
   - 

4. 추가 제안 사항:
   - 
   - 

### 서명

**검증자**: _______________  
**소속**: _______________  
**경력**: ___ 년  
**날짜**: _______________

---

**검증 완료 후 이 파일을 다음 경로로 제출해주세요**:
- 이메일: [your-email@example.com]
- 또는: eval/expert_reviews/[검증자명]_validation.md
""")
        
        print(f"  📋 전문가 검증 양식 생성: {form_path}")
        
        return form_path


def main():
    """메인 실행"""
    
    base_dir = Path(__file__).parent.parent
    generator = GoldStandardGenerator(base_dir)
    
    print("=" * 70)
    print("🎯 Gold Standard QA 데이터셋 생성")
    print("=" * 70)
    print()
    
    # 1. QA 쌍 생성
    qa_pairs = generator.generate_gold_standard(count=50)
    
    # 2. 저장
    output_path = generator.save_gold_standard(qa_pairs)
    
    # 3. 전문가 검증 양식 생성
    form_path = generator.create_expert_validation_form(qa_pairs)
    
    # 요약
    print()
    print("=" * 70)
    print("✅ Gold Standard 생성 완료")
    print("=" * 70)
    print(f"""
📊 통계:
  - 총 QA 쌍: {len(qa_pairs)}개
  - 카테고리: 6개 (Entity, Relationship, Temporal, Forgetting, Change, Complex)
  - 난이도: Easy/Medium/Hard

📂 생성 파일:
  - {output_path}
  - {output_path.parent / 'gold_standard_stats.json'}
  - {form_path}

📝 다음 단계:
  1. ⚠️  템플릿을 실제 데이터로 채우기
     → python eval/fill_gold_standard.py
  
  2. 전문가 검증 의뢰
     → eval/EXPERT_VALIDATION_FORM.md 전달
  
  3. 평가 메트릭 구현
     → python eval/metrics.py
""")


if __name__ == "__main__":
    main()

