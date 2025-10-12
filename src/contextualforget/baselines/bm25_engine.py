"""
BM25-based keyword search engine for baseline comparison.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from whoosh import index
from whoosh.analysis import StandardAnalyzer
from whoosh.fields import DATETIME, ID, KEYWORD, TEXT, Schema
from whoosh.qparser import MultifieldParser
from whoosh.query import Term, And

from .base import BaselineQueryEngine


class BM25QueryEngine(BaselineQueryEngine):
    """BM25-based keyword search engine."""
    
    def __init__(self, index_dir: str = "data/processed/bm25_index"):
        super().__init__("BM25")
        self.index_dir = Path(index_dir)
        self.schema = None
        self.ix = None
        self.analyzer = StandardAnalyzer()
        
    def initialize(self, graph_data: dict[str, Any]) -> None:
        """Initialize BM25 index with graph data."""
        print("🔧 BM25 엔진 초기화 중...")
        
        # Create index directory
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Define schema
        self.schema = Schema(
            doc_id=ID(stored=True, unique=True),
            doc_type=ID(stored=True),
            title=TEXT(stored=True, analyzer=self.analyzer),
            content=TEXT(stored=True, analyzer=self.analyzer),
            author=TEXT(stored=True),
            created=DATETIME(stored=True),
            guid=TEXT(stored=True),
            entity_type=TEXT(stored=True),
            keywords=KEYWORD(stored=True, commas=True)
        )
        
        # Create or open index
        if index.exists_in(str(self.index_dir)):
            self.ix = index.open_dir(str(self.index_dir))
            print(f"  ✅ 기존 인덱스 로드: {self.index_dir}")
        else:
            self.ix = index.create_in(str(self.index_dir), self.schema)
            self._build_index(graph_data)
            print(f"  ✅ 새 인덱스 생성: {self.index_dir}")
        
        self.initialized = True
        print("  ✅ BM25 엔진 초기화 완료")
    
    def _build_index(self, graph_data: dict[str, Any]) -> None:
        """Build BM25 index from graph data."""
        print("  📚 인덱스 구축 중...")
        
        writer = self.ix.writer()
        
        # Index BCF data
        bcf_count = 0
        for node, data in graph_data.get('nodes', []):
            if isinstance(node, tuple) and len(node) == 2:
                node_type, node_id = node
                if node_type == "BCF":
                    # Extract BCF data
                    title = data.get('title', '')
                    description = data.get('description', '')
                    author = data.get('author', '')
                    created = data.get('created', '')
                    
                    # Combine title and description
                    content = f"{title} {description}".strip()
                    
                    # Extract keywords
                    keywords = self._extract_keywords(content)
                    
                    # Parse creation date
                    created_date = None
                    if created:
                        try:
                            created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        except Exception:
                            pass
                    
                    try:
                        writer.add_document(
                            doc_id=f"bcf_{node_id}",
                            doc_type="BCF",
                            title=title,
                            content=content,
                            author=author,
                            created=created_date,
                            guid="",
                            entity_type="",
                            keywords=",".join(keywords)
                        )
                        bcf_count += 1
                    except Exception as e:
                        print(f"    ⚠️ BCF 문서 인덱싱 오류: {e}")
        
        # Index IFC data
        ifc_count = 0
        for node, data in graph_data.get('nodes', []):
            if isinstance(node, tuple) and len(node) == 2:
                node_type, node_id = node
                if node_type == "IFC":
                    # Extract IFC data
                    name = data.get('name', node_id)
                    entity_type = data.get('type', 'Unknown')
                    
                    # Create content from name and type
                    content = f"{name} {entity_type}".strip()
                    
                    # Extract keywords
                    keywords = self._extract_keywords(content)
                    
                    try:
                        writer.add_document(
                            doc_id=f"ifc_{node_id}",
                            doc_type="IFC",
                            title=name,
                            content=content,
                            author="",
                            created=None,
                            guid=node_id,
                            entity_type=entity_type,
                            keywords=",".join(keywords)
                        )
                        ifc_count += 1
                    except Exception as e:
                        print(f"    ⚠️ IFC 문서 인덱싱 오류: {e}")
        
        writer.commit()
        print(f"    📋 BCF 문서: {bcf_count}개")
        print(f"    📐 IFC 문서: {ifc_count}개")
        print(f"    ✅ 총 {bcf_count + ifc_count}개 문서 인덱싱 완료")
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text."""
        if not text:
            return []
        
        # Simple keyword extraction
        # Remove special characters and split
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:10]  # Limit to 10 keywords
    
    def process_query(self, question: str, **kwargs) -> dict[str, Any]:
        """Process a natural language query using BM25."""
        if not self.initialized:
            raise RuntimeError("BM25 engine not initialized")
        
        # Extract keywords from question
        keywords = self._extract_keywords(question)
        
        # Handle different query types
        if self._is_guid_query(question):
            return self._handle_guid_query(question)
        elif self._is_temporal_query(question):
            return self._handle_temporal_query(question, keywords)
        elif self._is_author_query(question):
            return self._handle_author_query(question, keywords)
        else:
            return self._handle_general_query(question, keywords)
    
    def _is_guid_query(self, question: str) -> bool:
        """Check if query is asking for GUID information."""
        guid_pattern = r'\b[A-Za-z0-9]{22}\b'
        return bool(re.search(guid_pattern, question))
    
    def _is_temporal_query(self, question: str) -> bool:
        """Check if query is temporal (date/time related)."""
        temporal_keywords = ['최근', '이전', '생성', '날짜', '일', '주', '월', '년', 'recent', 'ago', 'created', 'date']
        return any(keyword in question.lower() for keyword in temporal_keywords)
    
    def _is_author_query(self, question: str) -> bool:
        """Check if query is asking about author."""
        author_keywords = ['작성', 'author', 'engineer', 'architect']
        return any(keyword in question.lower() for keyword in author_keywords)
    
    def _handle_guid_query(self, question: str) -> dict[str, Any]:
        """Handle GUID-specific queries."""
        # Extract GUID from question
        guid_pattern = r'\b([A-Za-z0-9]{22})\b'
        match = re.search(guid_pattern, question)
        
        if not match:
            return {"error": "GUID not found in question"}
        
        guid = match.group(1)
        
        # Search for IFC element with this GUID
        with self.ix.searcher() as searcher:
            query = Term("guid", guid)
            results = searcher.search(query, limit=1)
            
            if results:
                hit = results[0]
                return {
                    "answer": f"GUID {guid}는 {hit['entity_type']} 타입의 IFC 요소입니다.",
                    "confidence": 1.0,
                    "source": "BM25",
                    "details": {
                        "guid": guid,
                        "entity_type": hit['entity_type'],
                        "name": hit['title']
                    }
                }
            else:
                return {
                    "answer": f"GUID {guid}에 대한 정보를 찾을 수 없습니다.",
                    "confidence": 0.0,
                    "source": "BM25"
                }
    
    def _handle_temporal_query(self, question: str, keywords: list[str]) -> dict[str, Any]:
        """Handle temporal queries."""
        # Extract time period from question
        time_period = self._extract_time_period(question)
        
        with self.ix.searcher() as searcher:
            # Search for BCF documents
            query = And([
                Term("doc_type", "BCF"),
                MultifieldParser(["title", "content"], self.schema).parse(" ".join(keywords))
            ])
            
            results = searcher.search(query, limit=10)
            
            # Filter by time if specified
            if time_period:
                filtered_results = []
                cutoff_date = datetime.now() - time_period
                
                for hit in results:
                    if hit.get('created') and hit['created'] >= cutoff_date:
                        filtered_results.append(hit)
                
                results = filtered_results
            
            if results:
                issues = [hit['title'] for hit in results[:5]]
                answer = f"관련 이슈: {', '.join(issues)}"
                return {
                    "answer": answer,
                    "confidence": 0.7,
                    "source": "BM25",
                    "details": {
                        "issues": issues,
                        "count": len(results)
                    }
                }
            else:
                return {
                    "answer": "해당 기간의 이슈를 찾을 수 없습니다.",
                    "confidence": 0.0,
                    "source": "BM25"
                }
    
    def _handle_author_query(self, question: str, keywords: list[str]) -> dict[str, Any]:
        """Handle author-specific queries."""
        # Extract author name from question
        author = None
        
        # Look for author patterns in the original question
        author_patterns = [
            r'engineer_([a-z]+)',
            r'architect_([a-z]+)',
            r'([a-z]+)_a',
            r'([a-z]+)_b'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, question.lower())
            if match:
                author = match.group(0)
                break
        
        if not author:
            return {
                "answer": "작성자 정보를 찾을 수 없습니다.",
                "confidence": 0.0,
                "source": "BM25"
            }
        
        with self.ix.searcher() as searcher:
            query = And([
                Term("doc_type", "BCF"),
                Term("author", author)
            ])
            
            results = searcher.search(query, limit=10)
            
            if results:
                issues = [hit['title'] for hit in results]
                answer = f"{author}가 작성한 이슈: {', '.join(issues[:3])}"
                return {
                    "answer": answer,
                    "confidence": 0.8,
                    "source": "BM25",
                    "details": {
                        "author": author,
                        "issues": issues,
                        "count": len(results)
                    }
                }
            else:
                return {
                    "answer": f"{author}가 작성한 이슈를 찾을 수 없습니다.",
                    "confidence": 0.0,
                    "source": "BM25"
                }
    
    def _handle_general_query(self, question: str, keywords: list[str]) -> dict[str, Any]:
        """Handle general queries."""
        if not keywords:
            return {
                "answer": "검색할 키워드를 찾을 수 없습니다.",
                "confidence": 0.0,
                "source": "BM25"
            }
        
        with self.ix.searcher() as searcher:
            # Search across title and content
            query = MultifieldParser(["title", "content"], self.schema).parse(" ".join(keywords))
            results = searcher.search(query, limit=5)
            
            if results:
                # Group results by type
                bcf_results = [hit for hit in results if hit['doc_type'] == 'BCF']
                ifc_results = [hit for hit in results if hit['doc_type'] == 'IFC']
                
                answer_parts = []
                
                if bcf_results:
                    bcf_titles = [hit['title'] for hit in bcf_results[:3]]
                    answer_parts.append(f"관련 이슈: {', '.join(bcf_titles)}")
                
                if ifc_results:
                    ifc_names = [hit['title'] for hit in ifc_results[:3]]
                    answer_parts.append(f"관련 요소: {', '.join(ifc_names)}")
                
                answer = " | ".join(answer_parts) if answer_parts else "관련 정보를 찾을 수 없습니다."
                
                return {
                    "answer": answer,
                    "confidence": 0.6,
                    "source": "BM25",
                    "details": {
                        "bcf_count": len(bcf_results),
                        "ifc_count": len(ifc_results),
                        "total_results": len(results)
                    }
                }
            else:
                return {
                    "answer": "관련 정보를 찾을 수 없습니다.",
                    "confidence": 0.0,
                    "source": "BM25"
                }
    
    def _extract_time_period(self, question: str) -> datetime | None:
        """Extract time period from question."""
        # Simple time period extraction
        if '1일' in question or '1 day' in question:
            return datetime.now() - timedelta(days=1)
        elif '7일' in question or '1주' in question or '7 days' in question:
            return datetime.now() - timedelta(days=7)
        elif '30일' in question or '1개월' in question or '30 days' in question:
            return datetime.now() - timedelta(days=30)
        elif '60일' in question or '2개월' in question or '60 days' in question:
            return datetime.now() - timedelta(days=60)
        elif '90일' in question or '3개월' in question or '90 days' in question:
            return datetime.now() - timedelta(days=90)
        
        return None
