# Object Reference

## Overview

This document provides a comprehensive reference for all objects and data structures used in the Arxos platform.

## Symbol Objects

### Basic Symbol Structure
```json
{
  "id": "hvac_unit_001",
  "name": "HVAC Unit",
  "system": "mechanical",
  "category": "hvac",
  "description": "Air handling unit for commercial buildings",
  "svg": {
    "content": "<g id=\"hvac\">...</g>",
    "viewBox": "0 0 100 100",
    "width": 100,
    "height": 100
  },
  "properties": {
    "capacity": "5000 CFM",
    "voltage": "480V",
    "efficiency": "95%",
    "manufacturer": "Carrier",
    "model": "48TC"
  },
  "connections": [
    {
      "id": "conn_001",
      "type": "electrical",
      "position": {"x": 10, "y": 20},
      "properties": {
        "voltage": "480V",
        "amperage": "20A"
      }
    },
    {
      "id": "conn_002",
      "type": "ductwork",
      "position": {"x": 50, "y": 30},
      "properties": {
        "diameter": "12 inches",
        "material": "galvanized steel"
      }
    }
  ],
  "metadata": {
    "version": "1.0",
    "created": "2024-01-01T00:00:00Z",
    "modified": "2024-01-15T10:30:00Z",
    "author": "system",
    "funding_source": "federal_grant_2024",
    "tags": ["hvac", "mechanical", "air-handling"]
  }
}
```

### Symbol Properties
```json
{
  "properties": {
    "physical": {
      "width": "24 inches",
      "height": "36 inches",
      "depth": "18 inches",
      "weight": "150 lbs"
    },
    "electrical": {
      "voltage": "480V",
      "amperage": "20A",
      "phase": "3",
      "frequency": "60Hz"
    },
    "mechanical": {
      "capacity": "5000 CFM",
      "efficiency": "95%",
      "noise_level": "65 dB"
    },
    "operational": {
      "temperature_range": "55-85°F",
      "humidity_range": "30-70%",
      "maintenance_interval": "6 months"
    }
  }
}
```

### Symbol Connections
```json
{
  "connections": [
    {
      "id": "conn_001",
      "name": "Electrical Supply",
      "type": "electrical",
      "position": {"x": 10, "y": 20},
      "direction": "input",
      "properties": {
        "voltage": "480V",
        "amperage": "20A",
        "phase": "3",
        "connection_type": "hardwired"
      },
      "compatibility": ["electrical_panel", "circuit_breaker"],
      "metadata": {
        "created": "2024-01-01T00:00:00Z",
        "modified": "2024-01-15T10:30:00Z"
      }
    },
    {
      "id": "conn_002",
      "name": "Supply Air",
      "type": "ductwork",
      "position": {"x": 50, "y": 30},
      "direction": "output",
      "properties": {
        "diameter": "12 inches",
        "material": "galvanized steel",
        "insulation": "R-8",
        "air_flow": "5000 CFM"
      },
      "compatibility": ["air_duct", "air_handler"],
      "metadata": {
        "created": "2024-01-01T00:00:00Z",
        "modified": "2024-01-15T10:30:00Z"
      }
    }
  ]
}
```

## BIM Objects

### BIM Element Structure
```json
{
  "id": "bim_element_001",
  "type": "IfcAirTerminal",
  "name": "HVAC Unit - Floor 1",
  "description": "Air handling unit for first floor",
  "position": {
    "x": 100.5,
    "y": 200.3,
    "z": 0.0
  },
  "dimensions": {
    "width": 24.0,
    "height": 36.0,
    "depth": 18.0
  },
  "properties": {
    "capacity": "5000 CFM",
    "voltage": "480V",
    "efficiency": "95%"
  },
  "relationships": [
    {
      "type": "connected_to",
      "target_id": "electrical_panel_001",
      "relationship_type": "electrical_supply"
    },
    {
      "type": "connected_to",
      "target_id": "air_duct_001",
      "relationship_type": "air_supply"
    }
  ],
  "metadata": {
    "created": "2024-01-01T00:00:00Z",
    "modified": "2024-01-15T10:30:00Z",
    "author": "user@example.com",
    "project_id": "building_001"
  }
}
```

### BIM Property Sets
```json
{
  "property_sets": {
    "Pset_AirTerminalTypeCommon": {
      "AirFlowRate": "5000 CFM",
      "NominalPower": "5.0 kW",
      "Efficiency": "95%"
    },
    "Pset_AirTerminalTypeMechanical": {
      "FanType": "Centrifugal",
      "FanEfficiency": "85%",
      "NoiseLevel": "65 dB"
    },
    "Pset_AirTerminalTypeElectrical": {
      "Voltage": "480V",
      "Current": "20A",
      "Phase": "3"
    }
  }
}
```

## Rule Objects

### Rule Definition
```json
{
  "rule_id": "fire_safety_egress_001",
  "name": "Fire Safety Egress Requirements",
  "description": "Ensures proper egress routes for fire safety compliance",
  "category": "fire_safety",
  "priority": 1,
  "version": "1.0",
  "jurisdiction": {
    "country": "US",
    "state": "FL",
    "city": "Miami"
  },
  "conditions": [
    {
      "id": "cond_001",
      "type": "spatial",
      "element_type": "room",
      "property": "area",
      "operator": ">",
      "value": 100,
      "unit": "sq_ft"
    },
    {
      "id": "cond_002",
      "type": "relationship",
      "element_type": "door",
      "relationship": "connected_to",
      "target_type": "exit",
      "min_count": 2
    }
  ],
  "actions": [
    {
      "id": "action_001",
      "type": "validation",
      "message": "Large rooms require minimum of 2 exit doors",
      "severity": "error",
      "code_reference": "NFPA 101 Section 7.1",
      "suggested_fix": "Add additional exit door or reduce room area"
    }
  ],
  "metadata": {
    "created": "2024-01-01T00:00:00Z",
    "modified": "2024-01-15T10:30:00Z",
    "author": "code_official@city.gov",
    "status": "active",
    "tags": ["fire_safety", "egress", "compliance"]
  }
}
```

### Rule Condition
```json
{
  "id": "cond_001",
  "name": "Room Area Check",
  "type": "spatial",
  "element_type": "room",
  "property": "area",
  "operator": ">",
  "value": 100,
  "unit": "sq_ft",
  "description": "Check if room area exceeds 100 square feet",
  "parameters": {
    "tolerance": 5.0,
    "include_hallways": false,
    "include_storage": true
  }
}
```

### Rule Action
```json
{
  "id": "action_001",
  "name": "Egress Validation",
  "type": "validation",
  "message": "Large rooms require minimum of 2 exit doors",
  "severity": "error",
  "code_reference": "NFPA 101 Section 7.1",
  "suggested_fix": "Add additional exit door or reduce room area",
  "parameters": {
    "auto_fix": false,
    "requires_review": true,
    "notification_required": true
  }
}
```

## Project Objects

### Project Structure
```json
{
  "project_id": "building_001",
  "name": "Downtown Office Building",
  "description": "10-story commercial office building with retail space",
  "type": "commercial",
  "status": "design",
  "version": "1.0.0",
  "location": {
    "address": "123 Main Street",
    "city": "Miami",
    "state": "FL",
    "zip": "33101",
    "country": "US",
    "coordinates": {
      "latitude": 25.7617,
      "longitude": -80.1918
    }
  },
  "dimensions": {
    "floors": 10,
    "height": 120.0,
    "area": 50000.0,
    "unit": "sq_ft"
  },
  "systems": [
    "mechanical",
    "electrical",
    "plumbing",
    "fire_safety",
    "security"
  ],
  "permissions": {
    "owner": "architect@firm.com",
    "editors": [
      "engineer@firm.com",
      "designer@firm.com"
    ],
    "viewers": [
      "client@company.com",
      "contractor@company.com"
    ]
  },
  "metadata": {
    "created": "2024-01-01T00:00:00Z",
    "modified": "2024-01-15T10:30:00Z",
    "created_by": "architect@firm.com",
    "tags": ["commercial", "office", "downtown", "10-floors"]
  }
}
```

### Project Configuration
```json
{
  "project_id": "building_001",
  "configuration": {
    "units": "imperial",
    "coordinate_system": "local",
    "precision": 0.01,
    "default_symbol_library": "../arx-symbol-library",
    "validation_rules": [
      "fire_safety_rules.json",
      "structural_rules.json",
      "energy_rules.json"
    ],
    "export_formats": ["ifc", "svg", "pdf", "json"],
    "auto_save": true,
    "auto_validate": true
  },
  "sync": {
    "enabled": true,
    "remote_path": "/projects/building_001",
    "include_patterns": ["*.json", "*.svg", "*.bim"],
    "exclude_patterns": ["*.tmp", "*.log", "node_modules/"],
    "conflict_resolution": "auto"
  },
  "notifications": {
    "email": ["architect@firm.com", "engineer@firm.com"],
    "webhook": "https://hooks.slack.com/...",
    "events": ["validation_errors", "sync_complete", "project_modified"]
  }
}
```

## User Objects

### User Profile
```json
{
  "user_id": "user_001",
  "username": "architect@firm.com",
  "email": "architect@firm.com",
  "first_name": "John",
  "last_name": "Smith",
  "role": "architect",
  "organization": "Smith & Associates",
  "permissions": {
    "projects": ["create", "read", "update", "delete"],
    "symbols": ["create", "read", "update", "delete"],
    "rules": ["create", "read", "update", "delete"],
    "reports": ["create", "read", "update", "delete"]
  },
  "preferences": {
    "units": "imperial",
    "theme": "dark",
    "language": "en",
    "timezone": "America/New_York",
    "notifications": {
      "email": true,
      "web": true,
      "mobile": false
    }
  },
  "metadata": {
    "created": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z",
    "status": "active",
    "subscription": "professional"
  }
}
```

### User Session
```json
{
  "session_id": "session_001",
  "user_id": "user_001",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2024-01-15T11:30:00Z",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "permissions": {
    "projects": ["read", "update"],
    "symbols": ["read", "update"],
    "rules": ["read"],
    "reports": ["read"]
  },
  "metadata": {
    "created": "2024-01-15T10:30:00Z",
    "last_activity": "2024-01-15T10:30:00Z"
  }
}
```

## Report Objects

### Validation Report
```json
{
  "report_id": "validation_001",
  "project_id": "building_001",
  "type": "validation",
  "status": "completed",
  "summary": {
    "total_checks": 150,
    "passed": 145,
    "failed": 3,
    "warnings": 2,
    "errors": 1
  },
  "results": [
    {
      "rule_id": "fire_safety_egress_001",
      "status": "failed",
      "severity": "error",
      "message": "Large rooms require minimum of 2 exit doors",
      "element_id": "room_001",
      "location": {
        "floor": 1,
        "x": 100.5,
        "y": 200.3
      },
      "suggested_fix": "Add additional exit door or reduce room area",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "metadata": {
    "created": "2024-01-15T10:30:00Z",
    "created_by": "architect@firm.com",
    "duration": 45.2,
    "rules_applied": ["fire_safety_rules.json", "structural_rules.json"]
  }
}
```

### Export Report
```json
{
  "report_id": "export_001",
  "project_id": "building_001",
  "type": "export",
  "format": "ifc",
  "status": "completed",
  "summary": {
    "elements_exported": 1250,
    "symbols_exported": 150,
    "rules_applied": 25,
    "file_size": "2.5 MB"
  },
  "files": [
    {
      "name": "building_001.ifc",
      "size": "2.5 MB",
      "url": "/exports/building_001.ifc",
      "expires_at": "2024-01-22T10:30:00Z"
    }
  ],
  "metadata": {
    "created": "2024-01-15T10:30:00Z",
    "created_by": "architect@firm.com",
    "duration": 120.5,
    "options": {
      "include_properties": true,
      "include_relationships": true,
      "include_metadata": true
    }
  }
}
```
