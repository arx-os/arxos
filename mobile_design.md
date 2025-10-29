# ArxOS Mobile: AR + Terminal Hybrid View Design

**Version:** 1.0  
**Date:** December 2024  
**Status:** Design Specification - Ready for Implementation

---

## Overview

This document specifies the design and implementation of an AR + Terminal hybrid view that combines the AR camera view with a semi-transparent terminal overlay. This allows users to run terminal commands while simultaneously viewing and interacting with AR-detected equipment in real-time.

### Design Goals

1. **Unified Experience**: Single screen combining AR scanning and terminal interaction
2. **Contextual Command Execution**: Run commands that interact with AR-detected equipment
3. **Adjustable Visibility**: User-controlled terminal opacity to balance readability with AR visibility
4. **Real-time Integration**: Terminal commands can query and modify AR-detected equipment
5. **Performance**: Smooth operation with AR processing running in background

---

## Architecture

### Component Layers

```
┌─────────────────────────────────────────────────────────┐
│  UI Layer (SwiftUI / Jetpack Compose)                  │
│  - ARTerminalView / ARTerminalScreen                    │
│  - Opacity Control UI                                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  View Model / State Management                          │
│  - Terminal State (commands, output)                   │
│  - AR State (detected equipment, scanning)             │
│  - UI State (opacity, toggle states)                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  Service Layer                                         │
│  - TerminalService (command execution)                 │
│  - ARService (equipment detection)                      │
│  - SyncService (coordinate AR + Terminal data)          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  FFI Layer (Rust Core)                                  │
│  - Command execution via FFI                            │
│  - AR data processing                                   │
│  - Pending equipment management                         │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Types Command → Terminal Service → FFI → Rust Core
                                                      │
                                                      ▼
AR Detects Equipment → AR Service → FFI → Rust Core (pending)
                                                      │
                                                      ▼
                                                    Sync
                                                      │
                                                      ▼
Terminal Commands can query/confirm AR detections ←──┘
```

---

## iOS Implementation (SwiftUI)

### File Structure

```
ios/ArxOSMobile/ArxOSMobile/
├── Views/
│   ├── ARTerminalView.swift          # Main hybrid view
│   ├── ARViewContainer.swift         # Existing AR container
│   └── Components/
│       ├── TerminalOverlay.swift     # Terminal UI component
│       └── OpacityControl.swift      # Opacity slider
└── ViewModels/
    └── ARTerminalViewModel.swift     # State management
```

### Core Component: ARTerminalView

```swift
import SwiftUI
import ARKit

struct ARTerminalView: View {
    // MARK: - State
    @StateObject private var viewModel = ARTerminalViewModel()
    @State private var terminalOpacity: Double = 0.7
    @State private var showTerminal: Bool = true
    @State private var terminalMode: TerminalMode = .overlay
    
    // MARK: - Body
    var body: some View {
        ZStack {
            // Background: AR Camera View
            ARViewContainer(
                detectedEquipment: $viewModel.detectedEquipment,
                isScanning: $viewModel.isScanning
            )
            .ignoresSafeArea()
            
            // Foreground: Terminal Overlay (conditionally visible)
            if showTerminal {
                VStack(spacing: 0) {
                    // Terminal Output Area
                    TerminalOverlay(
                        outputLines: $viewModel.outputLines,
                        opacity: terminalOpacity,
                        mode: terminalMode
                    )
                    
                    Spacer()
                    
                    // Command Input Area
                    TerminalInput(
                        commandText: $viewModel.commandText,
                        onExecute: { command in
                            viewModel.executeCommand(command)
                        },
                        opacity: min(terminalOpacity + 0.1, 0.95)
                    )
                }
                .transition(.opacity)
            }
            
            // Controls Overlay
            VStack {
                HStack {
                    Spacer()
                    ControlPanel(
                        terminalOpacity: $terminalOpacity,
                        showTerminal: $showTerminal,
                        terminalMode: $terminalMode
                    )
                }
                Spacer()
            }
            .padding()
        }
        .onChange(of: viewModel.detectedEquipment) { equipment in
            // Auto-update terminal when new equipment detected
            handleNewEquipmentDetected(equipment)
        }
    }
    
    // MARK: - Helpers
    private func handleNewEquipmentDetected(_ equipment: [DetectedEquipment]) {
        if let latest = equipment.last {
            viewModel.addOutput(
                "🔍 AR Detected: \(latest.name) (\(latest.type))"
            )
        }
    }
}
```

### Terminal Overlay Component

```swift
struct TerminalOverlay: View {
    @Binding var outputLines: [String]
    let opacity: Double
    let mode: TerminalMode
    
    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 2) {
                    ForEach(Array(outputLines.enumerated()), id: \.offset) { index, line in
                        Text(line)
                            .font(.system(.body, design: .monospaced))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .id(index)
                    }
                }
                .padding()
            }
            .background(
                Color.black.opacity(opacity)
            )
            .cornerRadius(12)
            .padding(.horizontal)
            .frame(
                maxHeight: mode == .overlay ? 300 : .infinity
            )
            .onChange(of: outputLines.count) { _ in
                withAnimation {
                    proxy.scrollTo(outputLines.count - 1, anchor: .bottom)
                }
            }
        }
    }
}

enum TerminalMode {
    case overlay      // Semi-transparent overlay (default)
    case split        // Split screen (terminal bottom half)
    case minimized    // Minimized to small widget
}
```

### Terminal Input Component

```swift
struct TerminalInput: View {
    @Binding var commandText: String
    let onExecute: (String) -> Void
    let opacity: Double
    
    var body: some View {
        HStack {
            Text("arx$")
                .font(.system(.body, design: .monospaced))
                .foregroundColor(.green)
            
            TextField("Enter command...", text: $commandText)
                .font(.system(.body, design: .monospaced))
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .onSubmit {
                    executeCommand()
                }
            
            Button(action: executeCommand) {
                Image(systemName: "play.fill")
                    .foregroundColor(.blue)
            }
            .disabled(commandText.isEmpty)
        }
        .padding()
        .background(
            Color.black.opacity(opacity)
        )
        .cornerRadius(12)
        .padding()
    }
    
    private func executeCommand() {
        guard !commandText.isEmpty else { return }
        onExecute(commandText)
        commandText = ""
    }
}
```

### Control Panel

```swift
struct ControlPanel: View {
    @Binding var terminalOpacity: Double
    @Binding var showTerminal: Bool
    @Binding var terminalMode: TerminalMode
    
    var body: some View {
        VStack(spacing: 12) {
            // Toggle Terminal Visibility
            Button(action: {
                withAnimation {
                    showTerminal.toggle()
                }
            }) {
                Image(systemName: showTerminal ? "eye.slash" : "eye")
                    .foregroundColor(.white)
                    .padding(8)
                    .background(Color.black.opacity(0.6))
                    .clipShape(Circle())
            }
            
            if showTerminal {
                // Opacity Control
                VStack(spacing: 4) {
                    Text("Opacity")
                        .font(.caption)
                        .foregroundColor(.white)
                    
                    Slider(
                        value: $terminalOpacity,
                        in: 0.2...0.9,
                        step: 0.05
                    )
                    .frame(width: 100)
                    .accentColor(.blue)
                    
                    Text("\(Int(terminalOpacity * 100))%")
                        .font(.caption2)
                        .foregroundColor(.white)
                    
                    // Terminal Mode Toggle
                    Picker("Mode", selection: $terminalMode) {
                        Text("Overlay").tag(TerminalMode.overlay)
                        Text("Split").tag(TerminalMode.split)
                        Text("Min").tag(TerminalMode.minimized)
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 120)
                }
                .padding(8)
                .background(Color.black.opacity(0.6))
                .cornerRadius(8)
                .transition(.opacity)
            }
        }
    }
}
```

### View Model

```swift
import Combine

@MainActor
class ARTerminalViewModel: ObservableObject {
    @Published var outputLines: [String] = [
        "ArxOS AR Terminal - Git for Buildings",
        "Type 'help' for available commands",
        "AR scanning is active in background..."
    ]
    @Published var commandText: String = ""
    @Published var detectedEquipment: [DetectedEquipment] = []
    @Published var isScanning: Bool = false
    @Published var isExecuting: Bool = false
    
    private let terminalService = TerminalService()
    private let arService = ARService()
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        setupSubscriptions()
    }
    
    func executeCommand(_ command: String) {
        guard !command.isEmpty else { return }
        
        isExecuting = true
        outputLines.append("arx$ \(command)")
        
        terminalService.executeCommand(command) { [weak self] result in
            Task { @MainActor in
                switch result {
                case .success(let output):
                    if !output.isEmpty {
                        self?.outputLines.append(output)
                    }
                case .failure(let error):
                    self?.outputLines.append("Error: \(error.localizedDescription)")
                }
                self?.isExecuting = false
            }
        }
    }
    
    func addOutput(_ line: String) {
        outputLines.append(line)
    }
    
    private func setupSubscriptions() {
        // Subscribe to AR equipment detection updates
        arService.$detectedEquipment
            .sink { [weak self] equipment in
                self?.detectedEquipment = equipment
            }
            .store(in: &cancellables)
    }
}
```

---

## Android Implementation (Jetpack Compose)

### File Structure

```
android/app/src/main/java/com/arxos/mobile/
├── ui/
│   ├── screens/
│   │   └── ARTerminalScreen.kt          # Main hybrid view
│   └── components/
│       ├── TerminalOverlay.kt           # Terminal UI component
│       ├── TerminalInput.kt             # Input component
│       └── OpacityControl.kt            # Control panel
└── viewmodel/
    └── ARTerminalViewModel.kt           # State management
```

### Core Component: ARTerminalScreen

```kotlin
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ARTerminalScreen() {
    val viewModel: ARTerminalViewModel = viewModel()
    
    var terminalOpacity by remember { mutableStateOf(0.7f) }
    var showTerminal by remember { mutableStateOf(true) }
    var terminalMode by remember { mutableStateOf(TerminalMode.Overlay) }
    
    // Observe state
    val outputLines by viewModel.outputLines.collectAsState()
    val commandText by viewModel.commandText.collectAsState()
    val detectedEquipment by viewModel.detectedEquipment.collectAsState()
    val isScanning by viewModel.isScanning.collectAsState()
    
    Box(modifier = Modifier.fillMaxSize()) {
        // Background: AR Camera View
        ARViewContainer(
            modifier = Modifier.fillMaxSize(),
            detectedEquipment = detectedEquipment,
            onEquipmentDetected = { equipment ->
                viewModel.handleEquipmentDetected(equipment)
            },
            isScanning = isScanning
        )
        
        // Foreground: Terminal Overlay
        if (showTerminal) {
            Column(
                modifier = Modifier.fillMaxSize()
            ) {
                // Terminal Output Area
                TerminalOverlay(
                    outputLines = outputLines,
                    opacity = terminalOpacity,
                    mode = terminalMode
                )
                
                Spacer(modifier = Modifier.weight(1f))
                
                // Command Input Area
                TerminalInput(
                    commandText = commandText,
                    onCommandChange = { viewModel.updateCommandText(it) },
                    onExecute = { command ->
                        viewModel.executeCommand(command)
                    },
                    opacity = (terminalOpacity + 0.1f).coerceAtMost(0.95f)
                )
            }
        }
        
        // Control Panel (Top Right)
        Column(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(16.dp)
        ) {
            ControlPanel(
                terminalOpacity = terminalOpacity,
                onOpacityChange = { terminalOpacity = it },
                showTerminal = showTerminal,
                onToggleTerminal = { showTerminal = !showTerminal },
                terminalMode = terminalMode,
                onModeChange = { terminalMode = it }
            )
        }
        
        // Auto-update when new equipment detected
        LaunchedEffect(detectedEquipment.size) {
            if (detectedEquipment.isNotEmpty()) {
                val latest = detectedEquipment.last()
                viewModel.addOutput(
                    "🔍 AR Detected: ${latest.name} (${latest.type})"
                )
            }
        }
    }
}

enum class TerminalMode {
    Overlay,     // Semi-transparent overlay (default)
    Split,       // Split screen (terminal bottom half)
    Minimized    // Minimized to small widget
}
```

### Terminal Overlay Component

```kotlin
@Composable
fun TerminalOverlay(
    outputLines: List<String>,
    opacity: Float,
    mode: TerminalMode
) {
    val listState = rememberLazyListState()
    
    // Auto-scroll to bottom
    LaunchedEffect(outputLines.size) {
        if (outputLines.isNotEmpty()) {
            listState.animateScrollToItem(outputLines.size - 1)
        }
    }
    
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .then(
                when (mode) {
                    TerminalMode.Overlay -> Modifier.padding(16.dp)
                    TerminalMode.Split -> Modifier
                        .weight(1f)
                        .fillMaxWidth()
                    TerminalMode.Minimized -> Modifier
                        .height(150.dp)
                        .padding(16.dp)
                }
            ),
        colors = CardDefaults.cardColors(
            containerColor = Color.Black.copy(alpha = opacity)
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        LazyColumn(
            state = listState,
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            itemsIndexed(outputLines) { index, line ->
                Text(
                    text = line,
                    color = Color.White,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
    }
}
```

### Terminal Input Component

```kotlin
@Composable
fun TerminalInput(
    commandText: String,
    onCommandChange: (String) -> Unit,
    onExecute: (String) -> Unit,
    opacity: Float
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color.Black.copy(alpha = opacity)
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "arx$",
                color = Color.Green,
                fontFamily = FontFamily.Monospace,
                modifier = Modifier.padding(end = 8.dp)
            )
            
            OutlinedTextField(
                value = commandText,
                onValueChange = onCommandChange,
                modifier = Modifier.weight(1f),
                placeholder = { Text("Enter command...") },
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                )
            )
            
            Spacer(modifier = Modifier.width(8.dp))
            
            FloatingActionButton(
                onClick = {
                    if (commandText.isNotEmpty()) {
                        onExecute(commandText.trim())
                    }
                },
                modifier = Modifier.size(48.dp)
            ) {
                Icon(
                    Icons.Default.PlayArrow,
                    contentDescription = "Execute"
                )
            }
        }
    }
}
```

### Control Panel

```kotlin
@Composable
fun ControlPanel(
    terminalOpacity: Float,
    onOpacityChange: (Float) -> Unit,
    showTerminal: Boolean,
    onToggleTerminal: () -> Unit,
    terminalMode: TerminalMode,
    onModeChange: (TerminalMode) -> Unit
) {
    Column(
        horizontalAlignment = Alignment.End,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Toggle Terminal Visibility
        IconButton(
            onClick = onToggleTerminal,
            modifier = Modifier
                .background(
                    Color.Black.copy(alpha = 0.6f),
                    CircleShape
                )
        ) {
            Icon(
                if (showTerminal) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                contentDescription = if (showTerminal) "Hide Terminal" else "Show Terminal",
                tint = Color.White
            )
        }
        
        if (showTerminal) {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = Color.Black.copy(alpha = 0.6f)
                ),
                modifier = Modifier.padding(8.dp)
            ) {
                Column(
                    modifier = Modifier.padding(12.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Opacity",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White
                    )
                    
                    Slider(
                        value = terminalOpacity,
                        onValueChange = onOpacityChange,
                        valueRange = 0.2f..0.9f,
                        modifier = Modifier.width(120.dp)
                    )
                    
                    Text(
                        text = "${(terminalOpacity * 100).toInt()}%",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    // Terminal Mode Picker
                    Row {
                        IconButton(
                            onClick = { onModeChange(TerminalMode.Overlay) },
                            modifier = Modifier.background(
                                if (terminalMode == TerminalMode.Overlay) 
                                    MaterialTheme.colorScheme.primary.copy(alpha = 0.5f)
                                else Color.Transparent,
                                CircleShape
                            )
                        ) {
                            Icon(
                                Icons.Default.Layers,
                                contentDescription = "Overlay Mode",
                                tint = if (terminalMode == TerminalMode.Overlay) 
                                    Color.White else Color.Gray
                            )
                        }
                        
                        IconButton(
                            onClick = { onModeChange(TerminalMode.Split) },
                            modifier = Modifier.background(
                                if (terminalMode == TerminalMode.Split) 
                                    MaterialTheme.colorScheme.primary.copy(alpha = 0.5f)
                                else Color.Transparent,
                                CircleShape
                            )
                        ) {
                            Icon(
                                Icons.Default.ViewSplit,
                                contentDescription = "Split Mode",
                                tint = if (terminalMode == TerminalMode.Split) 
                                    Color.White else Color.Gray
                            )
                        }
                    }
                }
            }
        }
    }
}
```

### View Model

```kotlin
class ARTerminalViewModel(
    private val terminalService: TerminalService,
    private val arService: ARService
) : ViewModel() {
    
    private val _outputLines = MutableStateFlow(listOf(
        "ArxOS AR Terminal - Git for Buildings",
        "Type 'help' for available commands",
        "AR scanning is active in background..."
    ))
    val outputLines: StateFlow<List<String>> = _outputLines.asStateFlow()
    
    private val _commandText = MutableStateFlow("")
    val commandText: StateFlow<String> = _commandText.asStateFlow()
    
    private val _detectedEquipment = MutableStateFlow<List<DetectedEquipment>>(emptyList())
    val detectedEquipment: StateFlow<List<DetectedEquipment>> = _detectedEquipment.asStateFlow()
    
    private val _isScanning = MutableStateFlow(false)
    val isScanning: StateFlow<Boolean> = _isScanning.asStateFlow()
    
    init {
        observeARUpdates()
    }
    
    fun executeCommand(command: String) {
        if (command.isBlank()) return
        
        viewModelScope.launch {
            _outputLines.value += "arx$ $command"
            
            try {
                val result = terminalService.executeCommand(command)
                if (result.output.isNotEmpty()) {
                    _outputLines.value += result.output
                }
            } catch (e: Exception) {
                _outputLines.value += "Error: ${e.message}"
            }
        }
    }
    
    fun updateCommandText(text: String) {
        _commandText.value = text
    }
    
    fun addOutput(line: String) {
        _outputLines.value += line
    }
    
    fun handleEquipmentDetected(equipment: List<DetectedEquipment>) {
        _detectedEquipment.value = equipment
    }
    
    private fun observeARUpdates() {
        viewModelScope.launch {
            arService.detectedEquipment.collect { equipment ->
                _detectedEquipment.value = equipment
                
                // Auto-update terminal when new equipment detected
                if (equipment.isNotEmpty()) {
                    val latest = equipment.last()
                    addOutput(
                        "🔍 AR Detected: ${latest.name} (${latest.type})"
                    )
                }
            }
        }
    }
}
```

---

## Terminal Commands for AR Integration

### New Commands

1. **`ar pending list [--floor <level>]`**
   - List all pending AR-detected equipment
   - Optional floor filtering

2. **`ar pending confirm <id> [--commit]`**
   - Confirm a pending equipment item
   - Optionally commit to Git

3. **`ar pending batch <ids...> [--commit]`**
   - Batch confirm multiple pending items

4. **`equipment list --ar`**
   - Filter equipment list to AR-detected items only

5. **`equipment confirm <id>`**
   - Quick confirm for AR-detected equipment (if ID is from AR scan)

### Enhanced Existing Commands

- **`equipment list`** - Show AR-detected items with `[AR]` badge
- **`status`** - Include AR scan status and pending count

---

## Technical Specifications

### Opacity Ranges

| Component | Min | Max | Default | Increment |
|-----------|-----|-----|---------|-----------|
| Terminal Output | 0.2 | 0.9 | 0.7 | 0.05 |
| Terminal Input | +0.1 from output | 0.95 | 0.8 | 0.05 |

### Performance Targets

- **Frame Rate**: Maintain 30+ FPS with AR + Terminal active
- **Terminal Rendering**: < 16ms per frame
- **AR Detection**: < 100ms latency for new equipment
- **Command Execution**: < 500ms response time

### Memory Considerations

- Terminal output limited to 1000 lines (scroll oldest out)
- AR detection buffer limited to 100 items
- Terminate AR session when app backgrounded

---

## User Experience Flow

### Initial Load

1. User opens AR Terminal view
2. AR camera starts automatically
3. Terminal overlay appears with default opacity
4. Background AR scanning begins

### Command Execution While Scanning

1. User sees equipment detected in AR (tags appear)
2. Terminal auto-updates: "🔍 AR Detected: VAV-301 (HVAC)"
3. User types: `ar pending list`
4. Terminal shows list of pending equipment
5. User types: `ar pending confirm pending_123 --commit`
6. Equipment confirmed and committed

### Opacity Adjustment

1. User drags opacity slider
2. Terminal becomes more/less transparent
3. AR visibility adjusts in real-time
4. Setting persisted for next session

---

## Integration Points

### With Existing Components

1. **TerminalView.swift** → **ARTerminalView.swift**
   - Reuse TerminalService logic
   - Adapt terminal UI for overlay mode

2. **ARScanView.swift** → **ARViewContainer.swift**
   - Reuse AR detection logic
   - Extract AR component for background operation

3. **ArxOSCoreFFI.swift**
   - Extend with AR-specific commands
   - Add pending equipment management functions

4. **PendingEquipmentManager** (Rust)
   - Already supports pending workflow
   - Integrate with terminal commands

---

## Implementation Phases

### Phase 1: Basic Hybrid View (Week 1-2)
- [ ] Create ARTerminalView/ARTerminalScreen
- [ ] Implement ZStack/Box layout with AR background
- [ ] Add basic terminal overlay with fixed opacity
- [ ] Ensure AR continues working behind terminal

### Phase 2: Controls & Interaction (Week 2-3)
- [ ] Implement opacity slider
- [ ] Add terminal visibility toggle
- [ ] Add terminal mode switching (overlay/split/minimized)
- [ ] Persist opacity setting

### Phase 3: Command Integration (Week 3-4)
- [ ] Add `ar pending list` command
- [ ] Add `ar pending confirm` command
- [ ] Add `ar pending batch` command
- [ ] Enhance existing commands with AR badges

### Phase 4: Real-time Sync (Week 4-5)
- [ ] Auto-update terminal when AR detects equipment
- [ ] Sync terminal commands with AR state
- [ ] Add command shortcuts for AR-detected items
- [ ] Performance optimization

### Phase 5: Polish & Testing (Week 5-6)
- [ ] UI/UX refinements
- [ ] Performance testing
- [ ] Edge case handling
- [ ] Documentation

---

## Testing Considerations

### Unit Tests

- Terminal opacity calculations
- Command parsing with AR context
- State management transitions

### Integration Tests

- AR detection → Terminal update flow
- Command execution with AR state
- Memory management with both systems active

### Performance Tests

- Frame rate with AR + Terminal
- Memory usage over time
- Command response time under load

### User Acceptance Tests

- Opacity adjustment feels natural
- Terminal remains readable at various opacities
- AR detection not impacted by terminal overlay
- Commands execute correctly with AR context

---

## Future Enhancements

1. **AR Tags as Command Shortcuts**: Tap AR tag → auto-fill equipment ID in terminal
2. **Voice Commands**: "Confirm VAV-301" → executed in terminal
3. **Split View Drag**: Drag divider to adjust split screen proportions
4. **Command History Integration**: Show AR context in command history
5. **Custom Terminal Themes**: Adjust colors/opacity per theme
6. **Gesture Controls**: Swipe to adjust opacity, double-tap to toggle
7. **Haptic Feedback**: Tactile response when equipment detected
8. **Offline Mode**: Queue commands when network unavailable

---

## Open Questions

1. **Terminal Scroll Behavior**: Should terminal auto-scroll pause when user manually scrolls?
2. **AR Tag Interaction**: Can users tap AR tags to execute commands?
3. **Command Suggestions**: Should terminal suggest commands based on AR context?
4. **Multi-Device Sync**: If using on multiple devices, sync AR + Terminal state?
5. **Accessibility**: How to make hybrid view accessible (screen readers, etc.)?

---

## Conclusion

The AR + Terminal hybrid view provides a powerful unified interface for building management. By combining real-time AR detection with terminal command execution, users can efficiently work with building data in a single, contextually-aware interface.

**Next Steps:**
1. Review this specification with engineering team
2. Prioritize implementation phases
3. Create detailed technical tickets
4. Begin Phase 1 implementation

---

**Document Status:** Ready for Engineering Review  
**Last Updated:** December 2024  
**Next Review:** After Phase 1 Completion

