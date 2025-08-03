"""
GUS Service for PDF Analysis

This module contains the GUS service interface for PDF analysis operations.
It provides integration with the GUS agent for PDF processing and analysis.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
import asyncio

from domain.value_objects import TaskId, ConfidenceScore, AnalysisResult
from domain.exceptions import ServiceError, ProcessingError


class GUSService:
    """
    GUS service for PDF analysis operations.
    
    This service provides integration with the GUS agent for PDF processing,
    symbol recognition, and system schedule generation.
    """
    
    def __init__(self, gus_base_url: str, timeout: int = 300):
    """
    Perform __init__ operation

Args:
        gus_base_url: Description of gus_base_url
        timeout: Description of timeout

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.gus_base_url = gus_base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # HTTP client for GUS communication
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def analyze_pdf(
        self,
        task_id: str,
        file_content: bytes,
        filename: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> 'PDFAnalysisResult':
        """
        Analyze a PDF file using GUS service.
        
        Args:
            task_id: Task ID for tracking
            file_content: PDF file content as bytes
            filename: Original filename
            requirements: Analysis requirements
            
        Returns:
            PDFAnalysisResult with analysis data
            
        Raises:
            ServiceError: If service communication fails
            ProcessingError: If PDF processing fails
        """
        try:
            self.logger.info(f"Starting PDF analysis for task: {task_id}")
            
            # Prepare request data
            request_data = {
                'task_id': task_id,
                'filename': filename,
                'requirements': requirements or {},
                'include_cost_estimation': requirements.get('include_cost_estimation', True),
                'include_timeline': requirements.get('include_timeline', True),
                'include_quantities': requirements.get('include_quantities', True)
            }
            
            # Send file and analysis request to GUS
            files = {'file': (filename, file_content, 'application/pdf')}
            
            async with self.client.stream(
                'POST',
                f"{self.gus_base_url}/api/v1/pdf_analysis",
                data=request_data,
                files=files
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise ServiceError(f"GUS service error: {response.status_code} - {error_text}")
                
                # Process streaming response
                result_data = await self._process_streaming_response(response)
                
                # Convert to domain result
                return self._convert_to_analysis_result(result_data)
                
        except httpx.RequestError as e:
            self.logger.error(f"HTTP error during PDF analysis: {e}")
            raise ServiceError(f"Failed to communicate with GUS service: {e}")
        except Exception as e:
            self.logger.error(f"Error during PDF analysis: {e}")
            raise ProcessingError(f"PDF analysis failed: {e}")
    
    async def get_analysis_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get analysis status from GUS service.
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Status information
            
        Raises:
            ServiceError: If service communication fails
        """
        try:
            response = await self.client.get(
                f"{self.gus_base_url}/api/v1/pdf_analysis/{task_id}/status"
            )
            
            if response.status_code != 200:
                raise ServiceError(f"GUS service error: {response.status_code}")
            
            return response.json()
            
        except httpx.RequestError as e:
            self.logger.error(f"HTTP error getting analysis status: {e}")
            raise ServiceError(f"Failed to get analysis status: {e}")
    
    async def get_analysis_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get analysis result from GUS service.
        
        Args:
            task_id: Task ID to retrieve result for
            
        Returns:
            Analysis result data
            
        Raises:
            ServiceError: If service communication fails
        """
        try:
            response = await self.client.get(
                f"{self.gus_base_url}/api/v1/pdf_analysis/{task_id}/result"
            )
            
            if response.status_code != 200:
                raise ServiceError(f"GUS service error: {response.status_code}")
            
            return response.json()
            
        except httpx.RequestError as e:
            self.logger.error(f"HTTP error getting analysis result: {e}")
            raise ServiceError(f"Failed to get analysis result: {e}")
    
    async def cancel_analysis(self, task_id: str) -> bool:
        """
        Cancel analysis in GUS service.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled successfully
            
        Raises:
            ServiceError: If service communication fails
        """
        try:
            response = await self.client.post(
                f"{self.gus_base_url}/api/v1/pdf_analysis/{task_id}/cancel"
            )
            
            if response.status_code != 200:
                raise ServiceError(f"GUS service error: {response.status_code}")
            
            return response.json().get('success', False)
            
        except httpx.RequestError as e:
            self.logger.error(f"HTTP error cancelling analysis: {e}")
            raise ServiceError(f"Failed to cancel analysis: {e}")
    
    async def validate_analysis(self, task_id: str) -> Dict[str, Any]:
        """
        Validate analysis result in GUS service.
        
        Args:
            task_id: Task ID to validate
            
        Returns:
            Validation results
            
        Raises:
            ServiceError: If service communication fails
        """
        try:
            response = await self.client.post(
                f"{self.gus_base_url}/api/v1/pdf_analysis/{task_id}/validate"
            )
            
            if response.status_code != 200:
                raise ServiceError(f"GUS service error: {response.status_code}")
            
            return response.json()
            
        except httpx.RequestError as e:
            self.logger.error(f"HTTP error validating analysis: {e}")
            raise ServiceError(f"Failed to validate analysis: {e}")
    
    async def export_analysis(
        self,
        task_id: str,
        export_format: str,
        include_metadata: bool = True
    ) -> bytes:
        """
        Export analysis result from GUS service.
        
        Args:
            task_id: Task ID to export
            export_format: Export format ('json', 'csv', 'pdf', 'excel')
            include_metadata: Whether to include metadata
            
        Returns:
            Exported file content as bytes
            
        Raises:
            ServiceError: If service communication fails
        """
        try:
            params = {
                'format': export_format,
                'include_metadata': include_metadata
            }
            
            response = await self.client.get(
                f"{self.gus_base_url}/api/v1/pdf_analysis/{task_id}/export",
                params=params
            )
            
            if response.status_code != 200:
                raise ServiceError(f"GUS service error: {response.status_code}")
            
            return response.content
            
        except httpx.RequestError as e:
            self.logger.error(f"HTTP error exporting analysis: {e}")
            raise ServiceError(f"Failed to export analysis: {e}")
    
    async def _process_streaming_response(self, response) -> Dict[str, Any]:
        """
        Process streaming response from GUS service.
        
        Args:
            response: Streaming HTTP response
            
        Returns:
            Processed result data
        """
        result_data = {}
        
        async for line in response.aiter_lines():
            if not line.strip():
                continue
                
            try:
                # Parse JSON line
                data = response.json()
                
                # Handle different response types
                if 'progress' in data:
                    self.logger.info(f"Progress: {data['progress']}%")
                elif 'status' in data:
                    self.logger.info(f"Status: {data['status']}")
                elif 'result' in data:
                    result_data = data['result']
                    break
                elif 'error' in data:
                    raise ProcessingError(f"GUS processing error: {data['error']}")
                    
            except Exception as e:
                self.logger.warning(f"Error parsing streaming response: {e}")
                continue
        
        return result_data
    
    def _convert_to_analysis_result(self, result_data: Dict[str, Any]) -> 'PDFAnalysisResult':
        """
        Convert GUS result data to domain AnalysisResult.
        
        Args:
            result_data: Raw result data from GUS
            
        Returns:
            PDFAnalysisResult with domain objects
        """
        from domain.value_objects import ConfidenceScore, AnalysisResult
        
        # Extract confidence score
        confidence_value = result_data.get('confidence', 0.0)
        confidence = ConfidenceScore(confidence_value)
        
        # Extract systems found
        systems_found = result_data.get('systems_found', [])
        
        # Extract total components
        total_components = result_data.get('total_components', 0)
        
        # Create analysis result
        analysis_result = AnalysisResult(
            project_info=result_data.get('project_info', {}),
            systems=result_data.get('systems', {}),
            quantities=result_data.get('quantities', {}),
            cost_estimates=result_data.get('cost_estimates', {}),
            timeline=result_data.get('timeline', {}),
            confidence=confidence,
            metadata=result_data.get('metadata', {}),
            created_at=datetime.utcnow()
        )
        
        return PDFAnalysisResult(
            confidence=confidence,
            systems_found=systems_found,
            total_components=total_components,
            analysis_result=analysis_result
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class PDFAnalysisResult:
    """
    Perform __init__ operation

Args:
        confidence: Description of confidence
        systems_found: Description of systems_found
        total_components: Description of total_components
        analysis_result: Description of analysis_result

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Result container for PDF analysis."""
    
    def __init__(
        self,
        confidence: ConfidenceScore,
        systems_found: list,
        total_components: int,
        analysis_result: AnalysisResult
    ):
        self.confidence = confidence
        self.systems_found = systems_found
        self.total_components = total_components
        self.analysis_result = analysis_result 