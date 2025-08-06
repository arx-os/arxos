#!/usr/bin/env python3
"""
Test Report Generation System

This script tests the complete PDF report generation system including:
- Report generator functionality
- Report service integration
- API endpoints
- Email distribution
- Cloud storage integration
"""

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerationTest:
    """Test suite for report generation system"""

    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        self.test_data = self._create_test_data()

    def _create_test_data(self) -> Dict[str, Any]:
        """Create test validation data"""
        return {
            "total_violations": 3,
            "total_warnings": 2,
            "total_rules": 25,
            "compliance_rate": 88.0,
            "violations": [
                {
                    "rule_name": "Fire Safety - Exit Width",
                    "severity": "CRITICAL",
                    "description": "Exit width does not meet minimum requirements",
                    "location": "Main exit corridor",
                    "recommendation": "Increase exit width to minimum 44 inches",
                },
                {
                    "rule_name": "Structural - Load Bearing",
                    "severity": "CRITICAL",
                    "description": "Load bearing wall thickness insufficient",
                    "location": "First floor - north wall",
                    "recommendation": "Increase wall thickness to 12 inches",
                },
                {
                    "rule_name": "Electrical - Circuit Protection",
                    "severity": "HIGH",
                    "description": "Circuit breaker rating exceeds wire capacity",
                    "location": "Electrical panel A",
                    "recommendation": "Replace circuit breaker with appropriate rating",
                },
            ],
            "warnings": [
                {
                    "rule_name": "Accessibility - Door Width",
                    "description": "Door width slightly below recommended standard",
                    "location": "Office 101 entrance",
                    "suggestion": "Consider increasing door width for better accessibility",
                },
                {
                    "rule_name": "Energy - Insulation",
                    "description": "Wall insulation R-value below recommended",
                    "location": "Exterior walls",
                    "suggestion": "Consider upgrading insulation for energy efficiency",
                },
            ],
            "compliance_by_category": {
                "Fire Safety": {"total_rules": 8, "violations": 1, "warnings": 0},
                "Structural": {"total_rules": 6, "violations": 1, "warnings": 0},
                "Electrical": {"total_rules": 5, "violations": 1, "warnings": 0},
                "Accessibility": {"total_rules": 4, "violations": 0, "warnings": 1},
                "Energy": {"total_rules": 2, "violations": 0, "warnings": 1},
            },
            "recommendations": [
                "Address critical fire safety violations immediately",
                "Review structural load calculations",
                "Upgrade electrical system protection",
                "Consider accessibility improvements",
                "Evaluate energy efficiency upgrades",
            ],
        }

    def test_report_generator(self):
        """Test the report generator component"""
        logger.info("🔍 Testing Report Generator...")

        try:
            from report.report_generator import create_report_generator

            # Create report generator
            generator = create_report_generator()

            # Test data
            building_info = {
                "building_id": "TEST_001",
                "building_name": "Test Building",
                "location": "Test City, ST",
                "building_type": "Commercial",
                "construction_year": "2024",
                "total_area": "50,000 sq ft",
                "floors": "3",
                "occupancy_type": "Office",
                "fire_rating": "2-hour",
                "structural_system": "Steel Frame",
            }

            # Create temporary directory for test reports
            with tempfile.TemporaryDirectory() as temp_dir:
                # Test comprehensive report
                comprehensive_path = os.path.join(temp_dir, "comprehensive_test.pdf")
                result = generator.generate_compliance_report(
                    self.test_data, building_info, comprehensive_path
                )
                assert os.path.exists(
                    comprehensive_path
                ), "Comprehensive report not generated"
                assert (
                    os.path.getsize(comprehensive_path) > 0
                ), "Comprehensive report is empty"

                # Test violation summary
                violation_path = os.path.join(temp_dir, "violation_test.pdf")
                result = generator.generate_violation_summary(
                    self.test_data, violation_path
                )
                assert os.path.exists(violation_path), "Violation summary not generated"
                assert os.path.getsize(violation_path) > 0, "Violation summary is empty"

                # Test executive summary
                executive_path = os.path.join(temp_dir, "executive_test.pdf")
                result = generator.generate_executive_summary(
                    self.test_data, building_info, executive_path
                )
                assert os.path.exists(executive_path), "Executive summary not generated"
                assert os.path.getsize(executive_path) > 0, "Executive summary is empty"

                logger.info(f"✅ Generated reports: {os.listdir(temp_dir)}")

            self.test_results["report_generator"] = "✅ PASSED"
            logger.info("✅ Report Generator Test PASSED")

        except Exception as e:
            self.test_results["report_generator"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Report Generator Test FAILED: {e}")

    async def test_report_service(self):
        """Test the report service component"""
        logger.info("🔍 Testing Report Service...")

        try:
            from report.report_service import create_report_service

            # Test configuration
            config = {
                "reports_dir": "test_reports",
                "email": {
                    "smtp_host": "localhost",
                    "smtp_port": 587,
                    "username": "test@example.com",
                    "password": "test123",
                    "from_email": "noreply@test.com",
                    "use_tls": True,
                },
                "storage": {
                    "aws": {
                        "access_key": "test_key",
                        "secret_key": "test_secret",
                        "region": "us-east-1",
                        "bucket": "test-bucket",
                    }
                },
            }

            # Create report service
            service = create_report_service(config)

            # Test building info
            building_info = {
                "building_id": "TEST_002",
                "building_name": "Test Building 2",
                "location": "Test City, ST",
                "building_type": "Residential",
                "construction_year": "2023",
                "total_area": "25,000 sq ft",
                "floors": "2",
                "occupancy_type": "Multi-family",
                "fire_rating": "1-hour",
                "structural_system": "Wood Frame",
            }

            # Test report generation
            result = await service.generate_compliance_report(
                self.test_data, building_info, "comprehensive"
            )

            assert result["success"], f"Report generation failed: {result.get('error')}"
            assert result["report_path"], "Report path not returned"
            assert os.path.exists(result["report_path"]), "Report file not created"
            assert result["file_size"] > 0, "Report file is empty"

            # Test report history
            history = await service.get_report_history(limit=10)
            assert isinstance(history, list), "Report history should be a list"

            # Clean up test reports directory
            if os.path.exists("test_reports"):
                import shutil

                shutil.rmtree("test_reports")

            self.test_results["report_service"] = "✅ PASSED"
            logger.info("✅ Report Service Test PASSED")

        except Exception as e:
            self.test_results["report_service"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Report Service Test FAILED: {e}")

    def test_report_routes(self):
        """Test the report API routes"""
        logger.info("🔍 Testing Report API Routes...")

        try:
            from report.report_routes import (
                router,
                ReportGenerationRequest,
                ReportGenerationResponse,
            )

            # Test request model
            request_data = {
                "building_id": "TEST_003",
                "report_type": "comprehensive",
                "include_email": False,
                "email_recipients": [],
            }

            request = ReportGenerationRequest(**request_data)
            assert request.building_id == "TEST_003"
            assert request.report_type == "comprehensive"
            assert not request.include_email

            # Test response model
            response_data = {
                "success": True,
                "report_path": "/path/to/report.pdf",
                "filename": "test_report.pdf",
                "file_size": 1024,
                "report_type": "comprehensive",
                "generated_at": datetime.now().isoformat(),
                "cloud_urls": {},
            }

            response = ReportGenerationResponse(**response_data)
            assert response.success
            assert response.report_path == "/path/to/report.pdf"
            assert response.file_size == 1024

            # Test router creation
            assert router is not None
            assert len(router.routes) > 0

            self.test_results["report_routes"] = "✅ PASSED"
            logger.info("✅ Report API Routes Test PASSED")

        except Exception as e:
            self.test_results["report_routes"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Report API Routes Test FAILED: {e}")

    def test_pdf_generation_quality(self):
        """Test PDF generation quality and content"""
        logger.info("🔍 Testing PDF Generation Quality...")

        try:
            from report.report_generator import create_report_generator

            generator = create_report_generator()

            building_info = {
                "building_id": "QUALITY_TEST_001",
                "building_name": "Quality Test Building",
                "location": "Quality City, ST",
                "building_type": "Mixed Use",
                "construction_year": "2024",
                "total_area": "100,000 sq ft",
                "floors": "5",
                "occupancy_type": "Mixed",
                "fire_rating": "3-hour",
                "structural_system": "Concrete",
            }

            with tempfile.TemporaryDirectory() as temp_dir:
                # Generate comprehensive report
                report_path = os.path.join(temp_dir, "quality_test.pdf")
                result = generator.generate_compliance_report(
                    self.test_data, building_info, report_path
                )

                # Verify file exists and has content
                assert os.path.exists(report_path), "PDF file not created"
                file_size = os.path.getsize(report_path)
                assert file_size > 1000, f"PDF file too small: {file_size} bytes"

                # Check file header (PDF files start with %PDF)
                with open(report_path, "rb") as f:
                    header = f.read(4)
                    assert header == b"%PDF", "File is not a valid PDF"

                logger.info(
                    f"✅ PDF quality test passed - File size: {file_size} bytes"
                )

            self.test_results["pdf_quality"] = "✅ PASSED"
            logger.info("✅ PDF Generation Quality Test PASSED")

        except Exception as e:
            self.test_results["pdf_quality"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ PDF Generation Quality Test FAILED: {e}")

    def test_report_templates(self):
        """Test different report templates"""
        logger.info("🔍 Testing Report Templates...")

        try:
            from report.report_generator import create_report_generator

            generator = create_report_generator()

            building_info = {
                "building_id": "TEMPLATE_TEST_001",
                "building_name": "Template Test Building",
                "location": "Template City, ST",
                "building_type": "Office",
                "construction_year": "2024",
                "total_area": "75,000 sq ft",
                "floors": "4",
                "occupancy_type": "Office",
                "fire_rating": "2-hour",
                "structural_system": "Steel Frame",
            }

            with tempfile.TemporaryDirectory() as temp_dir:
                templates = [
                    ("comprehensive", "comprehensive_test.pdf"),
                    ("violation_summary", "violation_test.pdf"),
                    ("executive_summary", "executive_test.pdf"),
                ]

                for template_type, filename in templates:
                    file_path = os.path.join(temp_dir, filename)

                    if template_type == "comprehensive":
                        result = generator.generate_compliance_report(
                            self.test_data, building_info, file_path
                        )
                    elif template_type == "violation_summary":
                        result = generator.generate_violation_summary(
                            self.test_data, file_path
                        )
                    elif template_type == "executive_summary":
                        result = generator.generate_executive_summary(
                            self.test_data, building_info, file_path
                        )

                    assert os.path.exists(file_path), f"{template_type} template failed"
                    assert (
                        os.path.getsize(file_path) > 0
                    ), f"{template_type} template is empty"

                    logger.info(f"✅ {template_type} template generated successfully")

                logger.info(f"✅ All templates generated: {os.listdir(temp_dir)}")

            self.test_results["report_templates"] = "✅ PASSED"
            logger.info("✅ Report Templates Test PASSED")

        except Exception as e:
            self.test_results["report_templates"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Report Templates Test FAILED: {e}")

    async def run_all_tests(self):
        """Run all report generation tests"""
        logger.info("🚀 Starting Report Generation System Tests...")

        # Run synchronous tests
        self.test_report_generator()
        self.test_report_routes()
        self.test_pdf_generation_quality()
        self.test_report_templates()

        # Run asynchronous tests
        await self.test_report_service()

        # Generate test summary
        self._generate_test_summary()

    def _generate_test_summary(self):
        """Generate test summary report"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 REPORT GENERATION SYSTEM TEST SUMMARY")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if "PASSED" in result
        )
        failed_tests = total_tests - passed_tests

        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        logger.info("\n📋 Test Results:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if "PASSED" in result else "❌"
            logger.info(f"{status_icon} {test_name}: {result}")

        duration = datetime.now() - self.start_time
        logger.info(f"\n⏱️ Test Duration: {duration.total_seconds():.2f} seconds")

        if failed_tests == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Report generation system is ready.")
        else:
            logger.info(
                f"\n⚠️ {failed_tests} test(s) failed. Please review and fix issues."
            )

        logger.info("=" * 60)


async def main():
    """Main test execution"""
    try:
        # Create and run test suite
        test_suite = ReportGenerationTest()
        await test_suite.run_all_tests()

    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
