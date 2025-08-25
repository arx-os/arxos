"""
Suggestion Engine - Help field workers identify building components
Lightweight AI assistance for component recognition and suggestions
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class ComponentSuggestion:
    """Component suggestion for field workers"""
    component_type: str
    confidence: float
    properties: Dict[str, Any]
    reasoning: str
    alternatives: List[str]

class SuggestionEngine:
    """
    Lightweight suggestion engine for building component identification
    Uses simple pattern matching and common sense rather than complex AI
    """
    
    def __init__(self):
        # Component recognition patterns
        self.component_patterns = {
            'electrical_outlet': [
                r'outlet', r'socket', r'receptacle', r'plug',
                r'120v', r'220v', r'voltage', r'electrical'
            ],
            'electrical_switch': [
                r'switch', r'toggle', r'light.*switch', r'power.*switch',
                r'on.*off', r'control'
            ],
            'electrical_panel': [
                r'panel', r'breaker.*box', r'electrical.*panel',
                r'fuse.*box', r'circuit.*breaker'
            ],
            'hvac_unit': [
                r'hvac', r'air.*conditioner', r'heating', r'cooling',
                r'unit', r'system', r'thermostat'
            ],
            'plumbing_fixture': [
                r'sink', r'faucet', r'toilet', r'shower', r'bathtub',
                r'fixture', r'plumbing', r'water'
            ],
            'fire_sprinkler': [
                r'sprinkler', r'fire.*protection', r'fire.*suppression',
                r'water.*spray', r'fire.*system'
            ]
        }
        
        # Common component properties
        self.default_properties = {
            'electrical_outlet': {
                'voltage': 120,
                'amperage': 15,
                'circuit_type': 'general'
            },
            'electrical_switch': {
                'voltage': 120,
                'amperage': 15,
                'switch_type': 'toggle'
            },
            'hvac_unit': {
                'capacity_tons': 5,
                'efficiency': 0.8,
                'fuel_type': 'electric'
            }
        }
    
    async def suggest_component(self, 
                              input_data: Dict[str, Any],
                              photo_data: Optional[bytes] = None) -> List[ComponentSuggestion]:
        """
        Suggest component types based on field worker input
        
        Args:
            input_data: Field worker input (text, properties, etc.)
            photo_data: Optional photo for visual analysis
            
        Returns:
            List of component suggestions with confidence scores
        """
        try:
            suggestions = []
            
            # Extract text input
            text_input = self._extract_text_input(input_data)
            
            # Generate text-based suggestions
            text_suggestions = self._suggest_from_text(text_input)
            suggestions.extend(text_suggestions)
            
            # Generate property-based suggestions
            property_suggestions = self._suggest_from_properties(input_data.get('properties', {}))
            suggestions.extend(property_suggestions)
            
            # Generate location-based suggestions
            location_suggestions = self._suggest_from_location(input_data.get('location', {}))
            suggestions.extend(location_suggestions)
            
            # Remove duplicates and sort by confidence
            unique_suggestions = self._deduplicate_suggestions(suggestions)
            unique_suggestions.sort(key=lambda x: x.confidence, reverse=True)
            
            return unique_suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Suggestion generation error: {e}")
            return []
    
    def _extract_text_input(self, input_data: Dict[str, Any]) -> str:
        """Extract text input from various sources"""
        text_parts = []
        
        # Check for direct text input
        if 'text' in input_data:
            text_parts.append(str(input_data['text']))
        
        # Check for component name
        if 'name' in input_data:
            text_parts.append(str(input_data['name']))
        
        # Check for description
        if 'description' in input_data:
            text_parts.append(str(input_data['description']))
        
        # Check for notes
        if 'notes' in input_data:
            text_parts.append(str(input_data['notes']))
        
        return ' '.join(text_parts).lower()
    
    def _suggest_from_text(self, text: str) -> List[ComponentSuggestion]:
        """Generate suggestions based on text input"""
        suggestions = []
        
        if not text:
            return suggestions
        
        # Check each component pattern
        for component_type, patterns in self.component_patterns.items():
            confidence = 0.0
            matched_patterns = []
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matched_patterns.append(pattern)
                    confidence += 0.3  # Base confidence per pattern match
            
            if confidence > 0:
                # Cap confidence at 0.9 for text-only suggestions
                confidence = min(confidence, 0.9)
                
                suggestion = ComponentSuggestion(
                    component_type=component_type,
                    confidence=confidence,
                    properties=self.default_properties.get(component_type, {}),
                    reasoning=f"Text matches patterns: {', '.join(matched_patterns)}",
                    alternatives=self._get_alternatives(component_type)
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_from_properties(self, properties: Dict[str, Any]) -> List[ComponentSuggestion]:
        """Generate suggestions based on component properties"""
        suggestions = []
        
        if not properties:
            return suggestions
        
        # Check for electrical properties
        if 'voltage' in properties or 'amperage' in properties:
            voltage = properties.get('voltage', 120)
            amperage = properties.get('amperage', 15)
            
            if voltage <= 480 and amperage <= 1000:
                suggestion = ComponentSuggestion(
                    component_type='electrical_outlet',
                    confidence=0.8,
                    properties={'voltage': voltage, 'amperage': amperage},
                    reasoning=f"Electrical properties detected (voltage: {voltage}V, amperage: {amperage}A)",
                    alternatives=['electrical_switch', 'electrical_panel']
                )
                suggestions.append(suggestion)
        
        # Check for HVAC properties
        if 'capacity_tons' in properties or 'efficiency' in properties:
            capacity = properties.get('capacity_tons', 5)
            efficiency = properties.get('efficiency', 0.8)
            
            if 0 < capacity <= 100 and 0 < efficiency <= 1.0:
                suggestion = ComponentSuggestion(
                    component_type='hvac_unit',
                    confidence=0.85,
                    properties={'capacity_tons': capacity, 'efficiency': efficiency},
                    reasoning=f"HVAC properties detected (capacity: {capacity} tons, efficiency: {efficiency})",
                    alternatives=['thermostat', 'duct']
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_from_location(self, location: Dict[str, Any]) -> List[ComponentSuggestion]:
        """Generate suggestions based on location context"""
        suggestions = []
        
        if not location:
            return suggestions
        
        room = location.get('room', '').lower()
        floor = location.get('floor', '').lower()
        
        # Kitchen context
        if 'kitchen' in room or 'cafeteria' in room:
            suggestions.append(ComponentSuggestion(
                component_type='plumbing_fixture',
                confidence=0.7,
                properties={'fixture_type': 'sink'},
                reasoning="Kitchen location suggests plumbing fixture",
                alternatives=['electrical_outlet', 'hvac_unit']
            ))
        
        # Mechanical room context
        if 'mechanical' in room or 'utility' in room:
            suggestions.append(ComponentSuggestion(
                component_type='hvac_unit',
                confidence=0.8,
                properties={'capacity_tons': 10, 'efficiency': 0.85},
                reasoning="Mechanical room location suggests HVAC equipment",
                alternatives=['electrical_panel', 'plumbing_fixture']
            ))
        
        # Electrical room context
        if 'electrical' in room or 'panel' in room:
            suggestions.append(ComponentSuggestion(
                component_type='electrical_panel',
                confidence=0.9,
                properties={'voltage': 480, 'amperage': 400},
                reasoning="Electrical room location suggests electrical panel",
                alternatives=['electrical_outlet', 'electrical_switch']
            ))
        
        return suggestions
    
    def _get_alternatives(self, component_type: str) -> List[str]:
        """Get alternative component types"""
        alternatives_map = {
            'electrical_outlet': ['electrical_switch', 'electrical_panel'],
            'electrical_switch': ['electrical_outlet', 'electrical_panel'],
            'electrical_panel': ['electrical_outlet', 'electrical_switch'],
            'hvac_unit': ['thermostat', 'duct', 'vent'],
            'plumbing_fixture': ['pipe', 'valve', 'drain'],
            'fire_sprinkler': ['fire_alarm', 'smoke_detector']
        }
        
        return alternatives_map.get(component_type, [])
    
    def _deduplicate_suggestions(self, suggestions: List[ComponentSuggestion]) -> List[ComponentSuggestion]:
        """Remove duplicate suggestions and merge confidence scores"""
        unique_suggestions = {}
        
        for suggestion in suggestions:
            if suggestion.component_type in unique_suggestions:
                # Merge with existing suggestion
                existing = unique_suggestions[suggestion.component_type]
                existing.confidence = max(existing.confidence, suggestion.confidence)
                
                # Merge properties
                for key, value in suggestion.properties.items():
                    if key not in existing.properties:
                        existing.properties[key] = value
                
                # Merge reasoning
                if suggestion.reasoning not in existing.reasoning:
                    existing.reasoning += f"; {suggestion.reasoning}"
            else:
                unique_suggestions[suggestion.component_type] = suggestion
        
        return list(unique_suggestions.values())
