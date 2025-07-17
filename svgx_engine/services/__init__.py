"""
SVGX Engine - Services Package

Provides all services for SVGX Engine including:
- Database and persistence services
- Caching and performance services
- Logging and monitoring services
- Symbol management services
- Rendering and generation services
- Security and authentication services
"""

# Database and Infrastructure Services
try:
    from .database import SVGXDatabaseService as DatabaseService
except ImportError:
    DatabaseService = None

try:
    from .cache.redis_client import RedisCacheClient, get_cache_client, initialize_cache, close_cache
except ImportError:
    RedisCacheClient = None
    get_cache_client = None
    initialize_cache = None
    close_cache = None

try:
    from .logging.structured_logger import SVGXLogger, get_logger, setup_logging, logging_context
except ImportError:
    SVGXLogger = None
    get_logger = None
    setup_logging = None
    logging_context = None

try:
    from .metadata_service import SVGXMetadataService, SVGXObjectMetadata, SVGXSymbolMetadata, SVGXUserMetadata, SVGXExportMetadata
except ImportError:
    SVGXMetadataService = None
    SVGXObjectMetadata = None
    SVGXSymbolMetadata = None
    SVGXUserMetadata = None
    SVGXExportMetadata = None

# Symbol Management Services
try:
    from .symbol_manager import SVGXSymbolManager as SymbolManagerService
except ImportError:
    SymbolManagerService = None

try:
    from .symbol_recognition import SVGXSymbolRecognitionService as SymbolRecognitionService
except ImportError:
    SymbolRecognitionService = None

try:
    from .symbol_schema_validator import SVGXSchemaValidator, ValidationRule, ValidationResult, get_schema_validator, validate_symbol_schema, add_validation_rule, get_validation_statistics
except ImportError:
    SVGXSchemaValidator = None
    ValidationRule = None
    ValidationResult = None
    get_schema_validator = None
    validate_symbol_schema = None
    add_validation_rule = None
    get_validation_statistics = None

try:
    from .symbol_renderer import SVGXSymbolRenderer, RenderOptions, RenderResult, get_symbol_renderer, render_symbol, render_batch, get_rendering_capabilities
except ImportError:
    SVGXSymbolRenderer = None
    RenderOptions = None
    RenderResult = None
    get_symbol_renderer = None
    render_symbol = None
    render_batch = None
    get_rendering_capabilities = None

try:
    from .symbol_generator import SVGXSymbolGenerator, GenerationTemplate, GenerationOptions, GenerationResult, get_symbol_generator, generate_symbol, generate_batch, get_generation_statistics
except ImportError:
    SVGXSymbolGenerator = None
    GenerationTemplate = None
    GenerationOptions = None
    GenerationResult = None
    get_symbol_generator = None
    generate_symbol = None
    generate_batch = None
    get_generation_statistics = None

# Export and Interoperability Services
try:
    from .advanced_export import SVGXAdvancedExportService as AdvancedExportService
except ImportError:
    AdvancedExportService = None

try:
    from .export_interoperability import SVGXExportInteroperabilityService as ExportInteroperabilityService
except ImportError:
    ExportInteroperabilityService = None

try:
    from .persistence_export import SVGXPersistenceExportService as PersistenceExportService
except ImportError:
    PersistenceExportService = None

try:
    from .export_integration import SVGXExportIntegrationService, ScaleMetadata, ExportMetadata, ExportOptions
except ImportError:
    SVGXExportIntegrationService = None
    ScaleMetadata = None
    ExportMetadata = None
    ExportOptions = None

# BIM Integration Services
try:
    from .bim_builder import BIMBuilder as BIMBuilderService
except ImportError:
    BIMBuilderService = None

try:
    from .bim_export import SVGXBIMExportService as BIMExportService
except ImportError:
    BIMExportService = None

try:
    from .bim_validator import SVGXBIMValidatorService as BIMValidatorService
except ImportError:
    BIMValidatorService = None

try:
    from .bim_assembly import SVGXBIMAssemblyService as BIMAssemblyService
except ImportError:
    BIMAssemblyService = None

try:
    from .bim_health import SVGXBIMHealthCheckerService as BIMHealthService
except ImportError:
    BIMHealthService = None

try:
    from .bim_extractor import SVGXBIMExtractor as BIMExtractorService
except ImportError:
    BIMExtractorService = None

# Performance and Caching Services
try:
    from .advanced_caching import SVGXAdvancedCachingService as AdvancedCachingService
except ImportError:
    AdvancedCachingService = None

try:
    from .performance import SVGXPerformanceProfiler as PerformanceService
except ImportError:
    PerformanceService = None

try:
    from .performance_optimizer import SVGXPerformanceOptimizer as PerformanceOptimizerService
except ImportError:
    PerformanceOptimizerService = None

# Security and Authentication Services
try:
    from .access_control import SVGXAccessControlService as AccessControlService
except ImportError:
    AccessControlService = None

try:
    from .advanced_security import SVGXAdvancedSecurityService as AdvancedSecurityService
except ImportError:
    AdvancedSecurityService = None

try:
    from .security import SVGXSecurityService as SecurityService
except ImportError:
    SecurityService = None

try:
    from .security_hardener import SVGXSecurityHardener as SecurityHardenerService
except ImportError:
    SecurityHardenerService = None

# Telemetry and Monitoring Services
try:
    from .telemetry import SVGXTelemetryIngestor as TelemetryService
except ImportError:
    TelemetryService = None

try:
    from .realtime import SVGXRealtimeTelemetryServer as RealtimeService
except ImportError:
    RealtimeService = None

# Advanced Features Services
try:
    from .enhanced_simulation_engine import EnhancedSimulationEngine as EnhancedSimulationEngineService
except ImportError:
    EnhancedSimulationEngineService = None

try:
    from .interactive_capabilities import InteractiveCapabilitiesService
except ImportError:
    InteractiveCapabilitiesService = None

try:
    from .advanced_cad_features import AdvancedCADFeatures as AdvancedCADFeaturesService
except ImportError:
    AdvancedCADFeaturesService = None

try:
    from .realtime_collaboration import RealtimeCollaboration as RealtimeCollaborationService
except ImportError:
    RealtimeCollaborationService = None

# Error Handling Services
try:
    from .error_handler import SVGXErrorHandler as ErrorHandlerService, create_error_handler
except ImportError:
    ErrorHandlerService = None
    create_error_handler = None

# Database Models
try:
    from ..database.models import (
        SVGXDocument, SVGXElement, Symbol, SymbolUsage, User,
        CollaborationSession, CollaborationOperation, ExportHistory,
        PerformanceMetric, TelemetryEvent
    )
except ImportError:
    # Fallback if database models don't exist
    SVGXDocument = None
    SVGXElement = None
    Symbol = None
    SymbolUsage = None
    User = None
    CollaborationSession = None
    CollaborationOperation = None
    ExportHistory = None
    PerformanceMetric = None
    TelemetryEvent = None

# Configuration
try:
    from ..config.settings import (
        SVGXConfig, DatabaseConfig, RedisConfig, LoggingConfig,
        SecurityConfig, PerformanceConfig, APIConfig, ServerConfig,
        MonitoringConfig, get_config, load_config, reload_config
    )
except ImportError:
    # Fallback if config doesn't exist
    SVGXConfig = None
    DatabaseConfig = None
    RedisConfig = None
    LoggingConfig = None
    SecurityConfig = None
    PerformanceConfig = None
    APIConfig = None
    ServerConfig = None
    MonitoringConfig = None
    get_config = None
    load_config = None
    reload_config = None

__all__ = [
    # Database and Infrastructure
    'DatabaseService',
    'RedisCacheClient', 'get_cache_client', 'initialize_cache', 'close_cache',
    'SVGXLogger', 'get_logger', 'setup_logging', 'logging_context',
    
    # Symbol Management
    'SymbolManagerService',
    'SymbolRecognitionService',
    'SVGXSchemaValidator', 'ValidationRule', 'ValidationResult',
    'get_schema_validator', 'validate_symbol_schema', 'add_validation_rule', 'get_validation_statistics',
    'SVGXSymbolRenderer', 'RenderOptions', 'RenderResult',
    'get_symbol_renderer', 'render_symbol', 'render_batch', 'get_rendering_capabilities',
    'SVGXSymbolGenerator', 'GenerationTemplate', 'GenerationOptions', 'GenerationResult',
    'get_symbol_generator', 'generate_symbol', 'generate_batch', 'get_generation_statistics',
    
    # Export and Interoperability
    'AdvancedExportService',
    'ExportInteroperabilityService',
    'PersistenceExportService',
    'SVGXExportIntegrationService', 'ScaleMetadata', 'ExportMetadata', 'ExportOptions',
    
    # BIM Integration
    'BIMBuilderService',
    'BIMExportService',
    'BIMValidatorService',
    'BIMAssemblyService',
    'BIMHealthService',
    'BIMExtractorService',
    
    # Performance and Caching
    'AdvancedCachingService',
    'PerformanceService',
    'PerformanceOptimizerService',
    
    # Security and Authentication
    'AccessControlService',
    'AdvancedSecurityService',
    'SecurityService',
    'SecurityHardenerService',
    
    # Telemetry and Monitoring
    'TelemetryService',
    'RealtimeService',
    
    # Advanced Features
    'EnhancedSimulationEngineService',
    'InteractiveCapabilitiesService',
    'AdvancedCADFeaturesService',
    'RealtimeCollaborationService',
    
    # Error Handling
    'ErrorHandlerService',
    
    # Database Models
    'SVGXDocument', 'SVGXElement', 'Symbol', 'SymbolUsage', 'User',
    'CollaborationSession', 'CollaborationOperation', 'ExportHistory',
    'PerformanceMetric', 'TelemetryEvent',
    
    # Configuration
    'SVGXConfig', 'DatabaseConfig', 'RedisConfig', 'LoggingConfig',
    'SecurityConfig', 'PerformanceConfig', 'APIConfig', 'ServerConfig',
    'MonitoringConfig', 'get_config', 'load_config', 'reload_config'
] 