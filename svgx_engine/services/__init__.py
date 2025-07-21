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
    from svgx_engine.services.database import SVGXDatabaseService as DatabaseService
except ImportError:
    DatabaseService = None

try:
    from svgx_engine.services.cache.redis_client import RedisCacheClient, get_cache_client, initialize_cache, close_cache
except ImportError:
    RedisCacheClient = None
    get_cache_client = None
    initialize_cache = None
    close_cache = None

try:
    from svgx_engine.services.logging.structured_logger import SVGXLogger, get_logger, setup_logging, logging_context
except ImportError:
    SVGXLogger = None
    get_logger = None
    setup_logging = None
    logging_context = None

try:
    from svgx_engine.services.metadata_service import SVGXMetadataService, SVGXObjectMetadata, SVGXSymbolMetadata, SVGXUserMetadata, SVGXExportMetadata
except ImportError:
    SVGXMetadataService = None
    SVGXObjectMetadata = None
    SVGXSymbolMetadata = None
    SVGXUserMetadata = None
    SVGXExportMetadata = None

# Symbol Management Services
try:
    from svgx_engine.services.symbol_manager import SVGXSymbolManager as SymbolManagerService
except ImportError:
    SymbolManagerService = None

try:
    from svgx_engine.services.symbol_recognition import SVGXSymbolRecognitionService as SymbolRecognitionService
except ImportError:
    SymbolRecognitionService = None

try:
    from svgx_engine.services.symbol_schema_validator import SVGXSchemaValidator, ValidationRule, ValidationResult, get_schema_validator, validate_symbol_schema, add_validation_rule, get_validation_statistics
except ImportError:
    SVGXSchemaValidator = None
    ValidationRule = None
    ValidationResult = None
    get_schema_validator = None
    validate_symbol_schema = None
    add_validation_rule = None
    get_validation_statistics = None

try:
    from svgx_engine.services.symbol_renderer import SVGXSymbolRenderer, RenderOptions, RenderResult, get_symbol_renderer, render_symbol, render_batch, get_rendering_capabilities
except ImportError:
    SVGXSymbolRenderer = None
    RenderOptions = None
    RenderResult = None
    get_symbol_renderer = None
    render_symbol = None
    render_batch = None
    get_rendering_capabilities = None

try:
    from svgx_engine.services.symbol_generator import SVGXSymbolGenerator, GenerationTemplate, GenerationOptions, GenerationResult, get_symbol_generator, generate_symbol, generate_batch, get_generation_statistics
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
    from svgx_engine.services.advanced_export import SVGXAdvancedExportService as AdvancedExportService
except ImportError:
    AdvancedExportService = None

try:
    from svgx_engine.services.export_interoperability import SVGXExportInteroperabilityService as ExportInteroperabilityService
except ImportError:
    ExportInteroperabilityService = None

try:
    from svgx_engine.services.persistence_export import SVGXPersistenceExportService as PersistenceExportService
except ImportError:
    PersistenceExportService = None

try:
    from svgx_engine.services.export_integration import SVGXExportIntegrationService, ScaleMetadata, ExportMetadata, ExportOptions
except ImportError:
    SVGXExportIntegrationService = None
    ScaleMetadata = None
    ExportMetadata = None
    ExportOptions = None

# BIM Integration Services
try:
    from svgx_engine.services.bim_builder import BIMBuilder as BIMBuilderService
except ImportError:
    BIMBuilderService = None

try:
    from svgx_engine.services.bim_export import SVGXBIMExportService as BIMExportService
except ImportError:
    BIMExportService = None

try:
    from svgx_engine.services.bim_validator import SVGXBIMValidatorService as BIMValidatorService
except ImportError:
    BIMValidatorService = None

try:
    from svgx_engine.services.bim_assembly import SVGXBIMAssemblyService as BIMAssemblyService
except ImportError:
    BIMAssemblyService = None

try:
    from svgx_engine.services.bim_health import SVGXBIMHealthCheckerService as BIMHealthService
except ImportError:
    BIMHealthService = None

try:
    from svgx_engine.services.bim_extractor import SVGXBIMExtractor as BIMExtractorService
except ImportError:
    BIMExtractorService = None

# Performance and Caching Services
try:
    from svgx_engine.services.advanced_caching import SVGXAdvancedCachingService as AdvancedCachingService
except ImportError:
    AdvancedCachingService = None

try:
    from svgx_engine.utils.performance import SVGXPerformanceProfiler as PerformanceService
except ImportError:
    PerformanceService = None

try:
    from svgx_engine.services.performance_optimizer import SVGXPerformanceOptimizer as PerformanceOptimizerService
except ImportError:
    PerformanceOptimizerService = None

# Security and Authentication Services
try:
    from svgx_engine.services.access_control import SVGXAccessControlService as AccessControlService
except ImportError:
    AccessControlService = None

try:
    from svgx_engine.services.advanced_security import SVGXAdvancedSecurityService as AdvancedSecurityService
except ImportError:
    AdvancedSecurityService = None

try:
    from svgx_engine.services.security import SVGXSecurityService as SecurityService
except ImportError:
    SecurityService = None

try:
    from svgx_engine.services.security_hardener import SVGXSecurityHardener as SecurityHardenerService
except ImportError:
    SecurityHardenerService = None

# Telemetry and Monitoring Services
try:
    from svgx_engine.utils.telemetry import SVGXTelemetryIngestor as TelemetryService
except ImportError:
    TelemetryService = None

try:
    from svgx_engine.services.realtime import SVGXRealtimeTelemetryServer as RealtimeService
except ImportError:
    RealtimeService = None

# Advanced Features Services
try:
    from svgx_engine.services.enhanced_simulation_engine import EnhancedSimulationEngine as EnhancedSimulationEngineService
except ImportError:
    EnhancedSimulationEngineService = None

try:
    from svgx_engine.services.interactive_capabilities import InteractiveCapabilitiesService
except ImportError:
    InteractiveCapabilitiesService = None

try:
    from svgx_engine.services.advanced_cad_features import AdvancedCADFeatures as AdvancedCADFeaturesService
except ImportError:
    AdvancedCADFeaturesService = None

try:
    from svgx_engine.services.realtime_collaboration import RealtimeCollaboration as RealtimeCollaborationService
except ImportError:
    RealtimeCollaborationService = None

# Error Handling Services
try:
    from svgx_engine.services.error_handler import SVGXErrorHandler as ErrorHandlerService, create_error_handler
except ImportError:
    ErrorHandlerService = None
    create_error_handler = None

# Database Models
try:
    from svgx_engine.database.models import (
        SVGXDatabaseModel,
        SVGXObjectModel,
        SVGXSymbolModel,
        SVGXUserModel,
        SVGXExportModel,
        SVGXMetadataModel,
        SVGXBehaviorModel,
        SVGXComplianceModel,
        SVGXPerformanceModel,
        SVGXSecurityModel,
        SVGXTelemetryModel,
        SVGXCollaborationModel,
        SVGXIntegrationModel,
        SVGXValidationModel,
        SVGXGenerationModel,
        SVGXRenderModel,
        SVGXExportModel,
        SVGXImportModel,
        SVGXTransformModel,
        SVGXAnalysisModel
    )
except ImportError:
    SVGXDatabaseModel = None
    SVGXObjectModel = None
    SVGXSymbolModel = None
    SVGXUserModel = None
    SVGXExportModel = None
    SVGXMetadataModel = None
    SVGXBehaviorModel = None
    SVGXComplianceModel = None
    SVGXPerformanceModel = None
    SVGXSecurityModel = None
    SVGXTelemetryModel = None
    SVGXCollaborationModel = None
    SVGXIntegrationModel = None
    SVGXValidationModel = None
    SVGXGenerationModel = None
    SVGXRenderModel = None
    SVGXExportModel = None
    SVGXImportModel = None
    SVGXTransformModel = None
    SVGXAnalysisModel = None

# Configuration
try:
    from svgx_engine.config.settings import (
        SVGXConfig,
        SVGXSettings,
        SVGXEnvironment,
        SVGXDatabaseConfig,
        SVGXCacheConfig,
        SVGXSecurityConfig,
        SVGXPerformanceConfig,
        SVGXTelemetryConfig,
        SVGXExportConfig,
        SVGXImportConfig,
        SVGXValidationConfig,
        SVGXGenerationConfig,
        SVGXRenderConfig,
        SVGXAnalysisConfig,
        SVGXCollaborationConfig,
        SVGXIntegrationConfig,
        SVGXComplianceConfig,
        SVGXBehaviorConfig,
        SVGXSymbolConfig,
        SVGXUserConfig,
        SVGXMetadataConfig
    )
except ImportError:
    SVGXConfig = None
    SVGXSettings = None
    SVGXEnvironment = None
    SVGXDatabaseConfig = None
    SVGXCacheConfig = None
    SVGXSecurityConfig = None
    SVGXPerformanceConfig = None
    SVGXTelemetryConfig = None
    SVGXExportConfig = None
    SVGXImportConfig = None
    SVGXValidationConfig = None
    SVGXGenerationConfig = None
    SVGXRenderConfig = None
    SVGXAnalysisConfig = None
    SVGXCollaborationConfig = None
    SVGXIntegrationConfig = None
    SVGXComplianceConfig = None
    SVGXBehaviorConfig = None
    SVGXSymbolConfig = None
    SVGXUserConfig = None
    SVGXMetadataConfig = None

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
    'SVGXDatabaseModel',
    'SVGXObjectModel',
    'SVGXSymbolModel',
    'SVGXUserModel',
    'SVGXExportModel',
    'SVGXMetadataModel',
    'SVGXBehaviorModel',
    'SVGXComplianceModel',
    'SVGXPerformanceModel',
    'SVGXSecurityModel',
    'SVGXTelemetryModel',
    'SVGXCollaborationModel',
    'SVGXIntegrationModel',
    'SVGXValidationModel',
    'SVGXGenerationModel',
    'SVGXRenderModel',
    'SVGXExportModel',
    'SVGXImportModel',
    'SVGXTransformModel',
    'SVGXAnalysisModel',
    
    # Configuration
    'SVGXConfig',
    'SVGXSettings',
    'SVGXEnvironment',
    'SVGXDatabaseConfig',
    'SVGXCacheConfig',
    'SVGXSecurityConfig',
    'SVGXPerformanceConfig',
    'SVGXTelemetryConfig',
    'SVGXExportConfig',
    'SVGXImportConfig',
    'SVGXValidationConfig',
    'SVGXGenerationConfig',
    'SVGXRenderConfig',
    'SVGXAnalysisConfig',
    'SVGXCollaborationConfig',
    'SVGXIntegrationConfig',
    'SVGXComplianceConfig',
    'SVGXBehaviorConfig',
    'SVGXSymbolConfig',
    'SVGXUserConfig',
    'SVGXMetadataConfig'
] 