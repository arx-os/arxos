"""
Arx AI Agent

Core AI agent providing GPT-based logic, geometry validation,
voice input processing, and AI agent task execution.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import openai
import anthropic
from pydantic import BaseModel
import structlog

from .geometry_validator import GeometryValidator
from .voice_processor import VoiceProcessor
from .nlp_engine import NLPEngine


logger = structlog.get_logger()


class AIResponse(BaseModel):
    """Response model for AI operations"""
    success: bool
    message: str
    data: Dict[str, Any] = {}
    timestamp: datetime
    session_id: Optional[str] = None
    model_used: Optional[str] = None


class AIAgent:
    """Arx AI Agent for handling AI/ML operations"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the AI agent"""
        self.config = config
        self.logger = structlog.get_logger(__name__)

        # Initialize components
        self.geometry_validator = GeometryValidator(config)
        self.voice_processor = VoiceProcessor(config)
        self.nlp_engine = NLPEngine(config)

        # Initialize AI clients
        self._init_ai_clients()

        self.logger.info("AI Agent initialized successfully")

    def _init_ai_clients(self):
        """Initialize AI service clients"""
        try:
            # OpenAI client
            if "openai_api_key" in self.config:
                openai.api_key = self.config["openai_api_key"]
                self.openai_client = openai.OpenAI()
            else:
                self.openai_client = None
                self.logger.warning("OpenAI API key not configured")

            # Anthropic client
            if "anthropic_api_key" in self.config:
                self.anthropic_client = anthropic.Anthropic(
                    api_key=self.config["anthropic_api_key"]
                )
            else:
                self.anthropic_client = None
                self.logger.warning("Anthropic API key not configured")

        except Exception as e:
            self.logger.error(f"Failed to initialize AI clients: {e}")
            raise

    async def process_query(
        self,
        query: str,
        user_id: str,
        context: Dict[str, Any] = {},
        session_id: Optional[str] = None,
        model: str = "gpt-4"
    ) -> AIResponse:
        """Process AI queries using GPT-based logic"""
        try:
            self.logger.info(f"Processing AI query for user {user_id}",
                           query=query, model=model)

            # Process with NLP engine first
            nlp_result = await self.nlp_engine.process_query(query, context)

            # Generate AI response
            if model.startswith("gpt") and self.openai_client:
                response = await self._generate_openai_response(
                    query, context, nlp_result, model
                )
            elif model.startswith("claude") and self.anthropic_client:
                response = await self._generate_anthropic_response(
                    query, context, nlp_result, model
                )
            else:
                # Fallback to basic NLP processing
                response = nlp_result

            return AIResponse(
                success=True,
                message="Query processed successfully",
                data={
                    "response": response,
                    "nlp_analysis": nlp_result,
                    "model_used": model
                },
                timestamp=datetime.utcnow(),
                session_id=session_id,
                model_used=model
            )

        except Exception as e:
            self.logger.error(f"Error processing AI query: {e}")
            return AIResponse(
                success=False,
                message=f"Error processing query: {str(e)}",
                timestamp=datetime.utcnow(),
                session_id=session_id
            )

    async def validate_geometry(
        self,
        geometry_data: Dict[str, Any],
        validation_type: str = "comprehensive",
        user_id: str = ""
    ) -> AIResponse:
        """Validate geometry using AI-powered analysis"""
        try:
            self.logger.info(f"Validating geometry for user {user_id}",
                           validation_type=validation_type)

            validation_result = await self.geometry_validator.validate(
                geometry_data, validation_type
            )

            return AIResponse(
                success=True,
                message="Geometry validation completed",
                data=validation_result,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Error validating geometry: {e}")
            return AIResponse(
                success=False,
                message=f"Error validating geometry: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def process_voice_input(
        self,
        audio_data: str,
        user_id: str,
        language: str = "en"
    ) -> AIResponse:
        """Process voice input and convert to text"""
        try:
            self.logger.info(f"Processing voice input for user {user_id}",
                           language=language)

            # Convert base64 audio to text
            text_result = await self.voice_processor.process_audio(
                audio_data, language
            )

            # Process the transcribed text
            nlp_result = await self.nlp_engine.process_query(
                text_result["text"], {}
            )

            return AIResponse(
                success=True,
                message="Voice input processed successfully",
                data={
                    "transcription": text_result,
                    "nlp_analysis": nlp_result
                },
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Error processing voice input: {e}")
            return AIResponse(
                success=False,
                message=f"Error processing voice input: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def execute_task(
        self,
        task: str,
        parameters: Dict[str, Any],
        user_id: str,
        agent_type: str = "general"
    ) -> AIResponse:
        """Execute AI agent tasks"""
        try:
            self.logger.info(f"Executing agent task for user {user_id}",
                           task=task, agent_type=agent_type)

            # Route to appropriate agent type
            if agent_type == "geometry":
                result = await self._execute_geometry_task(task, parameters)
            elif agent_type == "voice":
                result = await self._execute_voice_task(task, parameters)
            elif agent_type == "nlp":
                result = await self._execute_nlp_task(task, parameters)
            else:
                result = await self._execute_general_task(task, parameters)

            return AIResponse(
                success=True,
                message="Task executed successfully",
                data=result,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Error executing agent task: {e}")
            return AIResponse(
                success=False,
                message=f"Error executing task: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def _generate_openai_response(
        self,
        query: str,
        context: Dict[str, Any],
        nlp_result: Dict[str, Any],
        model: str
    ) -> str:
        """Generate response using OpenAI"""
        prompt = f"""
        Context: {context}
        NLP Analysis: {nlp_result}

        User Query: {query}

        Please provide a helpful and accurate response based on the context and NLP analysis.
        """

        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )

        return response.choices[0].message.content

    async def _generate_anthropic_response(
        self,
        query: str,
        context: Dict[str, Any],
        nlp_result: Dict[str, Any],
        model: str
    ) -> str:
        """Generate response using Anthropic"""
        prompt = f"""
        Context: {context}
        NLP Analysis: {nlp_result}

        User Query: {query}

        Please provide a helpful and accurate response based on the context and NLP analysis.
        """

        response = await asyncio.to_thread(
            self.anthropic_client.messages.create,
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def _execute_geometry_task(
        self, task: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute geometry-related tasks"""
        return await self.geometry_validator.execute_task(task, parameters)

    async def _execute_voice_task(
        self, task: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute voice-related tasks"""
        return await self.voice_processor.execute_task(task, parameters)

    async def _execute_nlp_task(
        self, task: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute NLP-related tasks"""
        return await self.nlp_engine.execute_task(task, parameters)

    async def _execute_general_task(
        self, task: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute general AI tasks"""
        # Use OpenAI for general tasks
        if self.openai_client:
            prompt = f"Task: {task}\nParameters: {parameters}\nPlease execute this task."

            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )

            return {
                "task": task,
                "result": response.choices[0].message.content,
                "model": "gpt-4"
            }
        else:
            return {
                "task": task,
                "result": "AI service not available",
                "error": "OpenAI client not configured"
            }

    async def shutdown(self):
        """Shutdown the AI agent"""
        self.logger.info("Shutting down AI Agent...")
        # Cleanup resources if needed
        pass
