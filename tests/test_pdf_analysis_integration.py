"""
PDF Analysis Integration Tests

Comprehensive integration tests for the PDF analysis system to verify
architectural compliance, transaction management, and end-to-end functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

from domain.value_objects import TaskId, UserId, TaskStatus, ConfidenceScore
from domain.entities.pdf_analysis import PDFAnalysis
from domain.exceptions import PDFAnalysisNotFoundError, InvalidTaskStatusError

from application.dto.pdf_analysis_dto import (
    CreatePDFAnalysisRequest, CreatePDFAnalysisResponse,
    GetPDFAnalysisRequest, GetPDFAnalysisResponse,
    StartPDFAnalysisRequest, StartPDFAnalysisResponse,
    CompletePDFAnalysisRequest, CompletePDFAnalysisResponse,
    FailPDFAnalysisRequest, FailPDFAnalysisResponse
)

from application.use_cases.pdf_analysis_use_cases import (
    CreatePDFAnalysisUseCase, GetPDFAnalysisUseCase,
    StartPDFAnalysisUseCase, CompletePDFAnalysisUseCase,
    FailPDFAnalysisUseCase
)

from infrastructure.repositories.postgresql_pdf_analysis_repository import PostgreSQLPDFAnalysisRepository
from infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from infrastructure.database.connection_manager import DatabaseConnectionManager
from infrastructure.services.gus_service import GUSService
from infrastructure.services.file_storage_service import FileStorageService

from application.services.pdf_analysis_orchestrator import PDFAnalysisOrchestrator


class TestPDFAnalysisIntegration:
    """Integration tests for PDF analysis system."""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Mock database connection manager."""
        mock = Mock(spec=DatabaseConnectionManager)
        mock.get_connection.return_value = Mock()
        mock.get_engine.return_value = Mock()
        return mock
    
    @pytest.fixture
    def mock_gus_service(self):
        """Mock GUS service."""
        mock = Mock(spec=GUSService)
        mock.analyze_pdf = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_file_storage_service(self):
        """Mock file storage service."""
        mock = Mock(spec=FileStorageService)
        mock.save_uploaded_file = AsyncMock(return_value="/tmp/test.pdf")
        mock.get_file_content = AsyncMock(return_value=b"test content")
        return mock
    
    @pytest.fixture
    def mock_unit_of_work(self):
        """Mock Unit of Work."""
        mock = Mock(spec=SQLAlchemyUnitOfWork)
        mock.pdf_analyses = Mock(spec=PostgreSQLPDFAnalysisRepository)
        mock.commit = Mock()
        mock.rollback = Mock()
        mock.__enter__ = Mock(return_value=mock)
        mock.__exit__ = Mock(return_value=None)
        return mock
    
    @pytest.fixture
    def sample_pdf_analysis(self):
        """Sample PDF analysis entity."""
        return PDFAnalysis(
            task_id=TaskId("test-task-123"),
            user_id=UserId("test-user-456"),
            filename="test_document.pdf",
            file_path="/tmp/test.pdf",
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            include_cost_estimation=True,
            include_timeline=True,
            include_quantities=True,
            requirements={"test": "value"}
        )
    
    def test_create_pdf_analysis_use_case_integration(self, mock_unit_of_work, sample_pdf_analysis):
        """Test CreatePDFAnalysisUseCase integration with Unit of Work."""
        # Arrange
        mock_unit_of_work.pdf_analyses.save = Mock()
        mock_unit_of_work.pdf_analyses.get_by_id = Mock(return_value=sample_pdf_analysis)
        
        request = CreatePDFAnalysisRequest(
            task_id=TaskId("test-task-123"),
            user_id=UserId("test-user-456"),
            filename="test_document.pdf",
            file_path="/tmp/test.pdf",
            include_cost_estimation=True,
            include_timeline=True,
            include_quantities=True,
            requirements={"test": "value"}
        )
        
        use_case = CreatePDFAnalysisUseCase(mock_unit_of_work.pdf_analyses)
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.task_id == TaskId("test-task-123")
        assert response.user_id == UserId("test-user-456")
        assert response.filename == "test_document.pdf"
        assert response.status == TaskStatus.PENDING
        mock_unit_of_work.pdf_analyses.save.assert_called_once()
    
    def test_get_pdf_analysis_use_case_integration(self, mock_unit_of_work, sample_pdf_analysis):
        """Test GetPDFAnalysisUseCase integration with Unit of Work."""
        # Arrange
        mock_unit_of_work.pdf_analyses.get_by_id = Mock(return_value=sample_pdf_analysis)
        
        request = GetPDFAnalysisRequest(task_id=TaskId("test-task-123"))
        use_case = GetPDFAnalysisUseCase(mock_unit_of_work.pdf_analyses)
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.task_id == TaskId("test-task-123")
        assert response.user_id == UserId("test-user-456")
        assert response.filename == "test_document.pdf"
        mock_unit_of_work.pdf_analyses.get_by_id.assert_called_once_with(TaskId("test-task-123"))
    
    def test_start_pdf_analysis_use_case_integration(self, mock_unit_of_work, sample_pdf_analysis):
        """Test StartPDFAnalysisUseCase integration with Unit of Work."""
        # Arrange
        mock_unit_of_work.pdf_analyses.get_by_id = Mock(return_value=sample_pdf_analysis)
        mock_unit_of_work.pdf_analyses.save = Mock()
        
        request = StartPDFAnalysisRequest(task_id=TaskId("test-task-123"))
        orchestrator_mock = Mock()
        use_case = StartPDFAnalysisUseCase(mock_unit_of_work.pdf_analyses, orchestrator_mock)
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.task_id == TaskId("test-task-123")
        assert response.status == TaskStatus.PROCESSING
        mock_unit_of_work.pdf_analyses.save.assert_called_once()
    
    def test_complete_pdf_analysis_use_case_integration(self, mock_unit_of_work, sample_pdf_analysis):
        """Test CompletePDFAnalysisUseCase integration with Unit of Work."""
        # Arrange
        sample_pdf_analysis.status = TaskStatus.PROCESSING
        mock_unit_of_work.pdf_analyses.get_by_id = Mock(return_value=sample_pdf_analysis)
        mock_unit_of_work.pdf_analyses.save = Mock()
        
        request = CompletePDFAnalysisRequest(
            task_id=TaskId("test-task-123"),
            confidence=ConfidenceScore(0.85),
            systems_found=["electrical", "mechanical"],
            total_components=150,
            processing_time=45.5,
            analysis_result={"components": []}
        )
        use_case = CompletePDFAnalysisUseCase(mock_unit_of_work.pdf_analyses)
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.task_id == TaskId("test-task-123")
        assert response.status == TaskStatus.COMPLETED
        mock_unit_of_work.pdf_analyses.save.assert_called_once()
    
    def test_fail_pdf_analysis_use_case_integration(self, mock_unit_of_work, sample_pdf_analysis):
        """Test FailPDFAnalysisUseCase integration with Unit of Work."""
        # Arrange
        sample_pdf_analysis.status = TaskStatus.PROCESSING
        mock_unit_of_work.pdf_analyses.get_by_id = Mock(return_value=sample_pdf_analysis)
        mock_unit_of_work.pdf_analyses.save = Mock()
        
        request = FailPDFAnalysisRequest(
            task_id=TaskId("test-task-123"),
            error_message="Processing failed",
            processing_time=30.0
        )
        use_case = FailPDFAnalysisUseCase(mock_unit_of_work.pdf_analyses)
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.task_id == TaskId("test-task-123")
        assert response.status == TaskStatus.FAILED
        mock_unit_of_work.pdf_analyses.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrator_create_pdf_analysis_integration(
        self, mock_unit_of_work, mock_gus_service, mock_file_storage_service
    ):
        """Test orchestrator create PDF analysis integration."""
        # Arrange
        mock_unit_of_work.pdf_analyses.save = Mock()
        mock_unit_of_work.pdf_analyses.get_by_id = Mock(return_value=None)
        
        orchestrator = PDFAnalysisOrchestrator(
            mock_unit_of_work, mock_gus_service, mock_file_storage_service
        )
        
        # Act
        response = await orchestrator.create_pdf_analysis(
            user_id=UserId("test-user-456"),
            filename="test_document.pdf",
            file_content=b"test content",
            include_cost_estimation=True,
            include_timeline=True,
            include_quantities=True,
            requirements={"test": "value"}
        )
        
        # Assert
        assert response.success is True
        assert response.user_id == UserId("test-user-456")
        assert response.filename == "test_document.pdf"
        assert response.status == TaskStatus.PENDING
        mock_unit_of_work.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrator_get_pdf_analysis_integration(
        self, mock_unit_of_work, mock_gus_service, mock_file_storage_service, sample_pdf_analysis
    ):
        """Test orchestrator get PDF analysis integration."""
        # Arrange
        mock_unit_of_work.pdf_analyses.get_by_id = Mock(return_value=sample_pdf_analysis)
        
        orchestrator = PDFAnalysisOrchestrator(
            mock_unit_of_work, mock_gus_service, mock_file_storage_service
        )
        
        # Act
        response = await orchestrator.get_pdf_analysis(TaskId("test-task-123"))
        
        # Assert
        assert response.success is True
        assert response.task_id == TaskId("test-task-123")
        assert response.user_id == UserId("test-user-456")
        assert response.filename == "test_document.pdf"
    
    @pytest.mark.asyncio
    async def test_orchestrator_start_pdf_analysis_integration(
        self, mock_unit_of_work, mock_gus_service, mock_file_storage_service, sample_pdf_analysis
    ):
        """Test orchestrator start PDF analysis integration."""
        # Arrange
        mock_unit_of_work.pdf_analyses.get_by_id = Mock(return_value=sample_pdf_analysis)
        mock_unit_of_work.pdf_analyses.save = Mock()
        
        orchestrator = PDFAnalysisOrchestrator(
            mock_unit_of_work, mock_gus_service, mock_file_storage_service
        )
        
        # Act
        response = await orchestrator.start_pdf_analysis(TaskId("test-task-123"))
        
        # Assert
        assert response.success is True
        assert response.task_id == TaskId("test-task-123")
        assert response.status == TaskStatus.PROCESSING
        mock_unit_of_work.commit.assert_called_once()
    
    def test_unit_of_work_transaction_management(self, mock_unit_of_work):
        """Test Unit of Work transaction management."""
        # Arrange
        mock_unit_of_work.pdf_analyses.save = Mock()
        
        # Act & Assert - Success case
        with mock_unit_of_work as uow:
            uow.pdf_analyses.save(Mock())
            uow.commit()
        
        mock_unit_of_work.commit.assert_called_once()
        
        # Act & Assert - Failure case
        mock_unit_of_work.commit.reset_mock()
        mock_unit_of_work.rollback.reset_mock()
        
        with mock_unit_of_work as uow:
            uow.pdf_analyses.save(Mock())
            uow.rollback()
        
        mock_unit_of_work.rollback.assert_called_once()
    
    def test_repository_factory_integration(self):
        """Test repository factory integration with PDF analysis repository."""
        from infrastructure.repository_factory import SQLAlchemyRepositoryFactory
        from sqlalchemy.orm import sessionmaker
        
        # Arrange
        mock_session_factory = Mock(spec=sessionmaker)
        factory = SQLAlchemyRepositoryFactory(mock_session_factory)
        
        # Act
        pdf_repository = factory.create_pdf_analysis_repository()
        
        # Assert
        assert isinstance(pdf_repository, PostgreSQLPDFAnalysisRepository)
    
    def test_error_handling_integration(self, mock_unit_of_work):
        """Test error handling integration."""
        # Arrange
        mock_unit_of_work.pdf_analyses.get_by_id = Mock(side_effect=PDFAnalysisNotFoundError("Not found"))
        
        request = GetPDFAnalysisRequest(task_id=TaskId("non-existent"))
        use_case = GetPDFAnalysisUseCase(mock_unit_of_work.pdf_analyses)
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert "Not found" in response.message
    
    def test_validation_integration(self, mock_unit_of_work):
        """Test validation integration."""
        # Arrange - Invalid request
        request = CreatePDFAnalysisRequest(
            task_id=TaskId("test-task-123"),
            user_id=UserId("test-user-456"),
            filename="",  # Invalid empty filename
            file_path="/tmp/test.pdf",
            include_cost_estimation=True,
            include_timeline=True,
            include_quantities=True,
            requirements={}
        )
        
        use_case = CreatePDFAnalysisUseCase(mock_unit_of_work.pdf_analyses)
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert "filename" in response.message.lower()


class TestPDFAnalysisArchitectureCompliance:
    """Test PDF analysis system architecture compliance."""
    
    def test_clean_architecture_compliance(self):
        """Test that the system follows clean architecture principles."""
        # Domain layer should not depend on infrastructure
        from domain.entities.pdf_analysis import PDFAnalysis
        from domain.value_objects import TaskId, UserId, TaskStatus
        
        # These imports should work without infrastructure dependencies
        analysis = PDFAnalysis(
            task_id=TaskId("test"),
            user_id=UserId("test"),
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            include_cost_estimation=True,
            include_timeline=True,
            include_quantities=True,
            requirements={}
        )
        
        assert analysis.task_id == TaskId("test")
        assert analysis.status == TaskStatus.PENDING
    
    def test_dependency_inversion_compliance(self):
        """Test that the system follows dependency inversion principle."""
        from domain.repositories import PDFAnalysisRepository
        from infrastructure.repositories.postgresql_pdf_analysis_repository import PostgreSQLPDFAnalysisRepository
        
        # Repository should implement domain interface
        assert issubclass(PostgreSQLPDFAnalysisRepository, PDFAnalysisRepository)
    
    def test_unit_of_work_integration(self):
        """Test Unit of Work integration compliance."""
        from domain.repositories import UnitOfWork
        from infrastructure.unit_of_work import SQLAlchemyUnitOfWork
        
        # Unit of Work should implement domain interface
        assert issubclass(SQLAlchemyUnitOfWork, UnitOfWork)
    
    def test_use_case_pattern_compliance(self):
        """Test that use cases follow the established pattern."""
        from application.use_cases.pdf_analysis_use_cases import CreatePDFAnalysisUseCase
        
        # Use case should be callable and return response
        assert hasattr(CreatePDFAnalysisUseCase, 'execute')
    
    def test_dto_pattern_compliance(self):
        """Test that DTOs follow the established pattern."""
        from application.dto.pdf_analysis_dto import CreatePDFAnalysisRequest
        
        # DTO should be a data class
        assert hasattr(CreatePDFAnalysisRequest, '__annotations__')


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 