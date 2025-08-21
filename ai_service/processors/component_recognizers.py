"""
Component Recognizers for Arxos
Specialized recognizers for building components (walls, rooms, doors, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum

from models.arxobject import ArxObject, ArxObjectType, ConfidenceScore, Metadata
from models.coordinate_system import Point3D, BoundingBox, Dimensions


@dataclass
class ComponentFeatures:
    """Features extracted for component recognition"""
    length: float
    width: float
    area: float
    aspect_ratio: float
    orientation: float  # Angle in radians
    is_closed: bool
    has_opening: bool
    thickness: Optional[float] = None
    adjacent_count: int = 0
    text_annotations: List[str] = None
    

class ComponentRecognizer(ABC):
    """Base class for component recognizers"""
    
    @abstractmethod
    def recognize(self, features: ComponentFeatures, context: Dict[str, Any]) -> Tuple[ArxObjectType, float]:
        """
        Recognize component type from features
        Returns: (object_type, confidence)
        """
        pass
    
    @abstractmethod
    def get_standard_dimensions(self, region: str = "US") -> Dict[str, Any]:
        """Get standard dimensions for this component type"""
        pass


class WallRecognizer(ComponentRecognizer):
    """Recognizer for walls"""
    
    # Standard wall thicknesses in mm
    STANDARD_THICKNESSES = {
        "US": [
            101.6,  # 4" interior wall
            152.4,  # 6" standard wall
            203.2,  # 8" thick wall
            254.0,  # 10" exterior wall
            304.8,  # 12" structural wall
        ],
        "EU": [
            100,    # 100mm interior
            150,    # 150mm standard
            200,    # 200mm thick
            250,    # 250mm exterior
            300,    # 300mm structural
        ]
    }
    
    def recognize(self, features: ComponentFeatures, context: Dict[str, Any]) -> Tuple[ArxObjectType, float]:
        """Recognize walls based on features"""
        confidence = 0.0
        
        # Check aspect ratio - walls are typically long and thin
        if features.aspect_ratio > 5:  # Length at least 5x thickness
            confidence += 0.3
        elif features.aspect_ratio > 3:
            confidence += 0.2
        
        # Check if it's a line or thin rectangle
        if features.width < 500:  # Less than 500mm thick
            confidence += 0.2
        
        # Check length - walls are typically at least 1m long
        if features.length > 1000:  # More than 1m
            confidence += 0.2
        
        # Check orientation - walls are often horizontal or vertical
        angle_deg = abs(np.degrees(features.orientation))
        if angle_deg < 5 or angle_deg > 85 or abs(angle_deg - 90) < 5 or abs(angle_deg - 180) < 5:
            confidence += 0.1
        
        # Check for standard thickness
        if features.thickness:
            for thickness in self.STANDARD_THICKNESSES.get(context.get("region", "US"), []):
                if abs(features.thickness - thickness) < 10:  # Within 10mm tolerance
                    confidence += 0.2
                    break
        
        # Check text annotations
        if features.text_annotations:
            wall_keywords = ["WALL", "W", "PARTITION", "EXTERIOR", "INTERIOR", "BEARING"]
            for text in features.text_annotations:
                if any(keyword in text.upper() for keyword in wall_keywords):
                    confidence += 0.3
                    break
        
        # Minimum confidence threshold
        if confidence < 0.4:
            return None, 0.0
        
        return ArxObjectType.WALL, min(confidence, 1.0)
    
    def get_standard_dimensions(self, region: str = "US") -> Dict[str, Any]:
        """Get standard wall dimensions"""
        return {
            "thicknesses": self.STANDARD_THICKNESSES.get(region, self.STANDARD_THICKNESSES["US"]),
            "min_length": 600,  # 600mm minimum wall length
            "max_length": 15000,  # 15m maximum single wall segment
            "standard_height": 3000  # 3m standard ceiling height
        }


class RoomRecognizer(ComponentRecognizer):
    """Recognizer for rooms"""
    
    # Typical room sizes in square meters
    ROOM_SIZE_RANGES = {
        "bathroom": (3, 15),
        "bedroom": (9, 30),
        "living_room": (15, 50),
        "kitchen": (6, 25),
        "dining_room": (10, 30),
        "office": (6, 20),
        "storage": (1, 10),
        "hallway": (2, 20),
        "garage": (15, 60),
    }
    
    def recognize(self, features: ComponentFeatures, context: Dict[str, Any]) -> Tuple[ArxObjectType, float]:
        """Recognize rooms based on features"""
        confidence = 0.0
        
        # Must be a closed polygon
        if not features.is_closed:
            return None, 0.0
        
        confidence += 0.2
        
        # Check area - rooms are typically larger areas
        area_m2 = features.area / 1_000_000  # Convert mm² to m²
        
        if area_m2 > 3:  # At least 3m²
            confidence += 0.3
        
        # Check aspect ratio - rooms are usually not too elongated
        if features.aspect_ratio < 3:
            confidence += 0.2
        elif features.aspect_ratio < 5:
            confidence += 0.1
        
        # Check for reasonable room dimensions
        if 2000 < features.length < 20000 and 2000 < features.width < 20000:
            confidence += 0.2
        
        # Check text annotations for room labels
        if features.text_annotations:
            room_keywords = ["ROOM", "RM", "BEDROOM", "BATH", "KITCHEN", "LIVING", 
                           "DINING", "OFFICE", "GARAGE", "STORAGE", "CLOSET"]
            for text in features.text_annotations:
                if any(keyword in text.upper() for keyword in room_keywords):
                    confidence += 0.3
                    break
        
        # Check if it has adjacent walls
        if features.adjacent_count >= 3:
            confidence += 0.1
        
        return ArxObjectType.ROOM, min(confidence, 1.0)
    
    def classify_room_type(self, area_m2: float, text_annotations: List[str] = None) -> str:
        """Classify specific room type based on area and annotations"""
        room_type = "room"
        
        # First check text annotations
        if text_annotations:
            text = " ".join(text_annotations).upper()
            
            if "BATH" in text or "WC" in text or "TOILET" in text:
                room_type = "bathroom"
            elif "BED" in text or "BR" in text:
                room_type = "bedroom"
            elif "KITCHEN" in text or "KIT" in text:
                room_type = "kitchen"
            elif "LIVING" in text or "LR" in text:
                room_type = "living_room"
            elif "DINING" in text or "DR" in text:
                room_type = "dining_room"
            elif "OFFICE" in text or "STUDY" in text:
                room_type = "office"
            elif "GARAGE" in text or "GAR" in text:
                room_type = "garage"
            elif "STORAGE" in text or "CLOSET" in text or "CLO" in text:
                room_type = "storage"
            elif "HALL" in text or "CORRIDOR" in text:
                room_type = "hallway"
        
        # If no text match, use area as hint
        if room_type == "room":
            for rtype, (min_area, max_area) in self.ROOM_SIZE_RANGES.items():
                if min_area <= area_m2 <= max_area:
                    room_type = rtype
                    break
        
        return room_type
    
    def get_standard_dimensions(self, region: str = "US") -> Dict[str, Any]:
        """Get standard room dimensions"""
        return {
            "size_ranges": self.ROOM_SIZE_RANGES,
            "min_area": 1000000,  # 1m² minimum
            "max_area": 200000000,  # 200m² maximum
            "standard_height": 3000  # 3m standard ceiling height
        }


class DoorRecognizer(ComponentRecognizer):
    """Recognizer for doors"""
    
    # Standard door widths in mm
    STANDARD_WIDTHS = {
        "US": [
            610,   # 24" narrow door
            711,   # 28" bathroom door
            762,   # 30" standard interior
            813,   # 32" standard
            864,   # 34" 
            914,   # 36" standard exterior
            1524,  # 60" double door
        ],
        "EU": [
            600,   # Narrow door
            700,   # Standard bathroom
            800,   # Standard interior
            900,   # Standard
            1000,  # Wide door
            1600,  # Double door
        ]
    }
    
    def recognize(self, features: ComponentFeatures, context: Dict[str, Any]) -> Tuple[ArxObjectType, float]:
        """Recognize doors based on features"""
        confidence = 0.0
        
        # Check for opening indicator
        if features.has_opening:
            confidence += 0.4
        
        # Check dimensions against standard door sizes
        for width in self.STANDARD_WIDTHS.get(context.get("region", "US"), []):
            if abs(features.width - width) < 50:  # Within 50mm tolerance
                confidence += 0.3
                break
        
        # Doors are typically 2000-2400mm tall
        if 1800 < features.length < 2600:
            confidence += 0.2
        
        # Check for door swing arc (common in floor plans)
        if context.get("has_arc", False):
            confidence += 0.3
        
        # Check text annotations
        if features.text_annotations:
            door_keywords = ["DOOR", "DR", "D", "ENTRY", "EXIT", "ACCESS"]
            for text in features.text_annotations:
                if any(keyword in text.upper() for keyword in door_keywords):
                    confidence += 0.3
                    break
        
        # Check if it's in a wall opening
        if context.get("in_wall_opening", False):
            confidence += 0.2
        
        return ArxObjectType.DOOR, min(confidence, 1.0)
    
    def get_standard_dimensions(self, region: str = "US") -> Dict[str, Any]:
        """Get standard door dimensions"""
        return {
            "widths": self.STANDARD_WIDTHS.get(region, self.STANDARD_WIDTHS["US"]),
            "standard_height": 2032 if region == "US" else 2100,  # 80" US, 2100mm EU
            "min_width": 500,
            "max_width": 2000,
            "swing_radius": 900  # Typical door swing radius
        }


class WindowRecognizer(ComponentRecognizer):
    """Recognizer for windows"""
    
    STANDARD_WIDTHS = {
        "US": [
            610,   # 24" small window
            914,   # 36" standard window
            1219,  # 48" wide window
            1524,  # 60" picture window
            1829,  # 72" wide window
        ],
        "EU": [
            600,   # Small window
            900,   # Standard window
            1200,  # Wide window
            1500,  # Picture window
            1800,  # Extra wide
        ]
    }
    
    def recognize(self, features: ComponentFeatures, context: Dict[str, Any]) -> Tuple[ArxObjectType, float]:
        """Recognize windows based on features"""
        confidence = 0.0
        
        # Windows are typically shown as thin lines or rectangles in walls
        if features.width < 100:  # Very thin
            confidence += 0.2
        
        # Check dimensions against standard window sizes
        for width in self.STANDARD_WIDTHS.get(context.get("region", "US"), []):
            if abs(features.length - width) < 100:  # Within 100mm tolerance
                confidence += 0.3
                break
        
        # Windows are typically 600-1800mm tall
        if 500 < features.width < 2000 or 500 < features.length < 2000:
            confidence += 0.2
        
        # Check if it's in a wall
        if context.get("in_wall", False):
            confidence += 0.3
        
        # Check for parallel lines (common window representation)
        if context.get("has_parallel_lines", False):
            confidence += 0.2
        
        # Check text annotations
        if features.text_annotations:
            window_keywords = ["WINDOW", "WIN", "W", "GLAZING", "GLASS"]
            for text in features.text_annotations:
                if any(keyword in text.upper() for keyword in window_keywords):
                    confidence += 0.3
                    break
        
        return ArxObjectType.WINDOW, min(confidence, 1.0)
    
    def get_standard_dimensions(self, region: str = "US") -> Dict[str, Any]:
        """Get standard window dimensions"""
        return {
            "widths": self.STANDARD_WIDTHS.get(region, self.STANDARD_WIDTHS["US"]),
            "standard_heights": [600, 900, 1200, 1500, 1800],  # Various heights
            "sill_height": 900,  # Typical sill height from floor
            "head_height": 2100,  # Typical head height from floor
        }


class StairRecognizer(ComponentRecognizer):
    """Recognizer for stairs"""
    
    def recognize(self, features: ComponentFeatures, context: Dict[str, Any]) -> Tuple[ArxObjectType, float]:
        """Recognize stairs based on features"""
        confidence = 0.0
        
        # Check for parallel lines pattern (stair treads)
        if context.get("parallel_lines_count", 0) > 5:
            confidence += 0.4
        
        # Check aspect ratio - stairs are typically rectangular
        if 1.5 < features.aspect_ratio < 4:
            confidence += 0.2
        
        # Check dimensions - typical stair width 900-1200mm
        if 800 < features.width < 1500 or 800 < features.length < 1500:
            confidence += 0.2
        
        # Check for arrow or direction indicator
        if context.get("has_arrow", False):
            confidence += 0.2
        
        # Check text annotations
        if features.text_annotations:
            stair_keywords = ["STAIR", "STAIRS", "ST", "UP", "DN", "DOWN"]
            for text in features.text_annotations:
                if any(keyword in text.upper() for keyword in stair_keywords):
                    confidence += 0.4
                    break
        
        return ArxObjectType.STAIRWELL, min(confidence, 1.0)
    
    def get_standard_dimensions(self, region: str = "US") -> Dict[str, Any]:
        """Get standard stair dimensions"""
        return {
            "min_width": 900,  # Minimum stair width
            "standard_width": 1100,  # Standard width
            "tread_depth": 280,  # Standard tread depth
            "riser_height": 180,  # Standard riser height
            "min_headroom": 2000,  # Minimum headroom
        }


class ColumnRecognizer(ComponentRecognizer):
    """Recognizer for structural columns"""
    
    STANDARD_SIZES = {
        "US": [
            305,   # 12" square column
            406,   # 16" square column
            457,   # 18" square column
            508,   # 20" square column
            610,   # 24" square column
        ],
        "EU": [
            300,   # 300mm square
            400,   # 400mm square
            450,   # 450mm square
            500,   # 500mm square
            600,   # 600mm square
        ]
    }
    
    def recognize(self, features: ComponentFeatures, context: Dict[str, Any]) -> Tuple[ArxObjectType, float]:
        """Recognize columns based on features"""
        confidence = 0.0
        
        # Columns are typically square or circular
        if features.aspect_ratio < 1.5:  # Nearly square
            confidence += 0.3
        
        # Check dimensions against standard column sizes
        avg_size = (features.length + features.width) / 2
        for size in self.STANDARD_SIZES.get(context.get("region", "US"), []):
            if abs(avg_size - size) < 50:  # Within 50mm tolerance
                confidence += 0.3
                break
        
        # Columns are relatively small
        if features.area < 1000000:  # Less than 1m²
            confidence += 0.2
        
        # Check if it's a filled rectangle or circle
        if context.get("is_filled", False):
            confidence += 0.2
        
        # Check for grid pattern (columns often in regular grid)
        if context.get("in_grid_pattern", False):
            confidence += 0.2
        
        # Check text annotations
        if features.text_annotations:
            column_keywords = ["COLUMN", "COL", "C", "PILLAR", "POST"]
            for text in features.text_annotations:
                if any(keyword in text.upper() for keyword in column_keywords):
                    confidence += 0.3
                    break
        
        return ArxObjectType.COLUMN, min(confidence, 1.0)
    
    def get_standard_dimensions(self, region: str = "US") -> Dict[str, Any]:
        """Get standard column dimensions"""
        return {
            "sizes": self.STANDARD_SIZES.get(region, self.STANDARD_SIZES["US"]),
            "min_size": 200,  # Minimum column dimension
            "max_size": 1000,  # Maximum column dimension
            "typical_spacing": 6000,  # Typical column spacing
        }


class ComponentClassifier:
    """Main classifier that uses all recognizers"""
    
    def __init__(self, region: str = "US"):
        self.region = region
        self.recognizers = [
            WallRecognizer(),
            RoomRecognizer(),
            DoorRecognizer(),
            WindowRecognizer(),
            StairRecognizer(),
            ColumnRecognizer(),
        ]
    
    def classify(self, features: ComponentFeatures, context: Dict[str, Any]) -> Tuple[ArxObjectType, float]:
        """
        Classify component using all recognizers
        Returns the classification with highest confidence
        """
        context["region"] = self.region
        
        best_type = None
        best_confidence = 0.0
        
        for recognizer in self.recognizers:
            obj_type, confidence = recognizer.recognize(features, context)
            if obj_type and confidence > best_confidence:
                best_type = obj_type
                best_confidence = confidence
        
        # Default to wall if confidence is too low
        if best_confidence < 0.3:
            best_type = ArxObjectType.WALL
            best_confidence = 0.3
        
        return best_type, best_confidence
    
    def extract_features(self, geometry: Dict[str, Any], annotations: List[str] = None) -> ComponentFeatures:
        """Extract features from geometry"""
        geom_type = geometry.get("type", "")
        
        if geom_type == "LineString":
            coords = geometry["coordinates"]
            p1, p2 = coords[0], coords[1]
            
            length = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            width = 10  # Default thin width for lines
            area = length * width
            aspect_ratio = length / width if width > 0 else length
            orientation = np.arctan2(p2[1] - p1[1], p2[0] - p1[0])
            is_closed = False
            has_opening = False
            
        elif geom_type == "Polygon":
            coords = geometry["coordinates"][0]
            
            # Calculate bounding box
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            length = max_x - min_x
            width = max_y - min_y
            area = length * width  # Simplified - actual polygon area would be better
            aspect_ratio = max(length, width) / min(length, width) if min(length, width) > 0 else 1
            
            # Calculate orientation from longest edge
            orientation = 0
            max_edge_len = 0
            for i in range(len(coords) - 1):
                edge_len = np.sqrt((coords[i+1][0] - coords[i][0])**2 + 
                                 (coords[i+1][1] - coords[i][1])**2)
                if edge_len > max_edge_len:
                    max_edge_len = edge_len
                    orientation = np.arctan2(coords[i+1][1] - coords[i][1], 
                                           coords[i+1][0] - coords[i][0])
            
            is_closed = True
            # Simple check for opening - if polygon is not convex
            has_opening = len(coords) > 5
            
        else:
            # Default values for other geometry types
            length = 100
            width = 100
            area = 10000
            aspect_ratio = 1
            orientation = 0
            is_closed = False
            has_opening = False
        
        return ComponentFeatures(
            length=length,
            width=width,
            area=area,
            aspect_ratio=aspect_ratio,
            orientation=orientation,
            is_closed=is_closed,
            has_opening=has_opening,
            text_annotations=annotations
        )
    
    def get_context_from_surroundings(self, element: Any, all_elements: List[Any]) -> Dict[str, Any]:
        """Extract context from surrounding elements"""
        context = {
            "has_arc": False,
            "in_wall": False,
            "in_wall_opening": False,
            "has_parallel_lines": False,
            "parallel_lines_count": 0,
            "is_filled": False,
            "in_grid_pattern": False,
            "has_arrow": False,
            "adjacent_walls": 0,
        }
        
        # This would analyze surrounding elements to provide context
        # Simplified version for now
        
        return context