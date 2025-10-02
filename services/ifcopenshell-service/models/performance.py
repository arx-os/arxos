"""
Performance Optimization Module

This module provides performance optimizations including:
- Advanced caching strategies
- Async processing capabilities
- Memory management
- Performance monitoring
"""

import redis
import json
import hashlib
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading
from queue import Queue
import os

logger = logging.getLogger(__name__)


class PerformanceCache:
    """Advanced caching system with Redis backend"""
    
    def __init__(self):
        self.redis_client = None
        self.local_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_db = int(os.getenv('REDIS_DB', '0'))
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis cache connected: {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using local cache only.")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        try:
            # Try Redis first
            if self.redis_client:
                cached = self.redis_client.get(key)
                if cached:
                    self.cache_stats["hits"] += 1
                    return json.loads(cached)
            
            # Fallback to local cache
            if key in self.local_cache:
                cached_data = self.local_cache[key]
                if cached_data["expires"] > time.time():
                    self.cache_stats["hits"] += 1
                    return cached_data["data"]
                else:
                    del self.local_cache[key]
                    self.cache_stats["evictions"] += 1
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = 3600):
        """Set value in cache"""
        try:
            self.cache_stats["sets"] += 1
            
            # Try Redis first
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value))
                return
            
            # Fallback to local cache
            self.local_cache[key] = {
                "data": value,
                "expires": time.time() + ttl
            }
            
            # Clean expired entries periodically
            if len(self.local_cache) > 1000:
                self._cleanup_local_cache()
                
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def _cleanup_local_cache(self):
        """Clean up expired entries from local cache"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.local_cache.items()
            if data["expires"] <= current_time
        ]
        
        for key in expired_keys:
            del self.local_cache[key]
            self.cache_stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "sets": self.cache_stats["sets"],
            "evictions": self.cache_stats["evictions"],
            "hit_rate_percent": round(hit_rate, 2),
            "local_cache_size": len(self.local_cache),
            "redis_connected": self.redis_client is not None
        }


class AsyncProcessor:
    """Async processing for heavy IFC operations"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.task_queue = Queue()
        self.results = {}
        self.workers = []
        self.running = False
        self._start_workers()
    
    def _start_workers(self):
        """Start worker threads"""
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def _worker(self):
        """Worker thread function"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    break
                
                task_id, func, args, kwargs = task
                try:
                    result = func(*args, **kwargs)
                    self.results[task_id] = {"success": True, "result": result}
                except Exception as e:
                    self.results[task_id] = {"success": False, "error": str(e)}
                
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def submit_task(self, task_id: str, func, *args, **kwargs) -> str:
        """Submit a task for async processing"""
        self.task_queue.put((task_id, func, args, kwargs))
        return task_id
    
    def get_result(self, task_id: str, timeout: float = None) -> Optional[Dict[str, Any]]:
        """Get result of async task"""
        start_time = time.time()
        
        while task_id not in self.results:
            if timeout and (time.time() - start_time) > timeout:
                return {"success": False, "error": "Task timeout"}
            time.sleep(0.1)
        
        return self.results.pop(task_id, None)
    
    def shutdown(self):
        """Shutdown async processor"""
        self.running = False
        for _ in range(self.max_workers):
            self.task_queue.put(None)


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_by_endpoint": {},
            "processing_times": [],
            "memory_usage": [],
            "error_count": 0,
            "cache_performance": {}
        }
        self.start_time = time.time()
    
    def record_request(self, endpoint: str, processing_time: float, success: bool = True):
        """Record request metrics"""
        self.metrics["requests_total"] += 1
        
        if endpoint not in self.metrics["requests_by_endpoint"]:
            self.metrics["requests_by_endpoint"][endpoint] = {
                "total": 0,
                "success": 0,
                "errors": 0,
                "avg_time": 0
            }
        
        endpoint_metrics = self.metrics["requests_by_endpoint"][endpoint]
        endpoint_metrics["total"] += 1
        
        if success:
            endpoint_metrics["success"] += 1
        else:
            endpoint_metrics["errors"] += 1
            self.metrics["error_count"] += 1
        
        # Update average processing time
        total_time = endpoint_metrics["avg_time"] * (endpoint_metrics["total"] - 1)
        endpoint_metrics["avg_time"] = (total_time + processing_time) / endpoint_metrics["total"]
        
        # Record processing time
        self.metrics["processing_times"].append(processing_time)
        if len(self.metrics["processing_times"]) > 1000:
            self.metrics["processing_times"] = self.metrics["processing_times"][-1000:]
    
    def record_memory_usage(self):
        """Record current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            self.metrics["memory_usage"].append({
                "timestamp": time.time(),
                "rss": memory_info.rss,
                "vms": memory_info.vms
            })
            
            # Keep only last 100 memory readings
            if len(self.metrics["memory_usage"]) > 100:
                self.metrics["memory_usage"] = self.metrics["memory_usage"][-100:]
                
        except ImportError:
            logger.warning("psutil not available for memory monitoring")
        except Exception as e:
            logger.error(f"Memory monitoring error: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        uptime = time.time() - self.start_time
        
        # Calculate percentiles for processing times
        processing_times = self.metrics["processing_times"]
        percentiles = {}
        if processing_times:
            sorted_times = sorted(processing_times)
            percentiles = {
                "p50": sorted_times[int(len(sorted_times) * 0.5)],
                "p90": sorted_times[int(len(sorted_times) * 0.9)],
                "p95": sorted_times[int(len(sorted_times) * 0.95)],
                "p99": sorted_times[int(len(sorted_times) * 0.99)]
            }
        
        return {
            "uptime_seconds": uptime,
            "requests_total": self.metrics["requests_total"],
            "requests_per_second": self.metrics["requests_total"] / uptime if uptime > 0 else 0,
            "error_rate": self.metrics["error_count"] / self.metrics["requests_total"] if self.metrics["requests_total"] > 0 else 0,
            "requests_by_endpoint": self.metrics["requests_by_endpoint"],
            "processing_time_percentiles": percentiles,
            "memory_usage": self.metrics["memory_usage"][-10:] if self.metrics["memory_usage"] else [],
            "timestamp": datetime.utcnow().isoformat()
        }


class CacheKeyGenerator:
    """Generate cache keys for different operations"""
    
    @staticmethod
    def generate_ifc_key(ifc_data: bytes, operation: str = "parse") -> str:
        """Generate cache key for IFC data"""
        data_hash = hashlib.md5(ifc_data).hexdigest()
        return f"ifc:{operation}:{data_hash}"
    
    @staticmethod
    def generate_validation_key(ifc_data: bytes) -> str:
        """Generate cache key for validation"""
        return CacheKeyGenerator.generate_ifc_key(ifc_data, "validate")
    
    @staticmethod
    def generate_spatial_key(ifc_data: bytes, query_params: Dict[str, Any]) -> str:
        """Generate cache key for spatial queries"""
        data_hash = hashlib.md5(ifc_data).hexdigest()
        params_hash = hashlib.md5(json.dumps(query_params, sort_keys=True).encode()).hexdigest()
        return f"spatial:{data_hash}:{params_hash}"
    
    @staticmethod
    def generate_bounds_key(ifc_data: bytes) -> str:
        """Generate cache key for bounds queries"""
        return CacheKeyGenerator.generate_ifc_key(ifc_data, "bounds")


# Global instances
performance_cache = PerformanceCache()
async_processor = AsyncProcessor()
performance_monitor = PerformanceMonitor()
cache_key_generator = CacheKeyGenerator()
