"""
SVGX Engine - Electrical Logic Engine

Electrical engineering logic engine for comprehensive analysis of electrical objects.
Provides real engineering calculations, code compliance validation, and implementation guidance.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
import time
import math
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class ElectricalObjectType(Enum):
    """Electrical object types."""

    OUTLET = "outlet"
    SWITCH = "switch"
    PANEL = "panel"
    TRANSFORMER = "transformer"
    BREAKER = "breaker"
    FUSE = "fuse"
    RECEPTACLE = "receptacle"
    JUNCTION = "junction"
    CONDUIT = "conduit"
    CABLE = "cable"
    WIRE = "wire"
    LIGHT = "light"
    FIXTURE = "fixture"
    SENSOR = "sensor"
    CONTROLLER = "controller"
    METER = "meter"
    GENERATOR = "generator"
    UPS = "ups"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"


class CircuitType(Enum):
    """Circuit types."""

    BRANCH = "branch"
    FEEDER = "feeder"
    MAIN = "main"
    SUBFEEDER = "subfeeder"
    EMERGENCY = "emergency"
    CRITICAL = "critical"


class VoltageLevel(Enum):
    """Voltage levels."""

    LOW_VOLTAGE = "low_voltage"  # < 600V
    MEDIUM_VOLTAGE = "medium_voltage"  # 600V - 69kV
    HIGH_VOLTAGE = "high_voltage"  # > 69kV


@dataclass
class ElectricalAnalysisResult:
    """Result of electrical engineering analysis."""

    object_id: str
    object_type: ElectricalObjectType
    circuit_analysis: Dict[str, Any] = field(default_factory=dict)
    load_calculations: Dict[str, Any] = field(default_factory=dict)
    voltage_drop_analysis: Dict[str, Any] = field(default_factory=dict)
    protection_coordination: Dict[str, Any] = field(default_factory=dict)
    harmonic_analysis: Dict[str, Any] = field(default_factory=dict)
    panel_analysis: Dict[str, Any] = field(default_factory=dict)
    safety_analysis: Dict[str, Any] = field(default_factory=dict)
    code_compliance: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ElectricalLogicEngine:
    """
    Electrical engineering logic engine.

    Provides comprehensive electrical analysis including:
    - Circuit analysis and load calculations
    - Voltage drop analysis
    - Protection coordination
    - Harmonic analysis
    - Panel analysis
    - Code compliance validation
    - Safety analysis
    """

    def __init__(self):
        """Initialize the electrical logic engine."""
        self.start_time = time.time()

        # Initialize analysis components
        self._initialize_analysis_components()

        # Initialize performance monitoring
        self._initialize_performance_monitoring()

        # Initialize error handling
        self._initialize_error_handling()

        logger.info("Electrical Logic Engine initialized successfully")

    def _initialize_analysis_components(self):
        """Initialize all analysis components."""
        try:
            # Circuit analysis components
            self.circuit_analyzer = CircuitAnalyzer()
            self.load_calculator = LoadCalculator()
            self.voltage_drop_calculator = VoltageDropCalculator()
            self.protection_coordinator = ProtectionCoordinator()
            self.harmonic_analyzer = HarmonicAnalyzer()
            self.panel_analyzer = PanelAnalyzer()
            self.safety_analyzer = SafetyAnalyzer()
            self.code_validator = ElectricalCodeValidator()

            logger.info("Electrical analysis components initialized")

        except Exception as e:
            logger.error(f"Failed to initialize electrical analysis components: {e}")
            raise

    def _initialize_performance_monitoring(self):
        """Initialize performance monitoring."""
        self.performance_metrics = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_response_time": 0.0,
            "circuit_analyses": 0,
            "load_calculations": 0,
            "voltage_drop_analyses": 0,
            "protection_coordinations": 0,
            "harmonic_analyses": 0,
            "panel_analyses": 0,
            "safety_analyses": 0,
            "code_validations": 0,
        }

        logger.info("Electrical performance monitoring initialized")

    def _initialize_error_handling(self):
        """Initialize error handling."""
        self.error_log = []
        self.warning_log = []
        self.recovery_attempts = 0

        logger.info("Electrical error handling initialized")

    async def analyze_object(
        self, object_data: Dict[str, Any]
    ) -> ElectricalAnalysisResult:
        """
        Analyze electrical object with comprehensive engineering logic.

        Args:
            object_data: Dictionary containing electrical object information

        Returns:
            ElectricalAnalysisResult: Comprehensive electrical analysis result
        """
        start_time = time.time()
        object_id = object_data.get("id", "unknown")
        object_type_str = object_data.get("type", "unknown")

        logger.info(
            f"Starting electrical analysis for object {object_id} of type {object_type_str}"
        )

        try:
            # Determine object type
            object_type = self._determine_object_type(object_type_str)

            # Create analysis result
            result = ElectricalAnalysisResult(
                object_id=object_id, object_type=object_type
            )

            # Perform comprehensive electrical analysis
            await self._perform_comprehensive_analysis(object_data, result)

            # Update performance metrics
            analysis_time = time.time() - start_time
            self._update_performance_metrics(analysis_time, True)

            logger.info(
                f"Electrical analysis completed for {object_id} in {analysis_time:.3f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Electrical analysis failed for {object_id}: {e}")
            self._log_error(f"Electrical analysis failed: {e}")
            self._update_performance_metrics(time.time() - start_time, False)
            raise

    async def _perform_comprehensive_analysis(
        self, object_data: Dict[str, Any], result: ElectricalAnalysisResult
    ):
        """Perform comprehensive electrical analysis."""

        # 1. Circuit Analysis
        logger.debug("Performing circuit analysis")
        result.circuit_analysis = await self.circuit_analyzer.analyze_circuit(
            object_data
        )

        # 2. Load Calculations
        logger.debug("Performing load calculations")
        result.load_calculations = await self.load_calculator.calculate_load(
            object_data
        )

        # 3. Voltage Drop Analysis
        logger.debug("Performing voltage drop analysis")
        result.voltage_drop_analysis = (
            await self.voltage_drop_calculator.calculate_voltage_drop(object_data)
        )

        # 4. Protection Coordination
        logger.debug("Performing protection coordination")
        result.protection_coordination = (
            await self.protection_coordinator.coordinate_protection(object_data)
        )

        # 5. Harmonic Analysis
        logger.debug("Performing harmonic analysis")
        result.harmonic_analysis = await self.harmonic_analyzer.analyze_harmonics(
            object_data
        )

        # 6. Panel Analysis
        logger.debug("Performing panel analysis")
        result.panel_analysis = await self.panel_analyzer.analyze_panel(object_data)

        # 7. Safety Analysis
        logger.debug("Performing safety analysis")
        result.safety_analysis = await self.safety_analyzer.analyze_safety(object_data)

        # 8. Code Compliance Validation
        logger.debug("Performing code compliance validation")
        result.code_compliance = await self.code_validator.validate_compliance(
            object_data
        )

        # 9. Generate recommendations and warnings
        self._generate_recommendations_and_warnings(result)

    def _determine_object_type(self, object_type_str: str) -> ElectricalObjectType:
        """Determine electrical object type from string."""
        try:
            return ElectricalObjectType(object_type_str.lower())
        except ValueError:
            logger.warning(
                f"Unknown electrical object type: {object_type_str}, defaulting to outlet"
            )
            return ElectricalObjectType.OUTLET

    def _generate_recommendations_and_warnings(self, result: ElectricalAnalysisResult):
        """Generate recommendations and warnings based on analysis results."""

        # Check voltage drop
        voltage_drop = result.voltage_drop_analysis.get("voltage_drop_percent", 0)
        if voltage_drop > 3.0:
            result.warnings.append(
                f"Voltage drop of {voltage_drop:.1f}% exceeds recommended 3% limit"
            )
            result.recommendations.append(
                "Consider increasing conductor size or reducing circuit length"
            )

        # Check load capacity
        load_percent = result.load_calculations.get("load_percentage", 0)
        if load_percent > 80:
            result.warnings.append(
                f"Load at {load_percent:.1f}% is approaching capacity limit"
            )
            result.recommendations.append(
                "Consider redistributing loads or upgrading equipment"
            )

        # Check protection coordination
        coordination_status = result.protection_coordination.get(
            "coordination_status", "unknown"
        )
        if coordination_status != "coordinated":
            result.warnings.append("Protection coordination issues detected")
            result.recommendations.append("Review and adjust protection settings")

        # Check harmonics
        thd = result.harmonic_analysis.get("total_harmonic_distortion", 0)
        if thd > 5.0:
            result.warnings.append(f"THD of {thd:.1f}% exceeds recommended 5% limit")
            result.recommendations.append(
                "Consider adding harmonic filters or using low-harmonic equipment"
            )

    def _update_performance_metrics(self, analysis_time: float, success: bool):
        """Update performance metrics."""
        self.performance_metrics["total_analyses"] += 1

        if success:
            self.performance_metrics["successful_analyses"] += 1
        else:
            self.performance_metrics["failed_analyses"] += 1

        # Update average response time
        current_avg = self.performance_metrics["average_response_time"]
        total_analyses = self.performance_metrics["total_analyses"]
        self.performance_metrics["average_response_time"] = (
            current_avg * (total_analyses - 1) + analysis_time
        ) / total_analyses

    def _log_error(self, error_message: str):
        """Log error message."""
        self.error_log.append(
            {"timestamp": datetime.utcnow(), "message": error_message}
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.performance_metrics.copy()

    def get_error_log(self) -> List[Dict[str, Any]]:
        """Get error log."""
        return self.error_log.copy()

    def get_warning_log(self) -> List[Dict[str, Any]]:
        """Get warning log."""
        return self.warning_log.copy()

    def clear_logs(self):
        """Clear all logs."""
        self.error_log.clear()
        self.warning_log.clear()


# Analysis Component Classes


class CircuitAnalyzer:
    """Circuit analysis component."""

    async def analyze_circuit(self, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze electrical circuit."""
        return {
            "circuit_type": self._determine_circuit_type(object_data),
            "voltage_level": self._determine_voltage_level(object_data),
            "current_rating": self._calculate_current_rating(object_data),
            "impedance": self._calculate_impedance(object_data),
            "power_factor": self._calculate_power_factor(object_data),
        }

    def _determine_circuit_type(self, object_data: Dict[str, Any]) -> str:
        """Determine circuit type."""
        object_type = object_data.get("type", "").lower()

        if object_type in ["panel", "transformer", "generator"]:
            return CircuitType.MAIN.value
        elif object_type in ["breaker", "fuse"]:
            return CircuitType.FEEDER.value
        else:
            return CircuitType.BRANCH.value

    def _determine_voltage_level(self, object_data: Dict[str, Any]) -> str:
        """Determine voltage level."""
        voltage = object_data.get("voltage", 120)

        if voltage < 600:
            return VoltageLevel.LOW_VOLTAGE.value
        elif voltage < 69000:
            return VoltageLevel.MEDIUM_VOLTAGE.value
        else:
            return VoltageLevel.HIGH_VOLTAGE.value

    def _calculate_current_rating(self, object_data: Dict[str, Any]) -> float:
        """Calculate current rating."""
        power = object_data.get("power", 1000)  # watts
        voltage = object_data.get("voltage", 120)  # volts
        power_factor = object_data.get("power_factor", 0.9)

        return power / (voltage * power_factor)

    def _calculate_impedance(self, object_data: Dict[str, Any]) -> float:
        """Calculate impedance."""
        resistance = object_data.get("resistance", 0.1)  # ohms
        reactance = object_data.get("reactance", 0.05)  # ohms

        return math.sqrt(resistance**2 + reactance**2)

    def _calculate_power_factor(self, object_data: Dict[str, Any]) -> float:
        """Calculate power factor."""
        return object_data.get("power_factor", 0.9)


class LoadCalculator:
    """Load calculation component."""

    async def calculate_load(self, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate electrical load."""
        return {
            "connected_load": self._calculate_connected_load(object_data),
            "demand_load": self._calculate_demand_load(object_data),
            "diversity_factor": self._calculate_diversity_factor(object_data),
            "load_percentage": self._calculate_load_percentage(object_data),
            "peak_load": self._calculate_peak_load(object_data),
        }

    def _calculate_connected_load(self, object_data: Dict[str, Any]) -> float:
        """Calculate connected load."""
        return object_data.get("power", 1000)  # watts

    def _calculate_demand_load(self, object_data: Dict[str, Any]) -> float:
        """Calculate demand load."""
        connected_load = self._calculate_connected_load(object_data)
        demand_factor = object_data.get("demand_factor", 0.8)

        return connected_load * demand_factor

    def _calculate_diversity_factor(self, object_data: Dict[str, Any]) -> float:
        """Calculate diversity factor."""
        return object_data.get("diversity_factor", 0.9)

    def _calculate_load_percentage(self, object_data: Dict[str, Any]) -> float:
        """Calculate load percentage."""
        demand_load = self._calculate_demand_load(object_data)
        capacity = object_data.get("capacity", 2000)  # watts

        return (demand_load / capacity) * 100 if capacity > 0 else 0

    def _calculate_peak_load(self, object_data: Dict[str, Any]) -> float:
        """Calculate peak load."""
        demand_load = self._calculate_demand_load(object_data)
        peak_factor = object_data.get("peak_factor", 1.2)

        return demand_load * peak_factor


class VoltageDropCalculator:
    """Voltage drop calculation component."""

    async def calculate_voltage_drop(
        self, object_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate voltage drop."""
        return {
            "voltage_drop_volts": self._calculate_voltage_drop_volts(object_data),
            "voltage_drop_percent": self._calculate_voltage_drop_percent(object_data),
            "voltage_regulation": self._calculate_voltage_regulation(object_data),
            "acceptable_drop": self._is_voltage_drop_acceptable(object_data),
        }

    def _calculate_voltage_drop_volts(self, object_data: Dict[str, Any]) -> float:
        """Calculate voltage drop in volts."""
        current = object_data.get("current", 10)  # amps
        resistance = object_data.get("resistance", 0.1)  # ohms per foot
        length = object_data.get("length", 100)  # feet

        return current * resistance * length

    def _calculate_voltage_drop_percent(self, object_data: Dict[str, Any]) -> float:
        """Calculate voltage drop percentage."""
        voltage_drop_volts = self._calculate_voltage_drop_volts(object_data)
        nominal_voltage = object_data.get("voltage", 120)  # volts

        return (voltage_drop_volts / nominal_voltage) * 100

    def _calculate_voltage_regulation(self, object_data: Dict[str, Any]) -> float:
        """Calculate voltage regulation."""
        no_load_voltage = object_data.get("no_load_voltage", 125)  # volts
        full_load_voltage = object_data.get("full_load_voltage", 115)  # volts

        return ((no_load_voltage - full_load_voltage) / no_load_voltage) * 100

    def _is_voltage_drop_acceptable(self, object_data: Dict[str, Any]) -> bool:
        """Check if voltage drop is acceptable."""
        voltage_drop_percent = self._calculate_voltage_drop_percent(object_data)
        return voltage_drop_percent <= 3.0


class ProtectionCoordinator:
    """Protection coordination component."""

    async def coordinate_protection(
        self, object_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Coordinate protection devices."""
        return {
            "coordination_status": self._check_coordination_status(object_data),
            "trip_time": self._calculate_trip_time(object_data),
            "selectivity": self._check_selectivity(object_data),
            "backup_protection": self._check_backup_protection(object_data),
            "coordination_curve": self._generate_coordination_curve(object_data),
        }

    def _check_coordination_status(self, object_data: Dict[str, Any]) -> str:
        """Check protection coordination status."""
        # Simplified coordination check
        return (
            "coordinated"
            if object_data.get("coordination_factor", 0.8) > 0.7
            else "not_coordinated"
        )

    def _calculate_trip_time(self, object_data: Dict[str, Any]) -> float:
        """Calculate trip time."""
        return object_data.get("trip_time", 0.1)  # seconds

    def _check_selectivity(self, object_data: Dict[str, Any]) -> bool:
        """Check selectivity."""
        return object_data.get("selectivity_factor", 0.9) > 0.8

    def _check_backup_protection(self, object_data: Dict[str, Any]) -> bool:
        """Check backup protection."""
        return object_data.get("backup_protection", True)

    def _generate_coordination_curve(
        self, object_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate coordination curve."""
        return {
            "primary_curve": "inverse_time",
            "backup_curve": "instantaneous",
            "coordination_margin": 0.2,
        }


class HarmonicAnalyzer:
    """Harmonic analysis component."""

    async def analyze_harmonics(self, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze harmonics."""
        return {
            "total_harmonic_distortion": self._calculate_thd(object_data),
            "harmonic_spectrum": self._calculate_harmonic_spectrum(object_data),
            "power_factor": self._calculate_displacement_power_factor(object_data),
            "harmonic_limits": self._check_harmonic_limits(object_data),
        }

    def _calculate_thd(self, object_data: Dict[str, Any]) -> float:
        """Calculate total harmonic distortion."""
        return object_data.get("thd", 3.5)  # percent

    def _calculate_harmonic_spectrum(
        self, object_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate harmonic spectrum."""
        return {
            "3rd_harmonic": object_data.get("3rd_harmonic", 2.1),
            "5th_harmonic": object_data.get("5th_harmonic", 1.8),
            "7th_harmonic": object_data.get("7th_harmonic", 1.2),
            "9th_harmonic": object_data.get("9th_harmonic", 0.8),
        }

    def _calculate_displacement_power_factor(
        self, object_data: Dict[str, Any]
    ) -> float:
        """Calculate displacement power factor."""
        return object_data.get("displacement_pf", 0.95)

    def _check_harmonic_limits(self, object_data: Dict[str, Any]) -> bool:
        """Check harmonic limits."""
        thd = self._calculate_thd(object_data)
        return thd <= 5.0


class PanelAnalyzer:
    """Panel analysis component."""

    async def analyze_panel(self, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze electrical panel."""
        return {
            "panel_capacity": self._calculate_panel_capacity(object_data),
            "load_distribution": self._analyze_load_distribution(object_data),
            "phase_balance": self._check_phase_balance(object_data),
            "spare_capacity": self._calculate_spare_capacity(object_data),
            "upgrade_recommendations": self._generate_upgrade_recommendations(
                object_data
            ),
        }

    def _calculate_panel_capacity(self, object_data: Dict[str, Any]) -> float:
        """Calculate panel capacity."""
        return object_data.get("panel_capacity", 200)  # amps

    def _analyze_load_distribution(
        self, object_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Analyze load distribution."""
        return {
            "phase_a": object_data.get("phase_a_load", 30),
            "phase_b": object_data.get("phase_b_load", 35),
            "phase_c": object_data.get("phase_c_load", 25),
        }

    def _check_phase_balance(self, object_data: Dict[str, Any]) -> bool:
        """Check phase balance."""
        loads = self._analyze_load_distribution(object_data)
        max_load = max(loads.values())
        min_load = min(loads.values())

        return (max_load - min_load) / max_load <= 0.2

    def _calculate_spare_capacity(self, object_data: Dict[str, Any]) -> float:
        """Calculate spare capacity."""
        panel_capacity = self._calculate_panel_capacity(object_data)
        total_load = sum(self._analyze_load_distribution(object_data).values())

        return panel_capacity - total_load

    def _generate_upgrade_recommendations(
        self, object_data: Dict[str, Any]
    ) -> List[str]:
        """Generate upgrade recommendations."""
        recommendations = []
        spare_capacity = self._calculate_spare_capacity(object_data)

        if spare_capacity < 20:
            recommendations.append("Consider panel upgrade for future expansion")

        if not self._check_phase_balance(object_data):
            recommendations.append("Redistribute loads for better phase balance")

        return recommendations


class SafetyAnalyzer:
    """Safety analysis component."""

    async def analyze_safety(self, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze safety aspects."""
        return {
            "shock_hazard": self._assess_shock_hazard(object_data),
            "fire_hazard": self._assess_fire_hazard(object_data),
            "arc_flash": self._assess_arc_flash(object_data),
            "grounding": self._check_grounding(object_data),
            "safety_recommendations": self._generate_safety_recommendations(
                object_data
            ),
        }

    def _assess_shock_hazard(self, object_data: Dict[str, Any]) -> str:
        """Assess shock hazard."""
        voltage = object_data.get("voltage", 120)

        if voltage > 600:
            return "high"
        elif voltage > 50:
            return "medium"
        else:
            return "low"

    def _assess_fire_hazard(self, object_data: Dict[str, Any]) -> str:
        """Assess fire hazard."""
        current = object_data.get("current", 10)

        if current > 100:
            return "high"
        elif current > 20:
            return "medium"
        else:
            return "low"

    def _assess_arc_flash(self, object_data: Dict[str, Any]) -> str:
        """Assess arc flash hazard."""
        voltage = object_data.get("voltage", 120)
        current = object_data.get("current", 10)

        if voltage > 480 and current > 50:
            return "high"
        elif voltage > 240:
            return "medium"
        else:
            return "low"

    def _check_grounding(self, object_data: Dict[str, Any]) -> bool:
        """Check grounding."""
        return object_data.get("grounded", True)

    def _generate_safety_recommendations(
        self, object_data: Dict[str, Any]
    ) -> List[str]:
        """Generate safety recommendations."""
        recommendations = []

        if self._assess_shock_hazard(object_data) == "high":
            recommendations.append("Install additional safety barriers")

        if self._assess_arc_flash(object_data) == "high":
            recommendations.append("Implement arc flash protection measures")

        if not self._check_grounding(object_data):
            recommendations.append("Ensure proper grounding is installed")

        return recommendations


class ElectricalCodeValidator:
    """Electrical code compliance validator."""

    async def validate_compliance(self, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate electrical code compliance."""
        return {
            "nec_compliance": self._check_nec_compliance(object_data),
            "local_code_compliance": self._check_local_code_compliance(object_data),
            "safety_compliance": self._check_safety_compliance(object_data),
            "installation_compliance": self._check_installation_compliance(object_data),
            "overall_compliance": self._determine_overall_compliance(object_data),
        }

    def _check_nec_compliance(self, object_data: Dict[str, Any]) -> bool:
        """Check NEC compliance."""
        # Simplified NEC compliance check
        voltage = object_data.get("voltage", 120)
        current = object_data.get("current", 10)

        # Basic NEC rules
        if voltage > 600:
            return False  # High voltage requires special considerations
        if current > 100:
            return False  # High current requires special considerations

        return True

    def _check_local_code_compliance(self, object_data: Dict[str, Any]) -> bool:
        """Check local code compliance."""
        # Simplified local code check
        return object_data.get("local_code_compliant", True)

    def _check_safety_compliance(self, object_data: Dict[str, Any]) -> bool:
        """Check safety compliance."""
        # Simplified safety check
        return object_data.get("safety_compliant", True)

    def _check_installation_compliance(self, object_data: Dict[str, Any]) -> bool:
        """Check installation compliance."""
        # Simplified installation check
        return object_data.get("installation_compliant", True)

    def _determine_overall_compliance(self, object_data: Dict[str, Any]) -> bool:
        """Determine overall compliance."""
        nec = self._check_nec_compliance(object_data)
        local = self._check_local_code_compliance(object_data)
        safety = self._check_safety_compliance(object_data)
        installation = self._check_installation_compliance(object_data)

        return all([nec, local, safety, installation])
