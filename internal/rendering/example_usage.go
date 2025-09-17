package rendering

import (
	"context"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/storage"
)

// ExampleConsolidatedRendering demonstrates the new consolidated rendering system
func ExampleConsolidatedRendering() {
	logger.Info("=== ArxOS Consolidated Rendering Examples ===")

	// Initialize storage coordinator and renderer
	storageConfig := storage.DefaultCoordinatorConfig()
	coordinator, err := storage.NewStorageCoordinator(storageConfig)
	if err != nil {
		logger.Error("Failed to create storage coordinator: %v", err)
		return
	}
	defer coordinator.Close()

	renderer := NewConsolidatedRenderer()
	ctx := context.Background()
	buildingID := "ARXOS-NA-US-NY-NYC-0001"

	// Example 1: Building Manager - Schematic Overview
	logger.Info("\n=== Building Manager Use Case ===")
	buildingData, err := coordinator.GetBuilding(ctx, buildingID, storage.QueryOverview)
	if err != nil {
		logger.Error("Failed to get building overview: %v", err)
	} else if buildingData.BIMBuilding != nil {
		output, err := renderer.RenderBuildingOverview(buildingData.BIMBuilding)
		if err != nil {
			logger.Error("Failed to render overview: %v", err)
		} else {
			logger.Info("Building Overview:\n%s", output)
		}
	}

	// Example 2: Systems Engineer - Detailed System Tracing
	logger.Info("\n=== Systems Engineer Use Case ===")
	detailData, err := coordinator.GetBuilding(ctx, buildingID, storage.QueryDetail)
	if err != nil {
		logger.Error("Failed to get detail data: %v", err)
	} else if detailData.FloorPlan != nil {
		// Trace electrical system
		output, err := renderer.RenderSystemTrace(detailData.FloorPlan, "electrical")
		if err != nil {
			logger.Error("Failed to render system trace: %v", err)
		} else {
			logger.Info("Electrical System Trace:\n%s", output)
		}

		// Trace connections from specific equipment
		if len(detailData.FloorPlan.Equipment) > 0 {
			equipmentID := detailData.FloorPlan.Equipment[0].ID
			output, err := renderer.RenderConnectionTrace(detailData.FloorPlan, equipmentID)
			if err != nil {
				logger.Error("Failed to render connection trace: %v", err)
			} else {
				logger.Info("Connection Trace from %s:\n%s", equipmentID, output)
			}
		}
	}

	// Example 3: Field Technician - Spatial Coordinates
	logger.Info("\n=== Field Technician Use Case ===")
	spatialData, err := coordinator.GetBuilding(ctx, buildingID, storage.QuerySpatial)
	if err != nil {
		logger.Error("Failed to get spatial data: %v", err)
	} else if spatialData.SpatialAnchors != nil {
		output, err := renderer.RenderSpatialAnchors(spatialData.SpatialAnchors)
		if err != nil {
			logger.Error("Failed to render spatial anchors: %v", err)
		} else {
			logger.Info("Spatial Anchors:\n%s", output)
		}

		// Nearby equipment search
		output, err = renderer.RenderNearbyEquipment(spatialData.SpatialAnchors, 12.5, 8.3, 2.0)
		if err != nil {
			logger.Error("Failed to render nearby equipment: %v", err)
		} else {
			logger.Info("Equipment within 2m of (12.5, 8.3):\n%s", output)
		}
	}

	// Example 4: Live Monitoring
	logger.Info("\n=== Live Monitoring Example ===")
	outputChan := make(chan string, 10)

	// Create render request for live monitoring
	request := &RenderRequest{
		ViewLevel:  ViewOverview,
		BuildingID: buildingID,
		ShowAll:    true,
	}

	// Start live monitoring (would run in background)
	go renderer.RenderLiveMonitor(request, outputChan)

	// Simulate receiving a few updates
	for i := 0; i < 3; i++ {
		select {
		case output := <-outputChan:
			logger.Info("Live Update %d:\n%s", i+1, output[:200]+"...") // Truncate for example
		default:
			logger.Info("No live update available")
		}
	}

	close(outputChan)
	logger.Info("Consolidated rendering examples completed")
}

// ExampleMigrationFromOldSystem shows how to migrate from old rendering system
func ExampleMigrationFromOldSystem() {
	logger.Info("=== Migration from Old Rendering System ===")

	// Old way (complex, multiple renderers)
	logger.Info("Before: Multiple overlapping renderers")
	logger.Info("  - renderer.go (3D isometric)")
	logger.Info("  - universal_renderer.go (adaptive)")
	logger.Info("  - layered_renderer.go (composited)")
	logger.Info("  - Plus 10+ other rendering files")

	// New way (consolidated, purpose-built)
	logger.Info("After: Consolidated multi-level system")
	renderer := NewConsolidatedRenderer()

	// Show available view levels
	levels := renderer.GetSupportedViewLevels()
	for level, description := range levels {
		logger.Info("  %d. %s", int(level)+1, description)
	}

	// Usage help
	help := renderer.RenderUsageHelp()
	logger.Info("Usage Help:\n%s", help)

	logger.Info("Migration example completed")
}

// ExampleCustomConfiguration shows custom renderer configuration
func ExampleCustomConfiguration() {
	logger.Info("=== Custom Renderer Configuration ===")

	// Create custom configuration
	config := &RendererConfig{
		Width:             100,        // Wider terminal
		Height:            30,         // Taller display
		DefaultView:       ViewDetail, // Default to detail view
		ShowGrid:          true,       // Show coordinate grid
		ShowLegend:        true,       // Show symbol legend
		ShowStatusSummary: true,       // Show status counts
		ColorEnabled:      true,       // Enable colors
	}

	// Create renderer with custom config
	renderer := NewConsolidatedRendererWithConfig(config)

	// Configure for specific use case
	renderer.EnableColors(false)         // Disable colors for logging
	renderer.SetDefaultView(ViewSpatial) // Default to spatial view

	logger.Info("Custom renderer configured:")
	logger.Info("  Size: %dx%d", config.Width, config.Height)
	logger.Info("  Default view: %s", GetViewLevelName(config.DefaultView))
	logger.Info("  Colors: %v", config.ColorEnabled)

	logger.Info("Custom configuration example completed")
}
