"""
SVGX Engine - Physics-BIM Integration Service

This service integrates the enhanced physics engine with the BIM behavior engine
to provide realistic physics-based building system simulation with AI optimization.

🎯 **Integration Features:**
- Real-time physics calculations for BIM elements
- Physics-based behavior simulation with AI optimization
- Performance monitoring and optimization
- Comprehensive validation and error handling
- Enterprise-grade reliability and scalability
- Multi-physics integration for complex building systems

🏗️ **Integration Capabilities:**
- HVAC physics integration (fluid dynamics, thermal, acoustic)
- Electrical physics integration (circuit analysis, load balancing, harmonics)
- Structural physics integration (load analysis, stress, buckling)
- Plumbing physics integration (fluid dynamics, pressure, flow)
- Acoustic physics integration (sound propagation, room acoustics, noise)
- Combined physics analysis for multi-system interactions
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from svgx_engine.services.enhanced_physics_engine import (
    EnhancedPhysicsEngine, PhysicsConfig, PhysicsType, PhysicsResult
)
from svgx_engine.services.bim_behavior_engine import (
    BIMBehaviorEngine, BIMBehaviorConfig, BIMBehaviorType, BIMBehaviorResult
)
from svgx_engine.models.enhanced_bim import (
    EnhancedBIMModel, EnhancedBIMElement, BIMElementType, BIMSystemType
)
from svgx_engine.utils.performance import PerformanceMonitor
from svgx_engine.utils.errors import IntegrationError, PhysicsError, BIMError

logger = logging.getLogger(__name__)


@dataclass
class PhysicsBIMConfig:
    """Configuration for physics-BIM integration with AI optimization."""
    # Physics settings
    physics_enabled: bool = True
    physics_update_interval: float = 1.0  # seconds
    physics_accuracy_threshold: float = 0.95
    ai_optimization_enabled: bool = True
    
    # BIM behavior settings
    behavior_enabled: bool = True
    behavior_update_interval: float = 1.0  # seconds
    
    # Integration settings
    integration_enabled: bool = True
    real_time_simulation: bool = True
    performance_monitoring: bool = True
    multi_physics_enabled: bool = True
    
    # Validation settings
    validate_physics_data: bool = True
    validate_bim_data: bool = True
    error_threshold: float = 0.05
    
    # AI optimization settings
    optimization_threshold: float = 0.1
    learning_rate: float = 0.01
    confidence_threshold: float = 0.8


@dataclass
class PhysicsBIMResult:
    """Result of physics-BIM integration simulation with AI optimization."""
    element_id: str
    physics_result: Optional[PhysicsResult] = None
    behavior_result: Optional[BIMBehaviorResult] = None
    integration_metrics: Dict[str, Any] = field(default_factory=dict)
    ai_optimization: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence_score: float = 1.0


class PhysicsBIMIntegration:
    """
    Physics-BIM integration service that combines physics calculations
    with BIM behavior simulation for realistic building system analysis.
    """
    
    def __init__(self, config: Optional[PhysicsBIMConfig] = None):
        self.config = config or PhysicsBIMConfig()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize engines
        self.physics_engine = EnhancedPhysicsEngine() if self.config.physics_enabled else None
        self.bim_behavior_engine = BIMBehaviorEngine() if self.config.behavior_enabled else None
        
        # Integration state
        self.active_simulations: Dict[str, Dict[str, Any]] = {}
        self.integration_history: Dict[str, List[PhysicsBIMResult]] = {}
        
        # Performance tracking
        self.physics_calculation_times: List[float] = []
        self.behavior_calculation_times: List[float] = []
        self.integration_times: List[float] = []
        
        # AI optimization tracking
        self.optimization_history: Dict[str, List[Dict[str, Any]]] = {}
        self.learning_rates: Dict[str, float] = {}
        
        logger.info("Physics-BIM integration service initialized with AI optimization")
    
    def start_integrated_simulation(self, bim_model: EnhancedBIMModel) -> str:
        """
        Start integrated physics-BIM simulation with AI optimization.
        
        Args:
            bim_model: BIM model to simulate
            
        Returns:
            Simulation session ID
        """
        session_id = f"physics_bim_sim_{int(time.time())}"
        
        try:
            # Initialize simulation state
            self.active_simulations[session_id] = {
                'model': bim_model,
                'start_time': datetime.now(),
                'elements': {},
                'physics_results': {},
                'behavior_results': {},
                'integration_results': {},
                'optimization_history': {},
                'performance_metrics': {}
            }
            
            # Initialize physics and behavior for each element
            for element in bim_model.elements.values():
                self._initialize_element_simulation(session_id, element)
            
            logger.info(f"Started integrated physics-BIM simulation: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start integrated simulation: {e}")
            raise IntegrationError(f"Failed to start integrated simulation: {e}")
    
    def _initialize_element_simulation(self, session_id: str, element: EnhancedBIMElement):
        """Initialize physics and behavior simulation for an element with AI optimization."""
        element_id = element.id
        
        # Determine physics type based on element type
        physics_type = self._get_physics_type(element)
        behavior_type = self._get_behavior_type(element)
        
        # Initialize element state
        self.active_simulations[session_id]['elements'][element_id] = {
            'element': element,
            'physics_type': physics_type,
            'behavior_type': behavior_type,
            'last_physics_update': datetime.now(),
            'last_behavior_update': datetime.now(),
            'optimization_history': [],
            'performance_metrics': {
                'physics_calculation_count': 0,
                'behavior_calculation_count': 0,
                'optimization_count': 0,
                'avg_physics_time': 0.0,
                'avg_behavior_time': 0.0
            }
        }
        
        # Prepare initial physics data
        physics_data = self._prepare_physics_data(element, physics_type)
        behavior_data = self._prepare_behavior_data(element, behavior_type)
        
        # Store initial data
        self.active_simulations[session_id]['elements'][element_id].update({
            'physics_data': physics_data,
            'behavior_data': behavior_data
        })
        
        logger.debug(f"Initialized simulation for element {element_id}")
    
    def _get_physics_type(self, element: EnhancedBIMElement) -> PhysicsType:
        """Determine physics type based on element type with enhanced logic."""
        element_type = element.element_type
        system_type = element.system_type
        
        if system_type == BIMSystemType.HVAC:
            return PhysicsType.FLUID_DYNAMICS
        elif system_type == BIMSystemType.ELECTRICAL:
            return PhysicsType.ELECTRICAL
        elif system_type == BIMSystemType.STRUCTURAL:
            return PhysicsType.STRUCTURAL
        elif system_type == BIMSystemType.PLUMBING:
            return PhysicsType.FLUID_DYNAMICS
        elif system_type == BIMSystemType.ACOUSTIC:
            return PhysicsType.ACOUSTIC
        elif element_type in [BIMElementType.ROOM, BIMElementType.ZONE]:
            return PhysicsType.THERMAL
        elif element_type in [BIMElementType.WALL, BIMElementType.FLOOR_SLAB]:
            return PhysicsType.STRUCTURAL
        else:
            # Default to thermal for general building elements
            return PhysicsType.THERMAL
    
    def _get_behavior_type(self, element: EnhancedBIMElement) -> BIMBehaviorType:
        """Determine behavior type based on element type with enhanced logic."""
        element_type = element.element_type
        system_type = element.system_type
        
        if system_type == BIMSystemType.HVAC:
            return BIMBehaviorType.HVAC
        elif system_type == BIMSystemType.ELECTRICAL:
            return BIMBehaviorType.ELECTRICAL
        elif system_type == BIMSystemType.PLUMBING:
            return BIMBehaviorType.PLUMBING
        elif system_type == BIMSystemType.FIRE_PROTECTION:
            return BIMBehaviorType.FIRE_PROTECTION
        elif system_type == BIMSystemType.SECURITY:
            return BIMBehaviorType.SECURITY
        elif system_type == BIMSystemType.LIGHTING:
            return BIMBehaviorType.LIGHTING
        elif element_type in [BIMElementType.COLUMN, BIMElementType.BEAM]:
            return BIMBehaviorType.STRUCTURAL
        elif element_type in [BIMElementType.ROOM, BIMElementType.ZONE]:
            return BIMBehaviorType.ENVIRONMENTAL
        else:
            return BIMBehaviorType.ENVIRONMENTAL
    
    def _prepare_physics_data(self, element: EnhancedBIMElement, physics_type: PhysicsType) -> Dict[str, Any]:
        """Prepare physics data for element with enhanced parameters."""
        physics_data = {
            'element_id': element.id,
            'element_type': element.element_type.value,
            'system_type': element.system_type.value
        }
        
        # Extract properties for physics calculation
        properties = element.properties or {}
        
        if physics_type == PhysicsType.FLUID_DYNAMICS:
            physics_data.update({
                'diameter': properties.get('diameter', 0.3),
                'length': properties.get('length', 10.0),
                'flow_rate': properties.get('flow_rate', 0.5),
                'roughness': properties.get('roughness', 0.0001),
                'fluid_type': properties.get('fluid_type', 'air')
            })
        
        elif physics_type == PhysicsType.ELECTRICAL:
            physics_data.update({
                'voltage': properties.get('voltage', 120.0),
                'resistance': properties.get('resistance', 10.0),
                'inductance': properties.get('inductance', 0.1),
                'capacitance': properties.get('capacitance', 0.001),
                'frequency': properties.get('frequency', 60.0),
                'load_type': properties.get('load_type', 'resistive')
            })
        
        elif physics_type == PhysicsType.STRUCTURAL:
            physics_data.update({
                'length': properties.get('length', 5.0),
                'width': properties.get('width', 0.2),
                'height': properties.get('height', 0.3),
                'load': properties.get('load', 1000.0),
                'material': properties.get('material', 'steel'),
                'load_type': properties.get('load_type', 'uniform'),
                'support_type': properties.get('support_type', 'simply_supported')
            })
        
        elif physics_type == PhysicsType.THERMAL:
            physics_data.update({
                'area': properties.get('area', 10.0),
                'thickness': properties.get('thickness', 0.2),
                'temp_difference': properties.get('temp_difference', 20.0),
                'material': properties.get('material', 'concrete'),
                'convection_coefficient': properties.get('convection_coefficient', 10.0)
            })
        
        elif physics_type == PhysicsType.ACOUSTIC:
            physics_data.update({
                'sound_power': properties.get('sound_power', 0.001),
                'distance': properties.get('distance', 5.0),
                'absorption_coefficient': properties.get('absorption_coefficient', 0.1),
                'room_volume': properties.get('room_volume', 100.0),
                'room_surface_area': properties.get('room_surface_area', 150.0),
                'frequency': properties.get('frequency', 1000.0)
            })
        
        return physics_data
    
    def _prepare_behavior_data(self, element: EnhancedBIMElement, behavior_type: BIMBehaviorType) -> Dict[str, Any]:
        """Prepare behavior data for element with enhanced parameters."""
        behavior_data = {
            'element_id': element.id,
            'element_type': element.element_type.value,
            'system_type': element.system_type.value
        }
        
        # Extract properties for behavior simulation
        properties = element.properties or {}
        
        if behavior_type == BIMBehaviorType.HVAC:
            behavior_data.update({
                'setpoint_temperature': properties.get('setpoint_temperature', 22.0),
                'air_flow_rate': properties.get('air_flow_rate', 0.5),
                'cooling_capacity': properties.get('cooling_capacity', 5000.0),
                'heating_capacity': properties.get('heating_capacity', 6000.0),
                'efficiency': properties.get('efficiency', 0.8)
            })
        
        elif behavior_type == BIMBehaviorType.ELECTRICAL:
            behavior_data.update({
                'voltage': properties.get('voltage', 120.0),
                'current': properties.get('current', 10.0),
                'power_factor': properties.get('power_factor', 0.9),
                'load_percentage': properties.get('load_percentage', 70.0)
            })
        
        elif behavior_type == BIMBehaviorType.PLUMBING:
            behavior_data.update({
                'water_flow_rate': properties.get('water_flow_rate', 0.01),
                'pressure': properties.get('pressure', 100.0),
                'temperature': properties.get('temperature', 20.0)
            })
        
        else:
            # Default behavior parameters
            behavior_data.update({
                'temperature': properties.get('temperature', 22.0),
                'humidity': properties.get('humidity', 50.0),
                'energy_consumption': properties.get('energy_consumption', 0.0),
                'status': properties.get('status', 'normal')
            })
        
        return behavior_data
    
    def run_integrated_simulation_step(self, session_id: str) -> Dict[str, PhysicsBIMResult]:
        """
        Run one step of integrated physics-BIM simulation with AI optimization.
        
        Args:
            session_id: Simulation session ID
            
        Returns:
            Dictionary of element results with AI optimization
        """
        if session_id not in self.active_simulations:
            raise IntegrationError(f"Session {session_id} not found")
        
        session_data = self.active_simulations[session_id]
        results = {}
        
        try:
            for element_id, element_data in session_data['elements'].items():
                start_time = time.time()
                
                # Run physics calculation with AI optimization
                physics_result = None
                if self.physics_engine and self.config.physics_enabled:
                    physics_start = time.time()
                    physics_result = self.physics_engine.calculate_physics(
                        element_data['physics_type'], 
                        element_data['physics_data']
                    )
                    physics_time = time.time() - physics_start
                    self.physics_calculation_times.append(physics_time)
                    
                    # Update performance metrics
                    element_data['performance_metrics']['physics_calculation_count'] += 1
                    element_data['performance_metrics']['avg_physics_time'] = (
                        (element_data['performance_metrics']['avg_physics_time'] * 
                         (element_data['performance_metrics']['physics_calculation_count'] - 1) + physics_time) /
                        element_data['performance_metrics']['physics_calculation_count']
                    )
                
                # Run behavior simulation
                behavior_result = None
                if self.bim_behavior_engine and self.config.behavior_enabled:
                    behavior_start = time.time()
                    behavior_result = self._simulate_behavior(
                        element_data['behavior_type'], 
                        element_data['behavior_data']
                    )
                    behavior_time = time.time() - behavior_start
                    self.behavior_calculation_times.append(behavior_time)
                    
                    # Update performance metrics
                    element_data['performance_metrics']['behavior_calculation_count'] += 1
                    element_data['performance_metrics']['avg_behavior_time'] = (
                        (element_data['performance_metrics']['avg_behavior_time'] * 
                         (element_data['performance_metrics']['behavior_calculation_count'] - 1) + behavior_time) /
                        element_data['performance_metrics']['behavior_calculation_count']
                    )
                
                # Integrate results with AI optimization
                integration_start = time.time()
                integration_result = self._integrate_results_with_ai(
                    element_id, physics_result, behavior_result, element_data
                )
                integration_time = time.time() - integration_start
                self.integration_times.append(integration_time)
                
                # Store results
                results[element_id] = integration_result
                session_data['integration_results'][element_id] = integration_result
                
                # Update optimization history
                if integration_result.ai_optimization:
                    element_data['optimization_history'].append(integration_result.ai_optimization)
                    element_data['performance_metrics']['optimization_count'] += 1
            
            # Update session performance metrics
            session_data['performance_metrics'] = self._calculate_session_performance(session_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Integrated simulation step failed: {e}")
            raise IntegrationError(f"Integrated simulation step failed: {e}")
    
    def _simulate_behavior(self, behavior_type: BIMBehaviorType, behavior_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate behavior for an element with enhanced parameters."""
        try:
            # Create a mock behavior result for demonstration
            # In a real implementation, this would call the BIM behavior engine
            timestamp = datetime.now()
            
            # Generate behavior metrics based on behavior type
            metrics = {}
            if behavior_type == BIMBehaviorType.HVAC:
                metrics = {
                    'temperature': behavior_data.get('setpoint_temperature', 22.0),
                    'air_flow_rate': behavior_data.get('air_flow_rate', 0.5),
                    'efficiency': behavior_data.get('efficiency', 0.8),
                    'energy_consumption': behavior_data.get('air_flow_rate', 0.5) * 1000,
                    'status': 'normal'
                }
            elif behavior_type == BIMBehaviorType.ELECTRICAL:
                metrics = {
                    'voltage': behavior_data.get('voltage', 120.0),
                    'current': behavior_data.get('current', 10.0),
                    'power_factor': behavior_data.get('power_factor', 0.9),
                    'load_percentage': behavior_data.get('load_percentage', 70.0),
                    'energy_consumption': behavior_data.get('current', 10.0) * behavior_data.get('voltage', 120.0),
                    'status': 'normal'
                }
            else:
                metrics = {
                    'temperature': behavior_data.get('temperature', 22.0),
                    'humidity': behavior_data.get('humidity', 50.0),
                    'energy_consumption': behavior_data.get('energy_consumption', 0.0),
                    'status': behavior_data.get('status', 'normal')
                }
            
            return BIMBehaviorResult(
                element_id=behavior_data.get('element_id', 'unknown'),
                behavior_type=behavior_type,
                state=BIMBehaviorState.NORMAL,
                timestamp=timestamp,
                metrics=metrics,
                alerts=[],
                recommendations=[]
            )
            
        except Exception as e:
            logger.error(f"Behavior simulation failed: {e}")
            raise IntegrationError(f"Behavior simulation failed: {e}")
    
    def _integrate_results_with_ai(self, element_id: str, physics_result: Optional[PhysicsResult], 
                                  behavior_result: Optional[BIMBehaviorResult], 
                                  element_data: Dict[str, Any]) -> PhysicsBIMResult:
        """Integrate physics and behavior results with AI optimization."""
        try:
            integration_metrics = {}
            ai_optimization = {}
            alerts = []
            recommendations = []
            confidence_score = 1.0
            
            # Integrate physics results
            if physics_result:
                integration_metrics.update({
                    'physics_state': physics_result.state.value,
                    'physics_confidence': physics_result.confidence_score,
                    'physics_metrics_count': len(physics_result.metrics)
                })
                alerts.extend(physics_result.alerts)
                recommendations.extend(physics_result.recommendations)
                confidence_score *= physics_result.confidence_score
            
            # Integrate behavior results
            if behavior_result:
                integration_metrics.update({
                    'behavior_state': behavior_result.state.value,
                    'behavior_metrics_count': len(behavior_result.metrics)
                })
                alerts.extend(behavior_result.alerts)
                recommendations.extend(behavior_result.recommendations)
            
            # Apply AI optimization if enabled
            if self.config.ai_optimization_enabled:
                ai_optimization = self._apply_ai_optimization_to_integration(
                    element_id, physics_result, behavior_result, element_data
                )
                
                if ai_optimization.get('improvement', 0) > self.config.optimization_threshold:
                    recommendations.extend(ai_optimization.get('recommendations', []))
                    confidence_score *= ai_optimization.get('confidence_multiplier', 1.0)
            
            # Calculate overall state
            overall_state = self._determine_overall_state(physics_result, behavior_result, ai_optimization)
            
            return PhysicsBIMResult(
                element_id=element_id,
                physics_result=physics_result,
                behavior_result=behavior_result,
                integration_metrics=integration_metrics,
                ai_optimization=ai_optimization,
                timestamp=datetime.now(),
                alerts=alerts,
                recommendations=recommendations,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Integration with AI failed: {e}")
            raise IntegrationError(f"Integration with AI failed: {e}")
    
    def _apply_ai_optimization_to_integration(self, element_id: str, physics_result: Optional[PhysicsResult],
                                             behavior_result: Optional[BIMBehaviorResult],
                                             element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply AI optimization to integrated results."""
        optimization = {
            'improvement': 0.0,
            'recommendations': [],
            'confidence_multiplier': 1.0,
            'optimization_type': 'integration'
        }
        
        # Analyze physics-behavior consistency
        if physics_result and behavior_result:
            # Check for inconsistencies between physics and behavior
            physics_metrics = physics_result.metrics
            behavior_metrics = behavior_result.metrics
            
            # Example: Check if HVAC physics and behavior are consistent
            if (physics_result.physics_type == PhysicsType.FLUID_DYNAMICS and 
                behavior_result.behavior_type == BIMBehaviorType.HVAC):
                
                physics_flow = physics_metrics.get('flow_rate', 0)
                behavior_flow = behavior_metrics.get('air_flow_rate', 0)
                
                if abs(physics_flow - behavior_flow) > 0.1:
                    optimization['improvement'] = 0.15
                    optimization['recommendations'].append(
                        "Inconsistency detected between physics and behavior flow rates"
                    )
                    optimization['recommendations'].append(
                        "Consider calibrating behavior model with physics results"
                    )
            
            # Check energy efficiency
            if 'energy_consumption' in behavior_metrics:
                energy_consumption = behavior_metrics['energy_consumption']
                if energy_consumption > 1000:  # High energy consumption
                    optimization['improvement'] = 0.12
                    optimization['recommendations'].append(
                        "High energy consumption detected - consider optimization"
                    )
                    optimization['recommendations'].append(
                        "Implement energy-efficient control strategies"
                    )
        
        # Update confidence multiplier
        optimization['confidence_multiplier'] = 1.0 + (optimization['improvement'] * 0.1)
        
        return optimization
    
    def _determine_overall_state(self, physics_result: Optional[PhysicsResult],
                                behavior_result: Optional[BIMBehaviorResult],
                                ai_optimization: Dict[str, Any]) -> str:
        """Determine overall state based on physics, behavior, and AI optimization."""
        states = []
        
        if physics_result:
            states.append(physics_result.state.value)
        if behavior_result:
            states.append(behavior_result.state.value)
        
        if not states:
            return 'normal'
        
        # Determine overall state
        if 'critical' in states:
            return 'critical'
        elif 'warning' in states:
            return 'warning'
        elif 'optimized' in states and len(states) == 1:
            return 'optimized'
        else:
            return 'normal'
    
    def _calculate_session_performance(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive session performance metrics."""
        performance = {
            'total_elements': len(session_data['elements']),
            'physics_calculations': 0,
            'behavior_calculations': 0,
            'optimizations': 0,
            'avg_physics_time': 0.0,
            'avg_behavior_time': 0.0,
            'avg_integration_time': 0.0
        }
        
        # Aggregate performance metrics from all elements
        for element_data in session_data['elements'].values():
            element_metrics = element_data['performance_metrics']
            performance['physics_calculations'] += element_metrics['physics_calculation_count']
            performance['behavior_calculations'] += element_metrics['behavior_calculation_count']
            performance['optimizations'] += element_metrics['optimization_count']
        
        # Calculate averages
        if performance['physics_calculations'] > 0:
            performance['avg_physics_time'] = sum(self.physics_calculation_times[-performance['physics_calculations']:]) / performance['physics_calculations']
        
        if performance['behavior_calculations'] > 0:
            performance['avg_behavior_time'] = sum(self.behavior_calculation_times[-performance['behavior_calculations']:]) / performance['behavior_calculations']
        
        if self.integration_times:
            performance['avg_integration_time'] = sum(self.integration_times[-len(session_data['elements']):]) / len(session_data['elements'])
        
        return performance
    
    def get_simulation_status(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive simulation status with AI optimization metrics."""
        if session_id not in self.active_simulations:
            raise IntegrationError(f"Session {session_id} not found")
        
        session_data = self.active_simulations[session_id]
        
        status = {
            'session_id': session_id,
            'start_time': session_data['start_time'].isoformat(),
            'duration': (datetime.now() - session_data['start_time']).total_seconds(),
            'total_elements': len(session_data['elements']),
            'performance_metrics': session_data.get('performance_metrics', {}),
            'element_status': {},
            'ai_optimization_summary': self._get_ai_optimization_summary(session_data),
            'overall_state': 'normal'
        }
        
        # Calculate element status
        critical_count = 0
        warning_count = 0
        optimized_count = 0
        normal_count = 0
        
        for element_id, element_data in session_data['elements'].items():
            if element_id in session_data['integration_results']:
                result = session_data['integration_results'][element_id]
                element_status = {
                    'physics_state': result.physics_result.state.value if result.physics_result else 'unknown',
                    'behavior_state': result.behavior_result.state.value if result.behavior_result else 'unknown',
                    'overall_state': result.integration_metrics.get('overall_state', 'normal'),
                    'confidence_score': result.confidence_score,
                    'alerts_count': len(result.alerts),
                    'recommendations_count': len(result.recommendations),
                    'optimization_applied': bool(result.ai_optimization)
                }
                
                status['element_status'][element_id] = element_status
                
                # Count states
                overall_state = element_status['overall_state']
                if overall_state == 'critical':
                    critical_count += 1
                elif overall_state == 'warning':
                    warning_count += 1
                elif overall_state == 'optimized':
                    optimized_count += 1
                else:
                    normal_count += 1
        
        # Determine overall state
        if critical_count > 0:
            status['overall_state'] = 'critical'
        elif warning_count > 0:
            status['overall_state'] = 'warning'
        elif optimized_count == len(session_data['elements']):
            status['overall_state'] = 'optimized'
        
        status['state_counts'] = {
            'critical': critical_count,
            'warning': warning_count,
            'optimized': optimized_count,
            'normal': normal_count
        }
        
        return status
    
    def _get_ai_optimization_summary(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI optimization summary for the session."""
        summary = {
            'total_optimizations': 0,
            'optimization_types': {},
            'avg_improvement': 0.0,
            'optimization_recommendations': []
        }
        
        total_improvement = 0.0
        optimization_count = 0
        
        for element_data in session_data['elements'].values():
            for optimization in element_data.get('optimization_history', []):
                summary['total_optimizations'] += 1
                improvement = optimization.get('improvement', 0.0)
                total_improvement += improvement
                optimization_count += 1
                
                # Track optimization types
                opt_type = optimization.get('optimization_type', 'unknown')
                if opt_type not in summary['optimization_types']:
                    summary['optimization_types'][opt_type] = 0
                summary['optimization_types'][opt_type] += 1
                
                # Collect recommendations
                recommendations = optimization.get('recommendations', [])
                summary['optimization_recommendations'].extend(recommendations)
        
        if optimization_count > 0:
            summary['avg_improvement'] = total_improvement / optimization_count
        
        return summary
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get comprehensive integration summary with AI optimization metrics."""
        summary = {
            'total_sessions': len(self.active_simulations),
            'total_calculations': {
                'physics': len(self.physics_calculation_times),
                'behavior': len(self.behavior_calculation_times),
                'integration': len(self.integration_times)
            },
            'performance_metrics': {
                'avg_physics_time': sum(self.physics_calculation_times) / len(self.physics_calculation_times) if self.physics_calculation_times else 0,
                'avg_behavior_time': sum(self.behavior_calculation_times) / len(self.behavior_calculation_times) if self.behavior_calculation_times else 0,
                'avg_integration_time': sum(self.integration_times) / len(self.integration_times) if self.integration_times else 0
            },
            'ai_optimization_stats': {
                'total_optimizations': sum(len(history) for history in self.optimization_history.values()),
                'optimization_hit_rate': len(self.optimization_history) / max(1, len(self.active_simulations)),
                'avg_learning_rate': sum(self.learning_rates.values()) / len(self.learning_rates) if self.learning_rates else 0
            }
        }
        
        return summary
    
    def stop_simulation(self, session_id: str) -> bool:
        """Stop integrated simulation and save results."""
        if session_id not in self.active_simulations:
            return False
        
        try:
            # Save final results to history
            session_data = self.active_simulations[session_id]
            if session_id not in self.integration_history:
                self.integration_history[session_id] = []
            
            # Add final results
            for element_id, result in session_data['integration_results'].items():
                self.integration_history[session_id].append(result)
            
            # Remove from active simulations
            del self.active_simulations[session_id]
            
            logger.info(f"Stopped integrated simulation: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop simulation: {e}")
            return False
    
    def validate_integration_data(self, bim_model: EnhancedBIMModel) -> bool:
        """Validate integration data for accuracy and completeness."""
        try:
            for element in bim_model.elements.values():
                # Validate element has required properties
                if not element.id or not element.element_type:
                    logger.warning(f"Element missing required properties: {element.id}")
                    return False
                
                # Validate physics data preparation
                physics_type = self._get_physics_type(element)
                physics_data = self._prepare_physics_data(element, physics_type)
                
                if not physics_data:
                    logger.warning(f"Failed to prepare physics data for element: {element.id}")
                    return False
                
                # Validate behavior data preparation
                behavior_type = self._get_behavior_type(element)
                behavior_data = self._prepare_behavior_data(element, behavior_type)
                
                if not behavior_data:
                    logger.warning(f"Failed to prepare behavior data for element: {element.id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Integration data validation failed: {e}")
            return False
    
    def get_ai_optimization_recommendations(self) -> Dict[str, List[str]]:
        """Get AI-based optimization recommendations for different physics types."""
        recommendations = {}
        
        for physics_type in PhysicsType:
            recommendations[physics_type.value] = self.physics_engine.get_optimization_recommendations(physics_type)
        
        return recommendations 