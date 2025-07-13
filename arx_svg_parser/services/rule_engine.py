"""
Enhanced Rule Engine for Building Code Validation

This module provides an enhanced rule engine that supports:
- Loading rules from external files (JSON/YAML)
- Rule management utilities (list, activate/deactivate, test)
- Rule compilation and execution
- Rule versioning and testing
"""

import json
import os
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from structlog import get_logger

try:
    from ..models.building_regulations import ValidationRule, ViolationSeverity
except ImportError:
    # Fallback for direct execution
    from models.building_regulations import ValidationRule, ViolationSeverity

logger = get_logger()


@dataclass
class RuleDefinition:
    """Rule definition from external file"""
    rule_name: str
    rule_type: str
    version: str = "1.0"
    description: Optional[str] = None
    severity: str = "error"
    priority: int = 1
    conditions: List[Dict[str, Any]] = None
    actions: List[Dict[str, Any]] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []
        if self.actions is None:
            self.actions = []
    
    def to_validation_rule(self, regulation_id: int) -> ValidationRule:
        """Convert to ValidationRule for database storage"""
        return ValidationRule(
            regulation_id=regulation_id,
            rule_name=self.rule_name,
            rule_type=self.rule_type,
            rule_logic=json.dumps(asdict(self)),
            conditions=json.dumps(self.conditions),
            actions=json.dumps(self.actions),
            severity=self.severity,
            priority=self.priority,
            description=self.description,
            active=self.enabled
        )


class EnhancedRuleEngine:
    """Enhanced rule engine with external file support and management utilities"""
    
    def __init__(self):
        self.rule_handlers: Dict[str, callable] = {
            'structural': self._validate_structural,
            'fire_safety': self._validate_fire_safety,
            'accessibility': self._validate_accessibility,
            'energy': self._validate_energy,
            'mechanical': self._validate_mechanical,
            'electrical': self._validate_electrical,
            'plumbing': self._validate_plumbing,
            'environmental': self._validate_environmental,
            'general': self._validate_general
        }
        self.loaded_rules: Dict[str, RuleDefinition] = {}
    
    def load_rules_from_file(self, file_path: str) -> List[RuleDefinition]:
        """Load rules from JSON file"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"Rule file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            rules = []
            
            # Handle single rule or list of rules
            if isinstance(data, dict):
                rules.append(self._parse_rule_definition(data))
            elif isinstance(data, list):
                for rule_data in data:
                    rules.append(self._parse_rule_definition(rule_data))
            else:
                raise ValueError("Invalid rule file format")
            
            # Store loaded rules
            for rule in rules:
                self.loaded_rules[rule.rule_name] = rule
            
            logger.info(f"Loaded {len(rules)} rules from {file_path}")
            return rules
            
        except Exception as e:
            logger.error(f"Error loading rules from {file_path}: {e}")
            raise
    
    def load_rules_from_directory(self, directory_path: str, pattern: str = "*.json") -> List[RuleDefinition]:
        """Load all rule files from a directory"""
        try:
            directory = Path(directory_path)
            
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            rules = []
            
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    file_rules = self.load_rules_from_file(str(file_path))
                    rules.extend(file_rules)
            
            logger.info(f"Loaded {len(rules)} rules from directory {directory_path}")
            return rules
            
        except Exception as e:
            logger.error(f"Error loading rules from directory {directory_path}: {e}")
            raise
    
    def _parse_rule_definition(self, rule_data: Dict[str, Any]) -> RuleDefinition:
        """Parse rule definition from dictionary"""
        try:
            return RuleDefinition(
                rule_name=rule_data['rule_name'],
                rule_type=rule_data['rule_type'],
                version=rule_data.get('version', '1.0'),
                description=rule_data.get('description'),
                severity=rule_data.get('severity', 'error'),
                priority=rule_data.get('priority', 1),
                conditions=rule_data.get('conditions', []),
                actions=rule_data.get('actions', []),
                enabled=rule_data.get('enabled', True)
            )
        except KeyError as e:
            raise ValueError(f"Missing required field in rule definition: {e}")
    
    def execute_rule(self, rule: Union[ValidationRule, RuleDefinition], 
                    building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Execute a validation rule against building data"""
        try:
            # Parse rule logic
            if isinstance(rule, ValidationRule):
                rule_logic = json.loads(rule.rule_logic) if rule.rule_logic else {}
            else:
                rule_logic = asdict(rule)
            
            # Get rule handler
            handler = self.rule_handlers.get(rule.rule_type, self._validate_general)
            
            # Execute rule
            is_valid, message = handler(rule_logic, building_data)
            
            return is_valid, message
            
        except Exception as e:
            logger.error(f"Error executing rule {getattr(rule, 'rule_name', 'unknown')}: {e}")
            return False, f"Rule execution error: {str(e)}"
    
    def test_rule(self, rule: Union[ValidationRule, RuleDefinition], 
                  test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a rule against test data and return detailed results"""
        try:
            is_valid, message = self.execute_rule(rule, test_data)
            
            result = {
                'rule_name': getattr(rule, 'rule_name', 'unknown'),
                'rule_type': getattr(rule, 'rule_type', 'unknown'),
                'passed': is_valid,
                'message': message,
                'test_data': test_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add condition details if available
            if hasattr(rule, 'conditions') and rule.conditions:
                result['condition_results'] = []
                for condition in rule.conditions:
                    condition_result = self._test_condition(condition, test_data)
                    result['condition_results'].append(condition_result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing rule: {e}")
            return {
                'rule_name': getattr(rule, 'rule_name', 'unknown'),
                'passed': False,
                'message': f"Test error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_condition(self, condition: Dict[str, Any], test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single condition against test data"""
        try:
            field_path = condition.get('field', '')
            operator = condition.get('operator', '')
            expected_value = condition.get('value')
            message = condition.get('message', '')
            
            # Get actual value
            actual_value = self._get_nested_value(test_data, field_path)
            
            # Apply operator
            is_valid = self._apply_operator(actual_value, operator, expected_value)
            
            return {
                'field': field_path,
                'operator': operator,
                'expected_value': expected_value,
                'actual_value': actual_value,
                'passed': is_valid,
                'message': message
            }
            
        except Exception as e:
            return {
                'field': condition.get('field', ''),
                'operator': condition.get('operator', ''),
                'expected_value': condition.get('value'),
                'actual_value': None,
                'passed': False,
                'message': f"Condition test error: {str(e)}"
            }
    
    def list_rules(self, rule_type: Optional[str] = None, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """List loaded rules with optional filtering"""
        rules = []
        
        for rule_name, rule in self.loaded_rules.items():
            if rule_type and rule.rule_type != rule_type:
                continue
            
            if enabled_only and not rule.enabled:
                continue
            
            rules.append({
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'version': rule.version,
                'description': rule.description,
                'severity': rule.severity,
                'priority': rule.priority,
                'enabled': rule.enabled,
                'condition_count': len(rule.conditions)
            })
        
        # Sort by priority (descending) then by name
        rules.sort(key=lambda x: (-x['priority'], x['rule_name']))
        
        return rules
    
    def get_rule(self, rule_name: str) -> Optional[RuleDefinition]:
        """Get a specific rule by name"""
        return self.loaded_rules.get(rule_name)
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable a rule"""
        if rule_name in self.loaded_rules:
            self.loaded_rules[rule_name].enabled = True
            logger.info(f"Enabled rule: {rule_name}")
            return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable a rule"""
        if rule_name in self.loaded_rules:
            self.loaded_rules[rule_name].enabled = False
            logger.info(f"Disabled rule: {rule_name}")
            return True
        return False
    
    def validate_rule_definition(self, rule_data: Dict[str, Any]) -> List[str]:
        """Validate a rule definition and return list of errors"""
        errors = []
        
        # Check required fields
        required_fields = ['rule_name', 'rule_type', 'conditions']
        for field in required_fields:
            if field not in rule_data:
                errors.append(f"Missing required field: {field}")
        
        # Check rule type
        if 'rule_type' in rule_data:
            valid_types = list(self.rule_handlers.keys())
            if rule_data['rule_type'] not in valid_types:
                errors.append(f"Invalid rule_type: {rule_data['rule_type']}. Valid types: {valid_types}")
        
        # Check severity
        if 'severity' in rule_data:
            valid_severities = ['error', 'warning', 'info']
            if rule_data['severity'] not in valid_severities:
                errors.append(f"Invalid severity: {rule_data['severity']}. Valid severities: {valid_severities}")
        
        # Check conditions
        if 'conditions' in rule_data:
            if not isinstance(rule_data['conditions'], list):
                errors.append("Conditions must be a list")
            else:
                for i, condition in enumerate(rule_data['conditions']):
                    condition_errors = self._validate_condition(condition)
                    for error in condition_errors:
                        errors.append(f"Condition {i}: {error}")
        
        return errors
    
    def _validate_condition(self, condition: Dict[str, Any]) -> List[str]:
        """Validate a single condition"""
        errors = []
        
        required_fields = ['field', 'operator', 'value']
        for field in required_fields:
            if field not in condition:
                errors.append(f"Missing required field: {field}")
        
        if 'operator' in condition:
            valid_operators = ['==', '!=', '>', '<', '>=', '<=', 'in', 'not_in']
            if condition['operator'] not in valid_operators:
                errors.append(f"Invalid operator: {condition['operator']}. Valid operators: {valid_operators}")
        
        return errors
    
    # Inherit all the validation methods from the original RuleEngine
    def _validate_structural(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate structural requirements"""
        try:
            structural_data = building_data.get('structural', {})
            
            # Check load requirements
            if 'load_requirements' in rule_logic:
                load_req = rule_logic['load_requirements']
                actual_loads = structural_data.get('loads', {})
                
                for load_type, required_value in load_req.items():
                    actual_value = actual_loads.get(load_type, 0)
                    if actual_value < required_value:
                        return False, f"Insufficient {load_type} load capacity: {actual_value} < {required_value}"
            
            # Check material requirements
            if 'material_requirements' in rule_logic:
                material_req = rule_logic['material_requirements']
                materials = structural_data.get('materials', {})
                
                for material_type, required_specs in material_req.items():
                    if material_type not in materials:
                        return False, f"Missing required material: {material_type}"
                    
                    material_specs = materials[material_type]
                    for spec, required_value in required_specs.items():
                        actual_value = material_specs.get(spec, 0)
                        if actual_value < required_value:
                            return False, f"Insufficient {spec} for {material_type}: {actual_value} < {required_value}"
            
            return True, None
            
        except Exception as e:
            return False, f"Structural validation error: {str(e)}"
    
    def _validate_fire_safety(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate fire safety requirements"""
        try:
            fire_data = building_data.get('fire_safety', {})
            
            # Check fire resistance ratings
            if 'fire_resistance' in rule_logic:
                fire_req = rule_logic['fire_resistance']
                actual_ratings = fire_data.get('fire_ratings', {})
                
                for element_type, required_rating in fire_req.items():
                    actual_rating = actual_ratings.get(element_type, 0)
                    if actual_rating < required_rating:
                        return False, f"Insufficient fire resistance for {element_type}: {actual_rating} < {required_rating}"
            
            # Check egress requirements
            if 'egress' in rule_logic:
                egress_req = rule_logic['egress']
                egress_data = fire_data.get('egress', {})
                
                # Check exit width
                if 'exit_width' in egress_req:
                    required_width = egress_req['exit_width']
                    actual_width = egress_data.get('exit_width', 0)
                    if actual_width < required_width:
                        return False, f"Insufficient exit width: {actual_width} < {required_width}"
                
                # Check exit distance
                if 'exit_distance' in egress_req:
                    required_distance = egress_req['exit_distance']
                    actual_distance = egress_data.get('exit_distance', float('inf'))
                    if actual_distance > required_distance:
                        return False, f"Exit distance too far: {actual_distance} > {required_distance}"
            
            return True, None
            
        except Exception as e:
            return False, f"Fire safety validation error: {str(e)}"
    
    def _validate_accessibility(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate accessibility requirements"""
        try:
            accessibility_data = building_data.get('accessibility', {})
            
            # Check clear width requirements
            if 'clear_width' in rule_logic:
                required_width = rule_logic['clear_width']
                actual_width = accessibility_data.get('clear_width', 0)
                if actual_width < required_width:
                    return False, f"Insufficient clear width: {actual_width} < {required_width}"
            
            # Check ramp requirements
            if 'ramp' in rule_logic:
                ramp_req = rule_logic['ramp']
                ramp_data = accessibility_data.get('ramp', {})
                
                # Check slope
                if 'max_slope' in ramp_req:
                    max_slope = ramp_req['max_slope']
                    actual_slope = ramp_data.get('slope', float('inf'))
                    if actual_slope > max_slope:
                        return False, f"Ramp slope too steep: {actual_slope} > {max_slope}"
                
                # Check handrails
                if 'handrails' in ramp_req and ramp_req['handrails']:
                    has_handrails = ramp_data.get('handrails', False)
                    if not has_handrails:
                        return False, "Missing required handrails on ramp"
            
            # Check door requirements
            if 'doors' in rule_logic:
                door_req = rule_logic['doors']
                doors_data = accessibility_data.get('doors', {})
                
                for door_type, requirements in door_req.items():
                    door_info = doors_data.get(door_type, {})
                    
                    # Check width
                    if 'width' in requirements:
                        required_width = requirements['width']
                        actual_width = door_info.get('width', 0)
                        if actual_width < required_width:
                            return False, f"Insufficient door width for {door_type}: {actual_width} < {required_width}"
                    
                    # Check threshold
                    if 'max_threshold' in requirements:
                        max_threshold = requirements['max_threshold']
                        actual_threshold = door_info.get('threshold', float('inf'))
                        if actual_threshold > max_threshold:
                            return False, f"Door threshold too high for {door_type}: {actual_threshold} > {max_threshold}"
            
            return True, None
            
        except Exception as e:
            return False, f"Accessibility validation error: {str(e)}"
    
    def _validate_energy(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate energy efficiency requirements"""
        try:
            energy_data = building_data.get('energy', {})
            
            # Check insulation requirements
            if 'insulation' in rule_logic:
                insulation_req = rule_logic['insulation']
                insulation_data = energy_data.get('insulation', {})
                
                for element_type, required_r_value in insulation_req.items():
                    actual_r_value = insulation_data.get(element_type, 0)
                    if actual_r_value < required_r_value:
                        return False, f"Insufficient insulation for {element_type}: R-{actual_r_value} < R-{required_r_value}"
            
            # Check window requirements
            if 'windows' in rule_logic:
                window_req = rule_logic['windows']
                windows_data = energy_data.get('windows', {})
                
                # Check U-factor
                if 'max_u_factor' in window_req:
                    max_u_factor = window_req['max_u_factor']
                    actual_u_factor = windows_data.get('u_factor', float('inf'))
                    if actual_u_factor > max_u_factor:
                        return False, f"Window U-factor too high: {actual_u_factor} > {max_u_factor}"
                
                # Check solar heat gain coefficient
                if 'max_shgc' in window_req:
                    max_shgc = window_req['max_shgc']
                    actual_shgc = windows_data.get('shgc', float('inf'))
                    if actual_shgc > max_shgc:
                        return False, f"Window SHGC too high: {actual_shgc} > {max_shgc}"
            
            return True, None
            
        except Exception as e:
            return False, f"Energy validation error: {str(e)}"
    
    def _validate_mechanical(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate mechanical system requirements"""
        try:
            mechanical_data = building_data.get('mechanical', {})
            
            # Check HVAC requirements
            if 'hvac' in rule_logic:
                hvac_req = rule_logic['hvac']
                hvac_data = mechanical_data.get('hvac', {})
                
                # Check ventilation rates
                if 'ventilation_rate' in hvac_req:
                    required_rate = hvac_req['ventilation_rate']
                    actual_rate = hvac_data.get('ventilation_rate', 0)
                    if actual_rate < required_rate:
                        return False, f"Insufficient ventilation rate: {actual_rate} < {required_rate}"
                
                # Check equipment efficiency
                if 'equipment_efficiency' in hvac_req:
                    efficiency_req = hvac_req['equipment_efficiency']
                    equipment_data = hvac_data.get('equipment', {})
                    
                    for equipment_type, required_efficiency in efficiency_req.items():
                        actual_efficiency = equipment_data.get(equipment_type, {}).get('efficiency', 0)
                        if actual_efficiency < required_efficiency:
                            return False, f"Insufficient efficiency for {equipment_type}: {actual_efficiency} < {required_efficiency}"
            
            return True, None
            
        except Exception as e:
            return False, f"Mechanical validation error: {str(e)}"
    
    def _validate_electrical(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate electrical system requirements"""
        try:
            electrical_data = building_data.get('electrical', {})
            
            # Check load calculations
            if 'load_calculations' in rule_logic:
                load_req = rule_logic['load_calculations']
                load_data = electrical_data.get('loads', {})
                
                for load_type, required_capacity in load_req.items():
                    actual_capacity = load_data.get(load_type, 0)
                    if actual_capacity < required_capacity:
                        return False, f"Insufficient electrical capacity for {load_type}: {actual_capacity} < {required_capacity}"
            
            # Check circuit requirements
            if 'circuits' in rule_logic:
                circuit_req = rule_logic['circuits']
                circuits_data = electrical_data.get('circuits', {})
                
                for circuit_type, requirements in circuit_req.items():
                    circuit_info = circuits_data.get(circuit_type, {})
                    
                    # Check wire size
                    if 'min_wire_size' in requirements:
                        min_wire_size = requirements['min_wire_size']
                        actual_wire_size = circuit_info.get('wire_size', 0)
                        if actual_wire_size < min_wire_size:
                            return False, f"Wire size too small for {circuit_type}: {actual_wire_size} < {min_wire_size}"
            
            return True, None
            
        except Exception as e:
            return False, f"Electrical validation error: {str(e)}"
    
    def _validate_plumbing(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate plumbing system requirements"""
        try:
            plumbing_data = building_data.get('plumbing', {})
            
            # Check fixture requirements
            if 'fixtures' in rule_logic:
                fixture_req = rule_logic['fixtures']
                fixtures_data = plumbing_data.get('fixtures', {})
                
                for fixture_type, requirements in fixture_req.items():
                    fixture_info = fixtures_data.get(fixture_type, {})
                    
                    # Check flow rate
                    if 'max_flow_rate' in requirements:
                        max_flow_rate = requirements['max_flow_rate']
                        actual_flow_rate = fixture_info.get('flow_rate', float('inf'))
                        if actual_flow_rate > max_flow_rate:
                            return False, f"Flow rate too high for {fixture_type}: {actual_flow_rate} > {max_flow_rate}"
            
            return True, None
            
        except Exception as e:
            return False, f"Plumbing validation error: {str(e)}"
    
    def _validate_environmental(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate environmental requirements"""
        try:
            environmental_data = building_data.get('environmental', {})
            
            # Check material sustainability
            if 'sustainable_materials' in rule_logic:
                material_req = rule_logic['sustainable_materials']
                materials_data = environmental_data.get('materials', {})
                
                for material_type, requirements in material_req.items():
                    material_info = materials_data.get(material_type, {})
                    
                    # Check recycled content
                    if 'min_recycled_content' in requirements:
                        min_content = requirements['min_recycled_content']
                        actual_content = material_info.get('recycled_content', 0)
                        if actual_content < min_content:
                            return False, f"Insufficient recycled content for {material_type}: {actual_content}% < {min_content}%"
            
            return True, None
            
        except Exception as e:
            return False, f"Environmental validation error: {str(e)}"
    
    def _validate_general(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate general requirements"""
        try:
            # Generic validation logic
            if 'conditions' in rule_logic:
                conditions = rule_logic['conditions']
                
                for condition in conditions:
                    field_path = condition.get('field')
                    operator = condition.get('operator')
                    value = condition.get('value')
                    
                    # Navigate to field in building data
                    field_value = self._get_nested_value(building_data, field_path)
                    
                    # Apply operator
                    if not self._apply_operator(field_value, operator, value):
                        return False, f"Condition failed: {field_path} {operator} {value}"
            
            return True, None
            
        except Exception as e:
            return False, f"General validation error: {str(e)}"
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _apply_operator(self, actual_value: Any, operator: str, expected_value: Any) -> bool:
        """Apply comparison operator"""
        if actual_value is None:
            return False
        
        if operator == '==':
            return actual_value == expected_value
        elif operator == '!=':
            return actual_value != expected_value
        elif operator == '>':
            return actual_value > expected_value
        elif operator == '>=':
            return actual_value >= expected_value
        elif operator == '<':
            return actual_value < expected_value
        elif operator == '<=':
            return actual_value <= expected_value
        elif operator == 'in':
            return actual_value in expected_value
        elif operator == 'not_in':
            return actual_value not in expected_value
        else:
            return False 