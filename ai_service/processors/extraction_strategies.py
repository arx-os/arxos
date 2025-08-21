"""
PDF Extraction Strategies for Arxos
Multiple approaches to extract building information from PDFs
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np
import fitz  # PyMuPDF
from PIL import Image
import io
from dataclasses import dataclass
from enum import Enum

from models.arxobject import ArxObject, ArxObjectType, ConfidenceScore, Metadata
from models.coordinate_system import CoordinateSystem, Point3D, BoundingBox, Dimensions

# Import component recognizers if available
try:
    from .component_recognizers import ComponentClassifier, ComponentFeatures
    HAS_RECOGNIZERS = True
except ImportError:
    HAS_RECOGNIZERS = False

# Import topology analyzer if available
try:
    from .topology_analyzer import TopologyAnalyzer
    HAS_TOPOLOGY = True
except ImportError:
    HAS_TOPOLOGY = False


class ExtractionMethod(Enum):
    """Available extraction methods"""
    VECTOR = "vector"  # Extract vector paths from PDF
    RASTER = "raster"  # Convert to image and process
    TEXT = "text"      # Extract text annotations
    HYBRID = "hybrid"  # Combine multiple methods


@dataclass
class ExtractedElement:
    """Raw element extracted from PDF"""
    type: str
    geometry: Any  # Can be path, polygon, line, etc.
    attributes: Dict[str, Any]
    confidence: float
    method: ExtractionMethod
    page: int


class ExtractionStrategy(ABC):
    """Base class for extraction strategies"""
    
    def __init__(self, coordinate_system: CoordinateSystem):
        self.coordinate_system = coordinate_system
    
    @abstractmethod
    def extract(self, pdf_path: str) -> List[ExtractedElement]:
        """Extract elements from PDF"""
        pass
    
    @abstractmethod
    def get_confidence_multiplier(self) -> float:
        """Return confidence multiplier for this strategy"""
        pass


class VectorExtractionStrategy(ExtractionStrategy):
    """
    Extract vector graphics directly from PDF
    Best for CAD exports and vector-based floor plans
    """
    
    def get_confidence_multiplier(self) -> float:
        return 0.9  # High confidence for vector data
    
    def extract(self, pdf_path: str) -> List[ExtractedElement]:
        """Extract vector paths from PDF"""
        elements = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc):
                # Get page dimensions
                rect = page.rect
                
                # Extract vector drawings
                drawings = page.get_drawings()
                
                for drawing in drawings:
                    # Process each drawing item (path, line, rect, etc.)
                    for item in drawing["items"]:
                        element = self._process_vector_item(item, page_num)
                        if element:
                            elements.append(element)
                
                # Extract text for annotations and labels
                text_blocks = page.get_text("blocks")
                for block in text_blocks:
                    if self._is_annotation(block):
                        element = self._process_text_annotation(block, page_num)
                        if element:
                            elements.append(element)
            
            doc.close()
            
        except Exception as e:
            print(f"Vector extraction error: {e}")
        
        return elements
    
    def _process_vector_item(self, item: Dict, page_num: int) -> Optional[ExtractedElement]:
        """Process a single vector item"""
        item_type = item.get("type", "")
        
        if item_type == "l":  # Line
            return self._extract_line(item, page_num)
        elif item_type == "r":  # Rectangle
            return self._extract_rectangle(item, page_num)
        elif item_type == "c":  # Curve
            return self._extract_curve(item, page_num)
        elif item_type == "qu":  # Quad
            return self._extract_quad(item, page_num)
        
        return None
    
    def _extract_line(self, item: Dict, page_num: int) -> ExtractedElement:
        """Extract line element"""
        p1 = item.get("p1", (0, 0))
        p2 = item.get("p2", (0, 0))
        
        # Calculate line properties
        length = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        angle = np.arctan2(p2[1] - p1[1], p2[0] - p1[0])
        
        # Determine if it's likely a wall based on thickness and length
        stroke_width = item.get("width", 1)
        is_wall = length > 50 and stroke_width > 0.5
        
        return ExtractedElement(
            type="wall" if is_wall else "line",
            geometry={"type": "LineString", "coordinates": [p1, p2]},
            attributes={
                "length": length,
                "angle": angle,
                "stroke_width": stroke_width,
                "color": item.get("color", None)
            },
            confidence=0.8 if is_wall else 0.6,
            method=ExtractionMethod.VECTOR,
            page=page_num
        )
    
    def _extract_rectangle(self, item: Dict, page_num: int) -> ExtractedElement:
        """Extract rectangle element"""
        rect = item.get("rect", [0, 0, 0, 0])
        
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        area = width * height
        
        # Classify based on dimensions
        if area > 10000:  # Large area - likely a room
            element_type = "room"
            confidence = 0.85
        elif width > height * 5 or height > width * 5:  # Long and thin - likely a wall
            element_type = "wall"
            confidence = 0.75
        else:
            element_type = "opening"
            confidence = 0.6
        
        return ExtractedElement(
            type=element_type,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [rect[0], rect[1]],
                    [rect[2], rect[1]],
                    [rect[2], rect[3]],
                    [rect[0], rect[3]],
                    [rect[0], rect[1]]
                ]]
            },
            attributes={
                "width": width,
                "height": height,
                "area": area,
                "fill": item.get("fill", None),
                "stroke": item.get("stroke", None)
            },
            confidence=confidence,
            method=ExtractionMethod.VECTOR,
            page=page_num
        )
    
    def _extract_curve(self, item: Dict, page_num: int) -> ExtractedElement:
        """Extract curve element (often doors)"""
        # Curves often represent door swings
        return ExtractedElement(
            type="door",
            geometry={"type": "Curve", "points": item.get("points", [])},
            attributes={
                "radius": item.get("radius", 0),
                "arc_angle": item.get("arc", 90)
            },
            confidence=0.7,
            method=ExtractionMethod.VECTOR,
            page=page_num
        )
    
    def _extract_quad(self, item: Dict, page_num: int) -> ExtractedElement:
        """Extract quadrilateral element"""
        quad = item.get("quad", [])
        
        return ExtractedElement(
            type="polygon",
            geometry={"type": "Polygon", "coordinates": [quad + [quad[0]]]},
            attributes={},
            confidence=0.6,
            method=ExtractionMethod.VECTOR,
            page=page_num
        )
    
    def _is_annotation(self, block: tuple) -> bool:
        """Check if text block is likely an annotation"""
        text = block[4].strip()
        # Common annotation patterns
        patterns = ["DOOR", "WINDOW", "ROOM", "WALL", "ELEV", "STAIR", r"\d+'-\d+\"", r"\d+mm", r"\d+m"]
        return any(pattern in text.upper() for pattern in patterns[:6])
    
    def _process_text_annotation(self, block: tuple, page_num: int) -> ExtractedElement:
        """Process text annotation"""
        x0, y0, x1, y1, text = block[:5]
        
        return ExtractedElement(
            type="annotation",
            geometry={"type": "Point", "coordinates": [(x0 + x1) / 2, (y0 + y1) / 2]},
            attributes={"text": text.strip()},
            confidence=0.9,
            method=ExtractionMethod.TEXT,
            page=page_num
        )


class RasterExtractionStrategy(ExtractionStrategy):
    """
    Convert PDF to image and use computer vision
    Better for scanned documents and complex drawings
    """
    
    def get_confidence_multiplier(self) -> float:
        return 0.7  # Lower confidence for raster processing
    
    def extract(self, pdf_path: str) -> List[ExtractedElement]:
        """Extract elements using computer vision on rasterized PDF"""
        elements = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc):
                # Convert page to image
                mat = fitz.Matrix(300/72, 300/72)  # 300 DPI
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to OpenCV format
                img = Image.open(io.BytesIO(img_data))
                cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Extract lines using Hough transform
                lines = self._detect_lines(cv_image)
                for line in lines:
                    element = self._line_to_element(line, page_num, cv_image.shape)
                    if element:
                        elements.append(element)
                
                # Detect rectangles
                rectangles = self._detect_rectangles(cv_image)
                for rect in rectangles:
                    element = self._rect_to_element(rect, page_num, cv_image.shape)
                    if element:
                        elements.append(element)
                
                # Detect circles (often symbols)
                circles = self._detect_circles(cv_image)
                for circle in circles:
                    element = self._circle_to_element(circle, page_num, cv_image.shape)
                    if element:
                        elements.append(element)
            
            doc.close()
            
        except Exception as e:
            print(f"Raster extraction error: {e}")
        
        return elements
    
    def _detect_lines(self, image: np.ndarray) -> List[np.ndarray]:
        """Detect lines using Hough transform"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10
        )
        
        return lines if lines is not None else []
    
    def _detect_rectangles(self, image: np.ndarray) -> List[np.ndarray]:
        """Detect rectangles using contour detection"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangles = []
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's a rectangle (4 vertices)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                rectangles.append([x, y, w, h])
        
        return rectangles
    
    def _detect_circles(self, image: np.ndarray) -> List[np.ndarray]:
        """Detect circles using Hough circles"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=50,
            param2=30,
            minRadius=5,
            maxRadius=50
        )
        
        return circles[0] if circles is not None else []
    
    def _line_to_element(self, line: np.ndarray, page_num: int, shape: tuple) -> ExtractedElement:
        """Convert detected line to element"""
        x1, y1, x2, y2 = line[0]
        
        # Scale coordinates back to PDF space
        scale_x = self.coordinate_system.pdf_width_pixels / shape[1]
        scale_y = self.coordinate_system.pdf_height_pixels / shape[0]
        
        x1, y1 = x1 * scale_x, y1 * scale_y
        x2, y2 = x2 * scale_x, y2 * scale_y
        
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        return ExtractedElement(
            type="wall" if length > 100 else "line",
            geometry={"type": "LineString", "coordinates": [[x1, y1], [x2, y2]]},
            attributes={"length": length},
            confidence=0.6,
            method=ExtractionMethod.RASTER,
            page=page_num
        )
    
    def _rect_to_element(self, rect: List[int], page_num: int, shape: tuple) -> ExtractedElement:
        """Convert detected rectangle to element"""
        x, y, w, h = rect
        
        # Scale coordinates back to PDF space
        scale_x = self.coordinate_system.pdf_width_pixels / shape[1]
        scale_y = self.coordinate_system.pdf_height_pixels / shape[0]
        
        x, y = x * scale_x, y * scale_y
        w, h = w * scale_x, h * scale_y
        
        area = w * h
        
        # Classify based on size
        if area > 5000:
            element_type = "room"
        elif w > h * 3 or h > w * 3:
            element_type = "wall"
        else:
            element_type = "opening"
        
        return ExtractedElement(
            type=element_type,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]
                ]]
            },
            attributes={"width": w, "height": h, "area": area},
            confidence=0.5,
            method=ExtractionMethod.RASTER,
            page=page_num
        )
    
    def _circle_to_element(self, circle: np.ndarray, page_num: int, shape: tuple) -> ExtractedElement:
        """Convert detected circle to element"""
        x, y, r = circle
        
        # Scale coordinates back to PDF space
        scale_x = self.coordinate_system.pdf_width_pixels / shape[1]
        scale_y = self.coordinate_system.pdf_height_pixels / shape[0]
        
        x, y = x * scale_x, y * scale_y
        r = r * scale_x
        
        return ExtractedElement(
            type="symbol",
            geometry={"type": "Point", "coordinates": [x, y]},
            attributes={"radius": r},
            confidence=0.4,
            method=ExtractionMethod.RASTER,
            page=page_num
        )


class HybridExtractionStrategy(ExtractionStrategy):
    """
    Combine multiple extraction strategies and merge results
    Provides best overall accuracy
    """
    
    def __init__(self, coordinate_system: CoordinateSystem):
        super().__init__(coordinate_system)
        self.strategies = [
            VectorExtractionStrategy(coordinate_system),
            RasterExtractionStrategy(coordinate_system)
        ]
    
    def get_confidence_multiplier(self) -> float:
        return 0.95  # Highest confidence for hybrid approach
    
    def extract(self, pdf_path: str) -> List[ExtractedElement]:
        """Extract using all strategies and merge results"""
        all_elements = []
        
        # Run all extraction strategies
        for strategy in self.strategies:
            elements = strategy.extract(pdf_path)
            all_elements.extend(elements)
        
        # Merge and deduplicate elements
        merged = self._merge_elements(all_elements)
        
        # Post-process to improve classifications
        processed = self._post_process(merged)
        
        return processed
    
    def _merge_elements(self, elements: List[ExtractedElement]) -> List[ExtractedElement]:
        """Merge similar elements from different strategies"""
        merged = []
        used = set()
        
        for i, elem1 in enumerate(elements):
            if i in used:
                continue
            
            # Find similar elements
            similar = []
            for j, elem2 in enumerate(elements[i+1:], i+1):
                if j not in used and self._are_similar(elem1, elem2):
                    similar.append(elem2)
                    used.add(j)
            
            # Merge similar elements
            if similar:
                merged_elem = self._merge_similar(elem1, similar)
                merged.append(merged_elem)
            else:
                merged.append(elem1)
        
        return merged
    
    def _are_similar(self, elem1: ExtractedElement, elem2: ExtractedElement) -> bool:
        """Check if two elements are similar enough to merge"""
        if elem1.page != elem2.page:
            return False
        
        # Check geometric proximity
        if elem1.geometry.get("type") == elem2.geometry.get("type"):
            if elem1.geometry["type"] == "LineString":
                # Check if lines are close and parallel
                coords1 = elem1.geometry["coordinates"]
                coords2 = elem2.geometry["coordinates"]
                
                # Simple distance check (can be improved)
                dist = np.min([
                    np.linalg.norm(np.array(coords1[0]) - np.array(coords2[0])),
                    np.linalg.norm(np.array(coords1[1]) - np.array(coords2[1]))
                ])
                
                return dist < 10  # Within 10 pixels
        
        return False
    
    def _merge_similar(self, primary: ExtractedElement, similar: List[ExtractedElement]) -> ExtractedElement:
        """Merge similar elements into one with higher confidence"""
        # Average confidence scores
        all_confidences = [primary.confidence] + [e.confidence for e in similar]
        merged_confidence = np.mean(all_confidences)
        
        # Boost confidence if multiple strategies agree
        if len(set(e.method for e in [primary] + similar)) > 1:
            merged_confidence = min(merged_confidence * 1.2, 1.0)
        
        # Use the element with highest individual confidence as base
        best = primary
        for elem in similar:
            if elem.confidence > best.confidence:
                best = elem
        
        # Update confidence
        best.confidence = merged_confidence
        
        return best
    
    def _post_process(self, elements: List[ExtractedElement]) -> List[ExtractedElement]:
        """Post-process elements to improve classifications"""
        # Group elements by type
        walls = [e for e in elements if e.type == "wall"]
        rooms = [e for e in elements if e.type == "room"]
        annotations = [e for e in elements if e.type == "annotation"]
        
        # Use annotations to improve classifications
        for annotation in annotations:
            text = annotation.attributes.get("text", "").upper()
            
            # Find nearby elements
            for element in elements:
                if element.type != "annotation" and self._is_near(annotation, element):
                    # Update element type based on annotation
                    if "DOOR" in text:
                        element.type = "door"
                        element.confidence = min(element.confidence * 1.1, 1.0)
                    elif "WINDOW" in text:
                        element.type = "window"
                        element.confidence = min(element.confidence * 1.1, 1.0)
                    elif "ROOM" in text or any(c.isdigit() for c in text):
                        if element.type == "polygon":
                            element.type = "room"
                            element.attributes["label"] = text
        
        return elements
    
    def _is_near(self, elem1: ExtractedElement, elem2: ExtractedElement, threshold: float = 50) -> bool:
        """Check if two elements are near each other"""
        # Simple proximity check based on geometry
        # This is a simplified version - can be made more sophisticated
        if elem1.geometry["type"] == "Point":
            point = elem1.geometry["coordinates"]
            
            if elem2.geometry["type"] == "LineString":
                # Check distance from point to line
                line = elem2.geometry["coordinates"]
                # Simplified - just check endpoints
                dist = min(
                    np.linalg.norm(np.array(point) - np.array(line[0])),
                    np.linalg.norm(np.array(point) - np.array(line[1]))
                )
                return dist < threshold
            elif elem2.geometry["type"] == "Polygon":
                # Check if point is inside or near polygon
                # Simplified - just check bounding box
                coords = elem2.geometry["coordinates"][0]
                xs = [c[0] for c in coords]
                ys = [c[1] for c in coords]
                
                return (min(xs) - threshold <= point[0] <= max(xs) + threshold and
                        min(ys) - threshold <= point[1] <= max(ys) + threshold)
        
        return False


class MultiStrategyProcessor:
    """
    Main processor that orchestrates multiple extraction strategies
    """
    
    def __init__(self, coordinate_system: CoordinateSystem):
        self.coordinate_system = coordinate_system
        self.hybrid_strategy = HybridExtractionStrategy(coordinate_system)
        
        # Initialize component classifier if available
        if HAS_RECOGNIZERS:
            self.component_classifier = ComponentClassifier()
        else:
            self.component_classifier = None
            
        # Initialize topology analyzer if available
        if HAS_TOPOLOGY:
            self.topology_analyzer = TopologyAnalyzer()
        else:
            self.topology_analyzer = None
    
    def process(self, pdf_path: str) -> List[ArxObject]:
        """Process PDF using multiple strategies and convert to ArxObjects"""
        # Extract elements using hybrid strategy
        elements = self.hybrid_strategy.extract(pdf_path)
        
        # Convert to ArxObjects
        arxobjects = []
        for element in elements:
            arxobj = self._element_to_arxobject(element)
            if arxobj:
                arxobjects.append(arxobj)
        
        # Build relationships between objects
        self._build_relationships(arxobjects)
        
        # Analyze topology if available
        if self.topology_analyzer and HAS_TOPOLOGY:
            topology_relationships = self.topology_analyzer.analyze(arxobjects)
            
            # Update objects with topology relationships
            for obj in arxobjects:
                if obj.id in topology_relationships:
                    # Merge topology relationships with existing ones
                    existing_rels = {(r.type, r.target_id) for r in obj.relationships}
                    
                    for new_rel in topology_relationships[obj.id]:
                        if (new_rel.type, new_rel.target_id) not in existing_rels:
                            obj.relationships.append(new_rel)
                    
                    # Update relationship confidence
                    if len(obj.relationships) > 0:
                        obj.confidence.relationships = min(
                            0.5 + 0.1 * len(obj.relationships), 1.0
                        )
            
            # Get topology metrics for debugging
            metrics = self.topology_analyzer.get_topology_metrics()
            print(f"Topology Analysis: {metrics}")
        
        return arxobjects
    
    def _element_to_arxobject(self, element: ExtractedElement) -> Optional[ArxObject]:
        """Convert extracted element to ArxObject"""
        # Use component classifier if available for better recognition
        if self.component_classifier and HAS_RECOGNIZERS:
            # Extract features from element
            features = self.component_classifier.extract_features(
                element.geometry,
                [element.attributes.get("text", "")] if "text" in element.attributes else None
            )
            
            # Get context (simplified for now)
            context = {
                "has_arc": element.type == "door" and "arc" in element.attributes,
                "is_filled": element.attributes.get("fill") is not None,
            }
            
            # Classify using component recognizers
            obj_type, classifier_confidence = self.component_classifier.classify(features, context)
            
            # Boost element confidence if classifier agrees
            if classifier_confidence > 0.5:
                element.confidence = min(element.confidence * 1.1, 1.0)
        else:
            # Fallback to simple mapping
            type_map = {
                "wall": ArxObjectType.WALL,
                "door": ArxObjectType.DOOR,
                "window": ArxObjectType.WINDOW,
                "room": ArxObjectType.ROOM,
                "column": ArxObjectType.COLUMN,
                "stair": ArxObjectType.STAIRWELL,
                "opening": ArxObjectType.OPENING
            }
            
            obj_type = type_map.get(element.type, ArxObjectType.WALL)
        
        # Calculate real-world coordinates
        geom = element.geometry
        if geom["type"] == "LineString":
            coords = geom["coordinates"]
            p1 = self.coordinate_system.pdf_to_world_point(coords[0][0], coords[0][1])
            p2 = self.coordinate_system.pdf_to_world_point(coords[1][0], coords[1][1])
            
            # Calculate dimensions
            width_nm = abs(p2.x - p1.x)
            height_nm = abs(p2.y - p1.y)
            length_nm = int(np.sqrt(float(width_nm)**2 + float(height_nm)**2))
            
            # Standard wall thickness
            thickness_nm = 152_400_000  # 152.4mm in nanometers
            
            position = Point3D(
                x=(p1.x + p2.x) // 2,
                y=(p1.y + p2.y) // 2,
                z=0
            )
            
            dimensions = Dimensions(
                width=length_nm,
                height=thickness_nm,
                depth=3_000_000_000  # 3m standard height
            )
            
            bounds = BoundingBox(
                min_point=Point3D(x=min(p1.x, p2.x), y=min(p1.y, p2.y), z=0),
                max_point=Point3D(x=max(p1.x, p2.x), y=max(p1.y, p2.y), z=3_000_000_000)
            )
            
        elif geom["type"] == "Polygon":
            coords = geom["coordinates"][0]
            # Calculate bounding box
            xs = [self.coordinate_system.pdf_to_world_point(c[0], c[1]).x for c in coords]
            ys = [self.coordinate_system.pdf_to_world_point(c[0], c[1]).y for c in coords]
            
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            position = Point3D(
                x=(min_x + max_x) // 2,
                y=(min_y + max_y) // 2,
                z=0
            )
            
            dimensions = Dimensions(
                width=max_x - min_x,
                height=max_y - min_y,
                depth=3_000_000_000  # 3m standard height
            )
            
            bounds = BoundingBox(
                min_point=Point3D(x=min_x, y=min_y, z=0),
                max_point=Point3D(x=max_x, y=max_y, z=3_000_000_000)
            )
            
        else:
            # Point or other geometry
            coord = geom.get("coordinates", [0, 0])
            p = self.coordinate_system.pdf_to_world_point(coord[0], coord[1])
            
            position = p
            dimensions = Dimensions(width=1_000_000, height=1_000_000, depth=1_000_000)  # 1mm cube
            bounds = BoundingBox(
                min_point=p,
                max_point=Point3D(x=p.x + 1_000_000, y=p.y + 1_000_000, z=p.z + 1_000_000)
            )
        
        # Create confidence score
        confidence = ConfidenceScore(
            classification=element.confidence,
            position=element.confidence * 0.9,
            properties=element.confidence * 0.8,
            relationships=0.5,  # Will be updated when relationships are built
            overall=element.confidence
        )
        
        # Create metadata
        metadata = Metadata(
            source="pdf",
            source_detail=f"Page {element.page}, Method: {element.method.value}"
        )
        
        # Create ArxObject
        arxobj = ArxObject(
            id=f"{obj_type.value}_{element.page}_{hash(str(geom))}"[:20],
            type=obj_type,
            position=position,
            dimensions=dimensions,
            bounds=bounds,
            geometry=geom,
            data={
                "x_mm": position.x / 1_000_000,
                "y_mm": position.y / 1_000_000,
                "width_mm": dimensions.width / 1_000_000,
                "height_mm": dimensions.height / 1_000_000,
                "attributes": element.attributes
            },
            confidence=confidence,
            metadata=metadata,
            relationships=[]
        )
        
        return arxobj
    
    def _build_relationships(self, arxobjects: List[ArxObject]):
        """Build spatial relationships between ArxObjects"""
        # This is a simplified version - can be made more sophisticated
        for i, obj1 in enumerate(arxobjects):
            for obj2 in arxobjects[i+1:]:
                # Check if objects are adjacent
                if obj1.bounds and obj2.bounds:
                    if self._are_adjacent(obj1.bounds, obj2.bounds):
                        # Add adjacency relationship
                        from models.arxobject import Relationship, RelationshipType
                        
                        obj1.relationships.append(Relationship(
                            type=RelationshipType.ADJACENT_TO,
                            target_id=obj2.id,
                            confidence=0.8
                        ))
                        
                        obj2.relationships.append(Relationship(
                            type=RelationshipType.ADJACENT_TO,
                            target_id=obj1.id,
                            confidence=0.8
                        ))
                        
                        # Update relationship confidence
                        obj1.confidence.relationships = min(obj1.confidence.relationships + 0.1, 1.0)
                        obj2.confidence.relationships = min(obj2.confidence.relationships + 0.1, 1.0)
    
    def _are_adjacent(self, bounds1: BoundingBox, bounds2: BoundingBox, threshold: int = 10_000_000) -> bool:
        """Check if two bounding boxes are adjacent (within threshold nanometers)"""
        # Check if boxes are close but not overlapping
        x_gap = max(0, max(bounds1.min_point.x, bounds2.min_point.x) - 
                      min(bounds1.max_point.x, bounds2.max_point.x))
        y_gap = max(0, max(bounds1.min_point.y, bounds2.min_point.y) - 
                      min(bounds1.max_point.y, bounds2.max_point.y))
        
        return (x_gap < threshold or y_gap < threshold) and not bounds1.intersects(bounds2)