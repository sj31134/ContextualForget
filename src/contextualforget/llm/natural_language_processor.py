"""자연어 질의 처리 및 LLM 통합 모듈."""

import logging
import re
from datetime import datetime
from typing import Any

from .llm_processor import LLMNaturalLanguageProcessor, QueryIntent

logger = logging.getLogger(__name__)


class NaturalLanguageProcessor:
    """자연어 질의 처리기 - LLM 기반."""
    
    def __init__(self, model_name: str = "qwen2.5:3b", use_llm: bool = True):
        """자연어 처리기 초기화.
        
        Args:
            model_name: 사용할 Ollama 모델 이름
            use_llm: LLM 사용 여부 (True면 LLM 기반, False면 정규식 폴백)
        """
        if use_llm:
            # LLM 기반 처리 (정규식 폴백 비활성화)
            self.processor = LLMNaturalLanguageProcessor(model_name=model_name, fallback_to_regex=False)
        else:
            # 정규식 기반 폴백
            self.processor = LLMNaturalLanguageProcessor(model_name=model_name, fallback_to_regex=True)
            self.processor.llm = None  # LLM 비활성화
        
        logger.info(f"NaturalLanguageProcessor 초기화 완료 (LLM 사용: {use_llm}, 모델: {model_name})")
    
    def parse_query(self, query: str) -> QueryIntent:
        """자연어 질의를 분석하여 의도와 엔티티를 추출."""
        return self.processor.parse_query(query)
    
    def is_available(self) -> bool:
        """LLM이 사용 가능한지 확인."""
        return self.processor.is_available()
    
    def get_model_info(self) -> dict[str, Any]:
        """모델 정보 반환."""
        return self.processor.get_model_info()


class LLMQueryEngine:
    """LLM 기반 자연어 질의 엔진."""
    
    def __init__(self, query_engine, nlp_processor: NaturalLanguageProcessor):
        self.query_engine = query_engine
        self.nlp = nlp_processor
        self.conversation_history = []
    
    def process_natural_query(self, query: str) -> dict[str, Any]:
        """자연어 질의를 처리하여 결과를 반환."""
        logger.info(f"Processing natural language query: {query}")
        
        # 의도 분석
        intent = self.nlp.parse_query(query)
        
        # 대화 기록에 추가
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "intent": intent
        })
        
        # 의도에 따른 처리
        result = self._execute_intent(intent, query)
        
        # 자연어 응답 생성 (LLM 기반)
        natural_response = self.nlp.processor.generate_natural_response(intent, result, query)
        
        return {
            "query": query,
            "intent": {
                "type": intent.intent_type,
                "confidence": intent.confidence,
                "entities": intent.entities,
                "parameters": intent.parameters
            },
            "result": result,
            "natural_response": natural_response,
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_intent(self, intent: QueryIntent, original_query: str) -> dict[str, Any]:
        """의도에 따라 적절한 쿼리를 실행."""
        try:
            if intent.intent_type == "search":
                return self._handle_search_intent(intent)
            elif intent.intent_type == "query":
                return self._handle_query_intent(intent)
            elif intent.intent_type == "timeline":
                return self._handle_timeline_intent(intent)
            elif intent.intent_type == "author":
                return self._handle_author_intent(intent)
            elif intent.intent_type == "connected":
                return self._handle_connected_intent(intent)
            elif intent.intent_type == "stats":
                return self._handle_stats_intent(intent)
            else:
                return {"error": f"Unknown intent type: {intent.intent_type}"}
        except Exception as e:
            logger.error(f"Error executing intent {intent.intent_type}: {e}")
            return {"error": str(e)}
    
    def _handle_search_intent(self, intent: QueryIntent) -> dict[str, Any]:
        """검색 의도 처리."""
        keywords = [entity for entity in intent.entities if not self._is_guid(entity)]
        guids = [entity for entity in intent.entities if self._is_guid(entity)]
        _limit = intent.parameters.get("limit", 5)
        
        # GUID 질문 처리
        if guids and not keywords:
            results = []
            for guid in guids:
                try:
                    ifc_info = self.query_engine.get_ifc_element_info(guid)
                    if "error" not in ifc_info:
                        results.append(ifc_info)
                except Exception as e:
                    logger.error(f"Error getting IFC info for {guid}: {e}")
            
            return {
                "type": "ifc_info",
                "guids": guids,
                "results": results,
                "total_found": len(results)
            }
        
        # 키워드 검색 처리
        if not keywords:
            return {"error": "검색할 키워드를 찾을 수 없습니다."}
        
        results = []
        for keyword in keywords:
            try:
                search_results = self.query_engine.find_by_keywords([keyword])
                results.extend(search_results)
            except Exception as e:
                logger.error(f"Error searching for keyword {keyword}: {e}")
        
        return {
            "type": "search",
            "keywords": keywords,
            "results": results,
            "total_found": len(results)
        }
    
    def _handle_query_intent(self, intent: QueryIntent) -> dict[str, Any]:
        """GUID 쿼리 의도 처리."""
        guids = [entity for entity in intent.entities if self._is_guid(entity)]
        ttl = intent.parameters.get("time_period", 365)
        limit = intent.parameters.get("limit", 5)
        
        if not guids:
            return {"error": "쿼리할 GUID를 찾을 수 없습니다."}
        
        results = []
        for guid in guids:
            try:
                query_results = self.query_engine.find_by_guid(guid, ttl=ttl, limit=limit)
                results.extend(query_results)
            except Exception as e:
                logger.error(f"Error querying GUID {guid}: {e}")
        
        return {
            "type": "query",
            "guids": guids,
            "results": results,
            "total_found": len(results)
        }
    
    def _handle_timeline_intent(self, intent: QueryIntent) -> dict[str, Any]:
        """시간 범위 의도 처리."""
        start_date = intent.parameters.get("start_date")
        end_date = intent.parameters.get("end_date")
        
        if not start_date or not end_date:
            return {"error": "시작 날짜와 종료 날짜를 모두 제공해주세요."}
        
        try:
            results = self.query_engine.find_by_timeline(start_date, end_date)
            return {
                "type": "timeline",
                "start_date": start_date,
                "end_date": end_date,
                "results": results,
                "total_found": len(results)
            }
        except Exception as e:
            logger.error(f"Error querying timeline: {e}")
            return {"error": str(e)}
    
    def _handle_author_intent(self, intent: QueryIntent) -> dict[str, Any]:
        """작성자 의도 처리."""
        authors = [entity for entity in intent.entities if "engineer" in entity.lower()]
        limit = intent.parameters.get("limit", 5)
        
        if not authors:
            return {"error": "작성자를 찾을 수 없습니다."}
        
        results = []
        for author in authors:
            try:
                author_results = self.query_engine.find_by_author(author, limit=limit)
                results.extend(author_results)
            except Exception as e:
                logger.error(f"Error querying author {author}: {e}")
        
        return {
            "type": "author",
            "authors": authors,
            "results": results,
            "total_found": len(results)
        }
    
    def _handle_connected_intent(self, intent: QueryIntent) -> dict[str, Any]:
        """연결된 컴포넌트 의도 처리."""
        guids = [entity for entity in intent.entities if self._is_guid(entity)]
        max_depth = intent.parameters.get("max_depth", 2)
        
        if not guids:
            return {"error": "연결된 컴포넌트를 찾을 GUID를 제공해주세요."}
        
        results = []
        for guid in guids:
            try:
                connected_results = self.query_engine.find_connected_components(guid, max_depth=max_depth)
                results.append({
                    "guid": guid,
                    "connected": connected_results
                })
            except Exception as e:
                logger.error(f"Error finding connected components for {guid}: {e}")
        
        return {
            "type": "connected",
            "guids": guids,
            "results": results
        }
    
    def _handle_stats_intent(self, intent: QueryIntent) -> dict[str, Any]:
        """통계 의도 처리."""
        try:
            stats = self.query_engine.get_statistics()
            return {
                "type": "stats",
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}
    
    def _is_guid(self, entity: str) -> bool:
        """엔티티가 GUID인지 확인."""
        guid_pattern = r"[0-9A-Fa-f]{22}|[0-9A-Fa-f-]{36}|[0-9A-Za-z]{22}"
        return bool(re.match(guid_pattern, entity))
    
    def get_conversation_history(self) -> list[dict[str, Any]]:
        """대화 기록을 반환."""
        return self.conversation_history
    
    def clear_history(self):
        """대화 기록을 초기화."""
        self.conversation_history = []
