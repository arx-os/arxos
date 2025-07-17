"""
SVGX Engine - Symbol Schema Validator Service

Provides comprehensive symbol schema validation for SVGX Engine with:
- SVGX schema validation
- Custom validation rules
- Performance optimization
- Error reporting and correction suggestions
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

from svgx_engine.utils.errors import ValidationError, SchemaError
from svgx_engine.logging.structured_logger import get_logger

logger = get_logger(__name__)


class ValidationLevel(Enum):
    """Validation levels for symbol schemas."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    COMPREHENSIVE = "comprehensive"


class SchemaType(Enum):
    """Schema types for validation."""
    SVGX_SYMBOL = "svgx_symbol"
    SVGX_ELEMENT = "svgx_element"
    SVGX_OBJECT = "svgx_object"
    SVGX_BEHAVIOR = "svgx_behavior"
    SVGX_PHYSICS = "svgx_physics"


@dataclass
class ValidationResult:
    """Result of schema validation."""
    is_valid: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    validation_time_ms: float = 0.0
    schema_type: Optional[SchemaType] = None
    validated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SchemaRule:
    """Schema validation rule."""
    name: str
    description: str
    rule_type: str
    pattern: Optional[str] = None
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    field_types: Dict[str, str] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    warning_message: str = ""


class SVGXSymbolSchemaValidator:
    """
    Comprehensive symbol schema validator for SVGX Engine.
    
    Features:
    - Multi-level validation (basic, standard, strict, comprehensive)
    - Custom validation rules and patterns
    - Performance optimization with caching
    - Detailed error reporting and correction suggestions
    - SVGX-specific schema validation
    - Real-time validation feedback
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """Initialize the symbol schema validator."""
        self.validation_level = validation_level
        self.rules: Dict[str, SchemaRule] = {}
        self.custom_validators: Dict[str, callable] = {}
        self.cache: Dict[str, ValidationResult] = {}
        self.stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'average_validation_time_ms': 0.0
        }
        
        self._initialize_default_rules()
        self._setup_custom_validators()
        
        logger.info("Symbol schema validator initialized", 
                   validation_level=validation_level.value)
    
    def _initialize_default_rules(self):
        """Initialize default validation rules."""
        # SVGX Symbol rules
        self.rules['svgx_symbol'] = SchemaRule(
            name="SVGX Symbol",
            description="Validates SVGX symbol structure",
            rule_type="object",
            required_fields=['id', 'type', 'attributes', 'content'],
            optional_fields=['metadata', 'behavior', 'physics', 'namespace'],
            field_types={
                'id': 'string',
                'type': 'string',
                'attributes': 'object',
                'content': 'string',
                'metadata': 'object',
                'behavior': 'object',
                'physics': 'object',
                'namespace': 'string'
            },
            constraints={
                'id': {'pattern': r'^[a-zA-Z][a-zA-Z0-9_-]*$'},
                'type': {'enum': ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path', 'text', 'g']},
                'namespace': {'pattern': r'^[a-zA-Z][a-zA-Z0-9_-]*$'}
            },
            error_message="Invalid SVGX symbol structure",
            warning_message="SVGX symbol has potential issues"
        )
        
        # SVGX Element rules
        self.rules['svgx_element'] = SchemaRule(
            name="SVGX Element",
            description="Validates SVGX element structure",
            rule_type="object",
            required_fields=['element_id', 'element_type', 'attributes'],
            optional_fields=['content', 'position', 'dimensions', 'style', 'transform'],
            field_types={
                'element_id': 'string',
                'element_type': 'string',
                'attributes': 'object',
                'content': 'string',
                'position': 'object',
                'dimensions': 'object',
                'style': 'object',
                'transform': 'object'
            },
            constraints={
                'element_id': {'pattern': r'^[a-zA-Z][a-zA-Z0-9_-]*$'},
                'element_type': {'enum': ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path', 'text', 'g']}
            },
            error_message="Invalid SVGX element structure",
            warning_message="SVGX element has potential issues"
        )
        
        # SVGX Object rules
        self.rules['svgx_object'] = SchemaRule(
            name="SVGX Object",
            description="Validates SVGX object structure",
            rule_type="object",
            required_fields=['object_id', 'object_type', 'system', 'properties'],
            optional_fields=['behavior', 'physics', 'metadata', 'relationships'],
            field_types={
                'object_id': 'string',
                'object_type': 'string',
                'system': 'string',
                'properties': 'object',
                'behavior': 'object',
                'physics': 'object',
                'metadata': 'object',
                'relationships': 'array'
            },
            constraints={
                'object_id': {'pattern': r'^[a-zA-Z][a-zA-Z0-9_-]*$'},
                'object_type': {'enum': ['electrical', 'mechanical', 'plumbing', 'fire_alarm', 'security', 'hvac']},
                'system': {'enum': ['electrical', 'mechanical', 'plumbing', 'fire_alarm', 'security', 'hvac', 'general']}
            },
            error_message="Invalid SVGX object structure",
            warning_message="SVGX object has potential issues"
        )
    
    def _setup_custom_validators(self):
        """Setup custom validation functions."""
        self.custom_validators['svgx_namespace'] = self._validate_svgx_namespace
        self.custom_validators['svgx_attributes'] = self._validate_svgx_attributes
        self.custom_validators['svgx_content'] = self._validate_svgx_content
        self.custom_validators['svgx_behavior'] = self._validate_svgx_behavior
        self.custom_validators['svgx_physics'] = self._validate_svgx_physics
    
    def validate_symbol(self, symbol_data: Dict[str, Any], 
                       schema_type: SchemaType = SchemaType.SVGX_SYMBOL,
                       cache_result: bool = True) -> ValidationResult:
        """
        Validate a symbol against the specified schema.
        
        Args:
            symbol_data: The symbol data to validate
            schema_type: The type of schema to validate against
            cache_result: Whether to cache the validation result
            
        Returns:
            ValidationResult: The validation result
        """
        start_time = datetime.utcnow()
        
        # Check cache first
        cache_key = self._generate_cache_key(symbol_data, schema_type)
        if cache_result and cache_key in self.cache:
            logger.debug("Using cached validation result", cache_key=cache_key)
            return self.cache[cache_key]
        
        # Initialize result
        result = ValidationResult(
            is_valid=True,
            schema_type=schema_type,
            validated_at=datetime.utcnow()
        )
        
        try:
            # Get validation rule
            rule = self.rules.get(schema_type.value)
            if not rule:
                result.errors.append({
                    'field': 'schema_type',
                    'message': f'Unknown schema type: {schema_type.value}',
                    'severity': 'error'
                })
                result.is_valid = False
                return result
            
            # Validate required fields
            self._validate_required_fields(symbol_data, rule, result)
            
            # Validate field types
            self._validate_field_types(symbol_data, rule, result)
            
            # Validate constraints
            self._validate_constraints(symbol_data, rule, result)
            
            # Run custom validators
            self._run_custom_validators(symbol_data, schema_type, result)
            
            # Update statistics
            self._update_stats(result)
            
            # Cache result if requested
            if cache_result:
                self.cache[cache_key] = result
            
            # Calculate validation time
            validation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.validation_time_ms = validation_time
            
            logger.info("Symbol validation completed",
                       schema_type=schema_type.value,
                       is_valid=result.is_valid,
                       error_count=len(result.errors),
                       warning_count=len(result.warnings),
                       validation_time_ms=validation_time)
            
            return result
            
        except Exception as e:
            logger.error("Symbol validation failed", error=str(e))
            result.is_valid = False
            result.errors.append({
                'field': 'validation',
                'message': f'Validation failed: {str(e)}',
                'severity': 'error'
            })
            return result
    
    def _validate_required_fields(self, data: Dict[str, Any], rule: SchemaRule, result: ValidationResult):
        """Validate required fields are present."""
        for field in rule.required_fields:
            if field not in data or data[field] is None:
                result.errors.append({
                    'field': field,
                    'message': f'Required field "{field}" is missing',
                    'severity': 'error'
                })
                result.is_valid = False
    
    def _validate_field_types(self, data: Dict[str, Any], rule: SchemaRule, result: ValidationResult):
        """Validate field types."""
        for field, expected_type in rule.field_types.items():
            if field in data:
                value = data[field]
                if not self._check_field_type(value, expected_type):
                    result.errors.append({
                        'field': field,
                        'message': f'Field "{field}" has wrong type. Expected {expected_type}, got {type(value).__name__}',
                        'severity': 'error'
                    })
                    result.is_valid = False
    
    def _validate_constraints(self, data: Dict[str, Any], rule: SchemaRule, result: ValidationResult):
        """Validate field constraints."""
        for field, constraints in rule.constraints.items():
            if field in data:
                value = data[field]
                
                # Pattern validation
                if 'pattern' in constraints:
                    pattern = constraints['pattern']
                    if not re.match(pattern, str(value)):
                        result.errors.append({
                            'field': field,
                            'message': f'Field "{field}" does not match pattern: {pattern}',
                            'severity': 'error'
                        })
                        result.is_valid = False
                
                # Enum validation
                if 'enum' in constraints:
                    allowed_values = constraints['enum']
                    if value not in allowed_values:
                        result.errors.append({
                            'field': field,
                            'message': f'Field "{field}" must be one of: {allowed_values}',
                            'severity': 'error'
                        })
                        result.is_valid = False
    
    def _run_custom_validators(self, data: Dict[str, Any], schema_type: SchemaType, result: ValidationResult):
        """Run custom validation functions."""
        for validator_name, validator_func in self.custom_validators.items():
            try:
                validator_result = validator_func(data, schema_type)
                if validator_result:
                    result.errors.extend(validator_result.get('errors', []))
                    result.warnings.extend(validator_result.get('warnings', []))
                    result.suggestions.extend(validator_result.get('suggestions', []))
                    
                    if validator_result.get('errors'):
                        result.is_valid = False
            except Exception as e:
                logger.warning(f"Custom validator {validator_name} failed", error=str(e))
    
    def _validate_svgx_namespace(self, data: Dict[str, Any], schema_type: SchemaType) -> Optional[Dict[str, Any]]:
        """Validate SVGX namespace."""
        result = {'errors': [], 'warnings': [], 'suggestions': []}
        
        if 'namespace' in data:
            namespace = data['namespace']
            if not namespace.startswith('arx:'):
                result['warnings'].append({
                    'field': 'namespace',
                    'message': 'Namespace should start with "arx:" for SVGX compatibility',
                    'severity': 'warning'
                })
                result['suggestions'].append('Consider using "arx:" prefix for namespace')
        
        return result if any(result.values()) else None
    
    def _validate_svgx_attributes(self, data: Dict[str, Any], schema_type: SchemaType) -> Optional[Dict[str, Any]]:
        """Validate SVGX attributes."""
        result = {'errors': [], 'warnings': [], 'suggestions': []}
        
        if 'attributes' in data:
            attributes = data['attributes']
            if isinstance(attributes, dict):
                # Check for required SVGX attributes
                svgx_attrs = ['arx:object', 'arx:type', 'arx:system']
                missing_attrs = [attr for attr in svgx_attrs if attr not in attributes]
                
                if missing_attrs:
                    result['warnings'].append({
                        'field': 'attributes',
                        'message': f'Missing recommended SVGX attributes: {missing_attrs}',
                        'severity': 'warning'
                    })
                    result['suggestions'].append('Add SVGX attributes for better integration')
        
        return result if any(result.values()) else None
    
    def _validate_svgx_content(self, data: Dict[str, Any], schema_type: SchemaType) -> Optional[Dict[str, Any]]:
        """Validate SVGX content."""
        result = {'errors': [], 'warnings': [], 'suggestions': []}
        
        if 'content' in data:
            content = data['content']
            if isinstance(content, str):
                # Check for basic SVG structure
                if not content.strip().startswith('<'):
                    result['errors'].append({
                        'field': 'content',
                        'message': 'Content should be valid SVG markup',
                        'severity': 'error'
                    })
        
        return result if any(result.values()) else None
    
    def _validate_svgx_behavior(self, data: Dict[str, Any], schema_type: SchemaType) -> Optional[Dict[str, Any]]:
        """Validate SVGX behavior."""
        result = {'errors': [], 'warnings': [], 'suggestions': []}
        
        if 'behavior' in data:
            behavior = data['behavior']
            if isinstance(behavior, dict):
                # Check for required behavior fields
                required_behavior_fields = ['type', 'triggers', 'actions']
                missing_fields = [field for field in required_behavior_fields if field not in behavior]
                
                if missing_fields:
                    result['warnings'].append({
                        'field': 'behavior',
                        'message': f'Missing recommended behavior fields: {missing_fields}',
                        'severity': 'warning'
                    })
        
        return result if any(result.values()) else None
    
    def _validate_svgx_physics(self, data: Dict[str, Any], schema_type: SchemaType) -> Optional[Dict[str, Any]]:
        """Validate SVGX physics."""
        result = {'errors': [], 'warnings': [], 'suggestions': []}
        
        if 'physics' in data:
            physics = data['physics']
            if isinstance(physics, dict):
                # Check for required physics fields
                required_physics_fields = ['type', 'properties']
                missing_fields = [field for field in required_physics_fields if field not in physics]
                
                if missing_fields:
                    result['warnings'].append({
                        'field': 'physics',
                        'message': f'Missing recommended physics fields: {missing_fields}',
                        'severity': 'warning'
                    })
        
        return result if any(result.values()) else None
    
    def _check_field_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches the expected type."""
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'integer':
            return isinstance(value, int)
        elif expected_type == 'number':
            return isinstance(value, (int, float))
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'object':
            return isinstance(value, dict)
        elif expected_type == 'array':
            return isinstance(value, list)
        else:
            return True  # Unknown type, assume valid
    
    def _generate_cache_key(self, data: Dict[str, Any], schema_type: SchemaType) -> str:
        """Generate cache key for validation result."""
        import hashlib
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(f"{schema_type.value}:{data_str}".encode()).hexdigest()
    
    def _update_stats(self, result: ValidationResult):
        """Update validation statistics."""
        self.stats['total_validations'] += 1
        if result.is_valid:
            self.stats['successful_validations'] += 1
        else:
            self.stats['failed_validations'] += 1
        
        # Update average validation time
        total_time = self.stats['average_validation_time_ms'] * (self.stats['total_validations'] - 1)
        total_time += result.validation_time_ms
        self.stats['average_validation_time_ms'] = total_time / self.stats['total_validations']
    
    def add_custom_rule(self, rule: SchemaRule):
        """Add a custom validation rule."""
        self.rules[rule.name] = rule
        logger.info("Custom validation rule added", rule_name=rule.name)
    
    def add_custom_validator(self, name: str, validator_func: callable):
        """Add a custom validation function."""
        self.custom_validators[name] = validator_func
        logger.info("Custom validator added", validator_name=name)
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            'stats': self.stats,
            'rules_count': len(self.rules),
            'custom_validators_count': len(self.custom_validators),
            'cache_size': len(self.cache)
        }
    
    def clear_cache(self):
        """Clear the validation cache."""
        self.cache.clear()
        logger.info("Validation cache cleared")
    
    def set_validation_level(self, level: ValidationLevel):
        """Set the validation level."""
        self.validation_level = level
        logger.info("Validation level updated", level=level.value)


# Factory function for creating validator instances
def create_symbol_validator(validation_level: ValidationLevel = ValidationLevel.STANDARD) -> SVGXSymbolSchemaValidator:
    """Create a new symbol schema validator instance."""
    return SVGXSymbolSchemaValidator(validation_level)


# Global validator instance
_symbol_validator = None


def get_symbol_validator() -> SVGXSymbolSchemaValidator:
    """Get the global symbol validator instance."""
    global _symbol_validator
    if _symbol_validator is None:
        _symbol_validator = create_symbol_validator()
    return _symbol_validator 