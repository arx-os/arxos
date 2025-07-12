"""
BIM Object Integration Service
Handles BIM object creation with real-world coordinate systems, scaling, and validation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import math

from services.coordinate_validator import CoordinateValidator
from utils.unified_logger import logger

class CoordinateSystem(Enum):
    """Supported coordinate systems"""
    SVG = "svg"
    REAL_WORLD_METERS = "real_world_meters"
    REAL_WORLD_FEET = "real_world_feet"
    BIM = "bim"

class Units(Enum):
    """Supported units"""
    PIXELS = "pixels"
    METERS = "meters"
    FEET = "feet"
    INCHES = "inches"
    MILLIMETERS = "millimeters"

@dataclass
class BIMObjectGeometry:
    """BIM object geometry with coordinate system support"""
    coordinates: List[List[float]]
    coordinate_system: CoordinateSystem
    units: Units
    scale_factors: Optional[Dict[str, float]] = None
    transformation_matrix: Optional[List[List[float]]] = None

@dataclass
class BIMObjectMetadata:
    """BIM object metadata"""
    object_id: str
    object_type: str
    name: str
    system: str
    category: str
    properties: Dict[str, Any]
    relationships: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: str
    version: str = "1.0"

class BIMObjectIntegrationService:
    """
    Service for creating and managing BIM objects with real-world coordinate support
    """
    
    def __init__(self):
        self.coordinate_validator = CoordinateValidator()
        self.logger = logger
        
    def create_bim_object_with_real_world_coordinates(
        self,
        object_data: Dict[str, Any],
        coordinate_system: CoordinateSystem = CoordinateSystem.REAL_WORLD_METERS,
        units: Units = Units.METERS,
        scale_factors: Optional[Dict[str, float]] = None,
        validate_coordinates: bool = True
    ) -> Dict[str, Any]:
        """
        Create a BIM object with real-world coordinate validation
        
        Args:
            object_data: BIM object data including geometry and metadata
            coordinate_system: Target coordinate system
            units: Units for the coordinate system
            scale_factors: Scale factors for coordinate transformation
            validate_coordinates: Whether to validate coordinates
            
        Returns:
            Created BIM object with validated coordinates
        """
        try:
            # Extract geometry data
            geometry_data = object_data.get('geometry', {})
            coordinates = geometry_data.get('coordinates', [])
            
            # Validate coordinate system
            if not self._is_valid_coordinate_system(coordinate_system.value):
                raise ValueError(f"Invalid coordinate system: {coordinate_system.value}")
            
            # Validate units
            if not self._is_valid_unit(units.value):
                raise ValueError(f"Invalid unit: {units.value}")
            
            # Validate coordinates if requested
            if validate_coordinates:
                validation_result = self.coordinate_validator.validate_coordinates(
                    coordinates, coordinate_system.value
                )
                if not validation_result['valid']:
                    raise ValueError(f"Coordinate validation failed: {validation_result['errors']}")
                
                if validation_result['warnings']:
                    self.logger.warning(f"Coordinate warnings: {validation_result['warnings']}")
            
            # Apply scale factors if provided
            if scale_factors:
                coordinates = self._apply_scale_factors(coordinates, scale_factors)
            
            # Create BIM object geometry
            bim_geometry = BIMObjectGeometry(
                coordinates=coordinates,
                coordinate_system=coordinate_system,
                units=units,
                scale_factors=scale_factors
            )
            
            # Create BIM object metadata
            bim_metadata = BIMObjectMetadata(
                object_id=object_data.get('id'),
                object_type=object_data.get('type'),
                name=object_data.get('name'),
                system=object_data.get('system'),
                category=object_data.get('category'),
                properties=object_data.get('properties', {}),
                relationships=object_data.get('relationships', []),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=object_data.get('created_by', 'system')
            )
            
            # Build BIM object
            bim_object = {
                'id': bim_metadata.object_id,
                'type': bim_metadata.object_type,
                'name': bim_metadata.name,
                'system': bim_metadata.system,
                'category': bim_metadata.category,
                'geometry': {
                    'coordinates': bim_geometry.coordinates,
                    'coordinate_system': bim_geometry.coordinate_system.value,
                    'units': bim_geometry.units.value,
                    'scale_factors': bim_geometry.scale_factors,
                    'transformation_matrix': bim_geometry.transformation_matrix
                },
                'properties': bim_metadata.properties,
                'relationships': bim_metadata.relationships,
                'metadata': {
                    'created_at': bim_metadata.created_at.isoformat(),
                    'updated_at': bim_metadata.updated_at.isoformat(),
                    'created_by': bim_metadata.created_by,
                    'version': bim_metadata.version,
                    'coordinate_system': coordinate_system.value,
                    'units': units.value
                }
            }
            
            self.logger.info(f"Created BIM object {bim_metadata.object_id} with {coordinate_system.value} coordinates")
            return bim_object
            
        except Exception as e:
            self.logger.error(f"Failed to create BIM object: {e}")
            raise
    
    def test_bim_object_scaling_with_real_world_units(
        self,
        test_objects: List[Dict[str, Any]],
        scale_factors: Dict[str, float],
        target_units: Units
    ) -> Dict[str, Any]:
        """
        Test BIM object scaling with real-world units
        
        Args:
            test_objects: List of BIM objects to test
            scale_factors: Scale factors to apply
            target_units: Target units for scaling
            
        Returns:
            Test results with scaling validation
        """
        test_results = {
            'total_objects': len(test_objects),
            'successful_scaling': 0,
            'failed_scaling': 0,
            'scaling_errors': [],
            'validation_results': [],
            'performance_metrics': {}
        }
        
        start_time = datetime.utcnow()
        
        for i, obj in enumerate(test_objects):
            try:
                # Test scaling with different coordinate systems
                for coord_system in [CoordinateSystem.SVG, CoordinateSystem.REAL_WORLD_METERS, CoordinateSystem.BIM]:
                    scaled_object = self._test_object_scaling(obj, coord_system, scale_factors, target_units)
                    
                    if scaled_object:
                        test_results['successful_scaling'] += 1
                        test_results['validation_results'].append({
                            'object_id': obj.get('id'),
                            'coordinate_system': coord_system.value,
                            'scaling_successful': True,
                            'scaled_coordinates': scaled_object['geometry']['coordinates'][:2]  # First 2 points
                        })
                    else:
                        test_results['failed_scaling'] += 1
                        test_results['scaling_errors'].append({
                            'object_id': obj.get('id'),
                            'coordinate_system': coord_system.value,
                            'error': 'Scaling failed'
                        })
                        
            except Exception as e:
                test_results['failed_scaling'] += 1
                test_results['scaling_errors'].append({
                    'object_id': obj.get('id'),
                    'error': str(e)
                })
        
        end_time = datetime.utcnow()
        test_results['performance_metrics'] = {
            'total_time_ms': (end_time - start_time).total_seconds() * 1000,
            'average_time_per_object_ms': (end_time - start_time).total_seconds() * 1000 / len(test_objects) if test_objects else 0
        }
        
        self.logger.info(f"BIM object scaling test completed: {test_results['successful_scaling']}/{test_results['total_objects']} successful")
        return test_results
    
    def validate_bim_object_relationships_at_different_scales(
        self,
        bim_objects: List[Dict[str, Any]],
        scale_factors: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Validate BIM object relationships at different scales
        
        Args:
            bim_objects: List of BIM objects to validate
            scale_factors: List of scale factors to test
            
        Returns:
            Validation results for relationships at different scales
        """
        validation_results = {
            'total_objects': len(bim_objects),
            'total_relationships': 0,
            'scale_tests': [],
            'relationship_validation': {},
            'spatial_consistency': {}
        }
        
        # Count total relationships
        for obj in bim_objects:
            relationships = obj.get('relationships', [])
            validation_results['total_relationships'] += len(relationships)
        
        # Test relationships at different scales
        for scale_factor in scale_factors:
            scale_test = {
                'scale_factors': scale_factor,
                'objects_tested': 0,
                'relationships_valid': 0,
                'relationships_invalid': 0,
                'spatial_issues': [],
                'validation_errors': []
            }
            
            for obj in bim_objects:
                try:
                    # Apply scale factors to object coordinates
                    scaled_coordinates = self._apply_scale_factors(
                        obj['geometry']['coordinates'], scale_factor
                    )
                    
                    # Validate relationships with scaled coordinates
                    relationship_validation = self._validate_object_relationships(
                        obj, scaled_coordinates, bim_objects
                    )
                    
                    scale_test['objects_tested'] += 1
                    scale_test['relationships_valid'] += relationship_validation['valid_count']
                    scale_test['relationships_invalid'] += relationship_validation['invalid_count']
                    
                    if relationship_validation['spatial_issues']:
                        scale_test['spatial_issues'].extend(relationship_validation['spatial_issues'])
                    
                    if relationship_validation['errors']:
                        scale_test['validation_errors'].extend(relationship_validation['errors'])
                        
                except Exception as e:
                    scale_test['validation_errors'].append({
                        'object_id': obj.get('id'),
                        'error': str(e)
                    })
            
            validation_results['scale_tests'].append(scale_test)
        
        # Calculate overall spatial consistency
        validation_results['spatial_consistency'] = self._calculate_spatial_consistency(bim_objects)
        
        self.logger.info(f"BIM object relationship validation completed for {len(scale_factors)} scale factors")
        return validation_results
    
    def test_bim_export_with_proper_scaling(
        self,
        bim_objects: List[Dict[str, Any]],
        export_format: str = "ifc",
        coordinate_system: CoordinateSystem = CoordinateSystem.REAL_WORLD_METERS,
        units: Units = Units.METERS
    ) -> Dict[str, Any]:
        """
        Test BIM export with proper scaling
        
        Args:
            bim_objects: List of BIM objects to export
            export_format: Export format (ifc, json, xml)
            coordinate_system: Target coordinate system for export
            units: Units for the export
            
        Returns:
            Export test results
        """
        export_results = {
            'total_objects': len(bim_objects),
            'export_format': export_format,
            'coordinate_system': coordinate_system.value,
            'units': units.value,
            'export_successful': False,
            'export_data': None,
            'validation_results': {},
            'performance_metrics': {},
            'errors': []
        }
        
        try:
            start_time = datetime.utcnow()
            
            # Prepare objects for export
            export_objects = []
            for obj in bim_objects:
                # Convert coordinates to target coordinate system
                converted_coordinates = self._convert_coordinates_for_export(
                    obj, coordinate_system, units
                )
                
                export_obj = {
                    'id': obj['id'],
                    'type': obj['type'],
                    'name': obj['name'],
                    'geometry': {
                        'coordinates': converted_coordinates,
                        'coordinate_system': coordinate_system.value,
                        'units': units.value
                    },
                    'properties': obj.get('properties', {}),
                    'relationships': obj.get('relationships', [])
                }
                export_objects.append(export_obj)
            
            # Generate export data
            if export_format.lower() == "ifc":
                export_data = self._generate_ifc_export(export_objects)
            elif export_format.lower() == "json":
                export_data = self._generate_json_export(export_objects)
            elif export_format.lower() == "xml":
                export_data = self._generate_xml_export(export_objects)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Validate export data
            validation_result = self._validate_export_data(export_data, export_format)
            
            end_time = datetime.utcnow()
            
            export_results.update({
                'export_successful': True,
                'export_data': export_data,
                'validation_results': validation_result,
                'performance_metrics': {
                    'export_time_ms': (end_time - start_time).total_seconds() * 1000,
                    'data_size_bytes': len(str(export_data)),
                    'objects_per_second': len(bim_objects) / (end_time - start_time).total_seconds()
                }
            })
            
            self.logger.info(f"BIM export test completed successfully: {export_format} format")
            
        except Exception as e:
            export_results['errors'].append(str(e))
            self.logger.error(f"BIM export test failed: {e}")
        
        return export_results
    
    def _is_valid_coordinate_system(self, system: str) -> bool:
        """Check if coordinate system is valid"""
        return system in [cs.value for cs in CoordinateSystem]
    
    def _is_valid_unit(self, unit: str) -> bool:
        """Check if unit is valid"""
        return unit in [u.value for u in Units]
    
    def _apply_scale_factors(self, coordinates: List[List[float]], scale_factors: Dict[str, float]) -> List[List[float]]:
        """Apply scale factors to coordinates"""
        scale_x = scale_factors.get('x', 1.0)
        scale_y = scale_factors.get('y', 1.0)
        
        scaled_coordinates = []
        for coord in coordinates:
            scaled_coordinates.append([coord[0] * scale_x, coord[1] * scale_y])
        
        return scaled_coordinates
    
    def _test_object_scaling(self, obj: Dict[str, Any], coord_system: CoordinateSystem, 
                           scale_factors: Dict[str, float], target_units: Units) -> Optional[Dict[str, Any]]:
        """Test scaling for a single object"""
        try:
            coordinates = obj.get('geometry', {}).get('coordinates', [])
            scaled_coordinates = self._apply_scale_factors(coordinates, scale_factors)
            
            # Validate scaled coordinates
            validation_result = self.coordinate_validator.validate_coordinates(
                scaled_coordinates, coord_system.value
            )
            
            if validation_result['valid']:
                return {
                    'id': obj['id'],
                    'geometry': {
                        'coordinates': scaled_coordinates,
                        'coordinate_system': coord_system.value,
                        'units': target_units.value
                    }
                }
            return None
            
        except Exception:
            return None
    
    def _validate_object_relationships(self, obj: Dict[str, Any], coordinates: List[List[float]], 
                                     all_objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate relationships for a single object"""
        validation_result = {
            'valid_count': 0,
            'invalid_count': 0,
            'spatial_issues': [],
            'errors': []
        }
        
        relationships = obj.get('relationships', [])
        
        for relationship in relationships:
            try:
                # Find related object
                related_obj = next((o for o in all_objects if o['id'] == relationship), None)
                
                if related_obj:
                    # Check spatial consistency
                    related_coords = related_obj.get('geometry', {}).get('coordinates', [])
                    
                    if self._check_spatial_consistency(coordinates, related_coords):
                        validation_result['valid_count'] += 1
                    else:
                        validation_result['invalid_count'] += 1
                        validation_result['spatial_issues'].append({
                            'object_id': obj['id'],
                            'related_id': relationship,
                            'issue': 'Spatial inconsistency detected'
                        })
                else:
                    validation_result['invalid_count'] += 1
                    validation_result['errors'].append({
                        'object_id': obj['id'],
                        'related_id': relationship,
                        'error': 'Related object not found'
                    })
                    
            except Exception as e:
                validation_result['invalid_count'] += 1
                validation_result['errors'].append({
                    'object_id': obj['id'],
                    'error': str(e)
                })
        
        return validation_result
    
    def _check_spatial_consistency(self, coords1: List[List[float]], coords2: List[List[float]]) -> bool:
        """Check spatial consistency between two coordinate sets"""
        if not coords1 or not coords2:
            return False
        
        # Simple distance-based consistency check
        # In a real implementation, this would be more sophisticated
        try:
            center1 = [sum(c[0] for c in coords1) / len(coords1), sum(c[1] for c in coords1) / len(coords1)]
            center2 = [sum(c[0] for c in coords2) / len(coords2), sum(c[1] for c in coords2) / len(coords2)]
            
            distance = math.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
            
            # Assume objects are spatially consistent if within reasonable distance
            return distance < 1000  # 1000 units threshold
        except:
            return False
    
    def _calculate_spatial_consistency(self, bim_objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall spatial consistency metrics"""
        total_relationships = 0
        consistent_relationships = 0
        
        for obj in bim_objects:
            relationships = obj.get('relationships', [])
            total_relationships += len(relationships)
            
            for relationship in relationships:
                related_obj = next((o for o in bim_objects if o['id'] == relationship), None)
                if related_obj:
                    coords1 = obj.get('geometry', {}).get('coordinates', [])
                    coords2 = related_obj.get('geometry', {}).get('coordinates', [])
                    
                    if self._check_spatial_consistency(coords1, coords2):
                        consistent_relationships += 1
        
        return {
            'total_relationships': total_relationships,
            'consistent_relationships': consistent_relationships,
            'consistency_percentage': (consistent_relationships / total_relationships * 100) if total_relationships > 0 else 0
        }
    
    def _convert_coordinates_for_export(self, obj: Dict[str, Any], coord_system: CoordinateSystem, 
                                      units: Units) -> List[List[float]]:
        """Convert coordinates for export to target coordinate system"""
        coordinates = obj.get('geometry', {}).get('coordinates', [])
        current_system = obj.get('geometry', {}).get('coordinate_system', 'svg')
        
        if current_system == coord_system.value:
            return coordinates
        
        # Use transform service for coordinate conversion
        converted_coordinates = []
        for coord in coordinates:
            converted = self.transform_service.convert_coordinates(
                coord[0], coord[1], current_system, coord_system.value
            )
            converted_coordinates.append([converted['x'], converted['y']])
        
        return converted_coordinates
    
    def _generate_ifc_export(self, objects: List[Dict[str, Any]]) -> str:
        """Generate IFC export data"""
        # Simplified IFC export - in a real implementation, this would use a proper IFC library
        ifc_data = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Arxos BIM Export'),'2;1');
FILE_NAME('arxos_export.ifc','{datetime.utcnow().isoformat()}',('Arxos System'),('Arxos'),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
"""
        
        for obj in objects:
            ifc_data += f"#{obj['id']}=IFCBUILDINGELEMENTPROXY('{obj['id']}',$,$,$,$,$,$,$,.ELEMENT.,NOTDEFINED);\n"
        
        ifc_data += "ENDSEC;\nEND-ISO-10303-21;"
        return ifc_data
    
    def _generate_json_export(self, objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate JSON export data"""
        return {
            'export_format': 'json',
            'export_date': datetime.utcnow().isoformat(),
            'objects': objects,
            'metadata': {
                'total_objects': len(objects),
                'coordinate_system': objects[0]['geometry']['coordinate_system'] if objects else None,
                'units': objects[0]['geometry']['units'] if objects else None
            }
        }
    
    def _generate_xml_export(self, objects: List[Dict[str, Any]]) -> str:
        """Generate XML export data"""
        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<bim_export>
    <metadata>
        <export_date>{datetime.utcnow().isoformat()}</export_date>
        <total_objects>{len(objects)}</total_objects>
    </metadata>
    <objects>
"""
        
        for obj in objects:
            xml_data += f"""        <object id="{obj['id']}" type="{obj['type']}">
            <name>{obj['name']}</name>
            <geometry>
                <coordinate_system>{obj['geometry']['coordinate_system']}</coordinate_system>
                <units>{obj['geometry']['units']}</units>
                <coordinates>
"""
            for coord in obj['geometry']['coordinates']:
                xml_data += f"                    <point x=\"{coord[0]}\" y=\"{coord[1]}\"/>\n"
            
            xml_data += """                </coordinates>
            </geometry>
        </object>
"""
        
        xml_data += """    </objects>
</bim_export>"""
        return xml_data
    
    def _validate_export_data(self, export_data: Any, export_format: str) -> Dict[str, Any]:
        """Validate export data"""
        validation_result = {
            'format_valid': True,
            'data_integrity': True,
            'coordinate_consistency': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            if export_format.lower() == "json":
                # Validate JSON structure
                if not isinstance(export_data, dict):
                    validation_result['format_valid'] = False
                    validation_result['errors'].append("Invalid JSON structure")
                
                if 'objects' not in export_data:
                    validation_result['data_integrity'] = False
                    validation_result['errors'].append("Missing objects array")
                    
            elif export_format.lower() == "xml":
                # Validate XML structure
                if not isinstance(export_data, str) or not export_data.startswith('<?xml'):
                    validation_result['format_valid'] = False
                    validation_result['errors'].append("Invalid XML structure")
                    
            elif export_format.lower() == "ifc":
                # Validate IFC structure
                if not isinstance(export_data, str) or "ISO-10303-21" not in export_data:
                    validation_result['format_valid'] = False
                    validation_result['errors'].append("Invalid IFC structure")
            
        except Exception as e:
            validation_result['format_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result


# Global instance
bim_object_integration_service = BIMObjectIntegrationService() 