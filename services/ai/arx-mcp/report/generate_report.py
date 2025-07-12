"""
MCP Report Generation Module

This module provides comprehensive report generation capabilities for MCP validation results,
including JSON and PDF audit reports with detailed compliance information, violation summaries,
and actionable recommendations.

Key Features:
- JSON report generation with detailed validation data
- PDF report generation with professional formatting
- Violation categorization and prioritization
- Compliance scoring and metrics
- Actionable recommendations
- Multi-format export capabilities
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import math

from ..models.mcp_models import (
    ComplianceReport, MCPValidationReport, ValidationResult, ValidationViolation,
    RuleSeverity, RuleCategory
)


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Comprehensive report generator for MCP validation results
    
    This class provides:
    - JSON report generation with detailed validation data
    - PDF report generation with professional formatting
    - Violation categorization and prioritization
    - Compliance scoring and metrics
    - Actionable recommendations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the report generator
        
        Args:
            config: Configuration dictionary for report generation
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Report templates and styling
        self.templates = self._load_templates()
        self.styles = self._load_styles()
        
        self.logger.info("Report Generator initialized")
    
    def generate_json_report(self, compliance_report: ComplianceReport, 
                           output_path: Optional[str] = None) -> str:
        """
        Generate comprehensive JSON report
        
        Args:
            compliance_report: Compliance report to convert
            output_path: Optional output file path
            
        Returns:
            JSON report content
        """
        try:
            # Create detailed JSON structure
            report_data = self._create_json_report_structure(compliance_report)
            
            # Convert to JSON string
            json_content = json.dumps(report_data, indent=2, default=str)
            
            # Write to file if path provided
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                
                self.logger.info(f"JSON report saved to: {output_path}")
            
            return json_content
            
        except Exception as e:
            self.logger.error(f"Error generating JSON report: {e}")
            raise
    
    def generate_pdf_report(self, compliance_report: ComplianceReport, 
                          output_path: str) -> str:
        """
        Generate comprehensive PDF report
        
        Args:
            compliance_report: Compliance report to convert
            output_path: Output file path
            
        Returns:
            Path to generated PDF file
        """
        try:
            # Create PDF content
            pdf_content = self._create_pdf_report_content(compliance_report)
            
            # Write PDF file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pdf_content)
            
            self.logger.info(f"PDF report saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            raise
    
    def generate_summary_report(self, compliance_report: ComplianceReport) -> Dict[str, Any]:
        """
        Generate executive summary report
        
        Args:
            compliance_report: Compliance report to summarize
            
        Returns:
            Summary report data
        """
        try:
            summary = {
                'building_info': {
                    'building_id': compliance_report.building_id,
                    'building_name': compliance_report.building_name,
                    'report_date': compliance_report.generated_date.isoformat()
                },
                'compliance_overview': {
                    'overall_score': compliance_report.overall_compliance_score,
                    'critical_violations': compliance_report.critical_violations,
                    'total_violations': compliance_report.total_violations,
                    'total_warnings': compliance_report.total_warnings,
                    'total_mcps': len(compliance_report.validation_reports)
                },
                'violation_summary': self._create_violation_summary(compliance_report),
                'recommendations': compliance_report.recommendations,
                'priority_actions': self._identify_priority_actions(compliance_report)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary report: {e}")
            raise
    
    def _create_json_report_structure(self, compliance_report: ComplianceReport) -> Dict[str, Any]:
        """Create detailed JSON report structure"""
        return {
            'report_metadata': {
                'report_type': 'MCP Compliance Report',
                'generated_date': compliance_report.generated_date.isoformat(),
                'version': '1.0',
                'generator': 'Arxos MCP Report Generator'
            },
            'building_information': {
                'building_id': compliance_report.building_id,
                'building_name': compliance_report.building_name
            },
            'compliance_summary': {
                'overall_compliance_score': compliance_report.overall_compliance_score,
                'critical_violations': compliance_report.critical_violations,
                'total_violations': compliance_report.total_violations,
                'total_warnings': compliance_report.total_warnings,
                'total_mcps_evaluated': len(compliance_report.validation_reports)
            },
            'mcp_validation_reports': [
                self._create_mcp_report_data(report) 
                for report in compliance_report.validation_reports
            ],
            'violation_analysis': self._create_violation_analysis(compliance_report),
            'recommendations': compliance_report.recommendations,
            'priority_actions': self._identify_priority_actions(compliance_report),
            'detailed_results': self._create_detailed_results(compliance_report)
        }
    
    def _create_mcp_report_data(self, mcp_report: MCPValidationReport) -> Dict[str, Any]:
        """Create MCP report data structure"""
        return {
            'mcp_information': {
                'mcp_id': mcp_report.mcp_id,
                'mcp_name': mcp_report.mcp_name,
                'jurisdiction': mcp_report.jurisdiction.to_dict(),
                'validation_date': mcp_report.validation_date.isoformat()
            },
            'validation_summary': {
                'total_rules': mcp_report.total_rules,
                'passed_rules': mcp_report.passed_rules,
                'failed_rules': mcp_report.failed_rules,
                'total_violations': mcp_report.total_violations,
                'total_warnings': mcp_report.total_warnings,
                'compliance_percentage': (mcp_report.passed_rules / mcp_report.total_rules * 100) 
                    if mcp_report.total_rules > 0 else 0.0
            },
            'rule_results': [
                self._create_rule_result_data(result) 
                for result in mcp_report.results
            ],
            'violations_by_category': self._group_violations_by_category(mcp_report.results),
            'warnings_by_category': self._group_warnings_by_category(mcp_report.results)
        }
    
    def _create_rule_result_data(self, result: ValidationResult) -> Dict[str, Any]:
        """Create rule result data structure"""
        return {
            'rule_information': {
                'rule_id': result.rule_id,
                'rule_name': result.rule_name,
                'category': result.category.value
            },
            'execution_summary': {
                'passed': result.passed,
                'execution_time': result.execution_time,
                'timestamp': result.timestamp.isoformat()
            },
            'violations': [
                self._create_violation_data(violation) 
                for violation in result.violations
            ],
            'warnings': [
                self._create_violation_data(warning) 
                for warning in result.warnings
            ],
            'calculations': result.calculations
        }
    
    def _create_violation_data(self, violation: ValidationViolation) -> Dict[str, Any]:
        """Create violation data structure"""
        return {
            'rule_id': violation.rule_id,
            'rule_name': violation.rule_name,
            'category': violation.category.value,
            'severity': violation.severity.value,
            'message': violation.message,
            'code_reference': violation.code_reference,
            'element_information': {
                'element_id': violation.element_id,
                'element_type': violation.element_type,
                'location': violation.location
            },
            'validation_details': {
                'calculated_value': violation.calculated_value,
                'expected_value': violation.expected_value
            },
            'timestamp': violation.timestamp.isoformat()
        }
    
    def _create_violation_analysis(self, compliance_report: ComplianceReport) -> Dict[str, Any]:
        """Create comprehensive violation analysis"""
        all_violations = []
        all_warnings = []
        
        for report in compliance_report.validation_reports:
            for result in report.results:
                all_violations.extend(result.violations)
                all_warnings.extend(result.warnings)
        
        return {
            'violation_statistics': {
                'total_violations': len(all_violations),
                'critical_violations': len([v for v in all_violations if v.severity == RuleSeverity.ERROR]),
                'warning_violations': len([v for v in all_violations if v.severity == RuleSeverity.WARNING]),
                'info_violations': len([v for v in all_violations if v.severity == RuleSeverity.INFO])
            },
            'violations_by_category': self._group_violations_by_category_from_list(all_violations),
            'violations_by_severity': self._group_violations_by_severity(all_violations),
            'most_common_violations': self._identify_most_common_violations(all_violations),
            'warnings_by_category': self._group_violations_by_category_from_list(all_warnings)
        }
    
    def _create_detailed_results(self, compliance_report: ComplianceReport) -> Dict[str, Any]:
        """Create detailed results section"""
        return {
            'performance_metrics': {
                'total_execution_time': sum(
                    sum(r.execution_time for r in report.results)
                    for report in compliance_report.validation_reports
                ),
                'average_rule_execution_time': self._calculate_average_execution_time(compliance_report),
                'total_rules_evaluated': sum(
                    len(report.results) for report in compliance_report.validation_reports
                )
            },
            'jurisdiction_analysis': self._analyze_jurisdictions(compliance_report),
            'category_performance': self._analyze_category_performance(compliance_report)
        }
    
    def _create_pdf_report_content(self, compliance_report: ComplianceReport) -> str:
        """Create PDF report content (simplified HTML for now)"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MCP Compliance Report - {compliance_report.building_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .summary {{ background-color: #f5f5f5; padding: 20px; margin: 20px 0; }}
        .violation {{ background-color: #ffe6e6; padding: 10px; margin: 10px 0; border-left: 4px solid #ff0000; }}
        .warning {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
        .recommendation {{ background-color: #d1ecf1; padding: 10px; margin: 10px 0; border-left: 4px solid #17a2b8; }}
        .section {{ margin: 30px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e9ecef; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MCP Compliance Report</h1>
        <h2>{compliance_report.building_name}</h2>
        <p>Generated: {compliance_report.generated_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h3>Executive Summary</h3>
        <div class="metric">
            <strong>Overall Compliance Score:</strong> {compliance_report.overall_compliance_score:.1f}%
        </div>
        <div class="metric">
            <strong>Critical Violations:</strong> {compliance_report.critical_violations}
        </div>
        <div class="metric">
            <strong>Total Violations:</strong> {compliance_report.total_violations}
        </div>
        <div class="metric">
            <strong>Total Warnings:</strong> {compliance_report.total_warnings}
        </div>
    </div>
    
    <div class="section">
        <h3>Critical Violations</h3>
        {self._generate_violations_html(compliance_report, RuleSeverity.ERROR)}
    </div>
    
    <div class="section">
        <h3>Warnings</h3>
        {self._generate_violations_html(compliance_report, RuleSeverity.WARNING)}
    </div>
    
    <div class="section">
        <h3>Recommendations</h3>
        {self._generate_recommendations_html(compliance_report)}
    </div>
    
    <div class="section">
        <h3>Detailed Results by MCP</h3>
        {self._generate_mcp_details_html(compliance_report)}
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _generate_violations_html(self, compliance_report: ComplianceReport, 
                                severity: RuleSeverity) -> str:
        """Generate HTML for violations of specific severity"""
        violations = []
        
        for report in compliance_report.validation_reports:
            for result in report.results:
                for violation in result.violations:
                    if violation.severity == severity:
                        violations.append(violation)
        
        if not violations:
            return f"<p>No {severity.value} violations found.</p>"
        
        html = ""
        for violation in violations:
            html += f"""
            <div class="{'violation' if severity == RuleSeverity.ERROR else 'warning'}">
                <h4>{violation.rule_name}</h4>
                <p><strong>Category:</strong> {violation.category.value}</p>
                <p><strong>Message:</strong> {violation.message}</p>
                <p><strong>Element:</strong> {violation.element_type} ({violation.element_id})</p>
                {f'<p><strong>Code Reference:</strong> {violation.code_reference}</p>' if violation.code_reference else ''}
            </div>
            """
        
        return html
    
    def _generate_recommendations_html(self, compliance_report: ComplianceReport) -> str:
        """Generate HTML for recommendations"""
        if not compliance_report.recommendations:
            return "<p>No specific recommendations at this time.</p>"
        
        html = ""
        for recommendation in compliance_report.recommendations:
            html += f'<div class="recommendation"><p>{recommendation}</p></div>'
        
        return html
    
    def _generate_mcp_details_html(self, compliance_report: ComplianceReport) -> str:
        """Generate HTML for MCP details"""
        html = ""
        
        for report in compliance_report.validation_reports:
            html += f"""
            <div class="section">
                <h4>{report.mcp_name}</h4>
                <p><strong>Jurisdiction:</strong> {report.jurisdiction.country}/{report.jurisdiction.state or 'N/A'}</p>
                <p><strong>Rules Evaluated:</strong> {report.total_rules}</p>
                <p><strong>Passed:</strong> {report.passed_rules}</p>
                <p><strong>Failed:</strong> {report.failed_rules}</p>
                <p><strong>Violations:</strong> {report.total_violations}</p>
                <p><strong>Warnings:</strong> {report.total_warnings}</p>
            </div>
            """
        
        return html
    
    def _create_violation_summary(self, compliance_report: ComplianceReport) -> Dict[str, Any]:
        """Create violation summary"""
        all_violations = []
        for report in compliance_report.validation_reports:
            for result in report.results:
                all_violations.extend(result.violations)
        
        return {
            'total_violations': len(all_violations),
            'by_severity': {
                'critical': len([v for v in all_violations if v.severity == RuleSeverity.ERROR]),
                'warning': len([v for v in all_violations if v.severity == RuleSeverity.WARNING]),
                'info': len([v for v in all_violations if v.severity == RuleSeverity.INFO])
            },
            'by_category': self._group_violations_by_category_from_list(all_violations),
            'most_common': self._identify_most_common_violations(all_violations)
        }
    
    def _identify_priority_actions(self, compliance_report: ComplianceReport) -> List[Dict[str, Any]]:
        """Identify priority actions based on violations"""
        priority_actions = []
        
        # Collect all critical violations
        critical_violations = []
        for report in compliance_report.validation_reports:
            for result in report.results:
                for violation in result.violations:
                    if violation.severity == RuleSeverity.ERROR:
                        critical_violations.append(violation)
        
        # Group by category and create priority actions
        violations_by_category = {}
        for violation in critical_violations:
            category = violation.category.value
            if category not in violations_by_category:
                violations_by_category[category] = []
            violations_by_category[category].append(violation)
        
        for category, violations in violations_by_category.items():
            priority_actions.append({
                'priority': 'HIGH',
                'category': category,
                'action': f"Address {len(violations)} critical violations in {category}",
                'violations': [v.rule_name for v in violations[:3]],  # Top 3
                'estimated_effort': self._estimate_effort(category, len(violations))
            })
        
        return priority_actions
    
    def _group_violations_by_category(self, results: List[ValidationResult]) -> Dict[str, int]:
        """Group violations by category"""
        violations_by_category = {}
        
        for result in results:
            for violation in result.violations:
                category = violation.category.value
                violations_by_category[category] = violations_by_category.get(category, 0) + 1
        
        return violations_by_category
    
    def _group_warnings_by_category(self, results: List[ValidationResult]) -> Dict[str, int]:
        """Group warnings by category"""
        warnings_by_category = {}
        
        for result in results:
            for warning in result.warnings:
                category = warning.category.value
                warnings_by_category[category] = warnings_by_category.get(category, 0) + 1
        
        return warnings_by_category
    
    def _group_violations_by_category_from_list(self, violations: List[ValidationViolation]) -> Dict[str, int]:
        """Group violations by category from list"""
        violations_by_category = {}
        
        for violation in violations:
            category = violation.category.value
            violations_by_category[category] = violations_by_category.get(category, 0) + 1
        
        return violations_by_category
    
    def _group_violations_by_severity(self, violations: List[ValidationViolation]) -> Dict[str, int]:
        """Group violations by severity"""
        violations_by_severity = {}
        
        for violation in violations:
            severity = violation.severity.value
            violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1
        
        return violations_by_severity
    
    def _identify_most_common_violations(self, violations: List[ValidationViolation]) -> List[Dict[str, Any]]:
        """Identify most common violations"""
        violation_counts = {}
        
        for violation in violations:
            key = f"{violation.rule_name} ({violation.category.value})"
            violation_counts[key] = violation_counts.get(key, 0) + 1
        
        # Sort by count and return top 10
        sorted_violations = sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'rule_name': rule_name, 'count': count, 'category': rule_name.split(' (')[1].rstrip(')')}
            for rule_name, count in sorted_violations[:10]
        ]
    
    def _calculate_average_execution_time(self, compliance_report: ComplianceReport) -> float:
        """Calculate average rule execution time"""
        total_time = 0
        total_rules = 0
        
        for report in compliance_report.validation_reports:
            for result in report.results:
                total_time += result.execution_time
                total_rules += 1
        
        return total_time / total_rules if total_rules > 0 else 0.0
    
    def _analyze_jurisdictions(self, compliance_report: ComplianceReport) -> Dict[str, Any]:
        """Analyze compliance by jurisdiction"""
        jurisdiction_analysis = {}
        
        for report in compliance_report.validation_reports:
            jurisdiction_key = f"{report.jurisdiction.country}_{report.jurisdiction.state or 'N/A'}"
            
            if jurisdiction_key not in jurisdiction_analysis:
                jurisdiction_analysis[jurisdiction_key] = {
                    'jurisdiction': report.jurisdiction.to_dict(),
                    'total_rules': 0,
                    'passed_rules': 0,
                    'failed_rules': 0,
                    'violations': 0,
                    'warnings': 0
                }
            
            jurisdiction_analysis[jurisdiction_key]['total_rules'] += report.total_rules
            jurisdiction_analysis[jurisdiction_key]['passed_rules'] += report.passed_rules
            jurisdiction_analysis[jurisdiction_key]['failed_rules'] += report.failed_rules
            jurisdiction_analysis[jurisdiction_key]['violations'] += report.total_violations
            jurisdiction_analysis[jurisdiction_key]['warnings'] += report.total_warnings
        
        return jurisdiction_analysis
    
    def _analyze_category_performance(self, compliance_report: ComplianceReport) -> Dict[str, Any]:
        """Analyze compliance by category"""
        category_analysis = {}
        
        for report in compliance_report.validation_reports:
            for result in report.results:
                category = result.category.value
                
                if category not in category_analysis:
                    category_analysis[category] = {
                        'total_rules': 0,
                        'passed_rules': 0,
                        'failed_rules': 0,
                        'violations': 0,
                        'warnings': 0
                    }
                
                category_analysis[category]['total_rules'] += 1
                if result.passed:
                    category_analysis[category]['passed_rules'] += 1
                else:
                    category_analysis[category]['failed_rules'] += 1
                
                category_analysis[category]['violations'] += len(result.violations)
                category_analysis[category]['warnings'] += len(result.warnings)
        
        return category_analysis
    
    def _estimate_effort(self, category: str, violation_count: int) -> str:
        """Estimate effort required to fix violations"""
        base_effort = {
            'electrical_safety': 'HIGH',
            'fire_safety_egress': 'HIGH',
            'structural_loads': 'HIGH',
            'accessibility': 'MEDIUM',
            'energy_efficiency': 'MEDIUM',
            'mechanical_hvac': 'MEDIUM',
            'plumbing_water_supply': 'MEDIUM',
            'electrical_design': 'LOW',
            'general': 'LOW'
        }
        
        base = base_effort.get(category, 'MEDIUM')
        
        if violation_count > 10:
            return f"{base} (Many violations)"
        elif violation_count > 5:
            return f"{base} (Several violations)"
        else:
            return f"{base} (Few violations)"
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load report templates"""
        return {
            'executive_summary': {
                'title': 'Executive Summary',
                'sections': ['overview', 'critical_issues', 'recommendations']
            },
            'detailed_report': {
                'title': 'Detailed Compliance Report',
                'sections': ['mcp_analysis', 'violation_details', 'performance_metrics']
            }
        }
    
    def _load_styles(self) -> Dict[str, Any]:
        """Load report styling"""
        return {
            'colors': {
                'critical': '#ff0000',
                'warning': '#ffc107',
                'info': '#17a2b8',
                'success': '#28a745'
            },
            'fonts': {
                'title': 'Arial, sans-serif',
                'body': 'Arial, sans-serif',
                'code': 'Courier New, monospace'
            }
        } 