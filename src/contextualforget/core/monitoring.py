"""시스템 모니터링 및 메트릭 수집."""

import json
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from queue import Queue
from typing import Any

import psutil


@dataclass
class SystemMetrics:
    """시스템 메트릭 데이터 클래스."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    process_count: int
    load_average: list[float]


@dataclass
class ApplicationMetrics:
    """애플리케이션 메트릭 데이터 클래스."""
    timestamp: str
    query_count: int
    query_avg_time: float
    graph_nodes: int
    graph_edges: int
    cache_hits: int
    cache_misses: int
    error_count: int
    active_connections: int


class MetricsCollector:
    """메트릭 수집기."""
    
    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.metrics_queue = Queue()
        self.is_running = False
        self.thread = None
        
        # 메트릭 저장소
        self.system_metrics: list[SystemMetrics] = []
        self.application_metrics: list[ApplicationMetrics] = []
        
        # 애플리케이션 카운터
        self.query_count = 0
        self.query_times: list[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.error_count = 0
    
    def start_collection(self):
        """메트릭 수집 시작."""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._collect_metrics_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop_collection(self):
        """메트릭 수집 중지."""
        self.is_running = False
        if self.thread:
            self.thread.join()
    
    def _collect_metrics_loop(self):
        """메트릭 수집 루프."""
        while self.is_running:
            try:
                # 시스템 메트릭 수집
                system_metrics = self._collect_system_metrics()
                self.system_metrics.append(system_metrics)
                
                # 애플리케이션 메트릭 수집
                app_metrics = self._collect_application_metrics()
                self.application_metrics.append(app_metrics)
                
                # 오래된 메트릭 정리 (24시간 이상)
                self._cleanup_old_metrics()
                
                time.sleep(self.collection_interval)
            except Exception as e:
                print(f"Error collecting metrics: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """시스템 메트릭 수집."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            disk_usage_percent=disk.percent,
            disk_free_gb=disk.free / 1024 / 1024 / 1024,
            process_count=len(psutil.pids()),
            load_average=psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        )
    
    def _collect_application_metrics(self) -> ApplicationMetrics:
        """애플리케이션 메트릭 수집."""
        avg_query_time = 0
        if self.query_times:
            avg_query_time = sum(self.query_times) / len(self.query_times)
        
        return ApplicationMetrics(
            timestamp=datetime.now().isoformat(),
            query_count=self.query_count,
            query_avg_time=avg_query_time,
            graph_nodes=0,  # 그래프에서 가져와야 함
            graph_edges=0,  # 그래프에서 가져와야 함
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
            error_count=self.error_count,
            active_connections=0  # 필요시 구현
        )
    
    def _cleanup_old_metrics(self):
        """오래된 메트릭 정리."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # 시스템 메트릭 정리
        self.system_metrics = [
            m for m in self.system_metrics 
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        # 애플리케이션 메트릭 정리
        self.application_metrics = [
            m for m in self.application_metrics 
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
    
    def record_query(self, execution_time: float):
        """쿼리 실행 기록."""
        self.query_count += 1
        self.query_times.append(execution_time)
        
        # 최근 100개 쿼리 시간만 유지
        if len(self.query_times) > 100:
            self.query_times = self.query_times[-100:]
    
    def record_cache_hit(self):
        """캐시 히트 기록."""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """캐시 미스 기록."""
        self.cache_misses += 1
    
    def record_error(self):
        """오류 기록."""
        self.error_count += 1
    
    def get_metrics_summary(self) -> dict[str, Any]:
        """메트릭 요약 반환."""
        if not self.system_metrics or not self.application_metrics:
            return {"error": "No metrics available"}
        
        latest_system = self.system_metrics[-1]
        latest_app = self.application_metrics[-1]
        
        return {
            "system": {
                "cpu_percent": latest_system.cpu_percent,
                "memory_percent": latest_system.memory_percent,
                "memory_used_mb": latest_system.memory_used_mb,
                "disk_usage_percent": latest_system.disk_usage_percent,
                "process_count": latest_system.process_count
            },
            "application": {
                "query_count": latest_app.query_count,
                "query_avg_time": latest_app.query_avg_time,
                "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
                "error_count": latest_app.error_count
            },
            "collection_info": {
                "system_metrics_count": len(self.system_metrics),
                "application_metrics_count": len(self.application_metrics),
                "collection_interval": self.collection_interval
            }
        }
    
    def export_metrics(self, filepath: str):
        """메트릭을 파일로 내보내기."""
        data = {
            "system_metrics": [asdict(m) for m in self.system_metrics],
            "application_metrics": [asdict(m) for m in self.application_metrics],
            "export_timestamp": datetime.now().isoformat()
        }
        
        with Path(filepath).open('w') as f:
            json.dump(data, f, indent=2)
    
    def get_metrics_history(self, hours: int = 24) -> dict[str, list[dict]]:
        """지정된 시간 범위의 메트릭 히스토리 반환."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        system_history = [
            asdict(m) for m in self.system_metrics 
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        app_history = [
            asdict(m) for m in self.application_metrics 
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        return {
            "system_metrics": system_history,
            "application_metrics": app_history
        }


class HealthChecker:
    """시스템 상태 체크 클래스."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.health_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "query_avg_time": 5.0,  # 5초
            "error_rate": 0.1  # 10%
        }
    
    def check_health(self) -> dict[str, Any]:
        """시스템 상태 체크."""
        summary = self.metrics_collector.get_metrics_summary()
        
        if "error" in summary:
            return {"status": "unknown", "message": summary["error"]}
        
        system = summary["system"]
        application = summary["application"]
        
        issues = []
        warnings = []
        
        # CPU 체크
        if system["cpu_percent"] > self.health_thresholds["cpu_percent"]:
            issues.append(f"High CPU usage: {system['cpu_percent']:.1f}%")
        
        # 메모리 체크
        if system["memory_percent"] > self.health_thresholds["memory_percent"]:
            issues.append(f"High memory usage: {system['memory_percent']:.1f}%")
        
        # 디스크 체크
        if system["disk_usage_percent"] > self.health_thresholds["disk_usage_percent"]:
            issues.append(f"High disk usage: {system['disk_usage_percent']:.1f}%")
        
        # 쿼리 성능 체크
        if application["query_avg_time"] > self.health_thresholds["query_avg_time"]:
            warnings.append(f"Slow query performance: {application['query_avg_time']:.2f}s avg")
        
        # 오류율 체크
        total_operations = self.metrics_collector.query_count + self.metrics_collector.error_count
        if total_operations > 0:
            error_rate = self.metrics_collector.error_count / total_operations
            if error_rate > self.health_thresholds["error_rate"]:
                issues.append(f"High error rate: {error_rate:.2%}")
        
        # 상태 결정
        if issues:
            status = "unhealthy"
        elif warnings:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "issues": issues,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat(),
            "metrics": summary
        }


# 전역 메트릭 수집기
metrics_collector = MetricsCollector()
health_checker = HealthChecker(metrics_collector)


def start_monitoring(collection_interval: int = 60):
    """모니터링 시작."""
    metrics_collector.collection_interval = collection_interval
    metrics_collector.start_collection()


def stop_monitoring():
    """모니터링 중지."""
    metrics_collector.stop_collection()


def get_health_status() -> dict[str, Any]:
    """시스템 상태 반환."""
    return health_checker.check_health()


def get_metrics_summary() -> dict[str, Any]:
    """메트릭 요약 반환."""
    return metrics_collector.get_metrics_summary()
