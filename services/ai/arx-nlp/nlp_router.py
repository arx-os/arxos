"""
NLP Router Engine for Arxos Platform

This module provides the core NLP routing functionality to parse natural language inputs
and convert them to structured ArxCLI instructions or queries. It includes intent detection,
slot-filling logic, and contextual object resolution.

Key Features:
- Intent detection with confidence scoring
- Slot filling for command parameters
- Contextual object resolution
- ArxCLI command generation
- Query translation for building data access
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .intent_detection.intent_detector import IntentDetector
from .slot_filling.slot_filler import SlotFiller
from .cli_translation.cli_translator import CLITranslator
from .models.nlp_models import NLPRequest, NLPResponse, Intent, Slot, CLICommand
from .utils.context_manager import ContextManager


class IntentType(Enum):
    """Supported intent types for building operations"""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    MOVE = "move"
    QUERY = "query"
    EXPORT = "export"
    IMPORT = "import"
    VALIDATE = "validate"
    SYNC = "sync"
    ANNOTATE = "annotate"
    INSPECT = "inspect"
    REPORT = "report"


class ObjectType(Enum):
    """Building object types that can be referenced"""
    ROOM = "room"
    WALL = "wall"
    DOOR = "door"
    WINDOW = "window"
    FIXTURE = "fixture"
    EQUIPMENT = "equipment"
    SYSTEM = "system"
    FLOOR = "floor"
    BUILDING = "building"
    SITE = "site"


@dataclass
class NLPContext:
    """Context information for NLP processing"""
    user_id: Optional[str] = None
    building_id: Optional[str] = None
    floor_id: Optional[str] = None
    session_id: Optional[str] = None
    previous_commands: List[str] = field(default_factory=list)
    object_context: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)


class NLPRouter:
    """
    Main NLP Router for converting natural language to ArxCLI commands
    
    This class orchestrates the entire NLP pipeline:
    1. Intent detection
    2. Slot filling
    3. Context resolution
    4. CLI command generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NLP Router
        
        Args:
            config: Configuration dictionary for NLP components
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.intent_detector = IntentDetector(config.get('intent_detection', {}))
        self.slot_filler = SlotFiller(config.get('slot_filling', {}))
        self.cli_translator = CLITranslator(config.get('cli_translation', {}))
        self.context_manager = ContextManager(config.get('context', {}))
        
        # Load patterns and rules
        self._load_patterns()
        self._load_object_mappings()
        
    def _load_patterns(self):
        """Load NLP patterns for intent detection"""
        self.nlp_patterns = {
            IntentType.CREATE: [
                r'create\s+(\w+)',
                r'add\s+(\w+)',
                r'new\s+(\w+)',
                r'build\s+(\w+)',
                r'generate\s+(\w+)'
            ],
            IntentType.MODIFY: [
                r'modify\s+(\w+)',
                r'change\s+(\w+)',
                r'update\s+(\w+)',
                r'edit\s+(\w+)',
                r'adjust\s+(\w+)'
            ],
            IntentType.DELETE: [
                r'delete\s+(\w+)',
                r'remove\s+(\w+)',
                r'destroy\s+(\w+)',
                r'eliminate\s+(\w+)'
            ],
            IntentType.MOVE: [
                r'move\s+(\w+)',
                r'relocate\s+(\w+)',
                r'transfer\s+(\w+)',
                r'reposition\s+(\w+)'
            ],
            IntentType.QUERY: [
                r'find\s+(\w+)',
                r'search\s+for\s+(\w+)',
                r'locate\s+(\w+)',
                r'where\s+is\s+(\w+)',
                r'what\s+(\w+)'
            ],
            IntentType.EXPORT: [
                r'export\s+(\w+)',
                r'save\s+(\w+)',
                r'download\s+(\w+)',
                r'backup\s+(\w+)'
            ],
            IntentType.IMPORT: [
                r'import\s+(\w+)',
                r'load\s+(\w+)',
                r'upload\s+(\w+)',
                r'bring\s+in\s+(\w+)'
            ],
            IntentType.VALIDATE: [
                r'validate\s+(\w+)',
                r'check\s+(\w+)',
                r'verify\s+(\w+)',
                r'test\s+(\w+)'
            ],
            IntentType.SYNC: [
                r'sync\s+(\w+)',
                r'synchronize\s+(\w+)',
                r'update\s+(\w+)',
                r'push\s+(\w+)'
            ],
            IntentType.ANNOTATE: [
                r'annotate\s+(\w+)',
                r'note\s+(\w+)',
                r'comment\s+on\s+(\w+)',
                r'mark\s+(\w+)'
            ],
            IntentType.INSPECT: [
                r'inspect\s+(\w+)',
                r'examine\s+(\w+)',
                r'review\s+(\w+)',
                r'look\s+at\s+(\w+)'
            ],
            IntentType.REPORT: [
                r'report\s+(\w+)',
                r'generate\s+report\s+(\w+)',
                r'summary\s+(\w+)',
                r'status\s+(\w+)'
            ]
        }
        
    def _load_object_mappings(self):
        """Load object type mappings for contextual resolution"""
        self.object_mappings = {
            'room': ObjectType.ROOM,
            'bedroom': ObjectType.ROOM,
            'bathroom': ObjectType.ROOM,
            'kitchen': ObjectType.ROOM,
            'living': ObjectType.ROOM,
            'office': ObjectType.ROOM,
            'wall': ObjectType.WALL,
            'door': ObjectType.DOOR,
            'window': ObjectType.WINDOW,
            'fixture': ObjectType.FIXTURE,
            'equipment': ObjectType.EQUIPMENT,
            'system': ObjectType.SYSTEM,
            'floor': ObjectType.FLOOR,
            'building': ObjectType.BUILDING,
            'site': ObjectType.SITE
        }
        
    def parse_natural_language(self, text: str, context: Optional[NLPContext] = None) -> NLPResponse:
        """
        Parse natural language input and convert to structured command
        
        Args:
            text: Natural language input text
            context: Optional context information
            
        Returns:
            NLPResponse with parsed intent, slots, and CLI command
        """
        try:
            self.logger.info(f"Processing NLP input: {text}")
            
            # Initialize context if not provided
            if context is None:
                context = NLPContext()
            
            # Step 1: Intent Detection
            intent_result = self.intent_detector.detect_intent(text, self.nlp_patterns)
            
            # Step 2: Slot Filling
            slot_result = self.slot_filler.extract_slots(text, intent_result.intent_type)
            
            # Step 3: Context Resolution
            resolved_context = self.context_manager.resolve_context(
                intent_result, slot_result, context
            )
            
            # Step 4: CLI Command Generation
            cli_command = self.cli_translator.generate_command(
                intent_result, slot_result, resolved_context
            )
            
            # Create response
            response = NLPResponse(
                original_text=text,
                intent=intent_result,
                slots=slot_result.slots,
                cli_command=cli_command,
                confidence=intent_result.confidence,
                context=resolved_context,
                timestamp=datetime.now()
            )
            
            self.logger.info(f"NLP processing completed with confidence: {intent_result.confidence}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing NLP input: {e}")
            return self._create_error_response(text, str(e))
    
    def _create_error_response(self, text: str, error: str) -> NLPResponse:
        """Create error response for failed NLP processing"""
        return NLPResponse(
            original_text=text,
            intent=Intent(
                intent_type=IntentType.QUERY,
                confidence=0.0,
                raw_text=text
            ),
            slots=[],
            cli_command=CLICommand(
                command="help",
                arguments=["--error", error],
                options={}
            ),
            confidence=0.0,
            context=NLPContext(),
            timestamp=datetime.now(),
            error=error
        )
    
    def batch_process(self, texts: List[str], context: Optional[NLPContext] = None) -> List[NLPResponse]:
        """
        Process multiple natural language inputs in batch
        
        Args:
            texts: List of natural language inputs
            context: Optional context information
            
        Returns:
            List of NLPResponse objects
        """
        results = []
        for text in texts:
            result = self.parse_natural_language(text, context)
            results.append(result)
        return results
    
    def get_suggestions(self, partial_text: str, context: Optional[NLPContext] = None) -> List[str]:
        """
        Get command suggestions based on partial input
        
        Args:
            partial_text: Partial natural language input
            context: Optional context information
            
        Returns:
            List of suggested completions
        """
        suggestions = []
        
        # Get intent suggestions
        intent_suggestions = self.intent_detector.get_suggestions(partial_text)
        suggestions.extend(intent_suggestions)
        
        # Get object suggestions
        object_suggestions = self._get_object_suggestions(partial_text)
        suggestions.extend(object_suggestions)
        
        # Get parameter suggestions
        param_suggestions = self.slot_filler.get_suggestions(partial_text)
        suggestions.extend(param_suggestions)
        
        return list(set(suggestions))[:10]  # Limit to 10 unique suggestions
    
    def _get_object_suggestions(self, partial_text: str) -> List[str]:
        """Get object type suggestions based on partial text"""
        suggestions = []
        partial_lower = partial_text.lower()
        
        for obj_name, obj_type in self.object_mappings.items():
            if obj_name.startswith(partial_lower) or partial_lower in obj_name:
                suggestions.append(f"create {obj_name}")
                suggestions.append(f"modify {obj_name}")
                suggestions.append(f"delete {obj_name}")
        
        return suggestions
    
    def validate_command(self, cli_command: CLICommand) -> bool:
        """
        Validate generated CLI command
        
        Args:
            cli_command: CLI command to validate
            
        Returns:
            True if command is valid, False otherwise
        """
        return self.cli_translator.validate_command(cli_command)
    
    def get_help(self, topic: Optional[str] = None) -> str:
        """
        Get help information for NLP commands
        
        Args:
            topic: Optional specific topic for help
            
        Returns:
            Help text
        """
        if topic is None:
            return self._get_general_help()
        else:
            return self._get_topic_help(topic)
    
    def _get_general_help(self) -> str:
        """Get general help information"""
        help_text = """
NLP Router Help

Supported Commands:
- create <object>: Create new building objects
- modify <object>: Modify existing objects
- delete <object>: Delete objects
- move <object>: Move objects
- query <object>: Query object information
- export <object>: Export object data
- import <object>: Import object data
- validate <object>: Validate object compliance
- sync <object>: Synchronize object data
- annotate <object>: Add annotations
- inspect <object>: Inspect object details
- report <object>: Generate reports

Examples:
- "create a bedroom"
- "modify the kitchen layout"
- "find all doors on floor 2"
- "export the building plan"
- "validate electrical systems"

For specific help, use: get_help("topic")
"""
        return help_text
    
    def _get_topic_help(self, topic: str) -> str:
        """Get help for specific topic"""
        topic_help = {
            "create": "Create commands: create <object_type> [parameters]",
            "modify": "Modify commands: modify <object> [parameters]",
            "query": "Query commands: query <object> [filters]",
            "export": "Export commands: export <object> [format]",
            "sync": "Sync commands: sync <object> [target]"
        }
        return topic_help.get(topic.lower(), f"No help available for topic: {topic}")


# Convenience function for quick NLP processing
def process_nlp_input(text: str, config: Optional[Dict[str, Any]] = None) -> NLPResponse:
    """
    Convenience function for quick NLP processing
    
    Args:
        text: Natural language input
        config: Optional configuration
        
    Returns:
        NLPResponse with parsed command
    """
    router = NLPRouter(config)
    return router.parse_natural_language(text)


if __name__ == "__main__":
    # Example usage
    router = NLPRouter()
    
    # Test NLP processing
    test_inputs = [
        "create a bedroom",
        "modify the kitchen layout",
        "find all doors on floor 2",
        "export the building plan",
        "validate electrical systems"
    ]
    
    for text in test_inputs:
        result = router.parse_natural_language(text)
        print(f"Input: {text}")
        print(f"Intent: {result.intent.intent_type}")
        print(f"Confidence: {result.confidence}")
        print(f"CLI Command: {result.cli_command.command} {' '.join(result.cli_command.arguments)}")
        print("-" * 50) 