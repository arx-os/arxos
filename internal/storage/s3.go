package storage

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
)

// S3Backend implements Backend for AWS S3
type S3Backend struct {
	client     *s3.Client
	bucket     string
	presignClient *s3.PresignClient
}

// S3Config contains S3 configuration
type S3Config struct {
	Region          string
	Bucket          string
	AccessKeyID     string
	SecretAccessKey string
	Endpoint        string // For S3-compatible services
	UseSSL          bool
}

// NewS3Backend creates a new S3 backend
func NewS3Backend(cfg *S3Config) (*S3Backend, error) {
	var awsCfg aws.Config
	var err error

	// Load AWS configuration
	if cfg.AccessKeyID != "" && cfg.SecretAccessKey != "" {
		// Use explicit credentials
		awsCfg, err = config.LoadDefaultConfig(context.TODO(),
			config.WithRegion(cfg.Region),
			config.WithCredentialsProvider(
				credentials.NewStaticCredentialsProvider(cfg.AccessKeyID, cfg.SecretAccessKey, ""),
			),
		)
	} else {
		// Use default credentials (IAM role, environment variables, etc.)
		awsCfg, err = config.LoadDefaultConfig(context.TODO(),
			config.WithRegion(cfg.Region),
		)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to load AWS config: %w", err)
	}

	// Configure custom endpoint if provided (for MinIO, etc.)
	var s3Options []func(*s3.Options)
	if cfg.Endpoint != "" {
		s3Options = append(s3Options, func(o *s3.Options) {
			o.BaseEndpoint = aws.String(cfg.Endpoint)
			o.UsePathStyle = true
		})
	}

	// Create S3 client
	client := s3.NewFromConfig(awsCfg, s3Options...)

	// Create presign client for generating URLs
	presignClient := s3.NewPresignClient(client)

	logger.Info("S3 backend initialized for bucket: %s", cfg.Bucket)

	return &S3Backend{
		client:        client,
		bucket:        cfg.Bucket,
		presignClient: presignClient,
	}, nil
}

// Get retrieves data from S3
func (b *S3Backend) Get(ctx context.Context, key string) ([]byte, error) {
	result, err := b.client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(b.bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get object %s: %w", key, err)
	}
	defer result.Body.Close()

	data, err := io.ReadAll(result.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read object body: %w", err)
	}

	return data, nil
}

// Put stores data in S3
func (b *S3Backend) Put(ctx context.Context, key string, data []byte) error {
	_, err := b.client.PutObject(ctx, &s3.PutObjectInput{
		Bucket: aws.String(b.bucket),
		Key:    aws.String(key),
		Body:   bytes.NewReader(data),
	})
	if err != nil {
		return fmt.Errorf("failed to put object %s: %w", key, err)
	}

	logger.Debug("Stored object %s to S3 bucket %s", key, b.bucket)
	return nil
}

// Delete removes an object from S3
func (b *S3Backend) Delete(ctx context.Context, key string) error {
	_, err := b.client.DeleteObject(ctx, &s3.DeleteObjectInput{
		Bucket: aws.String(b.bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return fmt.Errorf("failed to delete object %s: %w", key, err)
	}

	logger.Debug("Deleted object %s from S3 bucket %s", key, b.bucket)
	return nil
}

// Exists checks if an object exists in S3
func (b *S3Backend) Exists(ctx context.Context, key string) (bool, error) {
	_, err := b.client.HeadObject(ctx, &s3.HeadObjectInput{
		Bucket: aws.String(b.bucket),
		Key:    aws.String(key),
	})

	if err != nil {
		// Check if the error is because the object doesn't exist
		if isS3NotFoundError(err) {
			return false, nil
		}
		return false, fmt.Errorf("failed to check object existence: %w", err)
	}

	return true, nil
}

// GetReader returns a reader for the object
func (b *S3Backend) GetReader(ctx context.Context, key string) (io.ReadCloser, error) {
	result, err := b.client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(b.bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get object reader: %w", err)
	}

	return result.Body, nil
}

// PutReader stores data from a reader
func (b *S3Backend) PutReader(ctx context.Context, key string, reader io.Reader, size int64) error {
	input := &s3.PutObjectInput{
		Bucket: aws.String(b.bucket),
		Key:    aws.String(key),
		Body:   reader,
	}

	if size > 0 {
		input.ContentLength = aws.Int64(size)
	}

	_, err := b.client.PutObject(ctx, input)
	if err != nil {
		return fmt.Errorf("failed to put object with reader: %w", err)
	}

	logger.Debug("Stored object %s to S3 using reader", key)
	return nil
}

// GetMetadata retrieves object metadata
func (b *S3Backend) GetMetadata(ctx context.Context, key string) (*Metadata, error) {
	result, err := b.client.HeadObject(ctx, &s3.HeadObjectInput{
		Bucket: aws.String(b.bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get object metadata: %w", err)
	}

	metadata := &Metadata{
		Key:          key,
		Size:         aws.ToInt64(result.ContentLength),
		ContentType:  aws.ToString(result.ContentType),
		ETag:         aws.ToString(result.ETag),
		LastModified: aws.ToTime(result.LastModified),
		Metadata:     make(map[string]string),
	}

	// Copy user metadata
	for k, v := range result.Metadata {
		metadata.Metadata[k] = v
	}

	return metadata, nil
}

// SetMetadata updates object metadata
func (b *S3Backend) SetMetadata(ctx context.Context, key string, metadata *Metadata) error {
	// S3 requires copying the object to update metadata
	copySource := fmt.Sprintf("%s/%s", b.bucket, key)

	input := &s3.CopyObjectInput{
		Bucket:     aws.String(b.bucket),
		Key:        aws.String(key),
		CopySource: aws.String(copySource),
		Metadata:   metadata.Metadata,
		MetadataDirective: types.MetadataDirectiveReplace,
	}

	if metadata.ContentType != "" {
		input.ContentType = aws.String(metadata.ContentType)
	}

	_, err := b.client.CopyObject(ctx, input)
	if err != nil {
		return fmt.Errorf("failed to update object metadata: %w", err)
	}

	return nil
}

// List lists all objects with a given prefix
func (b *S3Backend) List(ctx context.Context, prefix string) ([]string, error) {
	var keys []string

	paginator := s3.NewListObjectsV2Paginator(b.client, &s3.ListObjectsV2Input{
		Bucket: aws.String(b.bucket),
		Prefix: aws.String(prefix),
	})

	for paginator.HasMorePages() {
		page, err := paginator.NextPage(ctx)
		if err != nil {
			return nil, fmt.Errorf("failed to list objects: %w", err)
		}

		for _, obj := range page.Contents {
			keys = append(keys, aws.ToString(obj.Key))
		}
	}

	return keys, nil
}

// ListWithMetadata lists objects with their metadata
func (b *S3Backend) ListWithMetadata(ctx context.Context, prefix string) ([]*Object, error) {
	var objects []*Object

	paginator := s3.NewListObjectsV2Paginator(b.client, &s3.ListObjectsV2Input{
		Bucket: aws.String(b.bucket),
		Prefix: aws.String(prefix),
	})

	for paginator.HasMorePages() {
		page, err := paginator.NextPage(ctx)
		if err != nil {
			return nil, fmt.Errorf("failed to list objects with metadata: %w", err)
		}

		for _, obj := range page.Contents {
			objects = append(objects, &Object{
				Key:      aws.ToString(obj.Key),
				Size:     aws.ToInt64(obj.Size),
				Modified: aws.ToTime(obj.LastModified),
				ETag:     aws.ToString(obj.ETag),
			})
		}
	}

	return objects, nil
}

// Type returns the backend type
func (b *S3Backend) Type() string {
	return "s3"
}

// IsAvailable checks if the S3 backend is available
func (b *S3Backend) IsAvailable(ctx context.Context) bool {
	// Try to list the bucket (with max 1 result)
	_, err := b.client.ListObjectsV2(ctx, &s3.ListObjectsV2Input{
		Bucket:  aws.String(b.bucket),
		MaxKeys: aws.Int32(1),
	})

	return err == nil
}

// GetPresignedURL generates a presigned URL for direct access
func (b *S3Backend) GetPresignedURL(ctx context.Context, key string, expiry time.Duration, upload bool) (string, error) {
	if upload {
		// Generate upload URL
		request, err := b.presignClient.PresignPutObject(ctx, &s3.PutObjectInput{
			Bucket: aws.String(b.bucket),
			Key:    aws.String(key),
		}, func(opts *s3.PresignOptions) {
			opts.Expires = expiry
		})
		if err != nil {
			return "", fmt.Errorf("failed to generate upload URL: %w", err)
		}
		return request.URL, nil
	}

	// Generate download URL
	request, err := b.presignClient.PresignGetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(b.bucket),
		Key:    aws.String(key),
	}, func(opts *s3.PresignOptions) {
		opts.Expires = expiry
	})
	if err != nil {
		return "", fmt.Errorf("failed to generate download URL: %w", err)
	}

	return request.URL, nil
}

// CreateBucket creates the S3 bucket if it doesn't exist
func (b *S3Backend) CreateBucket(ctx context.Context) error {
	_, err := b.client.CreateBucket(ctx, &s3.CreateBucketInput{
		Bucket: aws.String(b.bucket),
	})

	if err != nil {
		// Check if bucket already exists
		if isBucketExistsError(err) {
			logger.Debug("Bucket %s already exists", b.bucket)
			return nil
		}
		return fmt.Errorf("failed to create bucket: %w", err)
	}

	logger.Info("Created S3 bucket: %s", b.bucket)
	return nil
}

// Helper functions

func isS3NotFoundError(err error) bool {
	// Check for various "not found" error types
	if err == nil {
		return false
	}
	// This is a simplified check - in production, use proper AWS error checking
	return strings.Contains(err.Error(), "NoSuchKey") || strings.Contains(err.Error(), "NotFound")
}

func isBucketExistsError(err error) bool {
	if err == nil {
		return false
	}
	return strings.Contains(err.Error(), "BucketAlreadyExists") || strings.Contains(err.Error(), "BucketAlreadyOwnedByYou")
}

func findSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}