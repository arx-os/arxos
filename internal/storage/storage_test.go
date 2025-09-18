package storage

import (
	"context"
	"fmt"
	"io"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestLocalBackend(t *testing.T) {
	tmpDir := t.TempDir()
	backend, err := NewLocalBackend(tmpDir)
	require.NoError(t, err)

	ctx := context.Background()

	t.Run("Type", func(t *testing.T) {
		assert.Equal(t, "local", backend.Type())
	})

	t.Run("IsAvailable", func(t *testing.T) {
		assert.True(t, backend.IsAvailable(ctx))
	})

	t.Run("Put and Get", func(t *testing.T) {
		key := "test/file.txt"
		data := []byte("test content")

		err := backend.Put(ctx, key, data)
		require.NoError(t, err)

		retrieved, err := backend.Get(ctx, key)
		require.NoError(t, err)
		assert.Equal(t, data, retrieved)
	})

	t.Run("Exists", func(t *testing.T) {
		key := "test/exists.txt"

		exists, err := backend.Exists(ctx, key)
		require.NoError(t, err)
		assert.False(t, exists)

		err = backend.Put(ctx, key, []byte("data"))
		require.NoError(t, err)

		exists, err = backend.Exists(ctx, key)
		require.NoError(t, err)
		assert.True(t, exists)
	})

	t.Run("Delete", func(t *testing.T) {
		key := "test/delete.txt"

		err := backend.Put(ctx, key, []byte("data"))
		require.NoError(t, err)

		err = backend.Delete(ctx, key)
		require.NoError(t, err)

		exists, err := backend.Exists(ctx, key)
		require.NoError(t, err)
		assert.False(t, exists)
	})

	t.Run("GetReader and PutReader", func(t *testing.T) {
		key := "test/stream.txt"
		data := "streamed content"

		reader := strings.NewReader(data)
		err := backend.PutReader(ctx, key, reader, int64(len(data)))
		require.NoError(t, err)

		readCloser, err := backend.GetReader(ctx, key)
		require.NoError(t, err)
		defer readCloser.Close()

		retrieved, err := io.ReadAll(readCloser)
		require.NoError(t, err)
		assert.Equal(t, data, string(retrieved))
	})

	t.Run("List", func(t *testing.T) {
		// Create test files
		files := []string{
			"list/file1.txt",
			"list/file2.txt",
			"list/subdir/file3.txt",
			"other/file4.txt",
		}

		for _, file := range files {
			err := backend.Put(ctx, file, []byte("data"))
			require.NoError(t, err)
		}

		// List with prefix
		keys, err := backend.List(ctx, "list/")
		require.NoError(t, err)
		assert.Len(t, keys, 3)
		assert.Contains(t, keys, "list/file1.txt")
		assert.Contains(t, keys, "list/file2.txt")
		assert.Contains(t, keys, "list/subdir/file3.txt")
	})

	t.Run("ListWithMetadata", func(t *testing.T) {
		key := "metadata/test.txt"
		data := []byte("metadata test")

		err := backend.Put(ctx, key, data)
		require.NoError(t, err)

		objects, err := backend.ListWithMetadata(ctx, "metadata/")
		require.NoError(t, err)
		require.Len(t, objects, 1)

		obj := objects[0]
		assert.Equal(t, key, obj.Key)
		assert.Equal(t, int64(len(data)), obj.Size)
		assert.WithinDuration(t, time.Now(), obj.Modified, 5*time.Second)
	})

	t.Run("GetMetadata", func(t *testing.T) {
		key := "meta/file.pdf"
		data := []byte("pdf content")

		err := backend.Put(ctx, key, data)
		require.NoError(t, err)

		metadata, err := backend.GetMetadata(ctx, key)
		require.NoError(t, err)

		assert.Equal(t, key, metadata.Key)
		assert.Equal(t, int64(len(data)), metadata.Size)
		assert.Equal(t, "application/pdf", metadata.ContentType)
		assert.WithinDuration(t, time.Now(), metadata.LastModified, 5*time.Second)
	})
}

func TestStorageManager(t *testing.T) {
	tmpDir := t.TempDir()
	primaryBackend, err := NewLocalBackend(filepath.Join(tmpDir, "primary"))
	require.NoError(t, err)

	config := &Config{
		EnableCache:    false,
		EnableFallback: false,
		SyncEnabled:    false,
		RetryAttempts:  2,
		RetryDelay:     10 * time.Millisecond,
	}

	manager := NewManager(primaryBackend, config)
	ctx := context.Background()

	t.Run("Basic Operations", func(t *testing.T) {
		key := "manager/test.txt"
		data := []byte("manager test data")

		// Put
		err := manager.Put(ctx, key, data)
		require.NoError(t, err)

		// Get
		retrieved, err := manager.Get(ctx, key)
		require.NoError(t, err)
		assert.Equal(t, data, retrieved)

		// Exists
		exists, err := manager.Exists(ctx, key)
		require.NoError(t, err)
		assert.True(t, exists)

		// Delete
		err = manager.Delete(ctx, key)
		require.NoError(t, err)

		exists, err = manager.Exists(ctx, key)
		require.NoError(t, err)
		assert.False(t, exists)
	})

	t.Run("With Fallback", func(t *testing.T) {
		fallbackBackend, err := NewLocalBackend(filepath.Join(tmpDir, "fallback"))
		require.NoError(t, err)

		manager.SetFallback(fallbackBackend)
		config.EnableFallback = true

		key := "fallback/test.txt"
		data := []byte("fallback data")

		// Put to fallback only
		err = fallbackBackend.Put(ctx, key, data)
		require.NoError(t, err)

		// Should get from fallback
		retrieved, err := manager.Get(ctx, key)
		require.NoError(t, err)
		assert.Equal(t, data, retrieved)
	})

	t.Run("With Cache", func(t *testing.T) {
		cacheBackend, err := NewLocalBackend(filepath.Join(tmpDir, "cache"))
		require.NoError(t, err)

		manager.SetCache(cacheBackend)
		config.EnableCache = true

		key := "cached/test.txt"
		data := []byte("cached data")

		// Put through manager
		err = manager.Put(ctx, key, data)
		require.NoError(t, err)

		// Delete from primary
		err = primaryBackend.Delete(ctx, key)
		require.NoError(t, err)

		// Should still get from cache
		retrieved, err := manager.Get(ctx, key)
		require.NoError(t, err)
		assert.Equal(t, data, retrieved)
	})

	t.Run("List Operations", func(t *testing.T) {
		// Create test files
		for i := 0; i < 3; i++ {
			key := fmt.Sprintf("listing/file%d.txt", i)
			err := manager.Put(ctx, key, []byte("data"))
			require.NoError(t, err)
		}

		keys, err := manager.List(ctx, "listing/")
		require.NoError(t, err)
		assert.Len(t, keys, 3)

		objects, err := manager.ListWithMetadata(ctx, "listing/")
		require.NoError(t, err)
		assert.Len(t, objects, 3)
	})
}

func TestStorageSync(t *testing.T) {
	tmpDir := t.TempDir()
	primaryBackend, err := NewLocalBackend(filepath.Join(tmpDir, "primary"))
	require.NoError(t, err)

	fallbackBackend, err := NewLocalBackend(filepath.Join(tmpDir, "fallback"))
	require.NoError(t, err)

	config := &Config{
		EnableFallback: true,
		SyncEnabled:    true,
		RetryAttempts:  1,
		RetryDelay:     10 * time.Millisecond,
	}

	manager := NewManager(primaryBackend, config)
	manager.SetFallback(fallbackBackend)

	ctx := context.Background()

	// Create files in primary only
	for i := 0; i < 3; i++ {
		key := fmt.Sprintf("sync/primary%d.txt", i)
		err := primaryBackend.Put(ctx, key, []byte("primary data"))
		require.NoError(t, err)
	}

	// Create files in fallback only
	for i := 0; i < 3; i++ {
		key := fmt.Sprintf("sync/fallback%d.txt", i)
		err := fallbackBackend.Put(ctx, key, []byte("fallback data"))
		require.NoError(t, err)
	}

	// Sync
	err = manager.Sync(ctx, "sync/")
	require.NoError(t, err)

	// Verify all files exist in both backends
	primaryKeys, err := primaryBackend.List(ctx, "sync/")
	require.NoError(t, err)
	assert.Len(t, primaryKeys, 6)

	fallbackKeys, err := fallbackBackend.List(ctx, "sync/")
	require.NoError(t, err)
	assert.Len(t, fallbackKeys, 6)
}
