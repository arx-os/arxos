"""
Custom Decision Engine for GUS

Custom decision-making implementation for PDF analysis
and system schedule generation. Built specifically for Arxos without
external dependencies.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class DecisionResult:
    """Result from decision engine"""
    response: str
    confidence: float
    actions: List[Dict[str, Any]]
    reasoning: str


class DecisionEngine:
    """
    Custom Decision Engine for GUS
    
    Handles decision-making for PDF analysis and system schedule generation.
    Built without external dependencies using custom decision logic.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize decision engine"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Decision rules for different intents
        self.decision_rules = {
            'pdf_analysis': {
                'response_template': 'I will analyze the PDF for system schedule generation.',
                'confidence_boost': 0.1,
                'actions': ['start_pdf_analysis'],
                'reasoning': 'PDF analysis requested for system extraction'
            },
            'schedule_generation': {
                'response_template': 'I will generate a comprehensive system schedule.',
                'confidence_boost': 0.15,
                'actions': ['generate_schedule'],
                'reasoning': 'Schedule generation requested'
            },
            'cost_estimation': {
                'response_template': 'I will include cost estimation in the analysis.',
                'confidence_boost': 0.1,
                'actions': ['include_cost_estimation'],
                'reasoning': 'Cost estimation requested'
            },
            'timeline_generation': {
                'response_template': 'I will generate a project timeline.',
                'confidence_boost': 0.1,
                'actions': ['include_timeline'],
                'reasoning': 'Timeline generation requested'
            },
            'status_check': {
                'response_template': 'I will check the status of your analysis.',
                'confidence_boost': 0.05,
                'actions': ['check_status'],
                'reasoning': 'Status check requested'
            },
            'export_request': {
                'response_template': 'I will help you export the results.',
                'confidence_boost': 0.1,
                'actions': ['prepare_export'],
                'reasoning': 'Export requested'
            },
            'error': {
                'response_template': 'I encountered an error processing your request.',
                'confidence_boost': 0.0,
                'actions': ['log_error'],
                'reasoning': 'Error occurred during processing'
            },
            'unknown': {
                'response_template': 'I\'m not sure what you\'re asking for. Could you clarify?',
                'confidence_boost': 0.0,
                'actions': ['request_clarification'],
                'reasoning': 'Intent not recognized'
            }
        }
        
        # Context enhancement rules
        self.context_rules = {
            'high_confidence': {
                'threshold': 0.8,
                'action_boost': 0.2,
                'reasoning': 'High confidence allows immediate action'
            },
            'medium_confidence': {
                'threshold': 0.6,
                'action_boost': 0.1,
                'reasoning': 'Medium confidence requires validation'
            },
            'low_confidence': {
                'threshold': 0.4,
                'action_boost': 0.0,
                'reasoning': 'Low confidence requires user confirmation'
            }
        }
        
        self.logger.info("Custom Decision Engine initialized")
    
    async def decide(
        self, 
        nlp_result: Any, 
        knowledge_result: Any, 
        session: Dict[str, Any]
    ) -> DecisionResult:
        """
        Make decision based on NLP and knowledge results
        
        Args:
            nlp_result: Result from NLP processing
            knowledge_result: Result from knowledge query
            session: User session context
            
        Returns:
            DecisionResult: Decision result with response and actions
        """
        try:
            # Extract intent and confidence from NLP result
            intent = getattr(nlp_result, 'intent', 'unknown')
            nlp_confidence = getattr(nlp_result, 'confidence', 0.0)
            
            # Get knowledge confidence
            knowledge_confidence = getattr(knowledge_result, 'confidence', 0.0)
            
            # Get decision rule for intent
            rule = self.decision_rules.get(intent, self.decision_rules['unknown'])
            
            # Calculate overall confidence
            confidence = self._calculate_decision_confidence(
                nlp_confidence, 
                knowledge_confidence, 
                rule['confidence_boost']
            )
            
            # Generate response
            response = self._generate_response(rule, intent, session)
            
            # Determine actions
            actions = self._determine_actions(rule, intent, confidence, session)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(rule, intent, confidence, session)
            
            return DecisionResult(
                response=response,
                confidence=confidence,
                actions=actions,
                reasoning=reasoning
            )
            
        except Exception as e:
            self.logger.error(f"Error in decision engine: {e}")
            return DecisionResult(
                response="I encountered an error making a decision.",
                confidence=0.0,
                actions=[{'type': 'log_error', 'error': str(e)}],
                reasoning=f"Error occurred: {str(e)}"
            )
    
    def _calculate_decision_confidence(
        self, 
        nlp_confidence: float, 
        knowledge_confidence: float, 
        boost: float
    ) -> float:
        """Calculate overall decision confidence"""
        # Weight NLP confidence more heavily (70%)
        weighted_confidence = (nlp_confidence * 0.7) + (knowledge_confidence * 0.3)
        
        # Apply rule-specific boost
        boosted_confidence = weighted_confidence + boost
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, boosted_confidence))
    
    def _generate_response(self, rule: Dict[str, Any], intent: str, session: Dict[str, Any]) -> str:
        """Generate response message"""
        response = rule['response_template']
        
        # Enhance response based on session context
        if 'previous_actions' in session:
            if 'pdf_analysis' in session['previous_actions']:
                response += " This will build on your previous analysis."
        
        if 'user_preferences' in session:
            if 'detailed_output' in session['user_preferences']:
                response += " I'll provide detailed output as requested."
        
        return response
    
    def _determine_actions(
        self, 
        rule: Dict[str, Any], 
        intent: str, 
        confidence: float, 
        session: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Determine actions to take"""
        actions = []
        
        # Add base actions from rule
        for action_type in rule['actions']:
            actions.append({
                'type': action_type,
                'intent': intent,
                'confidence': confidence
            })
        
        # Add confidence-based actions
        confidence_actions = self._get_confidence_actions(confidence)
        actions.extend(confidence_actions)
        
        # Add session-based actions
        session_actions = self._get_session_actions(session)
        actions.extend(session_actions)
        
        return actions
    
    def _get_confidence_actions(self, confidence: float) -> List[Dict[str, Any]]:
        """Get actions based on confidence level"""
        actions = []
        
        if confidence >= self.context_rules['high_confidence']['threshold']:
            actions.append({
                'type': 'execute_immediately',
                'reasoning': 'High confidence allows immediate execution'
            })
        elif confidence >= self.context_rules['medium_confidence']['threshold']:
            actions.append({
                'type': 'request_validation',
                'reasoning': 'Medium confidence requires user validation'
            })
        else:
            actions.append({
                'type': 'request_confirmation',
                'reasoning': 'Low confidence requires explicit confirmation'
            })
        
        return actions
    
    def _get_session_actions(self, session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get actions based on session context"""
        actions = []
        
        # Add actions based on user history
        if 'analysis_count' in session:
            if session['analysis_count'] > 5:
                actions.append({
                    'type': 'optimize_for_experienced_user',
                    'reasoning': 'User has extensive analysis history'
                })
        
        # Add actions based on preferences
        if 'user_preferences' in session:
            prefs = session['user_preferences']
            if 'fast_processing' in prefs:
                actions.append({
                    'type': 'prioritize_speed',
                    'reasoning': 'User prefers fast processing'
                })
            
            if 'detailed_output' in prefs:
                actions.append({
                    'type': 'include_detailed_output',
                    'reasoning': 'User prefers detailed output'
                })
        
        return actions
    
    def _generate_reasoning(
        self, 
        rule: Dict[str, Any], 
        intent: str, 
        confidence: float, 
        session: Dict[str, Any]
    ) -> str:
        """Generate reasoning for decision"""
        reasoning = rule['reasoning']
        
        # Add confidence-based reasoning
        if confidence >= 0.8:
            reasoning += " High confidence allows immediate action."
        elif confidence >= 0.6:
            reasoning += " Medium confidence requires validation."
        else:
            reasoning += " Low confidence requires confirmation."
        
        # Add session-based reasoning
        if 'previous_actions' in session:
            reasoning += f" Based on {len(session['previous_actions'])} previous actions."
        
        return reasoning
    
    def get_supported_intents(self) -> List[str]:
        """Get list of supported intents"""
        return list(self.decision_rules.keys())
    
    def get_decision_rule(self, intent: str) -> Optional[Dict[str, Any]]:
        """Get decision rule for specific intent"""
        return self.decision_rules.get(intent)
    
    def add_decision_rule(self, intent: str, rule: Dict[str, Any]) -> bool:
        """Add new decision rule"""
        try:
            self.decision_rules[intent] = rule
            self.logger.info(f"Added decision rule for intent: {intent}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding decision rule: {e}")
            return False
    
    def update_decision_rule(self, intent: str, updates: Dict[str, Any]) -> bool:
        """Update existing decision rule"""
        try:
            if intent in self.decision_rules:
                self.decision_rules[intent].update(updates)
                self.logger.info(f"Updated decision rule for intent: {intent}")
                return True
            else:
                self.logger.warning(f"Intent not found: {intent}")
                return False
        except Exception as e:
            self.logger.error(f"Error updating decision rule: {e}")
            return False 