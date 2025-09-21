package storage

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"

	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/Azure/azure-sdk-for-go/sdk/storage/azblob"
)

// AzureBackend implements storage backend for Azure Blob Storage
type AzureBackend struct {
	client        *azblob.Client
	containerName string
}

// AzureConfig contains configuration for Azure backend
type AzureConfig struct {
	AccountName   string
	AccountKey    string
	ContainerName string
	SASToken      string // Optional: Use SAS token instead of account key
	ConnectionString string // Optional: Use connection string
}

// NewAzureBackend creates a new Azure Blob Storage backend
func NewAzureBackend(ctx context.Context, config *AzureConfig) (*AzureBackend, error) {
	var client *azblob.Client
	var err error

	if config.ConnectionString != "" {
		// Use connection string
		client, err = azblob.NewClientFromConnectionString(config.ConnectionString, nil)
	} else if config.SASToken != "" {
		// Use SAS token
		serviceURL := fmt.Sprintf("https://%s.blob.core.windows.net/?%s", config.AccountName, config.SASToken)
		client, err = azblob.NewClientWithNoCredential(serviceURL, nil)
	} else if config.AccountKey != "" {
		// Use account key
		cred, err := azblob.NewSharedKeyCredential(config.AccountName, config.AccountKey)
		if err != nil {
			return nil, fmt.Errorf("failed to create credentials: %w", err)
		}
		serviceURL := fmt.Sprintf("https://%s.blob.core.windows.net/", config.AccountName)
		client, err = azblob.NewClientWithSharedKeyCredential(serviceURL, cred, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create client: %w", err)
		}
	} else {
		return nil, fmt.Errorf("no authentication method provided")
	}

	if err != nil {
		return nil, fmt.Errorf("failed to create Azure client: %w", err)
	}

	// Verify container exists
	_, err = client.ServiceClient().NewContainerClient(config.ContainerName).GetProperties(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to access container %s: %w", config.ContainerName, err)
	}

	return &AzureBackend{
		client:        client,
		containerName: config.ContainerName,
	}, nil
}

// Get retrieves data from Azure Blob Storage
func (a *AzureBackend) Get(ctx context.Context, key string) ([]byte, error) {
	blobClient := a.client.ServiceClient().NewContainerClient(a.containerName).NewBlobClient(key)

	downloadResponse, err := blobClient.DownloadStream(ctx, nil)
	if err != nil {
		if isNotFoundError(err) {
			return nil, fmt.Errorf("blob not found: %s", key)
		}
		return nil, fmt.Errorf("failed to download blob: %w", err)
	}
	defer downloadResponse.Body.Close()

	data, err := io.ReadAll(downloadResponse.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read blob: %w", err)
	}

	return data, nil
}

// Put stores data in Azure Blob Storage
func (a *AzureBackend) Put(ctx context.Context, key string, data []byte) error {
	blobClient := a.client.ServiceClient().NewContainerClient(a.containerName).NewBlockBlobClient(key)

	reader := &readSeekCloser{bytes.NewReader(data)}
	_, err := blobClient.Upload(ctx, reader, nil)
	if err != nil {
		return fmt.Errorf("failed to upload blob: %w", err)
	}

	return nil
}

// Delete removes a blob from Azure Blob Storage
func (a *AzureBackend) Delete(ctx context.Context, key string) error {
	blobClient := a.client.ServiceClient().NewContainerClient(a.containerName).NewBlobClient(key)

	_, err := blobClient.Delete(ctx, nil)
	if err != nil {
		if isNotFoundError(err) {
			return nil // Already deleted
		}
		return fmt.Errorf("failed to delete blob: %w", err)
	}

	return nil
}

// Exists checks if a blob exists
func (a *AzureBackend) Exists(ctx context.Context, key string) (bool, error) {
	blobClient := a.client.ServiceClient().NewContainerClient(a.containerName).NewBlobClient(key)

	_, err := blobClient.GetProperties(ctx, nil)
	if err != nil {
		if isNotFoundError(err) {
			return false, nil
		}
		return false, fmt.Errorf("failed to check blob existence: %w", err)
	}

	return true, nil
}

// GetReader returns a reader for the blob
func (a *AzureBackend) GetReader(ctx context.Context, key string) (io.ReadCloser, error) {
	blobClient := a.client.ServiceClient().NewContainerClient(a.containerName).NewBlobClient(key)

	downloadResponse, err := blobClient.DownloadStream(ctx, nil)
	if err != nil {
		if isNotFoundError(err) {
			return nil, fmt.Errorf("blob not found: %s", key)
		}
		return nil, fmt.Errorf("failed to get reader: %w", err)
	}

	return downloadResponse.Body, nil
}

// PutReader stores data from a reader
func (a *AzureBackend) PutReader(ctx context.Context, key string, reader io.Reader, size int64) error {
	blobClient := a.client.ServiceClient().NewContainerClient(a.containerName).NewBlockBlobClient(key)

	// Wrap reader to satisfy ReadSeekCloser interface
	var rsc io.ReadSeekCloser
	if seeker, ok := reader.(io.ReadSeeker); ok {
		rsc = &readSeekCloser{seeker}
	} else {
		// For non-seekable readers, we need to read all data first
		data, err := io.ReadAll(reader)
		if err != nil {
			return fmt.Errorf("failed to read data: %w", err)
		}
		rsc = &readSeekCloser{bytes.NewReader(data)}
	}

	_, err := blobClient.Upload(ctx, rsc, nil)
	if err != nil {
		return fmt.Errorf("failed to upload from reader: %w", err)
	}

	return nil
}

// GetMetadata retrieves blob metadata
func (a *AzureBackend) GetMetadata(ctx context.Context, key string) (*Metadata, error) {
	blobClient := a.client.ServiceClient().NewContainerClient(a.containerName).NewBlobClient(key)

	props, err := blobClient.GetProperties(ctx, nil)
	if err != nil {
		if isNotFoundError(err) {
			return nil, fmt.Errorf("blob not found: %s", key)
		}
		return nil, fmt.Errorf("failed to get metadata: %w", err)
	}

	metadata := make(map[string]string)
	if props.Metadata != nil {
		for k, v := range props.Metadata {
			if v != nil {
				metadata[k] = *v
			}
		}
	}

	return &Metadata{
		Key:          key,
		Size:         *props.ContentLength,
		ContentType:  *props.ContentType,
		ETag:         string(*props.ETag),
		LastModified: *props.LastModified,
		Metadata:     metadata,
	}, nil
}

// SetMetadata updates blob metadata
func (a *AzureBackend) SetMetadata(ctx context.Context, key string, metadata *Metadata) error {
	blobClient := a.client.ServiceClient().NewContainerClient(a.containerName).NewBlobClient(key)

	azureMetadata := make(map[string]*string)
	for k, v := range metadata.Metadata {
		val := v
		azureMetadata[k] = &val
	}

	_, err := blobClient.SetMetadata(ctx, azureMetadata, nil)
	if err != nil {
		return fmt.Errorf("failed to set metadata: %w", err)
	}

	return nil
}

// List returns a list of blobs with the given prefix
func (a *AzureBackend) List(ctx context.Context, prefix string) ([]string, error) {
	var keys []string

	containerClient := a.client.ServiceClient().NewContainerClient(a.containerName)
	pager := containerClient.NewListBlobsFlatPager(&azblob.ListBlobsFlatOptions{
		Prefix: &prefix,
	})

	for pager.More() {
		page, err := pager.NextPage(ctx)
		if err != nil {
			return nil, fmt.Errorf("failed to list blobs: %w", err)
		}

		for _, blob := range page.Segment.BlobItems {
			if blob.Name != nil {
				keys = append(keys, *blob.Name)
			}
		}
	}

	return keys, nil
}

// ListWithMetadata returns blobs with metadata
func (a *AzureBackend) ListWithMetadata(ctx context.Context, prefix string) ([]*Object, error) {
	var objects []*Object

	containerClient := a.client.ServiceClient().NewContainerClient(a.containerName)
	pager := containerClient.NewListBlobsFlatPager(&azblob.ListBlobsFlatOptions{
		Prefix: &prefix,
	})

	for pager.More() {
		page, err := pager.NextPage(ctx)
		if err != nil {
			return nil, fmt.Errorf("failed to list blobs: %w", err)
		}

		for _, blob := range page.Segment.BlobItems {
			obj := &Object{
				Key:  *blob.Name,
			}

			if blob.Properties != nil {
				if blob.Properties.ContentLength != nil {
					obj.Size = *blob.Properties.ContentLength
				}
				if blob.Properties.LastModified != nil {
					obj.Modified = *blob.Properties.LastModified
				}
				if blob.Properties.ETag != nil {
					obj.ETag = string(*blob.Properties.ETag)
				}
			}

			objects = append(objects, obj)
		}
	}

	return objects, nil
}

// Type returns the backend type
func (a *AzureBackend) Type() string {
	return "azure"
}

// IsAvailable checks if the backend is available
func (a *AzureBackend) IsAvailable(ctx context.Context) bool {
	_, err := a.client.ServiceClient().NewContainerClient(a.containerName).GetProperties(ctx, nil)
	return err == nil
}

// isNotFoundError checks if the error is a not found error
func isNotFoundError(err error) bool {
	var respErr *azcore.ResponseError
	if errors.As(err, &respErr) {
		return respErr.StatusCode == 404
	}
	return false
}

// readSeekCloser wraps a ReadSeeker to add a Close method
type readSeekCloser struct {
	io.ReadSeeker
}

func (r *readSeekCloser) Close() error {
	return nil
}