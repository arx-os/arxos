"""
Dataset Preparation for Arxos AI
Prepares architectural symbol training data for YOLO
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import shutil

import cv2
import numpy as np
from PIL import Image

class DatasetPreparer:
    """
    Prepare floor plan datasets for training
    Converts various annotation formats to YOLO format
    """
    
    # Map common architectural symbols to class IDs
    CLASS_MAPPING = {
        'door': 0,
        'door_single': 0,
        'door_double': 1,
        'door_sliding': 2,
        'window': 3,
        'stairs': 4,
        'toilet': 5,
        'sink': 6,
        'bathtub': 7,
        'shower': 8,
        # Add more as needed
    }
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        
    def prepare_yolo_dataset(self):
        """
        Create YOLO format dataset structure:
        dataset/
        ├── images/
        │   ├── train/
        │   └── val/
        ├── labels/
        │   ├── train/
        │   └── val/
        └── data.yaml
        """
        # Create directories
        for split in ['train', 'val']:
            (self.output_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
            (self.output_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
        # Process annotations
        self._convert_annotations()
        
        # Create data.yaml
        self._create_data_yaml()
        
    def _convert_annotations(self):
        """Convert annotations to YOLO format"""
        # This would convert from your annotation format to YOLO
        # YOLO format: class_id center_x center_y width height (normalized 0-1)
        
        annotations = self._load_annotations()
        
        for ann in annotations:
            image_path = self.source_dir / ann['image']
            
            # Load image to get dimensions
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            # Convert bounding boxes to YOLO format
            yolo_labels = []
            for obj in ann['objects']:
                class_id = self.CLASS_MAPPING.get(obj['type'], -1)
                if class_id == -1:
                    continue
                
                # Convert bbox to YOLO format (normalized)
                x, y, w, h = obj['bbox']
                cx = (x + w/2) / img_width
                cy = (y + h/2) / img_height
                nw = w / img_width
                nh = h / img_height
                
                yolo_labels.append(f"{class_id} {cx} {cy} {nw} {nh}")
            
            # Save label file
            label_path = self.output_dir / 'labels' / 'train' / f"{ann['image'].stem}.txt"
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_labels))
            
            # Copy image
            shutil.copy(
                image_path,
                self.output_dir / 'images' / 'train' / ann['image'].name
            )
    
    def _create_data_yaml(self):
        """Create YOLO data configuration file"""
        data_config = {
            'path': str(self.output_dir.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'names': {
                0: 'door_single',
                1: 'door_double',
                2: 'door_sliding',
                3: 'window',
                4: 'stairs',
                5: 'toilet',
                6: 'sink',
                7: 'bathtub',
                8: 'shower'
            }
        }
        
        with open(self.output_dir / 'data.yaml', 'w') as f:
            import yaml
            yaml.dump(data_config, f)
    
    def _load_annotations(self) -> List[Dict[str, Any]]:
        """Load your annotation format"""
        # This would load your specific annotation format
        # Could be JSON, XML, CSV, etc.
        
        # Placeholder
        return []
    
    def augment_dataset(self):
        """
        Augment floor plan images for better training
        - Rotation (90, 180, 270 degrees - floor plans can be any orientation)
        - Scaling (different drawing scales)
        - Noise (scan artifacts)
        """
        # TODO: Implement augmentation
        pass

def download_pretrained():
    """
    Download pre-trained model weights
    In production, would download from your model repository
    """
    import urllib.request
    
    model_url = "https://your-models.s3.amazonaws.com/yolo_architecture_v1.pt"
    model_path = "models/yolo_architecture.pt"
    
    os.makedirs("models", exist_ok=True)
    
    print("Downloading pre-trained model...")
    # urllib.request.urlretrieve(model_url, model_path)
    print("Model ready!")

if __name__ == "__main__":
    # Example usage
    preparer = DatasetPreparer(
        source_dir="raw_data/floor_plans",
        output_dir="datasets/arxos_symbols"
    )
    preparer.prepare_yolo_dataset()