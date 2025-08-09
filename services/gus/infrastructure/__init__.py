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

from .gus_agent_impl import (
    ConcreteGUSAgent, OpenAIClient, KnowledgeBaseManager, PDFAnalyzer
)

__all__ = [
    'ConcreteGUSAgent',
    'OpenAIClient',
    'KnowledgeBaseManager',
    'PDFAnalyzer'
]
