"""
GUS Agent Main Class

The main GUS (General User Support) agent that orchestrates
all components including NLP, knowledge management, decision engine,
and learning system.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .nlp import NLPProcessor
from .knowledge import KnowledgeManager
from .decision import DecisionEngine
from .learning import LearningSystem


@dataclass
class GUSResponse:
    """Response from GUS agent"""

    message: str
    confidence: float
    intent: str
    entities: Dict[str, Any]
    actions: List[Dict[str, Any]]
    context: Dict[str, Any]
    timestamp: datetime


class GUSAgent:
    """
    GUS (General User Support) Agent

    The primary AI agent for the Arxos platform, providing intelligent
    assistance, natural language processing, and automated support for
    all Arxos operations.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize GUS agent with configuration

        Args:
            config: Configuration dictionary containing model settings,
                   knowledge base paths, and integration endpoints
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize core components
        self.nlp = NLPProcessor(config.get("nlp", {}))
        self.knowledge = KnowledgeManager(config.get("knowledge", {}))
        self.decision = DecisionEngine(config.get("decision", {}))
        self.learning = LearningSystem(config.get("learning", {}))

        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        self.logger.info("GUS Agent initialized successfully")

    async def process_query(
        self, query: str, user_id: str, context: Optional[Dict[str, Any]] = None
    ) -> GUSResponse:
        """
        Process a user query and generate a response

        Args:
            query: User's natural language query
            user_id: Unique identifier for the user
            context: Additional context information

        Returns:
            GUSResponse: Structured response with message, confidence, etc.
        """
        try:
            # Get or create user session
            session = self._get_user_session(user_id)

            # Process natural language
            nlp_result = await self.nlp.process(query, session)

            # Query knowledge base
            knowledge_result = await self.knowledge.query(
                nlp_result.intent.value, nlp_result.entities, context
            )

            # Make decision on response
            decision_result = await self.decision.decide(
                nlp_result, knowledge_result, session
            )

            # Generate response
            response = await self._generate_response(
                nlp_result, knowledge_result, decision_result, session
            )

            # Record learning event
            await self.learning.record_learning_event(
                user_query=query,
                predicted_intent=nlp_result.intent.value,
                confidence=nlp_result.confidence,
                success=response.confidence > 0.5
            )

            # Update session
            self._update_session(user_id, session, response)

            return response

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return GUSResponse(
                message="I apologize, but I encountered an error processing your request. Please try again.",
                confidence=0.0,
                intent="error",
                entities={},
                actions=[],
                context={},
                timestamp=datetime.now(),
            )

    async def execute_task(
        self, task: str, parameters: Dict[str, Any], user_id: str
    ) -> GUSResponse:
        """
        Execute a specific task with parameters

        Args:
            task: Task identifier
            parameters: Task parameters
            user_id: User identifier

        Returns:
            GUSResponse: Result of task execution
        """
        try:
            # Execute task based on decision engine actions
            actions = []
            message = f"Executing task: {task}"
            
            if task == "create_drawing":
                actions.append({
                    "type": "create_drawing",
                    "parameters": parameters
                })
                message = "Creating new drawing with specified parameters"
                
            elif task == "export_drawing":
                actions.append({
                    "type": "export_drawing", 
                    "parameters": parameters
                })
                message = "Exporting drawing in specified format"
                
            elif task == "contribute_bilt":
                actions.append({
                    "type": "contribute_bilt",
                    "parameters": parameters
                })
                message = "Processing BILT contribution"
                
            else:
                return GUSResponse(
                    message=f"Unknown task: {task}",
                    confidence=0.0,
                    intent="error",
                    entities={},
                    actions=[],
                    context={},
                    timestamp=datetime.now(),
                )

            # Generate response
            response = GUSResponse(
                message=message,
                confidence=1.0,
                intent="task_execution",
                entities=parameters,
                actions=actions,
                context={"task": task},
                timestamp=datetime.now(),
            )

            return response

        except Exception as e:
            self.logger.error(f"Error executing task {task}: {e}")
            return GUSResponse(
                message=f"Error executing task {task}: {str(e)}",
                confidence=0.0,
                intent="error",
                entities=parameters,
                actions=[],
                context={"task": task},
                timestamp=datetime.now(),
            )

    async def get_knowledge(
        self, topic: str, context: Optional[Dict[str, Any]] = None
    ) -> GUSResponse:
        """
        Query knowledge base for specific topic

        Args:
            topic: Knowledge topic to query
            context: Additional context

        Returns:
            GUSResponse: Knowledge base response
        """
        try:
            # Query knowledge base
            knowledge_result = await self.knowledge.query(topic, [], context)
            
            if knowledge_result.items:
                # Create summary from knowledge items
                summary = f"Found {len(knowledge_result.items)} items about {topic}: "
                summary += "; ".join([item.title for item in knowledge_result.items[:3]])
                
                return GUSResponse(
                    message=summary,
                    confidence=knowledge_result.confidence,
                    intent="knowledge_query",
                    entities={"topic": topic},
                    actions=[],
                    context=context or {},
                    timestamp=datetime.now(),
                )
            else:
                return GUSResponse(
                    message=f"No knowledge found for topic: {topic}",
                    confidence=0.0,
                    intent="knowledge_query",
                    entities={"topic": topic},
                    actions=[],
                    context=context or {},
                    timestamp=datetime.now(),
                )

        except Exception as e:
            self.logger.error(f"Error querying knowledge for {topic}: {e}")
            return GUSResponse(
                message=f"Unable to retrieve knowledge for {topic}",
                confidence=0.0,
                intent="error",
                entities={"topic": topic},
                actions=[],
                context=context or {},
                timestamp=datetime.now(),
            )

    def _get_user_session(self, user_id: str) -> Dict[str, Any]:
        """Get or create user session"""
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = {
                "created": datetime.now(),
                "conversation_history": [],
                "context": {},
                "preferences": {},
            }
        return self.active_sessions[user_id]

    def _update_session(
        self, user_id: str, session: Dict[str, Any], response: GUSResponse
    ):
        """Update user session with new response"""
        session["conversation_history"].append(
            {"timestamp": response.timestamp, "response": response}
        )

        # Keep only last 10 interactions
        if len(session["conversation_history"]) > 10:
            session["conversation_history"] = session["conversation_history"][-10:]

    async def _generate_response(
        self, nlp_result, knowledge_result, decision_result, session: Dict[str, Any]
    ) -> GUSResponse:
        """Generate final response from all components"""

        # Generate response message from NLP
        message = await self.nlp.generate_response(
            nlp_result.intent, nlp_result.entities, session
        )
        
        # Add knowledge information if available
        if knowledge_result and knowledge_result.items:
            knowledge_summary = f"Found {len(knowledge_result.items)} relevant items: "
            knowledge_summary += "; ".join([item.title for item in knowledge_result.items[:2]])
            message += f"\n\n{knowledge_summary}"

        # Calculate confidence
        confidence = min(
            nlp_result.confidence * knowledge_result.confidence * decision_result.confidence, 1.0
        )

        return GUSResponse(
            message=message,
            confidence=confidence,
            intent=nlp_result.intent.value,
            entities={e.type: e.value for e in nlp_result.entities},
            actions=decision_result.actions,
            context=session.get("context", {}),
            timestamp=datetime.now(),
        )

    async def shutdown(self):
        """Gracefully shutdown GUS agent"""
        self.logger.info("Shutting down GUS agent...")

        # Shutdown components
        await self.nlp.shutdown()
        await self.knowledge.shutdown()
        await self.decision.shutdown()
        await self.learning.shutdown()

        # Clear sessions
        self.active_sessions.clear()

        self.logger.info("GUS agent shutdown complete")
