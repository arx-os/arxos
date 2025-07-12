# Building Code MCP (Model Code Provisions)

## Overview

MCP files define building code requirements in a standardized JSON format for automated compliance checking.

## File Structure

```
arx-docs/mcp/
├── global/
│   ├── template.json
│   └── common.json
├── us/
│   ├── fl/
│   │   ├── nec-2020.json
│   │   ├── ipc-2021.json
│   │   └── ada-2010.json
│   └── ca/
│       ├── cbc-2019.json
│       └── energy-2019.json
└── eu/
    ├── uk/
    │   └── building-regs-2010.json
    └── de/
        └── din-2018.json
```

## MCP File Format

All MCP files are written in **JSON** and conform to a standardized schema.

### Example: `us/fl/nec-2020.json`

```json
{
  "mcp_id": "us_fl_nec_2020",
  "name": "Florida NEC 2020",
  "description": "National Electrical Code 2020 for Florida",
  "jurisdiction": {
    "country": "US",
    "state": "FL",
    "city": null
  },
  "version": "2020",
  "effective_date": "2020-01-01",
    "rules": [
    {
      "rule_id": "nec_210_8",
      "name": "GFCI Protection",
      "description": "Ground-fault circuit interrupter protection for personnel",
      "category": "electrical_safety",
      "priority": 1,
      "conditions": [
        {
          "type": "property",
          "element_type": "electrical_outlet",
          "property": "location",
          "operator": "in",
          "value": ["bathroom", "kitchen", "outdoor"]
        }
      ],
      "actions": [
        {
          "type": "validation",
          "message": "GFCI protection required for outlets in wet locations",
          "severity": "error",
          "code_reference": "NEC 210.8"
        }
      ]
    },
    {
      "rule_id": "nec_220_12",
      "name": "Branch Circuit Load Calculations",
      "description": "General lighting load calculations",
      "category": "electrical_design",
      "priority": 2,
      "conditions": [
        {
          "type": "spatial",
          "element_type": "room",
          "property": "area",
          "operator": ">",
          "value": 0
        }
      ],
      "actions": [
        {
          "type": "calculation",
          "formula": "area * 3.0",
          "unit": "VA",
          "description": "General lighting load calculation"
        }
      ]
    }
  ],
  "metadata": {
    "source": "National Fire Protection Association",
    "website": "https://www.nfpa.org/nec",
    "contact": "NFPA Customer Service",
    "notes": "Florida-specific amendments may apply"
  }
}
```

## MCP Usage

### Loading MCPs
1. Loads applicable MCPs (`arxfile.json` or CLI args)
2. Validates MCP syntax and structure
3. Applies rules to BIM model
4. Generates compliance report

### Command Line Usage
```bash
# Validate with specific MCP
arx validate floor1.svg --with mcp/us/fl/nec-2020.json

# Validate with multiple MCPs
arx validate floor1.svg --with mcp/us/fl/nec-2020.json,mcp/us/fl/ipc-2021.json

# Validate with jurisdiction auto-detection
arx validate floor1.svg --jurisdiction us/fl
```

### API Usage
```python
from arx_svg_parser import BuildingCodeValidator

validator = BuildingCodeValidator()

# Load MCP file
validator.load_mcp("mcp/us/fl/nec-2020.json")

# Validate model
results = validator.validate_model(bim_model)
print(f"Found {len(results.errors)} errors")
```

## MCP Development

### Creating New MCPs
1. Fork or copy the MCP template from `global/template.json`
2. Customize for your jurisdiction
3. Add specific rules and requirements
4. Test with sample models
5. Submit for review and approval

### MCP Template
```json
{
  "mcp_id": "template",
  "name": "Template MCP",
  "description": "Template for creating new MCP files",
  "jurisdiction": {
    "country": "XX",
    "state": "YY",
    "city": "ZZ"
  },
  "version": "YYYY",
  "effective_date": "YYYY-MM-DD",
  "rules": [
    {
      "rule_id": "template_rule_001",
      "name": "Template Rule",
      "description": "Template rule description",
      "category": "template_category",
      "priority": 1,
      "conditions": [
        {
          "type": "property",
          "element_type": "template_element",
          "property": "template_property",
          "operator": "==",
          "value": "template_value"
        }
      ],
      "actions": [
        {
          "type": "validation",
          "message": "Template validation message",
          "severity": "error",
          "code_reference": "TEMPLATE-001"
        }
      ]
    }
  ],
  "metadata": {
    "source": "Template Source",
    "website": "https://template.example.com",
    "contact": "Template Contact",
    "notes": "Template notes"
  }
}
```

## Rule Categories

### Electrical
- **Safety**: GFCI, AFCI, grounding requirements
- **Design**: Load calculations, circuit sizing
- **Installation**: Wiring methods, equipment mounting
- **Maintenance**: Inspection and testing requirements

### Plumbing
- **Water Supply**: Pipe sizing, pressure requirements
- **Drainage**: Pipe slope, venting requirements
- **Fixtures**: Fixture requirements and installation
- **Gas**: Gas piping and appliance requirements

### Mechanical
- **HVAC**: System design and installation
- **Ventilation**: Air exchange requirements
- **Ductwork**: Duct sizing and installation
- **Controls**: System control requirements

### Structural
- **Loads**: Dead, live, and environmental loads
- **Materials**: Material strength and properties
- **Connections**: Structural connection requirements
- **Foundations**: Foundation design requirements

### Fire Safety
- **Egress**: Exit requirements and routes
- **Fire Resistance**: Material fire resistance
- **Sprinklers**: Automatic sprinkler systems
- **Alarms**: Fire alarm system requirements

## MCP Validation

### Schema Validation
- **JSON Schema**: Validate MCP file structure
- **Rule Validation**: Validate individual rules
- **Reference Validation**: Validate element references
- **Logic Validation**: Validate rule logic

### Content Validation
- **Jurisdiction**: Validate jurisdiction information
- **Dates**: Validate effective dates
- **References**: Validate code references
- **Metadata**: Validate metadata completeness

## MCP Management

### Version Control
- **Git Repository**: MCP file version control
- **Change Tracking**: Track MCP changes
- **Review Process**: MCP review and approval
- **Deployment**: MCP deployment procedures

### Quality Assurance
- **Testing**: MCP testing procedures
- **Validation**: MCP validation procedures
- **Documentation**: MCP documentation requirements
- **Maintenance**: MCP maintenance procedures

## MCP Integration

### BIM Integration
- **Model Loading**: Load BIM models for validation
- **Rule Application**: Apply MCP rules to models
- **Result Generation**: Generate compliance reports
- **Visualization**: Visualize compliance results

### API Integration
- **REST API**: MCP management API
- **Validation API**: Rule validation API
- **Reporting API**: Compliance reporting API
- **Management API**: MCP management API

### CLI Integration
- **Validation Commands**: MCP validation commands
- **Management Commands**: MCP management commands
- **Reporting Commands**: Compliance reporting commands
- **Utility Commands**: MCP utility commands
