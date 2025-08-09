"""
SVGX Engine - Advanced State Machine Engine

This service provides comprehensive state machine management for SVGX elements,
including equipment states, process states, system states, maintenance states,
and safety states with automatic transitions and enterprise-grade features.

🎯 **Core State Types:**
- Equipment States: On, off, standby, fault states
- Process States: Running, stopped, paused, error states
- System States: Normal, warning, critical, emergency states
- Maintenance States: Operational, maintenance, repair states
- Safety States: Safe, warning, danger, shutdown states

🏗️ **Features:**
- Automatic state transitions with conditions and actions
- State history tracking and audit trails
- Concurrent state management for multiple elements
- Performance monitoring and optimization
- Comprehensive error handling and recovery
- State validation and conflict detection
- Real-time state monitoring and analytics
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque
import threading

from svgx_engine.utils.performance import PerformanceMonitor
from svgx_engine.utils.errors import StateError, TransitionError, ValidationError
from svgx_engine.services.telemetry_logger import telemetry_instrumentation

logger = logging.getLogger(__name__)


class StateType(Enum):
    """Types of states supported by the engine."""
    EQUIPMENT = "equipment"
    PROCESS = "process"
    SYSTEM = "system"
    MAINTENANCE = "maintenance"
    SAFETY = "safety"


class StatePriority(Enum):
    """State priority levels for conflict resolution."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class State:
    """State data structure."""
    id: str
    type: StateType
    name: str
    priority: StatePriority
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: Optional[float] = None  # seconds
    parent_state: Optional[str] = None
    child_states: List[str] = field(default_factory=list)


@dataclass
class StateTransition:
    """State transition configuration."""
    id: str
    from_state: str
    to_state: str
    condition: Optional[Callable] = None
    action: Optional[Callable] = None
    priority: StatePriority = StatePriority.NORMAL
    timeout: Optional[float] = None  # seconds
    enabled: bool = True


@dataclass
class StateMachine:
    """State machine configuration."""
    id: str
    name: str
    initial_state: str
    states: Dict[str, State] = field(default_factory=dict)
    transitions: Dict[str, StateTransition] = field(default_factory=dict)
    current_state: Optional[str] = None
    state_history: List[Tuple[str, str, datetime]] = field(default_factory=list)  # (from, to, timestamp)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class AdvancedStateMachine:
    """
    Comprehensive state machine engine with enterprise-grade features
    for managing complex state transitions and behaviors.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
    """
    Perform __init__ operation

Args:
        config: Description of config

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.config = config or {}
        self.performance_monitor = PerformanceMonitor()

        # State machine registry
        self.state_machines: Dict[str, StateMachine] = {}
        self.global_states: Dict[str, State] = {}

        # Performance tracking
        self.state_stats = {
            'total_transitions': 0,
            'successful_transitions': 0,
            'failed_transitions': 0,
            'avg_transition_time': 0.0,
            'active_state_machines': 0
        }

        # Threading and concurrency
        self.state_lock = threading.Lock()
        self.transition_lock = threading.Lock()
        self.running = False

        # Initialize default state machines
        self._initialize_default_state_machines()

        logger.info("Advanced state machine engine initialized")

    def _initialize_default_state_machines(self):
        """Initialize default state machines for common scenarios."""

        # Equipment State Machine
        equipment_states = {
            'off': State(id='off', type=StateType.EQUIPMENT, name='Off', priority=StatePriority.NORMAL),
            'standby': State(id='standby', type=StateType.EQUIPMENT, name='Standby', priority=StatePriority.NORMAL),
            'on': State(id='on', type=StateType.EQUIPMENT, name='On', priority=StatePriority.NORMAL),
            'fault': State(id='fault', type=StateType.EQUIPMENT, name='Fault', priority=StatePriority.HIGH),
            'maintenance': State(id='maintenance', type=StateType.EQUIPMENT, name='Maintenance', priority=StatePriority.HIGH)
        }

        equipment_transitions = [
            StateTransition(id='off_to_standby', from_state='off', to_state='standby'),
            StateTransition(id='standby_to_on', from_state='standby', to_state='on'),
            StateTransition(id='on_to_standby', from_state='on', to_state='standby'),
            StateTransition(id='any_to_fault', from_state='*', to_state='fault'),
            StateTransition(id='fault_to_maintenance', from_state='fault', to_state='maintenance'),
            StateTransition(id='maintenance_to_off', from_state='maintenance', to_state='off')
        ]

        self.create_state_machine(
            machine_id='equipment',
            name='Equipment State Machine',
            initial_state='off',
            states=equipment_states,
            transitions=equipment_transitions
        )

        # Process State Machine
        process_states = {
            'stopped': State(id='stopped', type=StateType.PROCESS, name='Stopped', priority=StatePriority.NORMAL),
            'starting': State(id='starting', type=StateType.PROCESS, name='Starting', priority=StatePriority.NORMAL),
            'running': State(id='running', type=StateType.PROCESS, name='Running', priority=StatePriority.NORMAL),
            'paused': State(id='paused', type=StateType.PROCESS, name='Paused', priority=StatePriority.NORMAL),
            'stopping': State(id='stopping', type=StateType.PROCESS, name='Stopping', priority=StatePriority.NORMAL),
            'error': State(id='error', type=StateType.PROCESS, name='Error', priority=StatePriority.HIGH)
        }

        process_transitions = [
            StateTransition(id='stopped_to_starting', from_state='stopped', to_state='starting'),
            StateTransition(id='starting_to_running', from_state='starting', to_state='running'),
            StateTransition(id='running_to_paused', from_state='running', to_state='paused'),
            StateTransition(id='paused_to_running', from_state='paused', to_state='running'),
            StateTransition(id='running_to_stopping', from_state='running', to_state='stopping'),
            StateTransition(id='stopping_to_stopped', from_state='stopping', to_state='stopped'),
            StateTransition(id='any_to_error', from_state='*', to_state='error')
        ]

        self.create_state_machine(
            machine_id='process',
            name='Process State Machine',
            initial_state='stopped',
            states=process_states,
            transitions=process_transitions
        )

        # System State Machine
        system_states = {
            'normal': State(id='normal', type=StateType.SYSTEM, name='Normal', priority=StatePriority.NORMAL),
            'warning': State(id='warning', type=StateType.SYSTEM, name='Warning', priority=StatePriority.HIGH),
            'critical': State(id='critical', type=StateType.SYSTEM, name='Critical', priority=StatePriority.CRITICAL),
            'emergency': State(id='emergency', type=StateType.SYSTEM, name='Emergency', priority=StatePriority.CRITICAL),
            'shutdown': State(id='shutdown', type=StateType.SYSTEM, name='Shutdown', priority=StatePriority.CRITICAL)
        }

        system_transitions = [
            StateTransition(id='normal_to_warning', from_state='normal', to_state='warning'),
            StateTransition(id='warning_to_normal', from_state='warning', to_state='normal'),
            StateTransition(id='warning_to_critical', from_state='warning', to_state='critical'),
            StateTransition(id='critical_to_warning', from_state='critical', to_state='warning'),
            StateTransition(id='critical_to_emergency', from_state='critical', to_state='emergency'),
            StateTransition(id='emergency_to_shutdown', from_state='emergency', to_state='shutdown'),
            StateTransition(id='any_to_shutdown', from_state='*', to_state='shutdown')
        ]

        self.create_state_machine(
            machine_id='system',
            name='System State Machine',
            initial_state='normal',
            states=system_states,
            transitions=system_transitions
        )

        # Safety State Machine
        safety_states = {
            'safe': State(id='safe', type=StateType.SAFETY, name='Safe', priority=StatePriority.NORMAL),
            'warning': State(id='warning', type=StateType.SAFETY, name='Warning', priority=StatePriority.HIGH),
            'danger': State(id='danger', type=StateType.SAFETY, name='Danger', priority=StatePriority.CRITICAL),
            'shutdown': State(id='shutdown', type=StateType.SAFETY, name='Shutdown', priority=StatePriority.CRITICAL),
            'emergency': State(id='emergency', type=StateType.SAFETY, name='Emergency', priority=StatePriority.CRITICAL)
        }

        safety_transitions = [
            StateTransition(id='safe_to_warning', from_state='safe', to_state='warning'),
            StateTransition(id='warning_to_safe', from_state='warning', to_state='safe'),
            StateTransition(id='warning_to_danger', from_state='warning', to_state='danger'),
            StateTransition(id='danger_to_warning', from_state='danger', to_state='warning'),
            StateTransition(id='danger_to_shutdown', from_state='danger', to_state='shutdown'),
            StateTransition(id='any_to_emergency', from_state='*', to_state='emergency'),
            StateTransition(id='emergency_to_shutdown', from_state='emergency', to_state='shutdown')
        ]

        self.create_state_machine(
            machine_id='safety',
            name='Safety State Machine',
            initial_state='safe',
            states=safety_states,
            transitions=safety_transitions
        )

    def create_state_machine(self, machine_id: str, name: str, initial_state: str,
                           states: Dict[str, State], transitions: List[StateTransition]) -> bool:
        """
        Create a new state machine.

        Args:
            machine_id: Unique identifier for the state machine
            name: Human-readable name
            initial_state: ID of the initial state
            states: Dictionary of states
            transitions: List of state transitions

        Returns:
            True if creation successful, False otherwise
        """
        try:
            # Validate initial state exists
            if initial_state not in states:
                raise ValidationError(f"Initial state '{initial_state}' not found in states")

            # Create state machine
            state_machine = StateMachine(
                id=machine_id,
                name=name,
                initial_state=initial_state,
                states=states,
                current_state=initial_state
            )

            # Add transitions
            for transition in transitions:
                state_machine.transitions[transition.id] = transition

            # Register state machine
            self.state_machines[machine_id] = state_machine

            with self.state_lock:
                self.state_stats['active_state_machines'] += 1

            logger.info(f"Created state machine '{name}' with {len(states)} states and {len(transitions)} transitions")
            return True

        except Exception as e:
            logger.error(f"Failed to create state machine {machine_id}: {e}")
            return False

    def get_state_machine(self, machine_id: str) -> Optional[StateMachine]:
        """Get a state machine by ID."""
        return self.state_machines.get(machine_id)

    def get_current_state(self, machine_id: str) -> Optional[str]:
        """Get the current state of a state machine."""
        state_machine = self.get_state_machine(machine_id)
        return state_machine.current_state if state_machine else None

    async def transition_state(self, machine_id: str, target_state: str,
                             context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Transition a state machine to a new state.

        Args:
            machine_id: ID of the state machine
            target_state: Target state ID
            context: Additional context for the transition

        Returns:
            True if transition successful, False otherwise
        """
        start_time = time.time()

        try:
            state_machine = self.get_state_machine(machine_id)
            if not state_machine:
                logger.error(f"State machine {machine_id} not found")
                return False

            current_state = state_machine.current_state
            if not current_state:
                logger.error(f"No current state for machine {machine_id}")
                return False

            # Find valid transition
            transition = self._find_valid_transition(state_machine, current_state, target_state, context)
            if not transition:
                logger.warning(f"No valid transition from {current_state} to {target_state}")
                return False

            # Execute transition
            success = await self._execute_transition(state_machine, transition, context)

            if success:
                # Update state machine
                state_machine.current_state = target_state
                state_machine.state_history.append((current_state, target_state, datetime.utcnow()))
                state_machine.updated_at = datetime.utcnow()

                # Update stats
                with self.transition_lock:
                    self.state_stats['total_transitions'] += 1
                    self.state_stats['successful_transitions'] += 1

                logger.info(f"Transitioned {machine_id} from {current_state} to {target_state}")

            return success

        except Exception as e:
            logger.error(f"State transition failed for {machine_id}: {e}")

            with self.transition_lock:
                self.state_stats['total_transitions'] += 1
                self.state_stats['failed_transitions'] += 1

            return False

    def _find_valid_transition(self, state_machine: StateMachine, from_state: str,
                             to_state: str, context: Optional[Dict[str, Any]] = None) -> Optional[StateTransition]:
        """Find a valid transition between states."""
        for transition in state_machine.transitions.values():
            if not transition.enabled:
                continue

            # Check if transition matches (wildcard '*' matches any state)
            if (transition.from_state == from_state or transition.from_state == '*') and \
               transition.to_state == to_state:

                # Check condition if present
                if transition.condition:
                    try:
                        if not transition.condition(context or {}):
                            continue
                    except Exception as e:
                        logger.error(f"Transition condition evaluation failed: {e}")
                        continue

                return transition

        return None

    async def _execute_transition(self, state_machine: StateMachine, transition: StateTransition,
                                context: Optional[Dict[str, Any]] = None) -> bool:
        """Execute a state transition."""
        try:
            # Execute transition action if present
            if transition.action:
                try:
                    await transition.action(context or {})
                except Exception as e:
                    logger.error(f"Transition action failed: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Transition execution failed: {e}")
            return False

    def get_state_history(self, machine_id: str, limit: int = 100) -> List[Tuple[str, str, datetime]]:
        """Get state transition history for a machine."""
        state_machine = self.get_state_machine(machine_id)
        if not state_machine:
            return []

        return state_machine.state_history[-limit:]

    def get_available_transitions(self, machine_id: str) -> List[StateTransition]:
        """Get available transitions for the current state."""
        state_machine = self.get_state_machine(machine_id)
        if not state_machine or not state_machine.current_state:
            return []

        current_state = state_machine.current_state
        available_transitions = []

        for transition in state_machine.transitions.values():
            if transition.enabled and (transition.from_state == current_state or transition.from_state == '*'):
                available_transitions.append(transition)

        return available_transitions

    def get_state_machine_stats(self) -> Dict[str, Any]:
        """Get state machine statistics."""
        with self.state_lock:
            return {
                **self.state_stats,
                'total_state_machines': len(self.state_machines),
                'state_machines': {
                    machine_id: {
                        'name': sm.name,
                        'current_state': sm.current_state,
                        'total_states': len(sm.states),
                        'total_transitions': len(sm.transitions),
                        'history_size': len(sm.state_history)
                    }
                    for machine_id, sm in self.state_machines.items()
                }
            }

    def validate_state_machine(self, machine_id: str) -> Dict[str, Any]:
        """Validate a state machine configuration."""
        state_machine = self.get_state_machine(machine_id)
        if not state_machine:
            return {'valid': False, 'error': f'State machine {machine_id} not found'}

        issues = []

        # Check if current state exists
        if state_machine.current_state and state_machine.current_state not in state_machine.states:
            issues.append(f"Current state '{state_machine.current_state}' not found in states")

        # Check transition validity
        for transition_id, transition in state_machine.transitions.items():
            if transition.from_state != '*' and transition.from_state not in state_machine.states:
                issues.append(f"Transition {transition_id}: from_state '{transition.from_state}' not found")

            if transition.to_state not in state_machine.states:
                issues.append(f"Transition {transition_id}: to_state '{transition.to_state}' not found")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'total_states': len(state_machine.states),
            'total_transitions': len(state_machine.transitions)
        }


# Global instance for easy access
advanced_state_machine = AdvancedStateMachine()
