"""
System Behavior Simulation Engine

This module provides simulation capabilities for:
- Power flow simulation (electrical systems)
- HVAC system simulation (air flow, temperature, humidity)
- Plumbing system simulation (water flow, pressure)
- Fire suppression system simulation
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """Result of a system simulation"""
    system_type: str
    timestamp: datetime
    status: str  # 'normal', 'warning', 'critical', 'failed'
    metrics: Dict[str, Any]
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PowerFlowNode:
    """Electrical node in power flow simulation"""
    node_id: str
    voltage: float  # Volts
    power_demand: float  # Watts
    power_supply: float = 0.0  # Watts
    max_capacity: float = float('inf')  # Watts
    efficiency: float = 1.0
    is_generator: bool = False
    is_load: bool = True
    is_bus: bool = False


@dataclass
class PowerFlowConnection:
    """Electrical connection between nodes"""
    from_node: str
    to_node: str
    resistance: float  # Ohms
    reactance: float  # Ohms
    max_current: float  # Amperes
    length: float = 0.0  # meters


@dataclass
class HVACZone:
    """HVAC zone for air flow simulation"""
    zone_id: str
    temperature: float  # Celsius
    humidity: float  # Percentage
    air_flow_rate: float  # CFM
    heat_load: float  # BTU/hr
    cooling_load: float  # BTU/hr
    volume: float  # cubic feet
    setpoint_temp: float = 22.0  # Celsius
    setpoint_humidity: float = 50.0  # Percentage


@dataclass
class HVACEquipment:
    """HVAC equipment (AHU, VAV, etc.)"""
    equipment_id: str
    equipment_type: str  # 'ahu', 'vav', 'chiller', 'boiler'
    capacity: float  # BTU/hr or CFM
    efficiency: float  # 0.0 to 1.0
    power_consumption: float  # Watts
    status: str = 'operational'  # 'operational', 'maintenance', 'failed'


@dataclass
class PlumbingNode:
    """Plumbing node for water flow simulation"""
    node_id: str
    pressure: float  # PSI
    flow_rate: float  # GPM
    demand: float  # GPM
    supply: float = 0.0  # GPM
    elevation: float = 0.0  # feet
    max_capacity: float = float('inf')  # GPM


@dataclass
class PlumbingConnection:
    """Plumbing connection between nodes"""
    from_node: str
    to_node: str
    diameter: float  # inches
    length: float  # feet
    roughness: float  # friction factor
    max_flow: float  # GPM


@dataclass
class FireSuppressionZone:
    """Fire suppression zone"""
    zone_id: str
    area: float  # square feet
    sprinkler_count: int
    sprinkler_spacing: float  # feet
    water_demand: float  # GPM
    pressure_required: float  # PSI
    coverage_density: float  # GPM/sq ft
    activation_time: float = 0.0  # seconds


class PowerFlowSimulator:
    """Electrical power flow simulation"""
    
    def __init__(self):
        self.nodes: Dict[str, PowerFlowNode] = {}
        self.connections: List[PowerFlowConnection] = []
        self.simulation_time = datetime.now()
    
    def add_node(self, node: PowerFlowNode):
        """Add a node to the power system"""
        self.nodes[node.node_id] = node
    
    def add_connection(self, connection: PowerFlowConnection):
        """Add a connection between nodes"""
        self.connections.append(connection)
    
    def simulate(self) -> SimulationResult:
        """Simulate power flow through the system"""
        try:
            # Initialize simulation
            self._initialize_simulation()
            
            # Run power flow calculation
            converged = self._solve_power_flow()
            
            if not converged:
                return SimulationResult(
                    system_type="power_flow",
                    timestamp=self.simulation_time,
                    status="critical",
                    metrics={"converged": False},
                    alerts=["Power flow simulation did not converge"]
                )
            
            # Calculate metrics
            metrics = self._calculate_power_metrics()
            
            # Check for issues
            alerts, recommendations = self._check_power_issues()
            
            # Determine status
            status = self._determine_power_status(alerts)
            
            return SimulationResult(
                system_type="power_flow",
                timestamp=self.simulation_time,
                status=status,
                metrics=metrics,
                alerts=alerts,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Power flow simulation error: {e}")
            return SimulationResult(
                system_type="power_flow",
                timestamp=self.simulation_time,
                status="failed",
                metrics={"error": str(e)},
                alerts=[f"Simulation error: {str(e)}"]
            )
    
    def _initialize_simulation(self):
        """Initialize simulation parameters"""
        # Set initial voltages for buses
        for node in self.nodes.values():
            if node.is_bus:
                node.voltage = 120.0  # Default voltage
            elif node.is_generator:
                node.voltage = 120.0
    
    def _solve_power_flow(self, max_iterations: int = 100, tolerance: float = 0.001) -> bool:
        """Solve power flow using Newton-Raphson method"""
        # Simplified power flow solution
        for iteration in range(max_iterations):
            max_change = 0.0
            
            for node in self.nodes.values():
                if node.is_load:
                    # Calculate power balance
                    total_power = node.power_supply - node.power_demand
                    
                    # Check capacity constraints
                    if abs(total_power) > node.max_capacity:
                        if total_power > 0:
                            node.power_supply = node.power_demand + node.max_capacity
                        else:
                            node.power_supply = node.power_demand - node.max_capacity
                    
                    # Update voltage based on power flow
                    if node.power_demand > 0:
                        voltage_drop = (node.power_demand * 0.1) / 120.0  # Simplified voltage drop
                        new_voltage = 120.0 - voltage_drop
                        voltage_change = abs(new_voltage - node.voltage)
                        node.voltage = new_voltage
                        max_change = max(max_change, voltage_change)
            
            if max_change < tolerance:
                return True
        
        return False
    
    def _calculate_power_metrics(self) -> Dict[str, Any]:
        """Calculate power system metrics"""
        total_demand = sum(node.power_demand for node in self.nodes.values() if node.is_load)
        total_supply = sum(node.power_supply for node in self.nodes.values() if node.is_generator)
        total_losses = sum(node.power_demand * 0.05 for node in self.nodes.values() if node.is_load)  # 5% losses
        
        return {
            "total_demand_watts": total_demand,
            "total_supply_watts": total_supply,
            "total_losses_watts": total_losses,
            "efficiency_percent": ((total_demand - total_losses) / total_demand * 100) if total_demand > 0 else 0,
            "voltage_range": {
                "min_voltage": min(node.voltage for node in self.nodes.values()),
                "max_voltage": max(node.voltage for node in self.nodes.values())
            },
            "node_count": len(self.nodes),
            "connection_count": len(self.connections)
        }
    
    def _check_power_issues(self) -> Tuple[List[str], List[str]]:
        """Check for power system issues"""
        alerts = []
        recommendations = []
        
        # Check voltage levels
        for node in self.nodes.values():
            if node.voltage < 110.0:
                alerts.append(f"Low voltage at node {node.node_id}: {node.voltage:.1f}V")
                recommendations.append(f"Check voltage regulation at node {node.node_id}")
            elif node.voltage > 130.0:
                alerts.append(f"High voltage at node {node.node_id}: {node.voltage:.1f}V")
                recommendations.append(f"Check voltage regulation at node {node.node_id}")
        
        # Check capacity constraints
        for node in self.nodes.values():
            if node.power_demand > node.max_capacity * 0.9:
                alerts.append(f"High load at node {node.node_id}: {node.power_demand:.1f}W")
                recommendations.append(f"Consider load balancing or capacity upgrade at node {node.node_id}")
        
        # Check power balance
        total_demand = sum(node.power_demand for node in self.nodes.values() if node.is_load)
        total_supply = sum(node.power_supply for node in self.nodes.values() if node.is_generator)
        
        if total_demand > total_supply:
            alerts.append(f"Power deficit: {total_demand - total_supply:.1f}W")
            recommendations.append("Increase power generation capacity")
        
        return alerts, recommendations
    
    def _determine_power_status(self, alerts: List[str]) -> str:
        """Determine overall system status"""
        if not alerts:
            return "normal"
        elif any("critical" in alert.lower() for alert in alerts):
            return "critical"
        elif len(alerts) > 3:
            return "warning"
        else:
            return "normal"


class HVACSimulator:
    """HVAC system simulation"""
    
    def __init__(self):
        self.zones: Dict[str, HVACZone] = {}
        self.equipment: Dict[str, HVACEquipment] = {}
        self.simulation_time = datetime.now()
        self.ambient_temp = 25.0  # Celsius
        self.ambient_humidity = 60.0  # Percentage
    
    def add_zone(self, zone: HVACZone):
        """Add a zone to the HVAC system"""
        self.zones[zone.zone_id] = zone
    
    def add_equipment(self, equipment: HVACEquipment):
        """Add equipment to the HVAC system"""
        self.equipment[equipment.equipment_id] = equipment
    
    def simulate(self, duration_minutes: int = 60) -> SimulationResult:
        """Simulate HVAC system behavior"""
        try:
            # Initialize simulation
            self._initialize_simulation()
            
            # Run time-step simulation
            for minute in range(duration_minutes):
                self._simulate_timestep()
            
            # Calculate metrics
            metrics = self._calculate_hvac_metrics()
            
            # Check for issues
            alerts, recommendations = self._check_hvac_issues()
            
            # Determine status
            status = self._determine_hvac_status(alerts)
            
            return SimulationResult(
                system_type="hvac",
                timestamp=self.simulation_time,
                status=status,
                metrics=metrics,
                alerts=alerts,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"HVAC simulation error: {e}")
            return SimulationResult(
                system_type="hvac",
                timestamp=self.simulation_time,
                status="failed",
                metrics={"error": str(e)},
                alerts=[f"Simulation error: {str(e)}"]
            )
    
    def _initialize_simulation(self):
        """Initialize HVAC simulation parameters"""
        for zone in self.zones.values():
            zone.temperature = self.ambient_temp
            zone.humidity = self.ambient_humidity
    
    def _simulate_timestep(self):
        """Simulate one time step"""
        for zone in self.zones.values():
            # Calculate heat transfer
            heat_gain = zone.heat_load / 60.0  # BTU per minute
            cooling_gain = zone.cooling_load / 60.0  # BTU per minute
            
            # Update temperature
            temp_change = (heat_gain - cooling_gain) / (zone.volume * 0.018)  # Simplified heat capacity
            zone.temperature += temp_change
            
            # Update humidity (simplified)
            if zone.temperature > zone.setpoint_temp:
                zone.humidity = max(30.0, zone.humidity - 0.1)
            else:
                zone.humidity = min(70.0, zone.humidity + 0.1)
            
            # Apply HVAC control
            if zone.temperature > zone.setpoint_temp + 1.0:
                # Cooling needed
                cooling_effect = min(2.0, zone.temperature - zone.setpoint_temp)
                zone.temperature -= cooling_effect
            elif zone.temperature < zone.setpoint_temp - 1.0:
                # Heating needed
                heating_effect = min(2.0, zone.setpoint_temp - zone.temperature)
                zone.temperature += heating_effect
    
    def _calculate_hvac_metrics(self) -> Dict[str, Any]:
        """Calculate HVAC system metrics"""
        total_cooling_load = sum(zone.cooling_load for zone in self.zones.values())
        total_heating_load = sum(zone.heat_load for zone in self.zones.values())
        total_power = sum(eq.power_consumption for eq in self.equipment.values())
        
        avg_temp = sum(zone.temperature for zone in self.zones.values()) / len(self.zones)
        avg_humidity = sum(zone.humidity for zone in self.zones.values()) / len(self.zones)
        
        return {
            "total_cooling_load_btu_hr": total_cooling_load,
            "total_heating_load_btu_hr": total_heating_load,
            "total_power_consumption_watts": total_power,
            "average_temperature_celsius": avg_temp,
            "average_humidity_percent": avg_humidity,
            "zone_count": len(self.zones),
            "equipment_count": len(self.equipment),
            "temperature_range": {
                "min_temp": min(zone.temperature for zone in self.zones.values()),
                "max_temp": max(zone.temperature for zone in self.zones.values())
            }
        }
    
    def _check_hvac_issues(self) -> Tuple[List[str], List[str]]:
        """Check for HVAC system issues"""
        alerts = []
        recommendations = []
        
        # Check temperature setpoints
        for zone in self.zones.values():
            if abs(zone.temperature - zone.setpoint_temp) > 3.0:
                alerts.append(f"Temperature deviation in zone {zone.zone_id}: {zone.temperature:.1f}°C")
                recommendations.append(f"Check HVAC controls for zone {zone.zone_id}")
            
            if zone.humidity < 30.0 or zone.humidity > 70.0:
                alerts.append(f"Humidity out of range in zone {zone.zone_id}: {zone.humidity:.1f}%")
                recommendations.append(f"Check humidity control for zone {zone.zone_id}")
        
        # Check equipment status
        for equipment in self.equipment.values():
            if equipment.status != 'operational':
                alerts.append(f"Equipment {equipment.equipment_id} status: {equipment.status}")
                recommendations.append(f"Service equipment {equipment.equipment_id}")
        
        return alerts, recommendations
    
    def _determine_hvac_status(self, alerts: List[str]) -> str:
        """Determine overall HVAC system status"""
        if not alerts:
            return "normal"
        elif any("failed" in alert.lower() for alert in alerts):
            return "critical"
        elif len(alerts) > 2:
            return "warning"
        else:
            return "normal"


class PlumbingSimulator:
    """Plumbing system simulation"""
    
    def __init__(self):
        self.nodes: Dict[str, PlumbingNode] = {}
        self.connections: List[PlumbingConnection] = []
        self.simulation_time = datetime.now()
        self.gravity = 32.2  # ft/s²
    
    def add_node(self, node: PlumbingNode):
        """Add a node to the plumbing system"""
        self.nodes[node.node_id] = node
    
    def add_connection(self, connection: PlumbingConnection):
        """Add a connection between nodes"""
        self.connections.append(connection)
    
    def simulate(self) -> SimulationResult:
        """Simulate water flow through the system"""
        try:
            # Initialize simulation
            self._initialize_simulation()
            
            # Solve flow network
            converged = self._solve_flow_network()
            
            if not converged:
                return SimulationResult(
                    system_type="plumbing",
                    timestamp=self.simulation_time,
                    status="critical",
                    metrics={"converged": False},
                    alerts=["Flow network simulation did not converge"]
                )
            
            # Calculate metrics
            metrics = self._calculate_plumbing_metrics()
            
            # Check for issues
            alerts, recommendations = self._check_plumbing_issues()
            
            # Determine status
            status = self._determine_plumbing_status(alerts)
            
            return SimulationResult(
                system_type="plumbing",
                timestamp=self.simulation_time,
                status=status,
                metrics=metrics,
                alerts=alerts,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Plumbing simulation error: {e}")
            return SimulationResult(
                system_type="plumbing",
                timestamp=self.simulation_time,
                status="failed",
                metrics={"error": str(e)},
                alerts=[f"Simulation error: {str(e)}"]
            )
    
    def _initialize_simulation(self):
        """Initialize plumbing simulation parameters"""
        # Set initial pressures for supply nodes
        for node in self.nodes.values():
            if node.supply > 0:
                node.pressure = 50.0  # PSI
            else:
                node.pressure = 0.0
    
    def _solve_flow_network(self, max_iterations: int = 100, tolerance: float = 0.001) -> bool:
        """Solve flow network using simplified method"""
        for iteration in range(max_iterations):
            max_change = 0.0
            
            # Calculate flow through connections
            for connection in self.connections:
                from_node = self.nodes[connection.from_node]
                to_node = self.nodes[connection.to_node]
                
                # Calculate pressure difference
                pressure_diff = from_node.pressure - to_node.pressure
                
                # Calculate flow using simplified Darcy-Weisbach
                if pressure_diff > 0:
                    # Flow from from_node to to_node
                    flow = math.sqrt(abs(pressure_diff) * connection.diameter**4 / (connection.length * connection.roughness))
                    flow = min(flow, connection.max_flow)
                    
                    # Update node flows
                    from_node.flow_rate = max(0, from_node.flow_rate - flow)
                    to_node.flow_rate += flow
                    
                    # Update pressure at to_node
                    new_pressure = from_node.pressure - (flow**2 * connection.roughness * connection.length) / (connection.diameter**4)
                    pressure_change = abs(new_pressure - to_node.pressure)
                    to_node.pressure = new_pressure
                    max_change = max(max_change, pressure_change)
            
            if max_change < tolerance:
                return True
        
        return False
    
    def _calculate_plumbing_metrics(self) -> Dict[str, Any]:
        """Calculate plumbing system metrics"""
        total_demand = sum(node.demand for node in self.nodes.values())
        total_supply = sum(node.supply for node in self.nodes.values())
        total_flow = sum(node.flow_rate for node in self.nodes.values())
        
        return {
            "total_demand_gpm": total_demand,
            "total_supply_gpm": total_supply,
            "total_flow_gpm": total_flow,
            "pressure_range": {
                "min_pressure": min(node.pressure for node in self.nodes.values()),
                "max_pressure": max(node.pressure for node in self.nodes.values())
            },
            "node_count": len(self.nodes),
            "connection_count": len(self.connections),
            "flow_efficiency": (total_flow / total_demand * 100) if total_demand > 0 else 0
        }
    
    def _check_plumbing_issues(self) -> Tuple[List[str], List[str]]:
        """Check for plumbing system issues"""
        alerts = []
        recommendations = []
        
        # Check pressure levels
        for node in self.nodes.values():
            if node.pressure < 20.0:
                alerts.append(f"Low pressure at node {node.node_id}: {node.pressure:.1f} PSI")
                recommendations.append(f"Check pressure regulation at node {node.node_id}")
            elif node.pressure > 100.0:
                alerts.append(f"High pressure at node {node.node_id}: {node.pressure:.1f} PSI")
                recommendations.append(f"Check pressure regulation at node {node.node_id}")
        
        # Check flow rates
        for node in self.nodes.values():
            if node.flow_rate > node.max_capacity * 0.9:
                alerts.append(f"High flow at node {node.node_id}: {node.flow_rate:.1f} GPM")
                recommendations.append(f"Check flow capacity at node {node.node_id}")
        
        # Check demand vs supply
        total_demand = sum(node.demand for node in self.nodes.values())
        total_supply = sum(node.supply for node in self.nodes.values())
        
        if total_demand > total_supply:
            alerts.append(f"Water deficit: {total_demand - total_supply:.1f} GPM")
            recommendations.append("Increase water supply capacity")
        
        return alerts, recommendations
    
    def _determine_plumbing_status(self, alerts: List[str]) -> str:
        """Determine overall plumbing system status"""
        if not alerts:
            return "normal"
        elif any("critical" in alert.lower() for alert in alerts):
            return "critical"
        elif len(alerts) > 2:
            return "warning"
        else:
            return "normal"


class FireSuppressionSimulator:
    """Fire suppression system simulation"""
    
    def __init__(self):
        self.zones: Dict[str, FireSuppressionZone] = {}
        self.simulation_time = datetime.now()
        self.water_supply_pressure = 80.0  # PSI
        self.water_supply_flow = 1000.0  # GPM
    
    def add_zone(self, zone: FireSuppressionZone):
        """Add a zone to the fire suppression system"""
        self.zones[zone.zone_id] = zone
    
    def simulate(self, fire_scenario: Dict[str, Any] = None) -> SimulationResult:
        """Simulate fire suppression system response"""
        try:
            # Initialize simulation
            self._initialize_simulation()
            
            # Apply fire scenario if provided
            if fire_scenario:
                self._apply_fire_scenario(fire_scenario)
            
            # Simulate system response
            self._simulate_system_response()
            
            # Calculate metrics
            metrics = self._calculate_fire_suppression_metrics()
            
            # Check for issues
            alerts, recommendations = self._check_fire_suppression_issues()
            
            # Determine status
            status = self._determine_fire_suppression_status(alerts)
            
            return SimulationResult(
                system_type="fire_suppression",
                timestamp=self.simulation_time,
                status=status,
                metrics=metrics,
                alerts=alerts,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Fire suppression simulation error: {e}")
            return SimulationResult(
                system_type="fire_suppression",
                timestamp=self.simulation_time,
                status="failed",
                metrics={"error": str(e)},
                alerts=[f"Simulation error: {str(e)}"]
            )
    
    def _initialize_simulation(self):
        """Initialize fire suppression simulation parameters"""
        for zone in self.zones.values():
            zone.activation_time = 0.0
    
    def _apply_fire_scenario(self, scenario: Dict[str, Any]):
        """Apply fire scenario to simulation"""
        fire_location = scenario.get('fire_location', 'zone_1')
        fire_intensity = scenario.get('fire_intensity', 'medium')  # low, medium, high
        
        if fire_location in self.zones:
            zone = self.zones[fire_location]
            if fire_intensity == 'high':
                zone.activation_time = 30.0  # seconds
            elif fire_intensity == 'medium':
                zone.activation_time = 60.0  # seconds
            else:
                zone.activation_time = 120.0  # seconds
    
    def _simulate_system_response(self):
        """Simulate fire suppression system response"""
        for zone in self.zones.values():
            if zone.activation_time > 0:
                # Calculate water flow to zone
                available_flow = min(self.water_supply_flow, zone.water_demand)
                zone.coverage_density = available_flow / zone.area
                
                # Check if pressure is sufficient
                if self.water_supply_pressure < zone.pressure_required:
                    zone.coverage_density *= 0.5  # Reduced effectiveness
    
    def _calculate_fire_suppression_metrics(self) -> Dict[str, Any]:
        """Calculate fire suppression system metrics"""
        total_area = sum(zone.area for zone in self.zones.values())
        total_sprinklers = sum(zone.sprinkler_count for zone in self.zones.values())
        activated_zones = sum(1 for zone in self.zones.values() if zone.activation_time > 0)
        
        return {
            "total_protected_area_sqft": total_area,
            "total_sprinkler_count": total_sprinklers,
            "activated_zones": activated_zones,
            "water_supply_pressure_psi": self.water_supply_pressure,
            "water_supply_flow_gpm": self.water_supply_flow,
            "average_coverage_density": sum(zone.coverage_density for zone in self.zones.values()) / len(self.zones),
            "zone_count": len(self.zones)
        }
    
    def _check_fire_suppression_issues(self) -> Tuple[List[str], List[str]]:
        """Check for fire suppression system issues"""
        alerts = []
        recommendations = []
        
        # Check coverage density
        for zone in self.zones.values():
            if zone.coverage_density < 0.1:  # Minimum coverage density
                alerts.append(f"Insufficient coverage in zone {zone.zone_id}: {zone.coverage_density:.2f} GPM/sq ft")
                recommendations.append(f"Increase sprinkler density in zone {zone.zone_id}")
        
        # Check water supply
        total_demand = sum(zone.water_demand for zone in self.zones.values())
        if total_demand > self.water_supply_flow:
            alerts.append(f"Insufficient water supply: {total_demand:.1f} GPM required")
            recommendations.append("Increase water supply capacity")
        
        # Check pressure
        max_pressure_required = max(zone.pressure_required for zone in self.zones.values())
        if max_pressure_required > self.water_supply_pressure:
            alerts.append(f"Insufficient water pressure: {max_pressure_required:.1f} PSI required")
            recommendations.append("Increase water supply pressure")
        
        return alerts, recommendations
    
    def _determine_fire_suppression_status(self, alerts: List[str]) -> str:
        """Determine overall fire suppression system status"""
        if not alerts:
            return "normal"
        elif any("critical" in alert.lower() for alert in alerts):
            return "critical"
        elif len(alerts) > 1:
            return "warning"
        else:
            return "normal"


class SystemSimulationEngine:
    """Main system simulation engine that coordinates all simulations"""
    
    def __init__(self):
        self.power_simulator = PowerFlowSimulator()
        self.hvac_simulator = HVACSimulator()
        self.plumbing_simulator = PlumbingSimulator()
        self.fire_suppression_simulator = FireSuppressionSimulator()
    
    def run_comprehensive_simulation(self, building_data: Dict[str, Any]) -> Dict[str, SimulationResult]:
        """Run comprehensive simulation of all building systems"""
        results = {}
        
        # Run power flow simulation
        if 'electrical' in building_data:
            self._setup_power_simulation(building_data['electrical'])
            results['power_flow'] = self.power_simulator.simulate()
        
        # Run HVAC simulation
        if 'hvac' in building_data:
            self._setup_hvac_simulation(building_data['hvac'])
            results['hvac'] = self.hvac_simulator.simulate()
        
        # Run plumbing simulation
        if 'plumbing' in building_data:
            self._setup_plumbing_simulation(building_data['plumbing'])
            results['plumbing'] = self.plumbing_simulator.simulate()
        
        # Run fire suppression simulation
        if 'fire_suppression' in building_data:
            self._setup_fire_suppression_simulation(building_data['fire_suppression'])
            results['fire_suppression'] = self.fire_suppression_simulator.simulate()
        
        return results
    
    def _setup_power_simulation(self, electrical_data: Dict[str, Any]):
        """Setup power flow simulation from building data"""
        # Clear existing data
        self.power_simulator.nodes.clear()
        self.power_simulator.connections.clear()
        
        # Add nodes
        for node_data in electrical_data.get('nodes', []):
            node = PowerFlowNode(
                node_id=node_data['id'],
                voltage=node_data.get('voltage', 120.0),
                power_demand=node_data.get('power_demand', 0.0),
                power_supply=node_data.get('power_supply', 0.0),
                max_capacity=node_data.get('max_capacity', float('inf')),
                is_generator=node_data.get('is_generator', False),
                is_load=node_data.get('is_load', True),
                is_bus=node_data.get('is_bus', False)
            )
            self.power_simulator.add_node(node)
        
        # Add connections
        for conn_data in electrical_data.get('connections', []):
            connection = PowerFlowConnection(
                from_node=conn_data['from_node'],
                to_node=conn_data['to_node'],
                resistance=conn_data.get('resistance', 0.1),
                reactance=conn_data.get('reactance', 0.0),
                max_current=conn_data.get('max_current', 100.0)
            )
            self.power_simulator.add_connection(connection)
    
    def _setup_hvac_simulation(self, hvac_data: Dict[str, Any]):
        """Setup HVAC simulation from building data"""
        # Clear existing data
        self.hvac_simulator.zones.clear()
        self.hvac_simulator.equipment.clear()
        
        # Add zones
        for zone_data in hvac_data.get('zones', []):
            zone = HVACZone(
                zone_id=zone_data['id'],
                temperature=zone_data.get('temperature', 22.0),
                humidity=zone_data.get('humidity', 50.0),
                air_flow_rate=zone_data.get('air_flow_rate', 100.0),
                heat_load=zone_data.get('heat_load', 0.0),
                cooling_load=zone_data.get('cooling_load', 0.0),
                volume=zone_data.get('volume', 1000.0)
            )
            self.hvac_simulator.add_zone(zone)
        
        # Add equipment
        for eq_data in hvac_data.get('equipment', []):
            equipment = HVACEquipment(
                equipment_id=eq_data['id'],
                equipment_type=eq_data['type'],
                capacity=eq_data.get('capacity', 1000.0),
                efficiency=eq_data.get('efficiency', 0.8),
                power_consumption=eq_data.get('power_consumption', 100.0)
            )
            self.hvac_simulator.add_equipment(equipment)
    
    def _setup_plumbing_simulation(self, plumbing_data: Dict[str, Any]):
        """Setup plumbing simulation from building data"""
        # Clear existing data
        self.plumbing_simulator.nodes.clear()
        self.plumbing_simulator.connections.clear()
        
        # Add nodes
        for node_data in plumbing_data.get('nodes', []):
            node = PlumbingNode(
                node_id=node_data['id'],
                pressure=node_data.get('pressure', 50.0),
                flow_rate=node_data.get('flow_rate', 0.0),
                demand=node_data.get('demand', 0.0),
                supply=node_data.get('supply', 0.0),
                elevation=node_data.get('elevation', 0.0)
            )
            self.plumbing_simulator.add_node(node)
        
        # Add connections
        for conn_data in plumbing_data.get('connections', []):
            connection = PlumbingConnection(
                from_node=conn_data['from_node'],
                to_node=conn_data['to_node'],
                diameter=conn_data.get('diameter', 1.0),
                length=conn_data.get('length', 10.0),
                roughness=conn_data.get('roughness', 0.01),
                max_flow=conn_data.get('max_flow', 100.0)
            )
            self.plumbing_simulator.add_connection(connection)
    
    def _setup_fire_suppression_simulation(self, fire_data: Dict[str, Any]):
        """Setup fire suppression simulation from building data"""
        # Clear existing data
        self.fire_suppression_simulator.zones.clear()
        
        # Add zones
        for zone_data in fire_data.get('zones', []):
            zone = FireSuppressionZone(
                zone_id=zone_data['id'],
                area=zone_data.get('area', 1000.0),
                sprinkler_count=zone_data.get('sprinkler_count', 10),
                sprinkler_spacing=zone_data.get('sprinkler_spacing', 12.0),
                water_demand=zone_data.get('water_demand', 100.0),
                pressure_required=zone_data.get('pressure_required', 30.0)
            )
            self.fire_suppression_simulator.add_zone(zone) 