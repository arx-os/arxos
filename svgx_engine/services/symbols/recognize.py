#!/usr/bin/env python3
"""
Bridge script to interface with the existing symbol recognition engine.
Accepts JSON input via stdin and returns JSON output via stdout.

This script bridges the Go symbol_recognizer.go with the Python SymbolRecognitionEngine,
providing PDF/image processing capabilities and JSON communication.
"""

import sys
import json
import base64
import time
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional

# PDF processing dependencies
try:
    import fitz  # PyMuPDF for PDF processing
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Image processing dependencies
try:
    from PIL import Image
    import numpy as np
    IMAGE_AVAILABLE = True
except ImportError:
    IMAGE_AVAILABLE = False

# OCR capabilities
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Computer vision for image processing
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Add the svgx_engine to path
sys.path.insert(0, '.')

from svgx_engine.services.symbols.symbol_recognition import SymbolRecognitionEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RecognitionBridge:
    """Bridge between Go services and Python symbol recognition engine."""
    
    def __init__(self):
        """Initialize the recognition bridge."""
        self.engine = SymbolRecognitionEngine()
        logger.info("RecognitionBridge initialized")
    
    def process_recognition_request(self) -> None:
        """Process a recognition request from Go via stdin."""
        try:
            # Read JSON request from stdin
            input_data = sys.stdin.read()
            request_data = json.loads(input_data)
            
            start_time = time.time()
            
            content_type = request_data.get('content_type', 'text')
            content = request_data.get('content', '')
            options = request_data.get('options', {})
            
            logger.info(f"Processing {content_type} content with options: {options}")
            
            # Process content based on type
            if content_type == 'pdf':
                symbols = self._recognize_pdf(content, options)
            elif content_type == 'image':
                symbols = self._recognize_image(content, options)
            elif content_type == 'svg':
                symbols = self.engine.recognize_symbols_in_content(content, 'svg')
            else:
                symbols = self.engine.recognize_symbols_in_content(content, 'text')
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Calculate statistics
            total_symbols = len(symbols)
            recognized_symbols = len([s for s in symbols if s.get('confidence', 0) > 0.5])
            avg_confidence = sum(s.get('confidence', 0) for s in symbols) / total_symbols if total_symbols > 0 else 0
            
            # Prepare response
            response = {
                'symbols': symbols,
                'errors': [],
                'stats': {
                    'total_symbols': total_symbols,
                    'recognized_symbols': recognized_symbols,
                    'average_confidence': avg_confidence,
                    'processing_time_ms': processing_time
                }
            }
            
            # Output JSON response
            print(json.dumps(response))
            logger.info(f"Processed {total_symbols} symbols in {processing_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error processing recognition request: {e}")
            error_response = {
                'symbols': [],
                'errors': [str(e)],
                'stats': {
                    'total_symbols': 0,
                    'recognized_symbols': 0,
                    'average_confidence': 0,
                    'processing_time_ms': 0
                }
            }
            print(json.dumps(error_response))
            sys.exit(1)
    
    def _recognize_pdf(self, content: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recognize symbols in PDF content."""
        if not PDF_AVAILABLE:
            logger.warning("PDF processing not available - PyMuPDF not installed")
            return self._fallback_text_recognition(content, options)
        
        try:
            # Decode base64 content if needed
            if isinstance(content, str):
                try:
                    pdf_bytes = base64.b64decode(content)
                except:
                    # If not base64, assume it's raw bytes as string
                    pdf_bytes = content.encode() if isinstance(content, str) else content
            else:
                pdf_bytes = content
            
            # Open PDF document
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            all_symbols = []
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text content
                text_content = page.get_text()
                if text_content.strip():
                    text_symbols = self.engine.recognize_symbols_in_content(text_content, 'text')
                    
                    # Add page context to symbols
                    for symbol in text_symbols:
                        symbol['page'] = page_num + 1
                        symbol['source'] = 'pdf_text'
                    
                    all_symbols.extend(text_symbols)
                
                # Extract vector graphics (if any)
                drawings = page.get_drawings()
                if drawings:
                    drawing_symbols = self._process_pdf_drawings(drawings, page_num)
                    all_symbols.extend(drawing_symbols)
                
                # Convert page to image for OCR if enabled
                if options.get('ocr_enabled', False) and OCR_AVAILABLE:
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    ocr_symbols = self._recognize_image_content(img_data, options)
                    
                    # Add page context
                    for symbol in ocr_symbols:
                        symbol['page'] = page_num + 1
                        symbol['source'] = 'pdf_ocr'
                    
                    all_symbols.extend(ocr_symbols)
            
            doc.close()
            
            # Apply fuzzy threshold filtering
            threshold = options.get('fuzzy_threshold', 0.6)
            filtered_symbols = [s for s in all_symbols if s.get('confidence', 0) >= threshold]
            
            logger.info(f"Extracted {len(filtered_symbols)} symbols from PDF ({len(doc)} pages)")
            return filtered_symbols
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return self._fallback_text_recognition(str(content), options)
    
    def _recognize_image(self, content: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recognize symbols in image content."""
        if not IMAGE_AVAILABLE:
            logger.warning("Image processing not available - PIL not installed")
            return []
        
        try:
            # Decode base64 content if needed
            if isinstance(content, str):
                try:
                    image_bytes = base64.b64decode(content)
                except:
                    logger.error("Failed to decode base64 image content")
                    return []
            else:
                image_bytes = content
            
            return self._recognize_image_content(image_bytes, options)
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return []
    
    def _recognize_image_content(self, image_bytes: bytes, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process image bytes for symbol recognition."""
        try:
            # Load image
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply perspective correction if enabled
            if options.get('perspective_correction', False) and CV2_AVAILABLE:
                image = self._apply_perspective_correction(image)
            
            # Apply edge detection if enabled
            if options.get('edge_detection', False) and CV2_AVAILABLE:
                edge_symbols = self._detect_edges(image)
            else:
                edge_symbols = []
            
            # Apply OCR if enabled
            ocr_symbols = []
            if options.get('ocr_enabled', False) and OCR_AVAILABLE:
                try:
                    # Extract text using OCR
                    ocr_text = pytesseract.image_to_string(image)
                    if ocr_text.strip():
                        ocr_symbols = self.engine.recognize_symbols_in_content(ocr_text, 'text')
                        
                        # Add OCR context
                        for symbol in ocr_symbols:
                            symbol['source'] = 'ocr'
                except Exception as e:
                    logger.warning(f"OCR failed: {e}")
            
            # Combine results
            all_symbols = edge_symbols + ocr_symbols
            
            # Apply fuzzy threshold filtering
            threshold = options.get('fuzzy_threshold', 0.5)
            filtered_symbols = [s for s in all_symbols if s.get('confidence', 0) >= threshold]
            
            logger.info(f"Extracted {len(filtered_symbols)} symbols from image")
            return filtered_symbols
            
        except Exception as e:
            logger.error(f"Error in image content recognition: {e}")
            return []
    
    def _apply_perspective_correction(self, image: Image.Image) -> Image.Image:
        """Apply perspective correction to straighten the image."""
        if not CV2_AVAILABLE:
            return image
        
        try:
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edged = cv2.Canny(blurred, 75, 200)
            
            # Find contours
            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
            
            # Look for a 4-point contour (document outline)
            for contour in contours:
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                
                if len(approx) == 4:
                    # Found document outline, apply perspective transform
                    pts = approx.reshape(4, 2)
                    
                    # Order points: top-left, top-right, bottom-right, bottom-left
                    rect = self._order_points(pts)
                    
                    # Calculate destination points
                    (tl, tr, br, bl) = rect
                    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                    maxWidth = max(int(widthA), int(widthB))
                    
                    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
                    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
                    maxHeight = max(int(heightA), int(heightB))
                    
                    dst = np.array([
                        [0, 0],
                        [maxWidth - 1, 0],
                        [maxWidth - 1, maxHeight - 1],
                        [0, maxHeight - 1]
                    ], dtype="float32")
                    
                    # Apply perspective transform
                    M = cv2.getPerspectiveTransform(rect.astype("float32"), dst)
                    warped = cv2.warpPerspective(cv_image, M, (maxWidth, maxHeight))
                    
                    # Convert back to PIL
                    return Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
            
            # If no document outline found, return original
            return image
            
        except Exception as e:
            logger.warning(f"Perspective correction failed: {e}")
            return image
    
    def _order_points(self, pts):
        """Order points in top-left, top-right, bottom-right, bottom-left order."""
        rect = np.zeros((4, 2), dtype="float32")
        
        # Sum and difference to find corners
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # top-left
        rect[2] = pts[np.argmax(s)]  # bottom-right
        
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  # top-right
        rect[3] = pts[np.argmax(diff)]  # bottom-left
        
        return rect
    
    def _detect_edges(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Detect edges in image that might represent symbols."""
        if not CV2_AVAILABLE:
            return []
        
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            edge_symbols = []
            
            for i, contour in enumerate(contours):
                # Filter small contours
                area = cv2.contourArea(contour)
                if area < 100:  # Minimum area threshold
                    continue
                
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Analyze shape characteristics
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                
                # Classify basic shapes
                shape_name = self._classify_shape(approx, area, perimeter)
                
                if shape_name:
                    # Try to match with known symbols
                    symbol_matches = self.engine.fuzzy_match_symbols(shape_name, 0.6)
                    
                    for match in symbol_matches:
                        edge_symbol = dict(match)
                        edge_symbol.update({
                            'source': 'edge_detection',
                            'position': {'x': float(x + w/2), 'y': float(y + h/2), 'z': 0.0},
                            'bounding_box': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                            'contour_area': float(area),
                            'contour_perimeter': float(perimeter)
                        })
                        edge_symbols.append(edge_symbol)
            
            return edge_symbols
            
        except Exception as e:
            logger.warning(f"Edge detection failed: {e}")
            return []
    
    def _classify_shape(self, approx, area: float, perimeter: float) -> Optional[str]:
        """Classify a shape based on its contour approximation."""
        vertices = len(approx)
        
        if vertices == 3:
            return "triangle"
        elif vertices == 4:
            # Check if it's a square or rectangle
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            if 0.95 <= aspect_ratio <= 1.05:
                return "square"
            else:
                return "rectangle"
        elif vertices > 8:
            # Likely a circle
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity > 0.7:
                return "circle"
        
        return None
    
    def _process_pdf_drawings(self, drawings: List, page_num: int) -> List[Dict[str, Any]]:
        """Process vector drawings extracted from PDF."""
        drawing_symbols = []
        
        for drawing in drawings:
            # Analyze drawing items
            for item in drawing.get('items', []):
                if item[0] == 'c':  # Circle/arc
                    symbol_data = {
                        'symbol_id': 'circle',
                        'confidence': 0.8,
                        'match_type': 'vector',
                        'symbol_data': self.engine.get_symbol_metadata('circle') or {},
                        'page': page_num + 1,
                        'source': 'pdf_vector',
                        'position': {'x': float(item[1].x), 'y': float(item[1].y), 'z': 0.0}
                    }
                    drawing_symbols.append(symbol_data)
                elif item[0] == 'l':  # Line
                    symbol_data = {
                        'symbol_id': 'line',
                        'confidence': 0.8,
                        'match_type': 'vector',
                        'symbol_data': self.engine.get_symbol_metadata('line') or {},
                        'page': page_num + 1,
                        'source': 'pdf_vector',
                        'position': {'x': float(item[1].x), 'y': float(item[1].y), 'z': 0.0}
                    }
                    drawing_symbols.append(symbol_data)
                elif item[0] == 're':  # Rectangle
                    symbol_data = {
                        'symbol_id': 'rectangle',
                        'confidence': 0.8,
                        'match_type': 'vector',
                        'symbol_data': self.engine.get_symbol_metadata('rectangle') or {},
                        'page': page_num + 1,
                        'source': 'pdf_vector',
                        'position': {'x': float(item[1].x), 'y': float(item[1].y), 'z': 0.0}
                    }
                    drawing_symbols.append(symbol_data)
        
        return drawing_symbols
    
    def _fallback_text_recognition(self, content: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to text-based recognition when PDF processing is unavailable."""
        logger.info("Using fallback text recognition")
        
        # Try to extract meaningful text patterns
        text_content = str(content)
        if len(text_content) > 1000:
            # If content is very long, it might be encoded binary data
            # Try to find readable patterns
            import re
            readable_parts = re.findall(r'[a-zA-Z\s]{10,}', text_content)
            if readable_parts:
                text_content = ' '.join(readable_parts[:10])  # Limit to first 10 matches
        
        symbols = self.engine.recognize_symbols_in_content(text_content, 'text')
        
        # Add fallback context
        for symbol in symbols:
            symbol['source'] = 'fallback_text'
        
        # Apply fuzzy threshold
        threshold = options.get('fuzzy_threshold', 0.6)
        return [s for s in symbols if s.get('confidence', 0) >= threshold]


def main():
    """Main entry point for the recognition bridge."""
    try:
        bridge = RecognitionBridge()
        bridge.process_recognition_request()
    except Exception as e:
        logger.error(f"Fatal error in recognition bridge: {e}")
        error_response = {
            'symbols': [],
            'errors': [f"Fatal error: {str(e)}"],
            'stats': {
                'total_symbols': 0,
                'recognized_symbols': 0,
                'average_confidence': 0,
                'processing_time_ms': 0
            }
        }
        print(json.dumps(error_response))
        sys.exit(1)


if __name__ == '__main__':
    main()