package storage

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"github.com/joelpate/arxos/internal/common/logger"
)

// MigrateFromOldStorage migrates data from the old complex storage system to the new coordinator
func MigrateFromOldStorage(oldStoragePath string, coordinator *StorageCoordinator) error {
	logger.Info("Starting migration from old storage system to new coordinator")

	// Check if old storage path exists
	if _, err := os.Stat(oldStoragePath); os.IsNotExist(err) {
		logger.Info("No old storage found at %s - starting fresh", oldStoragePath)
		return nil
	}

	ctx := context.Background()

	// Walk through old storage structure
	return filepath.Walk(oldStoragePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip directories
		if info.IsDir() {
			return nil
		}

		// Handle different file types
		switch filepath.Ext(path) {
		case ".json":
			return migrateBuildingJSON(ctx, path, coordinator)
		case ".txt":
			if filepath.Base(path) == "building.bim.txt" {
				return migrateBIMFile(ctx, path, coordinator)
			}
		}

		return nil
	})
}

// migrateBuildingJSON migrates a building JSON file to the new coordinator
func migrateBuildingJSON(ctx context.Context, jsonPath string, coordinator *StorageCoordinator) error {
	logger.Debug("Migrating building JSON: %s", jsonPath)

	// TODO: Implement JSON to BuildingData conversion
	// This would read the old JSON format and convert it to the new BuildingData structure

	return nil
}

// migrateBIMFile migrates a .bim.txt file to the new coordinator
func migrateBIMFile(ctx context.Context, bimPath string, coordinator *StorageCoordinator) error {
	logger.Debug("Migrating BIM file: %s", bimPath)

	// Extract building ID from path
	buildingID := extractBuildingIDFromPath(bimPath)

	// Load the existing BIM file
	building, err := coordinator.textFiles.LoadBuilding(buildingID)
	if err != nil {
		return fmt.Errorf("failed to load BIM file during migration: %w", err)
	}

	// Create BuildingData structure
	buildingData := &BuildingData{
		BIMBuilding: building,
		DataSources: []DataSource{SourceBIM},
	}

	// Save using the new coordinator
	return coordinator.SaveBuilding(ctx, buildingData, SourceBIM)
}

// extractBuildingIDFromPath extracts building ID from file path
func extractBuildingIDFromPath(path string) string {
	// Extract building ID from path structure
	// This is a simplified version - would need to match your actual path structure
	return filepath.Base(filepath.Dir(path))
}

// CleanupOldStorage removes the old storage system files after successful migration
func CleanupOldStorage(oldStoragePath string) error {
	logger.Info("Cleaning up old storage system at %s", oldStoragePath)

	// Create backup before deletion
	backupPath := oldStoragePath + ".backup"
	if err := os.Rename(oldStoragePath, backupPath); err != nil {
		return fmt.Errorf("failed to create backup: %w", err)
	}

	logger.Info("Old storage backed up to %s", backupPath)
	return nil
}
