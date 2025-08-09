"""
NLP Engine

Natural Language Processing engine for text analysis, intent detection,
and language understanding in the Arxos platform.
"""

import asyncio
from typing import Dict, Any, List, Optional
import spacy
import nltk
from textblob import TextBlob
import structlog

logger = structlog.get_logger()


class NLPEngine:
    """Natural Language Processing engine for text analysis"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the NLP engine"""
        self.config = config
        self.logger = structlog.get_logger(__name__)

        # Initialize NLP models
        self._init_nlp_models()

        # Intent patterns for CAD/BIM domain
        self.intent_patterns = {
            "create": ["create", "make", "build", "generate", "add"],
            "modify": ["modify", "change", "edit", "update", "adjust"],
            "delete": ["delete", "remove", "erase", "clear"],
            "query": ["query", "find", "search", "locate", "get"],
            "validate": ["validate", "check", "verify", "test"],
            "export": ["export", "save", "output", "download"],
            "import": ["import", "load", "upload", "read"],
            "measure": ["measure", "calculate", "compute", "size"],
            "analyze": ["analyze", "examine", "study", "investigate"],
            "visualize": ["visualize", "show", "display", "render"]
        }

        self.logger.info("NLP Engine initialized")

    def _init_nlp_models(self):
        """Initialize NLP models and download required data"""
        try:
            # Download NLTK data
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')

            try:
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                nltk.download('averaged_perceptron_tagger')

            # Load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning("spaCy model not found, using basic tokenization")
                self.nlp = None

        except Exception as e:
            self.logger.error(f"Error initializing NLP models: {e}")
            self.nlp = None

    async def process_query(
        self,
        query: str,
        context: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """Process natural language query"""
        try:
            self.logger.info(f"Processing NLP query: {query[:50]}...")

            # Basic text analysis
            text_analysis = await self._analyze_text(query)

            # Intent detection
            intent_analysis = await self._detect_intent(query)

            # Entity extraction
            entity_analysis = await self._extract_entities(query)

            # Sentiment analysis
            sentiment_analysis = await self._analyze_sentiment(query)

            # Domain-specific analysis for CAD/BIM
            domain_analysis = await self._analyze_domain_context(query, context)

            return {
                "success": True,
                "text_analysis": text_analysis,
                "intent_analysis": intent_analysis,
                "entity_analysis": entity_analysis,
                "sentiment_analysis": sentiment_analysis,
                "domain_analysis": domain_analysis,
                "timestamp": asyncio.get_event_loop().time()
            }

        except Exception as e:
            self.logger.error(f"Error processing NLP query: {e}")
            return {
                "success": False,
                "error": str(e),
                "text_analysis": {},
                "intent_analysis": {},
                "entity_analysis": {},
                "sentiment_analysis": {},
                "domain_analysis": {}
            }

    async def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Perform basic text analysis"""
        try:
            analysis = {
                "length": len(text),
                "word_count": len(text.split()),
                "sentence_count": len(text.split('.')),
                "average_word_length": 0,
                "unique_words": 0
            }

            words = text.split()
            if words:
                analysis["average_word_length"] = sum(len(word) for word in words) / len(words)
                analysis["unique_words"] = len(set(words))

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing text: {e}")
            return {"error": str(e)}

    async def _detect_intent(self, text: str) -> Dict[str, Any]:
        """Detect user intent from text"""
        try:
            text_lower = text.lower()
            detected_intents = []

            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        detected_intents.append({
                            "intent": intent,
                            "pattern": pattern,
                            "confidence": 0.8
                        })
                        break

            # Sort by confidence
            detected_intents.sort(key=lambda x: x["confidence"], reverse=True)

            return {
                "primary_intent": detected_intents[0]["intent"] if detected_intents else "unknown",
                "all_intents": detected_intents,
                "confidence": detected_intents[0]["confidence"] if detected_intents else 0.0
            }

        except Exception as e:
            self.logger.error(f"Error detecting intent: {e}")
            return {
                "primary_intent": "unknown",
                "all_intents": [],
                "confidence": 0.0,
                "error": str(e)
            }

    async def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract named entities from text"""
        try:
            entities = []

            if self.nlp:
                doc = self.nlp(text)

                for ent in doc.ents:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })

            # Extract CAD/BIM specific entities
            cad_entities = await self._extract_cad_entities(text)

            return {
                "general_entities": entities,
                "cad_entities": cad_entities,
                "total_entities": len(entities) + len(cad_entities)
            }

        except Exception as e:
            self.logger.error(f"Error extracting entities: {e}")
            return {
                "general_entities": [],
                "cad_entities": [],
                "total_entities": 0,
                "error": str(e)
            }

    async def _extract_cad_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract CAD/BIM specific entities"""
        cad_entities = []

        # CAD/BIM specific keywords
        cad_keywords = {
            "geometry": ["point", "line", "circle", "rectangle", "polygon", "curve", "surface"],
            "dimension": ["length", "width", "height", "depth", "radius", "diameter"],
            "material": ["steel", "concrete", "wood", "glass", "plastic", "aluminum"],
            "operation": ["extrude", "revolve", "sweep", "loft", "fillet", "chamfer"],
            "view": ["front", "back", "top", "bottom", "left", "right", "isometric"],
            "unit": ["mm", "cm", "m", "inch", "feet", "yard"]
        }

        text_lower = text.lower()

        for category, keywords in cad_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    cad_entities.append({
                        "text": keyword,
                        "category": category,
                        "confidence": 0.9
                    })

        return cad_entities

    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        try:
            blob = TextBlob(text)

            return {
                "polarity": blob.sentiment.polarity,
                "subjectivity": blob.sentiment.subjectivity,
                "sentiment": "positive" if blob.sentiment.polarity > 0 else "negative" if blob.sentiment.polarity < 0 else "neutral"
            }

        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "sentiment": "neutral",
                "error": str(e)
            }

    async def _analyze_domain_context(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze domain-specific context for CAD/BIM"""
        try:
            domain_analysis = {
                "is_cad_query": False,
                "is_bim_query": False,
                "suggested_actions": [],
                "domain_keywords": []
            }

            text_lower = text.lower()

            # CAD keywords
            cad_keywords = ["draw", "sketch", "model", "design", "geometry", "shape"]
            if any(keyword in text_lower for keyword in cad_keywords):
                domain_analysis["is_cad_query"] = True
                domain_analysis["domain_keywords"].extend([k for k in cad_keywords if k in text_lower])

            # BIM keywords
            bim_keywords = ["building", "construction", "floor", "wall", "room", "component"]
            if any(keyword in text_lower for keyword in bim_keywords):
                domain_analysis["is_bim_query"] = True
                domain_analysis["domain_keywords"].extend([k for k in bim_keywords if k in text_lower])

            # Suggest actions based on context
            if domain_analysis["is_cad_query"]:
                domain_analysis["suggested_actions"].extend([
                    "create_geometry", "modify_shape", "export_drawing"
                ])

            if domain_analysis["is_bim_query"]:
                domain_analysis["suggested_actions"].extend([
                    "create_component", "modify_building", "export_model"
                ])

            return domain_analysis

        except Exception as e:
            self.logger.error(f"Error analyzing domain context: {e}")
            return {
                "is_cad_query": False,
                "is_bim_query": False,
                "suggested_actions": [],
                "domain_keywords": [],
                "error": str(e)
            }

    async def execute_task(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute NLP-related tasks"""
        try:
            if task == "analyze":
                return await self.process_query(
                    parameters.get("text", ""),
                    parameters.get("context", {})
                )
            elif task == "detect_intent":
                text = parameters.get("text", "")
                intent_result = await self._detect_intent(text)
                return {
                    "intent": intent_result["primary_intent"],
                    "confidence": intent_result["confidence"],
                    "all_intents": intent_result["all_intents"]
                }
            elif task == "extract_entities":
                text = parameters.get("text", "")
                entity_result = await self._extract_entities(text)
                return entity_result
            elif task == "analyze_sentiment":
                text = parameters.get("text", "")
                sentiment_result = await self._analyze_sentiment(text)
                return sentiment_result
            else:
                return {
                    "error": f"Unknown NLP task: {task}",
                    "available_tasks": ["analyze", "detect_intent", "extract_entities", "analyze_sentiment"]
                }

        except Exception as e:
            self.logger.error(f"Error executing NLP task: {e}")
            return {"error": str(e)}
