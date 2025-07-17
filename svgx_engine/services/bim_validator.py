"""
SVGX Engine - BIM Validator Service

This module provides validation functionality for BIM models and elements.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime

from structlog import get_logger

from svgx_engine.models.bim import BIMModel, BIMElement, BIMSystem, BIMRelationship

try:
    from svgx_engine.utils.errors import ValidationError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import ValidationError

logger = get_logger()


class ValidationLevel(Enum):
    """Validation levels for BIM models."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    COMPREHENSIVE = "comprehensive"


class ValidationResult:
    """Result of a BIM validation operation."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.timestamp = datetime.now()
    
    def add_error(self, error: str):
        """Add an error to the validation result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning to the validation result."""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat(),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


class SVGXBIMValidatorService:
    """Validator for BIM models and elements."""
    
    def __init__(self):
        """Initialize the BIM validator."""
        self.validation_rules = {
            ValidationLevel.BASIC: self._basic_validation,
            ValidationLevel.STANDARD: self._standard_validation,
            ValidationLevel.STRICT: self._strict_validation,
            ValidationLevel.COMPREHENSIVE: self._comprehensive_validation
        }
    
    def validate_model(self, model: BIMModel, level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult:
        """
        Validate a BIM model according to the specified level.
        
        Args:
            model: The BIM model to validate
            level: The validation level to apply
            
        Returns:
            ValidationResult with validation results
        """
        result = ValidationResult(True)
        
        try:
            # Get validation function for the specified level
            validation_func = self.validation_rules.get(level, self._standard_validation)
            validation_func(model, result)
            
            logger.info(
                "BIM model validation completed",
                model_id=model.id,
                level=level.value,
                is_valid=result.is_valid,
                error_count=len(result.errors),
                warning_count=len(result.warnings)
            )
            
        except Exception as e:
            result.add_error(f"Validation failed with exception: {str(e)}")
            logger.error("BIM validation failed", model_id=model.id, error=str(e))
        
        return result
    
    def validate_element(self, element: BIMElement, level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult:
        """
        Validate a BIM element according to the specified level.
        
        Args:
            element: The BIM element to validate
            level: The validation level to apply
            
        Returns:
            ValidationResult with validation results
        """
        result = ValidationResult(True)
        
        try:
            # Basic element validation
            if not element.id:
                result.add_error("Element ID is required")
            
            if not element.name:
                result.add_error("Element name is required")
            
            # Geometry validation
            if element.geometry:
                self._validate_geometry(element.geometry, result)
            
            # Level-specific validation
            if level in [ValidationLevel.STRICT, ValidationLevel.COMPREHENSIVE]:
                self._validate_element_properties(element, result)
            
            logger.info(
                "BIM element validation completed",
                element_id=element.id,
                level=level.value,
                is_valid=result.is_valid,
                error_count=len(result.errors)
            )
            
        except Exception as e:
            result.add_error(f"Element validation failed with exception: {str(e)}")
            logger.error("BIM element validation failed", element_id=element.id, error=str(e))
        
        return result
    
    def _basic_validation(self, model: BIMModel, result: ValidationResult):
        """Perform basic validation on a BIM model."""
        # Check model structure
        if not model.id:
            result.add_error("Model ID is required")
        
        if not model.name:
            result.add_error("Model name is required")
        
        # Check for duplicate element IDs
        element_ids = [e.id for e in model.elements]
        if len(element_ids) != len(set(element_ids)):
            result.add_error("Duplicate element IDs found")
        
        # Check for duplicate system IDs
        system_ids = [s.id for s in model.systems]
        if len(system_ids) != len(set(system_ids)):
            result.add_error("Duplicate system IDs found")
    
    def _standard_validation(self, model: BIMModel, result: ValidationResult):
        """Perform standard validation on a BIM model."""
        # Run basic validation first
        self._basic_validation(model, result)
        
        # Validate all elements
        for element in model.elements:
            element_result = self.validate_element(element, ValidationLevel.BASIC)
            result.errors.extend(element_result.errors)
            result.warnings.extend(element_result.warnings)
        
        # Validate relationships
        for relationship in model.relationships:
            self._validate_relationship(relationship, model, result)
    
    def _strict_validation(self, model: BIMModel, result: ValidationResult):
        """Perform strict validation on a BIM model."""
        # Run standard validation first
        self._standard_validation(model, result)
        
        # Additional strict checks
        if not model.elements:
            result.add_warning("Model has no elements")
        
        # Check for orphaned relationships
        element_ids = {e.id for e in model.elements}
        for relationship in model.relationships:
            if relationship.source_element_id not in element_ids:
                result.add_error(f"Relationship references non-existent source element: {relationship.source_element_id}")
            if relationship.target_element_id not in element_ids:
                result.add_error(f"Relationship references non-existent target element: {relationship.target_element_id}")
    
    def _comprehensive_validation(self, model: BIMModel, result: ValidationResult):
        """Perform comprehensive validation on a BIM model."""
        # Run strict validation first
        self._strict_validation(model, result)
        
        # Additional comprehensive checks
        # Check for system consistency
        for system in model.systems:
            self._validate_system(system, model, result)
        
        # Check for spatial consistency
        self._validate_spatial_consistency(model, result)
        
        # Check for metadata completeness
        self._validate_metadata_completeness(model, result)
    
    def _validate_geometry(self, geometry, result: ValidationResult):
        """Validate geometry data."""
        if not hasattr(geometry, 'geometry_type'):
            result.add_error("Geometry must have a geometry_type")
            return
        
        if not hasattr(geometry, 'coordinates'):
            result.add_error("Geometry must have coordinates")
            return
        
        # Validate coordinates based on geometry type
        if geometry.geometry_type.value == 'point':
            if not isinstance(geometry.coordinates, (list, tuple)) or len(geometry.coordinates) < 2:
                result.add_error("Point geometry must have at least 2 coordinates")
        
        elif geometry.geometry_type.value == 'linestring':
            if not isinstance(geometry.coordinates, (list, tuple)) or len(geometry.coordinates) < 2:
                result.add_error("LineString geometry must have at least 2 points")
        
        elif geometry.geometry_type.value == 'polygon':
            if not isinstance(geometry.coordinates, (list, tuple)) or len(geometry.coordinates) < 3:
                result.add_error("Polygon geometry must have at least 3 points")
    
    def _validate_element_properties(self, element: BIMElement, result: ValidationResult):
        """Validate element properties."""
        # Check for required properties based on element type
        if hasattr(element, 'room_type') and element.room_type:
            if not hasattr(element, 'area') or element.area is None:
                result.add_warning(f"Room element {element.id} should have an area")
        
        if hasattr(element, 'wall_type') and element.wall_type:
            if not hasattr(element, 'thickness') or element.thickness is None:
                result.add_warning(f"Wall element {element.id} should have a thickness")
    
    def _validate_relationship(self, relationship: BIMRelationship, model: BIMModel, result: ValidationResult):
        """Validate a BIM relationship."""
        if not relationship.id:
            result.add_error("Relationship ID is required")
        
        if not relationship.source_element_id:
            result.add_error("Relationship source element ID is required")
        
        if not relationship.target_element_id:
            result.add_error("Relationship target element ID is required")
        
        if not relationship.relationship_type:
            result.add_error("Relationship type is required")
        
        # Check that referenced elements exist
        source_element = model.get_element_by_id(relationship.source_element_id)
        if not source_element:
            result.add_error(f"Relationship references non-existent source element: {relationship.source_element_id}")
        
        target_element = model.get_element_by_id(relationship.target_element_id)
        if not target_element:
            result.add_error(f"Relationship references non-existent target element: {relationship.target_element_id}")
    
    def _validate_system(self, system: BIMSystem, model: BIMModel, result: ValidationResult):
        """Validate a BIM system."""
        if not system.id:
            result.add_error("System ID is required")
        
        if not system.name:
            result.add_error("System name is required")
        
        # Check that system elements exist
        for element_id in [e.id for e in system.elements]:
            if not model.get_element_by_id(element_id):
                result.add_error(f"System references non-existent element: {element_id}")
    
    def _validate_spatial_consistency(self, model: BIMModel, result: ValidationResult):
        """Validate spatial consistency of the model."""
        # This would implement spatial validation logic
        # For now, just add a placeholder
        pass
    
    def _validate_metadata_completeness(self, model: BIMModel, result: ValidationResult):
        """Validate metadata completeness."""
        # Check for required metadata
        if not model.metadata.get('version'):
            result.add_warning("Model should have a version in metadata")
        
        if not model.metadata.get('created_by'):
            result.add_warning("Model should have creator information in metadata")
    
    def get_validation_summary(self, model: BIMModel) -> Dict[str, Any]:
        """Get a validation summary for a model."""
        basic_result = self.validate_model(model, ValidationLevel.BASIC)
        standard_result = self.validate_model(model, ValidationLevel.STANDARD)
        strict_result = self.validate_model(model, ValidationLevel.STRICT)
        comprehensive_result = self.validate_model(model, ValidationLevel.COMPREHENSIVE)
        
        return {
            'model_id': model.id,
            'model_name': model.name,
            'element_count': len(model.elements),
            'system_count': len(model.systems),
            'relationship_count': len(model.relationships),
            'validation_levels': {
                'basic': basic_result.to_dict(),
                'standard': standard_result.to_dict(),
                'strict': strict_result.to_dict(),
                'comprehensive': comprehensive_result.to_dict()
            }
        }


# Convenience function for creating validator
def create_bim_validator_service() -> SVGXBIMValidatorService:
    """Create and return a configured BIM validator."""
    return SVGXBIMValidatorService() 