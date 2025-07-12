"""
Unified Validation Framework

This module provides a comprehensive validation framework that consolidates:
- BIM model validation
- Coordinate validation
- Symbol schema validation
- Building code validation
- Custom validation rules
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, ValidationError
import json
import re

from models.bim import BIMModel, BIMElement, BIMSystem, BIMRelationship
from models.enhanced_bim_elements import EnhancedBIMModel, System, Connection
from utils.errors import ValidationError as ArxosValidationError


class ValidationLevel(Enum):
    """Validation levels"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    COMPLIANCE = "compliance"


class ValidationCategory(Enum):
    """Validation categories"""
    GEOMETRY = "geometry"
    SPATIAL = "spatial"
    SYSTEM = "system"
    PROPERTY = "property"
    RELATIONSHIP = "relationship"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"


class ValidationSeverity(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    issue_id: str
    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    element_id: Optional[str] = None
    property_name: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    location: Optional[Dict[str, float]] = None
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of validation process"""
    valid: bool
    level: ValidationLevel
    total_issues: int
    errors: int
    warnings: int
    info: int
    issues: List[ValidationIssue] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    validation_time: float = 0.0
    
    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue"""
        self.issues.append(issue)
        self.total_issues += 1
        
        if issue.severity == ValidationSeverity.ERROR:
            self.errors += 1
            self.valid = False
        elif issue.severity == ValidationSeverity.WARNING:
            self.warnings += 1
        elif issue.severity == ValidationSeverity.INFO:
            self.info += 1
    
    def get_issues_by_category(self, category: ValidationCategory) -> List[ValidationIssue]:
        """Get issues filtered by category"""
        return [issue for issue in self.issues if issue.category == category]
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get issues filtered by severity"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        return {
            "valid": self.valid,
            "level": self.level.value,
            "total_issues": self.total_issues,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "validation_time": self.validation_time,
            "performance_metrics": self.performance_metrics,
            "issues_by_category": {
                category.value: len(self.get_issues_by_category(category))
                for category in ValidationCategory
            },
            "issues_by_severity": {
                severity.value: len(self.get_issues_by_severity(severity))
                for severity in ValidationSeverity
            }
        }


class UnifiedValidator:
    """
    Unified validation framework that consolidates all validation services.
    
    Features:
    - BIM model validation
    - Coordinate validation
    - Symbol schema validation
    - Building code validation
    - Custom validation rules
    - Performance optimization
    - Detailed reporting
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.logger = logging.getLogger(__name__)
        
        # Validation rules and validators
        self.field_validators: Dict[str, List[Callable[[Any], Optional[str]]]] = {}
        self.model_validators: List[Callable[[BaseModel], Optional[str]]] = []
        self.warning_validators: List[Callable[[BaseModel], Optional[str]]] = []
        
        # BIM-specific validators
        self.bim_validators: List[Callable[[Any], List[ValidationIssue]]] = []
        self.coordinate_validators: List[Callable[[Any], List[ValidationIssue]]] = []
        self.symbol_validators: List[Callable[[Any], List[ValidationIssue]]] = []
        self.building_code_validators: List[Callable[[Any], List[ValidationIssue]]] = []
        
        # Initialize default validators
        self._initialize_default_validators()
    
    def _initialize_default_validators(self):
        """Initialize default validation rules"""
        # BIM model validators
        self.bim_validators.extend([
            self._validate_bim_elements,
            self._validate_bim_systems,
            self._validate_bim_relationships,
            self._validate_bim_geometry
        ])
        
        # Coordinate validators
        self.coordinate_validators.extend([
            self._validate_coordinate_system,
            self._validate_coordinate_precision,
            self._validate_coordinate_bounds
        ])
        
        # Symbol validators
        self.symbol_validators.extend([
            self._validate_symbol_schema,
            self._validate_symbol_properties,
            self._validate_symbol_geometry
        ])
        
        # Building code validators
        self.building_code_validators.extend([
            self._validate_building_codes,
            self._validate_safety_requirements,
            self._validate_accessibility_requirements
        ])
    
    def validate_bim_model(self, bim_model: Union[BIMModel, EnhancedBIMModel]) -> ValidationResult:
        """
        Validate a BIM model comprehensively.
        
        Args:
            bim_model: BIM model to validate
            
        Returns:
            ValidationResult with detailed validation information
        """
        import time
        start_time = time.time()
        
        result = ValidationResult(
            valid=True,
            level=self.validation_level,
            total_issues=0,
            errors=0,
            warnings=0,
            info=0
        )
        
        try:
            # Run BIM-specific validations
            for validator in self.bim_validators:
                issues = validator(bim_model)
                for issue in issues:
                    result.add_issue(issue)
            
            # Run coordinate validations
            for validator in self.coordinate_validators:
                issues = validator(bim_model)
                for issue in issues:
                    result.add_issue(issue)
            
            # Run building code validations for comprehensive level
            if self.validation_level in [ValidationLevel.COMPREHENSIVE, ValidationLevel.COMPLIANCE]:
                for validator in self.building_code_validators:
                    issues = validator(bim_model)
                    for issue in issues:
                        result.add_issue(issue)
            
            result.validation_time = time.time() - start_time
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            result.add_issue(ValidationIssue(
                issue_id="validation_error",
                category=ValidationCategory.PERFORMANCE,
                severity=ValidationSeverity.ERROR,
                message=f"Validation process failed: {str(e)}"
            ))
        
        return result
    
    def validate_coordinates(self, coordinates: List[float], context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate coordinate data.
        
        Args:
            coordinates: Coordinate data to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult with coordinate validation information
        """
        result = ValidationResult(
            valid=True,
            level=self.validation_level,
            total_issues=0,
            errors=0,
            warnings=0,
            info=0
        )
        
        try:
            for validator in self.coordinate_validators:
                issues = validator({"coordinates": coordinates, "context": context})
                for issue in issues:
                    result.add_issue(issue)
                    
        except Exception as e:
            self.logger.error(f"Coordinate validation failed: {e}")
            result.add_issue(ValidationIssue(
                issue_id="coordinate_validation_error",
                category=ValidationCategory.GEOMETRY,
                severity=ValidationSeverity.ERROR,
                message=f"Coordinate validation failed: {str(e)}"
            ))
        
        return result
    
    def validate_symbol(self, symbol_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate symbol data.
        
        Args:
            symbol_data: Symbol data to validate
            
        Returns:
            ValidationResult with symbol validation information
        """
        result = ValidationResult(
            valid=True,
            level=self.validation_level,
            total_issues=0,
            errors=0,
            warnings=0,
            info=0
        )
        
        try:
            for validator in self.symbol_validators:
                issues = validator(symbol_data)
                for issue in issues:
                    result.add_issue(issue)
                    
        except Exception as e:
            self.logger.error(f"Symbol validation failed: {e}")
            result.add_issue(ValidationIssue(
                issue_id="symbol_validation_error",
                category=ValidationCategory.PROPERTY,
                severity=ValidationSeverity.ERROR,
                message=f"Symbol validation failed: {str(e)}"
            ))
        
        return result
    
    def validate_building_codes(self, building_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate building code compliance.
        
        Args:
            building_data: Building data to validate
            
        Returns:
            ValidationResult with building code validation information
        """
        result = ValidationResult(
            valid=True,
            level=self.validation_level,
            total_issues=0,
            errors=0,
            warnings=0,
            info=0
        )
        
        try:
            for validator in self.building_code_validators:
                issues = validator(building_data)
                for issue in issues:
                    result.add_issue(issue)
                    
        except Exception as e:
            self.logger.error(f"Building code validation failed: {e}")
            result.add_issue(ValidationIssue(
                issue_id="building_code_validation_error",
                category=ValidationCategory.COMPLIANCE,
                severity=ValidationSeverity.ERROR,
                message=f"Building code validation failed: {str(e)}"
            ))
        
        return result
    
    # BIM Validation Methods
    def _validate_bim_elements(self, bim_model: Union[BIMModel, EnhancedBIMModel]) -> List[ValidationIssue]:
        """Validate BIM elements"""
        issues = []
        
        elements = bim_model.get_all_elements() if hasattr(bim_model, 'get_all_elements') else bim_model.elements
        
        for element in elements:
            # Check element ID
            if not element.id or not element.id.strip():
                issues.append(ValidationIssue(
                    issue_id="missing_element_id",
                    category=ValidationCategory.PROPERTY,
                    severity=ValidationSeverity.ERROR,
                    message="Element missing ID",
                    element_id=getattr(element, 'id', None)
                ))
            
            # Check element name
            if not element.name or not element.name.strip():
                issues.append(ValidationIssue(
                    issue_id="missing_element_name",
                    category=ValidationCategory.PROPERTY,
                    severity=ValidationSeverity.WARNING,
                    message="Element missing name",
                    element_id=getattr(element, 'id', None)
                ))
            
            # Check element type
            if not element.element_type:
                issues.append(ValidationIssue(
                    issue_id="missing_element_type",
                    category=ValidationCategory.PROPERTY,
                    severity=ValidationSeverity.ERROR,
                    message="Element missing type",
                    element_id=getattr(element, 'id', None)
                ))
        
        return issues
    
    def _validate_bim_systems(self, bim_model: Union[BIMModel, EnhancedBIMModel]) -> List[ValidationIssue]:
        """Validate BIM systems"""
        issues = []
        
        systems = bim_model.get_all_systems() if hasattr(bim_model, 'get_all_systems') else getattr(bim_model, 'systems', [])
        
        for system in systems:
            # Check system ID
            if not system.id or not system.id.strip():
                issues.append(ValidationIssue(
                    issue_id="missing_system_id",
                    category=ValidationCategory.SYSTEM,
                    severity=ValidationSeverity.ERROR,
                    message="System missing ID"
                ))
            
            # Check system elements
            if not system.elements:
                issues.append(ValidationIssue(
                    issue_id="empty_system",
                    category=ValidationCategory.SYSTEM,
                    severity=ValidationSeverity.WARNING,
                    message="System has no elements",
                    element_id=getattr(system, 'id', None)
                ))
        
        return issues
    
    def _validate_bim_relationships(self, bim_model: Union[BIMModel, EnhancedBIMModel]) -> List[ValidationIssue]:
        """Validate BIM relationships"""
        issues = []
        
        relationships = bim_model.get_all_relationships() if hasattr(bim_model, 'get_all_relationships') else getattr(bim_model, 'relationships', [])
        
        for relationship in relationships:
            # Check relationship ID
            if not relationship.id or not relationship.id.strip():
                issues.append(ValidationIssue(
                    issue_id="missing_relationship_id",
                    category=ValidationCategory.RELATIONSHIP,
                    severity=ValidationSeverity.ERROR,
                    message="Relationship missing ID"
                ))
            
            # Check source and target
            if not relationship.source_id or not relationship.target_id:
                issues.append(ValidationIssue(
                    issue_id="invalid_relationship",
                    category=ValidationCategory.RELATIONSHIP,
                    severity=ValidationSeverity.ERROR,
                    message="Relationship missing source or target",
                    element_id=getattr(relationship, 'id', None)
                ))
        
        return issues
    
    def _validate_bim_geometry(self, bim_model: Union[BIMModel, EnhancedBIMModel]) -> List[ValidationIssue]:
        """Validate BIM geometry"""
        issues = []
        
        elements = bim_model.get_all_elements() if hasattr(bim_model, 'get_all_elements') else bim_model.elements
        
        for element in elements:
            if hasattr(element, 'geometry') and element.geometry:
                # Check geometry coordinates
                if not element.geometry.coordinates:
                    issues.append(ValidationIssue(
                        issue_id="missing_geometry_coordinates",
                        category=ValidationCategory.GEOMETRY,
                        severity=ValidationSeverity.ERROR,
                        message="Element geometry missing coordinates",
                        element_id=getattr(element, 'id', None)
                    ))
                
                # Check geometry type
                if not element.geometry.type:
                    issues.append(ValidationIssue(
                        issue_id="missing_geometry_type",
                        category=ValidationCategory.GEOMETRY,
                        severity=ValidationSeverity.ERROR,
                        message="Element geometry missing type",
                        element_id=getattr(element, 'id', None)
                    ))
        
        return issues
    
    # Coordinate Validation Methods
    def _validate_coordinate_system(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate coordinate system"""
        issues = []
        coordinates = data.get('coordinates', [])
        context = data.get('context', {})
        
        if not coordinates:
            issues.append(ValidationIssue(
                issue_id="missing_coordinates",
                category=ValidationCategory.GEOMETRY,
                severity=ValidationSeverity.ERROR,
                message="No coordinates provided"
            ))
        
        return issues
    
    def _validate_coordinate_precision(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate coordinate precision"""
        issues = []
        coordinates = data.get('coordinates', [])
        
        for i, coord in enumerate(coordinates):
            if isinstance(coord, (int, float)):
                # Check for reasonable precision (not too many decimal places)
                if abs(coord) > 1e6:
                    issues.append(ValidationIssue(
                        issue_id="coordinate_precision_issue",
                        category=ValidationCategory.GEOMETRY,
                        severity=ValidationSeverity.WARNING,
                        message=f"Coordinate {i} has very large value: {coord}",
                        actual_value=coord
                    ))
        
        return issues
    
    def _validate_coordinate_bounds(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate coordinate bounds"""
        issues = []
        coordinates = data.get('coordinates', [])
        
        # Check for reasonable bounds (assuming meters)
        for i, coord in enumerate(coordinates):
            if isinstance(coord, (int, float)):
                if abs(coord) > 10000:  # 10km limit
                    issues.append(ValidationIssue(
                        issue_id="coordinate_out_of_bounds",
                        category=ValidationCategory.GEOMETRY,
                        severity=ValidationSeverity.ERROR,
                        message=f"Coordinate {i} out of reasonable bounds: {coord}",
                        actual_value=coord,
                        expected_value="Within ±10000"
                    ))
        
        return issues
    
    # Symbol Validation Methods
    def _validate_symbol_schema(self, symbol_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate symbol schema"""
        issues = []
        
        required_fields = ['id', 'name', 'svg']
        for field in required_fields:
            if field not in symbol_data:
                issues.append(ValidationIssue(
                    issue_id=f"missing_symbol_{field}",
                    category=ValidationCategory.PROPERTY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Symbol missing required field: {field}",
                    property_name=field
                ))
        
        return issues
    
    def _validate_symbol_properties(self, symbol_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate symbol properties"""
        issues = []
        
        # Check for valid SVG content
        svg_content = symbol_data.get('svg', '')
        if not svg_content or not svg_content.strip():
            issues.append(ValidationIssue(
                issue_id="empty_svg_content",
                category=ValidationCategory.PROPERTY,
                severity=ValidationSeverity.ERROR,
                message="Symbol has empty SVG content",
                property_name="svg"
            ))
        
        return issues
    
    def _validate_symbol_geometry(self, symbol_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate symbol geometry"""
        issues = []
        
        # Check for valid SVG structure
        svg_content = symbol_data.get('svg', '')
        if svg_content and not svg_content.startswith('<svg'):
            issues.append(ValidationIssue(
                issue_id="invalid_svg_structure",
                category=ValidationCategory.GEOMETRY,
                severity=ValidationSeverity.ERROR,
                message="Symbol SVG content is not valid SVG",
                property_name="svg"
            ))
        
        return issues
    
    # Building Code Validation Methods
    def _validate_building_codes(self, building_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate building codes"""
        issues = []
        
        # Check for required building information
        required_fields = ['building_type', 'floor_count', 'total_area']
        for field in required_fields:
            if field not in building_data:
                issues.append(ValidationIssue(
                    issue_id=f"missing_building_{field}",
                    category=ValidationCategory.COMPLIANCE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Building missing field: {field}",
                    property_name=field
                ))
        
        return issues
    
    def _validate_safety_requirements(self, building_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate safety requirements"""
        issues = []
        
        # Check for fire safety systems
        if building_data.get('building_type') in ['office', 'residential', 'industrial']:
            if not building_data.get('fire_safety_systems'):
                issues.append(ValidationIssue(
                    issue_id="missing_fire_safety",
                    category=ValidationCategory.COMPLIANCE,
                    severity=ValidationSeverity.ERROR,
                    message="Building missing fire safety systems",
                    suggestions=["Install smoke detectors", "Add sprinkler system", "Include fire alarms"]
                ))
        
        return issues
    
    def _validate_accessibility_requirements(self, building_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate accessibility requirements"""
        issues = []
        
        # Check for accessibility features
        if building_data.get('building_type') in ['office', 'public']:
            if not building_data.get('accessibility_features'):
                issues.append(ValidationIssue(
                    issue_id="missing_accessibility",
                    category=ValidationCategory.COMPLIANCE,
                    severity=ValidationSeverity.WARNING,
                    message="Building missing accessibility features",
                    suggestions=["Add wheelchair ramps", "Install elevators", "Include accessible restrooms"]
                ))
        
        return issues
    
    # Legacy compatibility methods
    def add_field_validator(self, field: str, func: Callable[[Any], Optional[str]]):
        """Add field validator (legacy compatibility)"""
        self.field_validators.setdefault(field, []).append(func)
    
    def add_model_validator(self, func: Callable[[BaseModel], Optional[str]]):
        """Add model validator (legacy compatibility)"""
        self.model_validators.append(func)
    
    def add_warning_validator(self, func: Callable[[BaseModel], Optional[str]]):
        """Add warning validator (legacy compatibility)"""
        self.warning_validators.append(func)
    
    def validate(self, model: BaseModel) -> ValidationResult:
        """Legacy validation method for Pydantic models"""
        result = ValidationResult(
            valid=True,
            level=self.validation_level,
            total_issues=0,
            errors=0,
            warnings=0,
            info=0
        )
        
        # Field-level validation
        for field, validators in self.field_validators.items():
            value = getattr(model, field, None)
            for validator in validators:
                error = validator(value)
                if error:
                    result.add_issue(ValidationIssue(
                        issue_id=f"field_validation_{field}",
                        category=ValidationCategory.PROPERTY,
                        severity=ValidationSeverity.ERROR,
                        message=f"{field}: {error}",
                        property_name=field
                    ))
        
        # Model-level validation
        for validator in self.model_validators:
            error = validator(model)
            if error:
                result.add_issue(ValidationIssue(
                    issue_id="model_validation",
                    category=ValidationCategory.PROPERTY,
                    severity=ValidationSeverity.ERROR,
                    message=error
                ))
        
        # Warning-level validation
        for validator in self.warning_validators:
            warning = validator(model)
            if warning:
                result.add_issue(ValidationIssue(
                    issue_id="model_warning",
                    category=ValidationCategory.PROPERTY,
                    severity=ValidationSeverity.WARNING,
                    message=warning
                ))
        
        return result 