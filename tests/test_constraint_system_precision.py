"""
Test suite for precision-aware constraint system.

This module tests the updated constraint system that now includes
precision validation hooks and error handling.
"""

import pytest
import math
from typing import List, Tuple
from decimal import Decimal

from svgx_engine.core.precision_config import PrecisionConfig, config_manager
from svgx_engine.core.precision_math import PrecisionMath
from svgx_engine.core.precision_coordinate import PrecisionCoordinate, CoordinateValidator
from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
from svgx_engine.core.precision_errors import PrecisionErrorHandler, PrecisionErrorType, PrecisionErrorSeverity

# Import constraint systems
from svgx_engine.core.constraint_system import (
    Constraint, DistanceConstraint, AngleConstraint, ParallelConstraint,
    PerpendicularConstraint, CoincidentConstraint, TangentConstraint,
    SymmetricConstraint, ConstraintSolver, ConstraintManager, ConstraintFactory
)
from svgx_engine.services.cad.constraint_system import (
    ConstraintSystem, create_constraint_system, create_constraint_solver
)
from core.svg_parser.services.geometry_resolver import (
    GeometryResolver, GeometricConflict, ConflictType, ResolutionResult
)


class TestPrecisionConstraintClasses:
    """Test the updated constraint classes with precision validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()
        
        # Test entities
        self.point1 = type('Point', (), {
            'precision_position': PrecisionCoordinate(0.0, 0.0, 0.0),
            'x': 0.0, 'y': 0.0
        })()
        
        self.point2 = type('Point', (), {
            'precision_position': PrecisionCoordinate(1.0, 1.0, 0.0),
            'x': 1.0, 'y': 1.0
        })()
        
        self.line1 = type('Line', (), {
            'precision_position': PrecisionCoordinate(0.0, 0.0, 0.0),
            'dx': 1.0, 'dy': 0.0,
            'start': type('Point', (), {'x': 0.0, 'y': 0.0})(),
            'end': type('Point', (), {'x': 1.0, 'y': 0.0})()
        })()
        
        self.line2 = type('Line', (), {
            'precision_position': PrecisionCoordinate(0.0, 1.0, 0.0),
            'dx': 0.0, 'dy': 1.0,
            'start': type('Point', (), {'x': 0.0, 'y': 1.0})(),
            'end': type('Point', (), {'x': 0.0, 'y': 2.0})()
        })()

    def test_distance_constraint_precision(self):
        """Test distance constraint with precision validation."""
        # Test valid distance constraint
        constraint = DistanceConstraint(
            constraint_id="test_distance",
            entities=[self.point1, self.point2],
            parameters={'distance': 1.4142135623730951}  # sqrt(2)
        )
        
        assert constraint.validate()
        assert constraint.constraint_type.value == "distance"
        
        # Test invalid distance constraint (negative distance)
        invalid_constraint = DistanceConstraint(
            constraint_id="test_invalid_distance",
            entities=[self.point1, self.point2],
            parameters={'distance': -1.0}
        )
        
        # Should fail validation due to negative distance
        assert not invalid_constraint.validate()

    def test_angle_constraint_precision(self):
        """Test angle constraint with precision validation."""
        # Test valid angle constraint
        constraint = AngleConstraint(
            constraint_id="test_angle",
            entities=[self.line1, self.line2],
            parameters={'angle': math.pi/2}  # 90 degrees
        )
        
        assert constraint.validate()
        assert constraint.constraint_type.value == "angle"
        
        # Test invalid angle constraint (out of range)
        invalid_constraint = AngleConstraint(
            constraint_id="test_invalid_angle",
            entities=[self.line1, self.line2],
            parameters={'angle': 3 * math.pi}  # Out of range
        )
        
        # Should fail validation due to out-of-range angle
        assert not invalid_constraint.validate()

    def test_parallel_constraint_precision(self):
        """Test parallel constraint with precision validation."""
        constraint = ParallelConstraint(
            constraint_id="test_parallel",
            entities=[self.line1, self.line2]
        )
        
        assert constraint.validate()
        assert constraint.constraint_type.value == "parallel"

    def test_perpendicular_constraint_precision(self):
        """Test perpendicular constraint with precision validation."""
        constraint = PerpendicularConstraint(
            constraint_id="test_perpendicular",
            entities=[self.line1, self.line2]
        )
        
        assert constraint.validate()
        assert constraint.constraint_type.value == "perpendicular"

    def test_coincident_constraint_precision(self):
        """Test coincident constraint with precision validation."""
        constraint = CoincidentConstraint(
            constraint_id="test_coincident",
            entities=[self.point1, self.point2]
        )
        
        assert constraint.validate()
        assert constraint.constraint_type.value == "coincident"

    def test_tangent_constraint_precision(self):
        """Test tangent constraint with precision validation."""
        constraint = TangentConstraint(
            constraint_id="test_tangent",
            entities=[self.point1, self.point2]
        )
        
        assert constraint.validate()
        assert constraint.constraint_type.value == "tangent"

    def test_symmetric_constraint_precision(self):
        """Test symmetric constraint with precision validation."""
        symmetry_line = type('Line', (), {
            'start': type('Point', (), {'x': 0.0, 'y': 0.0})(),
            'end': type('Point', (), {'x': 1.0, 'y': 0.0})()
        })()
        
        constraint = SymmetricConstraint(
            constraint_id="test_symmetric",
            entities=[self.point1, self.point2, symmetry_line],
            parameters={'axis': 'x'}
        )
        
        assert constraint.validate()
        assert constraint.constraint_type.value == "symmetric"

    def test_constraint_error_calculation(self):
        """Test constraint error calculation with precision math."""
        constraint = DistanceConstraint(
            constraint_id="test_error",
            entities=[self.point1, self.point2],
            parameters={'distance': 1.0}
        )
        
        error = constraint.get_error()
        assert isinstance(error, float)
        assert error >= 0.0

    def test_constraint_solving(self):
        """Test constraint solving with precision validation."""
        constraint = DistanceConstraint(
            constraint_id="test_solve",
            entities=[self.point1, self.point2],
            parameters={'distance': 1.0}
        )
        
        # Test solving (should not raise exceptions)
        result = constraint.solve()
        assert isinstance(result, bool)


class TestPrecisionConstraintSolver:
    """Test the precision-aware constraint solver."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.solver = ConstraintSolver(self.config)
        
        # Test entities
        self.entity1 = type('Entity', (), {
            'precision_position': PrecisionCoordinate(0.0, 0.0, 0.0),
            'id': 'entity1'
        })()
        
        self.entity2 = type('Entity', (), {
            'precision_position': PrecisionCoordinate(1.0, 1.0, 0.0),
            'id': 'entity2'
        })()

    def test_solver_initialization(self):
        """Test constraint solver initialization with precision."""
        assert self.solver.config == self.config
        assert isinstance(self.solver.precision_math, PrecisionMath)
        assert isinstance(self.solver.coordinate_validator, CoordinateValidator)
        assert isinstance(self.solver.precision_validator, PrecisionValidator)

    def test_add_constraint_precision(self):
        """Test adding constraints with precision validation."""
        constraint = DistanceConstraint(
            constraint_id="test_add",
            entities=[self.entity1, self.entity2],
            parameters={'distance': 1.0}
        )
        
        result = self.solver.add_constraint(constraint)
        assert result is True
        assert len(self.solver.constraints) == 1

    def test_add_entity_precision(self):
        """Test adding entities with precision validation."""
        self.solver.add_entity('entity1', self.entity1)
        assert 'entity1' in self.solver.entities

    def test_solve_constraints_precision(self):
        """Test solving constraints with precision validation."""
        # Add a simple constraint
        constraint = DistanceConstraint(
            constraint_id="test_solve",
            entities=[self.entity1, self.entity2],
            parameters={'distance': 1.0}
        )
        
        self.solver.add_constraint(constraint)
        
        # Test solving
        result = self.solver.solve_all()
        assert isinstance(result, bool)

    def test_get_constraint_status(self):
        """Test getting constraint solver status with precision information."""
        status = self.solver.get_constraint_status()
        
        assert 'total_constraints' in status
        assert 'status_counts' in status
        assert 'total_entities' in status
        assert 'precision_tolerance' in status
        assert 'max_iterations' in status

    def test_validate_system(self):
        """Test constraint system validation with precision."""
        result = self.solver.validate_system()
        assert isinstance(result, bool)


class TestPrecisionConstraintSystem:
    """Test the precision-aware constraint system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.system = ConstraintSystem(self.config)
        
        # Test entities
        self.entity1 = type('Entity', (), {
            'precision_position': PrecisionCoordinate(0.0, 0.0, 0.0),
            'id': 'entity1'
        })()
        
        self.entity2 = type('Entity', (), {
            'precision_position': PrecisionCoordinate(1.0, 1.0, 0.0),
            'id': 'entity2'
        })()

    def test_system_initialization(self):
        """Test constraint system initialization with precision."""
        assert self.system.config == self.config
        assert isinstance(self.system.solver, ConstraintSolver)

    def test_add_distance_constraint_precision(self):
        """Test adding distance constraint with precision validation."""
        constraint = self.system.add_distance_constraint(
            self.entity1, self.entity2, 1.0
        )
        
        assert isinstance(constraint, DistanceConstraint)
        assert constraint.constraint_id == "distance_entity1_entity2"

    def test_add_angle_constraint_precision(self):
        """Test adding angle constraint with precision validation."""
        constraint = self.system.add_angle_constraint(
            self.entity1, self.entity2, math.pi/2
        )
        
        assert isinstance(constraint, AngleConstraint)
        assert constraint.constraint_id == "angle_entity1_entity2"

    def test_add_parallel_constraint_precision(self):
        """Test adding parallel constraint with precision validation."""
        constraint = self.system.add_parallel_constraint(
            self.entity1, self.entity2
        )
        
        assert isinstance(constraint, ParallelConstraint)
        assert constraint.constraint_id == "parallel_entity1_entity2"

    def test_add_perpendicular_constraint_precision(self):
        """Test adding perpendicular constraint with precision validation."""
        constraint = self.system.add_perpendicular_constraint(
            self.entity1, self.entity2
        )
        
        assert isinstance(constraint, PerpendicularConstraint)
        assert constraint.constraint_id == "perpendicular_entity1_entity2"

    def test_solve_constraints_precision(self):
        """Test solving constraints with precision validation."""
        # Add a constraint
        self.system.add_distance_constraint(self.entity1, self.entity2, 1.0)
        
        # Test solving
        result = self.system.solve_constraints()
        assert isinstance(result, bool)

    def test_validate_constraints_precision(self):
        """Test validating constraints with precision validation."""
        # Add a constraint
        self.system.add_distance_constraint(self.entity1, self.entity2, 1.0)
        
        # Test validation
        result = self.system.validate_constraints()
        assert isinstance(result, bool)

    def test_get_constraint_status(self):
        """Test getting constraint system status with precision information."""
        status = self.system.get_constraint_status()
        
        assert 'total_constraints' in status
        assert 'status_counts' in status
        assert 'total_entities' in status
        assert 'precision_tolerance' in status
        assert 'max_iterations' in status


class TestPrecisionGeometryResolver:
    """Test the precision-aware geometry resolver."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.resolver = GeometryResolver(self.config)
        
        # Test geometric objects
        self.obj1 = type('GeometricObject', (), {
            'object_id': 'obj1',
            'precision_position': PrecisionCoordinate(0.0, 0.0, 0.0),
            'get_bounding_box': lambda: type('BoundingBox', (), {
                'min_point': type('Point', (), {'x': 0.0, 'y': 0.0, 'z': 0.0})(),
                'max_point': type('Point', (), {'x': 1.0, 'y': 1.0, 'z': 1.0})(),
                'size': type('Point', (), {'x': 1.0, 'y': 1.0, 'z': 1.0})(),
                'intersects': lambda other: True
            })()
        })()
        
        self.obj2 = type('GeometricObject', (), {
            'object_id': 'obj2',
            'precision_position': PrecisionCoordinate(1.0, 1.0, 0.0),
            'get_bounding_box': lambda: type('BoundingBox', (), {
                'min_point': type('Point', (), {'x': 1.0, 'y': 1.0, 'z': 0.0})(),
                'max_point': type('Point', (), {'x': 2.0, 'y': 2.0, 'z': 1.0})(),
                'size': type('Point', (), {'x': 1.0, 'y': 1.0, 'z': 1.0})(),
                'intersects': lambda other: True
            })()
        })()

    def test_resolver_initialization(self):
        """Test geometry resolver initialization with precision."""
        assert self.resolver.config == self.config
        assert isinstance(self.resolver.precision_math, PrecisionMath)
        assert isinstance(self.resolver.coordinate_validator, CoordinateValidator)
        assert isinstance(self.resolver.precision_validator, PrecisionValidator)

    def test_add_object_precision(self):
        """Test adding objects with precision validation."""
        self.resolver.add_object(self.obj1)
        assert 'obj1' in self.resolver.objects

    def test_detect_conflicts_precision(self):
        """Test conflict detection with precision validation."""
        # Add objects
        self.resolver.add_object(self.obj1)
        self.resolver.add_object(self.obj2)
        
        # Test conflict detection
        conflicts = self.resolver.detect_conflicts()
        assert isinstance(conflicts, list)
        
        for conflict in conflicts:
            assert isinstance(conflict, GeometricConflict)
            assert hasattr(conflict, 'conflict_id')
            assert hasattr(conflict, 'conflict_type')
            assert hasattr(conflict, 'objects')
            assert hasattr(conflict, 'severity')
            assert hasattr(conflict, 'description')
            assert hasattr(conflict, 'precision_violations')

    def test_resolve_constraints_precision(self):
        """Test constraint resolution with precision validation."""
        # Add objects and constraints
        self.resolver.add_object(self.obj1)
        self.resolver.add_object(self.obj2)
        
        constraint = DistanceConstraint(
            constraint_id="test_resolve",
            objects=['obj1', 'obj2'],
            parameters={'distance': 1.0}
        )
        
        self.resolver.add_constraint(constraint)
        
        # Test constraint resolution
        result = self.resolver.resolve_constraints()
        assert isinstance(result, ResolutionResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'iterations')
        assert hasattr(result, 'final_violations')
        assert hasattr(result, 'conflicts_resolved')
        assert hasattr(result, 'conflicts_remaining')
        assert hasattr(result, 'optimization_score')
        assert hasattr(result, 'execution_time')

    def test_calculate_overlap_volume_precision(self):
        """Test overlap volume calculation with precision math."""
        bbox1 = type('BoundingBox', (), {
            'min_point': type('Point', (), {'x': 0.0, 'y': 0.0, 'z': 0.0})(),
            'max_point': type('Point', (), {'x': 1.0, 'y': 1.0, 'z': 1.0})()
        })()
        
        bbox2 = type('BoundingBox', (), {
            'min_point': type('Point', (), {'x': 0.5, 'y': 0.5, 'z': 0.5})(),
            'max_point': type('Point', (), {'x': 1.5, 'y': 1.5, 'z': 1.5})()
        })()
        
        volume = self.resolver._calculate_overlap_volume_precision(bbox1, bbox2)
        assert isinstance(volume, float)
        assert volume >= 0.0

    def test_check_precision_violations(self):
        """Test precision violation checking."""
        violations = self.resolver._check_precision_violations(self.obj1, self.obj2)
        assert isinstance(violations, list)
        
        for violation in violations:
            assert isinstance(violation, str)

    def test_correct_coordinate_precision(self):
        """Test coordinate correction with precision math."""
        coord = PrecisionCoordinate(1.23456789, 2.34567890, 3.45678901)
        corrected = self.resolver._correct_coordinate(coord)
        
        assert isinstance(corrected, PrecisionCoordinate)
        assert corrected.x != coord.x or corrected.y != coord.y or corrected.z != coord.z


class TestPrecisionConstraintFactory:
    """Test the precision-aware constraint factory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ConstraintFactory()
        
        # Test entities
        self.entity1 = type('Entity', (), {'id': 'entity1'})()
        self.entity2 = type('Entity', (), {'id': 'entity2'})()
        self.entity3 = type('Entity', (), {'id': 'entity3'})()

    def test_create_distance_constraint(self):
        """Test creating distance constraint with precision validation."""
        constraint = self.factory.create_constraint(
            'DISTANCE',
            [self.entity1, self.entity2],
            distance=1.0
        )
        
        assert isinstance(constraint, DistanceConstraint)
        assert constraint.constraint_type.value == "distance"

    def test_create_angle_constraint(self):
        """Test creating angle constraint with precision validation."""
        constraint = self.factory.create_constraint(
            'ANGLE',
            [self.entity1, self.entity2],
            angle=math.pi/2
        )
        
        assert isinstance(constraint, AngleConstraint)
        assert constraint.constraint_type.value == "angle"

    def test_create_parallel_constraint(self):
        """Test creating parallel constraint with precision validation."""
        constraint = self.factory.create_constraint(
            'PARALLEL',
            [self.entity1, self.entity2]
        )
        
        assert isinstance(constraint, ParallelConstraint)
        assert constraint.constraint_type.value == "parallel"

    def test_create_perpendicular_constraint(self):
        """Test creating perpendicular constraint with precision validation."""
        constraint = self.factory.create_constraint(
            'PERPENDICULAR',
            [self.entity1, self.entity2]
        )
        
        assert isinstance(constraint, PerpendicularConstraint)
        assert constraint.constraint_type.value == "perpendicular"

    def test_create_coincident_constraint(self):
        """Test creating coincident constraint with precision validation."""
        constraint = self.factory.create_constraint(
            'COINCIDENT',
            [self.entity1, self.entity2]
        )
        
        assert isinstance(constraint, CoincidentConstraint)
        assert constraint.constraint_type.value == "coincident"

    def test_create_tangent_constraint(self):
        """Test creating tangent constraint with precision validation."""
        constraint = self.factory.create_constraint(
            'TANGENT',
            [self.entity1, self.entity2]
        )
        
        assert isinstance(constraint, TangentConstraint)
        assert constraint.constraint_type.value == "tangent"

    def test_create_symmetric_constraint(self):
        """Test creating symmetric constraint with precision validation."""
        constraint = self.factory.create_constraint(
            'SYMMETRIC',
            [self.entity1, self.entity2, self.entity3]
        )
        
        assert isinstance(constraint, SymmetricConstraint)
        assert constraint.constraint_type.value == "symmetric"

    def test_create_constraint_validation_error(self):
        """Test constraint creation with validation errors."""
        # Test with wrong number of entities
        with pytest.raises(ValueError):
            self.factory.create_constraint('DISTANCE', [self.entity1])

        # Test with unknown constraint type
        with pytest.raises(ValueError):
            self.factory.create_constraint('UNKNOWN', [self.entity1, self.entity2])


class TestPrecisionConstraintHooks:
    """Test precision validation hooks integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.hook_called = False
        self.hook_context = None

    def test_constraint_validation_hooks(self):
        """Test constraint validation hooks."""
        def test_hook(context: HookContext) -> HookContext:
            nonlocal self.hook_called, self.hook_context
            self.hook_called = True
            self.hook_context = context
            assert context.operation_name == "constraint_validation"
            return context

        # Register hook
        hook_manager.register_hook(
            hook_id="test_constraint_validation",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=test_hook,
            priority=0
        )

        try:
            # Create and validate constraint
            constraint = DistanceConstraint(
                constraint_id="test_hooks",
                entities=[type('Entity', (), {'id': 'entity1'})(), type('Entity', (), {'id': 'entity2'})()],
                parameters={'distance': 1.0}
            )
            
            constraint.validate()
            
            assert self.hook_called
            assert self.hook_context is not None
            
        finally:
            # Clean up
            hook_manager.unregister_hook("test_constraint_validation")

    def test_constraint_solving_hooks(self):
        """Test constraint solving hooks."""
        def test_hook(context: HookContext) -> HookContext:
            nonlocal self.hook_called, self.hook_context
            self.hook_called = True
            self.hook_context = context
            assert context.operation_name == "constraint_solving"
            return context

        # Register hook
        hook_manager.register_hook(
            hook_id="test_constraint_solving",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=test_hook,
            priority=0
        )

        try:
            # Create and solve constraint
            constraint = DistanceConstraint(
                constraint_id="test_hooks",
                entities=[type('Entity', (), {'id': 'entity1'})(), type('Entity', (), {'id': 'entity2'})()],
                parameters={'distance': 1.0}
            )
            
            constraint.solve()
            
            assert self.hook_called
            assert self.hook_context is not None
            
        finally:
            # Clean up
            hook_manager.unregister_hook("test_constraint_solving")


class TestPrecisionConstraintErrorHandling:
    """Test precision constraint error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.error_handler = PrecisionErrorHandler()

    def test_constraint_validation_error_handling(self):
        """Test constraint validation error handling."""
        # Create constraint that will fail validation
        constraint = DistanceConstraint(
            constraint_id="test_error",
            entities=[],  # Empty entities will cause validation failure
            parameters={'distance': -1.0}  # Negative distance will cause validation failure
        )
        
        # Test validation (should handle errors gracefully)
        result = constraint.validate()
        assert isinstance(result, bool)

    def test_constraint_solving_error_handling(self):
        """Test constraint solving error handling."""
        # Create constraint that will fail solving
        constraint = DistanceConstraint(
            constraint_id="test_error",
            entities=[type('Entity', (), {'id': 'entity1'})(), type('Entity', (), {'id': 'entity2'})()],
            parameters={'distance': 1.0}
        )
        
        # Test solving (should handle errors gracefully)
        result = constraint.solve()
        assert isinstance(result, bool)

    def test_error_recovery_strategies(self):
        """Test error recovery strategies."""
        # Configure error handler
        self.error_handler.set_recovery_strategy(
            PrecisionErrorType.VALIDATION_ERROR,
            "fallback_to_default"
        )
        
        # Test error handling
        assert self.error_handler.get_recovery_strategy(PrecisionErrorType.VALIDATION_ERROR) == "fallback_to_default"


if __name__ == "__main__":
    pytest.main([__file__]) 