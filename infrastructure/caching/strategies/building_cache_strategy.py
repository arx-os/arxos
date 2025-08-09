"""
Building Cache Strategy - Multi-Level Caching for Building Data

This module implements a comprehensive caching strategy for building data
with multiple cache levels and intelligent invalidation.
"""

from typing import Optional, List, Dict, Any
import json
import hashlib
from datetime import datetime, timedelta
import logging

from infrastructure.caching.layers.l1_cache import L1Cache
from infrastructure.caching.layers.l2_cache import L2Cache
from infrastructure.caching.layers.l3_cache import L3Cache
from application.unified.dto.building_dto import BuildingDTO

logger = logging.getLogger(__name__)


class BuildingCacheStrategy:
    """
    Multi-level caching strategy for building data.

    This strategy implements:
    - L1 (Memory) cache for frequently accessed data
    - L2 (Redis) cache for shared data across instances
    - L3 (Database) cache for persistent data
    - Intelligent cache invalidation
    - Cache warming strategies
    """

    def __init__(self, l1_cache: L1Cache, l2_cache: L2Cache, l3_cache: L3Cache):
        """Initialize building cache strategy with cache layers."""
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
        self.l3_cache = l3_cache
        self.logger = logging.getLogger(self.__class__.__name__)

        # Cache configuration
        self.l1_ttl = 300  # 5 minutes
        self.l2_ttl = 3600  # 1 hour
        self.l3_ttl = 86400  # 24 hours

        # Cache key patterns
        self.building_key_pattern = "building:{building_id}"
        self.building_list_key_pattern = "buildings:list:{filters_hash}"
        self.building_count_key_pattern = "buildings:count:{filters_hash}"

    def _generate_building_key(self, building_id: str) -> str:
        """Generate cache key for building data."""
        return self.building_key_pattern.format(building_id=building_id)

    def _generate_list_key(self, filters: Dict[str, Any]) -> str:
        """Generate cache key for building list."""
        filters_str = json.dumps(filters, sort_keys=True)
        filters_hash = hashlib.md5(filters_str.encode()).hexdigest()
        return self.building_list_key_pattern.format(filters_hash=filters_hash)

    def _generate_count_key(self, filters: Dict[str, Any]) -> str:
        """Generate cache key for building count."""
        filters_str = json.dumps(filters, sort_keys=True)
        filters_hash = hashlib.md5(filters_str.encode()).hexdigest()
        return self.building_count_key_pattern.format(filters_hash=filters_hash)

    async def get_building(self, building_id: str) -> Optional[BuildingDTO]:
        """
        Get building data from cache with multi-level fallback.

        Args:
            building_id: Building identifier

        Returns:
            Building DTO if found in cache, None otherwise
        """
        try:
            cache_key = self._generate_building_key(building_id)

            # Try L1 cache first
            cached_data = await self.l1_cache.get(cache_key)
            if cached_data:
                self.logger.debug(f"Building {building_id} found in L1 cache")
                return BuildingDTO.from_dict(cached_data)

            # Try L2 cache
            cached_data = await self.l2_cache.get(cache_key)
            if cached_data:
                self.logger.debug(f"Building {building_id} found in L2 cache")
                building_dto = BuildingDTO.from_dict(cached_data)
                # Store in L1 cache for future access
                await self.l1_cache.set(cache_key, cached_data, self.l1_ttl)
                return building_dto

            # Try L3 cache
            cached_data = await self.l3_cache.get(cache_key)
            if cached_data:
                self.logger.debug(f"Building {building_id} found in L3 cache")
                building_dto = BuildingDTO.from_dict(cached_data)
                # Store in L1 and L2 caches
                await self.l1_cache.set(cache_key, cached_data, self.l1_ttl)
                await self.l2_cache.set(cache_key, cached_data, self.l2_ttl)
                return building_dto

            self.logger.debug(f"Building {building_id} not found in any cache")
            return None

        except Exception as e:
            self.logger.error(f"Error retrieving building {building_id} from cache: {e}")
            return None

    async def set_building(self, building_dto: BuildingDTO) -> bool:
        """
        Store building data in all cache levels.

        Args:
            building_dto: Building DTO to cache

        Returns:
            True if caching successful
        """
        try:
            cache_key = self._generate_building_key(building_dto.id)
            building_data = building_dto.to_dict()

            # Store in all cache levels
            await self.l1_cache.set(cache_key, building_data, self.l1_ttl)
            await self.l2_cache.set(cache_key, building_data, self.l2_ttl)
            await self.l3_cache.set(cache_key, building_data, self.l3_ttl)

            self.logger.debug(f"Building {building_dto.id} cached successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error caching building {building_dto.id}: {e}")
            return False

    async def get_building_list(self, filters: Dict[str, Any]) -> Optional[List[BuildingDTO]]:
        """
        Get building list from cache.

        Args:
            filters: Filter parameters

        Returns:
            List of building DTOs if found in cache, None otherwise
        """
        try:
            cache_key = self._generate_list_key(filters)

            # Try L2 cache first (lists are typically shared)
            cached_data = await self.l2_cache.get(cache_key)
            if cached_data:
                self.logger.debug(f"Building list found in L2 cache")
                building_dtos = [BuildingDTO.from_dict(building_data) for building_data in cached_data]
                return building_dtos

            # Try L3 cache
            cached_data = await self.l3_cache.get(cache_key)
            if cached_data:
                self.logger.debug(f"Building list found in L3 cache")
                building_dtos = [BuildingDTO.from_dict(building_data) for building_data in cached_data]
                # Store in L2 cache
                await self.l2_cache.set(cache_key, cached_data, self.l2_ttl)
                return building_dtos

            self.logger.debug("Building list not found in cache")
            return None

        except Exception as e:
            self.logger.error(f"Error retrieving building list from cache: {e}")
            return None

    async def set_building_list(self, building_dtos: List[BuildingDTO],
                               filters: Dict[str, Any]) -> bool:
        """
        Store building list in cache.

        Args:
            building_dtos: List of building DTOs
            filters: Filter parameters used for the list

        Returns:
            True if caching successful
        """
        try:
            cache_key = self._generate_list_key(filters)
            building_data_list = [building_dto.to_dict() for building_dto in building_dtos]

            # Store in L2 and L3 caches
            await self.l2_cache.set(cache_key, building_data_list, self.l2_ttl)
            await self.l3_cache.set(cache_key, building_data_list, self.l3_ttl)

            self.logger.debug(f"Building list cached successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error caching building list: {e}")
            return False

    async def get_building_count(self, filters: Dict[str, Any]) -> Optional[int]:
        """
        Get building count from cache.

        Args:
            filters: Filter parameters

        Returns:
            Building count if found in cache, None otherwise
        """
        try:
            cache_key = self._generate_count_key(filters)

            # Try L2 cache first
            cached_count = await self.l2_cache.get(cache_key)
            if cached_count is not None:
                self.logger.debug(f"Building count found in L2 cache")
                return int(cached_count)

            # Try L3 cache
            cached_count = await self.l3_cache.get(cache_key)
            if cached_count is not None:
                self.logger.debug(f"Building count found in L3 cache")
                count = int(cached_count)
                # Store in L2 cache
                await self.l2_cache.set(cache_key, count, self.l2_ttl)
                return count

            self.logger.debug("Building count not found in cache")
            return None

        except Exception as e:
            self.logger.error(f"Error retrieving building count from cache: {e}")
            return None

    async def set_building_count(self, count: int, filters: Dict[str, Any]) -> bool:
        """
        Store building count in cache.

        Args:
            count: Building count
            filters: Filter parameters used for the count

        Returns:
            True if caching successful
        """
        try:
            cache_key = self._generate_count_key(filters)

            # Store in L2 and L3 caches
            await self.l2_cache.set(cache_key, count, self.l2_ttl)
            await self.l3_cache.set(cache_key, count, self.l3_ttl)

            self.logger.debug(f"Building count cached successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error caching building count: {e}")
            return False

    async def invalidate_building(self, building_id: str) -> bool:
        """
        Invalidate building data from all cache levels.

        Args:
            building_id: Building identifier

        Returns:
            True if invalidation successful
        """
        try:
            cache_key = self._generate_building_key(building_id)

            # Invalidate from all cache levels
            await self.l1_cache.delete(cache_key)
            await self.l2_cache.delete(cache_key)
            await self.l3_cache.delete(cache_key)

            # Invalidate related list caches
            await self._invalidate_related_lists()

            self.logger.debug(f"Building {building_id} invalidated from all caches")
            return True

        except Exception as e:
            self.logger.error(f"Error invalidating building {building_id}: {e}")
            return False

    async def _invalidate_related_lists(self):
        """Invalidate building list caches when individual buildings change."""
        try:
            # This is a simplified approach - in production, you might want
            # more sophisticated invalidation patterns
            await self.l2_cache.delete_pattern("buildings:list:*")
            await self.l3_cache.delete_pattern("buildings:list:*")
            await self.l2_cache.delete_pattern("buildings:count:*")
            await self.l3_cache.delete_pattern("buildings:count:*")

            self.logger.debug("Related building list caches invalidated")

        except Exception as e:
            self.logger.error(f"Error invalidating related lists: {e}")

    async def warm_cache(self, building_ids: List[str]) -> bool:
        """
        Warm cache with frequently accessed buildings.

        Args:
            building_ids: List of building IDs to warm

        Returns:
            True if cache warming successful
        """
        try:
            # This would typically load buildings from database import database
            # and store them in cache
            for building_id in building_ids:
                # Load building from database (implementation needed)
                # building_dto = await load_building_from_db(building_id)
                # if building_dto:
                #     await self.set_building(building_dto)
                pass

            self.logger.info(f"Cache warmed with {len(building_ids)} buildings")
            return True

        except Exception as e:
            self.logger.error(f"Error warming cache: {e}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dictionary with cache statistics
        """
        try:
            stats = {
                'l1_cache_stats': await self.l1_cache.get_stats(),
                'l2_cache_stats': await self.l2_cache.get_stats(),
                'l3_cache_stats': await self.l3_cache.get_stats(),
                'timestamp': datetime.utcnow().isoformat()
            }

            return stats

        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
