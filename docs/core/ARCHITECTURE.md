# ArxOS Architecture Documentation

**Version:** 2.0  
**Date:** December 2024  
**Author:** Joel (Founder)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Module Structure](#module-structure)
6. [Interactive 3D Rendering](#interactive-3d-rendering)
7. [Particle System & Animation](#particle-system--animation)
8. [Performance Considerations](#performance-considerations)
9. [Extension Points](#extension-points)
10. [Integration Patterns](#integration-patterns)

---

## System Overview

ArxOS is a terminal-first building management system built with Rust, designed around Git-like version control principles for building data. The system provides advanced 3D visualization, interactive controls, and real-time effects through a modular, layered architecture.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface Layer                      │
│  Commands: search, filter, render, interactive, config     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Application Layer                           │
│  Search Engine, 3D Renderer, Interactive Controller       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Core Services Layer                       │
│  Git Integration, IFC Processing, Spatial Operations       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Data Layer                               │
│  YAML/JSON Data, Building Models, Equipment Data          │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Terminal-First**: All functionality works in terminal environment
2. **Git-Native**: All data changes go through Git workflow
3. **Modular Design**: Clean separation of concerns
4. **Performance-Focused**: Optimized for large buildings (1000+ equipment)
5. **Extensible**: Easy to add new features and integrations

---

## Architecture Principles

### 1. Layered Architecture

ArxOS follows a strict layered architecture with clear boundaries:

- **Presentation Layer**: CLI interface and terminal rendering
- **Application Layer**: Business logic and orchestration
- **Service Layer**: Core services and data processing
- **Data Layer**: Data models and persistence

### 2. Event-Driven Design

Interactive components use event-driven architecture:

- **Event Sources**: Keyboard, mouse, timer events
- **Event Handlers**: Process events and update state
- **State Management**: Centralized state with reactive updates
- **Effect System**: Visual effects triggered by state changes

### 3. Performance Optimization

Multiple performance optimization strategies:

- **Caching**: Equipment and room data caching
- **Lazy Loading**: On-demand data loading
- **Particle Pooling**: Reuse particle objects
- **Parallel Processing**: Concurrent operations where possible
- **Memory Management**: Efficient data structures

### 4. Error Handling

Comprehensive error handling strategy:

- **Rich Error Context**: Detailed error information
- **Recovery Mechanisms**: Automatic retry and fallback
- **User-Friendly Messages**: Clear error messages for users
- **Logging**: Comprehensive logging for debugging

---

## Core Components

### 1. Search Engine (`src/search/mod.rs`)

**Purpose**: Advanced search and filtering capabilities

**Key Features**:
- Multi-field search across equipment, rooms, buildings
- Fuzzy matching with Levenshtein distance
- Regex pattern matching
- Real-time result highlighting
- Performance-optimized with caching

**Architecture**:
```rust
pub struct SearchEngine {
    pub buildings: Vec<Building>,
    pub equipment: Vec<EquipmentData>,
    pub rooms: Vec<RoomData>,
}

impl SearchEngine {
    pub fn search(&self, config: &SearchConfig) -> Result<Vec<SearchResult>, Error>
    pub fn filter(&self, config: &FilterConfig) -> Result<Vec<SearchResult>, Error>
    pub fn format_search_results(&self, results: &[SearchResult], format: &str, verbose: bool) -> String
}
```

### 2. 3D Renderer (`src/render3d/mod.rs`)

**Purpose**: 3D building visualization and rendering

**Key Features**:
- Multiple projection types (isometric, orthographic, perspective)
- Multi-floor building visualization
- Equipment placement in 3D space
- ASCII/Unicode terminal rendering
- Spatial coordinate system support

**Architecture**:
```rust
pub struct Building3DRenderer {
    pub building_data: BuildingData,
    pub config: Render3DConfig,
    pub camera: Camera3D,
}

impl Building3DRenderer {
    pub fn render_3d(&mut self) -> Result<Scene3D, Error>
    pub fn render_to_ascii(&self, scene: &Scene3D) -> Result<String, Error>
    pub fn set_camera(&mut self, position: Point3D, target: Point3D)
}
```

### 3. Interactive Renderer (`src/render3d/interactive.rs`)

**Purpose**: Real-time interactive 3D rendering with controls

**Key Features**:
- Event-driven input handling with crossterm
- Camera movement and rotation controls
- View mode switching
- Equipment selection and highlighting
- Integration with particle and animation systems

**Architecture**:
```rust
pub struct InteractiveRenderer {
    renderer: Building3DRenderer,
    state: InteractiveState,
    event_handler: EventHandler,
    effects_engine: VisualEffectsEngine,
    config: InteractiveConfig,
}
```

### 4. Particle System (`src/render3d/particles.rs`)

**Purpose**: High-performance particle effects for terminal rendering

**Key Features**:
- 8 particle types with unique behaviors
- Physics simulation with gravity and air resistance
- Particle pooling for performance
- Terminal-optimized rendering
- Real-time particle lifecycle management

**Architecture**:
```rust
pub struct ParticleSystem {
    particles: Vec<Particle>,
    particle_pool: VecDeque<Particle>,
    config: ParticleSystemConfig,
    stats: ParticleSystemStats,
}

pub enum ParticleType {
    Basic, Smoke, Fire, Spark, Dust,
    StatusIndicator, Connection, MaintenanceAlert,
}
```

### 5. Animation System (`src/render3d/animation.rs`)

**Purpose**: Smooth animations and transitions

**Key Features**:
- 8 animation types with specific behaviors
- 7 easing functions for smooth transitions
- Real-time animation updates
- Performance-optimized with pooling
- Integration with visual effects

**Architecture**:
```rust
pub struct AnimationSystem {
    animations: HashMap<String, Animation>,
    config: AnimationConfig,
    stats: AnimationStats,
}

pub enum AnimationType {
    Linear, CameraMove, StatusTransition, BuildingFade,
    ParticleEffect, SelectionHighlight, FloorTransition, ViewModeTransition,
}
```

### 6. Visual Effects Engine (`src/render3d/effects.rs`)

**Purpose**: Advanced visual effects integrating particles and animations

**Key Features**:
- 11 effect types for different scenarios
- Integration of particle and animation systems
- Real-time effect management
- Performance monitoring and optimization
- Customizable effect parameters

**Architecture**:
```rust
pub struct VisualEffectsEngine {
    particle_system: ParticleSystem,
    animation_system: AnimationSystem,
    active_effects: HashMap<String, VisualEffect>,
    config: EffectsConfig,
    stats: EffectsStats,
}
```

---

## Data Flow

### 1. Search Flow

```
User Query → SearchConfig → SearchEngine → Fuzzy Matching → Results → Formatting → Output
```

**Detailed Flow**:
1. User provides search query and configuration
2. SearchEngine validates configuration and compiles regex if needed
3. Multi-field search across equipment, rooms, buildings
4. Fuzzy matching algorithm calculates match scores
5. Results are sorted by relevance score
6. Results are formatted according to output format
7. Highlighted output is returned to user

### 2. 3D Rendering Flow

```
Building Data → 3D Renderer → Scene Generation → ASCII Conversion → Terminal Output
```

**Detailed Flow**:
1. Building data is loaded and validated
2. 3D renderer processes spatial data and equipment positions
3. Scene is generated with 3D coordinates and relationships
4. 3D scene is projected to 2D ASCII representation
5. ASCII output is formatted for terminal display
6. Result is displayed to user

### 3. Interactive Rendering Flow

```
User Input → Event Handler → State Update → Effects Update → Scene Render → Display
```

**Detailed Flow**:
1. User input (keyboard/mouse) is captured by crossterm
2. Event handler processes input and determines actions
3. Interactive state is updated (camera, selection, view mode)
4. Visual effects engine updates particles and animations
5. 3D scene is rendered with current state
6. Particle effects are integrated into ASCII output
7. Final output is displayed to user

### 4. Particle Effect Flow

```
Effect Trigger → Particle Creation → Physics Update → Rendering → Cleanup
```

**Detailed Flow**:
1. Effect is triggered (equipment status change, user action)
2. Appropriate particles are created and added to system
3. Physics simulation updates particle positions and properties
4. Particles are rendered as ASCII characters
5. Expired particles are removed and returned to pool

---

## Module Structure

### Core Modules

```
src/
├── main.rs                 # CLI entry point
├── lib.rs                  # Library API exports
├── cli/                    # Command-line interface
│   └── mod.rs             # CLI command definitions
├── search/                 # Search and filtering
│   └── mod.rs             # Search engine implementation
├── render3d/               # 3D rendering system
│   ├── mod.rs             # Core 3D renderer
│   ├── interactive.rs      # Interactive 3D renderer
│   ├── particles.rs        # Particle system
│   ├── animation.rs        # Animation framework
│   ├── effects.rs          # Visual effects engine
│   ├── events.rs           # Event handling
│   └── state.rs            # State management
├── spatial/                # Spatial operations
│   ├── mod.rs             # Spatial data structures
│   └── types.rs           # Spatial type definitions
├── yaml/                   # Data serialization
│   └── mod.rs             # YAML/JSON data handling
├── git/                    # Git integration
│   ├── mod.rs             # Git operations
│   └── manager.rs         # Git repository management
├── ifc/                    # IFC file processing
│   ├── mod.rs             # IFC processing pipeline
│   ├── enhanced.rs         # Enhanced IFC processing
│   └── fallback.rs         # Fallback processing
└── config/                 # Configuration management
    ├── mod.rs             # Configuration system
    ├── manager.rs         # Configuration manager
    └── validation.rs      # Configuration validation
```

### Module Organization

The project uses a **unified crate structure** with all modules in `src/`. As of December 2024, the architecture was refactored from a monolithic `main.rs` (2,132 lines) into a clean, modular structure with dedicated command handlers:

```
src/
├── lib.rs                  # Library API for tests and mobile FFI
├── main.rs                 # CLI entry point (~50 lines)
├── commands/               # Command handlers (NEW)
│   ├── mod.rs             # Command router
│   ├── import.rs          # IFC file import
│   ├── export.rs          # Git export
│   ├── git_ops.rs         # Git operations
│   ├── config_mgmt.rs     # Configuration
│   ├── room.rs            # Room management
│   ├── equipment.rs       # Equipment management
│   ├── spatial.rs         # Spatial operations
│   ├── search.rs          # Search and filter
│   ├── watch.rs           # Live monitoring
│   ├── ar.rs              # AR integration
│   ├── sensors.rs         # Sensor processing
│   ├── render.rs          # 2D/3D rendering
│   ├── interactive.rs     # Interactive 3D
│   ├── ifc.rs             # IFC commands
│   └── validate.rs        # Validation
├── utils/                  # Utility functions (NEW)
│   ├── mod.rs             # Utils module
│   └── loading.rs         # Data loading helpers
├── core/                   # Core business logic and data structures
│   └── mod.rs             # Building, Room, Equipment types
├── cli/                    # CLI command definitions
│   └── mod.rs             # Command parsing with clap
├── ifc/                    # IFC file processing
│   ├── mod.rs             # Main IFC processor
│   ├── enhanced.rs         # Enhanced parsing
│   ├── fallback.rs        # Fallback parsing
│   └── hierarchy.rs       # Building hierarchy extraction
├── render3d/               # 3D rendering system
│   ├── mod.rs             # 3D renderer
│   ├── interactive.rs     # Interactive rendering
│   ├── particles.rs       # Particle system
│   ├── animation.rs       # Animation framework
│   ├── effects.rs         # Visual effects
│   ├── events.rs          # Event handling
│   └── state.rs           # State management
├── git/                    # Git integration
│   ├── mod.rs             # Git operations
│   └── manager.rs         # Git repository management
├── spatial/                # Spatial operations
│   ├── mod.rs             # Spatial engine
│   └── types.rs           # Spatial types
├── search/                 # Search and filtering
│   └── mod.rs             # Search engine
├── mobile_ffi/             # Mobile FFI bindings
│   ├── mod.rs             # FFI definitions
│   ├── ffi.rs             # FFI functions
│   └── jni.rs             # JNI bindings for Android
└── [other modules]/       # Additional functionality
```

### Command Handler Architecture (Refactored December 2024)

The command handlers were refactored to follow best engineering practices:

**Before**: Monolithic `main.rs` with 2,132 lines containing all command logic mixed together

**After**: Modular structure with 16 focused command handler modules

**Key Improvements**:
- **Separation of Concerns**: Each handler in its own file with single responsibility
- **Reusability**: Helper functions extracted (e.g., `generate_yaml_output()` in import handler)
- **Testability**: 18 unit tests + 11 integration tests with 150+ total tests passing
- **Maintainability**: Easy to find, modify, and extend individual commands
- **Code Quality**: Removed duplications, improved error handling, added Git validation

**Pattern Example**:
```rust
// src/commands/mod.rs - Command Router
pub fn execute_command(command: Commands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        Commands::Import { ifc_file, repo } => import::handle_import(ifc_file, repo),
        Commands::Export { repo } => export::handle_export(repo),
        Commands::Status { verbose } => git_ops::handle_status(verbose),
        // ... other command delegations
    }
}
```

---

## Interactive 3D Rendering

### Architecture Overview

The interactive 3D rendering system uses a layered architecture that builds upon the existing static 3D renderer:

```
┌─────────────────────────────────────┐
│           CLI Layer                 │
│  `arx interactive --building 7`    │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│        Interactive Layer            │
│  InteractiveRenderer + EventLoop    │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│        Static Renderer              │
│  Building3DRenderer (existing)     │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│        Data Layer                   │
│  BuildingData + Spatial Types       │
└─────────────────────────────────────┘
```

### Event-Driven Architecture

The interactive system uses an event-driven architecture for real-time input handling:

```rust
pub enum InteractiveEvent {
    KeyPress(KeyCode, KeyModifiers),
    MouseClick(MouseClickEvent),
    MouseMove(MouseMoveEvent),
    Resize(usize, usize),
    Quit,
    Action(Action),
}

pub struct EventHandler {
    key_bindings: HashMap<KeyCode, Action>,
    mouse_bindings: HashMap<MouseButton, Action>,
    config: EventConfig,
}
```

### State Management

Interactive state is managed centrally with reactive updates:

```rust
pub struct InteractiveState {
    selected_equipment: HashSet<String>,
    camera_state: CameraState,
    view_mode: ViewMode,
    session_data: SessionData,
    current_floor: Option<i32>,
    is_active: bool,
}
```

### Integration Points

The interactive renderer integrates with multiple systems:

1. **Static 3D Renderer**: Uses existing Building3DRenderer for core rendering
2. **Particle System**: Integrates particle effects for visual feedback
3. **Animation System**: Uses animations for smooth transitions
4. **Event System**: Handles real-time input processing
5. **State Management**: Maintains session state and preferences

---

## Particle System & Animation

### Particle System Architecture

The particle system is designed for high-performance terminal rendering:

```rust
pub struct ParticleSystem {
    particles: Vec<Particle>,           // Active particles
    particle_pool: VecDeque<Particle>,   // Reusable particle pool
    config: ParticleSystemConfig,        // System configuration
    stats: ParticleSystemStats,          // Performance statistics
}
```

**Key Design Decisions**:

1. **Particle Pooling**: Reuse particle objects to avoid allocation overhead
2. **Type-Based Behavior**: Different particle types have specialized update logic
3. **Physics Simulation**: Realistic physics with gravity, air resistance, and forces
4. **Terminal Optimization**: ASCII/Unicode character rendering for terminal compatibility

### Animation System Architecture

The animation system provides smooth transitions and effects:

```rust
pub struct AnimationSystem {
    animations: HashMap<String, Animation>,  // Active animations
    config: AnimationConfig,                 // System configuration
    stats: AnimationStats,                   // Performance statistics
}
```

**Key Design Decisions**:

1. **Easing Functions**: Multiple easing functions for different animation styles
2. **Type-Specific Data**: Different animation types have specialized data structures
3. **Performance Optimization**: Efficient update loops with minimal overhead
4. **Integration**: Seamless integration with particle and visual effects systems

### Visual Effects Integration

The visual effects engine combines particles and animations:

```rust
pub struct VisualEffectsEngine {
    particle_system: ParticleSystem,      // Particle effects
    animation_system: AnimationSystem,   // Animation effects
    active_effects: HashMap<String, VisualEffect>, // Active effects
    config: EffectsConfig,               // System configuration
    stats: EffectsStats,                 // Performance statistics
}
```

**Integration Patterns**:

1. **Effect Composition**: Combine multiple particle and animation effects
2. **State Synchronization**: Effects respond to building and equipment state changes
3. **Performance Monitoring**: Real-time performance metrics and optimization
4. **Customizable Parameters**: Configurable effect intensity, duration, and behavior

---

## Performance Considerations

### Memory Management

1. **Particle Pooling**: Reuse particle objects to minimize allocations
2. **Efficient Data Structures**: Use appropriate data structures for different use cases
3. **Lazy Loading**: Load data on-demand to reduce memory footprint
4. **Cache Management**: Intelligent caching with invalidation strategies

### CPU Optimization

1. **Parallel Processing**: Use parallel processing where possible
2. **Efficient Algorithms**: Optimized algorithms for search and rendering
3. **Update Frequency Control**: Configurable update rates for different systems
4. **Early Termination**: Stop processing when results are sufficient

### Terminal Performance

1. **ASCII Optimization**: Efficient ASCII character rendering
2. **Screen Buffer Management**: Minimize screen updates and redraws
3. **Input Processing**: Efficient event handling with minimal latency
4. **Output Formatting**: Optimized string formatting and concatenation

### Scalability

1. **Large Dataset Support**: Handle buildings with 1000+ equipment items
2. **Concurrent Operations**: Support multiple simultaneous operations
3. **Resource Limits**: Configurable limits to prevent resource exhaustion
4. **Performance Monitoring**: Real-time performance metrics and alerts

---

## Extension Points

### Adding New Particle Types

```rust
pub enum ParticleType {
    // Existing types...
    Custom(CustomParticleData),
}

impl ParticleSystem {
    fn update_custom_particle(&mut self, particle: &mut Particle, delta_time: f64) {
        // Custom particle behavior implementation
    }
}
```

### Adding New Animation Types

```rust
pub enum AnimationType {
    // Existing types...
    Custom(CustomAnimationData),
}

impl AnimationSystem {
    fn update_custom_animation(&mut self, animation: &mut Animation, eased_progress: f64) {
        // Custom animation behavior implementation
    }
}
```

### Adding New Visual Effects

```rust
pub enum EffectType {
    // Existing types...
    Custom(CustomEffectData),
}

impl VisualEffectsEngine {
    fn update_custom_effect(&mut self, effect: &mut VisualEffect, delta_time: f64) {
        // Custom effect behavior implementation
    }
}
```

### Adding New Search Features

```rust
impl SearchEngine {
    pub fn custom_search(&self, config: &CustomSearchConfig) -> Result<Vec<SearchResult>, Error> {
        // Custom search implementation
    }
}
```

---

## Integration Patterns

### CLI Integration

The CLI layer provides a clean interface to all system components:

```rust
// Command handling pattern
match command {
    Commands::Search { query, options } => {
        let search_engine = SearchEngine::new(&building_data);
        let results = search_engine.search(&config)?;
        format_and_display_results(results, &options)?;
    }
    Commands::Interactive { options } => {
        let mut renderer = InteractiveRenderer::new(building_data, config)?;
        renderer.start_interactive_session()?;
    }
}
```

### Data Integration

Data flows through the system using consistent patterns:

```rust
// Data loading pattern
let building_data = load_building_data(&building_name)?;
let search_engine = SearchEngine::new(&building_data);
let renderer = Building3DRenderer::new(building_data, render_config);
```

### Error Handling Integration

Consistent error handling across all components:

```rust
// Error handling pattern
pub fn process_command() -> Result<(), Box<dyn std::error::Error>> {
    let result = risky_operation()?;
    Ok(result)
}
```

### Configuration Integration

Centralized configuration management:

```rust
// Configuration pattern
let config = load_config()?;
let search_config = SearchConfig::from(&config);
let render_config = Render3DConfig::from(&config);
```

---

## Conclusion

ArxOS is built with a modular, layered architecture that prioritizes performance, extensibility, and maintainability. The system's design allows for easy addition of new features while maintaining clean separation of concerns and consistent patterns throughout the codebase.

The interactive 3D rendering system demonstrates the power of combining multiple specialized systems (particles, animations, effects) into a cohesive user experience, while the search and filtering system showcases the importance of performance optimization and user-friendly interfaces.

This architecture provides a solid foundation for future development and ensures that ArxOS can scale to meet the needs of complex building management scenarios.

---

**Architecture Documentation Version:** 2.0  
**Last Updated:** December 2024  
**Status:** Complete