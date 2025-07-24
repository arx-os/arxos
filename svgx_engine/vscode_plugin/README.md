# SVGX Engine VS Code Extension

A comprehensive VS Code extension for SVGX (Scalable Vector Graphics Extended) development, providing syntax highlighting, IntelliSense, live preview, validation, and debugging capabilities.

## Features

### 🎨 **Syntax Highlighting**
- Full SVGX syntax support with color-coded elements, attributes, and values
- Custom language grammar for SVGX-specific keywords and patterns
- Support for comments, strings, numbers, and special characters

### 🧠 **IntelliSense & Autocompletion**
- Smart code completion for SVGX elements and attributes
- Context-aware suggestions based on element types
- Auto-completion for simulation types and parameters
- Snippet support for common SVGX patterns

### 👁️ **Live Preview Integration**
- Real-time preview of SVGX files
- Interactive preview panel with controls
- Syntax highlighting in preview
- Error and warning display

### ✅ **Validation & Error Reporting**
- Real-time validation of SVGX syntax
- Error and warning highlighting in editor
- Problem matcher integration
- Detailed error messages with line/column information

### 🐛 **Debugging Support**
- Integrated debugging for SVGX simulations
- Breakpoint support for simulation execution
- Variable inspection and watch expressions
- Step-through debugging capabilities

### 🔧 **Advanced Features**
- WebSocket integration for real-time updates
- Server communication for validation and compilation
- Multiple export formats (SVG, JSON)
- Simulation type support (structural, electrical, fluid dynamics, etc.)

## Installation

1. Clone the repository
2. Navigate to the `vscode_plugin` directory
3. Install dependencies:
   ```bash
   npm install
   ```
4. Open the folder in VS Code
5. Press `F5` to run the extension in development mode

## Configuration

### Server Settings
```json
{
  "svgx.server.url": "http://localhost:8000",
  "svgx.server.apiKey": "your-api-key"
}
```

### Feature Toggles
```json
{
  "svgx.preview.enabled": true,
  "svgx.validation.enabled": true,
  "svgx.debugging.enabled": true,
  "svgx.simulation.enabled": true
}
```

### Performance Settings
```json
{
  "svgx.performance.targetResponseTime": 16
}
```

## Usage

### Commands

- **SVGX: Open Preview** - Opens live preview of current SVGX file
- **SVGX: Validate File** - Validates the current SVGX file
- **SVGX: Debug Simulation** - Starts debugging session for simulations
- **SVGX: Run Simulation** - Runs simulation on current file
- **SVGX: Compile to SVG** - Compiles SVGX to SVG format
- **SVGX: Compile to JSON** - Compiles SVGX to JSON format

### Snippets

The extension provides numerous snippets for common SVGX patterns:

- `rect` - Basic rectangle element
- `circle` - Basic circle element
- `line` - Basic line element
- `beam` - Structural beam element
- `column` - Structural column element
- `pipe` - Pipe element
- `resistor` - Electrical resistor
- `capacitor` - Electrical capacitor
- `inductor` - Electrical inductor
- `voltage` - Voltage source
- `current` - Current source
- `sim-structural` - Structural simulation
- `sim-electrical` - Electrical simulation

### Views

The extension adds several views to the activity bar:

- **Simulations** - View and manage simulation sessions
- **Elements** - Browse SVGX elements in the current file
- **Constraints** - View and edit element constraints

## Architecture

### Core Components

1. **SVGXLanguageClient** - Handles communication with SVGX Engine server
2. **SVGXPreviewProvider** - Manages live preview functionality
3. **SVGXDiagnosticsProvider** - Provides error reporting and validation
4. **SVGXCompletionProvider** - Implements IntelliSense and autocompletion

### File Structure

```
vscode_plugin/
├── src/
│   └── extension.js          # Main extension file
├── syntaxes/
│   └── svgx.tmLanguage.json # Syntax highlighting rules
├── snippets/
│   └── svgx.json            # Code snippets
├── language-configuration.json
├── package.json
└── README.md
```

## Development

### Prerequisites
- Node.js (no TypeScript required)
- VS Code Extension Development Host
- SVGX Engine server running locally

### Building
```bash
npm install
```

### Testing
```bash
npm test
```

### Debugging
1. Open the extension in VS Code
2. Press `F5` to launch extension development host
3. Open an SVGX file to test functionality

## API Integration

The extension integrates with the SVGX Engine server via:

- **REST API** - For validation, parsing, and compilation
- **WebSocket** - For real-time updates and notifications
- **HTTP Client** - Using axios for reliable communication

### Server Endpoints

- `POST /validate` - Validate SVGX content
- `POST /parse` - Parse SVGX content to elements
- `POST /simulate` - Run simulations
- `POST /compile/svg` - Compile to SVG
- `POST /compile/json` - Compile to JSON
- `WS /ws` - WebSocket for real-time updates

## Error Handling

The extension includes comprehensive error handling:

- Network connectivity issues
- Server communication failures
- Invalid SVGX syntax
- Simulation execution errors
- Compilation failures

## Performance

- Optimized for large SVGX files
- Efficient syntax highlighting
- Minimal memory footprint
- Fast validation and parsing
- Real-time preview updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This extension is part of the Arxos Platform and follows the same licensing terms.

## Support

For issues and questions:
- Check the VS Code extension documentation
- Review the SVGX Engine documentation
- Open an issue in the repository

---

**Note**: This extension is designed to work with the SVGX Engine server. Ensure the server is running and properly configured before using the extension features. 