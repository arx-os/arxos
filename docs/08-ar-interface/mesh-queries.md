# Mesh Network Queries from AR

## Bridging iPhone to Building Intelligence

### Bluetooth LE to LoRa Bridge

```swift
import CoreBluetooth

class MeshBridge: NSObject {
    var peripheral: CBPeripheral?
    let serviceUUID = CBUUID(string: "6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    
    func queryObject(at position: simd_float3) -> ArxObject? {
        let query = MeshQuery(x: position.x, y: position.y, z: position.z)
        sendToMesh(query.bytes)
        
        // Wait for response
        return waitForResponse(timeout: 1.0)
    }
}
```

### Direct USB/Lightning Connection

```swift
// For professional installers
import ExternalAccessory

class USBMeshAdapter {
    let session: EASession
    
    func connect() {
        session = EASession(accessory: accessory, forProtocol: "com.arxos.mesh")
    }
}
```

### Query Optimization

```swift
// Cache recent queries
class MeshCache {
    var cache: [simd_float3: ArxObject] = [:]
    
    func query(position: simd_float3) -> ArxObject? {
        // Check cache first
        if let cached = cache[position] {
            return cached
        }
        
        // Query mesh
        let object = meshBridge.queryObject(at: position)
        cache[position] = object
        return object
    }
}
```

---

→ Next: [Gestures](gestures.md)