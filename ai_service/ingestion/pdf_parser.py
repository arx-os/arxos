"""
PDF Parser - Extract building plan data from PDF files
Converts PDF building plans into structured data for ASCII generation
"""

import logging
import fitz  # PyMuPDF
import cv2
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import json
import os
from .base_parser import BaseParser, BuildingElement, BuildingPlan

logger = logging.getLogger(__name__)

class PDFParser(BaseParser):
    """
    Parse PDF building plans to extract building elements and structure
    Focuses on common architectural elements and room layouts
    """
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['pdf']
        self.parser_name = "PDFParser"
        
        # Common architectural element patterns
        self.element_patterns = {
            'wall': {
                'keywords': ['wall', 'partition', 'exterior', 'interior'],
                'min_width': 0.1,  # Minimum wall thickness
                'min_height': 0.5   # Minimum wall height
            },
            'door': {
                'keywords': ['door', 'entrance', 'exit', 'opening'],
                'min_width': 0.6,   # Minimum door width
                'max_width': 1.2    # Maximum door width
            },
            'window': {
                'keywords': ['window', 'glazing', 'opening'],
                'min_width': 0.5,   # Minimum window width
                'min_height': 0.8   # Minimum window height
            },
            'room': {
                'keywords': ['room', 'space', 'area', 'chamber'],
                'min_area': 5.0     # Minimum room area in sq meters
            }
        }
    
    async def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the given PDF file"""
        try:
            # Check file extension
            if not file_path.lower().endswith('.pdf'):
                return False
            
            # Check if file exists and is readable
            if not os.path.exists(file_path) or not os.access(file_path, os.R_OK):
                return False
            
            # Try to open the PDF to verify it's valid
            try:
                doc = fitz.open(file_path)
                doc.close()
                return True
            except Exception:
                return False
                
        except Exception as e:
            logger.error(f"Error checking if PDF can be parsed: {e}")
            return False
    
    async def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate that the file is a valid PDF building plan"""
        try:
            if not await self.can_parse(file_path):
                return {
                    'is_valid': False,
                    'errors': [f"File {file_path} is not a valid PDF"],
                    'warnings': [],
                    'file_size': 0,
                    'page_count': 0
                }
            
            # Get file info
            file_info = await self.get_file_info(file_path)
            
            # Basic validation
            is_valid = True
            errors = []
            warnings = []
            
            if file_info['page_count'] == 0:
                is_valid = False
                errors.append("PDF has no pages")
            
            if file_info['file_size'] < 1000:  # Less than 1KB
                warnings.append("PDF file is very small, may not contain building plans")
            
            return {
                'is_valid': is_valid,
                'errors': errors,
                'warnings': warnings,
                'file_size': file_info['file_size'],
                'page_count': file_info['page_count']
            }
            
        except Exception as e:
            logger.error(f"Error validating PDF file: {e}")
            return {
                'is_valid': False,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'file_size': 0,
                'page_count': 0
            }
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic information about the PDF file without parsing"""
        try:
            doc = fitz.open(file_path)
            
            file_info = {
                'file_size': os.path.getsize(file_path),
                'page_count': len(doc),
                'dimensions': [],
                'metadata': doc.metadata
            }
            
            # Get dimensions of first few pages
            for i in range(min(3, len(doc))):
                page = doc[i]
                rect = page.rect
                file_info['dimensions'].append({
                    'page': i,
                    'width': rect.width,
                    'height': rect.height
                })
            
            doc.close()
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting PDF file info: {e}")
            return {
                'error': f"Failed to get file info: {str(e)}",
                'file_size': 0,
                'page_count': 0
            }
    
    async def estimate_processing_time(self, file_path: str) -> float:
        """Estimate processing time based on file size and page count"""
        try:
            file_info = await self.get_file_info(file_path)
            page_count = file_info.get('page_count', 1)
            file_size_mb = file_info.get('file_size', 0) / (1024 * 1024)
            
            # Base time: 2 seconds per page + 1 second per MB
            estimated_time = (page_count * 2.0) + (file_size_mb * 1.0)
            
            # Cap at reasonable limits
            return min(max(estimated_time, 1.0), 30.0)
            
        except Exception as e:
            logger.warning(f"Could not estimate processing time: {e}")
            return 5.0  # Default estimate
    
    async def get_memory_requirements(self, file_path: str) -> Dict[str, float]:
        """Estimate memory requirements for PDF processing"""
        try:
            file_info = await self.get_file_info(file_path)
            page_count = file_info.get('page_count', 1)
            file_size_mb = file_info.get('file_size', 0) / (1024 * 1024)
            
            # Memory scales with page count and file size
            min_memory = 50.0  # Base memory
            peak_memory = min_memory + (page_count * 10.0) + (file_size_mb * 2.0)
            recommended = min_memory + (page_count * 5.0) + (file_size_mb * 1.0)
            
            return {
                'min_memory': min_memory,
                'peak_memory': min(peak_memory, 500.0),  # Cap at 500MB
                'recommended': min(recommended, 200.0)     # Cap at 200MB
            }
            
        except Exception as e:
            logger.warning(f"Could not estimate memory requirements: {e}")
            return {
                'min_memory': 50.0,
                'peak_memory': 200.0,
                'recommended': 100.0
            }
    
    async def parse_building_plan(self, file_path: str) -> BuildingPlan:
        """
        Parse a PDF building plan and extract building structure
        
        Args:
            file_path: Path to PDF building plan
            
        Returns:
            BuildingPlan with extracted building data
        """
        try:
            # Open PDF document
            doc = fitz.open(file_path)
            
            # Extract basic document info
            building_name = self._extract_building_name(doc)
            dimensions = self._get_document_dimensions(doc)
            scale_factor = self._estimate_scale_factor(doc)
            
            # Extract building elements from all pages
            all_elements = []
            floors = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text and graphics
                text_blocks = page.get_text("dict")
                graphics = page.get_drawings()
                
                # Extract elements from this page
                page_elements = self._extract_page_elements(
                    text_blocks, graphics, page_num, dimensions, scale_factor, file_path
                )
                all_elements.extend(page_elements)
                
                # Identify floor from page content
                floor_info = self._identify_floor(text_blocks)
                if floor_info:
                    floors.append(floor_info)
            
            # Extract room information
            rooms = self._extract_rooms(all_elements, dimensions)
            
            # Create building plan
            building_plan = BuildingPlan(
                building_name=building_name,
                floors=floors,
                rooms=rooms,
                elements=all_elements,
                dimensions=dimensions,
                scale_factor=scale_factor,
                metadata={
                    'pdf_path': file_path,
                    'page_count': len(doc),
                    'extraction_timestamp': 'now'
                },
                source_format='pdf'
            )
            
            doc.close()
            return building_plan
            
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            raise
    
    def _extract_building_name(self, doc: fitz.Document) -> str:
        """Extract building name from PDF metadata or first page"""
        try:
            # Try to get from PDF metadata
            metadata = doc.metadata
            if metadata.get('title'):
                return metadata['title']
            
            # Try to get from first page text
            first_page = doc[0]
            text = first_page.get_text()
            
            # Look for common building name patterns
            lines = text.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line and len(line) < 100:  # Reasonable length for building name
                    # Check if it looks like a building name
                    if any(keyword in line.lower() for keyword in ['building', 'center', 'complex', 'tower', 'plaza']):
                        return line
            
            # Default name
            return "Unnamed Building"
            
        except Exception as e:
            logger.warning(f"Could not extract building name: {e}")
            return "Unnamed Building"
    
    def _get_document_dimensions(self, doc: fitz.Document) -> Tuple[float, float]:
        """Get document dimensions in points"""
        try:
            first_page = doc[0]
            rect = first_page.rect
            return (rect.width, rect.height)
        except Exception as e:
            logger.warning(f"Could not get document dimensions: {e}")
            return (595.0, 842.0)  # Default A4 size
    
    def _estimate_scale_factor(self, doc: fitz.Document) -> float:
        """Estimate scale factor from PDF content"""
        try:
            # This is a simplified scale estimation
            # In a real implementation, you'd look for scale bars or known dimensions
            
            # Default scale: 1 PDF point = 1 meter
            # This can be adjusted based on building type and PDF content
            return 1.0
            
        except Exception as e:
            logger.warning(f"Could not estimate scale factor: {e}")
            return 1.0
    
    def _extract_page_elements(self, 
                              text_blocks: Dict[str, Any], 
                              graphics: List[Dict[str, Any]], 
                              page_num: int,
                              dimensions: Tuple[float, float],
                              scale_factor: float,
                              file_path: str) -> List[BuildingElement]:
        """Extract building elements from a single page"""
        elements = []
        
        try:
            # Extract text-based elements
            text_elements = self._extract_text_elements(text_blocks, page_num, scale_factor, file_path)
            elements.extend(text_elements)
            
            # Extract graphic-based elements
            graphic_elements = self._extract_graphic_elements(graphics, page_num, scale_factor, file_path)
            elements.extend(graphic_elements)
            
            # Extract room boundaries from graphics
            room_elements = self._extract_room_boundaries(graphics, page_num, scale_factor, file_path)
            elements.extend(room_elements)
            
        except Exception as e:
            logger.error(f"Error extracting page elements: {e}")
        
        return elements
    
    def _extract_text_elements(self, 
                              text_blocks: Dict[str, Any], 
                              page_num: int,
                              scale_factor: float,
                              file_path: str) -> List[BuildingElement]:
        """Extract building elements from text blocks"""
        elements = []
        
        try:
            for block in text_blocks.get('blocks', []):
                if 'lines' in block:
                    for line in block['lines']:
                        for span in line.get('spans', []):
                            text = span.get('text', '').lower()
                            bbox = span.get('bbox', [0, 0, 0, 0])
                            
                            # Check if text describes a building element
                            element_type = self._identify_element_type(text)
                            if element_type:
                                # Convert bbox to coordinates
                                x1, y1, x2, y2 = bbox
                                coordinates = (x1 * scale_factor, y1 * scale_factor, 
                                            x2 * scale_factor, y2 * scale_factor)
                                
                                element = BuildingElement(
                                    element_type=element_type,
                                    coordinates=coordinates,
                                    properties={'text': span.get('text', '')},
                                    confidence=0.8,
                                    source_page=page_num,
                                    source_file=file_path
                                )
                                elements.append(element)
            
        except Exception as e:
            logger.error(f"Error extracting text elements: {e}")
        
        return elements
    
    def _extract_graphic_elements(self, 
                                 graphics: List[Dict[str, Any]], 
                                 page_num: int,
                                 scale_factor: float,
                                 file_path: str) -> List[BuildingElement]:
        """Extract building elements from graphics"""
        elements = []
        
        try:
            for graphic in graphics:
                # Look for walls (thick lines)
                if graphic.get('type') == 'l':  # Line
                    stroke_width = graphic.get('width', 0)
                    if stroke_width > 2.0:  # Thick line likely a wall
                        bbox = graphic.get('bbox', [0, 0, 0, 0])
                        coordinates = tuple(coord * scale_factor for coord in bbox)
                        
                        element = BuildingElement(
                            element_type='wall',
                            coordinates=coordinates,
                            properties={'stroke_width': stroke_width},
                            confidence=0.7,
                            source_page=page_num,
                            source_file=file_path
                        )
                        elements.append(element)
                
                # Look for doors (rectangles with specific dimensions)
                elif graphic.get('type') == 're':  # Rectangle
                    bbox = graphic.get('bbox', [0, 0, 0, 0])
                    width = abs(bbox[2] - bbox[0])
                    height = abs(bbox[3] - bbox[1])
                    
                    # Check if dimensions match typical door
                    if 0.6 <= width <= 1.2 and 1.8 <= height <= 2.4:
                        coordinates = tuple(coord * scale_factor for coord in bbox)
                        
                        element = BuildingElement(
                            element_type='door',
                            coordinates=coordinates,
                            properties={'width': width, 'height': height},
                            confidence=0.8,
                            source_page=page_num,
                            source_file=file_path
                        )
                        elements.append(element)
            
        except Exception as e:
            logger.error(f"Error extracting graphic elements: {e}")
        
        return elements
    
    def _extract_room_boundaries(self, 
                                graphics: List[Dict[str, Any]], 
                                page_num: int,
                                scale_factor: float,
                                file_path: str) -> List[BuildingElement]:
        """Extract room boundaries from graphics"""
        elements = []
        
        try:
            # Look for closed paths that could represent rooms
            for graphic in graphics:
                if graphic.get('type') == 'f':  # Filled path
                    bbox = graphic.get('bbox', [0, 0, 0, 0])
                    width = abs(bbox[2] - bbox[0])
                    height = abs(bbox[3] - bbox[1])
                    area = width * height
                    
                    # Check if this could be a room (reasonable size)
                    if area > 5.0:  # Minimum room area
                        coordinates = tuple(coord * scale_factor for coord in bbox)
                        
                        element = BuildingElement(
                            element_type='room',
                            coordinates=coordinates,
                            properties={'area': area, 'width': width, 'height': height},
                            confidence=0.6,
                            source_page=page_num,
                            source_file=file_path
                        )
                        elements.append(element)
            
        except Exception as e:
            logger.error(f"Error extracting room boundaries: {e}")
        
        return elements
    
    def _identify_element_type(self, text: str) -> Optional[str]:
        """Identify building element type from text"""
        for element_type, pattern in self.element_patterns.items():
            if any(keyword in text for keyword in pattern['keywords']):
                return element_type
        
        return None
    
    def _identify_floor(self, text_blocks: Dict[str, Any]) -> Optional[str]:
        """Identify floor information from text"""
        try:
            for block in text_blocks.get('blocks', []):
                if 'lines' in block:
                    for line in block['lines']:
                        for span in line.get('spans', []):
                            text = span.get('text', '').lower()
                            
                            # Look for floor indicators
                            if any(keyword in text for keyword in ['floor', 'level', 'story', 'basement']):
                                return span.get('text', '').strip()
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not identify floor: {e}")
            return None
    
    def _extract_rooms(self, 
                      elements: List[BuildingElement], 
                      dimensions: Tuple[float, float]) -> List[Dict[str, Any]]:
        """Extract room information from building elements"""
        rooms = []
        
        try:
            # Group elements by proximity to identify rooms
            room_elements = [e for e in elements if e.element_type == 'room']
            
            for room_element in room_elements:
                x1, y1, x2, y2 = room_element.coordinates
                
                room_info = {
                    'id': f"room_{len(rooms)}",
                    'type': 'general',
                    'coordinates': room_element.coordinates,
                    'area': room_element.properties.get('area', 0),
                    'elements': []
                }
                
                # Find elements that are inside this room
                for element in elements:
                    if element.element_type != 'room':
                        ex1, ey1, ex2, ey2 = element.coordinates
                        
                        # Check if element center is inside room
                        element_center_x = (ex1 + ex2) / 2
                        element_center_y = (ey1 + ey2) / 2
                        
                        if (x1 <= element_center_x <= x2 and 
                            y1 <= element_center_y <= y2):
                            room_info['elements'].append({
                                'type': element.element_type,
                                'coordinates': element.coordinates,
                                'properties': element.properties
                            })
                
                rooms.append(room_info)
            
        except Exception as e:
            logger.error(f"Error extracting rooms: {e}")
        
        return rooms
