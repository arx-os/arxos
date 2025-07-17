"""
SVGX Engine - Main Package

SVGX Engine is a comprehensive SVG processing and BIM integration engine
that provides advanced capabilities for building information modeling,
symbol recognition, and spatial analysis.
"""

# Core SVGX Engine components
from svgx_engine.parser import SVGXParser
from svgx_engine.runtime import SVGXRuntime
from svgx_engine.compiler import SVGXCompiler

# SVGX Engine utilities
from svgx_engine.utils.errors import SVGXError, ValidationError, ExportError, ImportError, PerformanceError
from svgx_engine.utils.performance import PerformanceMonitor
from svgx_engine.utils.telemetry import TelemetryLogger

# SVGX Engine services
from svgx_engine.services.export_integration import SVGXExportIntegrationService, ScaleMetadata, ExportMetadata, ExportOptions
from svgx_engine.services.metadata_service import SVGXMetadataService, SVGXObjectMetadata, SVGXSymbolMetadata, SVGXUserMetadata, SVGXExportMetadata
from svgx_engine.services.bim_health import SVGXBIMHealthCheckerService, ValidationStatus, IssueType, FixType, ValidationIssue, ValidationResult, BehaviorProfile
from svgx_engine.services.logic_engine import LogicEngine, RuleType, RuleStatus, ExecutionStatus, DataType, Rule, RuleExecution, RuleChain, DataContext
from svgx_engine.services.bim_assembly import SVGXBIMAssemblyService, AssemblyStep, ConflictType, ValidationLevel, AssemblyConflict, AssemblyResult, AssemblyConfig

# SVGX Engine models
from svgx_engine.models.svgx import SVGXDocument, SVGXElement, SVGXObject, ArxObject, ArxBehavior, ArxPhysics
from svgx_engine.models.bim import BIMElement, BIMSystem, BIMSpace, Geometry, GeometryType, SystemType, ElementCategory

# Import services module for direct access
import svgx_engine.services

__version__ = "1.0.0"
__author__ = "SVGX Engine Team"
__description__ = "Advanced SVG processing and BIM integration engine"

__all__ = [
    # Core components
    'SVGXParser',
    'SVGXRuntime', 
    'SVGXCompiler',
    
    # Services module
    'services',
    
    # Services
    'SVGXExportIntegrationService',
    'SVGXMetadataService',
    'SVGXBIMHealthCheckerService',
    'LogicEngine',
    'SVGXBIMAssemblyService',
    
    # Models
    'SVGXDocument',
    'SVGXElement',
    'SVGXObject',
    'ArxObject',
    'ArxBehavior',
    'ArxPhysics',
    'BIMElement',
    'BIMSystem',
    'BIMSpace',
    'Geometry',
    'GeometryType',
    'SystemType',
    'ElementCategory',
    
    # Utilities
    'SVGXError',
    'ValidationError',
    'ExportError',
    'ImportError',
    'PerformanceError',
    'PerformanceMonitor',
    'TelemetryLogger',
    
    # Metadata types
    'SVGXObjectMetadata',
    'SVGXSymbolMetadata',
    'SVGXUserMetadata',
    'SVGXExportMetadata',
    'ScaleMetadata',
    'ExportMetadata',
    'ExportOptions',
    
    # BIM Health types
    'ValidationStatus',
    'IssueType',
    'FixType',
    'ValidationIssue',
    'ValidationResult',
    'BehaviorProfile',
    
    # Logic Engine types
    'RuleType',
    'RuleStatus',
    'ExecutionStatus',
    'DataType',
    'Rule',
    'RuleExecution',
    'RuleChain',
    'DataContext',
    
    # BIM Assembly types
    'AssemblyStep',
    'ConflictType',
    'ValidationLevel',
    'AssemblyConflict',
    'AssemblyResult',
    'AssemblyConfig'
] 