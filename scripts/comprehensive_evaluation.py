"""
Comprehensive Evaluation of RAG Systems
종합 평가 및 성능 비교
"""

import json
import pickle
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.query.contextual_forget_engine import ContextualForgetEngine
from contextualforget.query.adaptive_retrieval import HybridRetrievalEngine
from contextualforget.baselines.bm25_engine import BM25QueryEngine
from contextualforget.baselines.vector_engine import VectorQueryEngine


class ComprehensiveRAGEvaluator:
    """종합 RAG 시스템 평가자"""
    
    def __init__(self, graph_path: str = 'data/processed/graph.gpickle'):
        self.graph_path = graph_path
        self.graph = None
        self.engines = {}
        self.evaluation_results = {}
        
        # 평가 메트릭
        self.metrics = {
            'response_time': [],
            'confidence': [],
            'result_count': [],
            'success_rate': [],
            'relevance_score': []
        }
        
    def load_graph(self):
        """그래프 로드"""
        print("📊 그래프 로드 중...")
        with open(self.graph_path, 'rb') as f:
            self.graph = pickle.load(f)
        print(f"✅ 그래프 로드 완료: {self.graph.number_of_nodes()}개 노드, {self.graph.number_of_edges()}개 엣지")
    
    def initialize_engines(self):
        """모든 엔진 초기화"""
        print("\\n🔧 엔진들 초기화 중...")
        
        # 데이터 추출
        bcf_data = []
        ifc_data = []
        for node, data in self.graph.nodes(data=True):
            if node[0] == 'BCF':
                bcf_data.append(data)
            elif node[0] == 'IFC':
                ifc_data.append(data)
        
        print(f"   📋 BCF 데이터: {len(bcf_data)}개")
        print(f"   📋 IFC 데이터: {len(ifc_data)}개")
        
        # BM25 엔진
        print("   🔍 BM25 엔진 초기화...")
        bm25_engine = BM25QueryEngine()
        bm25_engine.initialize({'bcf_data': bcf_data})
        self.engines['BM25'] = bm25_engine
        
        # Vector 엔진
        print("   🔍 Vector 엔진 초기화...")
        vector_engine = VectorQueryEngine()
        vector_engine.initialize({
            'bcf_data': bcf_data,
            'ifc_data': ifc_data,
            'graph': self.graph
        })
        self.engines['Vector'] = vector_engine
        
        # ContextualForget 엔진
        print("   🔍 ContextualForget 엔진 초기화...")
        contextual_engine = ContextualForgetEngine(
            self.graph, 
            enable_contextual_forgetting=True
        )
        self.engines['ContextualForget'] = contextual_engine
        
        # 하이브리드 엔진
        print("   🔍 하이브리드 엔진 초기화...")
        hybrid_engine = HybridRetrievalEngine(
            base_engines=self.engines.copy(),
            fusion_strategy='adaptive',
            enable_adaptation=True
        )
        self.engines['Hybrid'] = hybrid_engine
        
        print("✅ 모든 엔진 초기화 완료")
    
    def create_comprehensive_test_queries(self) -> List[Dict[str, Any]]:
        """종합 테스트 쿼리 생성"""
        # 실제 그래프에서 검증된 키워드만 추출
        verified_keywords = []
        for node, data in self.graph.nodes(data=True):
            if node[0] == 'BCF':
                title = data.get('title', '')
                if title and len(title) > 2:
                    # 각 키워드로 실제 검색 테스트
                    keywords = [w for w in title.split() if len(w) > 1]
                    for kw in keywords:
                        # 그래프에서 이 키워드로 찾을 수 있는지 확인
                        matches = sum(1 for _, d in self.graph.nodes(data=True) 
                                     if d.get('title', '').lower().count(kw.lower()) > 0)
                        if matches > 0:
                            verified_keywords.append((kw, matches))
        
        # 매칭 개수가 많은 순으로 정렬
        verified_keywords.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 키워드로 테스트 쿼리 생성
        test_queries = []
        for keyword, expected_count in verified_keywords[:10]:
            test_queries.append({
                'id': f'kw_{len(test_queries)+1}',
                'question': f'{keyword} 관련 이슈가 있나요?',
                'type': 'keyword',
                'expected_keywords': [keyword],
                'expected_min_count': min(expected_count, 5),
                'category': 'keyword_search'
            })
        
        # 작성자 기반 쿼리 (실제 존재하는 작성자만)
        authors = set()
        for node, data in self.graph.nodes(data=True):
            if node[0] == 'BCF':
                author = data.get('author', '')
                if author:
                    authors.add(author)
        
        author_list = list(authors)[:5]
        for author in author_list:
            test_queries.append({
                'id': f'auth_{len(test_queries)+1}',
                'question': f'{author}가 작성한 이슈는?',
                'type': 'author',
                'expected_author': author,
                'category': 'author_search'
            })
        
        # GUID 기반 쿼리 (실제 존재하는 GUID만)
        guids = set()
        for node, data in self.graph.nodes(data=True):
            if node[0] == 'BCF':
                topic_id = data.get('topic_id', '')
                if topic_id:
                    guids.add(topic_id)
        
        guid_list = list(guids)[:5]
        for guid in guid_list:
            test_queries.append({
                'id': f'guid_{len(test_queries)+1}',
                'question': f'{guid}와 관련된 문제는?',
                'type': 'guid',
                'expected_guid': guid,
                'category': 'guid_search'
            })
        
        # 검증된 복합 쿼리
        complex_queries = [
            {
                'id': f'comp_{len(test_queries)+1}',
                'question': '무균실 마감 관련 문제점은?',
                'type': 'complex',
                'expected_keywords': ['무균실', '마감'],
                'category': 'complex_search'
            },
            {
                'id': f'comp_{len(test_queries)+1}',
                'question': '최근 발생한 벽체 관련 이슈는?',
                'type': 'temporal',
                'expected_keywords': ['벽체'],
                'category': 'temporal_search'
            }
        ]
        test_queries.extend(complex_queries)
        
        return test_queries
    
    def evaluate_engine(self, engine_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """단일 엔진 평가"""
        start_time = time.perf_counter()
        
        try:
            engine = self.engines[engine_name]
            question = query['question']
            
            # 엔진별 쿼리 실행
            if engine_name == 'BM25':
                result = engine.process_query(question)
            elif engine_name == 'Vector':
                result = engine.process_query(question)
            elif engine_name == 'ContextualForget':
                result = engine.contextual_query(question, query_type=query['type'])
            elif engine_name == 'Hybrid':
                result = engine.query(question)
                # 하이브리드 결과에서 실제 결과 추출
                if 'result' in result:
                    result = result['result']
            else:
                result = {'error': 'Unknown engine'}
            
            response_time = max(time.perf_counter() - start_time, 0.0001)
            
            # 결과 분석
            if isinstance(result, dict) and 'error' not in result:
                confidence = result.get('confidence', 0.0)
                result_count = result.get('result_count', 0)
                # result_count가 0이고 details에 정보가 있으면 추출
                if result_count == 0 and 'details' in result:
                    details = result['details']
                    result_count = details.get('count', details.get('total_results', 0))
                # 성공 기준: 결과가 있고 신뢰도가 일정 수준 이상
                success = result_count > 0 and confidence > 0.1
                
                # 관련성 점수 계산
                relevance_score = self._calculate_relevance_score(query, result)
                
                return {
                    'engine': engine_name,
                    'query_id': query['id'],
                    'question': question,
                    'query_type': query['type'],
                    'category': query['category'],
                    'answer': result.get('answer', 'No answer'),
                    'confidence': confidence,
                    'response_time': response_time,
                    'result_count': result_count,
                    'success': success,
                    'relevance_score': relevance_score,
                    'error': None
                }
            else:
                return {
                    'engine': engine_name,
                    'query_id': query['id'],
                    'question': question,
                    'query_type': query['type'],
                    'category': query['category'],
                    'answer': 'Error occurred',
                    'confidence': 0.0,
                    'response_time': response_time,
                    'result_count': 0,
                    'success': False,
                    'relevance_score': 0.0,
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            response_time = max(time.perf_counter() - start_time, 0.0001)
            return {
                'engine': engine_name,
                'query_id': query['id'],
                'question': question,
                'query_type': query['type'],
                'category': query['category'],
                'answer': 'Exception occurred',
                'confidence': 0.0,
                'response_time': response_time,
                'result_count': 0,
                'success': False,
                'relevance_score': 0.0,
                'error': str(e)
            }
    
    def _calculate_relevance_score(self, query: Dict[str, Any], result: Dict[str, Any]) -> float:
        """관련성 점수 계산"""
        try:
            answer = result.get('answer', '').lower()
            question = query['question'].lower()
            
            # 키워드 매칭
            if 'expected_keywords' in query:
                expected_keywords = [kw.lower() for kw in query['expected_keywords']]
                matched_keywords = sum(1 for kw in expected_keywords if kw in answer)
                return matched_keywords / len(expected_keywords)
            
            # 작성자 매칭
            elif 'expected_author' in query:
                expected_author = query['expected_author'].lower()
                return 1.0 if expected_author in answer else 0.0
            
            # GUID 매칭
            elif 'expected_guid' in query:
                expected_guid = query['expected_guid']
                return 1.0 if expected_guid in answer else 0.0
            
            # 기본 관련성 (단어 겹침)
            else:
                question_words = set(question.split())
                answer_words = set(answer.split())
                if question_words:
                    overlap = len(question_words.intersection(answer_words))
                    return overlap / len(question_words)
                return 0.0
                
        except Exception:
            return 0.0
    
    def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """종합 평가 실행"""
        print("\\n🚀 종합 평가 시작...")
        
        # 테스트 쿼리 생성
        test_queries = self.create_comprehensive_test_queries()
        print(f"📝 생성된 테스트 쿼리: {len(test_queries)}개")
        
        # 각 엔진별 평가
        all_results = []
        
        for engine_name in self.engines.keys():
            print(f"\\n🔍 {engine_name} 엔진 평가 중...")
            engine_results = []
            
            for query in test_queries:
                result = self.evaluate_engine(engine_name, query)
                engine_results.append(result)
                all_results.append(result)
                
                # 진행 상황 출력
                if len(engine_results) % 5 == 0:
                    print(f"   진행률: {len(engine_results)}/{len(test_queries)}")
            
            self.evaluation_results[engine_name] = engine_results
            print(f"✅ {engine_name} 엔진 평가 완료")
        
        # 종합 분석
        comprehensive_analysis = self._analyze_results(all_results)
        
        return {
            'evaluation_results': self.evaluation_results,
            'comprehensive_analysis': comprehensive_analysis,
            'test_queries': test_queries,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _analyze_results(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """결과 종합 분석"""
        analysis = {
            'overall_metrics': {},
            'engine_comparison': {},
            'query_type_analysis': {},
            'category_analysis': {},
            'performance_ranking': {}
        }
        
        # 전체 메트릭 계산
        total_queries = len(all_results)
        successful_queries = sum(1 for r in all_results if r['success'])
        
        analysis['overall_metrics'] = {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'overall_success_rate': successful_queries / total_queries if total_queries > 0 else 0,
            'average_confidence': np.mean([r['confidence'] for r in all_results]),
            'average_response_time': np.mean([r['response_time'] for r in all_results]),
            'average_relevance_score': np.mean([r['relevance_score'] for r in all_results])
        }
        
        # 엔진별 비교
        for engine_name in self.engines.keys():
            engine_results = [r for r in all_results if r['engine'] == engine_name]
            
            if engine_results:
                analysis['engine_comparison'][engine_name] = {
                    'total_queries': len(engine_results),
                    'successful_queries': sum(1 for r in engine_results if r['success']),
                    'success_rate': sum(1 for r in engine_results if r['success']) / len(engine_results),
                    'average_confidence': np.mean([r['confidence'] for r in engine_results]),
                    'average_response_time': np.mean([r['response_time'] for r in engine_results]),
                    'average_relevance_score': np.mean([r['relevance_score'] for r in engine_results]),
                    'average_result_count': np.mean([r['result_count'] for r in engine_results])
                }
        
        # 쿼리 타입별 분석
        query_types = set(r['query_type'] for r in all_results)
        for query_type in query_types:
            type_results = [r for r in all_results if r['query_type'] == query_type]
            
            analysis['query_type_analysis'][query_type] = {
                'total_queries': len(type_results),
                'success_rate': sum(1 for r in type_results if r['success']) / len(type_results),
                'average_confidence': np.mean([r['confidence'] for r in type_results]),
                'average_response_time': np.mean([r['response_time'] for r in type_results])
            }
        
        # 카테고리별 분석
        categories = set(r['category'] for r in all_results)
        for category in categories:
            category_results = [r for r in all_results if r['category'] == category]
            
            analysis['category_analysis'][category] = {
                'total_queries': len(category_results),
                'success_rate': sum(1 for r in category_results if r['success']) / len(category_results),
                'average_confidence': np.mean([r['confidence'] for r in category_results]),
                'average_response_time': np.mean([r['response_time'] for r in category_results])
            }
        
        # 성능 순위
        engine_scores = {}
        for engine_name, metrics in analysis['engine_comparison'].items():
            # 복합 점수 계산 (신뢰도 중심: 성공률 30%, 신뢰도 50%, 관련성 15%, 응답시간 5%)
            score = (
                metrics['success_rate'] * 0.3 +
                metrics['average_confidence'] * 0.5 +
                metrics['average_relevance_score'] * 0.15 +
                max(0, 1 - metrics['average_response_time'] / 5.0) * 0.05
            )
            engine_scores[engine_name] = score
        
        analysis['performance_ranking'] = dict(sorted(engine_scores.items(), key=lambda x: x[1], reverse=True))
        
        return analysis
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """결과 저장"""
        # JSON 형태로 저장
        json_path = output_path.replace('.json', '_comprehensive.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        # CSV 형태로도 저장
        csv_path = output_path.replace('.json', '_detailed.csv')
        all_results = []
        for engine_name, engine_results in results['evaluation_results'].items():
            all_results.extend(engine_results)
        
        df = pd.DataFrame(all_results)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"\\n💾 결과 저장 완료:")
        print(f"   📄 JSON: {json_path}")
        print(f"   📊 CSV: {csv_path}")
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """평가 보고서 생성"""
        analysis = results['comprehensive_analysis']
        
        report = f"""
# ContextualForget 종합 평가 보고서

## 📊 전체 성능 요약

- **총 쿼리 수**: {analysis['overall_metrics']['total_queries']}
- **성공률**: {analysis['overall_metrics']['overall_success_rate']:.2%}
- **평균 신뢰도**: {analysis['overall_metrics']['average_confidence']:.3f}
- **평균 응답시간**: {analysis['overall_metrics']['average_response_time']:.3f}초
- **평균 관련성**: {analysis['overall_metrics']['average_relevance_score']:.3f}

## 🏆 엔진별 성능 비교

"""
        
        for engine_name, metrics in analysis['engine_comparison'].items():
            report += f"""
### {engine_name}
- **성공률**: {metrics['success_rate']:.2%}
- **평균 신뢰도**: {metrics['average_confidence']:.3f}
- **평균 응답시간**: {metrics['average_response_time']:.3f}초
- **평균 관련성**: {metrics['average_relevance_score']:.3f}
- **평균 결과 수**: {metrics['average_result_count']:.1f}

"""
        
        # 성능 순위
        report += "## 🥇 성능 순위\n\n"
        for i, (engine_name, score) in enumerate(analysis['performance_ranking'].items(), 1):
            report += f"{i}. **{engine_name}**: {score:.3f}\n"
        
        # 쿼리 타입별 분석
        report += "\\n## 📝 쿼리 타입별 성능\n\n"
        for query_type, metrics in analysis['query_type_analysis'].items():
            report += f"### {query_type}\n"
            report += f"- **성공률**: {metrics['success_rate']:.2%}\n"
            report += f"- **평균 신뢰도**: {metrics['average_confidence']:.3f}\n"
            report += f"- **평균 응답시간**: {metrics['average_response_time']:.3f}초\n\n"
        
        # 카테고리별 분석
        report += "## 🏷️ 카테고리별 성능\n\n"
        for category, metrics in analysis['category_analysis'].items():
            report += f"### {category}\n"
            report += f"- **성공률**: {metrics['success_rate']:.2%}\n"
            report += f"- **평균 신뢰도**: {metrics['average_confidence']:.3f}\n"
            report += f"- **평균 응답시간**: {metrics['average_response_time']:.3f}초\n\n"
        
        report += f"\\n---\\n*평가 완료 시간: {results['timestamp']}*"
        
        return report


def main():
    """메인 실행 함수"""
    print("🚀 ContextualForget 종합 평가 시작")
    
    # 평가자 초기화
    evaluator = ComprehensiveRAGEvaluator()
    
    # 그래프 로드
    evaluator.load_graph()
    
    # 엔진 초기화
    evaluator.initialize_engines()
    
    # 종합 평가 실행
    results = evaluator.run_comprehensive_evaluation()
    
    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"evaluation_comprehensive_{timestamp}.json"
    evaluator.save_results(results, output_path)
    
    # 보고서 생성
    report = evaluator.generate_report(results)
    report_path = f"evaluation_report_{timestamp}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\\n📋 평가 보고서: {report_path}")
    print("\\n✅ 종합 평가 완료!")
    
    # 간단한 요약 출력
    analysis = results['comprehensive_analysis']
    print("\\n📊 성능 순위:")
    for i, (engine_name, score) in enumerate(analysis['performance_ranking'].items(), 1):
        print(f"   {i}. {engine_name}: {score:.3f}")


if __name__ == "__main__":
    main()
