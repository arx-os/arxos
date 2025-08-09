# Rule Engine Developer Guide

## Overview

The Rule Engine allows you to define custom validation rules for building code compliance. Rules can be stored in JSON format in `arx_svg_parser/data/sample_rules/` or your own rules directory.

## Rule Structure

### Basic Rule Format
```json
{
  "rule_id": "unique_rule_identifier",
  "name": "Human Readable Rule Name",
  "description": "Detailed rule description",
  "category": "rule_category",
  "priority": 1,
  "conditions": [],
  "actions": [],
  "metadata": {}
}
```

## Creating Custom Rules

### Step 1: Define Rule Structure
1. Add your rule to a JSON file in `arx_svg_parser/data/sample_rules/` or your own directory.
2. Follow the JSON schema for rule validation
3. Include all required fields and optional metadata

### Step 2: Define Conditions
Conditions specify when the rule should be triggered:

```json
{
  "type": "property",
  "element_type": "room",
  "property": "area",
  "operator": ">",
  "value": 100
}
```

### Step 3: Define Actions
Actions specify what happens when conditions are met:

```json
{
  "type": "validation",
  "message": "Room area exceeds maximum allowed",
  "severity": "error",
  "code_reference": "BUILDING_CODE_101"
}
```

## Rule Categories

### Spatial Rules
- **Area Requirements**: Room size and area constraints
- **Height Requirements**: Ceiling height and clearance
- **Distance Requirements**: Minimum distances between elements
- **Layout Requirements**: Spatial arrangement rules

### Property Rules
- **Material Properties**: Material specifications and requirements
- **System Properties**: System performance requirements
- **Component Properties**: Component specifications
- **Connection Properties**: Connection requirements

### Relationship Rules
- **Connection Rules**: Element connection requirements
- **Dependency Rules**: Element dependency relationships
- **Hierarchy Rules**: Element hierarchy requirements
- **Grouping Rules**: Element grouping requirements

## Rule Examples

### Fire Safety Rule
```json
{
  "rule_id": "fire_safety_exit_001",
  "name": "Fire Exit Requirements",
  "description": "Ensures proper fire exit configuration",
  "category": "fire_safety",
  "priority": 1,
  "conditions": [
    {
      "type": "spatial",
      "element_type": "room",
      "property": "area",
      "operator": ">",
      "value": 200
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
      "message": "Large rooms require multiple exits",
      "severity": "error",
      "code_reference": "NFPA_101_7.1"
    }
  ],
  "metadata": {
    "jurisdiction": "US",
    "code_version": "2020",
    "source": "NFPA 101"
  }
}
```

### Energy Efficiency Rule
```json
{
  "rule_id": "energy_efficiency_insulation_001",
  "name": "Insulation Requirements",
  "description": "Validates insulation requirements for energy efficiency",
  "category": "energy_efficiency",
  "priority": 2,
  "conditions": [
    {
      "type": "property",
      "element_type": "wall",
      "property": "r_value",
      "operator": "<",
      "value": 13
    }
  ],
  "actions": [
    {
      "type": "validation",
      "message": "Wall insulation below minimum R-value",
      "severity": "warning",
      "code_reference": "ASHRAE_90.1_5.1"
    }
  ],
  "metadata": {
    "jurisdiction": "US",
    "code_version": "2019",
    "source": "ASHRAE 90.1"
  }
}
```

## Rule Engine Integration

### Loading Rules
```python
from arx_svg_parser.services.rule_engine import RuleEngine

# Load rules from JSON files
rule_engine = RuleEngine()
rule_engine.load_rules_from_directory("data/sample_rules/")

# Load specific rule file
rule_engine.load_rules_from_file("custom_rules.json")
```

### Executing Rules
```python
# Execute rules against BIM model
results = rule_engine.execute_rules(bim_model)

# Process results
for result in results:
    print(f"Rule: {result.rule_id}")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
```

### Rule Validation
```python
# Validate rule syntax
is_valid = rule_engine.validate_rule(rule_data)

# Validate rule logic
logic_valid = rule_engine.validate_rule_logic(rule_data)
```

## Advanced Rule Features

### Composite Conditions
```json
{
  "type": "composite",
  "operator": "AND",
  "conditions": [
    {
      "type": "property",
      "element_type": "room",
      "property": "area",
      "operator": ">",
      "value": 100
    },
    {
      "type": "property",
      "element_type": "room",
      "property": "occupancy",
      "operator": ">",
      "value": 50
    }
  ]
}
```

### Custom Actions
```json
{
  "type": "custom",
  "action_name": "calculate_egress_width",
  "parameters": {
    "occupancy_factor": 0.3,
    "minimum_width": 44
  }
}
```

### Rule Templates
```json
{
  "template_id": "area_requirement_template",
  "name": "Area Requirement Template",
  "description": "Template for area-based requirements",
  "parameters": {
    "element_type": "string",
    "max_area": "number",
    "message": "string"
  },
  "conditions": [
    {
      "type": "property",
      "element_type": "${element_type}",
      "property": "area",
      "operator": ">",
      "value": "${max_area}"
    }
  ],
  "actions": [
    {
      "type": "validation",
      "message": "${message}",
      "severity": "error"
    }
  ]
}
```

## Rule Development Best Practices

### Rule Design
- **Clear Naming**: Use descriptive rule names
- **Detailed Descriptions**: Explain rule purpose and requirements
- **Proper Categorization**: Use appropriate rule categories
- **Priority Setting**: Set appropriate rule priorities

### Condition Design
- **Specific Conditions**: Make conditions as specific as possible
- **Logical Operators**: Use appropriate logical operators
- **Value Ranges**: Use appropriate value ranges
- **Element Types**: Use correct element type references

### Action Design
- **Clear Messages**: Write clear and actionable messages
- **Appropriate Severity**: Use appropriate severity levels
- **Code References**: Include relevant code references
- **Actionable Results**: Provide actionable results

### Testing Rules
- **Unit Testing**: Test individual rules
- **Integration Testing**: Test rule combinations
- **Edge Case Testing**: Test edge cases and boundaries
- **Performance Testing**: Test rule performance

## Rule Management

### Version Control
- **Rule Versioning**: Track rule versions
- **Change Tracking**: Track rule changes
- **Review Process**: Implement rule review process
- **Deployment**: Manage rule deployment

### Rule Testing
- **Test Cases**: Create comprehensive test cases
- **Test Data**: Use realistic test data
- **Test Scenarios**: Test various scenarios
- **Test Results**: Document test results

### Rule Documentation
- **Rule Purpose**: Document rule purpose
- **Rule Logic**: Document rule logic
- **Rule Examples**: Provide rule examples
- **Rule Maintenance**: Document maintenance procedures

## Troubleshooting

### Common Issues
1. **Invalid JSON**: Check JSON syntax and structure
2. **Missing Fields**: Ensure all required fields are present
3. **Invalid References**: Check element type references
4. **Logic Errors**: Verify rule logic and conditions

### Debugging Tools
- **Rule Validator**: Validate rule syntax and structure
- **Rule Tester**: Test rules with sample data
- **Rule Logger**: Log rule execution details
- **Rule Analyzer**: Analyze rule performance and impact

### Performance Optimization
- **Rule Ordering**: Optimize rule execution order
- **Condition Optimization**: Optimize condition evaluation
- **Caching**: Cache rule evaluation results
- **Parallel Processing**: Use parallel rule execution
