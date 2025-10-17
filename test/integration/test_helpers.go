package integration

import (
	"context"
	"fmt"
	"io"
	"os"
	"testing"
	"time"
)

// Note: Main setupTestContainer is now in container.go
// This file contains additional test helper utilities

// LoadTestIFCFile loads a test IFC file from test_data/inputs
func LoadTestIFCFile(t *testing.T, filename string) []byte {
	t.Helper()

	path := fmt.Sprintf("../../test_data/inputs/%s", filename)
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			t.Skipf("Test IFC file not found: %s (place sample files in test_data/inputs/)", filename)
		}
		t.Fatalf("Failed to read test IFC file: %v", err)
	}

	t.Logf("Loaded test IFC file: %s (%d bytes)", filename, len(data))
	return data
}

// LoadTestBASFile loads a test BAS CSV file from test_data/bas
func LoadTestBASFile(t *testing.T, filename string) []byte {
	t.Helper()

	path := fmt.Sprintf("../../test_data/bas/%s", filename)
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			t.Skipf("Test BAS file not found: %s (place sample files in test_data/bas/)", filename)
		}
		t.Fatalf("Failed to read test BAS file: %v", err)
	}

	t.Logf("Loaded test BAS file: %s (%d bytes)", filename, len(data))
	return data
}

// CaptureOutput captures stdout/stderr for testing CLI output
func CaptureOutput(t *testing.T, fn func()) string {
	t.Helper()

	// Create a pipe to capture output
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("Failed to create pipe: %v", err)
	}

	// Save original stdout
	oldStdout := os.Stdout
	oldStderr := os.Stderr

	// Redirect stdout/stderr to pipe
	os.Stdout = w
	os.Stderr = w

	// Restore on cleanup
	defer func() {
		os.Stdout = oldStdout
		os.Stderr = oldStderr
	}()

	// Channel to receive output
	outputChan := make(chan string)

	// Read from pipe in goroutine
	go func() {
		output, _ := io.ReadAll(r)
		outputChan <- string(output)
	}()

	// Run function
	fn()

	// Close write end and wait for output
	w.Close()
	output := <-outputChan

	return output
}

// AssertNoError is a helper that fails the test immediately if err != nil
func AssertNoError(t *testing.T, err error, msgAndArgs ...interface{}) {
	t.Helper()
	if err != nil {
		if len(msgAndArgs) > 0 {
			t.Fatalf("Unexpected error: %v - %v", err, msgAndArgs)
		} else {
			t.Fatalf("Unexpected error: %v", err)
		}
	}
}

// CreateTestContext creates a context for testing with timeout
func CreateTestContext(t *testing.T) context.Context {
	t.Helper()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	t.Cleanup(cancel)

	return ctx
}
