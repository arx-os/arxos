"""
SVGX Engine Services Package

This package contains all the core services for the SVGX Engine.
"""

from .access_control import AccessControlService
from .advanced_security import (
    AdvancedSecurityService,
    PrivacyControlsService,
    EncryptionService,
    AuditTrailService,
    RBACService,
    DataClassification,
    PermissionLevel,
    AuditEventType,
    SecurityMetrics
)
from .advanced_caching import (
    AdvancedCachingSystem,
    MemoryCache,
    DiskCache,
    DatabaseCache,
    SVGXCacheKeyGenerator,
    CacheLevel,
    CachePolicy,
    SVGXCacheType,
    CacheMetrics,
    CacheEntry
)

from .telemetry import (
    SVGXTelemetryBuffer,
    SVGXTelemetryIngestor,
    SVGXTelemetryHook,
    SVGXTelemetryRecord,
    SVGXTelemetryType,
    SVGXTelemetrySeverity,
    generate_svgx_simulated_telemetry,
    create_svgx_telemetry_buffer,
    create_svgx_telemetry_ingestor,
    create_svgx_telemetry_hook
)

from .performance import (
    SVGXPerformanceOptimizer,
    SVGXAdaptiveCache,
    SVGXMemoryManager,
    SVGXParallelProcessor,
    SVGXPerformanceProfiler,
    SVGXPerformanceMetrics,
    SVGXResourceLimits,
    OptimizationLevel,
    CacheStrategy,
    optimize_operation,
    parallel_process,
    get_performance_report
)

from .bim_extractor import (
    SVGXBIMExtractor,
    SVGXElementType,
    SVGXGeometryType,
    SVGXElementMetadata,
    extract_bim_from_svg
)

__all__ = [
    'AccessControlService',
    'AdvancedSecurityService',
    'PrivacyControlsService',
    'EncryptionService',
    'AuditTrailService',
    'RBACService',
    'DataClassification',
    'PermissionLevel',
    'AuditEventType',
    'SecurityMetrics',
    'AdvancedCachingSystem',
    'MemoryCache',
    'DiskCache',
    'DatabaseCache',
    'SVGXCacheKeyGenerator',
    'CacheLevel',
    'CachePolicy',
    'SVGXCacheType',
    'CacheMetrics',
    'CacheEntry',
    'SVGXTelemetryBuffer',
    'SVGXTelemetryIngestor',
    'SVGXTelemetryHook',
    'SVGXTelemetryRecord',
    'SVGXTelemetryType',
    'SVGXTelemetrySeverity',
    'generate_svgx_simulated_telemetry',
    'create_svgx_telemetry_buffer',
    'create_svgx_telemetry_ingestor',
    'create_svgx_telemetry_hook',
    'SVGXPerformanceOptimizer',
    'SVGXAdaptiveCache',
    'SVGXMemoryManager',
    'SVGXParallelProcessor',
    'SVGXPerformanceProfiler',
    'SVGXPerformanceMetrics',
    'SVGXResourceLimits',
    'OptimizationLevel',
    'CacheStrategy',
    'optimize_operation',
    'parallel_process',
    'get_performance_report',
    'SVGXBIMExtractor',
    'SVGXElementType',
    'SVGXGeometryType',
    'SVGXElementMetadata',
    'extract_bim_from_svg'
] 