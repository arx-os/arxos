"""
Advanced Symbol Management Service

Implements advanced symbol versioning, collaboration, and AI-powered search capabilities:
- Git-like version control for symbols
- Real-time symbol editing collaboration
- AI-powered symbol search and recommendations
- Symbol dependency tracking and validation
- Symbol performance analytics and usage tracking
- Symbol marketplace and sharing features
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

logger = logging.getLogger(__name__)


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


class AdvancedSymbolManagement:
    """Advanced symbol management implementation"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
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
        }
        if options:
            self.options.update(options)
        
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
        
        logger.info('Advanced Symbol Management initialized')
    
    def _init_databases(self):
        """Initialize SQLite databases for persistent storage"""
        self.db_path = Path("data/symbol_management.db")
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
    
    # Version Control Methods
    
    def create_symbol_version(self, symbol_id: str, content: str, author: str, 
                            message: str, metadata: Dict[str, Any] = None) -> SymbolVersion:
        """Create a new version of a symbol with Git-like versioning"""
        try:
            # Generate unique version hash including timestamp and author
            timestamp = datetime.now()
            content_hash = hashlib.sha256(
                f"{content}{timestamp.isoformat()}{author}".encode()
            ).hexdigest()
            
            # Get parent version
            parent_hash = self.current_versions.get(symbol_id)
            
            # Create version object
            version = SymbolVersion(
                symbol_id=symbol_id,
                version_hash=content_hash,
                parent_hash=parent_hash,
                author=author,
                timestamp=timestamp,
                message=message,
                content=content,
                metadata=metadata or {},
                file_size=len(content.encode('utf-8')),
                compression_ratio=self._calculate_compression_ratio(content)
            )
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO symbol_versions 
                    (symbol_id, version_hash, parent_hash, author, timestamp, message, 
                     content, metadata, file_size, compression_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol_id, content_hash, parent_hash, author, 
                    timestamp.isoformat(), message, content, 
                    json.dumps(metadata or {}), version.file_size, version.compression_ratio
                ))
                conn.commit()
            
            # Update current version
            self.current_versions[symbol_id] = content_hash
            
            # Update version graph
            if symbol_id not in self.version_graph:
                self.version_graph[symbol_id] = []
            self.version_graph[symbol_id].append(version)
            
            # Limit version history
            if len(self.version_graph[symbol_id]) > self.options['version_history_limit']:
                self.version_graph[symbol_id] = self.version_graph[symbol_id][-self.options['version_history_limit']:]
            
            logger.info(f'Created version {content_hash[:8]} for symbol {symbol_id}')
            return version
            
        except Exception as e:
            logger.error(f'Failed to create symbol version: {e}')
            raise
    
    def get_symbol_version(self, symbol_id: str, version_hash: str = None) -> Optional[SymbolVersion]:
        """Get a specific version of a symbol"""
        try:
            if version_hash is None:
                version_hash = self.current_versions.get(symbol_id)
            
            if not version_hash:
                return None
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT symbol_id, version_hash, parent_hash, author, timestamp, message,
                           content, metadata, file_size, compression_ratio
                    FROM symbol_versions 
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
            logger.error(f'Failed to get symbol version: {e}')
            return None
    
    def get_version_history(self, symbol_id: str) -> List[SymbolVersion]:
        """Get complete version history for a symbol"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT symbol_id, version_hash, parent_hash, author, timestamp, message,
                           content, metadata, file_size, compression_ratio
                    FROM symbol_versions 
                    WHERE symbol_id = ?
                    ORDER BY timestamp DESC
                """, (symbol_id,))
                
                versions = []
                for row in cursor.fetchall():
                    versions.append(SymbolVersion(
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
                    ))
                
                return versions
                
        except Exception as e:
            logger.error(f'Failed to get version history: {e}')
            return []
    
    def rollback_symbol(self, symbol_id: str, target_version_hash: str) -> bool:
        """Rollback symbol to a specific version"""
        try:
            target_version = self.get_symbol_version(symbol_id, target_version_hash)
            if not target_version:
                return False
            
            # Create new version with rollback content
            self.create_symbol_version(
                symbol_id=symbol_id,
                content=target_version.content,
                author="system",
                message=f"Rollback to version {target_version_hash[:8]}",
                metadata={"rollback": True, "target_version": target_version_hash}
            )
            
            logger.info(f'Rolled back symbol {symbol_id} to version {target_version_hash[:8]}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to rollback symbol: {e}')
            return False
    
    def compare_versions(self, symbol_id: str, version1_hash: str, version2_hash: str) -> Dict[str, Any]:
        """Compare two versions of a symbol"""
        try:
            version1 = self.get_symbol_version(symbol_id, version1_hash)
            version2 = self.get_symbol_version(symbol_id, version2_hash)
            
            if not version1 or not version2:
                return {"error": "One or both versions not found"}
            
            # Calculate diff
            diff = list(difflib.unified_diff(
                version1.content.splitlines(keepends=True),
                version2.content.splitlines(keepends=True),
                fromfile=f"version_{version1_hash[:8]}",
                tofile=f"version_{version2_hash[:8]}"
            ))
            
            return {
                "version1": {
                    "hash": version1_hash,
                    "author": version1.author,
                    "timestamp": version1.timestamp.isoformat(),
                    "message": version1.message,
                    "file_size": version1.file_size
                },
                "version2": {
                    "hash": version2_hash,
                    "author": version2.author,
                    "timestamp": version2.timestamp.isoformat(),
                    "message": version2.message,
                    "file_size": version2.file_size
                },
                "diff": ''.join(diff),
                "changes": {
                    "lines_added": len([line for line in diff if line.startswith('+') and not line.startswith('+++')]),
                    "lines_removed": len([line for line in diff if line.startswith('-') and not line.startswith('---')]),
                    "total_changes": len(diff)
                }
            }
            
        except Exception as e:
            logger.error(f'Failed to compare versions: {e}')
            return {"error": str(e)}
    
    # Collaboration Methods
    
    def start_collaboration_session(self, symbol_id: str, user_id: str) -> str:
        """Start a real-time collaboration session for a symbol"""
        try:
            session_id = str(uuid.uuid4())
            
            # Create session lock if not exists
            if symbol_id not in self.session_locks:
                self.session_locks[symbol_id] = threading.Lock()
            
            with self.session_locks[symbol_id]:
                session = SymbolCollaboration(
                    session_id=session_id,
                    symbol_id=symbol_id,
                    participants=[user_id],
                    active_editors=[user_id],
                    last_activity=datetime.now(),
                    conflict_resolution={},
                    session_data={"current_content": self.get_current_content(symbol_id)}
                )
                
                self.active_sessions[session_id] = session
                
                # Store in database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO symbol_collaboration
                        (session_id, symbol_id, participants, active_editors, last_activity, 
                         conflict_resolution, session_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session_id, symbol_id, json.dumps([user_id]), json.dumps([user_id]),
                        session.last_activity.isoformat(), json.dumps({}), json.dumps(session.session_data)
                    ))
                    conn.commit()
                
                logger.info(f'Started collaboration session {session_id} for symbol {symbol_id}')
                return session_id
                
        except Exception as e:
            logger.error(f'Failed to start collaboration session: {e}')
            raise
    
    def join_collaboration_session(self, session_id: str, user_id: str) -> bool:
        """Join an existing collaboration session"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            with self.session_locks[session.symbol_id]:
                if user_id not in session.participants:
                    session.participants.append(user_id)
                
                if user_id not in session.active_editors:
                    session.active_editors.append(user_id)
                
                session.last_activity = datetime.now()
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE symbol_collaboration 
                        SET participants = ?, active_editors = ?, last_activity = ?
                        WHERE session_id = ?
                    """, (
                        json.dumps(session.participants),
                        json.dumps(session.active_editors),
                        session.last_activity.isoformat(),
                        session_id
                    ))
                    conn.commit()
                
                logger.info(f'User {user_id} joined session {session_id}')
                return True
                
        except Exception as e:
            logger.error(f'Failed to join collaboration session: {e}')
            return False
    
    def update_collaboration_content(self, session_id: str, user_id: str, 
                                   content: str, cursor_position: Dict[str, int] = None) -> bool:
        """Update content in a collaboration session"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            with self.session_locks[session.symbol_id]:
                # Update session data
                session.session_data["current_content"] = content
                session.session_data["last_editor"] = user_id
                session.session_data["last_edit_time"] = datetime.now().isoformat()
                
                if cursor_position:
                    session.session_data["cursor_positions"] = session.session_data.get("cursor_positions", {})
                    session.session_data["cursor_positions"][user_id] = cursor_position
                
                session.last_activity = datetime.now()
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE symbol_collaboration 
                        SET session_data = ?, last_activity = ?
                        WHERE session_id = ?
                    """, (
                        json.dumps(session.session_data),
                        session.last_activity.isoformat(),
                        session_id
                    ))
                    conn.commit()
                
                return True
                
        except Exception as e:
            logger.error(f'Failed to update collaboration content: {e}')
            return False
    
    def resolve_collaboration_conflict(self, session_id: str, conflict_data: Dict[str, Any]) -> bool:
        """Resolve a collaboration conflict"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            with self.session_locks[session.symbol_id]:
                session.conflict_resolution.update(conflict_data)
                session.last_activity = datetime.now()
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE symbol_collaboration 
                        SET conflict_resolution = ?, last_activity = ?
                        WHERE session_id = ?
                    """, (
                        json.dumps(session.conflict_resolution),
                        session.last_activity.isoformat(),
                        session_id
                    ))
                    conn.commit()
                
                logger.info(f'Resolved conflict in session {session_id}')
                return True
                
        except Exception as e:
            logger.error(f'Failed to resolve collaboration conflict: {e}')
            return False
    
    def end_collaboration_session(self, session_id: str) -> bool:
        """End a collaboration session"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Save final content as new version
            final_content = session.session_data.get("current_content")
            if final_content:
                self.create_symbol_version(
                    symbol_id=session.symbol_id,
                    content=final_content,
                    author="collaboration",
                    message=f"Collaborative edit by {', '.join(session.participants)}",
                    metadata={"session_id": session_id, "participants": session.participants}
                )
            
            # Clean up
            del self.active_sessions[session_id]
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM symbol_collaboration WHERE session_id = ?", (session_id,))
                conn.commit()
            
            logger.info(f'Ended collaboration session {session_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to end collaboration session: {e}')
            return False
    
    # AI Search Methods
    
    def index_symbol_for_search(self, symbol_id: str, content: str, metadata: Dict[str, Any] = None):
        """Index a symbol for AI-powered search"""
        try:
            # Extract searchable features
            search_features = self._extract_search_features(content, metadata)
            
            # Store in search index
            self.search_index[symbol_id] = {
                "features": search_features,
                "metadata": metadata or {},
                "last_indexed": datetime.now(),
                "content_hash": hashlib.sha256(content.encode()).hexdigest()
            }
            
            logger.info(f'Indexed symbol {symbol_id} for search')
            
        except Exception as e:
            logger.error(f'Failed to index symbol for search: {e}')
    
    def search_symbols(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[SymbolSearchResult]:
        """Search symbols using AI-powered search"""
        try:
            results = []
            query_features = self._extract_query_features(query)
            
            for symbol_id, index_data in self.search_index.items():
                score = self._calculate_search_score(query_features, index_data["features"])
                
                if score > 0.1:  # Minimum relevance threshold
                    results.append(SymbolSearchResult(
                        symbol_id=symbol_id,
                        score=score,
                        relevance_factors=self._get_relevance_factors(query_features, index_data["features"]),
                        metadata=index_data["metadata"],
                        usage_stats=self.get_symbol_analytics(symbol_id).__dict__ if self.get_symbol_analytics(symbol_id) else {}
                    ))
            
            # Sort by score and apply filters
            results.sort(key=lambda x: x.score, reverse=True)
            
            if filters:
                results = self._apply_search_filters(results, filters)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f'Failed to search symbols: {e}')
            return []
    
    def get_ai_recommendations(self, symbol_id: str, context: Dict[str, Any] = None) -> List[SymbolSearchResult]:
        """Get AI-powered symbol recommendations"""
        try:
            # Get current symbol features
            current_features = self.search_index.get(symbol_id, {}).get("features", {})
            
            # Find similar symbols
            recommendations = []
            for other_id, index_data in self.search_index.items():
                if other_id != symbol_id:
                    similarity = self._calculate_similarity(current_features, index_data["features"])
                    
                    if similarity > 0.3:  # Similarity threshold
                        recommendations.append(SymbolSearchResult(
                            symbol_id=other_id,
                            score=similarity,
                            relevance_factors=["similar_features", "usage_patterns"],
                            metadata=index_data["metadata"],
                            usage_stats=self.get_symbol_analytics(other_id).__dict__ if self.get_symbol_analytics(other_id) else {}
                        ))
            
            # Sort by similarity and return top recommendations
            recommendations.sort(key=lambda x: x.score, reverse=True)
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f'Failed to get AI recommendations: {e}')
            return []
    
    # Dependency Tracking Methods
    
    def add_symbol_dependency(self, symbol_id: str, dependency_id: str, 
                            dependency_type: str, version_constraint: str = "*", 
                            is_required: bool = True, metadata: Dict[str, Any] = None) -> bool:
        """Add a dependency relationship between symbols"""
        try:
            dependency = SymbolDependency(
                symbol_id=symbol_id,
                dependency_id=dependency_id,
                dependency_type=dependency_type,
                version_constraint=version_constraint,
                is_required=is_required,
                metadata=metadata or {}
            )
            
            # Update dependency graph
            self.dependency_graph[symbol_id].add(dependency_id)
            self.reverse_dependencies[dependency_id].add(symbol_id)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO symbol_dependencies
                    (symbol_id, dependency_id, dependency_type, version_constraint, is_required, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    symbol_id, dependency_id, dependency_type, version_constraint,
                    is_required, json.dumps(metadata or {})
                ))
                conn.commit()
            
            logger.info(f'Added dependency {dependency_id} to symbol {symbol_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to add symbol dependency: {e}')
            return False
    
    def get_symbol_dependencies(self, symbol_id: str) -> List[SymbolDependency]:
        """Get all dependencies for a symbol"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT symbol_id, dependency_id, dependency_type, version_constraint, 
                           is_required, metadata
                    FROM symbol_dependencies 
                    WHERE symbol_id = ?
                """, (symbol_id,))
                
                dependencies = []
                for row in cursor.fetchall():
                    dependencies.append(SymbolDependency(
                        symbol_id=row[0],
                        dependency_id=row[1],
                        dependency_type=row[2],
                        version_constraint=row[3],
                        is_required=bool(row[4]),
                        metadata=json.loads(row[5])
                    ))
                
                return dependencies
                
        except Exception as e:
            logger.error(f'Failed to get symbol dependencies: {e}')
            return []
    
    def validate_symbol_dependencies(self, symbol_id: str) -> Dict[str, Any]:
        """Validate all dependencies for a symbol"""
        try:
            dependencies = self.get_symbol_dependencies(symbol_id)
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "missing_dependencies": [],
                "version_conflicts": []
            }
            
            for dependency in dependencies:
                # Check if dependency exists
                if not self._symbol_exists(dependency.dependency_id):
                    validation_results["valid"] = False
                    validation_results["missing_dependencies"].append(dependency.dependency_id)
                    validation_results["errors"].append(f"Missing dependency: {dependency.dependency_id}")
                
                # Check version constraints
                if not self._check_version_constraint(dependency):
                    validation_results["warnings"].append(f"Version conflict for {dependency.dependency_id}")
                    validation_results["version_conflicts"].append(dependency.dependency_id)
            
            return validation_results
            
        except Exception as e:
            logger.error(f'Failed to validate symbol dependencies: {e}')
            return {"valid": False, "error": str(e)}
    
    # Analytics Methods
    
    def track_symbol_usage(self, symbol_id: str, user_id: str = None, context: Dict[str, Any] = None):
        """Track usage of a symbol for analytics"""
        try:
            now = datetime.now()
            
            # Update usage tracking
            if symbol_id not in self.usage_tracking:
                self.usage_tracking[symbol_id] = {
                    "usage_count": 0,
                    "last_used": None,
                    "users": set(),
                    "contexts": []
                }
            
            tracking = self.usage_tracking[symbol_id]
            tracking["usage_count"] += 1
            tracking["last_used"] = now
            
            if user_id:
                tracking["users"].add(user_id)
            
            if context:
                tracking["contexts"].append({
                    "timestamp": now.isoformat(),
                    "user_id": user_id,
                    "context": context
                })
            
            # Update database
            analytics = self.get_symbol_analytics(symbol_id)
            if analytics:
                analytics.usage_count += 1
                analytics.last_used = now
                self._update_analytics_in_db(analytics)
            
            logger.debug(f'Tracked usage of symbol {symbol_id}')
            
        except Exception as e:
            logger.error(f'Failed to track symbol usage: {e}')
    
    def get_symbol_analytics(self, symbol_id: str) -> Optional[SymbolAnalytics]:
        """Get analytics for a symbol"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT symbol_id, usage_count, popularity_score, performance_metrics,
                           user_feedback, last_used, created_date
                    FROM symbol_analytics 
                    WHERE symbol_id = ?
                """, (symbol_id,))
                
                row = cursor.fetchone()
                if row:
                    return SymbolAnalytics(
                        symbol_id=row[0],
                        usage_count=row[1],
                        popularity_score=row[2],
                        performance_metrics=json.loads(row[3]),
                        user_feedback=json.loads(row[4]),
                        last_used=datetime.fromisoformat(row[5]) if row[5] else None,
                        created_date=datetime.fromisoformat(row[6]) if row[6] else None
                    )
            
            return None
            
        except Exception as e:
            logger.error(f'Failed to get symbol analytics: {e}')
            return None
    
    def calculate_popularity_score(self, symbol_id: str) -> float:
        """Calculate popularity score for a symbol"""
        try:
            analytics = self.get_symbol_analytics(symbol_id)
            if not analytics:
                return 0.0
            
            # Calculate score based on usage, recency, and user feedback
            usage_factor = min(analytics.usage_count / 100.0, 1.0)
            
            recency_factor = 0.0
            if analytics.last_used:
                days_since_use = (datetime.now() - analytics.last_used).days
                recency_factor = max(0.0, 1.0 - (days_since_use / 365.0))
            
            feedback_factor = 0.0
            if analytics.user_feedback:
                ratings = [f.get("rating", 0) for f in analytics.user_feedback.values()]
                if ratings:
                    feedback_factor = sum(ratings) / len(ratings) / 5.0
            
            # Weighted score
            popularity_score = (usage_factor * 0.5) + (recency_factor * 0.3) + (feedback_factor * 0.2)
            
            return min(1.0, popularity_score)
            
        except Exception as e:
            logger.error(f'Failed to calculate popularity score: {e}')
            return 0.0
    
    # Marketplace Methods
    
    def add_marketplace_item(self, symbol_id: str, author: str, title: str, description: str,
                           category: str, tags: List[str], price: float = 0.0, 
                           license: str = "MIT", metadata: Dict[str, Any] = None) -> bool:
        """Add a symbol to the marketplace"""
        try:
            item = MarketplaceItem(
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
            
            # Store in memory
            self.marketplace_items[symbol_id] = item
            
            # Update indexes
            self.category_index[category].append(symbol_id)
            for tag in tags:
                self.tag_index[tag].add(symbol_id)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO marketplace_items
                    (symbol_id, author, title, description, category, tags, rating, 
                     download_count, price, license, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol_id, author, title, description, category, json.dumps(tags),
                    0.0, 0, price, license, json.dumps(metadata or {})
                ))
                conn.commit()
            
            logger.info(f'Added symbol {symbol_id} to marketplace')
            return True
            
        except Exception as e:
            logger.error(f'Failed to add marketplace item: {e}')
            return False
    
    def search_marketplace(self, query: str = "", category: str = None, 
                          tags: List[str] = None, max_price: float = None) -> List[MarketplaceItem]:
        """Search the marketplace for symbols"""
        try:
            results = []
            
            for symbol_id, item in self.marketplace_items.items():
                # Apply filters
                if category and item.category != category:
                    continue
                
                if max_price and item.price > max_price:
                    continue
                
                if tags and not any(tag in item.tags for tag in tags):
                    continue
                
                # Calculate relevance score
                relevance_score = 0.0
                
                if query:
                    # Text search
                    search_text = f"{item.title} {item.description} {' '.join(item.tags)}".lower()
                    if query.lower() in search_text:
                        relevance_score += 0.5
                    
                    # Title match
                    if query.lower() in item.title.lower():
                        relevance_score += 0.3
                
                # Rating factor
                relevance_score += item.rating * 0.2
                
                if relevance_score > 0.0:
                    results.append((item, relevance_score))
            
            # Sort by relevance and return
            results.sort(key=lambda x: x[1], reverse=True)
            return [item for item, score in results]
            
        except Exception as e:
            logger.error(f'Failed to search marketplace: {e}')
            return []
    
    def rate_marketplace_item(self, symbol_id: str, user_id: str, rating: float, 
                            review: str = None) -> bool:
        """Rate a marketplace item"""
        try:
            if symbol_id not in self.marketplace_items:
                return False
            
            item = self.marketplace_items[symbol_id]
            
            # Update rating
            if not hasattr(item, 'ratings'):
                item.ratings = {}
            
            item.ratings[user_id] = {
                "rating": rating,
                "review": review,
                "timestamp": datetime.now().isoformat()
            }
            
            # Calculate new average rating
            ratings = [r["rating"] for r in item.ratings.values()]
            item.rating = sum(ratings) / len(ratings)
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE marketplace_items 
                    SET rating = ?
                    WHERE symbol_id = ?
                """, (item.rating, symbol_id))
                conn.commit()
            
            logger.info(f'Updated rating for marketplace item {symbol_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to rate marketplace item: {e}')
            return False
    
    # Utility Methods
    
    def _calculate_compression_ratio(self, content: str) -> float:
        """Calculate compression ratio for content"""
        try:
            original_size = len(content.encode('utf-8'))
            compressed_size = len(zlib.compress(content.encode('utf-8')))
            return (original_size - compressed_size) / original_size
        except Exception:
            return 0.0
    
    def _extract_search_features(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract searchable features from symbol content"""
        features = {
            "text_content": content.lower(),
            "word_count": len(content.split()),
            "lines": len(content.splitlines()),
            "has_svg_tags": "<svg" in content.lower(),
            "has_paths": "<path" in content.lower(),
            "has_groups": "<g" in content.lower(),
            "has_text": "<text" in content.lower(),
            "metadata": metadata or {}
        }
        
        # Extract tags and attributes
        svg_tags = re.findall(r'<(\w+)', content.lower())
        features["svg_tags"] = list(set(svg_tags))
        
        # Extract colors
        colors = re.findall(r'#[0-9a-fA-F]{6}', content)
        features["colors"] = list(set(colors))
        
        return features
    
    def _extract_query_features(self, query: str) -> Dict[str, Any]:
        """Extract features from search query"""
        return {
            "query_text": query.lower(),
            "words": query.lower().split(),
            "has_svg_terms": any(term in query.lower() for term in ["svg", "path", "group", "text"]),
            "has_color_terms": any(term in query.lower() for term in ["color", "fill", "stroke"]),
            "query_length": len(query)
        }
    
    def _calculate_search_score(self, query_features: Dict[str, Any], 
                              symbol_features: Dict[str, Any]) -> float:
        """Calculate search relevance score"""
        score = 0.0
        
        # Text matching
        query_words = set(query_features["words"])
        symbol_words = set(symbol_features["text_content"].split())
        
        if query_words:
            word_overlap = len(query_words.intersection(symbol_words)) / len(query_words)
            score += word_overlap * 0.4
        
        # Exact text match
        if query_features["query_text"] in symbol_features["text_content"]:
            score += 0.3
        
        # SVG-specific features
        if query_features["has_svg_terms"] and symbol_features["has_svg_tags"]:
            score += 0.2
        
        # Color matching
        if query_features["has_color_terms"] and symbol_features["colors"]:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate similarity between two symbol feature sets"""
        similarity = 0.0
        
        # Tag similarity
        tags1 = set(features1.get("svg_tags", []))
        tags2 = set(features2.get("svg_tags", []))
        if tags1 and tags2:
            tag_similarity = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
            similarity += tag_similarity * 0.3
        
        # Color similarity
        colors1 = set(features1.get("colors", []))
        colors2 = set(features2.get("colors", []))
        if colors1 and colors2:
            color_similarity = len(colors1.intersection(colors2)) / len(colors1.union(colors2))
            similarity += color_similarity * 0.2
        
        # Size similarity
        size1 = features1.get("word_count", 0)
        size2 = features2.get("word_count", 0)
        if size1 and size2:
            size_similarity = 1.0 - abs(size1 - size2) / max(size1, size2)
            similarity += size_similarity * 0.1
        
        return min(1.0, similarity)
    
    def _get_relevance_factors(self, query_features: Dict[str, Any], 
                              symbol_features: Dict[str, Any]) -> List[str]:
        """Get factors that contributed to search relevance"""
        factors = []
        
        if query_features["query_text"] in symbol_features["text_content"]:
            factors.append("exact_text_match")
        
        if query_features["has_svg_terms"] and symbol_features["has_svg_tags"]:
            factors.append("svg_content")
        
        if query_features["has_color_terms"] and symbol_features["colors"]:
            factors.append("color_content")
        
        return factors
    
    def _apply_search_filters(self, results: List[SymbolSearchResult], 
                            filters: Dict[str, Any]) -> List[SymbolSearchResult]:
        """Apply filters to search results"""
        filtered_results = []
        
        for result in results:
            include = True
            
            # Category filter
            if "category" in filters and result.metadata.get("category") != filters["category"]:
                include = False
            
            # Rating filter
            if "min_rating" in filters and result.usage_stats.get("rating", 0) < filters["min_rating"]:
                include = False
            
            # Usage filter
            if "min_usage" in filters and result.usage_stats.get("usage_count", 0) < filters["min_usage"]:
                include = False
            
            if include:
                filtered_results.append(result)
        
        return filtered_results
    
    def _symbol_exists(self, symbol_id: str) -> bool:
        """Check if a symbol exists"""
        return symbol_id in self.current_versions
    
    def _check_version_constraint(self, dependency: SymbolDependency) -> bool:
        """Check if a dependency version constraint is satisfied"""
        # Simplified version constraint checking
        return self._symbol_exists(dependency.dependency_id)
    
    def _update_analytics_in_db(self, analytics: SymbolAnalytics):
        """Update analytics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO symbol_analytics
                    (symbol_id, usage_count, popularity_score, performance_metrics,
                     user_feedback, last_used, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    analytics.symbol_id, analytics.usage_count, analytics.popularity_score,
                    json.dumps(analytics.performance_metrics), json.dumps(analytics.user_feedback),
                    analytics.last_used.isoformat() if analytics.last_used else None,
                    analytics.created_date.isoformat() if analytics.created_date else None
                ))
                conn.commit()
        except Exception as e:
            logger.error(f'Failed to update analytics in database: {e}')
    
    def get_current_content(self, symbol_id: str) -> str:
        """Get current content for a symbol"""
        current_version = self.get_symbol_version(symbol_id)
        return current_version.content if current_version else ""
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # End all active collaboration sessions
            for session_id in list(self.active_sessions.keys()):
                self.end_collaboration_session(session_id)
            
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            logger.info('Advanced Symbol Management cleanup completed')
        except Exception as e:
            logger.error(f'Cleanup error: {e}')
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'total_symbols': len(self.current_versions),
            'total_versions': sum(len(versions) for versions in self.version_graph.values()),
            'active_sessions': len(self.active_sessions),
            'search_index_size': len(self.search_index),
            'marketplace_items': len(self.marketplace_items),
            'dependency_relationships': sum(len(deps) for deps in self.dependency_graph.values()),
            'analytics_tracked': len(self.usage_tracking)
        } 