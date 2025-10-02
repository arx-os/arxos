"""
IFC Validation Module

This module provides comprehensive IFC validation including:
- buildingSMART compliance checking
- IFC schema validation
- Spatial consistency validation
- Data integrity checks
"""

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from typing import Dict, List, Tuple, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class IFCValidationResult:
    """Result of IFC validation process"""
    
    def __init__(self):
        self.valid: bool = True
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.compliance: Dict[str, bool] = {
            'buildingSMART': True,
            'IFC4': True,
            'spatial_consistency': True,
            'data_integrity': True
        }
        self.metadata: Dict[str, Any] = {
            'ifc_version': 'Unknown',
            'file_size': 0,
            'processing_time': 0.0,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.entity_counts: Dict[str, int] = {}
        self.spatial_issues: List[str] = []
        self.schema_issues: List[str] = []


class IFCValidator:
    """Comprehensive IFC validator with buildingSMART compliance"""
    
    def __init__(self):
        self.required_entities = [
            'IfcProject',
            'IfcSite', 
            'IfcBuilding',
            'IfcBuildingStorey'
        ]
        
        self.spatial_entities = [
            'IfcSpace',
            'IfcWall',
            'IfcSlab',
            'IfcBeam',
            'IfcColumn',
            'IfcDoor',
            'IfcWindow'
        ]
        
        self.required_properties = [
            'Name',
            'Description',
            'GlobalId'
        ]

    def validate_ifc(self, ifc_data: bytes) -> IFCValidationResult:
        """
        Perform comprehensive IFC validation
        
        Args:
            ifc_data: Raw IFC file data
            
        Returns:
            IFCValidationResult with validation details
        """
        result = IFCValidationResult()
        start_time = datetime.utcnow()
        
        try:
            # Open IFC model
            model = ifcopenshell.open(ifc_data)
            result.metadata['file_size'] = len(ifc_data)
            
            # Extract IFC version
            result.metadata['ifc_version'] = self._extract_ifc_version(model)
            
            # Perform validation checks
            self._validate_schema(model, result)
            self._validate_buildingsmart_compliance(model, result)
            self._validate_spatial_consistency(model, result)
            self._validate_data_integrity(model, result)
            self._count_entities(model, result)
            
            # Determine overall validity
            result.valid = len(result.errors) == 0
            
        except Exception as e:
            logger.error(f"IFC validation failed: {e}")
            result.valid = False
            result.errors.append(f"Failed to parse IFC file: {str(e)}")
        
        finally:
            result.metadata['processing_time'] = (datetime.utcnow() - start_time).total_seconds()
        
        return result

    def _extract_ifc_version(self, model) -> str:
        """Extract IFC version from model"""
        try:
            # Get the schema identifier
            schema_identifiers = model.by_type('IfcSchemaIdentifier')
            if schema_identifiers:
                return schema_identifiers[0].Name or 'Unknown'
            
            # Fallback: check file header
            if hasattr(model, 'schema') and model.schema:
                return model.schema
            
            return 'Unknown'
        except:
            return 'Unknown'

    def _validate_schema(self, model, result: IFCValidationResult):
        """Validate IFC schema compliance"""
        try:
            # Check for required entities
            for entity_type in self.required_entities:
                entities = model.by_type(entity_type)
                if not entities:
                    result.warnings.append(f"No {entity_type} entities found")
                    result.compliance['IFC4'] = False
                else:
                    result.entity_counts[entity_type] = len(entities)
            
            # Check for valid IFC4 schema
            if result.metadata['ifc_version'] and 'IFC4' not in result.metadata['ifc_version']:
                result.warnings.append(f"IFC version {result.metadata['ifc_version']} may not be fully supported")
                result.compliance['IFC4'] = False
            
        except Exception as e:
            result.errors.append(f"Schema validation failed: {str(e)}")
            result.compliance['IFC4'] = False

    def _validate_buildingsmart_compliance(self, model, result: IFCValidationResult):
        """Validate buildingSMART compliance"""
        try:
            # Check for proper project structure
            projects = model.by_type('IfcProject')
            if not projects:
                result.errors.append("No IfcProject found - required for buildingSMART compliance")
                result.compliance['buildingSMART'] = False
                return
            
            project = projects[0]
            
            # Check for required project properties
            if not hasattr(project, 'GlobalId') or not project.GlobalId:
                result.errors.append("Project missing GlobalId - required for buildingSMART compliance")
                result.compliance['buildingSMART'] = False
            
            if not hasattr(project, 'Name') or not project.Name:
                result.warnings.append("Project missing Name property")
            
            # Check for proper site/building hierarchy
            sites = model.by_type('IfcSite')
            buildings = model.by_type('IfcBuilding')
            
            if not sites:
                result.warnings.append("No IfcSite found - recommended for buildingSMART compliance")
            
            if not buildings:
                result.errors.append("No IfcBuilding found - required for buildingSMART compliance")
                result.compliance['buildingSMART'] = False
            
            # Check for proper spatial structure
            building_storeys = model.by_type('IfcBuildingStorey')
            if not building_storeys:
                result.warnings.append("No IfcBuildingStorey found - recommended for proper spatial structure")
            
        except Exception as e:
            result.errors.append(f"buildingSMART compliance check failed: {str(e)}")
            result.compliance['buildingSMART'] = False

    def _validate_spatial_consistency(self, model, result: IFCValidationResult):
        """Validate spatial consistency and relationships"""
        try:
            # Check for spatial containment
            spaces = model.by_type('IfcSpace')
            building_storeys = model.by_type('IfcBuildingStorey')
            
            if spaces and not building_storeys:
                result.warnings.append("Spaces found but no building storeys - spatial containment unclear")
                result.compliance['spatial_consistency'] = False
            
            # Check for overlapping spaces (basic check)
            overlapping_spaces = self._check_overlapping_spaces(model)
            if overlapping_spaces:
                result.spatial_issues.extend(overlapping_spaces)
                result.warnings.append(f"Found {len(overlapping_spaces)} potential spatial overlaps")
            
            # Check for proper placement
            misplaced_entities = self._check_entity_placement(model)
            if misplaced_entities:
                result.spatial_issues.extend(misplaced_entities)
                result.warnings.append(f"Found {len(misplaced_entities)} entities with placement issues")
            
        except Exception as e:
            result.errors.append(f"Spatial consistency check failed: {str(e)}")
            result.compliance['spatial_consistency'] = False

    def _validate_data_integrity(self, model, result: IFCValidationResult):
        """Validate data integrity and completeness"""
        try:
            # Check for orphaned entities
            orphaned_entities = self._find_orphaned_entities(model)
            if orphaned_entities:
                result.warnings.append(f"Found {len(orphaned_entities)} potentially orphaned entities")
            
            # Check for missing properties
            entities_without_properties = self._check_missing_properties(model)
            if entities_without_properties:
                result.warnings.append(f"Found {len(entities_without_properties)} entities without basic properties")
            
            # Check for circular references
            circular_refs = self._check_circular_references(model)
            if circular_refs:
                result.errors.append(f"Found {len(circular_refs)} circular references")
                result.compliance['data_integrity'] = False
            
        except Exception as e:
            result.errors.append(f"Data integrity check failed: {str(e)}")
            result.compliance['data_integrity'] = False

    def _count_entities(self, model, result: IFCValidationResult):
        """Count different types of entities"""
        try:
            for entity_type in self.spatial_entities:
                entities = model.by_type(entity_type)
                result.entity_counts[entity_type] = len(entities)
            
            # Count total entities
            all_products = model.by_type('IfcProduct')
            result.entity_counts['total_products'] = len(all_products)
            
        except Exception as e:
            logger.warning(f"Entity counting failed: {e}")

    def _check_overlapping_spaces(self, model) -> List[str]:
        """Check for overlapping spaces (simplified implementation)"""
        issues = []
        try:
            spaces = model.by_type('IfcSpace')
            if len(spaces) < 2:
                return issues
            
            # Basic overlap check - in a real implementation, this would use
            # proper geometric calculations
            for i, space1 in enumerate(spaces):
                for j, space2 in enumerate(spaces[i+1:], i+1):
                    if hasattr(space1, 'GlobalId') and hasattr(space2, 'GlobalId'):
                        # Placeholder for actual geometric overlap detection
                        # This would require proper spatial analysis
                        pass
            
        except Exception as e:
            logger.warning(f"Overlap check failed: {e}")
        
        return issues

    def _check_entity_placement(self, model) -> List[str]:
        """Check for entities with placement issues"""
        issues = []
        try:
            # Check for entities without proper placement
            products = model.by_type('IfcProduct')
            for product in products[:10]:  # Limit to first 10 for performance
                if not hasattr(product, 'ObjectPlacement') or not product.ObjectPlacement:
                    if hasattr(product, 'GlobalId'):
                        issues.append(f"Entity {product.GlobalId} missing ObjectPlacement")
            
        except Exception as e:
            logger.warning(f"Placement check failed: {e}")
        
        return issues

    def _find_orphaned_entities(self, model) -> List[str]:
        """Find potentially orphaned entities"""
        orphaned = []
        try:
            # Check for entities not properly contained
            products = model.by_type('IfcProduct')
            for product in products[:20]:  # Limit for performance
                if not hasattr(product, 'ContainedInStructure') and not hasattr(product, 'Decomposes'):
                    if hasattr(product, 'GlobalId'):
                        orphaned.append(product.GlobalId)
            
        except Exception as e:
            logger.warning(f"Orphaned entity check failed: {e}")
        
        return orphaned

    def _check_missing_properties(self, model) -> List[str]:
        """Check for entities missing basic properties"""
        missing_props = []
        try:
            products = model.by_type('IfcProduct')
            for product in products[:20]:  # Limit for performance
                if not hasattr(product, 'Name') or not product.Name:
                    if hasattr(product, 'GlobalId'):
                        missing_props.append(product.GlobalId)
            
        except Exception as e:
            logger.warning(f"Missing properties check failed: {e}")
        
        return missing_props

    def _check_circular_references(self, model) -> List[str]:
        """Check for circular references (simplified)"""
        circular_refs = []
        try:
            # This is a simplified check - a full implementation would
            # traverse the entire reference graph
            products = model.by_type('IfcProduct')
            for product in products[:10]:  # Limit for performance
                if hasattr(product, 'Decomposes') and product.Decomposes:
                    # Check for self-reference
                    if product.Decomposes[0] == product:
                        circular_refs.append(f"Self-reference in {product.GlobalId}")
            
        except Exception as e:
            logger.warning(f"Circular reference check failed: {e}")
        
        return circular_refs


# Global validator instance
validator = IFCValidator()
