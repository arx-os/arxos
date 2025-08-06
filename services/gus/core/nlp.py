"""
GUS NLP Processor

Natural Language Processing component for the GUS agent.
Handles intent recognition, entity extraction, context management,
and response generation for Arxos platform queries.
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Try to import advanced NLP libraries
try:
    import spacy
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    ADVANCED_NLP_AVAILABLE = True
except ImportError:
    ADVANCED_NLP_AVAILABLE = False
    logging.warning("Advanced NLP libraries not available, using rule-based fallback")


class IntentType(Enum):
    """Intent types for Arxos platform queries"""
    
    # CAD and BIM operations
    CREATE_DRAWING = "create_drawing"
    EDIT_DRAWING = "edit_drawing"
    EXPORT_DRAWING = "export_drawing"
    IMPORT_DRAWING = "import_drawing"
    
    # Building systems
    ADD_DEVICE = "add_device"
    CONFIGURE_SYSTEM = "configure_system"
    ANALYZE_SYSTEM = "analyze_system"
    VALIDATE_SYSTEM = "validate_system"
    
    # Platform operations
    GET_HELP = "get_help"
    EXPLAIN_FEATURE = "explain_feature"
    SHOW_TUTORIAL = "show_tutorial"
    REPORT_ISSUE = "report_issue"
    
    # BILT operations
    CONTRIBUTE_BILT = "contribute_bilt"
    CLAIM_DIVIDENDS = "claim_dividends"
    CHECK_BALANCE = "check_balance"
    
    # General
    GREETING = "greeting"
    FAREWELL = "farewell"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Extracted entity from user query"""
    
    text: str
    type: str
    value: Any
    confidence: float
    start_pos: int
    end_pos: int


@dataclass
class NLPResult:
    """Result of NLP processing"""
    
    intent: IntentType
    confidence: float
    entities: List[Entity]
    original_text: str
    processed_text: str
    context: Dict[str, Any]
    timestamp: datetime


class NLPProcessor:
    """
    Natural Language Processing processor for GUS agent
    
    Handles:
    - Intent recognition for Arxos platform queries
    - Entity extraction for building objects, systems, etc.
    - Context management for multi-turn conversations
    - Response generation with confidence scoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize NLP processor
        
        Args:
            config: Configuration dictionary with model settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Intent patterns
        self.intent_patterns = self._initialize_intent_patterns()
        
        # Entity extraction patterns
        self.entity_patterns = self._initialize_entity_patterns()
        
        # Context management
        self.conversation_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Initialize advanced NLP if available
        if ADVANCED_NLP_AVAILABLE:
            self._initialize_advanced_nlp()
        else:
            self.logger.info("Using rule-based NLP fallback")
    
    def _initialize_advanced_nlp(self):
        """Initialize advanced NLP components"""
        try:
            # Load spaCy model for entity extraction
            self.nlp_model = spacy.load("en_core_web_sm")
            
            # Load intent classification model
            self.intent_classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
            
            self.logger.info("Advanced NLP components initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize advanced NLP: {e}")
            self.nlp_model = None
            self.intent_classifier = None
    
    def _initialize_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Initialize intent recognition patterns"""
        return {
            IntentType.CREATE_DRAWING: [
                r"create.*drawing", r"new.*drawing", r"start.*drawing",
                r"make.*drawing", r"begin.*drawing", r"draw.*new"
            ],
            IntentType.EDIT_DRAWING: [
                r"edit.*drawing", r"modify.*drawing", r"change.*drawing",
                r"update.*drawing", r"adjust.*drawing", r"fix.*drawing"
            ],
            IntentType.EXPORT_DRAWING: [
                r"export.*drawing", r"save.*as", r"download.*drawing",
                r"convert.*to", r"export.*to", r"save.*format"
            ],
            IntentType.IMPORT_DRAWING: [
                r"import.*drawing", r"load.*drawing", r"open.*file",
                r"upload.*drawing", r"bring.*in", r"add.*file"
            ],
            IntentType.ADD_DEVICE: [
                r"add.*device", r"insert.*device", r"place.*device",
                r"new.*device", r"install.*device", r"put.*device"
            ],
            IntentType.CONFIGURE_SYSTEM: [
                r"configure.*system", r"setup.*system", r"configure.*device",
                r"settings.*system", r"adjust.*system", r"tune.*system"
            ],
            IntentType.ANALYZE_SYSTEM: [
                r"analyze.*system", r"check.*system", r"inspect.*system",
                r"review.*system", r"examine.*system", r"test.*system"
            ],
            IntentType.VALIDATE_SYSTEM: [
                r"validate.*system", r"verify.*system", r"check.*compliance",
                r"validate.*code", r"verify.*standards", r"check.*requirements"
            ],
            IntentType.GET_HELP: [
                r"help", r"assist", r"support", r"guide", r"tutorial",
                r"how.*to", r"what.*is", r"explain", r"show.*me"
            ],
            IntentType.EXPLAIN_FEATURE: [
                r"explain.*feature", r"what.*does", r"how.*works",
                r"tell.*about", r"describe.*feature", r"show.*feature"
            ],
            IntentType.SHOW_TUTORIAL: [
                r"tutorial", r"guide", r"walkthrough", r"demo",
                r"show.*tutorial", r"learn.*how", r"step.*by.*step"
            ],
            IntentType.REPORT_ISSUE: [
                r"report.*issue", r"bug", r"problem", r"error",
                r"broken", r"not.*working", r"issue.*with"
            ],
            IntentType.CONTRIBUTE_BILT: [
                r"contribute.*bilt", r"mint.*bilt", r"earn.*bilt",
                r"add.*contribution", r"submit.*work", r"get.*bilt"
            ],
            IntentType.CLAIM_DIVIDENDS: [
                r"claim.*dividend", r"get.*dividend", r"collect.*dividend",
                r"withdraw.*dividend", r"claim.*reward", r"get.*reward"
            ],
            IntentType.CHECK_BALANCE: [
                r"check.*balance", r"show.*balance", r"my.*balance",
                r"bilt.*balance", r"token.*balance", r"wallet.*balance"
            ],
            IntentType.GREETING: [
                r"hello", r"hi", r"hey", r"good.*morning", r"good.*afternoon",
                r"good.*evening", r"greetings", r"welcome"
            ],
            IntentType.FAREWELL: [
                r"goodbye", r"bye", r"see.*you", r"farewell", r"exit",
                r"quit", r"end", r"stop"
            ]
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """Initialize entity extraction patterns"""
        return {
            "device_type": [
                r"hvac.*device", r"electrical.*device", r"plumbing.*device",
                r"fire.*protection.*device", r"security.*device", r"lighting.*device",
                r"av.*device", r"network.*device"
            ],
            "system_type": [
                r"mechanical.*system", r"electrical.*system", r"plumbing.*system",
                r"fire.*protection.*system", r"security.*system", r"lighting.*system",
                r"av.*system", r"network.*system"
            ],
            "file_format": [
                r"svgx", r"svg", r"dxf", r"dwg", r"ifc", r"pdf", r"png", r"jpg"
            ],
            "measurement": [
                r"\d+\.?\d*\s*(mm|cm|m|in|ft|yd)", r"\d+\.?\d*\s*(degrees?|deg)",
                r"\d+\.?\d*\s*(volts?|v)", r"\d+\.?\d*\s*(amps?|a)"
            ],
            "location": [
                r"room.*\d+", r"floor.*\d+", r"building.*\d+", r"level.*\d+",
                r"zone.*\d+", r"area.*\d+"
            ],
            "wallet_address": [
                r"0x[a-fA-F0-9]{40}", r"wallet.*address", r"account.*address"
            ],
            "bilt_amount": [
                r"\d+\.?\d*\s*bilt", r"\d+\.?\d*\s*tokens?", r"\d+\.?\d*\s*coins?"
            ]
        }
    
    async def process(
        self, text: str, session: Optional[Dict[str, Any]] = None
    ) -> NLPResult:
        """
        Process natural language text
        
        Args:
            text: Input text to process
            session: User session context
            
        Returns:
            NLPResult: Processed result with intent, entities, etc.
        """
        try:
            # Normalize text
            processed_text = self._normalize_text(text)
            
            # Recognize intent
            intent, confidence = await self._recognize_intent(processed_text)
            
            # Extract entities
            entities = await self._extract_entities(processed_text)
            
            # Update context
            context = self._update_context(session, intent, entities)
            
            return NLPResult(
                intent=intent,
                confidence=confidence,
                entities=entities,
                original_text=text,
                processed_text=processed_text,
                context=context,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing NLP: {e}")
            return NLPResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities=[],
                original_text=text,
                processed_text=text,
                context={},
                timestamp=datetime.utcnow()
            )
    
    def _normalize_text(self, text: str) -> str:
        """Normalize input text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove punctuation (keep some for entity extraction)
        text = re.sub(r'[^\w\s\.\,\-\+\=\&\|\<\>]', '', text)
        
        return text
    
    async def _recognize_intent(self, text: str) -> Tuple[IntentType, float]:
        """Recognize intent from text"""
        if ADVANCED_NLP_AVAILABLE and self.intent_classifier:
            return await self._recognize_intent_advanced(text)
        else:
            return self._recognize_intent_rule_based(text)
    
    async def _recognize_intent_advanced(self, text: str) -> Tuple[IntentType, float]:
        """Recognize intent using advanced NLP"""
        try:
            # Use transformer model for intent classification
            results = self.intent_classifier(text)
            
            # Map model outputs to our intent types
            # This is a simplified mapping - in practice you'd train a custom model
            if "create" in text or "new" in text or "draw" in text:
                return IntentType.CREATE_DRAWING, 0.9
            elif "edit" in text or "modify" in text or "change" in text:
                return IntentType.EDIT_DRAWING, 0.9
            elif "export" in text or "save" in text or "download" in text:
                return IntentType.EXPORT_DRAWING, 0.9
            elif "import" in text or "load" in text or "upload" in text:
                return IntentType.IMPORT_DRAWING, 0.9
            elif "help" in text or "assist" in text or "support" in text:
                return IntentType.GET_HELP, 0.9
            else:
                return IntentType.UNKNOWN, 0.5
                
        except Exception as e:
            self.logger.warning(f"Advanced intent recognition failed: {e}")
            return self._recognize_intent_rule_based(text)
    
    def _recognize_intent_rule_based(self, text: str) -> Tuple[IntentType, float]:
        """Recognize intent using rule-based patterns"""
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    confidence = len(re.findall(pattern, text, re.IGNORECASE)) / len(text.split())
                    if confidence > best_confidence:
                        best_intent = intent_type
                        best_confidence = confidence
        
        return best_intent, min(best_confidence, 1.0)
    
    async def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text"""
        entities = []
        
        if ADVANCED_NLP_AVAILABLE and self.nlp_model:
            entities.extend(await self._extract_entities_advanced(text))
        
        # Add rule-based entity extraction
        entities.extend(self._extract_entities_rule_based(text))
        
        return entities
    
    async def _extract_entities_advanced(self, text: str) -> List[Entity]:
        """Extract entities using advanced NLP"""
        try:
            doc = self.nlp_model(text)
            entities = []
            
            for ent in doc.ents:
                entity_type = self._map_spacy_entity_type(ent.label_)
                entities.append(Entity(
                    text=ent.text,
                    type=entity_type,
                    value=ent.text,
                    confidence=0.8,
                    start_pos=ent.start_char,
                    end_pos=ent.end_char
                ))
            
            return entities
            
        except Exception as e:
            self.logger.warning(f"Advanced entity extraction failed: {e}")
            return []
    
    def _extract_entities_rule_based(self, text: str) -> List[Entity]:
        """Extract entities using rule-based patterns"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append(Entity(
                        text=match.group(),
                        type=entity_type,
                        value=match.group(),
                        confidence=0.7,
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))
        
        return entities
    
    def _map_spacy_entity_type(self, spacy_type: str) -> str:
        """Map spaCy entity types to our entity types"""
        mapping = {
            "PERSON": "person",
            "ORG": "organization",
            "GPE": "location",
            "LOC": "location",
            "PRODUCT": "device_type",
            "QUANTITY": "measurement",
            "MONEY": "bilt_amount",
            "CARDINAL": "number"
        }
        return mapping.get(spacy_type, "unknown")
    
    def _update_context(
        self, session: Optional[Dict[str, Any]], intent: IntentType, entities: List[Entity]
    ) -> Dict[str, Any]:
        """Update conversation context"""
        if session is None:
            session = {}
        
        # Update context with current intent and entities
        context = session.copy()
        context["last_intent"] = intent.value
        context["last_entities"] = [e.type for e in entities]
        context["last_timestamp"] = datetime.utcnow().isoformat()
        
        # Track conversation history
        if "conversation_history" not in context:
            context["conversation_history"] = []
        
        context["conversation_history"].append({
            "intent": intent.value,
            "entities": [e.type for e in entities],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 10 interactions
        if len(context["conversation_history"]) > 10:
            context["conversation_history"] = context["conversation_history"][-10:]
        
        return context
    
    async def generate_response(
        self, intent: IntentType, entities: List[Entity], context: Dict[str, Any]
    ) -> str:
        """Generate natural language response"""
        # This would typically use a language model
        # For now, return template responses
        
        response_templates = {
            IntentType.CREATE_DRAWING: "I'll help you create a new drawing. What type of building system would you like to work on?",
            IntentType.EDIT_DRAWING: "I can help you edit your drawing. What specific changes would you like to make?",
            IntentType.EXPORT_DRAWING: "I'll help you export your drawing. What format would you prefer (SVG, DXF, IFC)?",
            IntentType.IMPORT_DRAWING: "I can help you import a drawing. What file format is it in?",
            IntentType.ADD_DEVICE: "I'll help you add a device to your drawing. What type of device do you want to add?",
            IntentType.CONFIGURE_SYSTEM: "I can help you configure the system. What specific settings would you like to adjust?",
            IntentType.ANALYZE_SYSTEM: "I'll analyze the system for you. What aspects would you like me to check?",
            IntentType.VALIDATE_SYSTEM: "I'll validate the system against building codes and standards. What type of validation do you need?",
            IntentType.GET_HELP: "I'm here to help! What specific assistance do you need with the Arxos platform?",
            IntentType.EXPLAIN_FEATURE: "I'd be happy to explain that feature. What would you like to know about it?",
            IntentType.SHOW_TUTORIAL: "I'll show you a tutorial for that feature. What would you like to learn about?",
            IntentType.REPORT_ISSUE: "I can help you report that issue. What specific problem are you experiencing?",
            IntentType.CONTRIBUTE_BILT: "I can help you contribute to earn BILT tokens. What building object would you like to contribute?",
            IntentType.CLAIM_DIVIDENDS: "I'll help you claim your BILT dividends. Let me check your wallet balance.",
            IntentType.CHECK_BALANCE: "I'll check your BILT token balance for you. Let me retrieve that information.",
            IntentType.GREETING: "Hello! I'm GUS, your Arxos platform assistant. How can I help you today?",
            IntentType.FAREWELL: "Goodbye! Feel free to ask for help anytime. Have a great day!",
            IntentType.UNKNOWN: "I'm not sure I understood that. Could you rephrase your request or ask for help?"
        }
        
        return response_templates.get(intent, response_templates[IntentType.UNKNOWN]) 