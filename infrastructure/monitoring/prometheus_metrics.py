"""
Prometheus Metrics Collection for MCP Engineering

This module provides comprehensive metrics collection for the MCP Engineering API,
including request metrics, performance metrics, and business metrics.
"""

import time
import psutil
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    multiprocess,
)


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""

    enable_metrics: bool = True
    metrics_port: int = 8000
    metrics_path: str = "/metrics"
    enable_multiprocess: bool = False


class MCPEngineeringMetrics:
    """Comprehensive metrics collection for MCP Engineering."""

    def __init__(self, config: MetricsConfig):
        """
        Initialize metrics collection.

        Args:
            config: Metrics configuration
        """
        self.config = config

        # Create registry
        if config.enable_multiprocess:
            self.registry = multiprocess.MultiProcessCollector()
        else:
            self.registry = CollectorRegistry()

        # HTTP request metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            registry=self.registry,
        )

        # Business metrics
        self.building_validations_total = Counter(
            "building_validations_total",
            "Total number of building validations",
            ["validation_type", "status"],
            registry=self.registry,
        )

        self.ai_recommendations_total = Counter(
            "ai_recommendations_total",
            "Total number of AI recommendations",
            ["recommendation_type", "confidence_level"],
            registry=self.registry,
        )

        self.ml_predictions_total = Counter(
            "ml_predictions_total",
            "Total number of ML predictions",
            ["prediction_type", "accuracy_level"],
            registry=self.registry,
        )

        # Performance metrics
        self.database_query_duration_seconds = Histogram(
            "database_query_duration_seconds",
            "Database query duration in seconds",
            ["query_type", "table"],
            registry=self.registry,
        )

        self.cache_hit_ratio = Gauge(
            "cache_hit_ratio",
            "Cache hit ratio percentage",
            ["cache_type"],
            registry=self.registry,
        )

        self.active_connections = Gauge(
            "active_connections",
            "Number of active connections",
            ["connection_type"],
            registry=self.registry,
        )

        # System metrics
        self.cpu_usage_percent = Gauge(
            "cpu_usage_percent", "CPU usage percentage", registry=self.registry
        )

        self.memory_usage_bytes = Gauge(
            "memory_usage_bytes", "Memory usage in bytes", registry=self.registry
        )

        self.disk_usage_percent = Gauge(
            "disk_usage_percent", "Disk usage percentage", registry=self.registry
        )

        # Error metrics
        self.errors_total = Counter(
            "errors_total",
            "Total number of errors",
            ["error_type", "severity"],
            registry=self.registry,
        )

        # Custom business metrics
        self.validation_accuracy = Gauge(
            "validation_accuracy",
            "Validation accuracy percentage",
            ["validation_type"],
            registry=self.registry,
        )

        self.recommendation_effectiveness = Gauge(
            "recommendation_effectiveness",
            "Recommendation effectiveness score",
            ["recommendation_type"],
            registry=self.registry,
        )

    def record_http_request(
        self, method: str, endpoint: str, status: int, duration: float
    ):
        """
        Record an HTTP request.

        Args:
            method: HTTP method
            endpoint: Request endpoint
            status: HTTP status code
            duration: Request duration in seconds
        """
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status=status
        ).inc()
        self.http_request_duration_seconds.labels(
            method=method, endpoint=endpoint
        ).observe(duration)

    def record_building_validation(self, validation_type: str, status: str):
        """
        Record a building validation.

        Args:
            validation_type: Type of validation
            status: Validation status
        """
        self.building_validations_total.labels(
            validation_type=validation_type, status=status
        ).inc()

    def record_ai_recommendation(self, recommendation_type: str, confidence_level: str):
        """
        Record an AI recommendation.

        Args:
            recommendation_type: Type of recommendation
            confidence_level: Confidence level
        """
        self.ai_recommendations_total.labels(
            recommendation_type=recommendation_type, confidence_level=confidence_level
        ).inc()

    def record_ml_prediction(self, prediction_type: str, accuracy_level: str):
        """
        Record an ML prediction.

        Args:
            prediction_type: Type of prediction
            accuracy_level: Accuracy level
        """
        self.ml_predictions_total.labels(
            prediction_type=prediction_type, accuracy_level=accuracy_level
        ).inc()

    def record_database_query(self, query_type: str, table: str, duration: float):
        """
        Record a database query.

        Args:
            query_type: Type of query
            table: Database table
            duration: Query duration in seconds
        """
        self.database_query_duration_seconds.labels(
            query_type=query_type, table=table
        ).observe(duration)

    def update_cache_hit_ratio(self, cache_type: str, hit_ratio: float):
        """
        Update cache hit ratio.

        Args:
            cache_type: Type of cache
            hit_ratio: Hit ratio percentage
        """
        self.cache_hit_ratio.labels(cache_type=cache_type).set(hit_ratio)

    def update_active_connections(self, connection_type: str, count: int):
        """
        Update active connections count.

        Args:
            connection_type: Type of connection
            count: Number of active connections
        """
        self.active_connections.labels(connection_type=connection_type).set(count)

    def update_system_metrics(self):
        """Update system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_usage_percent.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage_bytes.set(memory.used)

        # Disk usage
        disk = psutil.disk_usage("/")
        self.disk_usage_percent.set(disk.percent)

    def record_error(self, error_type: str, severity: str):
        """
        Record an error.

        Args:
            error_type: Type of error
            severity: Error severity
        """
        self.errors_total.labels(error_type=error_type, severity=severity).inc()

    def update_validation_accuracy(self, validation_type: str, accuracy: float):
        """
        Update validation accuracy.

        Args:
            validation_type: Type of validation
            accuracy: Accuracy percentage
        """
        self.validation_accuracy.labels(validation_type=validation_type).set(accuracy)

    def update_recommendation_effectiveness(
        self, recommendation_type: str, effectiveness: float
    ):
        """
        Update recommendation effectiveness.

        Args:
            recommendation_type: Type of recommendation
            effectiveness: Effectiveness score
        """
        self.recommendation_effectiveness.labels(
            recommendation_type=recommendation_type
        ).set(effectiveness)

    def get_metrics(self) -> str:
        """
        Get metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest(self.registry)

    def get_metrics_content_type(self) -> str:
        """
        Get metrics content type.

        Returns:
            Content type for metrics
        """
        return CONTENT_TYPE_LATEST


class MetricsMiddleware:
    """FastAPI middleware for metrics collection."""

    def __init__(self, metrics: MCPEngineeringMetrics):
        """
        Initialize metrics middleware.

        Args:
            metrics: Metrics collection instance
        """
        self.metrics = metrics

    async def record_request(self, request, response, duration: float):
        """
        Record request metrics.

        Args:
            request: FastAPI request object
            response: FastAPI response object
            duration: Request duration in seconds
        """
        method = request.method
        endpoint = request.url.path
        status = response.status_code

        self.metrics.record_http_request(method, endpoint, status, duration)

    async def update_system_metrics(self):
        """Update system metrics."""
        self.metrics.update_system_metrics()


# Global metrics instance
metrics_config = MetricsConfig()
metrics = MCPEngineeringMetrics(metrics_config)
