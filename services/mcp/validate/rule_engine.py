"""
MCP Rule Validation Engine

This module provides the core rule validation engine for checking building designs
against MCP (Model Context Protocol) rules and generating compliance reports.

Key Features:
- MCP file loading and validation
- Rule execution against building models
- Comprehensive violation detection
- Performance optimization and caching
- Multi-jurisdiction support
- Detailed reporting and analytics
"""

import json
import logging
import time
import re
import math
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

# Import models - handle both module and script execution
try:
    # For running as a module
    from models.mcp_models import (
        MCPFile,
        MCPRule,
        RuleCondition,
        RuleAction,
        BuildingModel,
        BuildingObject,
        ValidationResult,
        ValidationViolation,
        MCPValidationReport,
        ComplianceReport,
        RuleSeverity,
        RuleCategory,
        ConditionType,
        ActionType,
        serialize_mcp_file,
        deserialize_mcp_file,
    )
    from .spatial_engine import SpatialEngine
except ImportError:
    # For running as a script - add project root to path
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    # Import using the actual directory structure (arx-mcp)
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "mcp_models", Path(__file__).parent.parent / "models" / "mcp_models.py"
    )
    mcp_models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mcp_models)

    # Import spatial engine
    spatial_spec = importlib.util.spec_from_file_location(
        "spatial_engine", Path(__file__).parent / "spatial_engine.py"
    )
    spatial_engine_module = importlib.util.module_from_spec(spatial_spec)
    spatial_spec.loader.exec_module(spatial_engine_module)

    # Import all required classes and functions
    MCPFile = mcp_models.MCPFile
    MCPRule = mcp_models.MCPRule
    RuleCondition = mcp_models.RuleCondition
    RuleAction = mcp_models.RuleAction
    BuildingModel = mcp_models.BuildingModel
    BuildingObject = mcp_models.BuildingObject
    ValidationResult = mcp_models.ValidationResult
    ValidationViolation = mcp_models.ValidationViolation
    MCPValidationReport = mcp_models.MCPValidationReport
    ComplianceReport = mcp_models.ComplianceReport
    RuleSeverity = mcp_models.RuleSeverity
    RuleCategory = mcp_models.RuleCategory
    ConditionType = mcp_models.ConditionType
    ActionType = mcp_models.ActionType
    serialize_mcp_file = mcp_models.serialize_mcp_file
    deserialize_mcp_file = mcp_models.deserialize_mcp_file
    SpatialEngine = spatial_engine_module.SpatialEngine


logger = logging.getLogger(__name__)


@dataclass
class RuleExecutionContext:
    """Context for rule execution"""

    building_model: BuildingModel
    rule: MCPRule
    matched_objects: List[BuildingObject] = field(default_factory=list)
    calculations: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConditionEvaluator:
    """Evaluates rule conditions against building objects"""

    def __init__(self):
        self.operators = {
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            ">": lambda x, y: x > y,
            ">=": lambda x, y: x >= y,
            "<": lambda x, y: x < y,
            "<=": lambda x, y: x <= y,
            "in": lambda x, y: x in y if isinstance(y, (list, tuple)) else False,
            "not_in": lambda x, y: (
                x not in y if isinstance(y, (list, tuple)) else False
            ),
            "contains": lambda x, y: (
                y in x if isinstance(x, (list, tuple, str)) else False
            ),
            "starts_with": lambda x, y: str(x).startswith(str(y)),
            "ends_with": lambda x, y: str(x).endswith(str(y)),
            "regex": lambda x, y: bool(re.match(y, str(x))) if y else False,
        }
        self.spatial_engine = SpatialEngine()

    def evaluate_condition(
        self, condition: RuleCondition, objects: List[BuildingObject]
    ) -> List[BuildingObject]:
        """Evaluate a condition against building objects"""
        # Handle None condition gracefully
        if condition is None:
            return []

        if condition.type == ConditionType.PROPERTY:
            return self._evaluate_property_condition(condition, objects)
        elif condition.type == ConditionType.SPATIAL:
            return self._evaluate_spatial_condition(condition, objects)
        elif condition.type == ConditionType.RELATIONSHIP:
            return self._evaluate_relationship_condition(condition, objects)
        elif condition.type == ConditionType.SYSTEM:
            return self._evaluate_system_condition(condition, objects)
        elif condition.type == ConditionType.COMPOSITE:
            return self._evaluate_composite_condition(condition, objects)
        else:
            logger.warning(f"Unknown condition type: {condition.type}")
            return []

    def _evaluate_property_condition(
        self, condition: RuleCondition, objects: List[BuildingObject]
    ) -> List[BuildingObject]:
        """Evaluate property-based condition"""
        if (
            not condition.element_type
            or not condition.property
            or not condition.operator
        ):
            return []

        matched_objects = []
        operator_func = self.operators.get(condition.operator)

        if not operator_func:
            logger.warning(f"Unknown operator: {condition.operator}")
            return []

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Get property value
            property_value = obj.properties.get(condition.property)
            if property_value is None:
                continue

            # Evaluate condition
            try:
                if operator_func(property_value, condition.value):
                    matched_objects.append(obj)
            except (TypeError, ValueError) as e:
                logger.warning(f"Error evaluating property condition: {e}")
                continue

        return matched_objects

    def _evaluate_spatial_condition(
        self, condition: RuleCondition, objects: List[BuildingObject]
    ) -> List[BuildingObject]:
        """Evaluate spatial-based condition"""
        if not condition.element_type or not condition.property:
            return []

        matched_objects = []

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Enhanced spatial property evaluation
            if condition.property == "area":
                area = self.spatial_engine.calculate_room_area(obj)
                if self._evaluate_property_value(
                    area, condition.operator, condition.value
                ):
                    matched_objects.append(obj)

            elif condition.property == "volume":
                volume = self.spatial_engine.calculate_room_volume(obj)
                if self._evaluate_property_value(
                    volume, condition.operator, condition.value
                ):
                    matched_objects.append(obj)

            elif condition.property == "distance":
                # Distance to target object or point
                if isinstance(condition.value, dict) and "target_id" in condition.value:
                    target_obj = self._find_object_by_id(
                        objects, condition.value["target_id"]
                    )
                    if target_obj:
                        distance = self.spatial_engine.calculate_distance(
                            obj, target_obj
                        )
                        if self._evaluate_property_value(
                            distance,
                            condition.operator,
                            condition.value.get("max_distance", 0),
                        ):
                            matched_objects.append(obj)

            elif condition.property == "height":
                height = self._get_object_height(obj)
                if self._evaluate_property_value(
                    height, condition.operator, condition.value
                ):
                    matched_objects.append(obj)

            elif condition.property == "floor_level":
                floor_level = self.spatial_engine.get_floor_level(obj)
                if self._evaluate_property_value(
                    floor_level, condition.operator, condition.value
                ):
                    matched_objects.append(obj)

            elif condition.property == "adjacent_to":
                # Check if object is adjacent to specified type
                target_type = condition.value.get("target_type")
                max_distance = condition.value.get("max_distance", 2.0)
                if target_type:
                    target_objects = [
                        o for o in objects if o.object_type == target_type
                    ]
                    for target_obj in target_objects:
                        if self.spatial_engine.check_spatial_relationship(
                            obj, target_obj, "adjacent", max_distance=max_distance
                        ):
                            matched_objects.append(obj)
                            break

            elif condition.property == "within_distance":
                # Check if object is within distance of specified type
                target_type = condition.value.get("target_type")
                max_distance = condition.value.get("max_distance", 5.0)
                if target_type:
                    target_objects = [
                        o for o in objects if o.object_type == target_type
                    ]
                    for target_obj in target_objects:
                        if self.spatial_engine.check_spatial_relationship(
                            obj,
                            target_obj,
                            "within_distance",
                            max_distance=max_distance,
                        ):
                            matched_objects.append(obj)
                            break

        return matched_objects

    def _evaluate_property_value(
        self, value: Any, operator: str, target_value: Any
    ) -> bool:
        """Evaluate property value against target using operator"""
        operator_func = self.operators.get(operator)
        if not operator_func:
            logger.warning(f"Unknown operator: {operator}")
            return False

        try:
            return operator_func(value, target_value)
        except (TypeError, ValueError):
            return False

    def _find_object_by_id(
        self, objects: List[BuildingObject], object_id: str
    ) -> Optional[BuildingObject]:
        """Find object by ID"""
        for obj in objects:
            if obj.object_id == object_id:
                return obj
        return None

    def _evaluate_relationship_condition(
        self, condition: RuleCondition, objects: List[BuildingObject]
    ) -> List[BuildingObject]:
        """Evaluate relationship-based condition"""
        if (
            not condition.element_type
            or not condition.relationship
            or not condition.target_type
        ):
            return []

        matched_objects = []

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Check if object has connections to target type
            connected_objects = self._get_connected_objects(
                obj, objects, condition.target_type
            )
            if connected_objects:
                matched_objects.append(obj)

        return matched_objects

    def _evaluate_system_condition(
        self, condition: RuleCondition, objects: List[BuildingObject]
    ) -> List[BuildingObject]:
        """Evaluate system-based condition"""
        if not condition.element_type:
            return []

        matched_objects = []

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Check system properties
            system_type = obj.properties.get("system_type")
            if system_type and system_type == condition.value:
                matched_objects.append(obj)

        return matched_objects

    def _evaluate_composite_condition(
        self, condition: RuleCondition, objects: List[BuildingObject]
    ) -> List[BuildingObject]:
        """Evaluate composite condition with multiple sub-conditions"""
        if not condition.conditions:
            return []

        if condition.composite_operator == "AND":
            # All conditions must be true
            matched_objects = objects
            for sub_condition in condition.conditions:
                matched_objects = self.evaluate_condition(
                    sub_condition, matched_objects
                )
                if not matched_objects:
                    break
            return matched_objects

        elif condition.composite_operator == "OR":
            # Any condition can be true
            all_matched = []
            for sub_condition in condition.conditions:
                matched = self.evaluate_condition(sub_condition, objects)
                # Add objects that aren't already in the list
                for obj in matched:
                    if obj not in all_matched:
                        all_matched.append(obj)
            return all_matched

        else:
            logger.warning(
                f"Unknown composite operator: {condition.composite_operator}"
            )
            return []

    def _calculate_object_area(self, obj: BuildingObject) -> Optional[float]:
        """Calculate object area"""
        if obj.location and "width" in obj.location and "height" in obj.location:
            return obj.location["width"] * obj.location["height"]
        elif "area" in obj.properties:
            return obj.properties["area"]
        return None

    def _calculate_object_distance(
        self, obj: BuildingObject, target_value: Any
    ) -> Optional[float]:
        """Calculate object distance to target"""
        if not obj.location or not isinstance(target_value, dict):
            return None

        obj_x = obj.location.get("x", 0)
        obj_y = obj.location.get("y", 0)
        target_x = target_value.get("x", 0)
        target_y = target_value.get("y", 0)

        return math.sqrt((obj_x - target_x) ** 2 + (obj_y - target_y) ** 2)

    def _get_object_height(self, obj: BuildingObject) -> Optional[float]:
        """Get object height"""
        # Check properties first (more common)
        if "height" in obj.properties:
            return obj.properties["height"]
        elif obj.location and "height" in obj.location:
            return obj.location["height"]
        return None

    def _get_connected_objects(
        self, obj: BuildingObject, all_objects: List[BuildingObject], target_type: str
    ) -> List[BuildingObject]:
        """Get objects connected to the given object"""
        connected_objects = []

        for connection_id in obj.connections:
            for other_obj in all_objects:
                if (
                    other_obj.object_id == connection_id
                    and other_obj.object_type == target_type
                ):
                    connected_objects.append(other_obj)

        return connected_objects


class ActionExecutor:
    """Executes rule actions and generates violations/warnings"""

    def __init__(self):
        self.calculators = {
            "electrical_load": self._calculate_electrical_load,
            "plumbing_flow": self._calculate_plumbing_flow,
            "hvac_capacity": self._calculate_hvac_capacity,
            "structural_load": self._calculate_structural_load,
            "fire_egress": self._calculate_fire_egress,
        }

    def execute_actions(
        self, context: RuleExecutionContext
    ) -> Tuple[List[ValidationViolation], Dict[str, Any]]:
        """Execute rule actions and return violations and calculations"""
        violations = []
        calculations = {}

        for action in context.rule.actions:
            # Handle None actions gracefully
            if action is None:
                continue

            if action.type == ActionType.VALIDATION:
                validation_violations = self._execute_validation_action(action, context)
                violations.extend(validation_violations)

            elif action.type == ActionType.CALCULATION:
                calc_result = self._execute_calculation_action(action, context)
                if calc_result:
                    calculations.update(calc_result)

            elif action.type == ActionType.WARNING:
                warning_violations = self._execute_warning_action(action, context)
                violations.extend(warning_violations)

            elif action.type == ActionType.ERROR:
                error_violations = self._execute_error_action(action, context)
                violations.extend(error_violations)

        return violations, calculations

    def _execute_validation_action(
        self, action: RuleAction, context: RuleExecutionContext
    ) -> List[ValidationViolation]:
        """Execute validation action"""
        violations = []

        if not action.message or not action.severity:
            return violations

        # Check if validation should trigger based on matched objects
        if not context.matched_objects:
            return violations

        # Create violation for each matched object
        for obj in context.matched_objects:
            violation = ValidationViolation(
                rule_id=context.rule.rule_id,
                rule_name=context.rule.name,
                category=context.rule.category,
                severity=action.severity,
                message=action.message,
                code_reference=action.code_reference,
                element_id=obj.object_id,
                element_type=obj.object_type,
                location=obj.location,
            )
            violations.append(violation)

        return violations

    def _execute_calculation_action(
        self, action: RuleAction, context: RuleExecutionContext
    ) -> Optional[Dict[str, Any]]:
        """Execute calculation action"""
        if not action.formula:
            return None

        try:
            # Parse formula and calculate
            result = self._evaluate_formula(action.formula, context)

            return {
                action.formula: {
                    "formula": action.formula,
                    "result": result,
                    "unit": action.unit,
                    "description": action.description,
                }
            }

        except Exception as e:
            logger.error(f"Error executing calculation action '{action.formula}': {e}")
            # Return a default result instead of None to avoid breaking the validation
            return {
                action.formula: {
                    "formula": action.formula,
                    "result": 0.0,
                    "unit": action.unit,
                    "description": f"{action.description} (calculation failed: {str(e)})",
                }
            }

    def _execute_warning_action(
        self, action: RuleAction, context: RuleExecutionContext
    ) -> List[ValidationViolation]:
        """Execute warning action"""
        return self._execute_validation_action(action, context)

    def _execute_error_action(
        self, action: RuleAction, context: RuleExecutionContext
    ) -> List[ValidationViolation]:
        """Execute error action"""
        return self._execute_validation_action(action, context)

    def _evaluate_formula(self, formula: str, context: RuleExecutionContext) -> float:
        """Evaluate calculation formula"""

        # Handle special calculation functions
        if formula == "electrical_load":
            return self._calculate_electrical_load(context.matched_objects)
        elif formula == "plumbing_flow":
            return self._calculate_plumbing_flow(context.matched_objects)
        elif formula == "hvac_capacity":
            return self._calculate_hvac_capacity(context.matched_objects)
        elif formula == "structural_load":
            return self._calculate_structural_load(context.matched_objects)
        elif formula == "fire_egress":
            return self._calculate_fire_egress(context.matched_objects)
        elif formula == "area":
            return self._get_total_area(context.matched_objects)
        elif formula == "count":
            return len(context.matched_objects)

        # Extract all variables from matched objects
        variables = self._extract_variables_from_objects(context.matched_objects)

        # If no matched objects, try to extract from all building objects
        if not variables and not context.matched_objects:
            variables = self._extract_variables_from_objects(
                context.building_model.objects
            )

        # Add context calculations
        variables.update(context.calculations)

        # Add common calculated values
        variables["area"] = self._get_total_area(context.matched_objects)
        variables["count"] = len(context.matched_objects)

        # Create a safe evaluation environment with default values
        safe_dict = {}
        for k, v in variables.items():
            if isinstance(v, (int, float)):
                safe_dict[k] = float(v)
            else:
                safe_dict[k] = v

        # Add default values for common variables that might be missing
        default_vars = {
            "fixture_units": 0.0,
            "airflow": 0.0,
            "capacity": 0.0,
            "load": 0.0,
            "flow": 0.0,
            "structural_load": 0.0,
            "occupancy": 0.0,
            "efficiency": 0.0,
            "weight": 0.0,
        }

        # Only add defaults for variables not already present
        for var, default_val in default_vars.items():
            if var not in safe_dict:
                safe_dict[var] = default_val

        # Add math functions for complex calculations
        safe_dict.update(
            {"abs": abs, "round": round, "min": min, "max": max, "sum": sum, "len": len}
        )

        try:
            # Use eval with restricted namespace
            result = eval(formula, {"__builtins__": {}}, safe_dict)
            return float(result) if result is not None else 0.0
        except Exception as e:
            logger.error(
                f"Error evaluating formula '{formula}' with variables {variables}: {e}"
            )
            # Return 0 as fallback instead of raising
            return 0.0

    def _extract_variables_from_objects(
        self, objects: List[BuildingObject]
    ) -> Dict[str, Any]:
        """Extract all relevant variables from building objects"""
        variables = {}

        # Extract capacity from HVAC equipment
        total_capacity = 0
        for obj in objects:
            if obj.object_type in ["hvac_equipment", "hvac_unit"]:
                capacity = obj.properties.get("capacity", 0)
                total_capacity += capacity
        if total_capacity > 0:
            variables["capacity"] = total_capacity

        # Extract load from electrical outlets
        total_load = 0
        for obj in objects:
            if obj.object_type == "electrical_outlet":
                load = obj.properties.get("load", 0)
                total_load += load
        if total_load > 0:
            variables["load"] = total_load

        # Extract flow from plumbing fixtures
        total_flow = 0
        for obj in objects:
            if obj.object_type in ["plumbing_fixture", "sink", "toilet", "shower"]:
                flow = obj.properties.get("flow_rate", 0)
                total_flow += flow
        if total_flow > 0:
            variables["flow"] = total_flow

        # Extract fixture units from plumbing fixtures
        total_fixture_units = 0
        for obj in objects:
            if obj.object_type in ["plumbing_fixture", "sink", "toilet", "shower"]:
                fixture_units = obj.properties.get("fixture_units", 0)
                total_fixture_units += fixture_units
        if total_fixture_units > 0:
            variables["fixture_units"] = total_fixture_units

        # Extract airflow from ducts
        total_airflow = 0
        for obj in objects:
            if obj.object_type == "duct":
                airflow = obj.properties.get("airflow", 0)
                total_airflow += airflow
        if total_airflow > 0:
            variables["airflow"] = total_airflow

        # Extract structural loads
        total_structural_load = 0
        for obj in objects:
            if obj.object_type in ["wall", "column", "beam", "foundation"]:
                load = obj.properties.get("load", 0)
                total_structural_load += load
        if total_structural_load > 0:
            variables["structural_load"] = total_structural_load

        # Extract occupancy for fire egress calculations
        total_occupancy = 0
        for obj in objects:
            if obj.object_type == "room":
                occupancy = obj.properties.get("occupancy", 0)
                total_occupancy += occupancy
        if total_occupancy > 0:
            variables["occupancy"] = total_occupancy

        # Extract efficiency ratings
        for obj in objects:
            if obj.object_type in ["hvac_equipment", "hvac_unit"]:
                efficiency = obj.properties.get("efficiency_rating", 0)
                if efficiency > 0:
                    variables["efficiency"] = efficiency
                    break

        # Extract weight for seismic calculations
        total_weight = 0
        for obj in objects:
            weight = obj.properties.get("weight", 0)
            total_weight += weight
        if total_weight > 0:
            variables["weight"] = total_weight

        return variables

    def _get_total_area(self, objects: List[BuildingObject]) -> float:
        """Calculate total area of objects"""
        total_area = 0.0
        for obj in objects:
            area = self._calculate_object_area(obj)
            if area:
                total_area += area
        return total_area

    def _calculate_object_area(self, obj: BuildingObject) -> Optional[float]:
        """Calculate object area"""
        if obj.location and "width" in obj.location and "height" in obj.location:
            return obj.location["width"] * obj.location["height"]
        elif "area" in obj.properties:
            return obj.properties["area"]
        return None

    def _calculate_electrical_load(self, objects: List[BuildingObject]) -> float:
        """Calculate electrical load"""
        total_load = 0.0
        for obj in objects:
            if obj.object_type == "electrical_outlet":
                load = obj.properties.get("load", 0)
                total_load += load
        return total_load

    def _calculate_plumbing_flow(self, objects: List[BuildingObject]) -> float:
        """Calculate plumbing flow"""
        total_flow = 0.0
        for obj in objects:
            if obj.object_type in ["sink", "toilet", "shower"]:
                flow = obj.properties.get("flow_rate", 0)
                total_flow += flow
        return total_flow

    def _calculate_hvac_capacity(self, objects: List[BuildingObject]) -> float:
        """Calculate HVAC capacity"""
        total_capacity = 0.0
        for obj in objects:
            if obj.object_type == "hvac_unit":
                capacity = obj.properties.get("capacity", 0)
                total_capacity += capacity
        return total_capacity

    def _calculate_structural_load(self, objects: List[BuildingObject]) -> float:
        """Calculate structural load"""
        total_load = 0.0
        for obj in objects:
            if obj.object_type in ["wall", "column", "beam"]:
                load = obj.properties.get("load", 0)
                total_load += load
        return total_load

    def _calculate_fire_egress(self, objects: List[BuildingObject]) -> float:
        """Calculate fire egress requirements"""
        total_occupancy = 0.0
        for obj in objects:
            if obj.object_type == "room":
                occupancy = obj.properties.get("occupancy", 0)
                total_occupancy += occupancy
        return total_occupancy * 0.3  # 0.3 inches per person


class MCPRuleEngine:
    """
    Main MCP Rule Validation Engine

    This engine provides comprehensive rule validation capabilities:
    - Load and validate MCP files
    - Execute rules against building models
    - Generate detailed validation reports
    - Support multiple jurisdictions
    - Performance optimization and caching
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the MCP Rule Engine

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.condition_evaluator = ConditionEvaluator()
        self.action_executor = ActionExecutor()

        # Initialize jurisdiction matcher
        try:
            from .jurisdiction_matcher import JurisdictionMatcher

            self.jurisdiction_matcher = JurisdictionMatcher()
            self.logger.info("Jurisdiction matcher initialized")
        except ImportError:
            self.logger.warning("Jurisdiction matcher not available")
            self.jurisdiction_matcher = None

        # Cache for loaded MCP files
        self.mcp_cache: Dict[str, MCPFile] = {}

        # Performance metrics
        self.total_validations = 0
        self.total_execution_time = 0.0
        self.average_execution_time = 0.0

        self.logger.info("MCP Rule Engine initialized")

    def load_mcp_file(self, file_path: str) -> MCPFile:
        """
        Load MCP file from path

        Args:
            file_path: Path to MCP file

        Returns:
            Loaded MCP file
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise FileNotFoundError(f"MCP file not found: {file_path}")

            # Check cache first
            if str(file_path) in self.mcp_cache:
                self.logger.info(f"Loading MCP file from cache: {file_path}")
                return self.mcp_cache[str(file_path)]

            # Load and parse file
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate and create MCP file
            mcp_file = self._create_mcp_file_from_dict(data)

            # Cache the file
            self.mcp_cache[str(file_path)] = mcp_file

            self.logger.info(
                f"Loaded MCP file: {mcp_file.name} ({len(mcp_file.rules)} rules)"
            )
            return mcp_file

        except Exception as e:
            self.logger.error(f"Error loading MCP file {file_path}: {e}")
            raise

    def validate_building_model(
        self, building_model: BuildingModel, mcp_files: List[str] = None
    ) -> ComplianceReport:
        """
        Validate building model against multiple MCP files

        Args:
            building_model: Building model to validate
            mcp_files: List of MCP file paths (optional - will auto-detect if not provided)

        Returns:
            Comprehensive compliance report
        """
        try:
            self.logger.info(
                f"Starting validation of building: {building_model.building_name}"
            )
            start_time = time.time()

            # Auto-detect applicable codes if not provided
            if mcp_files is None and self.jurisdiction_matcher:
                building_dict = {
                    "building_id": building_model.building_id,
                    "building_name": building_model.building_name,
                    "metadata": building_model.metadata,
                }
                applicable_codes = self.jurisdiction_matcher.get_applicable_codes(
                    building_dict
                )
                mcp_files = [f"mcp/{code}.json" for code in applicable_codes]
                self.logger.info(f"Auto-detected applicable codes: {applicable_codes}")

            validation_reports = []
            total_violations = 0
            total_warnings = 0
            critical_violations = 0

            # Load and validate each MCP file
            for mcp_file_path in mcp_files:
                try:
                    mcp_file = self.load_mcp_file(mcp_file_path)
                    report = self._validate_with_mcp(building_model, mcp_file)
                    validation_reports.append(report)

                    total_violations += report.total_violations
                    total_warnings += report.total_warnings

                    # Count critical violations
                    for result in report.results:
                        for violation in result.violations:
                            if violation.severity == RuleSeverity.ERROR:
                                critical_violations += 1

                except Exception as e:
                    self.logger.error(
                        f"Error validating with MCP file {mcp_file_path}: {e}"
                    )
                    continue

            # Calculate overall compliance score
            total_rules = sum(r.total_rules for r in validation_reports)
            passed_rules = sum(r.passed_rules for r in validation_reports)
            overall_score = (
                (passed_rules / total_rules * 100) if total_rules > 0 else 0.0
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(validation_reports)

            # Create compliance report
            compliance_report = ComplianceReport(
                building_id=building_model.building_id,
                building_name=building_model.building_name,
                validation_reports=validation_reports,
                overall_compliance_score=overall_score,
                critical_violations=critical_violations,
                total_violations=total_violations,
                total_warnings=total_warnings,
                recommendations=recommendations,
            )

            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time)

            self.logger.info(f"Validation completed in {execution_time:.2f}s")
            self.logger.info(f"Overall compliance score: {overall_score:.1f}%")
            self.logger.info(f"Critical violations: {critical_violations}")

            return compliance_report

        except Exception as e:
            self.logger.error(f"Error during building validation: {e}")
            raise

    def _validate_with_mcp(
        self, building_model: BuildingModel, mcp_file: MCPFile
    ) -> MCPValidationReport:
        """Validate building model with a single MCP file"""
        self.logger.info(f"Validating with MCP: {mcp_file.name}")

        results = []
        passed_rules = 0
        failed_rules = 0
        total_violations = 0
        total_warnings = 0

        # Execute each rule
        for rule in mcp_file.rules:
            if not rule.enabled:
                continue

            try:
                result = self._execute_rule(rule, building_model)
                results.append(result)

                if result.passed:
                    passed_rules += 1
                else:
                    failed_rules += 1

                total_violations += len(result.violations)
                total_warnings += len(result.warnings)

            except Exception as e:
                self.logger.error(f"Error executing rule {rule.rule_id}: {e}")
                continue

        # Create validation report
        report = MCPValidationReport(
            mcp_id=mcp_file.mcp_id,
            mcp_name=mcp_file.name,
            jurisdiction=mcp_file.jurisdiction,
            validation_date=datetime.now(),
            total_rules=len([r for r in mcp_file.rules if r.enabled]),
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            total_violations=total_violations,
            total_warnings=total_warnings,
            results=results,
        )

        return report

    def _execute_rule(
        self, rule: MCPRule, building_model: BuildingModel
    ) -> ValidationResult:
        """Execute a single rule against building model"""
        start_time = time.time()

        # Find objects that match rule conditions
        matched_objects = building_model.objects

        for condition in rule.conditions:
            matched_objects = self.condition_evaluator.evaluate_condition(
                condition, matched_objects
            )

        # Create execution context
        context = RuleExecutionContext(
            building_model=building_model, rule=rule, matched_objects=matched_objects
        )

        # Execute actions
        violations, calculations = self.action_executor.execute_actions(context)

        # Determine if rule passed
        passed = len([v for v in violations if v.severity == RuleSeverity.ERROR]) == 0

        # Create validation result
        result = ValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            category=rule.category,
            passed=passed,
            violations=violations,
            calculations=calculations,
            execution_time=time.time() - start_time,
        )

        return result

    def _create_mcp_file_from_dict(self, data: Dict[str, Any]) -> MCPFile:
        """Create MCP file from dictionary data"""
        try:
            return deserialize_mcp_file(json.dumps(data))
        except Exception as e:
            self.logger.error(f"Error creating MCP file from dict: {e}")
            raise

    def _generate_recommendations(
        self, validation_reports: List[MCPValidationReport]
    ) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Analyze violations by category
        category_violations = {}
        for report in validation_reports:
            for result in report.results:
                for violation in result.violations:
                    category = violation.category.value
                    if category not in category_violations:
                        category_violations[category] = 0
                    category_violations[category] += 1

        # Generate recommendations
        for category, count in category_violations.items():
            if count > 5:
                recommendations.append(
                    f"High number of {category} violations ({count}). Consider comprehensive review."
                )
            elif count > 0:
                recommendations.append(
                    f"Address {count} {category} violations to improve compliance."
                )

        # Add general recommendations
        if not recommendations:
            recommendations.append(
                "Building design appears to meet most code requirements."
            )

        return recommendations

    def _update_performance_metrics(self, execution_time: float):
        """Update performance metrics"""
        self.total_validations += 1
        self.total_execution_time += execution_time
        self.average_execution_time = self.total_execution_time / self.total_validations

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "total_validations": self.total_validations,
            "total_execution_time": self.total_execution_time,
            "average_execution_time": self.average_execution_time,
            "cache_size": len(self.mcp_cache),
        }

    def get_jurisdiction_info(self, building_model: BuildingModel) -> Dict[str, Any]:
        """Get jurisdiction information for a building"""
        if not self.jurisdiction_matcher:
            return {"error": "Jurisdiction matcher not available"}

        building_dict = {
            "building_id": building_model.building_id,
            "building_name": building_model.building_name,
            "metadata": building_model.metadata,
        }

        return self.jurisdiction_matcher.get_jurisdiction_info(building_dict)

    def clear_cache(self):
        """Clear MCP file cache"""
        self.mcp_cache.clear()
        self.logger.info("MCP cache cleared")

    def validate_mcp_file(self, file_path: str) -> List[str]:
        """
        Validate MCP file structure and content

        Args:
            file_path: Path to MCP file

        Returns:
            List of validation errors
        """
        errors = []

        try:
            mcp_file = self.load_mcp_file(file_path)

            # Validate basic structure
            if not mcp_file.mcp_id:
                errors.append("Missing mcp_id")

            if not mcp_file.name:
                errors.append("Missing name")

            if not mcp_file.jurisdiction.country:
                errors.append("Missing jurisdiction country")

            # Validate rules
            for i, rule in enumerate(mcp_file.rules):
                rule_errors = self._validate_rule(rule, i)
                errors.extend(rule_errors)

        except Exception as e:
            errors.append(f"File loading error: {str(e)}")

        return errors

    def _validate_rule(self, rule: MCPRule, index: int) -> List[str]:
        """Validate individual rule"""
        errors = []

        if not rule.rule_id:
            errors.append(f"Rule {index}: Missing rule_id")

        if not rule.name:
            errors.append(f"Rule {index}: Missing name")

        if not rule.conditions:
            errors.append(f"Rule {index}: No conditions defined")

        if not rule.actions:
            errors.append(f"Rule {index}: No actions defined")

        # Validate conditions
        for i, condition in enumerate(rule.conditions):
            condition_errors = self._validate_condition(condition, i)
            errors.extend(
                [f"Rule {index}, Condition {i}: {error}" for error in condition_errors]
            )

        # Validate actions
        for i, action in enumerate(rule.actions):
            action_errors = self._validate_action(action, i)
            errors.extend(
                [f"Rule {index}, Action {i}: {error}" for error in action_errors]
            )

        return errors

    def _validate_condition(self, condition: RuleCondition, index: int) -> List[str]:
        """Validate rule condition"""
        errors = []

        if not condition.type:
            errors.append("Missing condition type")

        if condition.type == ConditionType.PROPERTY:
            if not condition.element_type:
                errors.append("Missing element_type for property condition")
            if not condition.property:
                errors.append("Missing property for property condition")
            if not condition.operator:
                errors.append("Missing operator for property condition")

        elif condition.type == ConditionType.SPATIAL:
            if not condition.element_type:
                errors.append("Missing element_type for spatial condition")
            if not condition.property:
                errors.append("Missing property for spatial condition")

        elif condition.type == ConditionType.RELATIONSHIP:
            if not condition.element_type:
                errors.append("Missing element_type for relationship condition")
            if not condition.relationship:
                errors.append("Missing relationship for relationship condition")
            if not condition.target_type:
                errors.append("Missing target_type for relationship condition")

        return errors

    def _validate_action(self, action: RuleAction, index: int) -> List[str]:
        """Validate rule action"""
        errors = []

        if not action.type:
            errors.append("Missing action type")

        if action.type == ActionType.VALIDATION:
            if not action.message:
                errors.append("Missing message for validation action")
            if not action.severity:
                errors.append("Missing severity for validation action")

        elif action.type == ActionType.CALCULATION:
            if not action.formula:
                errors.append("Missing formula for calculation action")

        return errors
