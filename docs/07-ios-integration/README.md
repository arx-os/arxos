# iOS Integration: Terminal + Camera

## The Simplest Possible App That Does Everything

The Arxos iOS app is intentionally minimal: just an SSH terminal client with camera access. All intelligence stays on the mesh nodes where it belongs.

## 🎯 Design Philosophy

### What the App Is
- **SSH Terminal**: Connect to mesh nodes
- **Camera Interface**: LiDAR scanning and AR markup
- **That's it**: No complex logic, no data processing

### What the App Is NOT
- Not a web browser
- Not a data processor
- Not a cloud connector
- Not a complex UI

## 📱 App Architecture

```swift
struct ArxosApp {
    // Two views, no more:
    let terminal: SSHTerminalViewController
    let camera: ARCameraViewController
    
    // Zero business logic:
    // All processing happens on mesh nodes
}
```

## 🔄 User Workflows

### Standard Terminal Usage (90% of time)
```bash
# User opens app, connects to mesh node:
$ ssh arxos@building-node.local
Password: [building-access-code]

# Full terminal access to building:
$ arxos status
> Building: Jefferson Elementary
> Nodes: 47 online, 2 offline
> Objects: 1,847 mapped
> Coverage: 87%

$ arxos query "all outlets in room 127"
> 8 outlets found:
> - North wall: 3 outlets (Circuits B-7, B-8)
> - South wall: 3 outlets (Circuit B-9)
> - East wall: 2 outlets (Circuit B-10)

$ arxos control lights --room=127 --state=off
> Room 127 lights turned off
```

### Camera Integration (10% of time)

#### LiDAR Room Scanning
```swift
// Terminal command triggers camera:
$ arxos scan --room=127 --lidar

// App behavior:
1. Terminal sends command to mesh node
2. Mesh node responds: "CAMERA_REQUEST:LIDAR"
3. App opens ARKit camera view
4. User scans room with LiDAR
5. Point cloud captured
6. Data sent to mesh node via SSH
7. Camera closes, returns to terminal

// Terminal shows result:
> Room scan complete
> Dimensions: 12.5m x 8.3m x 3.1m
> Objects detected: 8 outlets, 4 lights, 2 vents
> Compression: 50MB → 5KB (10,000:1)
> ASCII preview:
> ┌─────────────────────┐
> │ [O]  [L]  [L]  [O]  │
> │                     │
> │      ROOM 127       │
> │                     │
> │ [O]  [L]  [L]  [O]  │
> └─────────────────────┘
```

#### AR Object Markup
```swift
// Terminal command for AR markup:
$ arxos markup --object=outlet --ar-guided

// App behavior:
1. Camera opens with AR overlay
2. Crosshairs appear in center
3. User points at outlet
4. Tap to capture position
5. Camera closes
6. Terminal prompts for details

// Back in terminal:
> Position captured: (10.5m, 2.3m, 0.3m)
> Enter outlet specifications:
> Circuit ID: B-7
> Voltage: 120V
> Amperage: 15A
> 
> Outlet marked successfully
> Earned 25 BILT points
> Total balance: 347 BILT
```

## 💻 Implementation Details

### Terminal Component
```swift
import SwiftUI
import SwiftTerm

struct TerminalView: View {
    @State private var session: SSHSession?
    @State private var isConnected = false
    
    var body: some View {
        VStack {
            // Connection bar
            HStack {
                TextField("Host", text: $hostname)
                Button("Connect") { connect() }
            }
            .padding()
            
            // Terminal display
            TerminalViewRepresentable(session: session)
                .onReceive(session?.dataPublisher) { data in
                    // Check for camera requests
                    if data.contains("CAMERA_REQUEST") {
                        handleCameraRequest(data)
                    }
                }
            
            // Quick action buttons
            HStack {
                Button("Scan") { 
                    session?.send("arxos scan --room=current\n")
                }
                Button("Markup") {
                    session?.send("arxos markup --ar-guided\n")
                }
                Button("Status") {
                    session?.send("arxos status\n")
                }
            }
            .padding()
        }
    }
    
    func handleCameraRequest(_ data: String) {
        if data.contains("LIDAR") {
            presentLiDARScanner()
        } else if data.contains("AR_MARKUP") {
            presentARMarkup()
        }
    }
}
```

### Camera Component
```swift
import ARKit
import RoomPlan

struct LiDARScannerView: UIViewControllerRepresentable {
    let onScanComplete: (CapturedRoom) -> Void
    
    func makeUIViewController(context: Context) -> RoomCaptureViewController {
        let controller = RoomCaptureViewController()
        controller.delegate = context.coordinator
        return controller
    }
    
    class Coordinator: RoomCaptureViewControllerDelegate {
        let parent: LiDARScannerView
        
        func captureView(didPresent room: CapturedRoom) {
            // Send room data to mesh node
            parent.onScanComplete(room)
        }
    }
}

struct ARMarkupView: UIViewControllerRepresentable {
    let onPositionCaptured: (simd_float3) -> Void
    
    func makeUIViewController(context: Context) -> ARViewController {
        let controller = ARViewController()
        
        // Simple tap to capture position
        controller.onTap = { location in
            onPositionCaptured(location)
        }
        
        return controller
    }
}
```

### Data Flow
```swift
class MeshNodeConnection {
    let sshSession: SSHSession
    
    func sendLiDARData(_ room: CapturedRoom) {
        // Convert RoomPlan data to compressed format
        let compressed = compressRoomData(room)
        
        // Send via SSH to mesh node
        sshSession.sendBinary(compressed)
        
        // Mesh node processes and responds in terminal
    }
    
    func sendARPosition(_ position: simd_float3) {
        // Format: "POSITION:x,y,z"
        let message = "POSITION:\(position.x),\(position.y),\(position.z)\n"
        sshSession.send(message)
    }
}
```

## 🎨 UI Design

### Minimal Interface
```
┌─────────────────────────────────┐
│ Arxos Terminal                  │
├─────────────────────────────────┤
│ arxos@jefferson-elementary:~$   │
│                                 │
│ [Terminal Output Area]          │
│                                 │
│                                 │
│                                 │
│                                 │
├─────────────────────────────────┤
│ [Scan] [Markup] [Status] [Help] │
└─────────────────────────────────┘
```

### Camera View (When Activated)
```
┌─────────────────────────────────┐
│        📷 LiDAR Scanner         │
├─────────────────────────────────┤
│                                 │
│         [Camera View]           │
│             + +                 │
│         [Crosshairs]            │
│                                 │
│                                 │
├─────────────────────────────────┤
│    Tap to mark position         │
│    [Cancel]        [Capture]    │
└─────────────────────────────────┘
```

## 📦 App Store Listing

### Name
**Arxos Terminal - Building Intelligence**

### Description
Professional building management through secure mesh networks. Connect to your building's air-gapped intelligence system via SSH terminal. Scan rooms with LiDAR, mark equipment with AR, control systems through command line.

### Key Features
- SSH terminal for mesh network access
- LiDAR room scanning (iPhone 12 Pro+)
- AR equipment markup
- Works offline - no internet required
- Professional terminal interface
- BILT reward tracking

### Screenshots
1. Terminal connected to building
2. ASCII floor plan display
3. LiDAR scanning in progress
4. AR markup interface
5. BILT rewards summary

### Requirements
- iOS 15.0+
- iPhone 12 Pro or newer (for LiDAR)
- Local network access

## 🔒 Security Features

### No Internet Permission
```xml
<!-- Info.plist -->
<key>NSAppTransportSecurity</key>
<dict>
    <!-- No internet domains allowed -->
    <key>NSAllowsArbitraryLoads</key>
    <false/>
</dict>

<!-- Only local network access -->
<key>NSLocalNetworkUsageDescription</key>
<string>Connect to building mesh nodes on local network</string>
```

### SSH Key Management
```swift
struct SSHKeyManager {
    // Generate key pair on first launch
    func generateKeypair() -> (public: String, private: String)
    
    // Store in iOS Keychain (secure)
    func storeInKeychain(_ private: String)
    
    // Never transmitted over internet
    // Only used for local mesh node connections
}
```

## 🚀 Development Roadmap

### Phase 1: MVP (Current)
- ✅ Basic SSH terminal
- ✅ Connect to mesh nodes
- 🔄 LiDAR integration
- 🔄 AR markup

### Phase 2: Enhanced Terminal
- Terminal customization
- Command shortcuts
- Gesture controls
- Terminal themes

### Phase 3: Advanced Features
- Offline maps
- BILT wallet
- Multi-building support
- Biometric authentication

## 📝 Code Simplicity

The entire app is ~1000 lines of Swift:
- 300 lines: SSH terminal
- 300 lines: Camera integration
- 200 lines: UI layout
- 200 lines: Data handling

Compare to traditional building apps:
- 50,000+ lines of code
- Complex architectures
- Cloud dependencies
- Constant maintenance

## 🎯 Why This Design Wins

1. **Simple**: Two views, no complex logic
2. **Secure**: No internet, just local SSH
3. **Fast**: Native terminal performance
4. **Reliable**: Fewer things to break
5. **Professional**: Power users love terminals

---

*"The best code is no code. The second best is simple code."*