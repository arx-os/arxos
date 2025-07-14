#!/usr/bin/env python3
"""
Database Schema Export Tool

This script exports the current database schema and generates comprehensive
documentation for the Arxos database. It follows Arxos standards for
structured logging and comprehensive schema analysis.

Features:
- Exports complete database schema
- Generates table documentation
- Analyzes relationships and dependencies
- Creates index documentation
- Generates constraint documentation
- Exports migration history

Usage:
    python export_schema.py [--database-url postgresql://...]
    python export_schema.py --help
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
    numeric_precision: Optional[int]
    numeric_scale: Optional[int]
    is_primary_key: bool
    is_foreign_key: bool
    foreign_key_table: Optional[str]
    foreign_key_column: Optional[str]

@dataclass
class IndexInfo:
    """Information about a database index."""
    table_name: str
    index_name: str
    index_type: str
    columns: List[str]
    is_unique: bool
    is_primary: bool
    index_definition: str

@dataclass
class ConstraintInfo:
    """Information about a database constraint."""
    table_name: str
    constraint_name: str
    constraint_type: str
    column_name: Optional[str]
    check_clause: Optional[str]
    foreign_key_table: Optional[str]
    foreign_key_column: Optional[str]

@dataclass
class TableInfo:
    """Information about a database table."""
    table_name: str
    table_type: str
    row_count: int
    table_size_mb: float
    index_size_mb: float
    total_size_mb: float
    columns: List[ColumnInfo]
    indexes: List[IndexInfo]
    constraints: List[ConstraintInfo]
    dependencies: List[str]
    dependents: List[str]

@dataclass
class SchemaExport:
    """Complete schema export information."""
    export_timestamp: datetime
    database_name: str
    database_version: str
    total_tables: int
    total_indexes: int
    total_constraints: int
    tables: List[TableInfo]
    migration_history: List[Dict[str, Any]]

class SchemaExporter:
    """
    Exporter for comprehensive database schema documentation.
    
    Follows Arxos logging standards with structured logging, performance monitoring,
    and comprehensive schema analysis.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize the schema exporter.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.connection = None
        self.schema_export = None
        
        # Performance tracking
        self.metrics = {
            'tables_analyzed': 0,
            'indexes_found': 0,
            'constraints_found': 0,
            'processing_time_ms': 0,
            'errors': 0,
            'warnings': 0
        }
        
        logger.info("schema_exporter_initialized",
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
    
    def export_schema(self) -> bool:
        """
        Export comprehensive database schema.
        
        Returns:
            True if export successful, False otherwise
        """
        start_time = datetime.now()
        
        if not self.connect():
            return False
        
        try:
            logger.info("starting_schema_export")
            
            # Get database information
            db_info = self._get_database_info()
            
            # Export tables
            tables = self._export_tables()
            
            # Export migration history
            migration_history = self._export_migration_history()
            
            # Generate schema export
            self.schema_export = SchemaExport(
                export_timestamp=datetime.now(),
                database_name=db_info['database_name'],
                database_version=db_info['database_version'],
                total_tables=len(tables),
                total_indexes=sum(len(t.indexes) for t in tables),
                total_constraints=sum(len(t.constraints) for t in tables),
                tables=tables,
                migration_history=migration_history
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics['processing_time_ms'] = processing_time
            
            logger.info("schema_export_completed",
                       tables_analyzed=self.metrics['tables_analyzed'],
                       indexes_found=self.metrics['indexes_found'],
                       constraints_found=self.metrics['constraints_found'],
                       processing_time_ms=round(processing_time, 2))
            
            return True
            
        except Exception as e:
            logger.error("schema_export_failed",
                        error=str(e))
            return False
        finally:
            self.disconnect()
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Get basic database information."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    current_database() as database_name,
                    version() as database_version
            """)
            result = cursor.fetchone()
            return dict(result)
    
    def _export_tables(self) -> List[TableInfo]:
        """Export all tables with their metadata."""
        tables = []
        
        # Get all tables
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    table_name,
                    table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            for row in cursor.fetchall():
                table_name = row['table_name']
                table_type = row['table_type']
                
                logger.debug("exporting_table",
                           table_name=table_name)
                
                # Get table metadata
                metadata = self._get_table_metadata(table_name)
                
                # Get columns
                columns = self._get_table_columns(table_name)
                
                # Get indexes
                indexes = self._get_table_indexes(table_name)
                
                # Get constraints
                constraints = self._get_table_constraints(table_name)
                
                # Get dependencies
                dependencies = self._get_table_dependencies(table_name)
                dependents = self._get_table_dependents(table_name)
                
                table_info = TableInfo(
                    table_name=table_name,
                    table_type=table_type,
                    row_count=metadata['row_count'],
                    table_size_mb=metadata['table_size_mb'],
                    index_size_mb=metadata['index_size_mb'],
                    total_size_mb=metadata['total_size_mb'],
                    columns=columns,
                    indexes=indexes,
                    constraints=constraints,
                    dependencies=dependencies,
                    dependents=dependents
                )
                
                tables.append(table_info)
                self.metrics['tables_analyzed'] += 1
                self.metrics['indexes_found'] += len(indexes)
                self.metrics['constraints_found'] += len(constraints)
        
        return tables
    
    def _get_table_metadata(self, table_name: str) -> Dict[str, Any]:
        """Get table metadata including size and row count."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    n_tup_ins + n_tup_upd + n_tup_del as total_operations,
                    n_live_tup as row_count,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
                    pg_total_relation_size(schemaname||'.'||tablename) as total_size_bytes,
                    pg_relation_size(schemaname||'.'||tablename) as table_size_bytes,
                    pg_indexes_size(schemaname||'.'||tablename) as index_size_bytes
                FROM pg_stat_user_tables 
                WHERE tablename = %s
            """, (table_name,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'row_count': result['row_count'],
                    'total_size_mb': result['total_size_bytes'] / (1024 * 1024),
                    'table_size_mb': result['table_size_bytes'] / (1024 * 1024),
                    'index_size_mb': result['index_size_bytes'] / (1024 * 1024)
                }
            else:
                return {
                    'row_count': 0,
                    'total_size_mb': 0,
                    'table_size_mb': 0,
                    'index_size_mb': 0
                }
    
    def _get_table_columns(self, table_name: str) -> List[ColumnInfo]:
        """Get all columns for a table."""
        columns = []
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            for row in cursor.fetchall():
                # Check if column is primary key
                cursor.execute("""
                    SELECT 1 FROM information_schema.key_column_usage 
                    WHERE table_name = %s AND column_name = %s 
                    AND constraint_name LIKE '%%_pkey'
                """, (table_name, row['column_name']))
                is_primary_key = cursor.fetchone() is not None
                
                # Check if column is foreign key
                cursor.execute("""
                    SELECT 
                        referenced_table_name,
                        referenced_column_name
                    FROM information_schema.key_column_usage kcu
                    JOIN information_schema.table_constraints tc 
                        ON kcu.constraint_name = tc.constraint_name
                    WHERE kcu.table_name = %s 
                    AND kcu.column_name = %s 
                    AND tc.constraint_type = 'FOREIGN KEY'
                """, (table_name, row['column_name']))
                fk_result = cursor.fetchone()
                
                column_info = ColumnInfo(
                    table_name=table_name,
                    column_name=row['column_name'],
                    data_type=row['data_type'],
                    is_nullable=row['is_nullable'] == 'YES',
                    column_default=row['column_default'],
                    character_maximum_length=row['character_maximum_length'],
                    numeric_precision=row['numeric_precision'],
                    numeric_scale=row['numeric_scale'],
                    is_primary_key=is_primary_key,
                    is_foreign_key=fk_result is not None,
                    foreign_key_table=fk_result['referenced_table_name'] if fk_result else None,
                    foreign_key_column=fk_result['referenced_column_name'] if fk_result else None
                )
                
                columns.append(column_info)
        
        return columns
    
    def _get_table_indexes(self, table_name: str) -> List[IndexInfo]:
        """Get all indexes for a table."""
        indexes = []
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    indexname,
                    indexdef,
                    indisunique as is_unique,
                    indisprimary as is_primary
                FROM pg_indexes 
                WHERE tablename = %s
                ORDER BY indexname
            """, (table_name,))
            
            for row in cursor.fetchall():
                # Parse index columns from definition
                columns = self._parse_index_columns(row['indexdef'])
                
                # Determine index type
                index_type = 'btree'  # Default
                if 'USING gist' in row['indexdef']:
                    index_type = 'gist'
                elif 'USING gin' in row['indexdef']:
                    index_type = 'gin'
                elif 'USING hash' in row['indexdef']:
                    index_type = 'hash'
                
                index_info = IndexInfo(
                    table_name=table_name,
                    index_name=row['indexname'],
                    index_type=index_type,
                    columns=columns,
                    is_unique=row['is_unique'],
                    is_primary=row['is_primary'],
                    index_definition=row['indexdef']
                )
                
                indexes.append(index_info)
        
        return indexes
    
    def _parse_index_columns(self, index_definition: str) -> List[str]:
        """Parse column names from index definition."""
        columns = []
        
        # Extract columns from index definition
        # Example: CREATE INDEX idx_users_email ON users (email)
        if '(' in index_definition and ')' in index_definition:
            column_part = index_definition.split('(')[1].split(')')[0]
            columns = [col.strip() for col in column_part.split(',')]
        
        return columns
    
    def _get_table_constraints(self, table_name: str) -> List[ConstraintInfo]:
        """Get all constraints for a table."""
        constraints = []
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get check constraints
            cursor.execute("""
                SELECT 
                    constraint_name,
                    check_clause
                FROM information_schema.check_constraints cc
                JOIN information_schema.table_constraints tc 
                    ON cc.constraint_name = tc.constraint_name
                WHERE tc.table_name = %s
            """, (table_name,))
            
            for row in cursor.fetchall():
                constraint_info = ConstraintInfo(
                    table_name=table_name,
                    constraint_name=row['constraint_name'],
                    constraint_type='CHECK',
                    column_name=None,
                    check_clause=row['check_clause'],
                    foreign_key_table=None,
                    foreign_key_column=None
                )
                constraints.append(constraint_info)
            
            # Get foreign key constraints
            cursor.execute("""
                SELECT 
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name as foreign_table_name,
                    ccu.column_name as foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
            """, (table_name,))
            
            for row in cursor.fetchall():
                constraint_info = ConstraintInfo(
                    table_name=table_name,
                    constraint_name=row['constraint_name'],
                    constraint_type='FOREIGN KEY',
                    column_name=row['column_name'],
                    check_clause=None,
                    foreign_key_table=row['foreign_table_name'],
                    foreign_key_column=row['foreign_column_name']
                )
                constraints.append(constraint_info)
        
        return constraints
    
    def _get_table_dependencies(self, table_name: str) -> List[str]:
        """Get tables that this table depends on (foreign keys)."""
        dependencies = []
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT ccu.table_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
            """, (table_name,))
            
            for row in cursor.fetchall():
                dependencies.append(row[0])
        
        return dependencies
    
    def _get_table_dependents(self, table_name: str) -> List[str]:
        """Get tables that depend on this table (referenced by foreign keys)."""
        dependents = []
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT tc.table_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND ccu.table_name = %s
            """, (table_name,))
            
            for row in cursor.fetchall():
                dependents.append(row[0])
        
        return dependents
    
    def _export_migration_history(self) -> List[Dict[str, Any]]:
        """Export migration history from alembic_version table."""
        migration_history = []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM alembic_version")
                result = cursor.fetchone()
                if result:
                    migration_history.append(dict(result))
        except Exception as e:
            logger.warning("no_migration_history_found",
                          error=str(e))
        
        return migration_history
    
    def generate_documentation(self, output_format: str = "json", output_file: Optional[str] = None) -> str:
        """
        Generate schema documentation in specified format.
        
        Args:
            output_format: 'json' or 'markdown'
            output_file: Optional output file path
            
        Returns:
            Generated documentation content
        """
        if not self.schema_export:
            logger.warning("no_schema_export_to_document")
            return ""
        
        logger.info("generating_schema_documentation",
                   format=output_format,
                   total_tables=self.schema_export.total_tables)
        
        if output_format.lower() == "json":
            return self._generate_json_documentation(output_file)
        elif output_format.lower() == "markdown":
            return self._generate_markdown_documentation(output_file)
        else:
            logger.error("unsupported_output_format",
                        format=output_format)
            return ""
    
    def _generate_json_documentation(self, output_file: Optional[str] = None) -> str:
        """Generate JSON format documentation."""
        documentation = {
            'metadata': {
                'export_timestamp': self.schema_export.export_timestamp.isoformat(),
                'database_name': self.schema_export.database_name,
                'database_version': self.schema_export.database_version,
                'total_tables': self.schema_export.total_tables,
                'total_indexes': self.schema_export.total_indexes,
                'total_constraints': self.schema_export.total_constraints,
                'processing_metrics': self.metrics
            },
            'tables': [asdict(table) for table in self.schema_export.tables],
            'migration_history': self.schema_export.migration_history
        }
        
        content = json.dumps(documentation, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info("json_documentation_saved",
                       file=output_file)
        
        return content
    
    def _generate_markdown_documentation(self, output_file: Optional[str] = None) -> str:
        """Generate Markdown format documentation."""
        content = f"""# Database Schema Documentation

**Generated:** {self.schema_export.export_timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Database:** {self.schema_export.database_name}  
**Version:** {self.schema_export.database_version}

## Schema Overview

- **Total Tables:** {self.schema_export.total_tables}
- **Total Indexes:** {self.schema_export.total_indexes}
- **Total Constraints:** {self.schema_export.total_constraints}

## Tables

"""
        
        for table in self.schema_export.tables:
            content += f"### {table.table_name.title()}\n\n"
            content += f"- **Type:** {table.table_type}\n"
            content += f"- **Rows:** {table.row_count:,}\n"
            content += f"- **Size:** {table.total_size_mb:.2f}MB (table: {table.table_size_mb:.2f}MB, indexes: {table.index_size_mb:.2f}MB)\n"
            content += f"- **Columns:** {len(table.columns)}\n"
            content += f"- **Indexes:** {len(table.indexes)}\n"
            content += f"- **Constraints:** {len(table.constraints)}\n\n"
            
            # Dependencies
            if table.dependencies:
                content += f"- **Dependencies:** {', '.join(table.dependencies)}\n"
            if table.dependents:
                content += f"- **Dependents:** {', '.join(table.dependents)}\n"
            
            content += "\n#### Columns\n\n"
            for column in table.columns:
                content += f"- **{column.column_name}** (`{column.data_type}`)"
                if column.is_primary_key:
                    content += " PRIMARY KEY"
                if column.is_foreign_key:
                    content += f" → {column.foreign_key_table}.{column.foreign_key_column}"
                if not column.is_nullable:
                    content += " NOT NULL"
                if column.column_default:
                    content += f" DEFAULT {column.column_default}"
                content += "\n"
            
            content += "\n#### Indexes\n\n"
            for index in table.indexes:
                content += f"- **{index.index_name}** ({index.index_type})"
                if index.is_unique:
                    content += " UNIQUE"
                if index.is_primary:
                    content += " PRIMARY"
                content += f" on {', '.join(index.columns)}\n"
            
            content += "\n#### Constraints\n\n"
            for constraint in table.constraints:
                content += f"- **{constraint.constraint_name}** ({constraint.constraint_type})"
                if constraint.column_name:
                    content += f" on {constraint.column_name}"
                if constraint.check_clause:
                    content += f": {constraint.check_clause}"
                if constraint.foreign_key_table:
                    content += f" → {constraint.foreign_key_table}.{constraint.foreign_key_column}"
                content += "\n"
            
            content += "\n---\n\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info("markdown_documentation_saved",
                       file=output_file)
        
        return content


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Export database schema documentation"
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
        help="Output format for the documentation (default: json)"
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
    
    # Export schema
    exporter = SchemaExporter(args.database_url)
    success = exporter.export_schema()
    
    if success:
        # Generate documentation
        doc_content = exporter.generate_documentation(
            output_format=args.output_format,
            output_file=args.output_file
        )
        
        # Print summary
        if exporter.schema_export:
            print("\n" + "="*60)
            print("SCHEMA EXPORT SUMMARY")
            print("="*60)
            print(f"Database: {exporter.schema_export.database_name}")
            print(f"Tables: {exporter.schema_export.total_tables}")
            print(f"Indexes: {exporter.schema_export.total_indexes}")
            print(f"Constraints: {exporter.schema_export.total_constraints}")
            print("="*60)
        
        # Print documentation if no output file specified
        if not args.output_file and doc_content:
            print("\n" + doc_content)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 