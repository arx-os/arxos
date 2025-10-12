# IFC Service Notes

## Current Status

The IfcOpenShell service requires `ifcopenshell==0.8.3` which is not available via pip.

### Issue
```
ERROR: Could not find a version that satisfies the requirement ifcopenshell==0.8.3
```

### Solution Options

1. **Use Latest Version** - Update requirements.txt to use latest available version
2. **Build from Source** - Compile IfcOpenShell from GitHub
3. **Use Native Parser** - ArxOS has a fallback Go-based parser

### Recommended: Native Parser for Now

ArxOS includes a native Go IFC parser as fallback:
- Located in `internal/infrastructure/ifc/native_parser.go`
- Handles basic IFC parsing
- No Python dependencies
- Good enough for MVP

### Future: Proper IfcOpenShell Integration

When needed:
1. Install IfcOpenShell via conda or build from source
2. Update Docker image to use conda
3. Test with real IFC files

For now, the native parser is sufficient for basic IFC import functionality.

