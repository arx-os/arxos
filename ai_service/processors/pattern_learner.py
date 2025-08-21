"""
Pattern learning engine for confidence improvement
Implements the strategic validation cascade approach
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import numpy as np
from sklearn.cluster import DBSCAN
import json

from models.arxobject import ArxObject, ArxObjectType, ConfidenceScore
from utils.config import settings


class PatternLearner:
    """
    Learn and apply patterns from validated objects
    Implements the 80/20 validation strategy
    """
    
    def __init__(self):
        self.patterns = defaultdict(list)
        self.validation_history = []
        self.pattern_confidence = {}
        self.min_pattern_occurrences = settings.PATTERN_MIN_OCCURRENCES
        
    def learn_from_validation(
        self,
        validated_object: ArxObject,
        similar_objects: List[ArxObject],
        validation_confidence: float
    ) -> Dict[str, Any]:
        """
        Learn pattern from a validated object
        
        Args:
            validated_object: The validated ArxObject
            similar_objects: Similar unvalidated objects
            validation_confidence: Confidence in validation
        
        Returns:
            Pattern learning result
        """
        
        # Extract pattern features
        pattern = self._extract_pattern(validated_object)
        
        # Store pattern
        pattern_key = self._get_pattern_key(validated_object)
        self.patterns[pattern_key].append({
            "pattern": pattern,
            "confidence": validation_confidence,
            "object_id": validated_object.id,
            "timestamp": validated_object.metadata.created
        })
        
        # Update pattern confidence
        self._update_pattern_confidence(pattern_key)
        
        # Apply to similar objects
        cascade_results = []
        for obj in similar_objects:
            if self._matches_pattern(obj, pattern):
                boosted_confidence = self._cascade_confidence(
                    validated_object.confidence.overall,
                    validation_confidence,
                    self._calculate_similarity(obj, validated_object)
                )
                
                # Update object confidence
                obj.confidence.overall = max(
                    obj.confidence.overall,
                    boosted_confidence
                )
                
                cascade_results.append({
                    "object_id": obj.id,
                    "old_confidence": obj.confidence.overall,
                    "new_confidence": boosted_confidence,
                    "improvement": boosted_confidence - obj.confidence.overall
                })
        
        # Record validation
        self.validation_history.append({
            "validated_object": validated_object.id,
            "pattern_key": pattern_key,
            "cascaded_count": len(cascade_results),
            "total_improvement": sum(r["improvement"] for r in cascade_results)
        })
        
        return {
            "pattern_learned": True,
            "pattern_key": pattern_key,
            "cascaded_objects": len(cascade_results),
            "average_improvement": np.mean([r["improvement"] for r in cascade_results]) if cascade_results else 0
        }
    
    def apply_patterns(
        self,
        objects: List[ArxObject],
        building_type: Optional[str] = None
    ) -> List[ArxObject]:
        """
        Apply learned patterns to boost confidence
        
        Args:
            objects: List of ArxObjects to process
            building_type: Optional building type for context
        
        Returns:
            Objects with boosted confidence where applicable
        """
        
        for obj in objects:
            pattern_key = self._get_pattern_key(obj)
            
            # Check if we have patterns for this type
            if pattern_key in self.patterns:
                applicable_patterns = self._get_applicable_patterns(
                    obj, pattern_key, building_type
                )
                
                if applicable_patterns:
                    # Apply best matching pattern
                    best_pattern = max(
                        applicable_patterns,
                        key=lambda p: p["match_score"]
                    )
                    
                    # Boost confidence
                    boost = best_pattern["confidence_boost"]
                    obj.confidence.classification = min(
                        obj.confidence.classification + boost * 0.3, 0.95
                    )
                    obj.confidence.properties = min(
                        obj.confidence.properties + boost * 0.2, 0.95
                    )
                    
                    # Recalculate overall
                    # Calculate weighted average
                    obj.confidence.overall = (
                        obj.confidence.classification * 0.4 +
                        obj.confidence.position * 0.3 +
                        obj.confidence.properties * 0.2 +
                        obj.confidence.relationships * 0.1
                    )
                    
                    # Mark as pattern-enhanced
                    if not obj.data:
                        obj.data = {}
                    obj.data["pattern_enhanced"] = True
                    obj.data["pattern_confidence"] = best_pattern["confidence_boost"]
        
        return objects
    
    def identify_validation_priorities(
        self,
        objects: List[ArxObject]
    ) -> List[Tuple[ArxObject, float]]:
        """
        Identify objects that would benefit most from validation
        Implements the 80/20 rule - validate high-impact objects
        
        Args:
            objects: List of ArxObjects
        
        Returns:
            Prioritized list of (object, impact_score) tuples
        """
        
        priorities = []
        
        for obj in objects:
            # Calculate potential impact
            impact = self._calculate_validation_impact(obj, objects)
            
            # Only recommend if impact is significant
            if impact > 0.3:
                priorities.append((obj, impact))
        
        # Sort by impact (highest first)
        priorities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 20% that would impact 80% of objects
        cutoff = max(1, len(priorities) // 5)
        return priorities[:cutoff]
    
    def _extract_pattern(self, obj: ArxObject) -> Dict[str, Any]:
        """Extract pattern features from object"""
        
        pattern = {
            "type": obj.type,
            "geometry_type": obj.geometry.get("type") if obj.geometry else None,
            "has_relationships": len(obj.relationships) > 0,
            "relationship_types": [r.type for r in obj.relationships],
            "data_keys": list(obj.data.keys()) if obj.data else [],
            "confidence_profile": {
                "classification": obj.confidence.classification,
                "position": obj.confidence.position,
                "properties": obj.confidence.properties,
                "relationships": obj.confidence.relationships
            }
        }
        
        # Add dimensional features if available
        if obj.geometry and "coordinates" in obj.geometry:
            coords = obj.geometry["coordinates"]
            if len(coords) >= 2:
                # Calculate basic geometric features
                pattern["aspect_ratio"] = self._calculate_aspect_ratio(coords)
                pattern["complexity"] = len(coords)
        
        return pattern
    
    def _get_pattern_key(self, obj: ArxObject) -> str:
        """Generate pattern key for indexing"""
        return f"{obj.type}_{obj.geometry.get('type', 'unknown') if obj.geometry else 'no_geom'}"
    
    def _matches_pattern(
        self,
        obj: ArxObject,
        pattern: Dict[str, Any],
        threshold: float = 0.7
    ) -> bool:
        """Check if object matches pattern"""
        
        score = 0.0
        weights = 0.0
        
        # Type match (highest weight)
        if obj.type == pattern["type"]:
            score += 0.4
        weights += 0.4
        
        # Geometry type match
        if obj.geometry:
            if obj.geometry.get("type") == pattern.get("geometry_type"):
                score += 0.2
            weights += 0.2
        
        # Relationship similarity
        obj_rel_types = [r.type for r in obj.relationships]
        pattern_rel_types = pattern.get("relationship_types", [])
        if obj_rel_types and pattern_rel_types:
            overlap = len(set(obj_rel_types) & set(pattern_rel_types))
            max_len = max(len(obj_rel_types), len(pattern_rel_types))
            score += 0.2 * (overlap / max_len)
        weights += 0.2
        
        # Data key similarity
        obj_keys = list(obj.data.keys()) if obj.data else []
        pattern_keys = pattern.get("data_keys", [])
        if obj_keys and pattern_keys:
            overlap = len(set(obj_keys) & set(pattern_keys))
            max_len = max(len(obj_keys), len(pattern_keys))
            score += 0.2 * (overlap / max_len)
        weights += 0.2
        
        match_score = score / weights if weights > 0 else 0
        return match_score >= threshold
    
    def _cascade_confidence(
        self,
        source_confidence: float,
        validation_confidence: float,
        similarity: float
    ) -> float:
        """Calculate cascaded confidence"""
        
        # Base cascade from source
        base_cascade = source_confidence * settings.VALIDATION_CASCADE_DECAY
        
        # Adjust by validation confidence and similarity
        adjusted = base_cascade * validation_confidence * similarity
        
        # Apply confidence boost
        return min(adjusted + settings.PATTERN_CONFIDENCE_BOOST, 0.95)
    
    def _calculate_similarity(
        self,
        obj1: ArxObject,
        obj2: ArxObject
    ) -> float:
        """Calculate similarity between two objects"""
        
        if obj1.type != obj2.type:
            return 0.0
        
        similarity = 0.5  # Base similarity for same type
        
        # Spatial proximity (if both have geometry)
        if obj1.geometry and obj2.geometry:
            coords1 = obj1.geometry.get("coordinates", [[0,0]])
            coords2 = obj2.geometry.get("coordinates", [[0,0]])
            
            if coords1 and coords2:
                # Simple distance-based similarity
                dist = np.sqrt(
                    (coords1[0][0] - coords2[0][0])**2 +
                    (coords1[0][1] - coords2[0][1])**2
                )
                # Convert distance to similarity (closer = more similar)
                spatial_sim = max(0, 1 - dist / 1000)  # 1000 pixel max distance
                similarity += spatial_sim * 0.3
        
        # Property similarity
        if obj1.data and obj2.data:
            shared_keys = set(obj1.data.keys()) & set(obj2.data.keys())
            all_keys = set(obj1.data.keys()) | set(obj2.data.keys())
            if all_keys:
                property_sim = len(shared_keys) / len(all_keys)
                similarity += property_sim * 0.2
        
        return min(similarity, 1.0)
    
    def _update_pattern_confidence(self, pattern_key: str):
        """Update confidence for a pattern based on occurrences"""
        
        patterns = self.patterns[pattern_key]
        if len(patterns) >= self.min_pattern_occurrences:
            # Calculate average confidence
            avg_confidence = np.mean([p["confidence"] for p in patterns])
            
            # Boost for multiple validations
            occurrence_boost = min(len(patterns) * 0.05, 0.3)
            
            self.pattern_confidence[pattern_key] = min(
                avg_confidence + occurrence_boost, 0.95
            )
    
    def _get_applicable_patterns(
        self,
        obj: ArxObject,
        pattern_key: str,
        building_type: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get patterns applicable to an object"""
        
        applicable = []
        
        for pattern_data in self.patterns[pattern_key]:
            pattern = pattern_data["pattern"]
            
            if self._matches_pattern(obj, pattern, threshold=0.6):
                match_score = self._calculate_pattern_match_score(obj, pattern)
                
                applicable.append({
                    "pattern": pattern,
                    "match_score": match_score,
                    "confidence_boost": self.pattern_confidence.get(
                        pattern_key, 0.1
                    ) * match_score
                })
        
        return applicable
    
    def _calculate_pattern_match_score(
        self,
        obj: ArxObject,
        pattern: Dict[str, Any]
    ) -> float:
        """Calculate detailed match score"""
        
        scores = []
        
        # Type match
        if obj.type == pattern["type"]:
            scores.append(1.0)
        else:
            scores.append(0.0)
        
        # Geometry match
        if obj.geometry and pattern.get("geometry_type"):
            if obj.geometry.get("type") == pattern["geometry_type"]:
                scores.append(1.0)
            else:
                scores.append(0.5)
        
        # Aspect ratio similarity (if applicable)
        if "aspect_ratio" in pattern and obj.geometry:
            coords = obj.geometry.get("coordinates", [])
            if coords:
                obj_ratio = self._calculate_aspect_ratio(coords)
                pattern_ratio = pattern["aspect_ratio"]
                if pattern_ratio > 0:
                    ratio_diff = abs(obj_ratio - pattern_ratio) / pattern_ratio
                    scores.append(max(0, 1 - ratio_diff))
        
        return np.mean(scores) if scores else 0.0
    
    def _calculate_aspect_ratio(self, coordinates: List) -> float:
        """Calculate aspect ratio from coordinates"""
        
        if len(coordinates) < 2:
            return 1.0
        
        # Get bounding box
        x_coords = [c[0] for c in coordinates]
        y_coords = [c[1] for c in coordinates]
        
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        
        if height == 0:
            return float('inf')
        
        return width / height
    
    def _calculate_validation_impact(
        self,
        obj: ArxObject,
        all_objects: List[ArxObject]
    ) -> float:
        """
        Calculate potential impact of validating this object
        
        High impact if:
        - Low confidence critical object
        - Many similar objects that would benefit
        - Central to relationship network
        """
        
        impact = 0.0
        
        # Impact based on object criticality and confidence
        criticality = self._get_object_criticality(obj.type)
        confidence_gap = 1.0 - obj.confidence.overall
        impact += criticality * confidence_gap * 0.4
        
        # Impact based on similar objects
        similar_count = sum(
            1 for other in all_objects
            if other.id != obj.id and
            self._calculate_similarity(obj, other) > 0.7
        )
        impact += min(similar_count / 10, 1.0) * 0.3
        
        # Impact based on relationships
        relationship_impact = len(obj.relationships) / 5  # Normalize by 5
        impact += min(relationship_impact, 1.0) * 0.3
        
        return min(impact, 1.0)
    
    def _get_object_criticality(self, obj_type: ArxObjectType) -> float:
        """Get criticality score for object type"""
        
        # Structural elements most critical
        if obj_type in [ArxObjectType.WALL, ArxObjectType.COLUMN,
                        ArxObjectType.BEAM, ArxObjectType.FOUNDATION]:
            return 1.0
        # Safety systems critical
        elif obj_type in [ArxObjectType.FIRE_SPRINKLER, ArxObjectType.FIRE_ALARM,
                         ArxObjectType.EMERGENCY_EXIT]:
            return 0.9
        # MEP systems important
        elif obj_type in [ArxObjectType.ELECTRICAL_PANEL, ArxObjectType.HVAC_UNIT]:
            return 0.7
        # Spatial elements moderate
        elif obj_type in [ArxObjectType.ROOM, ArxObjectType.FLOOR]:
            return 0.5
        # Others lower
        else:
            return 0.3
    
    def has_patterns(self) -> bool:
        """Check if any patterns have been learned"""
        return len(self.pattern_confidence) > 0
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about learned patterns"""
        
        total_patterns = sum(len(p) for p in self.patterns.values())
        unique_types = len(self.patterns)
        
        avg_confidence = np.mean(list(self.pattern_confidence.values())) if self.pattern_confidence else 0
        
        total_cascaded = sum(
            v["cascaded_count"] for v in self.validation_history
        )
        
        return {
            "total_patterns": total_patterns,
            "unique_pattern_types": unique_types,
            "average_pattern_confidence": avg_confidence,
            "total_validations": len(self.validation_history),
            "total_objects_cascaded": total_cascaded,
            "patterns_by_type": {k: len(v) for k, v in self.patterns.items()}
        }
    
    def save_patterns(self, filepath: str):
        """Save learned patterns to file"""
        
        data = {
            "patterns": dict(self.patterns),
            "pattern_confidence": self.pattern_confidence,
            "validation_history": self.validation_history
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_patterns(self, filepath: str):
        """Load patterns from file"""
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.patterns = defaultdict(list, data["patterns"])
        self.pattern_confidence = data["pattern_confidence"]
        self.validation_history = data["validation_history"]