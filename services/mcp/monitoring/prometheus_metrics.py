#!/usr/bin/env python3
"""
Prometheus Metrics for MCP Performance Monitoring

This module provides comprehensive metrics collection for monitoring
MCP service performance, validation operations, and system health.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from prometheus_client import Counter, Histogram, Gauge, Summary, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    INFO = "info"


@dataclass
class ValidationMetrics:
    """Validation metrics data structure"""
    building_id: str
    jurisdiction: str
    total_rules: int
    passed_rules: int
    failed_rules: int
    violations_count: int
    warnings_count: int
    duration_seconds: float
    cache_hit: bool
    user_id: Optional[str] = None


class MetricsCollector:
    """Collects and exports Prometheus metrics"""
    
    def __init__(self):
        """Initialize metrics collector"""
        
        # Validation metrics
        self.validation_requests = Counter(
            'mcp_validation_requests_total',
            'Total validation requests',
            ['building_type', 'jurisdiction', 'user_role']
        )
        
        self.validation_duration = Histogram(
            'mcp_validation_duration_seconds',
            'Validation duration in seconds',
            ['validation_type', 'jurisdiction'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.violations_found = Counter(
            'mcp_violations_total',
            'Total violations found',
            ['severity', 'category', 'jurisdiction']
        )
        
        self.warnings_found = Counter(
            'mcp_warnings_total',
            'Total warnings found',
            ['category', 'jurisdiction']
        )
        
        self.rules_checked = Counter(
            'mcp_rules_checked_total',
            'Total rules checked',
            ['rule_type', 'jurisdiction', 'result']
        )
        
        # Performance metrics
        self.active_connections = Gauge(
            'mcp_websocket_connections',
            'Active WebSocket connections',
            ['building_id']
        )
        
        self.cache_hit_ratio = Gauge(
            'mcp_cache_hit_ratio',
            'Cache hit ratio percentage',
            ['cache_type']
        )
        
        self.cache_operations = Counter(
            'mcp_cache_operations_total',
            'Cache operations',
            ['operation', 'cache_type', 'result']
        )
        
        self.memory_usage = Gauge(
            'mcp_memory_usage_bytes',
            'Memory usage in bytes',
            ['component']
        )
        
        # System metrics
        self.system_uptime = Gauge(
            'mcp_system_uptime_seconds',
            'System uptime in seconds'
        )
        
        self.active_users = Gauge(
            'mcp_active_users',
            'Number of active users',
            ['user_role']
        )
        
        self.api_requests = Counter(
            'mcp_api_requests_total',
            'API requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.api_request_duration = Histogram(
            'mcp_api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Business metrics
        self.compliance_scores = Histogram(
            'mcp_compliance_scores',
            'Building compliance scores',
            ['jurisdiction', 'building_type'],
            buckets=[50, 60, 70, 80, 90, 95, 100]
        )
        
        self.jurisdiction_matches = Counter(
            'mcp_jurisdiction_matches_total',
            'Jurisdiction matching operations',
            ['country', 'state', 'match_level']
        )
        
        self.mcp_files_loaded = Counter(
            'mcp_files_loaded_total',
            'MCP files loaded',
            ['file_type', 'jurisdiction']
        )
        
        # Error metrics
        self.errors_total = Counter(
            'mcp_errors_total',
            'Total errors',
            ['error_type', 'component']
        )
        
        self.validation_errors = Counter(
            'mcp_validation_errors_total',
            'Validation errors',
            ['error_type', 'jurisdiction']
        )
        
        # Authentication metrics
        self.login_attempts = Counter(
            'mcp_login_attempts_total',
            'Login attempts',
            ['result', 'user_role']
        )
        
        self.active_sessions = Gauge(
            'mcp_active_sessions',
            'Active user sessions',
            ['user_role']
        )
        
        # WebSocket metrics
        self.websocket_messages = Counter(
            'mcp_websocket_messages_total',
            'WebSocket messages',
            ['message_type', 'building_id']
        )
        
        self.websocket_connections = Counter(
            'mcp_websocket_connections_total',
            'WebSocket connections',
            ['building_id', 'action']
        )
        
        # Initialize system uptime
        self.start_time = time.time()
        self.system_uptime.set_function(lambda: time.time() - self.start_time)
        
        logger.info("Metrics collector initialized")
    
    def record_validation(self, metrics: ValidationMetrics):
        """Record validation metrics"""
        try:
            # Record request
            self.validation_requests.labels(
                building_type="unknown",  # Could be extracted from building model
                jurisdiction=metrics.jurisdiction,
                user_role="unknown"  # Could be extracted from user context
            ).inc()
            
            # Record duration
            self.validation_duration.labels(
                validation_type="comprehensive",
                jurisdiction=metrics.jurisdiction
            ).observe(metrics.duration_seconds)
            
            # Record violations
            if metrics.violations_count > 0:
                self.violations_found.labels(
                    severity="violation",
                    category="general",
                    jurisdiction=metrics.jurisdiction
                ).inc(metrics.violations_count)
            
            # Record warnings
            if metrics.warnings_count > 0:
                self.warnings_found.labels(
                    category="general",
                    jurisdiction=metrics.jurisdiction
                ).inc(metrics.warnings_count)
            
            # Record rules checked
            self.rules_checked.labels(
                rule_type="comprehensive",
                jurisdiction=metrics.jurisdiction,
                result="passed"
            ).inc(metrics.passed_rules)
            
            self.rules_checked.labels(
                rule_type="comprehensive",
                jurisdiction=metrics.jurisdiction,
                result="failed"
            ).inc(metrics.failed_rules)
            
            # Record compliance score
            if metrics.total_rules > 0:
                compliance_score = (metrics.passed_rules / metrics.total_rules) * 100
                self.compliance_scores.labels(
                    jurisdiction=metrics.jurisdiction,
                    building_type="unknown"
                ).observe(compliance_score)
            
            # Record cache hit/miss
            cache_result = "hit" if metrics.cache_hit else "miss"
            self.cache_operations.labels(
                operation="validation_lookup",
                cache_type="validation_result",
                result=cache_result
            ).inc()
            
            logger.debug(f"Recorded validation metrics for building {metrics.building_id}")
            
        except Exception as e:
            logger.error(f"Error recording validation metrics: {e}")
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metrics"""
        try:
            # Record request count
            self.api_requests.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            
            # Record duration
            self.api_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Record errors
            if status_code >= 400:
                error_type = "client_error" if status_code < 500 else "server_error"
                self.errors_total.labels(
                    error_type=error_type,
                    component="api"
                ).inc()
                
        except Exception as e:
            logger.error(f"Error recording API request metrics: {e}")
    
    def record_websocket_connection(self, building_id: str, action: str):
        """Record WebSocket connection metrics"""
        try:
            self.websocket_connections.labels(
                building_id=building_id,
                action=action
            ).inc()
            
            # Update active connections gauge
            if action == "connect":
                self.active_connections.labels(building_id=building_id).inc()
            elif action == "disconnect":
                self.active_connections.labels(building_id=building_id).dec()
                
        except Exception as e:
            logger.error(f"Error recording WebSocket connection metrics: {e}")
    
    def record_websocket_message(self, message_type: str, building_id: str):
        """Record WebSocket message metrics"""
        try:
            self.websocket_messages.labels(
                message_type=message_type,
                building_id=building_id
            ).inc()
            
        except Exception as e:
            logger.error(f"Error recording WebSocket message metrics: {e}")
    
    def record_cache_operation(self, operation: str, cache_type: str, result: str):
        """Record cache operation metrics"""
        try:
            self.cache_operations.labels(
                operation=operation,
                cache_type=cache_type,
                result=result
            ).inc()
            
        except Exception as e:
            logger.error(f"Error recording cache operation metrics: {e}")
    
    def record_jurisdiction_match(self, country: str, state: str, match_level: str):
        """Record jurisdiction matching metrics"""
        try:
            self.jurisdiction_matches.labels(
                country=country,
                state=state,
                match_level=match_level
            ).inc()
            
        except Exception as e:
            logger.error(f"Error recording jurisdiction match metrics: {e}")
    
    def record_mcp_file_loaded(self, file_type: str, jurisdiction: str):
        """Record MCP file loading metrics"""
        try:
            self.mcp_files_loaded.labels(
                file_type=file_type,
                jurisdiction=jurisdiction
            ).inc()
            
        except Exception as e:
            logger.error(f"Error recording MCP file loading metrics: {e}")
    
    def record_login_attempt(self, result: str, user_role: str):
        """Record login attempt metrics"""
        try:
            self.login_attempts.labels(
                result=result,
                user_role=user_role
            ).inc()
            
        except Exception as e:
            logger.error(f"Error recording login attempt metrics: {e}")
    
    def record_error(self, error_type: str, component: str):
        """Record error metrics"""
        try:
            self.errors_total.labels(
                error_type=error_type,
                component=component
            ).inc()
            
        except Exception as e:
            logger.error(f"Error recording error metrics: {e}")
    
    def record_validation_error(self, error_type: str, jurisdiction: str):
        """Record validation error metrics"""
        try:
            self.validation_errors.labels(
                error_type=error_type,
                jurisdiction=jurisdiction
            ).inc()
            
        except Exception as e:
            logger.error(f"Error recording validation error metrics: {e}")
    
    def update_cache_hit_ratio(self, cache_type: str, hit_ratio: float):
        """Update cache hit ratio gauge"""
        try:
            self.cache_hit_ratio.labels(cache_type=cache_type).set(hit_ratio)
            
        except Exception as e:
            logger.error(f"Error updating cache hit ratio: {e}")
    
    def update_memory_usage(self, component: str, usage_bytes: int):
        """Update memory usage gauge"""
        try:
            self.memory_usage.labels(component=component).set(usage_bytes)
            
        except Exception as e:
            logger.error(f"Error updating memory usage: {e}")
    
    def update_active_users(self, user_role: str, count: int):
        """Update active users gauge"""
        try:
            self.active_users.labels(user_role=user_role).set(count)
            
        except Exception as e:
            logger.error(f"Error updating active users: {e}")
    
    def update_active_sessions(self, user_role: str, count: int):
        """Update active sessions gauge"""
        try:
            self.active_sessions.labels(user_role=user_role).set(count)
            
        except Exception as e:
            logger.error(f"Error updating active sessions: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for monitoring"""
        try:
            # This would typically query the metrics registry
            # For now, return a basic summary
            return {
                "total_validation_requests": 0,  # Would be calculated from metrics
                "average_validation_duration": 0.0,
                "total_violations": 0,
                "total_warnings": 0,
                "cache_hit_ratio": 0.0,
                "active_connections": 0,
                "system_uptime_seconds": time.time() - self.start_time,
                "total_errors": 0,
                "active_users": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {"error": str(e)}
    
    def generate_metrics_response(self) -> Response:
        """Generate Prometheus metrics response"""
        try:
            metrics_data = generate_latest()
            return FastAPIResponse(
                content=metrics_data,
                media_type=CONTENT_TYPE_LATEST
            )
            
        except Exception as e:
            logger.error(f"Error generating metrics response: {e}")
            return FastAPIResponse(
                content=f"Error generating metrics: {str(e)}",
                status_code=500
            )


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Middleware for automatic API request metrics
class MetricsMiddleware:
    """Middleware for automatic API request metrics collection"""
    
    def __init__(self, app):
        self.app = app
        self.metrics = metrics_collector
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Record request start time
            start_time = time.time()
            
            # Get request details
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "/")
            
            # Create a simple response wrapper
            response_status = 200
            
            async def send_wrapper(message):
                nonlocal response_status
                if message["type"] == "http.response.start":
                    response_status = message.get("status", 200)
                await send(message)
            
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as e:
                response_status = 500
                self.metrics.record_error("unhandled_exception", "middleware")
                raise
            finally:
                # Record metrics
                duration = time.time() - start_time
                self.metrics.record_api_request(method, path, response_status, duration)
        else:
            await self.app(scope, receive, send)


# Convenience functions for metrics recording
def record_validation_metrics(metrics: ValidationMetrics):
    """Record validation metrics"""
    metrics_collector.record_validation(metrics)


def record_api_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record API request metrics"""
    metrics_collector.record_api_request(method, endpoint, status_code, duration)


def record_websocket_connection(building_id: str, action: str):
    """Record WebSocket connection metrics"""
    metrics_collector.record_websocket_connection(building_id, action)


def record_websocket_message(message_type: str, building_id: str):
    """Record WebSocket message metrics"""
    metrics_collector.record_websocket_message(message_type, building_id)


def record_cache_operation(operation: str, cache_type: str, result: str):
    """Record cache operation metrics"""
    metrics_collector.record_cache_operation(operation, cache_type, result)


def record_jurisdiction_match(country: str, state: str, match_level: str):
    """Record jurisdiction matching metrics"""
    metrics_collector.record_jurisdiction_match(country, state, match_level)


def record_error(error_type: str, component: str):
    """Record error metrics"""
    metrics_collector.record_error(error_type, component)


def record_validation_error(error_type: str, jurisdiction: str):
    """Record validation error metrics"""
    metrics_collector.record_validation_error(error_type, jurisdiction) 