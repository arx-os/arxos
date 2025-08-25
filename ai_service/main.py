"""
Arxos AI Service - Real Computer Vision & LiDAR Processing
Two jobs: Detect architectural symbols & Process iPhone 3D scans
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
from fastapi import FastAPI, File, UploadFile, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from vision.symbol_detector import SymbolDetector
from lidar.iphone_processor import iPhoneLiDARProcessor
from cache_client import get_cache, close_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Arxos AI Service",
    description="Real AI for architectural intelligence",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI components
symbol_detector = SymbolDetector()
lidar_processor = iPhoneLiDARProcessor()

@app.on_event("startup")
async def startup():
    """Load ML models on startup"""
    logger.info("Loading ML models...")
    await symbol_detector.load_model()
    
    # Initialize cache connection
    cache = await get_cache()
    logger.info("Cache initialized")
    
    logger.info("AI Service ready!")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await close_cache()
    logger.info("AI Service shutdown complete")

@app.get("/")
async def health():
    """Health check"""
    return {
        "service": "Arxos AI Service",
        "status": "operational",
        "capabilities": [
            "symbol_detection",
            "lidar_processing"
        ],
        "models_loaded": symbol_detector.is_loaded()
    }

# ============================================
# SYMBOL DETECTION - Computer Vision
# ============================================

@app.post("/detect/symbols")
async def detect_symbols(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5
):
    """
    Detect architectural symbols in floor plan images
    Returns: doors, windows, stairs, fixtures, etc.
    """
    try:
        # Read image
        contents = await file.read()
        
        # Check cache first
        cache = await get_cache()
        cached = await cache.get_detection(
            contents, 
            model="yolo",
            threshold=confidence_threshold
        )
        
        if cached:
            logger.info("Returning cached detection results")
            return cached
        
        # Run YOLO detection
        detections = await symbol_detector.detect(
            contents, 
            threshold=confidence_threshold
        )
        
        # Convert to Arxos format
        arxobjects = []
        for det in detections:
            arxobjects.append({
                "id": f"{det['class']}_{det['id']}",
                "type": det['class'],  # door, window, stair, etc.
                "bbox": det['bbox'],  # [x, y, width, height]
                "confidence": det['confidence'],
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        det['bbox'][0] + det['bbox'][2]/2,
                        det['bbox'][1] + det['bbox'][3]/2
                    ]
                },
                "properties": {
                    "symbol_type": det['class'],
                    "subtype": det.get('subtype', ''),  # single door, double door, etc.
                }
            })
        
        result = {
            "success": True,
            "detections": len(arxobjects),
            "arxobjects": arxobjects,
            "metadata": {
                "model": "YOLOv8-Architecture",
                "confidence_threshold": confidence_threshold,
                "image_size": detections[0].get('image_size', []) if detections else []
            }
        }
        
        # Cache the results
        await cache.set_detection(
            contents,
            result,
            model="yolo",
            threshold=confidence_threshold
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Symbol detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect/rooms")
async def detect_rooms(file: UploadFile = File(...)):
    """
    Detect and classify rooms in floor plans
    Uses semantic segmentation to identify room boundaries and types
    """
    try:
        contents = await file.read()
        
        # Run room segmentation
        rooms = await symbol_detector.segment_rooms(contents)
        
        # Convert to Arxos format
        arxobjects = []
        for room in rooms:
            arxobjects.append({
                "id": f"room_{room['id']}",
                "type": "room",
                "subtype": room['room_type'],  # bedroom, kitchen, bathroom, etc.
                "geometry": room['polygon'],  # Actual room boundary
                "confidence": room['confidence'],
                "properties": {
                    "room_type": room['room_type'],
                    "area": room.get('area_sqft'),
                    "features": room.get('features', [])  # detected fixtures
                }
            })
        
        return {
            "success": True,
            "rooms": len(arxobjects),
            "arxobjects": arxobjects
        }
        
    except Exception as e:
        logger.error(f"Room detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# iPHONE LiDAR - 3D Scanning
# ============================================

@app.post("/lidar/process")
async def process_lidar(file: UploadFile = File(...)):
    """
    Process iPhone LiDAR scan data (PLY/USDZ format)
    Extracts walls, floors, and room geometry
    """
    try:
        contents = await file.read()
        file_ext = Path(file.filename).suffix.lower()
        
        # Process point cloud
        result = await lidar_processor.process_scan(
            contents,
            format=file_ext
        )
        
        # Extract architectural elements
        arxobjects = []
        
        # Add detected walls
        for wall in result['walls']:
            arxobjects.append({
                "id": f"wall_{wall['id']}",
                "type": "wall",
                "geometry": wall['line_3d'],  # 3D line segment
                "properties": {
                    "height": wall['height'],
                    "thickness": wall.get('thickness', 0.15),  # meters
                    "confidence": wall['confidence']
                }
            })
        
        # Add floor plane
        if result.get('floor'):
            arxobjects.append({
                "id": "floor_0",
                "type": "floor",
                "geometry": result['floor']['plane'],
                "properties": {
                    "elevation": result['floor']['elevation'],
                    "area": result['floor']['area']
                }
            })
        
        # Add detected rooms
        for room in result.get('rooms', []):
            arxobjects.append({
                "id": f"room_{room['id']}",
                "type": "room",
                "geometry": room['boundary_3d'],
                "properties": {
                    "height": room['height'],
                    "volume": room['volume'],
                    "floor_area": room['floor_area']
                }
            })
        
        return {
            "success": True,
            "arxobjects": arxobjects,
            "metadata": {
                "point_count": result['point_count'],
                "scan_quality": result['quality_score'],
                "processing_time": result['processing_time']
            }
        }
        
    except Exception as e:
        logger.error(f"LiDAR processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/lidar/stream")
async def lidar_stream(websocket: WebSocket):
    """
    Real-time LiDAR streaming from iPhone
    Processes point cloud data as it arrives
    """
    await websocket.accept()
    logger.info("LiDAR stream connected")
    
    try:
        while True:
            # Receive point cloud chunk
            data = await websocket.receive_bytes()
            
            # Process incrementally
            result = await lidar_processor.process_stream_chunk(data)
            
            # Send back detected elements
            if result['new_elements']:
                await websocket.send_json({
                    "type": "update",
                    "elements": result['new_elements'],
                    "scan_progress": result['progress']
                })
            
    except Exception as e:
        logger.error(f"Stream error: {e}")
    finally:
        await websocket.close()

# ============================================
# TRAINING ENDPOINTS (Development only)
# ============================================

@app.post("/train/symbols")
async def train_symbol_detector(
    dataset: UploadFile = File(...),
    epochs: int = 100
):
    """
    Train/fine-tune symbol detection model
    Upload annotated dataset in YOLO format
    """
    if not app.debug:
        raise HTTPException(403, "Training only available in development")
    
    # This would trigger model training
    # In production, training happens offline
    return {
        "message": "Training pipeline would start here",
        "epochs": epochs
    }

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        reload=debug
    )