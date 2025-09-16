package storage

import (
	"os"
	"path/filepath"
	"time"
)

// DefaultCoordinatorConfig returns a default configuration for the storage coordinator
func DefaultCoordinatorConfig() *CoordinatorConfig {
	homeDir, _ := os.UserHomeDir()

	return &CoordinatorConfig{
		BIMFilesPath:   filepath.Join(homeDir, ".arxos", "buildings"),
		DatabasePath:   filepath.Join(homeDir, ".arxos", "arxos.db"),
		AutoSync:       true,
		SyncInterval:   30 * time.Second,
		ValidateOnSave: true,
	}
}

// NewCoordinatorConfig creates a coordinator config with custom paths
func NewCoordinatorConfig(bimPath, dbPath string) *CoordinatorConfig {
	config := DefaultCoordinatorConfig()

	if bimPath != "" {
		config.BIMFilesPath = bimPath
	}

	if dbPath != "" {
		config.DatabasePath = dbPath
	}

	return config
}
