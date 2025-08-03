"""
AI Agent Infrastructure Implementation

This module contains the concrete implementation of the AI agent that
handles external dependencies (API calls, HTTP requests, etc.) while
keeping the domain layer pure and framework-independent.

Infrastructure Concerns:
- HTTP client for API calls
- Configuration management
- Logging and monitoring
- Error handling for external services
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
import aiohttp
import structlog
import uuid

from domain.entities.ai_agent import (
    AIAgent, AIQuery, AIResponse, AIAgentConfig, 
    ModelType, AIAgentError, InvalidConfigurationError
)


logger = structlog.get_logger()


class OpenAIAPIClient:
    """HTTP client for OpenAI API calls"""
    
    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize OpenAI API client.
        
        Args:
            api_key: OpenAI API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_chat_completion(
        self, 
        messages: list, 
        model: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Create chat completion via OpenAI API.
        
        Args:
            messages: List of message objects
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            API response
            
        Raises:
            AIAgentError: If API call fails
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise AIAgentError(f"API call failed: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            raise AIAgentError("API call timed out")
        except aiohttp.ClientError as e:
            raise AIAgentError(f"HTTP client error: {e}")
        except Exception as e:
            raise AIAgentError(f"Unexpected error in API call: {e}")


class ConcreteAIAgent(AIAgent):
    """
    Concrete implementation of AI Agent.
    
    This class implements the abstract AIAgent domain entity and handles
    all infrastructure concerns like HTTP calls, configuration, etc.
    """
    
    def __init__(self, config: AIAgentConfig):
        """
        Initialize concrete AI agent.
        
        Args:
            config: AI agent configuration
        """
        super().__init__(config)
        self.api_client = OpenAIAPIClient(config.api_key, config.timeout)
        logger.info("Concrete AI Agent initialized", agent_id=self.id)
    
    def _process_query_implementation(self, query: AIQuery) -> AIResponse:
        """
        Process query implementation using OpenAI API.
        
        Args:
            query: AI query to process
            
        Returns:
            AI response
        """
        start_time = time.time()
        
        try:
            # Prepare messages for API call
            messages = self._prepare_messages(query)
            
            # Make API call
            api_response = asyncio.run(
                self.api_client.create_chat_completion(
                    messages=messages,
                    model=query.model.value,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
            )
            
            # Extract response content
            content = self._extract_response_content(api_response)
            confidence = self._calculate_confidence(api_response)
            processing_time = time.time() - start_time
            
            # Create response object
            response = AIResponse(
                id=str(uuid.uuid4()),
                query_id=query.id,
                content=content,
                confidence=confidence,
                model_used=query.model,
                processing_time=processing_time,
                metadata={
                    "api_response": api_response,
                    "tokens_used": api_response.get("usage", {}).get("total_tokens", 0)
                }
            )
            
            logger.info(
                "Query processed successfully",
                query_id=query.id,
                response_id=response.id,
                processing_time=processing_time,
                tokens_used=response.metadata.get("tokens_used", 0)
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                "Failed to process query",
                query_id=query.id,
                error=str(e),
                processing_time=processing_time
            )
            raise AIAgentError(f"Failed to process query: {e}")
    
    def _prepare_messages(self, query: AIQuery) -> list:
        """Prepare messages for API call."""
        messages = []
        
        # Add system message if context provided
        if query.context.get("system_prompt"):
            messages.append({
                "role": "system",
                "content": query.context["system_prompt"]
            })
        
        # Add conversation history
        history = self.get_conversation_history(query.user_id, limit=5)
        for hist_query in history:
            messages.append({
                "role": "user",
                "content": hist_query.query
            })
        
        # Add current query
        messages.append({
            "role": "user",
            "content": query.query
        })
        
        return messages
    
    def _extract_response_content(self, api_response: Dict[str, Any]) -> str:
        """Extract content from API response."""
        try:
            choices = api_response.get("choices", [])
            if not choices:
                raise AIAgentError("No choices in API response")
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                raise AIAgentError("No content in API response")
            
            return content
            
        except KeyError as e:
            raise AIAgentError(f"Invalid API response format: {e}")
    
    def _calculate_confidence(self, api_response: Dict[str, Any]) -> float:
        """Calculate confidence score from API response."""
        try:
            # For now, use a simple heuristic based on finish_reason
            choices = api_response.get("choices", [])
            if not choices:
                return 0.0
            
            finish_reason = choices[0].get("finish_reason", "")
            
            # Map finish reasons to confidence scores
            confidence_map = {
                "stop": 0.9,  # Normal completion
                "length": 0.7,  # Hit token limit
                "content_filter": 0.5,  # Content filtered
                "null": 0.3  # Unknown reason
            }
            
            return confidence_map.get(finish_reason, 0.5)
            
        except Exception:
            return 0.5  # Default confidence 