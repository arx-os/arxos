"""
Component Validator - Validate field worker input in real-time
Lightweight validation to ensure field worker observations make sense
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of component validation"""
    is_valid: bool
    confidence: float  # 0.0 to 1.0
    suggestions: List[str]
    warnings: List[str]
    errors: List[str]

class ComponentValidator:
    """
    Lightweight validator for field worker component input
    Focuses on common sense validation rather than complex AI
    """
    
    def __init__(self):
        # Common building component types
        self.valid_component_types = {
            'electrical': ['outlet', 'switch', 'panel', 'conduit', 'fixture'],
            'hvac': ['unit', 'duct', 'vent', 'thermostat', 'filter'],
            'plumbing': ['pipe', 'fixture', 'valve', 'drain', 'faucet'],
            'structural': ['wall', 'column', 'beam', 'slab', 'foundation'],
            'life_safety': ['sprinkler', 'alarm', 'detector', 'exit', 'extinguisher']
        }
        
        # Common property validators
        self.property_validators = {
            'electrical': {
                'voltage': lambda x: 0 < x <= 480,
                'amperage': lambda x: 0 < x <= 1000,
                'circuit_number': lambda x: isinstance(x, (int, str))
            },
            'hvac': {
                'capacity_tons': lambda x: 0 < x <= 100,
                'efficiency': lambda x: 0 < x <= 1.0,
                'temperature': lambda x: -50 < x < 150
            }
        }
    
    async def validate_component(self, 
                               component_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate field worker component input
        
        Args:
            component_data: Component data from field worker
            
        Returns:
            ValidationResult with validation status and suggestions
        """
        try:
            # Extract basic component info
            component_type = component_data.get('type', '').lower()
            properties = component_data.get('properties', {})
            location = component_data.get('location', {})
            
            # Basic validation
            validation_checks = [
                self._validate_component_type(component_type),
                self._validate_properties(component_type, properties),
                self._validate_location(location),
                self._validate_common_sense(component_data)
            ]
            
            # Aggregate results
            is_valid = all(check['is_valid'] for check in validation_checks)
            confidence = sum(check['confidence'] for check in validation_checks) / len(validation_checks)
            
            # Collect all suggestions and warnings
            suggestions = []
            warnings = []
            errors = []
            
            for check in validation_checks:
                suggestions.extend(check.get('suggestions', []))
                warnings.extend(check.get('warnings', []))
                errors.extend(check.get('errors', []))
            
            return ValidationResult(
                is_valid=is_valid,
                confidence=confidence,
                suggestions=suggestions,
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                suggestions=[],
                warnings=[],
                errors=[f"Validation failed: {str(e)}"]
            )
    
    def _validate_component_type(self, component_type: str) -> Dict[str, Any]:
        """Validate component type makes sense"""
        result = {
            'is_valid': True,
            'confidence': 1.0,
            'suggestions': [],
            'warnings': [],
            'errors': []
        }
        
        # Check if component type is recognized
        if not component_type:
            result['is_valid'] = False
            result['confidence'] = 0.0
            result['errors'].append("Component type is required")
            return result
        
        # Check if it's a valid building component type
        valid_types = []
        for category, types in self.valid_component_types.items():
            valid_types.extend(types)
        
        if component_type not in valid_types:
            result['warnings'].append(f"Unknown component type: {component_type}")
            result['suggestions'].append(f"Did you mean one of: {', '.join(valid_types[:5])}")
            result['confidence'] = 0.7
        
        return result
    
    def _validate_properties(self, component_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component properties make sense"""
        result = {
            'is_valid': True,
            'confidence': 1.0,
            'suggestions': [],
            'warnings': [],
            'errors': []
        }
        
        if not properties:
            return result
        
        # Check if component type has specific validators
        if component_type in self.property_validators:
            validators = self.property_validators[component_type]
            
            for prop_name, prop_value in properties.items():
                if prop_name in validators:
                    validator_func = validators[prop_name]
                    try:
                        if not validator_func(prop_value):
                            result['warnings'].append(f"Property {prop_name} value {prop_value} seems unusual")
                            result['confidence'] = min(result['confidence'], 0.8)
                    except Exception:
                        result['warnings'].append(f"Could not validate property {prop_name}")
                        result['confidence'] = min(result['confidence'], 0.9)
        
        return result
    
    def _validate_location(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Validate location information"""
        result = {
            'is_valid': True,
            'confidence': 1.0,
            'suggestions': [],
            'warnings': [],
            'errors': []
        }
        
        if not location:
            result['warnings'].append("No location information provided")
            result['confidence'] = 0.8
            return result
        
        # Check for required location fields
        required_fields = ['room', 'floor']
        for field in required_fields:
            if field not in location:
                result['suggestions'].append(f"Consider adding {field} information")
                result['confidence'] = min(result['confidence'], 0.9)
        
        return result
    
    def _validate_common_sense(self, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Common sense validation checks"""
        result = {
            'is_valid': True,
            'confidence': 1.0,
            'suggestions': [],
            'warnings': [],
            'errors': []
        }
        
        # Check for obvious errors
        if 'name' in component_data and len(component_data['name']) > 100:
            result['warnings'].append("Component name seems very long")
            result['confidence'] = min(result['confidence'], 0.8)
        
        # Check for missing critical information
        if 'type' not in component_data:
            result['errors'].append("Component type is required")
            result['is_valid'] = False
            result['confidence'] = 0.0
        
        return result
