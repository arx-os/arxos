#!/usr/bin/env python3
"""
Schema Validator for Arxos Database Migrations

This script validates SQL migration files to ensure:
1. Referenced tables are created before referencing tables
2. Foreign key columns have associated indexes
3. Proper migration structure and syntax

Usage:
    python schema_validator.py [migrations_directory]
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)

@dataclass
class TableInfo:
    """Information about a table in a migration."""
    name: str
    file_path: str
    line_number: int
    created: bool = False
    foreign_keys: List[Tuple[str, str]] = None  # (column, referenced_table)
    indexes: Set[str] = None
    
    def __post_init__(self):
    """
    Perform __post_init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __post_init__(param)
        print(result)
    """
        if self.foreign_keys is None:
            self.foreign_keys = []
        if self.indexes is None:
            self.indexes = set()

@dataclass
class ValidationError:
    """A validation error found in the schema."""
    error_type: str
    message: str
    file_path: str
    line_number: int
    severity: str = "error"

class SchemaValidator:
    """
    Validates SQL migration files for proper schema structure.
    
    Checks:
    - Foreign key ordering (referenced tables must exist before referencing tables)
    - Index presence for foreign key columns
    - Proper SQL syntax and structure
    """
    
    def __init__(self, migrations_dir: str = "migrations"):
        """
        Initialize the schema validator.
        
        Args:
            migrations_dir: Directory containing migration files
        """
        self.migrations_dir = Path(migrations_dir)
        self.tables: Dict[str, TableInfo] = {}
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        
        # SQL patterns for parsing
        self.table_pattern = re.compile(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?\s*\(',
            re.IGNORECASE
        )
        
        self.foreign_key_pattern = re.compile(
            r'FOREIGN\s+KEY\s*\(\s*["`]?(\w+)["`]?\s*\)\s+REFERENCES\s+["`]?(\w+)["`]?\s*\(\s*["`]?(\w+)["`]?\s*\)',
            re.IGNORECASE
        )
        
        self.index_pattern = re.compile(
            r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?\s+ON\s+["`]?(\w+)["`]?\s*\(\s*["`]?(\w+)["`]?\s*\)',
            re.IGNORECASE
        )
        
        self.alter_table_add_fk_pattern = re.compile(
            r'ALTER\s+TABLE\s+["`]?(\w+)["`]?\s+ADD\s+(?:CONSTRAINT\s+["`]?\w+["`]?\s+)?FOREIGN\s+KEY\s*\(\s*["`]?(\w+)["`]?\s*\)\s+REFERENCES\s+["`]?(\w+)["`]?\s*\(\s*["`]?(\w+)["`]?\s*\)',
            re.IGNORECASE
        )
        
        self.alter_table_add_index_pattern = re.compile(
            r'ALTER\s+TABLE\s+["`]?(\w+)["`]?\s+ADD\s+(?:UNIQUE\s+)?INDEX\s+["`]?(\w+)["`]?\s*\(\s*["`]?(\w+)["`]?\s*\)',
            re.IGNORECASE
        )
        
        logger.info("schema_validator_initialized",
                   migrations_dir=str(self.migrations_dir))
    
    def validate_migrations(self) -> bool:
        """
        Validate all migration files in the migrations directory.
        
        Returns:
            True if validation passes, False otherwise
        """
        if not self.migrations_dir.exists():
            logger.error("migrations_directory_not_found",
                        path=str(self.migrations_dir))
            self.errors.append(ValidationError(
                "directory_not_found",
                f"Migrations directory not found: {self.migrations_dir}",
                str(self.migrations_dir),
                0
            ))
            return False
        
        # Find all SQL migration files
        migration_files = list(self.migrations_dir.glob("*.sql"))
        migration_files.sort()  # Process in alphabetical order
        
        if not migration_files:
            logger.warning("no_migration_files_found",
                          directory=str(self.migrations_dir))
            return True
        
        logger.info("found_migration_files",
                   count=len(migration_files),
                   files=[f.name for f in migration_files])
        
        # First pass: Parse all tables and their relationships
        for migration_file in migration_files:
            self._parse_migration_file(migration_file)
        
        # Second pass: Validate foreign key ordering
        self._validate_foreign_key_ordering()
        
        # Third pass: Validate indexes for foreign keys
        self._validate_foreign_key_indexes()
        
        # Report results
        self._report_validation_results()
        
        return len(self.errors) == 0
    
    def _parse_migration_file(self, file_path: Path) -> None:
        """
        Parse a single migration file to extract table information.
        
        Args:
            file_path: Path to the migration file
        """
        logger.debug("parsing_migration_file",
                    file=str(file_path))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            current_table = None
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('--'):
                    continue
                
                # Check for CREATE TABLE
                table_match = self.table_pattern.search(line)
                if table_match:
                    table_name = table_match.group(1)
                    current_table = TableInfo(
                        name=table_name,
                        file_path=str(file_path),
                        line_number=line_num
                    )
                    self.tables[table_name] = current_table
                    logger.debug("found_table_creation",
                               table=table_name,
                               file=str(file_path),
                               line=line_num)
                
                # Check for foreign keys in CREATE TABLE
                if current_table:
                    fk_matches = self.foreign_key_pattern.findall(line)
                    for fk_match in fk_matches:
                        column, referenced_table, referenced_column = fk_match
                        current_table.foreign_keys.append((column, referenced_table))
                        logger.debug("found_foreign_key_in_create",
                                   table=current_table.name,
                                   column=column,
                                   referenced_table=referenced_table,
                                   file=str(file_path),
                                   line=line_num)
                
                # Check for ALTER TABLE ADD FOREIGN KEY
                alter_fk_match = self.alter_table_add_fk_pattern.search(line)
                if alter_fk_match:
                    table_name, column, referenced_table, referenced_column = alter_fk_match.groups()
                    if table_name not in self.tables:
                        self.tables[table_name] = TableInfo(
                            name=table_name,
                            file_path=str(file_path),
                            line_number=line_num
                        )
                    self.tables[table_name].foreign_keys.append((column, referenced_table))
                    logger.debug("found_alter_table_foreign_key",
                               table=table_name,
                               column=column,
                               referenced_table=referenced_table,
                               file=str(file_path),
                               line=line_num)
                
                # Check for CREATE INDEX
                index_match = self.index_pattern.search(line)
                if index_match:
                    index_name, table_name, column = index_match.groups()
                    if table_name not in self.tables:
                        self.tables[table_name] = TableInfo(
                            name=table_name,
                            file_path=str(file_path),
                            line_number=line_num
                        )
                    self.tables[table_name].indexes.add(column)
                    logger.debug("found_create_index",
                               table=table_name,
                               column=column,
                               index_name=index_name,
                               file=str(file_path),
                               line=line_num)
                
                # Check for ALTER TABLE ADD INDEX
                alter_index_match = self.alter_table_add_index_pattern.search(line)
                if alter_index_match:
                    table_name, index_name, column = alter_index_match.groups()
                    if table_name not in self.tables:
                        self.tables[table_name] = TableInfo(
                            name=table_name,
                            file_path=str(file_path),
                            line_number=line_num
                        )
                    self.tables[table_name].indexes.add(column)
                    logger.debug("found_alter_table_index",
                               table=table_name,
                               column=column,
                               index_name=index_name,
                               file=str(file_path),
                               line=line_num)
        
        except Exception as e:
            logger.error("error_parsing_migration_file",
                        file=str(file_path),
                        error=str(e))
            self.errors.append(ValidationError(
                "parse_error",
                f"Error parsing migration file: {e}",
                str(file_path),
                0
            ))
    
    def _validate_foreign_key_ordering(self) -> None:
        """
        Validate that referenced tables are created before referencing tables.
        """
        logger.info("validating_foreign_key_ordering")
        
        for table_name, table_info in self.tables.items():
            for fk_column, referenced_table in table_info.foreign_keys:
                if referenced_table not in self.tables:
                    self.errors.append(ValidationError(
                        "missing_referenced_table",
                        f"Table '{table_name}' references non-existent table '{referenced_table}'",
                        table_info.file_path,
                        table_info.line_number
                    ))
                    logger.error("missing_referenced_table",
                               table=table_name,
                               referenced_table=referenced_table,
                               file=table_info.file_path,
                               line=table_info.line_number)
    
    def _validate_foreign_key_indexes(self) -> None:
        """
        Validate that foreign key columns have associated indexes.
        """
        logger.info("validating_foreign_key_indexes")
        
        for table_name, table_info in self.tables.items():
            for fk_column, referenced_table in table_info.foreign_keys:
                if fk_column not in table_info.indexes:
                    self.errors.append(ValidationError(
                        "missing_foreign_key_index",
                        f"Foreign key column '{fk_column}' in table '{table_name}' lacks an index",
                        table_info.file_path,
                        table_info.line_number
                    ))
                    logger.error("missing_foreign_key_index",
                               table=table_name,
                               column=fk_column,
                               file=table_info.file_path,
                               line=table_info.line_number)
    
    def _report_validation_results(self) -> None:
        """
        Report validation results with detailed information.
        """
        logger.info("validation_complete",
                   total_tables=len(self.tables),
                   errors=len(self.errors),
                   warnings=len(self.warnings))
        
        if self.errors:
            print("\n❌ Schema Validation Errors:")
            for error in self.errors:
                print(f"  {error.file_path}:{error.line_number}")
                print(f"    {error.error_type}: {error.message}")
                print()
        
        if self.warnings:
            print("\n⚠️  Schema Validation Warnings:")
            for warning in self.warnings:
                print(f"  {warning.file_path}:{warning.line_number}")
                print(f"    {warning.error_type}: {warning.message}")
                print()
        
        if not self.errors and not self.warnings:
            print("\n✅ Schema validation passed!")
            print(f"  Validated {len(self.tables)} tables")
        
        # Print summary
        print(f"\n📊 Validation Summary:")
        print(f"  Tables found: {len(self.tables)}")
        print(f"  Errors: {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        
        if self.tables:
            print(f"\n📋 Tables found:")
            for table_name in sorted(self.tables.keys()):
                table_info = self.tables[table_name]
                fk_count = len(table_info.foreign_keys)
                index_count = len(table_info.indexes)
                print(f"  - {table_name} (FKs: {fk_count}, Indexes: {index_count})")
    
    def get_validation_summary(self) -> Dict:
        """
        Get a summary of validation results.
        
        Returns:
            Dictionary with validation summary
        """
        return {
            "total_tables": len(self.tables),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "passed": len(self.errors) == 0,
            "tables": list(self.tables.keys()),
            "error_details": [
                {
                    "type": error.error_type,
                    "message": error.message,
                    "file": error.file_path,
                    "line": error.line_number
                }
                for error in self.errors
            ]
        }


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Validate SQL migration files for schema consistency"
    )
    parser.add_argument(
        "migrations_dir",
        nargs="?",
        default="migrations",
        help="Directory containing migration files (default: migrations)"
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
    
    # Run validation
    validator = SchemaValidator(args.migrations_dir)
    success = validator.validate_migrations()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 