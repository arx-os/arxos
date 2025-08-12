"""
LLM Service Domain Interface

This module defines the domain service interface for LLM interactions,
keeping the domain layer independent of external LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, AsyncGenerator
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    AZURE_OPENAI = "azure_openai"


@dataclass
class LLMConfig:
    """Configuration for LLM service"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    retry_count: int = 3
    
    def validate(self) -> bool:
        """Validate configuration"""
        if self.provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC] and not self.api_key:
            raise ValueError(f"API key required for {self.provider.value}")
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        if self.max_tokens < 1:
            raise ValueError("Max tokens must be positive")
        return True


@dataclass
class LLMMessage:
    """Message format for LLM"""
    role: str  # system, user, assistant, function
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class LLMFunction:
    """Function definition for LLM function calling"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters
        }


@dataclass
class LLMResponse:
    """Response from LLM service"""
    content: str
    role: str = "assistant"
    function_call: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None  # tokens used
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens used"""
        return self.usage.get('total_tokens', 0) if self.usage else 0


class LLMService(ABC):
    """
    Abstract base class for LLM service.
    
    This interface defines the contract for LLM interactions,
    allowing different implementations (OpenAI, Anthropic, local models).
    """
    
    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None,
        function_call: Optional[str] = None,  # auto, none, or function name
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: List of messages in the conversation
            functions: Optional list of functions the model can call
            function_call: Control function calling behavior
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    async def stream_complete(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion from the LLM.
        
        Args:
            messages: List of messages in the conversation
            functions: Optional list of functions the model can call
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Chunks of generated content
        """
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate the connection to the LLM provider.
        
        Returns:
            True if connection is valid
        """
        pass


class LLMServiceException(Exception):
    """Exception raised by LLM service"""
    pass


class LLMRateLimitException(LLMServiceException):
    """Exception raised when rate limit is hit"""
    pass


class LLMAuthenticationException(LLMServiceException):
    """Exception raised for authentication errors"""
    pass


class LLMTimeoutException(LLMServiceException):
    """Exception raised when request times out"""
    pass