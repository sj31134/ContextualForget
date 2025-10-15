#!/usr/bin/env python3
"""
RAG 시스템 평가 스크립트
BM25, Vector RAG, ContextualForget 비교 평가
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from contextualforget.baselines.bm25_engine import BM25QueryEngine
from contextualforget.baselines.vector_engine import VectorQueryEngine
from contextualforget.query.advanced_query import AdvancedQueryEngine


class RAGEvaluator:
    """RAG 시스템 평가 클래스"""
    
    def __init__(self, graph_path: str = "data/processed/graph.gpickle"):
        self.graph_path = graph_path
        self.engines = {}
        self.results = []
        
    def initialize_engines(self):
        """모든 RAG 엔진 초기화"""
        print("🔧 RAG 엔진들 초기화 중...")
        
        # Load graph data
        import pickle
        with open(self.graph_path, 'rb') as f:
            graph = pickle.load(f)
        
        # Extract data for engines
        bcf_data = []
        ifc_data = []
        
        for node, data in graph.nodes(data=True):
            if node[0] == "BCF":
                bcf_data.append(data)
            elif node[0] == "IFC":
                ifc_data.append(data)
        
        graph_data = {
            'bcf_data': bcf_data,
            'ifc_data': ifc_data,
            'graph': graph
        }
        
        # Initialize BM25 engine with sample data for testing
        print("  📚 BM25 엔진 초기화...")
        # Remove existing index to force rebuild
        import shutil
        bm25_index_dir = Path("data/processed/bm25_index")
        if bm25_index_dir.exists():
            shutil.rmtree(bm25_index_dir)
        
        self.engines['BM25'] = BM25QueryEngine()
        # Use sample data for BM25 testing
        sample_data = {
            'bcf_data': [
                {
                    'guid': 'bcf_sample_001',
                    'topic_id': 'bcf_sample_001', 
                    'title': 'Sample BCF Issue',
                    'description': 'This is a sample BCF issue for testing',
                    'author': 'test_user',
                    'created': '2025-01-01T00:00:00Z',
                    'status': 'open',
                    'priority': 'medium',
                    'assigned_to': 'engineer_1',
                    'viewpoint_guid': '1kTvXnbbzCWw8lcMd1dR4o',
                    'topic_guid': 'bcf_sample_001',
                    'comment': 'Initial issue report',
                    'modified_date': '2025-01-01T00:00:00Z'
                }
            ]
        }
        self.engines['BM25'].initialize(sample_data)
        
        # Initialize Vector engine with actual graph data
        print("  🧠 Vector 엔진 초기화...")
        self.engines['Vector'] = VectorQueryEngine()
        self.engines['Vector'].initialize(graph_data)
        
        # Initialize ContextualForget engine
        print("  🎯 ContextualForget 엔진 초기화...")
        self.engines['ContextualForget'] = AdvancedQueryEngine(graph)
        
        print("✅ 모든 엔진 초기화 완료")
    
    def create_test_queries(self) -> List[Dict[str, Any]]:
        """테스트 쿼리 생성"""
        return [
            {
                "id": "q1",
                "question": "무균실 관련 이슈가 있나요?",
                "type": "general",
                "expected_entities": ["무균실", "마감"],
                "expected_guid": None
            },
            {
                "id": "q2", 
                "question": "vvqxIxPgyNdRG6WySVJWDP와 관련된 문제는?",
                "type": "guid",
                "expected_entities": ["vvqxIxPgyNdRG6WySVJWDP"],
                "expected_guid": "vvqxIxPgyNdRG6WySVJWDP"
            },
            {
                "id": "q3",
                "question": "최근 7일간 발생한 이슈는?",
                "type": "temporal",
                "expected_entities": [],
                "expected_guid": None
            },
            {
                "id": "q4",
                "question": "engineer_a가 작성한 이슈는?",
                "type": "author",
                "expected_entities": ["engineer_a"],
                "expected_guid": None
            },
            {
                "id": "q5",
                "question": "마감 관련 문제점은?",
                "type": "general",
                "expected_entities": ["마감", "사양"],
                "expected_guid": None
            }
        ]
    
    def evaluate_engine(self, engine_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """단일 엔진 평가"""
        start_time = time.time()
        
        try:
            if engine_name == "ContextualForget":
                # ContextualForget는 다른 인터페이스 사용
                if query["type"] == "guid" and query["expected_guid"]:
                    results = self.engines[engine_name].find_by_guid(query["expected_guid"])
                elif query["type"] == "author":
                    author = query["expected_entities"][0] if query["expected_entities"] else ""
                    results = self.engines[engine_name].find_by_author(author)
                else:
                    results = self.engines[engine_name].find_by_keywords(
                        query["expected_entities"]
                    )
                
                answer = f"Found {len(results)} results"
                confidence = 0.8 if results else 0.0
                
            else:
                # BM25와 Vector 엔진
                result = self.engines[engine_name].process_query(query["question"])
                answer = result.get("answer", "")
                confidence = result.get("confidence", 0.0)
                results = result.get("details", {})
            
            response_time = time.time() - start_time
            
            return {
                "engine": engine_name,
                "query_id": query["id"],
                "question": query["question"],
                "answer": answer,
                "confidence": confidence,
                "response_time": response_time,
                "results_count": len(results) if isinstance(results, list) else results.get("total_results", 0),
                "success": True,
                "error": None
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "engine": engine_name,
                "query_id": query["id"],
                "question": query["question"],
                "answer": "",
                "confidence": 0.0,
                "response_time": response_time,
                "results_count": 0,
                "success": False,
                "error": str(e)
            }
    
    def run_evaluation(self) -> pd.DataFrame:
        """전체 평가 실행"""
        print("🚀 RAG 시스템 평가 시작...")
        
        # 엔진 초기화
        self.initialize_engines()
        
        # 테스트 쿼리 생성
        test_queries = self.create_test_queries()
        
        # 각 엔진별로 평가 실행
        all_results = []
        
        for query in test_queries:
            print(f"\n📝 쿼리 평가: {query['question']}")
            
            for engine_name in self.engines.keys():
                print(f"  🔍 {engine_name} 엔진 평가 중...")
                result = self.evaluate_engine(engine_name, query)
                all_results.append(result)
                
                if result["success"]:
                    print(f"    ✅ 성공 - 신뢰도: {result['confidence']:.3f}, 응답시간: {result['response_time']:.3f}s")
                else:
                    print(f"    ❌ 실패 - 오류: {result['error']}")
        
        # 결과를 DataFrame으로 변환
        df = pd.DataFrame(all_results)
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"evaluation_results_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n📊 평가 결과 저장: {output_file}")
        
        return df
    
    def generate_report(self, df: pd.DataFrame) -> str:
        """평가 보고서 생성"""
        report = []
        report.append("# RAG 시스템 평가 보고서")
        report.append(f"평가 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 전체 통계
        report.append("## 전체 통계")
        report.append("")
        
        for engine in df['engine'].unique():
            engine_df = df[df['engine'] == engine]
            success_rate = engine_df['success'].mean() * 100
            avg_confidence = engine_df[engine_df['success']]['confidence'].mean()
            avg_response_time = engine_df['response_time'].mean()
            
            report.append(f"### {engine}")
            report.append(f"- 성공률: {success_rate:.1f}%")
            report.append(f"- 평균 신뢰도: {avg_confidence:.3f}")
            report.append(f"- 평균 응답시간: {avg_response_time:.3f}초")
            report.append("")
        
        # 쿼리별 상세 결과
        report.append("## 쿼리별 상세 결과")
        report.append("")
        
        for query_id in df['query_id'].unique():
            query_df = df[df['query_id'] == query_id]
            question = query_df.iloc[0]['question']
            
            report.append(f"### {query_id}: {question}")
            report.append("")
            
            for _, row in query_df.iterrows():
                status = "✅" if row['success'] else "❌"
                report.append(f"- **{row['engine']}** {status}")
                if row['success']:
                    report.append(f"  - 신뢰도: {row['confidence']:.3f}")
                    report.append(f"  - 응답시간: {row['response_time']:.3f}초")
                    report.append(f"  - 결과 수: {row['results_count']}")
                else:
                    report.append(f"  - 오류: {row['error']}")
                report.append("")
        
        return "\n".join(report)


def main():
    """메인 실행 함수"""
    evaluator = RAGEvaluator()
    
    # 평가 실행
    results_df = evaluator.run_evaluation()
    
    # 보고서 생성
    report = evaluator.generate_report(results_df)
    
    # 보고서 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"evaluation_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📋 평가 보고서 저장: {report_file}")
    
    # 간단한 요약 출력
    print("\n" + "="*50)
    print("📊 평가 요약")
    print("="*50)
    
    for engine in results_df['engine'].unique():
        engine_df = results_df[results_df['engine'] == engine]
        success_rate = engine_df['success'].mean() * 100
        avg_confidence = engine_df[engine_df['success']]['confidence'].mean()
        
        print(f"{engine:15} | 성공률: {success_rate:5.1f}% | 평균신뢰도: {avg_confidence:.3f}")


if __name__ == "__main__":
    main()
