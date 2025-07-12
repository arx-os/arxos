"""
Rule Engine for Auto-Checks

This module provides a comprehensive rule engine that automatically validates
object logic like power flow, system connectivity, and code compliance.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Rule type enumeration."""
    POWER_FLOW = "power_flow"
    CONNECTIVITY = "connectivity"
    SPEC_COMPLIANCE = "spec_compliance"
    PRESSURE_LOSS = "pressure_loss"
    TEMPERATURE = "temperature"
    EFFICIENCY = "efficiency"
    SAFETY = "safety"
    CODE_COMPLIANCE = "code_compliance"


class Severity(Enum):
    """Rule severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class RuleCondition:
    """Rule condition definition."""
    field: str
    operator: str
    value: Any
    description: str = ""


@dataclass
class RuleAction:
    """Rule action definition."""
    type: str
    function: str
    params: List[str]
    description: str = ""


@dataclass
class Rule:
    """Rule definition."""
    rule_id: str
    name: str
    description: str
    rule_type: RuleType
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    priority: int = 1
    tags: List[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ValidationResult:
    """Validation result."""
    rule_id: str
    rule_name: str
    severity: Severity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    object_id: str = ""
    system_type: str = ""


class RuleEngine:
    """
    Advanced rule engine for automatic validation and compliance checking.
    
    This engine provides comprehensive rule processing capabilities including
    power flow analysis, connectivity validation, pressure loss calculations,
    and code compliance checking.
    """
    
    def __init__(self):
        """Initialize the rule engine."""
        self.rules: Dict[str, Rule] = {}
        self.rule_chains: Dict[str, List[str]] = {}
        self.validation_results: List[ValidationResult] = []
        self.builtin_functions = self._init_builtin_functions()
        self.logger = logging.getLogger(__name__)
        
        # Load default rules
        self._load_default_rules()
    
    def _init_builtin_functions(self) -> Dict[str, Callable]:
        """Initialize built-in validation functions."""
        return {
            "validatePowerFlow": self._validate_power_flow,
            "validateConnectivity": self._validate_connectivity,
            "validatePressureLoss": self._validate_pressure_loss,
            "validateSpecCompliance": self._validate_spec_compliance,
            "validateTemperature": self._validate_temperature,
            "validateEfficiency": self._validate_efficiency,
            "validateSafety": self._validate_safety,
            "validateCodeCompliance": self._validate_code_compliance,
            "calculateVoltageDrop": self._calculate_voltage_drop,
            "calculatePressureDrop": self._calculate_pressure_drop,
            "calculateTemperatureRise": self._calculate_temperature_rise,
            "calculateEfficiency": self._calculate_efficiency,
            "checkOverload": self._check_overload,
            "checkUndersizing": self._check_undersizing,
            "checkOversizing": self._check_oversizing
        }
    
    def _load_default_rules(self):
        """Load default validation rules."""
        default_rules = [
            # Power Flow Rules
            {
                "rule_id": "electrical_continuity",
                "name": "Electrical Continuity Check",
                "description": "Validate electrical circuit continuity",
                "rule_type": RuleType.POWER_FLOW,
                "conditions": [
                    RuleCondition("object.system_type", "equals", "electrical", "Electrical system object")
                ],
                "actions": [
                    RuleAction("call_function", "validatePowerFlow", ["object"], "Validate power flow")
                ],
                "priority": 1,
                "tags": ["electrical", "continuity", "power_flow"]
            },
            
            # Connectivity Rules
            {
                "rule_id": "system_connectivity",
                "name": "System Connectivity Check",
                "description": "Validate system connectivity and dependencies",
                "rule_type": RuleType.CONNECTIVITY,
                "conditions": [
                    RuleCondition("object.connections", "not_empty", None, "Object has connections")
                ],
                "actions": [
                    RuleAction("call_function", "validateConnectivity", ["object"], "Validate connectivity")
                ],
                "priority": 1,
                "tags": ["connectivity", "dependencies"]
            },
            
            # Pressure Loss Rules
            {
                "rule_id": "pressure_loss_validation",
                "name": "Pressure Loss Check",
                "description": "Validate pressure loss in fluid systems",
                "rule_type": RuleType.PRESSURE_LOSS,
                "conditions": [
                    RuleCondition("object.system_type", "in", ["mechanical", "plumbing"], "Fluid system object")
                ],
                "actions": [
                    RuleAction("call_function", "validatePressureLoss", ["object"], "Validate pressure loss")
                ],
                "priority": 1,
                "tags": ["pressure", "fluid_flow", "mechanical", "plumbing"]
            },
            
            # Spec Compliance Rules
            {
                "rule_id": "spec_compliance",
                "name": "Specification Compliance Check",
                "description": "Validate object specifications against requirements",
                "rule_type": RuleType.SPEC_COMPLIANCE,
                "conditions": [
                    RuleCondition("object.specifications", "not_empty", None, "Object has specifications")
                ],
                "actions": [
                    RuleAction("call_function", "validateSpecCompliance", ["object"], "Validate spec compliance")
                ],
                "priority": 1,
                "tags": ["specifications", "compliance"]
            },
            
            # Temperature Rules
            {
                "rule_id": "temperature_validation",
                "name": "Temperature Check",
                "description": "Validate temperature limits and thermal performance",
                "rule_type": RuleType.TEMPERATURE,
                "conditions": [
                    RuleCondition("object.temperature", "not_none", None, "Object has temperature data")
                ],
                "actions": [
                    RuleAction("call_function", "validateTemperature", ["object"], "Validate temperature")
                ],
                "priority": 2,
                "tags": ["temperature", "thermal"]
            },
            
            # Efficiency Rules
            {
                "rule_id": "efficiency_validation",
                "name": "Efficiency Check",
                "description": "Validate system efficiency and performance",
                "rule_type": RuleType.EFFICIENCY,
                "conditions": [
                    RuleCondition("object.efficiency", "not_none", None, "Object has efficiency data")
                ],
                "actions": [
                    RuleAction("call_function", "validateEfficiency", ["object"], "Validate efficiency")
                ],
                "priority": 2,
                "tags": ["efficiency", "performance"]
            },
            
            # Safety Rules
            {
                "rule_id": "safety_validation",
                "name": "Safety Check",
                "description": "Validate safety requirements and protections",
                "rule_type": RuleType.SAFETY,
                "conditions": [
                    RuleCondition("object.safety_features", "not_empty", None, "Object has safety features")
                ],
                "actions": [
                    RuleAction("call_function", "validateSafety", ["object"], "Validate safety")
                ],
                "priority": 1,
                "tags": ["safety", "protection"]
            },
            
            # Code Compliance Rules
            {
                "rule_id": "code_compliance",
                "name": "Code Compliance Check",
                "description": "Validate code compliance and standards",
                "rule_type": RuleType.CODE_COMPLIANCE,
                "conditions": [
                    RuleCondition("object.code_requirements", "not_empty", None, "Object has code requirements")
                ],
                "actions": [
                    RuleAction("call_function", "validateCodeCompliance", ["object"], "Validate code compliance")
                ],
                "priority": 1,
                "tags": ["code", "standards", "compliance"]
            }
        ]
        
        for rule_data in default_rules:
            rule = Rule(**rule_data)
            self.add_rule(rule)
    
    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine."""
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added rule: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> None:
        """Remove a rule from the engine."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self.logger.info(f"Removed rule: {rule_id}")
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)
    
    def list_rules(self, rule_type: Optional[RuleType] = None) -> List[Rule]:
        """List rules, optionally filtered by type."""
        rules = list(self.rules.values())
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]
        return rules
    
    def validate_object(self, object_data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate an object against all applicable rules.
        
        Args:
            object_data: Object data to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
                
            if self._evaluate_conditions(rule.conditions, object_data):
                try:
                    rule_results = self._execute_actions(rule.actions, object_data, rule)
                    results.extend(rule_results)
                except Exception as e:
                    self.logger.error(f"Error executing rule {rule.rule_id}: {e}")
                    results.append(ValidationResult(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        severity=Severity.ERROR,
                        message=f"Rule execution failed: {str(e)}",
                        details={"error": str(e)},
                        timestamp=datetime.now(),
                        object_id=object_data.get("id", ""),
                        system_type=object_data.get("system_type", "")
                    ))
        
        self.validation_results.extend(results)
        return results
    
    def _evaluate_conditions(self, conditions: List[RuleCondition], object_data: Dict[str, Any]) -> bool:
        """Evaluate rule conditions against object data."""
        for condition in conditions:
            if not self._evaluate_condition(condition, object_data):
                return False
        return True
    
    def _evaluate_condition(self, condition: RuleCondition, object_data: Dict[str, Any]) -> bool:
        """Evaluate a single condition."""
        try:
            # Get field value using dot notation
            field_value = self._get_field_value(condition.field, object_data)
            
            if condition.operator == "equals":
                return field_value == condition.value
            elif condition.operator == "not_equals":
                return field_value != condition.value
            elif condition.operator == "greater_than":
                return field_value > condition.value
            elif condition.operator == "less_than":
                return field_value < condition.value
            elif condition.operator == "greater_than_or_equal":
                return field_value >= condition.value
            elif condition.operator == "less_than_or_equal":
                return field_value <= condition.value
            elif condition.operator == "in":
                return field_value in condition.value
            elif condition.operator == "not_in":
                return field_value not in condition.value
            elif condition.operator == "contains":
                return condition.value in field_value
            elif condition.operator == "not_contains":
                return condition.value not in field_value
            elif condition.operator == "not_empty":
                return field_value is not None and field_value != ""
            elif condition.operator == "is_empty":
                return field_value is None or field_value == ""
            elif condition.operator == "not_none":
                return field_value is not None
            elif condition.operator == "is_none":
                return field_value is None
            else:
                self.logger.warning(f"Unknown operator: {condition.operator}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {e}")
            return False
    
    def _get_field_value(self, field_path: str, object_data: Dict[str, Any]) -> Any:
        """Get field value using dot notation."""
        keys = field_path.split('.')
        value = object_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _execute_actions(self, actions: List[RuleAction], object_data: Dict[str, Any], rule: Rule) -> List[ValidationResult]:
        """Execute rule actions."""
        results = []
        
        for action in actions:
            if action.type == "call_function":
                function_name = action.function
                if function_name in self.builtin_functions:
                    try:
                        function_result = self.builtin_functions[function_name](object_data, *action.params)
                        if function_result:
                            results.append(ValidationResult(
                                rule_id=rule.rule_id,
                                rule_name=rule.name,
                                severity=function_result.get("severity", Severity.INFO),
                                message=function_result.get("message", ""),
                                details=function_result.get("details", {}),
                                timestamp=datetime.now(),
                                object_id=object_data.get("id", ""),
                                system_type=object_data.get("system_type", "")
                            ))
                    except Exception as e:
                        self.logger.error(f"Error executing function {function_name}: {e}")
                        results.append(ValidationResult(
                            rule_id=rule.rule_id,
                            rule_name=rule.name,
                            severity=Severity.ERROR,
                            message=f"Function execution failed: {str(e)}",
                            details={"error": str(e)},
                            timestamp=datetime.now(),
                            object_id=object_data.get("id", ""),
                            system_type=object_data.get("system_type", "")
                        ))
        
        return results
    
    # Built-in validation functions
    
    def _validate_power_flow(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate electrical power flow."""
        try:
            # Extract electrical properties
            voltage = object_data.get("voltage", 0)
            current = object_data.get("current", 0)
            power = object_data.get("power", 0)
            
            # Basic power flow validation
            calculated_power = voltage * current
            power_mismatch = abs(calculated_power - power) / power if power > 0 else 0
            
            if power_mismatch > 0.1:  # 10% tolerance
                return {
                    "severity": Severity.WARNING,
                    "message": f"Power flow mismatch detected: {power_mismatch:.1%}",
                    "details": {
                        "calculated_power": calculated_power,
                        "specified_power": power,
                        "mismatch_percentage": power_mismatch
                    }
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Power flow validation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _validate_connectivity(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate system connectivity."""
        try:
            connections = object_data.get("connections", [])
            
            if not connections:
                return {
                    "severity": Severity.WARNING,
                    "message": "Object has no connections",
                    "details": {"connections": connections}
                }
            
            # Check for orphaned connections
            orphaned = []
            for conn in connections:
                if not conn.get("target_id"):
                    orphaned.append(conn)
            
            if orphaned:
                return {
                    "severity": Severity.ERROR,
                    "message": f"Found {len(orphaned)} orphaned connections",
                    "details": {"orphaned_connections": orphaned}
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Connectivity validation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _validate_pressure_loss(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate pressure loss in fluid systems."""
        try:
            pressure_drop = object_data.get("pressure_drop", 0)
            max_pressure_drop = object_data.get("max_pressure_drop", float('inf'))
            
            if pressure_drop > max_pressure_drop:
                return {
                    "severity": Severity.ERROR,
                    "message": f"Pressure drop {pressure_drop} exceeds maximum {max_pressure_drop}",
                    "details": {
                        "pressure_drop": pressure_drop,
                        "max_pressure_drop": max_pressure_drop
                    }
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Pressure loss validation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _validate_spec_compliance(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate specification compliance."""
        try:
            specifications = object_data.get("specifications", {})
            requirements = object_data.get("requirements", {})
            
            violations = []
            for req_key, req_value in requirements.items():
                if req_key in specifications:
                    spec_value = specifications[req_key]
                    if not self._check_spec_compliance(spec_value, req_value):
                        violations.append({
                            "requirement": req_key,
                            "specified": spec_value,
                            "required": req_value
                        })
            
            if violations:
                return {
                    "severity": Severity.ERROR,
                    "message": f"Found {len(violations)} specification violations",
                    "details": {"violations": violations}
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Spec compliance validation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _validate_temperature(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate temperature limits."""
        try:
            temperature = object_data.get("temperature", 0)
            min_temp = object_data.get("min_temperature", -273)
            max_temp = object_data.get("max_temperature", 1000)
            
            if temperature < min_temp or temperature > max_temp:
                return {
                    "severity": Severity.WARNING,
                    "message": f"Temperature {temperature} outside limits [{min_temp}, {max_temp}]",
                    "details": {
                        "temperature": temperature,
                        "min_temperature": min_temp,
                        "max_temperature": max_temp
                    }
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Temperature validation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _validate_efficiency(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate system efficiency."""
        try:
            efficiency = object_data.get("efficiency", 0)
            min_efficiency = object_data.get("min_efficiency", 0)
            
            if efficiency < min_efficiency:
                return {
                    "severity": Severity.WARNING,
                    "message": f"Efficiency {efficiency:.1%} below minimum {min_efficiency:.1%}",
                    "details": {
                        "efficiency": efficiency,
                        "min_efficiency": min_efficiency
                    }
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Efficiency validation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _validate_safety(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate safety requirements."""
        try:
            safety_features = object_data.get("safety_features", [])
            required_safety = object_data.get("required_safety_features", [])
            
            missing_safety = []
            for req_feature in required_safety:
                if req_feature not in safety_features:
                    missing_safety.append(req_feature)
            
            if missing_safety:
                return {
                    "severity": Severity.ERROR,
                    "message": f"Missing safety features: {missing_safety}",
                    "details": {"missing_safety_features": missing_safety}
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Safety validation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _validate_code_compliance(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate code compliance."""
        try:
            code_requirements = object_data.get("code_requirements", {})
            object_specs = object_data.get("specifications", {})
            
            violations = []
            for code_key, code_value in code_requirements.items():
                if code_key in object_specs:
                    spec_value = object_specs[code_key]
                    if not self._check_code_compliance(spec_value, code_value):
                        violations.append({
                            "code_requirement": code_key,
                            "specified": spec_value,
                            "required": code_value
                        })
            
            if violations:
                return {
                    "severity": Severity.ERROR,
                    "message": f"Found {len(violations)} code compliance violations",
                    "details": {"violations": violations}
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Code compliance validation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _calculate_voltage_drop(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate voltage drop."""
        try:
            current = object_data.get("current", 0)
            resistance = object_data.get("resistance", 0)
            voltage_drop = current * resistance
            
            return {
                "severity": Severity.INFO,
                "message": f"Voltage drop calculated: {voltage_drop:.2f}V",
                "details": {"voltage_drop": voltage_drop}
            }
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Voltage drop calculation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _calculate_pressure_drop(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate pressure drop."""
        try:
            flow_rate = object_data.get("flow_rate", 0)
            length = object_data.get("length", 0)
            diameter = object_data.get("diameter", 0)
            
            # Simplified pressure drop calculation
            pressure_drop = (flow_rate ** 2) * length / (diameter ** 5)
            
            return {
                "severity": Severity.INFO,
                "message": f"Pressure drop calculated: {pressure_drop:.2f} PSI",
                "details": {"pressure_drop": pressure_drop}
            }
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Pressure drop calculation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _calculate_temperature_rise(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate temperature rise."""
        try:
            power = object_data.get("power", 0)
            mass_flow = object_data.get("mass_flow", 0)
            specific_heat = object_data.get("specific_heat", 1.0)
            
            if mass_flow > 0:
                temperature_rise = power / (mass_flow * specific_heat)
            else:
                temperature_rise = 0
            
            return {
                "severity": Severity.INFO,
                "message": f"Temperature rise calculated: {temperature_rise:.2f}°F",
                "details": {"temperature_rise": temperature_rise}
            }
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Temperature rise calculation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _calculate_efficiency(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate system efficiency."""
        try:
            input_power = object_data.get("input_power", 0)
            output_power = object_data.get("output_power", 0)
            
            if input_power > 0:
                efficiency = output_power / input_power
            else:
                efficiency = 0
            
            return {
                "severity": Severity.INFO,
                "message": f"Efficiency calculated: {efficiency:.1%}",
                "details": {"efficiency": efficiency}
            }
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Efficiency calculation failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _check_overload(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for overload conditions."""
        try:
            current_load = object_data.get("current_load", 0)
            rated_capacity = object_data.get("rated_capacity", 0)
            
            if rated_capacity > 0:
                load_percentage = (current_load / rated_capacity) * 100
                
                if load_percentage > 100:
                    return {
                        "severity": Severity.CRITICAL,
                        "message": f"System overloaded: {load_percentage:.1%}",
                        "details": {
                            "load_percentage": load_percentage,
                            "current_load": current_load,
                            "rated_capacity": rated_capacity
                        }
                    }
                elif load_percentage > 80:
                    return {
                        "severity": Severity.WARNING,
                        "message": f"System near capacity: {load_percentage:.1%}",
                        "details": {
                            "load_percentage": load_percentage,
                            "current_load": current_load,
                            "rated_capacity": rated_capacity
                        }
                    }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Overload check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _check_undersizing(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for undersizing conditions."""
        try:
            required_capacity = object_data.get("required_capacity", 0)
            actual_capacity = object_data.get("actual_capacity", 0)
            
            if required_capacity > 0 and actual_capacity < required_capacity:
                return {
                    "severity": Severity.ERROR,
                    "message": f"System undersized: {actual_capacity} < {required_capacity}",
                    "details": {
                        "required_capacity": required_capacity,
                        "actual_capacity": actual_capacity
                    }
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Undersizing check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _check_oversizing(self, object_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for oversizing conditions."""
        try:
            required_capacity = object_data.get("required_capacity", 0)
            actual_capacity = object_data.get("actual_capacity", 0)
            
            if required_capacity > 0 and actual_capacity > required_capacity * 1.5:
                return {
                    "severity": Severity.WARNING,
                    "message": f"System oversized: {actual_capacity} > {required_capacity * 1.5}",
                    "details": {
                        "required_capacity": required_capacity,
                        "actual_capacity": actual_capacity
                    }
                }
            
            return None
            
        except Exception as e:
            return {
                "severity": Severity.ERROR,
                "message": f"Oversizing check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _check_spec_compliance(self, spec_value: Any, req_value: Any) -> bool:
        """Check if a specification value meets requirements."""
        try:
            if isinstance(req_value, dict):
                # Range check
                if "min" in req_value and spec_value < req_value["min"]:
                    return False
                if "max" in req_value and spec_value > req_value["max"]:
                    return False
                if "equals" in req_value and spec_value != req_value["equals"]:
                    return False
            else:
                # Direct comparison
                if spec_value != req_value:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _check_code_compliance(self, spec_value: Any, code_value: Any) -> bool:
        """Check if a specification meets code requirements."""
        return self._check_spec_compliance(spec_value, code_value)
    
    def get_validation_results(self, object_id: Optional[str] = None) -> List[ValidationResult]:
        """Get validation results, optionally filtered by object ID."""
        results = self.validation_results
        if object_id:
            results = [r for r in results if r.object_id == object_id]
        return results
    
    def clear_validation_results(self) -> None:
        """Clear validation results."""
        self.validation_results.clear()
    
    def export_rules(self, file_path: str) -> None:
        """Export rules to file."""
        try:
            rules_data = []
            for rule in self.rules.values():
                rule_dict = asdict(rule)
                rule_dict["rule_type"] = rule.rule_type.value
                rules_data.append(rule_dict)
            
            with open(file_path, 'w') as f:
                yaml.dump(rules_data, f, default_flow_style=False)
            
            self.logger.info(f"Exported {len(rules_data)} rules to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export rules: {e}")
    
    def import_rules(self, file_path: str) -> None:
        """Import rules from file."""
        try:
            with open(file_path, 'r') as f:
                rules_data = yaml.safe_load(f)
            
            for rule_data in rules_data:
                rule_data["rule_type"] = RuleType(rule_data["rule_type"])
                rule = Rule(**rule_data)
                self.add_rule(rule)
            
            self.logger.info(f"Imported {len(rules_data)} rules from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to import rules: {e}") 