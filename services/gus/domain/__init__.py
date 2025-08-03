"""
Domain Layer

This package contains the core business logic and domain entities
that are completely independent of any framework or external dependencies.

Clean Architecture Principles:
- Domain layer is the innermost layer
- No dependencies on external frameworks
- Pure business logic and rules
- Framework-agnostic design
"""

from .entities.gus_agent import (
    GUSAgent, GUSQuery, GUSResponse, GUSTask, KnowledgeQuery,
    PDFAnalysisRequest, GUSAgentConfig, QueryType, TaskStatus,
    AgentStatus, GUSAgentError, InvalidConfigurationError,
    QueryProcessingError, TaskExecutionError, KnowledgeQueryError,
    PDFAnalysisError
)

__all__ = [
    'GUSAgent',
    'GUSQuery',
    'GUSResponse',
    'GUSTask',
    'KnowledgeQuery',
    'PDFAnalysisRequest',
    'GUSAgentConfig',
    'QueryType',
    'TaskStatus',
    'AgentStatus',
    'GUSAgentError',
    'InvalidConfigurationError',
    'QueryProcessingError',
    'TaskExecutionError',
    'KnowledgeQueryError',
    'PDFAnalysisError'
] 