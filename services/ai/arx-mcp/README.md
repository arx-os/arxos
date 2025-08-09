# Arxos MCP (Model Context Protocol) Package

## Overview

The Arxos MCP package provides comprehensive regulatory compliance workflows for the Arxos Platform, enabling automated validation of building plans against jurisdictional rules. This system integrates with the Model Context Protocol (MCP) to automatically compare building object data against local AHJ (Authority Having Jurisdiction) rules and generate detailed compliance reports.

## Key Features

### 🏗️ Rule Validation Engine
- **MCP File Loading**: Load and validate MCP files from JSON format
- **Rule Execution**: Execute complex validation rules against building models
- **Condition Evaluation**: Support for property, spatial, relationship, and composite conditions
- **Action Execution**: Generate violations, warnings, and calculations
- **Performance Optimization**: Caching and parallel processing for large models

### 📊 Comprehensive Reporting
- **JSON Reports**: Detailed validation data in structured JSON format
- **PDF Reports**: Professional formatted reports with executive summaries
- **Violation Analysis**: Categorization and prioritization of violations
- **Compliance Scoring**: Overall compliance metrics and recommendations
- **Multi-format Export**: Support for various output formats

### 🌍 Multi-jurisdiction Support
- **Jurisdiction Mapping**: Support for country/state/city level rules
- **Code Versioning**: Track effective dates and rule versions
- **Local Amendments**: Handle jurisdiction-specific modifications
- **Compliance Tracking**: Monitor compliance across multiple jurisdictions

### 🔧 Advanced Features
- **Building Model Integration**: Work with Arxos building object models
- **Real-time Validation**: Immediate feedback on rule violations
- **Recommendation Engine**: Generate actionable improvement suggestions
- **Performance Metrics**: Track validation performance and optimization

## Architecture

### Core Components

1. **MCPRuleEngine**: Main validation engine orchestrating rule execution
2. **ConditionEvaluator**: Evaluates rule conditions against building objects
3. **ActionExecutor**: Executes rule actions and generates violations
4. **ReportGenerator**: Creates comprehensive compliance reports
5. **Data Models**: Structured data models for MCP files and validation results

### Data Flow

```
Building Model → MCP Files → Rule Engine → Validation Results → Reports
     ↓              ↓            ↓              ↓              ↓
  Objects      Rule Sets    Conditions    Violations    JSON/PDF
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Arxos Platform integration

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Development Setup
```bash
# Clone the repository
git clone <repository-url>
cd arx-mcp

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/
```

## Usage

### Basic Validation

```python
from arx_mcp import MCPRuleEngine, ReportGenerator
from arx_mcp.models import BuildingModel, BuildingObject

# Initialize the rule engine
engine = MCPRuleEngine()

# Create a building model
building_model = BuildingModel(
    building_id="building_001",
    building_name="Sample Building",
    objects=[
        BuildingObject(
            object_id="outlet_001",
            object_type="electrical_outlet",
            properties={
                "location": "bathroom",
                "load": 15.0,
                "gfci_protected": False
            }
        )
    ]
)

# Validate against MCP files
mcp_files = ["mcp/us/fl/nec-2020.json", "mcp/us/fl/ipc-2021.json"]
compliance_report = engine.validate_building_model(building_model, mcp_files)

# Generate reports
report_generator = ReportGenerator()

# JSON report
json_report = report_generator.generate_json_report(
    compliance_report,
    output_path="reports/compliance_report.json"
)

# PDF report
pdf_report = report_generator.generate_pdf_report(
    compliance_report,
    output_path="reports/compliance_report.pdf"
)

# Summary report
summary = report_generator.generate_summary_report(compliance_report)
print(f"Overall compliance: {summary['compliance_overview']['overall_score']}%")
```

### Advanced Usage

```python
# Load and validate MCP file
mcp_file = engine.load_mcp_file("mcp/us/fl/nec-2020.json")

# Validate MCP file structure
errors = engine.validate_mcp_file("mcp/us/fl/nec-2020.json")
if errors:
    print("MCP file validation errors:", errors)

# Get performance metrics
metrics = engine.get_performance_metrics()
print(f"Average execution time: {metrics['average_execution_time']:.2f}s")

# Clear cache if needed
engine.clear_cache()
```

### MCP File Format

MCP files are JSON documents that define building code requirements:

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
    }
  ],
  "metadata": {
    "source": "National Fire Protection Association",
    "website": "https://www.nfpa.org/nec",
    "contact": "NFPA Customer Service"
  }
}
```

## Rule Types

### Condition Types

- **Property**: Check object properties against values
- **Spatial**: Evaluate spatial relationships and measurements
- **Relationship**: Validate connections between objects
- **System**: Check system-level properties
- **Composite**: Combine multiple conditions with AND/OR logic

### Action Types

- **Validation**: Generate violations or warnings
- **Calculation**: Perform calculations and store results
- **Warning**: Generate warning messages
- **Error**: Generate error violations
- **Modification**: Suggest object modifications
- **Notification**: Send notifications

### Rule Categories

- **Electrical Safety**: GFCI, AFCI, grounding requirements
- **Electrical Design**: Load calculations, circuit sizing
- **Plumbing Water Supply**: Pipe sizing, pressure requirements
- **Plumbing Drainage**: Pipe slope, venting requirements
- **Mechanical HVAC**: System design and installation
- **Mechanical Ventilation**: Air exchange requirements
- **Structural Loads**: Dead, live, and environmental loads
- **Structural Materials**: Material strength and properties
- **Fire Safety Egress**: Exit requirements and routes
- **Fire Safety Resistance**: Material fire resistance
- **Accessibility**: ADA and accessibility requirements
- **Energy Efficiency**: Energy code compliance
- **Environmental**: Environmental impact requirements
- **General**: General building code requirements

## Report Formats

### JSON Report Structure

```json
{
  "report_metadata": {
    "report_type": "MCP Compliance Report",
    "generated_date": "2024-01-15T10:30:00",
    "version": "1.0"
  },
  "building_information": {
    "building_id": "building_001",
    "building_name": "Sample Building"
  },
  "compliance_summary": {
    "overall_compliance_score": 85.5,
    "critical_violations": 3,
    "total_violations": 12,
    "total_warnings": 5
  },
  "mcp_validation_reports": [...],
  "violation_analysis": {...},
  "recommendations": [...],
  "priority_actions": [...]
}
```

### PDF Report Features

- **Executive Summary**: High-level compliance overview
- **Critical Violations**: Detailed analysis of critical issues
- **Warnings**: Non-critical issues and recommendations
- **Detailed Results**: Per-MCP validation results
- **Recommendations**: Actionable improvement suggestions

## Integration with Arxos Platform

### CLI Integration

```bash
# Validate building with MCP files
arx validate building.svg --with mcp/us/fl/nec-2020.json

# Generate compliance report
arx report compliance --building building_001 --output reports/

# Validate MCP file
arx mcp validate mcp/us/fl/nec-2020.json
```

### API Integration

```python
from arx_svg_parser import BuildingCodeValidator

validator = BuildingCodeValidator()

# Load MCP file
validator.load_mcp("mcp/us/fl/nec-2020.json")

# Validate model
results = validator.validate_model(bim_model)
print(f"Found {len(results.errors)} errors")
```

### Web Interface Integration

The MCP system integrates with the Arxos web interface to provide:
- Real-time validation feedback
- Interactive violation visualization
- Compliance dashboard
- Report generation and export

## Performance

### Optimization Features

- **Rule Caching**: Cache parsed rules for faster execution
- **Parallel Processing**: Execute rules in parallel where possible
- **Condition Optimization**: Optimize condition evaluation order
- **Memory Management**: Efficient memory usage for large models

### Performance Targets

- **Rule Execution**: < 100ms per rule for simple rules
- **Large Models**: Handle buildings with 10,000+ objects
- **Multiple MCPs**: Validate against 10+ MCP files simultaneously
- **Report Generation**: Generate reports within 5 seconds

## Development

### Project Structure

```
arx-mcp/
├── __init__.py              # Package initialization
├── models/                  # Data models
│   ├── __init__.py
│   └── mcp_models.py       # MCP data models
├── validate/                # Validation engine
│   ├── __init__.py
│   └── rule_engine.py      # Main rule engine
├── report/                  # Report generation
│   ├── __init__.py
│   └── generate_report.py  # Report generator
├── utils/                   # Utility functions
├── tests/                   # Test suite
├── examples/                # Usage examples
├── requirements.txt         # Dependencies
└── README.md               # This file
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=arx_mcp tests/

# Run specific test file
pytest tests/test_rule_engine.py

# Run performance tests
pytest tests/test_performance.py
```

### Code Quality

```bash
# Format code
black arx_mcp/

# Lint code
flake8 arx_mcp/

# Type checking
mypy arx_mcp/
```

## Contributing

### Development Guidelines

1. **Follow Arxos Architecture**: Adhere to platform architectural principles
2. **Test Coverage**: Maintain 90%+ test coverage
3. **Documentation**: Update documentation for all changes
4. **Performance**: Ensure performance targets are met
5. **Compatibility**: Maintain backward compatibility

### Adding New Features

1. **Create Feature Branch**: `git checkout -b feature/new-feature`
2. **Implement Feature**: Follow coding standards
3. **Add Tests**: Comprehensive test coverage
4. **Update Documentation**: Update relevant documentation
5. **Submit PR**: Create pull request with detailed description

## Troubleshooting

### Common Issues

**MCP File Loading Errors**
- Verify JSON syntax is valid
- Check required fields are present
- Validate jurisdiction information

**Rule Execution Errors**
- Check condition syntax and operators
- Verify object types match expectations
- Review action definitions

**Performance Issues**
- Clear rule cache: `engine.clear_cache()`
- Check rule complexity and optimization
- Monitor memory usage

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for detailed execution information
engine = MCPRuleEngine()
engine.logger.setLevel(logging.DEBUG)
```

## License

This package is part of the Arxos Platform and follows the same licensing terms.

## Support

For support and questions:
- **Documentation**: Check the Arxos Platform documentation
- **Issues**: Report issues through the platform issue tracker
- **Community**: Join the Arxos developer community

---

**Version**: 1.0.0
**Last Updated**: 2024-01-15
**Compatibility**: Arxos Platform 2.0+
