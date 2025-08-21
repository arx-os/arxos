"""
Validation Engine for processing field validations and propagating confidence
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time

from models.arxobject import ArxObject, ConfidenceScore, ValidationState


@dataclass
class ValidationImpact:
    """Impact of a validation on the system"""
    object_id: str
    confidence_improvement: float
    cascaded_count: int
    cascaded_objects: List[str]
    processing_time: float


class ValidationEngine:
    """
    Engine for processing validations and managing pattern learning
    """
    
    def __init__(self):
        self.patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.validation_history: List[Dict[str, Any]] = []
    
    async def process_validation(self, validation_data: Dict[str, Any]) -> ValidationImpact:
        """
        Process a field validation and propagate confidence improvements
        
        Args:
            validation_data: Validation data from field
            
        Returns:
            ValidationImpact describing the effect of the validation
        """
        start_time = time.time()
        
        # Extract validation details
        object_id = validation_data.get("object_id")
        validation_type = validation_data.get("type")
        confidence_boost = validation_data.get("confidence_boost", 0.1)
        
        # Track cascaded improvements
        cascaded_objects = []
        
        # Apply confidence boost to validated object
        # In production, this would update the database
        initial_improvement = confidence_boost
        
        # Find related objects that could benefit from this validation
        # For example, if a wall is validated, nearby walls might also benefit
        related_objects = self._find_related_objects(object_id, validation_type)
        
        for related_id in related_objects:
            # Apply reduced confidence boost to related objects
            cascaded_boost = confidence_boost * 0.5
            cascaded_objects.append(related_id)
        
        # Record validation in history
        self.validation_history.append({
            "object_id": object_id,
            "type": validation_type,
            "timestamp": time.time(),
            "impact": len(cascaded_objects)
        })
        
        # Learn from this validation for future use
        self._update_patterns(validation_data)
        
        processing_time = time.time() - start_time
        
        return ValidationImpact(
            object_id=object_id,
            confidence_improvement=initial_improvement,
            cascaded_count=len(cascaded_objects),
            cascaded_objects=cascaded_objects,
            processing_time=processing_time
        )
    
    def _find_related_objects(self, object_id: str, validation_type: str) -> List[str]:
        """
        Find objects that could benefit from this validation
        
        Args:
            object_id: ID of validated object
            validation_type: Type of validation
            
        Returns:
            List of related object IDs
        """
        # In production, this would query the database for spatially
        # or functionally related objects
        related = []
        
        # Example logic: find objects of same type within proximity
        # This is simplified - actual implementation would use spatial queries
        if validation_type == "wall":
            # Find nearby walls that might have similar properties
            related = [f"wall_{i}" for i in range(3)]  # Mock data
        elif validation_type == "door":
            # Find connected walls
            related = [f"wall_connected_{i}" for i in range(2)]  # Mock data
        
        return related
    
    def _update_patterns(self, validation_data: Dict[str, Any]):
        """
        Update pattern library based on validation
        
        Args:
            validation_data: Validation data to learn from
        """
        building_type = validation_data.get("building_type", "general")
        object_type = validation_data.get("object_type")
        
        if building_type not in self.patterns:
            self.patterns[building_type] = []
        
        # Create pattern from validation
        pattern = {
            "object_type": object_type,
            "confidence_threshold": 0.8,
            "validated_properties": validation_data.get("properties", {}),
            "occurrence_count": 1,
            "last_updated": time.time()
        }
        
        # Check if similar pattern exists
        existing = False
        for p in self.patterns[building_type]:
            if p["object_type"] == object_type:
                # Update existing pattern
                p["occurrence_count"] += 1
                p["last_updated"] = time.time()
                existing = True
                break
        
        if not existing:
            self.patterns[building_type].append(pattern)
    
    def get_patterns(self, building_type: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get learned patterns for a building type
        
        Args:
            building_type: Type of building
            
        Returns:
            List of patterns or None if not found
        """
        return self.patterns.get(building_type)
    
    def apply_patterns(
        self, 
        objects: List[ArxObject], 
        building_type: str
    ) -> List[ArxObject]:
        """
        Apply learned patterns to improve confidence of new objects
        
        Args:
            objects: List of ArxObjects to enhance
            building_type: Type of building
            
        Returns:
            Enhanced objects with improved confidence
        """
        patterns = self.get_patterns(building_type)
        if not patterns:
            return objects
        
        for obj in objects:
            for pattern in patterns:
                if obj.type == pattern["object_type"]:
                    # Apply pattern-based confidence boost
                    boost = min(0.1, pattern["occurrence_count"] * 0.01)
                    obj.confidence.classification += boost
                    obj.confidence.properties += boost * 0.5
                    # Calculate weighted average
                    obj.confidence.overall = (
                        obj.confidence.classification * 0.4 +
                        obj.confidence.position * 0.3 +
                        obj.confidence.properties * 0.2 +
                        obj.confidence.relationships * 0.1
                    )
        
        return objects