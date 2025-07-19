#!/usr/bin/env python3
"""
Pipeline Monitoring and Observability Service

Provides comprehensive monitoring, metrics collection, health checks,
and observability for the Arxos pipeline system.
"""

import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import sqlite3
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineMetric:
    """Pipeline metric data structure."""
    timestamp: float
    metric_name: str
    metric_value: float
    metric_unit: str
    tags: Dict[str, str]
    system: Optional[str] = None
    execution_id: Optional[str] = None


@dataclass
class HealthCheck:
    """Health check data structure."""
    service: str
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    operation: str
    duration_ms: float
    success: bool
    timestamp: float
    system: Optional[str] = None
    error_message: Optional[str] = None


class PipelineMonitoring:
    """Comprehensive monitoring and observability for the pipeline."""
    
    def __init__(self, metrics_db_path: str = "pipeline_metrics.db"):
        self.metrics_db_path = metrics_db_path
        self.metrics_db = None
        self.health_checks = {}
        self.performance_metrics = []
        self.alerts = []
        self.monitoring_enabled = True
        
        # Initialize database
        self._init_metrics_database()
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def _init_metrics_database(self):
        """Initialize metrics database."""
        try:
            self.metrics_db = sqlite3.connect(self.metrics_db_path)
            self.metrics_db.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    system TEXT,
                    execution_id TEXT
                )
            """)
            
            self.metrics_db.execute("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    details TEXT NOT NULL,
                    error_message TEXT
                )
            """)
            
            self.metrics_db.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    timestamp REAL NOT NULL,
                    system TEXT,
                    error_message TEXT
                )
            """)
            
            self.metrics_db.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE
                )
            """)
            
            self.metrics_db.commit()
            logger.info("Metrics database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize metrics database: {e}")
            self.monitoring_enabled = False
    
    def record_metric(self, metric_name: str, metric_value: float, 
                     metric_unit: str, tags: Dict[str, str] = None,
                     system: str = None, execution_id: str = None):
        """Record a pipeline metric."""
        if not self.monitoring_enabled:
            return
        
        try:
            metric = PipelineMetric(
                timestamp=time.time(),
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                tags=tags or {},
                system=system,
                execution_id=execution_id
            )
            
            self.metrics_db.execute("""
                INSERT INTO pipeline_metrics 
                (timestamp, metric_name, metric_value, metric_unit, tags, system, execution_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp,
                metric.metric_name,
                metric.metric_value,
                metric.metric_unit,
                json.dumps(metric.tags),
                metric.system,
                metric.execution_id
            ))
            
            self.metrics_db.commit()
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {e}")
    
    def record_performance_metric(self, operation: str, duration_ms: float,
                                success: bool, system: str = None,
                                error_message: str = None):
        """Record a performance metric."""
        if not self.monitoring_enabled:
            return
        
        try:
            metric = PerformanceMetric(
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                timestamp=time.time(),
                system=system,
                error_message=error_message
            )
            
            self.metrics_db.execute("""
                INSERT INTO performance_metrics 
                (operation, duration_ms, success, timestamp, system, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric.operation,
                metric.duration_ms,
                metric.success,
                metric.timestamp,
                metric.system,
                metric.error_message
            ))
            
            self.metrics_db.commit()
            
            # Store in memory for quick access
            self.performance_metrics.append(metric)
            
            # Keep only last 1000 metrics in memory
            if len(self.performance_metrics) > 1000:
                self.performance_metrics = self.performance_metrics[-1000:]
                
        except Exception as e:
            logger.error(f"Failed to record performance metric: {e}")
    
    def update_health_check(self, service: str, status: str, 
                          details: Dict[str, Any] = None,
                          error_message: str = None):
        """Update health check for a service."""
        if not self.monitoring_enabled:
            return
        
        try:
            health_check = HealthCheck(
                service=service,
                status=status,
                timestamp=time.time(),
                details=details or {},
                error_message=error_message
            )
            
            self.metrics_db.execute("""
                INSERT INTO health_checks 
                (service, status, timestamp, details, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                health_check.service,
                health_check.status,
                health_check.timestamp,
                json.dumps(health_check.details),
                health_check.error_message
            ))
            
            self.metrics_db.commit()
            
            # Update in-memory health checks
            self.health_checks[service] = health_check
            
        except Exception as e:
            logger.error(f"Failed to update health check for {service}: {e}")
    
    def create_alert(self, alert_type: str, severity: str, message: str):
        """Create an alert."""
        if not self.monitoring_enabled:
            return
        
        try:
            alert = {
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "timestamp": time.time(),
                "resolved": False
            }
            
            self.metrics_db.execute("""
                INSERT INTO alerts 
                (alert_type, severity, message, timestamp, resolved)
                VALUES (?, ?, ?, ?, ?)
            """, (
                alert["alert_type"],
                alert["severity"],
                alert["message"],
                alert["timestamp"],
                alert["resolved"]
            ))
            
            self.metrics_db.commit()
            
            # Store in memory
            self.alerts.append(alert)
            
            # Log alert
            logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}")
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        health_status = {
            "overall_status": "healthy",
            "services": {},
            "alerts": [],
            "timestamp": time.time()
        }
        
        # Check service health
        for service, health_check in self.health_checks.items():
            health_status["services"][service] = {
                "status": health_check.status,
                "last_check": health_check.timestamp,
                "details": health_check.details
            }
            
            if health_check.status == "unhealthy":
                health_status["overall_status"] = "unhealthy"
            elif health_check.status == "degraded" and health_status["overall_status"] == "healthy":
                health_status["overall_status"] = "degraded"
        
        # Get recent alerts
        try:
            cursor = self.metrics_db.execute("""
                SELECT alert_type, severity, message, timestamp 
                FROM alerts 
                WHERE resolved = FALSE 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            
            for row in cursor.fetchall():
                health_status["alerts"].append({
                    "type": row[0],
                    "severity": row[1],
                    "message": row[2],
                    "timestamp": row[3]
                })
                
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
        
        return health_status
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for the last N hours."""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            cursor = self.metrics_db.execute("""
                SELECT operation, AVG(duration_ms) as avg_duration,
                       COUNT(*) as total_operations,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_operations
                FROM performance_metrics 
                WHERE timestamp > ?
                GROUP BY operation
            """, (cutoff_time,))
            
            metrics = {}
            for row in cursor.fetchall():
                operation, avg_duration, total_ops, successful_ops = row
                success_rate = (successful_ops / total_ops * 100) if total_ops > 0 else 0
                
                metrics[operation] = {
                    "avg_duration_ms": round(avg_duration, 2),
                    "total_operations": total_ops,
                    "successful_operations": successful_ops,
                    "success_rate_percent": round(success_rate, 2)
                }
            
            return {
                "time_period_hours": hours,
                "metrics": metrics,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}
    
    def get_pipeline_metrics(self, system: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get pipeline-specific metrics."""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            query = """
                SELECT metric_name, AVG(metric_value) as avg_value,
                       COUNT(*) as total_measurements,
                       MIN(metric_value) as min_value,
                       MAX(metric_value) as max_value
                FROM pipeline_metrics 
                WHERE timestamp > ?
            """
            params = [cutoff_time]
            
            if system:
                query += " AND system = ?"
                params.append(system)
            
            query += " GROUP BY metric_name"
            
            cursor = self.metrics_db.execute(query, params)
            
            metrics = {}
            for row in cursor.fetchall():
                metric_name, avg_value, total_measurements, min_value, max_value = row
                metrics[metric_name] = {
                    "avg_value": round(avg_value, 2),
                    "total_measurements": total_measurements,
                    "min_value": min_value,
                    "max_value": max_value
                }
            
            return {
                "system": system,
                "time_period_hours": hours,
                "metrics": metrics,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline metrics: {e}")
            return {"error": str(e)}
    
    def _start_background_monitoring(self):
        """Start background monitoring tasks."""
        def monitor_system_resources():
            while self.monitoring_enabled:
                try:
                    # Monitor CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.record_metric("cpu_usage", cpu_percent, "percent", {"component": "system"})
                    
                    # Monitor memory usage
                    memory = psutil.virtual_memory()
                    self.record_metric("memory_usage", memory.percent, "percent", {"component": "system"})
                    
                    # Monitor disk usage
                    disk = psutil.disk_usage('/')
                    self.record_metric("disk_usage", disk.percent, "percent", {"component": "system"})
                    
                    # Check for high resource usage
                    if cpu_percent > 80:
                        self.create_alert("high_cpu_usage", "warning", f"CPU usage is {cpu_percent}%")
                    
                    if memory.percent > 85:
                        self.create_alert("high_memory_usage", "warning", f"Memory usage is {memory.percent}%")
                    
                    if disk.percent > 90:
                        self.create_alert("high_disk_usage", "critical", f"Disk usage is {disk.percent}%")
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Error in system resource monitoring: {e}")
                    time.sleep(60)
        
        # Start background monitoring thread
        monitoring_thread = threading.Thread(target=monitor_system_resources, daemon=True)
        monitoring_thread.start()
        logger.info("Background monitoring started")
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report."""
        health_status = self.get_system_health()
        performance_metrics = self.get_performance_metrics()
        pipeline_metrics = self.get_pipeline_metrics()
        
        report = {
            "report_timestamp": time.time(),
            "report_date": datetime.now().isoformat(),
            "health_status": health_status,
            "performance_metrics": performance_metrics,
            "pipeline_metrics": pipeline_metrics,
            "summary": {
                "overall_health": health_status["overall_status"],
                "active_alerts": len(health_status["alerts"]),
                "services_monitored": len(health_status["services"]),
                "performance_operations": len(performance_metrics.get("metrics", {}))
            }
        }
        
        return report
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        if format == "json":
            report = self.generate_health_report()
            return json.dumps(report, indent=2)
        else:
            return "Unsupported format"
    
    def cleanup_old_metrics(self, days: int = 30):
        """Clean up old metrics data."""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            # Clean up old metrics
            self.metrics_db.execute("DELETE FROM pipeline_metrics WHERE timestamp < ?", (cutoff_time,))
            
            # Clean up old health checks (keep last 1000)
            self.metrics_db.execute("""
                DELETE FROM health_checks 
                WHERE id NOT IN (
                    SELECT id FROM health_checks 
                    ORDER BY timestamp DESC 
                    LIMIT 1000
                )
            """)
            
            # Clean up old performance metrics
            self.metrics_db.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_time,))
            
            # Clean up resolved alerts older than 7 days
            alert_cutoff = time.time() - (7 * 24 * 3600)
            self.metrics_db.execute("DELETE FROM alerts WHERE resolved = TRUE AND timestamp < ?", (alert_cutoff,))
            
            self.metrics_db.commit()
            logger.info(f"Cleaned up metrics older than {days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")


# Global monitoring instance
monitoring = PipelineMonitoring()


def get_monitoring() -> PipelineMonitoring:
    """Get the global monitoring instance."""
    return monitoring


@contextmanager
def performance_timer(operation: str, system: str = None):
    """Context manager for timing operations."""
    start_time = time.time()
    success = False
    error_message = None
    
    try:
        yield
        success = True
    except Exception as e:
        error_message = str(e)
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        monitoring.record_performance_metric(operation, duration_ms, success, system, error_message)


def monitor_operation(operation: str, system: str = None):
    """Decorator for monitoring operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with performance_timer(operation, system):
                return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage
    monitoring = PipelineMonitoring()
    
    # Record some metrics
    monitoring.record_metric("pipeline_executions", 10, "count", {"status": "completed"})
    monitoring.record_metric("pipeline_duration", 150.5, "seconds", {"system": "electrical"})
    
    # Update health checks
    monitoring.update_health_check("pipeline_service", "healthy", {"version": "1.0.0"})
    monitoring.update_health_check("database", "healthy", {"connections": 5})
    
    # Generate health report
    report = monitoring.generate_health_report()
    print(json.dumps(report, indent=2)) 