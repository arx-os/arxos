"""
Physics Services Module

This module provides comprehensive physics simulation services including:
- Advanced thermal analysis
- Fluid dynamics simulation
- Structural analysis
- Electrical circuit simulation
- Signal propagation analysis

Author: Arxos Development Team
Date: December 2024
"""

from .advanced_thermal_analysis import (
    AdvancedThermalAnalysisService,
    PhaseChangeMaterial,
    TemperatureDependentProperty,
    AdvancedBoundaryCondition,
    BoundaryConditionType,
    MaterialPhase,
    NonLinearSolverSettings,
    AdaptiveMeshSettings
)

from .thermal_analysis import (
    ThermalAnalysisService,
    ThermalAnalysisRequest,
    ThermalAnalysisResult,
    HeatTransferType
)

from .thermal_integration import (
    ThermalIntegrationService,
    ThermalAnalysisMode,
    ThermalAnalysisConfig
)

from .fluid_dynamics import FluidDynamicsService
from .structural_analysis import StructuralAnalysisService
from .electrical_analysis import ElectricalAnalysisService
from .signal_propagation import SignalPropagationService

__all__ = [
    # Advanced Thermal Analysis
    'AdvancedThermalAnalysisService',
    'PhaseChangeMaterial',
    'TemperatureDependentProperty',
    'AdvancedBoundaryCondition',
    'BoundaryConditionType',
    'MaterialPhase',
    'NonLinearSolverSettings',
    'AdaptiveMeshSettings',
    
    # Basic Thermal Analysis
    'ThermalAnalysisService',
    'ThermalAnalysisRequest',
    'ThermalAnalysisResult',
    'HeatTransferType',
    
    # Thermal Integration
    'ThermalIntegrationService',
    'ThermalAnalysisMode',
    'ThermalAnalysisConfig',
    
    # Other Physics Services
    'FluidDynamicsService',
    'StructuralAnalysisService',
    'ElectricalAnalysisService',
    'SignalPropagationService'
] 