"""
PDF processor with confidence-aware ArxObject extraction
Following the strategic validation approach with multi-dimensional confidence
"""

import io
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
import fitz  # PyMuPDF
from PIL import Image
import cv2

from models.arxobject import (
    ArxObject, ArxObjectType, ConfidenceScore,
    ValidationState, Metadata, Relationship, RelationshipType,
    ConversionResult, Uncertainty
)
from utils.config import settings
from .confidence_calculator import ConfidenceCalculator
from .pattern_learner import PatternLearner


class PDFProcessor:
    """
    Core PDF processing engine with confidence scoring
    Implements strategic 80/20 validation approach
    """
    
    def __init__(self):
        self.confidence_calculator = ConfidenceCalculator()
        self.pattern_learner = PatternLearner()
        self.page_cache = {}
        
    async def process_pdf(
        self,
        pdf_content: bytes,
        building_type: Optional[str] = None,
        confidence_threshold: float = 0.6
    ) -> ConversionResult:
        """
        Process PDF and extract ArxObjects with confidence scoring
        
        Args:
            pdf_content: Raw PDF bytes
            building_type: Optional building type hint
            confidence_threshold: Minimum confidence for extraction
        
        Returns:
            ConversionResult with ArxObjects and confidence scores
        """
        start_time = time.time()
        
        # Open PDF
        pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        # Extract objects from all pages
        all_objects = []
        uncertainties = []
        
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc[page_num]
            
            # Extract vector graphics
            vector_objects = await self._extract_vector_objects(page, page_num)
            
            # Extract text annotations
            text_objects = await self._extract_text_objects(page, page_num)
            
            # Extract raster elements if present
            raster_objects = await self._extract_raster_objects(page, page_num)
            
            # Combine and deduplicate
            page_objects = self._merge_objects(
                vector_objects + text_objects + raster_objects
            )
            
            # Apply pattern learning
            if self.pattern_learner.has_patterns():
                page_objects = self.pattern_learner.apply_patterns(
                    page_objects, building_type
                )
            
            # Filter by confidence
            for obj in page_objects:
                if obj.confidence.overall >= confidence_threshold:
                    all_objects.append(obj)
                else:
                    uncertainties.append(
                        Uncertainty(
                            object_type=obj.type,
                            location={"x": obj.geometry.get("coordinates", [[0,0]])[0][0],
                                     "y": obj.geometry.get("coordinates", [[0,0]])[0][1]},
                            confidence=obj.confidence.overall,
                            reason=self._get_uncertainty_reason(obj)
                        )
                    )
        
        pdf_doc.close()
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(all_objects)
        
        # Record processing time
        processing_time = time.time() - start_time
        
        return ConversionResult(
            arxobjects=all_objects,
            overall_confidence=overall_confidence,
            uncertainties=uncertainties,
            processing_time=processing_time
        )
    
    async def _extract_vector_objects(
        self, page: fitz.Page, page_num: int
    ) -> List[ArxObject]:
        """Extract objects from vector graphics"""
        objects = []
        
        # Get page drawings
        drawings = page.get_drawings()
        
        for drawing in drawings:
            # Classify drawing type
            obj_type, confidence = self._classify_drawing(drawing)
            
            if obj_type:
                # Create ArxObject
                obj = self._create_arxobject_from_drawing(
                    drawing, obj_type, confidence, page_num
                )
                objects.append(obj)
        
        return objects
    
    async def _extract_text_objects(
        self, page: fitz.Page, page_num: int
    ) -> List[ArxObject]:
        """Extract objects from text annotations"""
        objects = []
        
        # Get text blocks
        text_blocks = page.get_text("dict")
        
        for block in text_blocks.get("blocks", []):
            if block.get("type") == 0:  # Text block
                # Analyze text for object identification
                obj_type, properties = self._analyze_text_block(block)
                
                if obj_type:
                    obj = self._create_arxobject_from_text(
                        block, obj_type, properties, page_num
                    )
                    objects.append(obj)
        
        return objects
    
    async def _extract_raster_objects(
        self, page: fitz.Page, page_num: int
    ) -> List[ArxObject]:
        """Extract objects from raster images using CV"""
        objects = []
        
        # Get page as image
        mat = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale
        img_data = mat.pil_tobytes(format="PNG")
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to OpenCV format
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Detect lines (walls)
        walls = self._detect_walls(cv_img, page_num)
        objects.extend(walls)
        
        # Detect symbols (doors, windows, fixtures)
        symbols = self._detect_symbols(cv_img, page_num)
        objects.extend(symbols)
        
        return objects
    
    def _classify_drawing(
        self, drawing: Dict
    ) -> Tuple[Optional[ArxObjectType], float]:
        """Classify a drawing element into ArxObject type"""
        
        # Get drawing properties
        items = drawing.get("items", [])
        if not items:
            return None, 0.0
        
        # Analyze geometry
        has_lines = any(item[0] == "l" for item in items)
        has_rect = any(item[0] == "re" for item in items)
        has_curve = any(item[0] == "c" for item in items)
        
        # Pattern matching for common elements
        if has_lines and not has_curve:
            # Likely a wall
            return ArxObjectType.WALL, 0.75
        elif has_rect:
            # Could be room, column, or equipment
            rect = drawing.get("rect", fitz.Rect())
            aspect_ratio = rect.width / rect.height if rect.height > 0 else 1
            
            if 0.8 < aspect_ratio < 1.2:
                # Square-ish - likely column
                return ArxObjectType.COLUMN, 0.70
            else:
                # Rectangle - likely room or equipment
                return ArxObjectType.ROOM, 0.65
        elif has_curve:
            # Could be plumbing or HVAC
            return ArxObjectType.PLUMBING_PIPE, 0.60
        
        return None, 0.0
    
    def _create_arxobject_from_drawing(
        self, drawing: Dict, obj_type: ArxObjectType, 
        base_confidence: float, page_num: int
    ) -> ArxObject:
        """Create ArxObject from drawing element"""
        
        rect = drawing.get("rect", fitz.Rect())
        
        # Calculate confidence scores
        confidence = self.confidence_calculator.calculate_drawing_confidence(
            drawing, obj_type, base_confidence
        )
        
        # Extract geometry
        geometry = self._extract_geometry(drawing)
        
        # Create object ID
        obj_id = f"pdf_p{page_num}_{obj_type.value}_{int(rect.x0)}_{int(rect.y0)}"
        
        return ArxObject(
            id=obj_id,
            type=obj_type,
            data={
                "source": "vector",
                "page": page_num,
                "stroke_width": drawing.get("width", 1),
                "color": drawing.get("color", None),
                "fill": drawing.get("fill", None)
            },
            confidence=confidence,
            geometry=geometry,
            relationships=[],
            metadata=Metadata(
                source="pdf_vector",
                created=time.strftime("%Y-%m-%dT%H:%M:%S"),
                validated=False
            ),
            validation_state=ValidationState.PENDING
        )
    
    def _analyze_text_block(
        self, block: Dict
    ) -> Tuple[Optional[ArxObjectType], Dict]:
        """Analyze text block for object information"""
        
        text = ""
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text += span.get("text", "") + " "
        
        text = text.strip().lower()
        
        # Pattern matching for common labels
        if "room" in text or "office" in text or "conference" in text:
            return ArxObjectType.ROOM, {"label": text}
        elif "electrical" in text or "panel" in text:
            return ArxObjectType.ELECTRICAL_PANEL, {"label": text}
        elif "hvac" in text or "mechanical" in text:
            return ArxObjectType.HVAC_UNIT, {"label": text}
        elif "stair" in text:
            return ArxObjectType.STAIR, {"label": text}
        elif "elevator" in text or "lift" in text:
            return ArxObjectType.ELEVATOR, {"label": text}
        
        return None, {}
    
    def _detect_walls(self, img: np.ndarray, page_num: int) -> List[ArxObject]:
        """Detect walls using line detection"""
        walls = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Line detection
        lines = cv2.HoughLinesP(
            edges, 1, np.pi/180, threshold=100,
            minLineLength=50, maxLineGap=10
        )
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Create wall object
                wall = self._create_wall_from_line(
                    x1, y1, x2, y2, page_num
                )
                walls.append(wall)
        
        return walls
    
    def _detect_symbols(self, img: np.ndarray, page_num: int) -> List[ArxObject]:
        """Detect symbols like doors, windows using template matching"""
        symbols = []
        
        # This would use template matching or ML model
        # For now, return empty list
        # In production, would use trained symbol detector
        
        return symbols
    
    def _create_wall_from_line(
        self, x1: int, y1: int, x2: int, y2: int, page_num: int
    ) -> ArxObject:
        """Create wall ArxObject from detected line"""
        
        # Calculate length
        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        
        # Calculate angle
        angle = np.degrees(np.arctan2(y2-y1, x2-x1))
        
        # Create confidence score (lower for raster detection)
        confidence = ConfidenceScore(
            classification=0.65,  # Moderate confidence from image
            position=0.70,        # Position accuracy from pixels
            properties=0.50,      # Limited properties from image
            relationships=0.40,   # No relationships yet
            overall=0.0
        )
        confidence.overall = confidence.calculate_weighted_average()
        
        return ArxObject(
            id=f"pdf_p{page_num}_wall_{x1}_{y1}",
            type=ArxObjectType.WALL,
            data={
                "source": "raster",
                "page": page_num,
                "length_pixels": length,
                "angle": angle
            },
            confidence=confidence,
            geometry={
                "type": "LineString",
                "coordinates": [[x1, y1], [x2, y2]]
            },
            relationships=[],
            metadata=Metadata(
                source="pdf_raster",
                created=time.strftime("%Y-%m-%dT%H:%M:%S"),
                validated=False
            ),
            validation_state=ValidationState.PENDING
        )
    
    def _merge_objects(self, objects: List[ArxObject]) -> List[ArxObject]:
        """Merge duplicate objects from different extraction methods"""
        
        merged = []
        processed = set()
        
        for i, obj1 in enumerate(objects):
            if i in processed:
                continue
            
            # Find potential duplicates
            duplicates = []
            for j, obj2 in enumerate(objects[i+1:], start=i+1):
                if j in processed:
                    continue
                    
                if self._are_duplicates(obj1, obj2):
                    duplicates.append(obj2)
                    processed.add(j)
            
            # Merge duplicates
            if duplicates:
                obj1 = self._merge_duplicate_objects(obj1, duplicates)
            
            merged.append(obj1)
            processed.add(i)
        
        return merged
    
    def _are_duplicates(self, obj1: ArxObject, obj2: ArxObject) -> bool:
        """Check if two objects are duplicates"""
        
        # Same type check
        if obj1.type != obj2.type:
            return False
        
        # Spatial proximity check
        if obj1.geometry and obj2.geometry:
            coords1 = obj1.geometry.get("coordinates", [[0,0]])
            coords2 = obj2.geometry.get("coordinates", [[0,0]])
            
            # Simple distance check (would be more sophisticated in production)
            if coords1 and coords2:
                dist = np.sqrt(
                    (coords1[0][0] - coords2[0][0])**2 +
                    (coords1[0][1] - coords2[0][1])**2
                )
                return dist < 10  # 10 pixel threshold
        
        return False
    
    def _merge_duplicate_objects(
        self, primary: ArxObject, duplicates: List[ArxObject]
    ) -> ArxObject:
        """Merge duplicate objects, improving confidence"""
        
        # Average confidence scores
        all_objects = [primary] + duplicates
        
        primary.confidence.classification = np.mean(
            [obj.confidence.classification for obj in all_objects]
        )
        primary.confidence.position = np.mean(
            [obj.confidence.position for obj in all_objects]
        )
        primary.confidence.properties = np.mean(
            [obj.confidence.properties for obj in all_objects]
        )
        primary.confidence.relationships = np.mean(
            [obj.confidence.relationships for obj in all_objects]
        )
        
        # Boost confidence for multiple detections
        boost = min(0.1 * len(duplicates), 0.3)
        primary.confidence.classification = min(
            primary.confidence.classification + boost, 1.0
        )
        
        # Recalculate overall
        primary.confidence.overall = primary.confidence.calculate_weighted_average()
        
        # Merge properties
        for dup in duplicates:
            primary.data.update(dup.data)
        
        return primary
    
    def _extract_geometry(self, drawing: Dict) -> Dict:
        """Extract geometry from drawing element"""
        
        items = drawing.get("items", [])
        rect = drawing.get("rect", fitz.Rect())
        
        # Build coordinate list
        coords = []
        for item in items:
            if item[0] == "l":  # Line
                coords.append([item[1].x, item[1].y])
                coords.append([item[2].x, item[2].y])
            elif item[0] == "re":  # Rectangle
                r = item[1]
                coords = [
                    [r.x0, r.y0],
                    [r.x1, r.y0],
                    [r.x1, r.y1],
                    [r.x0, r.y1],
                    [r.x0, r.y0]
                ]
        
        if len(coords) == 2:
            # Line
            return {
                "type": "LineString",
                "coordinates": coords
            }
        elif len(coords) > 2:
            # Polygon
            return {
                "type": "Polygon",
                "coordinates": [coords]
            }
        else:
            # Point
            return {
                "type": "Point",
                "coordinates": [rect.x0, rect.y0]
            }
    
    def _calculate_overall_confidence(
        self, objects: List[ArxObject]
    ) -> float:
        """Calculate overall confidence for extraction result"""
        
        if not objects:
            return 0.0
        
        # Weighted average based on object importance
        total_weight = 0.0
        weighted_sum = 0.0
        
        for obj in objects:
            # Weight by object type importance
            weight = self._get_object_weight(obj.type)
            weighted_sum += obj.confidence.overall * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _get_object_weight(self, obj_type: ArxObjectType) -> float:
        """Get importance weight for object type"""
        
        # Structural elements most important
        if obj_type in [ArxObjectType.WALL, ArxObjectType.COLUMN, 
                        ArxObjectType.BEAM, ArxObjectType.FOUNDATION]:
            return 1.0
        # MEP systems important
        elif obj_type in [ArxObjectType.ELECTRICAL_PANEL, ArxObjectType.HVAC_UNIT,
                         ArxObjectType.PLUMBING_FIXTURE]:
            return 0.8
        # Spatial elements
        elif obj_type in [ArxObjectType.ROOM, ArxObjectType.FLOOR, 
                         ArxObjectType.BUILDING]:
            return 0.7
        # Other elements
        else:
            return 0.5
    
    def _get_uncertainty_reason(self, obj: ArxObject) -> str:
        """Get human-readable reason for uncertainty"""
        
        conf = obj.confidence
        
        if conf.classification < 0.6:
            return "Uncertain object classification"
        elif conf.position < 0.6:
            return "Imprecise spatial location"
        elif conf.properties < 0.6:
            return "Incomplete property data"
        elif conf.relationships < 0.6:
            return "Unclear relationships"
        else:
            return "Overall confidence below threshold"