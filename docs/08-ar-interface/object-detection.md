# Object Detection in AR

## Recognizing Building Infrastructure

### Vision Framework

```swift
import Vision

func detectElectricalOutlet(in image: CVPixelBuffer) {
    let request = VNRecognizeTextRequest { request, error in
        // Look for outlet labels
    }
    
    let rectangleRequest = VNDetectRectanglesRequest { request, error in
        // Detect outlet shape
    }
    
    try? VNImageRequestHandler(cvPixelBuffer: image)
        .perform([request, rectangleRequest])
}
```

### CoreML Models

```swift
// Custom trained model for building objects
let model = try? VNCoreMLModel(for: ArxosObjectDetector().model)

let request = VNCoreMLRequest(model: model) { request, error in
    guard let results = request.results as? [VNRecognizedObjectObservation] else { return }
    
    for object in results {
        if object.label == "outlet" {
            queryMeshForObject(at: object.location)
        }
    }
}
```

### LiDAR Point Clouds

```swift
// Use LiDAR for precise positioning
func processLiDAR(_ frame: ARFrame) {
    guard let pointCloud = frame.sceneDepth?.depthMap else { return }
    
    // Find flat surfaces (walls)
    // Detect protrusions (outlets)
    // Calculate exact position
}
```

---

→ Next: [Mesh Queries](mesh-queries.md)