package commands

import (
	"testing"
	"time"
)

func TestWatchOptions(t *testing.T) {
	options := &WatchOptions{
		AutoRebuildIndex: true,
		DebounceDelay:    "2s",
		IgnorePatterns:   []string{".git", "*.tmp"},
		ShowStatus:       false,
		Quiet:            false,
	}

	if !options.AutoRebuildIndex {
		t.Error("Expected AutoRebuildIndex to be true")
	}

	if options.DebounceDelay != "2s" {
		t.Errorf("Expected DebounceDelay '2s', got '%s'", options.DebounceDelay)
	}

	if len(options.IgnorePatterns) != 2 {
		t.Errorf("Expected 2 ignore patterns, got %d", len(options.IgnorePatterns))
	}

	if options.ShowStatus {
		t.Error("Expected ShowStatus to be false")
	}

	if options.Quiet {
		t.Error("Expected Quiet to be false")
	}
}

func TestWatcherConfigDefaults(t *testing.T) {
	config := &WatcherConfig{
		Enabled:          true,
		WatchInterval:    5 * time.Second,
		DebounceDelay:    2 * time.Second,
		MaxConcurrent:    4,
		IgnorePatterns:   []string{".git", ".arxos/cache"},
		AutoRebuildIndex: true,
		NotifyOnChange:   true,
	}

	if !config.Enabled {
		t.Error("Expected Enabled to be true")
	}

	if config.WatchInterval != 5*time.Second {
		t.Errorf("Expected WatchInterval 5s, got %v", config.WatchInterval)
	}

	if config.DebounceDelay != 2*time.Second {
		t.Errorf("Expected DebounceDelay 2s, got %v", config.DebounceDelay)
	}

	if config.MaxConcurrent != 4 {
		t.Errorf("Expected MaxConcurrent 4, got %d", config.MaxConcurrent)
	}

	if len(config.IgnorePatterns) != 2 {
		t.Errorf("Expected 2 ignore patterns, got %d", len(config.IgnorePatterns))
	}

	if !config.AutoRebuildIndex {
		t.Error("Expected AutoRebuildIndex to be true")
	}

	if !config.NotifyOnChange {
		t.Error("Expected NotifyOnChange to be true")
	}
}

func TestFileEventStructure(t *testing.T) {
	event := FileEvent{
		Type:      "create",
		Path:      "/test/file.txt",
		Name:      "file.txt",
		IsDir:     false,
		Timestamp: time.Now().UTC(),
		User:      "test-user",
		Metadata: map[string]interface{}{
			"size": 1024,
		},
	}

	if event.Type != "create" {
		t.Errorf("Expected Type 'create', got '%s'", event.Type)
	}

	if event.Path != "/test/file.txt" {
		t.Errorf("Expected Path '/test/file.txt', got '%s'", event.Path)
	}

	if event.Name != "file.txt" {
		t.Errorf("Expected Name 'file.txt', got '%s'", event.Name)
	}

	if event.IsDir {
		t.Error("Expected IsDir to be false")
	}

	if event.User != "test-user" {
		t.Errorf("Expected User 'test-user', got '%s'", event.User)
	}

	if size, ok := event.Metadata["size"]; !ok || size != 1024 {
		t.Errorf("Expected metadata size 1024, got %v", size)
	}
}
