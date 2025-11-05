# ArxOS Examples

This directory contains example files demonstrating ArxOS data structures, formats, and usage patterns.

## 📚 Quick Navigation

- **[Building Examples](./buildings/)** - Example building data files
  - [Complete Office Building](./buildings/building.yaml) - Full example with equipment
  - [Minimal Building](./buildings/minimal-building.yaml) - Minimal valid structure
  - [Multi-Floor Building](./buildings/multi-floor-building.yaml) - Multi-story example

## 🎯 Purpose

These examples serve as:
- **Reference Documentation** - Show correct data formats and structures
- **Learning Resources** - Help users understand ArxOS data model
- **Testing Templates** - Starting points for creating your own data
- **Validation Examples** - Demonstrate valid ArxOS building data

## 📁 Directory Structure

```
examples/
├── README.md                    # This file - main examples index
└── buildings/                   # Building data examples
    ├── README.md                # Building examples documentation
    ├── building.yaml            # Complete office building example
    ├── minimal-building.yaml    # Minimal valid building
    └── multi-floor-building.yaml # Multi-floor building example
```

## 🚀 Getting Started

### Using Building Examples

```bash
# Validate an example file
arx validate --path examples/buildings/building.yaml

# View building information
arx browse --building "Example Office Building"

# Search within example
arx search "HVAC" --path examples/buildings/
```

### Using Examples Programmatically

```rust
use arxos::yaml::BuildingData;
use std::fs;

// Load example
let content = fs::read_to_string("examples/buildings/building.yaml")?;
let building: BuildingData = serde_yaml::from_str(&content)?;
```

## 📖 Documentation

- **[Building Examples Guide](./buildings/README.md)** - Detailed building data examples
- **[User Guide](../docs/core/USER_GUIDE.md)** - Complete ArxOS usage guide
- **[API Reference](../docs/core/API_REFERENCE.md)** - API documentation

## 🔗 Related Resources

- **[Test Data](../test_data/)** - Test fixtures (different from examples)
- **[Hardware Examples](../hardware/examples/)** - Hardware integration examples
- **[Schemas](../schemas/)** - JSON schemas for validation

## 📝 Notes

- Examples are **reference documentation** - clean, educational, and correct
- Examples are **separate from test data** - test fixtures are in `test_data/`
- Examples are **validated** - All files match current ArxOS schema
- Examples are **versioned** - Compatible with ArxOS v2.0+

## 🛠️ Contributing

When adding new examples:

1. **Use clean data** - Human-readable names, normalized coordinates
2. **Add documentation** - Update relevant README files
3. **Validate structure** - Ensure examples match current schema
4. **Test examples** - Verify examples work with current CLI commands

---

**Questions?** See [Documentation Index](../docs/DOCUMENTATION_INDEX.md) for complete documentation.

