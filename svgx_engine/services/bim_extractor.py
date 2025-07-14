"""
SVGX BIM Extractor Service

This module provides comprehensive BIM element extraction from SVGX content including:
- SVGX namespace-aware element classification
- Enhanced geometry extraction for SVGX elements
- Multi-system element recognition (Electrical, Plumbing, Fire Alarm, etc.)
- SVGX-specific metadata extraction
- Advanced pattern matching for element identification
- Comprehensive logging and error handling
"""

import structlog
from typing import List, Dict, Any, Tuple, Optional, Union
from lxml import etree as ET
import re
from dataclasses import dataclass
from enum import Enum

from ..utils.errors import ParserError, ValidationError
from ..models.system_elements import (
    ExtractionResponse, SystemElement, ElectricalElement, 
    FireAlarmElement, PlumbingElement
)

logger = structlog.get_logger(__name__)


class SVGXElementType(Enum):
    """SVGX element types for enhanced classification."""
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FIRE_ALARM = "fire_alarm"
    HVAC = "hvac"
    SECURITY = "security"
    AV = "av"
    NETWORK = "network"
    STRUCTURAL = "structural"
    UNKNOWN = "unknown"


class SVGXGeometryType(Enum):
    """SVGX geometry types for enhanced extraction."""
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    LINE = "line"
    POLYGON = "polygon"
    POLYLINE = "polyline"
    PATH = "path"
    TEXT = "text"
    GROUP = "group"
    UNKNOWN = "unknown"


@dataclass
class SVGXElementMetadata:
    """Enhanced metadata for SVGX elements."""
    namespace: str = ""
    component_type: str = ""
    properties: Dict[str, Any] = None
    attributes: Dict[str, str] = None
    parent_id: Optional[str] = None
    layer: Optional[str] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.attributes is None:
            self.attributes = {}


class SVGXBIMExtractor:
    """Advanced BIM extractor with SVGX-specific enhancements."""
    
    def __init__(self):
        # Enhanced system mappings for SVGX
        self.group_to_system = {
            'electrical': 'E', 'power': 'E', 'lighting': 'E', 'elec': 'E',
            'plumb': 'P', 'plumbing': 'P', 'water': 'P', 'sanitary': 'P',
            'fire': 'FA', 'alarm': 'FA', 'fire_alarm': 'FA', 'safety': 'FA',
            'lowvolt': 'LV', 'lv': 'LV', 'low_voltage': 'LV',
            'network': 'N', 'data': 'N', 'telecom': 'N', 'communication': 'N',
            'mech': 'M', 'hvac': 'M', 'mechanical': 'M', 'air': 'M',
            'security': 'Security', 'cctv': 'Security', 'access': 'Security',
            'controls': 'BAS', 'bms': 'BAS', 'building_automation': 'BAS',
            'av': 'AV', 'audio': 'AV', 'video': 'AV', 'audiovisual': 'AV',
            'structural': 'Structural', 'structure': 'Structural',
            'svgx': 'SVGX', 'svgx_core': 'SVGX', 'svgx_physics': 'SVGX',
            'svgx_behavior': 'SVGX', 'svgx_runtime': 'SVGX'
        }

        # Enhanced patterns for SVGX element type detection
        self.label_patterns = {
            # Electrical patterns
            'outlet': re.compile(r'outlet|receptacle|GFCI|duplex|quad', re.I),
            'panel': re.compile(r'panel|transformer|switchgear|MDP|SDP', re.I),
            'switch': re.compile(r'switch|toggle|dimmer|control', re.I),
            'light': re.compile(r'light|fixture|lamp|LED|fluorescent', re.I),
            'breaker': re.compile(r'breaker|CB|circuit', re.I),
            'conduit': re.compile(r'conduit|EMT|IMC|RMC', re.I),
            
            # Plumbing patterns
            'pipe': re.compile(r'pipe|CW|HW|HWR|SW|G|V|drain|vent', re.I),
            'valve': re.compile(r'valve|PRV|check|ball|gate|butterfly', re.I),
            'faucet': re.compile(r'faucet|sink|fixture|trap', re.I),
            'drain': re.compile(r'drain|cleanout|floor_drain', re.I),
            'pump': re.compile(r'pump|booster|circulator', re.I),
            
            # Fire Alarm patterns
            'horn': re.compile(r'horn|speaker|sounder', re.I),
            'strobe': re.compile(r'strobe|light|visual', re.I),
            'pull_station': re.compile(r'pull|manual|station', re.I),
            'smoke': re.compile(r'smoke|SD|detector', re.I),
            'heat': re.compile(r'heat|HD|thermal', re.I),
            'panel': re.compile(r'panel|FACP|fire_panel', re.I),
            
            # Security patterns
            'camera': re.compile(r'CCTV|camera|PTZ|dome|bullet', re.I),
            'sensor': re.compile(r'sensor|motion|PIR|door|window', re.I),
            'controller': re.compile(r'controller|DVR|NVR|recorder', re.I),
            'card_reader': re.compile(r'reader|card|access', re.I),
            
            # AV patterns
            'display': re.compile(r'display|projector|screen|monitor', re.I),
            'speaker': re.compile(r'speaker|SPKR|audio|sound', re.I),
            'mic': re.compile(r'mic|microphone|audio_in', re.I),
            'amplifier': re.compile(r'amp|amplifier|power', re.I),
            
            # Network patterns
            'ap': re.compile(r'AP|WAP|access_point|wireless', re.I),
            'rack': re.compile(r'rack|switch|router|server', re.I),
            'jack': re.compile(r'jack|outlet|data|voice', re.I),
            'fiber': re.compile(r'fiber|optic|FO', re.I),
            
            # HVAC patterns
            'duct': re.compile(r'duct|air|supply|return', re.I),
            'diffuser': re.compile(r'diffuser|grille|register', re.I),
            'ahu': re.compile(r'AHU|air_handler|unit', re.I),
            'vav': re.compile(r'VAV|variable|air|volume', re.I),
            
            # SVGX-specific patterns
            'svgx_element': re.compile(r'svgx|physics|behavior|runtime', re.I),
            'component': re.compile(r'component|element|object', re.I),
            'interactive': re.compile(r'interactive|click|hover', re.I),
            'animated': re.compile(r'animated|motion|transition', re.I)
        }

    def extract_svgx_namespace(self, elem: ET._Element) -> str:
        """Extract SVGX namespace from element, prioritizing 'svgx-namespace'."""
        if elem is None:
            return ""
        # Check for 'svgx-namespace' in element attributes
        if 'svgx-namespace' in elem.attrib:
            return elem.attrib['svgx-namespace']
        # Check parent elements for 'svgx-namespace'
        parent = elem.getparent()
        while parent is not None:
            if 'svgx-namespace' in parent.attrib:
                return parent.attrib['svgx-namespace']
            parent = parent.getparent()
        # Fallback: any attribute containing 'svgx' in name or value
        for attr, value in elem.attrib.items():
            if 'svgx' in attr.lower() or 'svgx' in value.lower():
                return value
        parent = elem.getparent()
        while parent is not None:
            for attr, value in parent.attrib.items():
                if 'svgx' in attr.lower() or 'svgx' in value.lower():
                    return value
            parent = parent.getparent()
        return ""

    def classify_svgx_system_and_type(self, elem: ET._Element, parent: ET._Element, 
                                     label: str, namespace: str) -> Tuple[str, str]:
        """Enhanced classification for SVGX elements."""
        # Default system/type
        system = 'Structural'
        type_ = 'unknown'
        
        # Check SVGX namespace first
        if namespace and 'svgx' in namespace.lower():
            system = 'SVGX'
            type_ = 'svgx_element'
        
        # Use parent group id if available
        if parent is not None and parent.tag.endswith('g'):
            group_id = parent.get('id', '').lower()
            for key, sys in self.group_to_system.items():
                if key in group_id:
                    system = sys
                    break
        
        # Use label patterns to refine type
        if label:
            for t, pat in self.label_patterns.items():
                if pat.search(label):
                    type_ = t
                    break
        
        return system, type_

    def extract_svgx_geometry(self, elem: ET._Element) -> Tuple[Tuple[float, float], SVGXGeometryType]:
        """Enhanced geometry extraction for SVGX elements."""
        tag = ET.QName(elem).localname
        coords = (0.0, 0.0)
        geometry_type = SVGXGeometryType.UNKNOWN
        
        try:
            if tag == 'circle':
                cx = float(elem.get('cx', '0'))
                cy = float(elem.get('cy', '0'))
                coords = (cx, cy)
                geometry_type = SVGXGeometryType.CIRCLE
                
            elif tag == 'rect':
                x = float(elem.get('x', '0'))
                y = float(elem.get('y', '0'))
                coords = (x, y)
                geometry_type = SVGXGeometryType.RECTANGLE
                
            elif tag == 'ellipse':
                cx = float(elem.get('cx', '0'))
                cy = float(elem.get('cy', '0'))
                coords = (cx, cy)
                geometry_type = SVGXGeometryType.ELLIPSE
                
            elif tag == 'line':
                x1 = float(elem.get('x1', '0'))
                y1 = float(elem.get('y1', '0'))
                coords = (x1, y1)
                geometry_type = SVGXGeometryType.LINE
                
            elif tag in ['polygon', 'polyline']:
                points = elem.get('points', '').strip().split()
                if points:
                    x, y = map(float, points[0].split(','))
                    coords = (x, y)
                geometry_type = SVGXGeometryType.POLYGON if tag == 'polygon' else SVGXGeometryType.POLYLINE
                
            elif tag == 'path':
                # Enhanced path parsing for SVGX
                d = elem.get('d', '')
                m = re.search(r'M\s*([\d.]+)[, ]+([\d.]+)', d)
                if m:
                    coords = (float(m.group(1)), float(m.group(2)))
                geometry_type = SVGXGeometryType.PATH
                
            elif tag == 'text':
                x = float(elem.get('x', '0'))
                y = float(elem.get('y', '0'))
                coords = (x, y)
                geometry_type = SVGXGeometryType.TEXT
                
            elif tag == 'g':
                # For groups, try to find the first child with coordinates
                for child in elem.iterchildren():
                    child_coords, child_geom = self.extract_svgx_geometry(child)
                    if child_coords != (0.0, 0.0):
                        coords = child_coords
                        geometry_type = SVGXGeometryType.GROUP
                        break
                        
        except (ValueError, TypeError) as e:
            logger.warning(f"Geometry extraction failed for element {elem.get('id', 'unknown')}: {e}")
            coords = (0.0, 0.0)
            geometry_type = SVGXGeometryType.UNKNOWN
        
        return coords, geometry_type

    def extract_svgx_metadata(self, elem: ET._Element, namespace: str) -> SVGXElementMetadata:
        """Extract enhanced metadata for SVGX elements."""
        if elem is None:
            return SVGXElementMetadata(namespace=namespace)
            
        component_type = elem.get('svgx-component', elem.get('class', ''))
        metadata = SVGXElementMetadata(
            namespace=namespace,
            component_type=component_type,
            parent_id=elem.getparent().get('id') if elem.getparent() is not None else None,
            layer=elem.get('data-layer', ''),
            attributes=dict(elem.attrib),
            properties={}
        )
        
        # Extract SVGX-specific properties
        for attr, value in elem.attrib.items():
            if attr.startswith('data-'):
                prop_name = attr[5:]  # Remove 'data-' prefix
                metadata.properties[prop_name] = value
            elif attr.startswith('svgx-'):
                prop_name = attr[5:]  # Remove 'svgx-' prefix
                metadata.properties[prop_name] = value
        
        return metadata

    def extract_bim_from_svgx(self, svg_xml: str, building_id: str, floor_id: str) -> ExtractionResponse:
        """
        Extract BIM elements from SVGX content with enhanced SVGX support.
        
        Args:
            svg_xml: SVGX XML content as string
            building_id: Building identifier
            floor_id: Floor identifier
            
        Returns:
            ExtractionResponse: Extracted BIM elements with SVGX enhancements
        """
        logger.info("svgx_bim_extraction_started",
                   building_id=building_id,
                   floor_id=floor_id,
                   svg_length=len(svg_xml))
        
        try:
            root = ET.fromstring(svg_xml.encode('utf-8'))
            logger.debug("svgx_parsing_successful",
                        building_id=building_id,
                        floor_id=floor_id,
                        root_tag=root.tag)
        except Exception as e:
            logger.error("svgx_parsing_failed",
                        building_id=building_id,
                        floor_id=floor_id,
                        error=str(e),
                        error_type=type(e).__name__)
            raise ParserError(f"Failed to parse SVGX content: {e}")

        elements: List[SystemElement] = []
        element_count = 0
        system_counts = {}
        svgx_elements = 0
        
        for elem in root.iter():
            tag = ET.QName(elem).localname
            elem_id = elem.get('id') or f"svgx-{tag}-{len(elements)+1}"
            label = elem.get('label') or elem.get('data-label') or elem.get('class') or ''
            parent = elem.getparent()
            
            # Extract SVGX namespace and metadata
            namespace = self.extract_svgx_namespace(elem)
            metadata = self.extract_svgx_metadata(elem, namespace)
            
            # Enhanced classification
            system, type_ = self.classify_svgx_system_and_type(elem, parent, label, namespace)
            
            # Enhanced geometry extraction
            coords, geometry_type = self.extract_svgx_geometry(elem)
            
            # Track system counts
            system_counts[system] = system_counts.get(system, 0) + 1
            if system == 'SVGX':
                svgx_elements += 1
            
            # Create element based on system type
            element = self._create_system_element(
                elem_id, label, system, type_, coords, metadata, 
                building_id, floor_id
            )
            
            if element:
                elements.append(element)
                element_count += 1
                
                logger.debug("svgx_element_extracted",
                            building_id=building_id,
                            floor_id=floor_id,
                            element_id=elem_id,
                            system=system,
                            element_type=type_,
                            namespace=namespace,
                            geometry_type=geometry_type.value,
                            label=label,
                            coordinates=coords)

        logger.info("svgx_bim_extraction_completed",
                   building_id=building_id,
                   floor_id=floor_id,
                   total_elements=element_count,
                   svgx_elements=svgx_elements,
                   system_counts=system_counts)

        return ExtractionResponse(
            building_id=building_id,
            floor_id=floor_id,
            elements=elements
        )

    def _create_system_element(self, elem_id: str, label: str, system: str, 
                              type_: str, coords: Tuple[float, float], 
                              metadata: SVGXElementMetadata,
                              building_id: str, floor_id: str) -> Optional[SystemElement]:
        """Create system element with SVGX enhancements."""
        try:
            if system == 'E':
                return ElectricalElement(
                    id=elem_id,
                    label=label,
                    system='E',
                    type=type_ if type_ in ['outlet', 'panel', 'switch', 'light'] else 'outlet',
                    coordinates=coords,
                    metadata={
                        'svgx_namespace': metadata.namespace,
                        'svgx_component_type': metadata.component_type,
                        'svgx_properties': metadata.properties,
                        'svgx_geometry_type': metadata.properties.get('geometry_type', 'unknown')
                    }
                )
                
            elif system == 'P':
                return PlumbingElement(
                    id=elem_id,
                    label=label,
                    system='P',
                    type=type_ if type_ in ['pipe', 'valve', 'faucet', 'drain'] else 'pipe',
                    coordinates=coords,
                    metadata={
                        'svgx_namespace': metadata.namespace,
                        'svgx_component_type': metadata.component_type,
                        'svgx_properties': metadata.properties,
                        'svgx_geometry_type': metadata.properties.get('geometry_type', 'unknown')
                    }
                )
                
            elif system == 'FA':
                return FireAlarmElement(
                    id=elem_id,
                    label=label,
                    system='FA',
                    type=type_ if type_ in ['horn', 'strobe', 'pull_station', 'panel'] else 'horn',
                    coordinates=coords,
                    metadata={
                        'svgx_namespace': metadata.namespace,
                        'svgx_component_type': metadata.component_type,
                        'svgx_properties': metadata.properties,
                        'svgx_geometry_type': metadata.properties.get('geometry_type', 'unknown')
                    }
                )
                
            elif system == 'SVGX':
                # Special handling for SVGX elements
                return SystemElement(
                    id=elem_id,
                    label=label,
                    system='Structural',  # Map SVGX to Structural for compatibility
                    type=f"svgx_{type_}",
                    coordinates=coords,
                    metadata={
                        'svgx_namespace': metadata.namespace,
                        'svgx_component_type': metadata.component_type,
                        'svgx_properties': metadata.properties,
                        'svgx_geometry_type': metadata.properties.get('geometry_type', 'unknown'),
                        'original_system': 'SVGX'
                    }
                )
                
            else:
                return SystemElement(
                    id=elem_id,
                    label=label,
                    system=system,
                    type=type_,
                    coordinates=coords,
                    metadata={
                        'svgx_namespace': metadata.namespace,
                        'svgx_component_type': metadata.component_type,
                        'svgx_properties': metadata.properties,
                        'svgx_geometry_type': metadata.properties.get('geometry_type', 'unknown')
                    }
                )
                
        except Exception as e:
            logger.error("element_creation_failed",
                        building_id=building_id,
                        floor_id=floor_id,
                        element_id=elem_id,
                        system=system,
                        error=str(e))
            return None


# Convenience function for backward compatibility
def extract_bim_from_svg(svg_xml: str, building_id: str, floor_id: str) -> ExtractionResponse:
    """
    Extract BIM elements from SVG content (backward compatibility).
    
    Args:
        svg_xml: SVG XML content as string
        building_id: Building identifier
        floor_id: Floor identifier
        
    Returns:
        ExtractionResponse: Extracted BIM elements
    """
    extractor = SVGXBIMExtractor()
    return extractor.extract_bim_from_svgx(svg_xml, building_id, floor_id) 