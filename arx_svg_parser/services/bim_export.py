"""
BIM Export/Import Service

Provides comprehensive export and import functionality for BIM models in various formats:
- IFC (Industry Foundation Classes)
- Revit-compatible formats
- JSON/XML schemas
- 3D visualization exports (glTF, OBJ, FBX)
- Import functionality for all supported formats
- Validation during export/import
- Error handling and recovery
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, BinaryIO
from enum import Enum
import base64
import gzip
import tempfile
import zipfile
from dataclasses import dataclass, field

from models.bim import (
    BIMModel, BIMElement, Room, Wall, Device, Geometry, GeometryType,
    BIMElementBase, BIMSystem, BIMRelationship, Door, Window, SystemType, DeviceCategory
)
from services.robust_error_handling import create_error_handler
from services.bim_validator import BIMValidator, ValidationLevel
from utils.errors import ExportError, ImportError, ValidationError

import time
import hashlib
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import sqlite3
from contextlib import contextmanager
import math
import re

from structlog import get_logger

logger = get_logger()


class ExportFormat(Enum):
    """Supported export formats."""
    IFC = "ifc"
    REVIT_RVT = "rvt"
    REVIT_RFA = "rfa"
    JSON = "json"
    XML = "xml"
    GLTF = "gltf"
    OBJ = "obj"
    FBX = "fbx"
    COLLADA = "dae"
    THREE_JS = "threejs"
    CUSTOM = "custom"


class ImportFormat(Enum):
    """Supported import formats."""
    IFC = "ifc"
    JSON = "json"
    XML = "xml"
    GLTF = "gltf"
    OBJ = "obj"
    FBX = "fbx"
    CUSTOM = "custom"


@dataclass
class ExportOptions:
    """Options for BIM export."""
    format: ExportFormat
    include_metadata: bool = True
    include_relationships: bool = True
    include_systems: bool = True
    include_geometry: bool = True
    include_properties: bool = True
    compression: bool = False
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    custom_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportOptions:
    """Options for BIM import."""
    format: ImportFormat
    validate_on_import: bool = True
    create_systems: bool = True
    create_relationships: bool = True
    merge_duplicates: bool = False
    custom_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportResult:
    """Result of BIM export operation."""
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    export_time: float
    format: ExportFormat
    elements_exported: int
    systems_exported: int
    relationships_exported: int
    validation_results: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ImportResult:
    """Result of BIM import operation."""
    success: bool
    elements_imported: int
    systems_imported: int
    relationships_imported: int
    validation_results: Optional[Dict[str, Any]] = None
    import_time: float
    format: ImportFormat
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BIMExportService:
    """Comprehensive BIM export/import service supporting multiple formats."""
    
    def __init__(self):
        self.error_handler = create_error_handler()
        self.validator = BIMValidator()
        self.export_config = {
            "ifc": {"version": "IFC4", "schema": "IFC4"},
            "revit": {"version": "2023", "compatibility": "latest"},
            "visualization": {"format": "gltf", "embed_textures": True}
        }
        
        # Export format handlers
        self.supported_formats = {
            ExportFormat.IFC: self._export_to_ifc,
            ExportFormat.REVIT_RVT: self._export_to_revit,
            ExportFormat.REVIT_RFA: self._export_to_revit,
            ExportFormat.JSON: self._export_to_json,
            ExportFormat.XML: self._export_to_xml,
            ExportFormat.GLTF: self._export_visualization,
            ExportFormat.OBJ: self._export_visualization,
            ExportFormat.FBX: self._export_visualization,
            ExportFormat.CUSTOM: self._export_custom
        }
        
        # Import format handlers
        self.import_formats = {
            ImportFormat.IFC: self._import_ifc,
            ImportFormat.JSON: self._import_json,
            ImportFormat.XML: self._import_xml,
            ImportFormat.GLTF: self._import_gltf,
            ImportFormat.OBJ: self._import_obj,
            ImportFormat.FBX: self._import_fbx,
            ImportFormat.CUSTOM: self._import_custom
        }
    
    def export_bim_model(self, model: BIMModel, format: ExportFormat, 
                        options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Export BIM model in specified format.
        
        Args:
            model: BIM model to export
            format: Export format
            options: Export-specific options
            
        Returns:
            Export result with data and metadata
        """
        try:
            if format == ExportFormat.IFC:
                return self._export_to_ifc(model, options or {})
            elif format in [ExportFormat.REVIT_RVT, ExportFormat.REVIT_RFA]:
                return self._export_to_revit(model, format, options or {})
            elif format == ExportFormat.JSON:
                return self._export_to_json(model, options or {})
            elif format == ExportFormat.XML:
                return self._export_to_xml(model, options or {})
            elif format in [ExportFormat.GLTF, ExportFormat.OBJ, ExportFormat.FBX]:
                return self._export_visualization(model, format, options or {})
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.error_handler.handle_export_error(str(e), format.value)
            raise
    
    def export_bim(self, bim_model: BIMModel, options: ExportOptions) -> ExportResult:
        """
        Export BIM model to specified format with enhanced options.
        
        Args:
            bim_model: BIM model to export
            options: Export options
            
        Returns:
            ExportResult with export details
        """
        start_time = datetime.now()
        
        try:
            # Validate model before export
            if options.validation_level != ValidationLevel.BASIC:
                self.validator.validation_level = options.validation_level
                validation_result = self.validator.validate_bim_model(
                    bim_model.get_all_elements(),
                    bim_model.get_all_systems(),
                    bim_model.get_all_relationships()
                )
                
                if not validation_result.valid and options.validation_level == ValidationLevel.COMPLIANCE:
                    raise ExportError(f"Model validation failed: {validation_result.errors} errors found")
            
            # Export based on format
            if options.format not in self.supported_formats:
                raise ExportError(f"Unsupported export format: {options.format}")
            
            export_func = self.supported_formats[options.format]
            file_path = export_func(bim_model, options)
            
            # Calculate export statistics
            export_time = (datetime.now() - start_time).total_seconds()
            file_size = Path(file_path).stat().st_size if file_path else None
            
            result = ExportResult(
                success=True,
                file_path=file_path,
                file_size=file_size,
                export_time=export_time,
                format=options.format,
                elements_exported=len(bim_model.get_all_elements()),
                systems_exported=len(bim_model.get_all_systems()),
                relationships_exported=len(bim_model.get_all_relationships()),
                validation_results=validation_result.__dict__ if 'validation_result' in locals() else None
            )
            
            return result
            
        except Exception as e:
            return ExportResult(
                success=False,
                export_time=(datetime.now() - start_time).total_seconds(),
                format=options.format,
                errors=[str(e)]
            )
    
    def import_bim(self, file_path: str, options: ImportOptions) -> ImportResult:
        """
        Import BIM model from specified format.
        
        Args:
            file_path: Path to file to import
            options: Import options
            
        Returns:
            ImportResult with import details
        """
        start_time = datetime.now()
        
        try:
            if options.format not in self.import_formats:
                raise ImportError(f"Unsupported import format: {options.format}")
            
            import_func = self.import_formats[options.format]
            bim_model = import_func(file_path, options)
            
            # Validate imported model
            validation_results = None
            if options.validate_on_import:
                validation_result = self.validator.validate_bim_model(
                    bim_model.get_all_elements(),
                    bim_model.get_all_systems(),
                    bim_model.get_all_relationships()
                )
                validation_results = validation_result.__dict__
            
            import_time = (datetime.now() - start_time).total_seconds()
            
            return ImportResult(
                success=True,
                elements_imported=len(bim_model.get_all_elements()),
                systems_imported=len(bim_model.get_all_systems()),
                relationships_imported=len(bim_model.get_all_relationships()),
                validation_results=validation_results,
                import_time=import_time,
                format=options.format
            )
            
        except Exception as e:
            return ImportResult(
                success=False,
                import_time=(datetime.now() - start_time).total_seconds(),
                format=options.format,
                errors=[str(e)]
            )
    
    def _export_to_ifc(self, model: BIMModel, options: Union[Dict[str, Any], ExportOptions]) -> Union[Dict[str, Any], str]:
        """Export to IFC format."""
        if isinstance(options, ExportOptions):
            # Enhanced export with options
            ifc_data = self._generate_ifc_content(model, options)
            file_path = self._save_to_file(ifc_data, "ifc", options)
            return file_path
        else:
            # Legacy export
            ifc_data = self._generate_ifc_content(model, options)
            return {
                "format": "ifc",
                "data": ifc_data,
                "metadata": {
                    "version": options.get("version", "IFC4"),
                    "timestamp": datetime.now().isoformat(),
                    "elements_count": len(model.elements)
                }
            }
    
    def _generate_ifc_content(self, model: BIMModel, options: Union[Dict[str, Any], ExportOptions]) -> str:
        """Generate IFC content from BIM model."""
        if isinstance(options, ExportOptions):
            ifc_version = options.custom_options.get("version", "IFC4")
        else:
            ifc_version = options.get("version", "IFC4")
        
        # IFC header
        ifc_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Arxos BIM Export'),'2;1');
FILE_NAME('{model.name}.ifc','{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}',('Arxos User'),('Arxos Organization'),'Arxos SVG-BIM System','Arxos BIM Export','');
FILE_SCHEMA(('{ifc_version}'));
ENDSEC;
DATA;
"""
        
        # IFC entities
        entity_id = 1
        
        # Project
        ifc_content += f"#{entity_id}=IFCPROJECT('{model.id}',$,{model.name},$,$,$,(#{entity_id+1}),(#{entity_id+2}));\n"
        entity_id += 1
        
        # Project context
        ifc_content += f"#{entity_id}=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.0E-5,$,$);\n"
        entity_id += 1
        
        # Site
        ifc_content += f"#{entity_id}=IFCSITE('SITE_GUID',$,{model.name} Site,$,$,$,$,$,$,.ELEMENT.,$,$,$,$);\n"
        entity_id += 1
        
        # Building
        ifc_content += f"#{entity_id}=IFCBUILDING('BUILDING_GUID',$,{model.name},$,$,$,$,$,$,.ELEMENT.,$,$,$);\n"
        entity_id += 1
        
        # Building storey
        ifc_content += f"#{entity_id}=IFCBUILDINGSTOREY('STOREY_GUID',$,Ground Floor,$,$,$,$,$,$,.ELEMENT.,$,$,$);\n"
        entity_id += 1
        
        # Export elements
        for element in model.elements:
            ifc_content += self._element_to_ifc(element, entity_id)
            entity_id += 1
        
        ifc_content += "ENDSEC;\nEND-ISO-10303-21;"
        return ifc_content
    
    def _element_to_ifc(self, element: BIMElement, entity_id: int) -> str:
        """Convert BIM element to IFC entity."""
        if isinstance(element, Room):
            return self._room_to_ifc(element, entity_id)
        elif isinstance(element, Wall):
            return self._wall_to_ifc(element, entity_id)
        elif isinstance(element, Device):
            return self._device_to_ifc(element, entity_id)
        else:
            return self._generic_element_to_ifc(element, entity_id)
    
    def _room_to_ifc(self, room: Room, entity_id: int) -> str:
        """Convert room to IFC space."""
        return f"""#{entity_id}=IFCSPACE('{room.id}',$,{room.name},$,$,$,$,$,$,.ELEMENT.,$,$,$,$);
#{entity_id+1}=IFCLOCALPLACEMENT($,#{entity_id+2});
#{entity_id+2}=IFCAXIS2PLACEMENT3D(#{entity_id+3},$,$,$);
#{entity_id+3}=IFCCARTESIANPOINT((0.,0.,0.));\n"""
    
    def _wall_to_ifc(self, wall: Wall, entity_id: int) -> str:
        """Convert wall to IFC wall."""
        return f"""#{entity_id}=IFCWALL('{wall.id}',$,{wall.name},$,$,$,$,$,$,.ELEMENT.,$,$,$,$);
#{entity_id+1}=IFCLOCALPLACEMENT($,#{entity_id+2});
#{entity_id+2}=IFCAXIS2PLACEMENT3D(#{entity_id+3},$,$,$);
#{entity_id+3}=IFCCARTESIANPOINT((0.,0.,0.));\n"""
    
    def _device_to_ifc(self, device: Device, entity_id: int) -> str:
        """Convert device to IFC distribution element."""
        return f"""#{entity_id}=IFCDISTRIBUTIONELEMENT('{device.id}',$,{device.name},$,$,$,$,$,$,.ELEMENT.,$,$,$,$);
#{entity_id+1}=IFCLOCALPLACEMENT($,#{entity_id+2});
#{entity_id+2}=IFCAXIS2PLACEMENT3D(#{entity_id+3},$,$,$);
#{entity_id+3}=IFCCARTESIANPOINT((0.,0.,0.));\n"""
    
    def _generic_element_to_ifc(self, element: BIMElement, entity_id: int) -> str:
        """Convert generic element to IFC building element."""
        return f"""#{entity_id}=IFCBUILDINGELEMENTPROXY('{element.id}',$,{element.name},$,$,$,$,$,$,.ELEMENT.,$,$,$,$);
#{entity_id+1}=IFCLOCALPLACEMENT($,#{entity_id+2});
#{entity_id+2}=IFCAXIS2PLACEMENT3D(#{entity_id+3},$,$,$);
#{entity_id+3}=IFCCARTESIANPOINT((0.,0.,0.));\n"""
    
    def _export_to_revit(self, model: BIMModel, format: ExportFormat, 
                         options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to Revit-compatible format."""
        if format == ExportFormat.REVIT_RVT:
            return self._export_to_rvt(model, options)
        else:
            return self._export_to_rfa(model, options)
    
    def _export_to_rvt(self, model: BIMModel, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to Revit RVT format (simplified XML-based)."""
        rvt_data = self._generate_rvt_content(model, options)
        return {
            "format": "rvt",
            "data": rvt_data,
            "metadata": {
                "version": options.get("version", "2023"),
                "timestamp": datetime.now().isoformat(),
                "elements_count": len(model.elements)
            }
        }
    
    def _generate_rvt_content(self, model: BIMModel, options: Dict[str, Any]) -> str:
        """Generate Revit RVT content."""
        root = ET.Element("RevitProject")
        root.set("version", options.get("version", "2023"))
        root.set("name", model.name)
        
        # Project information
        project_info = ET.SubElement(root, "ProjectInformation")
        ET.SubElement(project_info, "Name").text = model.name
        ET.SubElement(project_info, "Number").text = model.id
        ET.SubElement(project_info, "Created").text = datetime.now().isoformat()
        
        # Elements
        elements_elem = ET.SubElement(root, "Elements")
        for element in model.elements:
            element_elem = self._element_to_revit_xml(element)
            elements_elem.append(element_elem)
        
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def _element_to_revit_xml(self, element: BIMElement) -> ET.Element:
        """Convert element to Revit XML."""
        elem = ET.Element("Element")
        elem.set("id", element.id)
        elem.set("type", element.element_type)
        
        ET.SubElement(elem, "Name").text = element.name
        ET.SubElement(elem, "Category").text = element.element_type
        
        # Properties
        props_elem = ET.SubElement(elem, "Properties")
        for key, value in element.properties.items():
            prop_elem = ET.SubElement(props_elem, "Property")
            prop_elem.set("name", key)
            prop_elem.text = str(value)
        
        # Geometry
        if element.geometry:
            geom_elem = ET.SubElement(elem, "Geometry")
            geom_elem.set("type", element.geometry.type.value)
            coords_elem = ET.SubElement(geom_elem, "Coordinates")
            coords_elem.text = str(element.geometry.coordinates)
        
        return elem
    
    def _export_to_rfa(self, model: BIMModel, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to Revit RFA format (family file)."""
        rfa_data = self._generate_rfa_content(model, options)
        return {
            "format": "rfa",
            "data": rfa_data,
            "metadata": {
                "version": options.get("version", "2023"),
                "timestamp": datetime.now().isoformat(),
                "elements_count": len(model.elements)
            }
        }
    
    def _generate_rfa_content(self, model: BIMModel, options: Dict[str, Any]) -> str:
        """Generate Revit RFA content."""
        root = ET.Element("RevitFamily")
        root.set("version", options.get("version", "2023"))
        root.set("name", model.name)
        
        # Family information
        family_info = ET.SubElement(root, "FamilyInformation")
        ET.SubElement(family_info, "Name").text = model.name
        ET.SubElement(family_info, "Category").text = "Generic Models"
        ET.SubElement(family_info, "Created").text = datetime.now().isoformat()
        
        # Parameters
        params_elem = ET.SubElement(root, "Parameters")
        for element in model.elements:
            for key, value in element.properties.items():
                param_elem = ET.SubElement(params_elem, "Parameter")
                param_elem.set("name", key)
                param_elem.set("type", "Text")
                param_elem.text = str(value)
        
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def _export_to_json(self, model: BIMModel, options: Union[Dict[str, Any], ExportOptions]) -> Union[Dict[str, Any], str]:
        """Export to JSON format."""
        json_data = self._generate_json_content(model, options)
        
        if isinstance(options, ExportOptions):
            # Enhanced export with options
            file_path = self._save_to_file(json_data, "json", options)
            return file_path
        else:
            # Legacy export
            return {
                "format": "json",
                "data": json_data,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "elements_count": len(model.elements),
                    "pretty_print": options.get("pretty_print", True)
                }
            }
    
    def _generate_json_content(self, model: BIMModel, options: Union[Dict[str, Any], ExportOptions]) -> str:
        """Generate JSON content."""
        if isinstance(options, ExportOptions):
            # Enhanced export with options
            json_obj = {
                "bim_model": {
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "version": model.version,
                    "created_at": model.created_at.isoformat() if model.created_at else None,
                    "updated_at": model.updated_at.isoformat() if model.updated_at else None,
                    "elements": [self._element_to_json(elem) for elem in model.get_all_elements()] if options.include_geometry else [],
                    "systems": [self._system_to_json(sys) for sys in model.get_all_systems()] if options.include_systems else [],
                    "relationships": [self._relationship_to_json(rel) for rel in model.get_all_relationships()] if options.include_relationships else [],
                    "metadata": model.model_metadata if options.include_metadata else {},
                    "properties": model.properties if options.include_properties else {}
                }
            }
            
            indent = 2 if options.custom_options.get("pretty_print", True) else None
        else:
            # Legacy export
            json_obj = {
                "bim_model": {
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "version": model.version,
                    "created_at": model.created_at.isoformat() if model.created_at else None,
                    "updated_at": model.updated_at.isoformat() if model.updated_at else None,
                    "elements": [self._element_to_json(elem) for elem in model.elements],
                    "systems": [self._system_to_json(sys) for sys in model.systems],
                    "spaces": [self._space_to_json(space) for space in model.spaces],
                    "relationships": [self._relationship_to_json(rel) for rel in model.relationships],
                    "metadata": model.model_metadata,
                    "properties": model.properties
                }
            }
            
            indent = 2 if options.get("pretty_print", True) else None
        
        return json.dumps(json_obj, indent=indent, default=str)
    
    def _element_to_json(self, element: BIMElement) -> Dict[str, Any]:
        """Convert element to JSON."""
        return {
            "id": element.id,
            "name": element.name,
            "element_type": element.element_type,
            "geometry": self._geometry_to_json(element.geometry) if element.geometry else None,
            "properties": element.properties,
            "symbol_metadata": element.symbol_metadata,
            "tags": element.tags,
            "status": element.status.value if element.status else None
        }
    
    def _geometry_to_json(self, geometry: Geometry) -> Dict[str, Any]:
        """Convert geometry to JSON."""
        return {
            "type": geometry.type.value,
            "coordinates": geometry.coordinates,
            "properties": geometry.properties,
            "bounding_box": geometry.bounding_box,
            "centroid": geometry.centroid
        }
    
    def _system_to_json(self, system) -> Dict[str, Any]:
        """Convert system to JSON."""
        return {
            "id": system.id,
            "name": system.name,
            "system_type": system.system_type,
            "elements": [elem.id for elem in system.elements],
            "properties": system.properties
        }
    
    def _space_to_json(self, space) -> Dict[str, Any]:
        """Convert space to JSON."""
        return {
            "id": space.id,
            "name": space.name,
            "space_type": space.space_type,
            "elements": [elem.id for elem in space.elements],
            "properties": space.properties
        }
    
    def _relationship_to_json(self, relationship) -> Dict[str, Any]:
        """Convert relationship to JSON."""
        return {
            "id": relationship.id,
            "source_id": relationship.source_id,
            "target_id": relationship.target_id,
            "relationship_type": relationship.relationship_type.value,
            "properties": relationship.properties,
            "symbol_metadata": relationship.symbol_metadata
        }
    
    def _export_to_xml(self, model: BIMModel, options: Union[Dict[str, Any], ExportOptions]) -> Union[Dict[str, Any], str]:
        """Export to XML format."""
        xml_data = self._generate_xml_content(model, options)
        
        if isinstance(options, ExportOptions):
            # Enhanced export with options
            file_path = self._save_to_file(xml_data, "xml", options)
            return file_path
        else:
            # Legacy export
            return {
                "format": "xml",
                "data": xml_data,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "elements_count": len(model.elements),
                    "pretty_print": options.get("pretty_print", True)
                }
            }
    
    def _generate_xml_content(self, model: BIMModel, options: Dict[str, Any]) -> str:
        """Generate XML content."""
        root = ET.Element("BIMModel")
        root.set("id", model.id)
        root.set("name", model.name)
        root.set("version", model.version)
        
        # Model information
        info_elem = ET.SubElement(root, "ModelInformation")
        ET.SubElement(info_elem, "Description").text = model.description or ""
        ET.SubElement(info_elem, "CreatedAt").text = model.created_at.isoformat() if model.created_at else ""
        ET.SubElement(info_elem, "UpdatedAt").text = model.updated_at.isoformat() if model.updated_at else ""
        
        # Elements
        elements_elem = ET.SubElement(root, "Elements")
        for element in model.elements:
            element_elem = self._element_to_xml(element)
            elements_elem.append(element_elem)
        
        # Systems
        systems_elem = ET.SubElement(root, "Systems")
        for system in model.systems:
            system_elem = self._system_to_xml(system)
            systems_elem.append(system_elem)
        
        # Spaces
        spaces_elem = ET.SubElement(root, "Spaces")
        for space in model.spaces:
            space_elem = self._space_to_xml(space)
            spaces_elem.append(space_elem)
        
        # Relationships
        relationships_elem = ET.SubElement(root, "Relationships")
        for relationship in model.relationships:
            relationship_elem = self._relationship_to_xml(relationship)
            relationships_elem.append(relationship_elem)
        
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def _element_to_xml(self, element: BIMElement) -> ET.Element:
        """Convert element to XML."""
        elem = ET.Element("Element")
        elem.set("id", element.id)
        elem.set("type", element.element_type)
        
        ET.SubElement(elem, "Name").text = element.name
        
        # Geometry
        if element.geometry:
            geom_elem = ET.SubElement(elem, "Geometry")
            geom_elem.set("type", element.geometry.type.value)
            coords_elem = ET.SubElement(geom_elem, "Coordinates")
            coords_elem.text = str(element.geometry.coordinates)
        
        # Properties
        props_elem = ET.SubElement(elem, "Properties")
        for key, value in element.properties.items():
            prop_elem = ET.SubElement(props_elem, "Property")
            prop_elem.set("name", key)
            prop_elem.text = str(value)
        
        return elem
    
    def _system_to_xml(self, system) -> ET.Element:
        """Convert system to XML."""
        sys_elem = ET.Element("System")
        sys_elem.set("id", system.id)
        sys_elem.set("type", system.system_type)
        
        ET.SubElement(sys_elem, "Name").text = system.name
        
        # Elements
        elements_elem = ET.SubElement(sys_elem, "Elements")
        for element in system.elements:
            elem_ref = ET.SubElement(elements_elem, "ElementRef")
            elem_ref.set("id", element.id)
        
        return sys_elem
    
    def _space_to_xml(self, space) -> ET.Element:
        """Convert space to XML."""
        space_elem = ET.Element("Space")
        space_elem.set("id", space.id)
        space_elem.set("type", space.space_type)
        
        ET.SubElement(space_elem, "Name").text = space.name
        
        # Elements
        elements_elem = ET.SubElement(space_elem, "Elements")
        for element in space.elements:
            elem_ref = ET.SubElement(elements_elem, "ElementRef")
            elem_ref.set("id", element.id)
        
        return space_elem
    
    def _relationship_to_xml(self, relationship) -> ET.Element:
        """Convert relationship to XML."""
        rel_elem = ET.Element("Relationship")
        rel_elem.set("id", relationship.id)
        rel_elem.set("type", relationship.relationship_type.value)
        
        rel_elem.set("source_id", relationship.source_id)
        rel_elem.set("target_id", relationship.target_id)
        
        # Properties
        props_elem = ET.SubElement(rel_elem, "Properties")
        for key, value in relationship.properties.items():
            prop_elem = ET.SubElement(props_elem, "Property")
            prop_elem.set("name", key)
            prop_elem.text = str(value)
        
        return rel_elem
    
    def _export_visualization(self, model: BIMModel, format: ExportFormat, 
                             options: Dict[str, Any]) -> Dict[str, Any]:
        """Export visualization formats (3D models, diagrams)."""
        if format == ExportFormat.GLTF:
            return self._export_to_gltf(model, options)
        elif format == ExportFormat.OBJ:
            return self._export_to_obj(model, options)
        elif format == ExportFormat.FBX:
            return self._export_to_fbx(model, options)
        else:
            raise ValueError(f"Unsupported visualization format: {format}")
    
    def _export_to_gltf(self, model: BIMModel, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to glTF format for 3D visualization."""
        gltf_data = self._generate_gltf_content(model, options)
        return {
            "format": "gltf",
            "data": gltf_data,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "elements_count": len(model.elements),
                "embed_textures": options.get("embed_textures", True)
            }
        }
    
    def _generate_gltf_content(self, model: BIMModel, options: Dict[str, Any]) -> str:
        """Generate glTF content."""
        gltf_obj = {
            "asset": {
                "version": "2.0",
                "generator": "Arxos SVG-BIM System"
            },
            "scene": 0,
            "scenes": [{
                "nodes": [0]
            }],
            "nodes": [],
            "meshes": [],
            "accessors": [],
            "bufferViews": [],
            "buffers": []
        }
        
        # Convert elements to glTF nodes and meshes
        for i, element in enumerate(model.elements):
            if element.geometry:
                node = {
                    "mesh": i,
                    "name": element.name
                }
                gltf_obj["nodes"].append(node)
                
                mesh = self._geometry_to_gltf_mesh(element.geometry)
                gltf_obj["meshes"].append(mesh)
        
        return json.dumps(gltf_obj, indent=2)
    
    def _geometry_to_gltf_mesh(self, geometry: Geometry) -> Dict[str, Any]:
        """Convert geometry to glTF mesh."""
        if geometry.type == GeometryType.POLYGON:
            return self._polygon_to_gltf_mesh(geometry)
        elif geometry.type == GeometryType.LINESTRING:
            return self._linestring_to_gltf_mesh(geometry)
        elif geometry.type == GeometryType.POINT:
            return self._point_to_gltf_mesh(geometry)
        else:
            return {"primitives": []}
    
    def _polygon_to_gltf_mesh(self, geometry: Geometry) -> Dict[str, Any]:
        """Convert polygon to glTF mesh."""
        # Simplified polygon to mesh conversion
        return {
            "primitives": [{
                "attributes": {
                    "POSITION": 0
                },
                "indices": 1,
                "mode": 4  # TRIANGLES
            }]
        }
    
    def _linestring_to_gltf_mesh(self, geometry: Geometry) -> Dict[str, Any]:
        """Convert linestring to glTF mesh."""
        return {
            "primitives": [{
                "attributes": {
                    "POSITION": 0
                },
                "mode": 1  # LINES
            }]
        }
    
    def _point_to_gltf_mesh(self, geometry: Geometry) -> Dict[str, Any]:
        """Convert point to glTF mesh."""
        return {
            "primitives": [{
                "attributes": {
                    "POSITION": 0
                },
                "mode": 0  # POINTS
            }]
        }
    
    def _export_to_obj(self, model: BIMModel, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to OBJ format."""
        obj_data = self._generate_obj_content(model, options)
        return {
            "format": "obj",
            "data": obj_data,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "elements_count": len(model.elements)
            }
        }
    
    def _generate_obj_content(self, model: BIMModel, options: Dict[str, Any]) -> str:
        """Generate OBJ content."""
        obj_lines = ["# Arxos BIM Export", f"# {datetime.now().isoformat()}"]
        
        vertex_index = 1
        for element in model.elements:
            if element.geometry:
                obj_lines.append(f"# {element.name}")
                obj_lines.extend(self._geometry_to_obj(element.geometry, vertex_index))
                vertex_index += len(element.geometry.coordinates)
        
        return "\n".join(obj_lines)
    
    def _geometry_to_obj(self, geometry: Geometry, start_index: int) -> List[str]:
        """Convert geometry to OBJ format."""
        lines = []
        
        if geometry.type == GeometryType.POLYGON:
            # Add vertices
            for coord in geometry.coordinates[0]:
                lines.append(f"v {coord[0]} {coord[1]} 0")
            
            # Add face
            face_indices = [str(start_index + i) for i in range(len(geometry.coordinates[0]))]
            lines.append(f"f {' '.join(face_indices)}")
        
        return lines
    
    def _export_to_fbx(self, model: BIMModel, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to FBX format (simplified)."""
        # Simplified FBX export - in production would use FBX SDK
        fbx_data = self._generate_fbx_content(model, options)
        return {
            "format": "fbx",
            "data": fbx_data,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "elements_count": len(model.elements)
            }
        }
    
    def _generate_fbx_content(self, model: BIMModel, options: Dict[str, Any]) -> str:
        """Generate simplified FBX content."""
        # This is a placeholder - real FBX export would require FBX SDK
        return f"# FBX Export - {model.name}\n# Generated by Arxos SVG-BIM System\n# {datetime.now().isoformat()}"
    
    def _export_custom(self, model: BIMModel, options: Dict[str, Any]) -> str:
        """Placeholder for custom export logic."""
        raise NotImplementedError("Custom export is not yet implemented.")
    
    def _import_ifc(self, file_path: str, options: ImportOptions) -> BIMModel:
        """Import BIM model from IFC file."""
        ifc_data = self._read_file_content(file_path)
        ifc_parser = IFC4Parser()
        bim_model = ifc_parser.parse(ifc_data)
        
        # Apply import options
        if options.create_systems:
            bim_model.create_systems()
        if options.create_relationships:
            bim_model.create_relationships()
        if options.merge_duplicates:
            bim_model.merge_duplicates()
        
        return bim_model
    
    def _import_json(self, file_path: str, options: ImportOptions) -> BIMModel:
        """Import BIM model from JSON file."""
        json_data = self._read_file_content(file_path)
        json_obj = json.loads(json_data)
        
        bim_model = BIMModel.from_dict(json_obj["bim_model"])
        
        # Apply import options
        if options.create_systems:
            bim_model.create_systems()
        if options.create_relationships:
            bim_model.create_relationships()
        if options.merge_duplicates:
            bim_model.merge_duplicates()
        
        return bim_model
    
    def _import_xml(self, file_path: str, options: ImportOptions) -> BIMModel:
        """Import BIM model from XML file."""
        xml_data = self._read_file_content(file_path)
        root = ET.fromstring(xml_data)
        
        bim_model = BIMModel.from_xml(root)
        
        # Apply import options
        if options.create_systems:
            bim_model.create_systems()
        if options.create_relationships:
            bim_model.create_relationships()
        if options.merge_duplicates:
            bim_model.merge_duplicates()
        
        return bim_model
    
    def _import_gltf(self, file_path: str, options: ImportOptions) -> BIMModel:
        """Import BIM model from glTF file."""
        gltf_data = self._read_file_content(file_path)
        gltf_obj = json.loads(gltf_data)
        
        bim_model = BIMModel.from_gltf(gltf_obj)
        
        # Apply import options
        if options.create_systems:
            bim_model.create_systems()
        if options.create_relationships:
            bim_model.create_relationships()
        if options.merge_duplicates:
            bim_model.merge_duplicates()
        
        return bim_model
    
    def _import_obj(self, file_path: str, options: ImportOptions) -> BIMModel:
        """Import BIM model from OBJ file."""
        obj_data = self._read_file_content(file_path)
        obj_lines = obj_data.splitlines()
        
        bim_model = BIMModel()
        
        vertex_index = 0
        for line in obj_lines:
            if line.startswith("#"):
                continue
            if line.startswith("v "):
                vertex_data = line.replace("v ", "").split()
                x, y, z = float(vertex_data[0]), float(vertex_data[1]), float(vertex_data[2])
                bim_model.add_element(BIMElement(id=f"vertex_{vertex_index}", name=f"Vertex {vertex_index}", element_type="Vertex", geometry=Geometry(type=GeometryType.POINT, coordinates=[(x, y, z)])))
                vertex_index += 1
            elif line.startswith("f "):
                face_data = line.replace("f ", "").split()
                face_indices = [int(i) - 1 for i in face_data] # OBJ indices are 1-based
                for i in range(len(face_indices) - 2):
                    a, b, c = face_indices[0], face_indices[i+1], face_indices[i+2]
                    bim_model.add_relationship(BIMRelationship(id=f"face_{vertex_index}", source_id=f"vertex_{a}", target_id=f"vertex_{b}", relationship_type=RelationshipType.FACE_VERTEX))
                    bim_model.add_relationship(BIMRelationship(id=f"face_{vertex_index+1}", source_id=f"vertex_{b}", target_id=f"vertex_{c}", relationship_type=RelationshipType.FACE_VERTEX))
                    bim_model.add_relationship(BIMRelationship(id=f"face_{vertex_index+2}", source_id=f"vertex_{c}", target_id=f"vertex_{a}", relationship_type=RelationshipType.FACE_VERTEX))
                    vertex_index += 3
        
        # Apply import options
        if options.create_systems:
            bim_model.create_systems()
        if options.create_relationships:
            bim_model.create_relationships()
        if options.merge_duplicates:
            bim_model.merge_duplicates()
        
        return bim_model
    
    def _import_fbx(self, file_path: str, options: ImportOptions) -> BIMModel:
        """Import BIM model from FBX file."""
        # Simplified FBX import - in production would use FBX SDK
        fbx_data = self._read_file_content(file_path)
        
        bim_model = BIMModel()
        
        # Placeholder for FBX parsing logic
        # In a real application, you would use a FBX SDK to parse the file
        # and convert FBX nodes/meshes/geometry to BIM elements/systems/relationships
        
        # Example: If you had a FBX parser that returned a list of BIMElements
        # for element in fbx_elements:
        #     bim_model.add_element(element)
        
        # Apply import options
        if options.create_systems:
            bim_model.create_systems()
        if options.create_relationships:
            bim_model.create_relationships()
        if options.merge_duplicates:
            bim_model.merge_duplicates()
        
        return bim_model
    
    def _import_custom(self, file_path: str, options: ImportOptions) -> BIMModel:
        """Placeholder for custom import logic."""
        raise NotImplementedError("Custom import is not yet implemented.")
    
    def _read_file_content(self, file_path: str) -> str:
        """Read content from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise ImportError(f"File not found at {file_path}")
        except Exception as e:
            raise ImportError(f"Error reading file {file_path}: {e}")
    
    def _save_to_file(self, content: str, format_extension: str, options: ExportOptions) -> str:
        """Save content to file with optional compression."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bim_export_{timestamp}.{format_extension}"
        
        if options.compression:
            filename += ".gz"
            content_bytes = content.encode('utf-8')
            compressed_content = gzip.compress(content_bytes)
            
            with open(filename, 'wb') as f:
                f.write(compressed_content)
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return filename
    
    def _create_export_metadata(self, model: BIMModel, options: ExportOptions) -> Dict[str, Any]:
        """Create metadata for export."""
        return {
            "export_timestamp": datetime.now().isoformat(),
            "format": options.format.value,
            "elements_count": len(model.get_all_elements()),
            "systems_count": len(model.get_all_systems()),
            "relationships_count": len(model.get_all_relationships()),
            "include_metadata": options.include_metadata,
            "include_relationships": options.include_relationships,
            "include_systems": options.include_systems,
            "include_geometry": options.include_geometry,
            "include_properties": options.include_properties,
            "compression": options.compression,
            "validation_level": options.validation_level.value
        }
    
    def get_supported_formats(self) -> List[Dict[str, Any]]:
        """Get list of supported export formats."""
        return [
            {"format": "ifc", "name": "Industry Foundation Classes", "description": "Standard BIM format"},
            {"format": "rvt", "name": "Revit Project", "description": "Revit project file format"},
            {"format": "rfa", "name": "Revit Family", "description": "Revit family file format"},
            {"format": "json", "name": "JSON Schema", "description": "Structured JSON format"},
            {"format": "xml", "name": "XML Schema", "description": "Structured XML format"},
            {"format": "gltf", "name": "glTF 3D Model", "description": "3D visualization format"},
            {"format": "obj", "name": "Wavefront OBJ", "description": "3D model format"},
            {"format": "fbx", "name": "Autodesk FBX", "description": "3D model format"},
            {"format": "custom", "name": "Custom", "description": "Export/Import custom formats"}
        ]
    
    def validate_export_options(self, format: ExportFormat, options: Dict[str, Any]) -> bool:
        """Validate export options for given format."""
        try:
            if format == ExportFormat.IFC:
                return "version" in options or "schema" in options
            elif format in [ExportFormat.REVIT_RVT, ExportFormat.REVIT_RFA]:
                return "version" in options
            elif format in [ExportFormat.GLTF, ExportFormat.OBJ, ExportFormat.FBX]:
                return "embed_textures" in options
            else:
                return True
        except Exception:
            return False 