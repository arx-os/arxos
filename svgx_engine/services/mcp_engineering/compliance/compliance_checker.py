#!/usr/bin/env python3
"""
Code Compliance Checker

Code compliance validation service for engineering standards including:
- NEC (National Electrical Code) for electrical systems
- ASHRAE (American Society of Heating, Refrigerating and Air-Conditioning Engineers) for HVAC
- IPC (International Plumbing Code) for plumbing systems
- IBC (International Building Code) for structural systems

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CodeStandard(Enum):
    """Engineering code standards."""

    NEC = "nec"  # National Electrical Code
    ASHRAE = "ashrae"  # American Society of Heating, Refrigerating and Air-Conditioning Engineers
    IPC = "ipc"  # International Plumbing Code
    IBC = "ibc"  # International Building Code


class ComplianceLevel(Enum):
    """Compliance levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ComplianceViolation:
    """Represents a code compliance violation."""

    code_section: str
    description: str
    level: ComplianceLevel
    standard: CodeStandard
    element_id: str
    details: Dict[str, Any]


@dataclass
class ComplianceResult:
    """Result of code compliance checking."""

    is_compliant: bool
    confidence_score: float
    violations: List[ComplianceViolation]
    warnings: List[str]
    suggestions: List[str]
    compliance_time: float
    timestamp: datetime
    element_id: str
    standards_checked: List[CodeStandard]
    compliance_details: Dict[str, Any]


class CodeComplianceChecker:
    """
    Code Compliance Checker.

    Provides comprehensive code compliance validation for engineering standards:
    - NEC (National Electrical Code) for electrical systems
    - ASHRAE for HVAC systems
    - IPC for plumbing systems
    - IBC for structural systems
    """

    def __init__(self):
        """Initialize the code compliance checker."""
        self.nec_checker = NECComplianceChecker()
        self.ashrae_checker = ASHRAEComplianceChecker()
        self.ipc_checker = IPCComplianceChecker()
        self.ibc_checker = IBCComplianceChecker()

        logger.info("Code Compliance Checker initialized")

    async def check_compliance(self, element_data: Dict[str, Any]) -> ComplianceResult:
        """
        Check code compliance for a design element.

        Args:
            element_data: Design element data

        Returns:
            ComplianceResult: Compliance checking result
        """
        start_time = time.time()
        element_id = element_data.get("id", "unknown")
        system_type = element_data.get("system_type", "unknown")

        try:
            logger.info(
                f"Checking compliance for element {element_id} (system: {system_type})"
            )

            # Determine which standards to check based on system type
            standards_to_check = self._get_standards_for_system(system_type)

            all_violations = []
            all_warnings = []
            all_suggestions = []
            compliance_details = {}

            # Check compliance for each applicable standard
            for standard in standards_to_check:
                try:
                    if standard == CodeStandard.NEC:
                        result = await self.nec_checker.check_compliance(element_data)
                    elif standard == CodeStandard.ASHRAE:
                        result = await self.ashrae_checker.check_compliance(
                            element_data
                        )
                    elif standard == CodeStandard.IPC:
                        result = await self.ipc_checker.check_compliance(element_data)
                    elif standard == CodeStandard.IBC:
                        result = await self.ibc_checker.check_compliance(element_data)
                    else:
                        continue

                    all_violations.extend(result.get("violations", []))
                    all_warnings.extend(result.get("warnings", []))
                    all_suggestions.extend(result.get("suggestions", []))
                    compliance_details[standard.value] = result.get("details", {})

                except Exception as e:
                    logger.warning(f"Compliance check for {standard.value} failed: {e}")
                    all_warnings.append(
                        f"Compliance check for {standard.value} failed: {str(e)}"
                    )

            compliance_time = time.time() - start_time

            # Determine overall compliance
            critical_violations = [
                v for v in all_violations if v.level == ComplianceLevel.CRITICAL
            ]
            is_compliant = len(critical_violations) == 0

            # Calculate confidence score
            confidence_score = self._calculate_compliance_confidence(
                len(all_violations), len(standards_to_check), compliance_time
            )

            result = ComplianceResult(
                is_compliant=is_compliant,
                confidence_score=confidence_score,
                violations=all_violations,
                warnings=all_warnings,
                suggestions=all_suggestions,
                compliance_time=compliance_time,
                timestamp=datetime.utcnow(),
                element_id=element_id,
                standards_checked=standards_to_check,
                compliance_details=compliance_details,
            )

            logger.info(
                f"Compliance check completed for {element_id} in {compliance_time:.3f}s"
            )
            return result

        except Exception as e:
            compliance_time = time.time() - start_time
            logger.error(
                f"Compliance check failed for {element_id}: {e}", exc_info=True
            )

            return ComplianceResult(
                is_compliant=False,
                confidence_score=0.0,
                violations=[],
                warnings=[f"Compliance check failed: {str(e)}"],
                suggestions=[],
                compliance_time=compliance_time,
                timestamp=datetime.utcnow(),
                element_id=element_id,
                standards_checked=[],
                compliance_details={},
            )

    def _get_standards_for_system(self, system_type: str) -> List[CodeStandard]:
        """Get applicable standards for a system type."""
        if system_type == "electrical":
            return [CodeStandard.NEC]
        elif system_type == "hvac":
            return [CodeStandard.ASHRAE]
        elif system_type == "plumbing":
            return [CodeStandard.IPC]
        elif system_type == "structural":
            return [CodeStandard.IBC]
        elif system_type == "multi_system":
            return [
                CodeStandard.NEC,
                CodeStandard.ASHRAE,
                CodeStandard.IPC,
                CodeStandard.IBC,
            ]
        else:
            # Default to all standards
            return [
                CodeStandard.NEC,
                CodeStandard.ASHRAE,
                CodeStandard.IPC,
                CodeStandard.IBC,
            ]

    def _calculate_compliance_confidence(
        self, violation_count: int, standards_count: int, compliance_time: float
    ) -> float:
        """Calculate confidence score for compliance checking."""
        # Base confidence on violation count and standards checked
        base_confidence = 0.9

        # Reduce confidence for violations
        violation_penalty = min(violation_count * 0.1, 0.5)

        # Reduce confidence for long processing times
        time_penalty = min(compliance_time / 10.0, 0.2)

        # Increase confidence for multiple standards checked
        standards_bonus = min(standards_count * 0.05, 0.1)

        confidence = (
            base_confidence - violation_penalty - time_penalty + standards_bonus
        )
        return max(0.0, min(1.0, confidence))

    def is_healthy(self) -> bool:
        """Check if the compliance checker is healthy."""
        try:
            checkers = [
                self.nec_checker,
                self.ashrae_checker,
                self.ipc_checker,
                self.ibc_checker,
            ]

            for checker in checkers:
                if not hasattr(checker, "is_healthy"):
                    continue
                if not checker.is_healthy():
                    return False

            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


class NECComplianceChecker:
    """NEC (National Electrical Code) compliance checker."""

    def __init__(self):
        """Initialize NEC compliance checker."""
        self.standard = CodeStandard.NEC
        logger.info("NEC Compliance Checker initialized")

    async def check_compliance(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check NEC compliance for electrical elements."""
        violations = []
        warnings = []
        suggestions = []
        details = {}

        try:
            # Check wire sizing
            if "wire_size" in element_data:
                wire_size = element_data["wire_size"]
                current_rating = element_data.get("current_rating", 0)

                if wire_size < self._get_minimum_wire_size(current_rating):
                    violations.append(
                        ComplianceViolation(
                            code_section="NEC 310.16",
                            description=f"Wire size {wire_size} AWG is too small for {current_rating}A load",
                            level=ComplianceLevel.CRITICAL,
                            standard=self.standard,
                            element_id=element_data.get("id", "unknown"),
                            details={
                                "wire_size": wire_size,
                                "current_rating": current_rating,
                            },
                        )
                    )

            # Check circuit protection
            if "circuit_breaker" in element_data:
                breaker_rating = element_data["circuit_breaker"]
                wire_size = element_data.get("wire_size", 0)

                if breaker_rating > self._get_max_breaker_rating(wire_size):
                    violations.append(
                        ComplianceViolation(
                            code_section="NEC 240.4",
                            description=f"Circuit breaker {breaker_rating}A exceeds maximum for wire size {wire_size} AWG",
                            level=ComplianceLevel.CRITICAL,
                            standard=self.standard,
                            element_id=element_data.get("id", "unknown"),
                            details={
                                "breaker_rating": breaker_rating,
                                "wire_size": wire_size,
                            },
                        )
                    )

            # Check grounding
            if "grounding" not in element_data or not element_data["grounding"]:
                warnings.append("Consider adding proper grounding per NEC 250")
                suggestions.append("Add grounding conductor sized per NEC 250.122")

            details["nec_version"] = "2023"
            details["checks_performed"] = [
                "wire_sizing",
                "circuit_protection",
                "grounding",
            ]

        except Exception as e:
            logger.error(f"NEC compliance check failed: {e}")
            warnings.append(f"NEC compliance check failed: {str(e)}")

        return {
            "violations": violations,
            "warnings": warnings,
            "suggestions": suggestions,
            "details": details,
        }

    def _get_minimum_wire_size(self, current_rating: float) -> int:
        """Get minimum wire size for current rating."""
        # Simplified NEC wire sizing table
        if current_rating <= 15:
            return 14
        elif current_rating <= 20:
            return 12
        elif current_rating <= 30:
            return 10
        elif current_rating <= 40:
            return 8
        elif current_rating <= 55:
            return 6
        else:
            return 4

    def _get_max_breaker_rating(self, wire_size: int) -> int:
        """Get maximum circuit breaker rating for wire size."""
        # Simplified NEC breaker sizing table
        if wire_size >= 14:
            return 15
        elif wire_size >= 12:
            return 20
        elif wire_size >= 10:
            return 30
        elif wire_size >= 8:
            return 40
        else:
            return 60

    def is_healthy(self) -> bool:
        """Check if NEC checker is healthy."""
        return True


class ASHRAEComplianceChecker:
    """ASHRAE compliance checker."""

    def __init__(self):
        """Initialize ASHRAE compliance checker."""
        self.standard = CodeStandard.ASHRAE
        logger.info("ASHRAE Compliance Checker initialized")

    async def check_compliance(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check ASHRAE compliance for HVAC elements."""
        violations = []
        warnings = []
        suggestions = []
        details = {}

        try:
            # Check duct sizing
            if "duct_size" in element_data:
                duct_size = element_data["duct_size"]
                airflow = element_data.get("airflow", 0)

                if duct_size < self._get_minimum_duct_size(airflow):
                    violations.append(
                        ComplianceViolation(
                            code_section="ASHRAE 62.1",
                            description=f"Duct size {duct_size} is too small for {airflow} CFM airflow",
                            level=ComplianceLevel.CRITICAL,
                            standard=self.standard,
                            element_id=element_data.get("id", "unknown"),
                            details={"duct_size": duct_size, "airflow": airflow},
                        )
                    )

            # Check ventilation rates
            if "space_type" in element_data:
                space_type = element_data["space_type"]
                ventilation_rate = element_data.get("ventilation_rate", 0)
                required_rate = self._get_required_ventilation_rate(space_type)

                if ventilation_rate < required_rate:
                    violations.append(
                        ComplianceViolation(
                            code_section="ASHRAE 62.1",
                            description=f"Ventilation rate {ventilation_rate} CFM/person below required {required_rate} CFM/person for {space_type}",
                            level=ComplianceLevel.CRITICAL,
                            standard=self.standard,
                            element_id=element_data.get("id", "unknown"),
                            details={
                                "ventilation_rate": ventilation_rate,
                                "required_rate": required_rate,
                                "space_type": space_type,
                            },
                        )
                    )

            details["ashrae_version"] = "62.1-2022"
            details["checks_performed"] = ["duct_sizing", "ventilation_rates"]

        except Exception as e:
            logger.error(f"ASHRAE compliance check failed: {e}")
            warnings.append(f"ASHRAE compliance check failed: {str(e)}")

        return {
            "violations": violations,
            "warnings": warnings,
            "suggestions": suggestions,
            "details": details,
        }

    def _get_minimum_duct_size(self, airflow: float) -> float:
        """Get minimum duct size for airflow."""
        # Simplified ASHRAE duct sizing
        if airflow <= 100:
            return 6.0
        elif airflow <= 200:
            return 8.0
        elif airflow <= 500:
            return 10.0
        else:
            return 12.0

    def _get_required_ventilation_rate(self, space_type: str) -> float:
        """Get required ventilation rate for space type."""
        # Simplified ASHRAE ventilation rates
        rates = {
            "office": 20.0,
            "conference": 20.0,
            "classroom": 10.0,
            "restaurant": 7.5,
            "retail": 15.0,
            "residential": 7.5,
        }
        return rates.get(space_type.lower(), 20.0)

    def is_healthy(self) -> bool:
        """Check if ASHRAE checker is healthy."""
        return True


class IPCComplianceChecker:
    """IPC (International Plumbing Code) compliance checker."""

    def __init__(self):
        """Initialize IPC compliance checker."""
        self.standard = CodeStandard.IPC
        logger.info("IPC Compliance Checker initialized")

    async def check_compliance(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check IPC compliance for plumbing elements."""
        violations = []
        warnings = []
        suggestions = []
        details = {}

        try:
            # Check pipe sizing
            if "pipe_size" in element_data:
                pipe_size = element_data["pipe_size"]
                fixture_units = element_data.get("fixture_units", 0)

                if pipe_size < self._get_minimum_pipe_size(fixture_units):
                    violations.append(
                        ComplianceViolation(
                            code_section="IPC 709.1",
                            description=f"Pipe size {pipe_size} is too small for {fixture_units} fixture units",
                            level=ComplianceLevel.CRITICAL,
                            standard=self.standard,
                            element_id=element_data.get("id", "unknown"),
                            details={
                                "pipe_size": pipe_size,
                                "fixture_units": fixture_units,
                            },
                        )
                    )

            # Check venting
            if "vent_size" in element_data:
                vent_size = element_data["vent_size"]
                drain_size = element_data.get("drain_size", 0)

                if vent_size < self._get_minimum_vent_size(drain_size):
                    violations.append(
                        ComplianceViolation(
                            code_section="IPC 906.1",
                            description=f"Vent size {vent_size} is too small for drain size {drain_size}",
                            level=ComplianceLevel.CRITICAL,
                            standard=self.standard,
                            element_id=element_data.get("id", "unknown"),
                            details={"vent_size": vent_size, "drain_size": drain_size},
                        )
                    )

            details["ipc_version"] = "2021"
            details["checks_performed"] = ["pipe_sizing", "venting"]

        except Exception as e:
            logger.error(f"IPC compliance check failed: {e}")
            warnings.append(f"IPC compliance check failed: {str(e)}")

        return {
            "violations": violations,
            "warnings": warnings,
            "suggestions": suggestions,
            "details": details,
        }

    def _get_minimum_pipe_size(self, fixture_units: int) -> float:
        """Get minimum pipe size for fixture units."""
        # Simplified IPC pipe sizing
        if fixture_units <= 8:
            return 2.0
        elif fixture_units <= 24:
            return 2.5
        elif fixture_units <= 84:
            return 3.0
        else:
            return 4.0

    def _get_minimum_vent_size(self, drain_size: float) -> float:
        """Get minimum vent size for drain size."""
        # Simplified IPC vent sizing
        if drain_size <= 2.0:
            return 1.25
        elif drain_size <= 3.0:
            return 1.5
        else:
            return 2.0

    def is_healthy(self) -> bool:
        """Check if IPC checker is healthy."""
        return True


class IBCComplianceChecker:
    """IBC (International Building Code) compliance checker."""

    def __init__(self):
        """Initialize IBC compliance checker."""
        self.standard = CodeStandard.IBC
        logger.info("IBC Compliance Checker initialized")

    async def check_compliance(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check IBC compliance for structural elements."""
        violations = []
        warnings = []
        suggestions = []
        details = {}

        try:
            # Check beam sizing
            if "beam_size" in element_data:
                beam_size = element_data["beam_size"]
                span_length = element_data.get("span_length", 0)
                load = element_data.get("load", 0)

                if beam_size < self._get_minimum_beam_size(span_length, load):
                    violations.append(
                        ComplianceViolation(
                            code_section="IBC 1607",
                            description=f"Beam size {beam_size} is too small for span {span_length}ft with load {load}psf",
                            level=ComplianceLevel.CRITICAL,
                            standard=self.standard,
                            element_id=element_data.get("id", "unknown"),
                            details={
                                "beam_size": beam_size,
                                "span_length": span_length,
                                "load": load,
                            },
                        )
                    )

            # Check column sizing
            if "column_size" in element_data:
                column_size = element_data["column_size"]
                height = element_data.get("height", 0)
                load = element_data.get("load", 0)

                if column_size < self._get_minimum_column_size(height, load):
                    violations.append(
                        ComplianceViolation(
                            code_section="IBC 1607",
                            description=f"Column size {column_size} is too small for height {height}ft with load {load}kips",
                            level=ComplianceLevel.CRITICAL,
                            standard=self.standard,
                            element_id=element_data.get("id", "unknown"),
                            details={
                                "column_size": column_size,
                                "height": height,
                                "load": load,
                            },
                        )
                    )

            details["ibc_version"] = "2021"
            details["checks_performed"] = ["beam_sizing", "column_sizing"]

        except Exception as e:
            logger.error(f"IBC compliance check failed: {e}")
            warnings.append(f"IBC compliance check failed: {str(e)}")

        return {
            "violations": violations,
            "warnings": warnings,
            "suggestions": suggestions,
            "details": details,
        }

    def _get_minimum_beam_size(self, span_length: float, load: float) -> float:
        """Get minimum beam size for span and load."""
        # Simplified IBC beam sizing
        required_depth = span_length * 0.04 + load * 0.001
        return max(8.0, required_depth)

    def _get_minimum_column_size(self, height: float, load: float) -> float:
        """Get minimum column size for height and load."""
        # Simplified IBC column sizing
        required_size = height * 0.1 + load * 0.01
        return max(6.0, required_size)

    def is_healthy(self) -> bool:
        """Check if IBC checker is healthy."""
        return True
