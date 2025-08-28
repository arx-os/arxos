#!/usr/bin/env python3
"""
PDF to Geometry Extraction Service for Arxos
Converts PDF floor plans into ArxObject geometry with confidence scoring.
"""

import cv2
import numpy as np
import pdf2image
import pytesseract
from PIL import Image
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import math
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractedGeometry:
    """Represents extracted geometry from PDF."""
    walls: List[Dict[str, Any]]
    doors: List[Dict[str, Any]]
    windows: List[Dict[str, Any]]
    rooms: List[Dict[str, Any]]
    measurements: Dict[str, float]
    confidence: float
    processing_time: float

@dataclass
class WallSegment:
    """Represents a wall segment with properties."""
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    thickness: float
    material: str
    confidence: float
    properties: Dict[str, Any]

class PDFToGeometryExtractor:
    """
    Main service for converting PDF floor plans to ArxObject geometry.
    """
    
    def __init__(self):
        """Initialize the PDF to geometry extractor."""
        self.min_wall_length = 50.0  # Minimum wall length in pixels
        self.min_confidence = 0.3    # Minimum confidence threshold
        self.edge_detection_threshold = 50
        self.line_detection_threshold = 100
        
        # Pre-trained model paths (will be loaded from Arxos model registry)
        self.model_paths = {
            'wall_detector': 'models/wall_detection.pth',
            'door_detector': 'models/door_detection.pth',
            'window_detector': 'models/window_detection.pth'
        }
        
        logger.info("PDF to Geometry Extractor initialized")
    
    def extract_from_pdf(self, pdf_path: str, reference_measurement: Optional[Dict[str, float]] = None) -> ExtractedGeometry:
        """
        Extract geometry from PDF floor plan.
        
        Args:
            pdf_path: Path to PDF file
            reference_measurement: Optional reference measurement for scaling
            
        Returns:
            ExtractedGeometry object with all extracted elements
        """
        start_time = time.time()
        logger.info(f"Starting geometry extraction from {pdf_path}")
        
        try:
            # Convert PDF to image
            images = self._pdf_to_images(pdf_path)
            if not images:
                raise ValueError("Failed to convert PDF to images")
            
            # Process first page (assume single floor plan)
            main_image = images[0]
            
            # Extract basic geometry
            walls = self._extract_walls(main_image)
            doors = self._extract_doors(main_image)
            windows = self._extract_windows(main_image)
            rooms = self._extract_rooms(main_image, walls)
            
            # Apply reference measurement scaling if provided
            if reference_measurement:
                scale_factor = self._calculate_scale_factor(reference_measurement, main_image)
                walls = self._scale_geometry(walls, scale_factor)
                doors = self._scale_geometry(doors, scale_factor)
                windows = self._scale_geometry(windows, scale_factor)
                rooms = self._scale_geometry(rooms, scale_factor)
            
            # Calculate overall confidence
            confidence = self._calculate_overall_confidence(walls, doors, windows, rooms)
            
            # Create measurements dictionary
            measurements = self._extract_measurements(main_image, reference_measurement)
            
            processing_time = time.time() - start_time
            
            result = ExtractedGeometry(
                walls=walls,
                doors=doors,
                windows=windows,
                rooms=rooms,
                measurements=measurements,
                confidence=confidence,
                processing_time=processing_time
            )
            
            logger.info(f"Geometry extraction completed in {processing_time:.2f}s with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Geometry extraction failed: {str(e)}")
            raise
    
    def _pdf_to_images(self, pdf_path: str) -> List[np.ndarray]:
        """Convert PDF to list of images."""
        try:
            # Convert PDF pages to images
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=300,  # High resolution for accurate extraction
                grayscale=False
            )
            
            # Convert PIL images to OpenCV format
            cv_images = []
            for img in images:
                cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                cv_images.append(cv_img)
            
            logger.info(f"Converted PDF to {len(cv_images)} images")
            return cv_images
            
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {str(e)}")
            return []
    
    def _extract_walls(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Extract wall segments from image using computer vision."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, self.edge_detection_threshold, self.edge_detection_threshold * 2)
            
            # Line detection using Hough Transform
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi/180,
                threshold=self.line_detection_threshold,
                minLineLength=self.min_wall_length,
                maxLineGap=20
            )
            
            walls = []
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # Calculate wall properties
                    length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                    angle = math.atan2(y2-y1, x2-x1) * 180 / np.pi
                    
                    # Filter walls by length and angle (horizontal/vertical)
                    if length > self.min_wall_length and (abs(angle) < 10 or abs(angle - 90) < 10):
                        wall = {
                            'start_point': (float(x1), float(y1)),
                            'end_point': (float(x2), float(y2)),
                            'length': length,
                            'angle': angle,
                            'thickness': 8.0,  # Default wall thickness
                            'material': 'concrete',  # Default material
                            'confidence': 0.8,
                            'properties': {
                                'type': 'wall',
                                'load_bearing': True,
                                'fire_rating': '2_hour'
                            }
                        }
                        walls.append(wall)
            
            logger.info(f"Extracted {len(walls)} wall segments")
            return walls
            
        except Exception as e:
            logger.error(f"Wall extraction failed: {str(e)}")
            return []
    
    def _extract_doors(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Extract door locations from image."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Template matching for door symbols (simplified)
            # In production, this would use trained ML models
            doors = []
            
            # Simple edge-based door detection
            edges = cv2.Canny(gray, 30, 100)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 5000:  # Reasonable door area range
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Doors typically have aspect ratio around 0.4-0.6
                    if 0.3 < aspect_ratio < 0.7:
                        door = {
                            'center_point': (float(x + w/2), float(y + h/2)),
                            'width': float(w),
                            'height': float(h),
                            'type': 'standard',
                            'confidence': 0.6,
                            'properties': {
                                'type': 'door',
                                'material': 'wood',
                                'fire_rating': '1_hour'
                            }
                        }
                        doors.append(door)
            
            logger.info(f"Extracted {len(doors)} doors")
            return doors
            
        except Exception as e:
            logger.error(f"Door extraction failed: {str(e)}")
            return []
    
    def _extract_windows(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Extract window locations from image."""
        try:
            # Similar to door extraction but with different parameters
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            windows = []
            
            # Simple window detection (will be enhanced with ML models)
            edges = cv2.Canny(gray, 20, 80)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 200 < area < 10000:  # Window area range
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Windows typically have aspect ratio around 1.0-2.0
                    if 0.8 < aspect_ratio < 2.5:
                        window = {
                            'center_point': (float(x + w/2), float(y + h/2)),
                            'width': float(w),
                            'height': float(h),
                            'type': 'standard',
                            'confidence': 0.5,
                            'properties': {
                                'type': 'window',
                                'material': 'glass',
                                'insulation': 'double_pane'
                            }
                        }
                        windows.append(window)
            
            logger.info(f"Extracted {len(windows)} windows")
            return windows
            
        except Exception as e:
            logger.error(f"Window extraction failed: {str(e)}")
            return []
    
    def _extract_rooms(self, image: np.ndarray, walls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract room boundaries from walls."""
        try:
            rooms = []
            
            # Simple room detection based on wall intersections
            # This is a simplified approach - production would use more sophisticated algorithms
            
            # Group walls by orientation
            horizontal_walls = [w for w in walls if abs(w['angle']) < 10]
            vertical_walls = [w for w in walls if abs(w['angle'] - 90) < 10]
            
            # Find potential room corners
            corners = self._find_room_corners(horizontal_walls, vertical_walls)
            
            # Create rooms from corner combinations
            for i, corner in enumerate(corners):
                if i + 3 < len(corners):
                    room = {
                        'corners': [corner, corners[i+1], corners[i+2], corners[i+3]],
                        'area': self._calculate_room_area([corner, corners[i+1], corners[i+2], corners[i+3]]),
                        'type': 'office',  # Default room type
                        'confidence': 0.4,
                        'properties': {
                            'type': 'room',
                            'occupancy': '1-2_persons',
                            'ventilation': 'mechanical'
                        }
                    }
                    rooms.append(room)
            
            logger.info(f"Extracted {len(rooms)} rooms")
            return rooms
            
        except Exception as e:
            logger.error(f"Room extraction failed: {str(e)}")
            return []
    
    def _find_room_corners(self, horizontal_walls: List[Dict], vertical_walls: List[Dict]) -> List[Tuple[float, float]]:
        """Find potential room corners from wall intersections."""
        corners = []
        
        # Find intersections between horizontal and vertical walls
        for h_wall in horizontal_walls:
            for v_wall in vertical_walls:
                intersection = self._find_wall_intersection(h_wall, v_wall)
                if intersection:
                    corners.append(intersection)
        
        return corners
    
    def _find_wall_intersection(self, wall1: Dict, wall2: Dict) -> Optional[Tuple[float, float]]:
        """Find intersection point between two walls."""
        try:
            # Simple intersection calculation
            # In production, use proper geometric intersection algorithms
            
            # For now, return midpoint as approximation
            x1, y1 = wall1['start_point']
            x2, y2 = wall1['end_point']
            x3, y3 = wall2['start_point']
            x4, y4 = wall2['end_point']
            
            # Calculate intersection (simplified)
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            return (mid_x, mid_y)
            
        except Exception:
            return None
    
    def _calculate_room_area(self, corners: List[Tuple[float, float]]) -> float:
        """Calculate room area from corner points."""
        try:
            if len(corners) < 3:
                return 0.0
            
            # Simple polygon area calculation
            area = 0.0
            for i in range(len(corners)):
                j = (i + 1) % len(corners)
                area += corners[i][0] * corners[j][1]
                area -= corners[j][0] * corners[i][1]
            
            return abs(area) / 2.0
            
        except Exception:
            return 0.0
    
    def _calculate_scale_factor(self, reference_measurement: Dict[str, float], image: np.ndarray) -> float:
        """Calculate scale factor from reference measurement."""
        try:
            # Extract reference dimension from image
            ref_pixels = reference_measurement.get('pixels', 100)
            ref_units = reference_measurement.get('units', 1000)  # mm
            
            scale_factor = ref_units / ref_pixels
            logger.info(f"Calculated scale factor: {scale_factor:.3f} mm/pixel")
            return scale_factor
            
        except Exception as e:
            logger.warning(f"Scale factor calculation failed: {str(e)}, using default")
            return 1.0
    
    def _scale_geometry(self, geometry_list: List[Dict], scale_factor: float) -> List[Dict]:
        """Scale geometry by scale factor."""
        scaled_geometry = []
        
        for item in geometry_list:
            scaled_item = item.copy()
            
            # Scale coordinates and dimensions
            if 'start_point' in scaled_item:
                x, y = scaled_item['start_point']
                scaled_item['start_point'] = (x * scale_factor, y * scale_factor)
            
            if 'end_point' in scaled_item:
                x, y = scaled_item['end_point']
                scaled_item['end_point'] = (x * scale_factor, y * scale_factor)
            
            if 'center_point' in scaled_item:
                x, y = scaled_item['center_point']
                scaled_item['center_point'] = (x * scale_factor, y * scale_factor)
            
            if 'width' in scaled_item:
                scaled_item['width'] *= scale_factor
            
            if 'height' in scaled_item:
                scaled_item['height'] *= scale_factor
            
            if 'length' in scaled_item:
                scaled_item['length'] *= scale_factor
            
            if 'thickness' in scaled_item:
                scaled_item['thickness'] *= scale_factor
            
            scaled_geometry.append(scaled_item)
        
        return scaled_geometry
    
    def _extract_measurements(self, image: np.ndarray, reference_measurement: Optional[Dict[str, float]]) -> Dict[str, float]:
        """Extract key measurements from image."""
        measurements = {}
        
        try:
            # Extract text using OCR for measurements
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray)
            
            # Look for measurement patterns (e.g., "10'", "3.5m", "1200mm")
            import re
            measurement_patterns = [
                r'(\d+(?:\.\d+)?)\s*[\'"]',  # Feet/inches
                r'(\d+(?:\.\d+)?)\s*m',      # Meters
                r'(\d+(?:\.\d+)?)\s*mm',     # Millimeters
            ]
            
            for pattern in measurement_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    measurements[f'ocr_{pattern}'] = float(matches[0])
            
            # Add reference measurement if provided
            if reference_measurement:
                measurements.update(reference_measurement)
            
        except Exception as e:
            logger.warning(f"Measurement extraction failed: {str(e)}")
        
        return measurements
    
    def _calculate_overall_confidence(self, walls: List, doors: List, windows: List, rooms: List) -> float:
        """Calculate overall confidence score for extraction."""
        try:
            # Weighted confidence calculation
            total_elements = len(walls) + len(doors) + len(windows) + len(rooms)
            if total_elements == 0:
                return 0.0
            
            # Calculate weighted average confidence
            wall_conf = sum(w.get('confidence', 0.5) for w in walls) / max(len(walls), 1)
            door_conf = sum(d.get('confidence', 0.5) for d in doors) / max(len(doors), 1)
            window_conf = sum(w.get('confidence', 0.5) for w in windows) / max(len(windows), 1)
            room_conf = sum(r.get('confidence', 0.5) for r in rooms) / max(len(rooms), 1)
            
            # Weight by element importance
            overall_confidence = (
                wall_conf * 0.4 +      # Walls are most important
                room_conf * 0.3 +      # Rooms second
                door_conf * 0.2 +      # Doors third
                window_conf * 0.1      # Windows least important
            )
            
            return min(overall_confidence, 1.0)
            
        except Exception:
            return 0.5

# Example usage
if __name__ == "__main__":
    extractor = PDFToGeometryExtractor()
    
    # Test with sample PDF
    try:
        result = extractor.extract_from_pdf("sample_floorplan.pdf")
        print(f"Extraction completed with confidence: {result.confidence:.2f}")
        print(f"Found {len(result.walls)} walls, {len(result.doors)} doors, {len(result.windows)} windows, {len(result.rooms)} rooms")
        
        # Save results as JSON
        with open("extraction_results.json", "w") as f:
            json.dump({
                'walls': result.walls,
                'doors': result.doors,
                'windows': result.windows,
                'rooms': result.rooms,
                'measurements': result.measurements,
                'confidence': result.confidence,
                'processing_time': result.processing_time
            }, f, indent=2)
            
    except Exception as e:
        print(f"Extraction failed: {str(e)}")
