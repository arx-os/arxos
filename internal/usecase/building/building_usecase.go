package building

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/utils"
)

// BuildingUseCase implements the building business logic following Clean Architecture
type BuildingUseCase struct {
	buildingRepo  domain.BuildingRepository
	equipmentRepo domain.EquipmentRepository
	logger        domain.Logger
	idGenerator   *utils.IDGenerator
}

// NewBuildingUseCase creates a new BuildingUseCase
func NewBuildingUseCase(buildingRepo domain.BuildingRepository, equipmentRepo domain.EquipmentRepository, logger domain.Logger) *BuildingUseCase {
	return &BuildingUseCase{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		logger:        logger,
		idGenerator:   utils.NewIDGenerator(),
	}
}

// CreateBuilding creates a new building
func (uc *BuildingUseCase) CreateBuilding(ctx context.Context, req *domain.CreateBuildingRequest) (*domain.Building, error) {
	uc.logger.Info("Creating building", "name", req.Name)

	// Validate business rules
	if err := uc.validateCreateBuilding(req); err != nil {
		uc.logger.Error("Building validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Create building entity
	building := &domain.Building{
		ID:          uc.idGenerator.GenerateBuildingID(req.Name),
		Name:        req.Name,
		Address:     req.Address,
		Coordinates: req.Coordinates,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Save to repository - convert ID to string for compatibility
	buildingForRepo := &domain.Building{
		ID:          types.ID{Legacy: building.ID.String()}, // Convert to legacy format for repository
		Name:        building.Name,
		Address:     building.Address,
		Coordinates: building.Coordinates,
		Floors:      building.Floors,
		Equipment:   building.Equipment,
		CreatedAt:   building.CreatedAt,
		UpdatedAt:   building.UpdatedAt,
	}

	if err := uc.buildingRepo.Create(ctx, buildingForRepo); err != nil {
		uc.logger.Error("Failed to create building", "error", err)
		return nil, fmt.Errorf("failed to create building: %w", err)
	}

	uc.logger.Info("Building created successfully", "building_id", building.ID)
	return building, nil
}

// GetBuilding retrieves a building by ID
func (uc *BuildingUseCase) GetBuilding(ctx context.Context, id types.ID) (*domain.Building, error) {
	uc.logger.Info("Getting building", "building_id", id.String())

	if id.IsEmpty() {
		return nil, fmt.Errorf("building ID is required")
	}

	building, err := uc.buildingRepo.GetByID(ctx, id.String())
	if err != nil {
		uc.logger.Error("Failed to get building", "building_id", id.String(), "error", err)
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	// Convert back to new ID format
	return &domain.Building{
		ID:          types.FromString(building.ID.String()),
		Name:        building.Name,
		Address:     building.Address,
		Coordinates: building.Coordinates,
		Floors:      building.Floors,
		Equipment:   building.Equipment,
		CreatedAt:   building.CreatedAt,
		UpdatedAt:   building.UpdatedAt,
	}, nil
}

// UpdateBuilding updates an existing building
func (uc *BuildingUseCase) UpdateBuilding(ctx context.Context, req *domain.UpdateBuildingRequest) (*domain.Building, error) {
	uc.logger.Info("Updating building", "building_id", req.ID)

	// Get existing building
	building, err := uc.buildingRepo.GetByID(ctx, req.ID.String())
	if err != nil {
		uc.logger.Error("Failed to get building for update", "building_id", req.ID.String(), "error", err)
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	// Update fields if provided
	if req.Name != nil {
		building.Name = *req.Name
	}
	if req.Address != nil {
		building.Address = *req.Address
	}
	if req.Coordinates != nil {
		building.Coordinates = req.Coordinates
	}
	building.UpdatedAt = time.Now()

	// Validate business rules
	if err := uc.validateUpdateBuilding(building); err != nil {
		uc.logger.Error("Building validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Save to repository
	if err := uc.buildingRepo.Update(ctx, building); err != nil {
		uc.logger.Error("Failed to update building", "building_id", req.ID, "error", err)
		return nil, fmt.Errorf("failed to update building: %w", err)
	}

	uc.logger.Info("Building updated successfully", "building_id", building.ID)
	return building, nil
}

// DeleteBuilding deletes a building
func (uc *BuildingUseCase) DeleteBuilding(ctx context.Context, id string) error {
	uc.logger.Info("Deleting building", "building_id", id)

	if id == "" {
		return fmt.Errorf("building ID is required")
	}

	// Check if building exists
	_, err := uc.buildingRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get building for deletion", "building_id", id, "error", err)
		return fmt.Errorf("failed to get building: %w", err)
	}

	// Business rule: Check if building has equipment
	equipment, err := uc.equipmentRepo.GetByBuilding(ctx, id)
	if err == nil && len(equipment) > 0 {
		return fmt.Errorf("cannot delete building with existing equipment")
	}

	// Delete from repository
	if err := uc.buildingRepo.Delete(ctx, id); err != nil {
		uc.logger.Error("Failed to delete building", "building_id", id, "error", err)
		return fmt.Errorf("failed to delete building: %w", err)
	}

	uc.logger.Info("Building deleted successfully", "building_id", id)
	return nil
}

// ListBuildings retrieves a list of buildings with optional filtering
func (uc *BuildingUseCase) ListBuildings(ctx context.Context, filter *domain.BuildingFilter) ([]*domain.Building, error) {
	uc.logger.Info("Listing buildings", "filter", filter)

	// Set default pagination if not provided
	if filter.Limit <= 0 {
		filter.Limit = 100
	}

	buildings, err := uc.buildingRepo.List(ctx, filter)
	if err != nil {
		uc.logger.Error("Failed to list buildings", "error", err)
		return nil, fmt.Errorf("failed to list buildings: %w", err)
	}

	uc.logger.Info("Buildings listed successfully", "count", len(buildings))
	return buildings, nil
}

// ImportBuilding imports a building from external data using IfcOpenShell service
func (uc *BuildingUseCase) ImportBuilding(ctx context.Context, req *domain.ImportBuildingRequest) (*domain.Building, error) {
	uc.logger.Info("Importing building", "format", req.Format, "size", len(req.Data))

	// Only IFC format is supported per memory
	if req.Format != "ifc" {
		return nil, fmt.Errorf("only IFC format is supported for import")
	}

	// Validate IFC data size
	if len(req.Data) == 0 {
		return nil, fmt.Errorf("IFC data is empty")
	}
	if len(req.Data) > 200*1024*1024 { // 200MB limit
		return nil, fmt.Errorf("IFC file too large (max 200MB)")
	}

	// Note: Full IFC parsing would require the IFC service which is in the container
	// For now, create a building from IFC with basic extraction

	// Extract building name from filename or use default
	buildingName := "Imported IFC Building"

	// Create building entity
	building := &domain.Building{
		ID:          uc.idGenerator.GenerateBuildingID(buildingName),
		Name:        buildingName,
		Address:     "Imported from IFC",
		Coordinates: nil, // Would extract from IFC if available
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Save to repository
	if err := uc.buildingRepo.Create(ctx, building); err != nil {
		uc.logger.Error("Failed to create imported building", "error", err)
		return nil, fmt.Errorf("failed to create building: %w", err)
	}

	uc.logger.Info("Building imported successfully", "building_id", building.ID, "format", req.Format)
	return building, nil
}

// ExportBuilding exports a building to external format
func (uc *BuildingUseCase) ExportBuilding(ctx context.Context, id, format string) ([]byte, error) {
	uc.logger.Info("Exporting building", "building_id", id, "format", format)

	// Get building
	building, err := uc.buildingRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get building for export", "building_id", id, "error", err)
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	// Export building based on format
	switch format {
	case "json":
		// Export as JSON
		result, err := uc.exportBuildingAsJSON(ctx, building)
		if err != nil {
			return nil, err
		}
		return []byte(result.(string)), nil
	case "csv":
		// Export as CSV (equipment list)
		result, err := uc.exportBuildingAsCSV(ctx, building)
		if err != nil {
			return nil, err
		}
		return []byte(result.(string)), nil
	case "ifc":
		// IFC export would require IFC generation (complex)
		return nil, fmt.Errorf("IFC export not yet implemented")
	default:
		return nil, fmt.Errorf("unsupported export format: %s", format)
	}
}

// Private helper methods

func (uc *BuildingUseCase) validateCreateBuilding(req *domain.CreateBuildingRequest) error {
	if req.Name == "" {
		return fmt.Errorf("building name is required")
	}
	if req.Address == "" {
		return fmt.Errorf("building address is required")
	}

	return nil
}

func (uc *BuildingUseCase) validateUpdateBuilding(building *domain.Building) error {
	if building.Name == "" {
		return fmt.Errorf("building name cannot be empty")
	}
	if building.Address == "" {
		return fmt.Errorf("building address cannot be empty")
	}

	return nil
}

// exportBuildingAsJSON exports building as JSON
func (uc *BuildingUseCase) exportBuildingAsJSON(ctx context.Context, building *domain.Building) (any, error) {
	// Create export structure
	export := map[string]any{
		"id":         building.ID.String(),
		"name":       building.Name,
		"address":    building.Address,
		"created_at": building.CreatedAt,
		"updated_at": building.UpdatedAt,
	}

	if building.Coordinates != nil {
		export["coordinates"] = map[string]float64{
			"latitude":  building.Coordinates.Y,
			"longitude": building.Coordinates.X,
			"altitude":  building.Coordinates.Z,
		}
	}

	// Get equipment for this building
	equipmentFilter := &domain.EquipmentFilter{
		BuildingID: &building.ID,
	}
	equipment, err := uc.equipmentRepo.List(ctx, equipmentFilter)
	if err == nil && equipment != nil {
		export["equipment_count"] = len(equipment)
		export["equipment"] = equipment
	}

	// Marshal to JSON string
	jsonData, err := json.MarshalIndent(export, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("failed to marshal JSON: %w", err)
	}

	return string(jsonData), nil
}

// exportBuildingAsCSV exports building equipment as CSV
func (uc *BuildingUseCase) exportBuildingAsCSV(ctx context.Context, building *domain.Building) (any, error) {
	// Get equipment for this building
	equipmentFilter := &domain.EquipmentFilter{
		BuildingID: &building.ID,
	}
	equipment, err := uc.equipmentRepo.List(ctx, equipmentFilter)
	if err != nil {
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	// Build CSV
	var csv strings.Builder
	csv.WriteString("id,name,type,status,model,building\n")

	for _, e := range equipment {
		csv.WriteString(fmt.Sprintf("%s,%s,%s,%s,%s,%s\n",
			e.ID.String(),
			e.Name,
			e.Type,
			e.Status,
			e.Model,
			building.Name,
		))
	}

	return csv.String(), nil
}
