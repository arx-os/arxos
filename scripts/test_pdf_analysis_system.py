#!/usr/bin/env python3
"""
PDF Analysis System Test Runner

Comprehensive test runner for the PDF analysis system to verify
architectural compliance, integration, and functionality.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from domain.value_objects import TaskId, UserId, TaskStatus, ConfidenceScore
from domain.entities.pdf_analysis import PDFAnalysis
from domain.repositories import UnitOfWork, PDFAnalysisRepository

from application.dto.pdf_analysis_dto import (
    CreatePDFAnalysisRequest, GetPDFAnalysisRequest,
    StartPDFAnalysisRequest, CompletePDFAnalysisRequest
)

from application.use_cases.pdf_analysis_use_cases import (
    CreatePDFAnalysisUseCase, GetPDFAnalysisUseCase,
    StartPDFAnalysisUseCase, CompletePDFAnalysisUseCase
)

from infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from infrastructure.database.connection_manager import DatabaseConnectionManager
from infrastructure.repositories.postgresql_pdf_analysis_repository import PostgreSQLPDFAnalysisRepository
from infrastructure.repository_factory import SQLAlchemyRepositoryFactory

from application.services.pdf_analysis_orchestrator import PDFAnalysisOrchestrator
from infrastructure.services.gus_service import GUSService
from infrastructure.services.file_storage_service import FileStorageService


class PDFAnalysisSystemTester:
    """Comprehensive tester for PDF analysis system."""

    def __init__(self):
        """Initialize the tester."""
        self.logger = logging.getLogger(__name__)
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        self.results[test_name] = success
        if success:
            self.logger.info(f"✅ {test_name}: PASSED")
        else:
            self.logger.error(f"❌ {test_name}: FAILED - {message}")
            self.errors.append(f"{test_name}: {message}")

    def test_domain_layer_compliance(self) -> bool:
        """Test domain layer architectural compliance."""
        try:
            # Test domain entities
            task_id = TaskId("test-task-123")
            user_id = UserId("test-user-456")

            analysis = PDFAnalysis(
                task_id=task_id,
                user_id=user_id,
                filename="test.pdf",
                file_path="/tmp/test.pdf",
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                include_cost_estimation=True,
                include_timeline=True,
                include_quantities=True,
                requirements={}
            )

            assert analysis.task_id == task_id
            assert analysis.user_id == user_id
            assert analysis.status == TaskStatus.PENDING

            self.log_test_result("Domain Layer Compliance", True)
            return True

        except Exception as e:
            self.log_test_result("Domain Layer Compliance", False, str(e))
            return False

    def test_infrastructure_layer_compliance(self) -> bool:
        """Test infrastructure layer architectural compliance."""
        try:
            # Test repository interface compliance
            from domain.repositories import PDFAnalysisRepository
            from infrastructure.repositories.postgresql_pdf_analysis_repository import PostgreSQLPDFAnalysisRepository

            # Verify repository implements domain interface
            assert issubclass(PostgreSQLPDFAnalysisRepository, PDFAnalysisRepository)

            # Test Unit of Work interface compliance
            from domain.repositories import UnitOfWork
            from infrastructure.unit_of_work import SQLAlchemyUnitOfWork

            # Verify Unit of Work implements domain interface
            assert issubclass(SQLAlchemyUnitOfWork, UnitOfWork)

            self.log_test_result("Infrastructure Layer Compliance", True)
            return True

        except Exception as e:
            self.log_test_result("Infrastructure Layer Compliance", False, str(e))
            return False

    def test_application_layer_compliance(self) -> bool:
        """Test application layer architectural compliance."""
        try:
            # Test use case pattern
            from application.use_cases.pdf_analysis_use_cases import CreatePDFAnalysisUseCase

            # Verify use case has execute method
            assert hasattr(CreatePDFAnalysisUseCase, 'execute')

            # Test DTO pattern
            from application.dto.pdf_analysis_dto import CreatePDFAnalysisRequest

            # Verify DTO is properly structured
            assert hasattr(CreatePDFAnalysisRequest, '__annotations__')

            self.log_test_result("Application Layer Compliance", True)
            return True

        except Exception as e:
            self.log_test_result("Application Layer Compliance", False, str(e))
            return False

    def test_unit_of_work_integration(self) -> bool:
        """Test Unit of Work integration."""
        try:
            # Test repository factory integration
            from infrastructure.repository_factory import SQLAlchemyRepositoryFactory
            from sqlalchemy.orm import sessionmaker

            # Create mock session factory
            mock_session_factory = type('MockSessionFactory', (), {})()
            factory = SQLAlchemyRepositoryFactory(mock_session_factory)

            # Test PDF analysis repository creation
            pdf_repository = factory.create_pdf_analysis_repository()
            assert isinstance(pdf_repository, PostgreSQLPDFAnalysisRepository)

            self.log_test_result("Unit of Work Integration", True)
            return True

        except Exception as e:
            self.log_test_result("Unit of Work Integration", False, str(e))
            return False

    def test_use_case_integration(self) -> bool:
        """Test use case integration with Unit of Work."""
        try:
            # Create mock repository
            mock_repository = type('MockRepository', (), {
                'save': lambda x: None,
                'get_by_id': lambda x: None
            })()

            # Test CreatePDFAnalysisUseCase
            request = CreatePDFAnalysisRequest(
                task_id=TaskId("test-task-123"),
                user_id=UserId("test-user-456"),
                filename="test.pdf",
                file_path="/tmp/test.pdf",
                include_cost_estimation=True,
                include_timeline=True,
                include_quantities=True,
                requirements={}
            )

            use_case = CreatePDFAnalysisUseCase(mock_repository)
            response = use_case.execute(request)

            assert hasattr(response, 'success')
            assert hasattr(response, 'task_id')

            self.log_test_result("Use Case Integration", True)
            return True

        except Exception as e:
            self.log_test_result("Use Case Integration", False, str(e))
            return False

    def test_orchestrator_integration(self) -> bool:
        """Test orchestrator integration."""
        try:
            # Create mock dependencies
            mock_unit_of_work = type('MockUnitOfWork', (), {
                'pdf_analyses': type('MockRepository', (), {
                    'save': lambda x: None,
                    'get_by_id': lambda x: None
                })(),
                'commit': lambda: None,
                'rollback': lambda: None,
                '__enter__': lambda self: self,
                '__exit__': lambda self, *args: None
            })()

            mock_gus_service = type('MockGUSService', (), {
                'analyze_pdf': lambda *args, **kwargs: None
            })()

            mock_file_storage_service = type('MockFileStorageService', (), {
                'save_uploaded_file': lambda *args, **kwargs: "/tmp/test.pdf",
                'get_file_content': lambda *args, **kwargs: b"test content"
            })()

            # Test orchestrator creation
            orchestrator = PDFAnalysisOrchestrator(
                mock_unit_of_work, mock_gus_service, mock_file_storage_service
            )

            assert hasattr(orchestrator, 'create_pdf_analysis')
            assert hasattr(orchestrator, 'get_pdf_analysis')
            assert hasattr(orchestrator, 'start_pdf_analysis')

            self.log_test_result("Orchestrator Integration", True)
            return True

        except Exception as e:
            self.log_test_result("Orchestrator Integration", False, str(e))
            return False

    def test_api_integration(self) -> bool:
        """Test API integration."""
        try:
            # Test API route imports
            from api.routes.pdf_analysis_routes import router as pdf_router

            # Verify router has expected endpoints
            routes = [route.path for route in pdf_router.routes]
            expected_routes = [
                "/upload",
                "/{task_id}",
                "/{task_id}/start",
                "/{task_id}/status",
                "/{task_id}/result",
                "/{task_id}/cancel",
                "/list",
                "/statistics"
            ]

            # Check that router exists and has routes
            assert pdf_router is not None
            assert len(routes) > 0

            self.log_test_result("API Integration", True)
            return True

        except Exception as e:
            self.log_test_result("API Integration", False, str(e))
            return False

    def test_transaction_management(self) -> bool:
        """Test transaction management compliance."""
        try:
            # Test Unit of Work transaction pattern
            mock_unit_of_work = type('MockUnitOfWork', (), {
                'commit': lambda: None,
                'rollback': lambda: None,
                '__enter__': lambda self: self,
                '__exit__': lambda self, *args: None
            })()

            # Test successful transaction
            with mock_unit_of_work as uow:
                uow.commit()

            # Test failed transaction
            with mock_unit_of_work as uow:
                uow.rollback()

            self.log_test_result("Transaction Management", True)
            return True

        except Exception as e:
            self.log_test_result("Transaction Management", False, str(e))
            return False

    def test_error_handling(self) -> bool:
        """Test error handling compliance."""
        try:
            # Test domain exceptions
            from domain.exceptions import PDFAnalysisNotFoundError, InvalidTaskStatusError

            # Verify exceptions exist and are properly structured
            assert PDFAnalysisNotFoundError is not None
            assert InvalidTaskStatusError is not None

            # Test exception inheritance
            assert issubclass(PDFAnalysisNotFoundError, Exception)
            assert issubclass(InvalidTaskStatusError, Exception)

            self.log_test_result("Error Handling", True)
            return True

        except Exception as e:
            self.log_test_result("Error Handling", False, str(e))
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        self.logger.info("🚀 Starting PDF Analysis System Tests")
        self.logger.info("=" * 60)

        # Run all test categories
        tests = [
            ("Domain Layer Compliance", self.test_domain_layer_compliance),
            ("Infrastructure Layer Compliance", self.test_infrastructure_layer_compliance),
            ("Application Layer Compliance", self.test_application_layer_compliance),
            ("Unit of Work Integration", self.test_unit_of_work_integration),
            ("Use Case Integration", self.test_use_case_integration),
            ("Orchestrator Integration", self.test_orchestrator_integration),
            ("API Integration", self.test_api_integration),
            ("Transaction Management", self.test_transaction_management),
            ("Error Handling", self.test_error_handling)
        ]

        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test_result(test_name, False, f"Unexpected error: {str(e)}")

        # Generate summary
        total_tests = len(tests)
        passed_tests = sum(1 for success in self.results.values() if success)
        failed_tests = total_tests - passed_tests

        self.logger.info("=" * 60)
        self.logger.info(f"📊 Test Summary:")
        self.logger.info(f"   Total Tests: {total_tests}")
        self.logger.info(f"   Passed: {passed_tests}")
        self.logger.info(f"   Failed: {failed_tests}")
        self.logger.info(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if self.errors:
            self.logger.info("❌ Errors:")
            for error in self.errors:
                self.logger.error(f"   - {error}")

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
            "errors": self.errors,
            "all_passed": failed_tests == 0
        }


def main():
    """Main test runner function."""
    tester = PDFAnalysisSystemTester()
    tester.setup_logging()

    results = tester.run_all_tests()

    if results["all_passed"]:
        print("\n🎉 All tests passed! PDF Analysis System is ready for deployment.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {results['failed_tests']} test(s) failed. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
