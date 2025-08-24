# AI Service - Next Steps for Development

## Overview
The AI service is built but needs trained models and real data to function. This document outlines the steps to make it production-ready.

## 1. Training Data Collection

### Symbol Detection Dataset
- **Goal**: 500-1000 annotated floor plan images
- **Annotations needed**: Bounding boxes for:
  - Doors (single, double, sliding, pocket)
  - Windows (standard, bay)
  - Stairs (up, down)
  - Bathroom fixtures (toilet, sink, tub, shower)
  - Kitchen fixtures (sink, stove, refrigerator)
  - Other symbols (electrical outlets, columns, etc.)

### Tools for Annotation
- [LabelImg](https://github.com/tzutalin/labelImg) - Simple YOLO format annotation
- [Roboflow](https://roboflow.com) - Web-based, can export to YOLO
- [CVAT](https://github.com/openvinotoolkit/cvat) - Professional annotation tool

### Where to Get Floor Plans
- Public datasets: [CubiCasa5K](https://github.com/CubiCasa/CubiCasa5k)
- Architecture sites with Creative Commons plans
- Generate synthetic data using CAD software

## 2. Model Training

### Symbol Detection Model
```bash
# Install training dependencies
pip install ultralytics tensorboard

# Prepare dataset
python training/prepare_dataset.py

# Train YOLO model
yolo detect train data=datasets/arxos_symbols/data.yaml model=yolov8m.pt epochs=100 imgsz=640

# Model will be saved to runs/detect/train/weights/best.pt
cp runs/detect/train/weights/best.pt models/yolo_architecture.pt
```

### Estimated Training Time
- GPU (RTX 3080): ~2-4 hours
- Apple M1/M2: ~8-12 hours  
- CPU: Not recommended (24+ hours)

## 3. iPhone LiDAR Integration

### iOS App Requirements
- Use Apple's RoomPlan API (iOS 16+)
- Export formats: PLY or USDZ
- Required iPhone: 12 Pro or newer (with LiDAR)

### Sample RoomPlan Implementation
```swift
import RoomPlan

let captureSession = RoomCaptureSession()
// Capture room
let finalResult = captureSession.finalResult

// Export as USDZ
let exportURL = documentsDirectory.appendingPathComponent("scan.usdz")
try finalResult.export(to: exportURL)

// Send to Arxos AI Service
uploadToArxos(file: exportURL)
```

### Testing Without iPhone
- Download sample LiDAR scans from [Sketchfab](https://sketchfab.com)
- Use synthetic point clouds from Blender
- Test PLY files from Open3D examples

## 4. WebSocket Real-time Streaming

### Client Implementation (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/lidar/stream');

ws.onopen = () => {
    // Start sending point cloud chunks
    captureDevice.on('data', (chunk) => {
        ws.send(chunk);
    });
};

ws.onmessage = (event) => {
    const result = JSON.parse(event.data);
    // Update UI with detected walls
    updateARView(result.elements);
};
```

## 5. Performance Optimization

### GPU Setup (Recommended)
```bash
# For NVIDIA GPUs
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For Apple Silicon
pip install torch torchvision  # Already optimized for M1/M2
```

### Model Optimization
- Quantization: Reduce model size by 75%
- ONNX export: For faster inference
- TensorRT: For NVIDIA deployment

## 6. Testing & Validation

### Unit Tests
```bash
# Create test suite
pytest tests/test_symbol_detection.py
pytest tests/test_lidar_processing.py
```

### Integration Tests
```bash
# Test with sample data
python -m pytest tests/integration/
```

### Performance Benchmarks
- Symbol detection: Target <500ms per image
- LiDAR processing: Target <2s for 50k points
- WebSocket latency: Target <100ms

## 7. Deployment Considerations

### Docker Setup
```dockerfile
FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime
# Add CUDA support for GPU inference
```

### API Rate Limiting
- Add Redis for request queuing
- Limit concurrent model inference
- Cache repeated detections

### Monitoring
- Track inference times
- Monitor GPU memory usage
- Log detection confidence scores

## 8. Future Enhancements

### Phase 2 Features
- Room type classification (bedroom vs bathroom)
- Dimension extraction from floor plans
- Material detection (wood, tile, carpet)

### Phase 3 Features
- Multi-floor building support
- MEP (Mechanical, Electrical, Plumbing) detection
- Furniture recognition and placement

## Resources

### Documentation
- [YOLOv8 Docs](https://docs.ultralytics.com)
- [Open3D Docs](http://www.open3d.org/docs/)
- [Apple RoomPlan](https://developer.apple.com/documentation/roomplan)

### Example Datasets
- [CubiCasa5K](https://github.com/CubiCasa/CubiCasa5k) - 5000 floor plans
- [RPLAN](http://staff.ustc.edu.cn/~fuxm/projects/DeepLayout/) - 80K floor plans
- [Structured3D](https://structured3d-dataset.org) - 3D indoor scenes

## Quick Start Commands

```bash
# 1. Install dependencies
cd ai_service
pip install -r requirements.txt

# 2. Download sample model (when available)
python download_models.py

# 3. Start service
python main.py

# 4. Test symbol detection
curl -X POST -F "file=@sample_floorplan.png" http://localhost:8000/detect/symbols

# 5. Test LiDAR processing  
curl -X POST -F "file=@sample_scan.ply" http://localhost:8000/lidar/process
```

## Contact for ML Questions
When implementing, consider using:
- Weights & Biases for experiment tracking
- Hugging Face for model hosting
- GitHub Actions for continuous training

---

**Note**: This is a real AI service that requires actual machine learning. Don't proceed without training data and GPU resources.