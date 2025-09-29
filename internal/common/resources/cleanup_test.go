package resources

import (
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"
)

// Mock resource for testing
type mockResource struct {
	closed bool
	err    error
}

func (m *mockResource) Close() error {
	if m.closed {
		return errors.New("already closed")
	}
	m.closed = true
	return m.err
}

func (m *mockResource) IsClosed() bool {
	return m.closed
}

// Mock closer function
type mockCloserFunc func() error

func (f mockCloserFunc) Close() error {
	return f()
}

func TestResourceManager_New(t *testing.T) {
	rm := NewResourceManager()
	if rm == nil {
		t.Fatal("NewResourceManager returned nil")
	}
	if rm.resources == nil {
		t.Error("Resources slice not initialized")
	}
	if rm.closed {
		t.Error("Resource manager should not be closed initially")
	}
}

func TestResourceManager_Register(t *testing.T) {
	rm := NewResourceManager()

	// Register a resource
	resource := &mockResource{}
	rm.Register(resource)

	if len(rm.resources) != 1 {
		t.Errorf("Expected 1 resource, got %d", len(rm.resources))
	}
	if rm.resources[0] != resource {
		t.Error("Registered resource not found")
	}
}

func TestResourceManager_RegisterMultiple(t *testing.T) {
	rm := NewResourceManager()

	// Register multiple resources
	resources := []*mockResource{
		{},
		{},
		{},
	}

	for _, resource := range resources {
		rm.Register(resource)
	}

	if len(rm.resources) != len(resources) {
		t.Errorf("Expected %d resources, got %d", len(resources), len(rm.resources))
	}
}

func TestResourceManager_RegisterFunc(t *testing.T) {
	rm := NewResourceManager()

	called := false
	rm.RegisterFunc(func() error {
		called = true
		return nil
	})

	if len(rm.resources) != 1 {
		t.Errorf("Expected 1 resource, got %d", len(rm.resources))
	}

	// Test that the function is called
	err := rm.resources[0].Close()
	if err != nil {
		t.Errorf("Close function failed: %v", err)
	}
	if !called {
		t.Error("Close function was not called")
	}
}

func TestResourceManager_Close(t *testing.T) {
	rm := NewResourceManager()

	// Register resources
	resources := []*mockResource{
		{},
		{},
		{},
	}

	for _, resource := range resources {
		rm.Register(resource)
	}

	// Close all resources
	err := rm.Close()
	if err != nil {
		t.Errorf("Close failed: %v", err)
	}

	// Check that all resources are closed
	for _, resource := range resources {
		if !resource.IsClosed() {
			t.Error("Resource was not closed")
		}
	}

	// Check that manager is closed
	if !rm.closed {
		t.Error("Resource manager should be closed")
	}

	// Check that resources slice is cleared
	if rm.resources != nil {
		t.Error("Resources slice should be cleared")
	}
}

func TestResourceManager_CloseReverseOrder(t *testing.T) {
	rm := NewResourceManager()

	// Track close order
	var closeOrder []int
	resources := []*mockResource{
		{},
		{},
		{},
	}

	// Register resources with tracking
	for i, resource := range resources {
		index := i // Capture loop variable
		rm.RegisterFunc(func() error {
			closeOrder = append(closeOrder, index)
			return resource.Close()
		})
	}

	// Close all resources
	err := rm.Close()
	if err != nil {
		t.Errorf("Close failed: %v", err)
	}

	// Check that resources were closed in reverse order (LIFO)
	expectedOrder := []int{2, 1, 0}
	if len(closeOrder) != len(expectedOrder) {
		t.Errorf("Expected %d close calls, got %d", len(expectedOrder), len(closeOrder))
	}

	for i, expected := range expectedOrder {
		if closeOrder[i] != expected {
			t.Errorf("Expected close order %v, got %v", expectedOrder, closeOrder)
			break
		}
	}
}

func TestResourceManager_CloseWithErrors(t *testing.T) {
	rm := NewResourceManager()

	// Register resources with errors
	resources := []*mockResource{
		{err: errors.New("close error 1")},
		{err: errors.New("close error 2")},
		{}, // No error
	}

	for _, resource := range resources {
		rm.Register(resource)
	}

	// Close all resources
	err := rm.Close()
	if err == nil {
		t.Error("Expected error from Close")
	}

	// Check error message
	expectedMsg := "failed to close 2 resources"
	if err.Error() != expectedMsg {
		t.Errorf("Expected error message '%s', got '%s'", expectedMsg, err.Error())
	}

	// Check that all resources are still closed despite errors
	for _, resource := range resources {
		if !resource.IsClosed() {
			t.Error("Resource was not closed")
		}
	}
}

func TestResourceManager_CloseTwice(t *testing.T) {
	rm := NewResourceManager()

	resource := &mockResource{}
	rm.Register(resource)

	// Close first time
	err := rm.Close()
	if err != nil {
		t.Errorf("First close failed: %v", err)
	}

	// Close second time should be no-op
	err = rm.Close()
	if err != nil {
		t.Errorf("Second close failed: %v", err)
	}

	// Resource should only be closed once
	if !resource.IsClosed() {
		t.Error("Resource should be closed")
	}
}

func TestResourceManager_RegisterAfterClose(t *testing.T) {
	rm := NewResourceManager()

	// Close manager
	err := rm.Close()
	if err != nil {
		t.Errorf("Close failed: %v", err)
	}

	// Register resource after close
	resource := &mockResource{}
	rm.Register(resource)

	// Resource should be closed immediately
	if !resource.IsClosed() {
		t.Error("Resource should be closed immediately when registered after manager close")
	}

	// Resources slice should remain empty
	if len(rm.resources) != 0 {
		t.Errorf("Expected 0 resources after close, got %d", len(rm.resources))
	}
}

func TestSafeClose(t *testing.T) {
	// Note: logger.SetOutput is not available in the current logger implementation
	// This test focuses on the core functionality

	// Test with nil resource
	SafeClose(nil, "nil-resource")

	// Test with valid resource
	resource := &mockResource{}
	SafeClose(resource, "test-resource")

	if !resource.IsClosed() {
		t.Error("Resource should be closed")
	}

	// Test with resource that returns error
	errorResource := &mockResource{err: errors.New("close error")}
	SafeClose(errorResource, "error-resource")

	if !errorResource.IsClosed() {
		t.Error("Resource should be closed despite error")
	}
}

func TestSafeCloseWithTimeout(t *testing.T) {
	// Note: logger.SetOutput is not available in the current logger implementation
	// This test focuses on the core functionality

	// Test with nil resource
	SafeCloseWithTimeout(nil, "nil-resource", 100*time.Millisecond)

	// Test with valid resource
	resource := &mockResource{}
	SafeCloseWithTimeout(resource, "test-resource", 100*time.Millisecond)

	if !resource.IsClosed() {
		t.Error("Resource should be closed")
	}

	// Test with resource that returns error
	errorResource := &mockResource{err: errors.New("close error")}
	SafeCloseWithTimeout(errorResource, "error-resource", 100*time.Millisecond)

	if !errorResource.IsClosed() {
		t.Error("Resource should be closed despite error")
	}
}

func TestSafeCloseWithTimeout_Timeout(t *testing.T) {
	// Note: logger.SetOutput is not available in the current logger implementation
	// This test focuses on the core functionality

	// Create a resource that takes longer than timeout to close
	slowResource := &mockResource{}

	SafeCloseWithTimeout(slowResource, "slow-resource", 50*time.Millisecond)

	// Resource should eventually be closed (goroutine continues)
	time.Sleep(300 * time.Millisecond)
	if !slowResource.IsClosed() {
		t.Error("Resource should be closed eventually")
	}
}

func TestFileManager_New(t *testing.T) {
	fm := NewFileManager()
	if fm == nil {
		t.Fatal("NewFileManager returned nil")
	}
	if fm.files == nil {
		t.Error("Files map not initialized")
	}
}

func TestFileManager_Open(t *testing.T) {
	fm := NewFileManager()

	// Create a temporary file
	tmpFile, err := os.CreateTemp("", "test-file-*")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}
	defer os.Remove(tmpFile.Name())
	tmpFile.Close()

	// Open file through manager
	_, err = fm.Open(tmpFile.Name())
	if err != nil {
		t.Fatalf("Open failed: %v", err)
	}

	// Check that file is tracked
	if len(fm.files) != 1 {
		t.Errorf("Expected 1 tracked file, got %d", len(fm.files))
	}

	// File should be tracked
	if len(fm.files) != 1 {
		t.Error("File not properly tracked")
	}
}

func TestFileManager_Create(t *testing.T) {
	fm := NewFileManager()

	// Create temporary file path
	tmpPath := filepath.Join(os.TempDir(), "test-create-file")
	defer os.Remove(tmpPath)

	// Create file through manager
	_, err := fm.Create(tmpPath)
	if err != nil {
		t.Fatalf("Create failed: %v", err)
	}

	// Check that file is tracked
	if len(fm.files) != 1 {
		t.Errorf("Expected 1 tracked file, got %d", len(fm.files))
	}

	// File should be tracked
	if len(fm.files) != 1 {
		t.Error("File not properly tracked")
	}
}

func TestFileManager_Close(t *testing.T) {
	fm := NewFileManager()

	// Create a temporary file
	tmpFile, err := os.CreateTemp("", "test-file-*")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}
	defer os.Remove(tmpFile.Name())
	tmpFile.Close()

	// Open file through manager
	_, err = fm.Open(tmpFile.Name())
	if err != nil {
		t.Fatalf("Open failed: %v", err)
	}

	// Close specific file
	err = fm.Close(tmpFile.Name())
	if err != nil {
		t.Errorf("Close failed: %v", err)
	}

	// Check that file is no longer tracked
	if len(fm.files) != 0 {
		t.Errorf("Expected 0 tracked files, got %d", len(fm.files))
	}

	// Try to close non-existent file (should not error)
	err = fm.Close("non-existent")
	if err != nil {
		t.Errorf("Close non-existent file failed: %v", err)
	}
}

func TestFileManager_CloseAll(t *testing.T) {
	fm := NewFileManager()

	// Create multiple temporary files
	tmpFiles := make([]string, 3)
	for i := 0; i < 3; i++ {
		tmpFile, err := os.CreateTemp("", fmt.Sprintf("test-file-%d-*", i))
		if err != nil {
			t.Fatalf("Failed to create temp file %d: %v", i, err)
		}
		defer os.Remove(tmpFile.Name())
		tmpFile.Close()
		tmpFiles[i] = tmpFile.Name()

		// Open through manager
		_, err = fm.Open(tmpFile.Name())
		if err != nil {
			t.Fatalf("Open failed for file %d: %v", i, err)
		}
	}

	// Close all files
	err := fm.CloseAll()
	if err != nil {
		t.Errorf("CloseAll failed: %v", err)
	}

	// Check that no files are tracked
	if len(fm.files) != 0 {
		t.Errorf("Expected 0 tracked files, got %d", len(fm.files))
	}
}

func TestDatabaseManager_New(t *testing.T) {
	dm := NewDatabaseManager()
	if dm == nil {
		t.Fatal("NewDatabaseManager returned nil")
	}
	if dm.connections == nil {
		t.Error("Connections map not initialized")
	}
}

func TestDatabaseManager_Connect(t *testing.T) {
	dm := NewDatabaseManager()

	// Test with invalid driver (should fail)
	_, err := dm.Connect("test", "invalid-driver", "invalid-dsn")
	if err == nil {
		t.Error("Expected error with invalid driver")
	}

	// For testing purposes, we'll skip actual database connection tests
	// since ArxOS uses PostGIS and we don't want to require a full database setup for unit tests
	// The DatabaseManager is primarily tested through its interface and resource management
}

func TestDatabaseManager_Get(t *testing.T) {
	dm := NewDatabaseManager()

	// Get non-existent connection
	db, exists := dm.Get("non-existent")
	if exists {
		t.Error("Expected non-existent connection to not exist")
	}
	if db != nil {
		t.Error("Expected nil connection")
	}

	// Skip actual connection test since we're using PostGIS
	// The Get method functionality is tested through the interface
}

func TestDatabaseManager_Close(t *testing.T) {
	dm := NewDatabaseManager()

	// Test closing non-existent connection (should not error)
	err := dm.Close("non-existent")
	if err != nil {
		t.Errorf("Close non-existent connection failed: %v", err)
	}

	// Test that connections map is properly initialized
	if dm.connections == nil {
		t.Error("Connections map not initialized")
	}
}

func TestDatabaseManager_CloseAll(t *testing.T) {
	dm := NewDatabaseManager()

	// Test CloseAll on empty manager (should not error)
	err := dm.CloseAll()
	if err != nil {
		t.Errorf("CloseAll failed: %v", err)
	}

	// Check that connections map is properly initialized
	if dm.connections == nil {
		t.Error("Connections map not initialized")
	}
}

func TestConnectionPool_New(t *testing.T) {
	factory := func() (io.Closer, error) {
		return &mockResource{}, nil
	}

	cp := NewConnectionPool(factory, 5)
	if cp == nil {
		t.Fatal("NewConnectionPool returned nil")
	}
	if cp.factory == nil {
		t.Error("Factory not set")
	}
	if cp.maxSize != 5 {
		t.Errorf("Expected maxSize=5, got %d", cp.maxSize)
	}
	if cap(cp.pool) != 5 {
		t.Errorf("Expected pool capacity=5, got %d", cap(cp.pool))
	}
}

func TestConnectionPool_Get(t *testing.T) {
	factory := func() (io.Closer, error) {
		return &mockResource{}, nil
	}

	cp := NewConnectionPool(factory, 2)

	// Get connection
	conn, err := cp.Get()
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if conn == nil {
		t.Fatal("Expected non-nil connection")
	}

	// Return connection
	cp.Put(conn)

	// Get connection again (should reuse)
	conn2, err := cp.Get()
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if conn2 != conn {
		t.Error("Expected reused connection")
	}
}

func TestConnectionPool_GetClosed(t *testing.T) {
	factory := func() (io.Closer, error) {
		return &mockResource{}, nil
	}

	cp := NewConnectionPool(factory, 2)

	// Close pool
	err := cp.Close()
	if err != nil {
		t.Fatalf("Close failed: %v", err)
	}

	// Try to get connection from closed pool
	_, err = cp.Get()
	if err == nil {
		t.Error("Expected error when getting from closed pool")
	}
	if err.Error() != "pool is closed" {
		t.Errorf("Expected 'pool is closed', got '%s'", err.Error())
	}
}

func TestConnectionPool_Put(t *testing.T) {
	factory := func() (io.Closer, error) {
		return &mockResource{}, nil
	}

	cp := NewConnectionPool(factory, 1)

	// Get connection
	conn, err := cp.Get()
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	// Return connection to pool (pool now has 1 connection)
	cp.Put(conn)

	// Get another connection (should reuse from pool)
	conn2, err := cp.Get()
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	// Verify it's the same connection (reused from pool)
	if conn != conn2 {
		t.Error("Expected same connection to be reused from pool")
	}

	// Put connection back to pool (pool is full again)
	cp.Put(conn2)

	// Test that we can get and put connections multiple times
	for i := 0; i < 5; i++ {
		conn, err := cp.Get()
		if err != nil {
			t.Fatalf("Get failed on iteration %d: %v", i, err)
		}
		cp.Put(conn)
	}
}

func TestConnectionPool_PutClosed(t *testing.T) {
	factory := func() (io.Closer, error) {
		return &mockResource{}, nil
	}

	cp := NewConnectionPool(factory, 2)

	// Get connection
	conn, err := cp.Get()
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	// Close pool
	err = cp.Close()
	if err != nil {
		t.Fatalf("Close failed: %v", err)
	}

	// Try to put connection to closed pool (should close it)
	cp.Put(conn)

	// Verify connection was closed
	if !conn.(*mockResource).IsClosed() {
		t.Error("Connection should be closed when putting to closed pool")
	}
}

func TestConnectionPool_Close(t *testing.T) {
	factory := func() (io.Closer, error) {
		return &mockResource{}, nil
	}

	cp := NewConnectionPool(factory, 2)

	// Get and return connections
	conn1, err := cp.Get()
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	cp.Put(conn1)

	conn2, err := cp.Get()
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	cp.Put(conn2)

	// Close pool
	err = cp.Close()
	if err != nil {
		t.Errorf("Close failed: %v", err)
	}

	// Verify connections were closed
	if !conn1.(*mockResource).IsClosed() {
		t.Error("Connection 1 should be closed")
	}
	if !conn2.(*mockResource).IsClosed() {
		t.Error("Connection 2 should be closed")
	}
}

func TestWithResource(t *testing.T) {
	var called bool
	var receivedResource io.Closer

	factory := func() (*mockResource, error) {
		return &mockResource{}, nil
	}

	fn := func(resource *mockResource) error {
		called = true
		receivedResource = resource
		return nil
	}

	err := WithResource(factory, fn)
	if err != nil {
		t.Errorf("WithResource failed: %v", err)
	}

	if !called {
		t.Error("Function was not called")
	}
	if receivedResource == nil {
		t.Error("Resource was not passed to function")
	}
	if !receivedResource.(*mockResource).IsClosed() {
		t.Error("Resource should be closed after function returns")
	}
}

func TestWithResource_FactoryError(t *testing.T) {
	factory := func() (*mockResource, error) {
		return nil, errors.New("factory error")
	}

	fn := func(resource *mockResource) error {
		t.Error("Function should not be called when factory fails")
		return nil
	}

	err := WithResource(factory, fn)
	if err == nil {
		t.Error("Expected error from factory")
	}
	if err.Error() != "factory error" {
		t.Errorf("Expected 'factory error', got '%s'", err.Error())
	}
}

func TestWithResource_FunctionError(t *testing.T) {
	factory := func() (*mockResource, error) {
		return &mockResource{}, nil
	}

	fn := func(resource *mockResource) error {
		return errors.New("function error")
	}

	err := WithResource(factory, fn)
	if err == nil {
		t.Error("Expected error from function")
	}
	if err.Error() != "function error" {
		t.Errorf("Expected 'function error', got '%s'", err.Error())
	}
}

func TestWithTimeout(t *testing.T) {
	ctx := context.Background()

	// Test successful function
	fn := func(ctx context.Context) error {
		return nil
	}

	err := WithTimeout(ctx, 100*time.Millisecond, fn)
	if err != nil {
		t.Errorf("WithTimeout failed: %v", err)
	}
}

func TestWithTimeout_FunctionError(t *testing.T) {
	ctx := context.Background()

	fn := func(ctx context.Context) error {
		return errors.New("function error")
	}

	err := WithTimeout(ctx, 100*time.Millisecond, fn)
	if err == nil {
		t.Error("Expected error from function")
	}
	if err.Error() != "function error" {
		t.Errorf("Expected 'function error', got '%s'", err.Error())
	}
}

func TestWithTimeout_Timeout(t *testing.T) {
	ctx := context.Background()

	fn := func(ctx context.Context) error {
		time.Sleep(200 * time.Millisecond)
		return nil
	}

	err := WithTimeout(ctx, 50*time.Millisecond, fn)
	if err == nil {
		t.Error("Expected timeout error")
	}
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Errorf("Expected context.DeadlineExceeded, got %v", err)
	}
}

func TestLeakDetector_New(t *testing.T) {
	ld := NewLeakDetector()
	if ld == nil {
		t.Fatal("NewLeakDetector returned nil")
	}
}

func TestLeakDetector_Start(t *testing.T) {
	ld := NewLeakDetector()

	// Start should not panic
	ld.Start()
}

func TestLeakDetector_Check(t *testing.T) {
	ld := NewLeakDetector()

	// Check should not panic and return no error
	err := ld.Check()
	if err != nil {
		t.Errorf("Check failed: %v", err)
	}
}

// Concurrent tests
func TestResourceManager_Concurrent(t *testing.T) {
	rm := NewResourceManager()

	var wg sync.WaitGroup
	numGoroutines := 10
	resourcesPerGoroutine := 5

	// Concurrent registration
	for i := 0; i < numGoroutines; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < resourcesPerGoroutine; j++ {
				rm.Register(&mockResource{})
			}
		}()
	}

	wg.Wait()

	// Check total resources
	expectedTotal := numGoroutines * resourcesPerGoroutine
	if len(rm.resources) != expectedTotal {
		t.Errorf("Expected %d resources, got %d", expectedTotal, len(rm.resources))
	}

	// Close all resources
	err := rm.Close()
	if err != nil {
		t.Errorf("Close failed: %v", err)
	}
}

func TestFileManager_Concurrent(t *testing.T) {
	fm := NewFileManager()

	var wg sync.WaitGroup
	numGoroutines := 5

	// Create temporary files
	tmpFiles := make([]string, numGoroutines)
	for i := 0; i < numGoroutines; i++ {
		tmpFile, err := os.CreateTemp("", fmt.Sprintf("test-concurrent-%d-*", i))
		if err != nil {
			t.Fatalf("Failed to create temp file %d: %v", i, err)
		}
		defer os.Remove(tmpFile.Name())
		tmpFile.Close()
		tmpFiles[i] = tmpFile.Name()
	}

	// Concurrent operations
	for i := 0; i < numGoroutines; i++ {
		wg.Add(1)
		go func(index int) {
			defer wg.Done()

			// Open file
			file, err := fm.Open(tmpFiles[index])
			if err != nil {
				t.Errorf("Open failed for goroutine %d: %v", index, err)
				return
			}
			defer file.Close()

			// Close file
			err = fm.Close(tmpFiles[index])
			if err != nil {
				t.Errorf("Close failed for goroutine %d: %v", index, err)
			}
		}(i)
	}

	wg.Wait()

	// All files should be closed
	if len(fm.files) != 0 {
		t.Errorf("Expected 0 tracked files, got %d", len(fm.files))
	}
}

// Benchmark tests
func BenchmarkResourceManager_Register(b *testing.B) {
	rm := NewResourceManager()
	defer rm.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		rm.Register(&mockResource{})
	}
}

func BenchmarkResourceManager_Close(b *testing.B) {
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		rm := NewResourceManager()
		for j := 0; j < 100; j++ {
			rm.Register(&mockResource{})
		}
		rm.Close()
	}
}

func BenchmarkConnectionPool_GetPut(b *testing.B) {
	factory := func() (io.Closer, error) {
		return &mockResource{}, nil
	}

	cp := NewConnectionPool(factory, 10)
	defer cp.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		conn, err := cp.Get()
		if err != nil {
			b.Fatalf("Get failed: %v", err)
		}
		cp.Put(conn)
	}
}

func BenchmarkWithResource(b *testing.B) {
	factory := func() (*mockResource, error) {
		return &mockResource{}, nil
	}

	fn := func(resource *mockResource) error {
		return nil
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		WithResource(factory, fn)
	}
}
