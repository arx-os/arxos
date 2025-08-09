"""
Precision System Configuration

This module provides centralized configuration for the precision system,
including precision levels, validation settings, and feedback options.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class PrecisionLevel(Enum):
    """Precision levels for different use cases"""
    MILLIMETER = "millimeter"  # 0.001mm precision
    MICRON = "micron"          # 0.000001mm precision
    NANOMETER = "nanometer"    # 0.000000001mm precision
    SUB_MILLIMETER = "sub_millimeter"  # 0.0001mm precision (default)


class ValidationStrictness(Enum):
    """Validation strictness levels"""
    RELAXED = "relaxed"      # Allow minor precision violations
    NORMAL = "normal"         # Standard validation (default)
    STRICT = "strict"         # Strict validation, fail on any violation
    CRITICAL = "critical"     # Critical validation for high-precision applications


class FeedbackType(Enum):
    """Types of precision feedback"""
    VISUAL = "visual"         # Visual feedback (default)
    AUDIO = "audio"           # Audio feedback
    LOGGING = "logging"       # Log-based feedback
    NONE = "none"             # No feedback


class UseCase(Enum):
    """Predefined use cases with optimized configurations"""
    CAD_DESIGN = "cad_design"           # High precision CAD design
    VISUALIZATION = "visualization"     # Standard visualization
    RAPID_PROTOTYPING = "rapid_prototyping"  # Quick prototyping
    MANUFACTURING = "manufacturing"     # Manufacturing precision
    ARCHITECTURAL = "architectural"     # Architectural design
    ENGINEERING = "engineering"         # Engineering applications


@dataclass
class PrecisionConfig:
    """Configuration for the precision system"""

    # Precision settings
    precision_level: PrecisionLevel = PrecisionLevel.SUB_MILLIMETER
    tolerance: float = 0.001  # Default tolerance in mm
    max_precision_error: float = 0.0001  # Maximum allowed precision error

    # Validation settings
    validation_strictness: ValidationStrictness = ValidationStrictness.NORMAL
    enable_coordinate_validation: bool = True
    enable_geometric_validation: bool = True
    enable_constraint_validation: bool = True
    enable_performance_validation: bool = False

    # Feedback settings
    feedback_type: FeedbackType = FeedbackType.VISUAL
    enable_real_time_feedback: bool = True
    feedback_threshold: float = 0.001  # Threshold for feedback triggers

    # Performance settings
    enable_caching: bool = True
    cache_size: int = 1000
    enable_optimization: bool = True
    optimization_level: str = "medium"

    # Error handling
    fail_on_precision_violation: bool = False
    auto_correct_precision_errors: bool = True
    log_precision_violations: bool = True

    # Input settings
    input_precision_mode: str = "auto"  # auto, manual, grid
    grid_snap_enabled: bool = True
    grid_snap_tolerance: float = 0.001
    angle_snap_enabled: bool = True
    angle_snap_increment: float = 15.0  # degrees

    # Display settings
    display_precision: int = 3  # Decimal places to display
    show_precision_indicators: bool = True
    precision_color_scheme: str = "standard"  # standard, high_contrast, colorblind

    # Advanced settings
    enable_adaptive_precision: bool = False
    adaptive_precision_threshold: float = 0.01
    enable_precision_learning: bool = False
    precision_learning_rate: float = 0.1

    # Validation rules
    validation_rules: Dict[str, Any] = field(default_factory=lambda: {
        "coordinate_range": {"min": -1e6, "max": 1e6},
        "min_distance": 0.001,
        "max_distance": 1e6,
        "min_angle": 0.1,
        "max_angle": 359.9,
        "min_area": 0.000001,
        "max_area": 1e12,
        "min_perimeter": 0.001,
        "max_perimeter": 1e6
    })

    # Performance thresholds
    performance_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "max_calculation_time": 0.1,  # seconds
        "max_memory_usage": 100.0,    # MB
        "max_iterations": 1000,
        "convergence_tolerance": 0.001
    })

    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_config()

    def _validate_config(self):
        """Validate configuration parameters"""
        if self.tolerance <= 0:
            raise ValueError("Tolerance must be positive")

        if self.max_precision_error <= 0:
            raise ValueError("Max precision error must be positive")

        if self.feedback_threshold <= 0:
            raise ValueError("Feedback threshold must be positive")

        if self.cache_size <= 0:
            raise ValueError("Cache size must be positive")

        if self.grid_snap_tolerance <= 0:
            raise ValueError("Grid snap tolerance must be positive")

        if self.angle_snap_increment <= 0 or self.angle_snap_increment > 360:
            raise ValueError("Angle snap increment must be between 0 and 360")

        if self.display_precision < 0:
            raise ValueError("Display precision must be non-negative")

    @classmethod
def for_use_case(cls, use_case: UseCase) -> 'PrecisionConfig':
        """Create configuration optimized for a specific use case"""
        configs = {
            UseCase.CAD_DESIGN: cls._cad_design_config(),
            UseCase.VISUALIZATION: cls._visualization_config(),
            UseCase.RAPID_PROTOTYPING: cls._rapid_prototyping_config(),
            UseCase.MANUFACTURING: cls._manufacturing_config(),
            UseCase.ARCHITECTURAL: cls._architectural_config(),
            UseCase.ENGINEERING: cls._engineering_config()
        }
        return configs.get(use_case, cls()
    @classmethod
def _cad_design_config(cls) -> 'PrecisionConfig':
        """Configuration optimized for CAD design"""
        config = cls()
        config.precision_level = PrecisionLevel.MICRON
        config.tolerance = 0.0001
        config.max_precision_error = 0.00001
        config.validation_strictness = ValidationStrictness.STRICT
        config.fail_on_precision_violation = True
        config.auto_correct_precision_errors = False
        config.input_precision_mode = "manual"
        config.grid_snap_tolerance = 0.0001
        config.angle_snap_increment = 1.0
        config.display_precision = 4
        config.show_precision_indicators = True
        return config

    @classmethod
def _visualization_config(cls) -> 'PrecisionConfig':
        """Configuration optimized for visualization"""
        config = cls()
        config.precision_level = PrecisionLevel.MILLIMETER
        config.tolerance = 0.01
        config.max_precision_error = 0.001
        config.validation_strictness = ValidationStrictness.RELAXED
        config.fail_on_precision_violation = False
        config.auto_correct_precision_errors = True
        config.input_precision_mode = "auto"
        config.grid_snap_tolerance = 0.01
        config.angle_snap_increment = 15.0
        config.display_precision = 2
        config.show_precision_indicators = False
        config.enable_real_time_feedback = False
        return config

    @classmethod
def _rapid_prototyping_config(cls) -> 'PrecisionConfig':
        """Configuration optimized for rapid prototyping"""
        config = cls()
        config.precision_level = PrecisionLevel.SUB_MILLIMETER
        config.tolerance = 0.01
        config.max_precision_error = 0.001
        config.validation_strictness = ValidationStrictness.NORMAL
        config.fail_on_precision_violation = False
        config.auto_correct_precision_errors = True
        config.input_precision_mode = "grid"
        config.grid_snap_tolerance = 0.01
        config.angle_snap_increment = 5.0
        config.display_precision = 2
        config.show_precision_indicators = True
        config.enable_real_time_feedback = True
        return config

    @classmethod
def _manufacturing_config(cls) -> 'PrecisionConfig':
        """Configuration optimized for manufacturing"""
        config = cls()
        config.precision_level = PrecisionLevel.NANOMETER
        config.tolerance = 0.000001
        config.max_precision_error = 0.0000001
        config.validation_strictness = ValidationStrictness.CRITICAL
        config.fail_on_precision_violation = True
        config.auto_correct_precision_errors = False
        config.input_precision_mode = "manual"
        config.grid_snap_tolerance = 0.000001
        config.angle_snap_increment = 0.1
        config.display_precision = 6
        config.show_precision_indicators = True
        config.enable_real_time_feedback = True
        return config

    @classmethod
def _architectural_config(cls) -> 'PrecisionConfig':
        """Configuration optimized for architectural design"""
        config = cls()
        config.precision_level = PrecisionLevel.MILLIMETER
        config.tolerance = 0.1
        config.max_precision_error = 0.01
        config.validation_strictness = ValidationStrictness.NORMAL
        config.fail_on_precision_violation = False
        config.auto_correct_precision_errors = True
        config.input_precision_mode = "grid"
        config.grid_snap_tolerance = 0.1
        config.angle_snap_increment = 90.0
        config.display_precision = 1
        config.show_precision_indicators = True
        config.enable_real_time_feedback = True
        return config

    @classmethod
def _engineering_config(cls) -> 'PrecisionConfig':
        """Configuration optimized for engineering applications"""
        config = cls()
        config.precision_level = PrecisionLevel.MICRON
        config.tolerance = 0.001
        config.max_precision_error = 0.0001
        config.validation_strictness = ValidationStrictness.STRICT
        config.fail_on_precision_violation = True
        config.auto_correct_precision_errors = False
        config.input_precision_mode = "manual"
        config.grid_snap_tolerance = 0.001
        config.angle_snap_increment = 1.0
        config.display_precision = 3
        config.show_precision_indicators = True
        config.enable_real_time_feedback = True
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'precision_level': self.precision_level.value,
            'tolerance': self.tolerance,
            'max_precision_error': self.max_precision_error,
            'validation_strictness': self.validation_strictness.value,
            'enable_coordinate_validation': self.enable_coordinate_validation,
            'enable_geometric_validation': self.enable_geometric_validation,
            'enable_constraint_validation': self.enable_constraint_validation,
            'enable_performance_validation': self.enable_performance_validation,
            'feedback_type': self.feedback_type.value,
            'enable_real_time_feedback': self.enable_real_time_feedback,
            'feedback_threshold': self.feedback_threshold,
            'enable_caching': self.enable_caching,
            'cache_size': self.cache_size,
            'enable_optimization': self.enable_optimization,
            'optimization_level': self.optimization_level,
            'fail_on_precision_violation': self.fail_on_precision_violation,
            'auto_correct_precision_errors': self.auto_correct_precision_errors,
            'log_precision_violations': self.log_precision_violations,
            'input_precision_mode': self.input_precision_mode,
            'grid_snap_enabled': self.grid_snap_enabled,
            'grid_snap_tolerance': self.grid_snap_tolerance,
            'angle_snap_enabled': self.angle_snap_enabled,
            'angle_snap_increment': self.angle_snap_increment,
            'display_precision': self.display_precision,
            'show_precision_indicators': self.show_precision_indicators,
            'precision_color_scheme': self.precision_color_scheme,
            'enable_adaptive_precision': self.enable_adaptive_precision,
            'adaptive_precision_threshold': self.adaptive_precision_threshold,
            'enable_precision_learning': self.enable_precision_learning,
            'precision_learning_rate': self.precision_learning_rate,
            'validation_rules': self.validation_rules,
            'performance_thresholds': self.performance_thresholds
        }

    @classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'PrecisionConfig':
        """Create configuration from dictionary"""
        config = cls()

        # Update with provided values
        for key, value in data.items():
            if hasattr(config, key):
                if key == 'precision_level':
                    setattr(config, key, PrecisionLevel(value)
                elif key == 'validation_strictness':
                    setattr(config, key, ValidationStrictness(value)
                elif key == 'feedback_type':
                    setattr(config, key, FeedbackType(value)
                else:
                    setattr(config, key, value)

        return config

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Precision configuration saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save precision configuration: {e}")
            raise

    @classmethod
def load_from_file(cls, filepath: str) -> 'PrecisionConfig':
        """Load configuration from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            config = cls.from_dict(data)
            logger.info(f"Precision configuration loaded from {filepath}")
            return config
        except Exception as e:
            logger.error(f"Failed to load precision configuration: {e}")
            raise

    def get_precision_value(self) -> float:
        """Get the precision value based on precision level"""
        precision_values = {
            PrecisionLevel.MILLIMETER: 0.001,
            PrecisionLevel.MICRON: 0.000001,
            PrecisionLevel.NANOMETER: 0.000000001,
            PrecisionLevel.SUB_MILLIMETER: 0.0001
        }
        return precision_values.get(self.precision_level, 0.0001)

    def is_precision_violation(self, error: float) -> bool:
        """Check if an error constitutes a precision violation"""
        return abs(error) > self.max_precision_error

    def should_fail_on_violation(self) -> bool:
        """Check if the system should fail on precision violations"""
        return self.fail_on_precision_violation and self.validation_strictness in [
            ValidationStrictness.STRICT, ValidationStrictness.CRITICAL
        ]

    def get_validation_level(self) -> str:
        """Get validation level based on strictness"""
        if self.validation_strictness == ValidationStrictness.CRITICAL:
            return "CRITICAL"
        elif self.validation_strictness == ValidationStrictness.STRICT:
            return "WARNING"
        elif self.validation_strictness == ValidationStrictness.NORMAL:
            return "INFO"
        else:
            return "DEBUG"


class PrecisionConfigManager:
    """Manager for precision configurations"""

    def __init__(self):
        pass
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self._configs: Dict[str, PrecisionConfig] = {}
        self._default_config: Optional[PrecisionConfig] = None

    def register_config(self, name: str, config: PrecisionConfig) -> None:
        """Register a configuration with a name"""
        self._configs[name] = config

    def get_config(self, name: str) -> Optional[PrecisionConfig]:
        """Get a configuration by name"""
        return self._configs.get(name)

    def set_default_config(self, config: PrecisionConfig) -> None:
        """Set the default configuration"""
        self._default_config = config

    def get_default_config(self) -> PrecisionConfig:
        """Get the default configuration"""
        if self._default_config is None:
            self._default_config = PrecisionConfig()
        return self._default_config

    def list_configs(self) -> List[str]:
        """List all registered configuration names"""
        return list(self._configs.keys()
    def remove_config(self, name: str) -> bool:
        """Remove a configuration by name"""
        if name in self._configs:
            del self._configs[name]
            return True
        return False


# Global configuration manager instance
config_manager = PrecisionConfigManager()
