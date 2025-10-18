"""
Optimized BM25 Query Engine with batch processing and memory optimization
"""

import os
import re
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, DATETIME, KEYWORD
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import Term, And, Or
from whoosh.analysis import StandardAnalyzer

from .base import BaselineQueryEngine


class BM25QueryEngine(BaselineQueryEngine):
    """Optimized BM25-based query engine with batch processing."""
    
    def __init__(self, name: str = "BM25"):
        super().__init__(name)
        self.ix = None
        self.analyzer = StandardAnalyzer()
        self.schema = Schema(
            doc_id=ID(stored=True, unique=True),
            doc_type=ID(stored=True),
            title=TEXT(stored=True, analyzer=self.analyzer),
            content=TEXT(stored=True, analyzer=self.analyzer),
            author=TEXT(stored=True),
            created=DATETIME(stored=True),
            guid=ID(stored=True),
            entity_type=TEXT(stored=True),
            keywords=KEYWORD(stored=True, commas=True)
        )
    
    def initialize(self, graph_data: dict[str, Any]) -> None:
        """Initialize BM25 engine with optimized indexing."""
        print(f"🔧 {self.name} 엔진 초기화 중...")
        
        # Create cache directory
        cache_dir = Path("cache/bm25_index")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if index exists
        if index.exists_in(str(cache_dir)):
            print("  ✅ 기존 인덱스 로드: BM25")
            self.ix = index.open_dir(str(cache_dir))
        else:
            print("  🔨 새 인덱스 생성: BM25")
            self.ix = index.create_in(str(cache_dir), self.schema)
            self._build_index_optimized(graph_data)
        
        self.initialized = True
        print(f"  ✅ {self.name} 엔진 초기화 완료")
    
    def _build_index_optimized(self, graph_data: dict[str, Any]) -> None:
        """Build BM25 index with optimized batch processing."""
        print("  📚 인덱스 구축 중...")
        
        writer = self.ix.writer()
        
        # Handle different data structures
        if 'graph' in graph_data:
            # NetworkX graph object
            graph = graph_data['graph']
            nodes_to_process = list(graph.nodes(data=True))
        elif 'nodes' in graph_data:
            # List of (node, data) tuples
            nodes_to_process = graph_data['nodes']
        else:
            # Direct BCF data list
            nodes_to_process = []
            for item in graph_data.get('bcf_data', []):
                nodes_to_process.append((('BCF', item.get('guid', '')), item))
        
        # Separate BCF and IFC nodes for efficient processing
        bcf_nodes = []
        ifc_nodes = []
        
        for node, data in nodes_to_process:
            if isinstance(node, tuple) and len(node) == 2:
                node_type, node_id = node
                if node_type == "BCF":
                    bcf_nodes.append((node, data))
                elif node_type == "IFC":
                    ifc_nodes.append((node, data))
        
        print(f"    📊 BCF 노드: {len(bcf_nodes)}개, IFC 노드: {len(ifc_nodes)}개")
        
        # Process BCF data first (smaller dataset)
        bcf_count = self._process_bcf_batch(writer, bcf_nodes)
        
        # Process IFC data in batches (larger dataset)
        ifc_count = self._process_ifc_batch(writer, ifc_nodes)
        
        writer.commit()
        print(f"    📋 BCF 문서: {bcf_count}개")
        print(f"    📐 IFC 문서: {ifc_count}개")
        print(f"    ✅ 총 {bcf_count + ifc_count}개 문서 인덱싱 완료")
    
    def _process_bcf_batch(self, writer, bcf_nodes):
        """Process BCF nodes in batch."""
        bcf_count = 0
        for node, data in bcf_nodes:
            try:
                # Extract BCF data
                title = data.get('title', '')
                description = data.get('description', '')
                author = data.get('author', '')
                created = data.get('created', '')
                node_id = node[1]  # Extract node_id from tuple
                
                # Combine title and description
                content = f"{title} {description}".strip()
                
                # Extract keywords (simplified for performance)
                keywords = self._extract_keywords_simple(content)
                
                # Parse creation date
                created_date = None
                if created:
                    try:
                        created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    except Exception:
                        pass
                
                writer.add_document(
                    doc_id=f"bcf_{node_id}",
                    doc_type="BCF",
                    title=title,
                    content=content,
                    author=author,
                    created=created_date,
                    guid=node_id,  # BCF의 topic_id를 guid로 사용
                    entity_type="BCF_ISSUE",
                    keywords=",".join(keywords)
                )
                bcf_count += 1
            except Exception as e:
                print(f"    ⚠️ BCF 문서 인덱싱 오류: {e}")
        
        return bcf_count
    
    def _process_ifc_batch(self, writer, ifc_nodes):
        """Process IFC nodes in optimized batches."""
        ifc_count = 0
        batch_size = 1000  # Process in batches of 1000
        
        for i in range(0, len(ifc_nodes), batch_size):
            batch = ifc_nodes[i:i + batch_size]
            
            for node, data in batch:
                try:
                    # Extract IFC data
                    title = data.get('name', data.get('title', ''))
                    entity_type = data.get('entity_type', '')
                    node_id = node[1]  # Extract node_id from tuple
                    guid = data.get('guid', node_id)
                    
                    # Create content from available fields
                    content = f"{title} {entity_type}".strip()
                    
                    # Extract keywords (simplified for performance)
                    keywords = self._extract_keywords_simple(content)
                    
                    writer.add_document(
                        doc_id=f"ifc_{node_id}",
                        doc_type="IFC",
                        title=title,
                        content=content,
                        author="",
                        created=None,
                        guid=guid,
                        entity_type=entity_type,
                        keywords=",".join(keywords)
                    )
                    ifc_count += 1
                except Exception as e:
                    print(f"    ⚠️ IFC 문서 인덱싱 오류: {e}")
            
            # Progress update for large datasets
            if len(ifc_nodes) > 5000:
                progress = (i + batch_size) / len(ifc_nodes) * 100
                print(f"    📊 IFC 인덱싱 진행률: {min(progress, 100):.1f}%")
        
        return ifc_count
    
    def _extract_keywords_simple(self, text: str) -> list[str]:
        """Simplified keyword extraction for better performance."""
        if not text:
            return []
        
        # Simple word extraction (Korean + English)
        words = re.findall(r'[가-힣a-zA-Z]+', text.lower())
        
        # Filter out very short words and common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', '이', '그', '저', '의', '를', '을', '가', '은', '는'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Return top 10 keywords to limit memory usage
        return keywords[:10]
    
    def process_query(self, question: str, **kwargs) -> dict[str, Any]:
        """Process a natural language query with optimized search."""
        if not self.initialized:
            return {"error": "Engine not initialized"}
        
        # Extract keywords from question
        keywords = self._extract_keywords_simple(question)
        
        # Determine query type and handle accordingly
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
        guid_pattern = r'([A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12})'
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
        # Extract GUID from question (UUID 형식 지원)
        guid_pattern = r'([A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12})'
        match = re.search(guid_pattern, question)
        
        if not match:
            return {"error": "GUID not found in question"}
        
        guid = match.group(1)
        
        # Search for element with this GUID
        with self.ix.searcher() as searcher:
            query = Term("guid", guid)
            results = searcher.search(query, limit=1)
            
            if results:
                hit = results[0]
                return {
                    "answer": f"GUID {guid}는 {hit['entity_type']} 타입의 요소입니다.",
                    "confidence": 1.0,
                    "result_count": 1,
                    "entities": [guid],  # 실제 GUID 반환
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
                    "result_count": 0,
                    "entities": [],
                    "source": "BM25"
                }
    
    def _handle_temporal_query(self, question: str, keywords: list[str]) -> dict[str, Any]:
        """Handle temporal queries."""
        with self.ix.searcher() as searcher:
            # Search for recent documents
            query = MultifieldParser(["title", "content"], self.ix.schema).parse(" ".join(keywords))
            results = searcher.search(query, limit=10)
            
            if results:
                answer = f"최근 관련 문서 {len(results)}개를 찾았습니다."
                entities = [hit['guid'] for hit in results if hit.get('guid')]
                return {
                    "answer": answer,
                    "confidence": 0.7,
                    "result_count": len(results),
                    "entities": entities,
                    "source": "BM25",
                    "details": {"temporal_query": True, "keywords": keywords}
                }
            else:
                return {
                    "answer": "관련 문서를 찾을 수 없습니다.",
                    "confidence": 0.0,
                    "result_count": 0,
                    "entities": [],
                    "source": "BM25"
                }
    
    def _handle_author_query(self, question: str, keywords: list[str]) -> dict[str, Any]:
        """Handle author-specific queries."""
        with self.ix.searcher() as searcher:
            # Search by author field
            query = MultifieldParser(["author", "title", "content"], self.ix.schema).parse(" ".join(keywords))
            results = searcher.search(query, limit=10)
            
            if results:
                answer = f"작성자 관련 문서 {len(results)}개를 찾았습니다."
                entities = [hit['guid'] for hit in results if hit.get('guid')]
                return {
                    "answer": answer,
                    "confidence": 0.6,
                    "result_count": len(results),
                    "entities": entities,
                    "source": "BM25",
                    "details": {"author_query": True, "keywords": keywords}
                }
            else:
                return {
                    "answer": "작성자 관련 문서를 찾을 수 없습니다.",
                    "confidence": 0.0,
                    "result_count": 0,
                    "entities": [],
                    "source": "BM25"
                }
    
    def _handle_general_query(self, question: str, keywords: list[str]) -> dict[str, Any]:
        """Handle general queries."""
        with self.ix.searcher() as searcher:
            # Multi-field search
            query = MultifieldParser(["title", "content", "keywords"], self.ix.schema).parse(" ".join(keywords))
            results = searcher.search(query, limit=20)
            
            if results:
                # Separate BCF and IFC results
                bcf_results = [hit for hit in results if hit['doc_type'] == 'BCF']
                ifc_results = [hit for hit in results if hit['doc_type'] == 'IFC']
                
                answer = f"관련 문서 {len(results)}개를 찾았습니다. (BCF: {len(bcf_results)}개, IFC: {len(ifc_results)}개)"
                
                # Extract entity IDs (실제 GUID 추출)
                entities = []
                for hit in results:
                    if hit.get('doc_type') == 'IFC':
                        entities.append(hit.get('guid', ''))
                    else:
                        entities.append(hit.get('doc_id', ''))
                
                return {
                    "answer": answer,
                    "confidence": 0.6,
                    "result_count": len(results),
                    "entities": entities,
                    "source": "BM25",
                    "details": {
                        "bcf_count": len(bcf_results),
                        "ifc_count": len(ifc_results),
                        "total_results": len(results)
                    }
                }
            else:
                return {
                    "answer": "관련 문서를 찾을 수 없습니다.",
                    "confidence": 0.0,
                    "result_count": 0,
                    "entities": [],
                    "source": "BM25"
                }
