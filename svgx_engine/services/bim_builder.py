"""
SVGX Engine - Enhanced BIM Builder Service

Builds hierarchical BIM structures from extracted SVGX elements with spatial organization 
and system classification, optimized for SVGX-specific operations and metadata.
"""

import structlog
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from svgx_engine.models.bim import (
    BIMModel, Room, Wall, Door, Window, HVACZone, AirHandler, VAVBox,
    ElectricalCircuit, ElectricalPanel, ElectricalOutlet,
    PlumbingSystem, PlumbingFixture, Valve,
    FireAlarmSystem, SmokeDetector, SecuritySystem, Camera,
    Device, Label, SystemType, RoomType, DeviceCategory, Geometry, GeometryType
)
from svgx_engine.models.bim_metadata import BIMObjectMetadata, PropertySet, ClassificationReference
from svgx_engine.models.bim_relationships import BIMRelationship, BIMRelationshipSet, SpatialRelationshipType, SystemRelationshipType
from svgx_engine.services.bim_object_integration import BIMObjectIntegrationService
from svgx_engine.utils.errors import BIMError, ValidationError

logger = structlog.get_logger(__name__)

class BIMBuilder:
    """Enhanced BIM builder for creating hierarchical BIM structures."""
    
    def __init__(self):
        self.bim_integration = BIMObjectIntegrationService()
        self.relationships = BIMRelationshipSet()
        
        logger.info("bim_builder_initialized",
                   integration_service="BIMObjectIntegrationService",
                   relationships_set="BIMRelationshipSet")
        
    def build_hierarchical_bim_model(self, extracted_data: Dict[str, Any]) -> BIMModel:
        """
        Build a hierarchical BIM model from extracted SVGX data.
        
        Args:
            extracted_data: Data from BIM extraction service
            
        Returns:
            BIMModel: Complete hierarchical BIM model
        """
        try:
            logger.info("bim_model_construction_started",
                       building_id=extracted_data.get('metadata', {}).get('building_id'),
                       rooms_count=len(extracted_data.get('rooms', [])),
                       devices_count=len(extracted_data.get('devices', [])),
                       svg_elements_count=len(extracted_data.get('svg_elements', [])))
            
            # Create base BIM model
            bim_model = BIMModel(
                name=extracted_data.get('metadata', {}).get('building_id', 'Unknown Building'),
                description="BIM model built from SVGX extraction"
            )
            
            # 1. Build spatial hierarchy (floors -> rooms -> zones)
            self._build_spatial_hierarchy(bim_model, extracted_data)
            
            # 2. Build system hierarchy (systems -> equipment -> devices)
            self._build_system_hierarchy(bim_model, extracted_data)
            
            # 3. Establish relationships between elements
            self._establish_relationships(bim_model, extracted_data)
            
            # 4. Add metadata and classifications
            self._add_metadata_and_classifications(bim_model, extracted_data)
            
            # 5. Validate the complete model
            validation_errors = bim_model.validate_model()
            if validation_errors:
                logger.warning("bim_model_validation_warnings",
                              building_id=bim_model.name,
                              validation_errors=validation_errors)
            
            logger.info("bim_model_construction_completed",
                       building_id=bim_model.name,
                       rooms_count=len(bim_model.rooms),
                       devices_count=len(bim_model.devices),
                       walls_count=len(bim_model.walls),
                       air_handlers_count=len(bim_model.air_handlers),
                       vav_boxes_count=len(bim_model.vav_boxes),
                       electrical_panels_count=len(bim_model.electrical_panels),
                       plumbing_fixtures_count=len(bim_model.plumbing_fixtures))
            
            return bim_model
            
        except Exception as e:
            logger.error("bim_model_construction_failed",
                        building_id=extracted_data.get('metadata', {}).get('building_id'),
                        error=str(e),
                        error_type=type(e).__name__)
            raise

    # ... (rest of the methods from the arx_svg_parser version, with all imports and references updated to svgx_engine) 