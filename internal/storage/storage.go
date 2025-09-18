package storage

import (
	"context"
	"fmt"
	"io"
	"time"

	"github.com/arx-os/arxos/internal/config"
)

// Backend represents a storage backend interface
type Backend interface {
	// Core operations
	Get(ctx context.Context, key string) ([]byte, error)
	Put(ctx context.Context, key string, data []byte) error
	Delete(ctx context.Context, key string) error
	Exists(ctx context.Context, key string) (bool, error)

	// Streaming operations
	GetReader(ctx context.Context, key string) (io.ReadCloser, error)
	PutReader(ctx context.Context, key string, reader io.Reader, size int64) error

	// Metadata operations
	GetMetadata(ctx context.Context, key string) (*Metadata, error)
	SetMetadata(ctx context.Context, key string, metadata *Metadata) error

	// Listing operations
	List(ctx context.Context, prefix string) ([]string, error)
	ListWithMetadata(ctx context.Context, prefix string) ([]*Object, error)

	// Backend info
	Type() string
	IsAvailable(ctx context.Context) bool
}

// Metadata represents object metadata
type Metadata struct {
	Key          string            `json:"key"`
	Size         int64             `json:"size"`
	ContentType  string            `json:"content_type"`
	ETag         string            `json:"etag"`
	LastModified time.Time         `json:"last_modified"`
	Metadata     map[string]string `json:"metadata"`
}

// Object represents a storage object with metadata
type Object struct {
	Key      string    `json:"key"`
	Size     int64     `json:"size"`
	Modified time.Time `json:"modified"`
	ETag     string    `json:"etag"`
}

// Manager manages multiple storage backends
type Manager struct {
	primary  Backend
	fallback Backend
	cache    Backend
	config   *Config
}

// Config contains storage manager configuration
type Config struct {
	EnableCache    bool
	EnableFallback bool
	SyncEnabled    bool
	RetryAttempts  int
	RetryDelay     time.Duration
}

// NewManager creates a new storage manager
func NewManager(primary Backend, config *Config) *Manager {
	if config == nil {
		config = &Config{
			RetryAttempts: 3,
			RetryDelay:    1 * time.Second,
		}
	}

	return &Manager{
		primary: primary,
		config:  config,
	}
}

// SetFallback sets a fallback storage backend
func (m *Manager) SetFallback(backend Backend) {
	m.fallback = backend
}

// SetCache sets a cache storage backend
func (m *Manager) SetCache(backend Backend) {
	m.cache = backend
}

// Get retrieves data from storage with fallback and cache support
func (m *Manager) Get(ctx context.Context, key string) ([]byte, error) {
	// Try cache first
	if m.cache != nil && m.config.EnableCache {
		if data, err := m.cache.Get(ctx, key); err == nil {
			return data, nil
		}
	}

	// Try primary backend
	data, err := m.primary.Get(ctx, key)
	if err == nil {
		// Update cache on successful read
		if m.cache != nil && m.config.EnableCache {
			_ = m.cache.Put(ctx, key, data)
		}
		return data, nil
	}

	// Try fallback if primary fails
	if m.fallback != nil && m.config.EnableFallback {
		data, err = m.fallback.Get(ctx, key)
		if err == nil {
			// Sync to primary if enabled
			if m.config.SyncEnabled {
				_ = m.primary.Put(ctx, key, data)
			}
			// Update cache
			if m.cache != nil && m.config.EnableCache {
				_ = m.cache.Put(ctx, key, data)
			}
			return data, nil
		}
	}

	return nil, fmt.Errorf("failed to get %s: %w", key, err)
}

// Put stores data to storage with retry support
func (m *Manager) Put(ctx context.Context, key string, data []byte) error {
	var lastErr error

	// Retry logic for primary backend
	for i := 0; i < m.config.RetryAttempts; i++ {
		if err := m.primary.Put(ctx, key, data); err == nil {
			// Update cache on successful write
			if m.cache != nil && m.config.EnableCache {
				_ = m.cache.Put(ctx, key, data)
			}

			// Sync to fallback if enabled
			if m.fallback != nil && m.config.SyncEnabled {
				_ = m.fallback.Put(ctx, key, data)
			}

			return nil
		} else {
			lastErr = err
			if i < m.config.RetryAttempts-1 {
				time.Sleep(m.config.RetryDelay)
			}
		}
	}

	// If primary fails, try fallback
	if m.fallback != nil && m.config.EnableFallback {
		if err := m.fallback.Put(ctx, key, data); err == nil {
			return nil
		}
	}

	return fmt.Errorf("failed to put %s after %d attempts: %w", key, m.config.RetryAttempts, lastErr)
}

// Delete removes data from storage
func (m *Manager) Delete(ctx context.Context, key string) error {
	// Delete from cache
	if m.cache != nil {
		_ = m.cache.Delete(ctx, key)
	}

	// Delete from primary
	if err := m.primary.Delete(ctx, key); err != nil {
		return err
	}

	// Delete from fallback if sync is enabled
	if m.fallback != nil && m.config.SyncEnabled {
		_ = m.fallback.Delete(ctx, key)
	}

	return nil
}

// Exists checks if a key exists in storage
func (m *Manager) Exists(ctx context.Context, key string) (bool, error) {
	// Check cache first
	if m.cache != nil && m.config.EnableCache {
		if exists, err := m.cache.Exists(ctx, key); err == nil && exists {
			return true, nil
		}
	}

	// Check primary
	if exists, err := m.primary.Exists(ctx, key); err == nil {
		return exists, nil
	}

	// Check fallback
	if m.fallback != nil && m.config.EnableFallback {
		return m.fallback.Exists(ctx, key)
	}

	return false, nil
}

// GetReader returns a reader for the specified key
func (m *Manager) GetReader(ctx context.Context, key string) (io.ReadCloser, error) {
	// Try primary first
	reader, err := m.primary.GetReader(ctx, key)
	if err == nil {
		return reader, nil
	}

	// Try fallback
	if m.fallback != nil && m.config.EnableFallback {
		return m.fallback.GetReader(ctx, key)
	}

	return nil, fmt.Errorf("failed to get reader for %s: %w", key, err)
}

// PutReader stores data from a reader
func (m *Manager) PutReader(ctx context.Context, key string, reader io.Reader, size int64) error {
	// For streaming, we need to handle multiple backends carefully
	// Read data into memory if we need to write to multiple backends
	if m.fallback != nil && m.config.SyncEnabled {
		data, err := io.ReadAll(reader)
		if err != nil {
			return fmt.Errorf("failed to read data: %w", err)
		}

		// Write to primary
		if err := m.primary.Put(ctx, key, data); err != nil {
			return err
		}

		// Write to fallback
		_ = m.fallback.Put(ctx, key, data)

		// Update cache
		if m.cache != nil && m.config.EnableCache {
			_ = m.cache.Put(ctx, key, data)
		}

		return nil
	}

	// Single backend - stream directly
	return m.primary.PutReader(ctx, key, reader, size)
}

// List returns keys with the specified prefix
func (m *Manager) List(ctx context.Context, prefix string) ([]string, error) {
	// List from primary
	keys, err := m.primary.List(ctx, prefix)
	if err != nil && m.fallback != nil && m.config.EnableFallback {
		// Try fallback
		return m.fallback.List(ctx, prefix)
	}

	return keys, err
}

// ListWithMetadata returns objects with metadata
func (m *Manager) ListWithMetadata(ctx context.Context, prefix string) ([]*Object, error) {
	// List from primary
	objects, err := m.primary.ListWithMetadata(ctx, prefix)
	if err != nil && m.fallback != nil && m.config.EnableFallback {
		// Try fallback
		return m.fallback.ListWithMetadata(ctx, prefix)
	}

	return objects, err
}

// Sync synchronizes data between primary and fallback backends
func (m *Manager) Sync(ctx context.Context, prefix string) error {
	if m.fallback == nil || !m.config.SyncEnabled {
		return fmt.Errorf("sync not enabled or no fallback configured")
	}

	// Get list from both backends
	primaryKeys, err := m.primary.List(ctx, prefix)
	if err != nil {
		return fmt.Errorf("failed to list primary: %w", err)
	}

	fallbackKeys, err := m.fallback.List(ctx, prefix)
	if err != nil {
		return fmt.Errorf("failed to list fallback: %w", err)
	}

	// Create maps for efficient lookup
	primaryMap := make(map[string]bool)
	for _, key := range primaryKeys {
		primaryMap[key] = true
	}

	fallbackMap := make(map[string]bool)
	for _, key := range fallbackKeys {
		fallbackMap[key] = true
	}

	// Sync missing keys to primary
	for _, key := range fallbackKeys {
		if !primaryMap[key] {
			data, err := m.fallback.Get(ctx, key)
			if err == nil {
				_ = m.primary.Put(ctx, key, data)
			}
		}
	}

	// Sync missing keys to fallback
	for _, key := range primaryKeys {
		if !fallbackMap[key] {
			data, err := m.primary.Get(ctx, key)
			if err == nil {
				_ = m.fallback.Put(ctx, key, data)
			}
		}
	}

	return nil
}

// HealthCheck verifies all configured backends are available
func (m *Manager) HealthCheck(ctx context.Context) error {
	if !m.primary.IsAvailable(ctx) {
		return fmt.Errorf("primary backend %s is not available", m.primary.Type())
	}

	if m.fallback != nil && !m.fallback.IsAvailable(ctx) {
		return fmt.Errorf("fallback backend %s is not available", m.fallback.Type())
	}

	if m.cache != nil && !m.cache.IsAvailable(ctx) {
		return fmt.Errorf("cache backend %s is not available", m.cache.Type())
	}

	return nil
}

// NewFromConfig creates a storage backend from configuration
func NewFromConfig(cfg config.StorageConfig) (Backend, error) {
	switch cfg.Backend {
	case "local", "":
		if cfg.LocalPath == "" {
			return nil, fmt.Errorf("local storage path not configured")
		}
		return Local(cfg.LocalPath), nil
	case "s3":
		// TODO: Implement S3 backend
		return nil, fmt.Errorf("S3 storage not yet implemented")
	case "azure":
		// TODO: Implement Azure backend
		return nil, fmt.Errorf("Azure storage not yet implemented")
	default:
		return nil, fmt.Errorf("unknown storage backend: %s", cfg.Backend)
	}
}
