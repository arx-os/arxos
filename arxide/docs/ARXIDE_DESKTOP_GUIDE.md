# ArxIDE Desktop Application Guide

## Overview

ArxIDE is a professional desktop CAD application built with Tauri (Rust + WebView) that provides a native desktop experience for building information modeling (BIM) and computer-aided design (CAD). It integrates our browser CAD engine with native desktop capabilities for optimal performance and user experience.

## Architecture

### Technology Stack

- **Frontend**: React + TypeScript + Material-UI
- **Backend**: Rust (Tauri)
- **CAD Engine**: JavaScript (from Browser CAD)
- **File System**: Native OS integration
- **Export Formats**: DXF, IFC, PDF, SVG, GLTF

### Component Structure

```
arxide/
├── src/
│   ├── components/
│   │   └── ArxIDEApplication.tsx    # Main application component
│   ├── static/
│   │   ├── js/                      # CAD engine scripts
│   │   └── css/                     # Styles
│   └── main.tsx                     # Application entry point
├── src-tauri/
│   ├── src/
│   │   └── main.rs                  # Rust backend
│   ├── tests/
│   │   └── desktop_tests.rs         # Comprehensive test suite
│   └── Cargo.toml                   # Rust dependencies
└── docs/
    └── ARXIDE_DESKTOP_GUIDE.md     # This documentation
```

## Features

### Core CAD Features

1. **Multi-Level Precision System**
   - UI Level: 0.01" precision for general interface
   - Edit Level: 0.001" precision for detailed editing
   - Compute Level: 0.0001" precision for calculations

2. **Geometric Constraints**
   - Distance constraints
   - Parallel constraints
   - Perpendicular constraints
   - Angle constraints
   - Coincident constraints
   - Horizontal/Vertical constraints

3. **Professional Drawing Tools**
   - Line, Circle, Rectangle tools
   - Advanced geometric shapes
   - Parametric modeling
   - Real-time constraint solving

### Desktop-Specific Features

1. **Native File System Integration**
   - Open/Save SVGX files
   - File watching for external changes
   - Recent files management
   - Auto-save functionality

2. **Professional Export Capabilities**
   - DXF export (AutoCAD compatibility)
   - IFC export (BIM standards)
   - PDF export (documentation)
   - SVG export (web compatibility)
   - GLTF export (3D visualization)

3. **System Integration**
   - Native notifications
   - System tray integration
   - Keyboard shortcuts
   - Drag and drop support
   - Multi-monitor support

4. **Performance Optimizations**
   - Hardware acceleration
   - Multi-threading support
   - Memory management
   - Background processing

## Installation & Setup

### Prerequisites

- Node.js 18+ and npm
- Rust 1.70+
- Platform-specific build tools

### Development Setup

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos/arxide

# Install dependencies
npm install

# Install Rust dependencies
cargo build

# Start development server
npm run dev
```

### Production Build

```bash
# Build for current platform
npm run build

# Build for all platforms
npm run build -- --target all
```

## Usage Guide

### Getting Started

1. **Launch ArxIDE**
   - Double-click the ArxIDE executable
   - Or run from command line: `./arxide`

2. **Create New Project**
   - Click "New File" in the sidebar
   - Or use Ctrl+N keyboard shortcut

3. **Open Existing Project**
   - Click "Open File" in the sidebar
   - Or use Ctrl+O keyboard shortcut
   - Supported formats: SVGX, DXF, IFC

### Drawing Tools

1. **Basic Shapes**
   - **Line Tool**: Click and drag to create lines
   - **Circle Tool**: Click center, drag for radius
   - **Rectangle Tool**: Click corner, drag to opposite corner

2. **Precision Controls**
   - **Precision Level**: Select UI/EDIT/COMPUTE precision
   - **Grid Size**: Set grid spacing (0.01", 0.1", 1", 12")
   - **Grid Snap**: Enable/disable grid snapping

3. **Constraints**
   - **Distance Constraint**: Set exact distance between objects
   - **Parallel Constraint**: Make lines parallel
   - **Perpendicular Constraint**: Make lines perpendicular
   - **Angle Constraint**: Set specific angles

### File Operations

1. **Save Project**
   - Click "Save" in sidebar (Ctrl+S)
   - Or "Save As" for new filename (Ctrl+Shift+S)
   - Projects save as SVGX format

2. **Export Options**
   - **DXF**: For AutoCAD compatibility
   - **IFC**: For BIM software
   - **PDF**: For documentation
   - **SVG**: For web use
   - **GLTF**: For 3D visualization

3. **Batch Processing**
   - Select multiple files
   - Choose export format
   - Process all files automatically

### Advanced Features

1. **Collaboration**
   - Real-time collaboration
   - Version control integration
   - Comment and annotation tools

2. **AI Integration**
   - Smart object recognition
   - Automated constraint suggestions
   - Design optimization

3. **Customization**
   - Theme selection (Dark/Light)
   - Toolbar customization
   - Keyboard shortcut mapping

## Development Guidelines

### Code Organization

1. **Frontend (React/TypeScript)**
   - Components in `src/components/`
   - Static assets in `src/static/`
   - Type definitions in `src/types/`

2. **Backend (Rust)**
   - Main logic in `src-tauri/src/main.rs`
   - Tests in `src-tauri/tests/`
   - Dependencies in `Cargo.toml`

3. **CAD Engine (JavaScript)**
   - Core engine in `src/static/js/cad-engine.js`
   - Constraints in `src/static/js/cad-constraints.js`
   - UI integration in `src/static/js/cad-ui.js`

### Testing Strategy

1. **Unit Tests**
   - Rust backend tests in `desktop_tests.rs`
   - JavaScript CAD engine tests
   - React component tests

2. **Integration Tests**
   - File system operations
   - Export functionality
   - UI interactions

3. **Performance Tests**
   - Large file handling
   - Real-time rendering
   - Memory usage

### Best Practices

1. **Error Handling**
   - Graceful degradation
   - User-friendly error messages
   - Comprehensive logging

2. **Performance**
   - Lazy loading of components
   - Efficient memory management
   - Background processing

3. **Security**
   - File system sandboxing
   - Input validation
   - Secure communication

## API Reference

### Frontend API

```typescript
// File operations
const openFile = async (path: string): Promise<ProjectData>
const saveFile = async (path: string, data: ProjectData): Promise<void>
const exportToDXF = async (path: string, data: ProjectData): Promise<void>

// System integration
const showNotification = async (title: string, body: string): Promise<void>
const getSystemInfo = async (): Promise<SystemInfo>

// CAD engine
const initializeCAD = async (): Promise<void>
const loadProject = async (data: ProjectData): Promise<void>
const exportProject = async (format: ExportFormat): Promise<void>
```

### Backend API

```rust
// File operations
pub async fn read_file(path: String) -> Result<String, String>
pub async fn write_file(path: String, content: String) -> Result<(), String>
pub async fn watch_file(path: String, window: Window) -> Result<(), String>

// Export functions
pub async fn export_to_dxf(path: String, project_data: ProjectData) -> Result<(), String>
pub async fn export_to_ifc(path: String, project_data: ProjectData) -> Result<(), String>
pub async fn export_to_pdf(path: String, project_data: ProjectData) -> Result<(), String>

// System functions
pub async fn get_system_info() -> Result<HashMap<String, String>, String>
pub async fn show_notification(title: String, body: String) -> Result<(), String>
```

## Troubleshooting

### Common Issues

1. **Application Won't Start**
   - Check Rust installation: `rustc --version`
   - Verify dependencies: `cargo check`
   - Check system requirements

2. **File Operations Fail**
   - Verify file permissions
   - Check disk space
   - Ensure file path is valid

3. **Export Issues**
   - Verify export format support
   - Check file permissions for output directory
   - Ensure project data is valid

4. **Performance Problems**
   - Close other applications
   - Reduce project complexity
   - Check system resources

### Debug Mode

```bash
# Enable debug logging
RUST_LOG=debug npm run dev

# Check for errors
npm run lint
cargo clippy
```

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Make changes** following coding standards
4. **Add tests** for new functionality
5. **Run tests**: `npm test && cargo test`
6. **Submit pull request**

### Coding Standards

1. **TypeScript/React**
   - Use TypeScript strict mode
   - Follow React best practices
   - Use Material-UI components

2. **Rust**
   - Follow Rust style guide
   - Use async/await for I/O
   - Implement proper error handling

3. **JavaScript (CAD Engine)**
   - Use ES6+ features
   - Follow JSDoc conventions
   - Implement proper error handling

## Roadmap

### Phase 1: Core Features ✅
- [x] Basic CAD functionality
- [x] File system integration
- [x] Export capabilities
- [x] System integration

### Phase 2: Advanced Features 🚧
- [ ] 3D modeling support
- [ ] Advanced constraints
- [ ] Parametric modeling
- [ ] Plugin system

### Phase 3: Professional Features 📋
- [ ] Collaboration tools
- [ ] Version control
- [ ] Cloud synchronization
- [ ] Mobile companion app

### Phase 4: Enterprise Features 📋
- [ ] Multi-user support
- [ ] Advanced security
- [ ] Enterprise deployment
- [ ] Custom integrations

## Support

### Documentation
- [API Reference](./api-reference.md)
- [Architecture Guide](./architecture.md)
- [Development Guide](./development.md)

### Community
- GitHub Issues: [Report bugs](https://github.com/arx-os/arxos/issues)
- Discussions: [Community forum](https://github.com/arx-os/arxos/discussions)
- Wiki: [User guides](https://github.com/arx-os/arxos/wiki)

### Professional Support
- Email: support@arxos.com
- Documentation: https://docs.arxos.com
- Training: https://training.arxos.com

---

**ArxIDE Desktop** - Professional CAD for the modern world.

*Built with ❤️ by the Arxos Team* 