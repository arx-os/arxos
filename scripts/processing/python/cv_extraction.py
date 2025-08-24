#!/usr/bin/env python3
"""
Real computer vision extraction from floor plan images
Analyzes actual pixels to detect walls, rooms, and text
"""

import sys
import json
import subprocess
import os
import cv2
import numpy as np
import pytesseract

def extract_floor_plan_image(pdf_path):
    """Extract the embedded image from PDF"""
    temp_prefix = '/tmp/floorplan_cv'
    subprocess.run(['pdfimages', '-png', pdf_path, temp_prefix], capture_output=True)
    
    # Find the extracted image
    for i in range(10):
        path = f'{temp_prefix}-{i:03d}.png'
        if os.path.exists(path):
            return path
    
    raise Exception("No image found in PDF")

def detect_walls_from_pixels(image):
    """Detect walls by finding black lines in the image"""
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Threshold to get binary image (walls are black)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    # Invert so walls are white
    binary = cv2.bitwise_not(binary)
    
    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    
    # Detect vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    
    # Find contours for horizontal walls
    h_contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find contours for vertical walls
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
    
    return walls, binary

def detect_rooms_from_pixels(image, binary_walls):
    """Detect rooms by finding enclosed white spaces"""
    height, width = image.shape[:2]
    
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Threshold to get binary image
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Dilate walls slightly to close small gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    walls_dilated = cv2.dilate(binary_walls, kernel, iterations=1)
    
    # Subtract walls from image to get room areas
    room_areas = cv2.bitwise_and(binary, cv2.bitwise_not(walls_dilated))
    
    # Apply morphological opening to remove noise
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    room_areas = cv2.morphologyEx(room_areas, cv2.MORPH_OPEN, kernel_open)
    
    # Find contours (rooms)
    contours, hierarchy = cv2.findContours(room_areas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rooms = []
    
    # Process each contour
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        
        # Filter by area (rooms should be reasonably sized)
        # Adjusted thresholds for actual floor plan scale
        if area > 1000:  # Minimum room size
            x, y, w, h = cv2.boundingRect(contour)
            
            # Additional filtering based on aspect ratio (rooms shouldn't be too thin)
            aspect_ratio = w / h if h > 0 else 0
            if 0.2 < aspect_ratio < 5:  # Reasonable room proportions
                rooms.append({
                    'id': f'room_{i}',
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'area': area,
                    'center_x': x + w//2,
                    'center_y': y + h//2
                })
    
    return rooms

def detect_doors_and_openings(image, walls):
    """Detect doors by finding gaps in walls"""
    doors = []
    
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Look for arc patterns (common door symbol)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                               param1=50, param2=30, minRadius=10, maxRadius=40)
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            x, y, r = circle
            doors.append({
                'type': 'door',
                'x': int(x),
                'y': int(y),
                'radius': int(r)
            })
    
    return doors

def extract_text_with_ocr(image):
    """Extract text using OCR"""
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Apply threshold for better OCR
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    # Run OCR
    try:
        # Get text with bounding boxes
        data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT)
        
        text_regions = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text:  # Only process non-empty text
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                conf = data['conf'][i]
                
                # Filter by confidence
                if conf > 30:  # Confidence threshold
                    text_regions.append({
                        'text': text,
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'center_x': x + w//2,
                        'center_y': y + h//2,
                        'confidence': conf
                    })
        
        return text_regions
        
    except Exception as e:
        print(f"OCR failed: {e}", file=sys.stderr)
        return []

def associate_text_with_rooms(text_regions, rooms):
    """Match text labels to their corresponding rooms"""
    for text in text_regions:
        tx, ty = text['center_x'], text['center_y']
        
        # Find closest room
        min_dist = float('inf')
        closest_room = None
        
        for room in rooms:
            rx, ry = room['center_x'], room['center_y']
            dist = np.sqrt((tx - rx)**2 + (ty - ry)**2)
            
            # Check if text is inside or near the room
            if (room['x'] <= tx <= room['x'] + room['width'] and 
                room['y'] <= ty <= room['y'] + room['height']):
                # Text is inside the room
                room['text_label'] = text
                break
            elif dist < min_dist and dist < 100:  # Within 100 pixels
                min_dist = dist
                closest_room = room
        
        if closest_room and 'text_label' not in closest_room:
            closest_room['text_label'] = text

def process_floor_plan(pdf_path):
    """Main processing pipeline"""
    try:
        # Extract image from PDF
        image_path = extract_floor_plan_image(pdf_path)
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise Exception(f"Could not load image from {image_path}")
        
        height, width = image.shape[:2]
        print(f"Processing {width}x{height} image", file=sys.stderr)
        
        # Detect walls
        walls, binary_walls = detect_walls_from_pixels(image)
        print(f"Detected {len(walls)} walls", file=sys.stderr)
        
        # Detect rooms
        rooms = detect_rooms_from_pixels(image, binary_walls)
        print(f"Detected {len(rooms)} rooms", file=sys.stderr)
        
        # Detect doors
        doors = detect_doors_and_openings(image, walls)
        print(f"Detected {len(doors)} doors", file=sys.stderr)
        
        # Extract text with OCR
        text_regions = extract_text_with_ocr(image)
        print(f"Extracted {len(text_regions)} text regions with OCR", file=sys.stderr)
        
        # Associate text with rooms
        associate_text_with_rooms(text_regions, rooms)
        
        # Calculate scale (building is approximately 150m wide)
        # Find the extent of detected walls
        if walls:
            min_x = min(w['x1'] for w in walls)
            max_x = max(w['x2'] if w['type'] == 'horizontal' else w['x1'] for w in walls)
            building_width_pixels = max_x - min_x
            scale = 150000.0 / building_width_pixels if building_width_pixels > 0 else 50.0
        else:
            scale = 150000.0 / width
        
        # Clean up temporary files
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Return results
        return {
            'success': True,
            'image_width': width,
            'image_height': height,
            'scale_x': scale,
            'scale_y': scale,
            'walls': walls,
            'rooms': rooms,
            'doors': doors,
            'text_regions': text_regions,
            'stats': {
                'wall_count': len(walls),
                'room_count': len(rooms),
                'door_count': len(doors),
                'text_count': len(text_regions)
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'walls': [],
            'rooms': [],
            'doors': [],
            'text_regions': []
        }

def convert_to_serializable(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: python3 cv_extraction.py <pdf_path>'}))
        sys.exit(1)
    
    result = process_floor_plan(sys.argv[1])
    result = convert_to_serializable(result)
    print(json.dumps(result))

if __name__ == '__main__':
    main()