"""
Business Rules Engine

This module provides a comprehensive business rules engine that validates
business logic, enforces constraints, and provides rule-based validation
for the application layer.
"""

import re
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

from application.exceptions import (
    BusinessRuleError, ValidationError, ApplicationError
)
from application.logging_config import get_logger

logger = get_logger("business_rules")


@dataclass
class BusinessRule:
    """Represents a business rule with validation logic."""
    
    name: str
    description: str
    validator: Callable[[Any], bool]
    error_message: str
    severity: str = "error"  # error, warning, info
    context: Optional[Dict[str, Any]] = None


class BusinessRuleEngine:
    """Engine for executing business rules and validations."""
    
    def __init__(self):
        """Initialize business rule engine."""
        self.logger = get_logger("business_rules.engine")
        self.rules: Dict[str, BusinessRule] = {}
        self._register_default_rules()
    
    def register_rule(self, rule: BusinessRule) -> None:
        """Register a business rule."""
        self.rules[rule.name] = rule
        self.logger.debug(f"Registered business rule: {rule.name}")
    
    def validate(self, data: Any, rule_names: List[str] = None) -> List[str]:
        """Validate data against specified rules or all rules."""
        errors = []
        warnings = []
        
        rules_to_check = rule_names if rule_names else list(self.rules.keys())
        
        for rule_name in rules_to_check:
            if rule_name not in self.rules:
                self.logger.warning(f"Unknown business rule: {rule_name}")
                continue
            
            rule = self.rules[rule_name]
            try:
                if not rule.validator(data):
                    if rule.severity == "error":
                        errors.append(rule.error_message)
                    elif rule.severity == "warning":
                        warnings.append(rule.error_message)
                    
                    self.logger.debug(f"Business rule '{rule.name}' failed: {rule.error_message}")
                    
            except Exception as e:
                self.logger.error(f"Error executing business rule '{rule.name}': {e}")
                errors.append(f"Rule execution error: {str(e)}")
        
        if errors:
            raise BusinessRuleError(
                message="Business rule validation failed",
                rule="multiple",
                context={"errors": errors, "warnings": warnings}
            )
        
        return warnings
    
    def _register_default_rules(self) -> None:
        """Register default business rules."""
        
        # Device rules
        self.register_rule(BusinessRule(
            name="device_name_required",
            description="Device name must be provided",
            validator=lambda data: bool(data.get('name', '').strip()),
            error_message="Device name is required"
        ))
        
        self.register_rule(BusinessRule(
            name="device_type_valid",
            description="Device type must be valid",
            validator=lambda data: data.get('device_type') in ['sensor', 'controller', 'monitor', 'actuator'],
            error_message="Device type must be one of: sensor, controller, monitor, actuator"
        ))
        
        self.register_rule(BusinessRule(
            name="device_serial_unique",
            description="Device serial number must be unique",
            validator=lambda data: self._validate_unique_serial(data),
            error_message="Device serial number must be unique"
        ))
        
        # Room rules
        self.register_rule(BusinessRule(
            name="room_number_format",
            description="Room number must follow proper format",
            validator=lambda data: re.match(r'^[A-Z]?\d+[A-Z]?$', data.get('room_number', '')),
            error_message="Room number must follow format: A1, 101, 2B, etc."
        ))
        
        self.register_rule(BusinessRule(
            name="room_capacity_limit",
            description="Room cannot exceed maximum device capacity",
            validator=lambda data: self._validate_room_capacity(data),
            error_message="Room has reached maximum device capacity"
        ))
        
        # User rules
        self.register_rule(BusinessRule(
            name="email_format",
            description="Email must be in valid format",
            validator=lambda data: re.match(r'^[^@]+@[^@]+\.[^@]+$', data.get('email', '')),
            error_message="Email must be in valid format"
        ))
        
        self.register_rule(BusinessRule(
            name="password_strength",
            description="Password must meet security requirements",
            validator=lambda data: self._validate_password_strength(data.get('password', '')),
            error_message="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        ))
        
        # Project rules
        self.register_rule(BusinessRule(
            name="project_dates_valid",
            description="Project start date must be before end date",
            validator=lambda data: self._validate_project_dates(data),
            error_message="Project start date must be before end date"
        ))
        
        self.register_rule(BusinessRule(
            name="project_budget_limit",
            description="Project budget must be within limits",
            validator=lambda data: self._validate_project_budget(data),
            error_message="Project budget exceeds maximum allowed amount"
        ))
        
        # Building rules
        self.register_rule(BusinessRule(
            name="building_address_valid",
            description="Building address must be valid",
            validator=lambda data: bool(data.get('address', '').strip()),
            error_message="Building address is required"
        ))
        
        self.register_rule(BusinessRule(
            name="building_coordinates_valid",
            description="Building coordinates must be valid",
            validator=lambda data: self._validate_coordinates(data),
            error_message="Building coordinates must be valid latitude/longitude"
        ))
    
    def _validate_unique_serial(self, data: Dict[str, Any]) -> bool:
        """Validate that device serial number is unique."""
        # This would typically check against the database
        # For now, we'll assume it's unique
        return True
    
    def _validate_room_capacity(self, data: Dict[str, Any]) -> bool:
        """Validate room device capacity."""
        # This would check current device count in the room
        # For now, we'll assume capacity is unlimited
        return True
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength."""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def _validate_project_dates(self, data: Dict[str, Any]) -> bool:
        """Validate project date constraints."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date or not end_date:
            return True  # Allow if dates are not provided
        
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        return start_date < end_date
    
    def _validate_project_budget(self, data: Dict[str, Any]) -> bool:
        """Validate project budget constraints."""
        budget = data.get('budget', 0)
        max_budget = 1000000  # $1M limit
        return budget <= max_budget
    
    def _validate_coordinates(self, data: Dict[str, Any]) -> bool:
        """Validate building coordinates."""
        coordinates = data.get('coordinates', {})
        lat = coordinates.get('latitude')
        lon = coordinates.get('longitude')
        
        if lat is None or lon is None:
            return True  # Allow if coordinates are not provided
        
        return -90 <= lat <= 90 and -180 <= lon <= 180


class ValidationEngine:
    """Engine for data validation and business rule enforcement."""
    
    def __init__(self):
        """Initialize validation engine."""
        self.logger = get_logger("validation.engine")
        self.business_rules = BusinessRuleEngine()
        self.validators: Dict[str, Callable] = {}
        self._register_default_validators()
    
    def register_validator(self, name: str, validator: Callable) -> None:
        """Register a custom validator."""
        self.validators[name] = validator
        self.logger.debug(f"Registered validator: {name}")
    
    def validate_data(self, data: Dict[str, Any], validators: List[str] = None) -> None:
        """Validate data using specified validators."""
        try:
            # Apply business rules
            if validators:
                self.business_rules.validate(data, validators)
            else:
                self.business_rules.validate(data)
            
            # Apply custom validators
            for validator_name, validator_func in self.validators.items():
                if not validators or validator_name in validators:
                    if not validator_func(data):
                        raise ValidationError(
                            message=f"Validation failed for {validator_name}",
                            field=validator_name,
                            value=data
                        )
            
            self.logger.debug("Data validation passed")
            
        except BusinessRuleError:
            raise
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            raise ValidationError(
                message="Data validation failed",
                field="general",
                value=str(e)
            )
    
    def _register_default_validators(self) -> None:
        """Register default validators."""
        
        # String validators
        self.register_validator("non_empty_string", lambda data: all(
            isinstance(v, str) and v.strip() for v in data.values() if isinstance(v, str)
        ))
        
        # Numeric validators
        self.register_validator("positive_number", lambda data: all(
            isinstance(v, (int, float)) and v > 0 for v in data.values() if isinstance(v, (int, float))
        ))
        
        # Date validators
        self.register_validator("future_date", lambda data: all(
            v > datetime.now() for v in data.values() if isinstance(v, datetime)
        ))
        
        # Email validator
        self.register_validator("valid_email", lambda data: all(
            re.match(r'^[^@]+@[^@]+\.[^@]+$', v) for v in data.values() if isinstance(v, str) and '@' in v
        ))


class BusinessRuleService:
    """Service for managing business rules and validations."""
    
    def __init__(self):
        """Initialize business rule service."""
        self.logger = get_logger("business_rules.service")
        self.validation_engine = ValidationEngine()
        self.business_rules = BusinessRuleEngine()
    
    def validate_entity_creation(self, entity_type: str, data: Dict[str, Any]) -> None:
        """Validate entity creation data."""
        try:
            # Get entity-specific rules
            rules = self._get_entity_rules(entity_type)
            
            # Validate data
            self.validation_engine.validate_data(data, rules)
            
            self.logger.info(f"Entity creation validation passed for {entity_type}")
            
        except Exception as e:
            self.logger.error(f"Entity creation validation failed for {entity_type}: {e}")
            raise
    
    def validate_entity_update(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> None:
        """Validate entity update data."""
        try:
            # Get entity-specific rules
            rules = self._get_entity_rules(entity_type)
            
            # Add update-specific rules
            update_rules = rules + [f"{entity_type}_update_specific"]
            
            # Validate data
            self.validation_engine.validate_data(data, update_rules)
            
            self.logger.info(f"Entity update validation passed for {entity_type} {entity_id}")
            
        except Exception as e:
            self.logger.error(f"Entity update validation failed for {entity_type} {entity_id}: {e}")
            raise
    
    def validate_business_operation(self, operation: str, data: Dict[str, Any]) -> None:
        """Validate business operation data."""
        try:
            # Get operation-specific rules
            rules = self._get_operation_rules(operation)
            
            # Validate data
            self.validation_engine.validate_data(data, rules)
            
            self.logger.info(f"Business operation validation passed for {operation}")
            
        except Exception as e:
            self.logger.error(f"Business operation validation failed for {operation}: {e}")
            raise
    
    def _get_entity_rules(self, entity_type: str) -> List[str]:
        """Get rules specific to an entity type."""
        rule_mapping = {
            "device": ["device_name_required", "device_type_valid", "device_serial_unique"],
            "room": ["room_number_format", "room_capacity_limit"],
            "user": ["email_format", "password_strength"],
            "project": ["project_dates_valid", "project_budget_limit"],
            "building": ["building_address_valid", "building_coordinates_valid"]
        }
        
        return rule_mapping.get(entity_type, [])
    
    def _get_operation_rules(self, operation: str) -> List[str]:
        """Get rules specific to a business operation."""
        rule_mapping = {
            "device_assignment": ["device_available", "room_capacity_limit"],
            "user_registration": ["email_format", "password_strength", "username_unique"],
            "project_creation": ["project_dates_valid", "project_budget_limit"],
            "building_construction": ["building_address_valid", "building_coordinates_valid"]
        }
        
        return rule_mapping.get(operation, [])


# Global business rule service instance
business_rule_service = BusinessRuleService()


def get_business_rule_service() -> BusinessRuleService:
    """Get the global business rule service instance."""
    return business_rule_service


def validate_business_rules(entity_type: str, data: Dict[str, Any]) -> None:
    """Validate business rules for entity data."""
    business_rule_service.validate_entity_creation(entity_type, data)


def validate_entity_update(entity_type: str, entity_id: str, data: Dict[str, Any]) -> None:
    """Validate business rules for entity update."""
    business_rule_service.validate_entity_update(entity_type, entity_id, data)


def validate_business_operation(operation: str, data: Dict[str, Any]) -> None:
    """Validate business rules for business operation."""
    business_rule_service.validate_business_operation(operation, data) 