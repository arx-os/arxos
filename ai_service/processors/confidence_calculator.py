"""
Confidence calculation engine for ArxObject extraction
Implements multi-dimensional confidence scoring
"""

from typing import Dict, Any, Optional, List
import numpy as np

from models.arxobject import ConfidenceScore, ArxObjectType


class ConfidenceCalculator:
    """
    Calculate multi-dimensional confidence scores for ArxObjects
    Based on extraction method, data quality, and context
    """
    
    def __init__(self):
        # Base confidence by extraction method
        self.method_confidence = {
            "vector": 0.85,      # High confidence from vector graphics
            "text": 0.70,        # Moderate from text analysis
            "raster": 0.60,      # Lower from image processing
            "inference": 0.50,   # Lowest from inference
            "validated": 0.95    # Highest from field validation
        }
        
        # Type classification confidence
        self.type_confidence = {
            ArxObjectType.WALL: 0.80,           # Easy to identify
            ArxObjectType.COLUMN: 0.75,         # Fairly distinctive
            ArxObjectType.ROOM: 0.85,           # Usually labeled
            ArxObjectType.DOOR: 0.70,           # Standard symbols
            ArxObjectType.WINDOW: 0.70,         # Standard symbols
            ArxObjectType.ELECTRICAL_PANEL: 0.65,  # Requires context
            ArxObjectType.HVAC_UNIT: 0.60,      # Variable representation
            ArxObjectType.PLUMBING_FIXTURE: 0.65,  # Standard symbols
            ArxObjectType.STAIRWELL: 0.75,          # Distinctive pattern
            ArxObjectType.ELEVATOR_SHAFT: 0.80        # Usually labeled
        }
    
    def calculate_drawing_confidence(
        self,
        drawing: Dict,
        obj_type: ArxObjectType,
        base_confidence: float
    ) -> ConfidenceScore:
        """
        Calculate confidence for object extracted from vector drawing
        
        Args:
            drawing: Drawing dict from PyMuPDF
            obj_type: Identified object type
            base_confidence: Initial confidence from classification
        
        Returns:
            Multi-dimensional confidence score
        """
        
        # Classification confidence
        type_conf = self.type_confidence.get(obj_type, 0.5)
        classification = min(base_confidence * type_conf * self.method_confidence["vector"], 1.0)
        
        # Position confidence (vector graphics are precise)
        has_precise_coords = len(drawing.get("items", [])) > 0
        position = 0.90 if has_precise_coords else 0.70
        
        # Properties confidence (based on available attributes)
        properties_available = sum([
            1 if drawing.get("width") else 0,
            1 if drawing.get("color") else 0,
            1 if drawing.get("fill") else 0,
            1 if drawing.get("opacity") else 0,
        ])
        properties = 0.4 + (properties_available * 0.15)
        
        # Relationships confidence (not yet established)
        relationships = 0.30  # Low initial confidence
        
        # Create score
        score = ConfidenceScore(
            classification=classification,
            position=position,
            properties=min(properties, 1.0),
            relationships=relationships,
            overall=0.0
        )
        
        # Calculate weighted overall
        score.overall = self.calculate_weighted_average(score)
        
        return score
    
    def calculate_text_confidence(
        self,
        text: str,
        obj_type: ArxObjectType,
        context: Dict[str, Any]
    ) -> ConfidenceScore:
        """
        Calculate confidence for object extracted from text
        
        Args:
            text: Extracted text
            obj_type: Identified object type
            context: Additional context (font size, position, etc.)
        
        Returns:
            Multi-dimensional confidence score
        """
        
        # Classification confidence (text labels are usually accurate)
        text_lower = text.lower()
        exact_match = any([
            "wall" in text_lower and obj_type == ArxObjectType.WALL,
            "column" in text_lower and obj_type == ArxObjectType.COLUMN,
            "room" in text_lower and obj_type == ArxObjectType.ROOM,
            "electrical" in text_lower and obj_type == ArxObjectType.ELECTRICAL_PANEL,
            "hvac" in text_lower and obj_type == ArxObjectType.HVAC_UNIT,
        ])
        
        classification = 0.85 if exact_match else 0.65
        
        # Position confidence (text position less precise than graphics)
        font_size = context.get("font_size", 10)
        position = 0.60 if font_size > 8 else 0.50
        
        # Properties confidence (text may contain specifications)
        has_numbers = any(char.isdigit() for char in text)
        properties = 0.70 if has_numbers else 0.40
        
        # Relationships (not from text)
        relationships = 0.25
        
        score = ConfidenceScore(
            classification=classification,
            position=position,
            properties=properties,
            relationships=relationships,
            overall=0.0
        )
        
        score.overall = self.calculate_weighted_average(score)
        
        return score
    
    def calculate_raster_confidence(
        self,
        detection_score: float,
        obj_type: ArxObjectType,
        image_quality: float
    ) -> ConfidenceScore:
        """
        Calculate confidence for object extracted from raster image
        
        Args:
            detection_score: ML model or CV detection confidence
            obj_type: Identified object type
            image_quality: Image quality metric (0-1)
        
        Returns:
            Multi-dimensional confidence score
        """
        
        # Classification confidence (depends on detection and image quality)
        classification = detection_score * image_quality * self.method_confidence["raster"]
        
        # Position confidence (pixel accuracy)
        position = 0.55 * image_quality  # Lower precision from pixels
        
        # Properties confidence (limited from images)
        properties = 0.35 * image_quality
        
        # Relationships (minimal from single image)
        relationships = 0.20
        
        score = ConfidenceScore(
            classification=classification,
            position=position,
            properties=properties,
            relationships=relationships,
            overall=0.0
        )
        
        score.overall = self.calculate_weighted_average(score)
        
        return score
    
    def boost_confidence_from_validation(
        self,
        original: ConfidenceScore,
        validation_confidence: float,
        validation_type: str
    ) -> ConfidenceScore:
        """
        Boost confidence based on validation
        
        Args:
            original: Original confidence score
            validation_confidence: Confidence in validation (0-1)
            validation_type: Type of validation performed
        
        Returns:
            Boosted confidence score
        """
        
        # Different validation types boost different dimensions
        if validation_type == "dimension":
            # Dimension validation improves position and properties
            position_boost = 0.3 * validation_confidence
            properties_boost = 0.25 * validation_confidence
            
            new_position = min(original.position + position_boost, 0.95)
            new_properties = min(original.properties + properties_boost, 0.95)
            
            return ConfidenceScore(
                classification=original.classification,
                position=new_position,
                properties=new_properties,
                relationships=original.relationships,
                overall=0.0
            )
            
        elif validation_type == "type":
            # Type validation improves classification
            classification_boost = 0.35 * validation_confidence
            new_classification = min(original.classification + classification_boost, 0.95)
            
            return ConfidenceScore(
                classification=new_classification,
                position=original.position,
                properties=original.properties,
                relationships=original.relationships,
                overall=0.0
            )
            
        elif validation_type == "relationship":
            # Relationship validation
            relationship_boost = 0.4 * validation_confidence
            new_relationships = min(original.relationships + relationship_boost, 0.95)
            
            return ConfidenceScore(
                classification=original.classification,
                position=original.position,
                properties=original.properties,
                relationships=new_relationships,
                overall=0.0
            )
        
        return original
    
    def cascade_confidence(
        self,
        source_confidence: float,
        distance: float,
        similarity: float
    ) -> float:
        """
        Calculate cascaded confidence for pattern application
        
        Args:
            source_confidence: Confidence of validated source
            distance: Spatial/contextual distance (0-1, 0 is closest)
            similarity: Similarity score (0-1)
        
        Returns:
            Cascaded confidence value
        """
        
        # Confidence decays with distance and dissimilarity
        decay_factor = (1 - distance * 0.5) * similarity
        cascaded = source_confidence * decay_factor * 0.9  # 90% max cascade
        
        return max(cascaded, 0.3)  # Minimum 30% confidence
    
    def calculate_aggregate_confidence(
        self,
        objects: List[Any],
        weights: Optional[List[float]] = None
    ) -> float:
        """
        Calculate aggregate confidence for a set of objects
        
        Args:
            objects: List of objects with confidence scores
            weights: Optional weights for each object
        
        Returns:
            Aggregate confidence score
        """
        
        if not objects:
            return 0.0
        
        if weights is None:
            weights = [1.0] * len(objects)
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(
            obj.confidence.overall * weight 
            for obj, weight in zip(objects, weights)
        )
        
        return weighted_sum / total_weight
    
    def calculate_weighted_average(self, score: ConfidenceScore) -> float:
        """
        Calculate weighted average for overall confidence
        
        Args:
            score: Multi-dimensional confidence score
        
        Returns:
            Weighted average (0-1)
        """
        
        # Weights for different dimensions
        weights = {
            "classification": 0.35,
            "position": 0.30,
            "properties": 0.20,
            "relationships": 0.15
        }
        
        weighted_sum = (
            score.classification * weights["classification"] +
            score.position * weights["position"] +
            score.properties * weights["properties"] +
            score.relationships * weights["relationships"]
        )
        
        return min(weighted_sum, 1.0)
    
    def get_confidence_level(self, score: float) -> str:
        """
        Get human-readable confidence level
        
        Args:
            score: Confidence score (0-1)
        
        Returns:
            Confidence level string
        """
        
        if score >= 0.85:
            return "high"
        elif score >= 0.60:
            return "medium"
        else:
            return "low"
    
    def should_flag_for_validation(self, score: ConfidenceScore) -> bool:
        """
        Determine if object should be flagged for validation
        
        Args:
            score: Multi-dimensional confidence score
        
        Returns:
            True if validation recommended
        """
        
        # Flag if any dimension is critically low
        if (score.classification < 0.5 or
            score.position < 0.4 or
            score.overall < 0.6):
            return True
        
        # Flag if high-importance object with medium confidence
        # (This would check object type in production)
        if score.overall < 0.75:
            return True
        
        return False