"""
Database Query Optimization

Provides query optimization patterns, connection pooling configuration,
and performance monitoring for database interactions.
"""

from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import time
import logging
from contextlib import contextmanager
from functools import wraps

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text

from infrastructure.logging.structured_logging import get_logger, performance_logger

T = TypeVar('T')

logger = get_logger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels for optimization strategies."""
    SIMPLE = "simple"          # Simple CRUD operations
    MODERATE = "moderate"      # Joins with 2-3 tables
    COMPLEX = "complex"        # Multiple joins, subqueries
    HEAVY = "heavy"           # Complex aggregations, large datasets


@dataclass
class QueryMetrics:
    """Query performance metrics."""
    query_hash: str
    execution_time: float
    rows_examined: int
    rows_returned: int
    complexity: QueryComplexity
    table_names: List[str]
    slow_query: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "query_hash": self.query_hash,
            "execution_time_ms": round(self.execution_time * 1000, 2),
            "rows_examined": self.rows_examined,
            "rows_returned": self.rows_returned,
            "complexity": self.complexity.value,
            "tables": self.table_names,
            "slow_query": self.slow_query
        }


class DatabaseOptimizer:
    """Database optimization utilities and configuration."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.slow_query_threshold = 1.0  # seconds
        self.query_metrics: List[QueryMetrics] = []
        self.setup_event_listeners()
    
    def setup_event_listeners(self) -> None:
        """Setup SQLAlchemy event listeners for performance monitoring."""
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Called before query execution."""
            context._query_start_time = time.time()
            
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Called after query execution."""
            if hasattr(context, '_query_start_time'):
                execution_time = time.time() - context._query_start_time
                
                # Extract table names from query
                table_names = self._extract_table_names(statement)
                
                # Determine query complexity
                complexity = self._determine_query_complexity(statement, table_names)
                
                # Create metrics
                metrics = QueryMetrics(
                    query_hash=str(hash(statement)),
                    execution_time=execution_time,
                    rows_examined=cursor.rowcount if hasattr(cursor, 'rowcount') else 0,
                    rows_returned=cursor.rowcount if hasattr(cursor, 'rowcount') else 0,
                    complexity=complexity,
                    table_names=table_names,
                    slow_query=execution_time > self.slow_query_threshold
                )
                
                self.query_metrics.append(metrics)
                
                # Log slow queries
                if metrics.slow_query:
                    performance_logger.log_database_query(
                        query_type="slow_query",
                        table=", ".join(table_names) if table_names else "unknown",
                        duration=execution_time,
                        success=True
                    )
                    
                    logger.warning("Slow query detected", extra={
                        "query_metrics": metrics.to_dict(),
                        "statement": statement[:200] + "..." if len(statement) > 200 else statement
                    })
    
    def _extract_table_names(self, statement: str) -> List[str]:
        """Extract table names from SQL statement."""
        import re
        
        # Simple regex to find table names after FROM, JOIN, INTO, UPDATE
        table_patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'INTO\s+(\w+)',
            r'UPDATE\s+(\w+)'
        ]
        
        tables = set()
        for pattern in table_patterns:
            matches = re.findall(pattern, statement.upper())
            tables.update(matches)
        
        return list(tables)
    
    def _determine_query_complexity(self, statement: str, table_names: List[str]) -> QueryComplexity:
        """Determine query complexity based on statement analysis."""
        statement_upper = statement.upper()
        
        # Count complexity indicators
        join_count = statement_upper.count('JOIN')
        subquery_count = statement_upper.count('SELECT') - 1  # Subtract main SELECT
        aggregate_count = len([x for x in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN'] 
                              if x in statement_upper])
        
        if join_count >= 3 or subquery_count >= 2 or aggregate_count >= 3:
            return QueryComplexity.HEAVY
        elif join_count >= 2 or subquery_count >= 1 or aggregate_count >= 2:
            return QueryComplexity.COMPLEX
        elif join_count >= 1 or len(table_names) > 1:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get database performance report."""
        if not self.query_metrics:
            return {"message": "No query metrics available"}
        
        # Calculate statistics
        total_queries = len(self.query_metrics)
        slow_queries = [m for m in self.query_metrics if m.slow_query]
        avg_execution_time = sum(m.execution_time for m in self.query_metrics) / total_queries
        
        # Group by complexity
        complexity_stats = {}
        for complexity in QueryComplexity:
            matching_queries = [m for m in self.query_metrics if m.complexity == complexity]
            if matching_queries:
                complexity_stats[complexity.value] = {
                    "count": len(matching_queries),
                    "avg_time": sum(m.execution_time for m in matching_queries) / len(matching_queries),
                    "slow_queries": len([m for m in matching_queries if m.slow_query])
                }
        
        return {
            "total_queries": total_queries,
            "slow_queries_count": len(slow_queries),
            "slow_query_percentage": (len(slow_queries) / total_queries) * 100,
            "average_execution_time_ms": round(avg_execution_time * 1000, 2),
            "complexity_breakdown": complexity_stats,
            "most_frequent_tables": self._get_most_frequent_tables()
        }
    
    def _get_most_frequent_tables(self) -> Dict[str, int]:
        """Get most frequently queried tables."""
        table_counts = {}
        for metrics in self.query_metrics:
            for table in metrics.table_names:
                table_counts[table] = table_counts.get(table, 0) + 1
        
        # Return top 10 most frequent tables
        return dict(sorted(table_counts.items(), key=lambda x: x[1], reverse=True)[:10])


class OptimizedConnectionPool:
    """Optimized database connection pool configuration."""
    
    @staticmethod
    def create_engine(database_url: str, 
                     pool_size: int = 20,
                     max_overflow: int = 30,
                     pool_timeout: int = 30,
                     pool_recycle: int = 3600,
                     echo_queries: bool = False) -> Engine:
        """Create optimized database engine with connection pooling."""
        
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=echo_queries,
            # Connection pool optimization
            pool_pre_ping=True,  # Validate connections before use
            # Query optimization
            execution_options={
                "autocommit": False,
                "isolation_level": "READ_COMMITTED"
            }
        )
        
        # Add query optimization event listeners
        optimizer = DatabaseOptimizer(engine)
        
        logger.info("Database engine created with optimized connection pool", extra={
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": pool_recycle
        })
        
        return engine
    
    @staticmethod
    def get_pool_status(engine: Engine) -> Dict[str, Any]:
        """Get connection pool status."""
        pool = engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }


class QueryOptimizer:
    """Query optimization utilities."""
    
    @staticmethod
    def optimize_pagination_query(base_query, page: int, page_size: int, 
                                count_query: Optional[Any] = None) -> Dict[str, Any]:
        """Optimize pagination queries."""
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Execute paginated query
        paginated_query = base_query.offset(offset).limit(page_size)
        results = paginated_query.all()
        
        # Get total count if needed (use separate count query if provided)
        if count_query is not None:
            total_count = count_query.scalar()
        else:
            # Fallback to count from base query (less efficient)
            total_count = base_query.count()
        
        return {
            "results": results,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "has_next": offset + page_size < total_count,
            "has_prev": page > 1
        }
    
    @staticmethod
    def batch_load_relationships(session: Session, entities: List[T], 
                               relationship_attr: str) -> List[T]:
        """Batch load relationships to avoid N+1 queries."""
        if not entities:
            return entities
        
        # Extract entity IDs
        entity_ids = [entity.id for entity in entities]
        
        # Load relationships in batch
        from sqlalchemy.orm import selectinload
        relationship_query = session.query(entities[0].__class__).options(
            selectinload(getattr(entities[0].__class__, relationship_attr))
        ).filter(entities[0].__class__.id.in_(entity_ids))
        
        # Create lookup dictionary
        loaded_entities = {entity.id: entity for entity in relationship_query.all()}
        
        # Replace original entities with loaded ones
        return [loaded_entities.get(entity.id, entity) for entity in entities]
    
    @staticmethod
    def bulk_insert_optimized(session: Session, model_class: type, 
                            data_list: List[Dict[str, Any]]) -> None:
        """Optimized bulk insert operation."""
        if not data_list:
            return
        
        try:
            # Use SQLAlchemy bulk_insert_mappings for best performance
            session.bulk_insert_mappings(model_class, data_list)
            session.flush()
            
            performance_logger.log_database_query(
                query_type="bulk_insert",
                table=model_class.__tablename__,
                duration=0,  # Would need timing wrapper
                rows_affected=len(data_list)
            )
            
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk insert failed for {model_class.__name__}: {e}")
            raise


def optimized_query(complexity: QueryComplexity = QueryComplexity.SIMPLE):
    """Decorator for query optimization based on complexity."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log performance
                performance_logger.log_database_query(
                    query_type=f"{complexity.value}_query",
                    table=func.__name__,
                    duration=execution_time,
                    success=True
                )
                
                # Log slow queries
                if execution_time > 1.0:  # 1 second threshold
                    logger.warning(f"Slow {complexity.value} query in {func.__name__}", extra={
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "function": func.__name__,
                        "complexity": complexity.value
                    })
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                performance_logger.log_database_query(
                    query_type=f"{complexity.value}_query",
                    table=func.__name__,
                    duration=execution_time,
                    success=False
                )
                
                logger.error(f"Query failed in {func.__name__}: {e}", extra={
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "complexity": complexity.value
                })
                raise
        
        return wrapper
    return decorator


@contextmanager
def optimized_session(session_factory: sessionmaker):
    """Context manager for optimized database sessions."""
    session = session_factory()
    try:
        # Set session-level optimizations
        session.execute(text("SET SESSION sql_mode = 'STRICT_TRANS_TABLES'"))
        
        yield session
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Session error: {e}")
        raise
    finally:
        session.close()


class DatabaseHealthChecker:
    """Database health monitoring utilities."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def check_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health check."""
        health_status = {
            "database": "unknown",
            "connection_pool": "unknown",
            "query_performance": "unknown",
            "details": {}
        }
        
        try:
            # Test basic connectivity
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            health_status["database"] = "healthy"
            
        except Exception as e:
            health_status["database"] = "unhealthy"
            health_status["details"]["database_error"] = str(e)
        
        try:
            # Check connection pool
            pool_status = OptimizedConnectionPool.get_pool_status(self.engine)
            health_status["details"]["pool_status"] = pool_status
            
            # Determine pool health
            if pool_status["invalid"] > 0:
                health_status["connection_pool"] = "degraded"
            elif pool_status["checked_out"] / pool_status["pool_size"] > 0.8:
                health_status["connection_pool"] = "high_utilization"
            else:
                health_status["connection_pool"] = "healthy"
                
        except Exception as e:
            health_status["connection_pool"] = "unhealthy"
            health_status["details"]["pool_error"] = str(e)
        
        return health_status