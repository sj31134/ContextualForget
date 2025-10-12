import json
import signal
import time
from pathlib import Path
from typing import List, Optional

import typer

from ..core import get_health_status, get_logger, get_metrics_summary, start_monitoring
from ..llm import LLMQueryEngine, NaturalLanguageProcessor
from ..query import AdvancedQueryEngine, QueryBuilder, find_by_guid
from ..realtime import RealtimeMonitor
from ..visualization import GraphVisualizer, create_visualization_report

app = typer.Typer()

# 로깅 시스템 초기화
logger = get_logger("contextualforget.cli")

def load_graph(graph_path: str):
    """Load graph from file."""
    import pickle
    with Path(graph_path).open('rb') as f:
        return pickle.load(f)

@app.command()
def query(
    guid: str,
    ttl: int = 365,
    topk: int = 5,
    graph: str = "data/processed/graph.gpickle"
):
    """Query BCF topics related to an IFC GUID."""
    G = load_graph(graph)
    hits = find_by_guid(G, guid, ttl=ttl)[:topk]
    out = [{
        "topic_id": n[1],
        "created": d.get("created"),
        "edge": {"type": e.get("type"), "confidence": e.get("confidence")}
    } for n, d, e in hits]
    typer.echo(json.dumps(out, indent=2, ensure_ascii=False))

@app.command()
def search(
    keywords: list[str] = typer.Argument(help="Keywords to search for"),
    ttl: int = 365,
    topk: int = 10,
    graph: str = "data/processed/graph.gpickle"
):
    """Search BCF topics by keywords."""
    G = load_graph(graph)
    engine = AdvancedQueryEngine(G)
    results = engine.find_by_keywords(keywords, ttl=ttl)[:topk]
    typer.echo(json.dumps(results, indent=2, ensure_ascii=False))

@app.command()
def author(
    author_name: str = typer.Argument(..., help="Author name to search for"),
    ttl: int = 365,
    topk: int = 10,
    graph: str = "data/processed/graph.gpickle"
):
    """Find BCF topics by author."""
    G = load_graph(graph)
    engine = AdvancedQueryEngine(G)
    results = engine.find_by_author(author_name, ttl=ttl)[:topk]
    typer.echo(json.dumps(results, indent=2, ensure_ascii=False))

@app.command()
def timeline(
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    graph: str = "data/processed/graph.gpickle"
):
    """Find BCF topics within a time range."""
    G = load_graph(graph)
    engine = AdvancedQueryEngine(G)
    results = engine.find_by_time_range(start_date, end_date)
    typer.echo(json.dumps(results, indent=2, ensure_ascii=False))

@app.command()
def connected(
    guid: str = typer.Argument(..., help="IFC GUID to analyze"),
    max_depth: int = 2,
    graph: str = "data/processed/graph.gpickle"
):
    """Find all entities connected to a GUID."""
    G = load_graph(graph)
    engine = AdvancedQueryEngine(G)
    results = engine.find_connected_components(guid, max_depth)
    typer.echo(json.dumps(results, indent=2, ensure_ascii=False))

@app.command()
def stats(
    graph: str = "data/processed/graph.gpickle"
):
    """Get graph statistics."""
    logger.info("Retrieving graph statistics")
    G = load_graph(graph)
    engine = AdvancedQueryEngine(G)
    results = engine.get_statistics()
    typer.echo(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info("Graph statistics retrieved successfully")


@app.command()
def health():
    """Show system health status."""
    logger.info("Checking system health")
    health_status = get_health_status()
    typer.echo(json.dumps(health_status, indent=2, ensure_ascii=False))
    logger.info("Health check completed")


@app.command()
def metrics():
    """Show system metrics."""
    logger.info("Retrieving system metrics")
    metrics = get_metrics_summary()
    typer.echo(json.dumps(metrics, indent=2, ensure_ascii=False))
    logger.info("Metrics retrieved successfully")


@app.command()
def start_monitor():
    """Start system monitoring."""
    logger.info("Starting system monitoring")
    start_monitoring()
    typer.echo("✅ System monitoring started")


@app.command()
def stop_monitor():
    """Stop system monitoring."""
    logger.info("Stopping system monitoring")
    from ..core import stop_monitoring
    stop_monitoring()
    typer.echo("✅ System monitoring stopped")


@app.command()
def ask(
    question: str = typer.Argument(..., help="Natural language question to ask"),
    graph: str = "data/processed/graph.gpickle"
):
    """Ask natural language questions about the graph data."""
    logger.info(f"Processing natural language question: {question}")
    
    try:
        # 그래프 로드
        G = load_graph(graph)
        engine = AdvancedQueryEngine(G)
        
        # 자연어 처리기 초기화
        nlp = NaturalLanguageProcessor()
        llm_engine = LLMQueryEngine(engine, nlp)
        
        # 자연어 질의 처리
        result = llm_engine.process_natural_query(question)
        
        # 결과 출력
        typer.echo("\n🤖 자연어 응답:")
        typer.echo("=" * 50)
        typer.echo(result["natural_response"])
        
        typer.echo("\n📊 분석된 의도:")
        typer.echo(f"  - 유형: {result['intent']['type']}")
        typer.echo(f"  - 신뢰도: {result['intent']['confidence']:.2f}")
        typer.echo(f"  - 추출된 엔티티: {result['intent']['entities']}")
        
        if result['intent']['parameters']:
            typer.echo(f"  - 파라미터: {result['intent']['parameters']}")
        
        logger.info("Natural language question processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing natural language question: {e}")
        typer.echo(f"❌ 오류가 발생했습니다: {e}")


@app.command()
def chat(
    graph: str = "data/processed/graph.gpickle"
):
    """Interactive chat mode for natural language queries."""
    logger.info("Starting interactive chat mode")
    
    try:
        # 그래프 로드
        G = load_graph(graph)
        engine = AdvancedQueryEngine(G)
        
        # 자연어 처리기 초기화
        nlp = NaturalLanguageProcessor()
        llm_engine = LLMQueryEngine(engine, nlp)
        
        typer.echo("🤖 ContextualForget 자연어 챗봇")
        typer.echo("=" * 50)
        
        # 모델 정보 표시
        model_info = nlp.get_model_info()
        if model_info["available"]:
            typer.echo(f"🧠 LLM 모델: {model_info['model_name']} (활성화됨)")
        else:
            typer.echo("🧠 LLM 모델: 정규식 기반 폴백 모드")
        
        typer.echo("자연어로 질문해보세요! (종료: 'quit' 또는 'exit')")
        typer.echo()
        
        while True:
            try:
                question = typer.prompt("질문")
                
                if question.lower() in ['quit', 'exit', '종료']:
                    typer.echo("👋 채팅을 종료합니다.")
                    break
                
                if not question.strip():
                    continue
                
                # 자연어 질의 처리
                result = llm_engine.process_natural_query(question)
                
                # 결과 출력
                typer.echo("\n🤖 응답:")
                typer.echo("-" * 30)
                typer.echo(result["natural_response"])
                typer.echo()
                
            except KeyboardInterrupt:
                typer.echo("\n👋 채팅을 종료합니다.")
                break
            except Exception as e:
                typer.echo(f"❌ 오류: {e}")
                typer.echo()
        
        logger.info("Interactive chat mode ended")
        
    except Exception as e:
        logger.error(f"Error starting chat mode: {e}")
        typer.echo(f"❌ 오류가 발생했습니다: {e}")


@app.command()
def model_info():
    """Show LLM model information and status."""
    try:
        nlp = NaturalLanguageProcessor()
        model_info = nlp.get_model_info()
        
        typer.echo("🧠 LLM 모델 정보")
        typer.echo("=" * 30)
        typer.echo(f"모델 이름: {model_info['model_name']}")
        typer.echo(f"사용 가능: {'✅ 예' if model_info['available'] else '❌ 아니오'}")
        typer.echo(f"폴백 모드: {'✅ 활성화' if model_info['fallback_enabled'] else '❌ 비활성화'}")
        typer.echo(f"Ollama 설치: {'✅ 예' if model_info['ollama_installed'] else '❌ 아니오'}")
        
        if not model_info['available']:
            typer.echo("\n💡 LLM을 사용하려면:")
            typer.echo("1. Ollama가 설치되어 있는지 확인")
            typer.echo("2. 'ollama list'로 모델이 있는지 확인")
            typer.echo("3. 'ollama pull exaone-deep:latest'로 모델 다운로드")
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        typer.echo(f"❌ 오류가 발생했습니다: {e}")


@app.command()
def watch(
    watch_dirs: list[str] = typer.Option(
        default=["data", "data/raw"],
        help="감시할 디렉토리 (여러 개 지정 가능)"
    ),
    graph: str = typer.Option(
        "data/processed/graph.gpickle",
        "--graph",
        "-g",
        help="그래프 파일 경로"
    ),
    processed: str = typer.Option(
        "data/processed",
        "--processed",
        "-p",
        help="처리된 데이터 저장 디렉토리"
    ),
    interval: float = typer.Option(
        2.0,
        "--interval",
        "-i",
        help="폴링 간격 (초)"
    )
):
    """Start real-time file monitoring and auto-update graph."""
    logger.info("Starting real-time monitoring")
    
    try:
        # 실시간 모니터 초기화
        monitor = RealtimeMonitor(
            watch_dirs=[Path(d) for d in watch_dirs],
            graph_path=Path(graph),
            processed_dir=Path(processed),
            poll_interval=interval
        )
        
        # 모니터링 시작
        monitor.start()
        
        typer.echo("📡 실시간 모니터링 시작")
        typer.echo("=" * 60)
        typer.echo(f"감시 디렉토리: {', '.join(watch_dirs)}")
        typer.echo(f"그래프 파일: {graph}")
        typer.echo(f"폴링 간격: {interval}초")
        typer.echo("")
        typer.echo("파일 변경 시 자동으로 그래프가 업데이트됩니다.")
        typer.echo("중지하려면 Ctrl+C를 누르세요.")
        typer.echo("=" * 60)
        
        # Signal handler 설정
        def signal_handler(sig, frame):
            typer.echo("\n\n⏹️  중지 신호 수신")
            monitor.stop()
            typer.echo("\n👋 실시간 모니터링이 종료되었습니다.")
            raise typer.Exit()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 무한 대기
        while monitor.is_running():
            time.sleep(1)
        
    except typer.Exit:
        pass
    except Exception as e:
        logger.error(f"Error in watch command: {e}")
        typer.echo(f"❌ 오류가 발생했습니다: {e}")


@app.command()
def watch_status():
    """Show real-time monitoring status."""
    typer.echo("📊 실시간 모니터링 상태")
    typer.echo("=" * 30)
    typer.echo("현재 실시간 모니터링 기능은 'ctxf watch' 명령어로 시작할 수 있습니다.")
    typer.echo("\n사용법:")
    typer.echo("  ctxf watch                    # 기본 설정으로 시작")
    typer.echo("  ctxf watch -w data -w data/raw -i 5.0  # 커스텀 설정")

@app.command()
def visualize(
    guid: Optional[str] = typer.Option(None, help="Specific GUID to visualize"),
    output_dir: str = "visualizations",
    graph: str = "data/processed/graph.gpickle"
):
    """Create visualization reports."""
    import matplotlib.pyplot as plt
    
    if guid:
        # Visualize specific GUID subgraph
        G = load_graph(graph)
        visualizer = GraphVisualizer(G)
        fig = visualizer.plot_subgraph(guid, save_path=f"{output_dir}/subgraph_{guid[:8]}.png")
        plt.close(fig)
        typer.echo(f"Subgraph visualization saved to {output_dir}/subgraph_{guid[:8]}.png")
    else:
        # Create full visualization report
        create_visualization_report(graph, output_dir)
        typer.echo(f"Full visualization report created in {output_dir}/")

@app.command()
def advanced_query(
    guid: Optional[str] = typer.Option(None, help="IFC GUID"),
    author: Optional[str] = typer.Option(None, help="Author name"),
    keywords: Optional[List[str]] = typer.Option(default=None, help="Keywords"),
    start_date: Optional[str] = typer.Option(None, help="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = typer.Option(None, help="End date (YYYY-MM-DD)"),
    ttl: int = 365,
    sort_by: str = typer.Option("date", help="Sort by: date, confidence"),
    ascending: bool = typer.Option(False, help="Sort ascending"),
    limit: int = 10,
    graph: str = "data/processed/graph.gpickle"
):
    """Advanced query with multiple filters."""
    G = load_graph(graph)
    engine = AdvancedQueryEngine(G)
    builder = QueryBuilder(engine)
    
    # Apply filters
    if guid:
        builder.by_guid(guid)
    if author:
        builder.by_author(author)
    if keywords:
        builder.by_keywords(keywords)
    if start_date and end_date:
        builder.by_time_range(start_date, end_date)
    if ttl > 0:
        builder.with_ttl(ttl)
    
    # Apply sorting
    if sort_by == "date":
        builder.sort_by_date(ascending)
    elif sort_by == "confidence":
        builder.sort_by_confidence(ascending)
    
    # Apply limit
    builder.limit_results(limit)
    
    # Execute query
    results = builder.execute()
    typer.echo(json.dumps(results, indent=2, ensure_ascii=False))


@app.command()
def analytics(
    graph: str = typer.Option("data/processed/graph.gpickle", "--graph", "-g", help="그래프 파일 경로"),
    output: str = typer.Option("analytics", "--output", "-o", help="출력 디렉토리"),
    include_visualizations: bool = typer.Option(True, "--viz/--no-viz", help="시각화 포함 여부")
):
    """그래프 분석 및 통계 생성"""
    try:
        from ..analytics import create_analytics_report
        
        typer.echo("📊 그래프 분석 시작...")
        
        # 분석 보고서 생성
        report = create_analytics_report(graph, output)
        
        # 기본 통계 출력
        basic_stats = report.get("basic_statistics", {})
        typer.echo(f"\n📈 기본 통계:")
        typer.echo(f"  총 노드: {basic_stats.get('total_nodes', 0)}개")
        typer.echo(f"  총 엣지: {basic_stats.get('total_edges', 0)}개")
        typer.echo(f"  IFC 노드: {basic_stats.get('ifc_nodes', 0)}개")
        typer.echo(f"  BCF 노드: {basic_stats.get('bcf_nodes', 0)}개")
        typer.echo(f"  그래프 밀도: {basic_stats.get('density', 0):.3f}")
        
        # 인사이트 출력
        insights = report.get("insights", [])
        if insights:
            typer.echo(f"\n💡 인사이트 ({len(insights)}개):")
            for i, insight in enumerate(insights, 1):
                severity_emoji = {
                    "critical": "🚨",
                    "warning": "⚠️",
                    "info": "ℹ️"
                }.get(insight.get("severity", "info"), "ℹ️")
                
                typer.echo(f"  {i}. {severity_emoji} {insight.get('message', '')}")
                if insight.get("recommendation"):
                    typer.echo(f"     💡 {insight['recommendation']}")
        
        typer.echo(f"\n✅ 분석 완료! 결과는 {output}/ 디렉토리에 저장되었습니다.")
        
    except Exception as e:
        typer.echo(f"❌ 분석 중 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()


@app.command()
def optimize(
    input_graph: str = typer.Option("data/processed/graph.gpickle", "--input", "-i", help="입력 그래프 파일"),
    output_graph: str = typer.Option("data/processed/optimized_graph.gpickle", "--output", "-o", help="출력 그래프 파일"),
    enable_indexing: bool = typer.Option(True, "--index/--no-index", help="인덱싱 활성화"),
    enable_caching: bool = typer.Option(True, "--cache/--no-cache", help="캐싱 활성화"),
    enable_compression: bool = typer.Option(True, "--compress/--no-compress", help="압축 활성화"),
    cache_size: int = typer.Option(1000, "--cache-size", help="캐시 크기")
):
    """그래프 성능 최적화"""
    try:
        from ..optimization import GraphOptimizer, OptimizationConfig
        
        typer.echo("⚡ 그래프 최적화 시작...")
        
        # 최적화 설정
        config = OptimizationConfig(
            enable_indexing=enable_indexing,
            enable_caching=enable_caching,
            enable_compression=enable_compression,
            cache_size=cache_size
        )
        
        # 그래프 로드
        import pickle
        with open(input_graph, 'rb') as f:
            graph = pickle.load(f)
        
        typer.echo(f"원본 그래프: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 엣지")
        
        # 최적화 수행
        optimizer = GraphOptimizer(config)
        optimized_graph = optimizer.optimize_graph(graph)
        
        typer.echo(f"최적화된 그래프: {optimized_graph.number_of_nodes()}개 노드, {optimized_graph.number_of_edges()}개 엣지")
        
        # 최적화된 그래프 저장
        optimizer.save_optimized_graph(optimized_graph, output_graph)
        
        # 통계 출력
        stats = optimizer.get_optimization_stats()
        typer.echo(f"\n📊 최적화 통계:")
        typer.echo(f"  인덱스 구축 시간: {stats.get('index_build_time', 0):.2f}초")
        
        cache_stats = stats.get('cache_stats', {})
        typer.echo(f"  캐시 히트율: {cache_stats.get('hit_rate', 0):.2%}")
        typer.echo(f"  캐시 크기: {cache_stats.get('cache_size', 0)}/{cache_stats.get('max_size', 0)}")
        
        indexer_stats = stats.get('indexer_stats', {})
        typer.echo(f"  GUID 인덱스: {indexer_stats.get('guid_index_size', 0)}개")
        typer.echo(f"  키워드 인덱스: {indexer_stats.get('keyword_index_size', 0)}개")
        
        typer.echo(f"\n✅ 최적화 완료! 결과는 {output_graph}에 저장되었습니다.")
        
    except Exception as e:
        typer.echo(f"❌ 최적화 중 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    app()
