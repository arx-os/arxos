#!/usr/bin/env python3
"""
Analyze floor plan by actually processing the image pixels
No hardcoded positions - everything detected from the actual image
"""

import sys
import json
import subprocess
import os
from PIL import Image

def extract_image_from_pdf(pdf_path):
    """Extract the floor plan image from PDF"""
    temp_prefix = '/tmp/floorplan'
    subprocess.run(['pdfimages', '-png', pdf_path, temp_prefix], capture_output=True)
    
    # Find extracted images
    for i in range(10):
        path = f'{temp_prefix}-{i:03d}.png'
        if os.path.exists(path):
            return path
    
    raise Exception("No image found in PDF")

def analyze_pixels(image_path):
    """Analyze the actual pixels to find walls and rooms"""
    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    pixels = img.load()
    
    print(f"Analyzing {width}x{height} image...", file=sys.stderr)
    
    # Detect black lines (walls)
    walls = []
    
    # Sample the image to find horizontal lines
    for y in range(0, height, 5):  # Sample every 5 pixels
        black_segments = []
        in_black = False
        start_x = 0
        
        for x in range(width):
            r, g, b = pixels[x, y]
            is_black = (r < 50 and g < 50 and b < 50)
            
            if is_black and not in_black:
                start_x = x
                in_black = True
            elif not is_black and in_black:
                if x - start_x > 10:  # Minimum line length
                    black_segments.append((start_x, x, y))
                in_black = False
        
        # Add long segments as walls
        for seg in black_segments:
            if seg[1] - seg[0] > 50:  # Significant wall length
                walls.append({
                    'type': 'horizontal',
                    'x1': seg[0],
                    'y1': seg[2],
                    'x2': seg[1],
                    'y2': seg[2]
                })
    
    # Sample for vertical lines
    for x in range(0, width, 5):  # Sample every 5 pixels
        black_segments = []
        in_black = False
        start_y = 0
        
        for y in range(height):
            r, g, b = pixels[x, y]
            is_black = (r < 50 and g < 50 and b < 50)
            
            if is_black and not in_black:
                start_y = y
                in_black = True
            elif not is_black and in_black:
                if y - start_y > 10:  # Minimum line length
                    black_segments.append((x, start_y, y))
                in_black = False
        
        # Add long segments as walls
        for seg in black_segments:
            if seg[2] - seg[1] > 50:  # Significant wall length
                walls.append({
                    'type': 'vertical',
                    'x1': seg[0],
                    'y1': seg[1],
                    'x2': seg[0],
                    'y2': seg[2]
                })
    
    # Find white rectangles (rooms) by flood fill approach
    # This is simplified - just finding large white areas
    visited = set()
    rooms = []
    
    # Sample points to find room centers
    for y in range(50, height - 50, 50):
        for x in range(50, width - 50, 50):
            if (x, y) in visited:
                continue
            
            r, g, b = pixels[x, y]
            if r > 200 and g > 200 and b > 200:  # White pixel (room interior)
                # Find bounds of this white area
                min_x, max_x = x, x
                min_y, max_y = y, y
                
                # Expand to find room boundaries
                # Check left
                test_x = x
                while test_x > 0:
                    r, g, b = pixels[test_x, y]
                    if r < 100:  # Hit a wall
                        break
                    min_x = test_x
                    test_x -= 5
                
                # Check right
                test_x = x
                while test_x < width - 1:
                    r, g, b = pixels[test_x, y]
                    if r < 100:  # Hit a wall
                        break
                    max_x = test_x
                    test_x += 5
                
                # Check up
                test_y = y
                while test_y > 0:
                    r, g, b = pixels[x, test_y]
                    if r < 100:  # Hit a wall
                        break
                    min_y = test_y
                    test_y -= 5
                
                # Check down
                test_y = y
                while test_y < height - 1:
                    r, g, b = pixels[x, test_y]
                    if r < 100:  # Hit a wall
                        break
                    max_y = test_y
                    test_y += 5
                
                # Add room if it's significant size
                room_width = max_x - min_x
                room_height = max_y - min_y
                if room_width > 30 and room_height > 30:
                    rooms.append({
                        'x': min_x,
                        'y': min_y,
                        'width': room_width,
                        'height': room_height
                    })
                    
                    # Mark area as visited
                    for vy in range(min_y, max_y, 10):
                        for vx in range(min_x, max_x, 10):
                            visited.add((vx, vy))
    
    return walls, rooms, width, height

def main(pdf_path):
    """Process the PDF and extract real geometry"""
    try:
        # Extract image from PDF
        image_path = extract_image_from_pdf(pdf_path)
        
        # Analyze actual pixels
        walls, rooms, width, height = analyze_pixels(image_path)
        
        # Building is approximately 150m wide
        scale = 150000.0 / width  # mm per pixel
        
        result = {
            'success': True,
            'image_width': width,
            'image_height': height,
            'scale': scale,
            'walls': walls,
            'rooms': rooms,
            'wall_count': len(walls),
            'room_count': len(rooms)
        }
        
        print(json.dumps(result), file=sys.stdout)
        
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'walls': [],
            'rooms': []
        }), file=sys.stdout)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: python3 analyze_floorplan.py <pdf_path>'}))
        sys.exit(1)
    
    main(sys.argv[1])