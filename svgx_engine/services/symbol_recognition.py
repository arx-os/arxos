"""
SVGX Engine - Advanced Symbol Recognition Service

Provides comprehensive symbol recognition for SVGX Engine, including:
- Fuzzy and context-aware recognition with advanced algorithms
- SVGX symbol library integration with architectural/engineering symbols
- SVG and text content recognition with shape extraction
- Comprehensive validation and placement verification
- Performance monitoring and error handling
- Clean, extensible architecture with excellent documentation
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from collections import defaultdict
import structlog

from svgx_engine.services.symbol_manager import SVGXSymbolManager
from svgx_engine.utils.errors import RecognitionError, ValidationError
from svgx_engine.utils.performance import PerformanceMonitor

logger = structlog.get_logger(__name__)

class SVGXSymbolRecognitionService:
    """
    Enhanced engine for recognizing building system symbols with fuzzy matching 
    and context awareness, specifically designed for SVGX Engine.
    
    Features:
    - Advanced fuzzy matching with configurable thresholds
    - Context-aware interpretation with spatial, system, and scale rules
    - Comprehensive validation with architectural/engineering symbols
    - SVG content parsing and shape extraction
    - Performance monitoring and error handling
    - Extensible symbol library with JSON support
    """
    
    def __init__(self, symbol_manager: Optional[SVGXSymbolManager] = None):
        """
        Initialize the SVGX Symbol Recognition Engine.
        
        Args:
            symbol_manager: Optional SVGX symbol manager for enhanced functionality
        """
        self.symbol_manager = symbol_manager or SVGXSymbolManager()
        self.performance_monitor = PerformanceMonitor()
        self.symbol_library = self._load_complete_symbol_library()
        self.recognition_patterns = self._build_recognition_patterns()
        self.context_rules = self._build_context_rules()
        self.validation_rules = self._build_validation_rules()
        
        logger.info(f"SVGX Symbol Recognition Engine initialized with {len(self.symbol_library)} symbols")
        
    def _load_complete_symbol_library(self) -> Dict[str, Any]:
        """
        Load both SVGX symbols and architectural/engineering symbols.
        
        Returns:
            Dictionary containing all available symbols for recognition
        """
        # Start with SVGX symbols from symbol manager
        symbols = {}
        for symbol in self.symbol_manager.list_symbols():
            symbol_id = symbol.get('id')
            if symbol_id:
                symbols[symbol_id] = {
                    'system': symbol.get('system', 'unknown'),
                    'display_name': symbol.get('name', symbol_id),
                    'svg': symbol.get('svg', ''),
                    'category': symbol.get('category', ''),
                    'properties': symbol.get('properties', []),
                    'connections': symbol.get('connections', []),
                    'tags': symbol.get('tags', []),
                    'architectural_type': symbol.get('architectural_type', ''),
                    'engineering_type': symbol.get('engineering_type', ''),
                    'validation_rules': symbol.get('validation_rules', [])
                }
        
        # Add architectural/engineering symbols
        self._add_architectural_symbols(symbols)
        self._add_engineering_symbols(symbols)
        
        logger.info(f"Loaded {len(symbols)} symbols for recognition")
        return symbols
    
    def _add_architectural_symbols(self, symbols: Dict[str, Any]):
        """Add architectural symbols to the library."""
        arch_symbols = {
            'wall': {
                'system': 'structural',
                'display_name': 'Wall',
                'category': 'structural',
                'architectural_type': 'wall',
                'tags': ['wall', 'partition', 'structural'],
                'validation_rules': ['must_have_thickness', 'must_have_material']
            },
            'door': {
                'system': 'architectural',
                'display_name': 'Door',
                'category': 'architectural',
                'architectural_type': 'door',
                'tags': ['door', 'entrance', 'exit'],
                'validation_rules': ['must_have_width', 'must_have_height']
            },
            'window': {
                'system': 'architectural',
                'display_name': 'Window',
                'category': 'architectural',
                'architectural_type': 'window',
                'tags': ['window', 'glazing', 'opening'],
                'validation_rules': ['must_have_width', 'must_have_height']
            },
            'column': {
                'system': 'structural',
                'display_name': 'Column',
                'category': 'structural',
                'architectural_type': 'column',
                'tags': ['column', 'pillar', 'support'],
                'validation_rules': ['must_have_dimensions']
            },
            'beam': {
                'system': 'structural',
                'display_name': 'Beam',
                'category': 'structural',
                'architectural_type': 'beam',
                'tags': ['beam', 'girder', 'support'],
                'validation_rules': ['must_have_dimensions']
            }
        }
        
        for symbol_id, symbol_data in arch_symbols.items():
            symbols[symbol_id] = symbol_data
    
    def _add_engineering_symbols(self, symbols: Dict[str, Any]):
        """Add engineering symbols to the library."""
        eng_symbols = {
            'duct_supply': {
                'system': 'mechanical',
                'display_name': 'Supply Duct',
                'category': 'mechanical',
                'engineering_type': 'duct',
                'tags': ['duct', 'supply', 'air'],
                'validation_rules': ['must_have_size', 'must_have_flow_rate']
            },
            'duct_return': {
                'system': 'mechanical',
                'display_name': 'Return Duct',
                'category': 'mechanical',
                'engineering_type': 'duct',
                'tags': ['duct', 'return', 'air'],
                'validation_rules': ['must_have_size', 'must_have_flow_rate']
            },
            'pipe_hot_water': {
                'system': 'plumbing',
                'display_name': 'Hot Water Pipe',
                'category': 'plumbing',
                'engineering_type': 'pipe',
                'tags': ['pipe', 'hot water', 'hw'],
                'validation_rules': ['must_have_size', 'must_have_pressure']
            },
            'pipe_cold_water': {
                'system': 'plumbing',
                'display_name': 'Cold Water Pipe',
                'category': 'plumbing',
                'engineering_type': 'pipe',
                'tags': ['pipe', 'cold water', 'cw'],
                'validation_rules': ['must_have_size', 'must_have_pressure']
            },
            'electrical_conduit': {
                'system': 'electrical',
                'display_name': 'Electrical Conduit',
                'category': 'electrical',
                'engineering_type': 'conduit',
                'tags': ['conduit', 'electrical', 'wire'],
                'validation_rules': ['must_have_size', 'must_have_capacity']
            }
        }
        
        for symbol_id, symbol_data in eng_symbols.items():
            symbols[symbol_id] = symbol_data
    
    def _build_context_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build context-aware interpretation rules."""
        return {
            'spatial_context': [
                {
                    'rule': 'room_contains_devices',
                    'description': 'Devices found in room context are likely room equipment',
                    'confidence_boost': 0.2
                },
                {
                    'rule': 'corridor_contains_lighting',
                    'description': 'Lighting in corridor context is likely emergency lighting',
                    'confidence_boost': 0.3
                }
            ],
            'system_context': [
                {
                    'rule': 'electrical_panel_near_outlets',
                    'description': 'Electrical panels are typically near outlet clusters',
                    'confidence_boost': 0.2
                },
                {
                    'rule': 'hvac_equipment_near_thermostats',
                    'description': 'HVAC equipment is typically near thermostats',
                    'confidence_boost': 0.2
                }
            ],
            'scale_context': [
                {
                    'rule': 'large_symbols_are_equipment',
                    'description': 'Large symbols are typically major equipment',
                    'confidence_boost': 0.1
                },
                {
                    'rule': 'small_symbols_are_devices',
                    'description': 'Small symbols are typically devices or sensors',
                    'confidence_boost': 0.1
                }
            ]
        }
    
    def _build_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Build validation rules for symbols."""
        return {
            'must_have_dimensions': {
                'required': True,
                'description': 'Symbol must have width and height dimensions'
            },
            'must_have_material': {
                'required': True,
                'description': 'Symbol must have material specification'
            },
            'must_have_thickness': {
                'required': True,
                'description': 'Symbol must have thickness specification'
            },
            'must_have_width': {
                'required': True,
                'description': 'Symbol must have width specification'
            },
            'must_have_height': {
                'required': True,
                'description': 'Symbol must have height specification'
            },
            'must_have_size': {
                'required': True,
                'description': 'Symbol must have size specification'
            },
            'must_have_flow_rate': {
                'required': False,
                'description': 'Symbol should have flow rate specification'
            },
            'must_have_pressure': {
                'required': False,
                'description': 'Symbol should have pressure specification'
            },
            'must_have_capacity': {
                'required': False,
                'description': 'Symbol should have capacity specification'
            }
        }
    
    def fuzzy_match_symbols(self, query: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Perform fuzzy matching of query against symbol names and tags.
        
        Args:
            query: String to match against symbols
            threshold: Minimum similarity ratio (0.0 to 1.0)
            
        Returns:
            List of matching symbols with scores
        """
        matches = []
        
        for symbol_id, symbol_data in self.symbol_library.items():
            # Check display name
            name_ratio = SequenceMatcher(None, query.lower(), 
                                       symbol_data.get('display_name', '').lower()).ratio()
            
            # Check tags
            tag_ratios = []
            for tag in symbol_data.get('tags', []):
                tag_ratio = SequenceMatcher(None, query.lower(), tag.lower()).ratio()
                tag_ratios.append(tag_ratio)
            
            # Get best match from name and tags
            best_ratio = max([name_ratio] + tag_ratios)
            
            if best_ratio >= threshold:
                matches.append({
                    'symbol_id': symbol_id,
                    'symbol_data': symbol_data,
                    'score': best_ratio,
                    'match_type': 'name' if name_ratio == best_ratio else 'tag'
                })
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches
    
    def context_aware_interpretation(self, symbol_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply context-aware interpretation to a symbol.
        
        Args:
            symbol_id: ID of the symbol to interpret
            context: Context information (spatial, system, scale)
            
        Returns:
            Interpretation result with confidence score
        """
        if symbol_id not in self.symbol_library:
            raise RecognitionError(f"Symbol '{symbol_id}' not found in library")
        
        symbol_data = self.symbol_library[symbol_id]
        base_confidence = 1.0
        applied_rules = []
        
        # Apply spatial context rules
        spatial_context = context.get('spatial_context', {})
        for rule in self.context_rules['spatial_context']:
            rule_name = rule['rule']
            if rule_name in spatial_context:
                base_confidence += rule['confidence_boost']
                applied_rules.append({
                    'rule': rule_name,
                    'description': rule['description'],
                    'boost': rule['confidence_boost']
                })
        
        # Apply system context rules
        system_context = context.get('system_context', {})
        for rule in self.context_rules['system_context']:
            rule_name = rule['rule']
            if rule_name in system_context:
                base_confidence += rule['confidence_boost']
                applied_rules.append({
                    'rule': rule_name,
                    'description': rule['description'],
                    'boost': rule['confidence_boost']
                })
        
        # Apply scale context rules
        scale_context = context.get('scale_context', {})
        for rule in self.context_rules['scale_context']:
            rule_name = rule['rule']
            if rule_name in scale_context:
                base_confidence += rule['confidence_boost']
                applied_rules.append({
                    'rule': rule_name,
                    'description': rule['description'],
                    'boost': rule['confidence_boost']
                })
        
        return {
            'symbol_id': symbol_id,
            'symbol_data': symbol_data,
            'confidence': min(base_confidence, 1.0),
            'applied_rules': applied_rules,
            'context_used': context
        }
    
    def validate_symbol(self, symbol_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate symbol properties against validation rules.
        
        Args:
            symbol_id: ID of the symbol to validate
            properties: Properties to validate
            
        Returns:
            Validation result with errors and warnings
        """
        if symbol_id not in self.symbol_library:
            raise ValidationError(f"Symbol '{symbol_id}' not found in library")
        
        symbol_data = self.symbol_library[symbol_id]
        validation_rules = symbol_data.get('validation_rules', [])
        
        errors = []
        warnings = []
        
        for rule_name in validation_rules:
            rule_def = self.validation_rules.get(rule_name)
            if rule_def:
                if rule_def['required'] and rule_name not in properties:
                    errors.append({
                        'rule': rule_name,
                        'description': rule_def['description'],
                        'type': 'missing_required'
                    })
                elif not rule_def['required'] and rule_name not in properties:
                    warnings.append({
                        'rule': rule_name,
                        'description': rule_def['description'],
                        'type': 'missing_optional'
                    })
        
        return {
            'symbol_id': symbol_id,
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'properties_checked': list(properties.keys())
        }
    
    def verify_symbol_placement(self, symbol_id: str, position: Dict[str, float], 
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify symbol placement against context and other symbols.
        
        Args:
            symbol_id: ID of the symbol to verify
            position: Position coordinates {'x': float, 'y': float}
            context: Context information including other symbols
            
        Returns:
            Placement verification result
        """
        if symbol_id not in self.symbol_library:
            raise RecognitionError(f"Symbol '{symbol_id}' not found in library")
        
        symbol_data = self.symbol_library[symbol_id]
        issues = []
        
        # Check for overlaps with other symbols
        other_symbols = context.get('other_symbols', [])
        for other_symbol in other_symbols:
            if self._symbols_overlap(position, other_symbol.get('position', {})):
                issues.append({
                    'type': 'overlap',
                    'description': f"Symbol overlaps with {other_symbol.get('symbol_id', 'unknown')}",
                    'severity': 'warning'
                })
        
        # Check spatial constraints
        spatial_constraints = context.get('spatial_constraints', {})
        if 'room_boundaries' in spatial_constraints:
            room_bounds = spatial_constraints['room_boundaries']
            if not (room_bounds['min_x'] <= position['x'] <= room_bounds['max_x'] and
                   room_bounds['min_y'] <= position['y'] <= room_bounds['max_y']):
                issues.append({
                    'type': 'out_of_bounds',
                    'description': "Symbol placed outside room boundaries",
                    'severity': 'error'
                })
        
        return {
            'symbol_id': symbol_id,
            'position': position,
            'valid_placement': len([i for i in issues if i['severity'] == 'error']) == 0,
            'issues': issues,
            'context_used': context
        }
    
    def _symbols_overlap(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> bool:
        """Check if two symbol positions overlap."""
        # Simple distance-based overlap check
        distance = ((pos1.get('x', 0) - pos2.get('x', 0)) ** 2 + 
                   (pos1.get('y', 0) - pos2.get('y', 0)) ** 2) ** 0.5
        return distance < 10.0  # 10 unit threshold for overlap
    
    def _build_recognition_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build recognition patterns for efficient matching."""
        patterns = {}
        
        for symbol_id, symbol_data in self.symbol_library.items():
            symbol_patterns = []
            
            # Add display name
            display_name = symbol_data.get('display_name', '')
            if display_name:
                symbol_patterns.append({
                    'type': 'exact_name',
                    'pattern': display_name.lower(),
                    'weight': 1.0
                })
                
                # Add abbreviations
                abbreviations = self._get_abbreviations(symbol_id, display_name)
                for abbr in abbreviations:
                    symbol_patterns.append({
                        'type': 'abbreviation',
                        'pattern': abbr.lower(),
                        'weight': 0.8
                    })
            
            # Add tags
            for tag in symbol_data.get('tags', []):
                symbol_patterns.append({
                    'type': 'tag',
                    'pattern': tag.lower(),
                    'weight': 0.6
                })
            
            patterns[symbol_id] = symbol_patterns
        
        return patterns
    
    def _get_abbreviations(self, symbol_id: str, display_name: str) -> List[str]:
        """Generate abbreviations for a symbol name."""
        abbreviations = []
        
        # Common abbreviations
        abbr_map = {
            'duct': 'dct',
            'pipe': 'p',
            'electrical': 'elec',
            'conduit': 'cond',
            'supply': 'sup',
            'return': 'ret',
            'hot water': 'hw',
            'cold water': 'cw',
            'window': 'wnd',
            'door': 'dr'
        }
        
        name_lower = display_name.lower()
        for full, abbr in abbr_map.items():
            if full in name_lower:
                abbreviations.append(abbr)
        
        # Generate acronyms from words
        words = display_name.split()
        if len(words) > 1:
            acronym = ''.join(word[0].upper() for word in words if word)
            abbreviations.append(acronym)
        
        return abbreviations
    
    def _extract_shapes_from_svg(self, svg_content: str) -> List[Dict[str, Any]]:
        """
        Extract shapes and elements from SVG content.
        
        Args:
            svg_content: SVG string content
            
        Returns:
            List of extracted shapes with properties
        """
        shapes = []
        
        try:
            root = ET.fromstring(svg_content)
            
            # Extract basic shapes
            for element in root.iter():
                shape_info = {
                    'tag': element.tag,
                    'attributes': dict(element.attrib),
                    'text': element.text.strip() if element.text else ''
                }
                
                # Extract specific shape properties
                if element.tag.endswith('rect'):
                    shape_info['type'] = 'rectangle'
                    shape_info['width'] = element.get('width', '0')
                    shape_info['height'] = element.get('height', '0')
                elif element.tag.endswith('circle'):
                    shape_info['type'] = 'circle'
                    shape_info['radius'] = element.get('r', '0')
                elif element.tag.endswith('path'):
                    shape_info['type'] = 'path'
                    shape_info['d'] = element.get('d', '')
                
                shapes.append(shape_info)
                
        except ET.ParseError as e:
            logger.warning(f"Failed to parse SVG content: {e}")
        
        return shapes
    
    def recognize_symbols_in_content(self, content: str, content_type: str = 'text') -> List[Dict[str, Any]]:
        """
        Recognize symbols in various content types.
        
        Args:
            content: Content to analyze
            content_type: Type of content ('text', 'svg', 'svgx')
            
        Returns:
            List of recognized symbols
        """
        if content_type == 'text':
            return self._recognize_from_text(content)
        elif content_type == 'svg':
            return self._recognize_from_svg(content)
        elif content_type == 'svgx':
            return self._recognize_from_svgx(content)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    
    def _recognize_from_text(self, text_content: str) -> List[Dict[str, Any]]:
        """Recognize symbols from text content."""
        recognized = []
        
        # Split text into words and phrases
        words = re.findall(r'\b\w+\b', text_content.lower())
        
        for word in words:
            matches = self.fuzzy_match_symbols(word, threshold=0.7)
            if matches:
                best_match = matches[0]
                recognized.append({
                    'text': word,
                    'symbol_id': best_match['symbol_id'],
                    'symbol_data': best_match['symbol_data'],
                    'confidence': best_match['score'],
                    'match_type': best_match['match_type']
                })
        
        return recognized
    
    def _recognize_from_svg(self, svg_content: str) -> List[Dict[str, Any]]:
        """Recognize symbols from SVG content."""
        recognized = []
        
        try:
            root = ET.fromstring(svg_content)
            shapes = self._recognize_shapes_in_svg(root)
            
            for shape in shapes:
                # Try to match shape properties to symbols
                shape_text = shape.get('text', '')
                if shape_text:
                    matches = self.fuzzy_match_symbols(shape_text, threshold=0.6)
                    if matches:
                        best_match = matches[0]
                        recognized.append({
                            'shape': shape,
                            'symbol_id': best_match['symbol_id'],
                            'symbol_data': best_match['symbol_data'],
                            'confidence': best_match['score']
                        })
                
                # Match by shape type
                shape_type = shape.get('type', '')
                if shape_type:
                    type_matches = self.fuzzy_match_symbols(shape_type, threshold=0.5)
                    if type_matches:
                        best_match = type_matches[0]
                        recognized.append({
                            'shape': shape,
                            'symbol_id': best_match['symbol_id'],
                            'symbol_data': best_match['symbol_data'],
                            'confidence': best_match['score'] * 0.8  # Lower confidence for type matching
                        })
        
        except ET.ParseError as e:
            logger.warning(f"Failed to parse SVG content: {e}")
        
        return recognized
    
    def _recognize_from_svgx(self, svgx_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recognize symbols from SVGX content (dict format)."""
        recognized = []
        
        elements = svgx_content.get('svgx_elements', [])
        for element in elements:
            name = element.get('name', '')
            if name:
                matches = self.fuzzy_match_symbols(name, threshold=0.6)
                if matches:
                    best_match = matches[0]
                    recognized.append({
                        'element': element,
                        'symbol_id': best_match['symbol_id'],
                        'symbol_data': best_match['symbol_data'],
                        'confidence': best_match['score']
                    })
        
        return recognized
    
    def _recognize_shapes_in_svg(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Recognize shapes within SVG element tree."""
        shapes = []
        
        for element in root.iter():
            shape_info = {
                'tag': element.tag,
                'attributes': dict(element.attrib),
                'text': element.text.strip() if element.text else ''
            }
            
            # Extract shape-specific properties
            if element.tag.endswith('rect'):
                shape_info['type'] = 'rectangle'
                shape_info['width'] = element.get('width', '0')
                shape_info['height'] = element.get('height', '0')
            elif element.tag.endswith('circle'):
                shape_info['type'] = 'circle'
                shape_info['radius'] = element.get('r', '0')
            elif element.tag.endswith('path'):
                shape_info['type'] = 'path'
                shape_info['d'] = element.get('d', '')
            elif element.tag.endswith('text'):
                shape_info['type'] = 'text'
                shape_info['content'] = element.text or ''
            
            shapes.append(shape_info)
        
        return shapes
    
    def get_symbol_metadata(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific symbol."""
        return self.symbol_library.get(symbol_id)
    
    def get_symbols_by_system(self, system: str) -> List[str]:
        """Get all symbols for a specific system."""
        return [symbol_id for symbol_id, data in self.symbol_library.items() 
                if data.get('system') == system]
    
    def get_symbols_by_category(self, category: str) -> List[str]:
        """Get all symbols for a specific category."""
        return [symbol_id for symbol_id, data in self.symbol_library.items() 
                if data.get('category') == category]
    
    def get_symbol_library_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the symbol library."""
        systems = defaultdict(int)
        categories = defaultdict(int)
        
        for symbol_data in self.symbol_library.values():
            systems[symbol_data.get('system', 'unknown')] += 1
            categories[symbol_data.get('category', 'unknown')] += 1
        
        return {
            'total_symbols': len(self.symbol_library),
            'systems': dict(systems),
            'categories': dict(categories),
            'validation_rules': list(self.validation_rules.keys()),
            'context_rules': {k: len(v) for k, v in self.context_rules.items()}
        }

# Convenience functions for backward compatibility
def create_symbol_recognition_service(symbol_manager: Optional[SVGXSymbolManager] = None) -> SVGXSymbolRecognitionService:
    """Create and return a configured SVGX Symbol Recognition Engine."""
    return SVGXSymbolRecognitionService(symbol_manager)

def create_svgx_symbol_recognition_service(symbol_manager: Optional[SVGXSymbolManager] = None) -> SVGXSymbolRecognitionService:
    """Create and return a configured SVGX Symbol Recognition Engine."""
    return SVGXSymbolRecognitionService(symbol_manager) 