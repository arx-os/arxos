# ARKit Development Setup

## Building the iOS AR Experience

### Project Setup

```swift
// Info.plist requirements
<key>NSCameraUsageDescription</key>
<string>Arxos needs camera for AR building mapping</string>

<key>NSBluetoothAlwaysUsageDescription</key>
<string>Arxos uses Bluetooth for mesh radio connection</string>
```

### ARKit Configuration

```swift
import ARKit

class ARViewController: UIViewController {
    @IBOutlet var sceneView: ARSCNView!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Configure AR session
        let configuration = ARWorldTrackingConfiguration()
        configuration.planeDetection = [.horizontal, .vertical]
        configuration.environmentTexturing = .automatic
        
        // Use LiDAR if available
        if ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh) {
            configuration.sceneReconstruction = .mesh
        }
        
        sceneView.session.run(configuration)
    }
}
```

### Rust-Swift Bridge

```swift
// Call Rust code from Swift via FFI
@_silgen_name("arxos_decode_object")
func arxos_decode_object(_ bytes: UnsafePointer<UInt8>) -> ArxObject

@_silgen_name("arxos_encode_object")
func arxos_encode_object(_ object: ArxObject) -> UnsafePointer<UInt8>
```

---

→ Next: [Object Detection](object-detection.md)