"""
Physics Integration Service for Main Behavior Engine

This service provides the critical integration layer between the enhanced physics engine
and the main behavior engine, enabling real-time physics calculations in BIM behavior simulation.

🎯 **Core Integration Features:**
- Real-time physics calculations for behavior simulation
- Multi-physics coupling for complex building systems
- Performance optimization and caching
- Error handling and validation
- Enterprise-grade reliability and scalability

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from datetime import datetime

from svgx_engine.services.enhanced_physics_engine import (
    EnhancedPhysicsEngine, PhysicsConfig, PhysicsType, PhysicsResult
)
from svgx_engine.utils.performance import PerformanceMonitor
from svgx_engine.utils.errors import PhysicsError, IntegrationError, ValidationError

logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    """Types of physics integration."""
    REAL_TIME = "real_time"
    BATCH = "batch"
    ON_DEMAND = "on_demand"
    SCHEDULED = "scheduled"


class PhysicsBehaviorType(Enum):
    """Types of physics behavior integration."""
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    STRUCTURAL = "structural"
    THERMAL = "thermal"
    ACOUSTIC = "acoustic"
    FIRE_PROTECTION = "fire_protection"
    SECURITY = "security"
    LIGHTING = "lighting"
    ENVIRONMENTAL = "environmental"


@dataclass
class PhysicsIntegrationConfig:
    """Configuration for physics integration service."""
    integration_type: IntegrationType = IntegrationType.REAL_TIME
    physics_enabled: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    max_concurrent_calculations: int = 10
    performance_monitoring: bool = True
    error_handling: bool = True
    validation_enabled: bool = True
    ai_optimization_enabled: bool = True


@dataclass
class PhysicsBehaviorRequest:
    """Request for physics behavior calculation."""
    element_id: str
    behavior_type: PhysicsBehaviorType
    physics_type: PhysicsType
    element_data: Dict[str, Any]
    environmental_data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


@dataclass
class PhysicsBehaviorResult:
    """Result of physics behavior calculation."""
    element_id: str
    behavior_type: PhysicsBehaviorType
    physics_type: PhysicsType
    physics_result: PhysicsResult
    behavior_state: str
    recommendations: List[str]
    alerts: List[str]
    performance_metrics: Dict[str, Any]
    timestamp: datetime


class PhysicsIntegrationService:
    """
    Physics integration service that connects enhanced physics engine to behavior engine.
    
    This service provides the critical missing integration layer between physics calculations
    and behavior simulation, enabling real-time physics-based behavior modeling.
    """
    
    def __init__(self, config: Optional[PhysicsIntegrationConfig] = None):
        """Initialize the physics integration service."""
        self.config = config or PhysicsIntegrationConfig()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize enhanced physics engine
        physics_config = PhysicsConfig(
            ai_optimization_enabled=self.config.ai_optimization_enabled,
            performance_monitoring=self.config.performance_monitoring
        )
        self.physics_engine = EnhancedPhysicsEngine(physics_config)
        
        # Integration state tracking
        self.integration_history: Dict[str, List[PhysicsBehaviorResult]] = {}
        self.active_calculations: Dict[str, PhysicsBehaviorRequest] = {}
        self.cache: Dict[str, PhysicsBehaviorResult] = {}
        
        # Performance tracking
        self.calculation_times: Dict[str, List[float]] = {}
        self.integration_metrics: Dict[str, Any] = {}
        
        logger.info("Physics integration service initialized")
    
    def calculate_physics_behavior(
        self, 
        request: PhysicsBehaviorRequest
    ) -> PhysicsBehaviorResult:
        """
        Calculate physics behavior for a specific element and behavior type.
        
        Args:
            request: Physics behavior calculation request
            
        Returns:
            PhysicsBehaviorResult with physics calculations and behavior state
        """
        start_time = time.time()
        
        try:
            # Validate request
            if not self._validate_request(request):
                raise ValidationError(f"Invalid physics behavior request: {request.element_id}")
            
            # Check cache if enabled
            if self.config.cache_enabled:
                cached_result = self._get_cached_result(request)
                if cached_result:
                    logger.debug(f"Using cached result for {request.element_id}")
                    return cached_result
            
            # Calculate physics
            physics_result = self.physics_engine.calculate_physics(
                request.physics_type, 
                request.element_data
            )
            
            # Determine behavior state based on physics results
            behavior_state = self._determine_behavior_state(
                request.behavior_type, 
                physics_result, 
                request.environmental_data
            )
            
            # Generate recommendations and alerts
            recommendations = self._generate_recommendations(
                request.behavior_type, 
                physics_result, 
                behavior_state
            )
            
            alerts = self._generate_alerts(
                request.behavior_type, 
                physics_result, 
                behavior_state
            )
            
            # Create result
            result = PhysicsBehaviorResult(
                element_id=request.element_id,
                behavior_type=request.behavior_type,
                physics_type=request.physics_type,
                physics_result=physics_result,
                behavior_state=behavior_state,
                recommendations=recommendations,
                alerts=alerts,
                performance_metrics=self._get_performance_metrics(start_time),
                timestamp=datetime.now()
            )
            
            # Cache result if enabled
            if self.config.cache_enabled:
                self._cache_result(request, result)
            
            # Store in history
            self._store_in_history(result)
            
            # Update performance metrics
            self._update_integration_metrics(request, result, time.time() - start_time)
            
            logger.info(f"Physics behavior calculated for {request.element_id}: {behavior_state}")
            return result
            
        except Exception as e:
            logger.error(f"Physics behavior calculation failed: {e}")
            raise IntegrationError(f"Physics behavior calculation failed: {e}")
    
    def simulate_hvac_behavior(self, element_id: str, element_data: Dict[str, Any]) -> PhysicsBehaviorResult:
        """Simulate HVAC behavior with physics calculations."""
        request = PhysicsBehaviorRequest(
            element_id=element_id,
            behavior_type=PhysicsBehaviorType.HVAC,
            physics_type=PhysicsType.FLUID_DYNAMICS,
            element_data=element_data
        )
        return self.calculate_physics_behavior(request)
    
    def simulate_electrical_behavior(self, element_id: str, element_data: Dict[str, Any]) -> PhysicsBehaviorResult:
        """Simulate electrical behavior with physics calculations."""
        request = PhysicsBehaviorRequest(
            element_id=element_id,
            behavior_type=PhysicsBehaviorType.ELECTRICAL,
            physics_type=PhysicsType.ELECTRICAL,
            element_data=element_data
        )
        return self.calculate_physics_behavior(request)
    
    def simulate_structural_behavior(self, element_id: str, element_data: Dict[str, Any]) -> PhysicsBehaviorResult:
        """Simulate structural behavior with physics calculations."""
        request = PhysicsBehaviorRequest(
            element_id=element_id,
            behavior_type=PhysicsBehaviorType.STRUCTURAL,
            physics_type=PhysicsType.STRUCTURAL,
            element_data=element_data
        )
        return self.calculate_physics_behavior(request)
    
    def simulate_thermal_behavior(self, element_id: str, element_data: Dict[str, Any]) -> PhysicsBehaviorResult:
        """Simulate thermal behavior with physics calculations."""
        request = PhysicsBehaviorRequest(
            element_id=element_id,
            behavior_type=PhysicsBehaviorType.THERMAL,
            physics_type=PhysicsType.THERMAL,
            element_data=element_data
        )
        return self.calculate_physics_behavior(request)
    
    def simulate_acoustic_behavior(self, element_id: str, element_data: Dict[str, Any]) -> PhysicsBehaviorResult:
        """Simulate acoustic behavior with physics calculations."""
        request = PhysicsBehaviorRequest(
            element_id=element_id,
            behavior_type=PhysicsBehaviorType.ACOUSTIC,
            physics_type=PhysicsType.ACOUSTIC,
            element_data=element_data
        )
        return self.calculate_physics_behavior(request)
    
    def _validate_request(self, request: PhysicsBehaviorRequest) -> bool:
        """Validate physics behavior request."""
        if not request.element_id or not request.element_data:
            return False
        
        if not request.behavior_type or not request.physics_type:
            return False
        
        return True
    
    def _get_cached_result(self, request: PhysicsBehaviorRequest) -> Optional[PhysicsBehaviorResult]:
        """Get cached result if available and valid."""
        cache_key = f"{request.element_id}_{request.behavior_type.value}_{request.physics_type.value}"
        
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if (datetime.now() - cached_result.timestamp).seconds < self.config.cache_ttl:
                return cached_result
        
        return None
    
    def _cache_result(self, request: PhysicsBehaviorRequest, result: PhysicsBehaviorResult):
        """Cache physics behavior result."""
        cache_key = f"{request.element_id}_{request.behavior_type.value}_{request.physics_type.value}"
        self.cache[cache_key] = result
    
    def _determine_behavior_state(
        self, 
        behavior_type: PhysicsBehaviorType, 
        physics_result: PhysicsResult, 
        environmental_data: Optional[Dict[str, Any]]
    ) -> str:
        """Determine behavior state based on physics results."""
        # Analyze physics results to determine state
        if physics_result.state == "critical":
            return "critical"
        elif physics_result.state == "warning":
            return "warning"
        elif physics_result.state == "normal":
            return "normal"
        else:
            return "unknown"
    
    def _generate_recommendations(
        self, 
        behavior_type: PhysicsBehaviorType, 
        physics_result: PhysicsResult, 
        behavior_state: str
    ) -> List[str]:
        """Generate recommendations based on physics results."""
        recommendations = []
        
        if behavior_state == "critical":
            recommendations.append(f"Immediate attention required for {behavior_type.value} system")
        
        if behavior_state == "warning":
            recommendations.append(f"Monitor {behavior_type.value} system performance")
        
        # Add physics-specific recommendations
        if hasattr(physics_result, 'recommendations'):
            recommendations.extend(physics_result.recommendations)
        
        return recommendations
    
    def _generate_alerts(
        self, 
        behavior_type: PhysicsBehaviorType, 
        physics_result: PhysicsResult, 
        behavior_state: str
    ) -> List[str]:
        """Generate alerts based on physics results."""
        alerts = []
        
        if behavior_state == "critical":
            alerts.append(f"CRITICAL: {behavior_type.value} system failure detected")
        
        if behavior_state == "warning":
            alerts.append(f"WARNING: {behavior_type.value} system performance degraded")
        
        # Add physics-specific alerts
        if hasattr(physics_result, 'alerts'):
            alerts.extend(physics_result.alerts)
        
        return alerts
    
    def _get_performance_metrics(self, start_time: float) -> Dict[str, Any]:
        """Get performance metrics for the calculation."""
        calculation_time = time.time() - start_time
        
        return {
            "calculation_time": calculation_time,
            "cache_hit": False,  # Will be updated by caller
            "physics_engine_performance": self.physics_engine.performance_monitor.get_metrics()
        }
    
    def _store_in_history(self, result: PhysicsBehaviorResult):
        """Store result in integration history."""
        key = f"{result.behavior_type.value}_{result.physics_type.value}"
        
        if key not in self.integration_history:
            self.integration_history[key] = []
        
        self.integration_history[key].append(result)
        
        # Keep only last 100 results per type
        if len(self.integration_history[key]) > 100:
            self.integration_history[key] = self.integration_history[key][-100:]
    
    def _update_integration_metrics(
        self, 
        request: PhysicsBehaviorRequest, 
        result: PhysicsBehaviorResult, 
        calculation_time: float
    ):
        """Update integration performance metrics."""
        key = f"{request.behavior_type.value}_{request.physics_type.value}"
        
        if key not in self.calculation_times:
            self.calculation_times[key] = []
        
        self.calculation_times[key].append(calculation_time)
        
        # Keep only last 100 calculation times
        if len(self.calculation_times[key]) > 100:
            self.calculation_times[key] = self.calculation_times[key][-100:]
        
        # Update integration metrics
        self.integration_metrics[key] = {
            "total_calculations": len(self.calculation_times[key]),
            "average_calculation_time": np.mean(self.calculation_times[key]),
            "max_calculation_time": np.max(self.calculation_times[key]),
            "min_calculation_time": np.min(self.calculation_times[key]),
            "last_calculation": result.timestamp.isoformat()
        }
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get integration performance metrics."""
        return {
            "integration_metrics": self.integration_metrics,
            "cache_size": len(self.cache),
            "active_calculations": len(self.active_calculations),
            "total_history_entries": sum(len(history) for history in self.integration_history.values())
        }
    
    def clear_cache(self):
        """Clear the physics behavior cache."""
        self.cache.clear()
        logger.info("Physics behavior cache cleared")
    
    def get_integration_history(self, behavior_type: Optional[PhysicsBehaviorType] = None) -> Dict[str, List[PhysicsBehaviorResult]]:
        """Get integration history for specific behavior type or all types."""
        if behavior_type:
            key = f"{behavior_type.value}_*"
            return {k: v for k, v in self.integration_history.items() if k.startswith(behavior_type.value)}
        else:
            return self.integration_history.copy() 