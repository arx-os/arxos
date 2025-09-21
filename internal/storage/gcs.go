package storage

import (
	"context"
	"fmt"
	"io"

	"cloud.google.com/go/storage"
	"google.golang.org/api/option"
)

// GCSBackend implements storage backend for Google Cloud Storage
type GCSBackend struct {
	client     *storage.Client
	bucket     *storage.BucketHandle
	bucketName string
}

// GCSConfig contains configuration for GCS backend
type GCSConfig struct {
	BucketName      string
	CredentialsJSON string // Optional: JSON credentials
	CredentialsFile string // Optional: Path to credentials file
	ProjectID       string
}

// NewGCSBackend creates a new Google Cloud Storage backend
func NewGCSBackend(ctx context.Context, config *GCSConfig) (*GCSBackend, error) {
	var opts []option.ClientOption

	if config.CredentialsJSON != "" {
		opts = append(opts, option.WithCredentialsJSON([]byte(config.CredentialsJSON)))
	} else if config.CredentialsFile != "" {
		opts = append(opts, option.WithCredentialsFile(config.CredentialsFile))
	}
	// If no credentials provided, will use Application Default Credentials

	client, err := storage.NewClient(ctx, opts...)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCS client: %w", err)
	}

	bucket := client.Bucket(config.BucketName)

	// Verify bucket exists
	_, err = bucket.Attrs(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to access bucket %s: %w", config.BucketName, err)
	}

	return &GCSBackend{
		client:     client,
		bucket:     bucket,
		bucketName: config.BucketName,
	}, nil
}

// Get retrieves data from GCS
func (g *GCSBackend) Get(ctx context.Context, key string) ([]byte, error) {
	reader, err := g.bucket.Object(key).NewReader(ctx)
	if err != nil {
		if err == storage.ErrObjectNotExist {
			return nil, fmt.Errorf("object not found: %s", key)
		}
		return nil, fmt.Errorf("failed to get object: %w", err)
	}
	defer reader.Close()

	data, err := io.ReadAll(reader)
	if err != nil {
		return nil, fmt.Errorf("failed to read object: %w", err)
	}

	return data, nil
}

// Put stores data in GCS
func (g *GCSBackend) Put(ctx context.Context, key string, data []byte) error {
	writer := g.bucket.Object(key).NewWriter(ctx)
	defer writer.Close()

	if _, err := writer.Write(data); err != nil {
		return fmt.Errorf("failed to write object: %w", err)
	}

	return nil
}

// Delete removes an object from GCS
func (g *GCSBackend) Delete(ctx context.Context, key string) error {
	if err := g.bucket.Object(key).Delete(ctx); err != nil {
		if err == storage.ErrObjectNotExist {
			return nil // Already deleted
		}
		return fmt.Errorf("failed to delete object: %w", err)
	}
	return nil
}

// Exists checks if an object exists in GCS
func (g *GCSBackend) Exists(ctx context.Context, key string) (bool, error) {
	_, err := g.bucket.Object(key).Attrs(ctx)
	if err != nil {
		if err == storage.ErrObjectNotExist {
			return false, nil
		}
		return false, fmt.Errorf("failed to check object existence: %w", err)
	}
	return true, nil
}

// GetReader returns a reader for the object
func (g *GCSBackend) GetReader(ctx context.Context, key string) (io.ReadCloser, error) {
	reader, err := g.bucket.Object(key).NewReader(ctx)
	if err != nil {
		if err == storage.ErrObjectNotExist {
			return nil, fmt.Errorf("object not found: %s", key)
		}
		return nil, fmt.Errorf("failed to get reader: %w", err)
	}
	return reader, nil
}

// PutReader stores data from a reader
func (g *GCSBackend) PutReader(ctx context.Context, key string, reader io.Reader, size int64) error {
	writer := g.bucket.Object(key).NewWriter(ctx)
	defer writer.Close()

	if size > 0 {
		writer.Size = size
	}

	if _, err := io.Copy(writer, reader); err != nil {
		return fmt.Errorf("failed to copy data: %w", err)
	}

	return nil
}

// GetMetadata retrieves object metadata
func (g *GCSBackend) GetMetadata(ctx context.Context, key string) (*Metadata, error) {
	attrs, err := g.bucket.Object(key).Attrs(ctx)
	if err != nil {
		if err == storage.ErrObjectNotExist {
			return nil, fmt.Errorf("object not found: %s", key)
		}
		return nil, fmt.Errorf("failed to get metadata: %w", err)
	}

	return &Metadata{
		Key:          key,
		Size:         attrs.Size,
		ContentType:  attrs.ContentType,
		ETag:         attrs.Etag,
		LastModified: attrs.Updated,
		Metadata:     attrs.Metadata,
	}, nil
}

// SetMetadata updates object metadata
func (g *GCSBackend) SetMetadata(ctx context.Context, key string, metadata *Metadata) error {
	object := g.bucket.Object(key)

	update := storage.ObjectAttrsToUpdate{
		ContentType: metadata.ContentType,
		Metadata:    metadata.Metadata,
	}

	_, err := object.Update(ctx, update)
	if err != nil {
		return fmt.Errorf("failed to update metadata: %w", err)
	}

	return nil
}

// List returns a list of objects with the given prefix
func (g *GCSBackend) List(ctx context.Context, prefix string) ([]string, error) {
	var keys []string

	iter := g.bucket.Objects(ctx, &storage.Query{
		Prefix: prefix,
	})

	for {
		attrs, err := iter.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("failed to list objects: %w", err)
		}
		keys = append(keys, attrs.Name)
	}

	return keys, nil
}

// ListWithMetadata returns objects with metadata
func (g *GCSBackend) ListWithMetadata(ctx context.Context, prefix string) ([]*Object, error) {
	var objects []*Object

	iter := g.bucket.Objects(ctx, &storage.Query{
		Prefix: prefix,
	})

	for {
		attrs, err := iter.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("failed to list objects: %w", err)
		}

		objects = append(objects, &Object{
			Key:      attrs.Name,
			Size:     attrs.Size,
			Modified: attrs.Updated,
			ETag:     attrs.Etag,
		})
	}

	return objects, nil
}

// Type returns the backend type
func (g *GCSBackend) Type() string {
	return "gcs"
}

// IsAvailable checks if the backend is available
func (g *GCSBackend) IsAvailable(ctx context.Context) bool {
	_, err := g.bucket.Attrs(ctx)
	return err == nil
}

// Close closes the GCS client
func (g *GCSBackend) Close() error {
	return g.client.Close()
}