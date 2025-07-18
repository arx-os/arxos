"""
SVGX Runtime Module

Handles simulation, behavior evaluation, and runtime execution
of SVGX files with programmable logic and physics.
"""

import logging
from typing import Dict, Any, List

from svgx_engine.runtime.evaluator import SVGXEvaluator
from svgx_engine.runtime.behavior_engine import SVGXBehaviorEngine
from svgx_engine.runtime.advanced_behavior_engine import AdvancedBehaviorEngine
from svgx_engine.runtime.physics_engine import SVGXPhysicsEngine

logger = logging.getLogger(__name__)

__all__ = [
    "SVGXRuntime",
    "SVGXEvaluator",
    "SVGXBehaviorEngine",
    "AdvancedBehaviorEngine",
    "SVGXPhysicsEngine",
]

class SVGXRuntime:
    """Main runtime class that orchestrates simulation and behavior execution."""
    
    def __init__(self):
        self.evaluator = SVGXEvaluator()
        self.behavior_engine = SVGXBehaviorEngine()
        self.advanced_behavior_engine = AdvancedBehaviorEngine()
        self.physics_engine = SVGXPhysicsEngine()
        
        # Initialize logic engine for rule-based processing
        try:
            import sys
            import os
            # Add the services directory to the path
            services_path = os.path.join(os.path.dirname(__file__), '..', 'services')
            if services_path not in sys.path:
                sys.path.insert(0, services_path)
            
            from logic_engine import LogicEngine
            self.logic_engine = LogicEngine()
            logger.info("Logic engine initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize logic engine: {e}")
            self.logic_engine = None
    
    def simulate(self, svgx_content):
        """Run simulation on SVGX content."""
        # TODO: Implement simulation logic
        pass
    
    async def evaluate_advanced_behaviors(self, element_id: str, context: Dict[str, Any]):
        """Evaluate advanced behaviors for an element."""
        try:
            # Evaluate rules using advanced behavior engine
            applicable_rules = await self.advanced_behavior_engine.evaluate_rules(element_id, context)
            
            # Execute applicable rules
            for rule in applicable_rules:
                await self.advanced_behavior_engine._execute_actions(rule['actions'], element_id, context)
            
            # Handle state transitions if needed
            if 'target_state' in context:
                await self.advanced_behavior_engine.execute_state_transition(
                    element_id, context['target_state'], context
                )
            
            return applicable_rules
            
        except Exception as e:
            logger.error(f"Failed to evaluate advanced behaviors for {element_id}: {e}")
            return []
    
    def execute_logic_rules(self, element_id: str, data: Dict[str, Any], rule_ids: List[str] = None):
        """Execute logic engine rules for an element."""
        if not self.logic_engine:
            logger.warning("Logic engine not available")
            return []
        
        try:
            results = []
            
            if rule_ids:
                # Execute specific rules
                for rule_id in rule_ids:
                    rule = self.logic_engine.get_rule(rule_id)
                    if rule:
                        execution = self.logic_engine.execute_rule(rule_id, data)
                        results.append(execution)
            else:
                # Execute all applicable rules
                rules = self.logic_engine.list_rules(status="active")
                for rule in rules:
                    execution = self.logic_engine.execute_rule(rule.rule_id, data)
                    results.append(execution)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to execute logic rules for {element_id}: {e}")
            return []
    
    def create_logic_rule(self, name: str, description: str, rule_type: str, 
                         conditions: List[Dict[str, Any]], actions: List[Dict[str, Any]], 
                         priority: int = 1, tags: List[str] = None):
        """Create a new logic rule."""
        if not self.logic_engine:
            logger.warning("Logic engine not available")
            return None
        
        try:
            from logic_engine import RuleType
            
            rule_type_enum = getattr(RuleType, rule_type.upper(), RuleType.CONDITIONAL)
            
            rule_id = self.logic_engine.create_rule(
                name=name,
                description=description,
                rule_type=rule_type_enum,
                conditions=conditions,
                actions=actions,
                priority=priority,
                tags=tags or []
            )
            
            logger.info(f"Created logic rule: {rule_id}")
            return rule_id
            
        except Exception as e:
            logger.error(f"Failed to create logic rule: {e}")
            return None
    
    def get_logic_engine_stats(self):
        """Get logic engine performance statistics."""
        if not self.logic_engine:
            return {"status": "not_available"}
        
        try:
            return self.logic_engine.get_performance_metrics()
        except Exception as e:
            logger.error(f"Failed to get logic engine stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def register_advanced_behavior(self, element_id: str, behavior_config: Dict[str, Any]):
        """Register advanced behavior configuration for an element."""
        try:
            from svgx_engine.runtime.advanced_behavior_engine import BehaviorRule, BehaviorState, TimeTrigger, Condition
            
            # Register rules
            if 'rules' in behavior_config:
                for rule_data in behavior_config['rules']:
                    rule = BehaviorRule(**rule_data)
                    self.advanced_behavior_engine.register_rule(rule)
            
            # Register state machine
            if 'state_machine' in behavior_config:
                states_data = behavior_config['state_machine']['states']
                initial_state = behavior_config['state_machine']['initial_state']
                
                states = [BehaviorState(**state_data) for state_data in states_data]
                self.advanced_behavior_engine.register_state_machine(element_id, states, initial_state)
            
            # Register time triggers
            if 'time_triggers' in behavior_config:
                for trigger_data in behavior_config['time_triggers']:
                    trigger = TimeTrigger(**trigger_data)
                    self.advanced_behavior_engine.register_time_trigger(trigger)
            
            # Register conditions
            if 'conditions' in behavior_config:
                for condition_data in behavior_config['conditions']:
                    condition = Condition(**condition_data)
                    self.advanced_behavior_engine.register_condition(condition)
            
            logger.info(f"Registered advanced behavior for {element_id}")
            
        except Exception as e:
            logger.error(f"Failed to register advanced behavior for {element_id}: {e}")
    
    def start_advanced_behavior_engine(self):
        """Start the advanced behavior engine."""
        self.advanced_behavior_engine.start()
    
    def stop_advanced_behavior_engine(self):
        """Stop the advanced behavior engine."""
        self.advanced_behavior_engine.stop()
    
    def get_advanced_behavior_status(self):
        """Get status of advanced behavior engine."""
        return {
            'running': self.advanced_behavior_engine.running,
            'registered_rules': len(self.advanced_behavior_engine.get_registered_rules()),
            'registered_state_machines': len(self.advanced_behavior_engine.get_registered_state_machines()),
            'registered_time_triggers': len(self.advanced_behavior_engine.get_registered_time_triggers())
        } 