# BuildingOps: The Complete Building Operations Stack

## Overview

BuildingOps is ArxOS's unified approach to building management that combines CLI commands, natural language processing, visual workflows (n8n), and physical hardware control into a single, cohesive platform. Every interaction ultimately resolves to ArxOS paths, whether typed in terminal, spoken naturally, or dragged-and-dropped.

## The Three Interfaces, One System

```
User Intent → ArxOS Path → Physical Action

1. CLI:      "arx set /B1/3/HVAC/DAMPER-01 position:50"
2. Natural:  "Set conference room temperature to 72"
3. Visual:   [Drag Temperature Node] → [Connect to Damper Node]
                          ↓
               All resolve to paths
                          ↓
              Physical hardware responds
```

## CLI Command Reference

### Core Command Structure

```bash
arx [verb] [path] [parameters] [options]
```

### Query Commands (Read Operations)

```bash
# Basic queries
arx get /B1/3/SENSORS/TEMP-01
arx query /B1/*/SENSORS/*
arx list /B1/3/CONF-301

# Advanced queries
arx query /B1/*/SENSORS/TEMP-* --above 75
arx query /B1/3/*/HVAC/* --status failed
arx find --type sensor --building B1 --floor 3

# Live monitoring
arx watch /B1/3/SENSORS/* --interval 5s
arx monitor /B1/3/*/ENERGY/* --graph

# Historical data
arx history /B1/3/HVAC/UNIT-01 --days 7
arx trends /B1/*/ENERGY/* --compare yesterday
```

### Control Commands (Write Operations)

```bash
# Direct control
arx set /B1/3/HVAC/DAMPER-01 position:50
arx set /B1/3/LIGHTS/ZONE-A brightness:75
arx set /B1/3/DOORS/MAIN state:locked

# Batch operations
arx set /B1/*/LIGHTS/* state:off
arx set /B1/3/*/HVAC/* mode:eco
arx apply --file weekend-settings.yaml

# Scene control
arx scene /B1/3/CONF-301 presentation
arx scene /B1/* night-mode
arx scene --save current-state --name comfortable

# Scheduled operations
arx schedule /B1/*/LIGHTS/* off --at "10:00 PM"
arx schedule /B1/3/HVAC/* eco --days "Sat,Sun"
```

### Natural Language Commands

```bash
# AI-interpreted commands
arx do "turn off all lights on floor 3"
arx do "set conference room to presentation mode"
arx do "prepare building for weekend"
arx do "optimize energy usage"

# Context-aware commands
arx do "make it cooler" --room /B1/3/CONF-301
arx do "save energy" --building B1
arx do "secure the building"

# Complex operations
arx do "if temperature above 75, increase cooling"
arx do "turn on lights where motion detected"
```

### Workflow Commands

```bash
# Workflow management
arx workflow list
arx workflow run emergency-shutdown
arx workflow trigger comfort-mode --room /B1/3/CONF-301
arx workflow create --from-template hvac-optimization

# n8n integration
arx workflow connect --n8n-url http://localhost:5678
arx workflow import my-workflow.json
arx workflow export comfort-control --format n8n

# Testing workflows
arx workflow test fire-evacuation --dry-run
arx workflow simulate power-failure
```

### Building Management Commands

```bash
# Building operations
arx building status B1
arx building shutdown B1 --emergency
arx building optimize B1 --target energy

# Floor operations
arx floor /B1/3 --lights off
arx floor /B1/3 --hvac eco
arx floor /B1/3 --secure

# Zone operations
arx zone /B1/3/EAST --evacuate
arx zone /B1/*/PUBLIC --lights auto
```

### Diagnostic Commands

```bash
# System health
arx health /B1
arx diagnose /B1/3/HVAC/*
arx test /B1/3/SENSORS/*

# Troubleshooting
arx troubleshoot /B1/3/HVAC/UNIT-01
arx validate /B1/*/SAFETY/*
arx calibrate /B1/3/SENSORS/TEMP-*
```

## Natural Language Processing

### How Natural Language Maps to Paths

```yaml
Input Processing Pipeline:
  1. Intent Recognition
     "Set conference room temperature to 72"
     → Intent: set_temperature
     → Location: conference room
     → Value: 72

  2. Path Resolution
     "conference room" → Database lookup → /B1/3/CONF-301
     "temperature" → Equipment type → /HVAC/SETPOINT

  3. Command Generation
     Final: arx set /B1/3/CONF-301/HVAC/SETPOINT value:72
```

### Natural Language Examples

```bash
# Temperature control
"Make it warmer" → arx set ./HVAC/SETPOINT +2
"Too cold in here" → arx set ./HVAC/SETPOINT +3
"Set temperature to 72" → arx set ./HVAC/SETPOINT 72

# Lighting control
"Lights on" → arx set ./LIGHTS/* state:on
"Dim the lights" → arx set ./LIGHTS/* brightness:30
"Presentation mode" → arx scene . presentation

# Complex commands
"Turn off everything except emergency lights" →
  arx set ./* state:off --except */EMERGENCY/*

"If anyone is in the room, turn on lights" →
  arx do "query ./SENSORS/MOTION && set ./LIGHTS state:on"
```

## Visual Workflow Integration (n8n)

### How Workflows Execute Physical Actions

```yaml
n8n Visual Flow:
  [Temperature Sensor] → [Decision: > 75°F] → [Damper Control: Open 50%]

Execution Path:
  1. n8n polls: GET /api/v1/path/B1/3/SENSORS/TEMP-01
  2. n8n evaluates: if value > 75
  3. n8n commands: POST /api/v1/control/B1/3/HVAC/DAMPER-01
     Body: {"action": "position", "value": 50}
  4. ArxOS routes to gateway
  5. Gateway sends to TinyGo device
  6. Physical damper moves
```

### Available n8n Operations

```yaml
Sensor Nodes (Inputs):
  - Temperature/Humidity Reader
  - Motion/Occupancy Detector
  - Energy Monitor
  - Air Quality Sensor
  - Light Level Sensor
  - Equipment Status

Action Nodes (Outputs):
  - HVAC Control (temp, dampers, fans)
  - Lighting Control (on/off/dim/color)
  - Access Control (lock/unlock)
  - Motor Control (blinds, valves)
  - Alert/Notification
  - Scene Activation

Logic Nodes:
  - Path Pattern Matcher
  - Threshold Trigger
  - Schedule Timer
  - State Machine
  - Aggregator
  - PID Controller
```

## Implementation Architecture

### Command Processing Pipeline

```go
// internal/cli/processor.go
type CommandProcessor struct {
    nlp        *NLPInterpreter
    pathEngine *PathEngine
    validator  *SafetyValidator
    executor   *CommandExecutor
}

func (cp *CommandProcessor) Process(input string) error {
    // 1. Parse command type
    cmd := cp.parseCommand(input)

    // 2. Natural language processing if needed
    if cmd.Type == "natural" {
        cmd = cp.nlp.Interpret(cmd.Raw)
    }

    // 3. Resolve paths
    paths, err := cp.pathEngine.Resolve(cmd.PathPattern)
    if err != nil {
        return err
    }

    // 4. Validate safety
    for _, path := range paths {
        if err := cp.validator.Check(path, cmd); err != nil {
            return fmt.Errorf("safety check failed: %w", err)
        }
    }

    // 5. Execute command
    return cp.executor.Execute(paths, cmd)
}
```

### Path Resolution Engine

```go
// internal/engine/paths.go
type PathEngine struct {
    db        *database.DB
    cache     *PathCache
    aliases   map[string]string
}

func (pe *PathEngine) Resolve(pattern string) ([]string, error) {
    // Handle natural language references
    if !strings.HasPrefix(pattern, "/") {
        pattern = pe.resolveAlias(pattern)
    }

    // Expand wildcards
    if strings.Contains(pattern, "*") {
        return pe.expandWildcard(pattern)
    }

    // Handle relative paths
    if strings.HasPrefix(pattern, "./") {
        pattern = pe.makeAbsolute(pattern)
    }

    return []string{pattern}, nil
}

// Examples:
// "conference room" → "/B1/3/CONF-301"
// "/B1/*/LIGHTS/*" → ["/B1/1/LIGHTS/...", "/B1/2/LIGHTS/...", ...]
// "./HVAC/*" → "/B1/3/CURRENT-ROOM/HVAC/*"
```

### Safety Validation Layer

```go
// internal/safety/validator.go
type SafetyValidator struct {
    rules      []SafetyRule
    interlocks map[string]bool
}

func (sv *SafetyValidator) Check(path string, cmd Command) error {
    // Emergency interlocks
    if sv.interlocks["emergency_active"] && !cmd.Override {
        return ErrEmergencyActive
    }

    // Equipment-specific rules
    if strings.Contains(path, "/FIRE_DOORS/") {
        if sv.interlocks["fire_alarm"] {
            return ErrFireDoorsLocked
        }
    }

    // Rate limiting for mechanical equipment
    if sv.isRateLimited(path) {
        return ErrRateLimited
    }

    // Range validation
    if cmd.Action == "position" {
        if cmd.Value < 0 || cmd.Value > 100 {
            return ErrOutOfRange
        }
    }

    return nil
}
```

## Real-World Scenarios

### Scenario 1: Meeting Room Automation

```bash
# Via CLI
arx scene /B1/3/CONF-301 meeting-start

# Via Natural Language
arx do "prepare conference room for meeting"

# Via n8n Workflow
Calendar Trigger → Room Preparation Workflow → Physical Actions

# All result in:
- Lights: 70% brightness
- Blinds: 50% closed
- HVAC: Comfort mode
- Display: On
- Door: Unlocked
```

### Scenario 2: Emergency Response

```bash
# Via CLI
arx workflow trigger emergency-evacuation --building B1

# Via Natural Language
arx do "emergency evacuation now"

# Via n8n Workflow
Fire Alarm Input → Emergency Workflow → Multiple Actions

# All result in:
- All doors: Unlocked
- Emergency lights: On
- HVAC: Shutdown
- Elevators: Ground floor
- Alarms: Activated
```

### Scenario 3: Energy Optimization

```bash
# Via CLI
arx optimize /B1 --target energy --aggressive

# Via Natural Language
arx do "reduce energy consumption by 20%"

# Via n8n Workflow
Schedule → Energy Optimization → Gradual Adjustments

# All result in:
- Unoccupied rooms: Minimal HVAC
- Lighting: Motion-activated only
- Equipment: Standby mode
- Blinds: Optimize for natural light
```

## Testing and Simulation

### Dry Run Mode

```bash
# Test commands without physical execution
arx set /B1/*/LIGHTS/* off --dry-run
arx workflow trigger emergency --simulate

# Simulation mode
arx simulate --scenario power-failure --duration 1h
arx simulate --load-profile typical-monday
```

### Virtual Devices

```go
// testing/virtual_device.go
type VirtualDevice struct {
    Path     string
    Type     string
    State    map[string]interface{}
    History  []Command
}

func (vd *VirtualDevice) Execute(cmd Command) {
    // Simulate physical action
    vd.State[cmd.Action] = cmd.Value
    vd.History = append(vd.History, cmd)

    // Log for testing
    log.Printf("VIRTUAL: %s → %s = %v", vd.Path, cmd.Action, cmd.Value)
}
```

## Performance Considerations

### Command Response Times

```yaml
Target Performance:
  - CLI command parsing: < 10ms
  - Path resolution: < 50ms
  - Natural language: < 200ms
  - Physical actuation: < 2s
  - Visual workflow: < 5s

Optimization Strategies:
  - Path caching in memory
  - Pre-compiled safety rules
  - Gateway command batching
  - Device state caching
  - Async physical operations
```

## Security Model

### Permission Levels

```yaml
BuildingOps Roles:
  Admin:
    - All commands allowed
    - Override safety interlocks
    - Create/modify workflows

  Operator:
    - Control commands allowed
    - Cannot override safety
    - Execute workflows

  Viewer:
    - Query commands only
    - No control operations
    - Read-only access

  Guest:
    - Limited query access
    - Specific paths only
```

## Future Enhancements

### Planned Features

```yaml
Version 2.0:
  - Voice control integration
  - AR/VR visualization
  - Predictive control AI
  - Multi-building orchestration
  - Mobile app with gestures

Version 3.0:
  - Autonomous optimization
  - Blockchain audit trail
  - Quantum-safe encryption
  - Digital twin sync
  - Neural building control
```

## Conclusion

BuildingOps unifies all building control interfaces into a single, path-based system. Whether using CLI commands, natural language, or visual workflows, every operation resolves to ArxOS paths that trigger real physical actions. This creates a powerful, flexible, and intuitive building management platform that scales from simple sensors to complex automation scenarios.

The key innovation is that **the terminal, the AI, and the visual interface all speak the same language: paths**. This makes BuildingOps not just a building management system, but a complete building operating system where software directly controls physical reality.