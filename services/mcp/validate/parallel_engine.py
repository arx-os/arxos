"""
Parallel Processing Engine for MCP Rule Validation

This module provides parallel processing capabilities for large building models:
- Multi-threaded rule execution
- Chunked object processing
- Load balancing across CPU cores
- Thread-safe result aggregation
"""

import logging
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from queue import Queue
import time
import psutil

from models.mcp_models import (
    BuildingModel,
    BuildingObject,
    MCPFile,
    MCPRule,
    ValidationResult,
    ValidationViolation,
    ComplianceReport,
)
from validate.rule_engine import MCPRuleEngine, RuleExecutionContext


@dataclass
class ProcessingChunk:
    """Represents a chunk of objects for parallel processing"""

    chunk_id: int
    objects: List[BuildingObject]
    rules: List[MCPRule]
    mcp_file: MCPFile


@dataclass
class ProcessingResult:
    """Result from parallel processing"""

    chunk_id: int
    violations: List[ValidationViolation]
    calculations: Dict[str, Any]
    execution_time: float
    memory_usage: float


class ParallelRuleEngine:
    """
    Parallel processing engine for MCP rule validation

    Features:
    - Multi-threaded rule execution
    - Chunked object processing
    - Load balancing
    - Memory optimization
    - Performance monitoring
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize parallel processing engine

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Performance settings
        self.max_workers = self.config.get(
            "max_workers", min(32, (multiprocessing.cpu_count() or 1) + 4)
        )
        self.chunk_size = self.config.get("chunk_size", 1000)
        self.use_processes = self.config.get("use_processes", False)
        self.memory_limit_mb = self.config.get("memory_limit_mb", 2048)

        # Initialize base engine
        self.base_engine = MCPRuleEngine(config)

        # Performance metrics
        self.total_parallel_validations = 0
        self.total_parallel_execution_time = 0.0
        self.average_parallel_execution_time = 0.0
        self.max_memory_usage = 0.0

        # Thread safety
        self._lock = threading.Lock()

        self.logger.info(
            f"Parallel Rule Engine initialized with {self.max_workers} workers"
        )

    def validate_building_model_parallel(
        self,
        building_model: BuildingModel,
        mcp_files: List[str],
        chunk_size: Optional[int] = None,
    ) -> ComplianceReport:
        """
        Validate building model using parallel processing

        Args:
            building_model: Building model to validate
            mcp_files: List of MCP file paths
            chunk_size: Optional chunk size override

        Returns:
            ComplianceReport with validation results
        """
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        self.logger.info(
            f"Starting parallel validation of {len(building_model.objects)} objects"
        )

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

        # Create processing chunks
        chunks = self._create_processing_chunks(
            building_model.objects, loaded_mcp_files, chunk_size or self.chunk_size
        )

        self.logger.info(f"Created {len(chunks)} processing chunks")

        # Execute parallel processing
        results = self._execute_parallel_processing(chunks)

        # Aggregate results
        aggregated_results = self._aggregate_results(results)

        # Generate compliance report
        report = self._generate_compliance_report(
            building_model, aggregated_results, loaded_mcp_files
        )

        # Update performance metrics
        execution_time = time.time() - start_time
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_usage = final_memory - initial_memory

        self._update_performance_metrics(execution_time, memory_usage)

        self.logger.info(
            f"Parallel validation completed in {execution_time:.3f}s, "
            f"memory usage: {memory_usage:.1f}MB"
        )

        return report

    def _create_processing_chunks(
        self, objects: List[BuildingObject], mcp_files: List[MCPFile], chunk_size: int
    ) -> List[ProcessingChunk]:
        """Create processing chunks for parallel execution"""
        chunks = []

        # Group objects by type for better load balancing
        objects_by_type = {}
        for obj in objects:
            obj_type = obj.object_type
            if obj_type not in objects_by_type:
                objects_by_type[obj_type] = []
            objects_by_type[obj_type].append(obj)

        chunk_id = 0
        for mcp_file in mcp_files:
            for rule in mcp_file.rules:
                # Create chunks based on object types that match rule conditions
                matching_objects = self._get_matching_objects_for_rule(rule, objects)

                if not matching_objects:
                    continue

                # Split matching objects into chunks
                for i in range(0, len(matching_objects), chunk_size):
                    chunk_objects = matching_objects[i : i + chunk_size]

                    chunk = ProcessingChunk(
                        chunk_id=chunk_id,
                        objects=chunk_objects,
                        rules=[rule],
                        mcp_file=mcp_file,
                    )
                    chunks.append(chunk)
                    chunk_id += 1

        return chunks

    def _get_matching_objects_for_rule(
        self, rule: MCPRule, objects: List[BuildingObject]
    ) -> List[BuildingObject]:
        """Get objects that potentially match a rule based on element types"""
        matching_objects = []

        for condition in rule.conditions:
            if condition.element_type:
                for obj in objects:
                    if obj.object_type == condition.element_type:
                        matching_objects.append(obj)

        # Remove duplicates while preserving order
        seen = set()
        unique_objects = []
        for obj in matching_objects:
            if obj.object_id not in seen:
                seen.add(obj.object_id)
                unique_objects.append(obj)

        return unique_objects

    def _execute_parallel_processing(
        self, chunks: List[ProcessingChunk]
    ) -> List[ProcessingResult]:
        """Execute parallel processing of chunks"""
        results = []

        if self.use_processes:
            # Use process pool for CPU-intensive tasks
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self._process_chunk, chunk) for chunk in chunks
                ]

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Error in parallel processing: {e}")
        else:
            # Use thread pool for I/O-bound tasks
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self._process_chunk, chunk) for chunk in chunks
                ]

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Error in parallel processing: {e}")

        return results

    def _process_chunk(self, chunk: ProcessingChunk) -> ProcessingResult:
        """Process a single chunk of objects"""
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        violations = []
        calculations = {}

        # Create a local engine instance for this chunk
        local_engine = MCPRuleEngine()

        try:
            # Process each rule in the chunk
            for rule in chunk.rules:
                # Create building model for this chunk
                chunk_model = BuildingModel(
                    building_id=f"chunk_{chunk.chunk_id}",
                    building_name=f"Chunk {chunk.chunk_id}",
                    objects=chunk.objects,
                )

                # Execute rule
                result = local_engine._execute_rule(rule, chunk_model)

                # Collect violations and calculations
                violations.extend(result.violations)
                calculations.update(result.calculations)

        except Exception as e:
            self.logger.error(f"Error processing chunk {chunk.chunk_id}: {e}")

        execution_time = time.time() - start_time
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_usage = final_memory - initial_memory

        return ProcessingResult(
            chunk_id=chunk.chunk_id,
            violations=violations,
            calculations=calculations,
            execution_time=execution_time,
            memory_usage=memory_usage,
        )

    def _aggregate_results(
        self, results: List[ProcessingResult]
    ) -> Tuple[List[ValidationViolation], Dict[str, Any]]:
        """Aggregate results from parallel processing"""
        all_violations = []
        all_calculations = {}

        for result in results:
            all_violations.extend(result.violations)

            # Merge calculations (handle conflicts by taking the latest)
            for key, value in result.calculations.items():
                all_calculations[key] = value

        return all_violations, all_calculations

    def _generate_compliance_report(
        self,
        building_model: BuildingModel,
        aggregated_results: Tuple[List[ValidationViolation], Dict[str, Any]],
        mcp_files: List[MCPFile],
    ) -> ComplianceReport:
        """Generate compliance report from aggregated results"""
        violations, calculations = aggregated_results

        # Calculate compliance score
        total_rules = sum(len(mcp_file.rules) for mcp_file in mcp_files)
        failed_rules = len(set(v.rule_id for v in violations))
        compliance_score = (
            max(0, (total_rules - failed_rules) / total_rules * 100)
            if total_rules > 0
            else 100
        )

        # Create validation reports
        validation_reports = []
        for mcp_file in mcp_files:
            mcp_violations = [
                v
                for v in violations
                if v.rule_id in [r.rule_id for r in mcp_file.rules]
            ]

            # Create MCPValidationReport manually
            from models.mcp_models import MCPValidationReport
            from datetime import datetime

            # Calculate statistics
            total_violations = len(mcp_violations)
            total_warnings = len(
                [v for v in mcp_violations if v.severity.value == "warning"]
            )
            failed_rules = len(set(v.rule_id for v in mcp_violations))
            passed_rules = len(mcp_file.rules) - failed_rules

            report = MCPValidationReport(
                mcp_id=mcp_file.mcp_id,
                mcp_name=mcp_file.name,
                jurisdiction=mcp_file.jurisdiction,
                validation_date=datetime.now(),
                total_rules=len(mcp_file.rules),
                passed_rules=passed_rules,
                failed_rules=failed_rules,
                total_violations=total_violations,
                total_warnings=total_warnings,
                results=[],  # We'll leave this empty for now
                summary={"calculations": calculations},
                metadata={},
            )
            validation_reports.append(report)

        # Generate recommendations
        recommendations = self.base_engine._generate_recommendations(validation_reports)

        return ComplianceReport(
            building_id=building_model.building_id,
            building_name=building_model.building_name,
            validation_reports=validation_reports,
            overall_compliance_score=compliance_score,
            critical_violations=len(
                [v for v in violations if v.severity.value == "error"]
            ),
            total_violations=len(violations),
            total_warnings=len(
                [v for v in violations if v.severity.value == "warning"]
            ),
            recommendations=recommendations,
        )

    def _update_performance_metrics(self, execution_time: float, memory_usage: float):
        """Update performance metrics"""
        with self._lock:
            self.total_parallel_validations += 1
            self.total_parallel_execution_time += execution_time
            self.average_parallel_execution_time = (
                self.total_parallel_execution_time / self.total_parallel_validations
            )
            self.max_memory_usage = max(self.max_memory_usage, memory_usage)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        with self._lock:
            return {
                "total_parallel_validations": self.total_parallel_validations,
                "total_parallel_execution_time": self.total_parallel_execution_time,
                "average_parallel_execution_time": self.average_parallel_execution_time,
                "max_memory_usage_mb": self.max_memory_usage,
                "max_workers": self.max_workers,
                "chunk_size": self.chunk_size,
                "use_processes": self.use_processes,
            }

    def optimize_chunk_size(
        self, building_model: BuildingModel, mcp_files: List[str]
    ) -> int:
        """Dynamically optimize chunk size based on building model characteristics"""
        total_objects = len(building_model.objects)
        cpu_count = multiprocessing.cpu_count() or 1

        # Base chunk size calculation
        base_chunk_size = max(100, total_objects // (cpu_count * 4))

        # Adjust based on object complexity
        avg_properties = (
            sum(len(obj.properties) for obj in building_model.objects) / total_objects
        )
        if avg_properties > 10:
            base_chunk_size = max(50, base_chunk_size // 2)

        # Adjust based on memory constraints
        available_memory = psutil.virtual_memory().available / 1024 / 1024  # MB
        memory_per_object = 0.1  # Estimated MB per object
        max_objects_for_memory = int(available_memory / memory_per_object / cpu_count)

        optimized_chunk_size = min(base_chunk_size, max_objects_for_memory)

        self.logger.info(
            f"Optimized chunk size: {optimized_chunk_size} "
            f"(base: {base_chunk_size}, memory limit: {max_objects_for_memory})"
        )

        return optimized_chunk_size

    def clear_cache(self):
        """Clear all caches"""
        self.base_engine.clear_cache()
