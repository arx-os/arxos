"""
Rule Engine for Workflow Automation.

Provides intelligent rule evaluation, threshold monitoring, pattern detection,
and automated decision making for workflow automation.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from collections import deque, defaultdict

from infrastructure.logging.structured_logging import get_logger


logger = get_logger(__name__)


class RuleType(Enum):
    """Types of rules."""
    THRESHOLD = "threshold"
    PATTERN = "pattern"
    TIME_BASED = "time_based"
    CORRELATION = "correlation"
    ANOMALY = "anomaly"
    COMPOSITE = "composite"


class ComparisonOperator(Enum):
    """Comparison operators for rules."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


@dataclass
class RuleCondition:
    """Individual rule condition."""
    field: str
    operator: ComparisonOperator
    value: Any
    weight: float = 1.0
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate condition against data."""
        field_value = self._get_field_value(data, self.field)
        
        try:
            if self.operator == ComparisonOperator.EQUALS:
                return field_value == self.value
            elif self.operator == ComparisonOperator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == ComparisonOperator.GREATER_THAN:
                return float(field_value) > float(self.value)
            elif self.operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
                return float(field_value) >= float(self.value)
            elif self.operator == ComparisonOperator.LESS_THAN:
                return float(field_value) < float(self.value)
            elif self.operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
                return float(field_value) <= float(self.value)
            elif self.operator == ComparisonOperator.BETWEEN:
                if isinstance(self.value, list) and len(self.value) == 2:
                    return self.value[0] <= float(field_value) <= self.value[1]
                return False
            elif self.operator == ComparisonOperator.NOT_BETWEEN:
                if isinstance(self.value, list) and len(self.value) == 2:
                    return not (self.value[0] <= float(field_value) <= self.value[1])
                return True
            elif self.operator == ComparisonOperator.IN:
                return field_value in self.value
            elif self.operator == ComparisonOperator.NOT_IN:
                return field_value not in self.value
            elif self.operator == ComparisonOperator.CONTAINS:
                return str(self.value) in str(field_value)
            elif self.operator == ComparisonOperator.NOT_CONTAINS:
                return str(self.value) not in str(field_value)
            elif self.operator == ComparisonOperator.REGEX:
                return bool(re.match(str(self.value), str(field_value)))
            elif self.operator == ComparisonOperator.EXISTS:
                return field_value is not None
            elif self.operator == ComparisonOperator.NOT_EXISTS:
                return field_value is None
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Rule condition evaluation error: {e}")
            return False
        
        return False
    
    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get field value using dot notation."""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif isinstance(value, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(value):
                    value = value[index]
                else:
                    return None
            else:
                return None
        
        return value


@dataclass
class Rule:
    """Rule definition with conditions and actions."""
    id: str
    name: str
    description: str
    rule_type: RuleType
    conditions: List[RuleCondition] = field(default_factory=list)
    logic_operator: str = "AND"  # AND, OR
    priority: int = 5  # 1-10 scale
    enabled: bool = True
    
    # Time-based settings
    time_window_minutes: Optional[int] = None
    cooldown_minutes: Optional[int] = None
    
    # Pattern detection
    pattern_threshold: int = 3
    pattern_window_minutes: int = 30
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Execution tracking
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    
    def evaluate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate rule against data."""
        if not self.enabled:
            return {"triggered": False, "reason": "Rule disabled"}
        
        # Check cooldown period
        if self.cooldown_minutes and self.last_triggered_at:
            cooldown_end = self.last_triggered_at + timedelta(minutes=self.cooldown_minutes)
            if datetime.now(timezone.utc) < cooldown_end:
                return {"triggered": False, "reason": "Rule in cooldown period"}
        
        # Evaluate conditions
        if not self.conditions:
            return {"triggered": False, "reason": "No conditions defined"}
        
        condition_results = []
        weighted_score = 0.0
        total_weight = 0.0
        
        for condition in self.conditions:
            result = condition.evaluate(data)
            condition_results.append({
                "condition": f"{condition.field} {condition.operator.value} {condition.value}",
                "result": result,
                "weight": condition.weight
            })
            
            if result:
                weighted_score += condition.weight
            total_weight += condition.weight
        
        # Apply logic operator
        if self.logic_operator.upper() == "AND":
            triggered = all(cr["result"] for cr in condition_results)
        elif self.logic_operator.upper() == "OR":
            triggered = any(cr["result"] for cr in condition_results)
        else:
            triggered = False
        
        # Calculate confidence score
        confidence = (weighted_score / total_weight) if total_weight > 0 else 0.0
        
        evaluation_result = {
            "rule_id": self.id,
            "rule_name": self.name,
            "rule_type": self.rule_type.value,
            "triggered": triggered,
            "confidence": confidence,
            "condition_results": condition_results,
            "logic_operator": self.logic_operator,
            "evaluation_time": datetime.now(timezone.utc).isoformat(),
            "priority": self.priority
        }
        
        # Update trigger tracking if triggered
        if triggered:
            self.last_triggered_at = datetime.now(timezone.utc)
            self.trigger_count += 1
            evaluation_result["trigger_count"] = self.trigger_count
        
        return evaluation_result


class RuleEngine:
    """Advanced rule engine for workflow automation."""
    
    def __init__(self, max_history_size: int = 1000):
        self.rules: Dict[str, Rule] = {}
        self.rule_groups: Dict[str, List[str]] = {}
        self.max_history_size = max_history_size
        
        # Event history for pattern detection
        self.event_history: deque = deque(maxlen=max_history_size)
        
        # Threshold monitoring
        self.threshold_monitors: Dict[str, Dict[str, Any]] = {}
        
        # Pattern detection
        self.pattern_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Statistics
        self.evaluation_stats = {
            "total_evaluations": 0,
            "triggered_rules": 0,
            "rule_performance": defaultdict(lambda: {"evaluations": 0, "triggers": 0})
        }
    
    def add_rule(self, rule: Rule) -> None:
        """Add rule to engine."""
        self.rules[rule.id] = rule
        logger.info(f"Added rule: {rule.name} ({rule.id})")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove rule from engine."""
        if rule_id in self.rules:
            rule = self.rules.pop(rule_id)
            logger.info(f"Removed rule: {rule.name} ({rule_id})")
            return True
        return False
    
    def update_rule(self, rule: Rule) -> None:
        """Update existing rule."""
        if rule.id in self.rules:
            rule.updated_at = datetime.now(timezone.utc)
            self.rules[rule.id] = rule
            logger.info(f"Updated rule: {rule.name} ({rule.id})")
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get rule by ID."""
        return self.rules.get(rule_id)
    
    def list_rules(self, rule_type: Optional[RuleType] = None, enabled_only: bool = True) -> List[Rule]:
        """List rules with optional filtering."""
        rules = list(self.rules.values())
        
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]
        
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        
        return sorted(rules, key=lambda r: r.priority, reverse=True)
    
    def create_rule_group(self, group_name: str, rule_ids: List[str]) -> None:
        """Create rule group for batch operations."""
        self.rule_groups[group_name] = rule_ids
        logger.info(f"Created rule group: {group_name} with {len(rule_ids)} rules")
    
    def evaluate_rules(self, data: Dict[str, Any], rule_ids: Optional[List[str]] = None,
                      rule_types: Optional[List[RuleType]] = None) -> List[Dict[str, Any]]:
        """Evaluate rules against data."""
        # Record event in history
        self.event_history.append({
            "data": data.copy(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Determine which rules to evaluate
        if rule_ids:
            rules_to_evaluate = [self.rules[rid] for rid in rule_ids if rid in self.rules]
        elif rule_types:
            rules_to_evaluate = [r for r in self.rules.values() if r.rule_type in rule_types]
        else:
            rules_to_evaluate = [r for r in self.rules.values() if r.enabled]
        
        results = []
        triggered_rules = []
        
        for rule in rules_to_evaluate:
            self.evaluation_stats["total_evaluations"] += 1
            self.evaluation_stats["rule_performance"][rule.id]["evaluations"] += 1
            
            try:
                result = rule.evaluate(data)
                results.append(result)
                
                if result["triggered"]:
                    triggered_rules.append(result)
                    self.evaluation_stats["triggered_rules"] += 1
                    self.evaluation_stats["rule_performance"][rule.id]["triggers"] += 1
                    
                    logger.info(f"Rule triggered: {rule.name} with confidence {result['confidence']:.2f}")
                
            except Exception as e:
                logger.error(f"Rule evaluation error for {rule.name}: {e}")
                results.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "triggered": False,
                    "error": str(e),
                    "evaluation_time": datetime.now(timezone.utc).isoformat()
                })
        
        # Sort triggered rules by priority
        triggered_rules.sort(key=lambda r: r["priority"], reverse=True)
        
        return {
            "all_results": results,
            "triggered_rules": triggered_rules,
            "evaluation_summary": {
                "total_rules_evaluated": len(rules_to_evaluate),
                "rules_triggered": len(triggered_rules),
                "evaluation_time": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def evaluate_thresholds(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate threshold-based rules."""
        threshold_rules = [r for r in self.rules.values() if r.rule_type == RuleType.THRESHOLD and r.enabled]
        
        if not threshold_rules:
            return []
        
        results = self.evaluate_rules(data, rule_ids=[r.id for r in threshold_rules])
        return results["triggered_rules"]
    
    def detect_patterns(self, pattern_type: str, lookback_minutes: int = 30) -> List[Dict[str, Any]]:
        """Detect patterns in event history."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
        
        # Filter recent events
        recent_events = [
            event for event in self.event_history
            if datetime.fromisoformat(event["timestamp"]) > cutoff_time
        ]
        
        if len(recent_events) < 3:
            return []
        
        patterns = []
        
        # Simple pattern detection examples
        if pattern_type == "anomaly":
            patterns.extend(self._detect_anomalies(recent_events))
        elif pattern_type == "trend":
            patterns.extend(self._detect_trends(recent_events))
        elif pattern_type == "spike":
            patterns.extend(self._detect_spikes(recent_events))
        
        return patterns
    
    def _detect_anomalies(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in event data."""
        anomalies = []
        
        # Simple statistical anomaly detection
        # Group events by data fields
        field_values = defaultdict(list)
        
        for event in events:
            data = event["data"]
            for field, value in data.items():
                if isinstance(value, (int, float)):
                    field_values[field].append(value)
        
        for field, values in field_values.items():
            if len(values) < 5:  # Need minimum data points
                continue
            
            # Calculate statistics
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            
            # Check latest value
            latest_value = values[-1]
            z_score = abs(latest_value - mean_val) / std_dev if std_dev > 0 else 0
            
            if z_score > 2.5:  # Anomaly threshold
                anomalies.append({
                    "type": "statistical_anomaly",
                    "field": field,
                    "latest_value": latest_value,
                    "mean_value": mean_val,
                    "z_score": z_score,
                    "severity": "high" if z_score > 3 else "medium",
                    "detected_at": datetime.now(timezone.utc).isoformat()
                })
        
        return anomalies
    
    def _detect_trends(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect trends in event data."""
        trends = []
        
        # Group numeric values by field
        field_series = defaultdict(list)
        
        for event in events:
            timestamp = datetime.fromisoformat(event["timestamp"])
            data = event["data"]
            
            for field, value in data.items():
                if isinstance(value, (int, float)):
                    field_series[field].append((timestamp, value))
        
        for field, series in field_series.items():
            if len(series) < 5:
                continue
            
            # Sort by timestamp
            series.sort(key=lambda x: x[0])
            values = [v for _, v in series]
            
            # Simple trend detection using linear regression
            n = len(values)
            x_vals = list(range(n))
            
            # Calculate slope
            x_mean = sum(x_vals) / n
            y_mean = sum(values) / n
            
            numerator = sum((x_vals[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x - x_mean) ** 2 for x in x_vals)
            
            if denominator > 0:
                slope = numerator / denominator
                
                # Determine trend significance
                if abs(slope) > 0.1:  # Threshold for significant trend
                    trend_direction = "increasing" if slope > 0 else "decreasing"
                    
                    trends.append({
                        "type": "trend",
                        "field": field,
                        "direction": trend_direction,
                        "slope": slope,
                        "strength": min(abs(slope), 1.0),  # Normalize strength
                        "data_points": n,
                        "detected_at": datetime.now(timezone.utc).isoformat()
                    })
        
        return trends
    
    def _detect_spikes(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect spikes in event data."""
        spikes = []
        
        # Look for sudden increases in numeric values
        field_values = defaultdict(list)
        
        for event in events:
            timestamp = datetime.fromisoformat(event["timestamp"])
            data = event["data"]
            
            for field, value in data.items():
                if isinstance(value, (int, float)):
                    field_values[field].append((timestamp, value))
        
        for field, series in field_values.items():
            if len(series) < 3:
                continue
            
            series.sort(key=lambda x: x[0])
            values = [v for _, v in series]
            
            # Check for spikes (value significantly higher than recent average)
            for i in range(2, len(values)):
                recent_avg = sum(values[i-2:i]) / 2
                current_value = values[i]
                
                if recent_avg > 0 and current_value > recent_avg * 2:  # Spike threshold
                    spike_magnitude = current_value / recent_avg
                    
                    spikes.append({
                        "type": "spike",
                        "field": field,
                        "spike_value": current_value,
                        "baseline_average": recent_avg,
                        "magnitude": spike_magnitude,
                        "severity": "high" if spike_magnitude > 5 else "medium",
                        "timestamp": series[i][0].isoformat(),
                        "detected_at": datetime.now(timezone.utc).isoformat()
                    })
        
        return spikes
    
    def create_threshold_rule(self, name: str, field: str, threshold_value: float,
                            operator: ComparisonOperator = ComparisonOperator.GREATER_THAN,
                            description: str = "") -> Rule:
        """Create a threshold-based rule."""
        rule_id = f"threshold_{field}_{len(self.rules)}"
        
        condition = RuleCondition(
            field=field,
            operator=operator,
            value=threshold_value
        )
        
        rule = Rule(
            id=rule_id,
            name=name,
            description=description or f"Threshold rule for {field}",
            rule_type=RuleType.THRESHOLD,
            conditions=[condition]
        )
        
        self.add_rule(rule)
        return rule
    
    def create_pattern_rule(self, name: str, pattern_conditions: List[Dict[str, Any]],
                          pattern_threshold: int = 3, time_window_minutes: int = 30,
                          description: str = "") -> Rule:
        """Create a pattern-based rule."""
        rule_id = f"pattern_{len(self.rules)}"
        
        conditions = []
        for cond_data in pattern_conditions:
            condition = RuleCondition(
                field=cond_data["field"],
                operator=ComparisonOperator(cond_data["operator"]),
                value=cond_data["value"],
                weight=cond_data.get("weight", 1.0)
            )
            conditions.append(condition)
        
        rule = Rule(
            id=rule_id,
            name=name,
            description=description or f"Pattern rule with {len(conditions)} conditions",
            rule_type=RuleType.PATTERN,
            conditions=conditions,
            pattern_threshold=pattern_threshold,
            pattern_window_minutes=time_window_minutes
        )
        
        self.add_rule(rule)
        return rule
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rule engine statistics."""
        total_rules = len(self.rules)
        enabled_rules = len([r for r in self.rules.values() if r.enabled])
        
        # Rule type distribution
        type_distribution = defaultdict(int)
        for rule in self.rules.values():
            type_distribution[rule.rule_type.value] += 1
        
        # Performance statistics
        performance_stats = {}
        for rule_id, stats in self.evaluation_stats["rule_performance"].items():
            rule = self.rules.get(rule_id)
            if rule:
                trigger_rate = (stats["triggers"] / stats["evaluations"] * 100) if stats["evaluations"] > 0 else 0
                performance_stats[rule.name] = {
                    "evaluations": stats["evaluations"],
                    "triggers": stats["triggers"],
                    "trigger_rate": round(trigger_rate, 2)
                }
        
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": total_rules - enabled_rules,
            "rule_type_distribution": dict(type_distribution),
            "evaluation_stats": {
                "total_evaluations": self.evaluation_stats["total_evaluations"],
                "triggered_rules": self.evaluation_stats["triggered_rules"],
                "trigger_rate": round(
                    (self.evaluation_stats["triggered_rules"] / self.evaluation_stats["total_evaluations"] * 100)
                    if self.evaluation_stats["total_evaluations"] > 0 else 0, 2
                )
            },
            "rule_performance": performance_stats,
            "event_history_size": len(self.event_history),
            "rule_groups": len(self.rule_groups)
        }
    
    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        logger.info("Rule engine event history cleared")
    
    def export_rules(self) -> List[Dict[str, Any]]:
        """Export all rules to dictionary format."""
        exported_rules = []
        
        for rule in self.rules.values():
            rule_dict = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "rule_type": rule.rule_type.value,
                "logic_operator": rule.logic_operator,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "conditions": [
                    {
                        "field": cond.field,
                        "operator": cond.operator.value,
                        "value": cond.value,
                        "weight": cond.weight
                    } for cond in rule.conditions
                ],
                "time_window_minutes": rule.time_window_minutes,
                "cooldown_minutes": rule.cooldown_minutes,
                "pattern_threshold": rule.pattern_threshold,
                "pattern_window_minutes": rule.pattern_window_minutes,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat()
            }
            exported_rules.append(rule_dict)
        
        return exported_rules
    
    def import_rules(self, rules_data: List[Dict[str, Any]], overwrite: bool = False) -> Dict[str, Any]:
        """Import rules from dictionary format."""
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for rule_data in rules_data:
            try:
                rule_id = rule_data["id"]
                
                # Check if rule already exists
                if rule_id in self.rules and not overwrite:
                    skipped_count += 1
                    continue
                
                # Create conditions
                conditions = []
                for cond_data in rule_data.get("conditions", []):
                    condition = RuleCondition(
                        field=cond_data["field"],
                        operator=ComparisonOperator(cond_data["operator"]),
                        value=cond_data["value"],
                        weight=cond_data.get("weight", 1.0)
                    )
                    conditions.append(condition)
                
                # Create rule
                rule = Rule(
                    id=rule_id,
                    name=rule_data["name"],
                    description=rule_data.get("description", ""),
                    rule_type=RuleType(rule_data["rule_type"]),
                    conditions=conditions,
                    logic_operator=rule_data.get("logic_operator", "AND"),
                    priority=rule_data.get("priority", 5),
                    enabled=rule_data.get("enabled", True),
                    time_window_minutes=rule_data.get("time_window_minutes"),
                    cooldown_minutes=rule_data.get("cooldown_minutes"),
                    pattern_threshold=rule_data.get("pattern_threshold", 3),
                    pattern_window_minutes=rule_data.get("pattern_window_minutes", 30)
                )
                
                # Set timestamps
                if "created_at" in rule_data:
                    rule.created_at = datetime.fromisoformat(rule_data["created_at"])
                if "updated_at" in rule_data:
                    rule.updated_at = datetime.fromisoformat(rule_data["updated_at"])
                
                self.add_rule(rule)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Failed to import rule {rule_data.get('id', 'unknown')}: {str(e)}")
        
        return {
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "error_count": len(errors),
            "errors": errors
        }