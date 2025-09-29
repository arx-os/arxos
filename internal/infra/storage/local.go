package storage

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// LocalStorageService implements the storage interface using local file system
type LocalStorageService struct {
	basePath string
	mu       sync.RWMutex
	healthy  bool
	stats    map[string]interface{}
}

// NewLocalStorageService creates a new local storage service
func NewLocalStorageService() *LocalStorageService {
	return &LocalStorageService{
		healthy: false,
		stats:   make(map[string]interface{}),
	}
}

// Connect initializes the local storage service
func (l *LocalStorageService) Connect(ctx context.Context, basePath string) error {
	l.mu.Lock()
	defer l.mu.Unlock()

	if l.basePath != "" {
		return fmt.Errorf("local storage already connected")
	}

	// Create base directory if it doesn't exist
	if err := os.MkdirAll(basePath, 0755); err != nil {
		return fmt.Errorf("failed to create base directory %s: %w", basePath, err)
	}

	// Create subdirectories
	subdirs := []string{"buildings", "equipment", "analytics", "workflows", "temp"}
	for _, subdir := range subdirs {
		dir := filepath.Join(basePath, subdir)
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create subdirectory %s: %w", dir, err)
		}
	}

	l.basePath = basePath
	l.healthy = true
	l.updateStats()
	logger.Info("Connected to local storage at %s", basePath)
	return nil
}

// Disconnect closes the local storage service
func (l *LocalStorageService) Disconnect(ctx context.Context) error {
	l.mu.Lock()
	defer l.mu.Unlock()

	l.basePath = ""
	l.healthy = false
	logger.Info("Disconnected from local storage")
	return nil
}

// Put stores data in the local file system
func (l *LocalStorageService) Put(ctx context.Context, key string, data io.Reader) error {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if l.basePath == "" {
		return fmt.Errorf("local storage not connected")
	}

	filePath := filepath.Join(l.basePath, key)
	
	// Create directory if it doesn't exist
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory %s: %w", dir, err)
	}

	// Create file
	file, err := os.Create(filePath)
	if err != nil {
		return fmt.Errorf("failed to create file %s: %w", filePath, err)
	}
	defer file.Close()

	// Copy data to file
	if _, err := io.Copy(file, data); err != nil {
		return fmt.Errorf("failed to write data to file %s: %w", filePath, err)
	}

	return nil
}

// Get retrieves data from the local file system
func (l *LocalStorageService) Get(ctx context.Context, key string) (io.ReadCloser, error) {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if l.basePath == "" {
		return nil, fmt.Errorf("local storage not connected")
	}

	filePath := filepath.Join(l.basePath, key)
	
	file, err := os.Open(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("file not found: %s", key)
		}
		return nil, fmt.Errorf("failed to open file %s: %w", filePath, err)
	}

	return file, nil
}

// Delete removes a file from the local file system
func (l *LocalStorageService) Delete(ctx context.Context, key string) error {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if l.basePath == "" {
		return fmt.Errorf("local storage not connected")
	}

	filePath := filepath.Join(l.basePath, key)
	
	if err := os.Remove(filePath); err != nil {
		if os.IsNotExist(err) {
			return fmt.Errorf("file not found: %s", key)
		}
		return fmt.Errorf("failed to delete file %s: %w", filePath, err)
	}

	return nil
}

// Exists checks if a file exists in the local file system
func (l *LocalStorageService) Exists(ctx context.Context, key string) (bool, error) {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if l.basePath == "" {
		return false, fmt.Errorf("local storage not connected")
	}

	filePath := filepath.Join(l.basePath, key)
	_, err := os.Stat(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return false, nil
		}
		return false, fmt.Errorf("failed to check file existence %s: %w", filePath, err)
	}

	return true, nil
}

// List returns a list of files with the given prefix
func (l *LocalStorageService) List(ctx context.Context, prefix string) ([]string, error) {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if l.basePath == "" {
		return nil, fmt.Errorf("local storage not connected")
	}

	searchPath := filepath.Join(l.basePath, prefix)
	
	var files []string
	err := filepath.Walk(searchPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		if !info.IsDir() {
			relPath, err := filepath.Rel(l.basePath, path)
			if err != nil {
				return err
			}
			files = append(files, relPath)
		}
		
		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to list files with prefix %s: %w", prefix, err)
	}

	return files, nil
}

// DeletePrefix removes all files with the given prefix
func (l *LocalStorageService) DeletePrefix(ctx context.Context, prefix string) error {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if l.basePath == "" {
		return fmt.Errorf("local storage not connected")
	}

	searchPath := filepath.Join(l.basePath, prefix)
	
	err := filepath.Walk(searchPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		if !info.IsDir() {
			if err := os.Remove(path); err != nil {
				return fmt.Errorf("failed to delete file %s: %w", path, err)
			}
		}
		
		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to delete files with prefix %s: %w", prefix, err)
	}

	return nil
}

// GetMetadata retrieves metadata for a file
func (l *LocalStorageService) GetMetadata(ctx context.Context, key string) (*FileMetadata, error) {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if l.basePath == "" {
		return nil, fmt.Errorf("local storage not connected")
	}

	filePath := filepath.Join(l.basePath, key)
	
	info, err := os.Stat(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("file not found: %s", key)
		}
		return nil, fmt.Errorf("failed to get file info %s: %w", filePath, err)
	}

	metadata := &FileMetadata{
		Size:         info.Size(),
		LastModified: info.ModTime().Unix(),
		Custom:       make(map[string]string),
	}

	// Try to determine content type from extension
	ext := filepath.Ext(key)
	switch ext {
	case ".json":
		metadata.ContentType = "application/json"
	case ".txt":
		metadata.ContentType = "text/plain"
	case ".pdf":
		metadata.ContentType = "application/pdf"
	case ".jpg", ".jpeg":
		metadata.ContentType = "image/jpeg"
	case ".png":
		metadata.ContentType = "image/png"
	default:
		metadata.ContentType = "application/octet-stream"
	}

	return metadata, nil
}

// SetMetadata sets metadata for a file
func (l *LocalStorageService) SetMetadata(ctx context.Context, key string, metadata *FileMetadata) error {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if l.basePath == "" {
		return fmt.Errorf("local storage not connected")
	}

	filePath := filepath.Join(l.basePath, key)
	
	// Update file modification time if provided
	if metadata.LastModified > 0 {
		modTime := time.Unix(metadata.LastModified, 0)
		if err := os.Chtimes(filePath, modTime, modTime); err != nil {
			return fmt.Errorf("failed to update file modification time %s: %w", filePath, err)
		}
	}

	// Store custom metadata in a separate file
	if len(metadata.Custom) > 0 {
		metaPath := filePath + ".meta"
		metaFile, err := os.Create(metaPath)
		if err != nil {
			return fmt.Errorf("failed to create metadata file %s: %w", metaPath, err)
		}
		defer metaFile.Close()

		// Write custom metadata as key=value pairs
		for k, v := range metadata.Custom {
			if _, err := fmt.Fprintf(metaFile, "%s=%s\n", k, v); err != nil {
				return fmt.Errorf("failed to write metadata %s: %w", k, err)
			}
		}
	}

	return nil
}

// IsHealthy returns the health status of the local storage
func (l *LocalStorageService) IsHealthy() bool {
	l.mu.RLock()
	defer l.mu.RUnlock()
	return l.healthy && l.basePath != ""
}

// GetStats returns local storage statistics
func (l *LocalStorageService) GetStats() map[string]interface{} {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if l.basePath == "" {
		return map[string]interface{}{
			"status":  "disconnected",
			"healthy": false,
		}
	}

	// Update stats
	l.updateStats()
	return l.stats
}

// updateStats updates the local storage statistics
func (l *LocalStorageService) updateStats() {
	if l.basePath == "" {
		l.stats = map[string]interface{}{
			"status":  "disconnected",
			"healthy": false,
		}
		return
	}

	stats := map[string]interface{}{
		"status":  "connected",
		"healthy": l.healthy,
		"base_path": l.basePath,
	}

	// Get directory size and file count
	var totalSize int64
	var fileCount int64

	err := filepath.Walk(l.basePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		if !info.IsDir() {
			totalSize += info.Size()
			fileCount++
		}
		
		return nil
	})

	if err != nil {
		stats["error"] = err.Error()
	} else {
		stats["total_size_bytes"] = totalSize
		stats["file_count"] = fileCount
	}

	l.stats = stats
}