// Package cache provides caching functionality for the API layer
package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/infra/cache"
)

// Manager provides high-level caching operations for API responses
type Manager struct {
	cache      cache.Interface
	prefix     string
	defaultTTL time.Duration
	enabled    bool
}

// Config holds cache manager configuration
type Config struct {
	Prefix     string
	DefaultTTL time.Duration
	Enabled    bool
}

// NewManager creates a new API cache manager
func NewManager(cache cache.Interface, config Config) *Manager {
	if config.Prefix == "" {
		config.Prefix = "arxos:api:"
	}
	if config.DefaultTTL == 0 {
		config.DefaultTTL = 5 * time.Minute
	}

	return &Manager{
		cache:      cache,
		prefix:     config.Prefix,
		defaultTTL: config.DefaultTTL,
		enabled:    config.Enabled,
	}
}

// Get retrieves and unmarshals a cached value
func (m *Manager) Get(ctx context.Context, key string, dest interface{}) error {
	if !m.enabled {
		return ErrCacheDisabled
	}

	fullKey := m.prefix + key

	value, err := m.cache.Get(ctx, fullKey)
	if err != nil {
		return fmt.Errorf("cache get failed: %w", err)
	}

	// Value is stored as interface{}, need to unmarshal
	data, ok := value.([]byte)
	if !ok {
		// Try to marshal it first
		var jsonErr error
		data, jsonErr = json.Marshal(value)
		if jsonErr != nil {
			return fmt.Errorf("cache value not bytes: %w", jsonErr)
		}
	}

	if err := json.Unmarshal(data, dest); err != nil {
		return fmt.Errorf("cache unmarshal failed: %w", err)
	}

	logger.Debug("Cache hit: %s", key)
	return nil
}

// Set marshals and stores a value in cache
func (m *Manager) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	if !m.enabled {
		return nil // Silently succeed when disabled
	}

	fullKey := m.prefix + key

	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("cache marshal failed: %w", err)
	}

	if ttl == 0 {
		ttl = m.defaultTTL
	}

	if err := m.cache.Set(ctx, fullKey, data, ttl); err != nil {
		return fmt.Errorf("cache set failed: %w", err)
	}

	logger.Debug("Cache set: %s (TTL: %v)", key, ttl)
	return nil
}

// Delete removes a key from cache
func (m *Manager) Delete(ctx context.Context, key string) error {
	if !m.enabled {
		return nil
	}

	fullKey := m.prefix + key

	if err := m.cache.Delete(ctx, fullKey); err != nil {
		return fmt.Errorf("cache delete failed: %w", err)
	}

	logger.Debug("Cache deleted: %s", key)
	return nil
}

// DeletePattern removes keys matching a pattern
func (m *Manager) DeletePattern(ctx context.Context, pattern string) error {
	if !m.enabled {
		return nil
	}

	fullPattern := m.prefix + pattern

	if err := m.cache.ClearPattern(ctx, fullPattern); err != nil {
		return fmt.Errorf("cache delete pattern failed: %w", err)
	}

	logger.Debug("Cache pattern deleted: %s", pattern)
	return nil
}

// Exists checks if a key exists in cache
func (m *Manager) Exists(ctx context.Context, key string) (bool, error) {
	if !m.enabled {
		return false, nil
	}

	fullKey := m.prefix + key
	return m.cache.Exists(ctx, fullKey)
}

// Invalidate provides targeted cache invalidation for different entities

// InvalidateBuilding invalidates all building-related cache entries
func (m *Manager) InvalidateBuilding(ctx context.Context, buildingID string) error {
	if !m.enabled {
		return nil
	}

	patterns := []string{
		fmt.Sprintf("buildings:%s*", buildingID),
		"buildings:list*",
		fmt.Sprintf("equipment:building:%s*", buildingID),
		fmt.Sprintf("spatial:building:%s*", buildingID),
	}

	for _, pattern := range patterns {
		if err := m.DeletePattern(ctx, pattern); err != nil {
			logger.Warn("Failed to invalidate pattern %s: %v", pattern, err)
		}
	}

	return nil
}

// InvalidateEquipment invalidates all equipment-related cache entries
func (m *Manager) InvalidateEquipment(ctx context.Context, equipmentID string) error {
	if !m.enabled {
		return nil
	}

	patterns := []string{
		fmt.Sprintf("equipment:%s*", equipmentID),
		"equipment:list*",
		"spatial:*", // Spatial queries include equipment
	}

	for _, pattern := range patterns {
		if err := m.DeletePattern(ctx, pattern); err != nil {
			logger.Warn("Failed to invalidate pattern %s: %v", pattern, err)
		}
	}

	return nil
}

// InvalidateUser invalidates all user-related cache entries
func (m *Manager) InvalidateUser(ctx context.Context, userID string) error {
	if !m.enabled {
		return nil
	}

	patterns := []string{
		fmt.Sprintf("users:%s*", userID),
		"users:list*",
	}

	for _, pattern := range patterns {
		if err := m.DeletePattern(ctx, pattern); err != nil {
			logger.Warn("Failed to invalidate pattern %s: %v", pattern, err)
		}
	}

	return nil
}

// InvalidateOrganization invalidates all organization-related cache entries
func (m *Manager) InvalidateOrganization(ctx context.Context, orgID string) error {
	if !m.enabled {
		return nil
	}

	patterns := []string{
		fmt.Sprintf("organizations:%s*", orgID),
		"organizations:list*",
		fmt.Sprintf("users:org:%s*", orgID),
		fmt.Sprintf("buildings:org:%s*", orgID),
	}

	for _, pattern := range patterns {
		if err := m.DeletePattern(ctx, pattern); err != nil {
			logger.Warn("Failed to invalidate pattern %s: %v", pattern, err)
		}
	}

	return nil
}

// Cache key builders for consistent key generation

// BuildingKey generates a cache key for a building
func BuildingKey(buildingID string) string {
	return fmt.Sprintf("buildings:%s", buildingID)
}

// BuildingListKey generates a cache key for building list
func BuildingListKey(orgID string, limit, offset int) string {
	return fmt.Sprintf("buildings:list:org:%s:limit:%d:offset:%d", orgID, limit, offset)
}

// EquipmentKey generates a cache key for equipment
func EquipmentKey(equipmentID string) string {
	return fmt.Sprintf("equipment:%s", equipmentID)
}

// EquipmentListKey generates a cache key for equipment list
func EquipmentListKey(buildingID string, filters map[string]string, limit, offset int) string {
	key := fmt.Sprintf("equipment:list:building:%s:limit:%d:offset:%d", buildingID, limit, offset)
	for k, v := range filters {
		key += fmt.Sprintf(":%s:%s", k, v)
	}
	return key
}

// UserKey generates a cache key for a user
func UserKey(userID string) string {
	return fmt.Sprintf("users:%s", userID)
}

// OrganizationKey generates a cache key for an organization
func OrganizationKey(orgID string) string {
	return fmt.Sprintf("organizations:%s", orgID)
}

// SpatialQueryKey generates a cache key for spatial queries
func SpatialQueryKey(queryType string, params map[string]interface{}) string {
	key := fmt.Sprintf("spatial:%s", queryType)
	for k, v := range params {
		key += fmt.Sprintf(":%s:%v", k, v)
	}
	return key
}

// Error definitions
var (
	ErrCacheDisabled = fmt.Errorf("cache is disabled")
	ErrCacheMiss     = fmt.Errorf("cache miss")
)
