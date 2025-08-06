#!/usr/bin/env python3
"""
PDF Report Generator for MCP Service

This module provides professional PDF report generation for building code validation results.
It includes templates for compliance reports, violation summaries, and technical specifications.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

import jinja2
from jinja2 import Template

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Professional PDF report generator for building code validation"""

    def __init__(self, template_dir: str = "templates"):
        """Initialize the report generator"""
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)), autoescape=True
        )

        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        logger.info("✅ Report Generator initialized")

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=HexColor("#2E86AB"),
            )
        )

        # Heading style
        self.styles.add(
            ParagraphStyle(
                name="CustomHeading",
                parent=self.styles["Heading1"],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=12,
                textColor=HexColor("#2E86AB"),
            )
        )

        # Subheading style
        self.styles.add(
            ParagraphStyle(
                name="CustomSubheading",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceAfter=8,
                spaceBefore=8,
                textColor=HexColor("#A23B72"),
            )
        )

        # Violation style
        self.styles.add(
            ParagraphStyle(
                name="Violation",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=6,
                leftIndent=20,
                textColor=HexColor("#D62828"),
            )
        )

        # Warning style
        self.styles.add(
            ParagraphStyle(
                name="Warning",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=6,
                leftIndent=20,
                textColor=HexColor("#F77F00"),
            )
        )

        # Success style
        self.styles.add(
            ParagraphStyle(
                name="Success",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=6,
                leftIndent=20,
                textColor=HexColor("#2E8B57"),
            )
        )

    def generate_compliance_report(
        self,
        validation_data: Dict[str, Any],
        building_info: Dict[str, Any],
        output_path: str,
    ) -> str:
        """
        Generate a comprehensive compliance report

        Args:
            validation_data: Validation results from the rule engine
            building_info: Building information and metadata
            output_path: Path to save the PDF report

        Returns:
            Path to the generated PDF file
        """
        try:
            logger.info(
                f"Generating compliance report for building {building_info.get('building_id', 'unknown')}"
            )

            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []

            # Add header
            story.extend(self._create_header(building_info))

            # Add executive summary
            story.extend(self._create_executive_summary(validation_data, building_info))

            # Add detailed violations
            story.extend(self._create_violations_section(validation_data))

            # Add compliance summary
            story.extend(self._create_compliance_summary(validation_data))

            # Add technical specifications
            story.extend(self._create_technical_specs(building_info))

            # Add footer
            story.extend(self._create_footer())

            # Build PDF
            doc.build(story)

            logger.info(f"✅ Compliance report generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Failed to generate compliance report: {e}")
            raise

    def _create_header(self, building_info: Dict[str, Any]) -> List:
        """Create the report header"""
        elements = []

        # Title
        title = Paragraph("Building Code Compliance Report", self.styles["CustomTitle"])
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Building information table
        building_data = [
            ["Building ID:", building_info.get("building_id", "N/A")],
            ["Building Name:", building_info.get("building_name", "N/A")],
            ["Location:", building_info.get("location", "N/A")],
            ["Report Date:", datetime.now().strftime("%B %d, %Y")],
            ["Report Time:", datetime.now().strftime("%I:%M %p")],
        ]

        building_table = Table(building_data, colWidths=[2 * inch, 4 * inch])
        building_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), HexColor("#F8F9FA")),
                    ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#2E86AB")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(building_table)
        elements.append(Spacer(1, 20))

        return elements

    def _create_executive_summary(
        self, validation_data: Dict[str, Any], building_info: Dict[str, Any]
    ) -> List:
        """Create executive summary section"""
        elements = []

        # Section title
        title = Paragraph("Executive Summary", self.styles["CustomHeading"])
        elements.append(title)

        # Summary statistics
        total_violations = validation_data.get("total_violations", 0)
        total_warnings = validation_data.get("total_warnings", 0)
        total_rules = validation_data.get("total_rules", 0)
        passed_rules = total_rules - total_violations

        compliance_rate = (passed_rules / total_rules * 100) if total_rules > 0 else 0

        # Compliance status
        if compliance_rate >= 95:
            status = "COMPLIANT"
            status_color = HexColor("#2E8B57")
        elif compliance_rate >= 80:
            status = "MOSTLY COMPLIANT"
            status_color = HexColor("#F77F00")
        else:
            status = "NON-COMPLIANT"
            status_color = HexColor("#D62828")

        # Summary table
        summary_data = [
            ["Compliance Status:", status],
            ["Compliance Rate:", f"{compliance_rate:.1f}%"],
            ["Total Rules Checked:", str(total_rules)],
            ["Passed Rules:", str(passed_rules)],
            ["Violations:", str(total_violations)],
            ["Warnings:", str(total_warnings)],
        ]

        summary_table = Table(summary_data, colWidths=[2 * inch, 4 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), HexColor("#F8F9FA")),
                    ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#2E86AB")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(summary_table)
        elements.append(Spacer(1, 12))

        # Summary paragraph
        summary_text = f"""
        This building code compliance report provides a comprehensive analysis of the building 
        model against applicable building codes and regulations. The analysis covered {total_rules} 
        rules and identified {total_violations} violations and {total_warnings} warnings.
        
        The building demonstrates a {compliance_rate:.1f}% compliance rate, which is classified as 
        <b>{status}</b>. {'Immediate action is required to address critical violations.' if total_violations > 0 else 'The building meets all critical compliance requirements.'}
        """

        summary_para = Paragraph(summary_text, self.styles["Normal"])
        elements.append(summary_para)
        elements.append(Spacer(1, 20))

        return elements

    def _create_violations_section(self, validation_data: Dict[str, Any]) -> List:
        """Create detailed violations section"""
        elements = []

        # Section title
        title = Paragraph(
            "Detailed Violations and Warnings", self.styles["CustomHeading"]
        )
        elements.append(title)

        violations = validation_data.get("violations", [])
        warnings = validation_data.get("warnings", [])

        # Critical violations
        if violations:
            elements.append(
                Paragraph("Critical Violations", self.styles["CustomSubheading"])
            )

            for i, violation in enumerate(violations[:10], 1):  # Limit to first 10
                violation_text = f"""
                <b>{i}. {violation.get('rule_name', 'Unknown Rule')}</b><br/>
                <b>Severity:</b> {violation.get('severity', 'Unknown')}<br/>
                <b>Description:</b> {violation.get('description', 'No description available')}<br/>
                <b>Location:</b> {violation.get('location', 'Unknown')}<br/>
                <b>Recommendation:</b> {violation.get('recommendation', 'Review and correct')}
                """

                violation_para = Paragraph(violation_text, self.styles["Violation"])
                elements.append(violation_para)
                elements.append(Spacer(1, 8))

            if len(violations) > 10:
                remaining = len(violations) - 10
                elements.append(
                    Paragraph(
                        f"... and {remaining} additional violations",
                        self.styles["Normal"],
                    )
                )
                elements.append(Spacer(1, 12))

        # Warnings
        if warnings:
            elements.append(Paragraph("Warnings", self.styles["CustomSubheading"]))

            for i, warning in enumerate(warnings[:5], 1):  # Limit to first 5
                warning_text = f"""
                <b>{i}. {warning.get('rule_name', 'Unknown Rule')}</b><br/>
                <b>Description:</b> {warning.get('description', 'No description available')}<br/>
                <b>Location:</b> {warning.get('location', 'Unknown')}<br/>
                <b>Suggestion:</b> {warning.get('suggestion', 'Consider reviewing')}
                """

                warning_para = Paragraph(warning_text, self.styles["Warning"])
                elements.append(warning_para)
                elements.append(Spacer(1, 8))

            if len(warnings) > 5:
                remaining = len(warnings) - 5
                elements.append(
                    Paragraph(
                        f"... and {remaining} additional warnings",
                        self.styles["Normal"],
                    )
                )

        elements.append(Spacer(1, 20))
        return elements

    def _create_compliance_summary(self, validation_data: Dict[str, Any]) -> List:
        """Create compliance summary section"""
        elements = []

        # Section title
        title = Paragraph("Compliance Summary", self.styles["CustomHeading"])
        elements.append(title)

        # Compliance by category
        categories = validation_data.get("compliance_by_category", {})

        if categories:
            category_data = [["Category", "Status", "Rules Checked", "Violations"]]

            for category, stats in categories.items():
                status = "✅ PASS" if stats.get("violations", 0) == 0 else "❌ FAIL"
                category_data.append(
                    [
                        category,
                        status,
                        str(stats.get("total_rules", 0)),
                        str(stats.get("violations", 0)),
                    ]
                )

            category_table = Table(
                category_data, colWidths=[2 * inch, 1 * inch, 1.5 * inch, 1.5 * inch]
            )
            category_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2E86AB")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            elements.append(category_table)
            elements.append(Spacer(1, 12))

        # Recommendations
        recommendations = validation_data.get("recommendations", [])
        if recommendations:
            elements.append(
                Paragraph("Recommendations", self.styles["CustomSubheading"])
            )

            for i, rec in enumerate(recommendations[:5], 1):  # Limit to first 5
                rec_text = f"{i}. {rec}"
                rec_para = Paragraph(rec_text, self.styles["Normal"])
                elements.append(rec_para)
                elements.append(Spacer(1, 6))

        elements.append(Spacer(1, 20))
        return elements

    def _create_technical_specs(self, building_info: Dict[str, Any]) -> List:
        """Create technical specifications section"""
        elements = []

        # Section title
        title = Paragraph("Technical Specifications", self.styles["CustomHeading"])
        elements.append(title)

        # Building specifications
        specs_data = [
            ["Property", "Value"],
            ["Building Type:", building_info.get("building_type", "N/A")],
            ["Construction Year:", building_info.get("construction_year", "N/A")],
            ["Total Area:", building_info.get("total_area", "N/A")],
            ["Number of Floors:", building_info.get("floors", "N/A")],
            ["Occupancy Type:", building_info.get("occupancy_type", "N/A")],
            ["Fire Rating:", building_info.get("fire_rating", "N/A")],
            ["Structural System:", building_info.get("structural_system", "N/A")],
        ]

        specs_table = Table(specs_data, colWidths=[2 * inch, 4 * inch])
        specs_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), HexColor("#2E86AB")),
                    ("TEXTCOLOR", (0, 0), (0, 0), colors.whitesmoke),
                    ("BACKGROUND", (0, 1), (0, -1), HexColor("#F8F9FA")),
                    ("TEXTCOLOR", (0, 1), (0, -1), HexColor("#2E86AB")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(specs_table)
        elements.append(Spacer(1, 20))

        return elements

    def _create_footer(self) -> List:
        """Create report footer"""
        elements = []

        # Footer text
        footer_text = (
            """
        <b>Report Generated by MCP Service</b><br/>
        Model Context Protocol for Building Code Validation<br/>
        Generated on: """
            + datetime.now().strftime("%B %d, %Y at %I:%M %p")
            + """<br/>
        For technical support, contact: support@arxos.com
        """
        )

        footer_para = Paragraph(footer_text, self.styles["Normal"])
        elements.append(footer_para)

        return elements

    def generate_violation_summary(
        self, validation_data: Dict[str, Any], output_path: str
    ) -> str:
        """Generate a concise violation summary report"""
        try:
            logger.info("Generating violation summary report")

            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []

            # Title
            title = Paragraph("Violation Summary Report", self.styles["CustomTitle"])
            story.append(title)
            story.append(Spacer(1, 20))

            # Summary statistics
            total_violations = validation_data.get("total_violations", 0)
            critical_violations = len(
                [
                    v
                    for v in validation_data.get("violations", [])
                    if v.get("severity") == "CRITICAL"
                ]
            )

            summary_data = [
                ["Total Violations:", str(total_violations)],
                ["Critical Violations:", str(critical_violations)],
                ["Warnings:", str(validation_data.get("total_warnings", 0))],
                [
                    "Compliance Rate:",
                    f"{validation_data.get('compliance_rate', 0):.1f}%",
                ],
            ]

            summary_table = Table(summary_data, colWidths=[2 * inch, 2 * inch])
            summary_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), HexColor("#F8F9FA")),
                        ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#2E86AB")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            story.append(summary_table)
            story.append(Spacer(1, 20))

            # Critical violations list
            violations = validation_data.get("violations", [])
            if violations:
                story.append(
                    Paragraph("Critical Violations:", self.styles["CustomHeading"])
                )

                for i, violation in enumerate(violations[:10], 1):
                    violation_text = f"""
                    <b>{i}. {violation.get('rule_name', 'Unknown')}</b><br/>
                    {violation.get('description', 'No description')}
                    """
                    violation_para = Paragraph(violation_text, self.styles["Violation"])
                    story.append(violation_para)
                    story.append(Spacer(1, 6))

            # Build PDF
            doc.build(story)

            logger.info(f"✅ Violation summary generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Failed to generate violation summary: {e}")
            raise

    def generate_executive_summary(
        self,
        validation_data: Dict[str, Any],
        building_info: Dict[str, Any],
        output_path: str,
    ) -> str:
        """Generate an executive summary report"""
        try:
            logger.info("Generating executive summary report")

            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []

            # Title
            title = Paragraph("Executive Summary", self.styles["CustomTitle"])
            story.append(title)
            story.append(Spacer(1, 20))

            # Building info
            building_text = f"""
            <b>Building:</b> {building_info.get('building_name', 'N/A')}<br/>
            <b>Location:</b> {building_info.get('location', 'N/A')}<br/>
            <b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}
            """
            building_para = Paragraph(building_text, self.styles["Normal"])
            story.append(building_para)
            story.append(Spacer(1, 20))

            # Compliance status
            total_violations = validation_data.get("total_violations", 0)
            compliance_rate = validation_data.get("compliance_rate", 0)

            if compliance_rate >= 95:
                status = "✅ COMPLIANT"
                status_color = "green"
            elif compliance_rate >= 80:
                status = "⚠️ MOSTLY COMPLIANT"
                status_color = "orange"
            else:
                status = "❌ NON-COMPLIANT"
                status_color = "red"

            status_text = f"""
            <b>Compliance Status:</b> {status}<br/>
            <b>Compliance Rate:</b> {compliance_rate:.1f}%<br/>
            <b>Total Violations:</b> {total_violations}
            """
            status_para = Paragraph(status_text, self.styles["Normal"])
            story.append(status_para)
            story.append(Spacer(1, 20))

            # Key findings
            story.append(Paragraph("Key Findings:", self.styles["CustomHeading"]))

            findings = []
            if total_violations == 0:
                findings.append(
                    "✅ Building meets all critical compliance requirements"
                )
            else:
                findings.append(
                    f"❌ {total_violations} violations require immediate attention"
                )

            if validation_data.get("total_warnings", 0) > 0:
                findings.append(
                    f"⚠️ {validation_data.get('total_warnings', 0)} warnings for review"
                )

            for finding in findings:
                finding_para = Paragraph(f"• {finding}", self.styles["Normal"])
                story.append(finding_para)
                story.append(Spacer(1, 6))

            # Build PDF
            doc.build(story)

            logger.info(f"✅ Executive summary generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Failed to generate executive summary: {e}")
            raise


# Factory function for easy instantiation
def create_report_generator(template_dir: str = "templates") -> ReportGenerator:
    """Create a report generator instance"""
    return ReportGenerator(template_dir)
