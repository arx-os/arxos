# Building Code Rule Schema

## Overview

Building code rules can be defined inline (as JSON) or in external files (JSON) for rapid prototyping and testing.

## Rule Schema (JSON)

### Core Structure
```json
{
  "rule_id": "string",
  "name": "string",
  "description": "string",
  "category": "string",
  "priority": "number",
  "conditions": [],
  "actions": [],
  "metadata": {}
}
```

### Condition Types
- **Spatial**: Location-based conditions
- **Property**: Element property conditions
- **Relationship**: Connection-based conditions
- **System**: System type conditions
- **Composite**: Multiple condition combinations

### Action Types
- **Validation**: Rule validation actions
- **Warning**: Warning generation
- **Error**: Error generation
- **Modification**: Element modification
- **Notification**: Alert generation

## Example: Fire Safety Egress Rule (JSON)
```json
{
  "rule_id": "fire_safety_egress_001",
  "name": "Fire Safety Egress Requirements",
  "description": "Ensures proper egress routes for fire safety compliance",
  "category": "fire_safety",
  "priority": 1,
  "conditions": [
    {
      "type": "spatial",
      "element_type": "room",
      "property": "area",
      "operator": ">",
      "value": 100
    },
    {
      "type": "relationship",
      "element_type": "door",
      "relationship": "connected_to",
      "target_type": "exit"
    }
  ],
  "actions": [
    {
      "type": "validation",
      "message": "Room requires minimum of 2 exit doors",
      "severity": "error"
    }
  ],
  "metadata": {
    "code_reference": "NFPA 101 Section 7.1",
    "jurisdiction": "US",
    "version": "2020"
  }
}
```

## Example: Energy Efficiency Window Rule (JSON)
```json
{
  "rule_id": "energy_efficiency_windows_001",
  "name": "Energy Efficiency Window Requirements",
  "description": "Validates window specifications for energy efficiency",
  "category": "energy_efficiency",
  "priority": 2,
  "conditions": [
    {
      "type": "property",
      "element_type": "window",
      "property": "u_factor",
      "operator": "<=",
      "value": 0.35
    },
    {
      "type": "property",
      "element_type": "window",
      "property": "solar_heat_gain_coefficient",
      "operator": "<=",
      "value": 0.25
    }
  ],
  "actions": [
    {
      "type": "validation",
      "message": "Window must meet energy efficiency standards",
      "severity": "warning"
    }
  ],
  "metadata": {
    "code_reference": "ASHRAE 90.1 Section 5.5",
    "jurisdiction": "US",
    "version": "2019"
  }
}
```

## Rule Categories

### Fire Safety
- **Egress Requirements**: Exit route validation
- **Fire Resistance**: Material fire resistance
- **Sprinkler Systems**: Automatic sprinkler requirements
- **Alarm Systems**: Fire alarm system requirements

### Structural
- **Load Bearing**: Structural load requirements
- **Foundation**: Foundation design requirements
- **Seismic**: Earthquake resistance requirements
- **Wind Load**: Wind resistance requirements

### Energy Efficiency
- **Insulation**: Thermal insulation requirements
- **HVAC Systems**: Heating and cooling efficiency
- **Lighting**: Energy-efficient lighting requirements
- **Windows**: Window energy performance

### Accessibility
- **ADA Compliance**: Americans with Disabilities Act
- **Universal Design**: Universal design principles
- **Mobility Access**: Wheelchair accessibility
- **Sensory Access**: Visual and auditory accessibility

## Rule Implementation

### Inline Rules
- Define rules directly in code as JSON objects
- Or in external JSON files for rapid prototyping and testing

### Rule Engine Integration
- **Dynamic Loading**: Load rules from JSON files
- **Validation**: Validate rule syntax and structure
- **Execution**: Execute rules against BIM models
- **Reporting**: Generate compliance reports

### Rule Management
- **Version Control**: Rule versioning and history
- **Testing**: Rule testing and validation
- **Deployment**: Rule deployment and activation
- **Monitoring**: Rule execution monitoring

## Rule Validation

### Schema Validation
- **JSON Schema**: Validate rule structure
- **Syntax Checking**: Check rule syntax
- **Reference Validation**: Validate element references
- **Logic Validation**: Validate rule logic

### Rule Testing
- **Unit Testing**: Individual rule testing
- **Integration Testing**: Rule integration testing
- **Scenario Testing**: Real-world scenario testing
- **Performance Testing**: Rule performance testing

## Rule Documentation

### Rule Metadata
- **Description**: Clear rule description
- **References**: Code references and citations
- **Jurisdiction**: Applicable jurisdiction
- **Version**: Rule version information

### Rule Examples
- **Sample Data**: Example data for testing
- **Expected Results**: Expected validation results
- **Edge Cases**: Edge case handling
- **Troubleshooting**: Common issues and solutions

## Rule Deployment

### Production Deployment
- **Validation**: Pre-deployment validation
- **Testing**: Production testing
- **Monitoring**: Rule execution monitoring
- **Rollback**: Rule rollback procedures

### Rule Updates
- **Version Control**: Rule version management
- **Change Management**: Rule change procedures
- **Testing**: Update testing procedures
- **Deployment**: Update deployment procedures
