package postgis

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

// Note: These tests require a running PostgreSQL database with PostGIS extension
// They will be skipped if the database is not available

func setupTestObjectRepository(t *testing.T) (*ObjectRepository, func()) {
	t.Helper()

	// Use test database credentials
	dsn := "host=localhost port=5432 user=arxos_test password=test_password dbname=arxos_test sslmode=disable"
	db, err := sqlx.Connect("postgres", dsn)
	if err != nil {
		t.Skipf("Cannot connect to test database: %v", err)
		return nil, func() {}
	}

	// Verify connection
	if err := db.Ping(); err != nil {
		db.Close()
		t.Skipf("Cannot ping test database: %v", err)
		return nil, func() {}
	}

	// Create temporary object storage directory
	tempDir, err := os.MkdirTemp("", "arxos-test-objects-*")
	if err != nil {
		db.Close()
		t.Fatalf("Failed to create temp dir: %v", err)
	}

	repo := NewObjectRepository(db, tempDir)

	// Clean up any existing test data from previous runs
	db.ExecContext(context.Background(), "DELETE FROM version_objects WHERE hash LIKE 'test-%' OR hash LIKE 'small-%' OR hash LIKE 'medium-%' OR hash LIKE 'large-%'")
	db.ExecContext(context.Background(), "DELETE FROM version_objects WHERE type = 'test'")

	// Return cleanup function that removes both DB and temp dir
	return repo, func() {
		// Clean up test data
		db.ExecContext(context.Background(), "DELETE FROM version_objects WHERE hash LIKE 'test-%' OR hash LIKE 'small-%' OR hash LIKE 'medium-%' OR hash LIKE 'large-%'")
		db.ExecContext(context.Background(), "DELETE FROM version_objects WHERE type = 'test'")
		os.RemoveAll(tempDir)
		db.Close()
	}
}

func TestObjectRepository_StoreAndLoad_SmallObject(t *testing.T) {
	repo, cleanup := setupTestObjectRepository(t)
	defer cleanup()

	ctx := context.Background()

	// Create a small object (< 1KB, should be stored in DB)
	obj := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     100,
		Contents: []byte("This is a small test object that should be stored in the database"),
	}

	// Pre-calculate hash and ensure it's clean before test
	obj.Hash = building.CalculateObjectHash(obj.Type, obj.Size, obj.Contents)
	repo.db.ExecContext(ctx, "DELETE FROM version_objects WHERE hash = $1", obj.Hash)

	// Store object
	hash, err := repo.Store(ctx, obj)
	if err != nil {
		t.Fatalf("Failed to store object: %v", err)
	}

	// Verify hash is returned
	if hash == "" {
		t.Fatal("Store() returned empty hash")
	}

	// Load object
	loaded, err := repo.Load(ctx, hash)
	if err != nil {
		t.Fatalf("Failed to load object: %v", err)
	}

	// Verify contents match
	if string(loaded.Contents) != string(obj.Contents) {
		t.Errorf("Loaded contents don't match. Got %q, want %q", string(loaded.Contents), string(obj.Contents))
	}

	// Verify type matches
	if loaded.Type != obj.Type {
		t.Errorf("Loaded type = %v, want %v", loaded.Type, obj.Type)
	}

	// Verify size matches
	if loaded.Size != obj.Size {
		t.Errorf("Loaded size = %v, want %v", loaded.Size, obj.Size)
	}

	// Verify ref count is initialized
	if loaded.RefCount != 1 {
		t.Errorf("RefCount = %v, want 1", loaded.RefCount)
	}
}

func TestObjectRepository_StoreAndLoad_MediumObject(t *testing.T) {
	repo, cleanup := setupTestObjectRepository(t)
	defer cleanup()

	ctx := context.Background()

	// Create a medium object (1KB - 10MB, should be stored in filesystem uncompressed)
	contents := make([]byte, 5*1024) // 5KB
	for i := range contents {
		contents[i] = byte(i % 256)
	}

	obj := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(contents)),
		Contents: contents,
	}

	// Pre-calculate hash and ensure it's clean before test
	obj.Hash = building.CalculateObjectHash(obj.Type, obj.Size, obj.Contents)
	repo.db.ExecContext(ctx, "DELETE FROM version_objects WHERE hash = $1", obj.Hash)
	// Also clean up any filesystem objects from previous runs
	objectPath := repo.getObjectPath(obj.Hash)
	os.RemoveAll(filepath.Dir(objectPath))

	// Store object
	hash, err := repo.Store(ctx, obj)
	if err != nil {
		t.Fatalf("Failed to store object: %v", err)
	}

	// Verify file was created
	objectPath = repo.getObjectPath(hash)
	if _, err := os.Stat(objectPath); os.IsNotExist(err) {
		t.Errorf("Object file was not created at %s", objectPath)
	}

	// Load object
	loaded, err := repo.Load(ctx, hash)
	if err != nil {
		t.Fatalf("Failed to load object: %v", err)
	}

	// Verify contents match
	if len(loaded.Contents) != len(contents) {
		t.Errorf("Loaded contents length = %v, want %v", len(loaded.Contents), len(contents))
	}

	// Verify StorePath is set
	if loaded.StorePath == "" {
		t.Error("StorePath should be set for filesystem-stored objects")
	}
}

func TestObjectRepository_StoreAndLoad_LargeObject(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping large object test in short mode")
	}

	repo, cleanup := setupTestObjectRepository(t)
	defer cleanup()

	ctx := context.Background()

	// Create a large object (> 10MB, should be stored compressed)
	contents := make([]byte, 11*1024*1024) // 11MB
	for i := range contents {
		contents[i] = byte(i % 256)
	}

	obj := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(contents)),
		Contents: contents,
	}

	// Pre-calculate hash and ensure it's clean before test
	obj.Hash = building.CalculateObjectHash(obj.Type, obj.Size, obj.Contents)
	repo.db.ExecContext(ctx, "DELETE FROM version_objects WHERE hash = $1", obj.Hash)
	// Also clean up any filesystem objects from previous runs
	objectPath := repo.getObjectPath(obj.Hash)
	os.RemoveAll(filepath.Dir(objectPath))

	// Store object
	hash, err := repo.Store(ctx, obj)
	if err != nil {
		t.Fatalf("Failed to store object: %v", err)
	}

	// Load object
	loaded, err := repo.Load(ctx, hash)
	if err != nil {
		t.Fatalf("Failed to load object: %v", err)
	}

	// Verify compression flag is set
	if !loaded.Compressed {
		t.Error("Large object should be compressed")
	}

	// Verify contents match (after decompression)
	if len(loaded.Contents) != len(contents) {
		t.Errorf("Loaded contents length = %v, want %v", len(loaded.Contents), len(contents))
	}
}

func TestObjectRepository_Exists(t *testing.T) {
	repo, cleanup := setupTestObjectRepository(t)
	defer cleanup()

	ctx := context.Background()

	// Create and store an object
	obj := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     50,
		Contents: []byte("test object for exists check"),
	}

	hash, err := repo.Store(ctx, obj)
	if err != nil {
		t.Fatalf("Failed to store object: %v", err)
	}

	// Check if object exists (should be true)
	exists, err := repo.Exists(ctx, hash)
	if err != nil {
		t.Fatalf("Exists() error: %v", err)
	}
	if !exists {
		t.Error("Exists() = false, want true for stored object")
	}

	// Check non-existent object (should be false)
	exists, err = repo.Exists(ctx, "nonexistent-hash")
	if err != nil {
		t.Fatalf("Exists() error: %v", err)
	}
	if exists {
		t.Error("Exists() = true, want false for non-existent object")
	}
}

func TestObjectRepository_IncrementRef(t *testing.T) {
	repo, cleanup := setupTestObjectRepository(t)
	defer cleanup()

	ctx := context.Background()

	// Create and store an object
	obj := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     50,
		Contents: []byte("test object for ref count"),
	}

	// Pre-calculate hash and ensure it's clean before test
	obj.Hash = building.CalculateObjectHash(obj.Type, obj.Size, obj.Contents)
	repo.db.ExecContext(ctx, "DELETE FROM version_objects WHERE hash = $1", obj.Hash)

	hash, err := repo.Store(ctx, obj)
	if err != nil {
		t.Fatalf("Failed to store object: %v", err)
	}

	// Initial ref count should be 1
	loaded, err := repo.Load(ctx, hash)
	if err != nil {
		t.Fatalf("Failed to load object: %v", err)
	}
	if loaded.RefCount != 1 {
		t.Errorf("Initial RefCount = %v, want 1", loaded.RefCount)
	}

	// Increment ref count
	err = repo.IncrementRef(ctx, hash)
	if err != nil {
		t.Fatalf("IncrementRef() error: %v", err)
	}

	// Verify ref count increased
	loaded, err = repo.Load(ctx, hash)
	if err != nil {
		t.Fatalf("Failed to load object: %v", err)
	}
	if loaded.RefCount != 2 {
		t.Errorf("RefCount after increment = %v, want 2", loaded.RefCount)
	}
}

func TestObjectRepository_DecrementRef(t *testing.T) {
	repo, cleanup := setupTestObjectRepository(t)
	defer cleanup()

	ctx := context.Background()

	// Create and store an object
	obj := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     50,
		Contents: []byte("test object for decrement ref count test"),
	}

	// Pre-calculate hash and ensure it's clean before test
	obj.Hash = building.CalculateObjectHash(obj.Type, obj.Size, obj.Contents)
	repo.db.ExecContext(ctx, "DELETE FROM version_objects WHERE hash = $1", obj.Hash)

	hash, err := repo.Store(ctx, obj)
	if err != nil {
		t.Fatalf("Failed to store object: %v", err)
	}

	// Increment ref count first
	err = repo.IncrementRef(ctx, hash)
	if err != nil {
		t.Fatalf("IncrementRef() error: %v", err)
	}

	// Verify ref count is 2
	loaded, err := repo.Load(ctx, hash)
	if err != nil {
		t.Fatalf("Failed to load object: %v", err)
	}
	if loaded.RefCount != 2 {
		t.Errorf("RefCount before decrement = %v, want 2", loaded.RefCount)
	}

	// Decrement ref count
	err = repo.DecrementRef(ctx, hash)
	if err != nil {
		t.Fatalf("DecrementRef() error: %v", err)
	}

	// Verify ref count decreased
	loaded, err = repo.Load(ctx, hash)
	if err != nil {
		t.Fatalf("Failed to load object: %v", err)
	}
	if loaded.RefCount != 1 {
		t.Errorf("RefCount after decrement = %v, want 1", loaded.RefCount)
	}
}

func TestObjectRepository_ListByType(t *testing.T) {
	repo, cleanup := setupTestObjectRepository(t)
	defer cleanup()

	ctx := context.Background()

	// Store multiple objects of different types
	blobObj1 := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     50,
		Contents: []byte("blob 1"),
	}
	blobObj2 := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     50,
		Contents: []byte("blob 2"),
	}
	treeObj := &building.Object{
		Type:     building.ObjectTypeTree,
		Size:     100,
		Contents: []byte(`{"entries":[]}`),
	}

	_, err := repo.Store(ctx, blobObj1)
	if err != nil {
		t.Fatalf("Failed to store blob 1: %v", err)
	}
	_, err = repo.Store(ctx, blobObj2)
	if err != nil {
		t.Fatalf("Failed to store blob 2: %v", err)
	}
	_, err = repo.Store(ctx, treeObj)
	if err != nil {
		t.Fatalf("Failed to store tree: %v", err)
	}

	// List blob objects
	blobs, err := repo.ListByType(ctx, building.ObjectTypeBlob, 10, 0)
	if err != nil {
		t.Fatalf("ListByType() error: %v", err)
	}
	if len(blobs) < 2 {
		t.Errorf("ListByType(blob) returned %d objects, want at least 2", len(blobs))
	}

	// List tree objects
	trees, err := repo.ListByType(ctx, building.ObjectTypeTree, 10, 0)
	if err != nil {
		t.Fatalf("ListByType() error: %v", err)
	}
	if len(trees) < 1 {
		t.Errorf("ListByType(tree) returned %d objects, want at least 1", len(trees))
	}
}

func TestObjectRepository_DeleteUnreferenced(t *testing.T) {
	repo, cleanup := setupTestObjectRepository(t)
	defer cleanup()

	ctx := context.Background()

	// Create an old unreferenced object
	oldObj := &building.Object{
		Type:      building.ObjectTypeBlob,
		Size:      50,
		Contents:  []byte("old unreferenced object"),
		RefCount:  0,
		CreatedAt: time.Now().Add(-48 * time.Hour), // 2 days old
	}

	hash, err := repo.Store(ctx, oldObj)
	if err != nil {
		t.Fatalf("Failed to store object: %v", err)
	}

	// Manually set ref count to 0
	err = repo.DecrementRef(ctx, hash)
	if err != nil {
		t.Fatalf("DecrementRef() error: %v", err)
	}

	// Delete unreferenced objects older than 24 hours
	count, err := repo.DeleteUnreferenced(ctx, time.Now().Add(-24*time.Hour))
	if err != nil {
		t.Fatalf("DeleteUnreferenced() error: %v", err)
	}

	if count < 1 {
		t.Errorf("DeleteUnreferenced() deleted %d objects, want at least 1", count)
	}

	// Verify object no longer exists
	exists, err := repo.Exists(ctx, hash)
	if err != nil {
		t.Fatalf("Exists() error: %v", err)
	}
	if exists {
		t.Error("Object should have been deleted but still exists")
	}
}

func TestObjectRepository_Deduplication(t *testing.T) {
	repo, cleanup := setupTestObjectRepository(t)
	defer cleanup()

	ctx := context.Background()

	// Create two identical objects
	contents := []byte("identical content for deduplication test")
	obj1 := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(contents)),
		Contents: contents,
	}
	obj2 := &building.Object{
		Type:     building.ObjectTypeBlob,
		Size:     int64(len(contents)),
		Contents: contents,
	}

	// Pre-calculate hash and ensure it's clean before test
	obj1.Hash = building.CalculateObjectHash(obj1.Type, obj1.Size, obj1.Contents)
	repo.db.ExecContext(ctx, "DELETE FROM version_objects WHERE hash = $1", obj1.Hash)

	// Store first object
	hash1, err := repo.Store(ctx, obj1)
	if err != nil {
		t.Fatalf("Failed to store first object: %v", err)
	}

	// Store second identical object
	hash2, err := repo.Store(ctx, obj2)
	if err != nil {
		t.Fatalf("Failed to store second object: %v", err)
	}

	// Hashes should be identical (deduplication)
	if hash1 != hash2 {
		t.Errorf("Identical objects have different hashes: %s != %s", hash1, hash2)
	}

	// Load object and verify ref count increased
	loaded, err := repo.Load(ctx, hash1)
	if err != nil {
		t.Fatalf("Failed to load object: %v", err)
	}

	// Ref count should be 2 (stored twice)
	if loaded.RefCount != 2 {
		t.Errorf("RefCount = %v, want 2 (deduplication should increment ref count)", loaded.RefCount)
	}
}

func TestObjectRepository_GetObjectPath(t *testing.T) {
	tempDir := "/tmp/test-objects"
	repo := &ObjectRepository{storePath: tempDir}

	tests := []struct {
		hash string
		want string
	}{
		{
			hash: "abc123def456",
			want: filepath.Join(tempDir, "ab", "c123def456"),
		},
		{
			hash: "1234567890",
			want: filepath.Join(tempDir, "12", "34567890"),
		},
		{
			hash: "ab",
			want: filepath.Join(tempDir, "ab"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.hash, func(t *testing.T) {
			got := repo.getObjectPath(tt.hash)
			if got != tt.want {
				t.Errorf("getObjectPath(%s) = %s, want %s", tt.hash, got, tt.want)
			}
		})
	}
}
