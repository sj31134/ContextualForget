"""
Ollama LLM을 사용한 Gold Standard QA 생성
qwen2.5:3b 모델로 100개의 QA 쌍 생성
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core import write_jsonl


def generate_qa_prompt(sample_type: str, data: Dict) -> str:
    """
    샘플 타입에 따른 LLM 프롬프트 생성
    
    Args:
        sample_type: 'entity_search', 'issue_search', 'relationship'
        data: 샘플 데이터
        
    Returns:
        LLM 프롬프트 문자열
    """
    if sample_type == 'entity_search':
        return f"""당신은 BIM 전문가입니다. 다음 IFC 엔티티에 대한 자연스러운 한국어 질문-답변 쌍을 생성하세요.

IFC 엔티티:
- GUID: {data['guid']}
- 타입: {data['type']}
- 이름: {data.get('name', 'N/A')}

JSON 형식으로 질문-답변을 생성하세요:
{{"question": "이 GUID의 엔티티 타입은 무엇인가요?", "answer": "이 엔티티는 {data['type']}입니다.", "gold_entities": ["{data['guid']}"]}}

JSON만 출력하세요. 다른 텍스트는 포함하지 마세요."""

    elif sample_type == 'issue_search':
        return f"""당신은 BIM 전문가입니다. 다음 BCF 이슈에 대한 자연스러운 한국어 질문-답변 쌍을 생성하세요.

BCF 이슈:
- Topic ID: {data['topic_id']}
- 제목: {data.get('title', 'N/A')}
- 설명: {data.get('description', 'N/A')[:100]}
- 우선순위: {data.get('priority', 'N/A')}

JSON 형식으로 질문-답변을 생성하세요:
{{"question": "이 이슈의 제목은 무엇인가요?", "answer": "{data.get('title', 'N/A')}", "gold_entities": ["{data['topic_id']}"]}}

JSON만 출력하세요. 다른 텍스트는 포함하지 마세요."""

    elif sample_type == 'relationship':
        return f"""당신은 BIM 전문가입니다. BCF 이슈와 IFC 엔티티의 관계에 대한 자연스러운 한국어 질문-답변 쌍을 생성하세요.

BCF 이슈:
- 제목: {data.get('bcf_title', 'N/A')}
- 설명: {data.get('bcf_description', 'N/A')[:100]}

연결된 IFC:
- GUID: {data['ifc_guid']}
- 타입: {data.get('ifc_type', 'N/A')}
- 이름: {data.get('ifc_name', 'N/A')}

JSON 형식으로 질문-답변을 생성하세요:
{{"question": "이 이슈와 관련된 IFC 엔티티는 무엇인가요?", "answer": "{data.get('ifc_type', 'N/A')} (GUID: {data['ifc_guid']})", "gold_entities": ["{data['ifc_guid']}"]}}

JSON만 출력하세요. 다른 텍스트는 포함하지 마세요."""

    return ""


def call_ollama(prompt: str, model: str = "qwen2.5:3b") -> str:
    """
    Ollama LLM 호출
    
    Args:
        prompt: LLM 프롬프트
        model: 사용할 모델 이름
        
    Returns:
        LLM 응답 문자열
    """
    try:
        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"⚠️  Ollama 타임아웃")
        return ""
    except Exception as e:
        print(f"⚠️  Ollama 호출 실패: {e}")
        return ""


def extract_json_from_response(response: str) -> Dict:
    """
    LLM 응답에서 JSON 추출
    
    Args:
        response: LLM 응답 문자열
        
    Returns:
        파싱된 JSON 딕셔너리
    """
    # JSON 코드 블록 제거
    response = response.strip()
    if response.startswith('```json'):
        response = response[7:]
    if response.startswith('```'):
        response = response[3:]
    if response.endswith('```'):
        response = response[:-3]
    
    response = response.strip()
    
    # JSON 파싱 시도
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # JSON이 아닌 경우 첫 번째 { } 찾기
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(response[start:end+1])
            except json.JSONDecodeError:
                pass
        return None


def generate_qa_pairs(samples_file: str, output_file: str, model: str = "qwen2.5:3b"):
    """
    샘플에서 QA 쌍 생성
    
    Args:
        samples_file: 대표 샘플 JSON 파일
        output_file: 출력 JSONL 파일
        model: Ollama 모델 이름
    """
    print(f"📂 샘플 로드 중: {samples_file}")
    with open(samples_file, 'r', encoding='utf-8') as f:
        samples_data = json.load(f)
    
    # 샘플 준비
    all_samples = []
    
    # IFC 샘플 (30개 → entity_search)
    for sample in samples_data['ifc_samples']:
        all_samples.append({
            'type': 'entity_search',
            'data': sample
        })
    
    # BCF 샘플 (30개 → issue_search)
    for sample in samples_data['bcf_samples']:
        all_samples.append({
            'type': 'issue_search',
            'data': sample
        })
    
    # 연결된 쌍 (40개 → relationship)
    for sample in samples_data['connected_pairs']:
        all_samples.append({
            'type': 'relationship',
            'data': sample
        })
    
    print(f"✅ 총 샘플: {len(all_samples)}개")
    print(f"   entity_search: {len(samples_data['ifc_samples'])}개")
    print(f"   issue_search: {len(samples_data['bcf_samples'])}개")
    print(f"   relationship: {len(samples_data['connected_pairs'])}개")
    
    # QA 생성
    print(f"\n🤖 Ollama LLM ({model})으로 QA 생성 중...")
    print(f"   예상 시간: ~{len(all_samples) * 5 / 60:.1f}분")
    
    qa_pairs = []
    success_count = 0
    
    for i, sample in enumerate(all_samples):
        if (i + 1) % 10 == 0:
            print(f"   진행: {i+1}/{len(all_samples)} ({(i+1)/len(all_samples)*100:.1f}%)")
        
        # 프롬프트 생성
        prompt = generate_qa_prompt(sample['type'], sample['data'])
        
        # LLM 호출
        response = call_ollama(prompt, model)
        
        if not response:
            print(f"   ⚠️  QA {i+1} 생성 실패: 응답 없음")
            continue
        
        # JSON 파싱
        qa = extract_json_from_response(response)
        
        if qa and 'question' in qa and 'answer' in qa:
            qa['id'] = f"qa_llm_{i:03d}"
            qa['category'] = sample['type']
            qa['metadata'] = {
                'llm_generated': True,
                'model': model,
                'validated': False,
                'sample_index': i
            }
            
            # gold_entities가 없으면 빈 리스트
            if 'gold_entities' not in qa:
                qa['gold_entities'] = []
            
            qa_pairs.append(qa)
            success_count += 1
        else:
            print(f"   ⚠️  QA {i+1} 생성 실패: JSON 파싱 오류")
            print(f"      응답: {response[:100]}...")
    
    print(f"\n📊 생성 결과:")
    print(f"   성공: {success_count}개")
    print(f"   실패: {len(all_samples) - success_count}개")
    print(f"   성공률: {success_count/len(all_samples)*100:.1f}%")
    
    # 저장
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(str(output_path), qa_pairs)
    
    print(f"\n✅ QA 저장 완료: {output_file}")
    print(f"   총 QA 쌍: {len(qa_pairs)}개")
    
    # 카테고리별 분포
    from collections import Counter
    categories = Counter([qa['category'] for qa in qa_pairs])
    print(f"\n📊 카테고리 분포:")
    for cat, count in categories.items():
        print(f"   {cat}: {count}개")
    
    return qa_pairs


def main():
    ap = argparse.ArgumentParser(description='Ollama LLM 기반 Gold Standard QA 생성')
    ap.add_argument("--samples", default="data/processed/representative_samples.json", 
                    help="대표 샘플 JSON 파일")
    ap.add_argument("--output", default="eval/gold_standard_v2.jsonl",
                    help="출력 JSONL 파일")
    ap.add_argument("--model", default="qwen2.5:3b",
                    help="Ollama 모델 이름")
    a = ap.parse_args()
    
    # Ollama 설치 확인
    try:
        subprocess.run(['ollama', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Ollama가 설치되지 않았습니다.")
        print("   설치 방법: https://ollama.ai")
        return 1
    
    # 모델 확인
    print(f"🔍 Ollama 모델 확인 중: {a.model}")
    try:
        subprocess.run(['ollama', 'list'], capture_output=True, check=True)
        print(f"✅ Ollama 준비 완료")
    except subprocess.CalledProcessError:
        print(f"⚠️  모델 {a.model}를 다운로드해야 할 수 있습니다.")
        print(f"   실행: ollama pull {a.model}")
    
    # QA 생성
    qa_pairs = generate_qa_pairs(a.samples, a.output, a.model)
    
    # 검증
    if len(qa_pairs) >= 90:
        print(f"\n✅ 목표 달성: {len(qa_pairs)}개 >= 90개 (90% 성공률)")
        return 0
    else:
        print(f"\n⚠️  목표 미달: {len(qa_pairs)}개 < 90개")
        return 1


if __name__ == "__main__":
    sys.exit(main())

