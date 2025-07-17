"""
Core Platform Service

This service provides foundational infrastructure and platform capabilities including:
- Configuration management and environment handling
- Service discovery and registration
- Health monitoring and system diagnostics
- Centralized logging and error tracking
- Caching and performance optimization
- System orchestration and coordination
- Security and access control
- Data persistence and backup

Performance Targets:
- Service startup completes within 30 seconds
- 99.9%+ uptime and availability
- Sub-second response times for core operations
- Comprehensive system monitoring and alerting
"""

import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import uuid
import hashlib
import asyncio
from contextlib import contextmanager
import yaml
import redis
import psutil
import requests
from concurrent.futures import ThreadPoolExecutor
import schedule

from structlog import get_logger

logger = get_logger()


class ServiceStatus(Enum):
    """Service status enumeration."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DEGRADED = "degraded"


class ServiceType(Enum):
    """Service type enumeration."""
    CORE = "core"
    API = "api"
    WORKER = "worker"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL = "external"


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    """Represents service information."""
    service_id: str
    name: str
    service_type: ServiceType
    status: ServiceStatus
    version: str
    host: str
    port: int
    health_endpoint: Optional[str] = None
    metadata: Dict[str, Any] = None
    last_heartbeat: Optional[datetime] = None
    created_at: datetime = None


@dataclass
class SystemMetrics:
    """Represents system performance metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    response_time: float
    error_rate: float
    timestamp: datetime


@dataclass
class Configuration:
    """Represents system configuration."""
    environment: str
    debug_mode: bool
    log_level: str
    database_url: str
    redis_url: str
    api_host: str
    api_port: int
    max_workers: int
    cache_ttl: int
    health_check_interval: int
    backup_interval: int
    security_settings: Dict[str, Any]
    feature_flags: Dict[str, bool]


class CorePlatformService:
    """
    Core platform service providing foundational infrastructure.
    
    This service provides essential platform capabilities including configuration
    management, service discovery, health monitoring, logging, caching, and
    system orchestration.
    """
    
    def __init__(self, config_path: str = "config/platform.yaml"):
        """
        Initialize the core platform service.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_configuration()
        self.services: Dict[str, ServiceInfo] = {}
        self.metrics: List[SystemMetrics] = []
        self.cache = {}
        self.lock = threading.RLock()
        self.running = True
        
        # Initialize components
        self._init_database()
        self._init_logging()
        self._init_cache()
        self._init_health_monitoring()
        
        # Performance metrics
        self.startup_time = datetime.now()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("Core Platform Service initialized successfully")
    
    def _load_configuration(self) -> Configuration:
        """Load configuration from file or use defaults."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            else:
                config_data = {}
            
            return Configuration(
                environment=config_data.get('environment', 'development'),
                debug_mode=config_data.get('debug_mode', False),
                log_level=config_data.get('log_level', 'INFO'),
                database_url=config_data.get('database_url', 'sqlite:///platform.db'),
                redis_url=config_data.get('redis_url', 'redis://localhost:6379'),
                api_host=config_data.get('api_host', 'localhost'),
                api_port=config_data.get('api_port', 8000),
                max_workers=config_data.get('max_workers', 10),
                cache_ttl=config_data.get('cache_ttl', 3600),
                health_check_interval=config_data.get('health_check_interval', 30),
                backup_interval=config_data.get('backup_interval', 3600),
                security_settings=config_data.get('security_settings', {}),
                feature_flags=config_data.get('feature_flags', {})
            )
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Return default configuration
            return Configuration(
                environment='development',
                debug_mode=False,
                log_level='INFO',
                database_url='sqlite:///platform.db',
                redis_url='redis://localhost:6379',
                api_host='localhost',
                api_port=8000,
                max_workers=10,
                cache_ttl=3600,
                health_check_interval=30,
                backup_interval=3600,
                security_settings={},
                feature_flags={}
            )
    
    def _init_database(self) -> None:
        """Initialize database connection and tables."""
        try:
            db_path = self.config.database_url.replace('sqlite:///', '')
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create services table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS services (
                        service_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        service_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        version TEXT NOT NULL,
                        host TEXT NOT NULL,
                        port INTEGER NOT NULL,
                        health_endpoint TEXT,
                        metadata TEXT,
                        last_heartbeat TEXT,
                        created_at TEXT NOT NULL
                    )
                ''')
                
                # Create metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cpu_usage REAL NOT NULL,
                        memory_usage REAL NOT NULL,
                        disk_usage REAL NOT NULL,
                        network_io TEXT NOT NULL,
                        active_connections INTEGER NOT NULL,
                        response_time REAL NOT NULL,
                        error_rate REAL NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                ''')
                
                # Create cache table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        ttl INTEGER,
                        created_at TEXT NOT NULL
                    )
                ''')
                
                conn.commit()
                
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _init_logging(self) -> None:
        """Initialize logging configuration."""
        try:
            # Configure structlog
            import structlog
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
            
            logger.info("Logging initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize logging: {e}")
    
    def _init_cache(self) -> None:
        """Initialize cache system."""
        try:
            # Try to connect to Redis
            if self.config.redis_url != 'redis://localhost:6379':
                self.redis_client = redis.from_url(self.config.redis_url)
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Redis cache initialized successfully")
            else:
                self.use_redis = False
                logger.info("Using in-memory cache")
                
        except Exception as e:
            self.use_redis = False
            logger.warning(f"Redis not available, using in-memory cache: {e}")
    
    def _init_health_monitoring(self) -> None:
        """Initialize health monitoring system."""
        try:
            self.health_check_interval = self.config.health_check_interval
            self.last_health_check = datetime.now()
            
            logger.info("Health monitoring initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize health monitoring: {e}")
    
    def _register_core_services(self) -> None:
        """Register core platform services."""
        core_services = [
            {
                'service_id': 'platform-core',
                'name': 'Core Platform',
                'service_type': ServiceType.CORE,
                'version': '1.0.0',
                'host': self.config.api_host,
                'port': self.config.api_port,
                'health_endpoint': '/health'
            },
            {
                'service_id': 'platform-database',
                'name': 'Database Service',
                'service_type': ServiceType.DATABASE,
                'version': '1.0.0',
                'host': 'localhost',
                'port': 5432,
                'health_endpoint': '/db/health'
            },
            {
                'service_id': 'platform-cache',
                'name': 'Cache Service',
                'service_type': ServiceType.CACHE,
                'version': '1.0.0',
                'host': 'localhost',
                'port': 6379,
                'health_endpoint': '/cache/health'
            }
        ]
        
        for service_data in core_services:
            service = ServiceInfo(
                service_id=service_data['service_id'],
                name=service_data['name'],
                service_type=service_data['service_type'],
                status=ServiceStatus.RUNNING,
                version=service_data['version'],
                host=service_data['host'],
                port=service_data['port'],
                health_endpoint=service_data['health_endpoint'],
                metadata={},
                last_heartbeat=datetime.now(),
                created_at=datetime.now()
            )
            
            self.services[service.service_id] = service
            self._save_service_info(service)
    
    def _start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        try:
            # Start health monitoring thread
            self.health_thread = threading.Thread(
                target=self._health_monitoring_worker,
                daemon=True
            )
            self.health_thread.start()
            
            # Start metrics collection thread
            self.metrics_thread = threading.Thread(
                target=self._metrics_collection_worker,
                daemon=True
            )
            self.metrics_thread.start()
            
            # Start cache cleanup thread
            self.cache_thread = threading.Thread(
                target=self._cache_cleanup_worker,
                daemon=True
            )
            self.cache_thread.start()
            
            # Register core services
            self._register_core_services()
            
            logger.info("Background tasks started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
    
    def _health_monitoring_worker(self) -> None:
        """Background worker for health monitoring."""
        while self.running:
            try:
                self._perform_health_checks()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(10)
    
    def _metrics_collection_worker(self) -> None:
        """Background worker for metrics collection."""
        while self.running:
            try:
                self._collect_system_metrics()
                time.sleep(60)  # Collect metrics every minute
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(60)
    
    def _cache_cleanup_worker(self) -> None:
        """Background worker for cache cleanup."""
        while self.running:
            try:
                self._cleanup_expired_cache()
                time.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                time.sleep(300)
    
    def _perform_health_checks(self) -> None:
        """Perform health checks on all registered services."""
        try:
            with self.lock:
                for service_id, service in self.services.items():
                    if service.service_type != ServiceType.CORE:
                        health_status = self._check_service_health(service)
                        
                        if health_status == HealthStatus.UNHEALTHY:
                            service.status = ServiceStatus.ERROR
                        elif health_status == HealthStatus.DEGRADED:
                            service.status = ServiceStatus.DEGRADED
                        else:
                            service.status = ServiceStatus.RUNNING
                        
                        service.last_heartbeat = datetime.now()
                        self._save_service_info(service)
            
            self.last_health_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    def _check_service_health(self, service: ServiceInfo) -> HealthStatus:
        """Check health of a specific service."""
        try:
            if not service.health_endpoint:
                return HealthStatus.UNKNOWN
            
            url = f"http://{service.host}:{service.port}{service.health_endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return HealthStatus.HEALTHY
            elif response.status_code in [429, 503]:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.UNHEALTHY
                
        except Exception as e:
            logger.warning(f"Health check failed for {service.service_id}: {e}")
            return HealthStatus.UNHEALTHY
    
    def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Active connections
            active_connections = len(psutil.net_connections())
            
            # Response time (simplified)
            response_time = self.average_response_time
            
            # Error rate
            if self.total_requests > 0:
                error_rate = (self.failed_requests / self.total_requests) * 100
            else:
                error_rate = 0.0
            
            metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=active_connections,
                response_time=response_time,
                error_rate=error_rate,
                timestamp=datetime.now()
            )
            
            self.metrics.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
            
            self._save_system_metrics(metrics)
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def _cleanup_expired_cache(self) -> None:
        """Clean up expired cache entries."""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for key, (value, ttl, created_at) in self.cache.items():
                if ttl and (current_time - created_at).total_seconds() > ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
    
    def _save_service_info(self, service: ServiceInfo) -> None:
        """Save service information to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO services 
                    (service_id, name, service_type, status, version, host, port, 
                     health_endpoint, metadata, last_heartbeat, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    service.service_id,
                    service.name,
                    service.service_type.value,
                    service.status.value,
                    service.version,
                    service.host,
                    service.port,
                    service.health_endpoint,
                    json.dumps(service.metadata or {}),
                    service.last_heartbeat.isoformat() if service.last_heartbeat else None,
                    service.created_at.isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save service info: {e}")
    
    def _save_system_metrics(self, metrics: SystemMetrics) -> None:
        """Save system metrics to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO system_metrics 
                    (cpu_usage, memory_usage, disk_usage, network_io, 
                     active_connections, response_time, error_rate, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.cpu_usage,
                    metrics.memory_usage,
                    metrics.disk_usage,
                    json.dumps(metrics.network_io),
                    metrics.active_connections,
                    metrics.response_time,
                    metrics.error_rate,
                    metrics.timestamp.isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save system metrics: {e}")
    
    def register_service(self, service_info: ServiceInfo) -> bool:
        """Register a new service."""
        try:
            with self.lock:
                if service_info.service_id in self.services:
                    logger.warning(f"Service {service_info.service_id} already registered")
                    return False
                
                self.services[service_info.service_id] = service_info
                self._save_service_info(service_info)
                
                logger.info(f"Service {service_info.service_id} registered successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            return False
    
    def unregister_service(self, service_id: str) -> bool:
        """Unregister a service."""
        try:
            with self.lock:
                if service_id not in self.services:
                    logger.warning(f"Service {service_id} not found")
                    return False
                
                del self.services[service_id]
                
                # Remove from database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM services WHERE service_id = ?', (service_id,))
                    conn.commit()
                
                logger.info(f"Service {service_id} unregistered successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to unregister service: {e}")
            return False
    
    def get_service_info(self, service_id: str) -> Optional[ServiceInfo]:
        """Get service information."""
        try:
            with self.lock:
                return self.services.get(service_id)
                
        except Exception as e:
            logger.error(f"Failed to get service info: {e}")
            return None
    
    def list_services(self, service_type: Optional[ServiceType] = None) -> List[ServiceInfo]:
        """List all services, optionally filtered by type."""
        try:
            with self.lock:
                if service_type:
                    return [s for s in self.services.values() if s.service_type == service_type]
                else:
                    return list(self.services.values())
                    
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            with self.lock:
                total_services = len(self.services)
                healthy_services = len([s for s in self.services.values() if s.status == ServiceStatus.RUNNING])
                degraded_services = len([s for s in self.services.values() if s.status == ServiceStatus.DEGRADED])
                error_services = len([s for s in self.services.values() if s.status == ServiceStatus.ERROR])
                
                uptime = (datetime.now() - self.startup_time).total_seconds()
                
                return {
                    'status': 'healthy' if error_services == 0 else 'degraded' if degraded_services > 0 else 'unhealthy',
                    'total_services': total_services,
                    'healthy_services': healthy_services,
                    'degraded_services': degraded_services,
                    'error_services': error_services,
                    'uptime_seconds': uptime,
                    'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {'status': 'unknown', 'error': str(e)}
    
    def get_system_metrics(self, limit: int = 100) -> List[SystemMetrics]:
        """Get recent system metrics."""
        try:
            with self.lock:
                return self.metrics[-limit:] if self.metrics else []
                
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return []
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.use_redis:
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            else:
                if key in self.cache:
                    value, ttl, created_at = self.cache[key]
                    if not ttl or (datetime.now() - created_at).total_seconds() <= ttl:
                        return value
                    else:
                        del self.cache[key]
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            if self.use_redis:
                if ttl:
                    self.redis_client.setex(key, ttl, json.dumps(value))
                else:
                    self.redis_client.set(key, json.dumps(value))
            else:
                self.cache[key] = (value, ttl, datetime.now())
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def cache_delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if self.use_redis:
                self.redis_client.delete(key)
            else:
                if key in self.cache:
                    del self.cache[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def get_configuration(self) -> Configuration:
        """Get current configuration."""
        return self.config
    
    def update_configuration(self, updates: Dict[str, Any]) -> bool:
        """Update configuration."""
        try:
            # Update config object
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # Save to file
            config_data = asdict(self.config)
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if self.use_redis:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            else:
                return {
                    'type': 'memory',
                    'total_entries': len(self.cache),
                    'memory_usage': 'unknown'
                }
                
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'type': 'unknown', 'error': str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        try:
            return {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'average_response_time': self.average_response_time,
                'uptime_seconds': (datetime.now() - self.startup_time).total_seconds(),
                'active_services': len([s for s in self.services.values() if s.status == ServiceStatus.RUNNING])
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}
    
    def shutdown(self) -> None:
        """Shutdown the core platform service."""
        try:
            self.running = False
            
            # Wait for background threads to finish
            if hasattr(self, 'health_thread'):
                self.health_thread.join(timeout=5)
            if hasattr(self, 'metrics_thread'):
                self.metrics_thread.join(timeout=5)
            if hasattr(self, 'cache_thread'):
                self.cache_thread.join(timeout=5)
            
            logger.info("Core Platform Service shutdown successfully")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.shutdown() 