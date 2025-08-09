# Arxos XR SDK Entry Points & CLI Syntax

## 🎯 **Executive Summary**

This document defines the SDK entry points for XR developers and provides comprehensive CLI syntax for all AR/VR interactions within the Arxos mixed reality platform. These interfaces enable third-party developers to integrate with Arxos XR capabilities.

## 🔧 **XR SDK Entry Points**

### **Core SDK Interface**
```typescript
// Arxos XR SDK - Core Interface
interface ArxosXRSDK {
  // Initialization
  initialize(config: XRConfig): Promise<void>;
  connect(projectId: string): Promise<XRConnection>;
  disconnect(): Promise<void>;

  // Object Management
  stageObject(object: ArxObject): Promise<StagedObject>;
  confirmObject(objectId: string): Promise<ConfirmationResult>;
  rejectObject(objectId: string, reason: string): Promise<RejectionResult>;
  updateObjectPosition(objectId: string, position: Vector3): Promise<void>;

  // Scene Management
  loadScene(sceneId: string): Promise<XRScene>;
  saveScene(sceneId: string): Promise<void>;
  syncScene(): Promise<SyncResult>;

  // Collaboration
  joinSession(sessionId: string, role: UserRole): Promise<XRSession>;
  leaveSession(sessionId: string): Promise<void>;
  shareObject(objectId: string, userId: string): Promise<void>;

  // Voice Commands
  enableVoiceCommands(): Promise<void>;
  registerVoiceCommand(command: string, handler: VoiceHandler): void;

  // Events
  onObjectUpdate(callback: ObjectUpdateHandler): void;
  onSessionJoin(callback: SessionHandler): void;
  onVoiceCommand(callback: VoiceCommandHandler): void;
}
```

### **Platform-Specific SDKs**

#### **Unity SDK**
```csharp
// Unity Arxos XR SDK
using Arxos.XR;

public class ArxosXRManager : MonoBehaviour
{
    private ArxosXRSDK xrSDK;

    void Start()
    {
        xrSDK = new ArxosXRSDK();
        xrSDK.Initialize(new XRConfig
        {
            Platform = XRPlatform.Unity,
            DeviceType = XRDeviceType.VR,
            ProjectId = "construction_project_001"
        });

        // Register event handlers
        xrSDK.OnObjectUpdate += HandleObjectUpdate;
        xrSDK.OnVoiceCommand += HandleVoiceCommand;
    }

    public async void StageObject(ArxObject arxObject)
    {
        try
        {
            var stagedObject = await xrSDK.StageObject(arxObject);
            Debug.Log($"Object {stagedObject.Id} staged successfully");
        }
        catch (Exception ex)
        {
            Debug.LogError($"Failed to stage object: {ex.Message}");
        }
    }

    private void HandleObjectUpdate(ArxObject arxObject)
    {
        // Update Unity scene with object changes
        UpdateObjectInScene(arxObject);
    }

    private void HandleVoiceCommand(string command)
    {
        // Process voice commands
        ProcessVoiceCommand(command);
    }
}
```

#### **iOS SDK (ARKit)**
```swift
// iOS Arxos XR SDK
import ArxosXR
import ARKit
import RealityKit

class ArxosARViewController: UIViewController {
    private var arxosSDK: ArxosXRSDK!
    private var arView: ARView!

    override func viewDidLoad() {
        super.viewDidLoad()

        // Initialize Arxos SDK
        arxosSDK = ArxosXRSDK()
        arxosSDK.initialize(config: XRConfig(
            platform: .iOS,
            deviceType: .AR,
            projectId: "construction_project_001"
        ))

        // Setup AR session
        setupARSession()

        // Register handlers
        arxosSDK.onObjectUpdate = { [weak self] object in
            self?.handleObjectUpdate(object)
        }
    }

    func stageObject(_ arxObject: ArxObject) async {
        do {
            let stagedObject = try await arxosSDK.stageObject(arxObject)
            await displayStagedObject(stagedObject)
        } catch {
            print("Failed to stage object: \(error)")
        }
    }

    func confirmObject(_ objectId: String) async {
        do {
            let result = try await arxosSDK.confirmObject(objectId)
            await updateObjectState(result)
        } catch {
            print("Failed to confirm object: \(error)")
        }
    }

    private func handleObjectUpdate(_ object: ArxObject) {
        // Update AR scene with object changes
        updateObjectInARScene(object)
    }
}
```

#### **Android SDK (ARCore)**
```kotlin
// Android Arxos XR SDK
import com.arxos.xr.ArxosXRSDK
import com.arxos.xr.XRConfig
import com.arxos.xr.ArxObject

class ArxosARActivity : AppCompatActivity() {
    private lateinit var arxosSDK: ArxosXRSDK
    private lateinit var arFragment: ArFragment

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize Arxos SDK
        arxosSDK = ArxosXRSDK()
        arxosSDK.initialize(XRConfig(
            platform = XRPlatform.Android,
            deviceType = XRDeviceType.AR,
            projectId = "construction_project_001"
        ))

        // Setup AR fragment
        setupARFragment()

        // Register handlers
        arxosSDK.setOnObjectUpdateListener { object ->
            handleObjectUpdate(object)
        }
    }

    suspend fun stageObject(arxObject: ArxObject) {
        try {
            val stagedObject = arxosSDK.stageObject(arxObject)
            displayStagedObject(stagedObject)
        } catch (e: Exception) {
            Log.e("ArxosAR", "Failed to stage object: ${e.message}")
        }
    }

    suspend fun confirmObject(objectId: String) {
        try {
            val result = arxosSDK.confirmObject(objectId)
            updateObjectState(result)
        } catch (e: Exception) {
            Log.e("ArxosAR", "Failed to confirm object: ${e.message}")
        }
    }

    private fun handleObjectUpdate(object: ArxObject) {
        // Update AR scene with object changes
        updateObjectInARScene(object)
    }
}
```

#### **Web SDK (WebXR)**
```javascript
// Web Arxos XR SDK
import { ArxosXRSDK } from '@arxos/xr-web';

class ArxosWebXRManager {
    constructor() {
        this.xrSDK = new ArxosXRSDK();
        this.xrSession = null;
    }

    async initialize() {
        try {
            await this.xrSDK.initialize({
                platform: 'WebXR',
                deviceType: 'AR', // or 'VR'
                projectId: 'construction_project_001'
            });

            // Register event handlers
            this.xrSDK.onObjectUpdate = this.handleObjectUpdate.bind(this);
            this.xrSDK.onVoiceCommand = this.handleVoiceCommand.bind(this);

            console.log('Arxos XR SDK initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Arxos XR SDK:', error);
        }
    }

    async stageObject(arxObject) {
        try {
            const stagedObject = await this.xrSDK.stageObject(arxObject);
            await this.displayStagedObject(stagedObject);
            return stagedObject;
        } catch (error) {
            console.error('Failed to stage object:', error);
            throw error;
        }
    }

    async confirmObject(objectId) {
        try {
            const result = await this.xrSDK.confirmObject(objectId);
            await this.updateObjectState(result);
            return result;
        } catch (error) {
            console.error('Failed to confirm object:', error);
            throw error;
        }
    }

    handleObjectUpdate(object) {
        // Update WebXR scene with object changes
        this.updateObjectInScene(object);
    }

    handleVoiceCommand(command) {
        // Process voice commands
        this.processVoiceCommand(command);
    }
}
```

## 🎤 **CLI Syntax for AR/VR Interactions**

### **Object Management Commands**

#### **Staging Objects**
```bash
# Basic object staging
-arx stage pipe_14 --position "41.52,12.03,3.8" --rotation "0,45,0"

# Staging with metadata
-arx stage pipe_14 \
  --position "41.52,12.03,3.8" \
  --rotation "0,45,0" \
  --specifications '{"diameter":"2.5 inches","material":"copper"}' \
  --notes "Install with 2% slope for drainage"

# Staging multiple objects
-arx stage batch \
  --objects "pipe_14,pipe_15,valve_03" \
  --template "plumbing_layout_001"

# Staging with voice command
-arx voice "Stage pipe 14 at position 41.52, 12.03, 3.8"
```

#### **Object Confirmation**
```bash
# Basic confirmation
-arx confirm pipe_14

# Confirmation with metadata
-arx confirm pipe_14 \
  --method "AR" \
  --confidence 0.95 \
  --notes "Position matches design specifications"

# Voice confirmation
-arx voice "Confirm pipe 14 placement"

# Batch confirmation
-arx confirm batch \
  --objects "pipe_14,pipe_15,valve_03" \
  --method "AR"
```

#### **Object Rejection**
```bash
# Basic rejection
-arx reject pipe_14 --reason "Position conflicts with existing pipe"

# Rejection with details
-arx reject pipe_14 \
  --reason "Position conflicts with existing pipe" \
  --suggested_position "42.1,12.03,3.8" \
  --priority "high"

# Voice rejection
-arx voice "Reject pipe 14 placement"
```

#### **Object Updates**
```bash
# Update position
-arx update pipe_14 --position "42.1,12.03,3.8"

# Update rotation
-arx update pipe_14 --rotation "0,90,0"

# Update metadata
-arx update pipe_14 \
  --specifications '{"diameter":"3.0 inches"}' \
  --notes "Updated to larger diameter"

# Update state
-arx update pipe_14 --state "installed" --timestamp "2025-07-31T14:16:27Z"
```

### **Scene Management Commands**

#### **Scene Loading**
```bash
# Load specific scene
-arx scene load "mechanical_room_a"

# Load scene with options
-arx scene load "mechanical_room_a" \
  --scale "1.0" \
  --offset "0,0,0" \
  --layers "plumbing,electrical,structural"

# Load scene by coordinates
-arx scene load coordinates \
  --x "41.52" \
  --y "12.03" \
  --z "3.8" \
  --radius "10.0"
```

#### **Scene Saving**
```bash
# Save current scene
-arx scene save "current_layout"

# Save with metadata
-arx scene save "current_layout" \
  --description "Updated plumbing layout" \
  --tags "plumbing,mechanical_room" \
  --version "2.1"

# Save as template
-arx scene save template "plumbing_layout_001" \
  --description "Standard plumbing layout template"
```

#### **Scene Synchronization**
```bash
# Force sync
-arx scene sync --force

# Sync with specific project
-arx scene sync --project "construction_project_001"

# Sync with conflict resolution
-arx scene sync --resolve-conflicts "auto"

# Sync with backup
-arx scene sync --backup "before_sync_001"
```

### **Collaboration Commands**

#### **Session Management**
```bash
# Join session
-arx join "session_xyz" --role "technician"

# Join with permissions
-arx join "session_xyz" \
  --role "technician" \
  --permissions "stage,confirm,view" \
  --project "construction_project_001"

# Leave session
-arx leave "session_xyz"

# List active sessions
-arx sessions list

# Session details
-arx sessions info "session_xyz"
```

#### **Object Sharing**
```bash
# Share object with user
-arx share "pipe_14" --with "user_221"

# Share with permissions
-arx share "pipe_14" \
  --with "user_221" \
  --permissions "view,confirm" \
  --expires "2025-08-01T00:00:00Z"

# Share multiple objects
-arx share batch \
  --objects "pipe_14,pipe_15,valve_03" \
  --with "user_221,user_222"

# Revoke sharing
-arx share revoke "pipe_14" --with "user_221"
```

### **Voice Command Integration**

#### **Voice Command Syntax**
```bash
# Enable voice commands
-arx voice enable

# Disable voice commands
-arx voice disable

# Register custom voice command
-arx voice register "place pipe" --action "stage pipe_14"

# List registered commands
-arx voice list

# Voice command examples
-arx voice "Place pipe 14 at position 41.52, 12.03, 3.8"
-arx voice "Confirm pipe 14 placement"
-arx voice "Reject pipe 14 placement"
-arx voice "Show pipe 14 details"
-arx voice "Load mechanical room scene"
-arx voice "Save current layout"
-arx voice "Join session xyz as technician"
```

### **Advanced Commands**

#### **Batch Operations**
```bash
# Batch stage objects
-arx batch stage \
  --file "objects.json" \
  --template "plumbing_layout" \
  --validate

# Batch confirm objects
-arx batch confirm \
  --objects "pipe_14,pipe_15,valve_03" \
  --method "AR" \
  --confidence 0.95

# Batch update objects
-arx batch update \
  --objects "pipe_14,pipe_15" \
  --position "42.1,12.03,3.8" \
  --rotation "0,90,0"
```

#### **Template Management**
```bash
# Create template
-arx template create "plumbing_layout_001" \
  --objects "pipe_14,pipe_15,valve_03" \
  --description "Standard plumbing layout"

# Apply template
-arx template apply "plumbing_layout_001" \
  --position "41.52,12.03,3.8" \
  --scale "1.0"

# List templates
-arx template list

# Template details
-arx template info "plumbing_layout_001"
```

#### **Analytics and Reporting**
```bash
# Generate placement report
-arx report placement \
  --project "construction_project_001" \
  --date-range "2025-07-01,2025-07-31" \
  --format "json"

# Generate accuracy report
-arx report accuracy \
  --objects "pipe_14,pipe_15,valve_03" \
  --tolerance "1cm"

# Generate collaboration report
-arx report collaboration \
  --session "session_xyz" \
  --users "user_221,user_222"
```

## 🔧 **SDK Configuration**

### **XR Configuration Options**
```typescript
interface XRConfig {
  platform: XRPlatform;           // 'Unity' | 'iOS' | 'Android' | 'WebXR'
  deviceType: XRDeviceType;        // 'VR' | 'AR' | 'Mixed'
  projectId: string;               // Arxos project identifier
  apiKey?: string;                 // API key for authentication
  endpoint?: string;               // Custom API endpoint
  syncInterval?: number;           // Sync interval in milliseconds
  voiceEnabled?: boolean;          // Enable voice commands
  offlineMode?: boolean;           // Enable offline mode
  debugMode?: boolean;             // Enable debug logging
}
```

### **Event Handlers**
```typescript
interface ObjectUpdateHandler {
  (object: ArxObject): void;
}

interface SessionHandler {
  (session: XRSession): void;
}

interface VoiceCommandHandler {
  (command: string, confidence: number): void;
}

interface ErrorHandler {
  (error: XRError): void;
}
```

## 📋 **Implementation Examples**

### **Unity Integration Example**
```csharp
// Complete Unity integration example
public class ArxosXRIntegration : MonoBehaviour
{
    [SerializeField] private string projectId = "construction_project_001";
    [SerializeField] private bool enableVoiceCommands = true;

    private ArxosXRSDK xrSDK;
    private ArxObjectManager objectManager;

    async void Start()
    {
        // Initialize SDK
        xrSDK = new ArxosXRSDK();
        await xrSDK.Initialize(new XRConfig
        {
            Platform = XRPlatform.Unity,
            DeviceType = XRDeviceType.VR,
            ProjectId = projectId,
            VoiceEnabled = enableVoiceCommands
        });

        // Initialize object manager
        objectManager = new ArxObjectManager();

        // Register event handlers
        xrSDK.OnObjectUpdate += HandleObjectUpdate;
        xrSDK.OnVoiceCommand += HandleVoiceCommand;

        Debug.Log("Arxos XR integration initialized");
    }

    public async void StagePipe(string pipeId, Vector3 position, Quaternion rotation)
    {
        var arxObject = new ArxObject
        {
            Id = pipeId,
            Type = "pipe",
            Position = position,
            Rotation = rotation,
            Status = "proposed"
        };

        try
        {
            var stagedObject = await xrSDK.StageObject(arxObject);
            objectManager.AddStagedObject(stagedObject);
            Debug.Log($"Pipe {pipeId} staged successfully");
        }
        catch (Exception ex)
        {
            Debug.LogError($"Failed to stage pipe {pipeId}: {ex.Message}");
        }
    }

    public async void ConfirmPipe(string pipeId)
    {
        try
        {
            var result = await xrSDK.ConfirmObject(pipeId);
            objectManager.UpdateObjectState(pipeId, "installed");
            Debug.Log($"Pipe {pipeId} confirmed successfully");
        }
        catch (Exception ex)
        {
            Debug.LogError($"Failed to confirm pipe {pipeId}: {ex.Message}");
        }
    }

    private void HandleObjectUpdate(ArxObject arxObject)
    {
        // Update Unity scene
        objectManager.UpdateObjectInScene(arxObject);
    }

    private void HandleVoiceCommand(string command)
    {
        Debug.Log($"Voice command received: {command}");
        // Process voice command
        ProcessVoiceCommand(command);
    }

    private void ProcessVoiceCommand(string command)
    {
        // Parse and execute voice commands
        if (command.Contains("stage") && command.Contains("pipe"))
        {
            // Extract pipe ID and position from voice command
            var pipeId = ExtractPipeId(command);
            var position = ExtractPosition(command);
            StagePipe(pipeId, position, Quaternion.identity);
        }
        else if (command.Contains("confirm"))
        {
            var pipeId = ExtractPipeId(command);
            ConfirmPipe(pipeId);
        }
    }
}
```

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Status**: Ready for Implementation
