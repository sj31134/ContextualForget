"""로깅 및 모니터링 시스템."""

import logging
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import psutil


class ContextualForgetLogger:
    """ContextualForget 전용 로거 클래스."""
    
    def __init__(self, name: str = "contextualforget", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # 로그 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 파일 핸들러 (선택사항)
        log_file = os.getenv('CONTEXTUALFORGET_LOG_FILE')
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """정보 로그."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """경고 로그."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """오류 로그."""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """디버그 로그."""
        self.logger.debug(message, extra=kwargs)


class PerformanceMonitor:
    """성능 모니터링 클래스."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
    
    def record_metric(self, name: str, value: float, unit: str = ""):
        """메트릭 기록."""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """시스템 메트릭 수집."""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """메트릭 요약."""
        summary = {}
        for name, values in self.metrics.items():
            if values:
                summary[name] = {
                    "count": len(values),
                    "min": min(v["value"] for v in values),
                    "max": max(v["value"] for v in values),
                    "avg": sum(v["value"] for v in values) / len(values),
                    "latest": values[-1]["value"]
                }
        return summary


def log_execution_time(logger: ContextualForgetLogger):
    """함수 실행 시간을 로깅하는 데코레이터."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"Function {func.__name__} executed successfully",
                    execution_time=execution_time,
                    function_name=func.__name__
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function {func.__name__} failed",
                    execution_time=execution_time,
                    error=str(e),
                    function_name=func.__name__
                )
                raise
        return wrapper
    return decorator


def log_graph_operations(logger: ContextualForgetLogger):
    """그래프 작업을 로깅하는 데코레이터."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 그래프 정보 추출
            graph = None
            for arg in args:
                if hasattr(arg, 'nodes') and hasattr(arg, 'edges'):
                    graph = arg
                    break
            
            if graph:
                logger.info(
                    f"Graph operation: {func.__name__}",
                    nodes_count=graph.number_of_nodes(),
                    edges_count=graph.number_of_edges(),
                    function_name=func.__name__
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class QueryLogger:
    """쿼리 실행 로깅 클래스."""
    
    def __init__(self, logger: ContextualForgetLogger):
        self.logger = logger
        self.query_count = 0
    
    def log_query(self, query_type: str, parameters: Dict[str, Any], 
                  result_count: int, execution_time: float):
        """쿼리 실행 로그."""
        self.query_count += 1
        self.logger.info(
            f"Query executed: {query_type}",
            query_id=self.query_count,
            query_type=query_type,
            parameters=parameters,
            result_count=result_count,
            execution_time=execution_time
        )
    
    def log_query_error(self, query_type: str, parameters: Dict[str, Any], 
                       error: str, execution_time: float):
        """쿼리 오류 로그."""
        self.logger.error(
            f"Query failed: {query_type}",
            query_type=query_type,
            parameters=parameters,
            error=error,
            execution_time=execution_time
        )


class DataPipelineLogger:
    """데이터 파이프라인 로깅 클래스."""
    
    def __init__(self, logger: ContextualForgetLogger):
        self.logger = logger
    
    def log_pipeline_start(self, pipeline_name: str, input_files: list):
        """파이프라인 시작 로그."""
        self.logger.info(
            f"Pipeline started: {pipeline_name}",
            pipeline_name=pipeline_name,
            input_files=input_files,
            start_time=datetime.now().isoformat()
        )
    
    def log_pipeline_step(self, step_name: str, input_count: int, 
                         output_count: int, processing_time: float):
        """파이프라인 단계 로그."""
        self.logger.info(
            f"Pipeline step completed: {step_name}",
            step_name=step_name,
            input_count=input_count,
            output_count=output_count,
            processing_time=processing_time
        )
    
    def log_pipeline_complete(self, pipeline_name: str, total_time: float, 
                             output_files: list):
        """파이프라인 완료 로그."""
        self.logger.info(
            f"Pipeline completed: {pipeline_name}",
            pipeline_name=pipeline_name,
            total_time=total_time,
            output_files=output_files,
            end_time=datetime.now().isoformat()
        )
    
    def log_pipeline_error(self, pipeline_name: str, step_name: str, 
                          error: str, processing_time: float):
        """파이프라인 오류 로그."""
        self.logger.error(
            f"Pipeline failed: {pipeline_name} at step {step_name}",
            pipeline_name=pipeline_name,
            step_name=step_name,
            error=error,
            processing_time=processing_time
        )


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """로깅 시스템 초기 설정."""
    if log_file:
        os.environ['CONTEXTUALFORGET_LOG_FILE'] = log_file
    
    logger = ContextualForgetLogger(level=level)
    logger.info("ContextualForget logging system initialized")
    return logger


def get_logger(name: str = "contextualforget") -> ContextualForgetLogger:
    """로거 인스턴스 반환."""
    return ContextualForgetLogger(name)


# 전역 로거 인스턴스
default_logger = get_logger()
performance_monitor = PerformanceMonitor()
query_logger = QueryLogger(default_logger)
pipeline_logger = DataPipelineLogger(default_logger)
