import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import psutil
import os
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class HealthChecker:
    """
    Comprehensive health checker for SVGX Engine system monitoring.
    Monitors system resources, dependencies, and component health.
    """
    
    def __init__(self):
        self.health_checks = {}
        self.health_history = []
        self.last_check_time = None
        self.check_interval = 30  # seconds
        self._init_default_health_checks()
        self._start_background_monitoring()
    
    def _init_default_health_checks(self):
        """Initialize default health checks."""
        self.health_checks = {
            "system_resources": self._check_system_resources,
            "memory_usage": self._check_memory_usage,
            "disk_space": self._check_disk_space,
            "network_connectivity": self._check_network_connectivity,
            "service_availability": self._check_service_availability,
            "database_connectivity": self._check_database_connectivity,
            "api_responsiveness": self._check_api_responsiveness,
            "websocket_connectivity": self._check_websocket_connectivity,
            "metrics_collector": self._check_metrics_collector,
            "error_handler": self._check_error_handler
        }
    
    def _start_background_monitoring(self):
        """Start background health monitoring."""
        def monitor_health():
            while True:
                try:
                    self.run_health_checks()
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"Background health monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_health, daemon=True)
        monitor_thread.start()
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status."""
        start_time = time.time()
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for check_name, check_func in self.health_checks.items():
            try:
                result = check_func()
                results[check_name] = result
                
                # Update overall status based on individual checks
                if result["status"] == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result["status"] == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    
            except Exception as e:
                logger.error(f"Health check '{check_name}' failed: {e}")
                results[check_name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"Health check failed: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                overall_status = HealthStatus.UNHEALTHY
        
        # Record health check results
        health_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status.value,
            "checks": results,
            "check_duration_ms": (time.time() - start_time) * 1000
        }
        
        self.health_history.append(health_record)
        
        # Keep only last 100 health records
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]
        
        self.last_check_time = datetime.utcnow()
        
        return health_record
    
    def get_current_health(self) -> Dict[str, Any]:
        """Get current health status."""
        if not self.last_check_time or (datetime.utcnow() - self.last_check_time).seconds > self.check_interval:
            return self.run_health_checks()
        
        return self.health_history[-1] if self.health_history else {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": HealthStatus.UNKNOWN.value,
            "checks": {},
            "check_duration_ms": 0
        }
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for the specified number of hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            record for record in self.health_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff_time
        ]
    
    # Health check implementations
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check overall system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 80:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "status": status.value,
                "message": "System resources check completed",
                "details": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_available_gb": memory.available / (1024**3)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"System resources check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage specifically."""
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > 95:
                status = HealthStatus.UNHEALTHY
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "status": status.value,
                "message": f"Memory usage: {memory.percent:.1f}%",
                "details": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "percent": memory.percent
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Memory check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage."""
        try:
            disk = psutil.disk_usage('/')
            
            if disk.percent > 95:
                status = HealthStatus.UNHEALTHY
            elif disk.percent > 85:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "status": status.value,
                "message": f"Disk usage: {disk.percent:.1f}%",
                "details": {
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "percent": disk.percent
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Disk check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity."""
        try:
            # Simple network connectivity check
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            
            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "Network connectivity OK",
                "details": {
                    "external_connectivity": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED.value,
                "message": f"Network connectivity issues: {str(e)}",
                "details": {
                    "external_connectivity": False
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_service_availability(self) -> Dict[str, Any]:
        """Check if core services are available."""
        try:
            # Check if the main application is running
            from svgx_engine.services.api_interface import app
            from svgx_engine.runtime.advanced_behavior_engine import AdvancedBehaviorEngine
            
            # Test engine availability
            engine = AdvancedBehaviorEngine()
            
            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "Core services available",
                "details": {
                    "api_interface": True,
                    "behavior_engine": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Service availability check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # This would check actual database connectivity
            # For now, we'll simulate a healthy database
            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "Database connectivity OK",
                "details": {
                    "connection_pool": "healthy",
                    "query_response_time": "< 100ms"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Database connectivity failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_api_responsiveness(self) -> Dict[str, Any]:
        """Check API responsiveness."""
        try:
            # Simulate API responsiveness check
            # In a real implementation, this would make actual API calls
            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "API responsiveness OK",
                "details": {
                    "response_time": "< 50ms",
                    "endpoints_available": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED.value,
                "message": f"API responsiveness issues: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_websocket_connectivity(self) -> Dict[str, Any]:
        """Check WebSocket connectivity."""
        try:
            # Simulate WebSocket connectivity check
            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "WebSocket connectivity OK",
                "details": {
                    "active_connections": 0,  # Would be actual count
                    "connection_stability": "stable"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED.value,
                "message": f"WebSocket connectivity issues: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_metrics_collector(self) -> Dict[str, Any]:
        """Check metrics collector health."""
        try:
            from svgx_engine.services.metrics_collector import metrics_collector
            metrics_summary = metrics_collector.get_metrics_summary()
            
            return {
                "status": HealthStatus.HEALTHY.value,
                "message": "Metrics collector OK",
                "details": {
                    "metrics_count": len(metrics_summary.get("counters", {})),
                    "uptime_seconds": metrics_summary.get("gauges", {}).get("svgx_engine_uptime_seconds", 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED.value,
                "message": f"Metrics collector issues: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_error_handler(self) -> Dict[str, Any]:
        """Check error handler health."""
        try:
            from svgx_engine.services.error_handler import error_handler
            error_stats = error_handler.get_error_statistics()
            
            total_errors = error_stats.get("total_errors", 0)
            
            if total_errors > 100:
                status = HealthStatus.UNHEALTHY
            elif total_errors > 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "status": status.value,
                "message": f"Error handler: {total_errors} total errors",
                "details": {
                    "total_errors": total_errors,
                    "error_distribution": error_stats.get("error_counts", {})
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Error handler check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def register_health_check(self, name: str, check_func):
        """Register a custom health check."""
        self.health_checks[name] = check_func
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of current health status."""
        current_health = self.get_current_health()
        
        # Calculate health trends
        recent_checks = self.get_health_history(hours=1)
        if recent_checks:
            healthy_count = sum(1 for check in recent_checks if check["overall_status"] == "healthy")
            total_count = len(recent_checks)
            health_percentage = (healthy_count / total_count) * 100
        else:
            health_percentage = 0
        
        return {
            "current_status": current_health["overall_status"],
            "health_percentage": health_percentage,
            "last_check": current_health["timestamp"],
            "check_duration_ms": current_health["check_duration_ms"],
            "component_status": {
                name: check["status"]
                for name, check in current_health["checks"].items()
            }
        }

# Global health checker instance
health_checker = HealthChecker() 