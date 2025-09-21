package storage

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
)

// SpacesBackend implements storage backend for DigitalOcean Spaces
// Spaces is S3-compatible, so we use the AWS SDK
type SpacesBackend struct {
	client     *s3.Client
	bucketName string
	region     string
}

// SpacesConfig contains configuration for DigitalOcean Spaces backend
type SpacesConfig struct {
	AccessKey  string
	SecretKey  string
	Region     string // e.g., "nyc3", "sfo3", "ams3", "sgp1", "fra1"
	BucketName string
	Endpoint   string // Optional: Custom endpoint
}

// NewSpacesBackend creates a new DigitalOcean Spaces backend
func NewSpacesBackend(ctx context.Context, cfg *SpacesConfig) (*SpacesBackend, error) {
	// Build endpoint if not provided
	endpoint := cfg.Endpoint
	if endpoint == "" {
		endpoint = fmt.Sprintf("https://%s.digitaloceanspaces.com", cfg.Region)
	}

	// Create custom resolver for DigitalOcean Spaces endpoint
	customResolver := aws.EndpointResolverWithOptionsFunc(func(service, region string, options ...interface{}) (aws.Endpoint, error) {
		return aws.Endpoint{
			URL:           endpoint,
			SigningRegion: cfg.Region,
		}, nil
	})

	// Create AWS config for DigitalOcean Spaces
	awsCfg, err := config.LoadDefaultConfig(ctx,
		config.WithRegion(cfg.Region),
		config.WithEndpointResolverWithOptions(customResolver),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(
			cfg.AccessKey,
			cfg.SecretKey,
			"",
		)),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to load config: %w", err)
	}

	// Create S3 client
	client := s3.NewFromConfig(awsCfg, func(o *s3.Options) {
		o.UsePathStyle = false // DigitalOcean Spaces uses virtual-hosted-style
	})

	// Verify bucket exists
	_, err = client.HeadBucket(ctx, &s3.HeadBucketInput{
		Bucket: aws.String(cfg.BucketName),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to access Space %s: %w", cfg.BucketName, err)
	}

	return &SpacesBackend{
		client:     client,
		bucketName: cfg.BucketName,
		region:     cfg.Region,
	}, nil
}

// Get retrieves data from Spaces
func (s *SpacesBackend) Get(ctx context.Context, key string) ([]byte, error) {
	result, err := s.client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(s.bucketName),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get object: %w", err)
	}
	defer result.Body.Close()

	data, err := io.ReadAll(result.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read object: %w", err)
	}

	return data, nil
}

// Put stores data in Spaces
func (s *SpacesBackend) Put(ctx context.Context, key string, data []byte) error {
	_, err := s.client.PutObject(ctx, &s3.PutObjectInput{
		Bucket: aws.String(s.bucketName),
		Key:    aws.String(key),
		Body:   bytes.NewReader(data),
	})
	if err != nil {
		return fmt.Errorf("failed to put object: %w", err)
	}

	return nil
}

// Delete removes an object from Spaces
func (s *SpacesBackend) Delete(ctx context.Context, key string) error {
	_, err := s.client.DeleteObject(ctx, &s3.DeleteObjectInput{
		Bucket: aws.String(s.bucketName),
		Key:    aws.String(key),
	})
	if err != nil {
		return fmt.Errorf("failed to delete object: %w", err)
	}

	return nil
}

// Exists checks if an object exists
func (s *SpacesBackend) Exists(ctx context.Context, key string) (bool, error) {
	_, err := s.client.HeadObject(ctx, &s3.HeadObjectInput{
		Bucket: aws.String(s.bucketName),
		Key:    aws.String(key),
	})
	if err != nil {
		// Check if it's a not found error
		if isNotFoundS3Error(err) {
			return false, nil
		}
		return false, fmt.Errorf("failed to check object existence: %w", err)
	}

	return true, nil
}

// GetReader returns a reader for the object
func (s *SpacesBackend) GetReader(ctx context.Context, key string) (io.ReadCloser, error) {
	result, err := s.client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(s.bucketName),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get reader: %w", err)
	}

	return result.Body, nil
}

// PutReader stores data from a reader
func (s *SpacesBackend) PutReader(ctx context.Context, key string, reader io.Reader, size int64) error {
	input := &s3.PutObjectInput{
		Bucket: aws.String(s.bucketName),
		Key:    aws.String(key),
		Body:   reader,
	}

	if size > 0 {
		input.ContentLength = aws.Int64(size)
	}

	_, err := s.client.PutObject(ctx, input)
	if err != nil {
		return fmt.Errorf("failed to put object from reader: %w", err)
	}

	return nil
}

// GetMetadata retrieves object metadata
func (s *SpacesBackend) GetMetadata(ctx context.Context, key string) (*Metadata, error) {
	result, err := s.client.HeadObject(ctx, &s3.HeadObjectInput{
		Bucket: aws.String(s.bucketName),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get metadata: %w", err)
	}

	metadata := &Metadata{
		Key:         key,
		Size:        aws.ToInt64(result.ContentLength),
		ContentType: aws.ToString(result.ContentType),
		Metadata:    result.Metadata,
	}

	if result.ETag != nil {
		metadata.ETag = *result.ETag
	}

	if result.LastModified != nil {
		metadata.LastModified = *result.LastModified
	}

	return metadata, nil
}

// SetMetadata updates object metadata
func (s *SpacesBackend) SetMetadata(ctx context.Context, key string, metadata *Metadata) error {
	// In S3/Spaces, metadata can only be set by copying the object to itself
	copySource := fmt.Sprintf("%s/%s", s.bucketName, key)

	input := &s3.CopyObjectInput{
		Bucket:            aws.String(s.bucketName),
		Key:               aws.String(key),
		CopySource:        aws.String(copySource),
		Metadata:          metadata.Metadata,
		MetadataDirective: types.MetadataDirectiveReplace,
	}

	if metadata.ContentType != "" {
		input.ContentType = aws.String(metadata.ContentType)
	}

	_, err := s.client.CopyObject(ctx, input)
	if err != nil {
		return fmt.Errorf("failed to set metadata: %w", err)
	}

	return nil
}

// List returns a list of objects with the given prefix
func (s *SpacesBackend) List(ctx context.Context, prefix string) ([]string, error) {
	var keys []string

	paginator := s3.NewListObjectsV2Paginator(s.client, &s3.ListObjectsV2Input{
		Bucket: aws.String(s.bucketName),
		Prefix: aws.String(prefix),
	})

	for paginator.HasMorePages() {
		page, err := paginator.NextPage(ctx)
		if err != nil {
			return nil, fmt.Errorf("failed to list objects: %w", err)
		}

		for _, obj := range page.Contents {
			if obj.Key != nil {
				keys = append(keys, *obj.Key)
			}
		}
	}

	return keys, nil
}

// ListWithMetadata returns objects with metadata
func (s *SpacesBackend) ListWithMetadata(ctx context.Context, prefix string) ([]*Object, error) {
	var objects []*Object

	paginator := s3.NewListObjectsV2Paginator(s.client, &s3.ListObjectsV2Input{
		Bucket: aws.String(s.bucketName),
		Prefix: aws.String(prefix),
	})

	for paginator.HasMorePages() {
		page, err := paginator.NextPage(ctx)
		if err != nil {
			return nil, fmt.Errorf("failed to list objects: %w", err)
		}

		for _, obj := range page.Contents {
			object := &Object{
				Key:      aws.ToString(obj.Key),
				Size:     aws.ToInt64(obj.Size),
				Modified: aws.ToTime(obj.LastModified),
			}

			if obj.ETag != nil {
				object.ETag = *obj.ETag
			}

			objects = append(objects, object)
		}
	}

	return objects, nil
}

// Type returns the backend type
func (s *SpacesBackend) Type() string {
	return "spaces"
}

// IsAvailable checks if the backend is available
func (s *SpacesBackend) IsAvailable(ctx context.Context) bool {
	_, err := s.client.HeadBucket(ctx, &s3.HeadBucketInput{
		Bucket: aws.String(s.bucketName),
	})
	return err == nil
}

// isNotFoundS3Error checks if the error is a not found error
func isNotFoundS3Error(err error) bool {
	// Check for S3 specific not found error
	// This is a simplified check - in production you'd want more robust error handling
	return err != nil && (
		strings.Contains(err.Error(), "NoSuchKey") ||
		strings.Contains(err.Error(), "NotFound") ||
		strings.Contains(err.Error(), "404"))
}

