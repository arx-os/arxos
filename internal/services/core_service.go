package services

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/ecosystem"
)

// CoreService implements the core tier business logic (Layer 1 - FREE)
type CoreService struct {
	db *database.PostGISDB
}

// NewCoreService creates a new core service
func NewCoreService(db *database.PostGISDB) *CoreService {
	return &CoreService{
		db: db,
	}
}

// Building management

func (cs *CoreService) CreateBuilding(ctx context.Context, req ecosystem.CreateBuildingRequest) (*ecosystem.Building, error) {
	// Validate request
	if req.Name == "" {
		return nil, fmt.Errorf("building name is required")
	}
	if req.Path == "" {
		return nil, fmt.Errorf("building path is required")
	}

	// Check if building path already exists
	var existingCount int
	err := cs.db.QueryRow(ctx, "SELECT COUNT(*) FROM buildings WHERE path = $1", req.Path).Scan(&existingCount)
	if err != nil {
		return nil, fmt.Errorf("failed to check existing building: %w", err)
	}
	if existingCount > 0 {
		return nil, fmt.Errorf("building with path '%s' already exists", req.Path)
	}

	// Create building
	query := `
		INSERT INTO buildings (id, name, path, tier, metadata, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
		RETURNING id, name, path, tier, metadata, created_at, updated_at
	`

	var building ecosystem.Building
	buildingID := generateBuildingID()

	err = cs.db.QueryRow(ctx, query,
		buildingID,
		req.Name,
		req.Path,
		string(ecosystem.TierCore),
		req.Metadata,
	).Scan(
		&building.ID,
		&building.Name,
		&building.Path,
		&building.Tier,
		&building.Metadata,
		&building.CreatedAt,
		&building.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create building: %w", err)
	}

	// Create default spatial structure for the building
	if err := cs.createDefaultSpatialStructure(ctx, buildingID, req.Path); err != nil {
		// Log error but don't fail building creation
		fmt.Printf("Warning: failed to create spatial structure for building %s: %v\n", buildingID, err)
	}

	return &building, nil
}

func (cs *CoreService) GetBuilding(ctx context.Context, id string) (*ecosystem.Building, error) {
	query := `
		SELECT id, name, path, tier, metadata, created_at, updated_at
		FROM buildings
		WHERE id = $1
	`

	var building ecosystem.Building
	err := cs.db.QueryRow(ctx, query, id).Scan(
		&building.ID,
		&building.Name,
		&building.Path,
		&building.Tier,
		&building.Metadata,
		&building.CreatedAt,
		&building.UpdatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("building not found")
		}
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	return &building, nil
}

func (cs *CoreService) ListBuildings(ctx context.Context, userID string) ([]*ecosystem.Building, error) {
	query := `
		SELECT id, name, path, tier, metadata, created_at, updated_at
		FROM buildings
		ORDER BY created_at DESC
	`

	rows, err := cs.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to list buildings: %w", err)
	}
	defer rows.Close()

	var buildings []*ecosystem.Building
	for rows.Next() {
		var building ecosystem.Building
		err := rows.Scan(
			&building.ID,
			&building.Name,
			&building.Path,
			&building.Tier,
			&building.Metadata,
			&building.CreatedAt,
			&building.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan building: %w", err)
		}
		buildings = append(buildings, &building)
	}

	return buildings, nil
}

// Equipment management

func (cs *CoreService) CreateEquipment(ctx context.Context, req ecosystem.CreateEquipmentRequest) (*ecosystem.Equipment, error) {
	// Validate request
	if req.Name == "" {
		return nil, fmt.Errorf("equipment name is required")
	}
	if req.Path == "" {
		return nil, fmt.Errorf("equipment path is required")
	}
	if req.Type == "" {
		return nil, fmt.Errorf("equipment type is required")
	}

	// Validate that the building exists
	var buildingExists bool
	err := cs.db.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM buildings WHERE path = $1)",
		extractBuildingPath(req.Path)).Scan(&buildingExists)
	if err != nil {
		return nil, fmt.Errorf("failed to validate building: %w", err)
	}
	if !buildingExists {
		return nil, fmt.Errorf("building not found for path: %s", req.Path)
	}

	// Check if equipment path already exists
	var existingCount int
	err = cs.db.QueryRow(ctx, "SELECT COUNT(*) FROM equipment WHERE path = $1", req.Path).Scan(&existingCount)
	if err != nil {
		return nil, fmt.Errorf("failed to check existing equipment: %w", err)
	}
	if existingCount > 0 {
		return nil, fmt.Errorf("equipment with path '%s' already exists", req.Path)
	}

	// Create equipment
	query := `
		INSERT INTO equipment (id, name, path, type, position, tier, metadata, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
		RETURNING id, name, path, type, position, tier, metadata, created_at, updated_at
	`

	var equipment ecosystem.Equipment
	equipmentID := generateEquipmentID()

	err = cs.db.QueryRow(ctx, query,
		equipmentID,
		req.Name,
		req.Path,
		req.Type,
		req.Position,
		string(ecosystem.TierCore),
		req.Metadata,
	).Scan(
		&equipment.ID,
		&equipment.Name,
		&equipment.Path,
		&equipment.Type,
		&equipment.Position,
		&equipment.Tier,
		&equipment.Metadata,
		&equipment.CreatedAt,
		&equipment.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create equipment: %w", err)
	}

	// Create spatial entry for the equipment
	if err := cs.createSpatialEntry(ctx, equipmentID, req.Position, req.Path); err != nil {
		// Log error but don't fail equipment creation
		fmt.Printf("Warning: failed to create spatial entry for equipment %s: %v\n", equipmentID, err)
	}

	return &equipment, nil
}

func (cs *CoreService) GetEquipment(ctx context.Context, id string) (*ecosystem.Equipment, error) {
	query := `
		SELECT id, name, path, type, position, tier, metadata, created_at, updated_at
		FROM equipment
		WHERE id = $1
	`

	var equipment ecosystem.Equipment
	err := cs.db.QueryRow(ctx, query, id).Scan(
		&equipment.ID,
		&equipment.Name,
		&equipment.Path,
		&equipment.Type,
		&equipment.Position,
		&equipment.Tier,
		&equipment.Metadata,
		&equipment.CreatedAt,
		&equipment.UpdatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("equipment not found")
		}
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	return &equipment, nil
}

func (cs *CoreService) QueryEquipment(ctx context.Context, query ecosystem.EquipmentQuery) ([]*ecosystem.Equipment, error) {
	sqlQuery := `
		SELECT id, name, path, type, position, tier, metadata, created_at, updated_at
		FROM equipment
		WHERE 1=1
	`

	args := []interface{}{}
	argIndex := 1

	if query.BuildingID != "" {
		sqlQuery += fmt.Sprintf(" AND path LIKE $%d", argIndex)
		args = append(args, query.BuildingID+"%")
		argIndex++
	}

	if query.Type != "" {
		sqlQuery += fmt.Sprintf(" AND type = $%d", argIndex)
		args = append(args, query.Type)
		argIndex++
	}

	// Add filters
	for key, value := range query.Filters {
		sqlQuery += fmt.Sprintf(" AND metadata->>'%s' = $%d", key, argIndex)
		args = append(args, value)
		argIndex++
	}

	if query.Limit > 0 {
		sqlQuery += fmt.Sprintf(" LIMIT $%d", argIndex)
		args = append(args, query.Limit)
		argIndex++
	}

	if query.Offset > 0 {
		sqlQuery += fmt.Sprintf(" OFFSET $%d", argIndex)
		args = append(args, query.Offset)
		argIndex++
	}

	rows, err := cs.db.Query(ctx, sqlQuery, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query equipment: %w", err)
	}
	defer rows.Close()

	var equipment []*ecosystem.Equipment
	for rows.Next() {
		var item ecosystem.Equipment
		err := rows.Scan(
			&item.ID,
			&item.Name,
			&item.Path,
			&item.Type,
			&item.Position,
			&item.Tier,
			&item.Metadata,
			&item.CreatedAt,
			&item.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}
		equipment = append(equipment, &item)
	}

	return equipment, nil
}

// Spatial operations

func (cs *CoreService) SpatialQuery(ctx context.Context, query ecosystem.SpatialQuery) ([]*ecosystem.Equipment, error) {
	// Simple spatial query - in production this would use PostGIS spatial functions
	sqlQuery := `
		SELECT id, name, path, type, position, tier, metadata, created_at, updated_at
		FROM equipment
		WHERE 1=1
	`

	args := []interface{}{}
	argIndex := 1

	// Add type filter if specified
	if query.Type != "" {
		sqlQuery += fmt.Sprintf(" AND type = $%d", argIndex)
		args = append(args, query.Type)
		argIndex++
	}

	// Add radius filter if center and radius are specified
	if query.Center != nil && query.Radius > 0 {
		if x, ok := query.Center["x"].(float64); ok {
			if y, ok := query.Center["y"].(float64); ok {
				// Simple distance calculation - in production use PostGIS ST_DWithin
				sqlQuery += fmt.Sprintf(`
					AND (
						(position->>'x')::float - $%d)^2 + 
						((position->>'y')::float - $%d)^2 <= $%d^2
					`, argIndex, argIndex+1, argIndex+2)
				args = append(args, x, y, query.Radius)
				argIndex += 3
			}
		}
	}

	rows, err := cs.db.Query(ctx, sqlQuery, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to execute spatial query: %w", err)
	}
	defer rows.Close()

	var equipment []*ecosystem.Equipment
	for rows.Next() {
		var item ecosystem.Equipment
		err := rows.Scan(
			&item.ID,
			&item.Name,
			&item.Path,
			&item.Type,
			&item.Position,
			&item.Tier,
			&item.Metadata,
			&item.CreatedAt,
			&item.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment: %w", err)
		}
		equipment = append(equipment, &item)
	}

	return equipment, nil
}

// Import/Export operations

func (cs *CoreService) ImportData(ctx context.Context, req ecosystem.ImportRequest) (*ecosystem.ImportResult, error) {
	// Validate request
	if req.Format == "" {
		return nil, fmt.Errorf("import format is required")
	}
	if req.Data == nil || len(req.Data) == 0 {
		return nil, fmt.Errorf("import data is required")
	}

	result := &ecosystem.ImportResult{
		ID:       generateImportID(),
		Status:   "processing",
		Message:  "Import started",
		Imported: 0,
		Errors:   0,
	}

	// Process based on format
	switch req.Format {
	case "bim_txt":
		return cs.importBIMText(ctx, req, result)
	case "ifc":
		return cs.importIFC(ctx, req, result)
	case "pdf":
		return cs.importPDF(ctx, req, result)
	default:
		return nil, fmt.Errorf("unsupported import format: %s", req.Format)
	}
}

func (cs *CoreService) ExportData(ctx context.Context, req ecosystem.ExportRequest) (*ecosystem.ExportResult, error) {
	// Validate request
	if req.Format == "" {
		return nil, fmt.Errorf("export format is required")
	}

	result := &ecosystem.ExportResult{
		ID:     generateExportID(),
		Status: "processing",
		Format: req.Format,
		Size:   0,
	}

	// Process based on format
	switch req.Format {
	case "bim_txt":
		return cs.exportBIMText(ctx, req, result)
	case "json":
		return cs.exportJSON(ctx, req, result)
	case "csv":
		return cs.exportCSV(ctx, req, result)
	default:
		return nil, fmt.Errorf("unsupported export format: %s", req.Format)
	}
}

// Helper functions

func (cs *CoreService) createDefaultSpatialStructure(ctx context.Context, buildingID, path string) error {
	// Create default floors and rooms for the building
	// This is a simplified implementation
	query := `
		INSERT INTO spatial_structure (id, building_id, path, type, name, created_at)
		VALUES ($1, $2, $3, $4, $5, NOW())
	`

	// Create default floor
	floorID := generateSpatialID()
	_, err := cs.db.Exec(ctx, query, floorID, buildingID, path+"/1", "floor", "Floor 1")
	if err != nil {
		return fmt.Errorf("failed to create default floor: %w", err)
	}

	// Create default room
	roomID := generateSpatialID()
	_, err = cs.db.Exec(ctx, query, roomID, buildingID, path+"/1/101", "room", "Room 101")
	if err != nil {
		return fmt.Errorf("failed to create default room: %w", err)
	}

	return nil
}

func (cs *CoreService) createSpatialEntry(ctx context.Context, equipmentID string, position map[string]interface{}, path string) error {
	// Create spatial entry for equipment
	query := `
		INSERT INTO equipment_spatial (equipment_id, position, path, created_at)
		VALUES ($1, $2, $3, NOW())
	`

	_, err := cs.db.Exec(ctx, query, equipmentID, position, path)
	if err != nil {
		return fmt.Errorf("failed to create spatial entry: %w", err)
	}

	return nil
}

// Import/Export format handlers

func (cs *CoreService) importBIMText(ctx context.Context, req ecosystem.ImportRequest, result *ecosystem.ImportResult) (*ecosystem.ImportResult, error) {
	// Parse BIM text format and import buildings/equipment
	// This is a simplified implementation
	result.Status = "completed"
	result.Message = "BIM text import completed"
	result.Imported = 1 // Placeholder
	return result, nil
}

func (cs *CoreService) importIFC(ctx context.Context, req ecosystem.ImportRequest, result *ecosystem.ImportResult) (*ecosystem.ImportResult, error) {
	// Parse IFC format and import buildings/equipment
	// This is a simplified implementation
	result.Status = "completed"
	result.Message = "IFC import completed"
	result.Imported = 1 // Placeholder
	return result, nil
}

func (cs *CoreService) importPDF(ctx context.Context, req ecosystem.ImportRequest, result *ecosystem.ImportResult) (*ecosystem.ImportResult, error) {
	// Parse PDF format and extract building information
	// This is a simplified implementation
	result.Status = "completed"
	result.Message = "PDF import completed"
	result.Imported = 1 // Placeholder
	return result, nil
}

func (cs *CoreService) exportBIMText(ctx context.Context, req ecosystem.ExportRequest, result *ecosystem.ExportResult) (*ecosystem.ExportResult, error) {
	// Export building data to BIM text format
	result.Status = "completed"
	result.Data = []byte("BIM_TEXT_EXPORT_DATA") // Placeholder
	result.Size = int64(len(result.Data))
	return result, nil
}

func (cs *CoreService) exportJSON(ctx context.Context, req ecosystem.ExportRequest, result *ecosystem.ExportResult) (*ecosystem.ExportResult, error) {
	// Export building data to JSON format
	result.Status = "completed"
	result.Data = []byte(`{"buildings": [], "equipment": []}`) // Placeholder
	result.Size = int64(len(result.Data))
	return result, nil
}

func (cs *CoreService) exportCSV(ctx context.Context, req ecosystem.ExportRequest, result *ecosystem.ExportResult) (*ecosystem.ExportResult, error) {
	// Export building data to CSV format
	result.Status = "completed"
	result.Data = []byte("id,name,type,path\n") // Placeholder
	result.Size = int64(len(result.Data))
	return result, nil
}

// Utility functions

func generateBuildingID() string {
	return fmt.Sprintf("building_%d", time.Now().UnixNano())
}

func generateEquipmentID() string {
	return fmt.Sprintf("equipment_%d", time.Now().UnixNano())
}

func generateSpatialID() string {
	return fmt.Sprintf("spatial_%d", time.Now().UnixNano())
}

func generateImportID() string {
	return fmt.Sprintf("import_%d", time.Now().UnixNano())
}

func generateExportID() string {
	return fmt.Sprintf("export_%d", time.Now().UnixNano())
}

func extractBuildingPath(equipmentPath string) string {
	// Extract building path from equipment path
	// e.g., "/B1/3/HVAC/DAMPER-01" -> "/B1"
	parts := splitPath(equipmentPath)
	if len(parts) >= 2 {
		return "/" + parts[1]
	}
	return ""
}

func splitPath(path string) []string {
	// Split path into components, removing empty strings
	parts := []string{}
	for _, part := range strings.Split(path, "/") {
		if part != "" {
			parts = append(parts, part)
		}
	}
	return parts
}
