# SVGX Engine

A programmable spatial markup format and simulation engine for CAD-grade infrastructure modeling.

## Overview

SVGX Engine extends SVG with geometric precision, object semantics, programmable behavior, and spatial simulation capabilities suitable for CAD-level use cases in browser environments and future native applications.

## Core Features

### ✅ Human-readable Format
- Retains SVG readability and XML compatibility
- Extends standard SVG with semantic markup

### ✅ Geometry Precision
- Sub-mm precision support
- DXF-style units and path accuracy
- Precision attributes: `arx:precision="0.1mm"`

### ✅ Object Intelligence
- `arx:object` elements for semantic markup
- `arx:system` for system-level organization
- `arx:behavior` for programmable logic

### ✅ Spatial Awareness
- 2.5D and 3D layering support
- Z-index management
- Floorplan abstraction

### ✅ Simulation-Ready
- Inline variable definitions
- Rule-based calculations
- Physics behavior modeling

### ✅ Programmability
- Logic hooks and triggers
- Sensor integration
- Interactive behaviors

### ✅ SVG Compatibility
- Backward compatible with vanilla SVG
- Works with existing rendering engines

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/arxos/svgx-engine.git
cd svgx-engine

# Install the package
pip install -e .
```

### Basic Usage

```python
from svgx_engine.parser import SVGXParser
from svgx_engine.runtime import SVGXRuntime
from svgx_engine.compiler import SVGXCompiler

# Parse SVGX content
parser = SVGXParser()
elements = parser.parse(svgx_content)

# Run simulation
runtime = SVGXRuntime()
results = runtime.simulate(svgx_content)

# Compile to SVG
compiler = SVGXCompiler()
svg_content = compiler.compile(svgx_content, target_format="svg")
```

### Example SVGX File

```xml
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="rm201" type="room" system="architecture">
    <arx:geometry x="0" y="0" width="3000mm" height="4000mm"/>
    <arx:tags>
      <tag>classroom</tag>
      <tag>first_floor</tag>
    </arx:tags>
  </arx:object>

  <path d="M0,0 L3000,0 L3000,4000 L0,4000 Z"
        style="stroke:black;fill:none"
        arx:layer="walls"
        arx:precision="1mm"/>

  <arx:object id="lf01" type="electrical.light_fixture.surface_mount" system="electrical">
    <arx:behavior>
      <variables>
        <voltage unit="V">120</voltage>
        <resistance unit="ohm">720</resistance>
      </variables>
      <calculations>
        <current formula="voltage / resistance"/>
        <power formula="voltage * current"/>
      </calculations>
    </arx:behavior>
    <arx:physics>
      <mass unit="kg">2.5</mass>
      <anchor>ceiling</anchor>
      <forces>
        <force type="gravity" direction="down" value="9.81"/>
      </forces>
    </arx:physics>
  </arx:object>
</svg>
```

## Architecture

```
svgx-engine/
├── parser/                   # SVGX parsing and element extraction
│   ├── parser.py            # Main SVGX parser
│   ├── symbol_manager.py    # Symbol management
│   └── geometry.py          # Geometric calculations
├── runtime/                  # Simulation and behavior engine
│   ├── evaluator.py         # Behavior evaluation
│   ├── behavior_engine.py   # Event handling and triggers
│   └── physics_engine.py    # Physics simulation
├── compiler/                 # Format conversion
│   ├── svgx_to_svg.py      # SVGX to SVG conversion
│   ├── svgx_to_ifc.py      # SVGX to IFC conversion
│   ├── svgx_to_json.py     # SVGX to JSON conversion
│   └── svgx_to_gltf.py     # SVGX to GLTF conversion
├── schema/                   # XML schema definitions
│   └── svgx_schema.xsd     # SVGX schema
├── symbols/                  # Symbol library
│   ├── library_index.yaml   # Symbol index
│   └── *.svgx              # Symbol files
├── tests/                    # Test suite
└── docs/                     # Documentation
```

## API Reference

### Parser

```python
from svgx_engine.parser import SVGXParser

parser = SVGXParser()
elements = parser.parse(svgx_content)
```

### Runtime

```python
from svgx_engine.runtime import SVGXRuntime

runtime = SVGXRuntime()
results = runtime.simulate(svgx_content)
```

### Compiler

```python
from svgx_engine.compiler import SVGXCompiler

compiler = SVGXCompiler()
output = compiler.compile(svgx_content, target_format="svg")
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=svgx_engine --cov-report=html
```

### Code Formatting

```bash
# Format code
black svgx_engine/

# Check linting
flake8 svgx_engine/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Roadmap

- [ ] Advanced physics simulation
- [ ] Real-time collaboration
- [ ] AI-powered symbol recognition
- [ ] Mobile app support
- [ ] Cloud-based rendering
- [ ] Integration with BIM tools

## Support

- Documentation: [docs.arxos.com](https://docs.arxos.com)
- Issues: [GitHub Issues](https://github.com/arxos/svgx-engine/issues)
- Discussions: [GitHub Discussions](https://github.com/arxos/svgx-engine/discussions)
