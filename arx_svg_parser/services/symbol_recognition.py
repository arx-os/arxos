import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET
from arx_svg_parser.services.svg_symbol_library import SVG_SYMBOLS, load_symbol_library
import yaml
import os

logger = logging.getLogger(__name__)

class SymbolRecognitionEngine:
    """Engine for recognizing building system symbols in uploaded content."""
    
    def __init__(self):
        self.symbol_library = self._load_complete_symbol_library()
        self.recognition_patterns = self._build_recognition_patterns()
        
    def _load_complete_symbol_library(self) -> Dict[str, Any]:
        """Load both hardcoded symbols and YAML symbol library."""
        # Start with hardcoded symbols
        symbols = SVG_SYMBOLS.copy()
        
        # Load YAML symbols and merge
        yaml_symbols = load_symbol_library()
        for symbol in yaml_symbols:
            symbol_id = symbol.get('symbol_id')
            if symbol_id:
                symbols[symbol_id] = {
                    'system': symbol.get('system', 'unknown'),
                    'display_name': symbol.get('display_name', symbol_id),
                    'svg': symbol.get('svg', ''),
                    'category': symbol.get('category', ''),
                    'properties': symbol.get('properties', []),
                    'connections': symbol.get('connections', []),
                    'tags': symbol.get('tags', [])
                }
        
        logger.info(f"Loaded {len(symbols)} symbols for recognition")
        return symbols
    
    def _build_recognition_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build recognition patterns for each symbol type."""
        patterns = {}
        
        for symbol_id, symbol_data in self.symbol_library.items():
            patterns[symbol_id] = []
            
            # Text-based patterns
            display_name = symbol_data.get('display_name', '').lower()
            tags = symbol_data.get('tags', [])
            
            # Common abbreviations and variations
            abbreviations = self._get_abbreviations(symbol_id, display_name)
            
            # Build text patterns
            text_patterns = [
                display_name,
                symbol_id.lower(),
                *abbreviations,
                *[tag.lower() for tag in tags]
            ]
            
            # Add common variations
            if 'outlet' in display_name:
                text_patterns.extend(['outlet', 'receptacle', 'plug'])
            elif 'switch' in display_name:
                text_patterns.extend(['switch', 'sw', 'light switch'])
            elif 'panel' in display_name:
                text_patterns.extend(['panel', 'pnl', 'electrical panel'])
            elif 'thermostat' in display_name:
                text_patterns.extend(['thermostat', 'tstat', 'temp control'])
            
            patterns[symbol_id] = [
                {
                    'type': 'text',
                    'patterns': text_patterns,
                    'confidence': 0.8
                },
                {
                    'type': 'shape',
                    'shapes': self._extract_shapes_from_svg(symbol_data.get('svg', '')),
                    'confidence': 0.6
                }
            ]
        
        return patterns
    
    def _get_abbreviations(self, symbol_id: str, display_name: str) -> List[str]:
        """Get common abbreviations for a symbol."""
        abbreviations = []
        
        # Common abbreviations mapping
        abbrev_map = {
            'ahu': ['ahu', 'air handler', 'air handling'],
            'rtu': ['rtu', 'rooftop unit', 'rooftop'],
            'vav': ['vav', 'variable air volume'],
            'fcu': ['fcu', 'fan coil', 'fan coil unit'],
            'receptacle': ['receptacle', 'outlet', 'plug', 'r'],
            'switch': ['switch', 'sw', 'light switch'],
            'panel': ['panel', 'pnl', 'electrical panel'],
            'thermostat': ['thermostat', 'tstat', 'temp'],
            'sensor': ['sensor', 'detector'],
            'valve': ['valve', 'vlv'],
            'pump': ['pump', 'p'],
            'fan': ['fan', 'f'],
            'duct': ['duct', 'air duct'],
            'pipe': ['pipe', 'line'],
            'camera': ['camera', 'cam', 'cctv'],
            'speaker': ['speaker', 'spkr', 'sp'],
            'display': ['display', 'monitor', 'screen'],
            'router': ['router', 'rtr'],
            'switch_network': ['switch', 'sw', 'network switch'],
            'firewall': ['firewall', 'fw'],
            'server': ['server', 'srv'],
            'ups': ['ups', 'uninterruptible power supply']
        }
        
        # Add symbol-specific abbreviations
        for key, abbrevs in abbrev_map.items():
            if key in symbol_id.lower() or any(abbrev in display_name.lower() for abbrev in abbrevs):
                abbreviations.extend(abbrevs)
        
        return list(set(abbreviations))
    
    def _extract_shapes_from_svg(self, svg_content: str) -> List[Dict[str, Any]]:
        """Extract shape information from SVG for pattern matching."""
        shapes = []
        
        try:
            root = ET.fromstring(svg_content)
            
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                
                shape_info = {
                    'type': tag,
                    'attributes': dict(elem.attrib)
                }
                
                # Extract key attributes for matching
                if tag == 'rect':
                    shape_info.update({
                        'width': float(elem.get('width', 0)),
                        'height': float(elem.get('height', 0))
                    })
                elif tag == 'circle':
                    shape_info.update({
                        'radius': float(elem.get('r', 0))
                    })
                elif tag == 'line':
                    shape_info.update({
                        'x1': float(elem.get('x1', 0)),
                        'y1': float(elem.get('y1', 0)),
                        'x2': float(elem.get('x2', 0)),
                        'y2': float(elem.get('y2', 0))
                    })
                
                shapes.append(shape_info)
                
        except ET.ParseError:
            logger.warning(f"Failed to parse SVG for shape extraction: {svg_content[:100]}")
        
        return shapes
    
    def recognize_symbols_in_content(self, content: str, content_type: str = 'text') -> List[Dict[str, Any]]:
        """
        Recognize symbols in uploaded content.
        
        Args:
            content: Text content or SVG content to analyze
            content_type: 'text' or 'svg'
            
        Returns:
            List of recognized symbols with confidence scores
        """
        recognized_symbols = []
        
        if content_type == 'text':
            recognized_symbols = self._recognize_from_text(content)
        elif content_type == 'svg':
            recognized_symbols = self._recognize_from_svg(content)
        
        # Sort by confidence and remove duplicates
        recognized_symbols.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Remove duplicates (keep highest confidence)
        seen_symbols = set()
        unique_symbols = []
        for symbol in recognized_symbols:
            symbol_id = symbol['symbol_id']
            if symbol_id not in seen_symbols:
                seen_symbols.add(symbol_id)
                unique_symbols.append(symbol)
        
        logger.info(f"Recognized {len(unique_symbols)} unique symbols")
        return unique_symbols
    
    def _recognize_from_text(self, text_content: str) -> List[Dict[str, Any]]:
        """Recognize symbols from text content."""
        recognized = []
        text_lower = text_content.lower()
        
        for symbol_id, patterns in self.recognition_patterns.items():
            for pattern in patterns:
                if pattern['type'] == 'text':
                    for text_pattern in pattern['patterns']:
                        if text_pattern in text_lower:
                            # Calculate confidence based on pattern match
                            confidence = pattern['confidence']
                            
                            # Boost confidence for exact matches
                            if text_pattern in text_lower.split():
                                confidence += 0.1
                            
                            # Boost confidence for longer patterns
                            if len(text_pattern) > 3:
                                confidence += 0.05
                            
                            recognized.append({
                                'symbol_id': symbol_id,
                                'confidence': min(confidence, 1.0),
                                'match_type': 'text',
                                'matched_pattern': text_pattern,
                                'symbol_data': self.symbol_library[symbol_id]
                            })
                            break
        
        return recognized
    
    def _recognize_from_svg(self, svg_content: str) -> List[Dict[str, Any]]:
        """Recognize symbols from SVG content."""
        recognized = []
        
        try:
            root = ET.fromstring(svg_content)
            
            # Extract text elements
            text_elements = []
            for text_elem in root.findall('.//{http://www.w3.org/2000/svg}text'):
                text_content = text_elem.text or ''
                if text_content.strip():
                    text_elements.append({
                        'text': text_content,
                        'x': float(text_elem.get('x', 0)),
                        'y': float(text_elem.get('y', 0))
                    })
            
            # Match text elements to symbols
            for text_elem in text_elements:
                text_lower = text_elem['text'].lower()
                
                for symbol_id, patterns in self.recognition_patterns.items():
                    for pattern in patterns:
                        if pattern['type'] == 'text':
                            for text_pattern in pattern['patterns']:
                                if text_pattern in text_lower:
                                    confidence = pattern['confidence']
                                    
                                    # Boost confidence for exact matches
                                    if text_pattern == text_lower:
                                        confidence += 0.2
                                    
                                    recognized.append({
                                        'symbol_id': symbol_id,
                                        'confidence': min(confidence, 1.0),
                                        'match_type': 'svg_text',
                                        'matched_pattern': text_pattern,
                                        'position': {'x': text_elem['x'], 'y': text_elem['y']},
                                        'symbol_data': self.symbol_library[symbol_id]
                                    })
                                    break
            
            # Shape-based recognition (basic)
            recognized.extend(self._recognize_shapes_in_svg(root))
            
        except ET.ParseError:
            logger.warning("Failed to parse SVG for symbol recognition")
        
        return recognized
    
    def _recognize_shapes_in_svg(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Recognize symbols based on shape patterns in SVG."""
        recognized = []
        
        # Count shapes by type
        shape_counts = {}
        for elem in root.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            shape_counts[tag] = shape_counts.get(tag, 0) + 1
        
        # Match shape patterns to symbols
        for symbol_id, patterns in self.recognition_patterns.items():
            for pattern in patterns:
                if pattern['type'] == 'shape':
                    # Simple shape matching based on presence of key shapes
                    symbol_shapes = pattern['shapes']
                    shape_types = [shape['type'] for shape in symbol_shapes]
                    
                    # Check if symbol's shape types are present
                    matches = sum(1 for shape_type in shape_types if shape_counts.get(shape_type, 0) > 0)
                    
                    if matches > 0:
                        confidence = pattern['confidence'] * (matches / len(shape_types))
                        recognized.append({
                            'symbol_id': symbol_id,
                            'confidence': confidence,
                            'match_type': 'shape',
                            'matched_shapes': shape_types,
                            'symbol_data': self.symbol_library[symbol_id]
                        })
        
        return recognized
    
    def get_symbol_metadata(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """Get complete metadata for a symbol."""
        return self.symbol_library.get(symbol_id)
    
    def get_symbols_by_system(self, system: str) -> List[str]:
        """Get all symbols for a specific building system."""
        return [
            symbol_id for symbol_id, data in self.symbol_library.items()
            if data.get('system') == system
        ]
    
    def get_symbols_by_category(self, category: str) -> List[str]:
        """Get all symbols in a specific category."""
        return [
            symbol_id for symbol_id, data in self.symbol_library.items()
            if data.get('category', '').lower() == category.lower()
        ]
    
    def get_symbol_library_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the symbol library."""
        systems = {}
        categories = {}
        
        for symbol_id, data in self.symbol_library.items():
            system = data.get('system', 'unknown')
            category = data.get('category', 'general')
            
            if system not in systems:
                systems[system] = []
            systems[system].append(symbol_id)
            
            if category not in categories:
                categories[category] = []
            categories[category].append(symbol_id)
        
        return {
            'total_symbols': len(self.symbol_library),
            'systems': {system: len(symbols) for system, symbols in systems.items()},
            'categories': {cat: len(symbols) for cat, symbols in categories.items()},
            'available_systems': list(systems.keys()),
            'available_categories': list(categories.keys())
        } 