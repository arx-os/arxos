#!/usr/bin/env python3
"""
REAL floor plan extraction using computer vision
This actually processes the image to detect walls and rooms
"""

import sys
import json
import subprocess
import os
import cv2
import numpy as np

def extract_floor_plan_image(pdf_path):
    """Extract the embedded image from PDF"""
    temp_prefix = '/tmp/floor_extract'
    # Extract all images from PDF
    subprocess.run(['pdfimages', '-png', pdf_path, temp_prefix], capture_output=True)
    
    # Find the largest extracted image (likely the floor plan)
    image_files = []
    for i in range(10):  # Check first 10 possible images
        for ext in ['.png', '.jpg', '.ppm']:
            path = f'{temp_prefix}-{i:03d}{ext}'
            if os.path.exists(path):
                image_files.append(path)
    
    if not image_files:
        raise Exception("No images found in PDF")
    
    # Use the first image (usually the main floor plan)
    return image_files[0]

def detect_walls(image):
    """Detect walls using line detection"""
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Detect horizontal and vertical lines using morphology
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    
    # Detect horizontal lines
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    horizontal_lines = cv2.dilate(horizontal_lines, horizontal_kernel, iterations=2)
    
    # Detect vertical lines  
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
    vertical_lines = cv2.dilate(vertical_lines, vertical_kernel, iterations=2)
    
    # Find contours for horizontal lines
    h_contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find contours for vertical lines
    v_contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    walls = []
    
    # Process horizontal walls
    for contour in h_contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 30:  # Minimum wall length
            walls.append({
                'type': 'horizontal',
                'x1': x,
                'y1': y + h//2,
                'x2': x + w,
                'y2': y + h//2,
                'thickness': h
            })
    
    # Process vertical walls
    for contour in v_contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h > 30:  # Minimum wall length
            walls.append({
                'type': 'vertical',
                'x1': x + w//2,
                'y1': y,
                'x2': x + w//2,
                'y2': y + h,
                'thickness': w
            })
    
    return walls

def detect_rooms(image, walls):
    """Detect rooms by finding enclosed spaces"""
    height, width = image.shape[:2]
    
    # Create a mask with walls
    wall_mask = np.ones((height, width), dtype=np.uint8) * 255
    
    # Draw walls on mask
    for wall in walls:
        if wall['type'] == 'horizontal':
            cv2.line(wall_mask, (wall['x1'], wall['y1']), (wall['x2'], wall['y2']), 0, max(3, wall['thickness']))
        else:
            cv2.line(wall_mask, (wall['x1'], wall['y1']), (wall['x2'], wall['y2']), 0, max(3, wall['thickness']))
    
    # Find contours (rooms are the white spaces)
    contours, _ = cv2.findContours(wall_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rooms = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area > 1000:  # Minimum room size
            x, y, w, h = cv2.boundingRect(contour)
            # Skip the outer boundary
            if x > 5 and y > 5 and x + w < width - 5 and y + h < height - 5:
                rooms.append({
                    'id': f'room_{i}',
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'area': area
                })
    
    return rooms

def detect_text_labels(image):
    """Use OCR to detect room numbers and labels"""
    # This would use OCR (like pytesseract) to extract text
    # For now, return empty list
    return []

def process_floor_plan(pdf_path):
    """Main processing function"""
    try:
        # Extract image from PDF
        image_path = extract_floor_plan_image(pdf_path)
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise Exception(f"Could not load image from {image_path}")
        
        height, width = image.shape[:2]
        
        # Detect walls
        walls = detect_walls(image)
        
        # Detect rooms
        rooms = detect_rooms(image, walls)
        
        # Detect text labels
        labels = detect_text_labels(image)
        
        # Calculate scale (assuming building is approximately 150m wide)
        scale_factor = 150000.0 / width  # mm per pixel
        
        # Convert to output format
        result = {
            'success': True,
            'image_width': width,
            'image_height': height,
            'scale_factor': scale_factor,
            'walls': walls,
            'rooms': rooms,
            'labels': labels,
            'stats': {
                'wall_count': len(walls),
                'room_count': len(rooms),
                'label_count': len(labels)
            }
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'walls': [],
            'rooms': [],
            'labels': []
        }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: python3 real_extraction.py <pdf_path>'}))
        sys.exit(1)
    
    result = process_floor_plan(sys.argv[1])
    print(json.dumps(result))

if __name__ == '__main__':
    main()