"""
Custom Learning System for GUS

Custom learning implementation for PDF analysis
and system schedule generation. Built specifically for Arxos without
external dependencies.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LearningData:
    """Learning data point"""
    timestamp: str
    user_id: str
    intent: str
    entities: Dict[str, Any]
    confidence: float
    success: bool
    feedback: Optional[str] = None


class LearningSystem:
    """
    Custom Learning System for GUS

    Handles learning from user interactions and system performance.
    Built without external dependencies using custom learning algorithms.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize learning system"""
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Learning data storage
        self.learning_data: List[LearningData] = []

        # Performance metrics
        self.performance_metrics = {
            'total_interactions': 0,
            'successful_interactions': 0,
            'average_confidence': 0.0,
            'intent_accuracy': {},
            'user_satisfaction': {}
        }

        # Learning patterns
        self.learning_patterns = {
            'confidence_threshold': 0.7,
            'success_threshold': 0.8,
            'learning_rate': 0.1,
            'min_data_points': 10
        }

        # User preference learning
        self.user_preferences = {}

        # System optimization data
        self.optimization_data = {
            'processing_times': [],
            'accuracy_improvements': [],
            'user_feedback': []
        }

        self.logger.info("Custom Learning System initialized")

    async def update(
        self,
        query: str,
        response: Any,
        user_id: str,
        session: Dict[str, Any]
    ) -> bool:
        """
        Update learning system with interaction data

        Args:
            query: User query
            response: System response
            user_id: User identifier
            session: User session context

        Returns:
            bool: Success status
        """
        try:
            # Extract learning data
            learning_data = self._extract_learning_data(query, response, user_id, session)

            # Store learning data
            self.learning_data.append(learning_data)

            # Update performance metrics
            self._update_performance_metrics(learning_data)

            # Learn user preferences
            self._learn_user_preferences(learning_data, session)

            # Update system optimization data
            self._update_optimization_data(learning_data)

            # Apply learning improvements
            self._apply_learning_improvements()

            self.logger.info(f"Learning system updated for user: {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating learning system: {e}")
            return False

    def _extract_learning_data(
        self,
        query: str,
        response: Any,
        user_id: str,
        session: Dict[str, Any]
    ) -> LearningData:
        """Extract learning data from interaction"""
        # Extract intent and confidence from response import response
        intent = getattr(response, 'intent', 'unknown')
        confidence = getattr(response, 'confidence', 0.0)

        # Extract entities from response import response
        entities = getattr(response, 'entities', {})

        # Determine success based on confidence and user feedback
        success = confidence >= self.learning_patterns['confidence_threshold']

        # Extract feedback if available
        feedback = session.get('feedback', None)

        return LearningData(
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            intent=intent,
            entities=entities,
            confidence=confidence,
            success=success,
            feedback=feedback
        )

    def _update_performance_metrics(self, learning_data: LearningData):
        """Update performance metrics with new data"""
        self.performance_metrics['total_interactions'] += 1

        if learning_data.success:
            self.performance_metrics['successful_interactions'] += 1

        # Update average confidence
        total_confidence = sum(data.confidence for data in self.learning_data)
        self.performance_metrics['average_confidence'] = total_confidence / len(self.learning_data)

        # Update intent accuracy
        intent = learning_data.intent
        if intent not in self.performance_metrics['intent_accuracy']:
            self.performance_metrics['intent_accuracy'][intent] = {
                'total': 0,
                'successful': 0,
                'accuracy': 0.0
            }

        self.performance_metrics['intent_accuracy'][intent]['total'] += 1
        if learning_data.success:
            self.performance_metrics['intent_accuracy'][intent]['successful'] += 1

        # Calculate accuracy
        intent_data = self.performance_metrics['intent_accuracy'][intent]
        intent_data['accuracy'] = intent_data['successful'] / intent_data['total']

    def _learn_user_preferences(self, learning_data: LearningData, session: Dict[str, Any]):
        """Learn user preferences from interaction"""
        user_id = learning_data.user_id

        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'preferred_intents': {},
                'confidence_preferences': {},
                'response_preferences': {},
                'interaction_patterns': []
            }

        user_prefs = self.user_preferences[user_id]

        # Learn preferred intents
        intent = learning_data.intent
        if intent not in user_prefs['preferred_intents']:
            user_prefs['preferred_intents'][intent] = 0
        user_prefs['preferred_intents'][intent] += 1

        # Learn confidence preferences
        confidence_level = 'high' if learning_data.confidence >= 0.8 else 'medium' if learning_data.confidence >= 0.6 else 'low'
        if confidence_level not in user_prefs['confidence_preferences']:
            user_prefs['confidence_preferences'][confidence_level] = 0
        user_prefs['confidence_preferences'][confidence_level] += 1

        # Learn response preferences
        if learning_data.success:
            user_prefs['response_preferences']['successful'] = user_prefs['response_preferences'].get('successful', 0) + 1
        else:
            user_prefs['response_preferences']['failed'] = user_prefs['response_preferences'].get('failed', 0) + 1

        # Store interaction pattern
        pattern = {
            'timestamp': learning_data.timestamp,
            'intent': intent,
            'confidence': learning_data.confidence,
            'success': learning_data.success
        }
        user_prefs['interaction_patterns'].append(pattern)

        # Keep only recent patterns (last 50)
        if len(user_prefs['interaction_patterns']) > 50:
            user_prefs['interaction_patterns'] = user_prefs['interaction_patterns'][-50:]

    def _update_optimization_data(self, learning_data: LearningData):
        """Update system optimization data"""
        # Store processing time if available
        if hasattr(learning_data, 'processing_time'):
            self.optimization_data['processing_times'].append(learning_data.processing_time)

        # Store accuracy improvements
        if learning_data.success:
            self.optimization_data['accuracy_improvements'].append({
                'timestamp': learning_data.timestamp,
                'confidence': learning_data.confidence,
                'intent': learning_data.intent
            })

        # Store user feedback
        if learning_data.feedback:
            self.optimization_data['user_feedback'].append({
                'timestamp': learning_data.timestamp,
                'feedback': learning_data.feedback,
                'success': learning_data.success
            })

    def _apply_learning_improvements(self):
        """Apply learning improvements based on collected data"""
        if len(self.learning_data) < self.learning_patterns['min_data_points']:
            return

        # Adjust confidence thresholds based on success rate
        success_rate = self.performance_metrics['successful_interactions'] / self.performance_metrics['total_interactions']

        if success_rate < 0.7:
            # Lower confidence threshold if success rate is low
            self.learning_patterns['confidence_threshold'] = max(0.5, self.learning_patterns['confidence_threshold'] - 0.05)
        elif success_rate > 0.9:
            # Raise confidence threshold if success rate is high
            self.learning_patterns['confidence_threshold'] = min(0.9, self.learning_patterns['confidence_threshold'] + 0.05)

        # Optimize based on user preferences
        self._optimize_based_on_preferences()

    def _optimize_based_on_preferences(self):
        """Optimize system based on learned user preferences"""
        for user_id, preferences in self.user_preferences.items():
            # Find most preferred intent
            preferred_intent = max(preferences['preferred_intents'].items(), key=lambda x: x[1])[0]

            # Find preferred confidence level
            preferred_confidence = max(preferences['confidence_preferences'].items(), key=lambda x: x[1])[0]

            # Store optimization data
            self.optimization_data[f'user_{user_id}_preferences'] = {
                'preferred_intent': preferred_intent,
                'preferred_confidence': preferred_confidence,
                'success_rate': preferences['response_preferences'].get('successful', 0) / max(sum(preferences['response_preferences'].values()), 1)
            }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()

    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        return self.user_preferences.get(user_id)

    def get_optimization_data(self) -> Dict[str, Any]:
        """Get system optimization data"""
        return self.optimization_data.copy()

    def get_learning_patterns(self) -> Dict[str, Any]:
        """Get current learning patterns"""
        return self.learning_patterns.copy()

    def save_learning_data(self, file_path: str) -> bool:
        """Save learning data to file"""
        try:
            data = {
                'learning_data': [data.__dict__ for data in self.learning_data],
                'performance_metrics': self.performance_metrics,
                'user_preferences': self.user_preferences,
                'optimization_data': self.optimization_data,
                'learning_patterns': self.learning_patterns
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Learning data saved to: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")
            return False

    def load_learning_data(self, file_path: str) -> bool:
        """Load learning data from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Restore learning data
            self.learning_data = [LearningData(**item) for item in data.get('learning_data', [])]

            # Restore performance metrics
            self.performance_metrics = data.get('performance_metrics', self.performance_metrics)

            # Restore user preferences
            self.user_preferences = data.get('user_preferences', {})

            # Restore optimization data
            self.optimization_data = data.get('optimization_data', self.optimization_data)

            # Restore learning patterns
            self.learning_patterns = data.get('learning_patterns', self.learning_patterns)

            self.logger.info(f"Learning data loaded from: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading learning data: {e}")
            return False

    def reset_learning_data(self):
        """Reset all learning data"""
        self.learning_data.clear()
        self.performance_metrics = {
            'total_interactions': 0,
            'successful_interactions': 0,
            'average_confidence': 0.0,
            'intent_accuracy': {},
            'user_satisfaction': {}
        }
        self.user_preferences.clear()
        self.optimization_data = {
            'processing_times': [],
            'accuracy_improvements': [],
            'user_feedback': []
        }

        self.logger.info("Learning data reset")

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get learning system summary"""
        return {
            'total_interactions': len(self.learning_data),
            'success_rate': self.performance_metrics['successful_interactions'] / max(self.performance_metrics['total_interactions'], 1),
            'average_confidence': self.performance_metrics['average_confidence'],
            'unique_users': len(self.user_preferences),
            'top_intents': self._get_top_intents(),
            'recent_improvements': self._get_recent_improvements()
        }

    def _get_top_intents(self) -> List[Dict[str, Any]]:
        """Get top intents by usage"""
        intent_counts = {}
        for data in self.learning_data:
            intent_counts[data.intent] = intent_counts.get(data.intent, 0) + 1

        return [{'intent': intent, 'count': count} for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    def _get_recent_improvements(self) -> List[Dict[str, Any]]:
        """Get recent learning improvements"""
        recent_data = self.learning_data[-10:] if len(self.learning_data) >= 10 else self.learning_data

        improvements = []
        for data in recent_data:
            if data.success and data.confidence > 0.8:
                improvements.append({
                    'timestamp': data.timestamp,
                    'intent': data.intent,
                    'confidence': data.confidence
                })

        return improvements
