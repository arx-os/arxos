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
from .pdf_analysis import PDFAnalysisAgent, SystemSchedule


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
        
        # Initialize PDF analysis agent
        self.pdf_analyzer = PDFAnalysisAgent(config.get("pdf_analysis", {}))
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("GUS Agent initialized successfully")
    
    async def process_query(
        self, 
        query: str, 
        user_id: str,
        context: Optional[Dict[str, Any]] = None
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
                nlp_result.intent,
                nlp_result.entities,
                context
            )
            
            # Make decision on response
            decision_result = await self.decision.decide(
                nlp_result,
                knowledge_result,
                session
            )
            
            # Generate response
            response = await self._generate_response(
                nlp_result,
                knowledge_result,
                decision_result,
                session
            )
            
            # Update session
            self._update_session(user_id, session, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return GUSResponse(
                message=f"I encountered an error processing your request: {str(e)}",
                confidence=0.0,
                intent="error",
                entities={},
                actions=[],
                context={},
                timestamp=datetime.utcnow()
            )
    
    async def execute_task(
        self, 
        task: str, 
        parameters: Dict[str, Any],
        user_id: str
    ) -> GUSResponse:
        """
        Execute a specific task
        
        Args:
            task: Task identifier
            parameters: Task parameters
            user_id: User identifier
            
        Returns:
            GUSResponse: Task execution result
        """
        try:
            self.logger.info(f"Executing task: {task} for user: {user_id}")
            
            if task == "pdf_system_analysis":
                return await self._execute_pdf_analysis(parameters, user_id)
            elif task == "schedule_generation":
                return await self._execute_schedule_generation(parameters, user_id)
            elif task == "cost_estimation":
                return await self._execute_cost_estimation(parameters, user_id)
            else:
                return GUSResponse(
                    message=f"Unknown task: {task}",
                    confidence=0.0,
                    intent="error",
                    entities={},
                    actions=[],
                    context={},
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            self.logger.error(f"Error executing task {task}: {e}")
            return GUSResponse(
                message=f"Error executing task {task}: {str(e)}",
                confidence=0.0,
                intent="error",
                entities={},
                actions=[],
                context={},
                timestamp=datetime.utcnow()
            )
    
    async def _execute_pdf_analysis(
        self, 
        parameters: Dict[str, Any], 
        user_id: str
    ) -> GUSResponse:
        """
        Execute PDF analysis for system schedule generation
        
        Args:
            parameters: Analysis parameters including PDF file path
            user_id: User identifier
            
        Returns:
            GUSResponse: Analysis results
        """
        try:
            pdf_file_path = parameters.get('pdf_file_path')
            requirements = parameters.get('requirements', {})
            
            if not pdf_file_path:
                return GUSResponse(
                    message="PDF file path is required for analysis",
                    confidence=0.0,
                    intent="error",
                    entities={},
                    actions=[],
                    context={},
                    timestamp=datetime.utcnow()
                )
            
            # Execute PDF analysis
            system_schedule = await self.pdf_analyzer.analyze_pdf_for_schedule(
                pdf_file_path, 
                requirements
            )
            
            # Convert schedule to response format
            schedule_data = self._convert_schedule_to_dict(system_schedule)
            
            return GUSResponse(
                message=f"PDF analysis completed successfully. Found {schedule_data['quantities']['total_components']} system components with {system_schedule.confidence:.1%} confidence.",
                confidence=system_schedule.confidence,
                intent="pdf_analysis_complete",
                entities={
                    'total_components': schedule_data['quantities']['total_components'],
                    'systems_found': list(schedule_data['systems'].keys()),
                    'confidence': system_schedule.confidence
                },
                actions=[
                    {
                        'type': 'schedule_generated',
                        'data': schedule_data
                    }
                ],
                context={
                    'analysis_results': schedule_data,
                    'processing_time': system_schedule.metadata.get('processing_time', 0)
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"PDF analysis failed: {e}")
            return GUSResponse(
                message=f"PDF analysis failed: {str(e)}",
                confidence=0.0,
                intent="error",
                entities={},
                actions=[],
                context={},
                timestamp=datetime.utcnow()
            )
    
    async def _execute_schedule_generation(
        self, 
        parameters: Dict[str, Any], 
        user_id: str
    ) -> GUSResponse:
        """
        Execute schedule generation from analysis results
        
        Args:
            parameters: Schedule generation parameters
            user_id: User identifier
            
        Returns:
            GUSResponse: Schedule generation results
        """
        try:
            # Extract analysis results
            analysis_results = parameters.get('analysis_results', {})
            
            if not analysis_results:
                return GUSResponse(
                    message="Analysis results are required for schedule generation",
                    confidence=0.0,
                    intent="error",
                    entities={},
                    actions=[],
                    context={},
                    timestamp=datetime.utcnow()
                )
            
            # Generate enhanced schedule
            enhanced_schedule = self._enhance_schedule(analysis_results)
            
            return GUSResponse(
                message=f"Schedule generated successfully with {enhanced_schedule['total_items']} items across {len(enhanced_schedule['systems'])} systems.",
                confidence=0.9,
                intent="schedule_generated",
                entities={
                    'total_items': enhanced_schedule['total_items'],
                    'systems': list(enhanced_schedule['systems'].keys())
                },
                actions=[
                    {
                        'type': 'schedule_ready',
                        'data': enhanced_schedule
                    }
                ],
                context={
                    'schedule': enhanced_schedule
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Schedule generation failed: {e}")
            return GUSResponse(
                message=f"Schedule generation failed: {str(e)}",
                confidence=0.0,
                intent="error",
                entities={},
                actions=[],
                context={},
                timestamp=datetime.utcnow()
            )
    
    async def _execute_cost_estimation(
        self, 
        parameters: Dict[str, Any], 
        user_id: str
    ) -> GUSResponse:
        """
        Execute cost estimation for system components
        
        Args:
            parameters: Cost estimation parameters
            user_id: User identifier
            
        Returns:
            GUSResponse: Cost estimation results
        """
        try:
            # Extract system components
            system_components = parameters.get('system_components', {})
            
            if not system_components:
                return GUSResponse(
                    message="System components are required for cost estimation",
                    confidence=0.0,
                    intent="error",
                    entities={},
                    actions=[],
                    context={},
                    timestamp=datetime.utcnow()
                )
            
            # Calculate detailed costs
            detailed_costs = self._calculate_detailed_costs(system_components)
            
            return GUSResponse(
                message=f"Cost estimation completed. Total estimated cost: ${detailed_costs['total_cost']:,.2f}",
                confidence=0.8,
                intent="cost_estimated",
                entities={
                    'total_cost': detailed_costs['total_cost'],
                    'system_costs': detailed_costs['system_costs']
                },
                actions=[
                    {
                        'type': 'cost_estimate_ready',
                        'data': detailed_costs
                    }
                ],
                context={
                    'cost_estimate': detailed_costs
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Cost estimation failed: {e}")
            return GUSResponse(
                message=f"Cost estimation failed: {str(e)}",
                confidence=0.0,
                intent="error",
                entities={},
                actions=[],
                context={},
                timestamp=datetime.utcnow()
            )
    
    def _convert_schedule_to_dict(self, system_schedule: SystemSchedule) -> Dict[str, Any]:
        """Convert SystemSchedule to dictionary format"""
        return {
            'project_info': system_schedule.project_info,
            'systems': {
                system_type: [
                    {
                        'id': comp.id,
                        'type': comp.type,
                        'category': comp.category,
                        'properties': comp.properties,
                        'position': comp.position,
                        'confidence': comp.confidence,
                        'metadata': comp.metadata
                    }
                    for comp in components
                ]
                for system_type, components in system_schedule.systems.items()
            },
            'quantities': system_schedule.quantities,
            'cost_estimates': system_schedule.cost_estimates,
            'timeline': system_schedule.timeline,
            'confidence': system_schedule.confidence,
            'metadata': system_schedule.metadata
        }
    
    def _enhance_schedule(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance schedule with additional information"""
        enhanced = analysis_results.copy()
        
        # Add total items count
        total_items = sum(
            len(system.get('components', [])) 
            for system in enhanced.get('systems', {}).values()
        )
        enhanced['total_items'] = total_items
        
        # Add system summaries
        for system_type, system_data in enhanced.get('systems', {}).items():
            components = system_data.get('components', [])
            enhanced['systems'][system_type]['summary'] = {
                'count': len(components),
                'types': list(set(comp.get('type', '') for comp in components)),
                'confidence_avg': sum(comp.get('confidence', 0) for comp in components) / max(len(components), 1)
            }
        
        return enhanced
    
    def _calculate_detailed_costs(self, system_components: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed costs for system components"""
        system_costs = {}
        total_cost = 0.0
        
        # Cost factors by system type
        cost_factors = {
            'architectural': 1.0,
            'mechanical': 1.2,
            'electrical': 1.1,
            'plumbing': 1.15,
            'technology': 1.3
        }
        
        for system_type, components in system_components.items():
            system_cost = 0.0
            
            for component in components:
                # Base costs by component type
                base_costs = {
                    'wall': 50.0,
                    'duct': 25.0,
                    'outlet': 150.0,
                    'fixture': 500.0,
                    'equipment': 2000.0,
                    'panel': 1000.0,
                    'light': 200.0,
                    'valve': 300.0,
                    'pipe': 15.0
                }
                
                component_type = component.get('type', 'unknown')
                base_cost = base_costs.get(component_type, 100.0)
                
                # Apply system-specific factor
                factor = cost_factors.get(system_type, 1.0)
                component_cost = base_cost * factor
                
                system_cost += component_cost
            
            system_costs[system_type] = system_cost
            total_cost += system_cost
        
        return {
            'total_cost': total_cost,
            'system_costs': system_costs,
            'cost_factors': cost_factors
        }
    
    async def get_knowledge(
        self, 
        topic: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> GUSResponse:
        """
        Get knowledge about a specific topic
        
        Args:
            topic: Topic to query
            context: Additional context
            
        Returns:
            GUSResponse: Knowledge response
        """
        try:
            # Query knowledge base
            knowledge_result = await self.knowledge.query(topic, {}, context)
            
            return GUSResponse(
                message=f"Here's what I know about {topic}: {knowledge_result.get('summary', 'No information available')}",
                confidence=knowledge_result.get('confidence', 0.0),
                intent="knowledge_query",
                entities={'topic': topic},
                actions=[],
                context={'knowledge': knowledge_result},
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error getting knowledge: {e}")
            return GUSResponse(
                message=f"Error retrieving knowledge about {topic}: {str(e)}",
                confidence=0.0,
                intent="error",
                entities={},
                actions=[],
                context={},
                timestamp=datetime.utcnow()
            )
    
    def _get_user_session(self, user_id: str) -> Dict[str, Any]:
        """Get or create user session"""
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = {
                'created_at': datetime.utcnow(),
                'interaction_count': 0,
                'context': {},
                'preferences': {}
            }
        
        return self.active_sessions[user_id]
    
    def _update_session(
        self, 
        user_id: str, 
        session: Dict[str, Any], 
        response: GUSResponse
    ):
        """Update user session with response"""
        session['interaction_count'] += 1
        session['last_interaction'] = datetime.utcnow()
        session['last_intent'] = response.intent
        session['context'].update(response.context)
    
    async def _generate_response(
        self,
        nlp_result,
        knowledge_result,
        decision_result,
        session: Dict[str, Any]
    ) -> GUSResponse:
        """Generate response from processing results"""
        # Combine results to generate response
        message = decision_result.get('response', 'I understand your request.')
        confidence = decision_result.get('confidence', 0.5)
        
        return GUSResponse(
            message=message,
            confidence=confidence,
            intent=nlp_result.intent,
            entities=nlp_result.entities,
            actions=decision_result.get('actions', []),
            context={
                'nlp_result': nlp_result,
                'knowledge_result': knowledge_result,
                'decision_result': decision_result
            },
            timestamp=datetime.utcnow()
        )
    
    async def shutdown(self):
        """Shutdown the GUS agent"""
        self.logger.info("Shutting down GUS Agent...")
        
        # Cleanup sessions
        self.active_sessions.clear()
        self.active_tasks.clear()
        
        self.logger.info("GUS Agent shutdown complete") 