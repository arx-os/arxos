# SVGX Advanced Behavior Engine

## Overview

The SVGX Advanced Behavior Engine is a comprehensive system for managing complex behaviors in SVGX elements. It provides rule engines, state machines, time-based triggers, and advanced condition evaluation to enable CAD-parity behaviors and infrastructure simulation.

## Features

### 1. Rule Engines
- **Complex Logic Evaluation**: Multi-condition rule evaluation with priority ordering
- **Business Rules**: Business logic rule evaluation
- **Safety Rules**: Safety condition rule evaluation
- **Operational Rules**: Operational procedure rules
- **Maintenance Rules**: Maintenance schedule rules
- **Compliance Rules**: Regulatory compliance rules

### 2. State Machines
- **Equipment States**: On, off, standby, fault states
- **Process States**: Running, stopped, paused, error states
- **System States**: Normal, warning, critical, emergency states
- **Maintenance States**: Operational, maintenance, repair states
- **Safety States**: Safe, warning, danger, shutdown states

### 3. Time-Based Triggers
- **Scheduled Events**: Time-based behavior triggers
- **Duration-based**: Behavior based on elapsed time
- **Cyclic Events**: Repeating time-based behaviors
- **Sequential Events**: Ordered time-based behaviors
- **Delayed Events**: Time-delayed behavior execution

### 4. Advanced Condition Evaluation
- **Threshold Logic**: Value-based condition evaluation
- **Time-based Logic**: Time-dependent condition evaluation
- **Spatial Logic**: Location-based condition evaluation
- **Relational Logic**: Relationship-based condition evaluation
- **Complex Logic**: Multi-condition logical evaluation

### 5. CAD-Parity Behaviors
- **Dimensioning Behavior**: Automatic dimension generation
- **Constraint Behavior**: Geometric constraint application
- **Snap Behavior**: Object snapping behavior
- **Selection Behavior**: CAD-style object selection
- **Editing Behavior**: CAD-style object editing

### 6. Infrastructure Simulation Behaviors
- **HVAC Behavior**: Heating, ventilation, and air conditioning
- **Electrical Behavior**: Power distribution and lighting
- **Plumbing Behavior**: Water flow and pressure
- **Fire Protection**: Fire suppression system behavior
- **Security Behavior**: Access control and surveillance

## Architecture

```
AdvancedBehaviorEngine
├── Rules Engine
│   ├── BehaviorRule
│   ├── Rule Evaluation
│   └── Priority Management
├── State Machines
│   ├── BehaviorState
│   ├── State Transitions
│   └── Entry/Exit Actions
├── Time Triggers
│   ├── TimeTrigger
│   ├── Scheduling
│   └── Execution
├── Condition Evaluation
│   ├── Threshold Conditions
│   ├── Time Conditions
│   ├── Spatial Conditions
│   ├── Relational Conditions
│   └── Complex Conditions
└── Action Execution
    ├── Update Actions
    ├── Animate Actions
    ├── Calculate Actions
    ├── CAD-Parity Actions
    └── Infrastructure Actions
```

## Usage Examples

### 1. Basic Rule Registration

```python
from svgx_engine.runtime.advanced_behavior_engine import (
    AdvancedBehaviorEngine, BehaviorRule, RuleType
)

# Create behavior engine
engine = AdvancedBehaviorEngine()

# Create a safety rule
safety_rule = BehaviorRule(
    rule_id='temperature_alert',
    rule_type=RuleType.SAFETY,
    conditions=[
        {
            'type': 'threshold',
            'variable': 'temperature',
            'operator': '>',
            'threshold': 80.0
        }
    ],
    actions=[
        {
            'type': 'update',
            'target_property': 'alert_level',
            'value': 'critical'
        },
        {
            'type': 'log',
            'message': 'Temperature critical: {temperature}°C',
            'level': 'error'
        }
    ],
    priority=3
)

# Register the rule
engine.register_rule(safety_rule)
```

### 2. State Machine Registration

```python
from svgx_engine.runtime.advanced_behavior_engine import BehaviorState, StateType

# Create state machine for equipment
states = [
    BehaviorState(
        state_id='off',
        state_type=StateType.EQUIPMENT,
        properties={'power': False, 'status': 'inactive'},
        transitions=[
            {
                'target_state': 'on',
                'conditions': [
                    {
                        'type': 'simple',
                        'variable': 'power_command',
                        'operator': '==',
                        'value': 'start'
                    }
                ]
            }
        ],
        entry_actions=[
            {
                'type': 'update',
                'target_property': 'power_status',
                'value': 'off'
            }
        ],
        exit_actions=[
            {
                'type': 'log',
                'message': 'Equipment shutting down',
                'level': 'info'
            }
        ]
    ),
    BehaviorState(
        state_id='on',
        state_type=StateType.EQUIPMENT,
        properties={'power': True, 'status': 'active'},
        transitions=[
            {
                'target_state': 'off',
                'conditions': [
                    {
                        'type': 'simple',
                        'variable': 'power_command',
                        'operator': '==',
                        'value': 'stop'
                    }
                ]
            }
        ],
        entry_actions=[
            {
                'type': 'update',
                'target_property': 'power_status',
                'value': 'on'
            }
        ]
    )
]

# Register state machine
engine.register_state_machine('equipment_001', states, 'off')
```

### 3. Time-Based Triggers

```python
from svgx_engine.runtime.advanced_behavior_engine import TimeTrigger
from datetime import datetime, timedelta

# Create cyclic maintenance trigger
maintenance_trigger = TimeTrigger(
    trigger_id='daily_maintenance',
    schedule_type='cyclic',
    schedule_data={
        'interval': 86400,  # 24 hours
        'start_time': datetime.now()
    },
    actions=[
        {
            'type': 'update',
            'target_property': 'last_maintenance',
            'value': datetime.now().isoformat()
        },
        {
            'type': 'log',
            'message': 'Daily maintenance check performed',
            'level': 'info'
        }
    ]
)

# Register time trigger
engine.register_time_trigger(maintenance_trigger)
```

### 4. Complex Condition Evaluation

```python
from svgx_engine.runtime.advanced_behavior_engine import Condition

# Create complex condition
complex_condition = Condition(
    condition_id='environmental_check',
    condition_type='complex',
    expression='temperature > 25 and humidity < 60 and pressure > 100',
    parameters={
        'temperature': 30,
        'humidity': 45,
        'pressure': 101.3
    },
    operators=['and', 'or']
)

# Register condition
engine.register_condition(complex_condition)
```

### 5. CAD-Parity Actions

```python
# CAD-parity action for dimensioning
cad_action = {
    'type': 'cad_parity',
    'cad_action_type': 'dimension',
    'dimension_type': 'linear',
    'start_point': {'x': 0, 'y': 0},
    'end_point': {'x': 100, 'y': 0},
    'precision': 0.1
}

# Infrastructure action for HVAC
infrastructure_action = {
    'type': 'infrastructure',
    'system_type': 'hvac',
    'hvac_action': 'temperature_control',
    'target_temperature': 22.0,
    'tolerance': 1.0
}
```

### 6. Integration with SVGX Runtime

```python
from svgx_engine.runtime import SVGXRuntime

# Create runtime with advanced behavior engine
runtime = SVGXRuntime()

# Start advanced behavior engine
runtime.start_advanced_behavior_engine()

# Register advanced behavior for an element
behavior_config = {
    'rules': [
        {
            'rule_id': 'safety_rule',
            'rule_type': 'safety',
            'conditions': [
                {
                    'type': 'threshold',
                    'variable': 'temperature',
                    'operator': '>',
                    'threshold': 80.0
                }
            ],
            'actions': [
                {
                    'type': 'update',
                    'target_property': 'alert_level',
                    'value': 'critical'
                }
            ],
            'priority': 3
        }
    ],
    'state_machine': {
        'states': [
            {
                'state_id': 'normal',
                'state_type': 'equipment',
                'properties': {'status': 'normal'},
                'transitions': []
            }
        ],
        'initial_state': 'normal'
    }
}

runtime.register_advanced_behavior('element_001', behavior_config)

# Evaluate behaviors
context = {
    'element_id': 'element_001',
    'temperature': 85.0,
    'status': 'active'
}

applicable_rules = await runtime.evaluate_advanced_behaviors('element_001', context)
```

## Condition Types

### 1. Threshold Conditions
```python
{
    'type': 'threshold',
    'variable': 'temperature',
    'operator': '>',  # ==, !=, >, <, >=, <=
    'threshold': 30.0
}
```

### 2. Time Conditions
```python
{
    'type': 'time',
    'time_type': 'current',  # current, duration, schedule
    'start_time': datetime.now() - timedelta(hours=1),
    'end_time': datetime.now() + timedelta(hours=1)
}
```

### 3. Spatial Conditions
```python
{
    'type': 'spatial',
    'spatial_type': 'proximity',  # proximity, containment, intersection
    'target_position': {'x': 10, 'y': 20, 'z': 0},
    'max_distance': 5.0
}
```

### 4. Relational Conditions
```python
{
    'type': 'relational',
    'relation_type': 'dependency',  # dependency, hierarchy, connection
    'dependent_element': 'parent_element',
    'required_status': 'active'
}
```

### 5. Complex Conditions
```python
{
    'type': 'complex',
    'expression': 'temperature > 30 and humidity < 60',
    'variables': {
        'temperature': 35,
        'humidity': 45
    }
}
```

## Action Types

### 1. Update Actions
```python
{
    'type': 'update',
    'target_property': 'alert_level',
    'value': 'critical'
}
```

### 2. Animate Actions
```python
{
    'type': 'animate',
    'animation_type': 'motion',
    'duration': 1.0,
    'properties': {
        'position': {'x': 100, 'y': 200},
        'rotation': 45.0
    }
}
```

### 3. Calculate Actions
```python
{
    'type': 'calculate',
    'formula': 'temperature * 1.8 + 32',
    'target_variable': 'temperature_fahrenheit'
}
```

### 4. CAD-Parity Actions
```python
{
    'type': 'cad_parity',
    'cad_action_type': 'dimension',
    'dimension_type': 'linear',
    'start_point': {'x': 0, 'y': 0},
    'end_point': {'x': 100, 'y': 0}
}
```

### 5. Infrastructure Actions
```python
{
    'type': 'infrastructure',
    'system_type': 'hvac',
    'hvac_action': 'temperature_control',
    'target_temperature': 22.0
}
```

## Performance Considerations

### 1. Rule Caching
- Rules are cached for performance
- Rule evaluation is optimized for frequent conditions
- Priority-based rule ordering reduces unnecessary evaluations

### 2. State Machine Optimization
- State transitions are validated before execution
- Entry/exit actions are executed efficiently
- State properties are updated atomically

### 3. Time Trigger Efficiency
- Time triggers are scheduled efficiently
- Next execution times are calculated once
- Trigger execution is batched when possible

### 4. Condition Evaluation
- Simple conditions are evaluated first
- Complex conditions use cached results
- Spatial calculations use optimized algorithms

## Error Handling

### 1. Rule Evaluation Errors
- Invalid conditions return False
- Missing variables are handled gracefully
- Rule execution errors are logged

### 2. State Transition Errors
- Invalid transitions are rejected
- Missing states are handled
- State machine errors are logged

### 3. Time Trigger Errors
- Invalid schedules are handled
- Execution errors are logged
- Trigger recovery is automatic

### 4. Action Execution Errors
- Action errors are isolated
- Failed actions are logged
- System continues operation

## Monitoring and Debugging

### 1. Status Monitoring
```python
# Get engine status
status = engine.get_advanced_behavior_status()
print(f"Engine running: {status['running']}")
print(f"Registered rules: {status['registered_rules']}")
print(f"State machines: {status['registered_state_machines']}")
print(f"Time triggers: {status['registered_time_triggers']}")
```

### 2. Element State Monitoring
```python
# Get element state
state = engine.get_element_state('element_001')
print(f"Current state: {state}")
```

### 3. Rule Evaluation Monitoring
```python
# Monitor rule evaluation
applicable_rules = await engine.evaluate_rules('element_001', context)
for rule in applicable_rules:
    print(f"Rule {rule['rule_id']} applied with priority {rule['priority']}")
```

## Best Practices

### 1. Rule Design
- Use clear, descriptive rule IDs
- Set appropriate priorities
- Keep conditions simple and focused
- Test rules thoroughly

### 2. State Machine Design
- Use meaningful state names
- Define clear transition conditions
- Include entry/exit actions
- Handle error states

### 3. Time Trigger Design
- Use appropriate intervals
- Consider system load
- Handle timezone issues
- Test trigger execution

### 4. Condition Design
- Use appropriate condition types
- Keep expressions simple
- Test edge cases
- Document complex logic

### 5. Action Design
- Use appropriate action types
- Keep actions focused
- Handle errors gracefully
- Log important actions

## Integration with SVGX

### 1. SVGX Element Integration
```xml
<rect x="10" y="10" width="100" height="50"
      arx:object="equipment.pump.main"
      arx:behavior="advanced_behavior_engine"
      arx:behavior_config="pump_behavior.json"/>
```

### 2. Behavior Configuration Files
```json
{
  "rules": [
    {
      "rule_id": "pump_safety",
      "rule_type": "safety",
      "conditions": [
        {
          "type": "threshold",
          "variable": "pressure",
          "operator": ">",
          "threshold": 100.0
        }
      ],
      "actions": [
        {
          "type": "update",
          "target_property": "status",
          "value": "shutdown"
        }
      ],
      "priority": 3
    }
  ],
  "state_machine": {
    "states": [
      {
        "state_id": "running",
        "state_type": "equipment",
        "properties": {"status": "running"},
        "transitions": []
      }
    ],
    "initial_state": "running"
  }
}
```

## Future Enhancements

### 1. AI-Powered Behaviors
- Machine learning integration
- Predictive behavior modeling
- Adaptive rule generation
- Intelligent state transitions

### 2. Advanced Physics Integration
- Real-time physics simulation
- Force-based behaviors
- Collision detection
- Material properties

### 3. External System Integration
- IoT device integration
- CMMS system integration
- BMS system integration
- SCADA system integration

### 4. Advanced Visualization
- Real-time behavior visualization
- State transition animations
- Rule execution visualization
- Performance monitoring dashboards

## Conclusion

The SVGX Advanced Behavior Engine provides a comprehensive foundation for complex behavior management in SVGX elements. It enables CAD-parity behaviors, infrastructure simulation, and advanced rule-based systems while maintaining performance and reliability.

The engine is designed to be extensible, allowing for future enhancements while providing a stable foundation for current use cases. Its modular architecture makes it easy to integrate with existing SVGX systems and extend with new capabilities as needed.
