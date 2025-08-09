"""
Application Layer

This package contains the use cases and application services that
orchestrate the domain logic and handle application-specific concerns.

Clean Architecture Principles:
- Application layer depends only on domain layer
- Contains use cases and application services
- Handles orchestration and coordination
- Framework-independent business operations
"""

from .use_cases.process_ai_query_use_case import (
    ProcessAIQueryUseCase,
    ProcessAIQueryRequest,
    ProcessAIQueryResponse
)

__all__ = [
    'ProcessAIQueryUseCase',
    'ProcessAIQueryRequest',
    'ProcessAIQueryResponse'
]
