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

from .entities.ai_agent import (
    AIAgent, AIQuery, AIResponse, AIAgentConfig,
    ModelType, AgentStatus, AIAgentError,
    InvalidConfigurationError, ModelNotAvailableError
)

__all__ = [
    'AIAgent',
    'AIQuery',
    'AIResponse',
    'AIAgentConfig',
    'ModelType',
    'AgentStatus',
    'AIAgentError',
    'InvalidConfigurationError',
    'ModelNotAvailableError'
]
