"""
AI Agent Domain Entity

This module contains the core AI agent domain entity that is completely
independent of any framework or external dependencies.

Business Rules:
- AI agent must have a valid configuration
- AI agent must support multiple model types
- AI agent must handle errors gracefully
- AI agent must maintain conversation context

Domain Events:
- AIAgentInitialized
- AIAgentQueryProcessed
- AIAgentErrorOccurred
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
import uuid


class AgentStatus(Enum):
    """AI Agent status enumeration"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class ModelType(Enum):
    """Supported AI model types"""
    GPT_4 = "gpt-4"
    GPT_3_5 = "gpt-3.5-turbo"
    CLAUDE = "claude"
    CUSTOM = "custom"


@dataclass
class AIQuery:
    """AI query domain object"""
    id: str
    query: str
    user_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    model: ModelType = ModelType.GPT_4
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AIResponse:
    """AI response domain object"""
    id: str
    query_id: str
    content: str
    confidence: float
    model_used: ModelType
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AIAgentConfig:
    """AI Agent configuration domain object"""
    model_type: ModelType
    api_key: str
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    cache_enabled: bool = True
    logging_enabled: bool = True


class AIAgentError(Exception):
    """Base exception for AI agent errors"""
    pass


class InvalidConfigurationError(AIAgentError):
    """Raised when AI agent configuration is invalid"""
    pass


class ModelNotAvailableError(AIAgentError):
    """Raised when requested model is not available"""
    pass


class AIAgent(ABC):
    """
    Abstract AI Agent domain entity

    This is the core business logic for AI operations, completely
    independent of any framework or external dependencies.
    """

    def __init__(self, config: AIAgentConfig):
        """
        Initialize AI Agent with configuration.

        Args:
            config: AI agent configuration

        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        self._validate_config(config)
        self._config = config
        self._status = AgentStatus.INITIALIZING
        self._conversation_history: List[AIQuery] = []
        self._domain_events: List[Any] = []
        self._id = str(uuid.uuid4()
        self._initialize_agent()

    def _validate_config(self, config: AIAgentConfig) -> None:
        """Validate AI agent configuration."""
        if not config.api_key:
            raise InvalidConfigurationError("API key is required")

        if config.max_tokens <= 0:
            raise InvalidConfigurationError("Max tokens must be positive")

        if not 0 <= config.temperature <= 1:
            raise InvalidConfigurationError("Temperature must be between 0 and 1")

        if config.timeout <= 0:
            raise InvalidConfigurationError("Timeout must be positive")

    def _initialize_agent(self) -> None:
        """Initialize the AI agent."""
        try:
            self._status = AgentStatus.READY
            self._add_domain_event("AIAgentInitialized", {
                "agent_id": self._id,
                "model_type": self._config.model_type.value,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            self._status = AgentStatus.ERROR
            raise AIAgentError(f"Failed to initialize AI agent: {e}")

    @property
def id(self) -> str:
        """Get AI agent ID."""
        return self._id

    @property
def status(self) -> AgentStatus:
        """Get AI agent status."""
        return self._status

    @property
def config(self) -> AIAgentConfig:
        """Get AI agent configuration."""
        return self._config

    @property
def domain_events(self) -> List[Any]:
        """Get domain events."""
        return self._domain_events.copy()

    def process_query(self, query: AIQuery) -> AIResponse:
        """
        Process an AI query.

        Args:
            query: AI query to process

        Returns:
            AI response

        Raises:
            AIAgentError: If processing fails
        """
        if self._status != AgentStatus.READY:
            raise AIAgentError(f"Agent is not ready. Status: {self._status}")

        try:
            self._status = AgentStatus.BUSY

            # Validate query
            self._validate_query(query)

            # Process query using abstract method
            response = self._process_query_implementation(query)

            # Update conversation history
            self._conversation_history.append(query)

            # Add domain event
            self._add_domain_event("AIAgentQueryProcessed", {
                "query_id": query.id,
                "response_id": response.id,
                "processing_time": response.processing_time,
                "timestamp": datetime.utcnow()
            })

            self._status = AgentStatus.READY
            return response

        except Exception as e:
            self._status = AgentStatus.ERROR
            self._add_domain_event("AIAgentErrorOccurred", {
                "query_id": query.id,
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            raise AIAgentError(f"Failed to process query: {e}")

    def _validate_query(self, query: AIQuery) -> None:
        """Validate AI query."""
        if not query.query.strip():
            raise AIAgentError("Query cannot be empty")

        if not query.user_id:
            raise AIAgentError("User ID is required")

        if query.model not in ModelType:
            raise ModelNotAvailableError(f"Model {query.model} is not available")

    @abstractmethod
def _process_query_implementation(self, query: AIQuery) -> AIResponse:
        """
        Abstract method for processing queries.

        This must be implemented by concrete AI agent implementations.
        """
        pass

    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[AIQuery]:
        """Get conversation history for a user."""
        return [
            query for query in self._conversation_history[-limit:]
            if query.user_id == user_id
        ]

    def clear_conversation_history(self, user_id: Optional[str] = None) -> None:
        """Clear conversation history."""
        if user_id:
            self._conversation_history = [
                query for query in self._conversation_history
                if query.user_id != user_id
            ]
        else:
            self._conversation_history.clear()

    def shutdown(self) -> None:
        """Shutdown the AI agent."""
        self._status = AgentStatus.SHUTDOWN
        self._conversation_history.clear()
        self._domain_events.clear()

    def _add_domain_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add domain event."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow()
        }
        self._domain_events.append(event)
