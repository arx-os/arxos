"""
SVGX Engine - Performance Monitor Module

This module re-exports the PerformanceMonitor from utils.performance
to maintain backward compatibility and resolve import issues.
"""

from svgx_engine.performance import (
    PerformanceMonitor,
    get_performance_monitor,
    monitor_operation,
    get_performance_report,
    clear_performance_data
)

__all__ = [
    'PerformanceMonitor',
    'get_performance_monitor',
    'monitor_operation',
    'get_performance_report',
    'clear_performance_data'
] 