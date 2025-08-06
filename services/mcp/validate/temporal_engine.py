"""
Temporal Rules Engine for MCP Rule Validation

This module provides temporal rule capabilities:
- Time-based rule evaluation
- Scheduling and recurring rules
- Temporal condition evaluation
- Time-aware validation logic
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re
import pytz

from models.mcp_models import (
    BuildingModel,
    BuildingObject,
    MCPFile,
    MCPRule,
    RuleCondition,
    RuleAction,
    ValidationViolation,
    RuleCategory,
)
from validate.rule_engine import MCPRuleEngine, RuleExecutionContext


class TemporalOperator(Enum):
    """Temporal operators for rule evaluation"""

    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    BETWEEN = "between"
    ON = "on"
    EVERY = "every"
    WEEKDAY = "weekday"
    WEEKEND = "weekend"
    BUSINESS_HOURS = "business_hours"
    OFF_HOURS = "off_hours"


@dataclass
class TemporalCondition:
    """Temporal condition for rule evaluation"""

    operator: TemporalOperator
    start_time: Optional[Union[str, datetime]] = None
    end_time: Optional[Union[str, datetime]] = None
    timezone: str = "UTC"
    days_of_week: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    months: Optional[List[int]] = None  # 1-12
    years: Optional[List[int]] = None
    business_hours_start: str = "09:00"
    business_hours_end: str = "17:00"
    time_format: str = "%H:%M"
    date_format: str = "%Y-%m-%d"
    datetime_format: str = "%Y-%m-%d %H:%M:%S"


class TemporalRuleEngine:
    """
    Temporal rules engine for time-based validation

    Features:
    - Time-based rule evaluation
    - Scheduling and recurring rules
    - Business hours validation
    - Timezone-aware processing
    - Temporal condition evaluation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize temporal rules engine

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Time settings
        self.default_timezone = self.config.get("default_timezone", "UTC")
        self.business_hours_start = self.config.get("business_hours_start", "09:00")
        self.business_hours_end = self.config.get("business_hours_end", "17:00")
        self.weekend_days = self.config.get("weekend_days", [5, 6])  # Saturday, Sunday

        # Initialize base engine
        self.base_engine = MCPRuleEngine(config)

        self.logger.info("Temporal Rule Engine initialized")

    def evaluate_temporal_condition(
        self, condition: TemporalCondition, current_time: Optional[datetime] = None
    ) -> bool:
        """
        Evaluate a temporal condition

        Args:
            condition: Temporal condition to evaluate
            current_time: Current time (defaults to now)

        Returns:
            True if condition is satisfied
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Convert to condition timezone
        tz = pytz.timezone(condition.timezone)
        current_time = current_time.astimezone(tz)

        try:
            if condition.operator == TemporalOperator.BEFORE:
                return self._evaluate_before(condition, current_time)
            elif condition.operator == TemporalOperator.AFTER:
                return self._evaluate_after(condition, current_time)
            elif condition.operator == TemporalOperator.DURING:
                return self._evaluate_during(condition, current_time)
            elif condition.operator == TemporalOperator.BETWEEN:
                return self._evaluate_between(condition, current_time)
            elif condition.operator == TemporalOperator.ON:
                return self._evaluate_on(condition, current_time)
            elif condition.operator == TemporalOperator.EVERY:
                return self._evaluate_every(condition, current_time)
            elif condition.operator == TemporalOperator.WEEKDAY:
                return self._evaluate_weekday(current_time)
            elif condition.operator == TemporalOperator.WEEKEND:
                return self._evaluate_weekend(current_time)
            elif condition.operator == TemporalOperator.BUSINESS_HOURS:
                return self._evaluate_business_hours(condition, current_time)
            elif condition.operator == TemporalOperator.OFF_HOURS:
                return self._evaluate_off_hours(condition, current_time)
            else:
                self.logger.warning(f"Unknown temporal operator: {condition.operator}")
                return False

        except Exception as e:
            self.logger.error(f"Error evaluating temporal condition: {e}")
            return False

    def _evaluate_before(
        self, condition: TemporalCondition, current_time: datetime
    ) -> bool:
        """Evaluate 'before' condition"""
        if condition.start_time is None:
            return False

        target_time = self._parse_time(condition.start_time, condition)
        return current_time < target_time

    def _evaluate_after(
        self, condition: TemporalCondition, current_time: datetime
    ) -> bool:
        """Evaluate 'after' condition"""
        if condition.start_time is None:
            return False

        target_time = self._parse_time(condition.start_time, condition)
        return current_time > target_time

    def _evaluate_during(
        self, condition: TemporalCondition, current_time: datetime
    ) -> bool:
        """Evaluate 'during' condition"""
        if condition.start_time is None or condition.end_time is None:
            return False

        start_time = self._parse_time(condition.start_time, condition)
        end_time = self._parse_time(condition.end_time, condition)

        return start_time <= current_time <= end_time

    def _evaluate_between(
        self, condition: TemporalCondition, current_time: datetime
    ) -> bool:
        """Evaluate 'between' condition (same as during)"""
        return self._evaluate_during(condition, current_time)

    def _evaluate_on(
        self, condition: TemporalCondition, current_time: datetime
    ) -> bool:
        """Evaluate 'on' condition (specific date/time)"""
        if condition.start_time is None:
            return False

        target_time = self._parse_time(condition.start_time, condition)

        # Check if it's the same day
        return (
            current_time.date() == target_time.date()
            and current_time.hour == target_time.hour
            and current_time.minute == target_time.minute
        )

    def _evaluate_every(
        self, condition: TemporalCondition, current_time: datetime
    ) -> bool:
        """Evaluate 'every' condition (recurring)"""
        if condition.start_time is None:
            return False

        # Parse the recurring pattern (e.g., "every 30 minutes", "every 2 hours")
        pattern = str(condition.start_time)

        if "minute" in pattern:
            interval = int(re.search(r"(\d+)", pattern).group(1))
            return current_time.minute % interval == 0
        elif "hour" in pattern:
            interval = int(re.search(r"(\d+)", pattern).group(1))
            return current_time.hour % interval == 0
        elif "day" in pattern:
            interval = int(re.search(r"(\d+)", pattern).group(1))
            return current_time.day % interval == 0
        elif "week" in pattern:
            interval = int(re.search(r"(\d+)", pattern).group(1))
            week_num = current_time.isocalendar()[1]
            return week_num % interval == 0
        elif "month" in pattern:
            interval = int(re.search(r"(\d+)", pattern).group(1))
            return current_time.month % interval == 0

        return False

    def _evaluate_weekday(self, current_time: datetime) -> bool:
        """Evaluate weekday condition"""
        return current_time.weekday() < 5  # Monday = 0, Friday = 4

    def _evaluate_weekend(self, current_time: datetime) -> bool:
        """Evaluate weekend condition"""
        return current_time.weekday() >= 5  # Saturday = 5, Sunday = 6

    def _evaluate_business_hours(
        self, condition: TemporalCondition, current_time: datetime
    ) -> bool:
        """Evaluate business hours condition"""
        # Check if it's a weekday
        if not self._evaluate_weekday(current_time):
            return False

        # Check if it's within business hours
        start_time = datetime.strptime(
            condition.business_hours_start, condition.time_format
        ).time()
        end_time = datetime.strptime(
            condition.business_hours_end, condition.time_format
        ).time()

        return start_time <= current_time.time() <= end_time

    def _evaluate_off_hours(
        self, condition: TemporalCondition, current_time: datetime
    ) -> bool:
        """Evaluate off-hours condition"""
        return not self._evaluate_business_hours(condition, current_time)

    def _parse_time(
        self, time_value: Union[str, datetime], condition: TemporalCondition
    ) -> datetime:
        """Parse time value according to condition format"""
        if isinstance(time_value, datetime):
            return time_value

        # Try different formats
        formats = [
            condition.datetime_format,
            condition.date_format,
            condition.time_format,
            "%Y-%m-%d %H:%M",
            "%H:%M:%S",
            "%H:%M",
        ]

        for fmt in formats:
            try:
                if len(time_value) == 10:  # Date only
                    parsed = datetime.strptime(time_value, condition.date_format)
                    return parsed.replace(tzinfo=pytz.timezone(condition.timezone))
                elif len(time_value) == 5:  # Time only
                    parsed = datetime.strptime(time_value, condition.time_format)
                    # Use current date
                    now = datetime.now(pytz.timezone(condition.timezone))
                    return now.replace(hour=parsed.hour, minute=parsed.minute)
                else:  # Full datetime or ISO format
                    try:
                        # Try ISO format first
                        if "T" in time_value or "+" in time_value:
                            return datetime.fromisoformat(
                                time_value.replace("Z", "+00:00")
                            )
                        else:
                            parsed = datetime.strptime(
                                time_value, condition.datetime_format
                            )
                            return parsed.replace(
                                tzinfo=pytz.timezone(condition.timezone)
                            )
                    except ValueError:
                        continue
            except ValueError:
                continue

        raise ValueError(f"Could not parse time value: {time_value}")

    def create_temporal_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        temporal_condition: TemporalCondition,
        base_conditions: List[RuleCondition],
        actions: List[RuleAction],
    ) -> MCPRule:
        """
        Create a temporal rule

        Args:
            rule_id: Unique rule identifier
            name: Rule name
            description: Rule description
            temporal_condition: Temporal condition
            base_conditions: Base rule conditions
            actions: Rule actions

        Returns:
            MCPRule with temporal capabilities
        """
        # Add temporal condition as a special condition
        temporal_condition_dict = {
            "type": "temporal",
            "operator": temporal_condition.operator.value,
            "start_time": temporal_condition.start_time,
            "end_time": temporal_condition.end_time,
            "timezone": temporal_condition.timezone,
            "business_hours_start": temporal_condition.business_hours_start,
            "business_hours_end": temporal_condition.business_hours_end,
        }

        # Create a special condition for temporal evaluation
        temporal_rule_condition = RuleCondition(
            type=ConditionType.PROPERTY,  # Use existing enum type
            property="temporal_condition",
            value=temporal_condition_dict,
        )

        # Combine temporal and base conditions
        all_conditions = [temporal_rule_condition] + base_conditions

        return MCPRule(
            rule_id=rule_id,
            name=name,
            description=description,
            category=RuleCategory.GENERAL,  # Use enum instead of string
            conditions=all_conditions,
            actions=actions,
            metadata={"temporal_condition": temporal_condition},
        )

    def validate_building_model_temporal(
        self,
        building_model: BuildingModel,
        mcp_files: List[str],
        current_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Validate building model with temporal rules

        Args:
            building_model: Building model to validate
            mcp_files: List of MCP file paths
            current_time: Current time for temporal evaluation

        Returns:
            Validation results with temporal information
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        self.logger.info(f"Starting temporal validation at {current_time}")

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

        # Process temporal rules
        temporal_results = []
        for mcp_file in loaded_mcp_files:
            for rule in mcp_file.rules:
                # Check if this is a temporal rule
                temporal_condition = self._extract_temporal_condition(rule)

                if temporal_condition:
                    # Evaluate temporal condition
                    temporal_satisfied = self.evaluate_temporal_condition(
                        temporal_condition, current_time
                    )

                    if temporal_satisfied:
                        # Execute base rule
                        result = self.base_engine._execute_rule(rule, building_model)
                        temporal_results.append(
                            {
                                "rule_id": rule.rule_id,
                                "temporal_satisfied": True,
                                "current_time": current_time.isoformat(),
                                "result": result,
                            }
                        )
                    else:
                        # Temporal condition not satisfied
                        temporal_results.append(
                            {
                                "rule_id": rule.rule_id,
                                "temporal_satisfied": False,
                                "current_time": current_time.isoformat(),
                                "result": None,
                            }
                        )
                else:
                    # Regular rule, execute normally
                    result = self.base_engine._execute_rule(rule, building_model)
                    temporal_results.append(
                        {
                            "rule_id": rule.rule_id,
                            "temporal_satisfied": True,  # Always true for non-temporal rules
                            "current_time": current_time.isoformat(),
                            "result": result,
                        }
                    )

        return {
            "validation_time": current_time.isoformat(),
            "temporal_results": temporal_results,
            "total_rules": len(temporal_results),
            "temporal_rules_executed": len(
                [r for r in temporal_results if r["temporal_satisfied"]]
            ),
        }

    def _extract_temporal_condition(self, rule: MCPRule) -> Optional[TemporalCondition]:
        """Extract temporal condition from rule"""
        for condition in rule.conditions:
            if (
                condition.type == "temporal"
                or condition.property == "temporal_condition"
            ):
                if hasattr(condition, "value") and isinstance(condition.value, dict):
                    data = condition.value
                    return TemporalCondition(
                        operator=TemporalOperator(data.get("operator", "before")),
                        start_time=data.get("start_time"),
                        end_time=data.get("end_time"),
                        timezone=data.get("timezone", "UTC"),
                        business_hours_start=data.get("business_hours_start", "09:00"),
                        business_hours_end=data.get("business_hours_end", "17:00"),
                    )

        return None

    def get_temporal_schedule(
        self,
        mcp_files: List[str],
        start_date: datetime,
        end_date: datetime,
        interval_hours: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get temporal rule schedule for a date range

        Args:
            mcp_files: List of MCP file paths
            start_date: Start date for schedule
            end_date: End date for schedule
            interval_hours: Schedule interval in hours

        Returns:
            List of scheduled rule executions
        """
        schedule = []
        current = start_date

        while current <= end_date:
            # Validate at current time
            results = self.validate_building_model_temporal(
                BuildingModel(
                    building_id="schedule_test",
                    building_name="Schedule Test",
                    objects=[],
                ),
                mcp_files,
                current,
            )

            # Add to schedule if any temporal rules would execute
            temporal_rules = [
                r for r in results["temporal_results"] if r["temporal_satisfied"]
            ]
            if temporal_rules:
                schedule.append(
                    {
                        "time": current.isoformat(),
                        "rules": [r["rule_id"] for r in temporal_rules],
                        "count": len(temporal_rules),
                    }
                )

            current += timedelta(hours=interval_hours)

        return schedule
