#!/usr/bin/env python3
"""
확장성 벤치마크 스크립트
노드 수별 응답 시간, 메모리 사용량, CPU 사용률 측정
"""

import sys
import json
import time
import psutil
import gc
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from contextualforget.core.utils import read_jsonl
from contextualforget.baselines.bm25_engine import BM25QueryEngine
from contextualforget.baselines.vector_engine import VectorQueryEngine
from contextualforget.query.contextual_forget_engine import ContextualForgetEngine
from contextualforget.query.adaptive_retrieval import HybridRetrievalEngine
import networkx as nx


def create_scalability_graphs():
    """확장성 테스트용 그래프 생성"""
    
    print("📊 확장성 테스트용 그래프 생성 중...")
    
    # 테스트할 노드 수
    node_counts = [100, 500, 1000, 2000, 5000, 10000]
    graphs = {}
    
    for node_count in node_counts:
        print(f"  🔧 {node_count}개 노드 그래프 생성 중...")
        
        # 그래프 생성
        graph = nx.DiGraph()
        
        # BCF 노드 추가
        for i in range(node_count // 2):
            node_id = ("BCF", f"bcf_{i:06d}")
            graph.add_node(node_id, 
                          topic_id=f"topic_{i:06d}",
                          title=f"Test Issue {i}",
                          description=f"Test description for issue {i}",
                          author=f"engineer_{i%10:03d}",
                          created=datetime.now().isoformat())
        
        # IFC 노드 추가
        for i in range(node_count // 2):
            node_id = ("IFC", f"ifc_{i:06d}")
            graph.add_node(node_id,
                          guid=f"ifc_guid_{i:06d}",
                          type=f"IFC_TYPE_{i%20}",
                          name=f"IFC Entity {i}")
        
        # 간단한 연결 추가 (각 BCF 노드가 2-3개 IFC 노드와 연결)
        for i in range(node_count // 2):
            bcf_node = ("BCF", f"bcf_{i:06d}")
            for j in range(2):
                ifc_idx = (i * 2 + j) % (node_count // 2)
                ifc_node = ("IFC", f"ifc_{ifc_idx:06d}")
                graph.add_edge(bcf_node, ifc_node, relation="references")
        
        graphs[node_count] = graph
        print(f"    ✅ {node_count}개 노드 그래프 생성 완료: {len(graph.nodes)}개 노드, {len(graph.edges)}개 연결")
    
    return graphs


def measure_engine_performance(engine, query, iterations=5):
    """엔진 성능 측정"""
    
    times = []
    memory_usage = []
    cpu_usage = []
    
    for i in range(iterations):
        # 메모리 정리
        gc.collect()
        
        # 초기 리소스 측정
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        # 쿼리 실행 시간 측정
        start_time = time.time()
        
        try:
            if engine.__class__.__name__ == "HybridRetrievalEngine":
                result = engine.query(query)
            else:
                result = engine.process_query(query)
        except Exception as e:
            result = {"error": str(e)}
        
        end_time = time.time()
        
        # 최종 리소스 측정
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()
        
        # 결과 저장
        times.append(end_time - start_time)
        memory_usage.append(final_memory - initial_memory)
        cpu_usage.append(final_cpu - initial_cpu)
    
    return {
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
        "std_time": (sum((t - sum(times)/len(times))**2 for t in times) / len(times))**0.5,
        "avg_memory": sum(memory_usage) / len(memory_usage),
        "max_memory": max(memory_usage),
        "avg_cpu": sum(cpu_usage) / len(cpu_usage),
        "max_cpu": max(cpu_usage)
    }


def run_scalability_benchmark():
    """확장성 벤치마크 실행"""
    
    print("🚀 확장성 벤치마크 시작")
    print("=" * 60)
    
    # 1. 확장성 테스트용 그래프 생성
    graphs = create_scalability_graphs()
    
    print("\n" + "=" * 60)
    
    # 2. 테스트 쿼리 정의
    test_queries = [
        "GUID topic_000001과 관련된 이슈는 무엇인가요?",
        "engineer_001이 작성한 이슈들을 보여주세요.",
        "구조 관련 이슈들을 찾아주세요.",
        "최근 생성된 이슈는 무엇인가요?",
        "작업 우선순위를 높여야 할 이슈는 무엇인가요?"
    ]
    
    # 3. 벤치마크 결과 저장
    benchmark_results = {
        "benchmark_date": datetime.now().isoformat(),
        "node_counts": list(graphs.keys()),
        "test_queries": test_queries,
        "engine_results": defaultdict(lambda: defaultdict(dict))
    }
    
    # 4. 각 노드 수별로 엔진 성능 측정
    for node_count, graph in graphs.items():
        print(f"\n🔍 {node_count}개 노드 그래프 테스트 중...")
        
        # 엔진 초기화
        engines = {}
        
        try:
            print("  📚 BM25 엔진 초기화...")
            engines["BM25"] = BM25QueryEngine(graph)
            print("    ✅ BM25 엔진 초기화 완료")
        except Exception as e:
            print(f"    ❌ BM25 엔진 초기화 실패: {e}")
            continue
        
        try:
            print("  🔍 Vector 엔진 초기화...")
            engines["Vector"] = VectorQueryEngine(graph)
            print("    ✅ Vector 엔진 초기화 완료")
        except Exception as e:
            print(f"    ❌ Vector 엔진 초기화 실패: {e}")
            continue
        
        try:
            print("  🧠 ContextualForget 엔진 초기화...")
            engines["ContextualForget"] = ContextualForgetEngine(graph)
            print("    ✅ ContextualForget 엔진 초기화 완료")
        except Exception as e:
            print(f"    ❌ ContextualForget 엔진 초기화 실패: {e}")
            continue
        
        try:
            print("  🔗 Hybrid 엔진 초기화...")
            base_engines = {
                "BM25": engines["BM25"],
                "Vector": engines["Vector"],
                "ContextualForget": engines["ContextualForget"]
            }
            engines["Hybrid"] = HybridRetrievalEngine(base_engines)
            print("    ✅ Hybrid 엔진 초기화 완료")
        except Exception as e:
            print(f"    ❌ Hybrid 엔진 초기화 실패: {e}")
            continue
        
        # 각 엔진별 성능 측정
        for engine_name, engine in engines.items():
            print(f"  🔬 {engine_name} 엔진 성능 측정 중...")
            
            engine_results = {}
            
            for i, query in enumerate(test_queries):
                print(f"    📝 쿼리 {i+1}/{len(test_queries)}: {query[:50]}...")
                
                performance = measure_engine_performance(engine, query, iterations=3)
                engine_results[f"query_{i+1}"] = performance
            
            # 엔진별 평균 성능 계산
            avg_time = sum(r["avg_time"] for r in engine_results.values()) / len(engine_results)
            avg_memory = sum(r["avg_memory"] for r in engine_results.values()) / len(engine_results)
            avg_cpu = sum(r["avg_cpu"] for r in engine_results.values()) / len(engine_results)
            
            benchmark_results["engine_results"][engine_name][node_count] = {
                "node_count": node_count,
                "avg_response_time": avg_time,
                "avg_memory_usage": avg_memory,
                "avg_cpu_usage": avg_cpu,
                "detailed_results": engine_results
            }
            
            print(f"    ✅ {engine_name} 성능 측정 완료: {avg_time:.3f}s, {avg_memory:.1f}MB, {avg_cpu:.1f}%")
    
    return benchmark_results


def analyze_complexity(benchmark_results):
    """시간 복잡도 분석"""
    
    print("📈 시간 복잡도 분석 중...")
    
    complexity_analysis = {}
    
    for engine_name, engine_data in benchmark_results["engine_results"].items():
        print(f"  🔍 {engine_name} 복잡도 분석...")
        
        # 노드 수와 응답 시간 데이터 추출
        node_counts = []
        response_times = []
        
        for node_count, data in engine_data.items():
            node_counts.append(node_count)
            response_times.append(data["avg_response_time"])
        
        # 복잡도 추정 (O(n), O(n log n), O(n²) 중 선택)
        if len(node_counts) >= 3:
            # 로그 스케일에서 선형 회귀로 복잡도 추정
            import numpy as np
            
            log_nodes = np.log(node_counts)
            log_times = np.log(response_times)
            
            # 선형 회귀
            coeffs = np.polyfit(log_nodes, log_times, 1)
            complexity_exponent = coeffs[0]
            
            if complexity_exponent < 0.5:
                complexity = "O(log n)"
            elif complexity_exponent < 1.2:
                complexity = "O(n)"
            elif complexity_exponent < 1.8:
                complexity = "O(n log n)"
            else:
                complexity = "O(n²)"
        else:
            complexity = "Unknown"
        
        complexity_analysis[engine_name] = {
            "node_counts": node_counts,
            "response_times": response_times,
            "complexity": complexity,
            "complexity_exponent": complexity_exponent if len(node_counts) >= 3 else None
        }
        
        print(f"    ✅ {engine_name}: {complexity}")
    
    return complexity_analysis


def save_benchmark_results(benchmark_results, complexity_analysis):
    """벤치마크 결과 저장"""
    
    print("💾 벤치마크 결과 저장 중...")
    
    # 결과 디렉토리 생성
    results_dir = Path("results/scalability_benchmark")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 상세 벤치마크 결과
    benchmark_file = results_dir / f"scalability_benchmark_{timestamp}.json"
    with open(benchmark_file, 'w', encoding='utf-8') as f:
        json.dump(benchmark_results, f, indent=2, ensure_ascii=False)
    
    # 2. 복잡도 분석 결과
    complexity_file = results_dir / f"complexity_analysis_{timestamp}.json"
    with open(complexity_file, 'w', encoding='utf-8') as f:
        json.dump(complexity_analysis, f, indent=2, ensure_ascii=False)
    
    # 3. 요약 보고서
    summary_file = results_dir / f"scalability_summary_{timestamp}.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# 확장성 벤치마크 결과 요약\n\n")
        f.write(f"**벤치마크 일시**: {benchmark_results['benchmark_date']}\n")
        f.write(f"**테스트 노드 수**: {benchmark_results['node_counts']}\n")
        f.write(f"**테스트 쿼리 수**: {len(benchmark_results['test_queries'])}\n\n")
        
        f.write("## 엔진별 시간 복잡도\n\n")
        f.write("| 엔진 | 시간 복잡도 | 복잡도 지수 |\n")
        f.write("|------|-------------|-------------|\n")
        
        for engine_name, analysis in complexity_analysis.items():
            exponent = analysis["complexity_exponent"]
            exponent_str = f"{exponent:.2f}" if exponent is not None else "N/A"
            f.write(f"| {engine_name} | {analysis['complexity']} | {exponent_str} |\n")
        
        f.write("\n## 노드 수별 성능 요약\n\n")
        f.write("| 노드 수 | BM25 | Vector | ContextualForget | Hybrid |\n")
        f.write("|---------|------|--------|------------------|--------|\n")
        
        for node_count in benchmark_results["node_counts"]:
            row = f"| {node_count} |"
            for engine_name in ["BM25", "Vector", "ContextualForget", "Hybrid"]:
                if engine_name in benchmark_results["engine_results"] and node_count in benchmark_results["engine_results"][engine_name]:
                    time_val = benchmark_results["engine_results"][engine_name][node_count]["avg_response_time"]
                    row += f" {time_val:.3f}s |"
                else:
                    row += " N/A |"
            f.write(row + "\n")
        
        f.write("\n## 메모리 사용량 요약\n\n")
        f.write("| 노드 수 | BM25 | Vector | ContextualForget | Hybrid |\n")
        f.write("|---------|------|--------|------------------|--------|\n")
        
        for node_count in benchmark_results["node_counts"]:
            row = f"| {node_count} |"
            for engine_name in ["BM25", "Vector", "ContextualForget", "Hybrid"]:
                if engine_name in benchmark_results["engine_results"] and node_count in benchmark_results["engine_results"][engine_name]:
                    memory_val = benchmark_results["engine_results"][engine_name][node_count]["avg_memory_usage"]
                    row += f" {memory_val:.1f}MB |"
                else:
                    row += " N/A |"
            f.write(row + "\n")
    
    print(f"  ✅ 결과 저장 완료:")
    print(f"    • 벤치마크 결과: {benchmark_file}")
    print(f"    • 복잡도 분석: {complexity_file}")
    print(f"    • 요약 보고서: {summary_file}")
    
    return {
        "benchmark_file": str(benchmark_file),
        "complexity_file": str(complexity_file),
        "summary_file": str(summary_file)
    }


def main():
    """메인 실행 함수"""
    
    print("🚀 확장성 벤치마크 시작")
    print("=" * 60)
    
    # 1. 확장성 벤치마크 실행
    benchmark_results = run_scalability_benchmark()
    
    print("\n" + "=" * 60)
    
    # 2. 복잡도 분석
    complexity_analysis = analyze_complexity(benchmark_results)
    
    print("\n" + "=" * 60)
    
    # 3. 결과 저장
    saved_files = save_benchmark_results(benchmark_results, complexity_analysis)
    
    print("\n" + "=" * 60)
    print("🎉 확장성 벤치마크 완료!")
    print(f"\n📊 복잡도 분석 결과:")
    
    for engine_name, analysis in complexity_analysis.items():
        print(f"  • {engine_name}: {analysis['complexity']}")
    
    print(f"\n📁 결과 파일:")
    for file_type, file_path in saved_files.items():
        print(f"  • {file_type}: {file_path}")


if __name__ == "__main__":
    main()
