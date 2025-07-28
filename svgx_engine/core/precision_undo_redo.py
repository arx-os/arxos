"""
Precision-Aware Undo/Redo System

This module provides a comprehensive undo/redo system that preserves
precision information and validation state during geometric operations.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from copy import deepcopy

from .precision_coordinate import PrecisionCoordinate, CoordinateValidator
from .precision_math import PrecisionMath
from .precision_validator import PrecisionValidator, ValidationLevel, ValidationType
from .precision_config import PrecisionConfig, config_manager

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of geometric operations that can be undone/redone"""
    CREATE = "create"
    DELETE = "delete"
    MODIFY = "modify"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    CORRECT = "correct"
    BATCH = "batch"


class StateType(Enum):
    """Types of state that can be stored"""
    GEOMETRY = "geometry"
    COORDINATES = "coordinates"
    VALIDATION = "validation"
    PRECISION = "precision"
    CONFIGURATION = "configuration"


@dataclass
class PrecisionState:
    """Represents a precision-aware state snapshot"""
    timestamp: float
    operation_type: OperationType
    state_type: StateType
    object_id: str
    data: Dict[str, Any]
    precision_level: str
    validation_status: str
    precision_violations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate state after initialization"""
        if not self.object_id:
            raise ValueError("Object ID is required")
        if not self.data:
            raise ValueError("State data is required")


@dataclass
class UndoRedoEntry:
    """Represents a single undo/redo entry"""
    entry_id: str
    timestamp: float
    operation_type: OperationType
    description: str
    before_state: Optional[PrecisionState] = None
    after_state: Optional[PrecisionState] = None
    precision_config: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate entry after initialization"""
        if not self.entry_id:
            raise ValueError("Entry ID is required")
        if not self.description:
            raise ValueError("Description is required")


class PrecisionUndoRedo:
    """Manages precision-aware undo/redo operations"""
    
    def __init__(self, config: Optional[PrecisionConfig] = None):
        """Initialize the precision undo/redo system"""
        self.config = config or config_manager.get_default_config()
        self.undo_stack: List[UndoRedoEntry] = []
        self.redo_stack: List[UndoRedoEntry] = []
        self.max_stack_size = 100
        self.precision_math = PrecisionMath()
        self.coordinate_validator = CoordinateValidator()
        self.precision_validator = PrecisionValidator()
        
        # State tracking
        self.current_state: Dict[str, Any] = {}
        self.state_history: List[PrecisionState] = []
        
        # Performance tracking
        self.operation_count = 0
        self.total_operations = 0
    
    def create_state(self, object_id: str, data: Dict[str, Any], 
                    operation_type: OperationType, state_type: StateType) -> PrecisionState:
        """Create a precision-aware state snapshot"""
        try:
            # Validate data
            if not data:
                raise ValueError("State data cannot be empty")
            
            # Create precision state
            state = PrecisionState(
                timestamp=time.time(),
                operation_type=operation_type,
                state_type=state_type,
                object_id=object_id,
                data=deepcopy(data),
                precision_level=self.config.precision_level.value,
                validation_status='unknown'
            )
            
            # Validate state if it contains coordinates
            if 'coordinates' in data or 'precision_coordinates' in data:
                validation_result = self._validate_state_coordinates(state)
                state.validation_status = 'valid' if validation_result['is_valid'] else 'invalid'
                state.precision_violations = validation_result.get('precision_violations', [])
            
            return state
            
        except Exception as e:
            logger.error(f"Failed to create precision state: {e}")
            raise
    
    def _validate_state_coordinates(self, state: PrecisionState) -> Dict[str, Any]:
        """Validate coordinates in a state"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'precision_violations': []
        }
        
        try:
            # Check for precision coordinates
            if 'precision_coordinates' in state.data:
                for i, coord_data in enumerate(state.data['precision_coordinates']):
                    if isinstance(coord_data, dict):
                        coord = PrecisionCoordinate(coord_data['x'], coord_data['y'], coord_data.get('z', 0.0))
                    else:
                        coord = coord_data  # Assume it's already a PrecisionCoordinate
                    
                    coord_validation = self.coordinate_validator.validate_coordinate(coord)
                    if not coord_validation.is_valid:
                        validation_result['is_valid'] = False
                        validation_result['errors'].append(f"Coordinate {i}: {coord_validation.errors}")
                    
                    # Check precision violations
                    precision_violations = self._check_precision_violations(coord)
                    if precision_violations:
                        validation_result['precision_violations'].extend(precision_violations)
            
            # Check for legacy coordinates
            elif 'coordinates' in state.data:
                for i, coord in enumerate(state.data['coordinates']):
                    if isinstance(coord, list) and len(coord) >= 2:
                        precision_coord = PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0)
                        
                        coord_validation = self.coordinate_validator.validate_coordinate(precision_coord)
                        if not coord_validation.is_valid:
                            validation_result['is_valid'] = False
                            validation_result['errors'].append(f"Coordinate {i}: {coord_validation.errors}")
                        
                        # Check precision violations
                        precision_violations = self._check_precision_violations(precision_coord)
                        if precision_violations:
                            validation_result['precision_violations'].extend(precision_violations)
        
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _check_precision_violations(self, coord: PrecisionCoordinate) -> List[str]:
        """Check for precision violations in a coordinate"""
        violations = []
        precision_value = self.config.get_precision_value()
        
        # Check if coordinates are properly rounded to precision level
        if abs(coord.x - round(coord.x / precision_value) * precision_value) > 1e-10:
            violations.append(f"X-coordinate {coord.x} not at precision level {precision_value}")
        if abs(coord.y - round(coord.y / precision_value) * precision_value) > 1e-10:
            violations.append(f"Y-coordinate {coord.y} not at precision level {precision_value}")
        if abs(coord.z - round(coord.z / precision_value) * precision_value) > 1e-10:
            violations.append(f"Z-coordinate {coord.z} not at precision level {precision_value}")
        
        return violations
    
    def push_operation(self, operation_type: OperationType, description: str,
                      before_state: Optional[PrecisionState] = None,
                      after_state: Optional[PrecisionState] = None) -> str:
        """Push an operation to the undo stack"""
        try:
            # Generate entry ID
            entry_id = f"{operation_type.value}_{self.operation_count}_{int(time.time())}"
            
            # Create undo/redo entry
            entry = UndoRedoEntry(
                entry_id=entry_id,
                timestamp=time.time(),
                operation_type=operation_type,
                description=description,
                before_state=before_state,
                after_state=after_state,
                precision_config=self.config.to_dict(),
                validation_result=self._validate_entry(entry_id, before_state, after_state)
            )
            
            # Add to undo stack
            self.undo_stack.append(entry)
            
            # Clear redo stack (new operation invalidates redo)
            self.redo_stack.clear()
            
            # Maintain stack size
            if len(self.undo_stack) > self.max_stack_size:
                self.undo_stack.pop(0)
            
            self.operation_count += 1
            self.total_operations += 1
            
            logger.info(f"Pushed operation: {description} (ID: {entry_id})")
            return entry_id
            
        except Exception as e:
            logger.error(f"Failed to push operation: {e}")
            raise
    
    def _validate_entry(self, entry_id: str, before_state: Optional[PrecisionState], 
                       after_state: Optional[PrecisionState]) -> Dict[str, Any]:
        """Validate an undo/redo entry"""
        validation_result = {
            'entry_id': entry_id,
            'is_valid': True,
            'before_state_valid': True,
            'after_state_valid': True,
            'precision_preserved': True,
            'errors': []
        }
        
        try:
            # Validate before state
            if before_state:
                before_validation = self._validate_state_coordinates(before_state)
                validation_result['before_state_valid'] = before_validation['is_valid']
                if not before_validation['is_valid']:
                    validation_result['errors'].append(f"Before state validation failed: {before_validation['errors']}")
            
            # Validate after state
            if after_state:
                after_validation = self._validate_state_coordinates(after_state)
                validation_result['after_state_valid'] = after_validation['is_valid']
                if not after_validation['is_valid']:
                    validation_result['errors'].append(f"After state validation failed: {after_validation['errors']}")
            
            # Check precision preservation
            if before_state and after_state:
                precision_preserved = self._check_precision_preservation(before_state, after_state)
                validation_result['precision_preserved'] = precision_preserved
                if not precision_preserved:
                    validation_result['errors'].append("Precision not preserved between states")
            
            # Overall validation
            validation_result['is_valid'] = (
                validation_result['before_state_valid'] and
                validation_result['after_state_valid'] and
                validation_result['precision_preserved']
            )
        
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _check_precision_preservation(self, before_state: PrecisionState, 
                                    after_state: PrecisionState) -> bool:
        """Check if precision is preserved between states"""
        try:
            # Compare precision levels
            if before_state.precision_level != after_state.precision_level:
                return False
            
            # Compare precision coordinates if available
            if 'precision_coordinates' in before_state.data and 'precision_coordinates' in after_state.data:
                before_coords = before_state.data['precision_coordinates']
                after_coords = after_state.data['precision_coordinates']
                
                if len(before_coords) != len(after_coords):
                    return False
                
                for i, (before_coord, after_coord) in enumerate(zip(before_coords, after_coords)):
                    if isinstance(before_coord, dict):
                        before_precision = PrecisionCoordinate(before_coord['x'], before_coord['y'], before_coord.get('z', 0.0))
                    else:
                        before_precision = before_coord
                    
                    if isinstance(after_coord, dict):
                        after_precision = PrecisionCoordinate(after_coord['x'], after_coord['y'], after_coord.get('z', 0.0))
                    else:
                        after_precision = after_coord
                    
                    # Check if precision is maintained
                    precision_value = self.config.get_precision_value()
                    if (abs(before_precision.x - after_precision.x) > precision_value or
                        abs(before_precision.y - after_precision.y) > precision_value or
                        abs(before_precision.z - after_precision.z) > precision_value):
                        return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking precision preservation: {e}")
            return False
    
    def undo(self) -> Optional[UndoRedoEntry]:
        """Undo the last operation"""
        if not self.undo_stack:
            logger.warning("No operations to undo")
            return None
        
        try:
            # Pop the last operation
            entry = self.undo_stack.pop()
            
            # Validate the entry before undoing
            if not self._validate_entry_for_undo(entry):
                logger.error(f"Invalid entry for undo: {entry.entry_id}")
                return None
            
            # Add to redo stack
            self.redo_stack.append(entry)
            
            # Perform the undo operation
            self._perform_undo(entry)
            
            logger.info(f"Undid operation: {entry.description} (ID: {entry.entry_id})")
            return entry
            
        except Exception as e:
            logger.error(f"Failed to undo operation: {e}")
            # Restore the entry to undo stack
            if 'entry' in locals():
                self.undo_stack.append(entry)
            raise
    
    def redo(self) -> Optional[UndoRedoEntry]:
        """Redo the last undone operation"""
        if not self.redo_stack:
            logger.warning("No operations to redo")
            return None
        
        try:
            # Pop the last redo operation
            entry = self.redo_stack.pop()
            
            # Validate the entry before redoing
            if not self._validate_entry_for_redo(entry):
                logger.error(f"Invalid entry for redo: {entry.entry_id}")
                return None
            
            # Add back to undo stack
            self.undo_stack.append(entry)
            
            # Perform the redo operation
            self._perform_redo(entry)
            
            logger.info(f"Redid operation: {entry.description} (ID: {entry.entry_id})")
            return entry
            
        except Exception as e:
            logger.error(f"Failed to redo operation: {e}")
            # Restore the entry to redo stack
            if 'entry' in locals():
                self.redo_stack.append(entry)
            raise
    
    def _validate_entry_for_undo(self, entry: UndoRedoEntry) -> bool:
        """Validate an entry for undo operation"""
        try:
            # Check if entry has required data
            if not entry.before_state:
                logger.error(f"Entry {entry.entry_id} has no before state")
                return False
            
            # Validate before state
            validation_result = self._validate_state_coordinates(entry.before_state)
            if not validation_result['is_valid']:
                logger.error(f"Before state validation failed for entry {entry.entry_id}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating entry for undo: {e}")
            return False
    
    def _validate_entry_for_redo(self, entry: UndoRedoEntry) -> bool:
        """Validate an entry for redo operation"""
        try:
            # Check if entry has required data
            if not entry.after_state:
                logger.error(f"Entry {entry.entry_id} has no after state")
                return False
            
            # Validate after state
            validation_result = self._validate_state_coordinates(entry.after_state)
            if not validation_result['is_valid']:
                logger.error(f"After state validation failed for entry {entry.entry_id}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating entry for redo: {e}")
            return False
    
    def _perform_undo(self, entry: UndoRedoEntry):
        """Perform the actual undo operation"""
        try:
            if entry.before_state:
                # Restore the before state
                self._restore_state(entry.before_state)
                
                # Update current state tracking
                self.current_state[entry.before_state.object_id] = entry.before_state.data
                
                # Add to state history
                self.state_history.append(entry.before_state)
        
        except Exception as e:
            logger.error(f"Error performing undo: {e}")
            raise
    
    def _perform_redo(self, entry: UndoRedoEntry):
        """Perform the actual redo operation"""
        try:
            if entry.after_state:
                # Restore the after state
                self._restore_state(entry.after_state)
                
                # Update current state tracking
                self.current_state[entry.after_state.object_id] = entry.after_state.data
                
                # Add to state history
                self.state_history.append(entry.after_state)
        
        except Exception as e:
            logger.error(f"Error performing redo: {e}")
            raise
    
    def _restore_state(self, state: PrecisionState):
        """Restore a state to the system"""
        try:
            # Validate state before restoration
            validation_result = self._validate_state_coordinates(state)
            if not validation_result['is_valid'] and self.config.should_fail_on_violation():
                raise ValueError(f"Cannot restore invalid state: {validation_result['errors']}")
            
            # Apply state restoration logic here
            # This would typically involve updating the geometry engine
            logger.info(f"Restored state for object {state.object_id}")
        
        except Exception as e:
            logger.error(f"Error restoring state: {e}")
            raise
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return len(self.redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of the next undo operation"""
        if self.can_undo():
            return self.undo_stack[-1].description
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of the next redo operation"""
        if self.can_redo():
            return self.redo_stack[-1].description
        return None
    
    def clear_history(self):
        """Clear all undo/redo history"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.state_history.clear()
        self.current_state.clear()
        logger.info("Cleared undo/redo history")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get undo/redo system statistics"""
        return {
            'undo_stack_size': len(self.undo_stack),
            'redo_stack_size': len(self.redo_stack),
            'total_operations': self.total_operations,
            'operation_count': self.operation_count,
            'max_stack_size': self.max_stack_size,
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'next_undo': self.get_undo_description(),
            'next_redo': self.get_redo_description()
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export the current undo/redo state"""
        return {
            'timestamp': time.time(),
            'config': self.config.to_dict(),
            'statistics': self.get_statistics(),
            'undo_stack': [self._serialize_entry(entry) for entry in self.undo_stack],
            'redo_stack': [self._serialize_entry(entry) for entry in self.redo_stack],
            'current_state': self.current_state
        }
    
    def import_state(self, state_data: Dict[str, Any]):
        """Import undo/redo state"""
        try:
            # Clear current state
            self.clear_history()
            
            # Import configuration
            if 'config' in state_data:
                self.config = PrecisionConfig.from_dict(state_data['config'])
            
            # Import stacks
            if 'undo_stack' in state_data:
                for entry_data in state_data['undo_stack']:
                    entry = self._deserialize_entry(entry_data)
                    self.undo_stack.append(entry)
            
            if 'redo_stack' in state_data:
                for entry_data in state_data['redo_stack']:
                    entry = self._deserialize_entry(entry_data)
                    self.redo_stack.append(entry)
            
            # Import current state
            if 'current_state' in state_data:
                self.current_state = state_data['current_state']
            
            logger.info("Successfully imported undo/redo state")
        
        except Exception as e:
            logger.error(f"Failed to import undo/redo state: {e}")
            raise
    
    def _serialize_entry(self, entry: UndoRedoEntry) -> Dict[str, Any]:
        """Serialize an undo/redo entry"""
        return {
            'entry_id': entry.entry_id,
            'timestamp': entry.timestamp,
            'operation_type': entry.operation_type.value,
            'description': entry.description,
            'before_state': asdict(entry.before_state) if entry.before_state else None,
            'after_state': asdict(entry.after_state) if entry.after_state else None,
            'precision_config': entry.precision_config,
            'validation_result': entry.validation_result,
            'metadata': entry.metadata
        }
    
    def _deserialize_entry(self, entry_data: Dict[str, Any]) -> UndoRedoEntry:
        """Deserialize an undo/redo entry"""
        return UndoRedoEntry(
            entry_id=entry_data['entry_id'],
            timestamp=entry_data['timestamp'],
            operation_type=OperationType(entry_data['operation_type']),
            description=entry_data['description'],
            before_state=PrecisionState(**entry_data['before_state']) if entry_data['before_state'] else None,
            after_state=PrecisionState(**entry_data['after_state']) if entry_data['after_state'] else None,
            precision_config=entry_data.get('precision_config'),
            validation_result=entry_data.get('validation_result'),
            metadata=entry_data.get('metadata', {})
        ) 