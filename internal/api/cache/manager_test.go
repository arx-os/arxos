package cache

import (
	"context"
	"testing"
	"time"
)

// mockCache is a simple in-memory cache for testing
type mockCache struct {
	data map[string]interface{}
}

func newMockCache() *mockCache {
	return &mockCache{
		data: make(map[string]interface{}),
	}
}

func (m *mockCache) Get(ctx context.Context, key string) (interface{}, error) {
	if val, ok := m.data[key]; ok {
		return val, nil
	}
	return nil, ErrCacheMiss
}

func (m *mockCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	m.data[key] = value
	return nil
}

func (m *mockCache) Delete(ctx context.Context, key string) error {
	delete(m.data, key)
	return nil
}

func (m *mockCache) ClearPattern(ctx context.Context, pattern string) error {
	// Simple pattern matching for tests
	for key := range m.data {
		delete(m.data, key)
	}
	return nil
}

func (m *mockCache) Exists(ctx context.Context, key string) (bool, error) {
	_, exists := m.data[key]
	return exists, nil
}

func (m *mockCache) GetMultiple(ctx context.Context, keys []string) (map[string]interface{}, error) {
	result := make(map[string]interface{})
	for _, key := range keys {
		if val, ok := m.data[key]; ok {
			result[key] = val
		}
	}
	return result, nil
}

func (m *mockCache) SetMultiple(ctx context.Context, items map[string]interface{}, ttl time.Duration) error {
	for key, val := range items {
		m.data[key] = val
	}
	return nil
}

func (m *mockCache) DeleteMultiple(ctx context.Context, keys []string) error {
	for _, key := range keys {
		delete(m.data, key)
	}
	return nil
}

func (m *mockCache) Increment(ctx context.Context, key string, delta int64) (int64, error) {
	if val, ok := m.data[key].(int64); ok {
		val += delta
		m.data[key] = val
		return val, nil
	}
	m.data[key] = delta
	return delta, nil
}

func (m *mockCache) Decrement(ctx context.Context, key string, delta int64) (int64, error) {
	if val, ok := m.data[key].(int64); ok {
		val -= delta
		m.data[key] = val
		return val, nil
	}
	m.data[key] = -delta
	return -delta, nil
}

func (m *mockCache) Expire(ctx context.Context, key string, ttl time.Duration) error {
	return nil // No-op for simple mock
}

func (m *mockCache) TTL(ctx context.Context, key string) (time.Duration, error) {
	if _, ok := m.data[key]; ok {
		return 5 * time.Minute, nil
	}
	return 0, ErrCacheMiss
}

func (m *mockCache) Ping() error {
	return nil
}

func (m *mockCache) IsHealthy() bool {
	return true
}

func (m *mockCache) GetStats() map[string]interface{} {
	return map[string]interface{}{
		"keys": len(m.data),
	}
}

func (m *mockCache) Clear(ctx context.Context) error {
	m.data = make(map[string]interface{})
	return nil
}

func (m *mockCache) Close() error {
	return nil
}

func TestNewManager(t *testing.T) {
	cache := newMockCache()
	manager := NewManager(cache, Config{
		Enabled:    true,
		DefaultTTL: 5 * time.Minute,
		Prefix:     "test:",
	})

	if manager == nil {
		t.Fatal("Expected manager to be created")
	}

	if manager.prefix != "test:" {
		t.Errorf("Expected prefix 'test:', got '%s'", manager.prefix)
	}

	if manager.defaultTTL != 5*time.Minute {
		t.Errorf("Expected TTL 5m, got %v", manager.defaultTTL)
	}
}

func TestManagerGetSet(t *testing.T) {
	cache := newMockCache()
	manager := NewManager(cache, Config{
		Enabled:    true,
		DefaultTTL: 5 * time.Minute,
		Prefix:     "test:",
	})

	ctx := context.Background()
	key := "building:123"

	// Test data
	data := map[string]interface{}{
		"id":   "123",
		"name": "Test Building",
	}

	// Set
	err := manager.Set(ctx, key, data, 0)
	if err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	// Get
	var result map[string]interface{}
	err = manager.Get(ctx, key, &result)
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	// Verify
	if result["id"] != "123" {
		t.Errorf("Expected id '123', got '%v'", result["id"])
	}
	if result["name"] != "Test Building" {
		t.Errorf("Expected name 'Test Building', got '%v'", result["name"])
	}
}

func TestManagerDisabled(t *testing.T) {
	cache := newMockCache()
	manager := NewManager(cache, Config{
		Enabled:    false,
		DefaultTTL: 5 * time.Minute,
		Prefix:     "test:",
	})

	ctx := context.Background()
	data := map[string]string{"test": "value"}

	// Set should succeed silently when disabled
	err := manager.Set(ctx, "key", data, 0)
	if err != nil {
		t.Errorf("Set should succeed silently when disabled, got error: %v", err)
	}

	// Get should return error when disabled
	var result map[string]string
	err = manager.Get(ctx, "key", &result)
	if err != ErrCacheDisabled {
		t.Errorf("Expected ErrCacheDisabled, got: %v", err)
	}
}

func TestManagerDelete(t *testing.T) {
	cache := newMockCache()
	manager := NewManager(cache, Config{
		Enabled:    true,
		DefaultTTL: 5 * time.Minute,
		Prefix:     "test:",
	})

	ctx := context.Background()
	key := "building:123"
	data := map[string]string{"id": "123"}

	// Set
	manager.Set(ctx, key, data, 0)

	// Verify exists
	exists, _ := manager.Exists(ctx, key)
	if !exists {
		t.Error("Expected key to exist")
	}

	// Delete
	err := manager.Delete(ctx, key)
	if err != nil {
		t.Fatalf("Delete failed: %v", err)
	}

	// Verify deleted
	exists, _ = manager.Exists(ctx, key)
	if exists {
		t.Error("Expected key to be deleted")
	}
}

func TestCacheKeyBuilders(t *testing.T) {
	tests := []struct {
		name     string
		builder  func() string
		expected string
	}{
		{
			name:     "BuildingKey",
			builder:  func() string { return BuildingKey("123") },
			expected: "buildings:123",
		},
		{
			name:     "EquipmentKey",
			builder:  func() string { return EquipmentKey("456") },
			expected: "equipment:456",
		},
		{
			name:     "UserKey",
			builder:  func() string { return UserKey("789") },
			expected: "users:789",
		},
		{
			name:     "OrganizationKey",
			builder:  func() string { return OrganizationKey("abc") },
			expected: "organizations:abc",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.builder()
			if result != tt.expected {
				t.Errorf("Expected '%s', got '%s'", tt.expected, result)
			}
		})
	}
}

func TestBuildingListKey(t *testing.T) {
	key := BuildingListKey("org-123", 20, 0)
	expected := "buildings:list:org:org-123:limit:20:offset:0"
	
	if key != expected {
		t.Errorf("Expected '%s', got '%s'", expected, key)
	}
}

func TestEquipmentListKey(t *testing.T) {
	filters := map[string]string{
		"type":   "hvac",
		"status": "active",
	}
	
	key := EquipmentListKey("building-123", filters, 20, 0)
	
	// Should contain all components
	if key[:33] != "equipment:list:building:building-" {
		t.Errorf("Unexpected key prefix: %s", key)
	}
}
