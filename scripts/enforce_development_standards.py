#!/usr/bin/env python3
"""
Development Standards Enforcement Script

This script enforces enterprise development standards across the Arxos codebase,
including Clean Architecture compliance, code quality standards, and security checks.

Usage:
    python scripts/enforce_development_standards.py [--check-only] [--fix] [--report]

Author: Arxos Engineering Team
Date: 2024
License: MIT
"""

import os
import sys
import ast
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ViolationLevel(Enum):
    """Violation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ArchitectureLayer(Enum):
    """Clean Architecture layers."""

    DOMAIN = "domain"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    PRESENTATION = "presentation"


@dataclass
class Violation:
    """Represents a code violation."""

    file_path: str
    line_number: int
    violation_type: str
    message: str
    level: ViolationLevel
    suggestion: Optional[str] = None


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""

    file_path: str
    architecture_layer: Optional[ArchitectureLayer]
    violations: List[Violation]
    clean_architecture_compliant: bool
    code_quality_score: float
    security_score: float
    documentation_score: float


@dataclass
class ProjectAnalysis:
    """Complete project analysis results."""

    total_files: int
    analyzed_files: int
    violations: List[Violation]
    architecture_compliance: float
    overall_quality_score: float
    security_score: float
    recommendations: List[str]


class DevelopmentStandardsEnforcer:
    """Enforces enterprise development standards."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.violations: List[Violation] = []
        self.file_analyses: List[FileAnalysis] = []

        # Define architecture patterns
        self.architecture_patterns = {
            ArchitectureLayer.DOMAIN: [
                "entities",
                "value_objects",
                "aggregates",
                "repositories",
                "services",
                "events",
                "exceptions",
            ],
            ArchitectureLayer.APPLICATION: [
                "use_cases",
                "dto",
                "services",
                "interfaces",
            ],
            ArchitectureLayer.INFRASTRUCTURE: [
                "repositories",
                "services",
                "config",
                "database",
                "external",
            ],
            ArchitectureLayer.PRESENTATION: [
                "api",
                "web",
                "cli",
                "controllers",
                "views",
            ],
        }

        # Define naming conventions
        self.naming_conventions = {
            "entities": r"^[A-Z][a-zA-Z0-9]*$",
            "value_objects": r"^[A-Z][a-zA-Z0-9]*$",
            "repositories": r"^[A-Z][a-zA-Z0-9]*Repository$",
            "use_cases": r"^[A-Z][a-zA-Z0-9]*UseCase$",
            "services": r"^[A-Z][a-zA-Z0-9]*Service$",
            "controllers": r"^[A-Z][a-zA-Z0-9]*Controller$",
        }

        # Define security patterns
        self.security_patterns = {
            "sql_injection": [
                r"execute\s*\(\s*[\"'].*[\"']\s*\+\s*\w+",
                r"cursor\.execute\s*\(\s*[\"'].*[\"']\s*\+\s*\w+",
            ],
            "xss": [r"innerHTML\s*=", r"document\.write\s*\(", r"eval\s*\("],
            "hardcoded_secrets": [
                r"password\s*=\s*[\"'][^\"']+[\"']",
                r"secret\s*=\s*[\"'][^\"']+[\"']",
                r"api_key\s*=\s*[\"'][^\"']+[\"']",
            ],
        }

    def analyze_project(self) -> ProjectAnalysis:
        """Analyze the entire project for standards compliance."""
        logger.info("Starting project analysis...")

        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files")

        # Analyze each file
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue

            file_analysis = self._analyze_file(file_path)
            self.file_analyses.append(file_analysis)
            self.violations.extend(file_analysis.violations)

        # Calculate overall metrics
        total_violations = len(self.violations)
        error_violations = len(
            [v for v in self.violations if v.level == ViolationLevel.ERROR]
        )
        warning_violations = len(
            [v for v in self.violations if v.level == ViolationLevel.WARNING]
        )

        # Calculate scores
        architecture_compliance = self._calculate_architecture_compliance()
        overall_quality_score = self._calculate_overall_quality_score()
        security_score = self._calculate_security_score()

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return ProjectAnalysis(
            total_files=len(python_files),
            analyzed_files=len(self.file_analyses),
            violations=self.violations,
            architecture_compliance=architecture_compliance,
            overall_quality_score=overall_quality_score,
            security_score=security_score,
            recommendations=recommendations,
        )

    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if file should be skipped from analysis."""
        skip_patterns = [
            "venv/",
            "__pycache__/",
            ".git/",
            "node_modules/",
            "migrations/",
            "tests/",
            "test_",
            "_test.py",
        ]

        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single file for standards compliance."""
        logger.debug(f"Analyzing {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Determine architecture layer
            architecture_layer = self._determine_architecture_layer(file_path)

            # Check violations
            violations = []
            violations.extend(
                self._check_clean_architecture(tree, file_path, architecture_layer)
            )
            violations.extend(self._check_naming_conventions(tree, file_path))
            violations.extend(self._check_security_patterns(content, file_path))
            violations.extend(self._check_documentation(tree, file_path))
            violations.extend(self._check_code_quality(tree, file_path))

            # Calculate scores
            clean_architecture_compliant = (
                len([v for v in violations if "Clean Architecture" in v.violation_type])
                == 0
            )
            code_quality_score = self._calculate_file_quality_score(violations)
            security_score = self._calculate_file_security_score(violations)
            documentation_score = self._calculate_file_documentation_score(violations)

            return FileAnalysis(
                file_path=str(file_path),
                architecture_layer=architecture_layer,
                violations=violations,
                clean_architecture_compliant=clean_architecture_compliant,
                code_quality_score=code_quality_score,
                security_score=security_score,
                documentation_score=documentation_score,
            )

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return FileAnalysis(
                file_path=str(file_path),
                architecture_layer=None,
                violations=[
                    Violation(
                        file_path=str(file_path),
                        line_number=0,
                        violation_type="Analysis Error",
                        message=f"Failed to analyze file: {str(e)}",
                        level=ViolationLevel.ERROR,
                    )
                ],
                clean_architecture_compliant=False,
                code_quality_score=0.0,
                security_score=0.0,
                documentation_score=0.0,
            )

    def _determine_architecture_layer(
        self, file_path: Path
    ) -> Optional[ArchitectureLayer]:
        """Determine the Clean Architecture layer for a file."""
        file_str = str(file_path)

        for layer, patterns in self.architecture_patterns.items():
            for pattern in patterns:
                if pattern in file_str:
                    return layer

        return None

    def _check_clean_architecture(
        self,
        tree: ast.AST,
        file_path: Path,
        architecture_layer: Optional[ArchitectureLayer],
    ) -> List[Violation]:
        """Check Clean Architecture compliance."""
        violations = []

        # Check for domain layer dependencies
        if architecture_layer == ArchitectureLayer.DOMAIN:
            violations.extend(self._check_domain_layer_isolated(tree, file_path))
        elif architecture_layer == ArchitectureLayer.APPLICATION:
            violations.extend(
                self._check_application_layer_dependencies(tree, file_path)
            )
        elif architecture_layer == ArchitectureLayer.INFRASTRUCTURE:
            violations.extend(
                self._check_infrastructure_layer_dependencies(tree, file_path)
            )

        return violations

    def _check_domain_layer_isolated(
        self, tree: ast.AST, file_path: Path
    ) -> List[Violation]:
        """Check that domain layer has no external dependencies."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                module_name = node.module if hasattr(node, "module") else ""

                # Check for framework dependencies
                framework_modules = ["django", "fastapi", "sqlalchemy", "redis"]
                for framework in framework_modules:
                    if framework in module_name:
                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_number=getattr(node, "lineno", 0),
                                violation_type="Clean Architecture",
                                message=f"Domain layer should not depend on {framework}",
                                level=ViolationLevel.ERROR,
                                suggestion="Move framework dependencies to infrastructure layer",
                            )
                        )

        return violations

    def _check_application_layer_dependencies(
        self, tree: ast.AST, file_path: Path
    ) -> List[Violation]:
        """Check application layer dependencies."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                module_name = node.module if hasattr(node, "module") else ""

                # Application layer should not depend on infrastructure
                if "infrastructure" in module_name:
                    violations.append(
                        Violation(
                            file_path=str(file_path),
                            line_number=getattr(node, "lineno", 0),
                            violation_type="Clean Architecture",
                            message="Application layer should not depend on infrastructure",
                            level=ViolationLevel.ERROR,
                            suggestion="Use dependency injection or interfaces",
                        )
                    )

        return violations

    def _check_infrastructure_layer_dependencies(
        self, tree: ast.AST, file_path: Path
    ) -> List[Violation]:
        """Check infrastructure layer dependencies."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                module_name = node.module if hasattr(node, "module") else ""

                # Infrastructure can depend on domain and application
                # This is generally acceptable in Clean Architecture
                pass

        return violations

    def _check_naming_conventions(
        self, tree: ast.AST, file_path: Path
    ) -> List[Violation]:
        """Check naming convention compliance."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name

                # Check entity naming
                if (
                    "entity" in str(file_path).lower()
                    or "entities" in str(file_path).lower()
                ):
                    if not re.match(self.naming_conventions["entities"], class_name):
                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                violation_type="Naming Convention",
                                message=f"Entity class '{class_name}' should follow PascalCase",
                                level=ViolationLevel.WARNING,
                                suggestion=f"Rename to follow PascalCase convention",
                            )
                        )

                # Check repository naming
                if "repository" in str(file_path).lower():
                    if not re.match(
                        self.naming_conventions["repositories"], class_name
                    ):
                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                violation_type="Naming Convention",
                                message=f"Repository class '{class_name}' should end with 'Repository'",
                                level=ViolationLevel.WARNING,
                                suggestion=f"Rename to '{class_name}Repository'",
                            )
                        )

                # Check use case naming
                if (
                    "use_case" in str(file_path).lower()
                    or "usecase" in str(file_path).lower()
                ):
                    if not re.match(self.naming_conventions["use_cases"], class_name):
                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                violation_type="Naming Convention",
                                message=f"Use case class '{class_name}' should end with 'UseCase'",
                                level=ViolationLevel.WARNING,
                                suggestion=f"Rename to '{class_name}UseCase'",
                            )
                        )

        return violations

    def _check_security_patterns(
        self, content: str, file_path: Path
    ) -> List[Violation]:
        """Check for security vulnerabilities."""
        violations = []

        for vulnerability_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_number = content[: match.start()].count("\n") + 1
                    violations.append(
                        Violation(
                            file_path=str(file_path),
                            line_number=line_number,
                            violation_type="Security",
                            message=f"Potential {vulnerability_type} vulnerability detected",
                            level=ViolationLevel.ERROR,
                            suggestion=f"Review and fix {vulnerability_type} vulnerability",
                        )
                    )

        return violations

    def _check_documentation(self, tree: ast.AST, file_path: Path) -> List[Violation]:
        """Check documentation standards."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                # Check for docstrings
                if not ast.get_docstring(node):
                    if isinstance(node, ast.FunctionDef):
                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                violation_type="Documentation",
                                message=f"Function '{node.name}' missing docstring",
                                level=ViolationLevel.WARNING,
                                suggestion="Add comprehensive docstring",
                            )
                        )
                    elif isinstance(node, ast.ClassDef):
                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                violation_type="Documentation",
                                message=f"Class '{node.name}' missing docstring",
                                level=ViolationLevel.WARNING,
                                suggestion="Add comprehensive docstring",
                            )
                        )

        return violations

    def _check_code_quality(self, tree: ast.AST, file_path: Path) -> List[Violation]:
        """Check code quality standards."""
        violations = []

        for node in ast.walk(tree):
            # Check function complexity
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_function_complexity(node)
                if complexity > 10:
                    violations.append(
                        Violation(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            violation_type="Code Quality",
                            message=f"Function '{node.name}' has high complexity ({complexity})",
                            level=ViolationLevel.WARNING,
                            suggestion="Consider breaking into smaller functions",
                        )
                    )

            # Check for magic numbers
            if isinstance(node, ast.Num):
                if isinstance(node.n, (int, float)) and abs(node.n) > 100:
                    violations.append(
                        Violation(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            violation_type="Code Quality",
                            message=f"Magic number detected: {node.n}",
                            level=ViolationLevel.INFO,
                            suggestion="Define as named constant",
                        )
                    )

        return violations

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _calculate_architecture_compliance(self) -> float:
        """Calculate overall architecture compliance score."""
        if not self.file_analyses:
            return 0.0

        compliant_files = sum(
            1
            for analysis in self.file_analyses
            if analysis.clean_architecture_compliant
        )
        return (compliant_files / len(self.file_analyses)) * 100

    def _calculate_overall_quality_score(self) -> float:
        """Calculate overall code quality score."""
        if not self.file_analyses:
            return 0.0

        total_score = sum(
            analysis.code_quality_score for analysis in self.file_analyses
        )
        return total_score / len(self.file_analyses)

    def _calculate_security_score(self) -> float:
        """Calculate overall security score."""
        if not self.file_analyses:
            return 0.0

        total_score = sum(analysis.security_score for analysis in self.file_analyses)
        return total_score / len(self.file_analyses)

    def _calculate_file_quality_score(self, violations: List[Violation]) -> float:
        """Calculate quality score for a single file."""
        if not violations:
            return 100.0

        # Weight violations by severity
        error_weight = 10
        warning_weight = 5
        info_weight = 1

        total_penalty = 0
        for violation in violations:
            if violation.level == ViolationLevel.ERROR:
                total_penalty += error_weight
            elif violation.level == ViolationLevel.WARNING:
                total_penalty += warning_weight
            elif violation.level == ViolationLevel.INFO:
                total_penalty += info_weight

        return max(0.0, 100.0 - total_penalty)

    def _calculate_file_security_score(self, violations: List[Violation]) -> float:
        """Calculate security score for a single file."""
        security_violations = [v for v in violations if v.violation_type == "Security"]

        if not security_violations:
            return 100.0

        # Security violations are critical
        return max(0.0, 100.0 - (len(security_violations) * 20))

    def _calculate_file_documentation_score(self, violations: List[Violation]) -> float:
        """Calculate documentation score for a single file."""
        doc_violations = [v for v in violations if v.violation_type == "Documentation"]

        if not doc_violations:
            return 100.0

        return max(0.0, 100.0 - (len(doc_violations) * 5))

    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        # Architecture recommendations
        if self._calculate_architecture_compliance() < 80:
            recommendations.append(
                "Improve Clean Architecture compliance by reducing cross-layer dependencies"
            )

        # Security recommendations
        security_violations = [
            v for v in self.violations if v.violation_type == "Security"
        ]
        if security_violations:
            recommendations.append(
                f"Address {len(security_violations)} security vulnerabilities"
            )

        # Documentation recommendations
        doc_violations = [
            v for v in self.violations if v.violation_type == "Documentation"
        ]
        if doc_violations:
            recommendations.append(
                f"Add documentation to {len(doc_violations)} functions/classes"
            )

        # Code quality recommendations
        quality_violations = [
            v for v in self.violations if v.violation_type == "Code Quality"
        ]
        if quality_violations:
            recommendations.append(
                f"Improve code quality in {len(quality_violations)} areas"
            )

        return recommendations

    def generate_report(
        self, analysis: ProjectAnalysis, output_file: Optional[str] = None
    ) -> str:
        """Generate a comprehensive analysis report."""
        report = []
        report.append("=" * 80)
        report.append("ARXOS DEVELOPMENT STANDARDS ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Files Analyzed: {analysis.analyzed_files}")
        report.append(f"Total Violations: {len(analysis.violations)}")
        report.append(
            f"Architecture Compliance: {analysis.architecture_compliance:.1f}%"
        )
        report.append(f"Overall Quality Score: {analysis.overall_quality_score:.1f}%")
        report.append(f"Security Score: {analysis.security_score:.1f}%")
        report.append("")

        # Violations by type
        violation_types = {}
        for violation in analysis.violations:
            violation_types[violation.violation_type] = (
                violation_types.get(violation.violation_type, 0) + 1
            )

        report.append("🚨 VIOLATIONS BY TYPE")
        report.append("-" * 40)
        for violation_type, count in violation_types.items():
            report.append(f"{violation_type}: {count}")
        report.append("")

        # Critical violations
        critical_violations = [
            v for v in analysis.violations if v.level == ViolationLevel.ERROR
        ]
        if critical_violations:
            report.append("❌ CRITICAL VIOLATIONS")
            report.append("-" * 40)
            for violation in critical_violations[:10]:  # Show first 10
                report.append(
                    f"{violation.file_path}:{violation.line_number} - {violation.message}"
                )
            if len(critical_violations) > 10:
                report.append(f"... and {len(critical_violations) - 10} more")
            report.append("")

        # Recommendations
        if analysis.recommendations:
            report.append("💡 RECOMMENDATIONS")
            report.append("-" * 40)
            for recommendation in analysis.recommendations:
                report.append(f"• {recommendation}")
            report.append("")

        # File-level analysis
        report.append("📁 FILE-LEVEL ANALYSIS")
        report.append("-" * 40)
        for file_analysis in self.file_analyses[:10]:  # Show first 10 files
            report.append(f"{file_analysis.file_path}")
            report.append(
                f"  Architecture: {file_analysis.architecture_layer.value if file_analysis.architecture_layer else 'Unknown'}"
            )
            report.append(f"  Quality Score: {file_analysis.code_quality_score:.1f}%")
            report.append(f"  Security Score: {file_analysis.security_score:.1f}%")
            report.append(f"  Violations: {len(file_analysis.violations)}")
            report.append("")

        report_text = "\n".join(report)

        if output_file:
            with open(output_file, "w") as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_file}")

        return report_text


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enforce development standards")
    parser.add_argument(
        "--check-only", action="store_true", help="Only check, don't fix"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix violations where possible"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed report"
    )
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    # Initialize enforcer
    enforcer = DevelopmentStandardsEnforcer(args.project_root)

    # Run analysis
    analysis = enforcer.analyze_project()

    # Generate report
    if args.report:
        report = enforcer.generate_report(analysis, args.output)
        print(report)

    # Summary
    print(f"\n📊 Analysis Complete:")
    print(f"Files analyzed: {analysis.analyzed_files}")
    print(f"Total violations: {len(analysis.violations)}")
    print(f"Architecture compliance: {analysis.architecture_compliance:.1f}%")
    print(f"Overall quality: {analysis.overall_quality_score:.1f}%")
    print(f"Security score: {analysis.security_score:.1f}%")

    # Exit with error code if critical violations found
    critical_violations = [
        v for v in analysis.violations if v.level == ViolationLevel.ERROR
    ]
    if critical_violations:
        print(f"\n❌ Found {len(critical_violations)} critical violations!")
        sys.exit(1)
    else:
        print("\n✅ No critical violations found!")
        sys.exit(0)


if __name__ == "__main__":
    main()
