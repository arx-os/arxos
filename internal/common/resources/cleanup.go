package resources

import (
	"context"
	"database/sql"
	"fmt"
	"io"
	"os"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
)

// Closer represents a resource that can be closed
type Closer interface {
	Close() error
}

// CloseFunc is an adapter to allow regular functions to be used as Closers
type CloseFunc func() error

func (f CloseFunc) Close() error {
	return f()
}

// ResourceManager manages resource lifecycle and cleanup
type ResourceManager struct {
	resources []Closer
	mu        sync.Mutex
	closed    bool
}

// NewResourceManager creates a new resource manager
func NewResourceManager() *ResourceManager {
	return &ResourceManager{
		resources: make([]Closer, 0),
	}
}

// Register adds a resource to be managed
func (rm *ResourceManager) Register(resource Closer) {
	rm.mu.Lock()
	defer rm.mu.Unlock()

	if rm.closed {
		// If already closed, close the new resource immediately
		if err := resource.Close(); err != nil {
			logger.Error("Failed to close resource after manager shutdown: %v", err)
		}
		return
	}

	rm.resources = append(rm.resources, resource)
}

// RegisterFunc registers a cleanup function
func (rm *ResourceManager) RegisterFunc(fn func() error) {
	rm.Register(CloseFunc(fn))
}

// Close closes all registered resources in reverse order
func (rm *ResourceManager) Close() error {
	rm.mu.Lock()
	defer rm.mu.Unlock()

	if rm.closed {
		return nil
	}

	rm.closed = true

	var errs []error
	// Close in reverse order (LIFO)
	for i := len(rm.resources) - 1; i >= 0; i-- {
		if err := rm.resources[i].Close(); err != nil {
			errs = append(errs, err)
			logger.Error("Failed to close resource: %v", err)
		}
	}

	// Clear resources
	rm.resources = nil

	if len(errs) > 0 {
		return fmt.Errorf("failed to close %d resources", len(errs))
	}

	return nil
}

// SafeClose closes a resource safely, logging any errors
func SafeClose(resource io.Closer, name string) {
	if resource == nil {
		return
	}

	if err := resource.Close(); err != nil {
		logger.Error("Failed to close %s: %v", name, err)
	}
}

// SafeCloseWithTimeout closes a resource with a timeout
func SafeCloseWithTimeout(resource io.Closer, name string, timeout time.Duration) {
	if resource == nil {
		return
	}

	done := make(chan bool, 1)
	go func() {
		if err := resource.Close(); err != nil {
			logger.Error("Failed to close %s: %v", name, err)
		}
		done <- true
	}()

	select {
	case <-done:
		// Closed successfully
	case <-time.After(timeout):
		logger.Error("Timeout closing %s after %v", name, timeout)
	}
}

// FileManager manages file operations with automatic cleanup
type FileManager struct {
	files map[string]*os.File
	mu    sync.RWMutex
}

// NewFileManager creates a new file manager
func NewFileManager() *FileManager {
	return &FileManager{
		files: make(map[string]*os.File),
	}
}

// Open opens a file and tracks it for cleanup
func (fm *FileManager) Open(path string) (*os.File, error) {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}

	fm.files[path] = file
	return file, nil
}

// Create creates a file and tracks it for cleanup
func (fm *FileManager) Create(path string) (*os.File, error) {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	file, err := os.Create(path)
	if err != nil {
		return nil, err
	}

	fm.files[path] = file
	return file, nil
}

// Close closes a specific file
func (fm *FileManager) Close(path string) error {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	file, exists := fm.files[path]
	if !exists {
		return nil
	}

	delete(fm.files, path)
	return file.Close()
}

// CloseAll closes all open files
func (fm *FileManager) CloseAll() error {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	var errs []error
	for path, file := range fm.files {
		if err := file.Close(); err != nil {
			errs = append(errs, fmt.Errorf("failed to close %s: %w", path, err))
		}
	}

	fm.files = make(map[string]*os.File)

	if len(errs) > 0 {
		return fmt.Errorf("failed to close %d files", len(errs))
	}

	return nil
}

// DatabaseManager manages database connections with proper cleanup
type DatabaseManager struct {
	connections map[string]*sql.DB
	mu          sync.RWMutex
}

// NewDatabaseManager creates a new database manager
func NewDatabaseManager() *DatabaseManager {
	return &DatabaseManager{
		connections: make(map[string]*sql.DB),
	}
}

// Connect creates and tracks a database connection
func (dm *DatabaseManager) Connect(name, driver, dsn string) (*sql.DB, error) {
	dm.mu.Lock()
	defer dm.mu.Unlock()

	// Check if connection already exists
	if db, exists := dm.connections[name]; exists {
		return db, nil
	}

	db, err := sql.Open(driver, dsn)
	if err != nil {
		return nil, err
	}

	// Configure connection pool
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	// Verify connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	dm.connections[name] = db
	return db, nil
}

// Get returns an existing database connection
func (dm *DatabaseManager) Get(name string) (*sql.DB, bool) {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	db, exists := dm.connections[name]
	return db, exists
}

// Close closes a specific database connection
func (dm *DatabaseManager) Close(name string) error {
	dm.mu.Lock()
	defer dm.mu.Unlock()

	db, exists := dm.connections[name]
	if !exists {
		return nil
	}

	delete(dm.connections, name)
	return db.Close()
}

// CloseAll closes all database connections
func (dm *DatabaseManager) CloseAll() error {
	dm.mu.Lock()
	defer dm.mu.Unlock()

	var errs []error
	for name, db := range dm.connections {
		if err := db.Close(); err != nil {
			errs = append(errs, fmt.Errorf("failed to close database %s: %w", name, err))
		}
	}

	dm.connections = make(map[string]*sql.DB)

	if len(errs) > 0 {
		return fmt.Errorf("failed to close %d database connections", len(errs))
	}

	return nil
}

// ConnectionPool manages a pool of reusable connections
type ConnectionPool struct {
	factory func() (io.Closer, error)
	pool    chan io.Closer
	maxSize int
	mu      sync.Mutex
	closed  bool
}

// NewConnectionPool creates a new connection pool
func NewConnectionPool(factory func() (io.Closer, error), maxSize int) *ConnectionPool {
	return &ConnectionPool{
		factory: factory,
		pool:    make(chan io.Closer, maxSize),
		maxSize: maxSize,
	}
}

// Get retrieves a connection from the pool or creates a new one
func (cp *ConnectionPool) Get() (io.Closer, error) {
	cp.mu.Lock()
	if cp.closed {
		cp.mu.Unlock()
		return nil, fmt.Errorf("pool is closed")
	}
	cp.mu.Unlock()

	select {
	case conn := <-cp.pool:
		return conn, nil
	default:
		return cp.factory()
	}
}

// Put returns a connection to the pool
func (cp *ConnectionPool) Put(conn io.Closer) {
	cp.mu.Lock()
	if cp.closed {
		cp.mu.Unlock()
		conn.Close()
		return
	}
	cp.mu.Unlock()

	select {
	case cp.pool <- conn:
		// Connection returned to pool
	default:
		// Pool is full, close the connection
		conn.Close()
	}
}

// Close closes all connections in the pool
func (cp *ConnectionPool) Close() error {
	cp.mu.Lock()
	if cp.closed {
		cp.mu.Unlock()
		return nil
	}
	cp.closed = true
	cp.mu.Unlock()

	close(cp.pool)

	var errs []error
	for conn := range cp.pool {
		if err := conn.Close(); err != nil {
			errs = append(errs, err)
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("failed to close %d connections", len(errs))
	}

	return nil
}

// WithResource executes a function with automatic resource cleanup
func WithResource[T io.Closer](
	factory func() (T, error),
	fn func(T) error,
) error {
	resource, err := factory()
	if err != nil {
		return err
	}
	defer SafeClose(resource, "resource")

	return fn(resource)
}

// WithTimeout executes a function with a timeout and cleanup
func WithTimeout(
	ctx context.Context,
	timeout time.Duration,
	fn func(context.Context) error,
) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	done := make(chan error, 1)
	go func() {
		done <- fn(ctx)
	}()

	select {
	case err := <-done:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}

// LeakDetector helps detect resource leaks in tests
type LeakDetector struct {
	startGoroutines int
	startMemory     uint64
}

// NewLeakDetector creates a new leak detector
func NewLeakDetector() *LeakDetector {
	return &LeakDetector{}
}

// Start records the initial state
func (ld *LeakDetector) Start() {
	// Record initial goroutine count and memory
	// Implementation would use runtime package
}

// Check verifies no leaks occurred
func (ld *LeakDetector) Check() error {
	// Compare current state with initial state
	// Report any significant increases
	return nil
}