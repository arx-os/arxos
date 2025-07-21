"""
SVGX Engine - BIM Behavior Engine

This service provides comprehensive building system behavior simulation
for Building Information Models (BIM) including:

🎯 **Core BIM Behaviors:**
- HVAC system behavior (temperature, humidity, air flow)
- Electrical system behavior (power flow, load balancing)
- Plumbing system behavior (water flow, pressure, temperature)
- Fire protection system behavior (detection, suppression)
- Security system behavior (access control, surveillance)
- Lighting system behavior (occupancy, daylight, energy)

🏗️ **Behavior Types:**
- Real-time simulation with physics-based calculations
- Rule-based behavior with conditional logic
- State machine behaviors for equipment operation
- Time-based behaviors for scheduling and maintenance
- Environmental response behaviors
- Occupancy-based adaptive behaviors

📊 **Integration:**
- SVGX Engine behavior engine integration
- Physics engine for realistic calculations
- Logic engine for rule-based behaviors
- Real-time collaboration for multi-user simulation
"""

import asyncio
import logging
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from svgx_engine.models.enhanced_bim import (
    EnhancedBIMModel, EnhancedBIMElement, BIMElementType, BIMSystemType
)
from svgx_engine.services.behavior_engine import BehaviorEngine
from svgx_engine.services.physics_engine import PhysicsEngine
from svgx_engine.services.logic_engine import LogicEngine
from svgx_engine.utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


class BIMBehaviorType(Enum):
    """Types of BIM behaviors supported."""
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FIRE_PROTECTION = "fire_protection"
    SECURITY = "security"
    LIGHTING = "lighting"
    STRUCTURAL = "structural"
    ENVIRONMENTAL = "environmental"
    OCCUPANCY = "occupancy"
    MAINTENANCE = "maintenance"


class BIMBehaviorState(Enum):
    """States for BIM behavior simulation."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


@dataclass
class BIMBehaviorConfig:
    """Configuration for BIM behavior simulation."""
    simulation_interval: float = 1.0  # seconds
    physics_enabled: bool = True
    environmental_factors: bool = True
    occupancy_modeling: bool = True
    maintenance_scheduling: bool = True
    energy_optimization: bool = True
    real_time_simulation: bool = True


@dataclass
class BIMBehaviorResult:
    """Result of BIM behavior simulation."""
    element_id: str
    behavior_type: BIMBehaviorType
    state: BIMBehaviorState
    timestamp: datetime
    metrics: Dict[str, Any]
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class BIMBehaviorEngine:
    """
    Comprehensive BIM behavior engine that simulates realistic
    building system behaviors with physics-based calculations.
    """
    
    def __init__(self, config: Optional[BIMBehaviorConfig] = None):
        self.config = config or BIMBehaviorConfig()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize SVGX Engine components
        self.behavior_engine = BehaviorEngine()
        self.physics_engine = PhysicsEngine()
        self.logic_engine = LogicEngine()
        
        # BIM behavior state
        self.active_behaviors: Dict[str, Dict[str, Any]] = {}
        self.behavior_history: Dict[str, List[BIMBehaviorResult]] = {}
        self.simulation_running = False
        
        # Initialize behavior handlers
        self._initialize_behavior_handlers()
        
        logger.info("BIM behavior engine initialized")
    
    def _initialize_behavior_handlers(self):
        """Initialize behavior handlers for different system types."""
        self.behavior_handlers = {
            BIMBehaviorType.HVAC: self._simulate_hvac_behavior,
            BIMBehaviorType.ELECTRICAL: self._simulate_electrical_behavior,
            BIMBehaviorType.PLUMBING: self._simulate_plumbing_behavior,
            BIMBehaviorType.FIRE_PROTECTION: self._simulate_fire_protection_behavior,
            BIMBehaviorType.SECURITY: self._simulate_security_behavior,
            BIMBehaviorType.LIGHTING: self._simulate_lighting_behavior,
            BIMBehaviorType.STRUCTURAL: self._simulate_structural_behavior,
            BIMBehaviorType.ENVIRONMENTAL: self._simulate_environmental_behavior,
            BIMBehaviorType.OCCUPANCY: self._simulate_occupancy_behavior,
            BIMBehaviorType.MAINTENANCE: self._simulate_maintenance_behavior
        }
    
    def start_bim_simulation(self, bim_model: EnhancedBIMModel) -> str:
        """
        Start BIM behavior simulation for a model.
        
        Args:
            bim_model: BIM model to simulate
            
        Returns:
            Simulation session ID
        """
        session_id = f"bim_sim_{uuid.uuid4().hex[:8]}"
        
        try:
            # Initialize simulation state
            self.active_behaviors[session_id] = {
                'model': bim_model,
                'start_time': datetime.now(),
                'elements': {},
                'environment': self._initialize_environment()
            }
            
            # Initialize behavior for each element
            for element in bim_model.elements.values():
                self._initialize_element_behavior(session_id, element)
            
            # Start simulation loop
            if self.config.real_time_simulation:
                asyncio.create_task(self._run_simulation_loop(session_id))
            
            logger.info(f"Started BIM simulation session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start BIM simulation: {e}")
            raise
    
    def _initialize_environment(self) -> Dict[str, Any]:
        """Initialize environmental conditions for simulation."""
        return {
            'ambient_temperature': 22.0,  # Celsius
            'ambient_humidity': 50.0,     # Percentage
            'ambient_pressure': 101.325,  # kPa
            'outdoor_temperature': 15.0,  # Celsius
            'solar_radiation': 500.0,     # W/m²
            'wind_speed': 5.0,           # m/s
            'occupancy_level': 0.7,      # 0-1 scale
            'time_of_day': datetime.now().hour,
            'day_of_week': datetime.now().weekday()
        }
    
    def _initialize_element_behavior(self, session_id: str, element: EnhancedBIMElement):
        """Initialize behavior for a BIM element."""
        element_id = element.id
        
        # Determine behavior type based on element type
        behavior_type = self._get_behavior_type(element)
        
        # Initialize element state
        self.active_behaviors[session_id]['elements'][element_id] = {
            'element': element,
            'behavior_type': behavior_type,
            'state': BIMBehaviorState.NORMAL,
            'metrics': self._initialize_element_metrics(element, behavior_type),
            'last_update': datetime.now(),
            'alerts': [],
            'recommendations': []
        }
    
    def _get_behavior_type(self, element: EnhancedBIMElement) -> BIMBehaviorType:
        """Determine behavior type based on element type."""
        element_type = element.element_type
        
        if element_type in [BIMElementType.HVAC_ZONE, BIMElementType.AIR_HANDLER, 
                           BIMElementType.VAV_BOX, BIMElementType.DUCT, 
                           BIMElementType.DIFFUSER, BIMElementType.THERMOSTAT]:
            return BIMBehaviorType.HVAC
        
        elif element_type in [BIMElementType.ELECTRICAL_PANEL, BIMElementType.ELECTRICAL_CIRCUIT,
                             BIMElementType.ELECTRICAL_OUTLET, BIMElementType.SWITCH]:
            return BIMBehaviorType.ELECTRICAL
        
        elif element_type in [BIMElementType.PLUMBING_PIPE, BIMElementType.PLUMBING_FIXTURE,
                             BIMElementType.VALVE, BIMElementType.PUMP, BIMElementType.WATER_HEATER]:
            return BIMBehaviorType.PLUMBING
        
        elif element_type in [BIMElementType.FIRE_ALARM_PANEL, BIMElementType.SMOKE_DETECTOR,
                             BIMElementType.FIRE_SPRINKLER, BIMElementType.PULL_STATION]:
            return BIMBehaviorType.FIRE_PROTECTION
        
        elif element_type in [BIMElementType.SECURITY_CAMERA, BIMElementType.ACCESS_CONTROL,
                             BIMElementType.CARD_READER]:
            return BIMBehaviorType.SECURITY
        
        elif element_type == BIMElementType.LIGHTING_FIXTURE:
            return BIMBehaviorType.LIGHTING
        
        elif element_type in [BIMElementType.COLUMN, BIMElementType.BEAM, 
                             BIMElementType.TRUSS, BIMElementType.FOUNDATION]:
            return BIMBehaviorType.STRUCTURAL
        
        else:
            return BIMBehaviorType.ENVIRONMENTAL
    
    def _initialize_element_metrics(self, element: EnhancedBIMElement, 
                                  behavior_type: BIMBehaviorType) -> Dict[str, Any]:
        """Initialize metrics for an element based on its behavior type."""
        base_metrics = {
            'temperature': 22.0,
            'humidity': 50.0,
            'pressure': 101.325,
            'energy_consumption': 0.0,
            'operational_hours': 0,
            'maintenance_hours': 0,
            'efficiency': 1.0,
            'status': 'operational'
        }
        
        if behavior_type == BIMBehaviorType.HVAC:
            base_metrics.update({
                'air_flow_rate': 0.0,
                'setpoint_temperature': 22.0,
                'cooling_capacity': 0.0,
                'heating_capacity': 0.0,
                'filter_pressure_drop': 0.0
            })
        
        elif behavior_type == BIMBehaviorType.ELECTRICAL:
            base_metrics.update({
                'voltage': 120.0,
                'current': 0.0,
                'power_factor': 0.95,
                'load_percentage': 0.0,
                'circuit_breaker_status': 'closed'
            })
        
        elif behavior_type == BIMBehaviorType.PLUMBING:
            base_metrics.update({
                'water_flow_rate': 0.0,
                'water_pressure': 200.0,  # kPa
                'water_temperature': 20.0,
                'valve_position': 0.0,  # 0-1 scale
                'pump_speed': 0.0
            })
        
        return base_metrics
    
    async def _run_simulation_loop(self, session_id: str):
        """Run continuous simulation loop for a session."""
        while session_id in self.active_behaviors:
            try:
                start_time = time.time()
                
                # Update environmental conditions
                self._update_environment(session_id)
                
                # Simulate all elements
                for element_id, element_data in self.active_behaviors[session_id]['elements'].items():
                    behavior_type = element_data['behavior_type']
                    handler = self.behavior_handlers.get(behavior_type)
                    
                    if handler:
                        result = await handler(session_id, element_id, element_data)
                        self._update_element_state(session_id, element_id, result)
                
                # Store simulation results
                self._store_simulation_results(session_id)
                
                # Performance monitoring
                elapsed = time.time() - start_time
                self.performance_monitor.record_operation('bim_simulation_step', elapsed)
                
                # Wait for next simulation step
                await asyncio.sleep(self.config.simulation_interval)
                
            except Exception as e:
                logger.error(f"Simulation loop error: {e}")
                await asyncio.sleep(1.0)
    
    def _update_environment(self, session_id: str):
        """Update environmental conditions for simulation."""
        env = self.active_behaviors[session_id]['environment']
        now = datetime.now()
        
        # Simulate daily temperature cycle
        hour = now.hour
        base_temp = 15.0
        temp_variation = 10.0 * math.sin((hour - 6) * math.pi / 12)
        env['outdoor_temperature'] = base_temp + temp_variation
        
        # Update indoor conditions based on outdoor
        env['ambient_temperature'] = env['outdoor_temperature'] + 7.0  # Building heating
        env['ambient_humidity'] = max(30.0, min(70.0, 50.0 + (env['ambient_temperature'] - 22.0) * 2))
        
        # Update time-based factors
        env['time_of_day'] = hour
        env['day_of_week'] = now.weekday()
        
        # Simulate occupancy patterns
        if 8 <= hour <= 18:  # Work hours
            env['occupancy_level'] = 0.8
        elif 18 <= hour <= 22:  # Evening
            env['occupancy_level'] = 0.4
        else:  # Night
            env['occupancy_level'] = 0.1
    
    async def _simulate_hvac_behavior(self, session_id: str, element_id: str, 
                                     element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate HVAC system behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        env = self.active_behaviors[session_id]['environment']
        
        # Calculate heat transfer
        temp_diff = env['ambient_temperature'] - metrics['setpoint_temperature']
        heat_load = abs(temp_diff) * 1000  # Simplified heat load calculation
        
        # Update system response
        if temp_diff > 1.0:  # Too hot
            metrics['cooling_capacity'] = min(heat_load, 5000)  # W
            metrics['temperature'] -= 0.5
        elif temp_diff < -1.0:  # Too cold
            metrics['heating_capacity'] = min(heat_load, 5000)  # W
            metrics['temperature'] += 0.5
        else:
            metrics['cooling_capacity'] = 0
            metrics['heating_capacity'] = 0
        
        # Calculate energy consumption
        total_capacity = metrics['cooling_capacity'] + metrics['heating_capacity']
        metrics['energy_consumption'] = total_capacity * 0.3  # Simplified efficiency
        
        # Update air flow
        if total_capacity > 0:
            metrics['air_flow_rate'] = total_capacity / 1000  # m³/s
        else:
            metrics['air_flow_rate'] = 0.1  # Minimum ventilation
        
        # Determine state
        state = self._determine_hvac_state(metrics)
        
        # Generate alerts and recommendations
        alerts, recommendations = self._generate_hvac_alerts(metrics, env)
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.HVAC,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=alerts,
            recommendations=recommendations
        )
    
    async def _simulate_electrical_behavior(self, session_id: str, element_id: str,
                                          element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate electrical system behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        env = self.active_behaviors[session_id]['environment']
        
        # Calculate load based on occupancy and time
        base_load = 1000  # W
        occupancy_factor = env['occupancy_level']
        time_factor = 1.0 if 8 <= env['time_of_day'] <= 18 else 0.3
        
        # Update electrical metrics
        metrics['current'] = (base_load * occupancy_factor * time_factor) / metrics['voltage']
        metrics['load_percentage'] = (metrics['current'] / 20.0) * 100  # Assume 20A max
        
        # Calculate power consumption
        metrics['energy_consumption'] = base_load * occupancy_factor * time_factor
        
        # Check for overload conditions
        if metrics['load_percentage'] > 90:
            metrics['circuit_breaker_status'] = 'tripped'
            state = BIMBehaviorState.CRITICAL
        elif metrics['load_percentage'] > 80:
            state = BIMBehaviorState.WARNING
        else:
            state = BIMBehaviorState.NORMAL
        
        # Generate alerts
        alerts, recommendations = self._generate_electrical_alerts(metrics)
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.ELECTRICAL,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=alerts,
            recommendations=recommendations
        )
    
    async def _simulate_plumbing_behavior(self, session_id: str, element_id: str,
                                         element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate plumbing system behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        env = self.active_behaviors[session_id]['environment']
        
        # Calculate water demand based on occupancy
        base_flow = 0.1  # L/s per person
        occupancy_factor = env['occupancy_level']
        metrics['water_flow_rate'] = base_flow * occupancy_factor * 100  # Assume 100 people
        
        # Update pressure based on flow
        if metrics['water_flow_rate'] > 0:
            pressure_drop = metrics['water_flow_rate'] * 0.5  # kPa per L/s
            metrics['water_pressure'] = max(50, 200 - pressure_drop)
        else:
            metrics['water_pressure'] = 200
        
        # Update temperature (heating system)
        if env['ambient_temperature'] < 20:
            metrics['water_temperature'] = 60  # Hot water
        else:
            metrics['water_temperature'] = 20  # Cold water
        
        # Determine state
        state = self._determine_plumbing_state(metrics)
        
        # Generate alerts
        alerts, recommendations = self._generate_plumbing_alerts(metrics)
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.PLUMBING,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=alerts,
            recommendations=recommendations
        )
    
    async def _simulate_fire_protection_behavior(self, session_id: str, element_id: str,
                                                element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate fire protection system behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        
        # Simulate smoke detection (simplified)
        smoke_level = 0.0  # Normal conditions
        if element.element_type == BIMElementType.SMOKE_DETECTOR:
            # Simulate potential smoke detection
            if smoke_level > 0.5:
                metrics['status'] = 'alarm'
                state = BIMBehaviorState.CRITICAL
            else:
                metrics['status'] = 'normal'
                state = BIMBehaviorState.NORMAL
        
        # Simulate sprinkler system
        elif element.element_type == BIMElementType.FIRE_SPRINKLER:
            if metrics['status'] == 'activated':
                metrics['water_flow_rate'] = 100  # L/min
                state = BIMBehaviorState.EMERGENCY
            else:
                metrics['water_flow_rate'] = 0
                state = BIMBehaviorState.NORMAL
        
        else:
            state = BIMBehaviorState.NORMAL
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.FIRE_PROTECTION,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=[],
            recommendations=[]
        )
    
    async def _simulate_security_behavior(self, session_id: str, element_id: str,
                                         element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate security system behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        env = self.active_behaviors[session_id]['environment']
        
        # Simulate access control
        if element.element_type == BIMElementType.ACCESS_CONTROL:
            # Simulate access attempts based on time
            if 8 <= env['time_of_day'] <= 18:
                access_attempts = 50  # High during work hours
            else:
                access_attempts = 5   # Low during off hours
            
            metrics['access_attempts'] = access_attempts
            metrics['authorized_access'] = access_attempts * 0.95  # 95% authorized
            metrics['unauthorized_access'] = access_attempts * 0.05  # 5% unauthorized
        
        # Simulate camera surveillance
        elif element.element_type == BIMElementType.SECURITY_CAMERA:
            metrics['recording_status'] = 'active'
            metrics['motion_detected'] = env['occupancy_level'] > 0.1
        
        state = BIMBehaviorState.NORMAL
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.SECURITY,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=[],
            recommendations=[]
        )
    
    async def _simulate_lighting_behavior(self, session_id: str, element_id: str,
                                         element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate lighting system behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        env = self.active_behaviors[session_id]['environment']
        
        # Calculate lighting based on occupancy and time
        if env['occupancy_level'] > 0.1 and 6 <= env['time_of_day'] <= 22:
            metrics['light_level'] = 500  # lux
            metrics['energy_consumption'] = 100  # W
        else:
            metrics['light_level'] = 50   # lux (night lighting)
            metrics['energy_consumption'] = 10   # W
        
        state = BIMBehaviorState.NORMAL
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.LIGHTING,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=[],
            recommendations=[]
        )
    
    async def _simulate_structural_behavior(self, session_id: str, element_id: str,
                                          element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate structural system behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        
        # Simulate structural load (simplified)
        metrics['load_percentage'] = 60.0  # Normal structural load
        metrics['deflection'] = 0.001      # mm
        metrics['stress_level'] = 0.4      # Normalized stress
        
        state = BIMBehaviorState.NORMAL
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.STRUCTURAL,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=[],
            recommendations=[]
        )
    
    async def _simulate_environmental_behavior(self, session_id: str, element_id: str,
                                             element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate environmental system behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        env = self.active_behaviors[session_id]['environment']
        
        # Update environmental metrics
        metrics['temperature'] = env['ambient_temperature']
        metrics['humidity'] = env['ambient_humidity']
        metrics['pressure'] = env['ambient_pressure']
        
        state = BIMBehaviorState.NORMAL
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.ENVIRONMENTAL,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=[],
            recommendations=[]
        )
    
    async def _simulate_occupancy_behavior(self, session_id: str, element_id: str,
                                          element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate occupancy behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        env = self.active_behaviors[session_id]['environment']
        
        # Update occupancy metrics
        metrics['occupancy_level'] = env['occupancy_level']
        metrics['movement_detected'] = env['occupancy_level'] > 0.1
        
        state = BIMBehaviorState.NORMAL
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.OCCUPANCY,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=[],
            recommendations=[]
        )
    
    async def _simulate_maintenance_behavior(self, session_id: str, element_id: str,
                                           element_data: Dict[str, Any]) -> BIMBehaviorResult:
        """Simulate maintenance behavior."""
        element = element_data['element']
        metrics = element_data['metrics']
        
        # Update maintenance metrics
        metrics['operational_hours'] += 1
        metrics['maintenance_hours'] += 1
        
        # Check maintenance schedule
        if metrics['operational_hours'] > 8760:  # 1 year
            state = BIMBehaviorState.MAINTENANCE
        else:
            state = BIMBehaviorState.NORMAL
        
        return BIMBehaviorResult(
            element_id=element_id,
            behavior_type=BIMBehaviorType.MAINTENANCE,
            state=state,
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            alerts=[],
            recommendations=[]
        )
    
    def _determine_hvac_state(self, metrics: Dict[str, Any]) -> BIMBehaviorState:
        """Determine HVAC system state based on metrics."""
        if metrics['energy_consumption'] > 10000:  # High energy consumption
            return BIMBehaviorState.WARNING
        elif metrics['temperature'] > 30 or metrics['temperature'] < 10:
            return BIMBehaviorState.CRITICAL
        else:
            return BIMBehaviorState.NORMAL
    
    def _determine_plumbing_state(self, metrics: Dict[str, Any]) -> BIMBehaviorState:
        """Determine plumbing system state based on metrics."""
        if metrics['water_pressure'] < 50:  # Low pressure
            return BIMBehaviorState.WARNING
        elif metrics['water_pressure'] < 20:
            return BIMBehaviorState.CRITICAL
        else:
            return BIMBehaviorState.NORMAL
    
    def _generate_hvac_alerts(self, metrics: Dict[str, Any], env: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Generate HVAC alerts and recommendations."""
        alerts = []
        recommendations = []
        
        if metrics['energy_consumption'] > 8000:
            alerts.append("High energy consumption detected")
            recommendations.append("Consider adjusting temperature setpoints")
        
        if abs(metrics['temperature'] - metrics['setpoint_temperature']) > 3:
            alerts.append("Temperature deviation from setpoint")
            recommendations.append("Check HVAC system operation")
        
        return alerts, recommendations
    
    def _generate_electrical_alerts(self, metrics: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Generate electrical alerts and recommendations."""
        alerts = []
        recommendations = []
        
        if metrics['load_percentage'] > 80:
            alerts.append("High electrical load detected")
            recommendations.append("Consider load balancing or equipment upgrade")
        
        if metrics['circuit_breaker_status'] == 'tripped':
            alerts.append("Circuit breaker tripped")
            recommendations.append("Check for electrical faults")
        
        return alerts, recommendations
    
    def _generate_plumbing_alerts(self, metrics: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Generate plumbing alerts and recommendations."""
        alerts = []
        recommendations = []
        
        if metrics['water_pressure'] < 100:
            alerts.append("Low water pressure detected")
            recommendations.append("Check for pipe leaks or pump issues")
        
        return alerts, recommendations
    
    def _update_element_state(self, session_id: str, element_id: str, result: BIMBehaviorResult):
        """Update element state with simulation results."""
        if session_id in self.active_behaviors:
            element_data = self.active_behaviors[session_id]['elements'].get(element_id)
            if element_data:
                element_data['state'] = result.state
                element_data['metrics'] = result.metrics.copy()
                element_data['last_update'] = result.timestamp
                element_data['alerts'] = result.alerts
                element_data['recommendations'] = result.recommendations
    
    def _store_simulation_results(self, session_id: str):
        """Store simulation results in history."""
        if session_id not in self.behavior_history:
            self.behavior_history[session_id] = []
        
        # Store current state for all elements
        for element_id, element_data in self.active_behaviors[session_id]['elements'].items():
            result = BIMBehaviorResult(
                element_id=element_id,
                behavior_type=element_data['behavior_type'],
                state=element_data['state'],
                timestamp=element_data['last_update'],
                metrics=element_data['metrics'].copy(),
                alerts=element_data['alerts'],
                recommendations=element_data['recommendations']
            )
            self.behavior_history[session_id].append(result)
    
    def get_simulation_status(self, session_id: str) -> Dict[str, Any]:
        """Get current simulation status."""
        if session_id not in self.active_behaviors:
            return {"error": "Session not found"}
        
        session_data = self.active_behaviors[session_id]
        elements = session_data['elements']
        
        # Calculate summary statistics
        total_elements = len(elements)
        normal_elements = sum(1 for e in elements.values() if e['state'] == BIMBehaviorState.NORMAL)
        warning_elements = sum(1 for e in elements.values() if e['state'] == BIMBehaviorState.WARNING)
        critical_elements = sum(1 for e in elements.values() if e['state'] == BIMBehaviorState.CRITICAL)
        
        total_energy = sum(e['metrics'].get('energy_consumption', 0) for e in elements.values())
        
        return {
            "session_id": session_id,
            "status": "running" if self.simulation_running else "stopped",
            "total_elements": total_elements,
            "normal_elements": normal_elements,
            "warning_elements": warning_elements,
            "critical_elements": critical_elements,
            "total_energy_consumption": total_energy,
            "environment": session_data['environment'],
            "start_time": session_data['start_time'].isoformat()
        }
    
    def stop_simulation(self, session_id: str) -> bool:
        """Stop BIM behavior simulation."""
        if session_id in self.active_behaviors:
            del self.active_behaviors[session_id]
            logger.info(f"Stopped BIM simulation session: {session_id}")
            return True
        return False 