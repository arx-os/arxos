"""
SVGX Engine - Symbol Generator Service

Provides automated symbol generation capabilities with:
- Template-based generation
- Quality assurance
- Custom generation rules
- Performance optimization
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import re

from svgx_engine.utils.errors import GenerationError, ValidationError
from svgx_engine.logging.structured_logger import get_logger

logger = get_logger(__name__)


class GenerationType(Enum):
    """Symbol generation types."""
    TEMPLATE_BASED = "template_based"
    RULE_BASED = "rule_based"
    AI_GENERATED = "ai_generated"
    MANUAL = "manual"


class SymbolCategory(Enum):
    """Symbol categories."""
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    FIRE_ALARM = "fire_alarm"
    SECURITY = "security"
    HVAC = "hvac"
    GENERAL = "general"


@dataclass
class GenerationOptions:
    """Options for symbol generation."""
    generation_type: GenerationType = GenerationType.TEMPLATE_BASED
    category: SymbolCategory = SymbolCategory.GENERAL
    template_name: Optional[str] = None
    quality_level: str = "standard"
    include_metadata: bool = True
    validate_output: bool = True
    optimize_generated: bool = True
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    generation_rules: List[str] = field(default_factory=list)


@dataclass
class GenerationResult:
    """Result of symbol generation."""
    symbol_data: Dict[str, Any]
    generation_type: GenerationType
    category: SymbolCategory
    template_used: Optional[str] = None
    generation_time_ms: float = 0.0
    validation_passed: bool = False
    quality_score: float = 0.0
    generated_at: datetime = field(default_factory=datetime.utcnow)


class SVGXSymbolGenerator:
    """
    Comprehensive symbol generator for SVGX Engine.
    
    Features:
    - Template-based generation with customizable templates
    - Rule-based generation with configurable rules
    - Quality assurance and validation
    - Performance optimization
    - Custom generation pipelines
    - SVGX-specific optimizations
    """
    
    def __init__(self, default_options: Optional[GenerationOptions] = None):
        """Initialize the symbol generator."""
        self.default_options = default_options or GenerationOptions()
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.generation_rules: Dict[str, Callable] = {}
        self.quality_validators: List[Callable] = []
        self.generated_cache: Dict[str, GenerationResult] = {}
        self.stats = {
            'total_generations': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'average_generation_time_ms': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        self._initialize_default_templates()
        self._setup_generation_rules()
        self._setup_quality_validators()
        
        logger.info("Symbol generator initialized")
    
    def _initialize_default_templates(self):
        """Initialize default symbol templates."""
        # Electrical symbol templates
        self.templates['electrical_switch'] = {
            'type': 'rect',
            'attributes': {
                'x': 0, 'y': 0, 'width': 20, 'height': 30,
                'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
            },
            'content': '',
            'metadata': {
                'category': 'electrical',
                'subcategory': 'switch',
                'description': 'Electrical switch symbol'
            }
        }
        
        self.templates['electrical_outlet'] = {
            'type': 'circle',
            'attributes': {
                'cx': 15, 'cy': 15, 'r': 8,
                'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
            },
            'content': '',
            'metadata': {
                'category': 'electrical',
                'subcategory': 'outlet',
                'description': 'Electrical outlet symbol'
            }
        }
        
        # Mechanical symbol templates
        self.templates['mechanical_pump'] = {
            'type': 'circle',
            'attributes': {
                'cx': 20, 'cy': 20, 'r': 15,
                'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
            },
            'content': '<text x="20" y="25" text-anchor="middle" font-size="12">P</text>',
            'metadata': {
                'category': 'mechanical',
                'subcategory': 'pump',
                'description': 'Mechanical pump symbol'
            }
        }
        
        # Plumbing symbol templates
        self.templates['plumbing_valve'] = {
            'type': 'rect',
            'attributes': {
                'x': 5, 'y': 5, 'width': 30, 'height': 20,
                'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
            },
            'content': '<text x="20" y="18" text-anchor="middle" font-size="10">V</text>',
            'metadata': {
                'category': 'plumbing',
                'subcategory': 'valve',
                'description': 'Plumbing valve symbol'
            }
        }
        
        # Fire alarm symbol templates
        self.templates['fire_alarm_pull'] = {
            'type': 'rect',
            'attributes': {
                'x': 0, 'y': 0, 'width': 25, 'height': 35,
                'fill': '#ff0000', 'stroke': '#000000', 'stroke-width': '2'
            },
            'content': '<text x="12.5" y="22" text-anchor="middle" font-size="10" fill="#ffffff">P</text>',
            'metadata': {
                'category': 'fire_alarm',
                'subcategory': 'pull_station',
                'description': 'Fire alarm pull station symbol'
            }
        }
        
        # HVAC symbol templates
        self.templates['hvac_thermostat'] = {
            'type': 'rect',
            'attributes': {
                'x': 0, 'y': 0, 'width': 30, 'height': 25,
                'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
            },
            'content': '<text x="15" y="17" text-anchor="middle" font-size="12">T</text>',
            'metadata': {
                'category': 'hvac',
                'subcategory': 'thermostat',
                'description': 'HVAC thermostat symbol'
            }
        }
    
    def _setup_generation_rules(self):
        """Setup generation rules."""
        self.generation_rules['electrical_rule'] = self._apply_electrical_rules
        self.generation_rules['mechanical_rule'] = self._apply_mechanical_rules
        self.generation_rules['plumbing_rule'] = self._apply_plumbing_rules
        self.generation_rules['fire_alarm_rule'] = self._apply_fire_alarm_rules
        self.generation_rules['hvac_rule'] = self._apply_hvac_rules
    
    def _setup_quality_validators(self):
        """Setup quality validation functions."""
        self.quality_validators.append(self._validate_symbol_structure)
        self.quality_validators.append(self._validate_symbol_attributes)
        self.quality_validators.append(self._validate_symbol_content)
        self.quality_validators.append(self._validate_symbol_metadata)
    
    def generate_symbol(self, options: Optional[GenerationOptions] = None,
                       cache_result: bool = True) -> GenerationResult:
        """
        Generate a symbol with the specified options.
        
        Args:
            options: Generation options
            cache_result: Whether to cache the generation result
            
        Returns:
            GenerationResult: The generated symbol
        """
        start_time = datetime.utcnow()
        
        # Merge options with defaults
        generation_options = self._merge_options(options)
        
        # Check cache first
        cache_key = self._generate_cache_key(generation_options)
        if cache_result and cache_key in self.generated_cache:
            self.stats['cache_hits'] += 1
            logger.debug("Using cached generation result", cache_key=cache_key)
            return self.generated_cache[cache_key]
        
        self.stats['cache_misses'] += 1
        
        try:
            # Generate symbol based on type
            if generation_options.generation_type == GenerationType.TEMPLATE_BASED:
                symbol_data = self._generate_from_template(generation_options)
            elif generation_options.generation_type == GenerationType.RULE_BASED:
                symbol_data = self._generate_from_rules(generation_options)
            elif generation_options.generation_type == GenerationType.AI_GENERATED:
                symbol_data = self._generate_ai_symbol(generation_options)
            else:
                raise GenerationError(f"Unsupported generation type: {generation_options.generation_type.value}")
            
            # Apply custom attributes
            if generation_options.custom_attributes:
                symbol_data['attributes'].update(generation_options.custom_attributes)
            
            # Validate if requested
            validation_passed = True
            quality_score = 1.0
            if generation_options.validate_output:
                validation_passed, quality_score = self._validate_generated_symbol(symbol_data)
            
            # Create result
            result = GenerationResult(
                symbol_data=symbol_data,
                generation_type=generation_options.generation_type,
                category=generation_options.category,
                template_used=generation_options.template_name,
                validation_passed=validation_passed,
                quality_score=quality_score,
                generated_at=datetime.utcnow()
            )
            
            # Calculate generation time
            generation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.generation_time_ms = generation_time
            
            # Update statistics
            self._update_stats(result)
            
            # Cache result if requested
            if cache_result:
                self.generated_cache[cache_key] = result
            
            logger.info("Symbol generation completed",
                       generation_type=generation_options.generation_type.value,
                       category=generation_options.category.value,
                       validation_passed=validation_passed,
                       quality_score=quality_score,
                       generation_time_ms=generation_time)
            
            return result
            
        except Exception as e:
            logger.error("Symbol generation failed", error=str(e))
            raise GenerationError(f"Generation failed: {str(e)}")
    
    def _generate_from_template(self, options: GenerationOptions) -> Dict[str, Any]:
        """Generate symbol from template."""
        template_name = options.template_name
        if not template_name:
            # Select template based on category
            template_name = self._select_template_for_category(options.category)
        
        if template_name not in self.templates:
            raise GenerationError(f"Template not found: {template_name}")
        
        template = self.templates[template_name].copy()
        
        # Generate unique ID
        symbol_id = f"{options.category.value}_{str(uuid.uuid4())[:8]}"
        
        # Create symbol data
        symbol_data = {
            'id': symbol_id,
            'type': template['type'],
            'attributes': template['attributes'].copy(),
            'content': template['content'],
            'metadata': template['metadata'].copy(),
            'namespace': f"arx:{options.category.value}",
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return symbol_data
    
    def _generate_from_rules(self, options: GenerationOptions) -> Dict[str, Any]:
        """Generate symbol using rules."""
        # Get rule function for category
        rule_name = f"{options.category.value}_rule"
        rule_func = self.generation_rules.get(rule_name)
        
        if not rule_func:
            raise GenerationError(f"No generation rule found for category: {options.category.value}")
        
        # Generate symbol using rule
        symbol_data = rule_func(options)
        
        # Generate unique ID
        symbol_id = f"{options.category.value}_{str(uuid.uuid4())[:8]}"
        symbol_data['id'] = symbol_id
        symbol_data['namespace'] = f"arx:{options.category.value}"
        symbol_data['generated_at'] = datetime.utcnow().isoformat()
        
        return symbol_data
    
    def _generate_ai_symbol(self, options: GenerationOptions) -> Dict[str, Any]:
        """Generate symbol using AI (placeholder for future implementation)."""
        # For now, fall back to template-based generation
        logger.warning("AI generation not implemented, falling back to template-based generation")
        return self._generate_from_template(options)
    
    def _apply_electrical_rules(self, options: GenerationOptions) -> Dict[str, Any]:
        """Apply electrical generation rules."""
        # Generate electrical symbol based on rules
        symbol_type = 'rect'  # Default electrical symbol type
        attributes = {
            'x': 0, 'y': 0, 'width': 25, 'height': 25,
            'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
        }
        
        # Apply electrical-specific rules
        if 'outlet' in options.generation_rules:
            symbol_type = 'circle'
            attributes = {
                'cx': 12.5, 'cy': 12.5, 'r': 8,
                'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
            }
        elif 'switch' in options.generation_rules:
            attributes['height'] = 35
            attributes['width'] = 20
        
        return {
            'type': symbol_type,
            'attributes': attributes,
            'content': '',
            'metadata': {
                'category': 'electrical',
                'description': 'Generated electrical symbol'
            }
        }
    
    def _apply_mechanical_rules(self, options: GenerationOptions) -> Dict[str, Any]:
        """Apply mechanical generation rules."""
        symbol_type = 'circle'
        attributes = {
            'cx': 20, 'cy': 20, 'r': 15,
            'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
        }
        
        content = '<text x="20" y="25" text-anchor="middle" font-size="12">M</text>'
        
        return {
            'type': symbol_type,
            'attributes': attributes,
            'content': content,
            'metadata': {
                'category': 'mechanical',
                'description': 'Generated mechanical symbol'
            }
        }
    
    def _apply_plumbing_rules(self, options: GenerationOptions) -> Dict[str, Any]:
        """Apply plumbing generation rules."""
        symbol_type = 'rect'
        attributes = {
            'x': 5, 'y': 5, 'width': 30, 'height': 20,
            'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
        }
        
        content = '<text x="20" y="18" text-anchor="middle" font-size="10">P</text>'
        
        return {
            'type': symbol_type,
            'attributes': attributes,
            'content': content,
            'metadata': {
                'category': 'plumbing',
                'description': 'Generated plumbing symbol'
            }
        }
    
    def _apply_fire_alarm_rules(self, options: GenerationOptions) -> Dict[str, Any]:
        """Apply fire alarm generation rules."""
        symbol_type = 'rect'
        attributes = {
            'x': 0, 'y': 0, 'width': 25, 'height': 35,
            'fill': '#ff0000', 'stroke': '#000000', 'stroke-width': '2'
        }
        
        content = '<text x="12.5" y="22" text-anchor="middle" font-size="10" fill="#ffffff">F</text>'
        
        return {
            'type': symbol_type,
            'attributes': attributes,
            'content': content,
            'metadata': {
                'category': 'fire_alarm',
                'description': 'Generated fire alarm symbol'
            }
        }
    
    def _apply_hvac_rules(self, options: GenerationOptions) -> Dict[str, Any]:
        """Apply HVAC generation rules."""
        symbol_type = 'rect'
        attributes = {
            'x': 0, 'y': 0, 'width': 30, 'height': 25,
            'fill': '#ffffff', 'stroke': '#000000', 'stroke-width': '2'
        }
        
        content = '<text x="15" y="17" text-anchor="middle" font-size="12">H</text>'
        
        return {
            'type': symbol_type,
            'attributes': attributes,
            'content': content,
            'metadata': {
                'category': 'hvac',
                'description': 'Generated HVAC symbol'
            }
        }
    
    def _select_template_for_category(self, category: SymbolCategory) -> str:
        """Select appropriate template for category."""
        category_templates = {
            SymbolCategory.ELECTRICAL: 'electrical_switch',
            SymbolCategory.MECHANICAL: 'mechanical_pump',
            SymbolCategory.PLUMBING: 'plumbing_valve',
            SymbolCategory.FIRE_ALARM: 'fire_alarm_pull',
            SymbolCategory.HVAC: 'hvac_thermostat',
            SymbolCategory.GENERAL: 'electrical_switch'  # Default fallback
        }
        
        return category_templates.get(category, 'electrical_switch')
    
    def _validate_generated_symbol(self, symbol_data: Dict[str, Any]) -> Tuple[bool, float]:
        """Validate generated symbol and return quality score."""
        passed_checks = 0
        total_checks = len(self.quality_validators)
        
        for validator in self.quality_validators:
            try:
                if validator(symbol_data):
                    passed_checks += 1
            except Exception as e:
                logger.warning(f"Validation check failed: {e}")
        
        validation_passed = passed_checks == total_checks
        quality_score = passed_checks / total_checks if total_checks > 0 else 0.0
        
        return validation_passed, quality_score
    
    def _validate_symbol_structure(self, symbol_data: Dict[str, Any]) -> bool:
        """Validate symbol structure."""
        required_fields = ['id', 'type', 'attributes']
        return all(field in symbol_data for field in required_fields)
    
    def _validate_symbol_attributes(self, symbol_data: Dict[str, Any]) -> bool:
        """Validate symbol attributes."""
        attributes = symbol_data.get('attributes', {})
        return isinstance(attributes, dict) and len(attributes) > 0
    
    def _validate_symbol_content(self, symbol_data: Dict[str, Any]) -> bool:
        """Validate symbol content."""
        # Content is optional, so this always passes
        return True
    
    def _validate_symbol_metadata(self, symbol_data: Dict[str, Any]) -> bool:
        """Validate symbol metadata."""
        metadata = symbol_data.get('metadata', {})
        return isinstance(metadata, dict)
    
    def _merge_options(self, options: Optional[GenerationOptions]) -> GenerationOptions:
        """Merge options with defaults."""
        if options is None:
            return self.default_options
        
        # Create a new options object with merged values
        merged = GenerationOptions()
        for field in merged.__dataclass_fields__:
            user_value = getattr(options, field)
            default_value = getattr(self.default_options, field)
            setattr(merged, field, user_value if user_value is not None else default_value)
        
        return merged
    
    def _generate_cache_key(self, options: GenerationOptions) -> str:
        """Generate cache key for generation result."""
        import hashlib
        options_str = json.dumps({
            'generation_type': options.generation_type.value,
            'category': options.category.value,
            'template_name': options.template_name,
            'quality_level': options.quality_level,
            'include_metadata': options.include_metadata,
            'validate_output': options.validate_output,
            'optimize_generated': options.optimize_generated,
            'custom_attributes': options.custom_attributes,
            'generation_rules': options.generation_rules
        }, sort_keys=True)
        
        return hashlib.md5(options_str.encode()).hexdigest()
    
    def _update_stats(self, result: GenerationResult):
        """Update generation statistics."""
        self.stats['total_generations'] += 1
        if result.validation_passed:
            self.stats['successful_generations'] += 1
        else:
            self.stats['failed_generations'] += 1
        
        # Update average generation time
        total_time = self.stats['average_generation_time_ms'] * (self.stats['total_generations'] - 1)
        total_time += result.generation_time_ms
        self.stats['average_generation_time_ms'] = total_time / self.stats['total_generations']
    
    def add_template(self, name: str, template: Dict[str, Any]):
        """Add a custom template."""
        self.templates[name] = template
        logger.info("Custom template added", template_name=name)
    
    def add_generation_rule(self, name: str, rule_func: Callable):
        """Add a custom generation rule."""
        self.generation_rules[name] = rule_func
        logger.info("Custom generation rule added", rule_name=name)
    
    def add_quality_validator(self, validator_func: Callable):
        """Add a custom quality validator."""
        self.quality_validators.append(validator_func)
        logger.info("Custom quality validator added")
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return {
            'stats': self.stats,
            'templates_count': len(self.templates),
            'rules_count': len(self.generation_rules),
            'validators_count': len(self.quality_validators),
            'cache_size': len(self.generated_cache)
        }
    
    def clear_cache(self):
        """Clear the generation cache."""
        self.generated_cache.clear()
        logger.info("Generation cache cleared")
    
    def set_default_options(self, options: GenerationOptions):
        """Set default generation options."""
        self.default_options = options
        logger.info("Default generation options updated")


# Factory function for creating generator instances
def create_symbol_generator(default_options: Optional[GenerationOptions] = None) -> SVGXSymbolGenerator:
    """Create a new symbol generator instance."""
    return SVGXSymbolGenerator(default_options)


# Global generator instance
_symbol_generator = None


def get_symbol_generator() -> SVGXSymbolGenerator:
    """Get the global symbol generator instance."""
    global _symbol_generator
    if _symbol_generator is None:
        _symbol_generator = create_symbol_generator()
    return _symbol_generator 