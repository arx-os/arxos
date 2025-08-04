"""
Dynamic Rules Engine for MCP Rule Validation

This module provides dynamic rule capabilities:
- Runtime rule modification
- Adaptive rule conditions
- Dynamic rule generation
- Rule versioning and rollback
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import copy
import threading

from models.mcp_models import (
    BuildingModel, BuildingObject, MCPFile, MCPRule, 
    RuleCondition, RuleAction, ValidationViolation
)
from validate.rule_engine import MCPRuleEngine, RuleExecutionContext


@dataclass
class RuleVersion:
    """Rule version for tracking changes"""
    version_id: str
    rule_id: str
    rule_data: Dict[str, Any]
    created_at: datetime
    created_by: str
    description: str
    is_active: bool = True


@dataclass
class DynamicRule:
    """Dynamic rule with runtime modification capabilities"""
    rule_id: str
    base_rule: MCPRule
    versions: List[RuleVersion] = field(default_factory=list)
    current_version: Optional[str] = None
    modification_history: List[Dict[str, Any]] = field(default_factory=list)
    adaptive_conditions: List[Dict[str, Any]] = field(default_factory=list)
    last_modified: datetime = field(default_factory=datetime.now)


class DynamicRuleEngine:
    """
    Dynamic rules engine for runtime rule modification
    
    Features:
    - Runtime rule modification
    - Adaptive rule conditions
    - Dynamic rule generation
    - Rule versioning and rollback
    - Thread-safe rule updates
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize dynamic rules engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Dynamic settings
        self.enable_runtime_modification = self.config.get('enable_runtime_modification', True)
        self.max_rule_versions = self.config.get('max_rule_versions', 10)
        self.auto_backup = self.config.get('auto_backup', True)
        
        # Initialize base engine
        self.base_engine = MCPRuleEngine(config)
        
        # Dynamic rules storage
        self.dynamic_rules: Dict[str, DynamicRule] = {}
        self.rule_lock = threading.RLock()
        
        # Modification callbacks
        self.modification_callbacks: List[callable] = []
        
        self.logger.info("Dynamic Rule Engine initialized")
    
    def create_dynamic_rule(self, rule: MCPRule, description: str = "") -> str:
        """
        Create a dynamic rule from a base rule
        
        Args:
            rule: Base rule to make dynamic
            description: Description of the dynamic rule
            
        Returns:
            Dynamic rule ID
        """
        with self.rule_lock:
            dynamic_rule = DynamicRule(
                rule_id=rule.rule_id,
                base_rule=rule,
                current_version="v1.0"
            )
            
            # Create initial version
            initial_version = RuleVersion(
                version_id="v1.0",
                rule_id=rule.rule_id,
                rule_data=self._rule_to_dict(rule),
                created_at=datetime.now(),
                created_by="system",
                description="Initial version"
            )
            
            dynamic_rule.versions.append(initial_version)
            self.dynamic_rules[rule.rule_id] = dynamic_rule
            
            self.logger.info(f"Created dynamic rule {rule.rule_id}")
            return rule.rule_id
    
    def modify_rule(self, rule_id: str, modifications: Dict[str, Any], 
                   user: str = "system", description: str = "") -> bool:
        """
        Modify a dynamic rule at runtime
        
        Args:
            rule_id: Rule ID to modify
            modifications: Dictionary of modifications
            user: User making the modification
            description: Description of the modification
            
        Returns:
            True if modification was successful
        """
        if not self.enable_runtime_modification:
            self.logger.warning("Runtime modification is disabled")
            return False
        
        with self.rule_lock:
            if rule_id not in self.dynamic_rules:
                self.logger.error(f"Dynamic rule {rule_id} not found")
                return False
            
            dynamic_rule = self.dynamic_rules[rule_id]
            
            # Create backup if enabled
            if self.auto_backup:
                self._create_backup(dynamic_rule)
            
            # Apply modifications
            try:
                modified_rule = self._apply_modifications(dynamic_rule.base_rule, modifications)
                
                # Create new version
                version_id = f"v{len(dynamic_rule.versions) + 1}.0"
                new_version = RuleVersion(
                    version_id=version_id,
                    rule_id=rule_id,
                    rule_data=self._rule_to_dict(modified_rule),
                    created_at=datetime.now(),
                    created_by=user,
                    description=description
                )
                
                # Update dynamic rule
                dynamic_rule.versions.append(new_version)
                dynamic_rule.current_version = version_id
                dynamic_rule.base_rule = modified_rule
                dynamic_rule.last_modified = datetime.now()
                
                # Record modification
                modification_record = {
                    'timestamp': datetime.now().isoformat(),
                    'user': user,
                    'description': description,
                    'modifications': modifications,
                    'version_id': version_id
                }
                dynamic_rule.modification_history.append(modification_record)
                
                # Clean up old versions
                if len(dynamic_rule.versions) > self.max_rule_versions:
                    dynamic_rule.versions = dynamic_rule.versions[-self.max_rule_versions:]
                
                # Notify callbacks
                self._notify_modification_callbacks(rule_id, modification_record)
                
                self.logger.info(f"Modified rule {rule_id} to version {version_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error modifying rule {rule_id}: {e}")
                return False
    
    def _apply_modifications(self, rule: MCPRule, modifications: Dict[str, Any]) -> MCPRule:
        """Apply modifications to a rule"""
        modified_rule = copy.deepcopy(rule)
        
        for key, value in modifications.items():
            if key == 'name':
                modified_rule.name = value
            elif key == 'description':
                modified_rule.description = value
            elif key == 'category':
                modified_rule.category = value
            elif key == 'priority':
                modified_rule.priority = value
            elif key == 'enabled':
                modified_rule.enabled = value
            elif key == 'conditions':
                modified_rule.conditions = self._modify_conditions(rule.conditions, value)
            elif key == 'actions':
                modified_rule.actions = self._modify_actions(rule.actions, value)
            elif key == 'metadata':
                modified_rule.metadata.update(value)
        
        return modified_rule
    
    def _modify_conditions(self, conditions: List[RuleCondition], modifications: List[Dict[str, Any]]) -> List[RuleCondition]:
        """Modify rule conditions"""
        modified_conditions = []
        
        for i, condition in enumerate(conditions):
            if i < len(modifications):
                mod = modifications[i]
                modified_condition = copy.deepcopy(condition)
                
                for key, value in mod.items():
                    if hasattr(modified_condition, key):
                        setattr(modified_condition, key, value)
                
                modified_conditions.append(modified_condition)
            else:
                modified_conditions.append(condition)
        
        return modified_conditions
    
    def _modify_actions(self, actions: List[RuleAction], modifications: List[Dict[str, Any]]) -> List[RuleAction]:
        """Modify rule actions"""
        modified_actions = []
        
        for i, action in enumerate(actions):
            if i < len(modifications):
                mod = modifications[i]
                modified_action = copy.deepcopy(action)
                
                for key, value in mod.items():
                    if hasattr(modified_action, key):
                        setattr(modified_action, key, value)
                
                modified_actions.append(modified_action)
            else:
                modified_actions.append(action)
        
        return modified_actions
    
    def rollback_rule(self, rule_id: str, version_id: str) -> bool:
        """
        Rollback a rule to a specific version
        
        Args:
            rule_id: Rule ID to rollback
            version_id: Version ID to rollback to
            
        Returns:
            True if rollback was successful
        """
        with self.rule_lock:
            if rule_id not in self.dynamic_rules:
                self.logger.error(f"Dynamic rule {rule_id} not found")
                return False
            
            dynamic_rule = self.dynamic_rules[rule_id]
            
            # Find the target version
            target_version = None
            for version in dynamic_rule.versions:
                if version.version_id == version_id:
                    target_version = version
                    break
            
            if not target_version:
                self.logger.error(f"Version {version_id} not found for rule {rule_id}")
                return False
            
            # Create backup
            if self.auto_backup:
                self._create_backup(dynamic_rule)
            
            # Rollback to target version
            dynamic_rule.base_rule = self._dict_to_rule(target_version.rule_data)
            dynamic_rule.current_version = version_id
            dynamic_rule.last_modified = datetime.now()
            
            # Record rollback
            rollback_record = {
                'timestamp': datetime.now().isoformat(),
                'user': 'system',
                'description': f"Rollback to version {version_id}",
                'rollback_to': version_id
            }
            dynamic_rule.modification_history.append(rollback_record)
            
            self.logger.info(f"Rolled back rule {rule_id} to version {version_id}")
            return True
    
    def add_adaptive_condition(self, rule_id: str, condition: Dict[str, Any]) -> bool:
        """
        Add an adaptive condition to a dynamic rule
        
        Args:
            rule_id: Rule ID to add condition to
            condition: Adaptive condition definition
            
        Returns:
            True if condition was added successfully
        """
        with self.rule_lock:
            if rule_id not in self.dynamic_rules:
                self.logger.error(f"Dynamic rule {rule_id} not found")
                return False
            
            dynamic_rule = self.dynamic_rules[rule_id]
            dynamic_rule.adaptive_conditions.append(condition)
            
            self.logger.info(f"Added adaptive condition to rule {rule_id}")
            return True
    
    def evaluate_adaptive_conditions(self, rule_id: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate adaptive conditions for a rule
        
        Args:
            rule_id: Rule ID to evaluate
            context: Context for condition evaluation
            
        Returns:
            True if adaptive conditions are satisfied
        """
        if rule_id not in self.dynamic_rules:
            return True  # No adaptive conditions for non-dynamic rules
        
        dynamic_rule = self.dynamic_rules[rule_id]
        
        for condition in dynamic_rule.adaptive_conditions:
            if not self._evaluate_adaptive_condition(condition, context):
                return False
        
        return True
    
    def _evaluate_adaptive_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a single adaptive condition"""
        condition_type = condition.get('type', 'simple')
        
        if condition_type == 'simple':
            return self._evaluate_simple_condition(condition, context)
        elif condition_type == 'complex':
            return self._evaluate_complex_condition(condition, context)
        elif condition_type == 'time_based':
            return self._evaluate_time_based_condition(condition, context)
        else:
            self.logger.warning(f"Unknown adaptive condition type: {condition_type}")
            return True
    
    def _evaluate_simple_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate simple adaptive condition"""
        field = condition.get('field')
        operator = condition.get('operator', '==')
        value = condition.get('value')
        
        if field not in context:
            return True  # Field not present, condition passes
        
        context_value = context[field]
        
        if operator == '==':
            return context_value == value
        elif operator == '!=':
            return context_value != value
        elif operator == '>':
            return context_value > value
        elif operator == '<':
            return context_value < value
        elif operator == '>=':
            return context_value >= value
        elif operator == '<=':
            return context_value <= value
        elif operator == 'in':
            return context_value in value
        elif operator == 'not_in':
            return context_value not in value
        else:
            return True
    
    def _evaluate_complex_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate complex adaptive condition"""
        expression = condition.get('expression', '')
        
        try:
            # Simple expression evaluation (be careful with eval in production)
            # In a real implementation, use a proper expression parser
            local_vars = context.copy()
            return eval(expression, {"__builtins__": {}}, local_vars)
        except Exception as e:
            self.logger.error(f"Error evaluating complex condition: {e}")
            return True
    
    def _evaluate_time_based_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate time-based adaptive condition"""
        current_time = datetime.now()
        
        start_time = condition.get('start_time')
        end_time = condition.get('end_time')
        
        if start_time and current_time < start_time:
            return False
        
        if end_time and current_time > end_time:
            return False
        
        return True
    
    def validate_building_model_dynamic(self, building_model: BuildingModel,
                                      mcp_files: List[str],
                                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate building model with dynamic rules
        
        Args:
            building_model: Building model to validate
            mcp_files: List of MCP file paths
            context: Context for adaptive conditions
            
        Returns:
            Validation results with dynamic rule information
        """
        if context is None:
            context = {}
        
        self.logger.info("Starting dynamic validation")
        
        # Load MCP files
        loaded_mcp_files = []
        for file_path in mcp_files:
            try:
                mcp_file = self.base_engine.load_mcp_file(file_path)
                loaded_mcp_files.append(mcp_file)
            except Exception as e:
                self.logger.error(f"Failed to load MCP file {file_path}: {e}")
                continue
        
        if not loaded_mcp_files:
            raise ValueError("No valid MCP files loaded")
        
        # Process dynamic rules
        dynamic_results = []
        with self.rule_lock:
            for mcp_file in loaded_mcp_files:
                for rule in mcp_file.rules:
                    # Check if this is a dynamic rule
                    if rule.rule_id in self.dynamic_rules:
                        dynamic_rule = self.dynamic_rules[rule.rule_id]
                        
                        # Evaluate adaptive conditions
                        adaptive_satisfied = self.evaluate_adaptive_conditions(rule.rule_id, context)
                        
                        if adaptive_satisfied:
                            # Execute the current version of the rule
                            result = self.base_engine._execute_rule(dynamic_rule.base_rule, building_model)
                            dynamic_results.append({
                                'rule_id': rule.rule_id,
                                'version': dynamic_rule.current_version,
                                'adaptive_satisfied': True,
                                'result': result,
                                'last_modified': dynamic_rule.last_modified.isoformat()
                            })
                        else:
                            # Adaptive conditions not satisfied
                            dynamic_results.append({
                                'rule_id': rule.rule_id,
                                'version': dynamic_rule.current_version,
                                'adaptive_satisfied': False,
                                'result': None,
                                'last_modified': dynamic_rule.last_modified.isoformat()
                            })
                    else:
                        # Regular rule, execute normally
                        result = self.base_engine._execute_rule(rule, building_model)
                        dynamic_results.append({
                            'rule_id': rule.rule_id,
                            'version': 'static',
                            'adaptive_satisfied': True,
                            'result': result,
                            'last_modified': None
                        })
        
        return {
            'dynamic_results': dynamic_results,
            'total_rules': len(dynamic_results),
            'dynamic_rules': len([r for r in dynamic_results if r['version'] != 'static']),
            'adaptive_rules_executed': len([r for r in dynamic_results if r['adaptive_satisfied']])
        }
    
    def get_rule_versions(self, rule_id: str) -> List[Dict[str, Any]]:
        """Get version history for a dynamic rule"""
        if rule_id not in self.dynamic_rules:
            return []
        
        dynamic_rule = self.dynamic_rules[rule_id]
        
        versions = []
        for version in dynamic_rule.versions:
            versions.append({
                'version_id': version.version_id,
                'created_at': version.created_at.isoformat(),
                'created_by': version.created_by,
                'description': version.description,
                'is_active': version.version_id == dynamic_rule.current_version
            })
        
        return versions
    
    def get_modification_history(self, rule_id: str) -> List[Dict[str, Any]]:
        """Get modification history for a dynamic rule"""
        if rule_id not in self.dynamic_rules:
            return []
        
        return self.dynamic_rules[rule_id].modification_history
    
    def add_modification_callback(self, callback: callable):
        """Add a callback for rule modifications"""
        self.modification_callbacks.append(callback)
    
    def _notify_modification_callbacks(self, rule_id: str, modification: Dict[str, Any]):
        """Notify modification callbacks"""
        for callback in self.modification_callbacks:
            try:
                callback(rule_id, modification)
            except Exception as e:
                self.logger.error(f"Error in modification callback: {e}")
    
    def _create_backup(self, dynamic_rule: DynamicRule):
        """Create a backup of the current rule state"""
        backup = {
            'rule_id': dynamic_rule.rule_id,
            'current_version': dynamic_rule.current_version,
            'base_rule': self._rule_to_dict(dynamic_rule.base_rule),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store backup (in a real implementation, save to persistent storage)
        self.logger.debug(f"Created backup for rule {dynamic_rule.rule_id}")
    
    def _rule_to_dict(self, rule: MCPRule) -> Dict[str, Any]:
        """Convert rule to dictionary"""
        return {
            'rule_id': rule.rule_id,
            'name': rule.name,
            'description': rule.description,
            'category': rule.category.value if hasattr(rule.category, 'value') else rule.category,
            'priority': rule.priority,
            'enabled': rule.enabled,
            'version': rule.version,
            'conditions': [self._condition_to_dict(c) for c in rule.conditions],
            'actions': [self._action_to_dict(a) for a in rule.actions],
            'metadata': rule.metadata
        }
    
    def _condition_to_dict(self, condition: RuleCondition) -> Dict[str, Any]:
        """Convert condition to dictionary"""
        return {
            'type': condition.type.value if hasattr(condition.type, 'value') else condition.type,
            'element_type': condition.element_type,
            'property': condition.property,
            'operator': condition.operator,
            'value': condition.value,
            'relationship': condition.relationship,
            'target_type': condition.target_type,
            'composite_operator': condition.composite_operator
        }
    
    def _action_to_dict(self, action: RuleAction) -> Dict[str, Any]:
        """Convert action to dictionary"""
        return {
            'type': action.type.value if hasattr(action.type, 'value') else action.type,
            'message': action.message,
            'severity': action.severity.value if action.severity and hasattr(action.severity, 'value') else action.severity,
            'code_reference': action.code_reference,
            'formula': action.formula,
            'unit': action.unit,
            'description': action.description,
            'parameters': action.parameters
        }
    
    def _dict_to_rule(self, rule_data: Dict[str, Any]) -> MCPRule:
        """Convert dictionary to rule"""
        from models.mcp_models import RuleCategory, ConditionType, ActionType, RuleSeverity
        
        conditions = []
        for cond_data in rule_data.get('conditions', []):
            condition = RuleCondition(
                type=ConditionType(cond_data['type']) if isinstance(cond_data['type'], str) else cond_data['type'],
                element_type=cond_data.get('element_type'),
                property=cond_data.get('property'),
                operator=cond_data.get('operator'),
                value=cond_data.get('value'),
                relationship=cond_data.get('relationship'),
                target_type=cond_data.get('target_type'),
                composite_operator=cond_data.get('composite_operator')
            )
            conditions.append(condition)
        
        actions = []
        for act_data in rule_data.get('actions', []):
            action = RuleAction(
                type=ActionType(act_data['type']) if isinstance(act_data['type'], str) else act_data['type'],
                message=act_data.get('message'),
                severity=RuleSeverity(act_data['severity']) if act_data.get('severity') and isinstance(act_data['severity'], str) else act_data.get('severity'),
                code_reference=act_data.get('code_reference'),
                formula=act_data.get('formula'),
                unit=act_data.get('unit'),
                description=act_data.get('description'),
                parameters=act_data.get('parameters')
            )
            actions.append(action)
        
        return MCPRule(
            rule_id=rule_data['rule_id'],
            name=rule_data['name'],
            description=rule_data['description'],
            category=RuleCategory(rule_data['category']) if isinstance(rule_data['category'], str) else rule_data['category'],
            priority=rule_data.get('priority', 1),
            conditions=conditions,
            actions=actions,
            enabled=rule_data.get('enabled', True),
            version=rule_data.get('version', '1.0'),
            metadata=rule_data.get('metadata', {})
        ) 