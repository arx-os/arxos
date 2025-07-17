"""
SVGX Engine Advanced Symbol Management Service.

Implements advanced symbol versioning, collaboration, and AI-powered search capabilities:
- Git-like version control for symbols
- Real-time symbol editing collaboration
- AI-powered symbol search and recommendations
- Symbol dependency tracking and validation
- Symbol performance analytics and usage tracking
- Symbol marketplace and sharing features
- SVGX-specific symbol optimizations
"""

import logging
import hashlib
import json
import time
import uuid
import threading
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import asyncio
from concurrent.futures import ThreadPoolExecutor
import difflib
import re
from collections import defaultdict, deque
import pickle
import zlib

from svgx_engine.symbol_manager import SVGXSymbolManager
from svgx_engine.symbol_recognition import SVGXSymbolRecognitionService

try:
    from svgx_engine.utils.performance import PerformanceMonitor
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.performance import PerformanceMonitor

from svgx_engine.models.svgx import SVGXElement, SVGXDocument

try:
    from svgx_engine.utils.errors import (
        AdvancedSymbolError, VersionControlError, CollaborationError,
        SearchError, DependencyError, AnalyticsError, MarketplaceError
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import (
        AdvancedSymbolError, VersionControlError, CollaborationError,
        SearchError, DependencyError, AnalyticsError, MarketplaceError
    )


@dataclass
class SymbolVersion:
    """Represents a version of a symbol"""
    symbol_id: str
    version_hash: str
    parent_hash: Optional[str]
    author: str
    timestamp: datetime
    message: str
    content: str
    metadata: Dict[str, Any]
    file_size: int
    compression_ratio: float


@dataclass
class SymbolCollaboration:
    """Represents a collaboration session for a symbol"""
    session_id: str
    symbol_id: str
    participants: List[str]
    active_editors: List[str]
    last_activity: datetime
    conflict_resolution: Dict[str, Any]
    session_data: Dict[str, Any]


@dataclass
class SymbolSearchResult:
    """Result of symbol search"""
    symbol_id: str
    score: float
    relevance_factors: List[str]
    metadata: Dict[str, Any]
    usage_stats: Dict[str, Any]


@dataclass
class SymbolDependency:
    """Represents a symbol dependency"""
    symbol_id: str
    dependency_id: str
    dependency_type: str  # 'includes', 'references', 'extends'
    version_constraint: str
    is_required: bool
    metadata: Dict[str, Any]


@dataclass
class SymbolAnalytics:
    """Symbol usage analytics"""
    symbol_id: str
    usage_count: int
    popularity_score: float
    performance_metrics: Dict[str, float]
    user_feedback: Dict[str, Any]
    last_used: datetime
    created_date: datetime


@dataclass
class MarketplaceItem:
    """Represents a symbol in the marketplace"""
    symbol_id: str
    author: str
    title: str
    description: str
    category: str
    tags: List[str]
    rating: float
    download_count: int
    price: float
    license: str
    metadata: Dict[str, Any]


class SVGXAdvancedSymbolManagementService:
    """
    SVGX Engine Advanced Symbol Management Service.
    
    Provides advanced symbol management capabilities including version control,
    collaboration, AI-powered search, dependency tracking, analytics, and marketplace features.
    """
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the Advanced Symbol Management Service.
        
        Args:
            options: Configuration options
        """
        self.options = {
            'enable_version_control': True,
            'enable_collaboration': True,
            'enable_ai_search': True,
            'enable_dependency_tracking': True,
            'enable_analytics': True,
            'enable_marketplace': True,
            'max_concurrent_editors': 10,
            'version_history_limit': 100,
            'search_cache_size': 1000,
            'collaboration_timeout': 300,  # 5 minutes
            'analytics_retention_days': 365,
            'marketplace_enabled': True,
            'svgx_optimization_enabled': True,
        }
        if options:
            self.options.update(options)
        
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize dependent services
        self.symbol_manager = SVGXSymbolManager()
        self.symbol_recognition = SVGXSymbolRecognitionService()
        
        # Initialize databases
        self._init_databases()
        
        # Version control system
        self.version_graph = {}  # symbol_id -> version history
        self.current_versions = {}  # symbol_id -> current version hash
        
        # Collaboration system
        self.active_sessions = {}  # session_id -> SymbolCollaboration
        self.session_locks = {}  # symbol_id -> threading.Lock
        
        # AI search system
        self.search_index = {}  # symbol_id -> search metadata
        self.search_cache = {}
        self.ai_recommendations = {}
        
        # Dependency tracking
        self.dependency_graph = defaultdict(set)  # symbol_id -> dependencies
        self.reverse_dependencies = defaultdict(set)  # dependency_id -> dependents
        
        # Analytics system
        self.usage_tracking = {}  # symbol_id -> usage data
        self.performance_metrics = {}  # symbol_id -> performance data
        
        # Marketplace system
        self.marketplace_items = {}  # symbol_id -> MarketplaceItem
        self.category_index = defaultdict(list)
        self.tag_index = defaultdict(set)
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Background tasks
        self.cleanup_task = None
        self.analytics_task = None
        
        self.logger.info('Advanced Symbol Management Service initialized')
    
    def _init_databases(self):
        """Initialize SQLite databases for persistent storage"""
        try:
            self.db_path = Path("data/svgx_symbol_management.db")
            self.db_path.parent.mkdir(exist_ok=True)
            
            # Create tables
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS symbol_versions (
                        symbol_id TEXT,
                        version_hash TEXT PRIMARY KEY,
                        parent_hash TEXT,
                        author TEXT,
                        timestamp TEXT,
                        message TEXT,
                        content TEXT,
                        metadata TEXT,
                        file_size INTEGER,
                        compression_ratio REAL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS symbol_collaboration (
                        session_id TEXT PRIMARY KEY,
                        symbol_id TEXT,
                        participants TEXT,
                        active_editors TEXT,
                        last_activity TEXT,
                        conflict_resolution TEXT,
                        session_data TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS symbol_search_index (
                        symbol_id TEXT PRIMARY KEY,
                        search_metadata TEXT,
                        last_indexed TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS symbol_dependencies (
                        symbol_id TEXT,
                        dependency_id TEXT,
                        dependency_type TEXT,
                        version_constraint TEXT,
                        is_required BOOLEAN,
                        metadata TEXT,
                        PRIMARY KEY (symbol_id, dependency_id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS symbol_analytics (
                        symbol_id TEXT PRIMARY KEY,
                        usage_count INTEGER,
                        popularity_score REAL,
                        performance_metrics TEXT,
                        user_feedback TEXT,
                        last_used TEXT,
                        created_date TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS marketplace_items (
                        symbol_id TEXT PRIMARY KEY,
                        author TEXT,
                        title TEXT,
                        description TEXT,
                        category TEXT,
                        tags TEXT,
                        rating REAL,
                        download_count INTEGER,
                        price REAL,
                        license TEXT,
                        metadata TEXT
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize databases: {str(e)}")
            raise AdvancedSymbolError(f"Database initialization failed: {str(e)}")
    
    def create_symbol_version(self, symbol_id: str, content: str, author: str, 
                            message: str, metadata: Dict[str, Any] = None) -> SymbolVersion:
        """
        Create a new version of a symbol.
        
        Args:
            symbol_id: ID of the symbol
            content: Symbol content
            author: Author of the version
            message: Version message
            metadata: Additional metadata
            
        Returns:
            SymbolVersion object
        """
        try:
            # Generate version hash
            version_hash = self._generate_version_hash(content, metadata)
            
            # Get parent hash (current version)
            parent_hash = self.current_versions.get(symbol_id)
            
            # Calculate file size and compression ratio
            file_size = len(content.encode('utf-8'))
            compression_ratio = self._calculate_compression_ratio(content)
            
            # Create version object
            version = SymbolVersion(
                symbol_id=symbol_id,
                version_hash=version_hash,
                parent_hash=parent_hash,
                author=author,
                timestamp=datetime.now(),
                message=message,
                content=content,
                metadata=metadata or {},
                file_size=file_size,
                compression_ratio=compression_ratio
            )
            
            # Save to database
            self._save_symbol_version(version)
            
            # Update current version
            self.current_versions[symbol_id] = version_hash
            
            # Update version graph
            if symbol_id not in self.version_graph:
                self.version_graph[symbol_id] = []
            self.version_graph[symbol_id].append(version)
            
            # Apply SVGX optimizations if enabled
            if self.options['svgx_optimization_enabled']:
                self._apply_svgx_optimizations(version)
            
            self.logger.info(f"Created version {version_hash} for symbol {symbol_id}")
            return version
            
        except Exception as e:
            self.logger.error(f"Failed to create symbol version: {str(e)}")
            raise VersionControlError(f"Failed to create version: {str(e)}")
    
    def _generate_version_hash(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Generate hash for symbol version."""
        data = content + json.dumps(metadata or {}, sort_keys=True)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _calculate_compression_ratio(self, content: str) -> float:
        """Calculate compression ratio for content."""
        try:
            original_size = len(content.encode('utf-8'))
            compressed_size = len(zlib.compress(content.encode('utf-8')))
            return compressed_size / original_size if original_size > 0 else 1.0
        except Exception:
            return 1.0
    
    def _save_symbol_version(self, version: SymbolVersion):
        """Save symbol version to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO symbol_versions 
                    (symbol_id, version_hash, parent_hash, author, timestamp, message, 
                     content, metadata, file_size, compression_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    version.symbol_id,
                    version.version_hash,
                    version.parent_hash,
                    version.author,
                    version.timestamp.isoformat(),
                    version.message,
                    version.content,
                    json.dumps(version.metadata),
                    version.file_size,
                    version.compression_ratio
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save symbol version: {str(e)}")
            raise VersionControlError(f"Failed to save version: {str(e)}")
    
    def _apply_svgx_optimizations(self, version: SymbolVersion):
        """Apply SVGX-specific optimizations to symbol version."""
        try:
            # Optimize SVGX content
            if version.content and '<svg' in version.content.lower():
                # Apply SVGX optimizations
                optimized_content = self._optimize_svgx_content(version.content)
                if optimized_content != version.content:
                    version.content = optimized_content
                    version.file_size = len(optimized_content.encode('utf-8'))
                    version.compression_ratio = self._calculate_compression_ratio(optimized_content)
                    
        except Exception as e:
            self.logger.warning(f"Failed to apply SVGX optimizations: {str(e)}")
    
    def _optimize_svgx_content(self, content: str) -> str:
        """Optimize SVGX content."""
        # Simple optimizations - can be enhanced
        optimized = content
        
        # Remove unnecessary whitespace
        optimized = re.sub(r'\s+', ' ', optimized)
        
        # Remove comments
        optimized = re.sub(r'<!--.*?-->', '', optimized, flags=re.DOTALL)
        
        return optimized
    
    def get_symbol_version(self, symbol_id: str, version_hash: str = None) -> Optional[SymbolVersion]:
        """
        Get a specific version of a symbol.
        
        Args:
            symbol_id: ID of the symbol
            version_hash: Version hash (None for current version)
            
        Returns:
            SymbolVersion object or None
        """
        try:
            if version_hash is None:
                version_hash = self.current_versions.get(symbol_id)
                if not version_hash:
                    return None
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM symbol_versions 
                    WHERE symbol_id = ? AND version_hash = ?
                """, (symbol_id, version_hash))
                
                row = cursor.fetchone()
                if row:
                    return SymbolVersion(
                        symbol_id=row[0],
                        version_hash=row[1],
                        parent_hash=row[2],
                        author=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        message=row[5],
                        content=row[6],
                        metadata=json.loads(row[7]),
                        file_size=row[8],
                        compression_ratio=row[9]
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get symbol version: {str(e)}")
            raise VersionControlError(f"Failed to get version: {str(e)}")
    
    def get_version_history(self, symbol_id: str) -> List[SymbolVersion]:
        """
        Get version history for a symbol.
        
        Args:
            symbol_id: ID of the symbol
            
        Returns:
            List of SymbolVersion objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM symbol_versions 
                    WHERE symbol_id = ? 
                    ORDER BY timestamp DESC
                """, (symbol_id,))
                
                versions = []
                for row in cursor.fetchall():
                    version = SymbolVersion(
                        symbol_id=row[0],
                        version_hash=row[1],
                        parent_hash=row[2],
                        author=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        message=row[5],
                        content=row[6],
                        metadata=json.loads(row[7]),
                        file_size=row[8],
                        compression_ratio=row[9]
                    )
                    versions.append(version)
                
                return versions
                
        except Exception as e:
            self.logger.error(f"Failed to get version history: {str(e)}")
            raise VersionControlError(f"Failed to get history: {str(e)}")
    
    def start_collaboration_session(self, symbol_id: str, user_id: str) -> str:
        """
        Start a collaboration session for a symbol.
        
        Args:
            symbol_id: ID of the symbol
            user_id: ID of the user starting the session
            
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            
            # Create session
            session = SymbolCollaboration(
                session_id=session_id,
                symbol_id=symbol_id,
                participants=[user_id],
                active_editors=[user_id],
                last_activity=datetime.now(),
                conflict_resolution={},
                session_data={}
            )
            
            # Save to database
            self._save_collaboration_session(session)
            
            # Add to active sessions
            self.active_sessions[session_id] = session
            
            # Create lock for symbol
            if symbol_id not in self.session_locks:
                self.session_locks[symbol_id] = threading.Lock()
            
            self.logger.info(f"Started collaboration session {session_id} for symbol {symbol_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to start collaboration session: {str(e)}")
            raise CollaborationError(f"Failed to start session: {str(e)}")
    
    def _save_collaboration_session(self, session: SymbolCollaboration):
        """Save collaboration session to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO symbol_collaboration 
                    (session_id, symbol_id, participants, active_editors, 
                     last_activity, conflict_resolution, session_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    session.symbol_id,
                    json.dumps(session.participants),
                    json.dumps(session.active_editors),
                    session.last_activity.isoformat(),
                    json.dumps(session.conflict_resolution),
                    json.dumps(session.session_data)
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save collaboration session: {str(e)}")
            raise CollaborationError(f"Failed to save session: {str(e)}")
    
    def join_collaboration_session(self, session_id: str, user_id: str) -> bool:
        """
        Join an existing collaboration session.
        
        Args:
            session_id: ID of the session
            user_id: ID of the user joining
            
        Returns:
            True if successful
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            # Add user to participants
            if user_id not in session.participants:
                session.participants.append(user_id)
            
            # Add user to active editors
            if user_id not in session.active_editors:
                session.active_editors.append(user_id)
            
            # Update last activity
            session.last_activity = datetime.now()
            
            # Save to database
            self._save_collaboration_session(session)
            
            self.logger.info(f"User {user_id} joined session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to join collaboration session: {str(e)}")
            raise CollaborationError(f"Failed to join session: {str(e)}")
    
    def search_symbols(self, query: str, limit: int = 10, 
                      filters: Dict[str, Any] = None) -> List[SymbolSearchResult]:
        """
        Search symbols using AI-powered search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Search filters
            
        Returns:
            List of SymbolSearchResult objects
        """
        try:
            # Extract query features
            query_features = self._extract_query_features(query)
            
            # Search through indexed symbols
            results = []
            for symbol_id, symbol_features in self.search_index.items():
                # Calculate search score
                score = self._calculate_search_score(query_features, symbol_features)
                
                if score > 0.1:  # Minimum relevance threshold
                    # Get relevance factors
                    relevance_factors = self._get_relevance_factors(query_features, symbol_features)
                    
                    # Get usage stats
                    usage_stats = self.usage_tracking.get(symbol_id, {})
                    
                    result = SymbolSearchResult(
                        symbol_id=symbol_id,
                        score=score,
                        relevance_factors=relevance_factors,
                        metadata=symbol_features.get('metadata', {}),
                        usage_stats=usage_stats
                    )
                    results.append(result)
            
            # Sort by score
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Apply filters
            if filters:
                results = self._apply_search_filters(results, filters)
            
            # Limit results
            results = results[:limit]
            
            self.logger.info(f"Search returned {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search symbols: {str(e)}")
            raise SearchError(f"Search failed: {str(e)}")
    
    def _extract_query_features(self, query: str) -> Dict[str, Any]:
        """Extract features from search query."""
        features = {
            'text': query.lower(),
            'words': query.lower().split(),
            'length': len(query),
            'has_svgx_keywords': any(keyword in query.lower() for keyword in ['svgx', 'svg', 'symbol', 'graphic']),
            'has_technical_terms': any(term in query.lower() for term in ['hvac', 'electrical', 'plumbing', 'fire', 'security'])
        }
        return features
    
    def _calculate_search_score(self, query_features: Dict[str, Any], 
                              symbol_features: Dict[str, Any]) -> float:
        """Calculate search relevance score."""
        score = 0.0
        
        # Text similarity
        query_text = query_features.get('text', '')
        symbol_text = symbol_features.get('text', '')
        
        if query_text and symbol_text:
            similarity = difflib.SequenceMatcher(None, query_text, symbol_text).ratio()
            score += similarity * 0.4
        
        # Word matching
        query_words = set(query_features.get('words', []))
        symbol_words = set(symbol_features.get('words', []))
        
        if query_words and symbol_words:
            word_overlap = len(query_words.intersection(symbol_words)) / len(query_words)
            score += word_overlap * 0.3
        
        # Category matching
        query_category = query_features.get('category')
        symbol_category = symbol_features.get('category')
        
        if query_category and symbol_category and query_category == symbol_category:
            score += 0.2
        
        # Usage popularity
        usage_count = symbol_features.get('usage_count', 0)
        if usage_count > 0:
            popularity_bonus = min(usage_count / 100, 0.1)  # Max 0.1 bonus
            score += popularity_bonus
        
        return min(score, 1.0)
    
    def _get_relevance_factors(self, query_features: Dict[str, Any], 
                              symbol_features: Dict[str, Any]) -> List[str]:
        """Get relevance factors for search result."""
        factors = []
        
        # Text similarity
        if query_features.get('text') and symbol_features.get('text'):
            similarity = difflib.SequenceMatcher(None, 
                                               query_features['text'], 
                                               symbol_features['text']).ratio()
            if similarity > 0.5:
                factors.append(f"Text similarity: {similarity:.2f}")
        
        # Word matching
        query_words = set(query_features.get('words', []))
        symbol_words = set(symbol_features.get('words', []))
        
        if query_words and symbol_words:
            overlap = len(query_words.intersection(symbol_words))
            if overlap > 0:
                factors.append(f"Word overlap: {overlap} words")
        
        # Category match
        if (query_features.get('category') and 
            symbol_features.get('category') and 
            query_features['category'] == symbol_features['category']):
            factors.append("Category match")
        
        # Popularity
        usage_count = symbol_features.get('usage_count', 0)
        if usage_count > 10:
            factors.append(f"Popular symbol ({usage_count} uses)")
        
        return factors
    
    def _apply_search_filters(self, results: List[SymbolSearchResult], 
                            filters: Dict[str, Any]) -> List[SymbolSearchResult]:
        """Apply search filters to results."""
        filtered_results = results
        
        # Category filter
        if 'category' in filters:
            category = filters['category']
            filtered_results = [r for r in filtered_results 
                              if r.metadata.get('category') == category]
        
        # Usage count filter
        if 'min_usage' in filters:
            min_usage = filters['min_usage']
            filtered_results = [r for r in filtered_results 
                              if r.usage_stats.get('usage_count', 0) >= min_usage]
        
        # Rating filter
        if 'min_rating' in filters:
            min_rating = filters['min_rating']
            filtered_results = [r for r in filtered_results 
                              if r.metadata.get('rating', 0) >= min_rating]
        
        return filtered_results
    
    def add_symbol_dependency(self, symbol_id: str, dependency_id: str, 
                            dependency_type: str, version_constraint: str = "*", 
                            is_required: bool = True, metadata: Dict[str, Any] = None) -> bool:
        """
        Add a dependency to a symbol.
        
        Args:
            symbol_id: ID of the symbol
            dependency_id: ID of the dependency
            dependency_type: Type of dependency
            version_constraint: Version constraint
            is_required: Whether dependency is required
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        try:
            dependency = SymbolDependency(
                symbol_id=symbol_id,
                dependency_id=dependency_id,
                dependency_type=dependency_type,
                version_constraint=version_constraint,
                is_required=is_required,
                metadata=metadata or {}
            )
            
            # Save to database
            self._save_symbol_dependency(dependency)
            
            # Update dependency graph
            self.dependency_graph[symbol_id].add(dependency_id)
            self.reverse_dependencies[dependency_id].add(symbol_id)
            
            self.logger.info(f"Added dependency {dependency_id} to symbol {symbol_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add symbol dependency: {str(e)}")
            raise DependencyError(f"Failed to add dependency: {str(e)}")
    
    def _save_symbol_dependency(self, dependency: SymbolDependency):
        """Save symbol dependency to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO symbol_dependencies 
                    (symbol_id, dependency_id, dependency_type, version_constraint, 
                     is_required, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    dependency.symbol_id,
                    dependency.dependency_id,
                    dependency.dependency_type,
                    dependency.version_constraint,
                    dependency.is_required,
                    json.dumps(dependency.metadata)
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save symbol dependency: {str(e)}")
            raise DependencyError(f"Failed to save dependency: {str(e)}")
    
    def track_symbol_usage(self, symbol_id: str, user_id: str = None, 
                          context: Dict[str, Any] = None):
        """
        Track symbol usage for analytics.
        
        Args:
            symbol_id: ID of the symbol
            user_id: ID of the user
            context: Usage context
        """
        try:
            # Update usage tracking
            if symbol_id not in self.usage_tracking:
                self.usage_tracking[symbol_id] = {
                    'usage_count': 0,
                    'users': set(),
                    'last_used': None,
                    'contexts': []
                }
            
            usage_data = self.usage_tracking[symbol_id]
            usage_data['usage_count'] += 1
            
            if user_id:
                usage_data['users'].add(user_id)
            
            usage_data['last_used'] = datetime.now()
            
            if context:
                usage_data['contexts'].append({
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user_id,
                    'context': context
                })
            
            # Update analytics in database
            self._update_analytics_in_db(symbol_id, usage_data)
            
        except Exception as e:
            self.logger.error(f"Failed to track symbol usage: {str(e)}")
            raise AnalyticsError(f"Failed to track usage: {str(e)}")
    
    def _update_analytics_in_db(self, symbol_id: str, usage_data: Dict[str, Any]):
        """Update analytics in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO symbol_analytics 
                    (symbol_id, usage_count, popularity_score, performance_metrics, 
                     user_feedback, last_used, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol_id,
                    usage_data['usage_count'],
                    self._calculate_popularity_score(symbol_id),
                    json.dumps(usage_data.get('performance_metrics', {})),
                    json.dumps(usage_data.get('user_feedback', {})),
                    usage_data['last_used'].isoformat() if usage_data['last_used'] else None,
                    datetime.now().isoformat()  # created_date
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update analytics in database: {str(e)}")
            raise AnalyticsError(f"Failed to update analytics: {str(e)}")
    
    def _calculate_popularity_score(self, symbol_id: str) -> float:
        """Calculate popularity score for a symbol."""
        try:
            usage_data = self.usage_tracking.get(symbol_id, {})
            usage_count = usage_data.get('usage_count', 0)
            unique_users = len(usage_data.get('users', set()))
            
            # Simple popularity formula
            score = (usage_count * 0.6) + (unique_users * 0.4)
            
            return min(score / 100, 1.0)  # Normalize to 0-1
            
        except Exception as e:
            self.logger.error(f"Failed to calculate popularity score: {str(e)}")
            return 0.0
    
    def add_marketplace_item(self, symbol_id: str, author: str, title: str, 
                           description: str, category: str, tags: List[str], 
                           price: float = 0.0, license: str = "MIT", 
                           metadata: Dict[str, Any] = None) -> bool:
        """
        Add a symbol to the marketplace.
        
        Args:
            symbol_id: ID of the symbol
            author: Author of the symbol
            title: Title of the symbol
            description: Description of the symbol
            category: Category of the symbol
            tags: Tags for the symbol
            price: Price of the symbol
            license: License of the symbol
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        try:
            marketplace_item = MarketplaceItem(
                symbol_id=symbol_id,
                author=author,
                title=title,
                description=description,
                category=category,
                tags=tags,
                rating=0.0,
                download_count=0,
                price=price,
                license=license,
                metadata=metadata or {}
            )
            
            # Save to database
            self._save_marketplace_item(marketplace_item)
            
            # Update indexes
            self.marketplace_items[symbol_id] = marketplace_item
            self.category_index[category].append(symbol_id)
            
            for tag in tags:
                self.tag_index[tag].add(symbol_id)
            
            self.logger.info(f"Added symbol {symbol_id} to marketplace")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add marketplace item: {str(e)}")
            raise MarketplaceError(f"Failed to add marketplace item: {str(e)}")
    
    def _save_marketplace_item(self, item: MarketplaceItem):
        """Save marketplace item to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO marketplace_items 
                    (symbol_id, author, title, description, category, tags, 
                     rating, download_count, price, license, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.symbol_id,
                    item.author,
                    item.title,
                    item.description,
                    item.category,
                    json.dumps(item.tags),
                    item.rating,
                    item.download_count,
                    item.price,
                    item.license,
                    json.dumps(item.metadata)
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save marketplace item: {str(e)}")
            raise MarketplaceError(f"Failed to save marketplace item: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            'total_symbols': len(self.current_versions),
            'total_versions': sum(len(versions) for versions in self.version_graph.values()),
            'active_sessions': len(self.active_sessions),
            'search_index_size': len(self.search_index),
            'marketplace_items': len(self.marketplace_items),
            'performance_metrics': self.performance_monitor.get_metrics()
        }
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Close thread pool
            self.executor.shutdown(wait=True)
            
            # Clear caches
            self.search_cache.clear()
            
            self.logger.info("Advanced Symbol Management Service cleaned up")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup: {str(e)}")
            raise AdvancedSymbolError(f"Cleanup failed: {str(e)}") 