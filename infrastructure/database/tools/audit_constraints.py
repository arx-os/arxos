#!/usr/bin/env python3
"""
Schema Constraint Audit Tool for Arxos Database

This script audits the existing database schema to identify candidates for
NOT NULL and CHECK constraints to strengthen data integrity.

Features:
- Analyzes existing schema for nullable columns that should be NOT NULL
- Identifies columns with finite domain values for CHECK constraints
- Generates comprehensive audit report with recommendations
- Follows Arxos logging standards and patterns
- Provides safe migration strategies

Usage:
    python audit_constraints.py [--database-url postgresql://...]
    python audit_constraints.py --help
"""

import os
import sys
import argparse
import json
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
class ColumnInfo:
    """Information about a database column."""
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str]
    character_maximum_length: Optional[int]
    current_null_count: int = 0
    distinct_values: List[str] = None
    recommended_constraint: Optional[str] = None
    constraint_reason: Optional[str] = None
    migration_risk: str = "low"  # low, medium, high
    
    def __post_init__(self):
        if self.distinct_values is None:
            self.distinct_values = []

@dataclass
class TableAudit:
    """Audit results for a single table."""
    table_name: str
    total_columns: int
    nullable_columns: int
    constraint_candidates: List[ColumnInfo]
    not_null_candidates: List[ColumnInfo]
    check_candidates: List[ColumnInfo]
    migration_priority: str  # high, medium, low

@dataclass
class SchemaAudit:
    """Complete schema audit results."""
    audit_timestamp: datetime
    database_name: str
    tables_audited: int
    total_constraint_candidates: int
    not_null_candidates: int
    check_candidates: int
    high_priority_tables: List[str]
    table_audits: List[TableAudit]
    recommendations: List[str]

class SchemaConstraintAuditor:
    """
    Auditor for identifying NOT NULL and CHECK constraint candidates.
    
    Follows Arxos logging standards with structured logging, performance monitoring,
    and comprehensive error handling.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize the schema auditor.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.connection = None
        self.audit_results = None
        
        # Performance tracking
        self.metrics = {
            'tables_analyzed': 0,
            'columns_analyzed': 0,
            'constraint_candidates_found': 0,
            'processing_time_ms': 0,
            'errors': 0,
            'warnings': 0
        }
        
        # Business rules for constraint recommendations
        self.business_rules = {
            'always_required_fields': [
                'email', 'username', 'password_hash', 'name', 'title', 'content',
                'message', 'action', 'change_type', 'object_type', 'object_id'
            ],
            'status_fields': [
                'status', 'role', 'type', 'category', 'material', 'system'
            ],
            'timestamp_fields': [
                'created_at', 'updated_at', 'assigned_at', 'released_at', 'changed_at'
            ],
            'finite_domain_patterns': {
                'status': ['active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled'],
                'role': ['user', 'admin', 'manager', 'viewer'],
                'type': ['education', 'commercial', 'residential', 'industrial'],
                'material': ['concrete', 'steel', 'wood', 'glass', 'plastic', 'metal'],
                'system': ['HVAC', 'electrical', 'plumbing', 'fire', 'security', 'lighting']
            }
        }
        
        logger.info("schema_auditor_initialized",
                   database_url=self._mask_password(database_url))
    
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
    
    def audit_schema(self) -> bool:
        """
        Perform comprehensive schema audit.
        
        Returns:
            True if audit successful, False otherwise
        """
        start_time = datetime.now()
        
        if not self.connect():
            return False
        
        try:
            logger.info("starting_schema_audit")
            
            # Get database information
            db_info = self._get_database_info()
            
            # Get list of tables to audit
            tables = self._get_tables_to_audit()
            
            # Audit each table
            table_audits = []
            for table in tables:
                table_audit = self._audit_table(table)
                if table_audit:
                    table_audits.append(table_audit)
                    self.metrics['tables_analyzed'] += 1
            
            # Generate audit results
            self.audit_results = SchemaAudit(
                audit_timestamp=datetime.now(),
                database_name=db_info['database_name'],
                tables_audited=len(table_audits),
                total_constraint_candidates=sum(len(t.constraint_candidates) for t in table_audits),
                not_null_candidates=sum(len(t.not_null_candidates) for t in table_audits),
                check_candidates=sum(len(t.check_candidates) for t in table_audits),
                high_priority_tables=[t.table_name for t in table_audits if t.migration_priority == 'high'],
                table_audits=table_audits,
                recommendations=self._generate_recommendations(table_audits)
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics['processing_time_ms'] = processing_time
            
            logger.info("schema_audit_completed",
                       tables_analyzed=self.metrics['tables_analyzed'],
                       constraint_candidates=self.audit_results.total_constraint_candidates,
                       processing_time_ms=round(processing_time, 2))
            
            return True
            
        except Exception as e:
            logger.error("schema_audit_failed",
                        error=str(e))
            return False
        finally:
            self.disconnect()
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Get basic database information."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT current_database() as database_name")
            result = cursor.fetchone()
            return dict(result)
    
    def _get_tables_to_audit(self) -> List[str]:
        """Get list of tables to audit based on task requirements."""
        target_tables = ['users', 'permissions', 'objects', 'projects', 'logs']
        
        # Map to actual table names in Arxos schema
        table_mapping = {
            'users': 'users',
            'permissions': 'user_category_permissions',
            'objects': ['rooms', 'walls', 'doors', 'windows', 'devices', 'labels', 'zones'],
            'projects': 'projects',
            'logs': ['audit_logs', 'object_history', 'slow_query_log']
        }
        
        tables_to_audit = []
        for category, tables in table_mapping.items():
            if isinstance(tables, list):
                tables_to_audit.extend(tables)
            else:
                tables_to_audit.append(tables)
        
        # Verify tables exist
        existing_tables = []
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = ANY(%s)
            """, (tables_to_audit,))
            
            for row in cursor.fetchall():
                existing_tables.append(row[0])
        
        logger.info("tables_to_audit",
                   requested=len(tables_to_audit),
                   existing=len(existing_tables),
                   tables=existing_tables)
        
        return existing_tables
    
    def _audit_table(self, table_name: str) -> Optional[TableAudit]:
        """
        Audit a single table for constraint candidates.
        
        Args:
            table_name: Name of the table to audit
            
        Returns:
            TableAudit object with audit results
        """
        try:
            logger.debug("auditing_table",
                        table=table_name)
            
            # Get column information
            columns = self._get_table_columns(table_name)
            
            # Analyze each column
            constraint_candidates = []
            not_null_candidates = []
            check_candidates = []
            
            for column in columns:
                # Check for NULL values
                null_count = self._get_null_count(table_name, column.column_name)
                column.current_null_count = null_count
                
                # Get distinct values for potential CHECK constraints
                if column.column_name in self.business_rules['status_fields']:
                    distinct_values = self._get_distinct_values(table_name, column.column_name)
                    column.distinct_values = distinct_values
                
                # Analyze for constraint candidates
                self._analyze_column_for_constraints(column)
                
                if column.recommended_constraint:
                    constraint_candidates.append(column)
                    
                    if column.recommended_constraint.startswith('NOT NULL'):
                        not_null_candidates.append(column)
                    elif column.recommended_constraint.startswith('CHECK'):
                        check_candidates.append(column)
            
            # Determine migration priority
            migration_priority = self._determine_migration_priority(table_name, constraint_candidates)
            
            return TableAudit(
                table_name=table_name,
                total_columns=len(columns),
                nullable_columns=len([c for c in columns if c.is_nullable]),
                constraint_candidates=constraint_candidates,
                not_null_candidates=not_null_candidates,
                check_candidates=check_candidates,
                migration_priority=migration_priority
            )
            
        except Exception as e:
            logger.error("failed_to_audit_table",
                        table=table_name,
                        error=str(e))
            self.metrics['errors'] += 1
            return None
    
    def _get_table_columns(self, table_name: str) -> List[ColumnInfo]:
        """Get column information for a table."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = []
            for row in cursor.fetchall():
                column = ColumnInfo(
                    table_name=table_name,
                    column_name=row['column_name'],
                    data_type=row['data_type'],
                    is_nullable=row['is_nullable'] == 'YES',
                    column_default=row['column_default'],
                    character_maximum_length=row['character_maximum_length']
                )
                columns.append(column)
            
            return columns
    
    def _get_null_count(self, table_name: str, column_name: str) -> int:
        """Get count of NULL values in a column."""
        with self.connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {table_name} 
                WHERE {column_name} IS NULL
            """)
            return cursor.fetchone()[0]
    
    def _get_distinct_values(self, table_name: str, column_name: str) -> List[str]:
        """Get distinct values in a column."""
        with self.connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT DISTINCT {column_name} 
                FROM {table_name} 
                WHERE {column_name} IS NOT NULL
                ORDER BY {column_name}
            """)
            return [str(row[0]) for row in cursor.fetchall()]
    
    def _analyze_column_for_constraints(self, column: ColumnInfo) -> None:
        """Analyze a column for potential constraints."""
        # Check for NOT NULL candidates
        if self._should_be_not_null(column):
            column.recommended_constraint = "NOT NULL"
            column.constraint_reason = self._get_not_null_reason(column)
            column.migration_risk = self._assess_not_null_risk(column)
        
        # Check for CHECK constraint candidates
        elif self._should_have_check_constraint(column):
            check_expression = self._generate_check_expression(column)
            if check_expression:
                column.recommended_constraint = f"CHECK ({check_expression})"
                column.constraint_reason = f"Finite domain values: {', '.join(column.distinct_values)}"
                column.migration_risk = "low"
    
    def _should_be_not_null(self, column: ColumnInfo) -> bool:
        """Determine if a column should be NOT NULL."""
        # Skip if already NOT NULL
        if not column.is_nullable:
            return False
        
        # Skip if has default value
        if column.column_default:
            return False
        
        # Check business rules
        if column.column_name in self.business_rules['always_required_fields']:
            return True
        
        # Check if column name suggests it should be required
        required_patterns = ['name', 'title', 'content', 'message', 'action', 'type', 'id']
        if any(pattern in column.column_name.lower() for pattern in required_patterns):
            return True
        
        # Check if it's a foreign key (should be NOT NULL unless optional)
        if column.column_name.endswith('_id') and column.data_type in ['integer', 'bigint']:
            return True
        
        return False
    
    def _should_have_check_constraint(self, column: ColumnInfo) -> bool:
        """Determine if a column should have a CHECK constraint."""
        # Check if it's a status/type field with finite domain
        if column.column_name in self.business_rules['status_fields']:
            return len(column.distinct_values) > 0 and len(column.distinct_values) <= 10
        
        # Check if it's a boolean field
        if column.data_type == 'boolean':
            return True
        
        return False
    
    def _get_not_null_reason(self, column: ColumnInfo) -> str:
        """Get reason for NOT NULL recommendation."""
        if column.column_name in self.business_rules['always_required_fields']:
            return f"Business rule: {column.column_name} is always required"
        elif column.column_name.endswith('_id'):
            return "Foreign key should be NOT NULL unless optional relationship"
        elif 'name' in column.column_name.lower():
            return "Name field should not be NULL"
        elif 'content' in column.column_name.lower() or 'message' in column.column_name.lower():
            return "Content/message field should not be NULL"
        else:
            return "Column appears to be required based on naming and usage"
    
    def _assess_not_null_risk(self, column: ColumnInfo) -> str:
        """Assess migration risk for NOT NULL constraint."""
        if column.current_null_count == 0:
            return "low"
        elif column.current_null_count < 100:
            return "medium"
        else:
            return "high"
    
    def _generate_check_expression(self, column: ColumnInfo) -> Optional[str]:
        """Generate CHECK constraint expression."""
        if column.column_name in self.business_rules['finite_domain_patterns']:
            valid_values = self.business_rules['finite_domain_patterns'][column.column_name]
            if column.distinct_values:
                # Use actual values found in database
                values = [f"'{v}'" for v in column.distinct_values if v]
                if values:
                    return f"{column.column_name} IN ({', '.join(values)})"
        
        # For boolean fields
        if column.data_type == 'boolean':
            return f"{column.column_name} IN (true, false)"
        
        # For status fields with actual values
        if column.distinct_values and len(column.distinct_values) <= 10:
            values = [f"'{v}'" for v in column.distinct_values if v]
            if values:
                return f"{column.column_name} IN ({', '.join(values)})"
        
        return None
    
    def _determine_migration_priority(self, table_name: str, candidates: List[ColumnInfo]) -> str:
        """Determine migration priority for a table."""
        if not candidates:
            return "low"
        
        # High priority tables
        high_priority_tables = ['users', 'projects', 'buildings']
        if table_name in high_priority_tables:
            return "high"
        
        # Check for high-risk constraints
        high_risk_count = len([c for c in candidates if c.migration_risk == 'high'])
        if high_risk_count > 0:
            return "high"
        
        # Medium priority for tables with many candidates
        if len(candidates) >= 3:
            return "medium"
        
        return "low"
    
    def _generate_recommendations(self, table_audits: List[TableAudit]) -> List[str]:
        """Generate migration recommendations."""
        recommendations = []
        
        # Count by priority
        high_priority = [t for t in table_audits if t.migration_priority == 'high']
        medium_priority = [t for t in table_audits if t.migration_priority == 'medium']
        
        if high_priority:
            recommendations.append(f"Start with {len(high_priority)} high-priority tables")
        
        if medium_priority:
            recommendations.append(f"Plan migration for {len(medium_priority)} medium-priority tables")
        
        # Specific recommendations
        total_not_null = sum(len(t.not_null_candidates) for t in table_audits)
        total_check = sum(len(t.check_candidates) for t in table_audits)
        
        if total_not_null > 0:
            recommendations.append(f"Add {total_not_null} NOT NULL constraints")
        
        if total_check > 0:
            recommendations.append(f"Add {total_check} CHECK constraints")
        
        # Backfill strategy
        high_risk_candidates = []
        for audit in table_audits:
            for candidate in audit.constraint_candidates:
                if candidate.migration_risk == 'high':
                    high_risk_candidates.append(f"{audit.table_name}.{candidate.column_name}")
        
        if high_risk_candidates:
            recommendations.append(f"Backfill NULL values in: {', '.join(high_risk_candidates[:5])}")
        
        return recommendations
    
    def generate_report(self, output_format: str = "json", output_file: Optional[str] = None) -> str:
        """
        Generate audit report in specified format.
        
        Args:
            output_format: 'json' or 'markdown'
            output_file: Optional output file path
            
        Returns:
            Generated report content
        """
        if not self.audit_results:
            logger.warning("no_audit_results_to_report")
            return ""
        
        logger.info("generating_audit_report",
                   format=output_format,
                   total_candidates=self.audit_results.total_constraint_candidates)
        
        if output_format.lower() == "json":
            return self._generate_json_report(output_file)
        elif output_format.lower() == "markdown":
            return self._generate_markdown_report(output_file)
        else:
            logger.error("unsupported_output_format",
                        format=output_format)
            return ""
    
    def _generate_json_report(self, output_file: Optional[str] = None) -> str:
        """Generate JSON format report."""
        report = {
            'metadata': {
                'audit_timestamp': self.audit_results.audit_timestamp.isoformat(),
                'database_name': self.audit_results.database_name,
                'tables_audited': self.audit_results.tables_audited,
                'processing_metrics': self.metrics
            },
            'summary': {
                'total_constraint_candidates': self.audit_results.total_constraint_candidates,
                'not_null_candidates': self.audit_results.not_null_candidates,
                'check_candidates': self.audit_results.check_candidates,
                'high_priority_tables': self.audit_results.high_priority_tables,
                'recommendations': self.audit_results.recommendations
            },
            'table_audits': [asdict(audit) for audit in self.audit_results.table_audits]
        }
        
        content = json.dumps(report, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info("json_report_saved",
                       file=output_file)
        
        return content
    
    def _generate_markdown_report(self, output_file: Optional[str] = None) -> str:
        """Generate Markdown format report."""
        content = f"""# Schema Constraint Audit Report

**Generated:** {self.audit_results.audit_timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Database:** {self.audit_results.database_name}  
**Tables Audited:** {self.audit_results.tables_audited}

## Executive Summary

- **Total Constraint Candidates:** {self.audit_results.total_constraint_candidates}
- **NOT NULL Candidates:** {self.audit_results.not_null_candidates}
- **CHECK Candidates:** {self.audit_results.check_candidates}
- **High Priority Tables:** {len(self.audit_results.high_priority_tables)}

## Recommendations

"""
        
        for rec in self.audit_results.recommendations:
            content += f"- {rec}\n"
        
        content += "\n## Detailed Table Analysis\n\n"
        
        for audit in self.audit_results.table_audits:
            content += f"### {audit.table_name.title()}\n\n"
            content += f"- **Priority:** {audit.migration_priority.upper()}\n"
            content += f"- **Total Columns:** {audit.total_columns}\n"
            content += f"- **Nullable Columns:** {audit.nullable_columns}\n"
            content += f"- **Constraint Candidates:** {len(audit.constraint_candidates)}\n\n"
            
            if audit.not_null_candidates:
                content += "#### NOT NULL Candidates\n\n"
                for candidate in audit.not_null_candidates:
                    content += f"- `{candidate.column_name}` ({candidate.data_type})\n"
                    content += f"  - **Reason:** {candidate.constraint_reason}\n"
                    content += f"  - **Risk:** {candidate.migration_risk}\n"
                    content += f"  - **NULL Count:** {candidate.current_null_count}\n\n"
            
            if audit.check_candidates:
                content += "#### CHECK Candidates\n\n"
                for candidate in audit.check_candidates:
                    content += f"- `{candidate.column_name}` ({candidate.data_type})\n"
                    content += f"  - **Values:** {', '.join(candidate.distinct_values)}\n"
                    content += f"  - **Constraint:** {candidate.recommended_constraint}\n\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info("markdown_report_saved",
                       file=output_file)
        
        return content


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Audit database schema for constraint candidates"
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://localhost/arxos_db"),
        help="PostgreSQL connection URL"
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
                structlog.stdlib.PositionalArgumentsFormatter(),
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
    
    # Run audit
    auditor = SchemaConstraintAuditor(args.database_url)
    success = auditor.audit_schema()
    
    if success:
        # Generate report
        report_content = auditor.generate_report(
            output_format=args.output_format,
            output_file=args.output_file
        )
        
        # Print summary
        if auditor.audit_results:
            print("\n" + "="*60)
            print("SCHEMA CONSTRAINT AUDIT SUMMARY")
            print("="*60)
            print(f"Tables audited: {auditor.audit_results.tables_audited}")
            print(f"Total candidates: {auditor.audit_results.total_constraint_candidates}")
            print(f"NOT NULL candidates: {auditor.audit_results.not_null_candidates}")
            print(f"CHECK candidates: {auditor.audit_results.check_candidates}")
            print(f"High priority tables: {len(auditor.audit_results.high_priority_tables)}")
            print("\nRecommendations:")
            for rec in auditor.audit_results.recommendations:
                print(f"- {rec}")
            print("="*60)
        
        # Print report if no output file specified
        if not args.output_file and report_content:
            print("\n" + report_content)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 