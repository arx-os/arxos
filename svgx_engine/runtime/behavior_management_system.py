"""
SVGX Engine - Behavior Management System

Handles comprehensive behavior organization and documentation including discovery, registration, validation, versioning, and documentation.
Supports behavior lifecycle management, conflict resolution, and performance analytics.
Integrates with all behavior systems and provides enterprise-grade behavior management.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Set, Tuple, Union
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import threading
import json
import hashlib
from copy import deepcopy
import inspect
import re
import subprocess
import shlex
from typing import List, Optional
import html

def safe_execute_command(command: str, args: List[str] = None, timeout: int = 30) -> subprocess.CompletedProcess:
    """
    Execute command safely with input validation.

    Args:
        command: Command to execute
        args: Command arguments
        timeout: Command timeout in seconds

    Returns:
        CompletedProcess result

    Raises:
        ValueError: If command is not allowed
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails
    """
    # Validate command
    if command not in ALLOWED_COMMANDS:
        raise ValueError(f"Command '{command}' is not allowed")

    # Prepare command
    cmd = [command] + (args or [])

    # Execute with security measures
    try:
        result = subprocess.run(
            cmd,
            shell=False,  # Prevent shell injection
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None,  # Use current directory
            env=None,  # Use current environment
            check=False  # Don't raise on non-zero exit'
        )
        return result
    except subprocess.TimeoutExpired:
        raise subprocess.TimeoutExpired(cmd, timeout)
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(e.returncode, cmd, e.stdout, e.stderr)
    except Exception as e:
        raise RuntimeError(f"Command execution failed: {e}")

# Allowed commands whitelist
ALLOWED_COMMANDS = [
    'git', 'docker', 'npm', 'python', 'python3',
    'pip', 'pip3', 'node', 'npm', 'yarn',
    'ls', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv',
    'chmod', 'chown', 'tar', 'gzip', 'gunzip'
]


logger = logging.getLogger(__name__)

class BehaviorType(Enum):
    """Types of behaviors supported by the Behavior Management System."""
    EVENT_DRIVEN = "event_driven"
    STATE_MACHINE = "state_machine"
    CONDITIONAL_LOGIC = "conditional_logic"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    UI_SELECTION = "ui_selection"
    UI_EDITING = "ui_editing"
    UI_NAVIGATION = "ui_navigation"
    UI_ANNOTATION = "ui_annotation"
    TIME_BASED_TRIGGER = "time_based_trigger"
    RULE_ENGINE = "rule_engine"
    CUSTOM = "custom"

class BehaviorStatus(Enum):
    """Status states for behaviors."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    TESTING = "testing"
    ARCHIVED = "archived"

class ValidationLevel(Enum):
    """Validation levels for behavior validation."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    ENTERPRISE = "enterprise"

@dataclass
class BehaviorMetadata:
    """Metadata for behavior documentation and management."""
    author: str
    created_at: datetime
    updated_at: datetime
    version: str
    description: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    usage_examples: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None

@dataclass
class BehaviorValidation:
    """Validation result for behavior validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    validation_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class BehaviorVersion:
    """Version information for behavior versioning."""
    version: str
    changes: List[str]
    author: str
    timestamp: datetime
    is_stable: bool = True
    rollback_supported: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Behavior:
    """Represents a behavior in the Behavior Management System."""
    id: str
    name: str
    behavior_type: BehaviorType
    status: BehaviorStatus
    metadata: BehaviorMetadata
    implementation: Dict[str, Any]
    validation: Optional[BehaviorValidation] = None
    versions: List[BehaviorVersion] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    performance_history: List[Dict[str, Any]] = field(default_factory=list)

class BehaviorManagementSystem:
    """
    Comprehensive behavior management system for discovery, registration, validation, versioning, and documentation.
    Supports enterprise-grade behavior lifecycle management.
    """
def __init__(self):
        # {behavior_id: Behavior}
        self.behaviors: Dict[str, Behavior] = {}
        # {behavior_type: Set[behavior_id]}
        self.behaviors_by_type: Dict[BehaviorType, Set[str]] = {}
        # {status: Set[behavior_id]}
        self.behaviors_by_status: Dict[BehaviorStatus, Set[str]] = {}
        # {tag: Set[behavior_id]}
        self.behaviors_by_tag: Dict[str, Set[str]] = {}
        # Behavior discovery patterns
        self.discovery_patterns: Dict[str, re.Pattern] = {}
        # Validation rules
        self.validation_rules: Dict[ValidationLevel, List[Dict[str, Any]]] = {}
        # Performance tracking
        self.performance_tracking: Dict[str, List[Dict[str, Any]]] = {}
        # Thread safety
        self._lock = threading.RLock()

        # Initialize discovery patterns
        self._initialize_discovery_patterns()
        # Initialize validation rules
        self._initialize_validation_rules()

    def _initialize_discovery_patterns(self):
        """Initialize patterns for behavior discovery."""
        self.discovery_patterns = {
            "event_handler": re.compile(r"def\s+handle_\w+_event\s*\("),
            "state_transition": re.compile(r"def\s+transition_\w+\s*\("),
            "condition_evaluation": re.compile(r"def\s+evaluate_\w+_condition\s*\("),
            "action_execution": re.compile(r"def\s+execute_\w+_action\s*\("),
            "rule_definition": re.compile(r"def\s+define_\w+_rule\s*\("),
            "ui_interaction": re.compile(r"def\s+handle_\w+_interaction\s*\("),
            "performance_optimization": re.compile(r"def\s+optimize_\w+\s*\("),
            "custom_behavior": re.compile(r"def\s+\w+_behavior\s*\(")
        }

    def _initialize_validation_rules(self):
        """Initialize validation rules for different levels."""
        self.validation_rules = {
            ValidationLevel.BASIC: [
                {"name": "required_fields", "check": self._validate_required_fields},
                {"name": "naming_convention", "check": self._validate_naming_convention}
            ],
            ValidationLevel.STANDARD: [
                {"name": "required_fields", "check": self._validate_required_fields},
                {"name": "naming_convention", "check": self._validate_naming_convention},
                {"name": "implementation_structure", "check": self._validate_implementation_structure},
                {"name": "dependency_check", "check": self._validate_dependencies}
            ],
            ValidationLevel.STRICT: [
                {"name": "required_fields", "check": self._validate_required_fields},
                {"name": "naming_convention", "check": self._validate_naming_convention},
                {"name": "implementation_structure", "check": self._validate_implementation_structure},
                {"name": "dependency_check", "check": self._validate_dependencies},
                {"name": "performance_requirements", "check": self._validate_performance_requirements},
                {"name": "security_check", "check": self._validate_security}
            ],
            ValidationLevel.ENTERPRISE: [
                {"name": "required_fields", "check": self._validate_required_fields},
                {"name": "naming_convention", "check": self._validate_naming_convention},
                {"name": "implementation_structure", "check": self._validate_implementation_structure},
                {"name": "dependency_check", "check": self._validate_dependencies},
                {"name": "performance_requirements", "check": self._validate_performance_requirements},
                {"name": "security_check", "check": self._validate_security},
                {"name": "compliance_check", "check": self._validate_compliance},
                {"name": "documentation_check", "check": self._validate_documentation}
            ]
        }

    async def discover_behaviors(self, element_id: str = None, behavior_types: Optional[List[BehaviorType]] = None) -> List[Behavior]:
        """
        Discover behaviors using pattern recognition and analysis.

        Args:
            element_id: Optional element ID to focus discovery on
            behavior_types: Optional filter for specific behavior types

        Returns:
            List of discovered behaviors
        """
        try:
            with self._lock:
                discovered_behaviors = []

                # Import behavior systems for discovery
                from svgx_engine import (
                    event_driven_behavior_engine, advanced_state_machine,
                    conditional_logic_engine, performance_optimization_engine,
                    selection_handler, editing_handler, navigation_handler,
                    annotation_handler, time_based_trigger_system, advanced_rule_engine
                )

                # Discover behaviors from each system
                systems = [
                    (event_driven_behavior_engine, BehaviorType.EVENT_DRIVEN),
                    (advanced_state_machine, BehaviorType.STATE_MACHINE),
                    (conditional_logic_engine, BehaviorType.CONDITIONAL_LOGIC),
                    (performance_optimization_engine, BehaviorType.PERFORMANCE_OPTIMIZATION),
                    (selection_handler, BehaviorType.UI_SELECTION),
                    (editing_handler, BehaviorType.UI_EDITING),
                    (navigation_handler, BehaviorType.UI_NAVIGATION),
                    (annotation_handler, BehaviorType.UI_ANNOTATION),
                    (time_based_trigger_system, BehaviorType.TIME_BASED_TRIGGER),
                    (advanced_rule_engine, BehaviorType.RULE_ENGINE)
                ]

                for system, behavior_type in systems:
                    if behavior_types and behavior_type not in behavior_types:
                        continue

                    # Discover behaviors from system import system
                    system_behaviors = await self._discover_system_behaviors(system, behavior_type, element_id)
                    discovered_behaviors.extend(system_behaviors)

                # Apply pattern recognition for custom behaviors
                custom_behaviors = await self._discover_custom_behaviors(element_id)
                discovered_behaviors.extend(custom_behaviors)

                logger.info(f"Discovered {len(discovered_behaviors)} behaviors")
                return discovered_behaviors

        except Exception as e:
            logger.error(f"Error discovering behaviors: {e}")
            return []

    async def _discover_system_behaviors(self, system, behavior_type: BehaviorType, element_id: str = None) -> List[Behavior]:
        """Discover behaviors from a specific system."""
        behaviors = []

        try:
            # Analyze system methods and attributes
            system_methods = inspect.getmembers(system, inspect.ismethod)
            system_attributes = inspect.getmembers(system, lambda x: not inspect.ismethod(x)
            for method_name, method in system_methods:
                if self._is_behavior_method(method_name, behavior_type):
                    behavior = await self._create_behavior_from_method(
                        method_name, method, behavior_type, system, element_id
                    )
                    if behavior:
                        behaviors.append(behavior)

            # Check for system-level behaviors
            system_behavior = await self._create_system_behavior(system, behavior_type, element_id)
            if system_behavior:
                behaviors.append(system_behavior)

        except Exception as e:
            logger.error(f"Error discovering behaviors from {behavior_type.value}: {e}")

        return behaviors

    def _is_behavior_method(self, method_name: str, behavior_type: BehaviorType) -> bool:
        """Check if a method represents a behavior based on naming patterns."""
        patterns = {
            BehaviorType.EVENT_DRIVEN: [r"handle_\w+_event", r"process_\w+_event"],
            BehaviorType.STATE_MACHINE: [r"transition_\w+", r"change_\w+_state"],
            BehaviorType.CONDITIONAL_LOGIC: [r"evaluate_\w+_condition", r"check_\w+_condition"],
            BehaviorType.PERFORMANCE_OPTIMIZATION: [r"optimize_\w+", r"cache_\w+", r"lazy_\w+"],
            BehaviorType.UI_SELECTION: [r"select_\w+", r"deselect_\w+", r"toggle_\w+"],
            BehaviorType.UI_EDITING: [r"edit_\w+", r"undo_\w+", r"redo_\w+"],
            BehaviorType.UI_NAVIGATION: [r"navigate_\w+", r"pan_\w+", r"zoom_\w+"],
            BehaviorType.UI_ANNOTATION: [r"annotate_\w+", r"create_\w+_annotation"],
            BehaviorType.TIME_BASED_TRIGGER: [r"schedule_\w+", r"trigger_\w+", r"time_\w+"],
            BehaviorType.RULE_ENGINE: [r"evaluate_\w+_rule", r"apply_\w+_rule", r"validate_\w+_rule"]
        }

        if behavior_type in patterns:
            for pattern in patterns[behavior_type]:
                if re.match(pattern, method_name):
                    return True

        return False

    async def _create_behavior_from_method(self, method_name: str, method, behavior_type: BehaviorType, system, element_id: str = None) -> Optional[Behavior]:
        """Create a behavior from a discovered method."""
        try:
            behavior_id = f"{behavior_type.value}_{method_name}"

            # Create metadata
            metadata = BehaviorMetadata(
                author="System Discovery",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version="1.0.0",
                description=f"Discovered {behavior_type.value} behavior: {method_name}",
                tags=[behavior_type.value, "discovered", method_name],
                dependencies=[],
                performance_metrics={},
                usage_examples=[f"system.{method_name}()"]
            )

            # Create implementation info
            implementation = {
                "method_name": method_name,
                "system_type": type(system).__name__,
                "signature": str(inspect.signature(method)),
                "docstring": method.__doc__ or "",
                "is_async": asyncio.iscoroutinefunction(method)
            }

            behavior = Behavior(
                id=behavior_id,
                name=f"{behavior_type.value.title()} {method_name.replace('_', ' ').title()}",
                behavior_type=behavior_type,
                status=BehaviorStatus.ACTIVE,
                metadata=metadata,
                implementation=implementation
            )

            return behavior

        except Exception as e:
            logger.error(f"Error creating behavior from method {method_name}: {e}")
            return None

    async def _create_system_behavior(self, system, behavior_type: BehaviorType, element_id: str = None) -> Optional[Behavior]:
        """Create a behavior representing the entire system."""
        try:
            system_name = type(system).__name__
            behavior_id = f"{behavior_type.value}_system_{system_name.lower()}"

            # Create metadata
            metadata = BehaviorMetadata(
                author="System Discovery",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version="1.0.0",
                description=f"System behavior: {system_name}",
                tags=[behavior_type.value, "system", system_name.lower()],
                dependencies=[],
                performance_metrics={},
                usage_examples=[f"system = {system_name}()"]
            )

            # Create implementation info
            implementation = {
                "system_name": system_name,
                "behavior_type": behavior_type.value,
                "methods": [name for name, _ in inspect.getmembers(system, inspect.ismethod)],
                "attributes": [name for name, _ in inspect.getmembers(system, lambda x: not inspect.ismethod(x))]
            }

            behavior = Behavior(
                id=behavior_id,
                name=f"{behavior_type.value.title()} System: {system_name}",
                behavior_type=behavior_type,
                status=BehaviorStatus.ACTIVE,
                metadata=metadata,
                implementation=implementation
            )

            return behavior

        except Exception as e:
            logger.error(f"Error creating system behavior: {e}")
            return None

    async def _discover_custom_behaviors(self, element_id: str = None) -> List[Behavior]:
        """Discover custom behaviors using pattern recognition."""
        behaviors = []

        try:
            # This would typically scan code files for custom behavior patterns
            # For now, return empty list as custom behaviors are user-defined
            pass

        except Exception as e:
            logger.error(f"Error discovering custom behaviors: {e}")

        return behaviors

    def register_behavior(self, behavior: Behavior) -> bool:
        """Register a behavior with validation and conflict detection."""
        try:
            with self._lock:
                # Validate behavior
                validation = self.validate_behavior(behavior, ValidationLevel.STANDARD)
                if not validation.is_valid:
                    logger.error(f"Behavior validation failed for {behavior.id}: {validation.errors}")
                    return False

                # Check for conflicts
                conflicts = self._detect_conflicts(behavior)
                if conflicts:
                    behavior.conflicts = conflicts
                    logger.warning(f"Behavior {behavior.id} has conflicts: {conflicts}")

                # Create initial version record
                initial_version = BehaviorVersion(
                    version=behavior.metadata.version,
                    changes=["Initial version"],
                    author=behavior.metadata.author,
                    timestamp=behavior.metadata.created_at
                )
                behavior.versions.append(initial_version)

                # Register behavior
                self.behaviors[behavior.id] = behavior

                # Update indexes
                if behavior.behavior_type not in self.behaviors_by_type:
                    self.behaviors_by_type[behavior.behavior_type] = set()
                self.behaviors_by_type[behavior.behavior_type].add(behavior.id)

                if behavior.status not in self.behaviors_by_status:
                    self.behaviors_by_status[behavior.status] = set()
                self.behaviors_by_status[behavior.status].add(behavior.id)

                for tag in behavior.metadata.tags:
                    if tag not in self.behaviors_by_tag:
                        self.behaviors_by_tag[tag] = set()
                    self.behaviors_by_tag[tag].add(behavior.id)

                logger.info(f"Registered behavior: {behavior.id}")
                return True

        except Exception as e:
            logger.error(f"Error registering behavior {behavior.id}: {e}")
            return False

    def validate_behavior(self, behavior: Behavior, level: ValidationLevel = ValidationLevel.STANDARD) -> BehaviorValidation:
        """Validate a behavior according to the specified validation level."""
        try:
            errors = []
            warnings = []
            suggestions = []

            # Run validation rules for the specified level
            if level in self.validation_rules:
                for rule in self.validation_rules[level]:
                    rule_name = rule["name"]
                    rule_check = rule["check"]

                    try:
                        result = rule_check(behavior)
                        if isinstance(result, dict):
                            if "errors" in result:
                                errors.extend(result["errors"])
                            if "warnings" in result:
                                warnings.extend(result["warnings"])
                            if "suggestions" in result:
                                suggestions.extend(result["suggestions"])
                    except Exception as e:
                        errors.append(f"Validation rule '{rule_name}' failed: {e}")

            # Calculate validation score
            total_checks = len(self.validation_rules.get(level, [])
            passed_checks = total_checks - len(errors)
            validation_score = passed_checks / total_checks if total_checks > 0 else 0.0

            is_valid = len(errors) == 0

            validation = BehaviorValidation(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                validation_level=level,
                validation_score=validation_score
            )

            # Update behavior with validation result
            behavior.validation = validation

            return validation

        except Exception as e:
            logger.error(f"Error validating behavior {behavior.id}: {e}")
            return BehaviorValidation(
                is_valid=False,
                errors=[f"Validation failed: {e}"],
                validation_level=level,
                validation_score=0.0
            )

    def _validate_required_fields(self, behavior: Behavior) -> Dict[str, List[str]]:
        """Validate that all required fields are present."""
        errors = []
        warnings = []

        required_fields = ["id", "name", "behavior_type", "status", "metadata", "implementation"]
        for field in required_fields:
            if not hasattr(behavior, field) or getattr(behavior, field) is None:
                errors.append(f"Missing required field: {field}")

        if not behavior.metadata.description:
            warnings.append("Behavior description is empty")

        return {"errors": errors, "warnings": warnings}

    def _validate_naming_convention(self, behavior: Behavior) -> Dict[str, List[str]]:
        """Validate naming conventions."""
        errors = []
        warnings = []

        # Check behavior ID format
        if not re.match(r"^[a-z][a-z0-9_]*$", behavior.id):
            errors.append("Behavior ID must follow snake_case convention")

        # Check behavior name
        if len(behavior.name) < 3:
            errors.append("Behavior name is too short")
        elif len(behavior.name) > 100:
            warnings.append("Behavior name is very long")

        return {"errors": errors, "warnings": warnings}

    def _validate_implementation_structure(self, behavior: Behavior) -> Dict[str, List[str]]:
        """Validate implementation structure."""
        errors = []
        warnings = []

        if "implementation" not in behavior.__dict__:
            errors.append("Missing implementation information")
        else:
            impl = behavior.implementation
            if not isinstance(impl, dict):
                errors.append("Implementation must be a dictionary")
            elif not impl:
                warnings.append("Implementation is empty")

        return {"errors": errors, "warnings": warnings}

    def _validate_dependencies(self, behavior: Behavior) -> Dict[str, List[str]]:
        """Validate behavior dependencies."""
        errors = []
        warnings = []

        for dep in behavior.metadata.dependencies:
            if dep not in self.behaviors:
                warnings.append(f"Dependency not found: {dep}")

        return {"errors": errors, "warnings": warnings}

    def _validate_performance_requirements(self, behavior: Behavior) -> Dict[str, List[str]]:
        """Validate performance requirements."""
        errors = []
        warnings = []

        # This would check against performance benchmarks
        # For now, just basic checks
        if "performance_metrics" in behavior.metadata.__dict__:
            metrics = behavior.metadata.performance_metrics
            if isinstance(metrics, dict):
                if "response_time" in metrics and metrics["response_time"] > 100:
                    warnings.append("Response time exceeds recommended threshold")

        return {"errors": errors, "warnings": warnings}

    def _validate_security(self, behavior: Behavior) -> Dict[str, List[str]]:
        """Validate security requirements."""
        errors = []
        warnings = []

        # Basic security checks
        impl_str = str(behavior.implementation)
        if "# SECURITY: eval() removed - use safe alternatives"
        # eval(" in impl_str or "exec(" in impl_str:"
            errors.append("Potentially unsafe code detected")

        return {"errors": errors, "warnings": warnings}

    def _validate_compliance(self, behavior: Behavior) -> Dict[str, List[str]]:
        """Validate compliance requirements."""
        errors = []
        warnings = []

        # This would check against compliance standards
        # For now, just basic checks
        if not behavior.metadata.documentation_url:
            warnings.append("Documentation URL is missing")

        return {"errors": errors, "warnings": warnings}

    def _validate_documentation(self, behavior: Behavior) -> Dict[str, List[str]]:
        """Validate documentation requirements."""
        errors = []
        warnings = []

        if not behavior.metadata.description or len(behavior.metadata.description) < 10:
            warnings.append("Behavior description is too short")

        if not behavior.metadata.usage_examples:
            warnings.append("No usage examples provided")

        return {"errors": errors, "warnings": warnings}

    def _detect_conflicts(self, behavior: Behavior) -> List[str]:
        """Detect conflicts with existing behaviors."""
        conflicts = []

        # Check for naming conflicts
        for existing_id, existing_behavior in self.behaviors.items():
            if existing_id != behavior.id:
                if existing_behavior.name == behavior.name:
                    conflicts.append(f"Naming conflict with {existing_id}")

                # Check for implementation conflicts
                if (existing_behavior.behavior_type == behavior.behavior_type and
                    existing_behavior.implementation.get("method_name") == behavior.implementation.get("method_name")):
                    conflicts.append(f"Implementation conflict with {existing_id}")

        return conflicts

    def version_behavior(self, behavior_id: str, version: str, changes: List[str], author: str) -> bool:
        """Create a new version of a behavior."""
        try:
            with self._lock:
                if behavior_id not in self.behaviors:
                    logger.error(f"Behavior {behavior_id} not found")
                    return False

                behavior = self.behaviors[behavior_id]

                # Create version record
                version_record = BehaviorVersion(
                    version=version,
                    changes=changes,
                    author=author,
                    timestamp=datetime.utcnow()
                # Add to versions list
                behavior.versions.append(version_record)

                # Update metadata
                behavior.metadata.version = version
                behavior.metadata.updated_at = datetime.utcnow()

                logger.info(f"Created version {version} for behavior {behavior_id}")
                return True

        except Exception as e:
            logger.error(f"Error versioning behavior {behavior_id}: {e}")
            return False

    def rollback_behavior(self, behavior_id: str, target_version: str) -> bool:
        """Rollback a behavior to a previous version."""
        try:
            with self._lock:
                if behavior_id not in self.behaviors:
                    logger.error(f"Behavior {behavior_id} not found")
                    return False

                behavior = self.behaviors[behavior_id]

                # Find target version
                target_version_record = None
                for version in behavior.versions:
                    if version.version == target_version:
                        target_version_record = version
                        break

                if not target_version_record:
                    logger.error(f"Version {target_version} not found for behavior {behavior_id}")
                    return False

                if not target_version_record.rollback_supported:
                    logger.error(f"Rollback not supported for version {target_version}")
                    return False

                # Create rollback version
                rollback_version = BehaviorVersion(
                    version=f"{behavior.metadata.version}_rollback_to_{target_version}",
                    changes=[f"Rolled back to version {target_version}"],
                    author="System",
                    timestamp=datetime.utcnow(),
                    is_stable=False
                )

                behavior.versions.append(rollback_version)
                behavior.metadata.version = target_version
                behavior.metadata.updated_at = datetime.utcnow()

                logger.info(f"Rolled back behavior {behavior_id} to version {target_version}")
                return True

        except Exception as e:
            logger.error(f"Error rolling back behavior {behavior_id}: {e}")
            return False

    def document_behavior(self, behavior_id: str) -> Optional[Dict[str, Any]]:
        """Generate comprehensive documentation for a behavior."""
        try:
            with self._lock:
                if behavior_id not in self.behaviors:
                    logger.error(f"Behavior {behavior_id} not found")
                    return None

                behavior = self.behaviors[behavior_id]

                documentation = {
                    "id": behavior.id,
                    "name": behavior.name,
                    "type": behavior.behavior_type.value,
                    "status": behavior.status.value,
                    "description": behavior.metadata.description,
                    "author": behavior.metadata.author,
                    "version": behavior.metadata.version,
                    "created_at": behavior.metadata.created_at.isoformat(),
                    "updated_at": behavior.metadata.updated_at.isoformat(),
                    "tags": behavior.metadata.tags,
                    "dependencies": behavior.metadata.dependencies,
                    "implementation": behavior.implementation,
                    "validation": {
                        "is_valid": behavior.validation.is_valid if behavior.validation else False,
                        "score": behavior.validation.validation_score if behavior.validation else 0.0,
                        "errors": behavior.validation.errors if behavior.validation else [],
                        "warnings": behavior.validation.warnings if behavior.validation else [],
                        "suggestions": behavior.validation.suggestions if behavior.validation else []
                    },
                    "versions": [
                        {
                            "version": v.version,
                            "changes": v.changes,
                            "author": v.author,
                            "timestamp": v.timestamp.isoformat(),
                            "is_stable": v.is_stable
                        }
                        for v in behavior.versions
                    ],
                    "conflicts": behavior.conflicts,
                    "performance_history": behavior.performance_history,
                    "usage_examples": behavior.metadata.usage_examples,
                    "documentation_url": behavior.metadata.documentation_url
                }

                return documentation

        except Exception as e:
            logger.error(f"Error documenting behavior {behavior_id}: {e}")
            return None

    def get_behavior(self, behavior_id: str) -> Optional[Behavior]:
        """Get a behavior by ID."""
        return self.behaviors.get(behavior_id)

    def get_behaviors_by_type(self, behavior_type: BehaviorType) -> List[Behavior]:
        """Get all behaviors of a specific type."""
        behavior_ids = self.behaviors_by_type.get(behavior_type, set()
        return [self.behaviors[bid] for bid in behavior_ids if bid in self.behaviors]

    def get_behaviors_by_status(self, status: BehaviorStatus) -> List[Behavior]:
        """Get all behaviors with a specific status."""
        behavior_ids = self.behaviors_by_status.get(status, set()
        return [self.behaviors[bid] for bid in behavior_ids if bid in self.behaviors]

    def get_behaviors_by_tag(self, tag: str) -> List[Behavior]:
        """Get all behaviors with a specific tag."""
        behavior_ids = self.behaviors_by_tag.get(tag, set()
        return [self.behaviors[bid] for bid in behavior_ids if bid in self.behaviors]

    def update_behavior(self, behavior_id: str, updates: Dict[str, Any]) -> bool:
        """Update a behavior with new information."""
        try:
            with self._lock:
                if behavior_id not in self.behaviors:
                    logger.error(f"Behavior {behavior_id} not found")
                    return False

                behavior = self.behaviors[behavior_id]

                # Update fields
                for field, value in updates.items():
                    if hasattr(behavior, field):
                        setattr(behavior, field, value)
                    elif hasattr(behavior.metadata, field):
                        setattr(behavior.metadata, field, value)

                behavior.metadata.updated_at = datetime.utcnow()

                # Re-validate behavior
                self.validate_behavior(behavior, ValidationLevel.STANDARD)

                logger.info(f"Updated behavior: {behavior_id}")
                return True

        except Exception as e:
            logger.error(f"Error updating behavior {behavior_id}: {e}")
            return False

    def delete_behavior(self, behavior_id: str) -> bool:
        """Delete a behavior."""
        try:
            with self._lock:
                if behavior_id not in self.behaviors:
                    logger.error(f"Behavior {behavior_id} not found")
                    return False

                behavior = self.behaviors[behavior_id]

                # Remove from indexes import indexes
                if behavior.behavior_type in self.behaviors_by_type:
                    self.behaviors_by_type[behavior.behavior_type].discard(behavior_id)

                if behavior.status in self.behaviors_by_status:
                    self.behaviors_by_status[behavior.status].discard(behavior_id)

                for tag in behavior.metadata.tags:
                    if tag in self.behaviors_by_tag:
                        self.behaviors_by_tag[tag].discard(behavior_id)

                # Remove behavior
                del self.behaviors[behavior_id]

                logger.info(f"Deleted behavior: {behavior_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting behavior {behavior_id}: {e}")
            return False

    def get_performance_analytics(self, behavior_id: str = None) -> Dict[str, Any]:
        """Get performance analytics for behaviors."""
        try:
            with self._lock:
                if behavior_id:
                    behavior = self.behaviors.get(behavior_id)
                    if not behavior:
                        return {}

                    return {
                        "behavior_id": behavior_id,
                        "performance_history": behavior.performance_history,
                        "validation_score": behavior.validation.validation_score if behavior.validation else 0.0,
                        "conflicts": len(behavior.conflicts),
                        "versions": len(behavior.versions)
                    }
                else:
                    # Aggregate analytics for all behaviors
                    total_behaviors = len(self.behaviors)
                    active_behaviors = len(self.behaviors_by_status.get(BehaviorStatus.ACTIVE, set()))
                    avg_validation_score = sum(
                        b.validation.validation_score if b.validation else 0.0
                        for b in self.behaviors.values()
                    ) / total_behaviors if total_behaviors > 0 else 0.0

                    return {
                        "total_behaviors": total_behaviors,
                        "active_behaviors": active_behaviors,
                        "average_validation_score": avg_validation_score,
                        "behaviors_by_type": {
                            bt.value: len(behaviors)
                            for bt, behaviors in self.behaviors_by_type.items()
                        },
                        "behaviors_by_status": {
                            bs.value: len(behaviors)
                            for bs, behaviors in self.behaviors_by_status.items()
                        }
                    }

        except Exception as e:
            logger.error(f"Error getting performance analytics: {e}")
            return {}

# Global instance
behavior_management_system = BehaviorManagementSystem()

# Register with the event-driven engine
def _register_behavior_management_system():
    def handler(event: Event):
        if event.type == EventType.SYSTEM and event.data.get('behavior_management'):
            # Behavior management events are handled internally
            return None
        return None

    # Import here to avoid circular imports
    from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine
    event_driven_behavior_engine.register_handler(
        event_type=EventType.SYSTEM,
        handler_id='behavior_management_system',
        handler=handler,
        priority=2
    )

_register_behavior_management_system() ))))))))))
