"""
OpenAI LLM Service Implementation

This module provides the OpenAI implementation of the LLM service interface.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import openai
from openai import AsyncOpenAI
import tiktoken
import structlog

from domain.services.llm_service import (
    LLMService, LLMConfig, LLMMessage, LLMFunction, LLMResponse,
    LLMServiceException, LLMRateLimitException, LLMAuthenticationException,
    LLMTimeoutException, LLMProvider
)

logger = structlog.get_logger()


class OpenAILLMService(LLMService):
    """OpenAI implementation of LLM service"""
    
    def __init__(self, config: LLMConfig):
        """
        Initialize OpenAI LLM service.
        
        Args:
            config: LLM configuration
        """
        if config.provider != LLMProvider.OPENAI:
            raise ValueError(f"Invalid provider: {config.provider}")
        
        config.validate()
        self.config = config
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=config.api_key or os.getenv("OPENAI_API_KEY"),
            base_url=config.api_base,
            timeout=config.timeout,
            max_retries=config.retry_count
        )
        
        # Initialize tokenizer for token counting
        try:
            self.encoding = tiktoken.encoding_for_model(config.model)
        except KeyError:
            # Fallback to cl100k_base encoding for newer models
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"Initialized OpenAI LLM service with model: {config.model}")
    
    async def complete(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None,
        function_call: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion from OpenAI"""
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)
            
            # Prepare request parameters
            params = {
                "model": self.config.model,
                "messages": openai_messages,
                "temperature": kwargs.get('temperature', self.config.temperature),
                "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
                "top_p": kwargs.get('top_p', self.config.top_p),
                "frequency_penalty": kwargs.get('frequency_penalty', self.config.frequency_penalty),
                "presence_penalty": kwargs.get('presence_penalty', self.config.presence_penalty),
            }
            
            # Add functions if provided
            if functions:
                params["tools"] = [
                    {
                        "type": "function",
                        "function": func.to_dict()
                    }
                    for func in functions
                ]
                if function_call:
                    if function_call == "auto":
                        params["tool_choice"] = "auto"
                    elif function_call == "none":
                        params["tool_choice"] = "none"
                    else:
                        params["tool_choice"] = {
                            "type": "function",
                            "function": {"name": function_call}
                        }
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            # Extract response
            choice = response.choices[0]
            message = choice.message
            
            # Build LLM response
            llm_response = LLMResponse(
                content=message.content or "",
                role=message.role,
                model=response.model,
                finish_reason=choice.finish_reason,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                } if response.usage else None
            )
            
            # Handle function calls (tool calls in new API)
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                llm_response.function_call = {
                    'name': tool_call.function.name,
                    'arguments': tool_call.function.arguments
                }
            
            logger.debug(f"OpenAI completion successful: {llm_response.total_tokens} tokens")
            return llm_response
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {e}")
            raise LLMRateLimitException(str(e))
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            raise LLMAuthenticationException(str(e))
        except asyncio.TimeoutError as e:
            logger.error(f"OpenAI timeout error: {e}")
            raise LLMTimeoutException(str(e))
        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            raise LLMServiceException(str(e))
    
    async def stream_complete(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[LLMFunction]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from OpenAI"""
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)
            
            # Prepare request parameters
            params = {
                "model": self.config.model,
                "messages": openai_messages,
                "temperature": kwargs.get('temperature', self.config.temperature),
                "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
                "stream": True
            }
            
            # Add functions if provided
            if functions:
                params["tools"] = [
                    {
                        "type": "function",
                        "function": func.to_dict()
                    }
                    for func in functions
                ]
            
            # Make streaming API call
            stream = await self.client.chat.completions.create(**params)
            
            # Stream response chunks
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {e}")
            raise LLMRateLimitException(str(e))
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise LLMServiceException(str(e))
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI"""
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise LLMServiceException(str(e))
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Token counting error: {e}")
            # Fallback to rough estimation
            return len(text.split()) * 1.3
    
    async def validate_connection(self) -> bool:
        """Validate OpenAI API connection"""
        try:
            # Try a simple API call
            response = await self.client.models.list()
            return bool(response.data)
        except openai.AuthenticationError:
            logger.error("OpenAI authentication failed")
            return False
        except Exception as e:
            logger.error(f"OpenAI connection validation error: {e}")
            return False
    
    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert LLMMessage objects to OpenAI format"""
        openai_messages = []
        for msg in messages:
            openai_msg = {
                "role": msg.role,
                "content": msg.content
            }
            if msg.name:
                openai_msg["name"] = msg.name
            if msg.function_call:
                openai_msg["tool_calls"] = [{
                    "type": "function",
                    "function": msg.function_call
                }]
            openai_messages.append(openai_msg)
        return openai_messages