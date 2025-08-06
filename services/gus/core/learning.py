"""
GUS Learning System

Learning system component for the GUS agent.
Handles continuous learning, model training, performance monitoring,
and knowledge updates for adaptive intelligence.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import hashlib

# Try to import ML libraries
try:
    import numpy as np
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available, using basic learning metrics")


@dataclass
class LearningMetrics:
    """Learning performance metrics"""
    
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    validation_samples: int
    model_version: str
    timestamp: datetime


@dataclass
class LearningEvent:
    """Learning event for continuous improvement"""
    
    event_id: str
    event_type: str
    user_query: str
    predicted_intent: str
    actual_intent: str
    confidence: float
    user_feedback: Optional[str]
    success: bool
    timestamp: datetime


class LearningSystem:
    """
    Learning System for GUS agent
    
    Handles:
    - Continuous learning from user interactions
    - Model performance monitoring and retraining
    - Knowledge base updates and improvements
    - Adaptive response generation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize learning system
        
        Args:
            config: Configuration dictionary with learning settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Learning database
        self.learning_db_path = config.get("learning_db_path", "gus_learning.db")
        self._initialize_learning_db()
        
        # Performance tracking
        self.performance_metrics = self._initialize_performance_metrics()
        
        # Learning thresholds
        self.retraining_threshold = config.get("retraining_threshold", 0.8)
        self.min_training_samples = config.get("min_training_samples", 100)
        self.learning_rate = config.get("learning_rate", 0.1)
        
        # Model versioning
        self.current_model_version = "1.0.0"
        self.model_history: List[Dict[str, Any]] = []
        
        self.logger.info("Learning System initialized successfully")
    
    def _initialize_learning_db(self):
        """Initialize SQLite learning database"""
        try:
            self.conn = sqlite3.connect(self.learning_db_path)
            self.cursor = self.conn.cursor()
            
            # Create learning events table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_query TEXT NOT NULL,
                    predicted_intent TEXT NOT NULL,
                    actual_intent TEXT,
                    confidence REAL NOT NULL,
                    user_feedback TEXT,
                    success INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create performance metrics table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id TEXT PRIMARY KEY,
                    model_version TEXT NOT NULL,
                    accuracy REAL NOT NULL,
                    precision REAL NOT NULL,
                    recall REAL NOT NULL,
                    f1_score REAL NOT NULL,
                    training_samples INTEGER NOT NULL,
                    validation_samples INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create knowledge updates table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_updates (
                    update_id TEXT PRIMARY KEY,
                    knowledge_item_id TEXT NOT NULL,
                    update_type TEXT NOT NULL,
                    old_content TEXT,
                    new_content TEXT,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.commit()
            self.logger.info("Learning database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize learning database: {e}")
    
    def _initialize_performance_metrics(self) -> Dict[str, Any]:
        """Initialize performance tracking metrics"""
        return {
            "intent_accuracy": 0.0,
            "entity_extraction_accuracy": 0.0,
            "response_satisfaction": 0.0,
            "user_feedback_score": 0.0,
            "total_interactions": 0,
            "successful_interactions": 0,
            "failed_interactions": 0,
            "last_updated": datetime.utcnow()
        }
    
    async def record_learning_event(
        self, user_query: str, predicted_intent: str, actual_intent: Optional[str] = None,
        confidence: float = 0.0, user_feedback: Optional[str] = None, success: bool = True
    ) -> bool:
        """
        Record a learning event
        
        Args:
            user_query: User's original query
            predicted_intent: Intent predicted by the system
            actual_intent: Actual intent (if known)
            confidence: Prediction confidence
            user_feedback: User feedback (if provided)
            success: Whether the interaction was successful
            
        Returns:
            bool: Success status
        """
        try:
            event_id = hashlib.md5(f"{user_query}{predicted_intent}{datetime.utcnow()}".encode()).hexdigest()
            
            # Insert learning event
            self.cursor.execute("""
                INSERT INTO learning_events 
                (event_id, event_type, user_query, predicted_intent, actual_intent, 
                 confidence, user_feedback, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (event_id, "intent_prediction", user_query, predicted_intent, actual_intent,
                  confidence, user_feedback, 1 if success else 0))
            
            self.conn.commit()
            
            # Update performance metrics
            await self._update_performance_metrics(success, confidence)
            
            # Check if retraining is needed
            await self._check_retraining_needed()
            
            self.logger.info(f"Recorded learning event: {event_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record learning event: {e}")
            return False
    
    async def _update_performance_metrics(self, success: bool, confidence: float):
        """Update performance metrics"""
        self.performance_metrics["total_interactions"] += 1
        
        if success:
            self.performance_metrics["successful_interactions"] += 1
        else:
            self.performance_metrics["failed_interactions"] += 1
        
        # Update accuracy
        self.performance_metrics["intent_accuracy"] = (
            self.performance_metrics["successful_interactions"] / 
            self.performance_metrics["total_interactions"]
        )
        
        # Update confidence tracking
        if "confidence_scores" not in self.performance_metrics:
            self.performance_metrics["confidence_scores"] = []
        
        self.performance_metrics["confidence_scores"].append(confidence)
        
        # Keep only last 1000 confidence scores
        if len(self.performance_metrics["confidence_scores"]) > 1000:
            self.performance_metrics["confidence_scores"] = self.performance_metrics["confidence_scores"][-1000:]
        
        self.performance_metrics["last_updated"] = datetime.utcnow()
    
    async def _check_retraining_needed(self):
        """Check if model retraining is needed"""
        if self.performance_metrics["total_interactions"] < self.min_training_samples:
            return
        
        # Check if accuracy is below threshold
        if self.performance_metrics["intent_accuracy"] < self.retraining_threshold:
            self.logger.info("Performance below threshold, triggering retraining")
            await self.trigger_retraining()
    
    async def trigger_retraining(self) -> bool:
        """
        Trigger model retraining
        
        Returns:
            bool: Success status
        """
        try:
            # Get recent learning events for training
            recent_events = await self._get_recent_learning_events(limit=1000)
            
            if len(recent_events) < self.min_training_samples:
                self.logger.info("Insufficient training data for retraining")
                return False
            
            # Prepare training data
            training_data = await self._prepare_training_data(recent_events)
            
            # Train new model (this would integrate with the NLP processor)
            new_model_version = await self._train_new_model(training_data)
            
            # Evaluate new model
            metrics = await self._evaluate_model(new_model_version, training_data)
            
            # Save performance metrics
            await self._save_performance_metrics(metrics)
            
            # Update model version if improvement is significant
            if metrics.accuracy > self.performance_metrics["intent_accuracy"] + 0.05:
                self.current_model_version = new_model_version
                self.model_history.append({
                    "version": new_model_version,
                    "accuracy": metrics.accuracy,
                    "timestamp": datetime.utcnow()
                })
                
                self.logger.info(f"Model updated to version {new_model_version}")
                return True
            else:
                self.logger.info("New model did not show significant improvement")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during retraining: {e}")
            return False
    
    async def _get_recent_learning_events(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent learning events"""
        try:
            self.cursor.execute("""
                SELECT event_id, user_query, predicted_intent, actual_intent, 
                       confidence, user_feedback, success, timestamp
                FROM learning_events 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = self.cursor.fetchall()
            events = []
            
            for row in rows:
                events.append({
                    "event_id": row[0],
                    "user_query": row[1],
                    "predicted_intent": row[2],
                    "actual_intent": row[3],
                    "confidence": row[4],
                    "user_feedback": row[5],
                    "success": bool(row[6]),
                    "timestamp": datetime.fromisoformat(row[7])
                })
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get learning events: {e}")
            return []
    
    async def _prepare_training_data(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare training data from learning events"""
        training_data = {
            "texts": [],
            "intents": [],
            "confidences": [],
            "success_labels": []
        }
        
        for event in events:
            training_data["texts"].append(event["user_query"])
            training_data["intents"].append(event["predicted_intent"])
            training_data["confidences"].append(event["confidence"])
            training_data["success_labels"].append(1 if event["success"] else 0)
        
        return training_data
    
    async def _train_new_model(self, training_data: Dict[str, Any]) -> str:
        """Train new model with training data"""
        # This would integrate with the NLP processor's model training
        # For now, return a new version string
        new_version = f"{self.current_model_version}.{len(self.model_history) + 1}"
        
        self.logger.info(f"Training new model version: {new_version}")
        
        # In practice, this would:
        # 1. Update the NLP processor's intent classification model
        # 2. Update the decision engine's ML models
        # 3. Save the new model weights
        
        return new_version
    
    async def _evaluate_model(self, model_version: str, training_data: Dict[str, Any]) -> LearningMetrics:
        """Evaluate model performance"""
        # Split data for evaluation
        split_index = int(len(training_data["texts"]) * 0.8)
        
        train_texts = training_data["texts"][:split_index]
        train_labels = training_data["success_labels"][:split_index]
        val_texts = training_data["texts"][split_index:]
        val_labels = training_data["success_labels"][split_index:]
        
        # Calculate metrics (simplified)
        accuracy = sum(train_labels) / len(train_labels) if train_labels else 0.0
        precision = accuracy  # Simplified
        recall = accuracy  # Simplified
        f1_score = accuracy  # Simplified
        
        return LearningMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            training_samples=len(train_texts),
            validation_samples=len(val_texts),
            model_version=model_version,
            timestamp=datetime.utcnow()
        )
    
    async def _save_performance_metrics(self, metrics: LearningMetrics):
        """Save performance metrics to database"""
        try:
            metric_id = hashlib.md5(f"{metrics.model_version}{metrics.timestamp}".encode()).hexdigest()
            
            self.cursor.execute("""
                INSERT INTO performance_metrics 
                (metric_id, model_version, accuracy, precision, recall, f1_score,
                 training_samples, validation_samples)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (metric_id, metrics.model_version, metrics.accuracy, metrics.precision,
                  metrics.recall, metrics.f1_score, metrics.training_samples, metrics.validation_samples))
            
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to save performance metrics: {e}")
    
    async def update_knowledge_base(
        self, knowledge_item_id: str, update_type: str, 
        old_content: Optional[str] = None, new_content: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Update knowledge base with new information
        
        Args:
            knowledge_item_id: ID of the knowledge item to update
            update_type: Type of update (add, modify, remove)
            old_content: Previous content (if modifying)
            new_content: New content
            reason: Reason for the update
            
        Returns:
            bool: Success status
        """
        try:
            update_id = hashlib.md5(f"{knowledge_item_id}{update_type}{datetime.utcnow()}".encode()).hexdigest()
            
            # Record knowledge update
            self.cursor.execute("""
                INSERT INTO knowledge_updates 
                (update_id, knowledge_item_id, update_type, old_content, new_content, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (update_id, knowledge_item_id, update_type, old_content, new_content, reason))
            
            self.conn.commit()
            
            self.logger.info(f"Recorded knowledge update: {update_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update knowledge base: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    async def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        try:
            # Get total events
            self.cursor.execute("SELECT COUNT(*) FROM learning_events")
            total_events = self.cursor.fetchone()[0]
            
            # Get recent events (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            self.cursor.execute("""
                SELECT COUNT(*) FROM learning_events 
                WHERE timestamp > ?
            """, (yesterday.isoformat(),))
            recent_events = self.cursor.fetchone()[0]
            
            # Get success rate
            self.cursor.execute("""
                SELECT COUNT(*) FROM learning_events 
                WHERE success = 1
            """)
            successful_events = self.cursor.fetchone()[0]
            
            success_rate = successful_events / total_events if total_events > 0 else 0.0
            
            return {
                "total_events": total_events,
                "recent_events_24h": recent_events,
                "success_rate": success_rate,
                "current_model_version": self.current_model_version,
                "model_history_count": len(self.model_history),
                "performance_metrics": self.performance_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get learning statistics: {e}")
            return {}
    
    async def get_model_history(self) -> List[Dict[str, Any]]:
        """Get model version history"""
        return self.model_history.copy()
    
    async def export_learning_data(self, output_path: str) -> bool:
        """
        Export learning data for analysis
        
        Args:
            output_path: Path to export file
            
        Returns:
            bool: Success status
        """
        try:
            # Get all learning events
            events = await self._get_recent_learning_events(limit=10000)
            
            # Get performance metrics
            self.cursor.execute("""
                SELECT model_version, accuracy, precision, recall, f1_score, 
                       training_samples, validation_samples, timestamp
                FROM performance_metrics 
                ORDER BY timestamp DESC
            """)
            
            metrics_rows = self.cursor.fetchall()
            metrics = []
            
            for row in metrics_rows:
                metrics.append({
                    "model_version": row[0],
                    "accuracy": row[1],
                    "precision": row[2],
                    "recall": row[3],
                    "f1_score": row[4],
                    "training_samples": row[5],
                    "validation_samples": row[6],
                    "timestamp": row[7]
                })
            
            # Export to JSON
            export_data = {
                "learning_events": events,
                "performance_metrics": metrics,
                "current_performance": self.performance_metrics,
                "model_history": self.model_history,
                "export_timestamp": datetime.utcnow().isoformat()
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Learning data exported to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export learning data: {e}")
            return False
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """
        Clean up old learning data
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            bool: Success status
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old learning events
            self.cursor.execute("""
                DELETE FROM learning_events 
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            # Delete old performance metrics (keep only last 10 versions)
            self.cursor.execute("""
                DELETE FROM performance_metrics 
                WHERE metric_id NOT IN (
                    SELECT metric_id FROM performance_metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                )
            """)
            
            self.conn.commit()
            
            self.logger.info(f"Cleaned up learning data older than {days_to_keep} days")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown learning system"""
        try:
            # Save current state
            await self.export_learning_data("gus_learning_backup.json")
            
            # Close database connection
            if hasattr(self, 'conn'):
                self.conn.close()
            
            self.logger.info("Learning System shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}") 