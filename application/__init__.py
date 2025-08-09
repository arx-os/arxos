"""
Application Layer

This module contains the application layer components that coordinate
use cases and provide high-level business operations with infrastructure integration.
"""

from .container import container, ApplicationContainer
from .config import get_config, ApplicationConfig
from .factory import ApplicationServiceFactory, get_building_service, get_health_check, get_metrics, get_logger
from .services.building_service import BuildingApplicationService

# PDF Analysis specific imports
from .use_cases.pdf_analysis_use_cases import (
    CreatePDFAnalysisUseCase, GetPDFAnalysisUseCase,
    StartPDFAnalysisUseCase, CompletePDFAnalysisUseCase,
    FailPDFAnalysisUseCase, CancelPDFAnalysisUseCase,
    GetPDFAnalysisStatusUseCase, GetPDFAnalysisResultUseCase,
    ListPDFAnalysesUseCase, GetPDFAnalysisStatisticsUseCase
)
from .dto.pdf_analysis_dto import (
    CreatePDFAnalysisRequest, CreatePDFAnalysisResponse,
    GetPDFAnalysisRequest, GetPDFAnalysisResponse,
    UpdatePDFAnalysisRequest, UpdatePDFAnalysisResponse,
    DeletePDFAnalysisRequest, DeletePDFAnalysisResponse,
    StartPDFAnalysisRequest, StartPDFAnalysisResponse,
    CompletePDFAnalysisRequest, CompletePDFAnalysisResponse,
    FailPDFAnalysisRequest, FailPDFAnalysisResponse,
    CancelPDFAnalysisRequest, CancelPDFAnalysisResponse,
    GetPDFAnalysisStatusRequest, GetPDFAnalysisStatusResponse,
    GetPDFAnalysisResultRequest, GetPDFAnalysisResultResponse,
    ExportPDFAnalysisRequest, ExportPDFAnalysisResponse,
    ValidatePDFAnalysisRequest, ValidatePDFAnalysisResponse,
    ListPDFAnalysesRequest, ListPDFAnalysesResponse,
    GetPDFAnalysisStatisticsRequest, GetPDFAnalysisStatisticsResponse,
    PDFAnalysisSummary, PDFAnalysisDetails, PDFAnalysisResult,
    PDFAnalysisStatistics, PDFAnalysisExport, PDFAnalysisValidation
)
from .services.pdf_analysis_orchestrator import PDFAnalysisOrchestrator

__all__ = [
    # Container
    'container',
    'ApplicationContainer',

    # Configuration
    'get_config',
    'ApplicationConfig',

    # Factory
    'ApplicationServiceFactory',
    'get_building_service',
    'get_health_check',
    'get_metrics',
    'get_logger',

    # Services
    'BuildingApplicationService',
    'PDFAnalysisOrchestrator',

    # PDF Analysis Use Cases
    'CreatePDFAnalysisUseCase',
    'GetPDFAnalysisUseCase',
    'StartPDFAnalysisUseCase',
    'CompletePDFAnalysisUseCase',
    'FailPDFAnalysisUseCase',
    'CancelPDFAnalysisUseCase',
    'GetPDFAnalysisStatusUseCase',
    'GetPDFAnalysisResultUseCase',
    'ListPDFAnalysesUseCase',
    'GetPDFAnalysisStatisticsUseCase',

    # PDF Analysis DTOs
    'CreatePDFAnalysisRequest',
    'CreatePDFAnalysisResponse',
    'GetPDFAnalysisRequest',
    'GetPDFAnalysisResponse',
    'UpdatePDFAnalysisRequest',
    'UpdatePDFAnalysisResponse',
    'DeletePDFAnalysisRequest',
    'DeletePDFAnalysisResponse',
    'StartPDFAnalysisRequest',
    'StartPDFAnalysisResponse',
    'CompletePDFAnalysisRequest',
    'CompletePDFAnalysisResponse',
    'FailPDFAnalysisRequest',
    'FailPDFAnalysisResponse',
    'CancelPDFAnalysisRequest',
    'CancelPDFAnalysisResponse',
    'GetPDFAnalysisStatusRequest',
    'GetPDFAnalysisStatusResponse',
    'GetPDFAnalysisResultRequest',
    'GetPDFAnalysisResultResponse',
    'ExportPDFAnalysisRequest',
    'ExportPDFAnalysisResponse',
    'ValidatePDFAnalysisRequest',
    'ValidatePDFAnalysisResponse',
    'ListPDFAnalysesRequest',
    'ListPDFAnalysesResponse',
    'GetPDFAnalysisStatisticsRequest',
    'GetPDFAnalysisStatisticsResponse',
    'PDFAnalysisSummary',
    'PDFAnalysisDetails',
    'PDFAnalysisResult',
    'PDFAnalysisStatistics',
    'PDFAnalysisExport',
    'PDFAnalysisValidation',
]
