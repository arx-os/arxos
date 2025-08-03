"""
SVGX Engine - Optimized Go Notification API Client

This module provides an optimized Python client for the Go notification API with:
- Connection pooling for external services
- Async notification processing
- Rate limiting and throttling
- Caching for templates and configs
- Background job processing
- Performance monitoring and metrics

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 2.0.0
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict, deque
import functools
import weakref

# Import base classes from the original client
from .go_client import (
    NotificationRequest,
    NotificationResponse,
    NotificationHistoryRequest,
    NotificationStatistics,
    NotificationChannelType,
    NotificationPriority,
    NotificationType,
    NotificationStatus
)

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL support"""
    
    def __init__(self, value: Any, ttl: int = 300):
    """
    Perform __init__ operation

Args:
        value: Description of value
        ttl: Description of ttl

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.created_at > self.ttl


class RateLimiter:
    """
    Perform __init__ operation

Args:
        max_requests: Description of max_requests
        time_window: Description of time_window

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Rate limiter for API calls"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = threading.Lock()
    
    def can_proceed(self) -> bool:
        """Check if request can proceed"""
        now = time.time()
        
        with self.lock:
            # Remove expired requests
            while self.requests and now - self.requests[0] > self.time_window:
                self.requests.popleft()
            
            # Check if we can add another request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    def wait_if_needed(self) -> float:
        """Wait if rate limit is exceeded and return wait time"""
        if not self.can_proceed():
            # Calculate wait time
            oldest_request = self.requests[0]
            wait_time = self.time_window - (time.time() - oldest_request)
            if wait_time > 0:
                time.sleep(wait_time)
                return wait_time
        return 0.0


class ConnectionPool:
    """Connection pool for HTTP clients"""
    
    def __init__(self, max_connections: int = 100, max_keepalive: int = 20):
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.session = None
        self.async_session = None
        self._lock = threading.Lock()
    
    def get_session(self) -> requests.Session:
        """Get or create HTTP session with connection pooling"""
        if self.session is None:
            with self._lock:
                if self.session is None:
                    self.session = requests.Session()
                    
                    # Configure connection pooling
                    adapter = HTTPAdapter(
                        pool_connections=self.max_connections,
                        pool_maxsize=self.max_keepalive,
                        max_retries=Retry(
                            total=3,
                            backoff_factor=0.1,
                            status_forcelist=[429, 500, 502, 503, 504]
                        )
                    )
                    self.session.mount("http://", adapter)
                    self.session.mount("https://", adapter)
        
        return self.session
    
    async def get_async_session(self) -> aiohttp.ClientSession:
        """Get or create async HTTP session with connection pooling"""
        if self.async_session is None or self.async_session.closed:
            with self._lock:
                if self.async_session is None or self.async_session.closed:
                    connector = aiohttp.TCPConnector(
                        limit=self.max_connections,
                        limit_per_host=self.max_keepalive,
                        ttl_dns_cache=300,
                        use_dns_cache=True
                    )
                    self.async_session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=aiohttp.ClientTimeout(total=30)
                    )
        
        return self.async_session
    
    def close(self):
        """Close all sessions"""
        if self.session:
            self.session.close()
        if self.async_session and not self.async_session.closed:
            asyncio.create_task(self.async_session.close())


class BackgroundJobProcessor:
    """Background job processor for notification tasks"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs = {}
        self._lock = threading.Lock()
    
    def submit_job(self, job_id: str, func: Callable, *args, **kwargs):
        """Submit a job for background processing"""
        future = self.executor.submit(func, *args, **kwargs)
        
        with self._lock:
            self.jobs[job_id] = {
                'future': future,
                'submitted_at': time.time(),
                'status': 'pending'
            }
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status"""
        with self._lock:
            if job_id not in self.jobs:
                return None
            
            job = self.jobs[job_id]
            future = job['future']
            
            if future.done():
                try:
                    result = future.result(timeout=0)
                    job['status'] = 'completed'
                    job['result'] = result
                except Exception as e:
                    job['status'] = 'failed'
                    job['error'] = str(e)
            else:
                job['status'] = 'running'
            
            return job
    
    def cleanup_completed_jobs(self):
        """Clean up completed jobs"""
        with self._lock:
            completed_jobs = [
                job_id for job_id, job in self.jobs.items()
                if job['status'] in ['completed', 'failed']
            ]
            
            for job_id in completed_jobs:
                del self.jobs[job_id]
    
    def shutdown(self):
        """Shutdown the job processor"""
        self.executor.shutdown(wait=True)


class OptimizedGoNotificationClient:
    """
    Optimized Go notification client with performance enhancements
    
    Features:
    - Connection pooling for external services
    - Async notification processing
    - Rate limiting and throttling
    - Caching for templates and configs
    - Background job processing
    - Performance monitoring
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_connections: int = 100,
        max_keepalive: int = 20,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,
        cache_ttl: int = 300,
        max_workers: int = 10
    ):
        """
        Initialize the optimized Go notification client
        
        Args:
            base_url: Base URL for the Go notification API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            max_connections: Maximum number of connections in pool
            max_keepalive: Maximum keepalive connections per host
            rate_limit_requests: Maximum requests per time window
            rate_limit_window: Time window for rate limiting in seconds
            cache_ttl: Cache TTL in seconds
            max_workers: Maximum background workers
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Performance components
        self.connection_pool = ConnectionPool(max_connections, max_keepalive)
        self.rate_limiter = RateLimiter(rate_limit_requests, rate_limit_window)
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_lock = threading.Lock()
        self.job_processor = BackgroundJobProcessor(max_workers)
        
        # Metrics
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_failed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limit_hits': 0,
            'avg_response_time': 0.0
        }
        self.metrics_lock = threading.Lock()
        
        # Background cleanup
        self._start_cleanup_thread()
        
        logger.info("Optimized Go notification client initialized")

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(60)  # Run every minute
                    self._cleanup_cache()
                    self.job_processor.cleanup_completed_jobs()
                except Exception as e:
                    logger.error(f"Cleanup worker error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def _cleanup_cache(self):
        """Clean up expired cache entries"""
        with self.cache_lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self.cache[key]

    def _get_cache(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.cache_lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    self._update_metrics('cache_hits', 1)
                    return entry.value
                else:
                    del self.cache[key]
        
        self._update_metrics('cache_misses', 1)
        return None

    def _set_cache(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        with self.cache_lock:
            self.cache[key] = CacheEntry(value, ttl)

    def _update_metrics(self, metric: str, value: int = 1):
        """Update metrics"""
        with self.metrics_lock:
            if metric in self.metrics:
                self.metrics[metric] += value

    def _record_request_time(self, duration: float):
        """Record request duration for metrics"""
        with self.metrics_lock:
            self.metrics['requests_total'] += 1
            # Update average response time
            total_requests = self.metrics['requests_total']
            current_avg = self.metrics['avg_response_time']
            self.metrics['avg_response_time'] = (
                (current_avg * (total_requests - 1) + duration) / total_requests
            )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = False,
        cache_key: Optional[str] = None,
        cache_ttl: int = 300
    ) -> requests.Response:
        """
        Make HTTP request with optimizations
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            use_cache: Whether to use caching
            cache_key: Cache key for response
            cache_ttl: Cache TTL in seconds
            
        Returns:
            HTTP response
        """
        # Check cache for GET requests
        if use_cache and cache_key and method.upper() == 'GET':
            cached_response = self._get_cache(cache_key)
            if cached_response:
                return cached_response
        
        # Rate limiting
        wait_time = self.rate_limiter.wait_if_needed()
        if wait_time > 0:
            self._update_metrics('rate_limit_hits', 1)
        
        # Get session from pool
        session = self.connection_pool.get_session()
        url = f"{self.base_url}{endpoint}"
        
        start_time = time.time()
        
        try:
            response = session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Cache successful GET responses
            if use_cache and cache_key and method.upper() == 'GET':
                self._set_cache(cache_key, response, cache_ttl)
            
            duration = time.time() - start_time
            self._record_request_time(duration)
            self._update_metrics('requests_success', 1)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_request_time(duration)
            self._update_metrics('requests_failed', 1)
            logger.error(f"HTTP request failed: {e}")
            raise

    async def _make_async_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> aiohttp.ClientResponse:
        """
        Make async HTTP request with optimizations
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            
        Returns:
            HTTP response
        """
        # Rate limiting (async version)
        if not self.rate_limiter.can_proceed():
            wait_time = self.rate_limiter.time_window
            await asyncio.sleep(wait_time)
            self._update_metrics('rate_limit_hits', 1)
        
        # Get async session from pool
        session = await self.connection_pool.get_async_session()
        url = f"{self.base_url}{endpoint}"
        
        start_time = time.time()
        
        try:
            async with session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                response.raise_for_status()
                
                duration = time.time() - start_time
                self._record_request_time(duration)
                self._update_metrics('requests_success', 1)
                
                return response
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_request_time(duration)
            self._update_metrics('requests_failed', 1)
            logger.error(f"Async HTTP request failed: {e}")
            raise

    def send_notification(self, request: NotificationRequest) -> NotificationResponse:
        """
        Send notification with optimizations
        
        Args:
            request: Notification request
            
        Returns:
            Notification response
        """
        try:
            response = self._make_request(
                method="POST",
                endpoint="/api/notifications/send",
                data=request.to_dict()
            )
            
            response_data = response.json()
            return NotificationResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return NotificationResponse(
                success=False,
                error=str(e)
            )

    async def send_notification_async(self, request: NotificationRequest) -> NotificationResponse:
        """
        Send notification asynchronously with optimizations
        
        Args:
            request: Notification request
            
        Returns:
            Notification response
        """
        try:
            response = await self._make_async_request(
                method="POST",
                endpoint="/api/notifications/send",
                data=request.to_dict()
            )
            
            response_data = await response.json()
            return NotificationResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Failed to send notification async: {e}")
            return NotificationResponse(
                success=False,
                error=str(e)
            )

    def send_notification_background(
        self,
        request: NotificationRequest
    ) -> str:
        """
        Send notification in background job
        
        Args:
            request: Notification request
            
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        
        def send_job():
            return self.send_notification(request)
        
        self.job_processor.submit_job(job_id, send_job)
        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get background job status"""
        return self.job_processor.get_job_status(job_id)

    def get_notification_history(
        self,
        request: NotificationHistoryRequest
    ) -> Dict[str, Any]:
        """
        Get notification history with caching
        
        Args:
            request: History request parameters
            
        Returns:
            Notification history data
        """
        # Create cache key
        cache_key = f"history_{hash(str(request.to_dict()))}"
        
        try:
            response = self._make_request(
                method="GET",
                endpoint="/api/notifications/history",
                params=request.to_dict(),
                use_cache=True,
                cache_key=cache_key,
                cache_ttl=60  # Cache for 1 minute
            )
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get notification history: {e}")
            return {"error": str(e)}

    def get_notification_statistics(
        self,
        period: str = "7d"
    ) -> Optional[NotificationStatistics]:
        """
        Get notification statistics with caching
        
        Args:
            period: Statistics period (e.g., "7d", "30d")
            
        Returns:
            Notification statistics
        """
        cache_key = f"stats_{period}"
        
        try:
            response = self._make_request(
                method="GET",
                endpoint="/api/notifications/statistics",
                params={"period": period},
                use_cache=True,
                cache_key=cache_key,
                cache_ttl=300  # Cache for 5 minutes
            )
            
            data = response.json()
            return NotificationStatistics(**data)
            
        except Exception as e:
            logger.error(f"Failed to get notification statistics: {e}")
            return None

    def get_templates(self) -> List[Dict[str, Any]]:
        """
        Get notification templates with caching
        
        Returns:
            List of notification templates
        """
        cache_key = "templates"
        
        try:
            response = self._make_request(
                method="GET",
                endpoint="/api/notifications/templates",
                use_cache=True,
                cache_key=cache_key,
                cache_ttl=600  # Cache for 10 minutes
            )
            
            return response.json().get("templates", [])
            
        except Exception as e:
            logger.error(f"Failed to get templates: {e}")
            return []

    def get_configs(self) -> List[Dict[str, Any]]:
        """
        Get notification configurations with caching
        
        Returns:
            List of notification configurations
        """
        cache_key = "configs"
        
        try:
            response = self._make_request(
                method="GET",
                endpoint="/api/notifications/configs",
                use_cache=True,
                cache_key=cache_key,
                cache_ttl=600  # Cache for 10 minutes
            )
            
            return response.json().get("configs", [])
            
        except Exception as e:
            logger.error(f"Failed to get configs: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """
        Check Go notification service health with metrics
        
        Returns:
            Health status with performance metrics
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="/api/notifications/health"
            )
            
            health_data = response.json()
            
            # Add performance metrics
            with self.metrics_lock:
                health_data.update({
                    "performance_metrics": self.metrics.copy(),
                    "cache_size": len(self.cache),
                    "active_jobs": len(self.job_processor.jobs),
                    "rate_limit_status": {
                        "can_proceed": self.rate_limiter.can_proceed(),
                        "current_requests": len(self.rate_limiter.requests)
                    }
                })
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "performance_metrics": self.metrics.copy()
            }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        with self.metrics_lock:
            metrics = self.metrics.copy()
        
        return {
            "metrics": metrics,
            "cache_info": {
                "size": len(self.cache),
                "keys": list(self.cache.keys())
            },
            "job_info": {
                "active_jobs": len(self.job_processor.jobs),
                "max_workers": self.job_processor.max_workers
            },
            "rate_limit_info": {
                "can_proceed": self.rate_limiter.can_proceed(),
                "current_requests": len(self.rate_limiter.requests),
                "max_requests": self.rate_limiter.max_requests
            }
        }

    def clear_cache(self):
        """Clear all cached data"""
        with self.cache_lock:
            self.cache.clear()
        logger.info("Cache cleared")

    def shutdown(self):
        """Shutdown the client and cleanup resources"""
        self.job_processor.shutdown()
        self.connection_pool.close()
        logger.info("Optimized Go notification client shutdown")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.shutdown()


# Factory function for optimized client
def create_optimized_go_notification_client(
    base_url: str = "http://localhost:8080",
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    max_connections: int = 100,
    max_keepalive: int = 20,
    rate_limit_requests: int = 100,
    rate_limit_window: int = 60,
    cache_ttl: int = 300,
    max_workers: int = 10
) -> OptimizedGoNotificationClient:
    """
    Create an optimized Go notification client
    
    Args:
        base_url: Base URL for the Go notification API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        max_connections: Maximum number of connections in pool
        max_keepalive: Maximum keepalive connections per host
        rate_limit_requests: Maximum requests per time window
        rate_limit_window: Time window for rate limiting in seconds
        cache_ttl: Cache TTL in seconds
        max_workers: Maximum background workers
        
    Returns:
        Optimized Go notification client
    """
    return OptimizedGoNotificationClient(
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
        max_connections=max_connections,
        max_keepalive=max_keepalive,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window=rate_limit_window,
        cache_ttl=cache_ttl,
        max_workers=max_workers
    )


# Export main classes and functions
__all__ = [
    'OptimizedGoNotificationClient',
    'ConnectionPool',
    'RateLimiter',
    'CacheEntry',
    'BackgroundJobProcessor',
    'create_optimized_go_notification_client'
] 