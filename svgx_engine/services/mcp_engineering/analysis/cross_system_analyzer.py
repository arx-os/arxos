#!/usr/bin/env python3
"""
Cross-System Analysis Service

Impact analysis service for engineering systems across multiple disciplines.
Provides comprehensive analysis of how changes in one system affect others.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
import time
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ImpactLevel(Enum):
    """Impact levels for cross-system analysis."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class SystemInteraction(Enum):
    """Types of system interactions."""

    CONFLICT = "conflict"
    DEPENDENCY = "dependency"
    ENHANCEMENT = "enhancement"
    NEUTRAL = "neutral"


@dataclass
class SystemImpact:
    """Represents impact of one system on another."""

    source_system: str
    target_system: str
    impact_level: ImpactLevel
    interaction_type: SystemInteraction
    description: str
    details: Dict[str, Any]
    confidence_score: float


@dataclass
class CrossSystemAnalysisResult:
    """Result of cross-system analysis."""

    element_id: str
    system_type: str
    impacts: List[SystemImpact]
    conflicts: List[SystemImpact]
    dependencies: List[SystemImpact]
    enhancements: List[SystemImpact]
    analysis_time: float
    timestamp: datetime
    confidence_score: float
    analysis_details: Dict[str, Any]


class CrossSystemAnalyzer:
    """
    Cross-System Analyzer.

    Provides comprehensive impact analysis across engineering systems:
    - Electrical system impacts on other systems
    - HVAC system impacts on other systems
    - Plumbing system impacts on other systems
    - Structural system impacts on other systems
    - Multi-system coordination analysis
    """

    def __init__(self):
        """Initialize the cross-system analyzer."""
        self.interaction_rules = self._initialize_interaction_rules()
        self.impact_thresholds = self._initialize_impact_thresholds()

        logger.info("Cross-System Analyzer initialized")

    async def analyze_cross_system_impacts(
        self, element_data: Dict[str, Any]
    ) -> CrossSystemAnalysisResult:
        """
        Analyze cross-system impacts for a design element.

        Args:
            element_data: Design element data

        Returns:
            CrossSystemAnalysisResult: Cross-system analysis result
        """
        start_time = time.time()
        element_id = element_data.get("id", "unknown")
        system_type = element_data.get("system_type", "unknown")

        try:
            logger.info(
                f"Analyzing cross-system impacts for element {element_id} (system: {system_type})"
            )

            # Analyze impacts on other systems
            impacts = await self._analyze_system_impacts(element_data, system_type)

            # Categorize impacts
            conflicts = [
                imp
                for imp in impacts
                if imp.interaction_type == SystemInteraction.CONFLICT
            ]
            dependencies = [
                imp
                for imp in impacts
                if imp.interaction_type == SystemInteraction.DEPENDENCY
            ]
            enhancements = [
                imp
                for imp in impacts
                if imp.interaction_type == SystemInteraction.ENHANCEMENT
            ]

            analysis_time = time.time() - start_time

            # Calculate confidence score
            confidence_score = self._calculate_analysis_confidence(
                impacts, analysis_time
            )

            result = CrossSystemAnalysisResult(
                element_id=element_id,
                system_type=system_type,
                impacts=impacts,
                conflicts=conflicts,
                dependencies=dependencies,
                enhancements=enhancements,
                analysis_time=analysis_time,
                timestamp=datetime.utcnow(),
                confidence_score=confidence_score,
                analysis_details={
                    "total_impacts": len(impacts),
                    "critical_impacts": len(
                        [
                            imp
                            for imp in impacts
                            if imp.impact_level == ImpactLevel.CRITICAL
                        ]
                    ),
                    "high_impacts": len(
                        [imp for imp in impacts if imp.impact_level == ImpactLevel.HIGH]
                    ),
                    "systems_analyzed": list(
                        set([imp.target_system for imp in impacts])
                    ),
                },
            )

            logger.info(
                f"Cross-system analysis completed for {element_id} in {analysis_time:.3f}s"
            )
            return result

        except Exception as e:
            analysis_time = time.time() - start_time
            logger.error(
                f"Cross-system analysis failed for {element_id}: {e}", exc_info=True
            )

            return CrossSystemAnalysisResult(
                element_id=element_id,
                system_type=system_type,
                impacts=[],
                conflicts=[],
                dependencies=[],
                enhancements=[],
                analysis_time=analysis_time,
                timestamp=datetime.utcnow(),
                confidence_score=0.0,
                analysis_details={"error": str(e)},
            )

    async def _analyze_system_impacts(
        self, element_data: Dict[str, Any], source_system: str
    ) -> List[SystemImpact]:
        """Analyze impacts of a system on other systems."""
        impacts = []

        # Get all target systems
        target_systems = ["electrical", "hvac", "plumbing", "structural"]

        for target_system in target_systems:
            if target_system == source_system:
                continue

            try:
                impact = await self._analyze_system_interaction(
                    element_data, source_system, target_system
                )
                if impact:
                    impacts.append(impact)

            except Exception as e:
                logger.warning(
                    f"Failed to analyze {source_system} -> {target_system} impact: {e}"
                )

        return impacts

    async def _analyze_system_interaction(
        self, element_data: Dict[str, Any], source_system: str, target_system: str
    ) -> Optional[SystemImpact]:
        """Analyze interaction between two systems."""
        try:
            # Get interaction rules for this system pair
            rules = self.interaction_rules.get(f"{source_system}_{target_system}", [])

            impact_level = ImpactLevel.NONE
            interaction_type = SystemInteraction.NEUTRAL
            description = ""
            details = {}
            confidence_score = 0.0

            # Apply interaction rules
            for rule in rules:
                rule_result = await self._apply_interaction_rule(element_data, rule)
                if rule_result:
                    impact_level = max(impact_level, rule_result["impact_level"])
                    interaction_type = rule_result["interaction_type"]
                    description = rule_result["description"]
                    details.update(rule_result["details"])
                    confidence_score = max(confidence_score, rule_result["confidence"])

            if impact_level == ImpactLevel.NONE:
                return None

            return SystemImpact(
                source_system=source_system,
                target_system=target_system,
                impact_level=impact_level,
                interaction_type=interaction_type,
                description=description,
                details=details,
                confidence_score=confidence_score,
            )

        except Exception as e:
            logger.error(f"System interaction analysis failed: {e}")
            return None

    async def _apply_interaction_rule(
        self, element_data: Dict[str, Any], rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Apply a specific interaction rule."""
        try:
            rule_type = rule.get("type")

            if rule_type == "electrical_hvac":
                return await self._analyze_electrical_hvac_interaction(
                    element_data, rule
                )
            elif rule_type == "electrical_plumbing":
                return await self._analyze_electrical_plumbing_interaction(
                    element_data, rule
                )
            elif rule_type == "electrical_structural":
                return await self._analyze_electrical_structural_interaction(
                    element_data, rule
                )
            elif rule_type == "hvac_plumbing":
                return await self._analyze_hvac_plumbing_interaction(element_data, rule)
            elif rule_type == "hvac_structural":
                return await self._analyze_hvac_structural_interaction(
                    element_data, rule
                )
            elif rule_type == "plumbing_structural":
                return await self._analyze_plumbing_structural_interaction(
                    element_data, rule
                )
            else:
                return None

        except Exception as e:
            logger.error(f"Rule application failed: {e}")
            return None

    async def _analyze_electrical_hvac_interaction(
        self, element_data: Dict[str, Any], rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze electrical-HVAC interaction."""
        if element_data.get("system_type") != "electrical":
            return None

        # Check for electrical loads that affect HVAC
        electrical_load = element_data.get("electrical_load", 0)
        if electrical_load > 0:
            # Electrical loads generate heat that affects HVAC
            heat_generation = (
                electrical_load * 0.3
            )  # 30% of electrical load becomes heat

            if heat_generation > 1000:  # Watts
                return {
                    "impact_level": ImpactLevel.HIGH,
                    "interaction_type": SystemInteraction.DEPENDENCY,
                    "description": f"Electrical load of {electrical_load}W generates {heat_generation}W of heat affecting HVAC",
                    "details": {
                        "electrical_load": electrical_load,
                        "heat_generation": heat_generation,
                        "hvac_impact": "cooling_load_increase",
                    },
                    "confidence": 0.8,
                }

        return None

    async def _analyze_electrical_plumbing_interaction(
        self, element_data: Dict[str, Any], rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze electrical-plumbing interaction."""
        if element_data.get("system_type") != "electrical":
            return None

        # Check for electrical equipment near plumbing
        location = element_data.get("location", {})
        if location.get("near_water", False):
            return {
                "impact_level": ImpactLevel.CRITICAL,
                "interaction_type": SystemInteraction.CONFLICT,
                "description": "Electrical equipment near water requires special protection",
                "details": {
                    "safety_requirement": "GFCI_protection",
                    "code_section": "NEC 210.8",
                },
                "confidence": 0.9,
            }

        return None

    async def _analyze_electrical_structural_interaction(
        self, element_data: Dict[str, Any], rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze electrical-structural interaction."""
        if element_data.get("system_type") != "electrical":
            return None

        # Check for electrical penetrations through structural elements
        penetrations = element_data.get("penetrations", [])
        if penetrations:
            structural_impacts = []
            for penetration in penetrations:
                if penetration.get("through_structural", False):
                    structural_impacts.append(
                        {
                            "penetration_size": penetration.get("size"),
                            "structural_element": penetration.get("element_type"),
                            "reinforcement_required": True,
                        }
                    )

            if structural_impacts:
                return {
                    "impact_level": ImpactLevel.MEDIUM,
                    "interaction_type": SystemInteraction.DEPENDENCY,
                    "description": f"Electrical penetrations require structural coordination",
                    "details": {
                        "penetrations": structural_impacts,
                        "coordination_required": True,
                    },
                    "confidence": 0.7,
                }

        return None

    async def _analyze_hvac_plumbing_interaction(
        self, element_data: Dict[str, Any], rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze HVAC-plumbing interaction."""
        if element_data.get("system_type") != "hvac":
            return None

        # Check for HVAC equipment that requires plumbing connections
        equipment_type = element_data.get("equipment_type", "")
        if "chiller" in equipment_type.lower() or "boiler" in equipment_type.lower():
            return {
                "impact_level": ImpactLevel.HIGH,
                "interaction_type": SystemInteraction.DEPENDENCY,
                "description": f"{equipment_type} requires plumbing connections for water flow",
                "details": {
                    "equipment_type": equipment_type,
                    "plumbing_requirements": ["water_supply", "drainage", "valves"],
                },
                "confidence": 0.8,
            }

        return None

    async def _analyze_hvac_structural_interaction(
        self, element_data: Dict[str, Any], rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze HVAC-structural interaction."""
        if element_data.get("system_type") != "hvac":
            return None

        # Check for HVAC equipment loads on structure
        equipment_weight = element_data.get("equipment_weight", 0)
        if equipment_weight > 500:  # lbs
            return {
                "impact_level": ImpactLevel.MEDIUM,
                "interaction_type": SystemInteraction.DEPENDENCY,
                "description": f"HVAC equipment weighing {equipment_weight}lbs requires structural support",
                "details": {
                    "equipment_weight": equipment_weight,
                    "structural_requirement": "equipment_support",
                },
                "confidence": 0.7,
            }

        return None

    async def _analyze_plumbing_structural_interaction(
        self, element_data: Dict[str, Any], rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze plumbing-structural interaction."""
        if element_data.get("system_type") != "plumbing":
            return None

        # Check for plumbing penetrations through structural elements
        pipe_size = element_data.get("pipe_size", 0)
        if pipe_size > 2:  # inches
            return {
                "impact_level": ImpactLevel.MEDIUM,
                "interaction_type": SystemInteraction.DEPENDENCY,
                "description": f'Large pipe ({pipe_size}") requires structural coordination',
                "details": {
                    "pipe_size": pipe_size,
                    "structural_requirement": "penetration_coordination",
                },
                "confidence": 0.6,
            }

        return None

    def _initialize_interaction_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize interaction rules between systems."""
        return {
            "electrical_hvac": [
                {
                    "type": "electrical_hvac",
                    "description": "Electrical loads affect HVAC cooling",
                }
            ],
            "electrical_plumbing": [
                {
                    "type": "electrical_plumbing",
                    "description": "Electrical near water requires protection",
                }
            ],
            "electrical_structural": [
                {
                    "type": "electrical_structural",
                    "description": "Electrical penetrations affect structure",
                }
            ],
            "hvac_plumbing": [
                {
                    "type": "hvac_plumbing",
                    "description": "HVAC equipment requires plumbing connections",
                }
            ],
            "hvac_structural": [
                {
                    "type": "hvac_structural",
                    "description": "HVAC equipment loads affect structure",
                }
            ],
            "plumbing_structural": [
                {
                    "type": "plumbing_structural",
                    "description": "Plumbing penetrations affect structure",
                }
            ],
        }

    def _initialize_impact_thresholds(self) -> Dict[str, float]:
        """Initialize impact thresholds for different metrics."""
        return {
            "electrical_load_threshold": 1000,  # Watts
            "equipment_weight_threshold": 500,  # lbs
            "pipe_size_threshold": 2,  # inches
            "heat_generation_threshold": 1000,  # Watts
        }

    def _calculate_analysis_confidence(
        self, impacts: List[SystemImpact], analysis_time: float
    ) -> float:
        """Calculate confidence score for cross-system analysis."""
        if not impacts:
            return 0.5

        # Base confidence on number of impacts and analysis time
        base_confidence = 0.7

        # Increase confidence for more impacts (more comprehensive analysis)
        impact_bonus = min(len(impacts) * 0.05, 0.2)

        # Reduce confidence for long analysis times
        time_penalty = min(analysis_time / 5.0, 0.2)

        # Increase confidence for high-confidence impacts
        avg_confidence = sum(imp.confidence_score for imp in impacts) / len(impacts)
        confidence_bonus = avg_confidence * 0.1

        confidence = base_confidence + impact_bonus - time_penalty + confidence_bonus
        return max(0.0, min(1.0, confidence))

    def is_healthy(self) -> bool:
        """Check if the cross-system analyzer is healthy."""
        try:
            # Check if interaction rules are properly initialized
            if not self.interaction_rules:
                return False

            # Check if impact thresholds are properly initialized
            if not self.impact_thresholds:
                return False

            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
