"""
PDF processor with confidence-aware ArxObject extraction
Following the strategic validation approach with multi-dimensional confidence
"""

import io
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
import pdfplumber  # Using pdfplumber for PDF processing
HAS_PDFPLUMBER = True
# Note: We're using pdfplumber exclusively to avoid PyMuPDF build issues on Mac
from PIL import Image
import cv2

from models.arxobject import (
    ArxObject, ArxObjectType, ConfidenceScore,
    ValidationState, Metadata, Relationship, RelationshipType,
    ConversionResult, Uncertainty
)
from models.coordinate_system import (
    CoordinateSystem, Point3D, BoundingBox, 
    Dimensions, Transform, Units
)
from utils.config import settings
from .confidence_calculator import ConfidenceCalculator
from .pattern_learner import PatternLearner

# Import multi-strategy processor if available
try:
    from .extraction_strategies import MultiStrategyProcessor
    HAS_MULTI_STRATEGY = True
except ImportError:
    HAS_MULTI_STRATEGY = False


class PDFProcessor:
    """
    Core PDF processing engine with confidence scoring
    Implements strategic 80/20 validation approach
    """
    
    def __init__(self):
        self.confidence_calculator = ConfidenceCalculator()
        self.pattern_learner = PatternLearner()
        self.page_cache = {}
        self.coordinate_system: Optional[CoordinateSystem] = None
        
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
        if HAS_PDFPLUMBER:
            # Use pdfplumber
            import io
            pdf_doc = pdfplumber.open(io.BytesIO(pdf_content))
        else:
            # Use PyMuPDF
            pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        # Initialize coordinate system and detect scale
        self.coordinate_system = await self._initialize_coordinate_system(pdf_doc)
        
        # Extract objects from all pages
        all_objects = []
        uncertainties = []
        
        # Use multi-strategy processor if available for better accuracy
        if HAS_MULTI_STRATEGY:
            # Save PDF to temporary file for multi-strategy processing
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_content)
                tmp_path = tmp_file.name
            
            try:
                # Use multi-strategy processor
                multi_processor = MultiStrategyProcessor(self.coordinate_system)
                all_objects = multi_processor.process(tmp_path)
                
                # Clean up temp file
                import os
                os.unlink(tmp_path)
                
            except Exception as e:
                print(f"Multi-strategy processing failed: {e}, falling back to basic extraction")
                # Fall back to basic extraction
                all_objects = await self._basic_extraction(pdf_doc, confidence_threshold, building_type)
        else:
            # Use basic extraction
            all_objects = await self._basic_extraction(pdf_doc, confidence_threshold, building_type)
        
        pdf_doc.close()
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(all_objects)
        
        # Record processing time
        processing_time = time.time() - start_time
        
        return ConversionResult(
            arxobjects=all_objects,
            overall_confidence=overall_confidence,
            uncertainties=uncertainties,
            validation_strategy=None,  # TODO: Implement validation strategy
            processing_time=processing_time
        )
    
    async def _basic_extraction(self, pdf_doc, confidence_threshold: float, building_type: Optional[str]) -> List[ArxObject]:
        """Basic extraction method using existing approach"""
        all_objects = []
        uncertainties = []
        
        # Get page count based on library
        if HAS_PDFPLUMBER:
            page_count = len(pdf_doc.pages)
        else:
            page_count = pdf_doc.page_count
            
        for page_num in range(page_count):
            if HAS_PDFPLUMBER:
                page = pdf_doc.pages[page_num]
            else:
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
            
            # Skip room grouping - let users organize as needed
            # page_objects = self._group_walls_into_rooms(page_objects)
            
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
                            object_id=obj.id,
                            confidence=obj.confidence.overall,
                            reason=self._get_uncertainty_reason(obj),
                            validation_priority=1.0 - obj.confidence.overall,
                            suggested_validation="field_measurement",
                            impact_score=0.5
                        )
                    )
        
        return all_objects
    
    async def _extract_vector_objects(
        self, page: Any, page_num: int
    ) -> List[ArxObject]:
        """Extract objects from vector graphics"""
        objects = []
        
        # Get page drawings - pdfplumber uses different API
        # Extract lines and rectangles from the page
        drawings = []
        
        # Handle pdfplumber's lines (each line is a dict with x0, y0, x1, y1)
        if hasattr(page, 'lines') and page.lines:
            for line in page.lines:
                try:
                    # Try to handle as dict
                    if isinstance(line, dict):
                        drawings.append({
                            'type': 'line',
                            'x0': line.get('x0', 0),
                            'y0': line.get('y0', 0),
                            'x1': line.get('x1', 0),
                            'y1': line.get('y1', 0),
                            'width': line.get('width', 1),
                        })
                    elif isinstance(line, (tuple, list)) and len(line) >= 4:
                        # Handle as tuple/list with coordinates
                        drawings.append({
                            'type': 'line',
                            'x0': float(line[0]),
                            'y0': float(line[1]),
                            'x1': float(line[2]),
                            'y1': float(line[3]),
                            'width': 1,
                        })
                except Exception as e:
                    print(f"Error processing line: {e}")
                    continue
        
        # Handle pdfplumber's rects (each rect is a dict with x0, y0, x1, y1)
        if hasattr(page, 'rects') and page.rects:
            for rect in page.rects:
                try:
                    if isinstance(rect, dict):
                        drawings.append({
                            'type': 'rect',
                            'x0': rect.get('x0', 0),
                            'y0': rect.get('y0', 0),
                            'x1': rect.get('x1', 0),
                            'y1': rect.get('y1', 0),
                            'width': rect.get('width', abs(rect.get('x1', 0) - rect.get('x0', 0))),
                            'height': rect.get('height', abs(rect.get('y1', 0) - rect.get('y0', 0))),
                        })
                    elif isinstance(rect, (tuple, list)) and len(rect) >= 4:
                        # Handle as tuple/list with coordinates
                        x0, y0, x1, y1 = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
                        drawings.append({
                            'type': 'rect',
                            'x0': x0,
                            'y0': y0,
                            'x1': x1,
                            'y1': y1,
                            'width': abs(x1 - x0),
                            'height': abs(y1 - y0),
                        })
                except Exception as e:
                    print(f"Error processing rect: {e}")
                    continue
        
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
        self, page: Any, page_num: int
    ) -> List[ArxObject]:
        """Extract ALL text as ArxObjects for user management"""
        objects = []
        
        # Extract text with positions using pdfplumber
        if hasattr(page, 'extract_words'):
            words = page.extract_words()
            for word in words:
                # Create text object for each word/label
                text_obj = ArxObject(
                    id=f"text_p{page_num}_{int(word.get('x0', 0))}_{int(word.get('top', 0))}",
                    type=ArxObjectType.TEXT,  # Add TEXT type for labels
                    data={
                        "text": word.get('text', ''),
                        "font_size": word.get('height', 10),
                        "source": "pdf_text",
                        "page": page_num
                    },
                    confidence=ConfidenceScore(
                        classification=0.95,  # High confidence - we know it's text
                        position=0.90,
                        properties=0.95,
                        relationships=0.30,
                        overall=0.80
                    ),
                    geometry={
                        "type": "Point",
                        "coordinates": [word.get('x0', 0), word.get('top', 0)]
                    },
                    relationships=[],
                    metadata=Metadata(
                        source="pdf_text",
                        created=time.strftime("%Y-%m-%dT%H:%M:%S"),
                        validated=False
                    ),
                    validation_state=ValidationState.PENDING
                )
                objects.append(text_obj)
        
        return objects
    
    async def _extract_raster_objects(
        self, page: Any, page_num: int
    ) -> List[ArxObject]:
        """Extract objects from raster images using CV"""
        objects = []
        
        # Get page as image using pdfplumber
        # Convert page to PIL image
        img = page.to_image(resolution=150).original
        
        # Ensure it's in the right format
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
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
        """Classify a drawing element - EXTRACT EVERYTHING for user cleanup"""
        
        draw_type = drawing.get('type', '')
        
        # Extract ALL lines as potential walls/elements
        if draw_type == 'line':
            x0 = drawing.get('x0', 0)
            y0 = drawing.get('y0', 0)
            x1 = drawing.get('x1', 0)
            y1 = drawing.get('y1', 0)
            line_width = drawing.get('width', 1)
            
            # Calculate line properties for confidence scoring
            length = ((x1 - x0)**2 + (y1 - y0)**2)**0.5
            
            # Don't filter anything - let users decide what to keep
            # Just adjust confidence based on likelihood
            if length < 5:
                # Very short - might be text or noise, low confidence
                return ArxObjectType.WALL, 0.30
            elif line_width < 0.5:
                # Thin line - might be dimension line, medium-low confidence
                return ArxObjectType.WALL, 0.40
            elif line_width >= 1.0:
                # Thicker line - likely actual wall, higher confidence
                return ArxObjectType.WALL, 0.75
            else:
                # Everything else gets medium confidence
                return ArxObjectType.WALL, 0.50
                
        elif draw_type == 'rect':
            # Extract ALL rectangles
            width = abs(drawing.get('width', drawing.get('x1', 0) - drawing.get('x0', 0)))
            height = abs(drawing.get('height', drawing.get('y1', 0) - drawing.get('y0', 0)))
            
            if width > 0 and height > 0:
                aspect_ratio = width / height
                area = width * height
                
                # Classify but don't filter
                if 0.8 < aspect_ratio < 1.2 and area < 400:
                    # Square-ish - might be column
                    return ArxObjectType.COLUMN, 0.60
                else:
                    # Rectangle - could be room, equipment, or annotation box
                    return ArxObjectType.ROOM, 0.50
        
        # Even if we can't classify it, still extract it as generic object
        return ArxObjectType.WALL, 0.30
    
    def _create_arxobject_from_drawing(
        self, drawing: Dict, obj_type: ArxObjectType, 
        base_confidence: float, page_num: int
    ) -> ArxObject:
        """Create ArxObject from drawing element"""
        
        # Get bounding rect from drawing
        rect = drawing if isinstance(drawing, dict) else {}
        
        # Calculate confidence scores
        confidence = self.confidence_calculator.calculate_drawing_confidence(
            drawing, obj_type, base_confidence
        )
        
        # Extract geometry
        geometry = self._extract_geometry(drawing)
        
        # Create object ID
        x0 = rect.get('x0', rect.get('x', 0))
        y0 = rect.get('y0', rect.get('y', 0))
        obj_id = f"pdf_p{page_num}_{obj_type.value}_{int(x0)}_{int(y0)}"
        
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
            return ArxObjectType.STAIRWELL, {"label": text}
        elif "elevator" in text or "lift" in text:
            return ArxObjectType.ELEVATOR_SHAFT, {"label": text}
        
        return None, {}
    
    def _detect_walls(self, img: np.ndarray, page_num: int) -> List[ArxObject]:
        """Detect walls using line detection"""
        walls = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Line detection with more conservative parameters
        # Increase threshold to reduce false positives
        # Increase minLineLength to filter out small segments
        lines = cv2.HoughLinesP(
            edges, 1, np.pi/180, threshold=150,  # Increased from 100
            minLineLength=100, maxLineGap=20     # Increased from 50 and 10
        )
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Convert numpy types to Python native types
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
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
    
    async def _initialize_coordinate_system(self, pdf_doc) -> CoordinateSystem:
        """
        Initialize coordinate system and detect scale from PDF
        """
        # Get first page dimensions
        if HAS_PDFPLUMBER:
            page = pdf_doc.pages[0]
            width = float(page.width)
            height = float(page.height)
            # Extract text to find scale
            text = page.extract_text() or ""
        else:
            page = pdf_doc[0]
            rect = page.rect
            width = rect.width
            height = rect.height
            text = page.get_text()
        
        # Initialize coordinate system with page dimensions
        coord_sys = CoordinateSystem(
            pdf_width_pixels=int(width),
            pdf_height_pixels=int(height),
            pdf_dpi=72.0,  # Standard PDF DPI
            scale_numerator=1.0,
            scale_denominator=48.0,  # Default 1/4" = 1'
            units=Units.IMPERIAL
        )
        
        # Try to extract scale from text
        if text:
            coord_sys.extract_scale_from_text(text)
        
        return coord_sys
    
    def _create_wall_from_line(
        self, x1: int, y1: int, x2: int, y2: int, page_num: int
    ) -> ArxObject:
        """Create wall ArxObject from detected line with proper world coordinates"""
        
        # Convert PDF coordinates to world space
        world_p1 = self.coordinate_system.pdf_to_world_point(x1, y1)
        world_p2 = self.coordinate_system.pdf_to_world_point(x2, y2)
        
        # Calculate real-world dimensions
        width_nm = abs(world_p2.x - world_p1.x)
        height_nm = abs(world_p2.y - world_p1.y)
        length_nm = int(np.sqrt(float(width_nm)**2 + float(height_nm)**2))
        
        # Standard wall thickness (6 inches in nanometers)
        thickness_nm = 152_400_000  # 6 inches
        
        # Create bounding box
        min_x = min(world_p1.x, world_p2.x)
        min_y = min(world_p1.y, world_p2.y)
        max_x = max(world_p1.x, world_p2.x)
        max_y = max(world_p1.y, world_p2.y)
        
        # Add thickness to bounding box based on orientation
        if width_nm > height_nm:  # Horizontal wall
            bounds = BoundingBox(
                min_point=Point3D(x=min_x, y=min_y - thickness_nm//2, z=0),
                max_point=Point3D(x=max_x, y=max_y + thickness_nm//2, z=0)
            )
            dimensions = Dimensions(width=length_nm, height=thickness_nm, depth=0)
        else:  # Vertical wall
            bounds = BoundingBox(
                min_point=Point3D(x=min_x - thickness_nm//2, y=min_y, z=0),
                max_point=Point3D(x=max_x + thickness_nm//2, y=max_y, z=0)
            )
            dimensions = Dimensions(width=thickness_nm, height=length_nm, depth=0)
        
        # Calculate center position
        position = Point3D(
            x=(world_p1.x + world_p2.x) // 2,
            y=(world_p1.y + world_p2.y) // 2,
            z=0
        )
        
        # Calculate angle for transform
        angle = float(np.degrees(np.arctan2(
            float(world_p2.y - world_p1.y), 
            float(world_p2.x - world_p1.x)
        )))
        
        # Create confidence score (lower for raster detection)
        confidence = ConfidenceScore(
            classification=0.65,  # Moderate confidence from image
            position=0.70,        # Position accuracy from pixels
            properties=0.50,      # Limited properties from image
            relationships=0.40,   # No relationships yet
            overall=0.0
        )
        # Calculate weighted average
        confidence.overall = (
            confidence.classification * 0.4 +
            confidence.position * 0.3 +
            confidence.properties * 0.2 +
            confidence.relationships * 0.1
        )
        
        return ArxObject(
            id=f"pdf_p{page_num}_wall_{int(position.x/1_000_000)}_{int(position.y/1_000_000)}",
            type=ArxObjectType.WALL,
            
            # Spatial properties with nanometer precision
            position=position,
            dimensions=dimensions,
            bounds=bounds,
            transform=Transform.rotation_z(float(np.radians(angle))),
            
            # Legacy data for compatibility
            data={
                "source": "raster",
                "page": page_num,
                "angle_degrees": angle,
                "thickness_inches": 6,
                # Add millimeter values for frontend
                "x_mm": position.x / 1_000_000,
                "y_mm": position.y / 1_000_000,
                "length_mm": length_nm / 1_000_000,
                "thickness_mm": thickness_nm / 1_000_000
            },
            
            # GeoJSON for compatibility
            geometry={
                "type": "LineString",
                "coordinates": [
                    [world_p1.x / 1_000_000, world_p1.y / 1_000_000],
                    [world_p2.x / 1_000_000, world_p2.y / 1_000_000]
                ]
            },
            
            confidence=confidence,
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
                dist = float(np.sqrt(
                    (coords1[0][0] - coords2[0][0])**2 +
                    (coords1[0][1] - coords2[0][1])**2
                ))
                return dist < 10  # 10 pixel threshold
        
        return False
    
    def _group_walls_into_rooms(self, objects: List[ArxObject]) -> List[ArxObject]:
        """Group connected walls to identify rooms"""
        import math
        
        # Separate walls from other objects
        walls = [obj for obj in objects if obj.type == ArxObjectType.WALL]
        other_objects = [obj for obj in objects if obj.type != ArxObjectType.WALL]
        
        # If no walls, return as is
        if not walls:
            return objects
        
        # Group walls by proximity
        wall_groups = []
        used_walls = set()
        
        for i, wall in enumerate(walls):
            if i in used_walls:
                continue
                
            # Start a new group
            group = [wall]
            used_walls.add(i)
            
            # Find connected walls
            if wall.geometry and wall.geometry.get('type') == 'LineString':
                coords = wall.geometry.get('coordinates', [])
                if len(coords) >= 2:
                    # Get wall endpoints
                    wall_start = coords[0]
                    wall_end = coords[1]
                    
                    # Look for walls that connect to this one
                    for j, other_wall in enumerate(walls):
                        if j in used_walls or j == i:
                            continue
                            
                        if other_wall.geometry and other_wall.geometry.get('type') == 'LineString':
                            other_coords = other_wall.geometry.get('coordinates', [])
                            if len(other_coords) >= 2:
                                other_start = other_coords[0]
                                other_end = other_coords[1]
                                
                                # Check if walls connect (within tolerance)
                                tolerance = 5  # pixels
                                
                                # Check all connection possibilities
                                connections = [
                                    (wall_start, other_start),
                                    (wall_start, other_end),
                                    (wall_end, other_start),
                                    (wall_end, other_end)
                                ]
                                
                                for p1, p2 in connections:
                                    dist = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                                    if dist < tolerance:
                                        group.append(other_wall)
                                        used_walls.add(j)
                                        break
            
            wall_groups.append(group)
        
        # Create room objects from wall groups that form enclosures
        room_objects = []
        for group in wall_groups:
            if len(group) >= 3:  # Need at least 3 walls for a room
                # Calculate bounding box of wall group
                all_coords = []
                for wall in group:
                    if wall.geometry and wall.geometry.get('coordinates'):
                        all_coords.extend(wall.geometry['coordinates'])
                
                if all_coords:
                    xs = [c[0] for c in all_coords]
                    ys = [c[1] for c in all_coords]
                    
                    # Create room object
                    room = ArxObject(
                        id=f"room_{min(xs)}_{min(ys)}",
                        type=ArxObjectType.ROOM,
                        data={
                            "wall_count": len(group),
                            "source": "wall_grouping"
                        },
                        confidence=ConfidenceScore(
                            classification=0.60,  # Moderate confidence from grouping
                            position=0.80,
                            properties=0.50,
                            relationships=0.70,
                            overall=0.65
                        ),
                        geometry={
                            "type": "Polygon",
                            "coordinates": [[
                                [min(xs), min(ys)],
                                [max(xs), min(ys)],
                                [max(xs), max(ys)],
                                [min(xs), max(ys)],
                                [min(xs), min(ys)]
                            ]]
                        },
                        relationships=[],
                        metadata=Metadata(
                            source="wall_grouping",
                            created=time.strftime("%Y-%m-%dT%H:%M:%S"),
                            validated=False
                        ),
                        validation_state=ValidationState.PENDING
                    )
                    room_objects.append(room)
                    
                    # Add relationships between room and walls
                    for wall in group:
                        wall.relationships.append(
                            Relationship(
                                type="contained_by",
                                target_id=room.id,
                                confidence=0.70
                            )
                        )
        
        # Return all objects including new rooms
        return walls + other_objects + room_objects
    
    def _merge_duplicate_objects(
        self, primary: ArxObject, duplicates: List[ArxObject]
    ) -> ArxObject:
        """Merge duplicate objects, improving confidence"""
        
        # Average confidence scores
        all_objects = [primary] + duplicates
        
        primary.confidence.classification = float(np.mean(
            [obj.confidence.classification for obj in all_objects]
        ))
        primary.confidence.position = float(np.mean(
            [obj.confidence.position for obj in all_objects]
        ))
        primary.confidence.properties = float(np.mean(
            [obj.confidence.properties for obj in all_objects]
        ))
        primary.confidence.relationships = float(np.mean(
            [obj.confidence.relationships for obj in all_objects]
        ))
        
        # Boost confidence for multiple detections
        boost = min(0.1 * len(duplicates), 0.3)
        primary.confidence.classification = min(
            primary.confidence.classification + boost, 1.0
        )
        
        # Recalculate overall
        # Calculate weighted average
        primary.confidence.overall = (
            primary.confidence.classification * 0.4 +
            primary.confidence.position * 0.3 +
            primary.confidence.properties * 0.2 +
            primary.confidence.relationships * 0.1
        )
        
        # Merge properties
        for dup in duplicates:
            primary.data.update(dup.data)
        
        return primary
    
    def _extract_geometry(self, drawing: Dict) -> Dict:
        """Extract geometry from drawing element"""
        
        draw_type = drawing.get('type', '')
        
        if draw_type == 'line':
            # Line geometry
            return {
                "type": "LineString",
                "coordinates": [
                    [drawing.get('x0', 0), drawing.get('y0', 0)],
                    [drawing.get('x1', 0), drawing.get('y1', 0)]
                ]
            }
        elif draw_type == 'rect':
            # Rectangle as polygon
            x0 = drawing.get('x0', 0)
            y0 = drawing.get('y0', 0)
            x1 = drawing.get('x1', 0)
            y1 = drawing.get('y1', 0)
            return {
                "type": "Polygon",
                "coordinates": [[
                    [x0, y0],
                    [x1, y0],
                    [x1, y1],
                    [x0, y1],
                    [x0, y0]
                ]]
            }
        else:
            # Default to point at origin
            x0 = drawing.get('x0', drawing.get('x', 0))
            y0 = drawing.get('y0', drawing.get('y', 0))
            return {
                "type": "Point",
                "coordinates": [x0, y0]
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