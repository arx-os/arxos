"""
Enhanced PDF extraction to capture all wall segments accurately
"""

from typing import List, Dict, Any, Optional, Tuple
import pdfplumber
import numpy as np
from models.arxobject import ArxObject, ArxObjectType, ConfidenceScore, Metadata

class EnhancedPDFExtractor:
    """
    Improved PDF extraction that captures all lines as potential walls
    """
    
    def __init__(self, 
                 min_length: float = 20.0,
                 thickness_threshold: float = 15.0):
        self.min_length = min_length
        self.thickness_threshold = thickness_threshold
        
    def extract_all_lines(self, page) -> List[Dict[str, Any]]:
        """
        Extract ALL lines from PDF page, not just rectangles
        """
        print(f"Enhanced extractor: Starting extraction from page")
        objects = []
        page_num = 0
        
        # Try to get lines - pdfplumber may not have all attributes by default
        try:
            # Method 1: Extract lines directly
            lines = getattr(page, 'lines', [])
            if lines:
                print(f"Extracting {len(lines)} lines from page")
                for line in lines:
                    obj = self._process_line(line, page_num)
                    if obj:
                        objects.append(obj)
            else:
                print("No lines attribute found")
        except Exception as e:
            print(f"Error accessing lines: {e}")
        
        try:
            # Method 2: Extract edges (more comprehensive)
            edges = getattr(page, 'edges', [])
            if edges:
                print(f"Extracting {len(edges)} edges from page")
                for edge in edges:
                    obj = self._process_edge(edge, page_num)
                    if obj:
                        objects.append(obj)
            else:
                print("No edges attribute found")
        except Exception as e:
            print(f"Error accessing edges: {e}")
        
        try:
            # Method 3: Extract rectangles and decompose to lines
            rects = getattr(page, 'rects', [])
            if rects:
                print(f"Extracting lines from {len(rects)} rectangles")
                for rect in rects:
                    rect_lines = self._decompose_rect_to_lines(rect, page_num)
                    objects.extend(rect_lines)
            else:
                print("No rects attribute found")
        except Exception as e:
            print(f"Error accessing rects: {e}")
        
        try:
            # Method 4: Extract curves that might be walls
            curves = getattr(page, 'curves', [])
            if curves:
                print(f"Extracting {len(curves)} curves from page")
                for curve in curves:
                    obj = self._process_curve(curve, page_num)
                    if obj:
                        objects.append(obj)
            else:
                print("No curves attribute found")
        except Exception as e:
            print(f"Error accessing curves: {e}")
        
        # Deduplicate similar lines
        objects = self._deduplicate_lines(objects)
        
        print(f"Total extracted: {len(objects)} potential wall segments")
        return objects
    
    def _process_line(self, line: Dict, page_num: int) -> Optional[Dict[str, Any]]:
        """Process a line object into a wall"""
        try:
            x0 = float(line.get('x0', 0))
            y0 = float(line.get('y0', 0)) 
            x1 = float(line.get('x1', x0))
            y1 = float(line.get('y1', y0))
            
            # Calculate length
            length = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            
            # Skip very short lines
            if length < self.min_length:
                return None
            
            # Determine if horizontal or vertical
            is_horizontal = abs(y1 - y0) < 5
            is_vertical = abs(x1 - x0) < 5
            
            # Higher confidence for orthogonal lines
            confidence = 0.8 if (is_horizontal or is_vertical) else 0.6
            
            return {
                'id': f"wall_{page_num}_{hash((x0, y0, x1, y1))}",
                'type': 'wall',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[x0, y0], [x1, y1]]
                },
                'confidence': {
                    'overall': confidence,
                    'classification': 0.85,
                    'position': 0.9,
                    'properties': 0.7
                },
                'data': {
                    'length': length,
                    'thickness': line.get('width', 1),
                    'is_horizontal': is_horizontal,
                    'is_vertical': is_vertical,
                    'source': 'line'
                },
                'metadata': {
                    'source': 'enhanced_pdf_extractor',
                    'extraction_method': 'direct_line'
                }
            }
        except Exception as e:
            print(f"Error processing line: {e}")
            return None
    
    def _process_edge(self, edge: Dict, page_num: int) -> Optional[Dict[str, Any]]:
        """Process an edge object into a wall"""
        try:
            # Edges have different structure than lines
            x0 = float(edge.get('x0', 0))
            y0 = float(edge.get('y0', 0))
            x1 = float(edge.get('x1', x0))
            y1 = float(edge.get('y1', y0))
            
            length = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            
            if length < self.min_length:
                return None
            
            return {
                'id': f"wall_{page_num}_{hash((x0, y0, x1, y1))}",
                'type': 'wall',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[x0, y0], [x1, y1]]
                },
                'confidence': {
                    'overall': 0.75,
                    'classification': 0.8,
                    'position': 0.85,
                    'properties': 0.65
                },
                'data': {
                    'length': length,
                    'thickness': edge.get('linewidth', 1),
                    'source': 'edge'
                },
                'metadata': {
                    'source': 'enhanced_pdf_extractor',
                    'extraction_method': 'edge'
                }
            }
        except Exception as e:
            print(f"Error processing edge: {e}")
            return None
    
    def _decompose_rect_to_lines(self, rect: Dict, page_num: int) -> List[Dict[str, Any]]:
        """Decompose a rectangle into 4 wall segments"""
        lines = []
        try:
            x0 = float(rect.get('x0', 0))
            y0 = float(rect.get('y0', 0))
            x1 = float(rect.get('x1', x0))
            y1 = float(rect.get('y1', y0))
            
            # Skip if too small
            width = abs(x1 - x0)
            height = abs(y1 - y0)
            
            if width < self.min_length and height < self.min_length:
                return []
            
            # Check if this is a filled rectangle (likely a wall)
            is_wall_rect = (width < self.thickness_threshold or 
                           height < self.thickness_threshold)
            
            if is_wall_rect:
                # Treat as a single thick wall
                if width < height:  # Vertical wall
                    center_x = (x0 + x1) / 2
                    return [{
                        'id': f"wall_{page_num}_{hash((center_x, y0, center_x, y1))}",
                        'type': 'wall',
                        'geometry': {
                            'type': 'LineString',
                            'coordinates': [[center_x, y0], [center_x, y1]]
                        },
                        'confidence': {
                            'overall': 0.85,
                            'classification': 0.9,
                            'position': 0.9,
                            'properties': 0.75
                        },
                        'data': {
                            'length': height,
                            'thickness': width,
                            'is_vertical': True,
                            'source': 'rect_wall'
                        },
                        'metadata': {
                            'source': 'enhanced_pdf_extractor',
                            'extraction_method': 'rect_as_wall'
                        }
                    }]
                else:  # Horizontal wall
                    center_y = (y0 + y1) / 2
                    return [{
                        'id': f"wall_{page_num}_{hash((x0, center_y, x1, center_y))}",
                        'type': 'wall',
                        'geometry': {
                            'type': 'LineString',
                            'coordinates': [[x0, center_y], [x1, center_y]]
                        },
                        'confidence': {
                            'overall': 0.85,
                            'classification': 0.9,
                            'position': 0.9,
                            'properties': 0.75
                        },
                        'data': {
                            'length': width,
                            'thickness': height,
                            'is_horizontal': True,
                            'source': 'rect_wall'
                        },
                        'metadata': {
                            'source': 'enhanced_pdf_extractor',
                            'extraction_method': 'rect_as_wall'
                        }
                    }]
            else:
                # Decompose to 4 lines (room boundary)
                # Top line
                if width >= self.min_length:
                    lines.append(self._create_wall_dict(x0, y0, x1, y0, page_num, 'rect_edge'))
                    # Bottom line
                    lines.append(self._create_wall_dict(x0, y1, x1, y1, page_num, 'rect_edge'))
                
                # Left line
                if height >= self.min_length:
                    lines.append(self._create_wall_dict(x0, y0, x0, y1, page_num, 'rect_edge'))
                    # Right line
                    lines.append(self._create_wall_dict(x1, y0, x1, y1, page_num, 'rect_edge'))
            
        except Exception as e:
            print(f"Error decomposing rect: {e}")
        
        return lines
    
    def _process_curve(self, curve: Dict, page_num: int) -> Optional[Dict[str, Any]]:
        """Process curves that might be walls"""
        try:
            points = curve.get('pts', [])
            if len(points) < 2:
                return None
            
            # For now, approximate curve as line from start to end
            # TODO: Could segment curve into multiple lines
            x0, y0 = points[0]
            x1, y1 = points[-1]
            
            length = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            
            if length < self.min_length:
                return None
            
            return {
                'id': f"wall_{page_num}_{hash((x0, y0, x1, y1))}",
                'type': 'wall',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[x0, y0], [x1, y1]]
                },
                'confidence': {
                    'overall': 0.6,
                    'classification': 0.7,
                    'position': 0.7,
                    'properties': 0.5
                },
                'data': {
                    'length': length,
                    'source': 'curve'
                },
                'metadata': {
                    'source': 'enhanced_pdf_extractor',
                    'extraction_method': 'curve_approximation'
                }
            }
        except Exception as e:
            print(f"Error processing curve: {e}")
            return None
    
    def _create_wall_dict(self, x0: float, y0: float, x1: float, y1: float, 
                         page_num: int, source: str) -> Dict[str, Any]:
        """Helper to create wall dictionary"""
        length = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
        is_horizontal = abs(y1 - y0) < 5
        is_vertical = abs(x1 - x0) < 5
        
        return {
            'id': f"wall_{page_num}_{hash((x0, y0, x1, y1))}",
            'type': 'wall',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[x0, y0], [x1, y1]]
            },
            'confidence': {
                'overall': 0.75,
                'classification': 0.85,
                'position': 0.85,
                'properties': 0.65
            },
            'data': {
                'length': length,
                'is_horizontal': is_horizontal,
                'is_vertical': is_vertical,
                'source': source
            },
            'metadata': {
                'source': 'enhanced_pdf_extractor',
                'extraction_method': source
            }
        }
    
    def _deduplicate_lines(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or very similar lines"""
        unique_lines = []
        seen_hashes = set()
        
        for line in lines:
            coords = line.get('geometry', {}).get('coordinates', [])
            if len(coords) >= 2:
                # Create hash of rounded coordinates
                x0, y0 = coords[0]
                x1, y1 = coords[-1]
                
                # Round to nearest unit to catch near-duplicates
                line_hash = (
                    round(x0, 1), round(y0, 1),
                    round(x1, 1), round(y1, 1)
                )
                
                # Also check reverse direction
                reverse_hash = (
                    round(x1, 1), round(y1, 1),
                    round(x0, 1), round(y0, 1)
                )
                
                if line_hash not in seen_hashes and reverse_hash not in seen_hashes:
                    unique_lines.append(line)
                    seen_hashes.add(line_hash)
        
        return unique_lines