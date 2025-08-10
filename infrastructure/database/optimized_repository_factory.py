"""
Optimized Repository Factory

Provides optimized repository instances with advanced caching,
query optimization, and performance monitoring capabilities.
"""

from typing import Type, TypeVar, Dict, Any, Optional
from functools import lru_cache
import threading
import time
from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from domain.repositories import (
    BuildingRepository, FloorRepository, RoomRepository, 
    DeviceRepository, UserRepository, ProjectRepository
)
from infrastructure.repositories.building_repository import SQLAlchemyBuildingRepository
from infrastructure.repositories.floor_repository import SQLAlchemyFloorRepository
from infrastructure.repositories.room_repository import SQLAlchemyRoomRepository
from infrastructure.repositories.device_repository import SQLAlchemyDeviceRepository
from infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from infrastructure.repositories.project_repository import SQLAlchemyProjectRepository

from infrastructure.database.query_optimization import (
    OptimizedConnectionPool, DatabaseOptimizer, DatabaseHealthChecker,
    optimized_session
)
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.logging.structured_logging import get_logger, performance_logger
from infrastructure.error_handling import handle_database_operation

T = TypeVar('T')

logger = get_logger(__name__)


class CachedRepository:
    """Wrapper that adds caching capabilities to repositories."""
    
    def __init__(self, repository: T, cache_service: Optional[RedisCacheService], 
                 entity_name: str, cache_ttl: int = 3600):
        self._repository = repository
        self._cache_service = cache_service
        self._entity_name = entity_name.lower()
        self._cache_ttl = cache_ttl
        self._logger = get_logger(f"repository.cached.{self._entity_name}")
    
    def __getattr__(self, name):
        """Delegate all method calls to the wrapped repository."""
        attr = getattr(self._repository, name)
        
        # If it's a method that might benefit from caching
        if callable(attr) and name.startswith(('get_', 'find_', 'list_')):
            return self._create_cached_method(attr, name)
        
        return attr
    
    def _create_cached_method(self, method, method_name):
        """Create a cached version of a repository method."""
        def cached_method(*args, **kwargs):
            # Generate cache key based on method name and arguments
            cache_key = self._generate_cache_key(method_name, args, kwargs)
            
            # Try to get from cache first
            if self._cache_service:
                try:
                    cached_result = self._cache_service.get(cache_key)
                    if cached_result is not None:
                        self._logger.debug(f"Cache hit for {cache_key}")
                        return cached_result
                except Exception as e:
                    self._logger.warning(f"Cache retrieval failed: {e}")
            
            # Execute the actual method
            start_time = time.time()
            result = method(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result if caching is available
            if self._cache_service and result is not None:
                try:
                    # Determine TTL based on method type
                    ttl = self._determine_cache_ttl(method_name)
                    self._cache_service.set(cache_key, result, ttl=ttl)
                    self._logger.debug(f"Cached result for {cache_key} (TTL: {ttl}s)")
                except Exception as e:
                    self._logger.warning(f"Cache storage failed: {e}")
            
            # Log performance
            performance_logger.log_database_query(
                query_type=f"repository_{method_name}",
                table=self._entity_name,
                duration=execution_time,
                success=True
            )
            
            return result
        
        return cached_method
    
    def _generate_cache_key(self, method_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a cache key from method name and arguments."""
        # Create a simple hash of the arguments
        import hashlib
        arg_str = f"{args}_{sorted(kwargs.items())}"
        arg_hash = hashlib.md5(arg_str.encode()).hexdigest()[:8]
        
        return f"{self._entity_name}:{method_name}:{arg_hash}"
    
    def _determine_cache_ttl(self, method_name: str) -> int:
        """Determine appropriate cache TTL based on method type."""
        if method_name.startswith('get_by_id'):
            return 3600  # 1 hour for specific entity lookups
        elif method_name.startswith('find_'):
            return 1800  # 30 minutes for search results
        elif method_name.startswith('list_'):
            return 600   # 10 minutes for list operations
        else:
            return self._cache_ttl
    
    def invalidate_cache(self, entity_id: Optional[str] = None) -> None:
        """Invalidate cache entries for this repository."""
        if not self._cache_service:
            return
        
        try:
            if entity_id:
                # Invalidate specific entity cache
                pattern = f"{self._entity_name}:*:{entity_id}*"
            else:
                # Invalidate all cache entries for this entity type
                pattern = f"{self._entity_name}:*"
            
            self._cache_service.delete_pattern(pattern)
            self._logger.debug(f"Cache invalidated for pattern: {pattern}")
            
        except Exception as e:
            self._logger.warning(f"Cache invalidation failed: {e}")


class OptimizedRepositoryFactory:
    """Factory for creating optimized repository instances."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern for repository factory."""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, engine: Engine, cache_service: Optional[RedisCacheService] = None):
        """Initialize the optimized repository factory."""
        if hasattr(self, '_initialized'):
            return
        
        self.engine = engine
        self.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        self.cache_service = cache_service
        
        # Initialize database optimizer
        self.db_optimizer = DatabaseOptimizer(engine)
        self.health_checker = DatabaseHealthChecker(engine)
        
        # Repository cache
        self._repository_cache: Dict[str, Any] = {}
        
        # Performance tracking
        self._repository_stats = {}
        
        self._initialized = True
        
        logger.info("Optimized repository factory initialized", extra={
            "cache_enabled": cache_service is not None,
            "optimization_enabled": True
        })
    
    @lru_cache(maxsize=32)
    def get_building_repository(self, session: Optional[Session] = None) -> BuildingRepository:
        """Get optimized building repository instance."""
        return self._create_cached_repository(
            SQLAlchemyBuildingRepository,
            "Building",
            session
        )
    
    @lru_cache(maxsize=32)
    def get_floor_repository(self, session: Optional[Session] = None) -> FloorRepository:
        """Get optimized floor repository instance."""
        return self._create_cached_repository(
            SQLAlchemyFloorRepository,
            "Floor",
            session
        )
    
    @lru_cache(maxsize=32)
    def get_room_repository(self, session: Optional[Session] = None) -> RoomRepository:
        """Get optimized room repository instance."""
        return self._create_cached_repository(
            SQLAlchemyRoomRepository,
            "Room",
            session
        )
    
    @lru_cache(maxsize=32)
    def get_device_repository(self, session: Optional[Session] = None) -> DeviceRepository:
        """Get optimized device repository instance."""
        return self._create_cached_repository(
            SQLAlchemyDeviceRepository,
            "Device",
            session
        )
    
    @lru_cache(maxsize=32)
    def get_user_repository(self, session: Optional[Session] = None) -> UserRepository:
        """Get optimized user repository instance."""
        return self._create_cached_repository(
            SQLAlchemyUserRepository,
            "User",
            session
        )
    
    @lru_cache(maxsize=32)
    def get_project_repository(self, session: Optional[Session] = None) -> ProjectRepository:
        """Get optimized project repository instance."""
        return self._create_cached_repository(
            SQLAlchemyProjectRepository,
            "Project",
            session
        )
    
    def _create_cached_repository(self, repository_class: Type[T], 
                                entity_name: str, session: Optional[Session] = None) -> T:
        """Create a cached repository instance."""
        if session is None:
            session = self.session_factory()
        
        # Create the base repository
        repository = repository_class(session)
        
        # Wrap with caching if cache service is available
        if self.cache_service:
            cached_repo = CachedRepository(
                repository=repository,
                cache_service=self.cache_service,
                entity_name=entity_name
            )
            
            logger.debug(f"Created cached repository for {entity_name}")
            return cached_repo
        else:
            logger.debug(f"Created standard repository for {entity_name}")
            return repository
    
    @contextmanager
    def create_optimized_session(self):
        """Create an optimized database session."""
        with optimized_session(self.session_factory) as session:
            try:
                yield session
            finally:
                # Clear repository cache for this session
                self._repository_cache.clear()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        try:
            db_report = self.db_optimizer.get_performance_report()
            health_report = self.health_checker.check_database_health()
            
            return {
                "timestamp": time.time(),
                "database_performance": db_report,
                "database_health": health_report,
                "repository_stats": self._repository_stats,
                "cache_enabled": self.cache_service is not None
            }
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {"error": str(e)}
    
    def optimize_for_read_heavy_workload(self) -> None:
        """Optimize configuration for read-heavy workloads."""
        logger.info("Optimizing for read-heavy workload")
        
        # Enable aggressive caching
        if self.cache_service:
            # Increase cache TTL for read operations
            for repo_type in ['building', 'floor', 'room', 'device', 'user', 'project']:
                cache_key = f"{repo_type}:read_optimized"
                self.cache_service.set(cache_key, True, ttl=86400)  # 24 hours
    
    def optimize_for_write_heavy_workload(self) -> None:
        """Optimize configuration for write-heavy workloads."""
        logger.info("Optimizing for write-heavy workload")
        
        # Reduce cache TTL to ensure consistency
        if self.cache_service:
            # Reduce cache TTL for write operations
            for repo_type in ['building', 'floor', 'room', 'device', 'user', 'project']:
                cache_key = f"{repo_type}:write_optimized"
                self.cache_service.set(cache_key, True, ttl=300)  # 5 minutes
    
    def clear_all_caches(self) -> None:
        """Clear all repository caches."""
        if not self.cache_service:
            logger.warning("No cache service available")
            return
        
        try:
            # Clear all entity caches
            for entity_type in ['building', 'floor', 'room', 'device', 'user', 'project']:
                pattern = f"{entity_type}:*"
                self.cache_service.delete_pattern(pattern)
            
            logger.info("All repository caches cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear caches: {e}")
    
    def bulk_operation_mode(self):
        """Context manager for bulk operations with optimized settings."""
        return self._bulk_operation_context()
    
    @contextmanager 
    def _bulk_operation_context(self):
        """Context for optimized bulk operations."""
        logger.info("Entering bulk operation mode")
        
        # Temporarily disable cache during bulk operations
        original_cache = self.cache_service
        self.cache_service = None
        
        try:
            yield
            logger.info("Bulk operation completed successfully")
        except Exception as e:
            logger.error(f"Bulk operation failed: {e}")
            raise
        finally:
            # Restore cache and clear all cached data
            self.cache_service = original_cache
            if self.cache_service:
                self.clear_all_caches()
            logger.info("Exited bulk operation mode")


# Global factory instance
_factory_instance: Optional[OptimizedRepositoryFactory] = None


def initialize_optimized_repository_factory(engine: Engine, 
                                          cache_service: Optional[RedisCacheService] = None) -> None:
    """Initialize the global optimized repository factory."""
    global _factory_instance
    _factory_instance = OptimizedRepositoryFactory(engine, cache_service)
    logger.info("Global optimized repository factory initialized")


def get_optimized_repository_factory() -> OptimizedRepositoryFactory:
    """Get the global optimized repository factory instance."""
    if _factory_instance is None:
        raise RuntimeError("Optimized repository factory not initialized. Call initialize_optimized_repository_factory() first.")
    return _factory_instance