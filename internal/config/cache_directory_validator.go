package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// CacheDirectoryValidator validates cache directory configuration
type CacheDirectoryValidator struct {
	errors   []string
	warnings []string
}

// NewCacheDirectoryValidator creates a new cache directory validator
func NewCacheDirectoryValidator() *CacheDirectoryValidator {
	return &CacheDirectoryValidator{
		errors:   make([]string, 0),
		warnings: make([]string, 0),
	}
}

// ValidateCacheDirectories validates cache directory configuration
func (cdv *CacheDirectoryValidator) ValidateCacheDirectories(appDataDir, buildCacheDir string) error {
	cdv.errors = make([]string, 0)
	cdv.warnings = make([]string, 0)

	// Validate application data directory
	if err := cdv.validateAppDataDirectory(appDataDir); err != nil {
		cdv.errors = append(cdv.errors, err.Error())
	}

	// Validate build cache directory
	if err := cdv.validateBuildCacheDirectory(buildCacheDir); err != nil {
		cdv.errors = append(cdv.errors, err.Error())
	}

	// Check for directory confusion
	cdv.checkDirectoryConfusion(appDataDir, buildCacheDir)

	// Check for misplaced cache data
	cdv.checkMisplacedCacheData(appDataDir, buildCacheDir)

	// Return validation result
	if len(cdv.errors) > 0 {
		return fmt.Errorf("cache directory validation failed: %s", strings.Join(cdv.errors, "; "))
	}

	return nil
}

// validateAppDataDirectory validates the application data directory
func (cdv *CacheDirectoryValidator) validateAppDataDirectory(appDataDir string) error {
	if appDataDir == "" {
		return fmt.Errorf("application data directory cannot be empty")
	}

	// Check if directory exists
	if _, err := os.Stat(appDataDir); os.IsNotExist(err) {
		cdv.warnings = append(cdv.warnings, fmt.Sprintf("application data directory does not exist: %s", appDataDir))
		return nil
	}

	// Check if it's a directory
	if info, err := os.Stat(appDataDir); err == nil && !info.IsDir() {
		return fmt.Errorf("application data directory is not a directory: %s", appDataDir)
	}

	// Check permissions
	if err := cdv.checkDirectoryPermissions(appDataDir, "application data"); err != nil {
		cdv.warnings = append(cdv.warnings, err.Error())
	}

	return nil
}

// validateBuildCacheDirectory validates the build cache directory
func (cdv *CacheDirectoryValidator) validateBuildCacheDirectory(buildCacheDir string) error {
	if buildCacheDir == "" {
		return fmt.Errorf("build cache directory cannot be empty")
	}

	// Check if directory exists
	if _, err := os.Stat(buildCacheDir); os.IsNotExist(err) {
		cdv.warnings = append(cdv.warnings, fmt.Sprintf("build cache directory does not exist: %s", buildCacheDir))
		return nil
	}

	// Check if it's a directory
	if info, err := os.Stat(buildCacheDir); err == nil && !info.IsDir() {
		return fmt.Errorf("build cache directory is not a directory: %s", buildCacheDir)
	}

	// Check permissions
	if err := cdv.checkDirectoryPermissions(buildCacheDir, "build cache"); err != nil {
		cdv.warnings = append(cdv.warnings, err.Error())
	}

	return nil
}

// checkDirectoryConfusion checks for directory confusion
func (cdv *CacheDirectoryValidator) checkDirectoryConfusion(appDataDir, buildCacheDir string) {
	// Check if directories are the same
	if appDataDir == buildCacheDir {
		cdv.errors = append(cdv.errors, fmt.Sprintf("application data directory and build cache directory cannot be the same: %s", appDataDir))
		return
	}

	// Check if one is a subdirectory of the other
	if strings.HasPrefix(appDataDir, buildCacheDir) || strings.HasPrefix(buildCacheDir, appDataDir) {
		cdv.warnings = append(cdv.warnings, fmt.Sprintf("application data directory and build cache directory should not be nested: %s, %s", appDataDir, buildCacheDir))
	}

	// Check for common confusion patterns
	if strings.Contains(appDataDir, ".cache") && !strings.Contains(appDataDir, ".arxos") {
		cdv.warnings = append(cdv.warnings, fmt.Sprintf("application data directory contains '.cache' but not '.arxos': %s", appDataDir))
	}

	if strings.Contains(buildCacheDir, ".arxos") && !strings.Contains(buildCacheDir, ".cache") {
		cdv.warnings = append(cdv.warnings, fmt.Sprintf("build cache directory contains '.arxos' but not '.cache': %s", buildCacheDir))
	}
}

// checkMisplacedCacheData checks for misplaced cache data
func (cdv *CacheDirectoryValidator) checkMisplacedCacheData(appDataDir, buildCacheDir string) {
	// Check for application cache data in build cache directory
	appCachePaths := []string{
		filepath.Join(buildCacheDir, "ifc"),
		filepath.Join(buildCacheDir, "spatial"),
		filepath.Join(buildCacheDir, "api"),
		filepath.Join(buildCacheDir, "config"),
		filepath.Join(buildCacheDir, "query"),
	}

	for _, path := range appCachePaths {
		if _, err := os.Stat(path); err == nil {
			cdv.warnings = append(cdv.warnings, fmt.Sprintf("application cache data found in build cache directory: %s", path))
		}
	}

	// Check for build cache data in application data directory
	buildCachePaths := []string{
		filepath.Join(appDataDir, "go-build"),
		filepath.Join(appDataDir, "go-mod"),
		filepath.Join(appDataDir, "docker"),
		filepath.Join(appDataDir, "test-cache"),
	}

	for _, path := range buildCachePaths {
		if _, err := os.Stat(path); err == nil {
			cdv.warnings = append(cdv.warnings, fmt.Sprintf("build cache data found in application data directory: %s", path))
		}
	}
}

// checkDirectoryPermissions checks directory permissions
func (cdv *CacheDirectoryValidator) checkDirectoryPermissions(dir, dirType string) error {
	// Check read permission
	if _, err := os.ReadDir(dir); err != nil {
		return fmt.Errorf("cannot read %s directory: %s", dirType, dir)
	}

	// Check write permission by creating a test file
	testFile := filepath.Join(dir, ".permission_test")
	if err := os.WriteFile(testFile, []byte("test"), 0644); err != nil {
		return fmt.Errorf("cannot write to %s directory: %s", dirType, dir)
	}

	// Clean up test file
	os.Remove(testFile)

	return nil
}

// GetErrors returns validation errors
func (cdv *CacheDirectoryValidator) GetErrors() []string {
	return cdv.errors
}

// GetWarnings returns validation warnings
func (cdv *CacheDirectoryValidator) GetWarnings() []string {
	return cdv.warnings
}

// HasErrors returns true if there are validation errors
func (cdv *CacheDirectoryValidator) HasErrors() bool {
	return len(cdv.errors) > 0
}

// HasWarnings returns true if there are validation warnings
func (cdv *CacheDirectoryValidator) HasWarnings() bool {
	return len(cdv.warnings) > 0
}

// ValidateCacheStructure validates the unified cache structure
func (cdv *CacheDirectoryValidator) ValidateCacheStructure(cacheDir string) error {
	if cacheDir == "" {
		return fmt.Errorf("cache directory cannot be empty")
	}

	// Check if cache directory exists
	if _, err := os.Stat(cacheDir); os.IsNotExist(err) {
		cdv.warnings = append(cdv.warnings, fmt.Sprintf("cache directory does not exist: %s", cacheDir))
		return nil
	}

	// Check for proper cache structure
	expectedDirs := []string{
		filepath.Join(cacheDir, "l2"),
	}

	for _, expectedDir := range expectedDirs {
		if _, err := os.Stat(expectedDir); os.IsNotExist(err) {
			cdv.warnings = append(cdv.warnings, fmt.Sprintf("expected cache subdirectory does not exist: %s", expectedDir))
		}
	}

	// Check for old cache structure
	oldDirs := []string{
		filepath.Join(cacheDir, "ifc"),
		filepath.Join(cacheDir, "spatial"),
		filepath.Join(cacheDir, "api"),
		filepath.Join(cacheDir, "config"),
		filepath.Join(cacheDir, "query"),
	}

	for _, oldDir := range oldDirs {
		if _, err := os.Stat(oldDir); err == nil {
			cdv.warnings = append(cdv.warnings, fmt.Sprintf("old cache structure found (should be migrated): %s", oldDir))
		}
	}

	return nil
}

// ValidateCachePermissions validates cache directory permissions
func (cdv *CacheDirectoryValidator) ValidateCachePermissions(cacheDir string) error {
	if cacheDir == "" {
		return fmt.Errorf("cache directory cannot be empty")
	}

	// Check if cache directory exists
	if _, err := os.Stat(cacheDir); os.IsNotExist(err) {
		return nil // Directory doesn't exist, permissions will be set when created
	}

	// Check read permission
	if _, err := os.ReadDir(cacheDir); err != nil {
		return fmt.Errorf("cannot read cache directory: %s", cacheDir)
	}

	// Check write permission
	testFile := filepath.Join(cacheDir, ".permission_test")
	if err := os.WriteFile(testFile, []byte("test"), 0644); err != nil {
		return fmt.Errorf("cannot write to cache directory: %s", cacheDir)
	}

	// Clean up test file
	os.Remove(testFile)

	return nil
}

// ValidateCacheSize validates cache size limits
func (cdv *CacheDirectoryValidator) ValidateCacheSize(cacheDir string, maxSizeMB int64) error {
	if cacheDir == "" {
		return fmt.Errorf("cache directory cannot be empty")
	}

	// Check if cache directory exists
	if _, err := os.Stat(cacheDir); os.IsNotExist(err) {
		return nil // Directory doesn't exist, size will be checked when created
	}

	// Calculate directory size
	size, err := cdv.calculateDirectorySize(cacheDir)
	if err != nil {
		return fmt.Errorf("cannot calculate cache directory size: %w", err)
	}

	// Convert to MB
	sizeMB := size / (1024 * 1024)

	// Check if size exceeds limit
	if sizeMB > maxSizeMB {
		cdv.warnings = append(cdv.warnings, fmt.Sprintf("cache directory size (%d MB) exceeds limit (%d MB): %s", sizeMB, maxSizeMB, cacheDir))
	}

	return nil
}

// calculateDirectorySize calculates the total size of a directory
func (cdv *CacheDirectoryValidator) calculateDirectorySize(dir string) (int64, error) {
	var size int64

	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		size += info.Size()
		return nil
	})

	return size, err
}

// ValidateCacheIntegrity validates cache data integrity
func (cdv *CacheDirectoryValidator) ValidateCacheIntegrity(cacheDir string) error {
	if cacheDir == "" {
		return fmt.Errorf("cache directory cannot be empty")
	}

	// Check if cache directory exists
	if _, err := os.Stat(cacheDir); os.IsNotExist(err) {
		return nil // Directory doesn't exist, nothing to validate
	}

	// Check for corrupted cache files
	err := filepath.Walk(cacheDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip directories
		if info.IsDir() {
			return nil
		}

		// Check for cache files (JSON files)
		if filepath.Ext(path) == ".json" {
			// Try to read the file to check for corruption
			if _, err := os.ReadFile(path); err != nil {
				cdv.warnings = append(cdv.warnings, fmt.Sprintf("corrupted cache file: %s", path))
			}
		}

		return nil
	})

	return err
}

// GetValidationReport returns a comprehensive validation report
func (cdv *CacheDirectoryValidator) GetValidationReport() string {
	var report strings.Builder

	report.WriteString("Cache Directory Validation Report\n")
	report.WriteString("================================\n\n")

	if len(cdv.errors) > 0 {
		report.WriteString("ERRORS:\n")
		for i, err := range cdv.errors {
			report.WriteString(fmt.Sprintf("  %d. %s\n", i+1, err))
		}
		report.WriteString("\n")
	}

	if len(cdv.warnings) > 0 {
		report.WriteString("WARNINGS:\n")
		for i, warning := range cdv.warnings {
			report.WriteString(fmt.Sprintf("  %d. %s\n", i+1, warning))
		}
		report.WriteString("\n")
	}

	if len(cdv.errors) == 0 && len(cdv.warnings) == 0 {
		report.WriteString("No issues found. Cache directory structure is valid.\n")
	}

	return report.String()
}
