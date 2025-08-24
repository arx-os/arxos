"""
Symbol Detection using YOLOv8
Detects architectural symbols: doors, windows, stairs, fixtures, etc.
"""

import io
import logging
from typing import List, Dict, Any, Optional

import numpy as np
from PIL import Image
import torch
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class SymbolDetector:
    """
    Computer vision for architectural symbol detection
    Uses YOLOv8 trained on floor plan symbols
    """
    
    # Architectural classes we detect
    CLASSES = [
        'door_single',
        'door_double', 
        'door_sliding',
        'door_pocket',
        'window',
        'window_bay',
        'stairs_up',
        'stairs_down',
        'elevator',
        'toilet',
        'sink',
        'bathtub', 
        'shower',
        'kitchen_sink',
        'stove',
        'refrigerator',
        'washer',
        'dryer',
        'fireplace',
        'wall_opening',
        'column',
        'electrical_outlet',
        'light_switch',
        'ceiling_fan'
    ]
    
    def __init__(self):
        self.model: Optional[YOLO] = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Symbol detector using device: {self.device}")
    
    async def load_model(self):
        """Load pre-trained YOLO model for architectural symbols"""
        try:
            # Check if custom model exists
            model_path = "models/yolo_architecture.pt"
            
            try:
                # Load custom trained model
                self.model = YOLO(model_path)
                logger.info("Loaded custom architecture model")
            except:
                # Fallback to base model (would need training)
                logger.warning("Custom model not found, using base YOLOv8")
                self.model = YOLO('yolov8m.pt')  # Medium model
                # In production, this would load our trained weights
                
            self.model.to(self.device)
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None
    
    async def detect(
        self, 
        image_bytes: bytes,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Detect architectural symbols in image
        
        Args:
            image_bytes: Image file bytes
            threshold: Confidence threshold
            
        Returns:
            List of detections with bbox, class, confidence
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Run inference
        results = self.model(image, conf=threshold)
        
        # Parse detections
        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for i, box in enumerate(boxes):
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    # Get class and confidence
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Map to our architectural classes
                    class_name = self._map_class(cls)
                    
                    detections.append({
                        'id': i,
                        'class': class_name,
                        'bbox': [x1, y1, x2-x1, y2-y1],  # [x, y, w, h]
                        'confidence': conf,
                        'image_size': [image.width, image.height]
                    })
        
        logger.info(f"Detected {len(detections)} symbols")
        return detections
    
    async def segment_rooms(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Segment and classify rooms in floor plan
        Uses semantic segmentation to identify room boundaries
        
        This would use a U-Net or DeepLabV3 model trained on floor plans
        """
        # TODO: Implement room segmentation model
        # For now, return placeholder
        logger.warning("Room segmentation not yet implemented")
        
        # In production, this would:
        # 1. Run semantic segmentation model
        # 2. Extract room polygons
        # 3. Classify each room (bedroom, kitchen, etc.)
        # 4. Return room boundaries and types
        
        return [
            {
                'id': 0,
                'room_type': 'bedroom',
                'polygon': [[0, 0], [100, 0], [100, 100], [0, 100]],
                'confidence': 0.85,
                'area_sqft': 150,
                'features': ['window', 'door_single']
            }
        ]
    
    def _map_class(self, class_id: int) -> str:
        """Map YOLO class ID to architectural symbol name"""
        # This mapping would depend on how model was trained
        if class_id < len(self.CLASSES):
            return self.CLASSES[class_id]
        return f"unknown_{class_id}"
    
    async def train(
        self,
        dataset_path: str,
        epochs: int = 100,
        batch_size: int = 16
    ):
        """
        Train or fine-tune model on architectural symbols
        
        Dataset should be in YOLO format:
        - images/
        - labels/
        - data.yaml
        """
        if not self.model:
            self.model = YOLO('yolov8m.pt')
        
        # Train model
        results = self.model.train(
            data=dataset_path,
            epochs=epochs,
            batch=batch_size,
            device=self.device,
            project='arxos_training',
            name='symbol_detection'
        )
        
        # Save trained model
        self.model.save('models/yolo_architecture.pt')
        
        return results