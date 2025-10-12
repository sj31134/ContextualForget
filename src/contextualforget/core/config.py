"""프로덕션 환경 설정 관리."""

import json
import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class DatabaseConfig:
    """데이터베이스 설정."""
    host: str = "localhost"
    port: int = 5432
    database: str = "contextualforget"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class CacheConfig:
    """캐시 설정."""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    cache_ttl: int = 3600  # 1시간
    max_cache_size: int = 1000


@dataclass
class LoggingConfig:
    """로깅 설정."""
    level: str = "INFO"
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class PerformanceConfig:
    """성능 설정."""
    max_workers: int = 4
    chunk_size: int = 1000
    memory_limit_mb: int = 1024
    query_timeout: int = 30
    batch_size: int = 100


@dataclass
class SecurityConfig:
    """보안 설정."""
    secret_key: str = ""
    allowed_hosts: list = None
    cors_origins: list = None
    rate_limit: int = 100  # requests per minute
    
    def __post_init__(self):
        if self.allowed_hosts is None:
            self.allowed_hosts = ["localhost", "127.0.0.1"]
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]


@dataclass
class MonitoringConfig:
    """모니터링 설정."""
    enabled: bool = True
    collection_interval: int = 60
    metrics_retention_hours: int = 24
    health_check_interval: int = 30
    alert_thresholds: dict[str, float] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "cpu_percent": 80.0,
                "memory_percent": 85.0,
                "disk_usage_percent": 90.0,
                "query_avg_time": 5.0
            }


class Config:
    """전체 설정 관리 클래스."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.database = DatabaseConfig()
        self.cache = CacheConfig()
        self.logging = LoggingConfig()
        self.performance = PerformanceConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        
        # 환경 변수에서 설정 로드
        self._load_from_env()
        
        # 설정 파일에서 로드 (있는 경우)
        if config_file and Path(config_file).exists():
            self._load_from_file(config_file)
    
    def _load_from_env(self):
        """환경 변수에서 설정 로드."""
        # 데이터베이스 설정
        self.database.host = os.getenv("DB_HOST", self.database.host)
        self.database.port = int(os.getenv("DB_PORT", self.database.port))
        self.database.database = os.getenv("DB_NAME", self.database.database)
        self.database.username = os.getenv("DB_USER", self.database.username)
        self.database.password = os.getenv("DB_PASSWORD", self.database.password)
        
        # 캐시 설정
        self.cache.redis_host = os.getenv("REDIS_HOST", self.cache.redis_host)
        self.cache.redis_port = int(os.getenv("REDIS_PORT", self.cache.redis_port))
        self.cache.redis_password = os.getenv("REDIS_PASSWORD", self.cache.redis_password)
        
        # 로깅 설정
        self.logging.level = os.getenv("LOG_LEVEL", self.logging.level)
        self.logging.log_file = os.getenv("LOG_FILE", self.logging.log_file)
        
        # 성능 설정
        self.performance.max_workers = int(os.getenv("MAX_WORKERS", self.performance.max_workers))
        self.performance.chunk_size = int(os.getenv("CHUNK_SIZE", self.performance.chunk_size))
        self.performance.memory_limit_mb = int(os.getenv("MEMORY_LIMIT_MB", self.performance.memory_limit_mb))
        
        # 보안 설정
        self.security.secret_key = os.getenv("SECRET_KEY", self.security.secret_key)
        
        # 모니터링 설정
        self.monitoring.enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
        self.monitoring.collection_interval = int(os.getenv("MONITORING_INTERVAL", self.monitoring.collection_interval))
    
    def _load_from_file(self, config_file: str):
        """설정 파일에서 로드."""
        try:
            with Path(config_file).open() as f:
                config_data = json.load(f)
            
            # 각 섹션별로 설정 업데이트
            if "database" in config_data:
                for key, value in config_data["database"].items():
                    if hasattr(self.database, key):
                        setattr(self.database, key, value)
            
            if "cache" in config_data:
                for key, value in config_data["cache"].items():
                    if hasattr(self.cache, key):
                        setattr(self.cache, key, value)
            
            if "logging" in config_data:
                for key, value in config_data["logging"].items():
                    if hasattr(self.logging, key):
                        setattr(self.logging, key, value)
            
            if "performance" in config_data:
                for key, value in config_data["performance"].items():
                    if hasattr(self.performance, key):
                        setattr(self.performance, key, value)
            
            if "security" in config_data:
                for key, value in config_data["security"].items():
                    if hasattr(self.security, key):
                        setattr(self.security, key, value)
            
            if "monitoring" in config_data:
                for key, value in config_data["monitoring"].items():
                    if hasattr(self.monitoring, key):
                        setattr(self.monitoring, key, value)
        
        except Exception as e:
            print(f"Warning: Failed to load config file {config_file}: {e}")
    
    def save_to_file(self, config_file: str):
        """설정을 파일로 저장."""
        config_data = {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "username": self.database.username,
                "password": self.database.password,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow
            },
            "cache": {
                "redis_host": self.cache.redis_host,
                "redis_port": self.cache.redis_port,
                "redis_db": self.cache.redis_db,
                "redis_password": self.cache.redis_password,
                "cache_ttl": self.cache.cache_ttl,
                "max_cache_size": self.cache.max_cache_size
            },
            "logging": {
                "level": self.logging.level,
                "log_file": self.logging.log_file,
                "max_file_size": self.logging.max_file_size,
                "backup_count": self.logging.backup_count,
                "format": self.logging.format
            },
            "performance": {
                "max_workers": self.performance.max_workers,
                "chunk_size": self.performance.chunk_size,
                "memory_limit_mb": self.performance.memory_limit_mb,
                "query_timeout": self.performance.query_timeout,
                "batch_size": self.performance.batch_size
            },
            "security": {
                "secret_key": self.security.secret_key,
                "allowed_hosts": self.security.allowed_hosts,
                "cors_origins": self.security.cors_origins,
                "rate_limit": self.security.rate_limit
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "collection_interval": self.monitoring.collection_interval,
                "metrics_retention_hours": self.monitoring.metrics_retention_hours,
                "health_check_interval": self.monitoring.health_check_interval,
                "alert_thresholds": self.monitoring.alert_thresholds
            }
        }
        
        with Path(config_file).open('w') as f:
            json.dump(config_data, f, indent=2)
    
    def validate(self) -> dict[str, Any]:
        """설정 유효성 검사."""
        errors = []
        warnings = []
        
        # 필수 설정 검사
        if not self.security.secret_key:
            errors.append("SECRET_KEY is required for production")
        
        if self.database.password == "":
            warnings.append("Database password is empty")
        
        if self.performance.max_workers > 8:
            warnings.append("High number of workers may cause resource issues")
        
        if self.performance.memory_limit_mb < 512:
            warnings.append("Low memory limit may cause performance issues")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_environment(self) -> str:
        """현재 환경 반환 (development, staging, production)."""
        return os.getenv("ENVIRONMENT", "development")
    
    def is_production(self) -> bool:
        """프로덕션 환경 여부."""
        return self.get_environment() == "production"
    
    def is_development(self) -> bool:
        """개발 환경 여부."""
        return self.get_environment() == "development"


# 전역 설정 인스턴스
config = Config()


def get_config() -> Config:
    """설정 인스턴스 반환."""
    return config


def load_config(config_file: str) -> Config:
    """설정 파일에서 새로운 설정 인스턴스 생성."""
    return Config(config_file)
