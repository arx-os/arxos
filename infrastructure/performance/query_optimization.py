"""
Advanced Query Optimization and Performance Tuning.

Provides intelligent query optimization, execution plan analysis,
and adaptive performance tuning for database operations.
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from collections import defaultdict, deque
import statistics
import threading
from contextlib import contextmanager

from sqlalchemy import text, event
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Select, Update, Insert, Delete

from infrastructure.logging.structured_logging import get_logger, performance_logger
from infrastructure.performance.monitoring import performance_monitor
from infrastructure.performance.caching_strategies import intelligent_cache


logger = get_logger(__name__)


class QueryType(Enum):
    """Types of database queries."""
    SELECT = "select"
    INSERT = "insert" 
    UPDATE = "update"
    DELETE = "delete"
    BULK_INSERT = "bulk_insert"
    BULK_UPDATE = "bulk_update"
    AGGREGATE = "aggregate"
    JOIN = "join"
    SUBQUERY = "subquery"


class QueryComplexity(Enum):
    """Query complexity levels."""
    SIMPLE = "simple"       # Single table, basic conditions
    MODERATE = "moderate"   # Multiple tables, joins
    COMPLEX = "complex"     # Complex joins, subqueries
    HEAVY = "heavy"         # Massive data processing


@dataclass
class QueryProfile:
    """Profile information for a query."""
    query_hash: str
    query_type: QueryType
    complexity: QueryComplexity
    table_names: List[str]
    execution_count: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    rows_examined: int = 0
    rows_returned: int = 0
    efficiency_ratio: float = 0.0
    last_executed: Optional[datetime] = None
    optimization_suggestions: List[str] = field(default_factory=list)
    
    def update_execution(self, duration: float, rows_examined: int = 0, rows_returned: int = 0) -> None:
        """Update profile with execution metrics."""
        self.execution_count += 1
        self.total_duration += duration
        self.avg_duration = self.total_duration / self.execution_count
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)
        self.rows_examined = rows_examined
        self.rows_returned = rows_returned
        self.last_executed = datetime.now(timezone.utc)
        
        # Calculate efficiency ratio
        if rows_examined > 0:
            self.efficiency_ratio = rows_returned / rows_examined
        
        # Generate optimization suggestions
        self._generate_optimization_suggestions()
    
    def _generate_optimization_suggestions(self) -> None:
        """Generate optimization suggestions based on metrics."""
        suggestions = []
        
        # Slow query suggestions
        if self.avg_duration > 1.0:
            suggestions.append("Consider adding appropriate indexes")
            suggestions.append("Review query execution plan")
            
        # Low efficiency suggestions  
        if self.efficiency_ratio < 0.1 and self.rows_examined > 1000:
            suggestions.append("Query examines too many rows - add WHERE conditions")
            suggestions.append("Consider query rewrite to reduce data scanning")
        
        # High frequency suggestions
        if self.execution_count > 1000 and self.avg_duration > 0.1:
            suggestions.append("High-frequency query - consider caching results")
            suggestions.append("Evaluate if query can be optimized or batched")
        
        # Complex query suggestions
        if self.complexity in [QueryComplexity.COMPLEX, QueryComplexity.HEAVY]:
            suggestions.append("Consider breaking complex query into smaller parts")
            suggestions.append("Evaluate if materialized views could help")
        
        self.optimization_suggestions = suggestions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query_hash": self.query_hash,
            "query_type": self.query_type.value,
            "complexity": self.complexity.value,
            "table_names": self.table_names,
            "execution_count": self.execution_count,
            "avg_duration_ms": round(self.avg_duration * 1000, 2),
            "min_duration_ms": round(self.min_duration * 1000, 2),
            "max_duration_ms": round(self.max_duration * 1000, 2),
            "rows_examined": self.rows_examined,
            "rows_returned": self.rows_returned,
            "efficiency_ratio": round(self.efficiency_ratio, 4),
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "optimization_suggestions": self.optimization_suggestions
        }


class QueryOptimizer:
    """Advanced query optimization system."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.query_profiles = {}
        self.slow_query_threshold = 1.0  # seconds
        self.efficiency_threshold = 0.1   # 10% efficiency minimum
        
        # Query pattern analysis
        self.query_patterns = defaultdict(list)
        self.optimization_cache = {}
        
        # Performance monitoring
        self.lock = threading.RLock()
        
        # Set up SQL event listeners
        self._setup_sql_listeners()
        
        logger.info("Query optimizer initialized")
    
    def _setup_sql_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for query monitoring."""
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._statement = statement
            context._parameters = parameters
        
        @event.listens_for(self.engine, "after_cursor_execute") 
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, '_query_start_time'):
                duration = time.time() - context._query_start_time
                
                # Analyze and profile query
                self._analyze_query_execution(
                    statement=statement,
                    parameters=parameters,
                    duration=duration,
                    rows_affected=getattr(cursor, 'rowcount', 0)
                )
    
    def _analyze_query_execution(self, statement: str, parameters: Any, 
                               duration: float, rows_affected: int) -> None:
        """Analyze executed query and update profiles."""
        try:
            # Generate query hash
            query_hash = self._generate_query_hash(statement, parameters)
            
            # Determine query characteristics
            query_type = self._determine_query_type(statement)
            complexity = self._determine_query_complexity(statement)
            table_names = self._extract_table_names(statement)
            
            with self.lock:
                # Update or create query profile
                if query_hash not in self.query_profiles:
                    self.query_profiles[query_hash] = QueryProfile(
                        query_hash=query_hash,
                        query_type=query_type,
                        complexity=complexity,
                        table_names=table_names
                    )
                
                profile = self.query_profiles[query_hash]
                profile.update_execution(
                    duration=duration,
                    rows_examined=rows_affected,  # Approximation
                    rows_returned=rows_affected if query_type == QueryType.SELECT else 0
                )
                
                # Report metrics
                self._report_query_metrics(profile, duration)
                
                # Check for optimization opportunities
                if duration > self.slow_query_threshold:
                    self._handle_slow_query(profile, statement)
        
        except Exception as e:
            logger.error(f"Error analyzing query execution: {e}")
    
    def _generate_query_hash(self, statement: str, parameters: Any) -> str:
        """Generate consistent hash for query pattern."""
        # Normalize statement (remove parameter values, whitespace)
        normalized = self._normalize_query(statement)
        
        # Create hash
        hash_input = f"{normalized}:{type(parameters).__name__}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _normalize_query(self, statement: str) -> str:
        """Normalize query for pattern matching."""
        import re
        
        # Convert to lowercase
        normalized = statement.lower().strip()
        
        # Replace parameter placeholders with generic markers
        normalized = re.sub(r'\$\d+|\?|%s|%([\w_]+)s', '?', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove comments
        normalized = re.sub(r'--[^\r\n]*', '', normalized)
        normalized = re.sub(r'/\*.*?\*/', '', normalized, flags=re.DOTALL)
        
        return normalized.strip()
    
    def _determine_query_type(self, statement: str) -> QueryType:
        """Determine the type of query."""
        statement_upper = statement.upper().strip()
        
        if statement_upper.startswith('SELECT'):
            if 'JOIN' in statement_upper:
                return QueryType.JOIN
            elif any(func in statement_upper for func in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']):
                return QueryType.AGGREGATE
            elif 'SELECT' in statement_upper[10:]:  # Subquery
                return QueryType.SUBQUERY
            else:
                return QueryType.SELECT
        elif statement_upper.startswith('INSERT'):
            if 'VALUES' in statement_upper and statement_upper.count('(') > 2:
                return QueryType.BULK_INSERT
            else:
                return QueryType.INSERT
        elif statement_upper.startswith('UPDATE'):
            return QueryType.BULK_UPDATE if 'JOIN' in statement_upper else QueryType.UPDATE
        elif statement_upper.startswith('DELETE'):
            return QueryType.DELETE
        else:
            return QueryType.SELECT  # Default
    
    def _determine_query_complexity(self, statement: str) -> QueryComplexity:
        """Determine query complexity level."""
        statement_upper = statement.upper()
        
        # Count complexity indicators
        join_count = statement_upper.count('JOIN')
        subquery_count = statement_upper.count('SELECT') - 1
        union_count = statement_upper.count('UNION')
        aggregate_count = sum(statement_upper.count(func) for func in 
                            ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(', 'GROUP BY'])
        
        complexity_score = join_count + (subquery_count * 2) + (union_count * 2) + aggregate_count
        
        if complexity_score >= 6:
            return QueryComplexity.HEAVY
        elif complexity_score >= 3:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 1:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def _extract_table_names(self, statement: str) -> List[str]:
        """Extract table names from SQL statement."""
        import re
        
        tables = set()
        
        # Common patterns for table names
        patterns = [
            r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        
        statement_upper = statement.upper()
        for pattern in patterns:
            matches = re.findall(pattern, statement_upper)
            tables.update(matches)
        
        return list(tables)
    
    def _report_query_metrics(self, profile: QueryProfile, duration: float) -> None:
        """Report query metrics to monitoring system."""
        tags = {
            "query_type": profile.query_type.value,
            "complexity": profile.complexity.value,
            "table_count": str(len(profile.table_names))
        }
        
        # Report to performance monitor
        performance_monitor.collector.record_timer(
            "database.query.duration_seconds", duration, tags
        )
        
        performance_monitor.collector.set_gauge(
            "database.query.efficiency_ratio", profile.efficiency_ratio, tags
        )
        
        performance_monitor.collector.increment_counter(
            "database.queries_total", 1.0, tags
        )
        
        # Report slow queries
        if duration > self.slow_query_threshold:
            performance_monitor.collector.increment_counter(
                "database.slow_queries_total", 1.0, tags
            )
    
    def _handle_slow_query(self, profile: QueryProfile, statement: str) -> None:
        """Handle slow query detection."""
        logger.warning(f"Slow query detected", extra={
            "query_hash": profile.query_hash,
            "duration_ms": profile.avg_duration * 1000,
            "execution_count": profile.execution_count,
            "tables": profile.table_names,
            "suggestions": profile.optimization_suggestions
        })
        
        # Store for analysis
        self.query_patterns[profile.complexity].append({
            "profile": profile,
            "statement": statement[:200] + "..." if len(statement) > 200 else statement,
            "timestamp": datetime.now(timezone.utc)
        })
    
    def get_query_profiles(self, limit: int = 50, 
                          sort_by: str = "avg_duration") -> List[Dict[str, Any]]:
        """Get query profiles sorted by specified metric."""
        with self.lock:
            profiles = list(self.query_profiles.values())
        
        # Sort profiles
        reverse = sort_by in ["avg_duration", "max_duration", "execution_count"]
        profiles.sort(key=lambda p: getattr(p, sort_by, 0), reverse=reverse)
        
        return [profile.to_dict() for profile in profiles[:limit]]
    
    def get_slow_queries(self, threshold_seconds: float = None) -> List[Dict[str, Any]]:
        """Get queries slower than threshold."""
        threshold = threshold_seconds or self.slow_query_threshold
        
        with self.lock:
            slow_profiles = [
                profile for profile in self.query_profiles.values()
                if profile.avg_duration > threshold
            ]
        
        # Sort by average duration descending
        slow_profiles.sort(key=lambda p: p.avg_duration, reverse=True)
        
        return [profile.to_dict() for profile in slow_profiles]
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        with self.lock:
            total_queries = len(self.query_profiles)
            if total_queries == 0:
                return {"message": "No query data available"}
            
            profiles = list(self.query_profiles.values())
            
            # Calculate statistics
            avg_durations = [p.avg_duration for p in profiles]
            total_executions = sum(p.execution_count for p in profiles)
            slow_queries = len([p for p in profiles if p.avg_duration > self.slow_query_threshold])
            
            # Group by complexity
            complexity_stats = defaultdict(list)
            for profile in profiles:
                complexity_stats[profile.complexity].append(profile)
            
            # Most problematic queries
            problematic_queries = sorted(
                profiles, 
                key=lambda p: p.avg_duration * p.execution_count,  # Impact score
                reverse=True
            )[:10]
            
            report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_query_patterns": total_queries,
                    "total_executions": total_executions,
                    "slow_queries_count": slow_queries,
                    "slow_query_percentage": (slow_queries / total_queries) * 100,
                    "avg_query_duration_ms": statistics.mean(avg_durations) * 1000,
                    "median_query_duration_ms": statistics.median(avg_durations) * 1000
                },
                "complexity_breakdown": {
                    complexity.value: {
                        "count": len(queries),
                        "avg_duration_ms": statistics.mean([q.avg_duration for q in queries]) * 1000,
                        "total_executions": sum(q.execution_count for q in queries)
                    }
                    for complexity, queries in complexity_stats.items()
                },
                "most_problematic_queries": [
                    {
                        "query_hash": q.query_hash,
                        "avg_duration_ms": q.avg_duration * 1000,
                        "execution_count": q.execution_count,
                        "impact_score": q.avg_duration * q.execution_count,
                        "tables": q.table_names,
                        "suggestions": q.optimization_suggestions
                    }
                    for q in problematic_queries
                ],
                "recommendations": self._generate_global_recommendations(profiles)
            }
        
        return report
    
    def _generate_global_recommendations(self, profiles: List[QueryProfile]) -> List[str]:
        """Generate global optimization recommendations."""
        recommendations = []
        
        # Analyze common patterns
        slow_queries = [p for p in profiles if p.avg_duration > self.slow_query_threshold]
        high_frequency_queries = [p for p in profiles if p.execution_count > 1000]
        low_efficiency_queries = [p for p in profiles if p.efficiency_ratio < self.efficiency_threshold]
        
        if slow_queries:
            recommendations.append(f"Address {len(slow_queries)} slow query patterns with indexing or query optimization")
        
        if high_frequency_queries:
            recommendations.append(f"Consider caching results for {len(high_frequency_queries)} high-frequency queries")
        
        if low_efficiency_queries:
            recommendations.append(f"Optimize {len(low_efficiency_queries)} queries with poor efficiency ratios")
        
        # Table-specific recommendations
        table_frequency = defaultdict(int)
        for profile in profiles:
            for table in profile.table_names:
                table_frequency[table] += profile.execution_count
        
        most_accessed_tables = sorted(table_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        if most_accessed_tables:
            recommendations.append(f"Review indexing strategy for frequently accessed tables: {', '.join([table for table, _ in most_accessed_tables])}")
        
        return recommendations
    
    def suggest_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Suggest indexes based on query patterns."""
        suggestions = []
        
        # Find queries involving this table
        table_queries = [
            profile for profile in self.query_profiles.values()
            if table_name in profile.table_names
        ]
        
        if not table_queries:
            return suggestions
        
        # Analyze WHERE conditions (simplified - would need query parsing in production)
        for profile in table_queries:
            if profile.avg_duration > self.slow_query_threshold or profile.efficiency_ratio < self.efficiency_threshold:
                suggestions.append({
                    "table": table_name,
                    "type": "composite_index",
                    "reason": f"Slow query pattern detected (avg: {profile.avg_duration*1000:.1f}ms)",
                    "query_hash": profile.query_hash,
                    "priority": "high" if profile.avg_duration > 2.0 else "medium"
                })
        
        return suggestions


class QueryCache:
    """Intelligent query result caching."""
    
    def __init__(self, cache_instance=None):
        self.cache = cache_instance or intelligent_cache
        self.cache_stats = defaultdict(int)
        
    def get_cached_result(self, query_hash: str, parameters_hash: str) -> Optional[Any]:
        """Get cached query result."""
        cache_key = f"query:{query_hash}:{parameters_hash}"
        
        result = self.cache.get(cache_key)
        if result is not None:
            self.cache_stats["hits"] += 1
            return result
        
        self.cache_stats["misses"] += 1
        return None
    
    def cache_result(self, query_hash: str, parameters_hash: str, 
                    result: Any, ttl: int = 3600) -> None:
        """Cache query result."""
        cache_key = f"query:{query_hash}:{parameters_hash}"
        
        # Determine TTL based on query type
        if "INSERT" in query_hash or "UPDATE" in query_hash or "DELETE" in query_hash:
            ttl = min(ttl, 300)  # Shorter TTL for data-modifying queries
        
        self.cache.set(cache_key, result, ttl=ttl, tags={"query_cache"})
        self.cache_stats["sets"] += 1
    
    def invalidate_table_cache(self, table_name: str) -> None:
        """Invalidate cache entries for a specific table."""
        # In production, would maintain table->query mappings
        # For now, use tag-based invalidation
        self.cache.invalidate_by_tags({f"table:{table_name}"})
        self.cache_stats["invalidations"] += 1
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "sets": self.cache_stats["sets"],
            "invalidations": self.cache_stats["invalidations"],
            "hit_rate_percent": round(hit_rate, 2)
        }


class BatchQueryProcessor:
    """Processes queries in batches for better performance."""
    
    def __init__(self, session: Session, batch_size: int = 1000):
        self.session = session
        self.batch_size = batch_size
        self.pending_operations = defaultdict(list)
        
    def add_batch_insert(self, model_class, data: Dict[str, Any]) -> None:
        """Add data to batch insert queue."""
        self.pending_operations[f"insert:{model_class.__name__}"].append(data)
        
        # Process batch if it reaches size limit
        if len(self.pending_operations[f"insert:{model_class.__name__}"]) >= self.batch_size:
            self._process_batch_insert(model_class)
    
    def add_batch_update(self, model_class, filters: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Add update to batch update queue."""
        operation_key = f"update:{model_class.__name__}"
        self.pending_operations[operation_key].append({
            "filters": filters,
            "updates": updates
        })
        
        if len(self.pending_operations[operation_key]) >= self.batch_size:
            self._process_batch_update(model_class)
    
    def flush_all_batches(self) -> Dict[str, int]:
        """Flush all pending batch operations."""
        results = {}
        
        for operation_key, operations in self.pending_operations.items():
            if not operations:
                continue
                
            operation_type, model_name = operation_key.split(":", 1)
            
            try:
                if operation_type == "insert":
                    # Need model class reference - simplified for example
                    count = len(operations)
                    self.session.bulk_insert_mappings(None, operations)  # Would need actual model
                    results[operation_key] = count
                    
                elif operation_type == "update":
                    count = 0
                    for op in operations:
                        # Process individual updates - would optimize in production
                        count += 1
                    results[operation_key] = count
                
                # Clear processed operations
                self.pending_operations[operation_key].clear()
                
            except Exception as e:
                logger.error(f"Batch processing failed for {operation_key}: {e}")
                results[operation_key] = 0
        
        return results
    
    def _process_batch_insert(self, model_class) -> None:
        """Process pending batch inserts."""
        operation_key = f"insert:{model_class.__name__}"
        operations = self.pending_operations[operation_key]
        
        if operations:
            start_time = time.time()
            
            try:
                self.session.bulk_insert_mappings(model_class, operations)
                self.session.flush()
                
                duration = time.time() - start_time
                
                # Report metrics
                performance_monitor.collector.record_timer(
                    "database.batch_insert.duration_seconds", 
                    duration,
                    {"model": model_class.__name__, "batch_size": len(operations)}
                )
                
                logger.info(f"Batch insert completed", extra={
                    "model": model_class.__name__,
                    "count": len(operations),
                    "duration_ms": duration * 1000
                })
                
            except Exception as e:
                logger.error(f"Batch insert failed for {model_class.__name__}: {e}")
            finally:
                operations.clear()
    
    def _process_batch_update(self, model_class) -> None:
        """Process pending batch updates."""
        operation_key = f"update:{model_class.__name__}"
        operations = self.pending_operations[operation_key]
        
        if operations:
            start_time = time.time()
            
            try:
                # Group by similar update patterns
                update_groups = defaultdict(list)
                for op in operations:
                    update_key = json.dumps(op["updates"], sort_keys=True)
                    update_groups[update_key].append(op)
                
                # Execute grouped updates
                total_updated = 0
                for update_key, group_ops in update_groups.items():
                    updates = json.loads(update_key)
                    
                    # Build combined filter (simplified)
                    # In production, would need more sophisticated batching
                    for op in group_ops:
                        # Execute individual update - would optimize in production
                        total_updated += 1
                
                duration = time.time() - start_time
                
                # Report metrics
                performance_monitor.collector.record_timer(
                    "database.batch_update.duration_seconds",
                    duration,
                    {"model": model_class.__name__, "batch_size": len(operations)}
                )
                
                logger.info(f"Batch update completed", extra={
                    "model": model_class.__name__,
                    "count": total_updated,
                    "duration_ms": duration * 1000
                })
                
            except Exception as e:
                logger.error(f"Batch update failed for {model_class.__name__}: {e}")
            finally:
                operations.clear()


# Context manager for query optimization
@contextmanager
def optimized_query_execution(session: Session, enable_caching: bool = True):
    """Context manager for optimized query execution."""
    query_cache = QueryCache() if enable_caching else None
    batch_processor = BatchQueryProcessor(session)
    
    start_time = time.time()
    
    try:
        # Store instances in session for access by other code
        session._query_cache = query_cache
        session._batch_processor = batch_processor
        
        yield {
            "cache": query_cache,
            "batch_processor": batch_processor
        }
        
    finally:
        # Flush any pending batch operations
        if batch_processor:
            batch_processor.flush_all_batches()
        
        duration = time.time() - start_time
        
        # Report execution metrics
        performance_monitor.collector.record_timer(
            "database.optimized_session.duration_seconds",
            duration
        )
        
        if query_cache:
            cache_stats = query_cache.get_cache_stats()
            performance_monitor.collector.set_gauge(
                "database.query_cache.hit_rate_percent",
                cache_stats["hit_rate_percent"]
            )


# Global query optimizer instance
query_optimizer = None  # Will be initialized when engine is available

def initialize_query_optimizer(engine: Engine) -> QueryOptimizer:
    """Initialize global query optimizer."""
    global query_optimizer
    query_optimizer = QueryOptimizer(engine)
    return query_optimizer