"""
Custom NLP Processor for GUS

Custom natural language processing implementation for PDF analysis
and system schedule generation. Built specifically for Arxos without
external dependencies.
"""

import logging
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class NLPResult:
    """Result from NLP processing"""
    intent: str
    entities: Dict[str, Any]
    confidence: float
    message: str


class NLPProcessor:
    """
    Custom NLP Processor for GUS
    
    Handles natural language understanding for PDF analysis requests
    and system schedule generation. Built without external dependencies.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize NLP processor"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Custom intent patterns
        self.intent_patterns = {
            'pdf_analysis': [
                r'analyze.*pdf',
                r'process.*pdf',
                r'extract.*from.*pdf',
                r'generate.*schedule.*from.*pdf',
                r'upload.*pdf.*for.*analysis'
            ],
            'schedule_generation': [
                r'generate.*schedule',
                r'create.*schedule',
                r'build.*schedule',
                r'system.*schedule'
            ],
            'cost_estimation': [
                r'estimate.*cost',
                r'calculate.*cost',
                r'cost.*analysis',
                r'budget.*estimate'
            ],
            'timeline_generation': [
                r'generate.*timeline',
                r'create.*timeline',
                r'schedule.*timeline',
                r'project.*timeline'
            ],
            'status_check': [
                r'check.*status',
                r'get.*status',
                r'analysis.*status',
                r'task.*status'
            ],
            'export_request': [
                r'export.*schedule',
                r'download.*schedule',
                r'export.*results',
                r'get.*export'
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'file_type': r'\.(pdf|PDF)',
            'file_size': r'(\d+)\s*(MB|GB|KB)',
            'system_type': r'(architectural|mechanical|electrical|plumbing|technology)',
            'confidence_level': r'(high|medium|low)\s*confidence',
            'export_format': r'(json|csv|pdf|excel)',
            'task_id': r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
        }
        
        self.logger.info("Custom NLP Processor initialized")
    
    async def process(self, query: str, session: Dict[str, Any]) -> NLPResult:
        """
        Process natural language query
        
        Args:
            query: User's natural language query
            session: User session context
            
        Returns:
            NLPResult: Processed query result
        """
        try:
            # Normalize query
            normalized_query = self._normalize_query(query)
            
            # Extract intent
            intent, intent_confidence = self._extract_intent(normalized_query)
            
            # Extract entities
            entities = self._extract_entities(normalized_query)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(intent_confidence, entities)
            
            # Generate response message
            message = self._generate_response_message(intent, entities)
            
            return NLPResult(
                intent=intent,
                entities=entities,
                confidence=confidence,
                message=message
            )
            
        except Exception as e:
            self.logger.error(f"Error processing NLP query: {e}")
            return NLPResult(
                intent="error",
                entities={},
                confidence=0.0,
                message=f"Error processing query: {str(e)}"
            )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for processing"""
        # Convert to lowercase
        normalized = query.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove punctuation (except for patterns we want to keep)
        normalized = re.sub(r'[^\w\s\-\.]', ' ', normalized)
        
        return normalized.strip()
    
    def _extract_intent(self, query: str) -> tuple[str, float]:
        """Extract intent from query"""
        best_intent = "unknown"
        best_confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    # Calculate confidence based on pattern match
                    confidence = self._calculate_pattern_confidence(pattern, query)
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
        
        return best_intent, best_confidence
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query)
            if matches:
                entities[entity_type] = matches
        
        # Extract custom entities
        entities.update(self._extract_custom_entities(query))
        
        return entities
    
    def _extract_custom_entities(self, query: str) -> Dict[str, Any]:
        """Extract custom entities specific to PDF analysis"""
        custom_entities = {}
        
        # Extract system requirements
        system_keywords = {
            'architectural': ['wall', 'door', 'window', 'room'],
            'mechanical': ['hvac', 'duct', 'vent', 'equipment'],
            'electrical': ['outlet', 'panel', 'light', 'circuit'],
            'plumbing': ['fixture', 'pipe', 'valve', 'drain'],
            'technology': ['av', 'telecom', 'security', 'network']
        }
        
        for system_type, keywords in system_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    if 'systems' not in custom_entities:
                        custom_entities['systems'] = []
                    if system_type not in custom_entities['systems']:
                        custom_entities['systems'].append(system_type)
        
        # Extract analysis requirements
        if 'cost' in query or 'estimate' in query:
            custom_entities['include_cost_estimation'] = True
        
        if 'timeline' in query or 'schedule' in query:
            custom_entities['include_timeline'] = True
        
        if 'export' in query or 'download' in query:
            custom_entities['include_export'] = True
        
        return custom_entities
    
    def _calculate_pattern_confidence(self, pattern: str, query: str) -> float:
        """Calculate confidence for pattern match"""
        # Base confidence for pattern match
        base_confidence = 0.7
        
        # Boost confidence for exact matches
        if pattern in query:
            base_confidence += 0.2
        
        # Boost confidence for longer patterns
        pattern_length = len(pattern.split())
        if pattern_length > 2:
            base_confidence += 0.1
        
        # Reduce confidence for partial matches
        if not re.search(pattern, query):
            base_confidence -= 0.3
        
        return min(base_confidence, 1.0)
    
    def _calculate_confidence(self, intent_confidence: float, entities: Dict[str, Any]) -> float:
        """Calculate overall confidence"""
        # Base confidence from intent
        confidence = intent_confidence
        
        # Boost confidence if we found relevant entities
        if entities:
            entity_boost = min(len(entities) * 0.1, 0.3)
            confidence += entity_boost
        
        # Reduce confidence for unknown intent
        if intent_confidence < 0.3:
            confidence *= 0.5
        
        return min(confidence, 1.0)
    
    def _generate_response_message(self, intent: str, entities: Dict[str, Any]) -> str:
        """Generate response message based on intent"""
        messages = {
            'pdf_analysis': 'I understand you want to analyze a PDF for system schedule generation.',
            'schedule_generation': 'I will help you generate a system schedule.',
            'cost_estimation': 'I will include cost estimation in the analysis.',
            'timeline_generation': 'I will generate a timeline for the project.',
            'status_check': 'I will check the status of your analysis.',
            'export_request': 'I will help you export the results.',
            'unknown': 'I\'m not sure what you\'re asking for. Could you clarify?',
            'error': 'I encountered an error processing your request.'
        }
        
        return messages.get(intent, messages['unknown'])
    
    def get_supported_intents(self) -> list[str]:
        """Get list of supported intents"""
        return list(self.intent_patterns.keys())
    
    def get_supported_entities(self) -> list[str]:
        """Get list of supported entity types"""
        return list(self.entity_patterns.keys()) 