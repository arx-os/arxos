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
        """Initialize database connections and schema."""
        try:
            # Initialize SQLite database for platform data
            self.db_path = "platform.db"
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
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
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        metric_id TEXT PRIMARY KEY,
                        cpu_usage REAL NOT NULL,
                        memory_usage REAL NOT NULL,
                        disk_usage REAL NOT NULL,
                        network_io TEXT NOT NULL,
                        active_connections INTEGER NOT NULL,
                        response_time REAL NOT NULL,
                        error_rate REAL NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS configuration_history (
                        config_id TEXT PRIMARY KEY,
                        environment TEXT NOT NULL,
                        configuration TEXT NOT NULL,
                        applied_at TEXT NOT NULL,
                        applied_by TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS health_checks (
                        check_id TEXT PRIMARY KEY,
                        service_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        response_time REAL,
                        error_message TEXT,
                        timestamp TEXT NOT NULL
                    )
                """)
                
                conn.commit()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _init_logging(self) -> None:
        """Initialize centralized logging system."""
        try:
            # Create logs directory
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Configure logging
            log_level = getattr(logging, self.config.log_level.upper())
            
            # File handler
            file_handler = logging.FileHandler(
                logs_dir / f"platform_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler.setLevel(log_level)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            logger.info("Logging system initialized successfully")
            
        except Exception as e:
            logger.error(f"Logging initialization failed: {e}")
    
    def _init_cache(self) -> None:
        """Initialize caching system."""
        try:
            # Initialize Redis connection if available
            try:
                self.redis_client = redis.from_url(self.config.redis_url)
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis not available, using in-memory cache: {e}")
                self.redis_client = None
            
            # Initialize in-memory cache
            self.memory_cache = {}
            self.cache_stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0
            }
            
        except Exception as e:
            logger.error(f"Cache initialization failed: {e}")
    
    def _init_health_monitoring(self) -> None:
        """Initialize health monitoring system."""
        try:
            self.health_checks = {}
            self.health_status = HealthStatus.HEALTHY
            self.last_health_check = datetime.now()
            
            # Register core services
            self._register_core_services()
            
            logger.info("Health monitoring initialized successfully")
            
        except Exception as e:
            logger.error(f"Health monitoring initialization failed: {e}")
    
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
        """Start background monitoring and maintenance tasks."""
        # Health monitoring thread
        self.health_thread = threading.Thread(
            target=self._health_monitoring_worker,
            daemon=True
        )
        self.health_thread.start()
        
        # Metrics collection thread
        self.metrics_thread = threading.Thread(
            target=self._metrics_collection_worker,
            daemon=True
        )
        self.metrics_thread.start()
        
        # Cache cleanup thread
        self.cache_thread = threading.Thread(
            target=self._cache_cleanup_worker,
            daemon=True
        )
        self.cache_thread.start()
        
        logger.info("Background tasks started successfully")
    
    def _health_monitoring_worker(self) -> None:
        """Background worker for health monitoring."""
        while self.running:
            try:
                self._perform_health_checks()
                time.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(60)  # Wait before retry
    
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
        """Perform health checks for all registered services."""
        healthy_services = 0
        total_services = len(self.services)
        
        for service_id, service in self.services.items():
            try:
                health_status = self._check_service_health(service)
                
                if health_status == HealthStatus.HEALTHY:
                    healthy_services += 1
                
                # Update service status
                if health_status == HealthStatus.UNHEALTHY:
                    service.status = ServiceStatus.ERROR
                elif health_status == HealthStatus.DEGRADED:
                    service.status = ServiceStatus.DEGRADED
                else:
                    service.status = ServiceStatus.RUNNING
                
                service.last_heartbeat = datetime.now()
                self._save_service_info(service)
                
            except Exception as e:
                logger.error(f"Health check failed for {service_id}: {e}")
                service.status = ServiceStatus.ERROR
                self._save_service_info(service)
        
        # Update overall health status
        if healthy_services == total_services:
            self.health_status = HealthStatus.HEALTHY
        elif healthy_services > total_services * 0.5:
            self.health_status = HealthStatus.DEGRADED
        else:
            self.health_status = HealthStatus.UNHEALTHY
        
        self.last_health_check = datetime.now()
    
    def _check_service_health(self, service: ServiceInfo) -> HealthStatus:
        """Check health of a specific service."""
        try:
            if not service.health_endpoint:
                return HealthStatus.UNKNOWN
            
            # Mock health check (in real implementation, this would make HTTP requests)
            if service.service_type == ServiceType.CORE:
                return HealthStatus.HEALTHY
            elif service.service_type == ServiceType.DATABASE:
                # Check database connectivity
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("SELECT 1")
                return HealthStatus.HEALTHY
            elif service.service_type == ServiceType.CACHE:
                # Check cache connectivity
                if self.redis_client:
                    self.redis_client.ping()
                    return HealthStatus.HEALTHY
                else:
                    return HealthStatus.DEGRADED
            else:
                return HealthStatus.UNKNOWN
                
        except Exception as e:
            logger.error(f"Health check failed for {service.service_id}: {e}")
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
            
            # Response time (mock)
            response_time = 0.1  # 100ms average
            
            # Error rate
            total_requests = self.total_requests
            error_rate = (self.failed_requests / total_requests * 100) if total_requests > 0 else 0
            
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
            
            # Save to database
            self._save_system_metrics(metrics)
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
    
    def _cleanup_expired_cache(self) -> None:
        """Clean up expired cache entries."""
        try:
            current_time = time.time()
            expired_keys = []
            
            # Clean in-memory cache
            for key, (value, expiry) in self.memory_cache.items():
                if current_time > expiry:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
                self.cache_stats['deletes'] += 1
            
            # Clean Redis cache if available
            if self.redis_client:
                # Redis handles expiration automatically
                pass
            
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    def _save_service_info(self, service: ServiceInfo) -> None:
        """Save service information to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO services 
                    (service_id, name, service_type, status, version, host, port,
                     health_endpoint, metadata, last_heartbeat, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    service.service_id,
                    service.name,
                    service.service_type.value,
                    service.status.value,
                    service.version,
                    service.host,
                    service.port,
                    service.health_endpoint,
                    json.dumps(service.metadata) if service.metadata else None,
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
                conn.execute("""
                    INSERT INTO system_metrics 
                    (metric_id, cpu_usage, memory_usage, disk_usage, network_io,
                     active_connections, response_time, error_rate, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
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
        """
        Register a new service with the platform.
        
        Args:
            service_info: Service information
            
        Returns:
            True if registration successful
        """
        try:
            with self.lock:
                self.services[service_info.service_id] = service_info
                self._save_service_info(service_info)
                
                logger.info(f"Registered service: {service_info.service_id}")
                return True
                
        except Exception as e:
            logger.error(f"Service registration failed: {e}")
            return False
    
    def unregister_service(self, service_id: str) -> bool:
        """
        Unregister a service from the platform.
        
        Args:
            service_id: Service identifier
            
        Returns:
            True if unregistration successful
        """
        try:
            with self.lock:
                if service_id in self.services:
                    del self.services[service_id]
                    logger.info(f"Unregistered service: {service_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Service unregistration failed: {e}")
            return False
    
    def get_service_info(self, service_id: str) -> Optional[ServiceInfo]:
        """
        Get information about a registered service.
        
        Args:
            service_id: Service identifier
            
        Returns:
            Service information or None if not found
        """
        return self.services.get(service_id)
    
    def list_services(self, service_type: Optional[ServiceType] = None) -> List[ServiceInfo]:
        """
        List all registered services.
        
        Args:
            service_type: Filter by service type
            
        Returns:
            List of service information
        """
        services = list(self.services.values())
        
        if service_type:
            services = [s for s in services if s.service_type == service_type]
        
        return services
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall system health status.
        
        Returns:
            Health status information
        """
        healthy_services = sum(1 for s in self.services.values() if s.status == ServiceStatus.RUNNING)
        total_services = len(self.services)
        
        return {
            'status': self.health_status.value,
            'healthy_services': healthy_services,
            'total_services': total_services,
            'health_percentage': (healthy_services / total_services * 100) if total_services > 0 else 0,
            'last_check': self.last_health_check.isoformat(),
            'uptime': (datetime.now() - self.startup_time).total_seconds()
        }
    
    def get_system_metrics(self, limit: int = 100) -> List[SystemMetrics]:
        """
        Get system performance metrics.
        
        Args:
            limit: Maximum number of metrics to return
            
        Returns:
            List of system metrics
        """
        return self.metrics[-limit:] if self.metrics else []
    
    def cache_get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            # Try Redis first
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats['hits'] += 1
                    return json.loads(value)
            
            # Try in-memory cache
            if key in self.memory_cache:
                value, expiry = self.memory_cache[key]
                if time.time() < expiry:
                    self.cache_stats['hits'] += 1
                    return value
            
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl or self.config.cache_ttl
            expiry = time.time() + ttl
            
            # Set in Redis
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value))
            
            # Set in memory cache
            self.memory_cache[key] = (value, expiry)
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    def cache_delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        try:
            # Delete from Redis
            if self.redis_client:
                self.redis_client.delete(key)
            
            # Delete from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            self.cache_stats['deletes'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    def get_configuration(self) -> Configuration:
        """
        Get current system configuration.
        
        Returns:
            Current configuration
        """
        return self.config
    
    def update_configuration(self, updates: Dict[str, Any]) -> bool:
        """
        Update system configuration.
        
        Args:
            updates: Configuration updates
            
        Returns:
            True if successful
        """
        try:
            # Update configuration
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO configuration_history 
                    (config_id, environment, configuration, applied_at, applied_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    self.config.environment,
                    json.dumps(asdict(self.config)),
                    datetime.now().isoformat(),
                    'system'
                ))
                conn.commit()
            
            logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Cache statistics
        """
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'deletes': self.cache_stats['deletes'],
            'hit_rate': hit_rate,
            'memory_cache_size': len(self.memory_cache),
            'redis_available': self.redis_client is not None
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics.
        
        Returns:
            Performance metrics
        """
        return {
            'uptime_seconds': (datetime.now() - self.startup_time).total_seconds(),
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            'average_response_time': self.average_response_time,
            'registered_services': len(self.services),
            'health_status': self.health_status.value,
            'cache_stats': self.get_cache_stats(),
            'system_metrics': self.metrics[-1].__dict__ if self.metrics else {}
        }
    
    def shutdown(self) -> None:
        """Shutdown the core platform service."""
        logger.info("Shutting down Core Platform Service...")
        
        self.running = False
        
        # Wait for background threads
        if hasattr(self, 'health_thread'):
            self.health_thread.join(timeout=5)
        if hasattr(self, 'metrics_thread'):
            self.metrics_thread.join(timeout=5)
        if hasattr(self, 'cache_thread'):
            self.cache_thread.join(timeout=5)
        
        logger.info("Core Platform Service shutdown complete")
    
    def __del__(self):
        """Cleanup on service destruction."""
        self.shutdown() 