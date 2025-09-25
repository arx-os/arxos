package storage

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// LocalBackend implements the Backend interface for local filesystem storage
type LocalBackend struct {
	basePath string
}

// NewLocalBackend creates a new local storage backend
func NewLocalBackend(basePath string) (*LocalBackend, error) {
	// Ensure base path exists
	if err := os.MkdirAll(basePath, 0755); err != nil {
		return nil, fmt.Errorf("failed to create base path: %w", err)
	}

	// Convert to absolute path
	absPath, err := filepath.Abs(basePath)
	if err != nil {
		return nil, fmt.Errorf("failed to get absolute path: %w", err)
	}

	return &LocalBackend{
		basePath: absPath,
	}, nil
}

// Local creates a new local filesystem backend (simplified constructor)
func Local(basePath string) Backend {
	backend, _ := NewLocalBackend(basePath)
	return backend
}

// Type returns the backend type
func (l *LocalBackend) Type() string {
	return "local"
}

// IsAvailable checks if the backend is available
func (l *LocalBackend) IsAvailable(ctx context.Context) bool {
	// Check if we can write to the base path
	testFile := filepath.Join(l.basePath, ".arxos_test")
	if err := os.WriteFile(testFile, []byte("test"), 0644); err != nil {
		return false
	}
	os.Remove(testFile)
	return true
}

// Get retrieves data from local storage
func (l *LocalBackend) Get(ctx context.Context, key string) ([]byte, error) {
	path := l.keyToPath(key)

	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("key not found: %s", key)
		}
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	return data, nil
}

// Put stores data to local storage
func (l *LocalBackend) Put(ctx context.Context, key string, data []byte) error {
	path := l.keyToPath(key)

	// Ensure directory exists
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	// Write file atomically
	tmpPath := path + ".tmp"
	if err := os.WriteFile(tmpPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	if err := os.Rename(tmpPath, path); err != nil {
		os.Remove(tmpPath)
		return fmt.Errorf("failed to rename file: %w", err)
	}

	return nil
}

// Delete removes data from local storage
func (l *LocalBackend) Delete(ctx context.Context, key string) error {
	path := l.keyToPath(key)

	if err := os.Remove(path); err != nil {
		if os.IsNotExist(err) {
			return nil // Already deleted
		}
		return fmt.Errorf("failed to delete file: %w", err)
	}

	// Also remove metadata file if it exists
	metaPath := path + ".meta"
	if err := os.Remove(metaPath); err != nil && !os.IsNotExist(err) {
		// Log warning but don't fail the operation
		fmt.Printf("Warning: failed to remove metadata file %s: %v\n", metaPath, err)
	}

	// Try to remove empty parent directories
	l.cleanEmptyDirs(filepath.Dir(path))

	return nil
}

// Exists checks if a key exists in local storage
func (l *LocalBackend) Exists(ctx context.Context, key string) (bool, error) {
	path := l.keyToPath(key)

	_, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return false, nil
		}
		return false, fmt.Errorf("failed to stat file: %w", err)
	}

	return true, nil
}

// GetReader returns a reader for the specified key
func (l *LocalBackend) GetReader(ctx context.Context, key string) (io.ReadCloser, error) {
	path := l.keyToPath(key)

	file, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("key not found: %s", key)
		}
		return nil, fmt.Errorf("failed to open file: %w", err)
	}

	return file, nil
}

// PutReader stores data from a reader to local storage
func (l *LocalBackend) PutReader(ctx context.Context, key string, reader io.Reader, size int64) error {
	path := l.keyToPath(key)

	// Ensure directory exists
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	// Write to temporary file first
	tmpPath := path + ".tmp"
	file, err := os.Create(tmpPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Copy data from reader
	written, err := io.Copy(file, reader)
	if err != nil {
		os.Remove(tmpPath)
		return fmt.Errorf("failed to write data: %w", err)
	}

	// Verify size if provided
	if size > 0 && written != size {
		os.Remove(tmpPath)
		return fmt.Errorf("size mismatch: expected %d, got %d", size, written)
	}

	// Close file before renaming
	file.Close()

	// Atomic rename
	if err := os.Rename(tmpPath, path); err != nil {
		os.Remove(tmpPath)
		return fmt.Errorf("failed to rename file: %w", err)
	}

	return nil
}

// GetMetadata retrieves metadata for a key
func (l *LocalBackend) GetMetadata(ctx context.Context, key string) (*Metadata, error) {
	path := l.keyToPath(key)

	info, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("key not found: %s", key)
		}
		return nil, fmt.Errorf("failed to stat file: %w", err)
	}

	// Create base metadata from file info
	metadata := &Metadata{
		Key:          key,
		Size:         info.Size(),
		ContentType:  l.detectContentType(path),
		LastModified: info.ModTime(),
		Metadata:     make(map[string]string),
	}

	// Try to load extended metadata from sidecar file
	metaPath := path + ".meta"
	if extendedMeta, err := l.loadMetadataFromFile(metaPath); err == nil {
		// Merge extended metadata
		metadata.Metadata = extendedMeta.Metadata
		if extendedMeta.ContentType != "" {
			metadata.ContentType = extendedMeta.ContentType
		}
		if !extendedMeta.LastModified.IsZero() {
			metadata.LastModified = extendedMeta.LastModified
		}
	}

	return metadata, nil
}

// SetMetadata sets metadata for a key (limited support for local storage)
func (l *LocalBackend) SetMetadata(ctx context.Context, key string, metadata *Metadata) error {
	path := l.keyToPath(key)

	// Check if file exists
	if _, err := os.Stat(path); err != nil {
		if os.IsNotExist(err) {
			return fmt.Errorf("key not found: %s", key)
		}
		return fmt.Errorf("failed to stat file: %w", err)
	}

	// For local storage, we can only update modification time
	if !metadata.LastModified.IsZero() {
		if err := os.Chtimes(path, time.Now(), metadata.LastModified); err != nil {
			return fmt.Errorf("failed to update times: %w", err)
		}
	}

	// Store extended metadata in a sidecar file if needed
	if len(metadata.Metadata) > 0 {
		metaPath := path + ".meta"
		if err := l.saveMetadataToFile(metaPath, metadata); err != nil {
			return fmt.Errorf("failed to save metadata: %w", err)
		}
	}

	return nil
}

// List returns keys with the specified prefix
func (l *LocalBackend) List(ctx context.Context, prefix string) ([]string, error) {
	var keys []string
	prefixPath := l.keyToPath(prefix)
	baseLen := len(l.basePath) + 1 // +1 for the separator

	err := filepath.Walk(l.basePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip errors
		}

		// Skip directories and hidden files
		if info.IsDir() || strings.HasPrefix(info.Name(), ".") {
			return nil
		}

		// Skip metadata files
		if strings.HasSuffix(path, ".meta") || strings.HasSuffix(path, ".tmp") {
			return nil
		}

		// Check if path matches prefix
		if strings.HasPrefix(path, prefixPath) {
			// Convert path back to key
			if len(path) > baseLen {
				key := l.pathToKey(path)
				keys = append(keys, key)
			}
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to walk directory: %w", err)
	}

	return keys, nil
}

// ListWithMetadata returns objects with metadata
func (l *LocalBackend) ListWithMetadata(ctx context.Context, prefix string) ([]*Object, error) {
	var objects []*Object
	prefixPath := l.keyToPath(prefix)

	err := filepath.Walk(l.basePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip errors
		}

		// Skip directories and hidden files
		if info.IsDir() || strings.HasPrefix(info.Name(), ".") {
			return nil
		}

		// Skip metadata files
		if strings.HasSuffix(path, ".meta") || strings.HasSuffix(path, ".tmp") {
			return nil
		}

		// Check if path matches prefix
		if strings.HasPrefix(path, prefixPath) {
			key := l.pathToKey(path)
			objects = append(objects, &Object{
				Key:      key,
				Size:     info.Size(),
				Modified: info.ModTime(),
			})
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to walk directory: %w", err)
	}

	return objects, nil
}

// keyToPath converts a storage key to a filesystem path
func (l *LocalBackend) keyToPath(key string) string {
	// Sanitize key to prevent directory traversal
	key = strings.ReplaceAll(key, "..", "")
	key = strings.TrimPrefix(key, "/")

	// Convert forward slashes to OS-specific separators
	parts := strings.Split(key, "/")
	return filepath.Join(append([]string{l.basePath}, parts...)...)
}

// pathToKey converts a filesystem path to a storage key
func (l *LocalBackend) pathToKey(path string) string {
	// Remove base path
	rel, err := filepath.Rel(l.basePath, path)
	if err != nil {
		return path
	}

	// Convert OS-specific separators to forward slashes
	return strings.ReplaceAll(rel, string(filepath.Separator), "/")
}

// cleanEmptyDirs removes empty parent directories
func (l *LocalBackend) cleanEmptyDirs(dir string) {
	// Don't remove the base directory
	if dir == l.basePath || !strings.HasPrefix(dir, l.basePath) {
		return
	}

	// Check if directory is empty
	entries, err := os.ReadDir(dir)
	if err != nil || len(entries) > 0 {
		return
	}

	// Remove empty directory
	if err := os.Remove(dir); err == nil {
		// Recursively clean parent
		l.cleanEmptyDirs(filepath.Dir(dir))
	}
}

// detectContentType attempts to detect the content type of a file
func (l *LocalBackend) detectContentType(path string) string {
	ext := strings.ToLower(filepath.Ext(path))
	switch ext {
	case ".json":
		return "application/json"
	case ".pdf":
		return "application/pdf"
	case ".txt":
		return "text/plain"
	case ".xml":
		return "application/xml"
	case ".png":
		return "image/png"
	case ".jpg", ".jpeg":
		return "image/jpeg"
	default:
		return "application/octet-stream"
	}
}

// saveMetadataToFile saves metadata to a JSON sidecar file
func (l *LocalBackend) saveMetadataToFile(metaPath string, metadata *Metadata) error {
	// Create directory if it doesn't exist
	dir := filepath.Dir(metaPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create metadata directory: %w", err)
	}

	// Write to temporary file first for atomic operation
	tmpPath := metaPath + ".tmp"
	file, err := os.Create(tmpPath)
	if err != nil {
		return fmt.Errorf("failed to create metadata file: %w", err)
	}
	defer file.Close()

	// Encode metadata as JSON
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(metadata); err != nil {
		os.Remove(tmpPath)
		return fmt.Errorf("failed to encode metadata: %w", err)
	}

	// Close file before renaming
	file.Close()

	// Atomic rename
	if err := os.Rename(tmpPath, metaPath); err != nil {
		os.Remove(tmpPath)
		return fmt.Errorf("failed to rename metadata file: %w", err)
	}

	return nil
}

// loadMetadataFromFile loads metadata from a JSON sidecar file
func (l *LocalBackend) loadMetadataFromFile(metaPath string) (*Metadata, error) {
	file, err := os.Open(metaPath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var metadata Metadata
	decoder := json.NewDecoder(file)
	if err := decoder.Decode(&metadata); err != nil {
		return nil, fmt.Errorf("failed to decode metadata: %w", err)
	}

	return &metadata, nil
}
