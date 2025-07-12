"""
Classification service for BIM element recognition.
"""

import re
from typing import Dict, Any, List, Optional
from enum import Enum

from models.bim import BIMElement


class ElementType(Enum):
    """BIM element types."""
    ROOM = "room"
    WALL = "wall"
    DOOR = "door"
    WINDOW = "window"
    DEVICE = "device"
    ANNOTATION = "annotation"
    UNKNOWN = "unknown"


class BIMClassifier:
    """Classifier for BIM element recognition."""
    
    def __init__(self):
        self.element_patterns = {
            ElementType.ROOM: [
                r'\broom\b', r'\boffice\b', r'\bconference\b', r'\bbathroom\b',
                r'\bkitchen\b', r'\bcloset\b', r'\bhallway\b', r'\bcorridor\b'
            ],
            ElementType.WALL: [
                r'\bwall\b', r'\bpartition\b', r'\bbarrier\b', r'\bdivider\b'
            ],
            ElementType.DOOR: [
                r'\bdoor\b', r'\bentrance\b', r'\bexit\b', r'\bopening\b'
            ],
            ElementType.WINDOW: [
                r'\bwindow\b', r'\bglazing\b', r'\baperture\b'
            ],
            ElementType.DEVICE: [
                r'\bhvac\b', r'\bvent\b', r'\boutlet\b', r'\bswitch\b',
                r'\boutlet\b', r'\bpanel\b', r'\bunit\b', r'\bdevice\b'
            ]
        }
    
    def classify_element(self, element: BIMElement) -> ElementType:
        """
        Classify BIM element based on its properties.
        
        Args:
            element: BIM element to classify
            
        Returns:
            Classified element type
        """
        # Check element type directly
        if hasattr(element, 'element_type'):
            element_type = element.element_type.lower()
            for elem_type, patterns in self.element_patterns.items():
                if element_type == elem_type.value:
                    return elem_type
        
        # Check element name
        if element.name:
            name_lower = element.name.lower()
            for elem_type, patterns in self.element_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, name_lower):
                        return elem_type
        
        # Check properties
        if element.properties:
            for key, value in element.properties.items():
                key_lower = key.lower()
                value_lower = str(value).lower()
                
                for elem_type, patterns in self.element_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, key_lower) or re.search(pattern, value_lower):
                            return elem_type
        
        # Check geometry properties
        if element.geometry and element.geometry.properties:
            for key, value in element.geometry.properties.items():
                key_lower = key.lower()
                value_lower = str(value).lower()
                
                for elem_type, patterns in self.element_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, key_lower) or re.search(pattern, value_lower):
                            return elem_type
        
        return ElementType.UNKNOWN
    
    def classify_elements(self, elements: List[BIMElement]) -> Dict[ElementType, List[BIMElement]]:
        """
        Classify multiple BIM elements.
        
        Args:
            elements: List of BIM elements to classify
            
        Returns:
            Dictionary of element types to lists of elements
        """
        classified = {elem_type: [] for elem_type in ElementType}
        
        for element in elements:
            element_type = self.classify_element(element)
            classified[element_type].append(element)
        
        return classified
    
    def get_element_confidence(self, element: BIMElement) -> float:
        """
        Get confidence score for element classification.
        
        Args:
            element: BIM element to evaluate
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.0
        
        # Check element type match
        if hasattr(element, 'element_type'):
            element_type = element.element_type.lower()
            for elem_type, patterns in self.element_patterns.items():
                if element_type == elem_type.value:
                    confidence += 0.4
                    break
        
        # Check name match
        if element.name:
            name_lower = element.name.lower()
            for elem_type, patterns in self.element_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, name_lower):
                        confidence += 0.3
                        break
        
        # Check properties match
        if element.properties:
            for key, value in element.properties.items():
                key_lower = key.lower()
                value_lower = str(value).lower()
                
                for elem_type, patterns in self.element_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, key_lower) or re.search(pattern, value_lower):
                            confidence += 0.2
                            break
        
        # Check geometry properties
        if element.geometry and element.geometry.properties:
            for key, value in element.geometry.properties.items():
                key_lower = key.lower()
                value_lower = str(value).lower()
                
                for elem_type, patterns in self.element_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, key_lower) or re.search(pattern, value_lower):
                            confidence += 0.1
                            break
        
        return min(confidence, 1.0)
    
    def validate_classification(self, element: BIMElement, 
                              expected_type: ElementType) -> bool:
        """
        Validate element classification against expected type.
        
        Args:
            element: BIM element to validate
            expected_type: Expected element type
            
        Returns:
            True if classification matches expected type
        """
        classified_type = self.classify_element(element)
        return classified_type == expected_type 