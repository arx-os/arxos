package services

// Global cache service instance
var globalCacheService *CacheService

// SetCacheService sets the global cache service instance
func SetCacheService(cacheService *CacheService) {
	globalCacheService = cacheService
}

// GetCacheService returns the global cache service instance
func GetCacheService() *CacheService {
	return globalCacheService
}