# SVGX Engine VS Code Extension

A comprehensive VS Code extension for SVGX Engine that provides syntax highlighting, IntelliSense, live preview, error reporting, and debugging support for SVGX files.

## Features

### 🎨 Syntax Highlighting
- Full syntax highlighting for SVGX files
- Support for elements, properties, and simulation types
- Color-coded syntax for better readability

### 🧠 IntelliSense & Autocompletion
- Smart autocompletion for SVGX elements
- Property suggestions and validation
- Simulation type suggestions
- Context-aware completions

### 👁️ Live Preview
- Real-time preview of SVGX files
- Interactive visualization
- Instant updates as you type
- Support for all SVGX element types

### ✅ Error Reporting & Validation
- Real-time validation of SVGX syntax
- Detailed error messages with line numbers
- Warning and error highlighting
- Connection to SVGX Engine server for validation

### 🐛 Debugging Support
- WebSocket connection to SVGX Engine
- Real-time debugging information
- Simulation status updates
- Debug console integration

### 📦 Compilation Support
- Compile SVGX to SVG format
- Compile SVGX to JSON format
- Export capabilities for different targets

## Installation

### Prerequisites
- VS Code 1.74.0 or higher
- SVGX Engine server running (default: http://localhost:8000)

### Installation Steps
1. Clone this repository
2. Navigate to the plugin directory: `cd vscode_plugin`
3. Install dependencies: `npm install`
4. Compile the extension: `npm run compile`
5. Package the extension: `vsce package`
6. Install the VSIX file in VS Code

## Configuration

### Server Settings
Configure the SVGX Engine server connection in VS Code settings:

```json
{
  "svgx.server.url": "http://localhost:8000",
  "svgx.server.apiKey": "your-api-key-here"
}
```

### Performance Settings
Adjust performance targets:

```json
{
  "svgx.performance.targetResponseTime": 16,
  "svgx.simulation.enabled": true,
  "svgx.simulation.types": ["structural", "electrical"]
}
```

## Usage

### Opening SVGX Files
1. Open any `.svgx` file in VS Code
2. The extension will automatically activate
3. Syntax highlighting and IntelliSense will be available

### Commands
Access SVGX commands through the Command Palette (`Ctrl+Shift+P`):

- **SVGX: Open Preview** - Open live preview of current SVGX file
- **SVGX: Validate File** - Validate SVGX syntax and structure
- **SVGX: Run Simulation** - Run simulation on current SVGX file
- **SVGX: Debug Simulation** - Start debugging session
- **SVGX: Compile to SVG** - Compile SVGX to SVG format
- **SVGX: Compile to JSON** - Compile SVGX to JSON format

### Snippets
Use code snippets for quick element creation:

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
- `sim-fluid` - Fluid dynamics simulation
- `sim-heat` - Heat transfer simulation
- `sim-rf` - RF propagation simulation

### Example SVGX File
```svgx
// Simple structural example
element beam(id="beam1", x=0, y=0, length=100, material="steel", elastic_modulus=200e9)
element column(id="column1", x=0, y=0, height=300, material="concrete", elastic_modulus=30e9)

simulate structural {
  elements: [beam1, column1],
  loads: [
    {type: "point_load", magnitude: 1000, position: [50, 0]}
  ],
  constraints: [
    {type: "fixed", element: "column1"}
  ]
}
```

## Development

### Building the Extension
```bash
npm install
npm run compile
```

### Running Tests
```bash
npm test
```

### Linting
```bash
npm run lint
```

### Watching for Changes
```bash
npm run watch
```

## Architecture

### Components
- **SVGXLanguageClient** - Handles communication with SVGX Engine server
- **SVGXPreviewProvider** - Provides live preview functionality
- **SVGXDiagnosticsProvider** - Handles error reporting and validation
- **SVGXCompletionProvider** - Provides IntelliSense and autocompletion

### Communication
- HTTP API calls to SVGX Engine server
- WebSocket connection for real-time updates
- File system monitoring for live preview

### Performance
- Optimized for <16ms response time (CTO directive)
- Efficient parsing and validation
- Minimal memory footprint
- Background processing for non-critical operations

## Troubleshooting

### Common Issues

**Extension not activating**
- Ensure SVGX Engine server is running
- Check server URL in settings
- Verify API key if required

**Preview not working**
- Check WebSocket connection
- Verify SVGX file syntax
- Check browser console for errors

**Validation errors**
- Ensure SVGX Engine server is accessible
- Check network connectivity
- Verify API key permissions

**Performance issues**
- Check server response times
- Monitor memory usage
- Verify target response time settings

### Debug Mode
Enable debug mode for detailed logging:

```json
{
  "svgx.debugging.enabled": true
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This extension is part of the SVGX Engine project and follows the same licensing terms.

## Support

For issues and questions:
- Check the troubleshooting section
- Review SVGX Engine documentation
- Submit issues to the project repository

## Roadmap

### Planned Features
- [ ] Advanced debugging tools
- [ ] Simulation visualization
- [ ] Performance profiling
- [ ] Multi-file support
- [ ] Version control integration
- [ ] Collaborative editing
- [ ] Custom themes
- [ ] Extension marketplace publication

### Performance Targets
- [x] <16ms interaction response time
- [x] Real-time validation
- [x] Live preview updates
- [ ] Advanced IntelliSense
- [ ] Debugging performance optimization 