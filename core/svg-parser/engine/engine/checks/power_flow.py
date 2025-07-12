"""
Power Flow Validation Module

This module provides comprehensive power flow validation for electrical systems,
including continuity checks, voltage drop calculations, current flow analysis,
and power distribution validation.
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PowerFlowStatus(Enum):
    """Power flow status enumeration."""
    NORMAL = "normal"
    OVERLOAD = "overload"
    UNDERLOAD = "underload"
    FAULT = "fault"
    OPEN_CIRCUIT = "open_circuit"
    SHORT_CIRCUIT = "short_circuit"


@dataclass
class PowerFlowResult:
    """Power flow validation result."""
    status: PowerFlowStatus
    voltage_drop: float
    current_flow: float
    power_loss: float
    efficiency: float
    warnings: List[str]
    errors: List[str]


@dataclass
class CircuitNode:
    """Circuit node representation."""
    node_id: str
    voltage: float
    current: float
    power: float
    resistance: float
    connections: List[str]
    node_type: str  # source, load, junction, etc.


@dataclass
class CircuitBranch:
    """Circuit branch representation."""
    branch_id: str
    from_node: str
    to_node: str
    resistance: float
    current: float
    voltage_drop: float
    power_loss: float


class PowerFlowValidator:
    """
    Power flow validator for electrical systems.
    
    This validator provides comprehensive analysis of electrical circuits,
    including voltage drop calculations, current flow analysis, power loss
    calculations, and fault detection.
    """
    
    def __init__(self):
        """Initialize the power flow validator."""
        self.circuits: Dict[str, Dict[str, CircuitNode]] = {}
        self.branches: Dict[str, List[CircuitBranch]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Electrical constants
        self.COPPER_RESISTIVITY = 1.68e-8  # ohm-meters
        self.ALUMINUM_RESISTIVITY = 2.82e-8  # ohm-meters
        
        # Validation thresholds
        self.MAX_VOLTAGE_DROP_PERCENT = 3.0  # 3% maximum voltage drop
        self.MAX_CURRENT_DENSITY = 1000  # A/mm²
        self.MIN_EFFICIENCY = 0.95  # 95% minimum efficiency
    
    def validate_circuit(self, circuit_data: Dict[str, Any]) -> PowerFlowResult:
        """
        Validate power flow in an electrical circuit.
        
        Args:
            circuit_data: Circuit configuration and parameters
            
        Returns:
            PowerFlowResult with validation results
        """
        try:
            # Parse circuit data
            circuit_id = circuit_data.get("circuit_id", "unknown")
            nodes = self._parse_nodes(circuit_data.get("nodes", []))
            branches = self._parse_branches(circuit_data.get("branches", []))
            
            # Store circuit data
            self.circuits[circuit_id] = nodes
            self.branches[circuit_id] = branches
            
            # Perform power flow analysis
            result = self._analyze_power_flow(circuit_id, nodes, branches)
            
            # Validate results
            warnings, errors = self._validate_power_flow_result(result, circuit_data)
            result.warnings.extend(warnings)
            result.errors.extend(errors)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Power flow validation failed: {e}")
            return PowerFlowResult(
                status=PowerFlowStatus.FAULT,
                voltage_drop=0.0,
                current_flow=0.0,
                power_loss=0.0,
                efficiency=0.0,
                warnings=[],
                errors=[f"Power flow validation failed: {str(e)}"]
            )
    
    def _parse_nodes(self, nodes_data: List[Dict[str, Any]]) -> Dict[str, CircuitNode]:
        """Parse circuit nodes from data."""
        nodes = {}
        
        for node_data in nodes_data:
            node = CircuitNode(
                node_id=node_data.get("node_id", ""),
                voltage=node_data.get("voltage", 0.0),
                current=node_data.get("current", 0.0),
                power=node_data.get("power", 0.0),
                resistance=node_data.get("resistance", 0.0),
                connections=node_data.get("connections", []),
                node_type=node_data.get("node_type", "load")
            )
            nodes[node.node_id] = node
        
        return nodes
    
    def _parse_branches(self, branches_data: List[Dict[str, Any]]) -> List[CircuitBranch]:
        """Parse circuit branches from data."""
        branches = []
        
        for branch_data in branches_data:
            branch = CircuitBranch(
                branch_id=branch_data.get("branch_id", ""),
                from_node=branch_data.get("from_node", ""),
                to_node=branch_data.get("to_node", ""),
                resistance=branch_data.get("resistance", 0.0),
                current=branch_data.get("current", 0.0),
                voltage_drop=0.0,
                power_loss=0.0
            )
            branches.append(branch)
        
        return branches
    
    def _analyze_power_flow(self, circuit_id: str, nodes: Dict[str, CircuitNode], 
                           branches: List[CircuitBranch]) -> PowerFlowResult:
        """Analyze power flow in the circuit."""
        try:
            # Find source nodes
            source_nodes = [node for node in nodes.values() if node.node_type == "source"]
            if not source_nodes:
                return PowerFlowResult(
                    status=PowerFlowStatus.FAULT,
                    voltage_drop=0.0,
                    current_flow=0.0,
                    power_loss=0.0,
                    efficiency=0.0,
                    warnings=[],
                    errors=["No source nodes found in circuit"]
                )
            
            # Calculate total load
            total_load = sum(node.power for node in nodes.values() if node.node_type == "load")
            
            # Calculate total current
            total_current = sum(node.current for node in nodes.values() if node.node_type == "load")
            
            # Calculate voltage drops in branches
            total_voltage_drop = 0.0
            total_power_loss = 0.0
            
            for branch in branches:
                # Calculate voltage drop in this branch
                branch.voltage_drop = branch.current * branch.resistance
                total_voltage_drop += branch.voltage_drop
                
                # Calculate power loss in this branch
                branch.power_loss = branch.current ** 2 * branch.resistance
                total_power_loss += branch.power_loss
            
            # Calculate efficiency
            total_input_power = sum(node.power for node in source_nodes)
            efficiency = (total_input_power - total_power_loss) / total_input_power if total_input_power > 0 else 0.0
            
            # Determine status
            status = self._determine_power_flow_status(total_voltage_drop, total_current, efficiency)
            
            return PowerFlowResult(
                status=status,
                voltage_drop=total_voltage_drop,
                current_flow=total_current,
                power_loss=total_power_loss,
                efficiency=efficiency,
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            self.logger.error(f"Power flow analysis failed: {e}")
            return PowerFlowResult(
                status=PowerFlowStatus.FAULT,
                voltage_drop=0.0,
                current_flow=0.0,
                power_loss=0.0,
                efficiency=0.0,
                warnings=[],
                errors=[f"Power flow analysis failed: {str(e)}"]
            )
    
    def _determine_power_flow_status(self, voltage_drop: float, current: float, 
                                   efficiency: float) -> PowerFlowStatus:
        """Determine power flow status based on analysis results."""
        if efficiency < self.MIN_EFFICIENCY:
            return PowerFlowStatus.FAULT
        elif voltage_drop > 0.03:  # 3% voltage drop
            return PowerFlowStatus.OVERLOAD
        elif current == 0:
            return PowerFlowStatus.OPEN_CIRCUIT
        else:
            return PowerFlowStatus.NORMAL
    
    def _validate_power_flow_result(self, result: PowerFlowResult, 
                                  circuit_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate power flow results and generate warnings/errors."""
        warnings = []
        errors = []
        
        # Check voltage drop
        if result.voltage_drop > 0.03:
            warnings.append(f"Voltage drop {result.voltage_drop:.2%} exceeds 3% limit")
        
        # Check efficiency
        if result.efficiency < self.MIN_EFFICIENCY:
            errors.append(f"Circuit efficiency {result.efficiency:.1%} below {self.MIN_EFFICIENCY:.1%}")
        
        # Check power loss
        total_power = circuit_data.get("total_power", 0)
        if total_power > 0:
            loss_percentage = (result.power_loss / total_power) * 100
            if loss_percentage > 5:
                warnings.append(f"Power loss {loss_percentage:.1%} is high")
        
        # Check current density
        conductor_area = circuit_data.get("conductor_area", 0)
        if conductor_area > 0 and result.current_flow > 0:
            current_density = result.current_flow / conductor_area
            if current_density > self.MAX_CURRENT_DENSITY:
                errors.append(f"Current density {current_density:.0f} A/mm² exceeds limit")
        
        return warnings, errors
    
    def calculate_voltage_drop(self, current: float, resistance: float, 
                             length: float, material: str = "copper") -> float:
        """
        Calculate voltage drop in a conductor.
        
        Args:
            current: Current in amperes
            resistance: Resistance in ohms
            length: Conductor length in meters
            material: Conductor material (copper or aluminum)
            
        Returns:
            Voltage drop in volts
        """
        try:
            # Calculate resistance per unit length
            if material.lower() == "copper":
                resistivity = self.COPPER_RESISTIVITY
            elif material.lower() == "aluminum":
                resistivity = self.ALUMINUM_RESISTIVITY
            else:
                resistivity = self.COPPER_RESISTIVITY  # Default to copper
            
            # Calculate voltage drop
            voltage_drop = current * resistance
            
            return voltage_drop
            
        except Exception as e:
            self.logger.error(f"Voltage drop calculation failed: {e}")
            return 0.0
    
    def calculate_conductor_resistance(self, length: float, cross_section: float, 
                                    material: str = "copper") -> float:
        """
        Calculate conductor resistance.
        
        Args:
            length: Conductor length in meters
            cross_section: Cross-sectional area in mm²
            material: Conductor material
            
        Returns:
            Resistance in ohms
        """
        try:
            if material.lower() == "copper":
                resistivity = self.COPPER_RESISTIVITY
            elif material.lower() == "aluminum":
                resistivity = self.ALUMINUM_RESISTIVITY
            else:
                resistivity = self.COPPER_RESISTIVITY
            
            # Convert cross-section from mm² to m²
            cross_section_m2 = cross_section * 1e-6
            
            # Calculate resistance
            resistance = resistivity * length / cross_section_m2
            
            return resistance
            
        except Exception as e:
            self.logger.error(f"Resistance calculation failed: {e}")
            return 0.0
    
    def validate_breaker_sizing(self, load_current: float, breaker_rating: float) -> Dict[str, Any]:
        """
        Validate circuit breaker sizing.
        
        Args:
            load_current: Load current in amperes
            breaker_rating: Breaker rating in amperes
            
        Returns:
            Validation result dictionary
        """
        try:
            load_percentage = (load_current / breaker_rating) * 100 if breaker_rating > 0 else 0
            
            if load_percentage > 100:
                return {
                    "valid": False,
                    "status": "overloaded",
                    "message": f"Breaker overloaded: {load_percentage:.1%}",
                    "load_percentage": load_percentage
                }
            elif load_percentage > 80:
                return {
                    "valid": True,
                    "status": "near_capacity",
                    "message": f"Breaker near capacity: {load_percentage:.1%}",
                    "load_percentage": load_percentage
                }
            else:
                return {
                    "valid": True,
                    "status": "normal",
                    "message": f"Breaker properly sized: {load_percentage:.1%}",
                    "load_percentage": load_percentage
                }
                
        except Exception as e:
            self.logger.error(f"Breaker sizing validation failed: {e}")
            return {
                "valid": False,
                "status": "error",
                "message": f"Validation failed: {str(e)}",
                "load_percentage": 0
            }
    
    def validate_wire_sizing(self, current: float, wire_size: float, 
                           insulation_temp: float = 90) -> Dict[str, Any]:
        """
        Validate wire sizing based on current and temperature.
        
        Args:
            current: Current in amperes
            wire_size: Wire size in AWG
            insulation_temp: Insulation temperature rating in °C
            
        Returns:
            Validation result dictionary
        """
        try:
            # Simplified ampacity table (90°C insulation)
            ampacity_table = {
                14: 25, 12: 30, 10: 40, 8: 55, 6: 75, 4: 95, 3: 115, 2: 130,
                1: 150, 1/0: 170, 2/0: 195, 3/0: 225, 4/0: 260, 250: 290, 300: 320,
                350: 350, 400: 380, 500: 430, 600: 475, 750: 545, 1000: 625
            }
            
            ampacity = ampacity_table.get(wire_size, 0)
            
            if ampacity == 0:
                return {
                    "valid": False,
                    "status": "invalid_size",
                    "message": f"Invalid wire size: {wire_size} AWG",
                    "ampacity": 0
                }
            
            load_percentage = (current / ampacity) * 100 if ampacity > 0 else 0
            
            if load_percentage > 100:
                return {
                    "valid": False,
                    "status": "oversized",
                    "message": f"Wire undersized: {load_percentage:.1%} of ampacity",
                    "ampacity": ampacity,
                    "load_percentage": load_percentage
                }
            elif load_percentage > 80:
                return {
                    "valid": True,
                    "status": "near_capacity",
                    "message": f"Wire near capacity: {load_percentage:.1%} of ampacity",
                    "ampacity": ampacity,
                    "load_percentage": load_percentage
                }
            else:
                return {
                    "valid": True,
                    "status": "properly_sized",
                    "message": f"Wire properly sized: {load_percentage:.1%} of ampacity",
                    "ampacity": ampacity,
                    "load_percentage": load_percentage
                }
                
        except Exception as e:
            self.logger.error(f"Wire sizing validation failed: {e}")
            return {
                "valid": False,
                "status": "error",
                "message": f"Validation failed: {str(e)}",
                "ampacity": 0
            }
    
    def calculate_power_factor(self, real_power: float, apparent_power: float) -> float:
        """
        Calculate power factor.
        
        Args:
            real_power: Real power in watts
            apparent_power: Apparent power in volt-amperes
            
        Returns:
            Power factor (0.0 to 1.0)
        """
        try:
            if apparent_power > 0:
                return real_power / apparent_power
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Power factor calculation failed: {e}")
            return 0.0
    
    def calculate_short_circuit_current(self, voltage: float, impedance: float) -> float:
        """
        Calculate short circuit current.
        
        Args:
            voltage: System voltage in volts
            impedance: System impedance in ohms
            
        Returns:
            Short circuit current in amperes
        """
        try:
            if impedance > 0:
                return voltage / impedance
            else:
                return float('inf')
                
        except Exception as e:
            self.logger.error(f"Short circuit current calculation failed: {e}")
            return 0.0
    
    def validate_ground_fault_protection(self, ground_fault_current: float, 
                                       trip_setting: float) -> Dict[str, Any]:
        """
        Validate ground fault protection.
        
        Args:
            ground_fault_current: Ground fault current in amperes
            trip_setting: Trip setting in amperes
            
        Returns:
            Validation result dictionary
        """
        try:
            if ground_fault_current > trip_setting:
                return {
                    "valid": False,
                    "status": "trip",
                    "message": f"Ground fault current {ground_fault_current}A exceeds trip setting {trip_setting}A",
                    "ground_fault_current": ground_fault_current,
                    "trip_setting": trip_setting
                }
            else:
                return {
                    "valid": True,
                    "status": "normal",
                    "message": f"Ground fault current {ground_fault_current}A within limits",
                    "ground_fault_current": ground_fault_current,
                    "trip_setting": trip_setting
                }
                
        except Exception as e:
            self.logger.error(f"Ground fault protection validation failed: {e}")
            return {
                "valid": False,
                "status": "error",
                "message": f"Validation failed: {str(e)}",
                "ground_fault_current": 0,
                "trip_setting": 0
            }
    
    def generate_power_flow_report(self, circuit_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive power flow report.
        
        Args:
            circuit_id: Circuit identifier
            
        Returns:
            Power flow report dictionary
        """
        try:
            if circuit_id not in self.circuits:
                return {"error": f"Circuit {circuit_id} not found"}
            
            nodes = self.circuits[circuit_id]
            branches = self.branches.get(circuit_id, [])
            
            # Calculate totals
            total_power = sum(node.power for node in nodes.values())
            total_current = sum(node.current for node in nodes.values())
            total_voltage_drop = sum(branch.voltage_drop for branch in branches)
            total_power_loss = sum(branch.power_loss for branch in branches)
            
            # Calculate efficiency
            efficiency = (total_power - total_power_loss) / total_power if total_power > 0 else 0.0
            
            # Generate node summary
            node_summary = []
            for node in nodes.values():
                node_summary.append({
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "voltage": node.voltage,
                    "current": node.current,
                    "power": node.power
                })
            
            # Generate branch summary
            branch_summary = []
            for branch in branches:
                branch_summary.append({
                    "branch_id": branch.branch_id,
                    "from_node": branch.from_node,
                    "to_node": branch.to_node,
                    "resistance": branch.resistance,
                    "current": branch.current,
                    "voltage_drop": branch.voltage_drop,
                    "power_loss": branch.power_loss
                })
            
            return {
                "circuit_id": circuit_id,
                "total_power": total_power,
                "total_current": total_current,
                "total_voltage_drop": total_voltage_drop,
                "total_power_loss": total_power_loss,
                "efficiency": efficiency,
                "voltage_drop_percentage": (total_voltage_drop / 120) * 100 if total_voltage_drop > 0 else 0,
                "power_loss_percentage": (total_power_loss / total_power) * 100 if total_power > 0 else 0,
                "nodes": node_summary,
                "branches": branch_summary
            }
            
        except Exception as e:
            self.logger.error(f"Power flow report generation failed: {e}")
            return {"error": f"Report generation failed: {str(e)}"} 