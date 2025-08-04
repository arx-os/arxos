#!/usr/bin/env python3

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from svgx_engine.services.cad.curve_system import CurveSystem, BezierCurve
    print("✅ Curve system imports work!")
except ImportError as e:
    print(f"❌ Import error: {e}")

try:
    from svgx_engine.services.cad.constraint_system import ConstraintSystem, CurveTangentConstraint
    print("✅ Constraint system imports work!")
except ImportError as e:
    print(f"❌ Import error: {e}")

try:
    from svgx_engine.core.precision_coordinate import PrecisionCoordinate
    print("✅ Precision coordinate imports work!")
except ImportError as e:
    print(f"❌ Import error: {e}") 