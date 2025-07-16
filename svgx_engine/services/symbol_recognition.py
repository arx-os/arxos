"""
SVGX Engine - Symbol Recognition Service

Provides advanced symbol recognition for SVGX Engine, including:
- Fuzzy and context-aware recognition
- SVGX symbol library integration
- SVG and text content recognition
- SVGX-specific metadata and validation
- Clean, extensible architecture
"""

import re
from typing import Dict, List, Any, Optional, Tuple
import structlog
from svgx_engine.services.symbol_manager import SVGXSymbolManager
from svgx_engine.utils.errors import RecognitionError
from svgx_engine.utils.performance import PerformanceMonitor

logger = structlog.get_logger(__name__)

class SVGXSymbolRecognitionService:
    """
    Advanced symbol recognition engine for SVGX Engine.
    Supports fuzzy, context-aware, and SVGX-specific recognition.
    """
    def __init__(self, symbol_manager: Optional[SVGXSymbolManager] = None):
        self.symbol_manager = symbol_manager or SVGXSymbolManager()
        self.performance_monitor = PerformanceMonitor()
        self.symbol_library = self._load_symbol_library()
        self.recognition_patterns = self._build_recognition_patterns()
        self.context_rules = self._build_context_rules()
        self.validation_rules = self._build_validation_rules()
        logger.info("SVGX Symbol Recognition Service initialized")

    def _load_symbol_library(self) -> Dict[str, Any]:
        """Load SVGX symbols from the symbol manager."""
        symbols = {}
        for symbol in self.symbol_manager.list_symbols():
            symbol_id = symbol.get("id")
            if symbol_id:
                symbols[symbol_id] = symbol
        logger.info(f"Loaded {len(symbols)} SVGX symbols for recognition")
        return symbols

    def _build_recognition_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build recognition patterns from SVGX symbol library."""
        patterns = {}
        for symbol_id, symbol in self.symbol_library.items():
            name = symbol.get("name", "")
            tags = symbol.get("tags", [])
            patterns[symbol_id] = [name] + tags
        return patterns

    def _build_context_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build context-aware interpretation rules."""
        return {
            'spatial_context': [
                {'rule': 'room_contains_devices', 'confidence_boost': 0.2},
                {'rule': 'corridor_contains_lighting', 'confidence_boost': 0.3}
            ],
            'system_context': [
                {'rule': 'electrical_panel_near_outlets', 'confidence_boost': 0.2},
                {'rule': 'hvac_equipment_near_thermostats', 'confidence_boost': 0.2}
            ],
            'scale_context': [
                {'rule': 'large_symbols_are_equipment', 'confidence_boost': 0.1},
                {'rule': 'small_symbols_are_devices', 'confidence_boost': 0.1}
            ]
        }

    def _build_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Build validation rules for SVGX symbols."""
        return {
            'must_have_dimensions': {'required': True},
            'must_have_material': {'required': True},
            'must_have_width': {'required': True},
            'must_have_height': {'required': True},
            'must_have_size': {'required': True},
            'must_have_flow_rate': {'required': False},
            'must_have_pressure': {'required': False},
            'must_have_capacity': {'required': False}
        }

    def fuzzy_match_symbols(self, query: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Fuzzy match query against SVGX symbol names and tags."""
        from difflib import SequenceMatcher
        matches = []
        for symbol_id, patterns in self.recognition_patterns.items():
            for pattern in patterns:
                ratio = SequenceMatcher(None, query.lower(), pattern.lower()).ratio()
                if ratio >= threshold:
                    matches.append({
                        'symbol_id': symbol_id,
                        'pattern': pattern,
                        'score': ratio,
                        'symbol': self.symbol_library[symbol_id]
                    })
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches

    def context_aware_interpretation(self, symbol_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret symbol with context-aware rules."""
        symbol = self.symbol_library.get(symbol_id)
        if not symbol:
            raise RecognitionError(f"Symbol '{symbol_id}' not found.")
        confidence = 1.0
        for context_type, rules in self.context_rules.items():
            for rule in rules:
                if rule['rule'] in context.get(context_type, []):
                    confidence += rule['confidence_boost']
        return {
            'symbol_id': symbol_id,
            'symbol': symbol,
            'confidence': min(confidence, 1.0)
        }

    def validate_symbol(self, symbol_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Validate symbol properties against SVGX validation rules."""
        symbol = self.symbol_library.get(symbol_id)
        if not symbol:
            raise RecognitionError(f"Symbol '{symbol_id}' not found.")
        errors = []
        for rule in symbol.get('validation_rules', []):
            rule_def = self.validation_rules.get(rule)
            if rule_def and rule_def['required'] and rule not in properties:
                errors.append(f"Missing required property: {rule}")
        return {
            'symbol_id': symbol_id,
            'valid': not errors,
            'errors': errors
        }

    def recognize_symbols_in_text(self, text: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Recognize symbols in text using fuzzy matching."""
        words = re.findall(r'\w+', text)
        recognized = []
        for word in words:
            matches = self.fuzzy_match_symbols(word, threshold)
            if matches:
                recognized.append(matches[0])
        return recognized

    def recognize_symbols_in_svgx(self, svgx_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recognize symbols in SVGX content (dict format)."""
        recognized = []
        elements = svgx_content.get('svgx_elements', [])
        for element in elements:
            name = element.get('name', '')
            matches = self.fuzzy_match_symbols(name)
            if matches:
                recognized.append({
                    'element': element,
                    'symbol_match': matches[0]
                })
        return recognized

    def get_symbol_metadata(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """Get SVGX symbol metadata by ID."""
        return self.symbol_library.get(symbol_id)

# Convenience function
def create_symbol_recognition_service(symbol_manager: Optional[SVGXSymbolManager] = None) -> SVGXSymbolRecognitionService:
    """Create and return a configured SVGX Symbol Recognition Service."""
    return SVGXSymbolRecognitionService(symbol_manager) 