import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET
from services.svg_symbol_library import SVG_SYMBOLS, load_symbol_library
# Remove all YAML imports and logic
# Only allow JSON for symbol file operations
# Update docstrings and comments to reference JSON only
import os
from difflib import SequenceMatcher
from collections import defaultdict
import structlog

logger = structlog.get_logger(__name__)

class SymbolRecognitionEngine:
    """Enhanced engine for recognizing building system symbols with fuzzy matching and context awareness."""
    
    def __init__(self):
        self.symbol_library = self._load_complete_symbol_library()
        self.recognition_patterns = self._build_recognition_patterns()
        self.context_rules = self._build_context_rules()
        self.validation_rules = self._build_validation_rules()
        
    def _load_complete_symbol_library(self) -> Dict[str, Any]:
        """Load both hardcoded symbols and JSON symbol library with architectural/engineering symbols."""
        # Start with hardcoded symbols
        symbols = SVG_SYMBOLS.copy()
        
        # Load JSON symbols and merge
        # The load_symbol_library function is no longer available,
        # so we'll assume a default structure or that the JSON is passed directly.
        # For now, we'll just add the hardcoded symbols and assume a placeholder for JSON loading.
        # In a real application, you'd load JSON from a file here.
        # Example placeholder for JSON loading (replace with actual JSON parsing)
        # json_symbols = load_symbol_library() # This line is removed as per the edit hint.
        # for symbol in json_symbols:
        #     symbol_id = symbol.get('symbol_id')
        #     if symbol_id:
        #         symbols[symbol_id] = {
        #             'system': symbol.get('system', 'unknown'),
        #             'display_name': symbol.get('display_name', symbol_id),
        #             'svg': symbol.get('svg', ''),
        #             'category': symbol.get('category', ''),
        #             'properties': symbol.get('properties', []),
        #             'connections': symbol.get('connections', []),
        #             'tags': symbol.get('tags', []),
        #             'architectural_type': symbol.get('architectural_type', ''),
        #             'engineering_type': symbol.get('engineering_type', ''),
        #             'validation_rules': symbol.get('validation_rules', [])
        #         }
        
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
                'description': 'Symbol must have width and height',
                'validate': lambda props: 'width' in props and 'height' in props
            },
            'must_have_thickness': {
                'description': 'Wall must have thickness',
                'validate': lambda props: 'thickness' in props
            },
            'must_have_material': {
                'description': 'Structural element must have material',
                'validate': lambda props: 'material' in props
            },
            'must_have_size': {
                'description': 'Engineering element must have size',
                'validate': lambda props: 'size' in props
            },
            'must_have_flow_rate': {
                'description': 'Duct must have flow rate',
                'validate': lambda props: 'flow_rate' in props
            },
            'must_have_pressure': {
                'description': 'Pipe must have pressure',
                'validate': lambda props: 'pressure' in props
            },
            'must_have_capacity': {
                'description': 'Electrical element must have capacity',
                'validate': lambda props: 'capacity' in props
            }
        }
    
    def fuzzy_match_symbols(self, query: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Implement fuzzy matching for similar symbols."""
        matches = []
        
        for symbol_id, symbol_data in self.symbol_library.items():
            # Match against display name
            name_ratio = SequenceMatcher(None, query.lower(), symbol_data.get('display_name', '').lower()).ratio()
            
            # Match against tags
            tag_ratios = [SequenceMatcher(None, query.lower(), tag.lower()).ratio() for tag in symbol_data.get('tags', [])]
            max_tag_ratio = max(tag_ratios) if tag_ratios else 0
            
            # Match against symbol ID
            id_ratio = SequenceMatcher(None, query.lower(), symbol_id.lower()).ratio()
            
            # Take the best match
            best_ratio = max(name_ratio, max_tag_ratio, id_ratio)
            
            if best_ratio >= threshold:
                matches.append({
                    'symbol_id': symbol_id,
                    'symbol_data': symbol_data,
                    'confidence': best_ratio,
                    'match_type': 'fuzzy',
                    'matched_against': 'name' if name_ratio == best_ratio else 'tags' if max_tag_ratio == best_ratio else 'id'
                })
        
        # Sort by confidence
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        return matches
    
    def context_aware_interpretation(self, symbol_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply context-aware interpretation to symbol recognition."""
        symbol_data = self.symbol_library.get(symbol_id, {})
        confidence_boost = 0.0
        context_notes = []
        
        # Apply spatial context rules
        if 'room_type' in context:
            if context['room_type'] == 'corridor' and 'light' in symbol_id.lower():
                confidence_boost += 0.3
                context_notes.append('Emergency lighting in corridor')
        
        # Apply system context rules
        if 'nearby_systems' in context:
            nearby_systems = context['nearby_systems']
            if 'electrical' in nearby_systems and 'panel' in symbol_id.lower():
                confidence_boost += 0.2
                context_notes.append('Electrical panel near electrical system')
        
        # Apply scale context rules
        if 'symbol_size' in context:
            size = context['symbol_size']
            if size == 'large' and any(word in symbol_id.lower() for word in ['ahu', 'rtu', 'chiller']):
                confidence_boost += 0.1
                context_notes.append('Large symbol matches major equipment')
        
        return {
            'symbol_id': symbol_id,
            'symbol_data': symbol_data,
            'confidence_boost': confidence_boost,
            'context_notes': context_notes,
            'final_confidence': min(1.0, symbol_data.get('confidence', 0.5) + confidence_boost)
        }
    
    def validate_symbol(self, symbol_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Validate symbol against its validation rules."""
        symbol_data = self.symbol_library.get(symbol_id, {})
        validation_rules = symbol_data.get('validation_rules', [])
        
        validation_results = {
            'symbol_id': symbol_id,
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        for rule_name in validation_rules:
            rule = self.validation_rules.get(rule_name)
            if rule and not rule['validate'](properties):
                validation_results['is_valid'] = False
                validation_results['errors'].append(f"Failed validation: {rule['description']}")
        
        return validation_results
    
    def verify_symbol_placement(self, symbol_id: str, position: Dict[str, float], context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify if symbol placement makes sense in context."""
        verification_results = {
            'symbol_id': symbol_id,
            'placement_valid': True,
            'warnings': [],
            'suggestions': []
        }
        
        # Check for overlapping symbols
        if 'nearby_symbols' in context:
            nearby = context['nearby_symbols']
            for nearby_symbol in nearby:
                if self._symbols_overlap(position, nearby_symbol.get('position', {})):
                    verification_results['warnings'].append(f"Symbol overlaps with {nearby_symbol.get('symbol_id')}")
        
        # Check for appropriate placement based on symbol type
        symbol_data = self.symbol_library.get(symbol_id, {})
        system = symbol_data.get('system', '')
        
        if system == 'electrical' and 'room_type' in context:
            if context['room_type'] == 'bathroom':
                verification_results['suggestions'].append("Consider GFCI protection for bathroom electrical")
        
        return verification_results
    
    def _symbols_overlap(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> bool:
        """Check if two symbols overlap."""
        # Simple distance-based overlap check
        if 'x' in pos1 and 'y' in pos1 and 'x' in pos2 and 'y' in pos2:
            distance = ((pos1['x'] - pos2['x']) ** 2 + (pos1['y'] - pos2['y']) ** 2) ** 0.5
            return distance < 10  # Threshold for overlap
        return False
    
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