import logging
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET
from uuid import uuid4
from datetime import datetime
import math

logger = logging.getLogger(__name__)

class SymbolRenderer:
    """Renders recognized symbols into dynamic SVG-BIM elements."""
    
    def __init__(self):
        self.svg_namespace = "http://www.w3.org/2000/svg"
        self.arx_namespace = "http://arxos.io/svg"
        
    def render_recognized_symbols(self, svg_content: str, recognized_symbols: List[Dict[str, Any]], 
                                building_id: str, floor_label: str) -> Dict[str, Any]:
        """
        Render recognized symbols into the SVG-BIM.
        
        Args:
            svg_content: Original SVG content
            recognized_symbols: List of recognized symbols from recognition engine
            building_id: Building identifier
            floor_label: Floor label
            
        Returns:
            Dict containing updated SVG and metadata
        """
        try:
            root = ET.fromstring(svg_content)
            
            # Create or find the arx-objects group
            arx_group = self._get_or_create_arx_group(root)
            
            # Track rendered symbols
            rendered_symbols = []
            
            # Render each recognized symbol
            for symbol_info in recognized_symbols:
                if symbol_info['confidence'] >= 0.5:  # Only render high-confidence matches
                    rendered_symbol = self._render_single_symbol(
                        arx_group, symbol_info, building_id, floor_label
                    )
                    if rendered_symbol:
                        rendered_symbols.append(rendered_symbol)
            
            # Convert back to string
            updated_svg = ET.tostring(root, encoding='unicode')
            
            return {
                'svg': updated_svg,
                'rendered_symbols': rendered_symbols,
                'total_recognized': len(recognized_symbols),
                'total_rendered': len(rendered_symbols),
                'building_id': building_id,
                'floor_label': floor_label
            }
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse SVG for rendering: {e}")
            return {
                'svg': svg_content,
                'error': f"SVG parsing failed: {str(e)}",
                'rendered_symbols': []
            }
    
    def _get_or_create_arx_group(self, root: ET.Element) -> ET.Element:
        """Get or create the arx-objects group in the SVG."""
        # Look for existing arx-objects group
        for group in root.findall(f'.//{{{self.svg_namespace}}}g'):
            if group.get('id') == 'arx-objects':
                return group
        
        # Create new arx-objects group
        arx_group = ET.Element(f'{{{self.svg_namespace}}}g', {
            'id': 'arx-objects',
            'class': 'arx-dynamic-objects'
        })
        root.append(arx_group)
        return arx_group
    
    def _render_single_symbol(self, arx_group: ET.Element, symbol_info: Dict[str, Any], 
                            building_id: str, floor_label: str) -> Optional[Dict[str, Any]]:
        """Render a single recognized symbol."""
        try:
            symbol_id = symbol_info['symbol_id']
            symbol_data = symbol_info['symbol_data']
            confidence = symbol_info['confidence']
            match_type = symbol_info['match_type']
            
            # Generate unique object ID
            object_id = f"{symbol_id}_{uuid4().hex[:8]}"
            
            # Determine position
            position = self._determine_symbol_position(symbol_info, arx_group)
            
            # Create the symbol element
            symbol_element = self._create_symbol_element(
                symbol_id, symbol_data, object_id, position, confidence, match_type
            )
            
            # Add to arx-group
            arx_group.append(symbol_element)
            
            # Create metadata
            metadata = {
                'object_id': object_id,
                'symbol_id': symbol_id,
                'symbol_name': symbol_data.get('display_name', symbol_id),
                'system': symbol_data.get('system', 'unknown'),
                'category': symbol_data.get('category', ''),
                'position': position,
                'confidence': confidence,
                'match_type': match_type,
                'rendered_at': datetime.utcnow().isoformat(),
                'building_id': building_id,
                'floor_label': floor_label,
                'properties': symbol_data.get('properties', []),
                'connections': symbol_data.get('connections', []),
                'tags': symbol_data.get('tags', [])
            }
            
            logger.info(f"Rendered symbol {symbol_id} at position {position}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to render symbol {symbol_info.get('symbol_id', 'unknown')}: {e}")
            return None
    
    def _determine_symbol_position(self, symbol_info: Dict[str, Any], arx_group: ET.Element) -> Dict[str, float]:
        """Determine the position for a symbol based on recognition context."""
        position = {'x': 0, 'y': 0}
        
        # If we have a position from SVG text recognition, use it
        if 'position' in symbol_info:
            position = symbol_info['position']
        else:
            # Calculate position based on existing symbols
            position = self._calculate_auto_position(arx_group, symbol_info)
        
        return position
    
    def _calculate_auto_position(self, arx_group: ET.Element, symbol_info: Dict[str, Any]) -> Dict[str, float]:
        """Calculate automatic position for a symbol."""
        # Get existing symbol positions
        existing_positions = []
        for elem in arx_group.findall(f'.//{{{self.svg_namespace}}}g'):
            transform = elem.get('transform', '')
            if 'translate(' in transform:
                # Extract position from transform
                try:
                    # Parse translate(x,y) from transform
                    import re
                    match = re.search(r'translate\(([^,]+),([^)]+)\)', transform)
                    if match:
                        x = float(match.group(1))
                        y = float(match.group(2))
                        existing_positions.append((x, y))
                except (ValueError, AttributeError):
                    pass
        
        # Calculate new position
        if existing_positions:
            # Find a position that doesn't overlap
            base_x, base_y = existing_positions[-1]  # Start from last position
            offset = 50  # 50 units offset
            
            # Try positions in a grid pattern
            for i in range(10):  # Try 10 different positions
                x = base_x + (i % 3) * offset
                y = base_y + (i // 3) * offset
                
                # Check if position is far enough from existing symbols
                if not any(math.sqrt((x-ex_x)**2 + (y-ex_y)**2) < 30 for ex_x, ex_y in existing_positions):
                    return {'x': x, 'y': y}
            
            # If no good position found, just offset from last
            last_x, last_y = existing_positions[-1]
            return {'x': last_x + offset, 'y': last_y + offset}
        else:
            # First symbol - place at origin
            return {'x': 100, 'y': 100}
    
    def _create_symbol_element(self, symbol_id: str, symbol_data: Dict[str, Any], 
                             object_id: str, position: Dict[str, float], 
                             confidence: float, match_type: str) -> ET.Element:
        """Create the SVG element for a symbol."""
        # Get the symbol's SVG content
        symbol_svg = symbol_data.get('svg', '')
        
        # Create the main group element
        group_attrs = {
            'id': object_id,
            'class': f'arx-symbol arx-{symbol_id}',
            'transform': f'translate({position["x"]},{position["y"]})',
            'data-symbol-id': symbol_id,
            'data-symbol-name': symbol_data.get('display_name', symbol_id),
            'data-system': symbol_data.get('system', 'unknown'),
            'data-category': symbol_data.get('category', ''),
            'data-confidence': str(confidence),
            'data-match-type': match_type,
            'data-rendered-at': datetime.utcnow().isoformat()
        }
        
        group = ET.Element(f'{{{self.svg_namespace}}}g', group_attrs)
        
        # Add the symbol SVG content
        if symbol_svg:
            try:
                symbol_root = ET.fromstring(symbol_svg)
                # Copy all child elements
                for child in symbol_root:
                    group.append(child)
            except ET.ParseError:
                # Fallback: add as text
                text_elem = ET.Element(f'{{{self.svg_namespace}}}text', {
                    'x': '0', 'y': '0',
                    'font-size': '12',
                    'text-anchor': 'middle'
                })
                text_elem.text = symbol_data.get('display_name', symbol_id)
                group.append(text_elem)
        
        # Add confidence indicator
        if confidence < 0.8:
            confidence_indicator = ET.Element(f'{{{self.svg_namespace}}}circle', {
                'cx': '0', 'cy': '0', 'r': '15',
                'fill': 'none',
                'stroke': '#ff6b6b' if confidence < 0.6 else '#ffd93d',
                'stroke-width': '2',
                'stroke-dasharray': '5,5',
                'opacity': '0.7'
            })
            group.append(confidence_indicator)
        
        # Add metadata text
        metadata_text = ET.Element(f'{{{self.svg_namespace}}}text', {
            'x': '0', 'y': '25',
            'font-size': '8',
            'text-anchor': 'middle',
            'fill': '#666',
            'class': 'arx-metadata'
        })
        metadata_text.text = f"{symbol_data.get('display_name', symbol_id)} ({confidence:.1f})"
        group.append(metadata_text)
        
        return group
    
    def update_symbol_position(self, svg_content: str, object_id: str, 
                             new_position: Dict[str, float]) -> str:
        """Update the position of an existing symbol."""
        try:
            root = ET.fromstring(svg_content)
            
            # Find the symbol element
            symbol_elem = root.find(f'.//*[@id="{object_id}"]')
            if symbol_elem is not None:
                # Update transform
                symbol_elem.set('transform', f'translate({new_position["x"]},{new_position["y"]})')
                
                # Update metadata
                symbol_elem.set('data-updated-at', datetime.utcnow().isoformat())
            
            return ET.tostring(root, encoding='unicode')
            
        except ET.ParseError as e:
            logger.error(f"Failed to update symbol position: {e}")
            return svg_content
    
    def remove_symbol(self, svg_content: str, object_id: str) -> str:
        """Remove a symbol from the SVG."""
        try:
            root = ET.fromstring(svg_content)
            
            # Find and remove the symbol element
            symbol_elem = root.find(f'.//*[@id="{object_id}"]')
            if symbol_elem is not None:
                # Find parent by searching through all elements
                for parent in root.iter():
                    if symbol_elem in list(parent):
                        parent.remove(symbol_elem)
                        break
            
            return ET.tostring(root, encoding='unicode')
            
        except ET.ParseError as e:
            logger.error(f"Failed to remove symbol: {e}")
            return svg_content
    
    def get_rendered_symbols(self, svg_content: str) -> List[Dict[str, Any]]:
        """Extract metadata from rendered symbols in SVG."""
        symbols = []
        
        try:
            root = ET.fromstring(svg_content)
            
            for group in root.findall(f'.//{{{self.svg_namespace}}}g'):
                if group.get('class', '').startswith('arx-symbol'):
                    symbol_data = {
                        'object_id': group.get('id'),
                        'symbol_id': group.get('data-symbol-id'),
                        'symbol_name': group.get('data-symbol-name'),
                        'system': group.get('data-system'),
                        'category': group.get('data-category'),
                        'confidence': float(group.get('data-confidence', 0)),
                        'match_type': group.get('data-match-type'),
                        'rendered_at': group.get('data-rendered-at')
                    }
                    
                    # Extract position from transform
                    transform = group.get('transform', '')
                    if 'translate(' in transform:
                        import re
                        match = re.search(r'translate\(([^,]+),([^)]+)\)', transform)
                        if match:
                            symbol_data['position'] = {
                                'x': float(match.group(1)),
                                'y': float(match.group(2))
                            }
                    
                    symbols.append(symbol_data)
            
        except ET.ParseError as e:
            logger.error(f"Failed to extract rendered symbols: {e}")
        
        return symbols 