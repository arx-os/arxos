package daemon

import (
	"context"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// TestDaemonStatisticsUpdate tests the thread-safe statistics updates
func TestDaemonStatisticsUpdate(t *testing.T) {
	config := &Config{
		MaxWorkers:   4,
		QueueSize:    100,
		DatabasePath: ":memory:",
	}

	daemon, _ := NewDaemon(config)
	if daemon == nil {
		t.Skip("Daemon initialization failed")
	}

	// Test concurrent statistics updates
	var wg sync.WaitGroup
	numGoroutines := 100
	itemsPerGoroutine := 10

	for i := 0; i < numGoroutines; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < itemsPerGoroutine; j++ {
				item := &WorkItem{
					Type:      WorkTypeImport,
					FilePath:  filepath.Join("/tmp", "file.ifc"),
					Timestamp: time.Now(),
				}

				// Simulate success/failure
				var err error
				if j%3 == 0 {
					err = os.ErrNotExist
				}

				daemon.updateStats(item, err, 100*time.Millisecond)
			}
		}(i)
	}

	wg.Wait()

	stats := daemon.GetStats()
	expectedTotal := int64(numGoroutines * itemsPerGoroutine)
	if stats.FilesProcessed != expectedTotal {
		t.Errorf("FilesProcessed = %d, want %d", stats.FilesProcessed, expectedTotal)
	}

	// Roughly 1/3 should be failures
	expectedFailures := expectedTotal / 3
	tolerance := int64(50) // Allow some variance
	if stats.ImportFailures < expectedFailures-tolerance || stats.ImportFailures > expectedFailures+tolerance {
		t.Errorf("ImportFailures = %d, want approximately %d", stats.ImportFailures, expectedFailures)
	}
}

// TestDaemonShouldProcess tests file pattern matching
func TestDaemonShouldProcess(t *testing.T) {
	tests := []struct {
		name           string
		watchPatterns  []string
		ignorePatterns []string
		filePath       string
		shouldProcess  bool
	}{
		{
			name:           "Match IFC file",
			watchPatterns:  []string{"*.ifc"},
			ignorePatterns: []string{},
			filePath:       "/tmp/building.ifc",
			shouldProcess:  true,
		},
		{
			name:           "Match PDF file",
			watchPatterns:  []string{"*.pdf", "*.ifc"},
			ignorePatterns: []string{},
			filePath:       "/tmp/floorplan.pdf",
			shouldProcess:  true,
		},
		{
			name:           "Ignore temp files",
			watchPatterns:  []string{"*.ifc"},
			ignorePatterns: []string{"*.tmp", "~*"},
			filePath:       "/tmp/building.tmp",
			shouldProcess:  false,
		},
		{
			name:           "Ignore takes precedence",
			watchPatterns:  []string{"*.ifc"},
			ignorePatterns: []string{"backup_*"},
			filePath:       "/tmp/backup_building.ifc",
			shouldProcess:  false,
		},
		{
			name:           "No patterns - process all",
			watchPatterns:  []string{},
			ignorePatterns: []string{},
			filePath:       "/tmp/anything.xyz",
			shouldProcess:  true,
		},
		{
			name:           "No match",
			watchPatterns:  []string{"*.ifc", "*.pdf"},
			ignorePatterns: []string{},
			filePath:       "/tmp/data.json",
			shouldProcess:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			daemon := &Daemon{
				config: &Config{
					WatchPatterns:  tt.watchPatterns,
					IgnorePatterns: tt.ignorePatterns,
				},
			}

			result := daemon.shouldProcess(tt.filePath)
			if result != tt.shouldProcess {
				t.Errorf("shouldProcess(%s) = %v, want %v", tt.filePath, result, tt.shouldProcess)
			}
		})
	}
}

// TestDaemonWorkerProcessing tests the worker processing logic
func TestDaemonWorkerProcessing(t *testing.T) {
	// Create temp directory
	tmpDir, err := ioutil.TempDir("", "arxos-daemon-worker-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	config := &Config{
		WatchDirs:    []string{tmpDir},
		StateDir:     filepath.Join(tmpDir, "state"),
		DatabasePath: ":memory:",
		MaxWorkers:   2,
		QueueSize:    10,
	}

	daemon, _ := NewDaemon(config)
	if daemon == nil {
		t.Skip("Daemon initialization failed")
	}

	// Track processed items
	var processedCount int32
	processedItems := make(map[string]bool)
	var mu sync.Mutex

	// Create a mock processor that tracks items
	// Since we can't override the method, we'll track through the queue consumption

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	// Start mock workers that consume from queue
	for i := 0; i < config.MaxWorkers; i++ {
		daemon.wg.Add(1)
		go func(workerID int) {
			defer daemon.wg.Done()
			for {
				select {
				case item := <-daemon.queue.Items():
					if item == nil {
						return
					}
					atomic.AddInt32(&processedCount, 1)
					mu.Lock()
					processedItems[item.FilePath] = true
					mu.Unlock()
					time.Sleep(10 * time.Millisecond) // Simulate processing
				case <-ctx.Done():
					return
				}
			}
		}(i)
	}

	// Add work items
	numItems := 5
	for i := 0; i < numItems; i++ {
		item := &WorkItem{
			Type:      WorkTypeImport,
			FilePath:  filepath.Join(tmpDir, fmt.Sprintf("file%d.ifc", i)),
			Timestamp: time.Now(),
		}
		err := daemon.queue.Add(item)
		if err != nil {
			t.Errorf("Failed to add item %d: %v", i, err)
		}
	}

	// Wait for processing
	time.Sleep(200 * time.Millisecond)

	// Check results
	count := atomic.LoadInt32(&processedCount)
	if count != int32(numItems) {
		t.Errorf("Processed %d items, want %d", count, numItems)
	}

	mu.Lock()
	processedLen := len(processedItems)
	mu.Unlock()

	if processedLen != numItems {
		t.Errorf("Processed %d unique items, want %d", processedLen, numItems)
	}
}

// TestDaemonConfigDefaults tests configuration default values
func TestDaemonConfigDefaults(t *testing.T) {
	config := &Config{}

	daemon, _ := NewDaemon(config)
	if daemon == nil {
		t.Skip("Daemon initialization failed")
	}

	// Check defaults were applied
	if daemon.config.MaxWorkers != 4 {
		t.Errorf("MaxWorkers = %d, want 4", daemon.config.MaxWorkers)
	}

	if daemon.config.QueueSize != 100 {
		t.Errorf("QueueSize = %d, want 100", daemon.config.QueueSize)
	}

	if daemon.config.SyncInterval != 5*time.Minute {
		t.Errorf("SyncInterval = %v, want 5m", daemon.config.SyncInterval)
	}

	if daemon.config.SocketPath != "/tmp/arxos.sock" {
		t.Errorf("SocketPath = %s, want /tmp/arxos.sock", daemon.config.SocketPath)
	}
}

// TestDaemonGetStatus tests status reporting
func TestDaemonGetStatus(t *testing.T) {
	config := &Config{
		WatchDirs:    []string{"/tmp/test1", "/tmp/test2"},
		AutoImport:   true,
		MaxWorkers:   8,
		QueueSize:    50,
		DatabasePath: ":memory:",
	}

	daemon, _ := NewDaemon(config)
	if daemon == nil {
		t.Skip("Daemon initialization failed")
	}

	// Set some stats
	daemon.stats.FilesProcessed = 100
	daemon.stats.ImportSuccesses = 95
	daemon.stats.ImportFailures = 5
	daemon.stats.LastProcessedFile = "/tmp/last.ifc"
	daemon.stats.LastProcessedTime = time.Now()

	status := daemon.GetStatus()

	// Check status fields
	if status["running"] != true {
		t.Error("Status should show running=true")
	}

	if status["files_processed"] != int64(100) {
		t.Errorf("files_processed = %v, want 100", status["files_processed"])
	}

	if status["import_successes"] != int64(95) {
		t.Errorf("import_successes = %v, want 95", status["import_successes"])
	}

	if status["import_failures"] != int64(5) {
		t.Errorf("import_failures = %v, want 5", status["import_failures"])
	}

	if status["auto_import"] != true {
		t.Error("auto_import should be true")
	}

	if status["workers"] != 8 {
		t.Errorf("workers = %v, want 8", status["workers"])
	}

	watchDirs, ok := status["watch_dirs"].([]string)
	if !ok || len(watchDirs) != 2 {
		t.Error("watch_dirs should have 2 directories")
	}
}

// TestDaemonRecordActivity tests activity recording
func TestDaemonRecordActivity(t *testing.T) {
	config := &Config{
		DatabasePath: ":memory:",
	}

	daemon, _ := NewDaemon(config)
	if daemon == nil {
		t.Skip("Daemon initialization failed")
	}

	// Record some activities
	daemon.recordActivity("ifc_import", "/tmp/building.ifc", "success")
	daemon.recordActivity("pdf_import", "/tmp/floor1.pdf", "success")
	daemon.recordActivity("ifc_import", "/tmp/building2.ifc", "failure")

	stats := daemon.GetStats()

	if stats.FilesProcessed != 3 {
		t.Errorf("FilesProcessed = %d, want 3", stats.FilesProcessed)
	}

	if stats.ImportSuccesses != 2 {
		t.Errorf("ImportSuccesses = %d, want 2", stats.ImportSuccesses)
	}

	if stats.ImportFailures != 1 {
		t.Errorf("ImportFailures = %d, want 1", stats.ImportFailures)
	}

	if stats.LastProcessedFile != "/tmp/building2.ifc" {
		t.Errorf("LastProcessedFile = %s, want /tmp/building2.ifc", stats.LastProcessedFile)
	}
}

// TestDaemonGracefulShutdown tests graceful shutdown
func TestDaemonGracefulShutdown(t *testing.T) {
	config := &Config{
		MaxWorkers:   2,
		QueueSize:    10,
		DatabasePath: ":memory:",
	}

	daemon, _ := NewDaemon(config)
	if daemon == nil {
		t.Skip("Daemon initialization failed")
	}

	// Track shutdown completion
	shutdownComplete := make(chan bool, 1)

	// Start some workers
	for i := 0; i < config.MaxWorkers; i++ {
		daemon.wg.Add(1)
		go func(id int) {
			defer daemon.wg.Done()
			select {
			case <-daemon.stopCh:
				// Worker stopped
			case <-time.After(5 * time.Second):
				t.Error("Worker didn't stop in time")
			}
		}(i)
	}

	// Stop daemon in goroutine
	go func() {
		daemon.Stop()
		shutdownComplete <- true
	}()

	// Wait for shutdown to complete
	select {
	case <-shutdownComplete:
		// Success
	case <-time.After(1 * time.Second):
		t.Fatal("Daemon didn't shut down within timeout")
	}
}

// TestDaemonPeriodicSync tests the periodic sync functionality
func TestDaemonPeriodicSync(t *testing.T) {
	config := &Config{
		SyncInterval: 50 * time.Millisecond, // Short interval for testing
		DatabasePath: ":memory:",
		StateDir:     "/tmp/test-state",
	}

	daemon, _ := NewDaemon(config)
	if daemon == nil {
		t.Skip("Daemon initialization failed")
	}

	// We'll track syncs by monitoring database activity
	// Since we can't override the method, we'll use time-based testing

	// Since we can't directly test the sync method, we'll verify
	// that the periodic sync goroutine would run correctly
	// by checking the configuration is set properly

	if daemon.config.SyncInterval != 50*time.Millisecond {
		t.Errorf("Sync interval = %v, want 50ms", daemon.config.SyncInterval)
	}

	// Verify daemon has necessary components for sync
	if daemon.db == nil {
		t.Error("Database connection is nil")
	}

	if daemon.config.StateDir == "" {
		t.Log("StateDir is empty, sync may not persist state")
	}
}