"""
AI Frontend Integration Service for HTMX-powered AI Interface

This module provides HTMX-powered AI interface capabilities including:
- Real-time AI interactions
- Dynamic content updates
- Intelligent form handling
- Context-aware suggestions
- Adaptive UI components
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from svgx_engine.services.ai.user_pattern_learning import UserPatternLearningService

logger = logging.getLogger(__name__)


class HTMXEventType(str, Enum):
    """Types of HTMX events"""
    CLICK = "click"
    SUBMIT = "submit"
    CHANGE = "change"
    FOCUS = "focus"
    BLUR = "blur"
    MOUSE_ENTER = "mouseenter"
    MOUSE_LEAVE = "mouseleave"
    KEYUP = "keyup"
    KEYDOWN = "keydown"
    SCROLL = "scroll"
    RESIZE = "resize"
    LOAD = "load"
    BEFORE_REQUEST = "beforeRequest"
    AFTER_REQUEST = "afterRequest"
    BEFORE_SWAP = "beforeSwap"
    AFTER_SWAP = "afterSwap"
    BEFORE_SEND = "beforeSend"
    AFTER_SEND = "afterSend"


class AIComponentType(str, Enum):
    """Types of AI-powered components"""
    SMART_FORM = "smart_form"
    INTELLIGENT_SEARCH = "intelligent_search"
    CONTEXT_SUGGESTIONS = "context_suggestions"
    ADAPTIVE_NAVIGATION = "adaptive_navigation"
    PERSONALIZED_DASHBOARD = "personalized_dashboard"
    AI_ASSISTANT = "ai_assistant"
    RECOMMENDATION_WIDGET = "recommendation_widget"
    PREDICTIVE_INPUT = "predictive_input"
    SMART_TABLE = "smart_table"
    INTELLIGENT_CHART = "intelligent_chart"


class HTMXRequest(BaseModel):
    """HTMX request data"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    event_type: HTMXEventType = Field(..., description="Type of HTMX event")
    target_id: str = Field(..., description="Target element ID")
    component_type: AIComponentType = Field(..., description="AI component type")
    request_data: Dict[str, Any] = Field(default_factory=dict, description="Request data")
    context: Dict[str, Any] = Field(default_factory=dict, description="Request context")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class HTMXResponse(BaseModel):
    """HTMX response data"""
    id: UUID = Field(default_factory=uuid4)
    request_id: UUID = Field(..., description="Original request ID")
    html_content: str = Field(..., description="HTML content to inject")
    css_updates: List[str] = Field(default_factory=list, description="CSS updates")
    js_updates: List[str] = Field(default_factory=list, description="JavaScript updates")
    htmx_attributes: Dict[str, str] = Field(default_factory=dict, description="HTMX attributes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIComponent(BaseModel):
    """AI-powered component configuration"""
    id: UUID = Field(default_factory=uuid4)
    component_type: AIComponentType = Field(..., description="Component type")
    name: str = Field(..., description="Component name")
    description: str = Field(..., description="Component description")
    target_selector: str = Field(..., description="CSS selector for target element")
    htmx_config: Dict[str, Any] = Field(default_factory=dict, description="HTMX configuration")
    ai_config: Dict[str, Any] = Field(default_factory=dict, description="AI configuration")
    is_active: bool = Field(default=True, description="Whether component is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SmartFormField(BaseModel):
    """Smart form field configuration"""
    id: UUID = Field(default_factory=uuid4)
    field_name: str = Field(..., description="Field name")
    field_type: str = Field(..., description="Field type")
    label: str = Field(..., description="Field label")
    placeholder: Optional[str] = None
    validation_rules: List[str] = Field(default_factory=list, description="Validation rules")
    ai_suggestions: List[str] = Field(default_factory=list, description="AI-generated suggestions")
    auto_complete: bool = Field(default=True, description="Enable auto-complete")
    smart_validation: bool = Field(default=True, description="Enable smart validation")
    context_aware: bool = Field(default=True, description="Enable context-aware behavior")


class IntelligentSearch(BaseModel):
    """Intelligent search configuration"""
    id: UUID = Field(default_factory=uuid4)
    search_id: str = Field(..., description="Search identifier")
    query: str = Field(..., description="Search query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Search context")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    suggestions: List[str] = Field(default_factory=list, description="Search suggestions")
    processing_time: float = Field(default=0.0, description="Processing time")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIAssistant(BaseModel):
    """AI assistant configuration"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    context: str = Field(..., description="Current context")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    current_task: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list, description="AI suggestions")
    is_active: bool = Field(default=True, description="Whether assistant is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AIFrontendIntegrationService:
    """Service for HTMX-powered AI frontend integration"""
    
    def __init__(self):
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.requests: Dict[UUID, HTMXRequest] = {}
        self.responses: Dict[UUID, HTMXResponse] = {}
        self.components: Dict[UUID, AIComponent] = {}
        self.smart_forms: Dict[str, List[SmartFormField]] = {}
        self.intelligent_searches: Dict[str, IntelligentSearch] = {}
        self.ai_assistants: Dict[str, AIAssistant] = {}
        self.user_pattern_service = UserPatternLearningService()
        
        logger.info("AIFrontendIntegrationService initialized")
    
    async def process_htmx_request(
        self,
        user_id: str,
        session_id: str,
        event_type: HTMXEventType,
        target_id: str,
        component_type: AIComponentType,
        request_data: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> HTMXResponse:
        """Process HTMX request and generate AI-powered response"""
        start_time = datetime.utcnow()
        
        # Create HTMX request
        request = HTMXRequest(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            target_id=target_id,
            component_type=component_type,
            request_data=request_data or {},
            context=context or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.requests[request.id] = request
        
        # Record user action for pattern learning
        await self.user_pattern_service.record_user_action(
            user_id=user_id,
            session_id=session_id,
            action_type="htmx_interaction",
            context="ai_frontend",
            resource_id=target_id,
            metadata={
                "event_type": event_type.value,
                "component_type": component_type.value,
                "request_data": request_data
            }
        )
        
        # Process request based on component type
        response = await self._process_component_request(request)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        response.processing_time = processing_time
        
        self.responses[response.id] = response
        
        logger.info(f"Processed HTMX request: {event_type.value} for {component_type.value}")
        return response
    
    async def _process_component_request(self, request: HTMXRequest) -> HTMXResponse:
        """Process request based on component type"""
        if request.component_type == AIComponentType.SMART_FORM:
            return await self._handle_smart_form(request)
        elif request.component_type == AIComponentType.INTELLIGENT_SEARCH:
            return await self._handle_intelligent_search(request)
        elif request.component_type == AIComponentType.CONTEXT_SUGGESTIONS:
            return await self._handle_context_suggestions(request)
        elif request.component_type == AIComponentType.ADAPTIVE_NAVIGATION:
            return await self._handle_adaptive_navigation(request)
        elif request.component_type == AIComponentType.PERSONALIZED_DASHBOARD:
            return await self._handle_personalized_dashboard(request)
        elif request.component_type == AIComponentType.AI_ASSISTANT:
            return await self._handle_ai_assistant(request)
        elif request.component_type == AIComponentType.RECOMMENDATION_WIDGET:
            return await self._handle_recommendation_widget(request)
        elif request.component_type == AIComponentType.PREDICTIVE_INPUT:
            return await self._handle_predictive_input(request)
        elif request.component_type == AIComponentType.SMART_TABLE:
            return await self._handle_smart_table(request)
        elif request.component_type == AIComponentType.INTELLIGENT_CHART:
            return await self._handle_intelligent_chart(request)
        else:
            return await self._handle_generic_request(request)
    
    async def _handle_smart_form(self, request: HTMXRequest) -> HTMXResponse:
        """Handle smart form interactions"""
        form_data = request.request_data.get("form_data", {})
        field_name = request.request_data.get("field_name")
        
        # Get user patterns for form optimization
        user_patterns = await self.user_pattern_service.get_user_patterns(
            user_id=request.user_id,
            pattern_type="preference"
        )
        
        # Generate smart suggestions based on patterns
        suggestions = []
        for pattern in user_patterns:
            if pattern.pattern_data.get("preference_type") == "form_preference":
                suggestions.append(pattern.pattern_data.get("suggestion", ""))
        
        # Create smart form HTML
        html_content = f"""
        <div class="smart-form-field" data-field="{field_name}">
            <label for="{field_name}">{field_name.title()}</label>
            <input type="text" 
                   id="{field_name}" 
                   name="{field_name}" 
                   value="{form_data.get(field_name, '')}"
                   hx-post="/ai/smart-form/validate"
                   hx-trigger="keyup changed delay:500ms"
                   hx-target="#{field_name}-suggestions"
                   class="smart-input" />
            <div id="{field_name}-suggestions" class="suggestions-container">
                {self._generate_suggestions_html(suggestions)}
            </div>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML",
                "hx-indicator": ".loading"
            },
            metadata={
                "suggestions": suggestions,
                "field_name": field_name
            },
            processing_time=0.0
        )
    
    async def _handle_intelligent_search(self, request: HTMXRequest) -> HTMXResponse:
        """Handle intelligent search interactions"""
        query = request.request_data.get("query", "")
        filters = request.request_data.get("filters", {})
        
        # Get user search patterns
        user_patterns = await self.user_pattern_service.get_user_patterns(
            user_id=request.user_id,
            pattern_type="search_pattern"
        )
        
        # Generate search suggestions based on patterns
        suggestions = []
        for pattern in user_patterns:
            if pattern.pattern_data.get("query_type") == "similar":
                suggestions.append(pattern.pattern_data.get("suggestion", ""))
        
        # Create intelligent search HTML
        html_content = f"""
        <div class="intelligent-search">
            <input type="text" 
                   id="search-input" 
                   placeholder="Search..."
                   value="{query}"
                   hx-post="/ai/search/suggest"
                   hx-trigger="keyup changed delay:300ms"
                   hx-target="#search-suggestions"
                   class="search-input" />
            <div id="search-suggestions" class="suggestions-dropdown">
                {self._generate_search_suggestions_html(suggestions)}
            </div>
            <div id="search-results" class="results-container">
                <!-- Results will be populated here -->
            </div>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML",
                "hx-indicator": ".search-loading"
            },
            metadata={
                "suggestions": suggestions,
                "query": query
            },
            processing_time=0.0
        )
    
    async def _handle_context_suggestions(self, request: HTMXRequest) -> HTMXResponse:
        """Handle context-aware suggestions"""
        context = request.context.get("current_context", "")
        user_id = request.user_id
        
        # Get user recommendations
        recommendations = await self.user_pattern_service.get_user_recommendations(
            user_id=user_id,
            active_only=True
        )
        
        # Filter recommendations by context
        context_recommendations = [
            rec for rec in recommendations
            if context.lower() in rec.description.lower() or context.lower() in rec.title.lower()
        ]
        
        # Create context suggestions HTML
        html_content = f"""
        <div class="context-suggestions">
            <h4>Suggestions for {context}</h4>
            <div class="suggestions-list">
                {self._generate_recommendations_html(context_recommendations)}
            </div>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML"
            },
            metadata={
                "recommendations": [rec.dict() for rec in context_recommendations],
                "context": context
            },
            processing_time=0.0
        )
    
    async def _handle_adaptive_navigation(self, request: HTMXRequest) -> HTMXResponse:
        """Handle adaptive navigation"""
        user_id = request.user_id
        
        # Get user navigation patterns
        user_patterns = await self.user_pattern_service.get_user_patterns(
            user_id=user_id,
            pattern_type="navigation"
        )
        
        # Generate adaptive navigation based on patterns
        navigation_items = []
        for pattern in user_patterns:
            if pattern.pattern_type == "frequency":
                navigation_items.append({
                    "label": pattern.pattern_data.get("page_name", "Unknown"),
                    "url": pattern.pattern_data.get("url", "#"),
                    "frequency": pattern.frequency
                })
        
        # Sort by frequency
        navigation_items.sort(key=lambda x: x["frequency"], reverse=True)
        
        # Create adaptive navigation HTML
        html_content = """
        <nav class="adaptive-navigation">
            <ul class="nav-list">
        """
        
        for item in navigation_items[:5]:  # Top 5 most used
            html_content += f"""
                <li class="nav-item">
                    <a href="{item['url']}" 
                       hx-get="{item['url']}"
                       hx-target="#main-content"
                       hx-push-url="true"
                       class="nav-link">
                        {item['label']}
                        <span class="usage-count">({item['frequency']})</span>
                    </a>
                </li>
            """
        
        html_content += """
            </ul>
        </nav>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML"
            },
            metadata={
                "navigation_items": navigation_items
            },
            processing_time=0.0
        )
    
    async def _handle_personalized_dashboard(self, request: HTMXRequest) -> HTMXResponse:
        """Handle personalized dashboard"""
        user_id = request.user_id
        
        # Get user analytics
        analytics = await self.user_pattern_service.get_user_analytics(user_id)
        
        # Get user recommendations
        recommendations = await self.user_pattern_service.get_user_recommendations(
            user_id=user_id,
            active_only=True
        )
        
        # Create personalized dashboard HTML
        html_content = f"""
        <div class="personalized-dashboard">
            <div class="dashboard-header">
                <h2>Your Personalized Dashboard</h2>
            </div>
            
            <div class="dashboard-stats">
                <div class="stat-card">
                    <h3>Efficiency Score</h3>
                    <div class="stat-value">{analytics.efficiency_score * 100:.1f}%</div>
                </div>
                <div class="stat-card">
                    <h3>Most Used Feature</h3>
                    <div class="stat-value">{analytics.most_used_features[0] if analytics.most_used_features else 'N/A'}</div>
                </div>
                <div class="stat-card">
                    <h3>Active Patterns</h3>
                    <div class="stat-value">{analytics.patterns_identified}</div>
                </div>
            </div>
            
            <div class="dashboard-recommendations">
                <h3>Recommended Actions</h3>
                <div class="recommendations-list">
                    {self._generate_recommendations_html(recommendations[:3])}
                </div>
            </div>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML"
            },
            metadata={
                "analytics": analytics.dict() if analytics else {},
                "recommendations": [rec.dict() for rec in recommendations[:3]]
            },
            processing_time=0.0
        )
    
    async def _handle_ai_assistant(self, request: HTMXRequest) -> HTMXResponse:
        """Handle AI assistant interactions"""
        message = request.request_data.get("message", "")
        user_id = request.user_id
        session_id = request.session_id
        
        # Get or create AI assistant
        assistant_key = f"{user_id}_{session_id}"
        if assistant_key not in self.ai_assistants:
            self.ai_assistants[assistant_key] = AIAssistant(
                user_id=user_id,
                session_id=session_id,
                context="general"
            )
        
        assistant = self.ai_assistants[assistant_key]
        
        # Add message to conversation history
        assistant.conversation_history.append({
            "role": "user",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Generate AI response (simplified for demo)
        ai_response = f"I understand you're asking about '{message}'. How can I help you with that?"
        
        assistant.conversation_history.append({
            "role": "assistant",
            "message": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Create AI assistant HTML
        html_content = f"""
        <div class="ai-assistant">
            <div class="conversation-history">
                {self._generate_conversation_html(assistant.conversation_history)}
            </div>
            <div class="assistant-input">
                <input type="text" 
                       id="assistant-input" 
                       placeholder="Ask me anything..."
                       hx-post="/ai/assistant/chat"
                       hx-trigger="keyup[key=='Enter']"
                       hx-target="#assistant-conversation"
                       class="assistant-input-field" />
                <button hx-post="/ai/assistant/chat"
                        hx-trigger="click"
                        hx-target="#assistant-conversation"
                        class="send-button">
                    Send
                </button>
            </div>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML"
            },
            metadata={
                "conversation_history": assistant.conversation_history
            },
            processing_time=0.0
        )
    
    async def _handle_recommendation_widget(self, request: HTMXRequest) -> HTMXResponse:
        """Handle recommendation widget"""
        user_id = request.user_id
        
        # Get user recommendations
        recommendations = await self.user_pattern_service.get_user_recommendations(
            user_id=user_id,
            active_only=True
        )
        
        # Create recommendation widget HTML
        html_content = f"""
        <div class="recommendation-widget">
            <h3>Recommended for You</h3>
            <div class="recommendations-list">
                {self._generate_recommendations_html(recommendations[:5])}
            </div>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML"
            },
            metadata={
                "recommendations": [rec.dict() for rec in recommendations[:5]]
            },
            processing_time=0.0
        )
    
    async def _handle_predictive_input(self, request: HTMXRequest) -> HTMXResponse:
        """Handle predictive input"""
        input_text = request.request_data.get("input_text", "")
        field_name = request.request_data.get("field_name", "")
        
        # Generate predictions based on input
        predictions = self._generate_predictions(input_text, field_name)
        
        # Create predictive input HTML
        html_content = f"""
        <div class="predictive-input">
            <input type="text" 
                   id="{field_name}" 
                   value="{input_text}"
                   hx-post="/ai/predictive-input"
                   hx-trigger="keyup changed delay:200ms"
                   hx-target="#{field_name}-predictions"
                   class="predictive-input-field" />
            <div id="{field_name}-predictions" class="predictions-dropdown">
                {self._generate_predictions_html(predictions)}
            </div>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML"
            },
            metadata={
                "predictions": predictions
            },
            processing_time=0.0
        )
    
    async def _handle_smart_table(self, request: HTMXRequest) -> HTMXResponse:
        """Handle smart table interactions"""
        table_data = request.request_data.get("table_data", [])
        sort_column = request.request_data.get("sort_column")
        filter_criteria = request.request_data.get("filter_criteria", {})
        
        # Apply smart sorting and filtering
        processed_data = self._process_table_data(table_data, sort_column, filter_criteria)
        
        # Create smart table HTML
        html_content = f"""
        <div class="smart-table">
            <table class="data-table">
                <thead>
                    <tr>
                        {self._generate_table_headers_html(processed_data)}
                    </tr>
                </thead>
                <tbody>
                    {self._generate_table_rows_html(processed_data)}
                </tbody>
            </table>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML"
            },
            metadata={
                "processed_data": processed_data
            },
            processing_time=0.0
        )
    
    async def _handle_intelligent_chart(self, request: HTMXRequest) -> HTMXResponse:
        """Handle intelligent chart interactions"""
        chart_data = request.request_data.get("chart_data", {})
        chart_type = request.request_data.get("chart_type", "line")
        
        # Process chart data intelligently
        processed_chart_data = self._process_chart_data(chart_data, chart_type)
        
        # Create intelligent chart HTML
        html_content = f"""
        <div class="intelligent-chart">
            <canvas id="chart-canvas" width="800" height="400"></canvas>
            <div class="chart-controls">
                <button hx-post="/ai/chart/update"
                        hx-target="#chart-container"
                        hx-vals='{{"chart_type": "line"}}'
                        class="chart-control-btn">Line</button>
                <button hx-post="/ai/chart/update"
                        hx-target="#chart-container"
                        hx-vals='{{"chart_type": "bar"}}'
                        class="chart-control-btn">Bar</button>
                <button hx-post="/ai/chart/update"
                        hx-target="#chart-container"
                        hx-vals='{{"chart_type": "pie"}}'
                        class="chart-control-btn">Pie</button>
            </div>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML"
            },
            metadata={
                "chart_data": processed_chart_data,
                "chart_type": chart_type
            },
            processing_time=0.0
        )
    
    async def _handle_generic_request(self, request: HTMXRequest) -> HTMXResponse:
        """Handle generic HTMX requests"""
        html_content = f"""
        <div class="ai-component">
            <p>AI-powered component: {request.component_type.value}</p>
            <p>Event: {request.event_type.value}</p>
            <p>Target: {request.target_id}</p>
        </div>
        """
        
        return HTMXResponse(
            request_id=request.id,
            html_content=html_content,
            htmx_attributes={
                "hx-swap": "innerHTML"
            },
            metadata={
                "component_type": request.component_type.value,
                "event_type": request.event_type.value
            },
            processing_time=0.0
        )
    
    def _generate_suggestions_html(self, suggestions: List[str]) -> str:
        """Generate HTML for suggestions"""
        if not suggestions:
            return ""
        
        html = '<div class="suggestions-list">'
        for suggestion in suggestions[:5]:
            html += f'<div class="suggestion-item">{suggestion}</div>'
        html += '</div>'
        return html
    
    def _generate_search_suggestions_html(self, suggestions: List[str]) -> str:
        """Generate HTML for search suggestions"""
        if not suggestions:
            return ""
        
        html = '<div class="search-suggestions">'
        for suggestion in suggestions[:8]:
            html += f'<div class="search-suggestion" onclick="selectSearchSuggestion(\'{suggestion}\')">{suggestion}</div>'
        html += '</div>'
        return html
    
    def _generate_recommendations_html(self, recommendations: List) -> str:
        """Generate HTML for recommendations"""
        if not recommendations:
            return '<div class="no-recommendations">No recommendations available</div>'
        
        html = '<div class="recommendations-list">'
        for rec in recommendations:
            html += f"""
            <div class="recommendation-item">
                <h4>{rec.title}</h4>
                <p>{rec.description}</p>
                <div class="recommendation-actions">
                    <button hx-post="/ai/recommendation/apply"
                            hx-vals='{{"recommendation_id": "{rec.id}"}}'
                            class="apply-btn">Apply</button>
                    <button hx-post="/ai/recommendation/dismiss"
                            hx-vals='{{"recommendation_id": "{rec.id}"}}'
                            class="dismiss-btn">Dismiss</button>
                </div>
            </div>
            """
        html += '</div>'
        return html
    
    def _generate_conversation_html(self, conversation_history: List[Dict]) -> str:
        """Generate HTML for conversation history"""
        html = '<div class="conversation-history">'
        for message in conversation_history[-10:]:  # Last 10 messages
            role_class = "user-message" if message["role"] == "user" else "assistant-message"
            html += f"""
            <div class="message {role_class}">
                <div class="message-content">{message["message"]}</div>
                <div class="message-timestamp">{message["timestamp"]}</div>
            </div>
            """
        html += '</div>'
        return html
    
    def _generate_predictions(self, input_text: str, field_name: str) -> List[str]:
        """Generate predictions based on input text and field name"""
        # Simple prediction logic (in real implementation, this would use ML models)
        predictions = []
        
        if field_name == "email":
            if "@" in input_text:
                predictions.extend(["gmail.com", "yahoo.com", "outlook.com"])
        elif field_name == "name":
            predictions.extend(["John", "Jane", "Mike", "Sarah"])
        elif field_name == "project":
            predictions.extend(["CAD Design", "3D Modeling", "Documentation", "Analysis"])
        
        return predictions
    
    def _generate_predictions_html(self, predictions: List[str]) -> str:
        """Generate HTML for predictions"""
        if not predictions:
            return ""
        
        html = '<div class="predictions-list">'
        for prediction in predictions:
            html += f'<div class="prediction-item" onclick="selectPrediction(\'{prediction}\')">{prediction}</div>'
        html += '</div>'
        return html
    
    def _generate_table_headers_html(self, data: List[Dict]) -> str:
        """Generate HTML for table headers"""
        if not data:
            return ""
        
        headers = list(data[0].keys())
        html = ""
        for header in headers:
            html += f'<th class="sortable-header" hx-post="/ai/table/sort" hx-vals=\'{{"column": "{header}"}}\'>{header.title()}</th>'
        return html
    
    def _generate_table_rows_html(self, data: List[Dict]) -> str:
        """Generate HTML for table rows"""
        html = ""
        for row in data:
            html += '<tr>'
            for value in row.values():
                html += f'<td>{value}</td>'
            html += '</tr>'
        return html
    
    def _process_table_data(self, data: List[Dict], sort_column: Optional[str], filter_criteria: Dict) -> List[Dict]:
        """Process table data with sorting and filtering"""
        # Apply filters
        if filter_criteria:
            filtered_data = []
            for row in data:
                if all(row.get(key) == value for key, value in filter_criteria.items()):
                    filtered_data.append(row)
            data = filtered_data
        
        # Apply sorting
        if sort_column and data:
            data.sort(key=lambda x: x.get(sort_column, ""))
        
        return data
    
    def _process_chart_data(self, data: Dict, chart_type: str) -> Dict:
        """Process chart data for different chart types"""
        # Simple data processing (in real implementation, this would be more sophisticated)
        processed_data = {
            "labels": data.get("labels", []),
            "datasets": data.get("datasets", []),
            "chart_type": chart_type
        }
        
        return processed_data
    
    async def create_ai_component(
        self,
        component_type: AIComponentType,
        name: str,
        description: str,
        target_selector: str,
        htmx_config: Dict[str, Any] = None,
        ai_config: Dict[str, Any] = None
    ) -> AIComponent:
        """Create a new AI component"""
        component = AIComponent(
            component_type=component_type,
            name=name,
            description=description,
            target_selector=target_selector,
            htmx_config=htmx_config or {},
            ai_config=ai_config or {}
        )
        
        self.components[component.id] = component
        logger.info(f"Created AI component: {name}")
        return component
    
    async def get_ai_component(self, component_id: UUID) -> Optional[AIComponent]:
        """Get AI component by ID"""
        return self.components.get(component_id)
    
    async def get_ai_components(
        self,
        component_type: Optional[AIComponentType] = None,
        active_only: bool = True
    ) -> List[AIComponent]:
        """Get AI components with optional filters"""
        components = list(self.components.values())
        
        if component_type:
            components = [c for c in components if c.component_type == component_type]
        if active_only:
            components = [c for c in components if c.is_active]
        
        return components 