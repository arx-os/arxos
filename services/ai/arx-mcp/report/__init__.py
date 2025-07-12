"""
MCP Report Generation Package

This package contains the report generation functionality for MCP validation results,
including JSON and PDF audit reports with detailed compliance information.
"""

from .generate_report import ReportGenerator

__all__ = [
    'ReportGenerator'
] 