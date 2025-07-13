"""
BIM Import Service

Provides import functionality for BIM models from various formats:
- IFC (Industry Foundation Classes)
- Revit-compatible formats (RVT, RFA)
- Other BIM formats (JSON, XML, gbXML, glTF, etc.)
- Robust validation and error handling
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from enum import Enum

from models.bim import BIMModel, BIMElement, Room, Wall, Device, Geometry, GeometryType
from services.robust_error_handling import create_error_handler
from structlog import get_logger

logger = get_logger()


class ImportFormat(Enum):
    """Supported import formats."""
    IFC = "ifc"
    REVIT_RVT = "rvt"
    REVIT_RFA = "rfa"
    JSON = "json"
    XML = "xml"
    GBXML = "gbxml"
    GLTF = "gltf"


class BIMImportService:
    """
    Comprehensive BIM import service supporting multiple formats.
    """
    def __init__(self):
        self.error_handler = create_error_handler()

    def import_bim_model(self, data: Union[str, bytes, Path], format: ImportFormat, options: Optional[Dict[str, Any]] = None) -> BIMModel:
        """
        Import a BIM model from the specified format.
        Args:
            data: File path, string, or bytes of the BIM file
            format: Import format
            options: Import-specific options
        Returns:
            BIMModel: Imported BIM model
        Raises:
            ImportError: If import fails
        """
        try:
            if format == ImportFormat.IFC:
                return self._import_from_ifc(data, options or {})
            elif format in [ImportFormat.REVIT_RVT, ImportFormat.REVIT_RFA]:
                return self._import_from_revit(data, format, options or {})
            elif format == ImportFormat.JSON:
                return self._import_from_json(data, options or {})
            elif format == ImportFormat.XML:
                return self._import_from_xml(data, options or {})
            elif format == ImportFormat.GBXML:
                return self._import_from_gbxml(data, options or {})
            elif format == ImportFormat.GLTF:
                return self._import_from_gltf(data, options or {})
            else:
                raise ValueError(f"Unsupported import format: {format}")
        except Exception as e:
            self.error_handler.handle_import_error(str(e), format.value)
            raise

    def _import_from_ifc(self, data: Union[str, bytes, Path], options: Dict[str, Any]) -> BIMModel:
        """Import BIM model from IFC file."""
        if isinstance(data, Path):
            with open(data, 'r', encoding='utf-8') as f:
                content = f.read()
        elif isinstance(data, bytes):
            content = data.decode('utf-8')
        else:
            content = data
        
        # Parse IFC content and extract project information
        name = "Imported IFC Model"
        for line in content.splitlines():
            if line.startswith("#1=IFCPROJECT"):
                parts = line.split(",")
                if len(parts) > 2:
                    name = parts[2].replace("$", "").strip()
        
        # Create BIM model with basic structure
        model = BIMModel(name=name)
        
        # Parse IFC entities and convert to BIM elements
        # This is a simplified implementation - production would use IFC parsing libraries
        elements = self._parse_ifc_entities(content)
        for element in elements:
            model.add_element(element)
        
        return model

    def _parse_ifc_entities(self, ifc_content: str) -> List[BIMElement]:
        """Parse IFC entities and convert to BIM elements."""
        elements = []
        
        # Simplified IFC parsing - production would use proper IFC libraries
        for line in ifc_content.splitlines():
            if line.startswith("#") and "=IFC" in line:
                # Extract entity type and basic properties
                if "IFCSPACE" in line:
                    # Create room element
                    room = Room(
                        name=f"Room_{len(elements)}",
                        geometry=self._create_default_geometry(),
                        room_type="office",
                        room_number=str(len(elements) + 1)
                    )
                    elements.append(room)
                elif "IFCWALL" in line:
                    # Create wall element
                    wall = Wall(
                        name=f"Wall_{len(elements)}",
                        geometry=self._create_default_geometry(),
                        wall_type="interior",
                        thickness=0.2,
                        height=3.0
                    )
                    elements.append(wall)
                elif "IFCDISTRIBUTIONELEMENT" in line:
                    # Create device element
                    device = Device(
                        name=f"Device_{len(elements)}",
                        geometry=self._create_default_geometry(),
                        device_type="hvac",
                        manufacturer="Unknown",
                        model="Unknown"
                    )
                    elements.append(device)
        
        return elements

    def _create_default_geometry(self) -> Geometry:
        """Create default geometry for imported elements."""
        return Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
            properties={}
        )

    def _import_from_revit(self, data: Union[str, bytes, Path], format: ImportFormat, options: Dict[str, Any]) -> BIMModel:
        """Import BIM model from Revit RVT/RFA file."""
        if isinstance(data, Path):
            with open(data, 'r', encoding='utf-8') as f:
                content = f.read()
        elif isinstance(data, bytes):
            content = data.decode('utf-8')
        else:
            content = data
        
        # Try XML first
        try:
            root = ET.fromstring(content)
            name = root.attrib.get('name', 'Imported Revit Model')
            model = BIMModel(name=name)
            
            # Parse Revit XML elements
            elements = self._parse_revit_xml(root)
            for element in elements:
                model.add_element(element)
            
            return model
        except ET.ParseError:
            # Try JSON
            try:
                obj = json.loads(content)
                name = obj.get('name', 'Imported Revit Model')
                model = BIMModel(name=name)
                
                # Parse Revit JSON elements
                elements = self._parse_revit_json(obj)
                for element in elements:
                    model.add_element(element)
                
                return model
            except Exception:
                raise ImportError("Unsupported Revit file format")

    def _parse_revit_xml(self, root: ET.Element) -> List[BIMElement]:
        """Parse Revit XML elements."""
        elements = []
        
        for elem in root.findall(".//Element"):
            elem_id = elem.get('id', f"element_{len(elements)}")
            elem_type = elem.get('type', 'unknown')
            name = elem.find('Name')
            name_text = name.text if name is not None else f"{elem_type}_{len(elements)}"
            
            # Create BIM element based on type
            if elem_type.lower() in ['room', 'space']:
                element = Room(
                    name=name_text,
                    geometry=self._create_default_geometry(),
                    room_type="office",
                    room_number=str(len(elements) + 1)
                )
            elif elem_type.lower() in ['wall', 'partition']:
                element = Wall(
                    name=name_text,
                    geometry=self._create_default_geometry(),
                    wall_type="interior",
                    thickness=0.2,
                    height=3.0
                )
            else:
                element = BIMElement(
                    id=elem_id,
                    name=name_text,
                    element_type=elem_type,
                    geometry=self._create_default_geometry(),
                    properties={}
                )
            
            elements.append(element)
        
        return elements

    def _parse_revit_json(self, data: Dict[str, Any]) -> List[BIMElement]:
        """Parse Revit JSON elements."""
        elements = []
        
        # Simplified JSON parsing
        for item in data.get('elements', []):
            elem_id = item.get('id', f"element_{len(elements)}")
            elem_type = item.get('type', 'unknown')
            name = item.get('name', f"{elem_type}_{len(elements)}")
            
            # Create BIM element based on type
            if elem_type.lower() in ['room', 'space']:
                element = Room(
                    name=name,
                    geometry=self._create_default_geometry(),
                    room_type="office",
                    room_number=str(len(elements) + 1)
                )
            elif elem_type.lower() in ['wall', 'partition']:
                element = Wall(
                    name=name,
                    geometry=self._create_default_geometry(),
                    wall_type="interior",
                    thickness=0.2,
                    height=3.0
                )
            else:
                element = BIMElement(
                    id=elem_id,
                    name=name,
                    element_type=elem_type,
                    geometry=self._create_default_geometry(),
                    properties={}
                )
            
            elements.append(element)
        
        return elements

    def _import_from_json(self, data: Union[str, bytes, Path], options: Dict[str, Any]) -> BIMModel:
        """Import BIM model from JSON schema."""
        if isinstance(data, Path):
            with open(data, 'r', encoding='utf-8') as f:
                obj = json.load(f)
        elif isinstance(data, bytes):
            obj = json.loads(data.decode('utf-8'))
        else:
            obj = json.loads(data)
        
        # Extract model information from JSON
        model_data = obj.get('bim_model', {})
        name = model_data.get('name', 'Imported JSON Model')
        description = model_data.get('description')
        metadata = model_data.get('metadata', {})
        
        # Create BIM model
        model = BIMModel(
            name=name,
            description=description,
            metadata=metadata
        )
        
        # Parse elements from JSON
        elements = self._parse_json_elements(model_data.get('elements', []))
        for element in elements:
            model.add_element(element)
        
        return model

    def _parse_json_elements(self, elements_data: List[Dict[str, Any]]) -> List[BIMElement]:
        """Parse JSON elements into BIM elements."""
        elements = []
        
        for elem_data in elements_data:
            elem_id = elem_data.get('id', f"element_{len(elements)}")
            name = elem_data.get('name', f"element_{len(elements)}")
            elem_type = elem_data.get('element_type', 'unknown')
            properties = elem_data.get('properties', {})
            
            # Create geometry from JSON data
            geometry_data = elem_data.get('geometry', {})
            geometry = self._create_geometry_from_json(geometry_data)
            
            # Create BIM element based on type
            if elem_type == 'room':
                element = Room(
                    name=name,
                    geometry=geometry,
                    room_type=properties.get('room_type', 'office'),
                    room_number=properties.get('room_number', str(len(elements) + 1)),
                    area=properties.get('area', 0.0)
                )
            elif elem_type == 'wall':
                element = Wall(
                    name=name,
                    geometry=geometry,
                    wall_type=properties.get('wall_type', 'interior'),
                    thickness=properties.get('thickness', 0.2),
                    height=properties.get('height', 3.0)
                )
            elif elem_type == 'device':
                element = Device(
                    name=name,
                    geometry=geometry,
                    device_type=properties.get('device_type', 'unknown'),
                    manufacturer=properties.get('manufacturer', ''),
                    model=properties.get('model', '')
                )
            else:
                element = BIMElement(
                    id=elem_id,
                    name=name,
                    element_type=elem_type,
                    geometry=geometry,
                    properties=properties
                )
            
            elements.append(element)
        
        return elements

    def _create_geometry_from_json(self, geometry_data: Dict[str, Any]) -> Geometry:
        """Create geometry from JSON data."""
        geom_type = geometry_data.get('type', 'POLYGON')
        coordinates = geometry_data.get('coordinates', [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]])
        properties = geometry_data.get('properties', {})
        
        return Geometry(
            type=GeometryType(geom_type.lower()),
            coordinates=coordinates,
            properties=properties
        )

    def _import_from_xml(self, data: Union[str, bytes, Path], options: Dict[str, Any]) -> BIMModel:
        """Import BIM model from XML schema."""
        if isinstance(data, Path):
            with open(data, 'r', encoding='utf-8') as f:
                content = f.read()
        elif isinstance(data, bytes):
            content = data.decode('utf-8')
        else:
            content = data
        
        root = ET.fromstring(content)
        name = root.attrib.get('name', 'Imported XML Model')
        model = BIMModel(name=name)
        
        # Parse XML elements
        elements = self._parse_xml_elements(root)
        for element in elements:
            model.add_element(element)
        
        return model

    def _parse_xml_elements(self, root: ET.Element) -> List[BIMElement]:
        """Parse XML elements into BIM elements."""
        elements = []
        
        for elem in root.findall(".//Element"):
            elem_id = elem.get('id', f"element_{len(elements)}")
            elem_type = elem.get('type', 'unknown')
            name_elem = elem.find('Name')
            name = name_elem.text if name_elem is not None else f"{elem_type}_{len(elements)}"
            
            # Parse properties
            properties = {}
            props_elem = elem.find('Properties')
            if props_elem is not None:
                for prop in props_elem.findall('Property'):
                    prop_name = prop.get('name', '')
                    prop_value = prop.text or ''
                    properties[prop_name] = prop_value
            
            # Create geometry
            geometry = self._create_default_geometry()
            geom_elem = elem.find('Geometry')
            if geom_elem is not None:
                geom_type = geom_elem.get('type', 'POLYGON')
                coords_elem = geom_elem.find('Coordinates')
                if coords_elem is not None:
                    # Parse coordinates (simplified)
                    geometry = self._create_default_geometry()
            
            # Create BIM element based on type
            if elem_type == 'room':
                element = Room(
                    name=name,
                    geometry=geometry,
                    room_type=properties.get('room_type', 'office'),
                    room_number=properties.get('room_number', str(len(elements) + 1))
                )
            elif elem_type == 'wall':
                element = Wall(
                    name=name,
                    geometry=geometry,
                    wall_type=properties.get('wall_type', 'interior'),
                    thickness=float(properties.get('thickness', 0.2)),
                    height=float(properties.get('height', 3.0))
                )
            else:
                element = BIMElement(
                    id=elem_id,
                    name=name,
                    element_type=elem_type,
                    geometry=geometry,
                    properties=properties
                )
            
            elements.append(element)
        
        return elements

    def _import_from_gbxml(self, data: Union[str, bytes, Path], options: Dict[str, Any]) -> BIMModel:
        """Import BIM model from gbXML format."""
        if isinstance(data, Path):
            with open(data, 'r', encoding='utf-8') as f:
                content = f.read()
        elif isinstance(data, bytes):
            content = data.decode('utf-8')
        else:
            content = data
        
        root = ET.fromstring(content)
        name = root.attrib.get('buildingName', 'Imported gbXML Model')
        model = BIMModel(name=name)
        
        # Parse gbXML elements
        elements = self._parse_gbxml_elements(root)
        for element in elements:
            model.add_element(element)
        
        return model

    def _parse_gbxml_elements(self, root: ET.Element) -> List[BIMElement]:
        """Parse gbXML elements into BIM elements."""
        elements = []
        
        # Parse spaces (rooms)
        for space in root.findall(".//Space"):
            space_id = space.get('id', f"space_{len(elements)}")
            name = space.get('name', f"Space_{len(elements)}")
            
            element = Room(
                name=name,
                geometry=self._create_default_geometry(),
                room_type="office",
                room_number=str(len(elements) + 1)
            )
            elements.append(element)
        
        return elements

    def _import_from_gltf(self, data: Union[str, bytes, Path], options: Dict[str, Any]) -> BIMModel:
        """Import BIM model from glTF format."""
        if isinstance(data, Path):
            with open(data, 'r', encoding='utf-8') as f:
                obj = json.load(f)
        elif isinstance(data, bytes):
            obj = json.loads(data.decode('utf-8'))
        else:
            obj = json.loads(data)
        
        name = obj.get('asset', {}).get('generator', 'Imported glTF Model')
        model = BIMModel(name=name)
        
        # Parse glTF elements
        elements = self._parse_gltf_elements(obj)
        for element in elements:
            model.add_element(element)
        
        return model

    def _parse_gltf_elements(self, data: Dict[str, Any]) -> List[BIMElement]:
        """Parse glTF elements into BIM elements."""
        elements = []
        
        # Simplified glTF parsing
        nodes = data.get('nodes', [])
        for i, node in enumerate(nodes):
            name = node.get('name', f"Node_{i}")
            
            element = BIMElement(
                id=f"gltf_element_{i}",
                name=name,
                element_type="unknown",
                geometry=self._create_default_geometry(),
                properties={}
            )
            elements.append(element)
        
        return elements

    def validate_import(self, model: BIMModel) -> bool:
        """Validate imported BIM model."""
        # Basic validation: must have a name
        if not model.name:
            self.error_handler.handle_import_error("Model missing name", "validation")
            return False
        
        # Validate elements have required properties
        for element in model.elements:
            if not element.name:
                self.error_handler.handle_import_error(f"Element missing name: {element.id}", "validation")
                return False
        
        # Additional validation rules can be added here
        return True 