#!/usr/bin/env python3
"""
Simple PDF extraction using only pdftotext and basic parsing
No external dependencies required
"""

import sys
import json
import subprocess
import re

def extract_from_pdf(pdf_path):
    """Extract text and approximate positions using pdftotext"""
    
    # Get text with bounding boxes
    cmd = ['pdftotext', '-bbox', pdf_path, '-']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    texts = []
    lines = result.stdout.split('\n')
    
    for line in lines:
        # Parse word elements with bbox
        if '<word' in line:
            match = re.search(r'xMin="([^"]+)" yMin="([^"]+)" xMax="([^"]+)" yMax="([^"]+)">([^<]+)</word>', line)
            if match:
                x1, y1, x2, y2, text = match.groups()
                texts.append({
                    'text': text.strip(),
                    'x': float(x1),
                    'y': float(y1),
                    'width': float(x2) - float(x1),
                    'height': float(y2) - float(y1)
                })
    
    # Extract room numbers and network rooms
    rooms = []
    for t in texts:
        text = t['text']
        # Check for room numbers (3 digits) or IDF/MDF rooms
        if re.match(r'^\d{3}[a-z]?$', text) or 'IDF' in text or 'MDF' in text:
            rooms.append(t)
    
    # Create approximate room boundaries based on text positions
    # Group nearby room numbers to estimate room areas
    room_rects = []
    for room in rooms:
        # Estimate room size around the label
        room_rects.append({
            'x': room['x'] - 50,
            'y': room['y'] - 30,
            'width': 100,
            'height': 60,
            'label': room['text']
        })
    
    # Create walls based on typical floor plan structure
    # This is a simplified approach - in production you'd use proper line detection
    horizontal_lines = []
    vertical_lines = []
    
    # Add perimeter walls (assuming typical page dimensions)
    page_width = 792  # Standard US Letter in points
    page_height = 612
    
    # Top and bottom walls
    horizontal_lines.append([50, page_width-50, 50])  # Top
    horizontal_lines.append([50, page_width-50, page_height-50])  # Bottom
    
    # Left and right walls
    vertical_lines.append([50, 50, page_height-50])  # Left
    vertical_lines.append([page_width-50, 50, page_height-50])  # Right
    
    # Add some interior walls based on typical patterns
    # Corridors typically run through the middle
    horizontal_lines.append([50, page_width-50, page_height/2])  # Main corridor
    
    # Vertical divisions for rooms
    for i in range(1, 5):
        x = 50 + (page_width-100) * i / 5
        vertical_lines.append([x, 50, page_height-50])
    
    result = {
        'texts': texts,
        'geometry': {
            'horizontal_lines': horizontal_lines,
            'vertical_lines': vertical_lines,
            'rectangles': room_rects,
            'image_width': page_width,
            'image_height': page_height
        }
    }
    
    return result

def main(pdf_path):
    """Main extraction"""
    try:
        result = extract_from_pdf(pdf_path)
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            'error': str(e),
            'texts': [],
            'geometry': {
                'horizontal_lines': [],
                'vertical_lines': [],
                'rectangles': [],
                'image_width': 792,
                'image_height': 612
            }
        }
        print(json.dumps(error_result))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('{"error": "Usage: python3 extract_simple.py <pdf_path>"}')
        sys.exit(1)
    
    main(sys.argv[1])