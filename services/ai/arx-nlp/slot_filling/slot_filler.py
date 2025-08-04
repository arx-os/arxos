"""
Slot Filler for Arxos NLP System

This module provides slot filling functionality for extracting parameters
from natural language input for building operations.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ..models.nlp_models import Slot, SlotResult, SlotType, IntentType


@dataclass
class SlotPattern:
    """Pattern for slot extraction"""
    pattern: str
    slot_type: SlotType
    value_type: str = "string"
    validation_rules: Dict[str, Any] = None
    confidence_boost: float = 0.0
    
    def __post_init__(self):
        if self.validation_rules is None:
            self.validation_rules = {}


class SlotFiller:
    """
    Slot Filler for extracting parameters from natural language
    
    This class provides:
    - Pattern-based slot extraction
    - Value validation
    - Confidence scoring
    - Context-aware slot filling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Slot Filler
        
        Args:
            config: Configuration dictionary for slot filling
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Load patterns
        self._load_patterns()
        
    def _load_patterns(self):
        """Load slot extraction patterns"""
        self.slot_patterns = [
            # Object type patterns
            SlotPattern(r'\b(room|bedroom|bathroom|kitchen|living|office)\b', SlotType.OBJECT_TYPE, "room", confidence_boost=0.1),
            SlotPattern(r'\b(wall|door|window|fixture|equipment|system)\b', SlotType.OBJECT_TYPE, "building_element", confidence_boost=0.1),
            SlotPattern(r'\b(floor|building|site)\b', SlotType.OBJECT_TYPE, "structure", confidence_boost=0.1),
            
            # Location patterns
            SlotPattern(r'on\s+floor\s+(\d+)', SlotType.LOCATION, "floor_number", confidence_boost=0.05),
            SlotPattern(r'in\s+(\w+)', SlotType.LOCATION, "room_name", confidence_boost=0.05),
            SlotPattern(r'at\s+(\w+)', SlotType.LOCATION, "position", confidence_boost=0.05),
            SlotPattern(r'to\s+(\w+)', SlotType.LOCATION, "destination", confidence_boost=0.05),
            
            # Property patterns
            SlotPattern(r'color\s+(\w+)', SlotType.PROPERTY, "color", confidence_boost=0.1),
            SlotPattern(r'size\s+(\w+)', SlotType.PROPERTY, "size", confidence_boost=0.05),
            SlotPattern(r'type\s+(\w+)', SlotType.PROPERTY, "type", confidence_boost=0.05),
            SlotPattern(r'width\s+(\d+)', SlotType.PROPERTY, "width", confidence_boost=0.05),
            SlotPattern(r'height\s+(\d+)', SlotType.PROPERTY, "height", confidence_boost=0.05),
            SlotPattern(r'length\s+(\d+)', SlotType.PROPERTY, "length", confidence_boost=0.05),
            
            # Value patterns
            SlotPattern(r'(\d+)\s*(?:x|by)\s*(\d+)', SlotType.VALUE, "dimensions", confidence_boost=0.1),
            SlotPattern(r'(\d+)\s*(?:feet|ft)', SlotType.VALUE, "distance", confidence_boost=0.05),
            SlotPattern(r'(\d+)\s*(?:inches|in)', SlotType.VALUE, "distance", confidence_boost=0.05),
            SlotPattern(r'(\d+)\s*(?:meters|m)', SlotType.VALUE, "distance", confidence_boost=0.05),
            
            # Format patterns
            SlotPattern(r'format\s+(\w+)', SlotType.FORMAT, "format", confidence_boost=0.05),
            SlotPattern(r'as\s+(\w+)', SlotType.FORMAT, "format", confidence_boost=0.05),
            SlotPattern(r'in\s+(\w+)\s+format', SlotType.FORMAT, "format", confidence_boost=0.05),
            
            # Target patterns
            SlotPattern(r'to\s+(\w+)', SlotType.TARGET, "target", confidence_boost=0.05),
            SlotPattern(r'target\s+(\w+)', SlotType.TARGET, "target", confidence_boost=0.05),
            SlotPattern(r'destination\s+(\w+)', SlotType.TARGET, "target", confidence_boost=0.05),
            
            # Source patterns
            SlotPattern(r'from\s+(\w+)', SlotType.SOURCE, "source", confidence_boost=0.05),
            SlotPattern(r'source\s+(\w+)', SlotType.SOURCE, "source", confidence_boost=0.05),
            SlotPattern(r'origin\s+(\w+)', SlotType.SOURCE, "source", confidence_boost=0.05),
            
            # Condition patterns
            SlotPattern(r'if\s+(\w+)', SlotType.CONDITION, "condition", confidence_boost=0.05),
            SlotPattern(r'when\s+(\w+)', SlotType.CONDITION, "condition", confidence_boost=0.05),
            SlotPattern(r'where\s+(\w+)', SlotType.CONDITION, "condition", confidence_boost=0.05),
            SlotPattern(r'(\w+)\s+only', SlotType.CONDITION, "condition", confidence_boost=0.05),
            
            # Unit patterns
            SlotPattern(r'(\d+)\s*(feet|ft|inches|in|meters|m)', SlotType.UNIT, "unit", confidence_boost=0.05),
            SlotPattern(r'(\w+)\s+units', SlotType.UNIT, "unit", confidence_boost=0.05),
            
            # Object ID patterns
            SlotPattern(r'id\s+(\w+)', SlotType.OBJECT_ID, "object_id", confidence_boost=0.1),
            SlotPattern(r'object\s+(\w+)', SlotType.OBJECT_ID, "object_id", confidence_boost=0.05),
            SlotPattern(r'element\s+(\w+)', SlotType.OBJECT_ID, "object_id", confidence_boost=0.05)
        ]
        
    def extract_slots(self, text: str, intent_type: IntentType) -> SlotResult:
        """
        Extract slots from natural language text
        
        Args:
            text: Natural language input text
            intent_type: Detected intent type
            
        Returns:
            SlotResult with extracted slots
        """
        text_lower = text.lower().strip()
        slots = []
        
        # Extract slots using patterns
        for pattern in self.slot_patterns:
            matches = re.finditer(pattern.pattern, text_lower)
            for match in matches:
                slot_value = match.group(1) if match.groups() else match.group(0)
                
                # Validate slot value
                if self._validate_slot_value(slot_value, pattern):
                    slot = Slot(
                        slot_type=pattern.slot_type,
                        value=slot_value,
                        value_type=pattern.value_type,
                        confidence=0.8 + pattern.confidence_boost,  # Base confidence for pattern matches
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    slots.append(slot)
        
        # Extract additional slots based on intent type
        additional_slots = self._extract_intent_specific_slots(text_lower, intent_type)
        slots.extend(additional_slots)
        
        # Resolve object references
        resolved_slots = self._resolve_object_references(slots)
        
        # Remove duplicates and merge overlapping slots
        final_slots = self._merge_overlapping_slots(resolved_slots)
        
        return SlotResult(
            slots=final_slots,
            confidence=min(1.0, len(final_slots) * 0.1 + 0.5)
        )
    
    def _validate_slot_value(self, value: str, pattern: SlotPattern) -> bool:
        """Validate slot value against pattern rules"""
        if not value or value.strip() == '':
            return False
        
        # Apply validation rules
        rules = pattern.validation_rules
        
        # Check minimum length
        if 'min_length' in rules and len(value) < rules['min_length']:
            return False
        
        # Check maximum length
        if 'max_length' in rules and len(value) > rules['max_length']:
            return False
        
        # Check pattern match
        if 'pattern' in rules and not re.match(rules['pattern'], value):
            return False
        
        # Check allowed values
        if 'allowed_values' in rules and value not in rules['allowed_values']:
            return False
        
        # Check numeric range
        if 'min_value' in rules or 'max_value' in rules:
            try:
                num_value = float(value)
                if 'min_value' in rules and num_value < rules['min_value']:
                    return False
                if 'max_value' in rules and num_value > rules['max_value']:
                    return False
            except ValueError:
                return False
        
        return True
    
    def _extract_intent_specific_slots(self, text: str, intent_type: IntentType) -> List[Slot]:
        """Extract slots specific to intent type"""
        slots = []
        
        if intent_type == IntentType.CREATE:
            # Extract object properties for creation
            size_match = re.search(r'(\d+)\s*(?:x|by)\s*(\d+)', text)
            if size_match:
                slots.append(Slot(
                    slot_type=SlotType.VALUE,
                    value=f"{size_match.group(1)}x{size_match.group(2)}",
                    value_type="dimensions",
                    confidence=0.9
                ))
            
            color_match = re.search(r'(red|green|blue|yellow|black|white|gray|grey)', text)
            if color_match:
                slots.append(Slot(
                    slot_type=SlotType.PROPERTY,
                    value=color_match.group(1),
                    value_type="color",
                    confidence=0.9
                ))
            
            # Extract room type
            room_match = re.search(r'(bedroom|bathroom|kitchen|living|office|dining|study)', text)
            if room_match:
                slots.append(Slot(
                    slot_type=SlotType.OBJECT_TYPE,
                    value=room_match.group(1),
                    value_type="room_type",
                    confidence=0.9
                ))
        
        elif intent_type == IntentType.MODIFY:
            # Extract property changes
            property_match = re.search(r'(\w+)\s+to\s+(\w+)', text)
            if property_match:
                slots.append(Slot(
                    slot_type=SlotType.PROPERTY,
                    value=property_match.group(1),
                    value_type="property_name",
                    confidence=0.8
                ))
                slots.append(Slot(
                    slot_type=SlotType.VALUE,
                    value=property_match.group(2),
                    value_type="new_value",
                    confidence=0.8
                ))
            
            # Extract dimension changes
            dim_match = re.search(r'(\w+)\s+(\d+)\s*(?:x|by)\s*(\d+)', text)
            if dim_match:
                slots.append(Slot(
                    slot_type=SlotType.PROPERTY,
                    value=dim_match.group(1),
                    value_type="dimension_property",
                    confidence=0.8
                ))
                slots.append(Slot(
                    slot_type=SlotType.VALUE,
                    value=f"{dim_match.group(2)}x{dim_match.group(3)}",
                    value_type="new_dimensions",
                    confidence=0.8
                ))
        
        elif intent_type == IntentType.QUERY:
            # Extract query filters
            filter_match = re.search(r'(\w+)\s+(\w+)', text)
            if filter_match:
                slots.append(Slot(
                    slot_type=SlotType.CONDITION,
                    value=f"{filter_match.group(1)} {filter_match.group(2)}",
                    value_type="filter",
                    confidence=0.7
                ))
            
            # Extract location queries
            location_match = re.search(r'on\s+floor\s+(\d+)', text)
            if location_match:
                slots.append(Slot(
                    slot_type=SlotType.LOCATION,
                    value=location_match.group(1),
                    value_type="floor_number",
                    confidence=0.8
                ))
        
        elif intent_type == IntentType.EXPORT:
            # Extract export format
            format_match = re.search(r'(svg|pdf|dxf|ifc|json)', text)
            if format_match:
                slots.append(Slot(
                    slot_type=SlotType.FORMAT,
                    value=format_match.group(1),
                    value_type="export_format",
                    confidence=0.9
                ))
        
        elif intent_type == IntentType.MOVE:
            # Extract destination
            dest_match = re.search(r'to\s+(\w+)', text)
            if dest_match:
                slots.append(Slot(
                    slot_type=SlotType.TARGET,
                    value=dest_match.group(1),
                    value_type="destination",
                    confidence=0.8
                ))
        
        return slots
    
    def _resolve_object_references(self, slots: List[Slot]) -> List[Slot]:
        """Resolve object references using context"""
        resolved_slots = []
        
        # Object type mappings
        object_mappings = {
            'room': 'room',
            'bedroom': 'room',
            'bathroom': 'room',
            'kitchen': 'room',
            'living': 'room',
            'office': 'room',
            'wall': 'wall',
            'door': 'door',
            'window': 'window',
            'fixture': 'fixture',
            'equipment': 'equipment',
            'system': 'system',
            'floor': 'floor',
            'building': 'building',
            'site': 'site'
        }
        
        for slot in slots:
            if slot.slot_type == SlotType.OBJECT_TYPE:
                # Map object names to standard types
                mapped_value = object_mappings.get(slot.value, slot.value)
                resolved_slot = Slot(
                    slot_type=slot.slot_type,
                    value=mapped_value,
                    value_type=slot.value_type,
                    confidence=slot.confidence,
                    start_pos=slot.start_pos,
                    end_pos=slot.end_pos,
                    original_value=slot.value
                )
                resolved_slots.append(resolved_slot)
            else:
                resolved_slots.append(slot)
        
        return resolved_slots
    
    def _merge_overlapping_slots(self, slots: List[Slot]) -> List[Slot]:
        """Merge overlapping slots and remove duplicates"""
        if not slots:
            return []
        
        # Sort by start position
        sorted_slots = sorted(slots, key=lambda x: x.start_pos)
        merged_slots = []
        
        for slot in sorted_slots:
            # Check if this slot overlaps with any existing slot
            overlapping = False
            for existing_slot in merged_slots:
                if (slot.start_pos < existing_slot.end_pos and 
                    slot.end_pos > existing_slot.start_pos):
                    # Overlap detected, keep the one with higher confidence
                    if slot.confidence > existing_slot.confidence:
                        merged_slots.remove(existing_slot)
                        merged_slots.append(slot)
                    overlapping = True
                    break
            
            if not overlapping:
                merged_slots.append(slot)
        
        return merged_slots
    
    def get_suggestions(self, partial_text: str) -> List[str]:
        """
        Get slot suggestions based on partial text
        
        Args:
            partial_text: Partial natural language input
            
        Returns:
            List of suggested completions
        """
        suggestions = []
        partial_lower = partial_text.lower().strip()
        
        # Get slot suggestions based on patterns
        for pattern in self.slot_patterns:
            if partial_lower in pattern.pattern.lower():
                suggestions.append(pattern.pattern.replace(r'(\w+)', '<value>'))
        
        # Get common property suggestions
        common_properties = [
            'color', 'size', 'type', 'width', 'height', 'length',
            'position', 'location', 'format', 'target', 'source'
        ]
        
        for prop in common_properties:
            if partial_lower in prop or prop.startswith(partial_lower):
                suggestions.append(f"{prop} <value>")
        
        return list(set(suggestions))[:10]  # Limit to 10 unique suggestions
    
    def validate_slot(self, slot: Slot) -> bool:
        """
        Validate extracted slot
        
        Args:
            slot: Slot to validate
            
        Returns:
            True if slot is valid, False otherwise
        """
        # Check if slot type is supported
        if slot.slot_type not in [e.value for e in SlotType]:
            return False
        
        # Check confidence threshold
        if slot.confidence < 0.1:
            return False
        
        # Check value is not empty
        if not slot.value or slot.value.strip() == '':
            return False
        
        return True
    
    def get_slot_help(self, slot_type: SlotType) -> str:
        """
        Get help information for specific slot type
        
        Args:
            slot_type: Slot type for help
            
        Returns:
            Help text for the slot type
        """
        help_texts = {
            SlotType.OBJECT_TYPE: "Object types: room, wall, door, window, fixture, equipment, system",
            SlotType.OBJECT_ID: "Object IDs: unique identifiers for building elements",
            SlotType.LOCATION: "Locations: floor numbers, room names, positions",
            SlotType.PROPERTY: "Properties: color, size, type, dimensions",
            SlotType.VALUE: "Values: dimensions, distances, measurements",
            SlotType.UNIT: "Units: feet, inches, meters, etc.",
            SlotType.FORMAT: "Formats: svg, pdf, dxf, ifc, json",
            SlotType.TARGET: "Targets: destinations for move operations",
            SlotType.SOURCE: "Sources: origins for import operations",
            SlotType.CONDITION: "Conditions: filters for query operations"
        }
        
        return help_texts.get(slot_type, f"No help available for slot type: {slot_type}")


# Convenience function for quick slot extraction
def extract_slots(text: str, intent_type: IntentType, config: Optional[Dict[str, Any]] = None) -> SlotResult:
    """
    Convenience function for quick slot extraction
    
    Args:
        text: Natural language input
        intent_type: Intent type
        config: Optional configuration
        
    Returns:
        SlotResult with extracted slots
    """
    filler = SlotFiller(config)
    return filler.extract_slots(text, intent_type) 