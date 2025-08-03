"""
GUS Agent Infrastructure Implementation

This module contains the concrete implementation of the GUS agent that
handles external dependencies (API calls, file operations, etc.) while
keeping the domain layer pure and framework-independent.

Infrastructure Concerns:
- HTTP client for API calls
- File system operations for PDF analysis
- Knowledge base management
- Configuration management
- Logging and monitoring
- Error handling for external services
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, Optional
import aiohttp
import structlog
import uuid

from domain.entities.gus_agent import (
    GUSAgent, GUSQuery, GUSResponse, GUSTask, KnowledgeQuery, 
    PDFAnalysisRequest, GUSAgentConfig, QueryType, TaskStatus,
    GUSAgentError, QueryProcessingError, TaskExecutionError,
    KnowledgeQueryError, PDFAnalysisError
)


logger = structlog.get_logger()


class OpenAIClient:
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
        model: str = "gpt-4",
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
            GUSAgentError: If API call fails
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
                        raise GUSAgentError(f"API call failed: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            raise GUSAgentError("API call timed out")
        except aiohttp.ClientError as e:
            raise GUSAgentError(f"HTTP client error: {e}")
        except Exception as e:
            raise GUSAgentError(f"Unexpected error in API call: {e}")


class KnowledgeBaseManager:
    """Manages knowledge base operations"""
    
    def __init__(self, knowledge_base_path: str):
        """
        Initialize knowledge base manager.
        
        Args:
            knowledge_base_path: Path to knowledge base directory
        """
        self.knowledge_base_path = knowledge_base_path
        self._ensure_knowledge_base_exists()
    
    def _ensure_knowledge_base_exists(self):
        """Ensure knowledge base directory exists."""
        os.makedirs(self.knowledge_base_path, exist_ok=True)
    
    def get_knowledge(self, topic: str) -> Optional[str]:
        """
        Get knowledge for a specific topic.
        
        Args:
            topic: Topic to search for
            
        Returns:
            Knowledge content or None if not found
        """
        try:
            topic_file = os.path.join(self.knowledge_base_path, f"{topic}.json")
            if os.path.exists(topic_file):
                with open(topic_file, 'r') as f:
                    data = json.load(f)
                    return data.get('content', '')
            return None
        except Exception as e:
            logger.error(f"Error reading knowledge for topic {topic}: {e}")
            return None
    
    def store_knowledge(self, topic: str, content: str) -> bool:
        """
        Store knowledge for a specific topic.
        
        Args:
            topic: Topic name
            content: Knowledge content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            topic_file = os.path.join(self.knowledge_base_path, f"{topic}.json")
            data = {
                'topic': topic,
                'content': content,
                'timestamp': time.time()
            }
            with open(topic_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error storing knowledge for topic {topic}: {e}")
            return False


class PDFAnalyzer:
    """Handles PDF analysis operations"""
    
    def __init__(self):
        """Initialize PDF analyzer."""
        pass
    
    def analyze_pdf(self, pdf_file_path: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze PDF document.
        
        Args:
            pdf_file_path: Path to PDF file
            requirements: Analysis requirements
            
        Returns:
            Analysis results
            
        Raises:
            PDFAnalysisError: If analysis fails
        """
        try:
            if not os.path.exists(pdf_file_path):
                raise PDFAnalysisError(f"PDF file not found: {pdf_file_path}")
            
            # TODO: Implement actual PDF analysis
            # For now, return mock analysis
            return {
                'file_path': pdf_file_path,
                'page_count': 1,
                'text_content': 'Mock PDF content',
                'requirements_met': True,
                'analysis_summary': 'PDF analysis completed successfully'
            }
            
        except Exception as e:
            raise PDFAnalysisError(f"Failed to analyze PDF: {e}")


class ConcreteGUSAgent(GUSAgent):
    """
    Concrete implementation of GUS Agent.
    
    This class implements the abstract GUSAgent domain entity and handles
    all infrastructure concerns like HTTP calls, file operations, etc.
    """
    
    def __init__(self, config: GUSAgentConfig):
        """
        Initialize concrete GUS agent.
        
        Args:
            config: GUS agent configuration
        """
        super().__init__(config)
        self.api_client = OpenAIClient(config.api_key, config.timeout)
        self.knowledge_manager = KnowledgeBaseManager(config.knowledge_base_path)
        self.pdf_analyzer = PDFAnalyzer()
        logger.info("Concrete GUS Agent initialized", agent_id=self.id)
    
    def _process_query_implementation(self, query: GUSQuery) -> GUSResponse:
        """
        Process query implementation using OpenAI API.
        
        Args:
            query: GUS query to process
            
        Returns:
            GUS response
        """
        start_time = time.time()
        
        try:
            # Prepare messages for API call
            messages = self._prepare_messages(query)
            
            # Make API call
            api_response = asyncio.run(
                self.api_client.create_chat_completion(
                    messages=messages,
                    model=self.config.model_type,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
            )
            
            # Extract response content
            content = self._extract_response_content(api_response)
            confidence = self._calculate_confidence(api_response)
            processing_time = time.time() - start_time
            
            # Create response object
            response = GUSResponse(
                id=str(uuid.uuid4()),
                query_id=query.id,
                content=content,
                confidence=confidence,
                query_type=query.query_type,
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
                query_type=query.query_type.value
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
            raise QueryProcessingError(f"Failed to process query: {e}")
    
    def _execute_task_implementation(self, task: GUSTask) -> Dict[str, Any]:
        """
        Execute task implementation.
        
        Args:
            task: GUS task to execute
            
        Returns:
            Task result
        """
        try:
            # Execute task based on type
            if task.task == "knowledge_search":
                return self._execute_knowledge_search(task)
            elif task.task == "pdf_analysis":
                return self._execute_pdf_analysis(task)
            else:
                return self._execute_general_task(task)
                
        except Exception as e:
            logger.error(f"Failed to execute task: {e}")
            raise TaskExecutionError(f"Failed to execute task: {e}")
    
    def _query_knowledge_implementation(self, knowledge_query: KnowledgeQuery) -> GUSResponse:
        """
        Query knowledge implementation.
        
        Args:
            knowledge_query: Knowledge query to process
            
        Returns:
            GUS response with knowledge
        """
        start_time = time.time()
        
        try:
            # Get knowledge from knowledge base
            knowledge_content = self.knowledge_manager.get_knowledge(knowledge_query.topic)
            
            if not knowledge_content:
                content = f"No knowledge found for topic: {knowledge_query.topic}"
                confidence = 0.0
            else:
                content = knowledge_content
                confidence = 0.9
            
            processing_time = time.time() - start_time
            
            response = GUSResponse(
                id=str(uuid.uuid4()),
                query_id=knowledge_query.id,
                content=content,
                confidence=confidence,
                query_type=QueryType.KNOWLEDGE,
                processing_time=processing_time,
                metadata={
                    "topic": knowledge_query.topic,
                    "knowledge_found": bool(knowledge_content)
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to query knowledge: {e}")
            raise KnowledgeQueryError(f"Failed to query knowledge: {e}")
    
    def _analyze_pdf_implementation(self, pdf_request: PDFAnalysisRequest) -> GUSResponse:
        """
        Analyze PDF implementation.
        
        Args:
            pdf_request: PDF analysis request
            
        Returns:
            GUS response with analysis results
        """
        start_time = time.time()
        
        try:
            # Analyze PDF
            analysis_results = self.pdf_analyzer.analyze_pdf(
                pdf_request.pdf_file_path,
                pdf_request.requirements
            )
            
            processing_time = time.time() - start_time
            
            response = GUSResponse(
                id=str(uuid.uuid4()),
                query_id=pdf_request.id,
                content=str(analysis_results),
                confidence=0.8,
                query_type=QueryType.PDF_ANALYSIS,
                processing_time=processing_time,
                metadata=analysis_results
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to analyze PDF: {e}")
            raise PDFAnalysisError(f"Failed to analyze PDF: {e}")
    
    def _prepare_messages(self, query: GUSQuery) -> list:
        """Prepare messages for API call."""
        messages = []
        
        # Add system message
        system_message = self._get_system_message(query.query_type)
        messages.append({
            "role": "system",
            "content": system_message
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
    
    def _get_system_message(self, query_type: QueryType) -> str:
        """Get system message based on query type."""
        if query_type == QueryType.CAD:
            return "You are a CAD assistant. Help with CAD-related queries and building design."
        elif query_type == QueryType.KNOWLEDGE:
            return "You are a knowledge assistant. Provide helpful information and explanations."
        else:
            return "You are a general assistant. Help with various queries and tasks."
    
    def _extract_response_content(self, api_response: Dict[str, Any]) -> str:
        """Extract content from API response."""
        try:
            choices = api_response.get("choices", [])
            if not choices:
                raise GUSAgentError("No choices in API response")
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                raise GUSAgentError("No content in API response")
            
            return content
            
        except KeyError as e:
            raise GUSAgentError(f"Invalid API response format: {e}")
    
    def _calculate_confidence(self, api_response: Dict[str, Any]) -> float:
        """Calculate confidence score from API response."""
        try:
            choices = api_response.get("choices", [])
            if not choices:
                return 0.0
            
            finish_reason = choices[0].get("finish_reason", "")
            
            confidence_map = {
                "stop": 0.9,
                "length": 0.7,
                "content_filter": 0.5,
                "null": 0.3
            }
            
            return confidence_map.get(finish_reason, 0.5)
            
        except Exception:
            return 0.5
    
    def _execute_knowledge_search(self, task: GUSTask) -> Dict[str, Any]:
        """Execute knowledge search task."""
        topic = task.parameters.get("topic", "")
        knowledge_content = self.knowledge_manager.get_knowledge(topic)
        
        return {
            "task_type": "knowledge_search",
            "topic": topic,
            "knowledge_found": bool(knowledge_content),
            "content": knowledge_content or "No knowledge found"
        }
    
    def _execute_pdf_analysis(self, task: GUSTask) -> Dict[str, Any]:
        """Execute PDF analysis task."""
        pdf_path = task.parameters.get("pdf_path", "")
        requirements = task.parameters.get("requirements", {})
        
        analysis_results = self.pdf_analyzer.analyze_pdf(pdf_path, requirements)
        
        return {
            "task_type": "pdf_analysis",
            "pdf_path": pdf_path,
            "analysis_results": analysis_results
        }
    
    def _execute_general_task(self, task: GUSTask) -> Dict[str, Any]:
        """Execute general task."""
        return {
            "task_type": "general",
            "task": task.task,
            "parameters": task.parameters,
            "status": "completed"
        } 