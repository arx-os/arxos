"""
Process GUS Query Use Case

This module contains the use case for processing GUS queries, following
Clean Architecture principles by separating business logic from framework concerns.

Use Case:
- Process natural language queries
- Validate input data
- Handle business rules
- Return structured responses
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from domain.entities.gus_agent import (
    GUSAgent, GUSQuery, GUSResponse, QueryType, 
    GUSAgentError, QueryProcessingError
)


@dataclass
class ProcessGUSQueryRequest:
    """Request DTO for processing GUS queries"""
    query: str
    user_id: str
    query_type: str = "general"
    context: Dict[str, Any] = None
    session_id: Optional[str] = None


@dataclass
class ProcessGUSQueryResponse:
    """Response DTO for GUS query processing"""
    success: bool
    response_id: str
    content: str
    confidence: float
    query_type: str
    processing_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class ProcessGUSQueryUseCase:
    """
    Use case for processing GUS queries.
    
    This use case encapsulates the business logic for processing GUS queries,
    following Clean Architecture principles by being independent of frameworks.
    """
    
    def __init__(self, gus_agent: GUSAgent):
        """
        Initialize the use case.
        
        Args:
            gus_agent: GUS agent instance for processing queries
        """
        self.gus_agent = gus_agent
    
    def execute(self, request: ProcessGUSQueryRequest) -> ProcessGUSQueryResponse:
        """
        Execute the GUS query processing use case.
        
        Args:
            request: GUS query request
            
        Returns:
            GUS query response
            
        Raises:
            QueryProcessingError: If processing fails
        """
        try:
            # Convert string query type to enum
            query_type = self._parse_query_type(request.query_type)
            
            # Create domain query object
            query = GUSQuery(
                id=str(uuid.uuid4()),
                query=request.query,
                user_id=request.user_id,
                query_type=query_type,
                context=request.context or {},
                session_id=request.session_id
            )
            
            # Process query using domain entity
            response = self.gus_agent.process_query(query)
            
            # Convert to response DTO
            return ProcessGUSQueryResponse(
                success=True,
                response_id=response.id,
                content=response.content,
                confidence=response.confidence,
                query_type=response.query_type.value,
                processing_time=response.processing_time,
                metadata=response.metadata
            )
            
        except QueryProcessingError as e:
            return ProcessGUSQueryResponse(
                success=False,
                response_id="",
                content="",
                confidence=0.0,
                query_type="",
                processing_time=0.0,
                error_message=str(e)
            )
        except Exception as e:
            return ProcessGUSQueryResponse(
                success=False,
                response_id="",
                content="",
                confidence=0.0,
                query_type="",
                processing_time=0.0,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _parse_query_type(self, query_type_str: str) -> QueryType:
        """Parse query type string to enum."""
        try:
            return QueryType(query_type_str.lower())
        except ValueError:
            return QueryType.GENERAL 