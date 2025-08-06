"""
GUS Decision Engine

Decision engine component for the GUS agent.
Handles rule-based logic, machine learning models, optimization algorithms,
and risk assessment for intelligent decision making.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Try to import ML libraries
try:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available, using rule-based decision making")


class DecisionType(Enum):
    """Decision types for GUS agent"""
    
    # Response decisions
    PROVIDE_INFORMATION = "provide_information"
    ASK_CLARIFICATION = "ask_clarification"
    EXECUTE_ACTION = "execute_action"
    REDIRECT_TO_TOOL = "redirect_to_tool"
    
    # Risk decisions
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    
    # Confidence decisions
    HIGH_CONFIDENCE = "high_confidence"
    MEDIUM_CONFIDENCE = "medium_confidence"
    LOW_CONFIDENCE = "low_confidence"


@dataclass
class DecisionResult:
    """Result of decision engine processing"""
    
    decision_type: DecisionType
    confidence: float
    reasoning: str
    actions: List[Dict[str, Any]]
    risk_level: str
    recommendations: List[str]
    timestamp: datetime


class DecisionEngine:
    """
    Decision Engine for GUS agent
    
    Handles:
    - Rule-based logic for response generation
    - Machine learning models for pattern recognition
    - Optimization algorithms for action selection
    - Risk assessment and mitigation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize decision engine
        
        Args:
            config: Configuration dictionary with decision settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Decision rules
        self.decision_rules = self._initialize_decision_rules()
        
        # Risk assessment rules
        self.risk_rules = self._initialize_risk_rules()
        
        # Initialize ML models if available
        if ML_AVAILABLE:
            self._initialize_ml_models()
        
        # Decision history for learning
        self.decision_history: List[Dict[str, Any]] = []
        
        self.logger.info("Decision Engine initialized successfully")
    
    def _initialize_decision_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize decision rules"""
        return {
            "intent_based": [
                {
                    "condition": "intent == 'create_drawing'",
                    "action": DecisionType.EXECUTE_ACTION,
                    "confidence_threshold": 0.7,
                    "risk_level": "low"
                },
                {
                    "condition": "intent == 'get_help'",
                    "action": DecisionType.PROVIDE_INFORMATION,
                    "confidence_threshold": 0.5,
                    "risk_level": "low"
                },
                {
                    "condition": "intent == 'unknown'",
                    "action": DecisionType.ASK_CLARIFICATION,
                    "confidence_threshold": 0.0,
                    "risk_level": "low"
                },
                {
                    "condition": "intent == 'contribute_bilt'",
                    "action": DecisionType.REDIRECT_TO_TOOL,
                    "confidence_threshold": 0.8,
                    "risk_level": "medium"
                }
            ],
            "confidence_based": [
                {
                    "condition": "confidence >= 0.8",
                    "action": DecisionType.EXECUTE_ACTION,
                    "risk_level": "low"
                },
                {
                    "condition": "0.5 <= confidence < 0.8",
                    "action": DecisionType.PROVIDE_INFORMATION,
                    "risk_level": "medium"
                },
                {
                    "condition": "confidence < 0.5",
                    "action": DecisionType.ASK_CLARIFICATION,
                    "risk_level": "high"
                }
            ],
            "entity_based": [
                {
                    "condition": "has_entity('device_type')",
                    "action": DecisionType.EXECUTE_ACTION,
                    "confidence_threshold": 0.6,
                    "risk_level": "low"
                },
                {
                    "condition": "has_entity('measurement')",
                    "action": DecisionType.EXECUTE_ACTION,
                    "confidence_threshold": 0.7,
                    "risk_level": "low"
                },
                {
                    "condition": "has_entity('wallet_address')",
                    "action": DecisionType.REDIRECT_TO_TOOL,
                    "confidence_threshold": 0.9,
                    "risk_level": "medium"
                }
            ]
        }
    
    def _initialize_risk_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize risk assessment rules"""
        return {
            "high_risk": [
                "intent == 'unknown' and confidence < 0.3",
                "has_entity('wallet_address') and intent == 'contribute_bilt'",
                "confidence < 0.2",
                "context_has_recent_errors"
            ],
            "medium_risk": [
                "0.3 <= confidence < 0.6",
                "intent == 'edit_drawing' and has_entity('measurement')",
                "has_entity('system_type') and intent == 'configure_system'",
                "context_has_recent_clarifications"
            ],
            "low_risk": [
                "confidence >= 0.7",
                "intent == 'greeting' or intent == 'farewell'",
                "intent == 'get_help' and confidence >= 0.5",
                "has_entity('file_format') and intent == 'export_drawing'"
            ]
        }
    
    def _initialize_ml_models(self):
        """Initialize machine learning models"""
        try:
            # Intent classification model
            self.intent_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Text vectorizer
            self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            
            # Model training data (would be populated from historical data)
            self.training_data = []
            self.training_labels = []
            
            self.logger.info("ML models initialized")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize ML models: {e}")
            self.intent_classifier = None
            self.text_vectorizer = None
    
    async def decide(
        self, nlp_result, knowledge_result, session: Dict[str, Any]
    ) -> DecisionResult:
        """
        Make decision based on NLP and knowledge results
        
        Args:
            nlp_result: NLP processing result
            knowledge_result: Knowledge base query result
            session: User session context
            
        Returns:
            DecisionResult: Decision with actions and recommendations
        """
        try:
            # Assess risk level
            risk_level = self._assess_risk(nlp_result, knowledge_result, session)
            
            # Determine decision type
            decision_type = self._determine_decision_type(nlp_result, knowledge_result, session)
            
            # Calculate confidence
            confidence = self._calculate_decision_confidence(nlp_result, knowledge_result, session)
            
            # Generate actions
            actions = self._generate_actions(decision_type, nlp_result, knowledge_result, session)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(decision_type, risk_level, session)
            
            # Create decision result
            result = DecisionResult(
                decision_type=decision_type,
                confidence=confidence,
                reasoning=self._generate_reasoning(decision_type, risk_level, confidence),
                actions=actions,
                risk_level=risk_level,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
            
            # Record decision for learning
            self._record_decision(result, nlp_result, knowledge_result, session)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in decision making: {e}")
            return DecisionResult(
                decision_type=DecisionType.ASK_CLARIFICATION,
                confidence=0.0,
                reasoning="Error in decision making, defaulting to clarification request",
                actions=[],
                risk_level="high",
                recommendations=["Please rephrase your request"],
                timestamp=datetime.utcnow()
            )
    
    def _assess_risk(
        self, nlp_result, knowledge_result, session: Dict[str, Any]
    ) -> str:
        """Assess risk level based on rules"""
        risk_score = 0
        
        # Check high risk conditions
        for condition in self.risk_rules["high_risk"]:
            if self._evaluate_condition(condition, nlp_result, knowledge_result, session):
                return "high"
        
        # Check medium risk conditions
        for condition in self.risk_rules["medium_risk"]:
            if self._evaluate_condition(condition, nlp_result, knowledge_result, session):
                risk_score += 1
        
        # Check low risk conditions
        for condition in self.risk_rules["low_risk"]:
            if self._evaluate_condition(condition, nlp_result, knowledge_result, session):
                risk_score -= 1
        
        # Determine risk level based on score
        if risk_score >= 2:
            return "medium"
        elif risk_score <= -1:
            return "low"
        else:
            return "medium"
    
    def _evaluate_condition(
        self, condition: str, nlp_result, knowledge_result, session: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition string"""
        try:
            # Simple condition evaluation (in practice, use a proper expression evaluator)
            if "intent == 'unknown'" in condition and nlp_result.intent.value == "unknown":
                return True
            elif "confidence < 0.3" in condition and nlp_result.confidence < 0.3:
                return True
            elif "confidence >= 0.7" in condition and nlp_result.confidence >= 0.7:
                return True
            elif "has_entity('wallet_address')" in condition:
                return any(e.type == "wallet_address" for e in nlp_result.entities)
            elif "has_entity('device_type')" in condition:
                return any(e.type == "device_type" for e in nlp_result.entities)
            elif "has_entity('measurement')" in condition:
                return any(e.type == "measurement" for e in nlp_result.entities)
            elif "has_entity('system_type')" in condition:
                return any(e.type == "system_type" for e in nlp_result.entities)
            elif "has_entity('file_format')" in condition:
                return any(e.type == "file_format" for e in nlp_result.entities)
            elif "context_has_recent_errors" in condition:
                return session.get("recent_errors", 0) > 0
            elif "context_has_recent_clarifications" in condition:
                return session.get("recent_clarifications", 0) > 0
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _determine_decision_type(
        self, nlp_result, knowledge_result, session: Dict[str, Any]
    ) -> DecisionType:
        """Determine decision type based on rules"""
        
        # Check intent-based rules
        for rule in self.decision_rules["intent_based"]:
            if self._evaluate_condition(rule["condition"], nlp_result, knowledge_result, session):
                if nlp_result.confidence >= rule.get("confidence_threshold", 0.0):
                    return rule["action"]
        
        # Check confidence-based rules
        for rule in self.decision_rules["confidence_based"]:
            if self._evaluate_condition(rule["condition"], nlp_result, knowledge_result, session):
                return rule["action"]
        
        # Check entity-based rules
        for rule in self.decision_rules["entity_based"]:
            if self._evaluate_condition(rule["condition"], nlp_result, knowledge_result, session):
                if nlp_result.confidence >= rule.get("confidence_threshold", 0.0):
                    return rule["action"]
        
        # Default decision
        if nlp_result.confidence >= 0.7:
            return DecisionType.EXECUTE_ACTION
        elif nlp_result.confidence >= 0.4:
            return DecisionType.PROVIDE_INFORMATION
        else:
            return DecisionType.ASK_CLARIFICATION
    
    def _calculate_decision_confidence(
        self, nlp_result, knowledge_result, session: Dict[str, Any]
    ) -> float:
        """Calculate confidence for the decision"""
        base_confidence = nlp_result.confidence
        
        # Boost confidence if we have relevant knowledge
        if knowledge_result.items:
            knowledge_boost = min(len(knowledge_result.items) * 0.1, 0.3)
            base_confidence += knowledge_boost
        
        # Reduce confidence if session has recent errors
        if session.get("recent_errors", 0) > 0:
            base_confidence *= 0.8
        
        # Boost confidence for common intents
        common_intents = ["greeting", "farewell", "get_help"]
        if nlp_result.intent.value in common_intents:
            base_confidence = min(base_confidence + 0.2, 1.0)
        
        return min(base_confidence, 1.0)
    
    def _generate_actions(
        self, decision_type: DecisionType, nlp_result, knowledge_result, session: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actions based on decision type"""
        actions = []
        
        if decision_type == DecisionType.EXECUTE_ACTION:
            # Generate specific actions based on intent
            if nlp_result.intent.value == "create_drawing":
                actions.append({
                    "type": "create_drawing",
                    "parameters": {
                        "system_type": self._extract_system_type(nlp_result.entities),
                        "precision": "high"
                    }
                })
            elif nlp_result.intent.value == "export_drawing":
                actions.append({
                    "type": "export_drawing",
                    "parameters": {
                        "format": self._extract_file_format(nlp_result.entities),
                        "precision": "high"
                    }
                })
            elif nlp_result.intent.value == "contribute_bilt":
                actions.append({
                    "type": "contribute_bilt",
                    "parameters": {
                        "wallet_address": self._extract_wallet_address(nlp_result.entities),
                        "object_data": self._extract_object_data(nlp_result.entities)
                    }
                })
        
        elif decision_type == DecisionType.PROVIDE_INFORMATION:
            # Provide information from knowledge base
            if knowledge_result.items:
                actions.append({
                    "type": "provide_information",
                    "parameters": {
                        "knowledge_items": [item.title for item in knowledge_result.items[:3]],
                        "confidence": knowledge_result.confidence
                    }
                })
        
        elif decision_type == DecisionType.REDIRECT_TO_TOOL:
            # Redirect to appropriate tool
            if nlp_result.intent.value == "contribute_bilt":
                actions.append({
                    "type": "redirect_to_bilt",
                    "parameters": {
                        "endpoint": "/api/v1/bilt/contribute",
                        "wallet_address": self._extract_wallet_address(nlp_result.entities)
                    }
                })
        
        elif decision_type == DecisionType.ASK_CLARIFICATION:
            # Ask for clarification
            actions.append({
                "type": "ask_clarification",
                "parameters": {
                    "question": self._generate_clarification_question(nlp_result),
                    "suggestions": self._generate_suggestions(nlp_result)
                }
            })
        
        return actions
    
    def _generate_recommendations(
        self, decision_type: DecisionType, risk_level: str, session: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on decision and risk"""
        recommendations = []
        
        if risk_level == "high":
            recommendations.extend([
                "Double-check all parameters before execution",
                "Consider asking for user confirmation",
                "Log this interaction for review"
            ])
        
        if decision_type == DecisionType.EXECUTE_ACTION:
            recommendations.append("Monitor the action execution for any issues")
        
        if decision_type == DecisionType.ASK_CLARIFICATION:
            recommendations.append("Provide specific examples to help the user")
        
        if session.get("recent_errors", 0) > 0:
            recommendations.append("Consider providing additional guidance due to recent errors")
        
        return recommendations
    
    def _generate_reasoning(
        self, decision_type: DecisionType, risk_level: str, confidence: float
    ) -> str:
        """Generate reasoning for the decision"""
        reasoning_parts = [
            f"Decision type: {decision_type.value}",
            f"Risk level: {risk_level}",
            f"Confidence: {confidence:.2f}"
        ]
        
        if risk_level == "high":
            reasoning_parts.append("High risk detected, proceeding with caution")
        
        if confidence < 0.5:
            reasoning_parts.append("Low confidence, requesting clarification")
        
        return "; ".join(reasoning_parts)
    
    def _extract_system_type(self, entities: List[Any]) -> Optional[str]:
        """Extract system type from entities"""
        for entity in entities:
            if entity.type == "system_type":
                return entity.value
        return None
    
    def _extract_file_format(self, entities: List[Any]) -> Optional[str]:
        """Extract file format from entities"""
        for entity in entities:
            if entity.type == "file_format":
                return entity.value
        return "svgx"  # Default format
    
    def _extract_wallet_address(self, entities: List[Any]) -> Optional[str]:
        """Extract wallet address from entities"""
        for entity in entities:
            if entity.type == "wallet_address":
                return entity.value
        return None
    
    def _extract_object_data(self, entities: List[Any]) -> Dict[str, Any]:
        """Extract object data from entities"""
        object_data = {}
        for entity in entities:
            if entity.type in ["device_type", "system_type", "measurement"]:
                object_data[entity.type] = entity.value
        return object_data
    
    def _generate_clarification_question(self, nlp_result) -> str:
        """Generate clarification question"""
        if nlp_result.intent.value == "unknown":
            return "Could you please clarify what you'd like me to help you with?"
        elif nlp_result.intent.value == "create_drawing":
            return "What type of building system would you like to create a drawing for?"
        elif nlp_result.intent.value == "export_drawing":
            return "What format would you like to export your drawing in?"
        else:
            return "Could you provide more details about your request?"
    
    def _generate_suggestions(self, nlp_result) -> List[str]:
        """Generate suggestions for clarification"""
        suggestions = []
        
        if nlp_result.intent.value == "unknown":
            suggestions = [
                "Create a new drawing",
                "Edit an existing drawing", 
                "Export a drawing",
                "Get help with the platform",
                "Check BILT token balance"
            ]
        elif nlp_result.intent.value == "create_drawing":
            suggestions = [
                "Mechanical system",
                "Electrical system",
                "Plumbing system",
                "Fire protection system"
            ]
        elif nlp_result.intent.value == "export_drawing":
            suggestions = [
                "SVGX format",
                "SVG format", 
                "DXF format",
                "IFC format"
            ]
        
        return suggestions
    
    def _record_decision(
        self, result: DecisionResult, nlp_result, knowledge_result, session: Dict[str, Any]
    ):
        """Record decision for learning"""
        decision_record = {
            "timestamp": result.timestamp.isoformat(),
            "decision_type": result.decision_type.value,
            "confidence": result.confidence,
            "risk_level": result.risk_level,
            "intent": nlp_result.intent.value,
            "entities": [e.type for e in nlp_result.entities],
            "knowledge_items": len(knowledge_result.items),
            "session_context": session.get("conversation_history", [])[-3:]  # Last 3 interactions
        }
        
        self.decision_history.append(decision_record)
        
        # Keep only last 1000 decisions
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]
    
    async def train_models(self):
        """Train ML models with decision history"""
        if not ML_AVAILABLE or not self.intent_classifier:
            return
        
        try:
            if len(self.training_data) < 10:
                self.logger.info("Insufficient training data")
                return
            
            # Prepare training data
            X = self.text_vectorizer.fit_transform(self.training_data)
            y = self.training_labels
            
            # Train model
            self.intent_classifier.fit(X, y)
            
            self.logger.info("ML models trained successfully")
            
        except Exception as e:
            self.logger.error(f"Error training models: {e}")
    
    async def shutdown(self):
        """Shutdown decision engine"""
        try:
            # Save decision history
            # In practice, save to database or file
            self.logger.info("Decision Engine shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}") 