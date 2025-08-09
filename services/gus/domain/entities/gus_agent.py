"""
GUS Agent Domain Entity

This module contains the core GUS agent domain entity that is completely
independent of any framework or external dependencies.

Business Rules:
- GUS agent must have valid configuration
- GUS agent must support multiple query types
- GUS agent must handle errors gracefully
- GUS agent must maintain conversation context
- GUS agent must support knowledge management
- GUS agent must support PDF analysis

Domain Events:
- GUSAgentInitialized
- GUSQueryProcessed
- GUSTaskExecuted
- GUSKnowledgeQueried
- GUSPDFAnalyzed
- GUSErrorOccurred
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
import uuid


class AgentStatus(Enum):
    """GUS Agent status enumeration"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class QueryType(Enum):
    """Supported query types"""
    GENERAL = "general"
    CAD = "cad"
    KNOWLEDGE = "knowledge"
    TASK = "task"
    PDF_ANALYSIS = "pdf_analysis"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GUSQuery:
    """GUS query domain object"""
    id: str
    query: str
    user_id: str
    query_type: QueryType = QueryType.GENERAL
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GUSResponse:
    """GUS response domain object"""
    id: str
    query_id: str
    content: str
    confidence: float
    query_type: QueryType
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GUSTask:
    """GUS task domain object"""
    id: str
    task: str
    parameters: Dict[str, Any]
    user_id: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeQuery:
    """Knowledge query domain object"""
    id: str
    topic: str
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PDFAnalysisRequest:
    """PDF analysis request domain object"""
    id: str
    pdf_file_path: str
    requirements: Dict[str, Any] = field(default_factory=dict)
    user_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GUSAgentConfig:
    """GUS Agent configuration domain object"""
    model_type: str
    api_key: str
    knowledge_base_path: str
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    cache_enabled: bool = True
    logging_enabled: bool = True


class GUSAgentError(Exception):
    """Base exception for GUS agent errors"""
    pass


class InvalidConfigurationError(GUSAgentError):
    """Raised when GUS agent configuration is invalid"""
    pass


class QueryProcessingError(GUSAgentError):
    """Raised when query processing fails"""
    pass


class TaskExecutionError(GUSAgentError):
    """Raised when task execution fails"""
    pass


class KnowledgeQueryError(GUSAgentError):
    """Raised when knowledge query fails"""
    pass


class PDFAnalysisError(GUSAgentError):
    """Raised when PDF analysis fails"""
    pass


class GUSAgent(ABC):
    """
    Abstract GUS Agent domain entity

    This is the core business logic for GUS operations, completely
    independent of any framework or external dependencies.
    """

    def __init__(self, config: GUSAgentConfig):
        """
        Initialize GUS Agent with configuration.

        Args:
            config: GUS agent configuration

        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        self._validate_config(config)
        self._config = config
        self._status = AgentStatus.INITIALIZING
        self._conversation_history: List[GUSQuery] = []
        self._domain_events: List[Any] = []
        self._id = str(uuid.uuid4()
        self._initialize_agent()

    def _validate_config(self, config: GUSAgentConfig) -> None:
        """Validate GUS agent configuration."""
        if not config.api_key:
            raise InvalidConfigurationError("API key is required")

        if not config.knowledge_base_path:
            raise InvalidConfigurationError("Knowledge base path is required")

        if config.max_tokens <= 0:
            raise InvalidConfigurationError("Max tokens must be positive")

        if not 0 <= config.temperature <= 1:
            raise InvalidConfigurationError("Temperature must be between 0 and 1")

        if config.timeout <= 0:
            raise InvalidConfigurationError("Timeout must be positive")

    def _initialize_agent(self) -> None:
        """Initialize the GUS agent."""
        try:
            self._status = AgentStatus.READY
            self._add_domain_event("GUSAgentInitialized", {
                "agent_id": self._id,
                "model_type": self._config.model_type,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            self._status = AgentStatus.ERROR
            raise GUSAgentError(f"Failed to initialize GUS agent: {e}")

    @property
def id(self) -> str:
        """Get GUS agent ID."""
        return self._id

    @property
def status(self) -> AgentStatus:
        """Get GUS agent status."""
        return self._status

    @property
def config(self) -> GUSAgentConfig:
        """Get GUS agent configuration."""
        return self._config

    @property
def domain_events(self) -> List[Any]:
        """Get domain events."""
        return self._domain_events.copy()

    def process_query(self, query: GUSQuery) -> GUSResponse:
        """
        Process a GUS query.

        Args:
            query: GUS query to process

        Returns:
            GUS response

        Raises:
            QueryProcessingError: If processing fails
        """
        if self._status != AgentStatus.READY:
            raise QueryProcessingError(f"Agent is not ready. Status: {self._status}")

        try:
            self._status = AgentStatus.BUSY

            # Validate query
            self._validate_query(query)

            # Process query using abstract method
            response = self._process_query_implementation(query)

            # Update conversation history
            self._conversation_history.append(query)

            # Add domain event
            self._add_domain_event("GUSQueryProcessed", {
                "query_id": query.id,
                "response_id": response.id,
                "query_type": query.query_type.value,
                "processing_time": response.processing_time,
                "timestamp": datetime.utcnow()
            })

            self._status = AgentStatus.READY
            return response

        except Exception as e:
            self._status = AgentStatus.ERROR
            self._add_domain_event("GUSErrorOccurred", {
                "query_id": query.id,
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            raise QueryProcessingError(f"Failed to process query: {e}")

    def execute_task(self, task: GUSTask) -> GUSTask:
        """
        Execute a GUS task.

        Args:
            task: GUS task to execute

        Returns:
            Updated GUS task with result

        Raises:
            TaskExecutionError: If execution fails
        """
        if self._status != AgentStatus.READY:
            raise TaskExecutionError(f"Agent is not ready. Status: {self._status}")

        try:
            self._status = AgentStatus.BUSY
            task.status = TaskStatus.RUNNING

            # Execute task using abstract method
            result = self._execute_task_implementation(task)

            # Update task with result
            task.result = result
            task.status = TaskStatus.COMPLETED

            # Add domain event
            self._add_domain_event("GUSTaskExecuted", {
                "task_id": task.id,
                "task": task.task,
                "status": task.status.value,
                "timestamp": datetime.utcnow()
            })

            self._status = AgentStatus.READY
            return task

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            self._status = AgentStatus.ERROR
            self._add_domain_event("GUSErrorOccurred", {
                "task_id": task.id,
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            raise TaskExecutionError(f"Failed to execute task: {e}")

    def query_knowledge(self, knowledge_query: KnowledgeQuery) -> GUSResponse:
        """
        Query knowledge base.

        Args:
            knowledge_query: Knowledge query to process

        Returns:
            GUS response with knowledge

        Raises:
            KnowledgeQueryError: If query fails
        """
        if self._status != AgentStatus.READY:
            raise KnowledgeQueryError(f"Agent is not ready. Status: {self._status}")

        try:
            self._status = AgentStatus.BUSY

            # Query knowledge using abstract method
            response = self._query_knowledge_implementation(knowledge_query)

            # Add domain event
            self._add_domain_event("GUSKnowledgeQueried", {
                "query_id": knowledge_query.id,
                "topic": knowledge_query.topic,
                "response_id": response.id,
                "timestamp": datetime.utcnow()
            })

            self._status = AgentStatus.READY
            return response

        except Exception as e:
            self._status = AgentStatus.ERROR
            self._add_domain_event("GUSErrorOccurred", {
                "query_id": knowledge_query.id,
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            raise KnowledgeQueryError(f"Failed to query knowledge: {e}")

    def analyze_pdf(self, pdf_request: PDFAnalysisRequest) -> GUSResponse:
        """
        Analyze PDF document.

        Args:
            pdf_request: PDF analysis request

        Returns:
            GUS response with analysis results

        Raises:
            PDFAnalysisError: If analysis fails
        """
        if self._status != AgentStatus.READY:
            raise PDFAnalysisError(f"Agent is not ready. Status: {self._status}")

        try:
            self._status = AgentStatus.BUSY

            # Analyze PDF using abstract method
            response = self._analyze_pdf_implementation(pdf_request)

            # Add domain event
            self._add_domain_event("GUSPDFAnalyzed", {
                "request_id": pdf_request.id,
                "pdf_file_path": pdf_request.pdf_file_path,
                "response_id": response.id,
                "timestamp": datetime.utcnow()
            })

            self._status = AgentStatus.READY
            return response

        except Exception as e:
            self._status = AgentStatus.ERROR
            self._add_domain_event("GUSErrorOccurred", {
                "request_id": pdf_request.id,
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            raise PDFAnalysisError(f"Failed to analyze PDF: {e}")

    def _validate_query(self, query: GUSQuery) -> None:
        """Validate GUS query."""
        if not query.query.strip():
            raise QueryProcessingError("Query cannot be empty")

        if not query.user_id:
            raise QueryProcessingError("User ID is required")

    @abstractmethod
def _process_query_implementation(self, query: GUSQuery) -> GUSResponse:
        """
        Abstract method for processing queries.

        This must be implemented by concrete GUS agent implementations.
        """
        pass

    @abstractmethod
def _execute_task_implementation(self, task: GUSTask) -> Dict[str, Any]:
        """
        Abstract method for executing tasks.

        This must be implemented by concrete GUS agent implementations.
        """
        pass

    @abstractmethod
def _query_knowledge_implementation(self, knowledge_query: KnowledgeQuery) -> GUSResponse:
        """
        Abstract method for querying knowledge.

        This must be implemented by concrete GUS agent implementations.
        """
        pass

    @abstractmethod
def _analyze_pdf_implementation(self, pdf_request: PDFAnalysisRequest) -> GUSResponse:
        """
        Abstract method for analyzing PDFs.

        This must be implemented by concrete GUS agent implementations.
        """
        pass

    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[GUSQuery]:
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
        """Shutdown the GUS agent."""
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
