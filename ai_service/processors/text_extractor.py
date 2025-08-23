"""
Text extraction module for PDF room labels and annotations
"""

from typing import List, Dict, Any, Optional, Tuple
import re

class TextExtractor:
    """
    Extracts and processes text labels from PDFs
    Identifies room numbers, names, and other annotations
    """
    
    def __init__(self):
        # Common room number patterns
        self.room_patterns = [
            r'\b\d{3}[A-Z]?\b',  # 101, 102A
            r'\b[A-Z]\d{2,3}\b',  # B101, A12
            r'\bRM\s*\d+\b',      # RM 101
            r'\bROOM\s*\d+\b',    # ROOM 101
            r'\b\d{1,2}-\d{2,3}\b',  # 1-101, 12-345
        ]
        
        # Common room type keywords
        self.room_types = [
            'OFFICE', 'CONFERENCE', 'STORAGE', 'MECHANICAL',
            'ELECTRICAL', 'RESTROOM', 'CORRIDOR', 'LOBBY',
            'CLASSROOM', 'LAB', 'KITCHEN', 'BREAK', 'SERVER',
            'IT', 'JANITOR', 'ELEVATOR', 'STAIR', 'ENTRY'
        ]
        
    def extract_text_objects(self, page, page_num: int = 0) -> List[Dict[str, Any]]:
        """
        Extract text objects from a PDF page
        
        Args:
            page: PDF page object (pdfplumber or PyMuPDF)
            page_num: Page number for ID generation
            
        Returns:
            List of text ArxObjects
        """
        text_objects = []
        
        try:
            # Extract all text with positions
            if hasattr(page, 'extract_words'):  # pdfplumber
                words = page.extract_words(
                    x_tolerance=3,
                    y_tolerance=3,
                    keep_blank_chars=False
                )
                
                for word_data in words:
                    text = word_data.get('text', '').strip()
                    if not text:
                        continue
                    
                    # Check if this is a room label
                    is_room_label = self._is_room_label(text)
                    
                    # Get position
                    x0 = word_data.get('x0', 0)
                    y0 = word_data.get('top', word_data.get('y0', 0))
                    x1 = word_data.get('x1', x0 + 50)
                    y1 = word_data.get('bottom', word_data.get('y1', y0 + 10))
                    
                    # Create text object
                    text_obj = {
                        'id': f"text_{page_num}_{hash(text)}",
                        'type': 'room_label' if is_room_label else 'text',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [(x0 + x1) / 2, (y0 + y1) / 2]
                        },
                        'data': {
                            'text': text,
                            'font_size': word_data.get('height', 10),
                            'is_room_label': is_room_label,
                            'bbox': [x0, y0, x1, y1]
                        },
                        'confidence': {
                            'overall': 0.9 if is_room_label else 0.7,
                            'classification': 0.95,
                            'position': 0.9,
                            'properties': 0.8
                        },
                        'metadata': {
                            'source': 'text_extraction',
                            'page': page_num
                        }
                    }
                    
                    text_objects.append(text_obj)
                    
            elif hasattr(page, 'get_text'):  # PyMuPDF
                # Extract text blocks with position
                blocks = page.get_text("dict")
                
                for block in blocks.get("blocks", []):
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span.get("text", "").strip()
                                if not text:
                                    continue
                                
                                is_room_label = self._is_room_label(text)
                                
                                bbox = span.get("bbox", [0, 0, 100, 20])
                                
                                text_obj = {
                                    'id': f"text_{page_num}_{hash(text)}",
                                    'type': 'room_label' if is_room_label else 'text',
                                    'geometry': {
                                        'type': 'Point',
                                        'coordinates': [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
                                    },
                                    'data': {
                                        'text': text,
                                        'font_size': span.get("size", 10),
                                        'font': span.get("font", "unknown"),
                                        'is_room_label': is_room_label,
                                        'bbox': bbox
                                    },
                                    'confidence': {
                                        'overall': 0.9 if is_room_label else 0.7,
                                        'classification': 0.95,
                                        'position': 0.9,
                                        'properties': 0.8
                                    },
                                    'metadata': {
                                        'source': 'text_extraction',
                                        'page': page_num
                                    }
                                }
                                
                                text_objects.append(text_obj)
        
        except Exception as e:
            print(f"Text extraction error: {e}")
        
        return text_objects
    
    def _is_room_label(self, text: str) -> bool:
        """
        Check if text is likely a room label
        
        Args:
            text: Text string to check
            
        Returns:
            True if text matches room label patterns
        """
        text_upper = text.upper()
        
        # Check room number patterns
        for pattern in self.room_patterns:
            if re.match(pattern, text_upper):
                return True
        
        # Check if it contains room type keywords
        for room_type in self.room_types:
            if room_type in text_upper:
                return True
        
        # Check for simple numeric patterns (likely room numbers)
        if re.match(r'^\d{2,4}[A-Z]?$', text):
            return True
        
        return False
    
    def associate_labels_with_rooms(self, 
                                   rooms: List[Dict[str, Any]], 
                                   text_objects: List[Dict[str, Any]]) -> None:
        """
        Associate text labels with their corresponding rooms
        
        Args:
            rooms: List of room ArxObjects
            text_objects: List of text ArxObjects
        """
        room_labels = [t for t in text_objects if t.get('type') == 'room_label']
        
        for room in rooms:
            # Get room centroid
            room_data = room.get('data', {})
            centroid = room_data.get('centroid')
            
            if not centroid:
                # Calculate centroid from geometry
                geometry = room.get('geometry', {})
                if geometry.get('type') == 'Polygon':
                    coords = geometry.get('coordinates', [[]])[0]
                    if coords:
                        centroid = [
                            sum(p[0] for p in coords) / len(coords),
                            sum(p[1] for p in coords) / len(coords)
                        ]
                        room_data['centroid'] = centroid
            
            if not centroid:
                continue
            
            # Find closest room label
            min_distance = float('inf')
            best_label = None
            
            for label in room_labels:
                label_coords = label.get('geometry', {}).get('coordinates', [0, 0])
                
                # Calculate distance
                dist = ((centroid[0] - label_coords[0]) ** 2 + 
                       (centroid[1] - label_coords[1]) ** 2) ** 0.5
                
                if dist < min_distance:
                    min_distance = dist
                    best_label = label
            
            # Associate label if close enough (within room bounds ideally)
            if best_label and min_distance < 100:  # 100 units threshold
                room_data['label'] = best_label.get('data', {}).get('text', '')
                room_data['label_confidence'] = best_label.get('confidence', {}).get('overall', 0.5)
                
                # Mark label as used
                best_label['data']['associated_room'] = room.get('id')
    
    def extract_dimensions(self, text: str) -> Optional[Dict[str, float]]:
        """
        Extract dimension information from text
        
        Args:
            text: Text that might contain dimensions
            
        Returns:
            Dictionary with extracted dimensions or None
        """
        # Look for dimension patterns like "10'-6"" or "3.2m"
        patterns = [
            r"(\d+)'[-\s]*(\d+)\"?",  # Feet and inches
            r"(\d+\.?\d*)\s*m",        # Meters
            r"(\d+\.?\d*)\s*mm",       # Millimeters
            r"(\d+\.?\d*)\s*cm",       # Centimeters
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Convert to millimeters
                if "'" in pattern:  # Feet and inches
                    feet = float(match.group(1))
                    inches = float(match.group(2)) if len(match.groups()) > 1 else 0
                    mm = (feet * 12 + inches) * 25.4
                elif "m" in pattern and "mm" not in pattern:  # Meters
                    mm = float(match.group(1)) * 1000
                elif "cm" in pattern:  # Centimeters
                    mm = float(match.group(1)) * 10
                else:  # Millimeters
                    mm = float(match.group(1))
                
                return {'value': mm, 'original': text}
        
        return None