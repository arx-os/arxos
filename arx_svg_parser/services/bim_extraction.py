"""
Enhanced service for extracting and classifying BIM data from SVG with recognized symbols.
This service processes recognized symbols and creates structured BIM data.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from arx_svg_parser.services.symbol_recognition import SymbolRecognitionEngine
from arx_svg_parser.services.symbol_renderer import SymbolRenderer

logger = logging.getLogger(__name__)

class BIMExtractor:
    """Enhanced BIM data extraction from SVG with recognized symbols."""
    
    def __init__(self):
        self.symbol_recognition = SymbolRecognitionEngine()
        self.symbol_renderer = SymbolRenderer()
        
    def extract_bim_from_svg(self, svg_content: str, building_id: str = None, floor_label: str = None) -> Dict[str, Any]:
        """
        Extract comprehensive BIM data from SVG content with recognized symbols.
        
        Args:
            svg_content: SVG content with recognized symbols
            building_id: Building identifier
            floor_label: Floor label
            
        Returns:
            Structured BIM data with rooms, devices, systems, and relationships
        """
        try:
            # Extract rendered symbols from SVG
            rendered_symbols = self.symbol_renderer.get_rendered_symbols(svg_content)
            
            # Extract text content for additional analysis
            text_content = self._extract_text_from_svg(svg_content)
            
            # Recognize additional symbols from text
            additional_symbols = self.symbol_recognition.recognize_symbols_in_content(
                text_content, content_type='text'
            )
            
            # Build comprehensive BIM structure
            bim_data = {
                'metadata': self._build_metadata(building_id, floor_label),
                'rooms': self._extract_rooms(text_content, rendered_symbols),
                'devices': self._extract_devices(rendered_symbols, additional_symbols),
                'systems': self._extract_systems(rendered_symbols, additional_symbols),
                'connections': self._extract_connections(rendered_symbols),
                'relationships': self._build_relationships(rendered_symbols),
                'spatial_data': self._extract_spatial_data(rendered_symbols),
                'properties': self._extract_properties(rendered_symbols),
                'classification': self._classify_building_elements(rendered_symbols, text_content)
            }
            
            logger.info(f"Extracted BIM data: {len(bim_data['devices'])} devices, {len(bim_data['rooms'])} rooms")
            return bim_data
            
        except Exception as e:
            logger.error(f"BIM extraction failed: {e}")
            return {
                'error': f"BIM extraction failed: {str(e)}",
                'metadata': self._build_metadata(building_id, floor_label),
                'rooms': [],
                'devices': [],
                'systems': {},
                'connections': [],
                'relationships': [],
                'spatial_data': {},
                'properties': {},
                'classification': {}
            }
    
    def _build_metadata(self, building_id: str, floor_label: str) -> Dict[str, Any]:
        """Build BIM metadata."""
        return {
            'building_id': building_id or 'unknown',
            'floor_label': floor_label or 'unknown',
            'extraction_date': datetime.utcnow().isoformat(),
            'extraction_method': 'symbol_recognition',
            'version': '1.0',
            'symbol_library_version': '1.0'
        }
    
    def _extract_rooms(self, text_content: str, rendered_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract room information from text and symbols."""
        rooms = []
        
        # Extract room information from text
        room_patterns = [
            r'room\s+(\d+)', r'office\s+(\d+)', r'conference\s+room', 
            r'break\s+room', r'lobby', r'hallway', r'corridor'
        ]
        
        import re
        text_lower = text_content.lower()
        
        for pattern in room_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                room_name = match.group(0)
                room_number = match.group(1) if len(match.groups()) > 0 else None
                
                rooms.append({
                    'id': f"room_{len(rooms) + 1}",
                    'name': room_name.title(),
                    'number': room_number,
                    'type': self._classify_room_type(room_name),
                    'devices': self._find_devices_in_room(room_name, rendered_symbols),
                    'area': None,  # Would be calculated from spatial data
                    'extraction_method': 'text_pattern'
                })
        
        return rooms
    
    def _classify_room_type(self, room_name: str) -> str:
        """Classify room type based on name."""
        room_lower = room_name.lower()
        
        if 'conference' in room_lower:
            return 'conference'
        elif 'office' in room_lower:
            return 'office'
        elif 'break' in room_lower:
            return 'break_room'
        elif 'lobby' in room_lower:
            return 'lobby'
        elif 'hallway' in room_lower or 'corridor' in room_lower:
            return 'circulation'
        else:
            return 'general'
    
    def _find_devices_in_room(self, room_name: str, rendered_symbols: List[Dict[str, Any]]) -> List[str]:
        """Find devices that might be in a specific room."""
        # This is a simplified implementation
        # In a real system, this would use spatial analysis
        devices = []
        
        for symbol in rendered_symbols:
            # Simple proximity-based assignment
            if symbol.get('position'):
                devices.append(symbol['object_id'])
        
        return devices
    
    def _extract_devices(self, rendered_symbols: List[Dict[str, Any]], 
                        additional_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract device information from rendered symbols."""
        devices = []
        
        # Process rendered symbols
        for symbol in rendered_symbols:
            device = {
                'id': symbol['object_id'],
                'symbol_id': symbol['symbol_id'],
                'name': symbol['symbol_name'],
                'system': symbol['system'],
                'category': symbol['category'],
                'position': symbol.get('position', {}),
                'confidence': symbol['confidence'],
                'match_type': symbol['match_type'],
                'rendered_at': symbol['rendered_at'],
                'properties': symbol.get('properties', []),
                'connections': symbol.get('connections', []),
                'tags': symbol.get('tags', [])
            }
            devices.append(device)
        
        # Process additional recognized symbols (not yet rendered)
        for symbol in additional_symbols:
            if symbol['confidence'] >= 0.7:  # Only high-confidence matches
                device = {
                    'id': f"recognized_{symbol['symbol_id']}_{len(devices)}",
                    'symbol_id': symbol['symbol_id'],
                    'name': symbol['symbol_data']['display_name'],
                    'system': symbol['symbol_data']['system'],
                    'category': symbol['symbol_data'].get('category', ''),
                    'position': symbol.get('position', {}),
                    'confidence': symbol['confidence'],
                    'match_type': symbol['match_type'],
                    'rendered_at': None,
                    'properties': symbol['symbol_data'].get('properties', []),
                    'connections': symbol['symbol_data'].get('connections', []),
                    'tags': symbol['symbol_data'].get('tags', [])
                }
                devices.append(device)
        
        return devices
    
    def _extract_systems(self, rendered_symbols: List[Dict[str, Any]], 
                        additional_symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract building systems information."""
        systems = {
            'mechanical': {'devices': [], 'count': 0},
            'electrical': {'devices': [], 'count': 0},
            'plumbing': {'devices': [], 'count': 0},
            'fire_alarm': {'devices': [], 'count': 0},
            'security': {'devices': [], 'count': 0},
            'low_voltage': {'devices': [], 'count': 0},
            'telecommunications': {'devices': [], 'count': 0},
            'building_controls': {'devices': [], 'count': 0},
            'network': {'devices': [], 'count': 0},
            'av': {'devices': [], 'count': 0}
        }
        
        all_symbols = rendered_symbols + additional_symbols
        
        for symbol in all_symbols:
            system = symbol.get('system', 'unknown')
            if system in systems:
                device_id = symbol.get('object_id') or f"recognized_{symbol['symbol_id']}"
                systems[system]['devices'].append(device_id)
                systems[system]['count'] += 1
        
        return systems
    
    def _extract_connections(self, rendered_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract connection information between devices."""
        connections = []
        
        for symbol in rendered_symbols:
            symbol_connections = symbol.get('connections', [])
            
            for conn in symbol_connections:
                connection = {
                    'id': f"conn_{len(connections) + 1}",
                    'from_device': symbol['object_id'],
                    'to_device': None,  # Would be determined by spatial analysis
                    'connection_type': conn.get('type', 'unknown'),
                    'description': conn.get('description', ''),
                    'system': symbol['system']
                }
                connections.append(connection)
        
        return connections
    
    def _build_relationships(self, rendered_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build relationships between building elements."""
        relationships = []
        
        # Group by system
        system_groups = {}
        for symbol in rendered_symbols:
            system = symbol['system']
            if system not in system_groups:
                system_groups[system] = []
            system_groups[system].append(symbol)
        
        # Create relationships within systems
        for system, symbols in system_groups.items():
            if len(symbols) > 1:
                for i, symbol1 in enumerate(symbols):
                    for symbol2 in symbols[i+1:]:
                        relationship = {
                            'id': f"rel_{len(relationships) + 1}",
                            'type': 'system_connection',
                            'from_element': symbol1['object_id'],
                            'to_element': symbol2['object_id'],
                            'system': system,
                            'relationship_type': 'same_system'
                        }
                        relationships.append(relationship)
        
        return relationships
    
    def _extract_spatial_data(self, rendered_symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract spatial information from symbols."""
        spatial_data = {
            'bounds': self._calculate_bounds(rendered_symbols),
            'symbol_positions': {},
            'system_locations': {},
            'density_analysis': {}
        }
        
        # Extract symbol positions
        for symbol in rendered_symbols:
            if symbol.get('position'):
                spatial_data['symbol_positions'][symbol['object_id']] = symbol['position']
        
        # Group by system for spatial analysis
        system_positions = {}
        for symbol in rendered_symbols:
            system = symbol['system']
            if system not in system_positions:
                system_positions[system] = []
            if symbol.get('position'):
                system_positions[system].append(symbol['position'])
        
        spatial_data['system_locations'] = system_positions
        
        return spatial_data
    
    def _calculate_bounds(self, rendered_symbols: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate bounding box for all symbols."""
        if not rendered_symbols:
            return {'x_min': 0, 'y_min': 0, 'x_max': 0, 'y_max': 0}
        
        x_coords = []
        y_coords = []
        
        for symbol in rendered_symbols:
            if symbol.get('position'):
                x_coords.append(symbol['position']['x'])
                y_coords.append(symbol['position']['y'])
        
        if x_coords and y_coords:
            return {
                'x_min': min(x_coords),
                'y_min': min(y_coords),
                'x_max': max(x_coords),
                'y_max': max(y_coords)
            }
        else:
            return {'x_min': 0, 'y_min': 0, 'x_max': 0, 'y_max': 0}
    
    def _extract_properties(self, rendered_symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract properties from symbols."""
        properties = {
            'device_properties': {},
            'system_properties': {},
            'overall_properties': {}
        }
        
        # Extract device-specific properties
        for symbol in rendered_symbols:
            device_props = symbol.get('properties', [])
            if device_props:
                properties['device_properties'][symbol['object_id']] = device_props
        
        # Aggregate system properties
        system_props = {}
        for symbol in rendered_symbols:
            system = symbol['system']
            if system not in system_props:
                system_props[system] = []
            
            # Add unique properties for this system
            for prop in symbol.get('properties', []):
                if prop not in system_props[system]:
                    system_props[system].append(prop)
        
        properties['system_properties'] = system_props
        
        return properties
    
    def _classify_building_elements(self, rendered_symbols: List[Dict[str, Any]], 
                                  text_content: str) -> Dict[str, Any]:
        """Classify building elements by type and function."""
        classification = {
            'equipment': [],
            'distribution': [],
            'controls': [],
            'fixtures': [],
            'sensors': [],
            'panels': [],
            'other': []
        }
        
        for symbol in rendered_symbols:
            symbol_id = symbol['symbol_id']
            system = symbol['system']
            
            # Classify based on symbol type and system
            if any(keyword in symbol_id for keyword in ['ahu', 'rtu', 'fcu', 'chiller', 'boiler', 'pump']):
                classification['equipment'].append(symbol['object_id'])
            elif any(keyword in symbol_id for keyword in ['duct', 'pipe', 'conduit', 'cable']):
                classification['distribution'].append(symbol['object_id'])
            elif any(keyword in symbol_id for keyword in ['thermostat', 'controller', 'actuator']):
                classification['controls'].append(symbol['object_id'])
            elif any(keyword in symbol_id for keyword in ['sink', 'wc', 'bathtub', 'lighting']):
                classification['fixtures'].append(symbol['object_id'])
            elif any(keyword in symbol_id for keyword in ['sensor', 'detector']):
                classification['sensors'].append(symbol['object_id'])
            elif any(keyword in symbol_id for keyword in ['panel', 'pnl']):
                classification['panels'].append(symbol['object_id'])
            else:
                classification['other'].append(symbol['object_id'])
        
        return classification
    
    def _extract_text_from_svg(self, svg_content: str) -> str:
        """Extract text content from SVG."""
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(svg_content)
            text_elements = []
            
            for text_elem in root.findall('.//{http://www.w3.org/2000/svg}text'):
                text_content = text_elem.text or ''
                if text_content.strip():
                    text_elements.append(text_content)
            
            return ' '.join(text_elements)
            
        except ET.ParseError:
            return ""

# Legacy function for backward compatibility
def extract_bim_from_svg(svg_content: str):
    """
    Legacy function for extracting BIM data from SVG.
    
    Args:
        svg_content (str): The raw SVG file content as a string.

    Returns:
        dict: Structured BIM data.
    """
    extractor = BIMExtractor()
    return extractor.extract_bim_from_svg(svg_content) 