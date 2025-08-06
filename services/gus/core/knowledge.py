"""
GUS Knowledge Manager

Knowledge management component for the GUS agent.
Handles building codes, engineering standards, platform documentation,
and historical data for intelligent assistance.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3
import hashlib

# Try to import vector database libraries
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False
    logging.warning("Vector database libraries not available, using simple search")


@dataclass
class KnowledgeItem:
    """Knowledge base item"""
    
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    source: str
    confidence: float
    last_updated: datetime


@dataclass
class KnowledgeResult:
    """Result of knowledge base query"""
    
    items: List[KnowledgeItem]
    total_count: int
    query: str
    categories: List[str]
    confidence: float


class KnowledgeManager:
    """
    Knowledge Manager for GUS agent
    
    Handles:
    - Building codes and standards
    - Engineering specifications
    - Platform documentation
    - Historical data and case studies
    - Semantic search and retrieval
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize knowledge manager
        
        Args:
            config: Configuration dictionary with knowledge base settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Knowledge base storage
        self.knowledge_db_path = config.get("knowledge_db_path", "gus_knowledge.db")
        self.vector_db_path = config.get("vector_db_path", "gus_vectors.npz")
        
        # Initialize knowledge base
        self._initialize_knowledge_base()
        
        # Initialize vector database if available
        if VECTOR_DB_AVAILABLE:
            self._initialize_vector_db()
        
        # Load knowledge categories
        self.categories = self._initialize_categories()
        
        self.logger.info("Knowledge Manager initialized successfully")
    
    def _initialize_knowledge_base(self):
        """Initialize SQLite knowledge base"""
        try:
            self.conn = sqlite3.connect(self.knowledge_db_path)
            self.cursor = self.conn.cursor()
            
            # Create knowledge table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT,
                    source TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create search index
            self.cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_search 
                USING fts5(id, title, content, category, tags)
            """)
            
            self.conn.commit()
            self.logger.info("Knowledge base initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize knowledge base: {e}")
    
    def _initialize_vector_db(self):
        """Initialize vector database for semantic search"""
        try:
            # Load sentence transformer model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Load or create vector database
            if Path(self.vector_db_path).exists():
                vectors_data = np.load(self.vector_db_path)
                self.vectors = vectors_data['vectors']
                self.vector_ids = vectors_data['ids']
            else:
                self.vectors = np.array([])
                self.vector_ids = []
            
            self.logger.info("Vector database initialized")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize vector database: {e}")
            self.embedding_model = None
    
    def _initialize_categories(self) -> Dict[str, Dict[str, Any]]:
        """Initialize knowledge categories"""
        return {
            "building_codes": {
                "name": "Building Codes",
                "description": "International, national, and local building codes",
                "subcategories": [
                    "structural_codes",
                    "mechanical_codes", 
                    "electrical_codes",
                    "plumbing_codes",
                    "fire_codes",
                    "accessibility_codes"
                ]
            },
            "engineering_standards": {
                "name": "Engineering Standards",
                "description": "Industry standards and best practices",
                "subcategories": [
                    "ashrae_standards",
                    "nfpa_standards",
                    "ieee_standards",
                    "astm_standards",
                    "iso_standards"
                ]
            },
            "platform_documentation": {
                "name": "Platform Documentation",
                "description": "Arxos platform documentation and guides",
                "subcategories": [
                    "svgx_engine",
                    "browser_cad",
                    "arxide",
                    "api_documentation",
                    "cli_tools",
                    "bilt_token"
                ]
            },
            "cad_bim_knowledge": {
                "name": "CAD/BIM Knowledge",
                "description": "Computer-aided design and building information modeling",
                "subcategories": [
                    "drawing_techniques",
                    "modeling_methods",
                    "export_formats",
                    "import_formats",
                    "precision_standards"
                ]
            },
            "building_systems": {
                "name": "Building Systems",
                "description": "Building system specifications and requirements",
                "subcategories": [
                    "mechanical_systems",
                    "electrical_systems", 
                    "plumbing_systems",
                    "fire_protection_systems",
                    "security_systems",
                    "av_systems"
                ]
            },
            "case_studies": {
                "name": "Case Studies",
                "description": "Real-world project examples and lessons learned",
                "subcategories": [
                    "commercial_buildings",
                    "residential_buildings",
                    "industrial_facilities",
                    "healthcare_facilities",
                    "educational_buildings"
                ]
            }
        }
    
    async def query(
        self, intent: str, entities: List[Any], context: Optional[Dict[str, Any]] = None
    ) -> KnowledgeResult:
        """
        Query knowledge base
        
        Args:
            intent: User intent
            entities: Extracted entities
            context: Additional context
            
        Returns:
            KnowledgeResult: Relevant knowledge items
        """
        try:
            # Build search query from intent and entities
            query = self._build_search_query(intent, entities, context)
            
            # Perform search
            if VECTOR_DB_AVAILABLE and self.embedding_model:
                items = await self._semantic_search(query)
            else:
                items = await self._keyword_search(query)
            
            # Filter by categories if specified
            if context and "categories" in context:
                items = [item for item in items if item.category in context["categories"]]
            
            # Calculate confidence
            confidence = self._calculate_confidence(items, query)
            
            return KnowledgeResult(
                items=items,
                total_count=len(items),
                query=query,
                categories=list(set(item.category for item in items)),
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Error querying knowledge base: {e}")
            return KnowledgeResult(
                items=[],
                total_count=0,
                query="",
                categories=[],
                confidence=0.0
            )
    
    def _build_search_query(self, intent: str, entities: List[Any], context: Optional[Dict[str, Any]]) -> str:
        """Build search query from intent and entities"""
        query_parts = [intent]
        
        # Add entity information
        for entity in entities:
            query_parts.append(entity.text)
        
        # Add context information
        if context:
            if "last_intent" in context:
                query_parts.append(context["last_intent"])
            if "conversation_history" in context:
                # Add recent conversation topics
                recent_topics = []
                for interaction in context["conversation_history"][-3:]:
                    recent_topics.extend(interaction.get("entities", []))
                query_parts.extend(recent_topics)
        
        return " ".join(query_parts)
    
    async def _semantic_search(self, query: str) -> List[KnowledgeItem]:
        """Perform semantic search using vector database"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Calculate similarities
            if len(self.vectors) > 0:
                similarities = np.dot(self.vectors, query_embedding.T).flatten()
                
                # Get top matches
                top_indices = np.argsort(similarities)[::-1][:10]
                
                # Retrieve items
                items = []
                for idx in top_indices:
                    if similarities[idx] > 0.3:  # Similarity threshold
                        item = await self._get_knowledge_item(self.vector_ids[idx])
                        if item:
                            items.append(item)
                
                return items
            else:
                return await self._keyword_search(query)
                
        except Exception as e:
            self.logger.warning(f"Semantic search failed: {e}")
            return await self._keyword_search(query)
    
    async def _keyword_search(self, query: str) -> List[KnowledgeItem]:
        """Perform keyword search using SQLite FTS"""
        try:
            # Search in FTS table
            self.cursor.execute("""
                SELECT id, title, content, category, tags, source, confidence, last_updated
                FROM knowledge_search 
                WHERE knowledge_search MATCH ?
                ORDER BY rank
                LIMIT 10
            """, (query,))
            
            rows = self.cursor.fetchall()
            items = []
            
            for row in rows:
                item = KnowledgeItem(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    category=row[3],
                    tags=json.loads(row[4]) if row[4] else [],
                    source=row[5],
                    confidence=row[6],
                    last_updated=datetime.fromisoformat(row[7])
                )
                items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Keyword search failed: {e}")
            return []
    
    async def _get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Get knowledge item by ID"""
        try:
            self.cursor.execute("""
                SELECT id, title, content, category, tags, source, confidence, last_updated
                FROM knowledge_items 
                WHERE id = ?
            """, (item_id,))
            
            row = self.cursor.fetchone()
            if row:
                return KnowledgeItem(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    category=row[3],
                    tags=json.loads(row[4]) if row[4] else [],
                    source=row[5],
                    confidence=row[6],
                    last_updated=datetime.fromisoformat(row[7])
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get knowledge item: {e}")
            return None
    
    def _calculate_confidence(self, items: List[KnowledgeItem], query: str) -> float:
        """Calculate confidence score for search results"""
        if not items:
            return 0.0
        
        # Calculate average confidence
        avg_confidence = sum(item.confidence for item in items) / len(items)
        
        # Boost confidence if we have multiple relevant items
        if len(items) > 1:
            avg_confidence *= 1.2
        
        return min(avg_confidence, 1.0)
    
    async def add_knowledge_item(
        self, title: str, content: str, category: str, 
        tags: List[str], source: str, confidence: float = 1.0
    ) -> bool:
        """
        Add new knowledge item
        
        Args:
            title: Item title
            content: Item content
            category: Item category
            tags: Item tags
            source: Item source
            confidence: Confidence score
            
        Returns:
            bool: Success status
        """
        try:
            # Generate unique ID
            item_id = hashlib.md5(f"{title}{content}{category}".encode()).hexdigest()
            
            # Insert into knowledge table
            self.cursor.execute("""
                INSERT OR REPLACE INTO knowledge_items 
                (id, title, content, category, tags, source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item_id, title, content, category, json.dumps(tags), source, confidence))
            
            # Insert into search table
            self.cursor.execute("""
                INSERT OR REPLACE INTO knowledge_search 
                (id, title, content, category, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (item_id, title, content, category, json.dumps(tags)))
            
            # Update vector database if available
            if VECTOR_DB_AVAILABLE and self.embedding_model:
                await self._update_vector_db(item_id, content)
            
            self.conn.commit()
            self.logger.info(f"Added knowledge item: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add knowledge item: {e}")
            return False
    
    async def _update_vector_db(self, item_id: str, content: str):
        """Update vector database with new item"""
        try:
            # Generate embedding
            embedding = self.embedding_model.encode([content])
            
            # Add to vectors
            if len(self.vectors) == 0:
                self.vectors = embedding
            else:
                self.vectors = np.vstack([self.vectors, embedding])
            
            # Add ID
            self.vector_ids.append(item_id)
            
            # Save to file
            np.savez(self.vector_db_path, vectors=self.vectors, ids=self.vector_ids)
            
        except Exception as e:
            self.logger.warning(f"Failed to update vector database: {e}")
    
    async def get_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get available knowledge categories"""
        return self.categories
    
    async def get_category_items(self, category: str) -> List[KnowledgeItem]:
        """Get all items in a category"""
        try:
            self.cursor.execute("""
                SELECT id, title, content, category, tags, source, confidence, last_updated
                FROM knowledge_items 
                WHERE category = ?
                ORDER BY last_updated DESC
            """, (category,))
            
            rows = self.cursor.fetchall()
            items = []
            
            for row in rows:
                item = KnowledgeItem(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    category=row[3],
                    tags=json.loads(row[4]) if row[4] else [],
                    source=row[5],
                    confidence=row[6],
                    last_updated=datetime.fromisoformat(row[7])
                )
                items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to get category items: {e}")
            return []
    
    async def search_by_tag(self, tag: str) -> List[KnowledgeItem]:
        """Search knowledge items by tag"""
        try:
            self.cursor.execute("""
                SELECT id, title, content, category, tags, source, confidence, last_updated
                FROM knowledge_items 
                WHERE tags LIKE ?
                ORDER BY confidence DESC
            """, (f"%{tag}%",))
            
            rows = self.cursor.fetchall()
            items = []
            
            for row in rows:
                item = KnowledgeItem(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    category=row[3],
                    tags=json.loads(row[4]) if row[4] else [],
                    source=row[5],
                    confidence=row[6],
                    last_updated=datetime.fromisoformat(row[7])
                )
                items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to search by tag: {e}")
            return []
    
    async def shutdown(self):
        """Shutdown knowledge manager"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
            self.logger.info("Knowledge Manager shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}") 