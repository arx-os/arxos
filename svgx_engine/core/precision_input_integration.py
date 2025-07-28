"""
Precision Input Integration System

This module provides integration between the precision input system and the geometry engine,
enabling precision-aware input feedback and validation for geometry creation operations.
"""

import logging
import time
from typing import Dict, Any, List, Tuple, Optional, Union, Callable
from dataclasses import dataclass, field
from decimal import Decimal

from .precision_input import (
    PrecisionInputHandler, 
    InputSettings, 
    InputType, 
    InputMode, 
    InputEvent,
    PrecisionInputValidator
)
from .precision_coordinate import PrecisionCoordinate, CoordinateValidator
from .precision_math import PrecisionMath
from .precision_validator import PrecisionValidator, ValidationLevel, ValidationType
from .precision_config import PrecisionConfig, config_manager
from .precision_hooks import hook_manager, HookType, HookContext
from .precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
from .precision_integration import PrecisionGeometryFactory, PrecisionGeometryAdapter

logger = logging.getLogger(__name__)


@dataclass
class GeometryCreationContext:
    """Context for geometry creation operations with precision input"""
    
    geometry_type: str
    input_coordinates: List[PrecisionCoordinate] = field(default_factory=list)
    input_mode: InputMode = InputMode.FREEHAND
    creation_timestamp: float = field(default_factory=time.time)
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    feedback_messages: List[str] = field(default_factory=list)
    
    def add_coordinate(self, coord: PrecisionCoordinate):
        """Add a coordinate to the creation context"""
        self.input_coordinates.append(coord)
    
    def get_coordinate_count(self) -> int:
        """Get the number of coordinates in the context"""
        return len(self.input_coordinates)
    
    def is_complete(self) -> bool:
        """Check if the geometry creation is complete"""
        if self.geometry_type == 'point':
            return self.get_coordinate_count() >= 1
        elif self.geometry_type in ['line', 'segment']:
            return self.get_coordinate_count() >= 2
        elif self.geometry_type in ['polygon', 'polyline']:
            return self.get_coordinate_count() >= 3
        elif self.geometry_type == 'circle':
            return self.get_coordinate_count() >= 2  # center + radius point
        elif self.geometry_type == 'rectangle':
            return self.get_coordinate_count() >= 2  # two corner points
        else:
            return False


@dataclass
class PrecisionInputFeedback:
    """Precision input feedback information"""
    
    feedback_type: str
    message: str
    coordinate: Optional[PrecisionCoordinate] = None
    validation_status: str = "valid"
    severity: str = "info"
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert feedback to dictionary"""
        return {
            'feedback_type': self.feedback_type,
            'message': self.message,
            'coordinate': self.coordinate.as_tuple if self.coordinate else None,
            'validation_status': self.validation_status,
            'severity': self.severity,
            'timestamp': self.timestamp
        }


class PrecisionInputGeometryIntegration:
    """
    Integration system for precision input with geometry creation operations.
    
    Provides precision-aware input handling, validation, and feedback for
    geometry creation operations in CAD applications.
    """
    
    def __init__(self, config: Optional[PrecisionConfig] = None):
        """
        Initialize precision input geometry integration.
        
        Args:
            config: Precision configuration (optional)
        """
        self.config = config or config_manager.get_default_config()
        
        # Initialize precision components
        self.input_handler = PrecisionInputHandler()
        self.input_validator = PrecisionInputValidator()
        self.coordinate_validator = CoordinateValidator()
        self.precision_math = PrecisionMath()
        self.precision_validator = PrecisionValidator()
        
        # Initialize geometry components
        self.geometry_adapter = PrecisionGeometryAdapter(self.config)
        self.geometry_factory = PrecisionGeometryFactory(self.config, self.geometry_adapter)
        
        # Active creation contexts
        self.active_contexts: Dict[str, GeometryCreationContext] = {}
        
        # Feedback callbacks
        self.on_input_feedback: Optional[Callable[[PrecisionInputFeedback], None]] = None
        self.on_geometry_created: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_validation_error: Optional[Callable[[str, Dict[str, Any]], None]] = None
        
        # Setup logging
        self._setup_logging()
        
        # Register input callbacks
        self._setup_input_callbacks()
    
    def _setup_logging(self):
        """Setup logging for input integration operations"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _setup_input_callbacks(self):
        """Setup callbacks for input handler"""
        self.input_handler.set_coordinate_callback(self._on_coordinate_input)
        self.input_handler.set_validation_callback(self._on_input_validation)
        self.input_handler.set_feedback_callback(self._on_precision_feedback)
    
    def set_input_feedback_callback(self, callback: Callable[[PrecisionInputFeedback], None]):
        """Set callback for input feedback events"""
        self.on_input_feedback = callback
    
    def set_geometry_created_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback for geometry creation events"""
        self.on_geometry_created = callback
    
    def set_validation_error_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Set callback for validation error events"""
        self.on_validation_error = callback
    
    def start_geometry_creation(self, geometry_type: str, input_mode: InputMode = InputMode.FREEHAND) -> str:
        """
        Start a new geometry creation session.
        
        Args:
            geometry_type: Type of geometry to create
            input_mode: Input mode for the creation session
            
        Returns:
            str: Session ID for the creation context
        """
        session_id = f"geom_creation_{int(time.time() * 1000)}"
        
        # Create creation context
        context = GeometryCreationContext(
            geometry_type=geometry_type,
            input_mode=input_mode
        )
        
        self.active_contexts[session_id] = context
        
        # Set input handler mode
        self.input_handler.set_input_mode(input_mode)
        
        # Provide feedback
        self._provide_creation_feedback(session_id, "creation_started", {
            "geometry_type": geometry_type,
            "input_mode": input_mode.value
        })
        
        logger.info(f"Started geometry creation session {session_id}: {geometry_type}")
        return session_id
    
    def handle_mouse_input(self, session_id: str, x: float, y: float, z: float = 0.0, 
                          event_type: str = "click") -> Optional[PrecisionCoordinate]:
        """
        Handle mouse input for geometry creation.
        
        Args:
            session_id: Geometry creation session ID
            x, y, z: Mouse coordinates
            event_type: Type of mouse event
            
        Returns:
            PrecisionCoordinate: Validated coordinate or None if invalid
        """
        if session_id not in self.active_contexts:
            self._handle_error(f"Invalid session ID: {session_id}")
            return None
        
        context = self.active_contexts[session_id]
        
        # Handle input through precision input handler
        coordinate = self.input_handler.handle_mouse_input(x, y, z, event_type)
        
        if coordinate:
            # Add coordinate to creation context
            context.add_coordinate(coordinate)
            
            # Validate coordinate for geometry creation
            validation_result = self._validate_coordinate_for_geometry(coordinate, context)
            
            # Provide feedback
            self._provide_creation_feedback(session_id, "coordinate_added", {
                "coordinate": coordinate,
                "coordinate_count": context.get_coordinate_count(),
                "validation_result": validation_result
            })
            
            # Check if geometry creation is complete
            if context.is_complete():
                self._complete_geometry_creation(session_id)
            
            return coordinate
        else:
            # Handle invalid input
            self._provide_creation_feedback(session_id, "invalid_coordinate", {
                "coordinates": (x, y, z),
                "event_type": event_type
            })
            return None
    
    def handle_touch_input(self, session_id: str, x: float, y: float, z: float = 0.0,
                          event_type: str = "touch") -> Optional[PrecisionCoordinate]:
        """
        Handle touch input for geometry creation.
        
        Args:
            session_id: Geometry creation session ID
            x, y, z: Touch coordinates
            event_type: Type of touch event
            
        Returns:
            PrecisionCoordinate: Validated coordinate or None if invalid
        """
        if session_id not in self.active_contexts:
            self._handle_error(f"Invalid session ID: {session_id}")
            return None
        
        context = self.active_contexts[session_id]
        
        # Handle input through precision input handler
        coordinate = self.input_handler.handle_touch_input(x, y, z, event_type)
        
        if coordinate:
            # Add coordinate to creation context
            context.add_coordinate(coordinate)
            
            # Validate coordinate for geometry creation
            validation_result = self._validate_coordinate_for_geometry(coordinate, context)
            
            # Provide feedback
            self._provide_creation_feedback(session_id, "coordinate_added", {
                "coordinate": coordinate,
                "coordinate_count": context.get_coordinate_count(),
                "validation_result": validation_result
            })
            
            # Check if geometry creation is complete
            if context.is_complete():
                self._complete_geometry_creation(session_id)
            
            return coordinate
        else:
            # Handle invalid input
            self._provide_creation_feedback(session_id, "invalid_coordinate", {
                "coordinates": (x, y, z),
                "event_type": event_type
            })
            return None
    
    def handle_keyboard_input(self, session_id: str, x_str: str, y_str: str, z_str: str = "0.0") -> Optional[PrecisionCoordinate]:
        """
        Handle keyboard input for geometry creation.
        
        Args:
            session_id: Geometry creation session ID
            x_str, y_str, z_str: Coordinate strings
            
        Returns:
            PrecisionCoordinate: Validated coordinate or None if invalid
        """
        if session_id not in self.active_contexts:
            self._handle_error(f"Invalid session ID: {session_id}")
            return None
        
        context = self.active_contexts[session_id]
        
        # Handle input through precision input handler
        coordinate = self.input_handler.handle_keyboard_input(x_str, y_str, z_str)
        
        if coordinate:
            # Add coordinate to creation context
            context.add_coordinate(coordinate)
            
            # Validate coordinate for geometry creation
            validation_result = self._validate_coordinate_for_geometry(coordinate, context)
            
            # Provide feedback
            self._provide_creation_feedback(session_id, "coordinate_added", {
                "coordinate": coordinate,
                "coordinate_count": context.get_coordinate_count(),
                "validation_result": validation_result
            })
            
            # Check if geometry creation is complete
            if context.is_complete():
                self._complete_geometry_creation(session_id)
            
            return coordinate
        else:
            # Handle invalid input
            self._provide_creation_feedback(session_id, "invalid_coordinate", {
                "coordinates": (x_str, y_str, z_str)
            })
            return None
    
    def cancel_geometry_creation(self, session_id: str) -> bool:
        """
        Cancel a geometry creation session.
        
        Args:
            session_id: Geometry creation session ID
            
        Returns:
            bool: True if session was cancelled successfully
        """
        if session_id not in self.active_contexts:
            return False
        
        context = self.active_contexts.pop(session_id)
        
        # Provide feedback
        self._provide_creation_feedback(session_id, "creation_cancelled", {
            "geometry_type": context.geometry_type,
            "coordinate_count": context.get_coordinate_count()
        })
        
        logger.info(f"Cancelled geometry creation session {session_id}")
        return True
    
    def get_creation_progress(self, session_id: str) -> Dict[str, Any]:
        """
        Get progress information for a geometry creation session.
        
        Args:
            session_id: Geometry creation session ID
            
        Returns:
            Dict[str, Any]: Progress information
        """
        if session_id not in self.active_contexts:
            return {"error": "Invalid session ID"}
        
        context = self.active_contexts[session_id]
        
        return {
            "geometry_type": context.geometry_type,
            "input_mode": context.input_mode.value,
            "coordinate_count": context.get_coordinate_count(),
            "is_complete": context.is_complete(),
            "coordinates": [coord.as_tuple for coord in context.input_coordinates],
            "validation_results": context.validation_results,
            "feedback_messages": context.feedback_messages
        }
    
    def _validate_coordinate_for_geometry(self, coordinate: PrecisionCoordinate, 
                                        context: GeometryCreationContext) -> Dict[str, Any]:
        """
        Validate coordinate for geometry creation.
        
        Args:
            coordinate: Coordinate to validate
            context: Geometry creation context
            
        Returns:
            Dict[str, Any]: Validation result
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Basic coordinate validation
            coord_validation = self.coordinate_validator.validate_coordinate(coordinate)
            if not coord_validation.is_valid:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Coordinate validation failed: {coord_validation.errors}")
            
            # Geometry-specific validation
            if context.geometry_type == "line" and context.get_coordinate_count() == 2:
                # Validate line length
                start_coord = context.input_coordinates[0]
                length = self.precision_math.distance(start_coord, coordinate)
                
                min_length = self.config.validation_rules.get('min_line_length', 0.001)
                if length < min_length:
                    validation_result["warnings"].append(f"Line length {length} is below minimum {min_length}")
            
            elif context.geometry_type == "circle" and context.get_coordinate_count() == 2:
                # Validate circle radius
                center_coord = context.input_coordinates[0]
                radius = self.precision_math.distance(center_coord, coordinate)
                
                min_radius = self.config.validation_rules.get('min_circle_radius', 0.001)
                if radius < min_radius:
                    validation_result["warnings"].append(f"Circle radius {radius} is below minimum {min_radius}")
            
            # Store validation result
            context.validation_results.append(validation_result)
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _complete_geometry_creation(self, session_id: str):
        """
        Complete geometry creation and generate the final geometry.
        
        Args:
            session_id: Geometry creation session ID
        """
        if session_id not in self.active_contexts:
            return
        
        context = self.active_contexts.pop(session_id)
        
        try:
            # Create geometry based on type and coordinates
            geometry = self._create_geometry_from_context(context)
            
            if geometry:
                # Provide success feedback
                self._provide_creation_feedback(session_id, "geometry_created", {
                    "geometry": geometry,
                    "coordinate_count": context.get_coordinate_count()
                })
                
                # Call geometry created callback
                if self.on_geometry_created:
                    self.on_geometry_created(geometry)
                
                logger.info(f"Completed geometry creation for session {session_id}: {context.geometry_type}")
            else:
                # Handle creation failure
                self._provide_creation_feedback(session_id, "creation_failed", {
                    "geometry_type": context.geometry_type,
                    "coordinate_count": context.get_coordinate_count()
                })
        
        except Exception as e:
            # Handle creation error
            self._handle_error(f"Geometry creation failed: {str(e)}")
            self._provide_creation_feedback(session_id, "creation_error", {
                "error": str(e),
                "geometry_type": context.geometry_type
            })
    
    def _create_geometry_from_context(self, context: GeometryCreationContext) -> Optional[Dict[str, Any]]:
        """
        Create geometry from creation context.
        
        Args:
            context: Geometry creation context
            
        Returns:
            Optional[Dict[str, Any]]: Created geometry or None if creation failed
        """
        try:
            if context.geometry_type == "point":
                if context.get_coordinate_count() >= 1:
                    coord = context.input_coordinates[0]
                    return self.geometry_factory.create_point_2d(coord.x, coord.y)
            
            elif context.geometry_type == "line":
                if context.get_coordinate_count() >= 2:
                    start_coord = context.input_coordinates[0]
                    end_coord = context.input_coordinates[1]
                    return self.geometry_factory.create_line_2d(
                        start_coord.x, start_coord.y,
                        end_coord.x, end_coord.y
                    )
            
            elif context.geometry_type == "polygon":
                if context.get_coordinate_count() >= 3:
                    coords = [coord.as_tuple for coord in context.input_coordinates]
                    return self.geometry_factory.create_polygon_2d(coords)
            
            elif context.geometry_type == "circle":
                if context.get_coordinate_count() >= 2:
                    center_coord = context.input_coordinates[0]
                    radius_coord = context.input_coordinates[1]
                    radius = self.precision_math.distance(center_coord, radius_coord)
                    return self.geometry_factory.create_circle_2d(
                        center_coord.x, center_coord.y, radius
                    )
            
            elif context.geometry_type == "rectangle":
                if context.get_coordinate_count() >= 2:
                    corner1 = context.input_coordinates[0]
                    corner2 = context.input_coordinates[1]
                    
                    x = min(corner1.x, corner2.x)
                    y = min(corner1.y, corner2.y)
                    width = abs(corner2.x - corner1.x)
                    height = abs(corner2.y - corner1.y)
                    
                    return self.geometry_factory.create_rectangle_2d(x, y, width, height)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to create geometry {context.geometry_type}: {e}")
            return None
    
    def _provide_creation_feedback(self, session_id: str, feedback_type: str, data: Dict[str, Any]):
        """
        Provide feedback for geometry creation operations.
        
        Args:
            session_id: Session ID
            feedback_type: Type of feedback
            data: Feedback data
        """
        feedback = PrecisionInputFeedback(
            feedback_type=feedback_type,
            message=f"Geometry creation {feedback_type}",
            coordinate=data.get('coordinate'),
            validation_status=data.get('validation_status', 'valid'),
            severity='info' if 'error' not in feedback_type else 'error'
        )
        
        # Call feedback callback
        if self.on_input_feedback:
            self.on_input_feedback(feedback)
        
        # Log feedback
        logger.info(f"Geometry creation feedback [{session_id}]: {feedback_type}")
    
    def _handle_error(self, error_message: str):
        """Handle error in input integration"""
        logger.error(f"Precision input integration error: {error_message}")
        
        if self.on_validation_error:
            self.on_validation_error("input_integration_error", {"message": error_message})
    
    def _on_coordinate_input(self, coordinate: PrecisionCoordinate):
        """Handle coordinate input from precision input handler"""
        logger.debug(f"Coordinate input received: {coordinate}")
    
    def _on_input_validation(self, event: InputEvent):
        """Handle input validation from precision input handler"""
        logger.debug(f"Input validation event: {event.event_type}")
    
    def _on_precision_feedback(self, feedback_type: str, data: Dict[str, Any]):
        """Handle precision feedback from precision input handler"""
        logger.debug(f"Precision feedback: {feedback_type}")


class PrecisionInputGeometryValidator:
    """
    Specialized validator for precision input geometry operations.
    """
    
    def __init__(self, config: Optional[PrecisionConfig] = None):
        """
        Initialize precision input geometry validator.
        
        Args:
            config: Precision configuration (optional)
        """
        self.config = config or config_manager.get_default_config()
        self.precision_validator = PrecisionValidator()
        self.coordinate_validator = CoordinateValidator()
    
    def validate_geometry_input(self, coordinates: List[PrecisionCoordinate], 
                               geometry_type: str) -> Dict[str, Any]:
        """
        Validate input coordinates for geometry creation.
        
        Args:
            coordinates: List of input coordinates
            geometry_type: Type of geometry to create
            
        Returns:
            Dict[str, Any]: Validation result
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "precision_violations": []
        }
        
        try:
            # Validate coordinate count
            min_coordinates = self._get_min_coordinates(geometry_type)
            if len(coordinates) < min_coordinates:
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    f"Insufficient coordinates for {geometry_type}: {len(coordinates)} < {min_coordinates}"
                )
            
            # Validate individual coordinates
            for i, coord in enumerate(coordinates):
                coord_validation = self.coordinate_validator.validate_coordinate(coord)
                if not coord_validation.is_valid:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"Coordinate {i}: {coord_validation.errors}")
            
            # Geometry-specific validation
            if geometry_type == "line" and len(coordinates) >= 2:
                self._validate_line_geometry(coordinates, validation_result)
            elif geometry_type == "circle" and len(coordinates) >= 2:
                self._validate_circle_geometry(coordinates, validation_result)
            elif geometry_type == "polygon" and len(coordinates) >= 3:
                self._validate_polygon_geometry(coordinates, validation_result)
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _get_min_coordinates(self, geometry_type: str) -> int:
        """Get minimum number of coordinates required for geometry type"""
        min_coords = {
            "point": 1,
            "line": 2,
            "segment": 2,
            "polygon": 3,
            "polyline": 2,
            "circle": 2,
            "rectangle": 2
        }
        return min_coords.get(geometry_type, 1)
    
    def _validate_line_geometry(self, coordinates: List[PrecisionCoordinate], 
                               validation_result: Dict[str, Any]):
        """Validate line geometry"""
        if len(coordinates) >= 2:
            start_coord = coordinates[0]
            end_coord = coordinates[1]
            
            # Check minimum line length
            length = start_coord.distance_to(end_coord)
            min_length = self.config.validation_rules.get('min_line_length', 0.001)
            
            if length < min_length:
                validation_result["warnings"].append(
                    f"Line length {length} is below minimum {min_length}"
                )
    
    def _validate_circle_geometry(self, coordinates: List[PrecisionCoordinate], 
                                 validation_result: Dict[str, Any]):
        """Validate circle geometry"""
        if len(coordinates) >= 2:
            center_coord = coordinates[0]
            radius_coord = coordinates[1]
            
            # Check minimum radius
            radius = center_coord.distance_to(radius_coord)
            min_radius = self.config.validation_rules.get('min_circle_radius', 0.001)
            
            if radius < min_radius:
                validation_result["warnings"].append(
                    f"Circle radius {radius} is below minimum {min_radius}"
                )
    
    def _validate_polygon_geometry(self, coordinates: List[PrecisionCoordinate], 
                                  validation_result: Dict[str, Any]):
        """Validate polygon geometry"""
        if len(coordinates) >= 3:
            # Check for degenerate polygon (zero area)
            area = self._calculate_polygon_area(coordinates)
            min_area = self.config.validation_rules.get('min_polygon_area', 0.000001)
            
            if area < min_area:
                validation_result["warnings"].append(
                    f"Polygon area {area} is below minimum {min_area}"
                )
    
    def _calculate_polygon_area(self, coordinates: List[PrecisionCoordinate]) -> float:
        """Calculate polygon area using shoelace formula"""
        if len(coordinates) < 3:
            return 0.0
        
        area = 0.0
        for i in range(len(coordinates)):
            j = (i + 1) % len(coordinates)
            area += coordinates[i].x * coordinates[j].y
            area -= coordinates[j].x * coordinates[i].y
        
        return abs(area) / 2.0


# Example usage and testing
if __name__ == "__main__":
    # Create precision input geometry integration
    integration = PrecisionInputGeometryIntegration()
    
    # Set up callbacks
    def on_input_feedback(feedback):
        print(f"Input feedback: {feedback.message}")
    
    def on_geometry_created(geometry):
        print(f"Geometry created: {geometry['type']}")
    
    integration.set_input_feedback_callback(on_input_feedback)
    integration.set_geometry_created_callback(on_geometry_created)
    
    # Test geometry creation
    session_id = integration.start_geometry_creation("line", InputMode.PRECISION_MODE)
    
    # Add coordinates
    integration.handle_mouse_input(session_id, 0.0, 0.0, 0.0, "click")
    integration.handle_mouse_input(session_id, 10.0, 10.0, 0.0, "click")
    
    # Get progress
    progress = integration.get_creation_progress(session_id)
    print(f"Creation progress: {progress}") 