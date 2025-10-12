"""LLM 기반 자연어 처리 모듈 - Ollama 통합."""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ChatOllama = None
    HumanMessage = None
    SystemMessage = None

logger = logging.getLogger(__name__)


@dataclass
class QueryIntent:
    """질의 의도 분석 결과."""
    intent_type: str  # "search", "query", "timeline", "author", "connected", "stats"
    entities: List[str]  # 추출된 엔티티들 (GUID, 키워드, 작성자 등)
    parameters: Dict[str, Any]  # 추가 파라미터들
    confidence: float  # 의도 분석 신뢰도
    reasoning: str  # LLM의 추론 과정


class LLMNaturalLanguageProcessor:
    """LLM 기반 자연어 질의 처리기."""
    
    def __init__(self, model_name: str = "qwen2.5:3b", fallback_to_regex: bool = False):
        self.model_name = model_name
        self.fallback_to_regex = fallback_to_regex
        self.llm = None
        
        if OLLAMA_AVAILABLE:
            try:
                self.llm = ChatOllama(
                    model=model_name,
                    temperature=0.1,      # 낮은 temperature로 일관성 확보
                    num_ctx=1024,         # 짧은 컨텍스트로 빠른 응답
                    timeout=10.0,         # 타임아웃 10초
                    num_predict=150,      # 최대 토큰 제한
                    stop=["\n\n", "```", "---", "</s>"]  # 반복 중단 토큰들
                )
                logger.info(f"LLM 모델 '{model_name}' 초기화 완료")
            except Exception as e:
                logger.warning(f"LLM 모델 초기화 실패: {e}")
                self.llm = None
        else:
            logger.warning("langchain-ollama가 설치되지 않음.")
        
        # 폴백용 정규식 패턴들
        self.fallback_patterns = {
            "guid": r"[0-9A-Fa-f]{22}|[0-9A-Fa-f-]{36}|[0-9A-Za-z]{22}",
            "author": r"engineer_[a-z]|엔지니어_[가-힣]",
            "date": r"\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2}",
        }
    
    def parse_query(self, query: str) -> QueryIntent:
        """자연어 질의를 LLM으로 분석하여 의도와 엔티티를 추출."""
        if self.llm:
            return self._parse_with_llm(query)
        elif self.fallback_to_regex:
            logger.warning("LLM을 사용할 수 없어 정규식 기반 처리로 폴백")
            return self._parse_with_regex(query)
        else:
            raise RuntimeError("LLM을 사용할 수 없고 폴백도 비활성화됨")
    
    def _parse_with_llm(self, query: str) -> QueryIntent:
        """LLM을 사용하여 질의를 분석."""
        system_prompt = """You are a BIM query analyzer. Parse the user query and return ONLY a JSON object with no additional text.

Required format:
{"intent_type": "stats|search|connected|timeline", "entities": [], "parameters": {}, "confidence": 0.8, "reasoning": "brief"}

Intent types:
- stats: statistics/overview
- search: find by GUID/author/keyword
- connected: find connected components
- timeline: time-based queries

Examples:
- "통계" → {"intent_type": "stats", "entities": [], "parameters": {}, "confidence": 0.9, "reasoning": "statistics request"}
- "1kTv... GUID 찾기" → {"intent_type": "search", "entities": ["1kTv..."], "parameters": {"guid": "1kTv..."}, "confidence": 0.9, "reasoning": "GUID search"}"""

        human_prompt = f"Query: {query}\nJSON:"
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # JSON 파싱 시도
            try:
                # JSON 블록이 있는 경우 추출
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text
                
                result = json.loads(json_text)
                
                return QueryIntent(
                    intent_type=result.get("intent_type", "search"),
                    entities=result.get("entities", []),
                    parameters=result.get("parameters", {}),
                    confidence=result.get("confidence", 0.8),
                    reasoning=result.get("reasoning", "LLM 분석 완료")
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}, 응답: {response_text}")
                # JSON 파싱 실패 시 폴백
                return self._parse_with_regex(query)
                
        except Exception as e:
            logger.error(f"LLM 처리 중 오류: {e}")
            if self.fallback_to_regex:
                return self._parse_with_regex(query)
            else:
                raise
    
    def _parse_with_regex(self, query: str) -> QueryIntent:
        """정규식 기반 폴백 처리."""
        import re
        
        query_lower = query.lower()
        
        # 의도 분석 (간단한 키워드 기반)
        if any(word in query_lower for word in ["통계", "stats", "개수", "총"]):
            intent_type = "stats"
        elif any(word in query_lower for word in ["작성자", "author", "engineer"]):
            intent_type = "author"
        elif any(word in query_lower for word in ["연결", "connected", "관련"]):
            intent_type = "connected"
        elif any(word in query_lower for word in ["시간", "날짜", "기간", "timeline"]):
            intent_type = "timeline"
        elif any(word in query_lower for word in ["guid", "식별자"]):
            intent_type = "query"
        else:
            intent_type = "search"
        
        # 엔티티 추출
        entities = []
        
        # GUID 추출
        guid_matches = re.findall(self.fallback_patterns["guid"], query)
        entities.extend(guid_matches)
        
        # 작성자 추출
        author_matches = re.findall(self.fallback_patterns["author"], query)
        entities.extend(author_matches)
        
        # 키워드 추출 (따옴표 안의 텍스트)
        keyword_matches = re.findall(r'"([^"]+)"', query)
        entities.extend(keyword_matches)
        
        # 파라미터 추출
        parameters = {}
        
        # 날짜 범위 추출
        date_matches = re.findall(self.fallback_patterns["date"], query)
        if len(date_matches) >= 2:
            parameters["start_date"] = date_matches[0]
            parameters["end_date"] = date_matches[1]
        elif len(date_matches) == 1:
            parameters["date"] = date_matches[0]
        
        # 개수 제한 추출
        limit_matches = re.findall(r"(\d+)\s*개|(\d+)\s*개씩|top\s*(\d+)", query)
        if limit_matches:
            for match in limit_matches:
                for num in match:
                    if num:
                        parameters["limit"] = int(num)
                        break
        
        return QueryIntent(
            intent_type=intent_type,
            entities=entities,
            parameters=parameters,
            confidence=0.6,  # 정규식 기반이므로 낮은 신뢰도
            reasoning="정규식 기반 폴백 처리"
        )
    
    def generate_natural_response(self, intent: QueryIntent, result: Dict[str, Any], original_query: str) -> str:
        """LLM을 사용하여 자연어 응답을 생성."""
        if not self.llm:
            return self._generate_simple_response(intent, result, original_query)
        
        system_prompt = """BIM 데이터베이스 AI 어시스턴트입니다. 사용자의 질문에 정확하고 구체적으로 응답하세요.

중요한 규칙:
1. GUID 질문에는 반드시 구체적인 IFC 요소 타입을 답변하세요
2. JSON 형식이 아닌 자연스러운 한국어로 답변하세요
3. 찾은 정보가 있으면 구체적으로 명시하세요

예시:
- "GUID lqcHgIvJujQ7EViQXtHQ7P는 FURNISHINGELEMENT입니다."
- "1개의 BCF 토픽을 찾았습니다: 발코니 난간 이슈"
- "해당 GUID와 관련된 결과를 찾을 수 없습니다."
- "현재 그래프에는 총 428개의 노드가 있습니다."""

        # 결과 요약 생성
        result_summary = self._summarize_result(result)
        
        human_prompt = f"""
원래 질의: {original_query}
분석된 의도: {intent.intent_type}
추출된 엔티티: {intent.entities}
추론 과정: {intent.reasoning}

쿼리 결과:
{result_summary}

위 정보를 바탕으로 사용자에게 자연스러운 한국어로 응답해주세요."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"자연어 응답 생성 중 오류: {e}")
            return self._generate_simple_response(intent, result, original_query)
    
    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """결과를 요약하여 LLM이 이해하기 쉽게 변환."""
        if "error" in result:
            return f"오류: {result['error']}"
        
        result_type = result.get("type", "unknown")
        total_found = result.get("total_found", 0)
        
        summary = f"결과 유형: {result_type}\n총 {total_found}개 결과 발견\n\n"
        
        if result_type == "search":
            keywords = result.get("keywords", [])
            summary += f"검색 키워드: {', '.join(keywords)}\n"
        elif result_type == "ifc_info":
            guids = result.get("guids", [])
            summary += f"조회한 GUID: {', '.join(guids)}\n"
        elif result_type == "query":
            guids = result.get("guids", [])
            summary += f"조회한 GUID: {', '.join(guids)}\n"
        elif result_type == "author":
            authors = result.get("authors", [])
            summary += f"조회한 작성자: {', '.join(authors)}\n"
        elif result_type == "stats":
            stats = result.get("statistics", {})
            summary += f"통계 정보: {json.dumps(stats, ensure_ascii=False, indent=2)}\n"
        
        # 결과 샘플 추가
        results = result.get("results", [])
        if results:
            summary += "\n주요 결과:\n"
            for i, item in enumerate(results[:3], 1):
                if isinstance(item, dict):
                    if result_type == "ifc_info":
                        # IFC 정보 결과 처리
                        guid = item.get("guid", "Unknown")
                        element_type = item.get("type", "Unknown")
                        name = item.get("name", guid)
                        summary += f"{i}. GUID {guid}: {element_type} (이름: {name})\n"
                    else:
                        # BCF 토픽 결과 처리
                        title = item.get("title", item.get("topic_id", "제목 없음"))
                        author = item.get("author", "작성자 불명")
                        created = item.get("created", "날짜 불명")
                        summary += f"{i}. {title} (작성자: {author}, 생성일: {created})\n"
        
        return summary
    
    def _generate_simple_response(self, intent: QueryIntent, result: Dict[str, Any], original_query: str) -> str:
        """간단한 템플릿 기반 응답 생성 (폴백용)."""
        if "error" in result:
            return f"죄송합니다. {result['error']}"
        
        result_type = result.get("type", "unknown")
        total_found = result.get("total_found", 0)
        
        if result_type == "search":
            keywords = ", ".join(result.get("keywords", []))
            if total_found == 0:
                return f"'{keywords}' 키워드로 검색한 결과를 찾을 수 없습니다."
            return f"'{keywords}' 키워드로 {total_found}개의 결과를 찾았습니다."
        
        elif result_type == "query":
            guids = ", ".join(result.get("guids", []))
            if total_found == 0:
                return f"GUID {guids}와 관련된 결과를 찾을 수 없습니다."
            return f"GUID {guids}와 관련된 {total_found}개의 BCF 토픽을 찾았습니다."
        
        elif result_type == "author":
            authors = ", ".join(result.get("authors", []))
            if total_found == 0:
                return f"{authors} 작성자의 결과를 찾을 수 없습니다."
            return f"{authors} 작성자가 작성한 {total_found}개의 토픽을 찾았습니다."
        
        elif result_type == "stats":
            stats = result.get("statistics", {})
            total_nodes = stats.get("total_nodes", 0)
            ifc_entities = stats.get("ifc_entities", 0)
            bcf_topics = stats.get("bcf_topics", 0)
            total_edges = stats.get("total_edges", 0)
            
            return f"현재 그래프 통계:\n• 총 노드: {total_nodes}개\n• IFC 엔티티: {ifc_entities}개\n• BCF 토픽: {bcf_topics}개\n• 총 엣지: {total_edges}개"
        
        else:
            return f"{total_found}개의 결과를 찾았습니다."
    
    def is_available(self) -> bool:
        """LLM이 사용 가능한지 확인."""
        return self.llm is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환."""
        return {
            "model_name": self.model_name,
            "available": self.is_available(),
            "fallback_enabled": self.fallback_to_regex,
            "ollama_installed": OLLAMA_AVAILABLE
        }
