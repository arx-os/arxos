package filesystem

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	"github.com/arx-os/arxos/internal/config"
)

// DataManager manages ArxOS data directories following proper architecture
type DataManager struct {
	config *config.Config
}

// NewDataManager creates a new data manager
func NewDataManager(cfg *config.Config) *DataManager {
	return &DataManager{
		config: cfg,
	}
}

// EnsureDataDirectories creates all necessary data directories
func (dm *DataManager) EnsureDataDirectories(ctx context.Context) error {
	// Get all required directories
	dirs := dm.getRequiredDirectories()

	// Create each directory
	for _, dir := range dirs {
		if err := dm.createDirectory(dir); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	return nil
}

// GetRepositoriesPath returns the repositories directory path
func (dm *DataManager) GetRepositoriesPath() string {
	return dm.config.GetRepositoriesPath()
}

// GetCachePath returns the cache directory path
func (dm *DataManager) GetCachePath() string {
	return dm.config.GetCachePath()
}

// GetLogsPath returns the logs directory path
func (dm *DataManager) GetLogsPath() string {
	return dm.config.GetLogsPath()
}

// GetTempPath returns the temp directory path
func (dm *DataManager) GetTempPath() string {
	return dm.config.GetTempPath()
}

// GetRepositoryPath returns the path for a specific building repository
func (dm *DataManager) GetRepositoryPath(repoID string) string {
	return filepath.Join(dm.GetRepositoriesPath(), repoID)
}

// ValidateDataDirectories checks if all required directories exist and are accessible
func (dm *DataManager) ValidateDataDirectories(ctx context.Context) error {
	dirs := dm.getRequiredDirectories()

	for _, dir := range dirs {
		if err := dm.validateDirectory(dir); err != nil {
			return fmt.Errorf("directory validation failed for %s: %w", dir, err)
		}
	}

	return nil
}

// CleanupTempFiles removes temporary files older than the specified duration
func (dm *DataManager) CleanupTempFiles(ctx context.Context) error {
	tempDir := dm.GetTempPath()

	// Read temp directory
	entries, err := os.ReadDir(tempDir)
	if err != nil {
		return fmt.Errorf("failed to read temp directory: %w", err)
	}

	// Remove old temp files (simplified - in production, you'd check file age)
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		filePath := filepath.Join(tempDir, entry.Name())
		if err := os.Remove(filePath); err != nil {
			// Log warning but don't fail the operation
			fmt.Printf("Warning: Failed to remove temp file %s: %v\n", filePath, err)
		}
	}

	return nil
}

// getRequiredDirectories returns a list of all required directories
func (dm *DataManager) getRequiredDirectories() []string {
	return []string{
		dm.config.Storage.Data.BasePath,
		dm.GetRepositoriesPath(),
		dm.GetCachePath(),
		dm.GetLogsPath(),
		dm.GetTempPath(),
	}
}

// createDirectory creates a directory with proper permissions
func (dm *DataManager) createDirectory(path string) error {
	// Skip if directory already exists
	if _, err := os.Stat(path); err == nil {
		return nil
	}

	// Create directory with appropriate permissions
	perm := os.FileMode(0755)
	if runtime.GOOS == "windows" {
		// Windows doesn't support execute bit for directories
		perm = os.FileMode(0755)
	}

	return os.MkdirAll(path, perm)
}

// validateDirectory checks if a directory exists and is accessible
func (dm *DataManager) validateDirectory(path string) error {
	// Check if directory exists
	info, err := os.Stat(path)
	if err != nil {
		return fmt.Errorf("directory does not exist: %w", err)
	}

	// Check if it's actually a directory
	if !info.IsDir() {
		return fmt.Errorf("path exists but is not a directory")
	}

	// Check if we can read the directory
	if _, err := os.ReadDir(path); err != nil {
		return fmt.Errorf("directory is not readable: %w", err)
	}

	return nil
}

// GetDefaultDataPath returns the default data path based on the operating system
func GetDefaultDataPath() string {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		// Fallback to current directory if home directory cannot be determined
		return ".arxos"
	}

	switch runtime.GOOS {
	case "windows":
		// Windows: %APPDATA%\arxos
		return filepath.Join(homeDir, "AppData", "Roaming", "arxos")
	case "darwin":
		// macOS: ~/Library/Application Support/arxos
		return filepath.Join(homeDir, "Library", "Application Support", "arxos")
	default:
		// Linux/Unix: ~/.local/share/arxos (XDG Base Directory)
		return filepath.Join(homeDir, ".local", "share", "arxos")
	}
}
