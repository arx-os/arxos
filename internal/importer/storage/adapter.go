package storage

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/core/building"
	"github.com/arx-os/arxos/internal/core/equipment"
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
	buildingID := "unknown"
	if model.Building != nil {
		buildingID = model.Building.ArxosID
	}
	logger.Debug("Saving building %s to database", buildingID)

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
	if d.spatial != nil && model.Building != nil && model.Building.Origin.Latitude != 0 {
		if err := d.saveSpatialData(ctx, model); err != nil {
			// Log but don't fail - spatial is enhancement
			logger.Warn("Failed to save spatial data: %v", err)
		}
	}

	// Update cache
	d.cache.Set(buildingID, model)

	logger.Info("Saved building %s with %d floors to database",
		buildingID, len(model.Floors))

	return nil
}

// SaveToBIM saves the building model to BIM format
func (d *DatabaseAdapter) SaveToBIM(ctx context.Context, model *building.BuildingModel) error {
	buildingID := "unknown"
	if model.Building != nil {
		buildingID = model.Building.ArxosID
	}
	logger.Debug("Saving building %s to BIM format", buildingID)

	// Convert to BIM format
	bimText := d.toBIMFormat(model)

	// Determine output path
	outputPath := fmt.Sprintf("%s.bim.txt", buildingID)
	if model.Building != nil && model.Building.Metadata != nil {
		if path, ok := model.Building.Metadata["output_path"].(string); ok {
			outputPath = path
		}
	}

	// Write to file
	if err := os.WriteFile(outputPath, []byte(bimText), 0644); err != nil {
		return fmt.Errorf("failed to write BIM file: %w", err)
	}

	logger.Info("Saved building %s to %s", buildingID, outputPath)

	return nil
}

// SaveToFile saves the building model to a JSON file
func (d *DatabaseAdapter) SaveToFile(ctx context.Context, model *building.BuildingModel) error {
	buildingID := "unknown"
	if model.Building != nil {
		buildingID = model.Building.ArxosID
	}
	logger.Debug("Saving building %s to JSON file", buildingID)

	// Determine output path
	outputPath := fmt.Sprintf("%s.json", buildingID)
	if model.Building != nil && model.Building.Metadata != nil {
		if path, ok := model.Building.Metadata["output_path"].(string); ok {
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

	logger.Info("Saved building %s to %s", buildingID, outputPath)

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
	// Use first floor or create a default
	floorLevel := 1
	floorName := "Floor 1"
	if len(model.Floors) > 0 {
		floorLevel = model.Floors[0].Level
		floorName = model.Floors[0].Name
	}

	buildingName := "Unknown"
	buildingID := "unknown"
	if model.Building != nil {
		buildingName = model.Building.Name
		buildingID = model.Building.ArxosID
	}

	floorPlan := &models.FloorPlan{
		ID:          buildingID,
		UUID:        buildingID,  // Use ArxosID as UUID
		Name:        floorName,
		Building:    buildingName,
		Description: "",
		Level:       floorLevel,
		Equipment:   []*models.Equipment{},
		Rooms:       []*models.Room{},
	}

	// Convert equipment from model.Equipment
	for _, eq := range model.Equipment {
		equipment := &models.Equipment{
			ID:     eq.ID.String(),
			Name:   eq.Name,
			Type:   eq.Type,
			Status: eq.Status,
		}
		floorPlan.Equipment = append(floorPlan.Equipment, equipment)
	}

	// Convert rooms from model.Rooms
	for _, rm := range model.Rooms {
		room := &models.Room{
			ID:   rm.ID.String(),
			Name: rm.Name,
		}

		// Build equipment list for this room from metadata
		equipmentInRoom := []string{}
		for _, eq := range model.Equipment {
			if eq.Metadata != nil {
				if roomID, ok := eq.Metadata["room_id"].(string); ok && roomID == rm.ID.String() {
					equipmentInRoom = append(equipmentInRoom, eq.ID.String())
				}
			}
		}
		room.Equipment = equipmentInRoom

		floorPlan.Rooms = append(floorPlan.Rooms, room)
	}

	return floorPlan, nil
}

// fromFloorPlan converts database FloorPlan to BuildingModel
func (d *DatabaseAdapter) fromFloorPlan(floorPlan *models.FloorPlan) *building.BuildingModel {
	// Create building from floor plan
	bldg := building.NewBuilding(floorPlan.ID, floorPlan.Building)

	model := building.NewBuildingModel(bldg)

	// Create floor
	floor := building.Floor{
		ID:          uuid.New(),
		BuildingID:  bldg.ID,
		Level:       floorPlan.Level,
		Name:        fmt.Sprintf("Floor %d", floorPlan.Level),
		Metadata:    make(map[string]interface{}),
	}

	// Convert rooms
	for _, rm := range floorPlan.Rooms {
		roomID, _ := uuid.Parse(rm.ID)
		if roomID == uuid.Nil {
			roomID = uuid.New()
		}
		room := building.Room{
			ID:         roomID,
			BuildingID: bldg.ID,
			FloorID:    floor.ID,
			Name:       rm.Name,
			Type:       "general", // Default type since models.Room doesn't have Type
			Metadata:   make(map[string]interface{}),
		}

		model.AddRoom(room)
	}

	// Convert equipment
	for _, eq := range floorPlan.Equipment {
		eqID, _ := uuid.Parse(eq.ID)
		if eqID == uuid.Nil {
			eqID = uuid.New()
		}
		equip := &equipment.Equipment{
			ID:         eqID,
			BuildingID: bldg.ID,
			Name:       eq.Name,
			Type:       eq.Type,
			Status:     string(eq.Status),
			Metadata:   make(map[string]interface{}),
		}

		model.AddEquipment(equip)
	}

	model.AddFloor(floor)

	return model
}

// toBIMFormat converts BuildingModel to BIM text format
func (d *DatabaseAdapter) toBIMFormat(model *building.BuildingModel) string {
	var sb strings.Builder

	// Header
	sb.WriteString("# ArxOS Building Information Model\n")
	sb.WriteString(fmt.Sprintf("# Generated: %s\n", time.Now().Format(time.RFC3339)))

	// Get source from import metadata if available
	source := "ArxOS Import Pipeline"
	if model.ImportMetadata.SourceFile != "" {
		source = model.ImportMetadata.SourceFile
	}
	sb.WriteString(fmt.Sprintf("# Source: %s\n\n", source))

	// Building info
	buildingID := "unknown"
	buildingName := "Unknown Building"
	if model.Building != nil {
		buildingID = model.Building.ArxosID
		buildingName = model.Building.Name
		sb.WriteString(fmt.Sprintf("BUILDING: %s %s\n", buildingID, buildingName))
		if model.Building.Address != "" {
			sb.WriteString(fmt.Sprintf("ADDRESS: %s\n", model.Building.Address))
		}
	}
	sb.WriteString("\n")

	// Floors
	for _, floor := range model.Floors {
		sb.WriteString(fmt.Sprintf("FLOOR: %d %s\n", floor.Level, floor.Name))

		// Get rooms for this floor
		roomsOnFloor := model.GetRoomsByFloor(floor.ID)
		for _, room := range roomsOnFloor {
			sb.WriteString(fmt.Sprintf("  ROOM: %s [%s] %s\n", room.ID.String(), room.Type, room.Name))

			// Room properties
			if room.Area > 0 {
				sb.WriteString(fmt.Sprintf("    AREA: %.2f sqm\n", room.Area))
			}
		}

		sb.WriteString("\n")
	}

	// Equipment section
	if len(model.Equipment) > 0 {
		sb.WriteString("# Equipment\n")
		for _, eq := range model.Equipment {
			sb.WriteString(fmt.Sprintf("EQUIPMENT: %s [%s] %s\n",
				eq.ID.String(), eq.Type, eq.Name))

			// Equipment details
			if eq.Metadata != nil {
				if roomID, ok := eq.Metadata["room_id"].(string); ok {
					sb.WriteString(fmt.Sprintf("  ROOM: %s\n", roomID))
				}
				if manufacturer, ok := eq.Metadata["manufacturer"].(string); ok {
					sb.WriteString(fmt.Sprintf("  MANUFACTURER: %s\n", manufacturer))
				}
				if modelNum, ok := eq.Metadata["model"].(string); ok {
					sb.WriteString(fmt.Sprintf("  MODEL: %s\n", modelNum))
				}
			}
			if eq.Position != nil {
				sb.WriteString(fmt.Sprintf("  POSITION: %.2f, %.2f, %.2f\n",
					eq.Position.X, eq.Position.Y, eq.Position.Z))
			}
			sb.WriteString(fmt.Sprintf("  STATUS: %s\n", eq.Status))
		}
		sb.WriteString("\n")
	}

	// Metadata
	sb.WriteString("# Metadata\n")
	if model.Building != nil && model.Building.Metadata != nil {
		if confidence, ok := model.Building.Metadata["confidence"].(string); ok {
			sb.WriteString(fmt.Sprintf("CONFIDENCE: %s\n", confidence))
		}
		if coverage, ok := model.Building.Metadata["equipment_coverage"].(float64); ok {
			sb.WriteString(fmt.Sprintf("COVERAGE: %.1f%%\n", coverage))
		}
	}
	if len(model.ValidationIssues) > 0 {
		sb.WriteString(fmt.Sprintf("ISSUES: %d\n", len(model.ValidationIssues)))
	}

	return sb.String()
}

// saveSpatialData saves spatial data to PostGIS
func (d *DatabaseAdapter) saveSpatialData(ctx context.Context, model *building.BuildingModel) error {
	// This would interact with the spatial database
	// Implementation depends on the spatial database interface
	buildingID := "unknown"
	if model.Building != nil {
		buildingID = model.Building.ArxosID
	}
	logger.Debug("Saving spatial data for building %s", buildingID)

	// Example: Save building origin
	if model.Building != nil && model.Building.Origin.Latitude != 0 {
		// d.spatial.SaveBuildingOrigin(ctx, buildingID, model.Building.Origin)
	}

	// Example: Save equipment positions
	for _, eq := range model.Equipment {
		if eq.Position != nil {
			// d.spatial.SaveEquipmentPosition(ctx, eq.ID.String(), eq.Position)
		}
	}

	return nil
}

// loadSpatialData loads spatial data from PostGIS
func (d *DatabaseAdapter) loadSpatialData(ctx context.Context, model *building.BuildingModel) error {
	// This would load spatial data from the database
	buildingID := "unknown"
	if model.Building != nil {
		buildingID = model.Building.ArxosID
	}
	logger.Debug("Loading spatial data for building %s", buildingID)

	// Example implementation would load:
	// - Building origin coordinates
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
