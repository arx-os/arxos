"""
Conversation Manager Application Service

This module manages conversations with the Gus AI agent, handling state,
context, and orchestrating interactions between domain services.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import structlog

from domain.entities.conversation import (
    Conversation, ConversationContext, Message, MessageRole, ConversationStatus
)
from domain.services.llm_service import LLMService, LLMMessage, LLMFunction
from domain.services.query_translator import QueryTranslator, AQLQuery
from domain.services.mcp_knowledge_service import MCPKnowledgeService
from infrastructure.repositories.conversation_repository import ConversationRepository
from application.services.mcp_integration import GusMCPIntegration

logger = structlog.get_logger()


class ConversationManager:
    """
    Application service for managing AI conversations.
    
    This service orchestrates the conversation flow, maintains state,
    and coordinates between different domain services including MCP
    building code knowledge.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        query_translator: QueryTranslator,
        conversation_repo: ConversationRepository,
        knowledge_service: Optional[Any] = None,
        mcp_integration: Optional[GusMCPIntegration] = None
    ):
        """
        Initialize conversation manager.
        
        Args:
            llm_service: LLM service for AI interactions
            query_translator: Service for translating queries to AQL
            conversation_repo: Repository for persisting conversations
            knowledge_service: Optional knowledge/RAG service
            mcp_integration: Optional MCP building code integration
        """
        self.llm_service = llm_service
        self.query_translator = query_translator
        self.conversation_repo = conversation_repo
        self.knowledge_service = knowledge_service
        self.mcp_integration = mcp_integration
        
        # Cache for active conversations
        self._conversation_cache: Dict[str, Conversation] = {}
        
        # Configuration
        self.max_conversation_age = timedelta(hours=24)
        self.max_cache_size = 100
        
        logger.info("Initialized ConversationManager")
    
    async def start_conversation(
        self,
        user_id: str,
        initial_context: Optional[ConversationContext] = None
    ) -> Conversation:
        """
        Start a new conversation.
        
        Args:
            user_id: User identifier
            initial_context: Optional initial context
            
        Returns:
            New conversation instance
        """
        conversation = Conversation.create(user_id)
        
        if initial_context:
            conversation.context = initial_context
        
        # Add system message with context
        system_prompt = self._build_system_prompt(conversation.context)
        conversation.add_message(MessageRole.SYSTEM, system_prompt)
        
        # Save to repository
        await self.conversation_repo.save(conversation)
        
        # Cache the conversation
        self._cache_conversation(conversation)
        
        logger.info(f"Started new conversation: {conversation.id}")
        return conversation
    
    async def process_message(
        self,
        conversation_id: str,
        user_message: str,
        context_updates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message in a conversation.
        
        Args:
            conversation_id: Conversation identifier
            user_message: User's message
            context_updates: Optional context updates
            
        Returns:
            Response dictionary with AI response and metadata
        """
        # Get or load conversation
        conversation = await self._get_conversation(conversation_id)
        
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        if conversation.status != ConversationStatus.ACTIVE:
            raise ValueError(f"Conversation is not active: {conversation.status.value}")
        
        # Update context if provided
        if context_updates:
            conversation.update_context(**context_updates)
        
        # Add user message
        conversation.add_message(MessageRole.USER, user_message)
        
        try:
            # Process the message
            response = await self._process_user_query(conversation, user_message)
            
            # Add assistant response
            assistant_message = conversation.add_message(
                MessageRole.ASSISTANT,
                response['content'],
                metadata=response.get('metadata', {})
            )
            
            # Save conversation
            await self.conversation_repo.save(conversation)
            
            return {
                'conversation_id': conversation.id,
                'message_id': assistant_message.id,
                'content': response['content'],
                'query_translation': response.get('query_translation'),
                'actions': response.get('actions', []),
                'suggestions': response.get('suggestions', []),
                'confidence': response.get('confidence', 0.0),
                'metadata': response.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            conversation.mark_error(str(e))
            await self.conversation_repo.save(conversation)
            raise
    
    async def _process_user_query(
        self,
        conversation: Conversation,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Process user query and generate response.
        
        Args:
            conversation: Conversation instance
            user_message: User's message
            
        Returns:
            Response dictionary
        """
        # Try to translate to AQL if it looks like a query
        aql_query = None
        if self._is_query_request(user_message):
            try:
                aql_query = self.query_translator.translate(user_message)
                logger.info(f"Translated to AQL: {aql_query.query_string}")
            except Exception as e:
                logger.warning(f"Could not translate to AQL: {e}")
        
        # Check if this is a building code question
        mcp_response = None
        if self.mcp_integration and self._is_code_question(user_message):
            try:
                mcp_response = await self.mcp_integration.answer_code_question(
                    question=user_message,
                    context={
                        'system_type': conversation.context.system_type,
                        'building_id': conversation.context.building_id,
                        'jurisdiction': self._get_jurisdiction_from_context(conversation.context)
                    }
                )
                logger.info(f"MCP response confidence: {mcp_response.get('confidence', 0)}")
            except Exception as e:
                logger.warning(f"MCP integration error: {e}")
        
        # Get relevant knowledge if available
        knowledge_context = ""
        if self.knowledge_service and aql_query:
            try:
                knowledge = await self.knowledge_service.get_relevant_knowledge(
                    user_message,
                    entities=aql_query.entities
                )
                if knowledge:
                    knowledge_context = f"\n\nRelevant knowledge:\n{knowledge}"
            except Exception as e:
                logger.warning(f"Could not retrieve knowledge: {e}")
        
        # Add MCP knowledge if available
        if mcp_response and mcp_response.get('confidence', 0) > 0.5:
            knowledge_context += f"\n\nBuilding Code Information:\n{mcp_response['answer']}"
            if mcp_response.get('references'):
                knowledge_context += "\n\nCode References:"
                for ref in mcp_response['references'][:3]:
                    knowledge_context += f"\n- {ref['code']}: {ref['name']}"
        
        # Build LLM messages
        messages = conversation.get_messages_for_llm(max_tokens=3000)
        
        # Add knowledge context if available
        if knowledge_context:
            messages.append(LLMMessage(
                role="system",
                content=f"Use this knowledge to answer: {knowledge_context}"
            ))
        
        # Define available functions for the LLM
        functions = self._get_available_functions(conversation.context)
        
        # Get LLM response
        llm_response = await self.llm_service.complete(
            messages=[LLMMessage(role=m['role'], content=m['content']) for m in messages],
            functions=functions,
            temperature=0.7
        )
        
        # Process function calls if any
        actions = []
        if llm_response.function_call:
            action_result = await self._execute_function_call(
                llm_response.function_call,
                conversation
            )
            actions.append(action_result)
        
        # Generate suggestions for follow-up
        suggestions = self._generate_suggestions(user_message, aql_query)
        
        return {
            'content': llm_response.content,
            'query_translation': aql_query.to_dict() if aql_query else None,
            'actions': actions,
            'suggestions': suggestions,
            'confidence': aql_query.confidence if aql_query else 0.5,
            'metadata': {
                'model': llm_response.model,
                'tokens_used': llm_response.total_tokens,
                'has_function_call': bool(llm_response.function_call)
            }
        }
    
    def _build_system_prompt(self, context: ConversationContext) -> str:
        """Build system prompt based on context"""
        prompt = """You are Gus, an AI assistant for the Arxos building management platform.
You help users query and manage building data, perform analyses, and provide recommendations.

Key capabilities:
- Translate natural language to building queries
- Analyze building systems (electrical, HVAC, plumbing, structural)
- Check code compliance
- Provide optimization recommendations
- Troubleshoot issues

Guidelines:
- Be concise and professional
- Provide specific, actionable information
- Reference relevant codes and standards when applicable
- Suggest follow-up actions when appropriate"""
        
        # Add context-specific information
        if context.building_id:
            prompt += f"\n\nCurrent building: {context.building_id}"
        if context.system_type:
            prompt += f"\nFocus system: {context.system_type}"
        if context.user_role:
            prompt += f"\nUser role: {context.user_role}"
        
        return prompt
    
    def _get_available_functions(self, context: ConversationContext) -> List[LLMFunction]:
        """Get available functions based on context"""
        functions = [
            LLMFunction(
                name="execute_query",
                description="Execute a building data query",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "AQL query string"},
                        "explanation": {"type": "string", "description": "Explanation of what the query does"}
                    },
                    "required": ["query"]
                }
            ),
            LLMFunction(
                name="analyze_system",
                description="Analyze a building system",
                parameters={
                    "type": "object",
                    "properties": {
                        "system": {"type": "string", "enum": ["electrical", "hvac", "plumbing", "structural"]},
                        "analysis_type": {"type": "string", "enum": ["compliance", "efficiency", "safety", "optimization"]},
                        "scope": {"type": "string", "description": "Scope of analysis (e.g., floor:3, room:301)"}
                    },
                    "required": ["system", "analysis_type"]
                }
            ),
            LLMFunction(
                name="create_report",
                description="Generate a report",
                parameters={
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "enum": ["compliance", "maintenance", "energy", "safety"]},
                        "scope": {"type": "string", "description": "Scope of report"},
                        "format": {"type": "string", "enum": ["summary", "detailed", "executive"]}
                    },
                    "required": ["report_type"]
                }
            )
        ]
        
        # Add context-specific functions
        if context.user_role in ["engineer", "admin"]:
            functions.append(LLMFunction(
                name="modify_system",
                description="Modify system parameters",
                parameters={
                    "type": "object",
                    "properties": {
                        "object_id": {"type": "string", "description": "ID of object to modify"},
                        "property": {"type": "string", "description": "Property to modify"},
                        "value": {"type": "string", "description": "New value"}
                    },
                    "required": ["object_id", "property", "value"]
                }
            ))
        
        return functions
    
    async def _execute_function_call(
        self,
        function_call: Dict[str, Any],
        conversation: Conversation
    ) -> Dict[str, Any]:
        """Execute a function call from the LLM"""
        function_name = function_call.get('name')
        arguments = json.loads(function_call.get('arguments', '{}'))
        
        logger.info(f"Executing function: {function_name} with args: {arguments}")
        
        # Route to appropriate handler
        if function_name == "execute_query":
            return {
                'action': 'query',
                'query': arguments.get('query'),
                'status': 'pending',
                'explanation': arguments.get('explanation')
            }
        elif function_name == "analyze_system":
            return {
                'action': 'analyze',
                'system': arguments.get('system'),
                'analysis_type': arguments.get('analysis_type'),
                'scope': arguments.get('scope'),
                'status': 'pending'
            }
        elif function_name == "create_report":
            return {
                'action': 'report',
                'report_type': arguments.get('report_type'),
                'scope': arguments.get('scope'),
                'format': arguments.get('format', 'summary'),
                'status': 'pending'
            }
        elif function_name == "modify_system":
            return {
                'action': 'modify',
                'object_id': arguments.get('object_id'),
                'property': arguments.get('property'),
                'value': arguments.get('value'),
                'status': 'requires_confirmation'
            }
        else:
            return {
                'action': 'unknown',
                'function': function_name,
                'status': 'error'
            }
    
    def _is_query_request(self, message: str) -> bool:
        """Check if message is likely a query request"""
        query_indicators = [
            'find', 'show', 'list', 'get', 'search',
            'how many', 'count', 'where', 'what',
            'analyze', 'check', 'verify', 'calculate'
        ]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in query_indicators)
    
    def _generate_suggestions(self, user_message: str, aql_query: Optional[AQLQuery]) -> List[str]:
        """Generate follow-up suggestions"""
        suggestions = []
        
        if aql_query:
            if aql_query.entities:
                entity = aql_query.entities[0]
                suggestions.append(f"Show details for specific {entity}")
                suggestions.append(f"Analyze {entity} for compliance")
                suggestions.append(f"Generate report for {entity}")
            
            if 'floor' in user_message.lower():
                suggestions.append("Compare with other floors")
                suggestions.append("Show floor plan visualization")
            
            if 'overloaded' in user_message.lower() or 'capacity' in user_message.lower():
                suggestions.append("Show load distribution")
                suggestions.append("Suggest load balancing")
                suggestions.append("Create maintenance ticket")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    async def _get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation from cache or repository"""
        # Check cache first
        if conversation_id in self._conversation_cache:
            return self._conversation_cache[conversation_id]
        
        # Load from repository
        conversation = await self.conversation_repo.get(conversation_id)
        if conversation:
            self._cache_conversation(conversation)
        
        return conversation
    
    def _cache_conversation(self, conversation: Conversation) -> None:
        """Cache conversation with size limit"""
        # Implement simple LRU by removing oldest if at capacity
        if len(self._conversation_cache) >= self.max_cache_size:
            oldest_id = min(
                self._conversation_cache.keys(),
                key=lambda k: self._conversation_cache[k].updated_at
            )
            del self._conversation_cache[oldest_id]
        
        self._conversation_cache[conversation.id] = conversation
    
    async def end_conversation(self, conversation_id: str) -> None:
        """End a conversation"""
        conversation = await self._get_conversation(conversation_id)
        if conversation:
            conversation.complete()
            await self.conversation_repo.save(conversation)
            
            # Remove from cache
            if conversation_id in self._conversation_cache:
                del self._conversation_cache[conversation_id]
            
            logger.info(f"Ended conversation: {conversation_id}")
    
    def _is_code_question(self, message: str) -> bool:
        """Check if message is likely a building code question"""
        code_indicators = [
            'code', 'compliance', 'regulation', 'standard', 'requirement',
            'nec', 'ibc', 'ipc', 'imc', 'ada', 'nfpa', 'ashrae',
            'violation', 'permit', 'inspection', 'approved', 'compliant',
            'gfci', 'arc fault', 'fire rating', 'egress', 'occupancy'
        ]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in code_indicators)
    
    def _get_jurisdiction_from_context(self, context: ConversationContext) -> Dict[str, str]:
        """Extract jurisdiction from conversation context"""
        # Default to Florida if not specified
        default_jurisdiction = {'country': 'US', 'state': 'FL'}
        
        if hasattr(context, 'preferences') and context.preferences:
            jurisdiction = context.preferences.get('jurisdiction', default_jurisdiction)
        else:
            jurisdiction = default_jurisdiction
        
        return jurisdiction