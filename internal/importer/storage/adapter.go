package storage

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/models/building"
	"github.com/arx-os/arxos/pkg/models"
)

// DatabaseAdapter implements storage for building models
type DatabaseAdapter struct {
	db      database.DB
	spatial database.SpatialDB
	cache   *BuildingCache
}

// NewDatabaseAdapter creates a new storage adapter
func NewDatabaseAdapter(db database.DB) *DatabaseAdapter {
	adapter := &DatabaseAdapter{
		db:    db,
		cache: NewBuildingCache(),
	}

	// Check for spatial support
	if db.HasSpatialSupport() {
		spatial, err := db.GetSpatialDB()
		if err == nil {
			adapter.spatial = spatial
			logger.Debug("Spatial database support enabled")
		}
	}

	return adapter
}

// SaveToDatabase saves the building model to the database
func (d *DatabaseAdapter) SaveToDatabase(ctx context.Context, model *building.BuildingModel) error {
	logger.Debug("Saving building %s to database", model.ID)

	// Convert to database model
	floorPlan, err := d.toFloorPlan(model)
	if err != nil {
		return fmt.Errorf("failed to convert model: %w", err)
	}

	// Save to database
	if err := d.db.SaveFloorPlan(ctx, floorPlan); err != nil {
		return fmt.Errorf("failed to save floor plan: %w", err)
	}

	// Save spatial data if available
	if d.spatial != nil && model.Origin != nil {
		if err := d.saveSpatialData(ctx, model); err != nil {
			// Log but don't fail - spatial is enhancement
			logger.Warn("Failed to save spatial data: %v", err)
		}
	}

	// Update cache
	d.cache.Set(model.ID, model)

	logger.Info("Saved building %s with %d floors to database",
		model.ID, len(model.Floors))

	return nil
}

// SaveToBIM saves the building model to BIM format
func (d *DatabaseAdapter) SaveToBIM(ctx context.Context, model *building.BuildingModel) error {
	logger.Debug("Saving building %s to BIM format", model.ID)

	// Convert to BIM format
	bimText := d.toBIMFormat(model)

	// Determine output path
	outputPath := fmt.Sprintf("%s.bim.txt", model.ID)
	if model.Properties["output_path"] != nil {
		if path, ok := model.Properties["output_path"].(string); ok {
			outputPath = path
		}
	}

	// Write to file
	if err := os.WriteFile(outputPath, []byte(bimText), 0644); err != nil {
		return fmt.Errorf("failed to write BIM file: %w", err)
	}

	logger.Info("Saved building %s to %s", model.ID, outputPath)

	return nil
}

// SaveToFile saves the building model to a JSON file
func (d *DatabaseAdapter) SaveToFile(ctx context.Context, model *building.BuildingModel) error {
	logger.Debug("Saving building %s to JSON file", model.ID)

	// Determine output path
	outputPath := fmt.Sprintf("%s.json", model.ID)
	if model.Properties["output_path"] != nil {
		if path, ok := model.Properties["output_path"].(string); ok {
			outputPath = path
		}
	}

	// Create output file
	file, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Write JSON
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(model); err != nil {
		return fmt.Errorf("failed to encode JSON: %w", err)
	}

	logger.Info("Saved building %s to %s", model.ID, outputPath)

	return nil
}

// LoadFromDatabase loads a building model from the database
func (d *DatabaseAdapter) LoadFromDatabase(ctx context.Context, buildingID string) (*building.BuildingModel, error) {
	// Check cache first
	if cached := d.cache.Get(buildingID); cached != nil {
		logger.Debug("Loaded building %s from cache", buildingID)
		return cached, nil
	}

	// Load from database
	floorPlan, err := d.db.GetFloorPlan(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to load floor plan: %w", err)
	}

	// Convert to building model
	model := d.fromFloorPlan(floorPlan)

	// Load spatial data if available
	if d.spatial != nil {
		if err := d.loadSpatialData(ctx, model); err != nil {
			logger.Warn("Failed to load spatial data: %v", err)
		}
	}

	// Update cache
	d.cache.Set(buildingID, model)

	return model, nil
}

// toFloorPlan converts BuildingModel to database FloorPlan
func (d *DatabaseAdapter) toFloorPlan(model *building.BuildingModel) (*models.FloorPlan, error) {
	floorPlan := &models.FloorPlan{
		ID:          model.ID,
		UUID:        model.UUID,
		Name:        model.Name,
		Building:    model.Name, // Required field
		Description: model.Description,
		Level:       1, // Default to first floor
		Equipment:   []*models.Equipment{},
		Rooms:       []*models.Room{},
	}

	// Convert equipment
	for _, floor := range model.Floors {
		for _, eq := range floor.Equipment {
			equipment := &models.Equipment{
				ID:     eq.ID,
				Name:   eq.Name,
				Type:   eq.Type,
				Status: models.StatusOperational, // Default status
			}

			// Add metadata to properties
			// Note: models.Equipment doesn't have all these fields
			// Store them in a metadata map if needed

			floorPlan.Equipment = append(floorPlan.Equipment, equipment)
		}

		// Convert rooms
		for _, rm := range floor.Rooms {
			room := &models.Room{
				ID:   rm.ID,
				Name: rm.Name,
			}

			// Room.Equipment in models is []string (equipment IDs)
			room.Equipment = rm.Equipment

			floorPlan.Rooms = append(floorPlan.Rooms, room)
		}
	}

	return floorPlan, nil
}

// fromFloorPlan converts database FloorPlan to BuildingModel
func (d *DatabaseAdapter) fromFloorPlan(floorPlan *models.FloorPlan) *building.BuildingModel {
	model := &building.BuildingModel{
		ID:         floorPlan.ID,
		UUID:       floorPlan.UUID,
		Name:       floorPlan.Name,
		Properties: make(map[string]interface{}),
		Floors:     []building.Floor{},
	}

	// Create floor
	floor := building.Floor{
		ID:         fmt.Sprintf("floor_%d", floorPlan.Level),
		Number:     floorPlan.Level,
		Name:       fmt.Sprintf("Floor %d", floorPlan.Level),
		Rooms:      []building.Room{},
		Equipment:  []building.Equipment{},
		Properties: make(map[string]interface{}),
	}

	// Convert rooms
	for _, rm := range floorPlan.Rooms {
		room := building.Room{
			ID:         rm.ID,
			Name:       rm.Name,
			Type:       "general", // Default type since models.Room doesn't have Type
			FloorID:    floor.ID,
			Equipment:  []string{},
			Properties: make(map[string]interface{}),
		}

		// rm.Equipment is already []string, just copy it
		room.Equipment = rm.Equipment

		floor.Rooms = append(floor.Rooms, room)
	}

	// Convert equipment
	for _, eq := range floorPlan.Equipment {
		equipment := building.Equipment{
			ID:         eq.ID,
			Name:       eq.Name,
			Type:       eq.Type,
			Status:     string(eq.Status),
			FloorID:    floor.ID,
			Properties: make(map[string]interface{}),
		}

		floor.Equipment = append(floor.Equipment, equipment)
	}

	model.Floors = append(model.Floors, floor)

	return model
}

// toBIMFormat converts BuildingModel to BIM text format
func (d *DatabaseAdapter) toBIMFormat(model *building.BuildingModel) string {
	var sb strings.Builder

	// Header
	sb.WriteString("# ArxOS Building Information Model\n")
	sb.WriteString(fmt.Sprintf("# Generated: %s\n", time.Now().Format(time.RFC3339)))
	sb.WriteString(fmt.Sprintf("# Source: %s\n\n", model.Source))

	// Building info
	sb.WriteString(fmt.Sprintf("BUILDING: %s %s\n", model.ID, model.Name))
	if model.Address != "" {
		sb.WriteString(fmt.Sprintf("ADDRESS: %s\n", model.Address))
	}
	if model.Description != "" {
		sb.WriteString(fmt.Sprintf("DESCRIPTION: %s\n", model.Description))
	}
	sb.WriteString("\n")

	// Floors
	for _, floor := range model.Floors {
		sb.WriteString(fmt.Sprintf("FLOOR: %d %s\n", floor.Number, floor.Name))

		// Rooms
		for _, room := range floor.Rooms {
			sb.WriteString(fmt.Sprintf("  ROOM: %s [%s] %s\n", room.Number, room.Type, room.Name))

			// Room properties
			if room.Area > 0 {
				sb.WriteString(fmt.Sprintf("    AREA: %.2f sqm\n", room.Area))
			}
			if room.Position != nil {
				sb.WriteString(fmt.Sprintf("    POSITION: %.2f, %.2f, %.2f\n",
					room.Position.X, room.Position.Y, room.Position.Z))
			}
		}

		// Equipment
		for _, equipment := range floor.Equipment {
			sb.WriteString(fmt.Sprintf("  EQUIPMENT: %s [%s] %s\n",
				equipment.ID, equipment.Type, equipment.Name))

			// Equipment details
			if equipment.RoomID != "" {
				sb.WriteString(fmt.Sprintf("    ROOM: %s\n", equipment.RoomID))
			}
			if equipment.Position != nil {
				sb.WriteString(fmt.Sprintf("    POSITION: %.2f, %.2f, %.2f\n",
					equipment.Position.X, equipment.Position.Y, equipment.Position.Z))
			}
			if equipment.Manufacturer != "" {
				sb.WriteString(fmt.Sprintf("    MANUFACTURER: %s\n", equipment.Manufacturer))
			}
			if equipment.Model != "" {
				sb.WriteString(fmt.Sprintf("    MODEL: %s\n", equipment.Model))
			}
			sb.WriteString(fmt.Sprintf("    STATUS: %s\n", equipment.Status))
		}

		sb.WriteString("\n")
	}

	// Systems
	if len(model.Systems) > 0 {
		sb.WriteString("# Building Systems\n")
		for _, system := range model.Systems {
			sb.WriteString(fmt.Sprintf("SYSTEM: %s [%s] %s\n", system.ID, system.Type, system.Name))
			for _, eqID := range system.Equipment {
				sb.WriteString(fmt.Sprintf("  EQUIPMENT: %s\n", eqID))
			}
			sb.WriteString("\n")
		}
	}

	// Metadata
	sb.WriteString("# Metadata\n")
	sb.WriteString(fmt.Sprintf("CONFIDENCE: %v\n", model.Confidence))
	sb.WriteString(fmt.Sprintf("COVERAGE: %.1f%%\n", model.Coverage))
	if len(model.ValidationIssues) > 0 {
		sb.WriteString(fmt.Sprintf("ISSUES: %d\n", len(model.ValidationIssues)))
	}

	return sb.String()
}

// saveSpatialData saves spatial data to PostGIS
func (d *DatabaseAdapter) saveSpatialData(ctx context.Context, model *building.BuildingModel) error {
	// This would interact with the spatial database
	// Implementation depends on the spatial database interface
	logger.Debug("Saving spatial data for building %s", model.ID)

	// Example: Save building origin
	if model.Origin != nil {
		// d.spatial.SaveBuildingOrigin(ctx, model.ID, model.Origin)
	}

	// Example: Save bounding box
	if model.BoundingBox != nil {
		// d.spatial.SaveBoundingBox(ctx, model.ID, model.BoundingBox)
	}

	// Example: Save equipment positions
	for _, floor := range model.Floors {
		for _, equipment := range floor.Equipment {
			if equipment.Position != nil {
				// d.spatial.SaveEquipmentPosition(ctx, equipment.ID, equipment.Position)
			}
		}
	}

	return nil
}

// loadSpatialData loads spatial data from PostGIS
func (d *DatabaseAdapter) loadSpatialData(ctx context.Context, model *building.BuildingModel) error {
	// This would load spatial data from the database
	logger.Debug("Loading spatial data for building %s", model.ID)

	// Example implementation would load:
	// - Building origin and bounding box
	// - Equipment positions
	// - Room boundaries
	// - System connections

	return nil
}

// BuildingCache provides in-memory caching for building models
type BuildingCache struct {
	cache map[string]*building.BuildingModel
	// In production, add mutex for thread safety
	// mu sync.RWMutex
}

// NewBuildingCache creates a new cache
func NewBuildingCache() *BuildingCache {
	return &BuildingCache{
		cache: make(map[string]*building.BuildingModel),
	}
}

// Set stores a building in the cache
func (c *BuildingCache) Set(id string, model *building.BuildingModel) {
	c.cache[id] = model
}

// Get retrieves a building from the cache
func (c *BuildingCache) Get(id string) *building.BuildingModel {
	return c.cache[id]
}

// Clear removes all entries from the cache
func (c *BuildingCache) Clear() {
	c.cache = make(map[string]*building.BuildingModel)
}

// MigrationAdapter helps migrate from old to new system
type MigrationAdapter struct {
	oldConverter interface{} // Old converter interface
	newPipeline  interface{} // New pipeline interface
}

// NewMigrationAdapter creates an adapter for gradual migration
func NewMigrationAdapter() *MigrationAdapter {
	return &MigrationAdapter{}
}

// ImportWithFallback tries new system, falls back to old if needed
func (m *MigrationAdapter) ImportWithFallback(ctx context.Context, input interface{}, opts interface{}) error {
	// Try new system first
	// If it fails, fall back to old system
	// Log the fallback for monitoring
	return nil
}