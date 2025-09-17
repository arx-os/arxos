package storage

import (
	"context"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ExampleUsage demonstrates how to use the new StorageCoordinator
func ExampleUsage() {
	// Create configuration
	config := DefaultCoordinatorConfig()
	config.AutoSync = true
	config.SyncInterval = 30 * time.Second

	// Initialize coordinator
	coordinator, err := NewStorageCoordinator(config)
	if err != nil {
		logger.Error("Failed to create storage coordinator: %v", err)
		return
	}
	defer coordinator.Close()

	ctx := context.Background()

	// Example 1: Building Manager queries building overview (from .bim.txt)
	logger.Info("=== Building Manager Use Case ===")
	buildingData, err := coordinator.GetBuilding(ctx, "ARXOS-NA-US-NY-NYC-0001", QueryOverview)
	if err != nil {
		logger.Error("Failed to get building overview: %v", err)
	} else {
		logger.Info("Loaded building: %s (from BIM file)", buildingData.BIMBuilding.Name)
	}

	// Example 2: Field Technician queries precise coordinates (from PostGIS)
	logger.Info("=== Field Technician Use Case ===")
	spatialData, err := coordinator.GetBuilding(ctx, "ARXOS-NA-US-NY-NYC-0001", QuerySpatial)
	if err != nil {
		logger.Error("Failed to get spatial data: %v", err)
	} else {
		logger.Info("Loaded %d spatial anchors for AR", len(spatialData.SpatialAnchors))
	}

	// Example 3: Systems Engineer queries for detailed tracing (from cache)
	logger.Info("=== Systems Engineer Use Case ===")
	detailData, err := coordinator.GetBuilding(ctx, "ARXOS-NA-US-NY-NYC-0001", QueryDetail)
	if err != nil {
		logger.Error("Failed to get detail data: %v", err)
	} else {
		logger.Info("Loaded floor plan: %s (from cache)", detailData.FloorPlan.Name)
	}

	// Example 4: AR app saves precise equipment position
	logger.Info("=== AR Edit Use Case ===")
	// This would typically come from the mobile AR app
	// coordinator.SaveBuilding(ctx, arEditedData, SourceAR)

	// Example 5: Terminal user edits building data
	logger.Info("=== Terminal Edit Use Case ===")
	// This would typically come from terminal commands
	// coordinator.SaveBuilding(ctx, terminalEditedData, SourceTerminal)

	logger.Info("Storage coordinator examples completed")
}

// ExampleMigration demonstrates migrating from old storage system
func ExampleMigration() {
	// Create new coordinator
	config := DefaultCoordinatorConfig()
	coordinator, err := NewStorageCoordinator(config)
	if err != nil {
		logger.Error("Failed to create coordinator: %v", err)
		return
	}
	defer coordinator.Close()

	// Migrate from old storage
	oldStoragePath := "/old/arxos/storage/path"
	if err := MigrateFromOldStorage(oldStoragePath, coordinator); err != nil {
		logger.Error("Migration failed: %v", err)
		return
	}

	// Clean up old storage after successful migration
	if err := CleanupOldStorage(oldStoragePath); err != nil {
		logger.Warn("Failed to cleanup old storage: %v", err)
	}

	logger.Info("Migration completed successfully")
}

// ExampleCoordinateTranslation demonstrates the coordinate system bridging
func ExampleCoordinateTranslation() {
	config := DefaultCoordinatorConfig()
	coordinator, err := NewStorageCoordinator(config)
	if err != nil {
		logger.Error("Failed to create coordinator: %v", err)
		return
	}
	defer coordinator.Close()

	// Example: AR user moves outlet by 15cm (precision that doesn't fit in grid)
	logger.Info("=== Coordinate Translation Example ===")

	// AR coordinates (millimeter precision)
	arPosition := Point3D{X: 12.547, Y: 8.291, Z: 1.127}
	logger.Info("AR position: (%.3f, %.3f, %.3f) meters", arPosition.X, arPosition.Y, arPosition.Z)

	// Convert to grid coordinates for .bim.txt
	gridX := int(arPosition.X / coordinator.translator.GridScale)
	gridY := int(arPosition.Y / coordinator.translator.GridScale)
	logger.Info("Grid position: (%d, %d) - for .bim.txt storage", gridX, gridY)

	// The coordinator would determine if this is a "significant change"
	// (different grid position or different room) and update .bim.txt accordingly

	logger.Info("Coordinate translation example completed")
}
