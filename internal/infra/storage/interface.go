package storage

import (
	"context"
	"io"
)

// Interface defines the storage interface following Clean Architecture principles
type Interface interface {
	// File operations
	Put(ctx context.Context, key string, data io.Reader) error
	Get(ctx context.Context, key string) (io.ReadCloser, error)
	Delete(ctx context.Context, key string) error
	Exists(ctx context.Context, key string) (bool, error)

	// Directory operations
	List(ctx context.Context, prefix string) ([]string, error)
	DeletePrefix(ctx context.Context, prefix string) error

	// Metadata operations
	GetMetadata(ctx context.Context, key string) (*FileMetadata, error)
	SetMetadata(ctx context.Context, key string, metadata *FileMetadata) error

	// Health check
	IsHealthy() bool
	GetStats() map[string]interface{}
}

// FileMetadata represents file metadata
type FileMetadata struct {
	Size         int64             `json:"size"`
	ContentType  string            `json:"content_type"`
	LastModified int64             `json:"last_modified"`
	ETag         string            `json:"etag"`
	Custom       map[string]string `json:"custom"`
}
