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

from services.models.mcp_models import (
    MCPFile, MCPRule, RuleCondition, RuleAction, BuildingModel, BuildingObject,
    ValidationResult, ValidationViolation, MCPValidationReport, ComplianceReport,
    RuleSeverity, RuleCategory, ConditionType, ActionType,
    serialize_mcp_file, deserialize_mcp_file
)
from services.ai.arx_mcp.validate.formula_evaluator import FormulaEvaluator, FormulaEvaluationError
from services.ai.arx_mcp.validate.spatial_analyzer import SpatialAnalyzer, SpatialAnalysisError, SpatialRelation
from services.ai.arx_mcp.validate.performance_optimizer import PerformanceOptimizer, OptimizationLevel, PerformanceOptimizationError
from services.ai.arx_mcp.validate.advanced_conditions import AdvancedConditionEvaluator, AdvancedConditionError
import html


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
        """Initialize the condition evaluator with supported operators"""
        self.operators = {
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<': lambda x, y: x < y,
            '<=': lambda x, y: x <= y,
            'in': lambda x, y: x in y if isinstance(y, (list, tuple)) else False,
            'not_in': lambda x, y: x not in y if isinstance(y, (list, tuple)) else False,
            'contains': lambda x, y: y in x if isinstance(x, (list, tuple, str)) else False,
            'starts_with': lambda x, y: str(x).startswith(str(y)),
            'ends_with': lambda x, y: str(x).endswith(str(y)),
            'regex': lambda x, y: bool(re.match(y, str(x))) if y else False
        }
        self.spatial_analyzer = SpatialAnalyzer()
        self.advanced_condition_evaluator = AdvancedConditionEvaluator()

    def evaluate_condition(self, condition: RuleCondition,
                          objects: List[BuildingObject],
                          context: Optional[RuleExecutionContext] = None) -> List[BuildingObject]:
        """Evaluate a condition against building objects with advanced condition support"""
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
        elif condition.type == ConditionType.TEMPORAL:
            return self.advanced_condition_evaluator.evaluate_temporal_condition(condition, objects)
        elif condition.type == ConditionType.DYNAMIC:
            return self.advanced_condition_evaluator.evaluate_dynamic_condition(condition, objects, context)
        elif condition.type == ConditionType.STATISTICAL:
            return self.advanced_condition_evaluator.evaluate_statistical_condition(condition, objects)
        elif condition.type == ConditionType.PATTERN:
            return self.advanced_condition_evaluator.evaluate_pattern_condition(condition, objects)
        elif condition.type == ConditionType.RANGE:
            return self.advanced_condition_evaluator.evaluate_range_condition(condition, objects)
        elif condition.type == ConditionType.LOGICAL:
            return self.advanced_condition_evaluator.evaluate_complex_logical_condition(condition, objects, context)
        else:
            logger.warning(f"Unknown condition type: {condition.type}")
            return []

    def _evaluate_property_condition(self, condition: RuleCondition,
                                   objects: List[BuildingObject]) -> List[BuildingObject]:
        """Evaluate property-based condition"""
        if not condition.element_type or not condition.property or not condition.operator:
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

    def _evaluate_spatial_condition(self, condition: RuleCondition,
                                  objects: List[BuildingObject]) -> List[BuildingObject]:
        """Evaluate spatial-based condition using advanced spatial analysis"""
        if not condition.element_type or not condition.property or not condition.operator:
            return []

        # Build spatial index for performance
        self.spatial_analyzer.build_spatial_index(objects)

        matched_objects = []
        operator_func = self.operators.get(condition.operator)

        if not operator_func:
            logger.warning(f"Unknown operator: {condition.operator}")
            return []

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Get spatial property value using advanced spatial analysis
            if condition.property == 'area':
                area = self.spatial_analyzer.calculate_area(obj)
                if operator_func(area, condition.value):
                    matched_objects.append(obj)
            elif condition.property == 'volume':
                volume = self.spatial_analyzer.calculate_volume(obj)
                if operator_func(volume, condition.value):
                    matched_objects.append(obj)
            elif condition.property == 'distance':
                # For distance conditions, check against target objects
                target_objects = [o for o in objects if o.object_type == condition.target_type]
                for target_obj in target_objects:
                    distance = self.spatial_analyzer.calculate_3d_distance(obj, target_obj)
                    if operator_func(distance, condition.value):
                        matched_objects.append(obj)
                        break
            elif condition.property == 'height':
                height = self._get_object_height(obj)
                if height is not None and operator_func(height, condition.value):
                    matched_objects.append(obj)
            elif condition.property == 'intersects':
                # Check if object intersects with any target objects
                target_objects = [o for o in objects if o.object_type == condition.target_type]
                for target_obj in target_objects:
                    if self.spatial_analyzer._objects_intersect(
                        self.spatial_analyzer.spatial_objects.get(obj.object_id),
                        self.spatial_analyzer.spatial_objects.get(target_obj.object_id)
                    ):
                        matched_objects.append(obj)
                        break
            elif condition.property == 'nearby':
                # Check if object is near any target objects
                target_objects = [o for o in objects if o.object_type == condition.target_type]
                nearby_objects = self.spatial_analyzer.find_nearby_objects(obj, target_objects, condition.value)
                if nearby_objects:
                    matched_objects.append(obj)

        return matched_objects

    def _evaluate_relationship_condition(self, condition: RuleCondition,
                                      objects: List[BuildingObject]) -> List[BuildingObject]:
        """Evaluate relationship-based condition using spatial analysis"""
        if not condition.element_type or not condition.relationship or not condition.target_type:
            return []

        # Build spatial index for performance
        self.spatial_analyzer.build_spatial_index(objects)

        matched_objects = []
        target_objects = [o for o in objects if o.object_type == condition.target_type]

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Check spatial relationships
            has_relationship = False

            for target_obj in target_objects:
                relationships = self.spatial_analyzer.calculate_spatial_relationships(obj, target_obj)

                if condition.relationship == 'intersects':
                    if SpatialRelation.INTERSECTS in relationships:
                        has_relationship = True
                        break
                elif condition.relationship == 'contains':
                    if SpatialRelation.CONTAINS in relationships:
                        has_relationship = True
                        break
                elif condition.relationship == 'adjacent':
                    if SpatialRelation.ADJACENT in relationships:
                        has_relationship = True
                        break
                elif condition.relationship == 'near':
                    if SpatialRelation.NEAR in relationships:
                        has_relationship = True
                        break
                elif condition.relationship == 'above':
                    if SpatialRelation.ABOVE in relationships:
                        has_relationship = True
                        break
                elif condition.relationship == 'below':
                    if SpatialRelation.BELOW in relationships:
                        has_relationship = True
                        break
                elif condition.relationship == 'connected':
                    # Check for explicit connections
                    connected_objects = self._get_connected_objects(obj, objects, condition.target_type)
                    if connected_objects:
                        has_relationship = True
                        break

            if has_relationship:
                matched_objects.append(obj)

        return matched_objects

    def _evaluate_system_condition(self, condition: RuleCondition,
                                 objects: List[BuildingObject]) -> List[BuildingObject]:
        """Evaluate system-based condition"""
        if not condition.element_type:
            return []

        matched_objects = []

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Check system properties
            system_type = obj.properties.get('system_type')
            if system_type and system_type == condition.value:
                matched_objects.append(obj)

        return matched_objects

    def _evaluate_composite_condition(self, condition: RuleCondition,
                                   objects: List[BuildingObject]) -> List[BuildingObject]:
        """Evaluate composite condition with multiple sub-conditions"""
        if not condition.conditions:
            return []

        if condition.composite_operator == 'AND':
            # All conditions must be true
            matched_objects = objects
            for sub_condition in condition.conditions:
                matched_objects = self.evaluate_condition(sub_condition, matched_objects)
                if not matched_objects:
                    break
            return matched_objects

        elif condition.composite_operator == 'OR':
            # Any condition can be true
            all_matched = set()
            for sub_condition in condition.conditions:
                matched = self.evaluate_condition(sub_condition, objects)
                all_matched.update(matched)
            return list(all_matched)

        else:
            logger.warning(f"Unknown composite operator: {condition.composite_operator}")
            return []

    def _calculate_object_area(self, obj: BuildingObject) -> Optional[float]:
        """Calculate object area"""
        if obj.location and 'width' in obj.location and 'height' in obj.location:
            return obj.location['width'] * obj.location['height']
        elif 'area' in obj.properties:
            return obj.properties['area']
        return None

    def _calculate_object_distance(self, obj: BuildingObject, target_value: Any) -> Optional[float]:
        """Calculate object distance to target"""
        if not obj.location or not isinstance(target_value, dict):
            return None

        obj_x = obj.location.get('x', 0)
        obj_y = obj.location.get('y', 0)
        target_x = target_value.get('x', 0)
        target_y = target_value.get('y', 0)

        return math.sqrt((obj_x - target_x) ** 2 + (obj_y - target_y) ** 2)

    def _get_object_height(self, obj: BuildingObject) -> Optional[float]:
        """Get object height"""
        if obj.location and 'height' in obj.location:
            return obj.location['height']
        elif 'height' in obj.properties:
            return obj.properties['height']
        return None

    def _get_connected_objects(self, obj: BuildingObject, all_objects: List[BuildingObject],
                              target_type: str) -> List[BuildingObject]:
        """Get objects connected to the given object"""
        connected_objects = []

        for connection_id in obj.connections:
            for other_obj in all_objects:
                if other_obj.object_id == connection_id and other_obj.object_type == target_type:
                    connected_objects.append(other_obj)

        return connected_objects


class ActionExecutor:
    """Executes rule actions and generates violations/warnings"""

    def __init__(self):
        self.calculators = {
            'electrical_load': self._calculate_electrical_load,
            'plumbing_flow': self._calculate_plumbing_flow,
            'hvac_capacity': self._calculate_hvac_capacity,
            'structural_load': self._calculate_structural_load,
            'fire_egress': self._calculate_fire_egress
        }
        self.formula_evaluator = FormulaEvaluator()
        self.spatial_analyzer = SpatialAnalyzer()

    def execute_actions(self, context: RuleExecutionContext) -> Tuple[List[ValidationViolation], Dict[str, Any]]:
        """Execute rule actions and return violations and calculations"""
        violations = []
        calculations = {}

        for action in context.rule.actions:
            if action.type == ActionType.VALIDATION:
                violation = self._execute_validation_action(action, context)
                if violation:
                    violations.append(violation)

            elif action.type == ActionType.CALCULATION:
                calc_result = self._execute_calculation_action(action, context)
                if calc_result:
                    calculations.update(calc_result)

            elif action.type == ActionType.WARNING:
                warning = self._execute_warning_action(action, context)
                if warning:
                    violations.append(warning)

            elif action.type == ActionType.ERROR:
                error = self._execute_error_action(action, context)
                if error:
                    violations.append(error)

        return violations, calculations

    def _execute_validation_action(self, action: RuleAction,
                                 context: RuleExecutionContext) -> Optional[ValidationViolation]:
        """Execute validation action"""
        if not action.message or not action.severity:
            return None

        # Check if validation should trigger based on matched objects
        if not context.matched_objects:
            return None

        # Create violation for each matched object
        violations = []
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
                location=obj.location
            )
            violations.append(violation)

        return violations[0] if violations else None

    def _execute_calculation_action(self, action: RuleAction,
                                  context: RuleExecutionContext) -> Optional[Dict[str, Any]]:
        """Execute calculation action"""
        if not action.formula:
            return None

        try:
            # Parse formula and calculate
            result = self._evaluate_formula(action.formula, context)

            return {
                'formula': action.formula,
                'result': result,
                'unit': action.unit,
                'description': action.description
            }

        except Exception as e:
            logger.error(f"Error executing calculation action: {e}")
            return None

    def _execute_warning_action(self, action: RuleAction,
                              context: RuleExecutionContext) -> Optional[ValidationViolation]:
        """Execute warning action"""
        return self._execute_validation_action(action, context)

    def _execute_error_action(self, action: RuleAction,
                            context: RuleExecutionContext) -> Optional[ValidationViolation]:
        """Execute error action"""
        return self._execute_validation_action(action, context)

    def _evaluate_formula(self, formula: str, context: RuleExecutionContext) -> float:
        """Evaluate calculation formula using the FormulaEvaluator"""
        try:
            return self.formula_evaluator.evaluate_formula(formula, context)
        except FormulaEvaluationError as e:
            logger.error(f"Formula evaluation error: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Unexpected error evaluating formula '{formula}': {e}")
            return 0.0

    def _get_total_area(self, objects: List[BuildingObject]) -> float:
        """Calculate total area of objects using spatial analysis"""
        return self.spatial_analyzer.get_total_area(objects)

    def _calculate_object_area(self, obj: BuildingObject) -> Optional[float]:
        """Calculate object area using spatial analysis"""
        area = self.spatial_analyzer.calculate_area(obj)
        return area if area > 0 else None

    def _calculate_electrical_load(self, objects: List[BuildingObject]) -> float:
        """Calculate electrical load"""
        total_load = 0.0
        for obj in objects:
            if obj.object_type == 'electrical_outlet':
                load = obj.properties.get('load', 0)
                total_load += load
        return total_load

    def _calculate_plumbing_flow(self, objects: List[BuildingObject]) -> float:
        """Calculate plumbing flow"""
        total_flow = 0.0
        for obj in objects:
            if obj.object_type in ['sink', 'toilet', 'shower']:
                flow = obj.properties.get('flow_rate', 0)
                total_flow += flow
        return total_flow

    def _calculate_hvac_capacity(self, objects: List[BuildingObject]) -> float:
        """Calculate HVAC capacity"""
        total_capacity = 0.0
        for obj in objects:
            if obj.object_type == 'hvac_unit':
                capacity = obj.properties.get('capacity', 0)
                total_capacity += capacity
        return total_capacity

    def _calculate_structural_load(self, objects: List[BuildingObject]) -> float:
        """Calculate structural load"""
        total_load = 0.0
        for obj in objects:
            if obj.object_type in ['wall', 'column', 'beam']:
                load = obj.properties.get('load', 0)
                total_load += load
        return total_load

    def _calculate_fire_egress(self, objects: List[BuildingObject]) -> float:
        """Calculate fire egress requirements"""
        total_occupancy = 0.0
        for obj in objects:
            if obj.object_type == 'room':
                occupancy = obj.properties.get('occupancy', 0)
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

        # Cache for loaded MCP files
        self.mcp_cache: Dict[str, MCPFile] = {}

        # Performance metrics
        self.total_validations = 0
        self.total_execution_time = 0.0
        self.average_execution_time = 0.0

        # Initialize performance optimizer
        optimization_config = {
            'cache_size': self.config.get('optimization_cache_size', 1000),
            'cache_strategy': self.config.get('optimization_cache_strategy', 'adaptive'),
            'max_workers': self.config.get('optimization_max_workers', 8),
            'use_processes': self.config.get('optimization_use_processes', False),
            'memory_threshold': self.config.get('optimization_memory_threshold', 0.8),
            'optimization_level': self.config.get('optimization_level', 'advanced'),
            'enabled': self.config.get('optimization_enabled', True)
        }
        self.performance_optimizer = PerformanceOptimizer(optimization_config)

        self.logger.info("MCP Rule Engine initialized with performance optimization")

    def load_mcp_file(self, file_path: str) -> MCPFile:
        """
        Load MCP file from path import path
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
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate and create MCP file
            mcp_file = self._create_mcp_file_from_dict(data)

            # Cache the file
            self.mcp_cache[str(file_path)] = mcp_file

            self.logger.info(f"Loaded MCP file: {mcp_file.name} ({len(mcp_file.rules)} rules)")
            return mcp_file

        except Exception as e:
            self.logger.error(f"Error loading MCP file {file_path}: {e}")
            raise

    def validate_building_model(self, building_model: BuildingModel,
                              mcp_files: List[str]) -> ComplianceReport:
        """
        Validate building model against multiple MCP files

        Args:
            building_model: Building model to validate
            mcp_files: List of MCP file paths

        Returns:
            Comprehensive compliance report
        """
        try:
            self.logger.info(f"Starting validation of building: {building_model.building_name}")
            start_time = time.time()

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
                    self.logger.error(f"Error validating with MCP file {mcp_file_path}: {e}")
                    continue

            # Calculate overall compliance score
            total_rules = sum(r.total_rules for r in validation_reports)
            passed_rules = sum(r.passed_rules for r in validation_reports)
            overall_score = (passed_rules / total_rules * 100) if total_rules > 0 else 0.0

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
                recommendations=recommendations
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

    def _validate_with_mcp(self, building_model: BuildingModel,
                          mcp_file: MCPFile) -> MCPValidationReport:
        """Validate building model with a single MCP file using performance optimization"""
        self.logger.info(f"Validating with MCP: {mcp_file.name}")

        # Use performance optimizer for rule execution
def execute_rule_wrapper(rule: MCPRule) -> ValidationResult:
            if not rule.enabled:
                return ValidationResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    category=rule.category,
                    passed=True,
                    violations=[],
                    calculations={},
                    execution_time=0.0
                )

            try:
                return self._execute_rule(rule, building_model)
            except Exception as e:
                self.logger.error(f"Error executing rule {rule.rule_id}: {e}")
                return ValidationResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    category=rule.category,
                    passed=False,
                    violations=[],
                    calculations={},
                    execution_time=0.0
                )

        # Execute rules with performance optimization
        enabled_rules = [rule for rule in mcp_file.rules if rule.enabled]
        results = self.performance_optimizer.optimize_rule_execution(
            rules=enabled_rules,
            building_objects=building_model.objects,
            execution_func=execute_rule_wrapper
        )

        # Calculate statistics
        passed_rules = 0
        failed_rules = 0
        total_violations = 0
        total_warnings = 0

        for result in results:
            if result:
                if result.passed:
                    passed_rules += 1
                else:
                    failed_rules += 1

                total_violations += len(result.violations)
                total_warnings += len(result.warnings)

        # Create validation report
        report = MCPValidationReport(
            mcp_id=mcp_file.mcp_id,
            mcp_name=mcp_file.name,
            jurisdiction=mcp_file.jurisdiction,
            validation_date=datetime.now(),
            total_rules=len(enabled_rules),
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            total_violations=total_violations,
            total_warnings=total_warnings,
            results=results
        )

        return report

    def _execute_rule(self, rule: MCPRule,
                     building_model: BuildingModel) -> ValidationResult:
        """Execute a single rule against building model"""
        start_time = time.time()

        # Find objects that match rule conditions
        matched_objects = building_model.objects

        # Create execution context
        context = RuleExecutionContext(
            building_model=building_model,
            rule=rule,
            matched_objects=matched_objects
        )

        for condition in rule.conditions:
            matched_objects = self.condition_evaluator.evaluate_condition(
                condition, matched_objects, context
            )
            # Update context with current matched objects
            context.matched_objects = matched_objects

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
            execution_time=time.time() - start_time
        )

        return result

    def _create_mcp_file_from_dict(self, data: Dict[str, Any]) -> MCPFile:
        """Create MCP file from dictionary data"""
        try:
            return deserialize_mcp_file(json.dumps(data)
        except Exception as e:
            self.logger.error(f"Error creating MCP file from dict: {e}")
            raise

    def _generate_recommendations(self, validation_reports: List[MCPValidationReport]) -> List[str]:
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
                recommendations.append(f"High number of {category} violations ({count}). Consider comprehensive review.")
            elif count > 0:
                recommendations.append(f"Address {count} {category} violations to improve compliance.")

        # Add general recommendations
        if not recommendations:
            recommendations.append("Building design appears to meet most code requirements.")

        return recommendations

    def _update_performance_metrics(self, execution_time: float):
        """Update performance metrics"""
        self.total_validations += 1
        self.total_execution_time += execution_time
        self.average_execution_time = self.total_execution_time / self.total_validations

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics including optimization stats"""
        base_metrics = {
            'total_validations': self.total_validations,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': self.average_execution_time,
            'cache_size': len(self.mcp_cache)
        }

        # Add optimization metrics
        optimization_stats = self.performance_optimizer.get_optimization_stats()

        return {
            **base_metrics,
            'optimization': optimization_stats
        }

    def clear_cache(self):
        """Clear all caches including optimization cache"""
        self.mcp_cache.clear()
        self.performance_optimizer.clear_cache()
        self.logger.info("All caches cleared")

    def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization"""
        return self.performance_optimizer.optimize_memory()

    def set_optimization_level(self, level: OptimizationLevel) -> None:
        """Set performance optimization level"""
        self.performance_optimizer.set_optimization_level(level)
        self.logger.info(f"Optimization level set to: {level.value}")

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get detailed optimization statistics"""
        return self.performance_optimizer.get_optimization_stats()

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
            errors.extend([f"Rule {index}, Condition {i}: {error}" for error in condition_errors])

        # Validate actions
        for i, action in enumerate(rule.actions):
            action_errors = self._validate_action(action, i)
            errors.extend([f"Rule {index}, Action {i}: {error}" for error in action_errors])

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
