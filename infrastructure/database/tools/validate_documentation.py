#!/usr/bin/env python3
"""
Database Documentation Validation Tool

This script validates that database documentation is synchronized with the actual
schema. It follows Arxos standards for automated validation and CI/CD integration.

Features:
- Validates schema documentation against actual database schema
- Checks migration documentation completeness
- Verifies constraint documentation accuracy
- Ensures performance documentation is current
- Generates validation reports for CI/CD

Usage:
    python validate_documentation.py [--database-url postgresql://...]
    python validate_documentation.py --help
"""

import os
import sys
import argparse
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import structlog
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure structured logging following Arxos standards
logger = structlog.get_logger(__name__)

@dataclass
class ValidationResult:
    """Result of a documentation validation check."""
    check_name: str
    status: str  # 'PASS', 'FAIL', 'WARNING'
    message: str
    details: Optional[Dict[str, Any]] = None
    severity: str = 'INFO'  # 'INFO', 'WARNING', 'ERROR'

@dataclass
class ValidationReport:
    """Complete validation report."""
    timestamp: datetime
    database_name: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    results: List[ValidationResult]
    summary: str

class DocumentationValidator:
    """
    Validator for database documentation synchronization.
    
    Follows Arxos standards for automated validation, comprehensive checking,
    and CI/CD integration with detailed reporting.
    """
    
    def __init__(self, database_url: str, docs_path: str = "arx-docs/database"):
        """
        Initialize the documentation validator.
        
        Args:
            database_url: PostgreSQL connection URL
            docs_path: Path to documentation directory
        """
        self.database_url = database_url
        self.docs_path = Path(docs_path)
        self.connection = None
        self.validation_report = None
        
        # Validation metrics
        self.metrics = {
            'checks_performed': 0,
            'validation_time_ms': 0,
            'schema_tables': 0,
            'doc_tables': 0,
            'mismatches_found': 0
        }
        
        logger.info("documentation_validator_initialized",
                   database_url=self._mask_password(database_url),
                   docs_path=str(self.docs_path))
    
    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging."""
        if '@' in url and ':' in url:
            parts = url.split('@')
            if len(parts) == 2:
                auth_part = parts[0]
                if ':' in auth_part:
                    user_pass = auth_part.split('://')
                    if len(user_pass) == 2:
                        protocol = user_pass[0]
                        credentials = user_pass[1]
                        if ':' in credentials:
                            user = credentials.split(':')[0]
                            return f"{protocol}://{user}:***@{parts[1]}"
        return url
    
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(self.database_url)
            logger.info("database_connection_established")
            return True
        except Exception as e:
            logger.error("database_connection_failed",
                        error=str(e))
            return False
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("database_connection_closed")
    
    def validate_documentation(self) -> bool:
        """
        Perform comprehensive documentation validation.
        
        Returns:
            True if validation successful, False otherwise
        """
        start_time = datetime.now()
        
        if not self.connect():
            return False
        
        try:
            logger.info("starting_documentation_validation")
            
            results = []
            
            # Perform validation checks
            checks = [
                self._validate_schema_documentation,
                self._validate_migration_documentation,
                self._validate_constraint_documentation,
                self._validate_performance_documentation,
                self._validate_file_structure,
                self._validate_documentation_completeness
            ]
            
            for check in checks:
                try:
                    result = check()
                    if isinstance(result, list):
                        results.extend(result)
                    else:
                        results.append(result)
                    self.metrics['checks_performed'] += 1
                except Exception as e:
                    logger.error("validation_check_failed",
                               check=check.__name__,
                               error=str(e))
                    results.append(ValidationResult(
                        check_name=check.__name__,
                        status='FAIL',
                        message=f"Validation check failed: {str(e)}",
                        severity='ERROR'
                    ))
            
            # Calculate metrics
            passed_checks = len([r for r in results if r.status == 'PASS'])
            failed_checks = len([r for r in results if r.status == 'FAIL'])
            warning_checks = len([r for r in results if r.status == 'WARNING'])
            
            # Generate summary
            if failed_checks == 0 and warning_checks == 0:
                summary = "✅ All documentation validation checks passed"
            elif failed_checks == 0:
                summary = f"⚠️ Documentation validation completed with {warning_checks} warnings"
            else:
                summary = f"❌ Documentation validation failed with {failed_checks} errors and {warning_checks} warnings"
            
            # Create validation report
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics['validation_time_ms'] = processing_time
            
            self.validation_report = ValidationReport(
                timestamp=datetime.now(),
                database_name=self._get_database_name(),
                total_checks=len(results),
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                warning_checks=warning_checks,
                results=results,
                summary=summary
            )
            
            logger.info("documentation_validation_completed",
                       total_checks=len(results),
                       passed_checks=passed_checks,
                       failed_checks=failed_checks,
                       warning_checks=warning_checks,
                       validation_time_ms=round(processing_time, 2))
            
            return failed_checks == 0
            
        except Exception as e:
            logger.error("documentation_validation_failed",
                        error=str(e))
            return False
        finally:
            self.disconnect()
    
    def _get_database_name(self) -> str:
        """Get database name for reporting."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                return cursor.fetchone()[0]
        except:
            return "unknown"
    
    def _validate_schema_documentation(self) -> List[ValidationResult]:
        """Validate that schema documentation matches actual database schema."""
        results = []
        
        # Get actual database tables
        actual_tables = self._get_actual_tables()
        self.metrics['schema_tables'] = len(actual_tables)
        
        # Get documented tables
        documented_tables = self._get_documented_tables()
        self.metrics['doc_tables'] = len(documented_tables)
        
        # Check for missing documentation
        missing_docs = actual_tables - documented_tables
        if missing_docs:
            results.append(ValidationResult(
                check_name="schema_documentation_completeness",
                status='FAIL',
                message=f"Missing documentation for {len(missing_docs)} tables",
                details={'missing_tables': list(missing_docs)},
                severity='ERROR'
            ))
            self.metrics['mismatches_found'] += len(missing_docs)
        else:
            results.append(ValidationResult(
                check_name="schema_documentation_completeness",
                status='PASS',
                message="All tables have documentation",
                details={'total_tables': len(actual_tables)}
            ))
        
        # Check for outdated documentation
        outdated_docs = documented_tables - actual_tables
        if outdated_docs:
            results.append(ValidationResult(
                check_name="schema_documentation_accuracy",
                status='WARNING',
                message=f"Documentation exists for {len(outdated_docs)} non-existent tables",
                details={'outdated_tables': list(outdated_docs)},
                severity='WARNING'
            ))
        
        # Validate individual table documentation
        for table_name in actual_tables:
            table_results = self._validate_table_documentation(table_name)
            results.extend(table_results)
        
        return results
    
    def _get_actual_tables(self) -> Set[str]:
        """Get actual tables from database."""
        tables = set()
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """)
            
            for row in cursor.fetchall():
                tables.add(row[0])
        
        return tables
    
    def _get_documented_tables(self) -> Set[str]:
        """Get tables that have documentation."""
        documented_tables = set()
        
        schema_docs_path = self.docs_path / "schema"
        if schema_docs_path.exists():
            for doc_file in schema_docs_path.glob("*.md"):
                table_name = doc_file.stem
                documented_tables.add(table_name)
        
        return documented_tables
    
    def _validate_table_documentation(self, table_name: str) -> List[ValidationResult]:
        """Validate documentation for a specific table."""
        results = []
        
        # Check if documentation file exists
        doc_file = self.docs_path / "schema" / f"{table_name}.md"
        if not doc_file.exists():
            results.append(ValidationResult(
                check_name=f"table_documentation_{table_name}",
                status='FAIL',
                message=f"Missing documentation file for table {table_name}",
                details={'table_name': table_name},
                severity='ERROR'
            ))
            return results
        
        # Read documentation content
        try:
            with open(doc_file, 'r') as f:
                doc_content = f.read()
        except Exception as e:
            results.append(ValidationResult(
                check_name=f"table_documentation_{table_name}",
                status='FAIL',
                message=f"Error reading documentation for table {table_name}: {str(e)}",
                details={'table_name': table_name, 'error': str(e)},
                severity='ERROR'
            ))
            return results
        
        # Validate schema section
        if "## Schema Definition" not in doc_content:
            results.append(ValidationResult(
                check_name=f"table_schema_section_{table_name}",
                status='WARNING',
                message=f"Missing schema definition section in {table_name} documentation",
                details={'table_name': table_name},
                severity='WARNING'
            ))
        
        # Validate relationships section
        if "## Relationships" not in doc_content:
            results.append(ValidationResult(
                check_name=f"table_relationships_section_{table_name}",
                status='WARNING',
                message=f"Missing relationships section in {table_name} documentation",
                details={'table_name': table_name},
                severity='WARNING'
            ))
        
        # Validate indexes section
        if "## Indexes" not in doc_content:
            results.append(ValidationResult(
                check_name=f"table_indexes_section_{table_name}",
                status='WARNING',
                message=f"Missing indexes section in {table_name} documentation",
                details={'table_name': table_name},
                severity='WARNING'
            ))
        
        return results
    
    def _validate_migration_documentation(self) -> ValidationResult:
        """Validate migration documentation completeness."""
        migration_doc = self.docs_path / "migrations.md"
        
        if not migration_doc.exists():
            return ValidationResult(
                check_name="migration_documentation_existence",
                status='FAIL',
                message="Missing migration documentation file",
                details={'expected_file': str(migration_doc)},
                severity='ERROR'
            )
        
        # Check for required sections
        try:
            with open(migration_doc, 'r') as f:
                content = f.read()
            
            required_sections = [
                "## Migration Workflow",
                "## Versioning Conventions",
                "## Rollback Strategy"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                return ValidationResult(
                    check_name="migration_documentation_completeness",
                    status='WARNING',
                    message=f"Missing required sections in migration documentation",
                    details={'missing_sections': missing_sections},
                    severity='WARNING'
                )
            else:
                return ValidationResult(
                    check_name="migration_documentation_completeness",
                    status='PASS',
                    message="Migration documentation is complete",
                    details={'total_sections': len(required_sections)}
                )
                
        except Exception as e:
            return ValidationResult(
                check_name="migration_documentation_readability",
                status='FAIL',
                message=f"Error reading migration documentation: {str(e)}",
                details={'error': str(e)},
                severity='ERROR'
            )
    
    def _validate_constraint_documentation(self) -> ValidationResult:
        """Validate constraint documentation accuracy."""
        constraint_doc = self.docs_path / "constraints.md"
        
        if not constraint_doc.exists():
            return ValidationResult(
                check_name="constraint_documentation_existence",
                status='FAIL',
                message="Missing constraint documentation file",
                details={'expected_file': str(constraint_doc)},
                severity='ERROR'
            )
        
        # Check actual constraints vs documented constraints
        actual_constraints = self._get_actual_constraints()
        documented_constraints = self._get_documented_constraints()
        
        missing_docs = actual_constraints - documented_constraints
        if missing_docs:
            return ValidationResult(
                check_name="constraint_documentation_accuracy",
                status='WARNING',
                message=f"Missing documentation for {len(missing_docs)} constraints",
                details={'missing_constraints': list(missing_docs)},
                severity='WARNING'
            )
        else:
            return ValidationResult(
                check_name="constraint_documentation_accuracy",
                status='PASS',
                message="All constraints are documented",
                details={'total_constraints': len(actual_constraints)}
            )
    
    def _get_actual_constraints(self) -> Set[str]:
        """Get actual constraints from database."""
        constraints = set()
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    tc.table_name || '.' || tc.constraint_name as constraint_id,
                    tc.constraint_type
                FROM information_schema.table_constraints tc
                WHERE tc.table_schema = 'public'
            """)
            
            for row in cursor.fetchall():
                constraints.add(f"{row[0]} ({row[1]})")
        
        return constraints
    
    def _get_documented_constraints(self) -> Set[str]:
        """Get documented constraints from documentation."""
        # This is a simplified check - in practice, you'd parse the constraints.md file
        # For now, we'll assume constraints are documented if the file exists
        constraint_doc = self.docs_path / "constraints.md"
        if constraint_doc.exists():
            return {"constraints_documented"}  # Placeholder
        return set()
    
    def _validate_performance_documentation(self) -> ValidationResult:
        """Validate performance documentation completeness."""
        performance_doc = self.docs_path / "performance_guide.md"
        
        if not performance_doc.exists():
            return ValidationResult(
                check_name="performance_documentation_existence",
                status='FAIL',
                message="Missing performance documentation file",
                details={'expected_file': str(performance_doc)},
                severity='ERROR'
            )
        
        # Check for required performance sections
        try:
            with open(performance_doc, 'r') as f:
                content = f.read()
            
            required_sections = [
                "## Index Strategy",
                "## Query Optimization",
                "## Performance Monitoring"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                return ValidationResult(
                    check_name="performance_documentation_completeness",
                    status='WARNING',
                    message=f"Missing required sections in performance documentation",
                    details={'missing_sections': missing_sections},
                    severity='WARNING'
                )
            else:
                return ValidationResult(
                    check_name="performance_documentation_completeness",
                    status='PASS',
                    message="Performance documentation is complete",
                    details={'total_sections': len(required_sections)}
                )
                
        except Exception as e:
            return ValidationResult(
                check_name="performance_documentation_readability",
                status='FAIL',
                message=f"Error reading performance documentation: {str(e)}",
                details={'error': str(e)},
                severity='ERROR'
            )
    
    def _validate_file_structure(self) -> ValidationResult:
        """Validate documentation file structure."""
        required_files = [
            "README.md",
            "schema/",
            "migrations.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.docs_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            return ValidationResult(
                check_name="documentation_file_structure",
                status='FAIL',
                message=f"Missing required documentation files",
                details={'missing_files': missing_files},
                severity='ERROR'
            )
        else:
            return ValidationResult(
                check_name="documentation_file_structure",
                status='PASS',
                message="Documentation file structure is complete",
                details={'total_files': len(required_files)}
            )
    
    def _validate_documentation_completeness(self) -> ValidationResult:
        """Validate overall documentation completeness."""
        # Check documentation coverage
        actual_tables = self._get_actual_tables()
        documented_tables = self._get_documented_tables()
        
        coverage_percentage = (len(documented_tables) / len(actual_tables)) * 100 if actual_tables else 0
        
        if coverage_percentage >= 90:
            status = 'PASS'
            message = f"Documentation coverage is excellent ({coverage_percentage:.1f}%)"
        elif coverage_percentage >= 70:
            status = 'WARNING'
            message = f"Documentation coverage needs improvement ({coverage_percentage:.1f}%)"
        else:
            status = 'FAIL'
            message = f"Documentation coverage is poor ({coverage_percentage:.1f}%)"
        
        return ValidationResult(
            check_name="documentation_completeness",
            status=status,
            message=message,
            details={
                'coverage_percentage': coverage_percentage,
                'actual_tables': len(actual_tables),
                'documented_tables': len(documented_tables)
            },
            severity='INFO' if status == 'PASS' else 'WARNING' if status == 'WARNING' else 'ERROR'
        )
    
    def generate_report(self, output_format: str = "json", output_file: Optional[str] = None) -> str:
        """
        Generate validation report in specified format.
        
        Args:
            output_format: 'json' or 'markdown'
            output_file: Optional output file path
            
        Returns:
            Generated report content
        """
        if not self.validation_report:
            logger.warning("no_validation_report_to_generate")
            return ""
        
        logger.info("generating_validation_report",
                   format=output_format,
                   total_checks=self.validation_report.total_checks)
        
        if output_format.lower() == "json":
            return self._generate_json_report(output_file)
        elif output_format.lower() == "markdown":
            return self._generate_markdown_report(output_file)
        else:
            logger.error("unsupported_output_format",
                        format=output_format)
            return ""
    
    def _generate_json_report(self, output_file: Optional[str] = None) -> str:
        """Generate JSON format validation report."""
        report_data = {
            'metadata': {
                'timestamp': self.validation_report.timestamp.isoformat(),
                'database_name': self.validation_report.database_name,
                'total_checks': self.validation_report.total_checks,
                'passed_checks': self.validation_report.passed_checks,
                'failed_checks': self.validation_report.failed_checks,
                'warning_checks': self.validation_report.warning_checks,
                'summary': self.validation_report.summary,
                'processing_metrics': self.metrics
            },
            'results': [asdict(result) for result in self.validation_report.results]
        }
        
        content = json.dumps(report_data, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info("json_report_saved",
                       file=output_file)
        
        return content
    
    def _generate_markdown_report(self, output_file: Optional[str] = None) -> str:
        """Generate Markdown format validation report."""
        content = f"""# Database Documentation Validation Report

**Generated:** {self.validation_report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Database:** {self.validation_report.database_name}

## Summary

{self.validation_report.summary}

## Validation Metrics

- **Total Checks:** {self.validation_report.total_checks}
- **Passed:** {self.validation_report.passed_checks}
- **Failed:** {self.validation_report.failed_checks}
- **Warnings:** {self.validation_report.warning_checks}

## Detailed Results

"""
        
        # Group results by status
        passed_results = [r for r in self.validation_report.results if r.status == 'PASS']
        failed_results = [r for r in self.validation_report.results if r.status == 'FAIL']
        warning_results = [r for r in self.validation_report.results if r.status == 'WARNING']
        
        if failed_results:
            content += "### ❌ Failed Checks\n\n"
            for result in failed_results:
                content += f"**{result.check_name}**\n"
                content += f"- {result.message}\n"
                if result.details:
                    content += f"- Details: {json.dumps(result.details, indent=2)}\n"
                content += "\n"
        
        if warning_results:
            content += "### ⚠️ Warning Checks\n\n"
            for result in warning_results:
                content += f"**{result.check_name}**\n"
                content += f"- {result.message}\n"
                if result.details:
                    content += f"- Details: {json.dumps(result.details, indent=2)}\n"
                content += "\n"
        
        if passed_results:
            content += "### ✅ Passed Checks\n\n"
            for result in passed_results:
                content += f"**{result.check_name}**\n"
                content += f"- {result.message}\n"
                if result.details:
                    content += f"- Details: {json.dumps(result.details, indent=2)}\n"
                content += "\n"
        
        content += f"""
## Processing Metrics

- **Validation Time:** {self.metrics['validation_time_ms']:.2f}ms
- **Checks Performed:** {self.metrics['checks_performed']}
- **Schema Tables:** {self.metrics['schema_tables']}
- **Documented Tables:** {self.metrics['doc_tables']}
- **Mismatches Found:** {self.metrics['mismatches_found']}

---
*This report was generated by the Arxos Database Documentation Validator.*
"""
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info("markdown_report_saved",
                       file=output_file)
        
        return content


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Validate database documentation synchronization"
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://localhost/arxos_db"),
        help="PostgreSQL connection URL"
    )
    parser.add_argument(
        "--docs-path",
        default="arx-docs/database",
        help="Path to documentation directory"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "markdown"],
        default="json",
        help="Output format for the report (default: json)"
    )
    parser.add_argument(
        "--output-file",
        help="Output file path (default: print to stdout)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Validate documentation
    validator = DocumentationValidator(args.database_url, args.docs_path)
    success = validator.validate_documentation()
    
    if validator.validation_report:
        # Generate report
        report_content = validator.generate_report(
            output_format=args.output_format,
            output_file=args.output_file
        )
        
        # Print summary
        print("\n" + "="*60)
        print("DOCUMENTATION VALIDATION SUMMARY")
        print("="*60)
        print(validator.validation_report.summary)
        print(f"Total Checks: {validator.validation_report.total_checks}")
        print(f"Passed: {validator.validation_report.passed_checks}")
        print(f"Failed: {validator.validation_report.failed_checks}")
        print(f"Warnings: {validator.validation_report.warning_checks}")
        print("="*60)
        
        # Print report if no output file specified
        if not args.output_file and report_content:
            print("\n" + report_content)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 