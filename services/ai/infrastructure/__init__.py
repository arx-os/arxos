"""
Infrastructure Layer

This package contains the concrete implementations that handle
external concerns like databases, APIs, frameworks, etc.

Clean Architecture Principles:
- Infrastructure layer is the outermost layer
- Implements interfaces defined by domain/application layers
- Handles external dependencies and frameworks
- Provides concrete implementations
"""

from .ai_agent_impl import ConcreteAIAgent, OpenAIAPIClient

__all__ = [
    'ConcreteAIAgent',
    'OpenAIAPIClient'
]
