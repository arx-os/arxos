# Constraint System

**Last Updated:** November 2025

---

## Overview

The constraint system validates equipment placements against real-world requirements including structural support, spatial clearance, building codes, budget limits, and user preferences.

---

## Constraint Types

### Structural Constraints

Validate that equipment is placed in locations with adequate structural support.

**Example:**
```yaml
constraints:
  structural:
    - type: wall_support
      floor: 0
      valid_areas:
        - bbox:
            min: {x: 5.0, y: 5.0, z: 0.0}
            max: {x: 15.0, y: 15.0, z: 3.0}
          load_capacity: 50.0  # kg
          notes: "Concrete wall - supports up to 50kg"
```

**Use Cases:**
- Heavy equipment requiring wall mounting
- Interactive boards that need structural support
- HVAC units with weight requirements

### Spatial Constraints

Enforce minimum clearance and proximity rules.

**Example:**
```yaml
constraints:
  spatial:
    - type: clearance
      min_clearance: 0.5  # meters
      equipment_type: "Electrical"
      notes: "Minimum 0.5m clearance for electrical safety"
    - type: clearance
      min_clearance: 1.0
      max_proximity: 3.0
      equipment_type: "HVAC"
```

**Use Cases:**
- Maintenance access requirements
- Safety clearance zones
- Equipment spacing for airflow

### Code Constraints

Ensure compliance with building codes and regulations.

**Example:**
```yaml
constraints:
  code:
    - type: "ADA"
      requirement: "Accessibility compliance required"
      is_mandatory: true
      equipment_type: "Safety"
    - type: "Fire Safety"
      requirement: "Must maintain 1.2m exit path width"
      is_mandatory: true
```

**Use Cases:**
- ADA accessibility requirements
- Fire safety egress paths
- Local building code compliance

### Budget Constraints

Enforce cost limits and track spending.

**Example:**
```yaml
constraints:
  budget:
    - max_cost: 50000.0  # total budget
      cost_per_item:
        "IFCLIGHTFIXTURE": 150.0
        "IFCAIRTERMINAL": 300.0
```

---

## Constraint Severity Levels

- **Info** - Informational, suggestions only
- **Warning** - Should be addressed but not blocking
- **Error** - Must be resolved before proceeding
- **Critical** - Cannot proceed with violation

---

## Validation Process

1. **Load Constraints** - From YAML file or building metadata
2. **Check Each Placement** - Validate against all applicable constraints
3. **Report Violations** - Group by severity with suggestions
4. **Update Game State** - Track validations and violations
5. **Generate Summary** - Total counts, critical issues, recommendations

---

## Best Practices

1. **Define constraints early** - Before planning begins
2. **Document thoroughly** - Explain why constraints exist
3. **Test constraints** - Validate against known good placements
4. **Version control** - Track constraint changes in Git
5. **Review regularly** - Update constraints as requirements change

