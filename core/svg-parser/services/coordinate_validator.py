"""
Coordinate validation service for real-world coordinate system integration
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

@dataclass
class CoordinateValidationError(Exception):
    """Custom exception for coordinate validation errors"""
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None

class CoordinateValidator:
    """Validates coordinates and coordinate systems for real-world integration"""
    
    def __init__(self):
        # Define reasonable bounds for different coordinate systems
        self.bounds = {
            "svg": {
                "x": (-1000000, 1000000),
                "y": (-1000000, 1000000)
            },
            "real_world_meters": {
                "x": (-100000, 100000),  # ±100km
                "y": (-100000, 100000)
            },
            "real_world_feet": {
                "x": (-328084, 328084),  # ±100km in feet
                "y": (-328084, 328084)
            },
            "bim": {
                "x": (-10000, 10000),    # ±10km for typical buildings
                "y": (-10000, 10000)
            }
        }
        
        # Define scale factor limits
        self.scale_limits = {
            "min": 0.0001,  # 1:10000 scale
            "max": 10000.0  # 10000:1 scale
        }
        
        # Define precision limits
        self.precision_limits = {
            "svg": 6,           # 6 decimal places for SVG
            "real_world": 3,    # 3 decimal places for real-world
            "bim": 2            # 2 decimal places for BIM
        }

    def validate_coordinates(self, coordinates: List[List[float]], 
                           system: str = "svg") -> Dict[str, Any]:
        """
        Validate a list of coordinates for a given coordinate system
        
        Args:
            coordinates: List of [x, y] coordinate pairs
            system: Coordinate system to validate against
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        if not coordinates:
            errors.append("No coordinates provided")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Validate coordinate format
        for i, coord in enumerate(coordinates):
            if not isinstance(coord, list) or len(coord) != 2:
                errors.append(f"Coordinate {i} must be a list of two numbers [x, y]")
                continue
                
            x, y = coord
            
            # Check for numeric values
            if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                errors.append(f"Coordinate {i} must contain numeric values")
                continue
            
            # Check for NaN or infinity
            if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
                errors.append(f"Coordinate {i} contains invalid values (NaN or infinity)")
                continue
            
            # Check bounds
            if system in self.bounds:
                bounds = self.bounds[system]
                if not (bounds["x"][0] <= x <= bounds["x"][1]):
                    warnings.append(f"Coordinate {i} X value ({x}) is outside typical bounds for {system}")
                if not (bounds["y"][0] <= y <= bounds["y"][1]):
                    warnings.append(f"Coordinate {i} Y value ({y}) is outside typical bounds for {system}")
            
            # Check precision
            precision_limit = self.precision_limits.get(system, 6)
            if len(str(x).split('.')[-1]) > precision_limit:
                warnings.append(f"Coordinate {i} X value has excessive precision for {system}")
            if len(str(y).split('.')[-1]) > precision_limit:
                warnings.append(f"Coordinate {i} Y value has excessive precision for {system}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def validate_scale_factors(self, scale_x: float, scale_y: float) -> Dict[str, Any]:
        """
        Validate scale factors for coordinate transformation
        
        Args:
            scale_x: Scale factor for X axis
            scale_y: Scale factor for Y axis
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check for positive values
        if scale_x <= 0:
            errors.append("Scale factor X must be positive")
        if scale_y <= 0:
            errors.append("Scale factor Y must be positive")
        
        # Check scale limits
        if scale_x < self.scale_limits["min"] or scale_x > self.scale_limits["max"]:
            warnings.append(f"Scale factor X ({scale_x}) is outside recommended range")
        if scale_y < self.scale_limits["min"] or scale_y > self.scale_limits["max"]:
            warnings.append(f"Scale factor Y ({scale_y}) is outside recommended range")
        
        # Check for uniform scaling
        scale_ratio = abs(scale_x - scale_y) / max(scale_x, scale_y)
        if scale_ratio > 0.01:  # More than 1% difference
            warnings.append("Non-uniform scaling detected - this may cause distortion")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "uniform": scale_ratio <= 0.01
        }

    def validate_anchor_points(self, anchor_points: List[Dict[str, List[float]]]) -> Dict[str, Any]:
        """
        Validate anchor points for coordinate system calibration
        
        Args:
            anchor_points: List of anchor point dictionaries with 'svg' and 'real' coordinates
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        if len(anchor_points) < 2:
            errors.append("At least two anchor points are required")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Validate each anchor point
        for i, point in enumerate(anchor_points):
            if "svg" not in point or "real" not in point:
                errors.append(f"Anchor point {i} must contain 'svg' and 'real' coordinates")
                continue
            
            # Validate SVG coordinates
            svg_validation = self.validate_coordinates([point["svg"]], "svg")
            if not svg_validation["valid"]:
                errors.extend([f"Anchor point {i} SVG: {e}" for e in svg_validation["errors"]])
            warnings.extend([f"Anchor point {i} SVG: {w}" for w in svg_validation["warnings"]])
            
            # Validate real-world coordinates
            real_validation = self.validate_coordinates([point["real"]], "real_world_meters")
            if not real_validation["valid"]:
                errors.extend([f"Anchor point {i} Real: {e}" for e in real_validation["errors"]])
            warnings.extend([f"Anchor point {i} Real: {w}" for w in real_validation["warnings"]])
        
        # Check for collinear points
        if len(anchor_points) >= 3:
            collinear = self._check_collinear_points(anchor_points)
            if collinear:
                warnings.append("Anchor points appear to be collinear - this may cause scaling issues")
        
        # Check for reasonable scale factors
        if len(anchor_points) >= 2:
            scale_factors = self._calculate_scale_factors(anchor_points[:2])
            scale_validation = self.validate_scale_factors(scale_factors["x"], scale_factors["y"])
            if not scale_validation["valid"]:
                errors.extend(scale_validation["errors"])
            warnings.extend(scale_validation["warnings"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _check_collinear_points(self, anchor_points: List[Dict[str, List[float]]]) -> bool:
        """
        Check if anchor points are collinear (which would cause scaling issues)
        """
        if len(anchor_points) < 3:
            return False
        
        # Use first three points to check collinearity
        p1 = anchor_points[0]["svg"]
        p2 = anchor_points[1]["svg"]
        p3 = anchor_points[2]["svg"]
        
        # Calculate area of triangle formed by three points
        area = abs((p2[0] - p1[0]) * (p3[1] - p1[1]) - (p3[0] - p1[0]) * (p2[1] - p1[1])) / 2
        
        # If area is very small, points are approximately collinear
        return area < 1e-6

    def _calculate_scale_factors(self, anchor_points: List[Dict[str, List[float]]]) -> Dict[str, float]:
        """
        Calculate scale factors from anchor points
        """
        if len(anchor_points) < 2:
            return {"x": 1.0, "y": 1.0}
        
        svg1, real1 = anchor_points[0]["svg"], anchor_points[0]["real"]
        svg2, real2 = anchor_points[1]["svg"], anchor_points[1]["real"]
        
        dx_svg = svg2[0] - svg1[0]
        dy_svg = svg2[1] - svg1[1]
        dx_real = real2[0] - real1[0]
        dy_real = real2[1] - real1[1]
        
        scale_x = dx_real / dx_svg if dx_svg != 0 else 1.0
        scale_y = dy_real / dy_svg if dy_svg != 0 else 1.0
        
        return {"x": scale_x, "y": scale_y}

    def validate_transformation_matrix(self, matrix: List[List[float]]) -> Dict[str, Any]:
        """
        Validate transformation matrix
        
        Args:
            matrix: 4x4 transformation matrix
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check matrix dimensions
        if len(matrix) != 4:
            errors.append("Transformation matrix must be 4x4")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        for i, row in enumerate(matrix):
            if len(row) != 4:
                errors.append(f"Row {i} must have 4 elements")
                continue
            
            # Check for numeric values
            for j, val in enumerate(row):
                if not isinstance(val, (int, float)):
                    errors.append(f"Element [{i}][{j}] must be numeric")
                elif math.isnan(val) or math.isinf(val):
                    errors.append(f"Element [{i}][{j}] contains invalid values")
        
        # Check for singular matrix (determinant = 0)
        if len(errors) == 0:
            try:
                det = self._matrix_determinant(matrix)
                if abs(det) < 1e-10:
                    errors.append("Transformation matrix is singular (determinant = 0)")
            except Exception:
                warnings.append("Could not validate matrix determinant")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _matrix_determinant(self, matrix: List[List[float]]) -> float:
        """
        Calculate determinant of 4x4 matrix
        """
        # Simple implementation for 4x4 matrix
        a, b, c, d = matrix[0]
        e, f, g, h = matrix[1]
        i, j, k, l = matrix[2]
        m, n, o, p = matrix[3]
        
        return (a * f * k * p - a * f * l * o - a * g * j * p + a * g * l * n + a * h * j * o - a * h * k * n
                - b * e * k * p + b * e * l * o + b * g * i * p - b * g * l * m - b * h * i * o + b * h * k * m
                + c * e * j * p - c * e * l * n - c * f * i * p + c * f * l * m + c * h * i * n - c * h * j * m
                - d * e * j * o + d * e * k * n + d * f * i * o - d * f * k * m - d * g * i * n + d * g * j * m)

# Global validator instance
validator = CoordinateValidator()

def validate_coordinates(coordinates: List[List[float]], system: str = "svg") -> Dict[str, Any]:
    """Global function to validate coordinates"""
    return validator.validate_coordinates(coordinates, system)

def validate_scale_factors(scale_x: float, scale_y: float) -> Dict[str, Any]:
    """Global function to validate scale factors"""
    return validator.validate_scale_factors(scale_x, scale_y)

def validate_anchor_points(anchor_points: List[Dict[str, List[float]]]) -> Dict[str, Any]:
    """Global function to validate anchor points"""
    return validator.validate_anchor_points(anchor_points)

def validate_transformation_matrix(matrix: List[List[float]]) -> Dict[str, Any]:
    """Global function to validate transformation matrix"""
    return validator.validate_transformation_matrix(matrix) 