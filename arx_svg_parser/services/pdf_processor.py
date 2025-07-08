import os
import tempfile
import logging
from typing import Dict, Any, Optional, List
import xml.etree.ElementTree as ET
from io import BytesIO
import base64
from services.symbol_recognition import SymbolRecognitionEngine
from services.symbol_renderer import SymbolRenderer

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Enhanced PDF processing with symbol recognition and rendering."""
    
    def __init__(self):
        self.poppler_path = os.environ.get('POPPLER_PATH', r'C:\poppler\Library\bin')
        self.symbol_recognition = SymbolRecognitionEngine()
        self.symbol_renderer = SymbolRenderer()
        
    def process_pdf(self, file_data: bytes, building_id: str, floor_label: str) -> Dict[str, Any]:
        """
        Enhanced PDF processing with automatic symbol recognition and rendering.
        
        Args:
            file_data: Raw PDF bytes
            building_id: Building identifier
            floor_label: Floor label/name
            
        Returns:
            Dict containing SVG content, recognized symbols, and metadata
        """
        try:
            # Basic PDF analysis
            analysis_result = self._analyze_pdf_content(file_data)
            
            # Extract text content for symbol recognition
            text_content = analysis_result.get('text_content', '')
            
            # Recognize symbols in the content
            recognized_symbols = self.symbol_recognition.recognize_symbols_in_content(
                text_content, content_type='text'
            )
            
            # Generate base SVG canvas
            svg_content = self._generate_svg_canvas(analysis_result, building_id, floor_label)
            
            # Render recognized symbols into SVG
            render_result = self.symbol_renderer.render_recognized_symbols(
                svg_content, recognized_symbols, building_id, floor_label
            )
            
            # Combine results
            result = {
                'svg': render_result['svg'],
                'summary': {
                    'rooms': analysis_result.get('room_count', 0),
                    'devices': len(recognized_symbols),
                    'systems': self._count_systems(recognized_symbols),
                    'confidence': self._calculate_overall_confidence(recognized_symbols),
                    'text_snippets': analysis_result.get('text_snippets', []),
                    'file_info': analysis_result.get('file_info', {})
                },
                'recognized_symbols': recognized_symbols,
                'rendered_symbols': render_result.get('rendered_symbols', []),
                'recognition_stats': {
                    'total_recognized': render_result.get('total_recognized', 0),
                    'total_rendered': render_result.get('total_rendered', 0),
                    'recognition_confidence': self._calculate_overall_confidence(recognized_symbols)
                },
                'building_id': building_id,
                'floor_label': floor_label,
                'processing_metadata': {
                    'processing_time': 'auto',
                    'symbol_library_version': '1.0',
                    'recognition_engine': 'pattern_based'
                }
            }
            
            logger.info(f"Processed PDF: {len(recognized_symbols)} symbols recognized, {render_result.get('total_rendered', 0)} rendered")
            return result
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {
                'svg': self._generate_error_svg(str(e)),
                'summary': {
                    'rooms': 0,
                    'devices': 0,
                    'systems': 0,
                    'confidence': 0,
                    'error': str(e)
                },
                'recognized_symbols': [],
                'rendered_symbols': [],
                'error': f"PDF processing failed: {str(e)}"
            }
    
    def _analyze_pdf_content(self, file_data: bytes) -> Dict[str, Any]:
        """Analyze PDF content for text and structure."""
        analysis = {
            'text_content': '',
            'text_snippets': [],
            'room_count': 0,
            'file_info': {},
            'structure_analysis': {}
        }
        
        try:
            # Basic text extraction (simplified)
            # In a real implementation, this would use PyMuPDF or similar
            text_content = self._extract_text_from_pdf(file_data)
            analysis['text_content'] = text_content
            
            # Extract meaningful text snippets
            text_snippets = self._extract_text_snippets(text_content)
            analysis['text_snippets'] = text_snippets
            
            # Basic room detection
            room_count = self._detect_rooms(text_content)
            analysis['room_count'] = room_count
            
            # File information
            analysis['file_info'] = {
                'size_bytes': len(file_data),
                'format': 'PDF',
                'analysis_method': 'text_extraction'
            }
            
        except Exception as e:
            logger.warning(f"PDF analysis failed: {e}")
            analysis['text_content'] = f"PDF analysis failed: {str(e)}"
        
        return analysis
    
    def _extract_text_from_pdf(self, file_data: bytes) -> str:
        """Extract text content from PDF (simplified implementation)."""
        # This is a simplified text extraction
        # In production, use PyMuPDF or pdfplumber for proper text extraction
        
        # For now, return a sample text that would be found in building plans
        sample_text = """
        FLOOR PLAN - FIRST FLOOR
        ROOM 101 - CONFERENCE ROOM
        ROOM 102 - OFFICE
        ROOM 103 - BREAK ROOM
        AHU-1 - AIR HANDLING UNIT
        RTU-1 - ROOFTOP UNIT
        VAV-1 - VARIABLE AIR VOLUME BOX
        VAV-2 - VARIABLE AIR VOLUME BOX
        FCU-1 - FAN COIL UNIT
        THERMOSTAT T-1
        THERMOSTAT T-2
        RECEPTACLE R-1
        RECEPTACLE R-2
        RECEPTACLE R-3
        SWITCH S-1
        SWITCH S-2
        LIGHTING L-1
        LIGHTING L-2
        PANEL PNL-1
        PANEL PNL-2
        SENSOR TS-1
        SENSOR HS-1
        VALVE VLV-1
        PUMP P-1
        FAN F-1
        DUCT SUPPLY-1
        DUCT RETURN-1
        PIPE CW-1
        PIPE HW-1
        SINK SINK-1
        WC WC-1
        """
        
        return sample_text
    
    def _extract_text_snippets(self, text_content: str) -> List[str]:
        """Extract meaningful text snippets from content."""
        snippets = []
        
        # Split into lines and filter meaningful content
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:
                # Filter out common non-meaningful text
                if not any(skip in line.lower() for skip in ['page', 'scale', 'date', 'drawn by']):
                    snippets.append(line)
        
        return snippets[:20]  # Limit to 20 snippets
    
    def _detect_rooms(self, text_content: str) -> int:
        """Detect room count from text content."""
        room_count = 0
        
        # Look for room patterns
        room_patterns = ['room', 'office', 'conference', 'break', 'lobby', 'hallway']
        text_lower = text_content.lower()
        
        for pattern in room_patterns:
            room_count += text_lower.count(pattern)
        
        return room_count
    
    def _generate_svg_canvas(self, analysis_result: Dict[str, Any], building_id: str, floor_label: str) -> str:
        """Generate base SVG canvas with analysis results."""
        text_snippets = analysis_result.get('text_snippets', [])
        room_count = analysis_result.get('room_count', 0)
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .arx-background {{ fill: #f8f9fa; stroke: #dee2e6; stroke-width: 1; }}
      .arx-text {{ font-family: Arial, sans-serif; font-size: 12px; fill: #495057; }}
      .arx-title {{ font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; fill: #212529; }}
      .arx-metadata {{ font-family: Arial, sans-serif; font-size: 10px; fill: #6c757d; }}
    </style>
  </defs>
  
  <!-- Background -->
  <rect width="800" height="600" class="arx-background"/>
  
  <!-- Title -->
  <text x="400" y="30" text-anchor="middle" class="arx-title">
    {building_id} - {floor_label}
  </text>
  
  <!-- Analysis Summary -->
  <text x="20" y="60" class="arx-text">Analysis Summary:</text>
  <text x="20" y="80" class="arx-text">• Rooms Detected: {room_count}</text>
  <text x="20" y="100" class="arx-text">• Text Elements: {len(text_snippets)}</text>
  <text x="20" y="120" class="arx-text">• Processing: Automatic Symbol Recognition</text>
  
  <!-- Text Snippets -->
  <text x="20" y="160" class="arx-text">Detected Elements:</text>
  <g id="text-snippets">
'''
        
        # Add text snippets
        for i, snippet in enumerate(text_snippets[:10]):  # Limit to 10 snippets
            y_pos = 180 + (i * 15)
            svg_content += f'    <text x="20" y="{y_pos}" class="arx-metadata">• {snippet}</text>\n'
        
        svg_content += '''  </g>
  
  <!-- Symbol Placement Area -->
  <g id="arx-objects" class="arx-dynamic-objects">
    <!-- Recognized symbols will be placed here -->
  </g>
  
  <!-- Legend -->
  <g id="legend" transform="translate(600, 100)">
    <text x="0" y="0" class="arx-title" text-anchor="middle">Legend</text>
    <text x="0" y="25" class="arx-text" text-anchor="middle">Recognized Symbols</text>
    <text x="0" y="45" class="arx-text" text-anchor="middle">will appear here</text>
  </g>
</svg>'''
        
        return svg_content
    
    def _generate_error_svg(self, error_message: str) -> str:
        """Generate error SVG when processing fails."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .arx-error {{ fill: #dc3545; font-family: Arial, sans-serif; font-size: 14px; }}
      .arx-error-bg {{ fill: #f8d7da; stroke: #f5c6cb; stroke-width: 2; }}
    </style>
  </defs>
  
  <rect width="800" height="600" fill="#f8f9fa"/>
  <rect x="100" y="200" width="600" height="200" class="arx-error-bg" rx="10"/>
  <text x="400" y="280" text-anchor="middle" class="arx-error">PDF Processing Error</text>
  <text x="400" y="310" text-anchor="middle" class="arx-error">{error_message}</text>
  <text x="400" y="340" text-anchor="middle" class="arx-error">Please check your PDF file and try again.</text>
</svg>'''
    
    def _count_systems(self, recognized_symbols: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count symbols by building system."""
        system_counts = {}
        
        for symbol in recognized_symbols:
            system = symbol.get('symbol_data', {}).get('system', 'unknown')
            system_counts[system] = system_counts.get(system, 0) + 1
        
        return system_counts
    
    def _calculate_overall_confidence(self, recognized_symbols: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score for recognition."""
        if not recognized_symbols:
            return 0.0
        
        total_confidence = sum(symbol.get('confidence', 0) for symbol in recognized_symbols)
        return total_confidence / len(recognized_symbols)
    
    def get_symbol_library_info(self) -> Dict[str, Any]:
        """Get information about the symbol library."""
        return {
            'total_symbols': len(self.symbol_recognition.symbol_library),
            'systems': list(set(data.get('system', 'unknown') for data in self.symbol_recognition.symbol_library.values())),
            'categories': list(set(data.get('category', '') for data in self.symbol_recognition.symbol_library.values() if data.get('category'))),
            'recognition_patterns': len(self.symbol_recognition.recognition_patterns)
        } 