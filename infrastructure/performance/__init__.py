"""
Performance Optimization Infrastructure Module.

Provides comprehensive performance monitoring, caching strategies,
and query optimization for the Arxos platform.
"""

from .monitoring import (
    PerformanceMonitor,
    MetricCollector,
    SystemResourceMonitor,
    DatabasePerformanceMonitor,
    ApplicationPerformanceMonitor,
    AlertManager,
    MetricType,
    AlertSeverity,
    PerformanceThreshold,
    performance_monitor,
    monitor_performance
)

from .caching_strategies import (
    IntelligentCache,
    MultiLevelCache,
    CacheWarmupManager,
    CacheStrategy,
    CacheLevel,
    CacheMetrics,
    intelligent_cache,
    multi_level_cache,
    cache_warmup_manager,
    cached
)

from .query_optimization import (
    QueryOptimizer,
    QueryCache,
    BatchQueryProcessor,
    QueryType,
    QueryComplexity,
    QueryProfile,
    query_optimizer,
    initialize_query_optimizer,
    optimized_query_execution
)


__all__ = [
    # Performance Monitoring
    "PerformanceMonitor",
    "MetricCollector",
    "SystemResourceMonitor",
    "DatabasePerformanceMonitor", 
    "ApplicationPerformanceMonitor",
    "AlertManager",
    "MetricType",
    "AlertSeverity",
    "PerformanceThreshold",
    "performance_monitor",
    "monitor_performance",
    
    # Caching Strategies
    "IntelligentCache",
    "MultiLevelCache",
    "CacheWarmupManager",
    "CacheStrategy",
    "CacheLevel", 
    "CacheMetrics",
    "intelligent_cache",
    "multi_level_cache",
    "cache_warmup_manager",
    "cached",
    
    # Query Optimization
    "QueryOptimizer",
    "QueryCache",
    "BatchQueryProcessor",
    "QueryType",
    "QueryComplexity",
    "QueryProfile",
    "query_optimizer", 
    "initialize_query_optimizer",
    "optimized_query_execution"
]


def initialize_performance_services(config: dict = None) -> dict:
    """Initialize all performance services with configuration."""
    config = config or {}
    
    # Start monitoring
    if config.get("enable_monitoring", True):
        performance_monitor.start_monitoring()
    
    # Start cache maintenance
    if config.get("enable_cache_maintenance", True):
        intelligent_cache.start_maintenance()
    
    # Set up cache warmup strategies
    if config.get("cache_warmup_strategies"):
        for name, strategy in config["cache_warmup_strategies"].items():
            cache_warmup_manager.register_warmup_strategy(name, strategy)
    
    # Configure alert callbacks
    if config.get("alert_callbacks"):
        for callback in config["alert_callbacks"]:
            performance_monitor.alert_manager.add_alert_callback(callback)
    
    services = {
        "performance_monitor": performance_monitor,
        "intelligent_cache": intelligent_cache,
        "multi_level_cache": multi_level_cache,
        "cache_warmup_manager": cache_warmup_manager,
        "query_optimizer": query_optimizer
    }
    
    return services


def get_performance_status() -> dict:
    """Get status of all performance services."""
    return {
        "monitoring": {
            "active": performance_monitor.monitoring_active,
            "metrics_count": len(performance_monitor.collector.metrics),
            "active_alerts": len(performance_monitor.alert_manager.get_active_alerts())
        },
        "caching": {
            "l1_cache": intelligent_cache.get_metrics(),
            "cache_warmup": {
                "strategies_registered": len(cache_warmup_manager.warmup_strategies)
            }
        },
        "query_optimization": {
            "profiles_tracked": len(query_optimizer.query_profiles) if query_optimizer else 0,
            "optimization_cache_size": len(query_optimizer.optimization_cache) if query_optimizer else 0
        }
    }


def generate_performance_report() -> dict:
    """Generate comprehensive performance report."""
    report = {
        "timestamp": performance_monitor.collector.metadata.get("last_report", "N/A"),
        "system_performance": performance_monitor.get_performance_report(),
        "cache_performance": {
            "l1_cache": intelligent_cache.get_metrics(),
            "multi_level_cache": {
                "l1_entries": len(multi_level_cache.levels[CacheLevel.L1_MEMORY].cache),
                "promotion_threshold": multi_level_cache.promotion_threshold
            }
        }
    }
    
    if query_optimizer:
        report["query_performance"] = query_optimizer.get_optimization_report()
    
    return report


def optimize_for_workload(workload_type: str) -> None:
    """Optimize performance settings for specific workload type."""
    if workload_type == "read_heavy":
        # Optimize for read-heavy workloads
        intelligent_cache.strategy = CacheStrategy.LRU
        intelligent_cache.default_ttl = 7200  # Longer TTL
        
        # Enable aggressive caching
        if hasattr(multi_level_cache, 'promotion_threshold'):
            multi_level_cache.promotion_threshold = 2  # Promote faster
        
    elif workload_type == "write_heavy":
        # Optimize for write-heavy workloads
        intelligent_cache.strategy = CacheStrategy.ADAPTIVE
        intelligent_cache.default_ttl = 1800  # Shorter TTL
        
        # Reduce cache pressure
        if hasattr(multi_level_cache, 'promotion_threshold'):
            multi_level_cache.promotion_threshold = 5  # Promote slower
        
    elif workload_type == "mixed":
        # Balanced optimization
        intelligent_cache.strategy = CacheStrategy.ADAPTIVE
        intelligent_cache.default_ttl = 3600  # Default TTL
        
    performance_monitor.collector.record_metric(
        "performance.optimization.workload_change",
        1.0,
        MetricType.COUNTER,
        {"workload_type": workload_type}
    )


# Auto-initialize on import with default configuration
_services = initialize_performance_services()