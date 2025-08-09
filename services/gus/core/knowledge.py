"""
Custom Knowledge Manager for GUS

Custom knowledge management implementation for PDF analysis
and system schedule generation. Built specifically for Arxos without
external dependencies.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class KnowledgeResult:
    """Result from knowledge query"""
    summary: str
    confidence: float
    details: Dict[str, Any]
    sources: List[str]


class KnowledgeManager:
    """
    Custom Knowledge Manager for GUS

    Handles knowledge queries for PDF analysis and system schedule generation.
    Built without external dependencies using custom knowledge base.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize knowledge manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Custom knowledge base
        self.knowledge_base = {
            'pdf_analysis': {
                'summary': 'PDF analysis extracts system components from architectural drawings',
                'confidence': 0.9,
                'details': {
                    'process': 'Upload PDF → Extract content → Recognize symbols → Generate schedule',
                    'supported_formats': ['PDF'],
                    'max_file_size': '50MB',
                    'processing_time': '2-5 minutes'
                },
                'sources': ['Arxos PDF Analysis System']
            },
            'system_schedule': {
                'summary': 'System schedule organizes building components by system type',
                'confidence': 0.9,
                'details': {
                    'architectural': 'Walls, doors, windows, rooms',
                    'mechanical': 'HVAC ducts, equipment, vents, controls',
                    'electrical': 'Outlets, panels, lighting, circuits',
                    'plumbing': 'Fixtures, pipes, valves, drains',
                    'technology': 'AV systems, telecom, security'
                },
                'sources': ['Arxos System Classification']
            },
            'cost_estimation': {
                'summary': 'Cost estimation calculates project costs based on system components',
                'confidence': 0.8,
                'details': {
                    'architectural_cost': '$50 per linear foot for walls',
                    'mechanical_cost': '$25 per linear foot for ducts',
                    'electrical_cost': '$150 per outlet',
                    'plumbing_cost': '$500 per fixture',
                    'technology_cost': '$200 per component'
                },
                'sources': ['Arxos Cost Database']
            },
            'timeline_generation': {
                'summary': 'Timeline generation estimates project duration based on system complexity',
                'confidence': 0.8,
                'details': {
                    'architectural_time': '2 days per component',
                    'mechanical_time': '3 days per component',
                    'electrical_time': '2.5 days per component',
                    'plumbing_time': '2.5 days per component',
                    'technology_time': '1.5 days per component'
                },
                'sources': ['Arxos Timeline Database']
            },
            'symbol_recognition': {
                'summary': 'Symbol recognition identifies architectural and MEP symbols in PDFs',
                'confidence': 0.85,
                'details': {
                    'wall_symbols': 'Thick lines, double lines, solid rectangles',
                    'door_symbols': 'Rectangles with swing indicators',
                    'hvac_symbols': 'Rectangles for ducts, circles for vents',
                    'electrical_symbols': 'Circles with plus signs for outlets',
                    'plumbing_symbols': 'Rectangles for fixtures, lines for pipes'
                },
                'sources': ['Arxos Symbol Library']
            },
            'quality_assurance': {
                'summary': 'Quality assurance validates analysis results for completeness and accuracy',
                'confidence': 0.9,
                'details': {
                    'confidence_threshold': '0.7 minimum confidence',
                    'completeness_check': 'Verify all expected systems found',
                    'accuracy_validation': 'Cross-reference with symbol library',
                    'consistency_check': 'Ensure spatial relationships are valid'
                },
                'sources': ['Arxos Quality Standards']
            }
        }

        # Query patterns for intent matching
        self.query_patterns = {
            'pdf_analysis': ['pdf', 'analysis', 'extract', 'process'],
            'system_schedule': ['schedule', 'system', 'component', 'organize'],
            'cost_estimation': ['cost', 'estimate', 'budget', 'price'],
            'timeline_generation': ['timeline', 'schedule', 'duration', 'time'],
            'symbol_recognition': ['symbol', 'recognize', 'identify', 'pattern'],
            'quality_assurance': ['quality', 'validate', 'check', 'assure']
        }

        self.logger.info("Custom Knowledge Manager initialized")

    async def query(self, intent: str, entities: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> KnowledgeResult:
        """
        Query knowledge base

        Args:
            intent: Query intent
            entities: Extracted entities
            context: Additional context

        Returns:
            KnowledgeResult: Knowledge query result
        """
        try:
            # Determine knowledge topic
            topic = self._determine_topic(intent, entities)

            # Get knowledge for topic
            knowledge = self.knowledge_base.get(topic, self._get_default_knowledge())

            # Enhance with context
            enhanced_knowledge = self._enhance_with_context(knowledge, context)

            return KnowledgeResult(
                summary=enhanced_knowledge['summary'],
                confidence=enhanced_knowledge['confidence'],
                details=enhanced_knowledge['details'],
                sources=enhanced_knowledge['sources']
            )

        except Exception as e:
            self.logger.error(f"Error querying knowledge: {e}")
            return KnowledgeResult(
                summary="Unable to retrieve knowledge",
                confidence=0.0,
                details={},
                sources=[]
            )

    def _determine_topic(self, intent: str, entities: Dict[str, Any]) -> str:
        """Determine knowledge topic from intent and entities"""
        # Direct intent mapping
        intent_mapping = {
            'pdf_analysis': 'pdf_analysis',
            'schedule_generation': 'system_schedule',
            'cost_estimation': 'cost_estimation',
            'timeline_generation': 'timeline_generation',
            'status_check': 'quality_assurance',
            'export_request': 'system_schedule'
        }

        # Check direct intent mapping
        if intent in intent_mapping:
            return intent_mapping[intent]

        # Check entities for topic hints
        if 'systems' in entities:
            return 'system_schedule'

        if 'cost' in entities or 'estimate' in entities:
            return 'cost_estimation'

        if 'timeline' in entities or 'schedule' in entities:
            return 'timeline_generation'

        if 'quality' in entities or 'validate' in entities:
            return 'quality_assurance'

        # Default to PDF analysis
        return 'pdf_analysis'

    def _get_default_knowledge(self) -> Dict[str, Any]:
        """Get default knowledge when topic not found"""
        return {
            'summary': 'General information about Arxos PDF analysis system',
            'confidence': 0.5,
            'details': {
                'system': 'Arxos PDF Analysis System',
                'capabilities': 'PDF processing, symbol recognition, schedule generation',
                'status': 'Operational'
            },
            'sources': ['Arxos System Documentation']
        }

    def _enhance_with_context(self, knowledge: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance knowledge with context information"""
        enhanced = knowledge.copy()

        if context:
            # Add context-specific details
            if 'file_size' in context:
                enhanced['details']['file_size'] = context['file_size']

            if 'systems_found' in context:
                enhanced['details']['systems_found'] = context['systems_found']

            if 'processing_time' in context:
                enhanced['details']['actual_processing_time'] = context['processing_time']

            # Adjust confidence based on context
            if 'confidence' in context:
                enhanced['confidence'] = min(enhanced['confidence'], context['confidence'])

        return enhanced

    def get_available_topics(self) -> List[str]:
        """Get list of available knowledge topics"""
        return list(self.knowledge_base.keys())

    def get_topic_summary(self, topic: str) -> str:
        """Get summary for specific topic"""
        knowledge = self.knowledge_base.get(topic)
        if knowledge:
            return knowledge['summary']
        return "Topic not found"

    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        results = []
        query_lower = query.lower()

        for topic, knowledge in self.knowledge_base.items():
            # Check if query matches topic
            if query_lower in topic.lower():
                results.append({
                    'topic': topic,
                    'summary': knowledge['summary'],
                    'confidence': knowledge['confidence']
                })

            # Check if query matches summary
            elif query_lower in knowledge['summary'].lower():
                results.append({
                    'topic': topic,
                    'summary': knowledge['summary'],
                    'confidence': knowledge['confidence']
                })

            # Check if query matches details
            else:
                for key, value in knowledge['details'].items():
                    if isinstance(value, str) and query_lower in value.lower():
                        results.append({
                            'topic': topic,
                            'summary': knowledge['summary'],
                            'confidence': knowledge['confidence'] * 0.8  # Lower confidence for detail match
                        })
                        break

        return results

    def add_knowledge(self, topic: str, knowledge: Dict[str, Any]) -> bool:
        """Add new knowledge to the knowledge base"""
        try:
            self.knowledge_base[topic] = knowledge
            self.logger.info(f"Added knowledge for topic: {topic}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding knowledge: {e}")
            return False

    def update_knowledge(self, topic: str, updates: Dict[str, Any]) -> bool:
        """Update existing knowledge"""
        try:
            if topic in self.knowledge_base:
                self.knowledge_base[topic].update(updates)
                self.logger.info(f"Updated knowledge for topic: {topic}")
                return True
            else:
                self.logger.warning(f"Topic not found: {topic}")
                return False
        except Exception as e:
            self.logger.error(f"Error updating knowledge: {e}")
            return False
