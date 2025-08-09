"""
Cache Manager

This module provides cache management functionality for the infrastructure layer.
"""

import logging
from typing import Any, Optional, Dict, List
from abc import ABC, abstractmethod

from .cache_strategy import CacheStrategy

logger = logging.getLogger(__name__)


class CacheManager:
    """Cache manager for handling multiple cache strategies."""

    def __init__(self):
        """Initialize cache manager."""
        self.strategies: Dict[str, CacheStrategy] = {}
        self.default_strategy: Optional[str] = None

    def add_strategy(self, name: str, strategy: CacheStrategy) -> None:
        """Add a cache strategy."""
        self.strategies[name] = strategy
        if self.default_strategy is None:
            self.default_strategy = name
        logger.info(f"Added cache strategy: {name}")

    def get_strategy(self, name: Optional[str] = None) -> Optional[CacheStrategy]:
        """Get a cache strategy by name."""
        strategy_name = name or self.default_strategy
        if strategy_name and strategy_name in self.strategies:
            return self.strategies[strategy_name]
        return None

    def get(self, key: str, strategy_name: Optional[str] = None) -> Optional[Any]:
        """Get a value from cache using the specified strategy."""
        strategy = self.get_strategy(strategy_name)
        if strategy:
            return strategy.get(key)
        logger.warning(f"No cache strategy available for key: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None,
            strategy_name: Optional[str] = None) -> bool:
        """Set a value in cache using the specified strategy."""
        strategy = self.get_strategy(strategy_name)
        if strategy:
            return strategy.set(key, value, ttl)
        logger.warning(f"No cache strategy available for key: {key}")
        return False

    def delete(self, key: str, strategy_name: Optional[str] = None) -> bool:
        """Delete a key from cache using the specified strategy."""
        strategy = self.get_strategy(strategy_name)
        if strategy:
            return strategy.delete(key)
        logger.warning(f"No cache strategy available for key: {key}")
        return False

    def clear_all(self) -> Dict[str, bool]:
        """Clear all caches."""
        results = {}
        for name, strategy in self.strategies.items():
            try:
                results[name] = strategy.clear()
            except Exception as e:
                logger.error(f"Error clearing cache strategy {name}: {e}")
                results[name] = False
        return results

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all cache strategies."""
        health_status = {
            "status": "healthy",
            "strategies": {}
        }

        for name, strategy in self.strategies.items():
            try:
                strategy_health = strategy.health_check()
                health_status["strategies"][name] = strategy_health
                if strategy_health.get("status") != "healthy":
                    health_status["status"] = "unhealthy"
            except Exception as e:
                logger.error(f"Error checking health of cache strategy {name}: {e}")
                health_status["strategies"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "unhealthy"

        return health_status

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all cache strategies."""
        stats = {
            "total_strategies": len(self.strategies),
            "default_strategy": self.default_strategy,
            "strategies": {}
        }

        for name, strategy in self.strategies.items():
            try:
                stats["strategies"][name] = strategy.get_stats()
            except Exception as e:
                logger.error(f"Error getting stats for cache strategy {name}: {e}")
                stats["strategies"][name] = {"error": str(e)}

        return stats
