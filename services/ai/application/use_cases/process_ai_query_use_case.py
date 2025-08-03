"""
Process AI Query Use Case

This module contains the use case for processing AI queries, following
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

from domain.entities.ai_agent import AIAgent, AIQuery, AIResponse, AIAgentError


@dataclass
class ProcessAIQueryRequest:
    """Request DTO for processing AI queries"""
    query: str
    user_id: str
    context: Dict[str, Any] = None
    session_id: Optional[str] = None
    model: str = "gpt-4"


@dataclass
class ProcessAIQueryResponse:
    """Response DTO for AI query processing"""
    success: bool
    response_id: str
    content: str
    confidence: float
    model_used: str
    processing_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class ProcessAIQueryUseCase:
    """
    Use case for processing AI queries.
    
    This use case encapsulates the business logic for processing AI queries,
    following Clean Architecture principles by being independent of frameworks.
    """
    
    def __init__(self, ai_agent: AIAgent):
        """
        Initialize the use case.
        
        Args:
            ai_agent: AI agent instance for processing queries
        """
        self.ai_agent = ai_agent
    
    def execute(self, request: ProcessAIQueryRequest) -> ProcessAIQueryResponse:
        """
        Execute the AI query processing use case.
        
        Args:
            request: AI query request
            
        Returns:
            AI query response
            
        Raises:
            AIAgentError: If processing fails
        """
        try:
            # Create domain query object
            query = AIQuery(
                id=str(uuid.uuid4()),
                query=request.query,
                user_id=request.user_id,
                context=request.context or {},
                session_id=request.session_id,
                model=request.model
            )
            
            # Process query using domain entity
            response = self.ai_agent.process_query(query)
            
            # Convert to response DTO
            return ProcessAIQueryResponse(
                success=True,
                response_id=response.id,
                content=response.content,
                confidence=response.confidence,
                model_used=response.model_used.value,
                processing_time=response.processing_time,
                metadata=response.metadata
            )
            
        except AIAgentError as e:
            return ProcessAIQueryResponse(
                success=False,
                response_id="",
                content="",
                confidence=0.0,
                model_used="",
                processing_time=0.0,
                error_message=str(e)
            )
        except Exception as e:
            return ProcessAIQueryResponse(
                success=False,
                response_id="",
                content="",
                confidence=0.0,
                model_used="",
                processing_time=0.0,
                error_message=f"Unexpected error: {str(e)}"
            ) 