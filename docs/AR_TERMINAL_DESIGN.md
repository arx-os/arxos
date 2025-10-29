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

## Field User Workflow: Simple Commands in AR+Terminal View

### Problem Statement

**Field User (Non-Technical):**
- Performs AR scans and equipment markup in buildings
- Doesn't know complex CLI commands
- Needs simple, intuitive commands
- Just wants to scan equipment and add notes

**Power User (Technical):**
- Reviews field user submissions
- Uses full CLI command set for integration
- Has full technical control
- Integrates approved markups into building repo

### Solution: Single AR+Terminal Interface with Simple Commands

**One app for everyone!** The AR+Terminal hybrid view supports both:
- **Simple commands** for field users (displayed prominently, with autocomplete)
- **Full CLI** for power users (all commands available)

Field users type simple commands like `add note` or `submit`, power users use full syntax. Both work in the same terminal overlay.

---

## Enhanced AR+Terminal View for Field Users

### Design Philosophy

**One Interface, Two User Levels:**

Field users see:
- Simple command suggestions at bottom of terminal
- Command autocomplete with explanations
- AR tags are tappable → auto-fills commands
- Visual feedback for each step

Power users see:
- Full terminal with all commands
- Can type any CLI command
- Advanced options available

**Same view, smart command assistance for non-technical users.**

### Enhanced Terminal Input Component

#### 1. Smart Command Input with Suggestions

**Enhancement to existing `ARTerminalView`:**

```swift
// Enhanced Terminal Input with Smart Suggestions
struct SmartTerminalInput: View {
    @Binding var commandText: String
    @Binding var detectedEquipment: [DetectedEquipment]
    @Binding var selectedEquipment: DetectedEquipment?
    let onExecute: (String) -> Void
    let opacity: Double
    
    @State private var suggestions: [CommandSuggestion] = []
    @State private var showSuggestions = true
    @FocusState private var isFocused: Bool
    
    var body: some View {
        VStack(spacing: 0) {
            // Command Input Field
            HStack {
                Text("arx$")
                    .font(.system(.body, design: .monospaced))
                    .foregroundColor(.green)
                
                TextField("Type command...", text: $commandText)
                    .font(.system(.body, design: .monospaced))
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocorrectionDisabled()
                    .onChange(of: commandText) { newValue in
                        updateSuggestions(for: newValue)
                    }
                    .onSubmit {
                        executeCommand()
                    }
                    .focused($isFocused)
                
                Button(action: executeCommand) {
                    Image(systemName: "play.fill")
                        .foregroundColor(.blue)
                }
                .disabled(commandText.isEmpty)
            }
            .padding()
            .background(Color.black.opacity(opacity))
            
            // Smart Suggestions Bar (for field users)
            if showSuggestions && suggestions.isEmpty && commandText.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(FieldUserCommands.allCases, id: \.self) { cmd in
                            SuggestionButton(cmd) {
                                commandText = cmd.terminalCommand
                                updateSuggestions(for: cmd.terminalCommand)
                            }
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical, 8)
                .background(Color.black.opacity(opacity * 0.8))
            }
            
            // Command Autocomplete (when typing)
            if !suggestions.isEmpty && !commandText.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(suggestions.prefix(3)) { suggestion in
                        AutocompleteRow(suggestion) {
                            commandText = suggestion.fullCommand
                            suggestions = []
                        }
                    }
                }
                .padding()
                .background(Color.black.opacity(opacity * 0.9))
                .cornerRadius(8)
            }
        }
        .cornerRadius(12)
        .padding()
    }
    
    private func updateSuggestions(for input: String) {
        if input.isEmpty {
            suggestions = []
            return
        }
        
        // Simple command matching for field users
        let simpleCommands = FieldUserCommands.allCases.filter { cmd in
            cmd.terminalCommand.localizedCaseInsensitiveContains(input) ||
            cmd.description.localizedCaseInsensitiveContains(input)
        }
        
        suggestions = simpleCommands.map { cmd in
            CommandSuggestion(
                command: cmd.terminalCommand,
                description: cmd.description,
                fullCommand: cmd.terminalCommand
            )
        }
        
        // Also check if user typed partial of AR tag name
        if let matchingEquipment = detectedEquipment.first(where: { eq in
            eq.name.localizedCaseInsensitiveContains(input)
        }) {
            suggestions.append(CommandSuggestion(
                command: "note \(matchingEquipment.name)",
                description: "Add note for \(matchingEquipment.name)",
                fullCommand: "note \(matchingEquipment.name) "
            ))
        }
    }
    
    private func executeCommand() {
        guard !commandText.isEmpty else { return }
        onExecute(commandText)
        commandText = ""
        suggestions = []
    }
}

// Simple commands for field users
enum FieldUserCommands: String, CaseIterable {
    case listEquipment = "list"
    case addNote = "note"
    case submit = "submit"
    case help = "help"
    
    var terminalCommand: String {
        switch self {
        case .listEquipment: return "equipment list"
        case .addNote: return "note"
        case .submit: return "pr submit"
        case .help: return "help"
        }
    }
    
    var description: String {
        switch self {
        case .listEquipment: return "List detected equipment"
        case .addNote: return "Add note to equipment"
        case .submit: return "Submit for review"
        case .help: return "Show help"
        }
    }
}

struct CommandSuggestion: Identifiable {
    let id = UUID()
    let command: String
    let description: String
    let fullCommand: String
}

struct SuggestionButton: View {
    let cmd: FieldUserCommands
    let action: () -> Void
    
    init(_ cmd: FieldUserCommands, action: @escaping () -> Void) {
        self.cmd = cmd
        self.action = action
    }
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Text(cmd.description)
                    .font(.caption)
                    .foregroundColor(.white)
                Text(cmd.terminalCommand)
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundColor(.green.opacity(0.8))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.blue.opacity(0.3))
            .cornerRadius(8)
        }
    }
}

struct AutocompleteRow: View {
    let suggestion: CommandSuggestion
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack {
                Text(suggestion.command)
                    .font(.system(.body, design: .monospaced))
                    .foregroundColor(.green)
                
                Text("→ \(suggestion.description)")
                    .font(.caption)
                    .foregroundColor(.gray)
                
                Spacer()
            }
            .padding(.vertical, 4)
        }
    }
}
```

#### 2. Tap AR Tags to Auto-Fill Commands

```swift
struct NoteInputSheet: View {
    let equipment: DetectedEquipment
    let existingNote: String?
    let onSave: (String) -> Void
    let onCancel: () -> Void
    
    @State private var noteText: String
    @FocusState private var isFocused: Bool
    
    init(equipment: DetectedEquipment, existingNote: String?, onSave: @escaping (String) -> Void, onCancel: @escaping () -> Void) {
        self.equipment = equipment
        self.existingNote = existingNote
        self.onSave = onSave
        self.onCancel = onCancel
        _noteText = State(initialValue: existingNote ?? "")
    }
    
    var body: some View {
        VStack(spacing: 16) {
            // Equipment Info
            HStack {
                Image(systemName: equipment.icon)
                    .font(.title2)
                VStack(alignment: .leading) {
                    Text(equipment.name)
                        .font(.headline)
                    Text(equipment.type)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                Spacer()
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(8)
            
            // Text Input
            TextEditor(text: $noteText)
                .frame(height: 150)
                .padding(8)
                .background(Color(.systemBackground))
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color(.systemGray4), lineWidth: 1)
                )
                .focused($isFocused)
            
            // Placeholder if empty
            if noteText.isEmpty {
                VStack {
                    HStack {
                        Text("Add a note about this equipment...")
                            .foregroundColor(.secondary)
                            .padding(.leading, 12)
                            .padding(.top, 8)
                        Spacer()
                    }
                    Spacer()
                }
                .allowsHitTesting(false)
            }
            
            // Quick Suggestions (Optional - for non-technical users)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    SuggestionChip("Needs repair") {
                        noteText = "Needs repair"
                    }
                    SuggestionChip("Working fine") {
                        noteText = "Working fine"
                    }
                    SuggestionChip("Check later") {
                        noteText = "Check later"
                    }
                    SuggestionChip("Missing parts") {
                        noteText = "Missing parts"
                    }
                }
            }
            
            // Action Buttons
            HStack(spacing: 12) {
                Button("Cancel") {
                    onCancel()
                }
                .foregroundColor(.secondary)
                
                Spacer()
                
                Button("Save") {
                    onSave(noteText.trimmingCharacters(in: .whitespacesAndNewlines))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 24)
                .padding(.vertical, 12)
                .background(noteText.isEmpty ? Color.gray : Color.blue)
                .cornerRadius(8)
                .disabled(noteText.isEmpty)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(radius: 10)
        .onAppear {
            isFocused = true
        }
    }
}

struct SuggestionChip: View {
    let text: String
    let action: () -> Void
    
    init(_ text: String, action: @escaping () -> Void) {
        self.text = text
        self.action = action
    }
    
    var body: some View {
        Button(action: action) {
            Text(text)
                .font(.caption)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color(.systemGray5))
                .cornerRadius(16)
        }
    }
}
```

#### 3. AR Tag Integration with Terminal

When user taps an AR equipment tag, auto-fill terminal command:

```swift
// Enhanced EquipmentTagView with tap-to-command
struct EquipmentTagView: View {
    let equipment: DetectedEquipment
    let onTap: (DetectedEquipment) -> Void
    let onCommandFill: (String) -> Void  // New: fills terminal
    
    var body: some View {
        Button(action: {
            // Fill terminal with note command for this equipment
            onCommandFill("note \(equipment.name) ")
        }) {
            HStack {
                Image(systemName: equipment.icon)
                Text(equipment.name)
                    .font(.caption)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Color.blue.opacity(0.8))
            .foregroundColor(.white)
            .cornerRadius(16)
        }
        .simultaneousGesture(
            LongPressGesture(minimumDuration: 0.5)
                .onEnded { _ in
                    // Long press for more options
                    onTap(equipment)
                }
        )
    }
}
```

**Workflow:**
1. AR detects equipment → tag appears in AR view
2. User taps tag → terminal auto-fills: `note VAV-301 `
3. User completes note in terminal: `note VAV-301 needs filter replacement`
4. User presses Enter → command executes in terminal
5. Terminal shows: `✓ Note added for VAV-301: needs filter replacement`

**No separate UI sheets or dialogs - everything stays in terminal!**

#### 4. Simple Command Parsing (Rust Side)

```rust
// src/commands/simple.rs (new module for field user commands)

/// Handle simple field user commands
/// These are shortcuts that map to full CLI commands
pub fn handle_simple_command(input: &str) -> Result<String, Box<dyn std::error::Error>> {
    let parts: Vec<&str> = input.trim().split_whitespace().collect();
    
    if parts.is_empty() {
        return Ok(help_text());
    }
    
    match parts[0] {
        "note" | "n" => {
            // Simple: "note VAV-301 needs repair"
            // Maps to: "ar pending note --equipment VAV-301 --note 'needs repair'"
            
            if parts.len() < 3 {
                return Ok("Usage: note <equipment-name> <your note here>".to_string());
            }
            
            let equipment_name = parts[1];
            let note = parts[2..].join(" ");
            
            // Find equipment in AR detected list
            // Add note via pending equipment manager
            add_equipment_note(equipment_name, &note)?;
            
            Ok(format!("✓ Note added for {}: {}", equipment_name, note))
        }
        
        "list" | "ls" => {
            // Simple: "list"
            // Maps to: "ar pending list"
            handle_ar_pending_list()
        }
        
        "submit" | "send" => {
            // Simple: "submit"
            // Maps to: "pr submit" - creates PR from all pending items
            handle_pr_submit()
        }
        
        "help" | "h" | "?" => {
            Ok(help_text())
        }
        
        _ => {
            // Not a simple command, pass through to full CLI parser
            // This allows power users to use full commands
            Err(format!("Unknown simple command: {}. Type 'help' for simple commands, or use full CLI syntax.", parts[0]).into())
        }
    }
}

fn add_equipment_note(equipment_name: &str, note: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Implementation: Add note to pending equipment
    // This would integrate with PendingEquipmentManager
    Ok(())
}

fn handle_ar_pending_list() -> Result<String, Box<dyn std::error::Error>> {
    // Call existing ar pending list command
    // Return formatted list
    Ok("Pending equipment list...".to_string())
}

fn handle_pr_submit() -> Result<String, Box<dyn std::error::Error>> {
    // Package all pending items into PR
    // Call PR creation
    Ok("PR submitted successfully!".to_string())
}

fn help_text() -> String {
    r#"Simple Commands (Field Users):
  note <name> <text>    Add note to equipment
  list                  List detected equipment
  submit                Submit for review
  
Full CLI commands also available for power users.
Type command name (e.g., "equipment") for more options."#.to_string()
}
```

**Integration in Command Router:**

```rust
// src/commands/mod.rs
pub fn execute_command(command: Commands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        // ... existing commands ...
        
        // New: Check if it's a simple field user command first
        Commands::Simple { input } => simple::handle_simple_command(&input),
    }
}
```

---

## PR Data Structure

### Pull Request Package Format

When field user submits, create a PR branch with:

```
prs/
  └── pr_<timestamp>_<user_id>/
      ├── metadata.yaml          # PR metadata
      ├── markup.json            # AR scan data + notes
      └── README.md              # Human-readable summary
```

**metadata.yaml:**
```yaml
pr_id: "pr_1703123456_john_doe"
author: "john.doe"
building: "Main Office Building"
floor: 2
room: "Conference Room A"
submitted_at: "2024-12-20T14:30:00Z"
status: "pending"
equipment_count: 5
notes_count: 3
```

**markup.json:**
```json
{
  "session_id": "session_abc123",
  "building": "Main Office Building",
  "floor": 2,
  "room": "Conference Room A",
  "equipment": [
    {
      "id": "pending_1703123456",
      "name": "VAV-301",
      "type": "HVAC",
      "position": { "x": 10.5, "y": 8.2, "z": 2.1 },
      "confidence": 0.92,
      "detection_method": "ARKit",
      "note": "Needs filter replacement - check next maintenance cycle",
      "marked_at": "2024-12-20T14:25:00Z"
    },
    {
      "id": "pending_1703123457",
      "name": "Light Fixture L-205",
      "type": "Electrical",
      "position": { "x": 12.3, "y": 8.5, "z": 3.0 },
      "confidence": 0.88,
      "detection_method": "Manual",
      "note": "Flickering when dimmed - may need new ballast",
      "marked_at": "2024-12-20T14:27:00Z"
    }
  ]
}
```

**README.md:**
```markdown
# AR Markup Submission

**Submitted by:** john.doe  
**Date:** December 20, 2024  
**Location:** Main Office Building, Floor 2, Conference Room A

## Equipment Marked

1. **VAV-301** (HVAC)
   - Note: Needs filter replacement - check next maintenance cycle
   - Position: (10.5, 8.2, 2.1)

2. **Light Fixture L-205** (Electrical)
   - Note: Flickering when dimmed - may need new ballast
   - Position: (12.3, 8.5, 3.0)

## Review Instructions

1. Review AR scan accuracy
2. Verify equipment identification
3. Validate notes make sense
4. Confirm spatial positioning
5. Approve or request changes

## CLI Review Commands

\`\`\`bash
# View PR details
arx pr view pr_1703123456_john_doe

# Review pending equipment
arx ar pending list --pr pr_1703123456_john_doe

# Approve and merge
arx pr approve pr_1703123456_john_doe --merge

# Request changes
arx pr request-changes pr_1703123456_john_doe --comment "Please clarify equipment ID"
\`\`\`
```

---

## Power User CLI Commands

### New PR Management Commands

```bash
# List all pending PRs
arx pr list [--status pending|approved|rejected]

# View specific PR details
arx pr view <pr_id>

# Review equipment in a PR
arx pr equipment <pr_id>

# Approve PR (with optional auto-merge)
arx pr approve <pr_id> [--merge] [--commit]

# Reject PR with comment
arx pr reject <pr_id> --comment "Reason for rejection"

# Request changes on PR
arx pr request-changes <pr_id> --comment "Please clarify..."

# Merge approved PR into main building repo
arx pr merge <pr_id>

# Diff PR changes before merging
arx pr diff <pr_id>
```

### Integration with Existing Commands

```bash
# List pending equipment with PR context
arx ar pending list --pr <pr_id>

# Confirm equipment from a PR
arx ar pending confirm <pending_id> --pr <pr_id> --commit
```

---

## Android Implementation (Same Terminal Interface)

Same concept applies to Android - enhance the existing `ARTerminalScreen`:

```kotlin
// Enhanced terminal input with suggestions
@Composable
fun SmartTerminalInput(
    commandText: String,
    onCommandChange: (String) -> Void,
    onExecute: (String) -> Void,
    detectedEquipment: List<DetectedEquipment>,
    onEquipmentTap: (DetectedEquipment) -> Void,
    opacity: Float
) {
    var suggestions by remember { mutableStateOf<List<CommandSuggestion>>(emptyList()) }
    
    Column {
        // Command suggestions bar (when input is empty)
        if (commandText.isEmpty()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                FieldUserCommand.values().forEach { cmd ->
                    SuggestionChip(
                        label = cmd.description,
                        command = cmd.terminalCommand,
                        onClick = { onCommandChange(cmd.terminalCommand) }
                    )
                }
            }
        }
        
        // Terminal input with autocomplete
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("arx$", color = Color.Green, fontFamily = FontFamily.Monospace)
            
            OutlinedTextField(
                value = commandText,
                onValueChange = { text ->
                    onCommandChange(text)
                    suggestions = getSuggestions(text, detectedEquipment)
                },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Type command...") },
                singleLine = true
            )
            
            FloatingActionButton(
                onClick = { onExecute(commandText) },
                modifier = Modifier.size(48.dp)
            ) {
                Icon(Icons.Default.PlayArrow, null)
            }
        }
        
        // Autocomplete suggestions
        if (suggestions.isNotEmpty()) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp)
            ) {
                suggestions.take(3).forEach { suggestion ->
                    AutocompleteRow(suggestion) {
                        onCommandChange(suggestion.fullCommand)
                    }
                }
            }
        }
    }
}

enum class FieldUserCommand(val terminalCommand: String, val description: String) {
    LIST("equipment list", "List equipment"),
    NOTE("note", "Add note"),
    SUBMIT("pr submit", "Submit for review"),
    HELP("help", "Show help")
}
```

---

## Rust FFI Extensions for PR

### New FFI Functions

```rust
// src/mobile_ffi/ffi.rs

/// Create a pull request from AR markup data
#[no_mangle]
pub unsafe extern "C" fn arxos_create_pr(
    markup_json: *const c_char,
    building_name: *const c_char
) -> *mut c_char {
    // Parse markup JSON
    // Create PR branch
    // Save PR files
    // Return PR info as JSON
}

/// Get PR status
#[no_mangle]
pub unsafe extern "C" fn arxos_get_pr_status(
    pr_id: *const c_char
) -> *mut c_char {
    // Return PR status JSON
}
```

### PR Service Implementation

```rust
// src/pr/mod.rs (new module)

pub struct PRService {
    repo: Repository,
}

impl PRService {
    pub fn create_pr(&self, markup: MarkupData) -> Result<PRInfo, Box<dyn std::error::Error>> {
        let pr_id = format!("pr_{}_{}", 
            Utc::now().timestamp(),
            markup.author.replace(" ", "_")
        );
        
        // Create PR branch
        let branch_name = format!("pr/{}", pr_id);
        self.create_pr_branch(&branch_name)?;
        
        // Write PR files
        self.write_pr_files(&pr_id, &markup)?;
        
        // Commit PR files
        self.commit_pr(&pr_id, &markup)?;
        
        Ok(PRInfo {
            pr_id: pr_id.clone(),
            branch: branch_name,
            status: PRStatus::Pending,
        })
    }
    
    fn write_pr_files(&self, pr_id: &str, markup: &MarkupData) -> Result<(), Box<dyn std::error::Error>> {
        let pr_dir = format!("prs/{}", pr_id);
        
        // Write metadata.yaml
        self.write_metadata(&pr_dir, markup)?;
        
        // Write markup.json
        self.write_markup_json(&pr_dir, markup)?;
        
        // Write README.md
        self.write_readme(&pr_dir, markup)?;
        
        Ok(())
    }
}
```

---

## Workflow Summary

### Field User Workflow (All in Terminal)

1. **Open AR+Terminal View**
   - AR camera starts automatically
   - Terminal overlay appears with suggestions

2. **Scan Equipment**
   - Point camera at equipment
   - AR auto-detects and shows tag in AR view
   - Terminal auto-updates: "🔍 AR Detected: VAV-301 (HVAC)"

3. **Add Note (Option A: Tap Tag)**
   - Tap AR equipment tag
   - Terminal auto-fills: `note VAV-301 `
   - User types note: `needs filter replacement`
   - Press Enter → Command executes

4. **Add Note (Option B: Type Command)**
   - User types: `note` or `n`
   - Autocomplete shows: `note <equipment-name> <text>`
   - User completes: `note VAV-301 needs filter replacement`
   - Press Enter → Command executes

5. **Check What's Pending**
   - User types: `list` or `ls`
   - Terminal shows all pending equipment with notes

6. **Submit PR**
   - User types: `submit` or `send`
   - Terminal shows: "Creating PR..."
   - Success: "✓ PR submitted! PR ID: pr_123456"
   - User is done!

### Power User Workflow

1. **List PRs**
   ```bash
   arx pr list
   ```

2. **Review PR**
   ```bash
   arx pr view pr_1703123456_john_doe
   arx pr equipment pr_1703123456_john_doe
   ```

3. **Approve/Reject**
   ```bash
   # Approve
   arx pr approve pr_1703123456_john_doe --merge
   
   # Or reject
   arx pr reject pr_1703123456_john_doe --comment "Invalid equipment ID"
   ```

4. **Merge** (if not auto-merged)
   ```bash
   arx pr merge pr_1703123456_john_doe
   ```

---

## Open Questions

1. **Terminal Scroll Behavior**: Should terminal auto-scroll pause when user manually scrolls?
2. **AR Tag Interaction**: Can users tap AR tags to execute commands?
3. **Command Suggestions**: Should terminal suggest commands based on AR context?
4. **Multi-Device Sync**: If using on multiple devices, sync AR + Terminal state?
5. **Accessibility**: How to make hybrid view accessible (screen readers, etc.)?
6. **PR Review UI**: Should power users have GUI option or CLI-only?
7. **PR Notifications**: How do power users get notified of new PRs?
8. **Offline PR Submission**: Queue PRs when offline, submit when online?

---

## Summary: Terminal-First Design

**Key Principle: ONE INTERFACE FOR ALL USERS**

The AR+Terminal hybrid view is the single interface for:
- **Field Users**: Simple commands with smart suggestions
- **Power Users**: Full CLI command set
- **Both**: Same view, same AR overlay, same terminal

**No mode switching, no separate UIs, no complexity.**

### Simple Commands for Field Users

Instead of learning full CLI syntax, field users type:
- `note VAV-301 needs repair` (instead of `ar pending note --equipment VAV-301 --note "needs repair"`)
- `list` (instead of `ar pending list`)
- `submit` (instead of `pr submit --all`)

**Smart assistance:**
- Command suggestions appear when terminal is empty
- Autocomplete while typing
- Tap AR tags to auto-fill commands
- All feedback in terminal output

### Power Users Unaffected

Power users can still use full CLI:
- `ar pending list --floor 2 --verbose`
- `equipment update VAV-301 --status critical --commit`
- `pr approve pr_123 --merge --commit`

**No restrictions - everything works as before.**

---

## Conclusion

The AR + Terminal hybrid view provides a powerful unified interface for building management. By combining real-time AR detection with terminal command execution, users can efficiently work with building data in a single, contextually-aware interface.

**The Field User Workflow** enables non-technical users to contribute building data through simple terminal commands with smart assistance, while power users retain full CLI capabilities - all in the same interface.

**Next Steps:**
1. Review this specification with engineering team
2. Prioritize implementation phases
3. Create detailed technical tickets
4. Begin Phase 1 implementation

---

**Document Status:** Ready for Engineering Review  
**Last Updated:** December 2024  
**Next Review:** After Phase 1 Completion

