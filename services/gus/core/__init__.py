"""
GUS (General User Support) Agent Core Module

This module contains the core functionality for the GUS AI agent,
including natural language processing, knowledge management,
and decision engine components.
"""

from .agent import GUSAgent
from .nlp import NLPProcessor
from .knowledge import KnowledgeManager
from .decision import DecisionEngine
from .learning import LearningSystem

__version__ = "1.0.0"
__author__ = "Arxos Team"

__all__ = [
    "GUSAgent",
    "NLPProcessor", 
    "KnowledgeManager",
    "DecisionEngine",
    "LearningSystem"
] 