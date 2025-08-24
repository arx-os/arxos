# Arxos AI Service

## Purpose
Real AI/ML for architectural intelligence:
1. **Symbol Detection** - Detect doors, windows, fixtures, stairs in floor plans
2. **iPhone LiDAR** - Real-time 3D scanning to BIM conversion

## What This Service Does
- **Computer Vision**: YOLO-based detection of architectural elements
- **3D Processing**: iPhone LiDAR point clouds → walls and rooms
- **Real Intelligence**: Trained ML models, not just geometry math

## What Go Backend Does
- PDF parsing and line extraction
- Geometric calculations and wall merging  
- Database and business logic
- API and authentication

## Architecture
```
ai_service/
├── models/          # Trained ML models
├── vision/          # Computer vision for symbols
├── lidar/           # iPhone 3D scanning
├── training/        # Model training pipelines
└── api/             # FastAPI endpoints
```

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Download pre-trained models
python download_models.py

# Start service
python main.py
```

## Endpoints
- `POST /detect/symbols` - Detect architectural symbols in image
- `POST /lidar/process` - Process iPhone LiDAR scan
- `WS /lidar/stream` - Real-time LiDAR streaming