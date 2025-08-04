"""
SVGX Engine - CAD Components Package

This package contains the CAD-parity components for the SVGX Engine,
providing professional CAD functionality with sub-millimeter precision.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from .precision_drawing_system import (
    PrecisionDrawingSystem,
    PrecisionConfig,
    PrecisionPoint,
    PrecisionVector,
    PrecisionLevel,
    PrecisionUnit,
    PrecisionCoordinateSystem,
    create_precision_drawing_system,
    create_precision_config
)

from .constraint_system import (
    ConstraintSystem,
    ConstraintSolver,
    ConstraintType,
    ConstraintStatus,
    DistanceConstraint,
    AngleConstraint,
    ParallelConstraint,
    PerpendicularConstraint,
    HorizontalConstraint,
    VerticalConstraint,
    CoincidentConstraint,
    TangentConstraint,
    SymmetricConstraint,
    CurveTangentConstraint,
    CurvatureContinuousConstraint,
    CurvePositionConstraint,
    CurveLengthConstraint,
    create_constraint_system,
    create_constraint_solver
)

from .grid_snap_system import (
    GridSnapSystem,
    GridSystem,
    SnapSystem,
    GridConfig,
    SnapConfig,
    SnapType,
    GridStyle,
    SnapPoint,
    create_grid_snap_system,
    create_grid_config,
    create_snap_config
)

from .dimensioning_system import (
    DimensioningSystem,
    DimensionType,
    DimensionStyle,
    TextPosition,
    LinearDimension,
    RadialDimension,
    AngularDimension,
    AlignedDimension,
    create_dimensioning_system,
    create_dimension_style
)

from .parametric_modeling import (
    ParametricModelingSystem,
    ParametricModel,
    Parameter,
    ParameterType,
    ParameterStatus,
    ParameterRelationship,
    ExpressionEvaluator,
    create_parametric_modeling_system,
    create_parametric_model,
    create_parameter,
    create_parameter_relationship
)

from .assembly_management import (
    AssemblyManager,
    Assembly,
    Component,
    ComponentType,
    AssemblyConstraint,
    AssemblyConstraintType,
    AssemblyStatus,
    create_assembly_manager,
    create_assembly,
    create_component,
    create_assembly_constraint
)

from .curve_system import (
    CurveSystem,
    BezierCurve,
    BSplineCurve,
    CurveFitter,
    ControlPoint,
    CurvePoint,
    KnotVector,
    CurveType,
    CurveDegree,
    create_curve_system,
    create_bezier_curve,
    create_bspline_curve
)

from .curve_constraints import (
    CurveTangentConstraint,
    CurvatureContinuousConstraint,
    CurvePositionConstraint,
    CurveLengthConstraint
)

from .drawing_views import (
    DrawingViewManager,
    DrawingView,
    ViewGenerator,
    ViewType,
    ViewConfig,
    ProjectionType,
    ViewScale,
    create_drawing_view_manager,
    create_drawing_view,
    create_view_generator,
    create_view_config
)

__all__ = [
    # Precision Drawing System
    "PrecisionDrawingSystem",
    "PrecisionConfig", 
    "PrecisionPoint",
    "PrecisionVector",
    "PrecisionLevel",
    "PrecisionUnit",
    "PrecisionCoordinateSystem",
    "create_precision_drawing_system",
    "create_precision_config",
    
    # Constraint System
    "ConstraintSystem",
    "ConstraintSolver",
    "ConstraintType",
    "ConstraintStatus",
    "DistanceConstraint",
    "AngleConstraint",
    "ParallelConstraint",
    "PerpendicularConstraint",
    "HorizontalConstraint",
    "VerticalConstraint",
    "CoincidentConstraint",
    "TangentConstraint",
    "SymmetricConstraint",
    "create_constraint_system",
    "create_constraint_solver",
    
    # Grid and Snap System
    "GridSnapSystem",
    "GridSystem",
    "SnapSystem",
    "GridConfig",
    "SnapConfig",
    "SnapType",
    "GridStyle",
    "SnapPoint",
    "create_grid_snap_system",
    "create_grid_config",
    "create_snap_config",
    
    # Dimensioning System
    "DimensioningSystem",
    "DimensionType",
    "DimensionStyle",
    "TextPosition",
    "LinearDimension",
    "RadialDimension",
    "AngularDimension",
    "AlignedDimension",
    "create_dimensioning_system",
    "create_dimension_style",
    
    # Parametric Modeling
    "ParametricModelingSystem",
    "ParametricModel",
    "Parameter",
    "ParameterType",
    "ParameterStatus",
    "ParameterRelationship",
    "ExpressionEvaluator",
    "create_parametric_modeling_system",
    "create_parametric_model",
    "create_parameter",
    "create_parameter_relationship",
    
    # Assembly Management
    "AssemblyManager",
    "Assembly",
    "Component",
    "ComponentType",
    "AssemblyConstraint",
    "AssemblyConstraintType",
    "AssemblyStatus",
    "create_assembly_manager",
    "create_assembly",
    "create_component",
    "create_assembly_constraint",
    
    # Drawing Views
    "DrawingViewManager",
    "DrawingView",
    "ViewGenerator",
    "ViewType",
    "ViewConfig",
    "ProjectionType",
    "ViewScale",
    "create_drawing_view_manager",
    "create_drawing_view",
    "create_view_generator",
    "create_view_config"
]

__version__ = "1.0.0"
__author__ = "Arxos Engineering Team" 