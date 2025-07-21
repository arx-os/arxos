"""
Building Code Validation Engine

This module provides the core validation engine for checking building designs
against building codes and regulations stored in the database.
"""

import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from core.models.building_regulations
    BuildingRegulationsDB, Regulation, ValidationRule, 
    BuildingValidation, ValidationViolation, ValidationStatus,
    ViolationSeverity, RegulationType
)

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, regulation_id: int, status: ValidationStatus, score: float = 0.0):
        self.regulation_id = regulation_id
        self.status = status
        self.score = score
        self.violations: List[ValidationViolation] = []
        self.warnings: List[ValidationViolation] = []
        self.passed_rules = 0
        self.failed_rules = 0
        self.total_rules = 0
        self.details: Dict[str, Any] = {}
    
    def add_violation(self, violation: ValidationViolation):
        """Add a violation to the result"""
        if violation.severity == ViolationSeverity.ERROR:
            self.violations.append(violation)
            self.failed_rules += 1
        elif violation.severity == ViolationSeverity.WARNING:
            self.warnings.append(violation)
        self.total_rules += 1
    
    def add_passed_rule(self):
        """Add a passed rule"""
        self.passed_rules += 1
        self.total_rules += 1
    
    def calculate_score(self):
        """Calculate compliance score"""
        if self.total_rules == 0:
            self.score = 100.0
        else:
            self.score = (self.passed_rules / self.total_rules) * 100.0
        
        # Determine status based on violations
        if self.failed_rules == 0:
            self.status = ValidationStatus.PASSED
        elif self.failed_rules < self.total_rules:
            self.status = ValidationStatus.PARTIAL
        else:
            self.status = ValidationStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'regulation_id': self.regulation_id,
            'status': self.status.value,
            'score': self.score,
            'total_rules': self.total_rules,
            'passed_rules': self.passed_rules,
            'failed_rules': self.failed_rules,
            'warnings': len(self.warnings),
            'violations': [v.__dict__ for v in self.violations],
            'warnings_list': [w.__dict__ for w in self.warnings],
            'details': self.details
        }


class RuleEngine:
    """Engine for executing validation rules"""
    
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
    
    def execute_rule(self, rule: ValidationRule, building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Execute a validation rule against building data"""
        try:
            # Parse rule logic
            rule_logic = json.loads(rule.rule_logic) if rule.rule_logic else {}
            
            # Get rule handler
            handler = self.rule_handlers.get(rule.rule_type, self._validate_general)
            
            # Execute rule
            is_valid, message = handler(rule_logic, building_data)
            
            return is_valid, message
            
        except Exception as e:
            logger.error(f"Error executing rule {rule.rule_name}: {e}")
            return False, f"Rule execution error: {str(e)}"
    
    def _validate_structural(self, rule_logic: Dict[str, Any], building_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate structural requirements"""
        try:
            # Extract structural data
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


class BuildingCodeValidator:
    """Main building code validation engine"""
    
    def __init__(self, db_path: str = "building_regulations.db"):
        """Initialize the validator with database connection"""
        self.db = BuildingRegulationsDB(db_path)
        self.rule_engine = RuleEngine()
        logger.info("Building code validator initialized")
    
    def validate_design(self, building_design: Dict[str, Any], 
                       regulation_types: Optional[List[str]] = None) -> List[ValidationResult]:
        """Validate building design against applicable regulations"""
        try:
            # Get applicable regulations
            regulations = self._get_applicable_regulations(regulation_types)
            
            results = []
            
            for regulation in regulations:
                logger.info(f"Validating regulation: {regulation.code}")
                
                # Get validation rules for this regulation
                rules = self.db.get_validation_rules(regulation.id)
                
                if not rules:
                    logger.warning(f"No validation rules found for regulation: {regulation.code}")
                    continue
                
                # Create validation result
                result = ValidationResult(regulation.id, ValidationStatus.PENDING)
                
                # Execute each rule
                for rule in rules:
                    is_valid, message = self.rule_engine.execute_rule(rule, building_design)
                    
                    if is_valid:
                        result.add_passed_rule()
                    else:
                        # Create violation
                        violation = ValidationViolation(
                            rule_id=rule.id,
                            violation_type=rule.rule_type,
                            severity=rule.severity,
                            description=message or f"Rule {rule.rule_name} failed",
                            created_dt=datetime.now()
                        )
                        result.add_violation(violation)
                
                # Calculate final result
                result.calculate_score()
                results.append(result)
                
                logger.info(f"Regulation {regulation.code} validation complete: {result.status.value} ({result.score:.1f}%)")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during design validation: {e}")
            raise
    
    def validate_specific_regulation(self, building_design: Dict[str, Any], 
                                   regulation_code: str) -> Optional[ValidationResult]:
        """Validate building design against a specific regulation"""
        try:
            # Get regulation by code
            regulations = self.db.get_regulations()
            regulation = next((r for r in regulations if r.code == regulation_code), None)
            
            if not regulation:
                logger.error(f"Regulation not found: {regulation_code}")
                return None
            
            # Validate against this regulation
            results = self.validate_design(building_design, [regulation.regulation_type])
            
            # Return the result for this regulation
            for result in results:
                if result.regulation_id == regulation.id:
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating specific regulation {regulation_code}: {e}")
            raise
    
    def _get_applicable_regulations(self, regulation_types: Optional[List[str]] = None) -> List[Regulation]:
        """Get regulations applicable to the current validation"""
        try:
            if regulation_types:
                # Filter by specific types
                regulations = []
                for reg_type in regulation_types:
                    type_regulations = self.db.get_regulations(regulation_type=reg_type)
                    regulations.extend(type_regulations)
                return regulations
            else:
                # Get all active regulations
                return self.db.get_regulations()
                
        except Exception as e:
            logger.error(f"Error getting applicable regulations: {e}")
            raise
    
    def get_compliance_report(self, building_id: str, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate a comprehensive compliance report"""
        try:
            report = {
                'building_id': building_id,
                'validation_date': datetime.now().isoformat(),
                'overall_status': 'passed',
                'overall_score': 0.0,
                'total_regulations': len(validation_results),
                'passed_regulations': 0,
                'failed_regulations': 0,
                'partial_regulations': 0,
                'total_violations': 0,
                'total_warnings': 0,
                'regulation_details': []
            }
            
            total_score = 0.0
            
            for result in validation_results:
                # Get regulation details
                regulations = self.db.get_regulations()
                regulation = next((r for r in regulations if r.id == result.regulation_id), None)
                
                regulation_detail = {
                    'regulation_code': regulation.code if regulation else 'Unknown',
                    'regulation_title': regulation.title if regulation else 'Unknown',
                    'status': result.status.value,
                    'score': result.score,
                    'total_rules': result.total_rules,
                    'passed_rules': result.passed_rules,
                    'failed_rules': result.failed_rules,
                    'warnings': len(result.warnings),
                    'violations': [v.__dict__ for v in result.violations],
                    'warnings_list': [w.__dict__ for w in result.warnings]
                }
                
                report['regulation_details'].append(regulation_detail)
                
                # Update counters
                if result.status == ValidationStatus.PASSED:
                    report['passed_regulations'] += 1
                elif result.status == ValidationStatus.FAILED:
                    report['failed_regulations'] += 1
                    report['overall_status'] = 'failed'
                elif result.status == ValidationStatus.PARTIAL:
                    report['partial_regulations'] += 1
                    report['overall_status'] = 'partial'
                
                report['total_violations'] += len(result.violations)
                report['total_warnings'] += len(result.warnings)
                total_score += result.score
            
            # Calculate overall score
            if report['total_regulations'] > 0:
                report['overall_score'] = total_score / report['total_regulations']
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        self.db.close()
        logger.info("Building code validator closed") 