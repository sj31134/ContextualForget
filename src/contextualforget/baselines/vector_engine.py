"""
Vector-based semantic search engine using Sentence-BERT.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .base import BaselineQueryEngine


class VectorQueryEngine(BaselineQueryEngine):
    """Vector-based semantic search engine using Sentence-BERT."""
    
    def __init__(self, 
                 model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
                 cache_dir: str = "data/processed/vector_cache"):
        super().__init__("Vector")
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.model = None
        self.embeddings = None
        self.documents = None
        self.document_metadata = None
        
    def initialize(self, graph_data: dict[str, Any]) -> None:
        """Initialize vector engine with graph data."""
        print("🔧 Vector 엔진 초기화 중...")
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create embeddings
        embeddings_path = self.cache_dir / "embeddings.npy"
        documents_path = self.cache_dir / "documents.json"
        metadata_path = self.cache_dir / "metadata.json"
        
        if (embeddings_path.exists() and 
            documents_path.exists() and 
            metadata_path.exists()):
            self._load_cached_embeddings(embeddings_path, documents_path, metadata_path)
            print(f"  ✅ 캐시된 임베딩 로드: {len(self.documents)}개 문서")
        else:
            self._build_embeddings(graph_data)
            self._save_embeddings(embeddings_path, documents_path, metadata_path)
            print(f"  ✅ 새 임베딩 생성: {len(self.documents)}개 문서")
        
        self.initialized = True
        print("  ✅ Vector 엔진 초기화 완료")
    
    def _load_cached_embeddings(self, 
                               embeddings_path: Path, 
                               documents_path: Path, 
                               metadata_path: Path) -> None:
        """Load cached embeddings and documents."""
        # Load model
        self.model = SentenceTransformer(self.model_name)
        
        # Load embeddings
        self.embeddings = np.load(embeddings_path)
        
        # Load documents
        with Path(documents_path).open(encoding='utf-8') as f:
            self.documents = json.load(f)
        
        # Load metadata
        with Path(metadata_path).open(encoding='utf-8') as f:
            self.document_metadata = json.load(f)
    
    def _build_embeddings(self, graph_data: dict[str, Any]) -> None:
        """Build embeddings from graph data."""
        print("  📚 임베딩 구축 중...")
        
        # Load model
        self.model = SentenceTransformer(self.model_name)
        
        # Prepare documents
        documents = []
        metadata = []
        
        # Process BCF data
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
                    
                    # Create document text
                    doc_text = f"{title} {description}".strip()
                    
                    if doc_text:  # Only add non-empty documents
                        documents.append(doc_text)
                        metadata.append({
                            "doc_id": f"bcf_{node_id}",
                            "doc_type": "BCF",
                            "title": title,
                            "author": author,
                            "created": created,
                            "guid": "",
                            "entity_type": ""
                        })
                        bcf_count += 1
        
        # Process IFC data
        ifc_count = 0
        for node, data in graph_data.get('nodes', []):
            if isinstance(node, tuple) and len(node) == 2:
                node_type, node_id = node
                if node_type == "IFC":
                    # Extract IFC data
                    name = data.get('name', node_id)
                    entity_type = data.get('type', 'Unknown')
                    
                    # Create document text
                    doc_text = f"{name} {entity_type}".strip()
                    
                    if doc_text:  # Only add non-empty documents
                        documents.append(doc_text)
                        metadata.append({
                            "doc_id": f"ifc_{node_id}",
                            "doc_type": "IFC",
                            "title": name,
                            "author": "",
                            "created": "",
                            "guid": node_id,
                            "entity_type": entity_type
                        })
                        ifc_count += 1
        
        # Generate embeddings
        print(f"    📋 BCF 문서: {bcf_count}개")
        print(f"    📐 IFC 문서: {ifc_count}개")
        print("    🔄 임베딩 생성 중...")
        
        self.embeddings = self.model.encode(documents, show_progress_bar=True)
        self.documents = documents
        self.document_metadata = metadata
        
        print(f"    ✅ 총 {len(documents)}개 문서 임베딩 완료")
    
    def _save_embeddings(self, 
                        embeddings_path: Path, 
                        documents_path: Path, 
                        metadata_path: Path) -> None:
        """Save embeddings and documents to cache."""
        # Save embeddings
        np.save(embeddings_path, self.embeddings)
        
        # Save documents
        with Path(documents_path).open('w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        # Save metadata
        with Path(metadata_path).open('w', encoding='utf-8') as f:
            json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
    
    def process_query(self, question: str, **kwargs) -> dict[str, Any]:
        """Process a natural language query using vector similarity."""
        if not self.initialized:
            raise RuntimeError("Vector engine not initialized")
        
        # Handle different query types
        if self._is_guid_query(question):
            return self._handle_guid_query(question)
        elif self._is_temporal_query(question):
            return self._handle_temporal_query(question)
        elif self._is_author_query(question):
            return self._handle_author_query(question)
        else:
            return self._handle_general_query(question)
    
    def _is_guid_query(self, question: str) -> bool:
        """Check if query is asking for GUID information."""
        import re
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
        import re
        
        # Extract GUID from question
        guid_pattern = r'\b([A-Za-z0-9]{22})\b'
        match = re.search(guid_pattern, question)
        
        if not match:
            return {"error": "GUID not found in question"}
        
        guid = match.group(1)
        
        # Search for IFC element with this GUID
        for _i, metadata in enumerate(self.document_metadata):
            if metadata['doc_type'] == 'IFC' and metadata['guid'] == guid:
                return {
                    "answer": f"GUID {guid}는 {metadata['entity_type']} 타입의 IFC 요소입니다.",
                    "confidence": 1.0,
                    "result_count": 1,
                    "source": "Vector",
                    "details": {
                        "guid": guid,
                        "entity_type": metadata['entity_type'],
                        "name": metadata['title']
                    }
                }
        
        return {
            "answer": f"GUID {guid}에 대한 정보를 찾을 수 없습니다.",
            "confidence": 0.0,
            "result_count": 0,
            "source": "Vector"
        }
    
    def _handle_temporal_query(self, question: str) -> dict[str, Any]:
        """Handle temporal queries."""
        # Extract time period from question
        time_period = self._extract_time_period(question)
        
        # Generate query embedding
        query_embedding = self.model.encode([question])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:10]
        
        # Filter by time if specified
        if time_period:
            filtered_results = []
            cutoff_date = datetime.now() - time_period
            
            for idx in top_indices:
                metadata = self.document_metadata[idx]
                if metadata['doc_type'] == 'BCF' and metadata['created']:
                    try:
                        created_date = datetime.fromisoformat(metadata['created'].replace('Z', '+00:00'))
                        if created_date >= cutoff_date:
                            filtered_results.append((idx, similarities[idx]))
                    except Exception:
                        pass
        else:
            # Filter for BCF documents only
            filtered_results = []
            for idx in top_indices:
                metadata = self.document_metadata[idx]
                if metadata['doc_type'] == 'BCF':
                    filtered_results.append((idx, similarities[idx]))
        
        if filtered_results:
            # Sort by similarity
            filtered_results.sort(key=lambda x: x[1], reverse=True)
            
            issues = []
            for idx, _similarity in filtered_results[:5]:
                metadata = self.document_metadata[idx]
                issues.append(metadata['title'])
            
            answer = f"관련 이슈: {', '.join(issues)}"
            return {
                "answer": answer,
                "confidence": 0.7,
                "result_count": len(filtered_results),
                "source": "Vector",
                "details": {
                    "issues": issues,
                    "count": len(filtered_results)
                }
            }
        else:
            return {
                "answer": "해당 기간의 이슈를 찾을 수 없습니다.",
                "confidence": 0.0,
                "result_count": 0,
                "source": "Vector"
            }
    
    def _handle_author_query(self, question: str) -> dict[str, Any]:
        """Handle author-specific queries."""
        import re
        
        # Extract author name from question
        author = None
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
                "source": "Vector"
            }
        
        # Find documents by this author
        author_docs = []
        for i, metadata in enumerate(self.document_metadata):
            if metadata['doc_type'] == 'BCF' and metadata['author'] == author:
                author_docs.append((i, metadata))
        
        if author_docs:
            issues = [metadata['title'] for _, metadata in author_docs[:10]]
            answer = f"{author}가 작성한 이슈: {', '.join(issues[:3])}"
            return {
                "answer": answer,
                "confidence": 0.8,
                "result_count": len(author_docs),
                "source": "Vector",
                "details": {
                    "author": author,
                    "issues": issues,
                    "count": len(author_docs)
                }
            }
        else:
            return {
                "answer": f"{author}가 작성한 이슈를 찾을 수 없습니다.",
                "confidence": 0.0,
                "result_count": 0,
                "source": "Vector"
            }
    
    def _handle_general_query(self, question: str) -> dict[str, Any]:
        """Handle general queries."""
        # Generate query embedding
        query_embedding = self.model.encode([question])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:5]
        
        if similarities[top_indices[0]] > 0.1:  # Minimum similarity threshold
            # Group results by type
            bcf_results = []
            ifc_results = []
            
            for idx in top_indices:
                metadata = self.document_metadata[idx]
                similarity = similarities[idx]
                
                if metadata['doc_type'] == 'BCF':
                    bcf_results.append((metadata['title'], similarity))
                elif metadata['doc_type'] == 'IFC':
                    ifc_results.append((metadata['title'], similarity))
            
            answer_parts = []
            
            if bcf_results:
                bcf_titles = [title for title, _ in bcf_results[:3]]
                answer_parts.append(f"관련 이슈: {', '.join(bcf_titles)}")
            
            if ifc_results:
                ifc_names = [name for name, _ in ifc_results[:3]]
                answer_parts.append(f"관련 요소: {', '.join(ifc_names)}")
            
            answer = " | ".join(answer_parts) if answer_parts else "관련 정보를 찾을 수 없습니다."
            
            return {
                "answer": answer,
                "confidence": float(similarities[top_indices[0]]),
                "result_count": len(bcf_results) + len(ifc_results),
                "source": "Vector",
                "details": {
                    "bcf_count": len(bcf_results),
                    "ifc_count": len(ifc_results),
                    "max_similarity": float(similarities[top_indices[0]])
                }
            }
        else:
            return {
                "answer": "관련 정보를 찾을 수 없습니다.",
                "confidence": 0.0,
                "result_count": 0,
                "source": "Vector"
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
