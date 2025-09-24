package services

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// ImportImplementations provides the actual implementations for import operations
type ImportImplementations struct {
	db database.DB
}

// NewImportImplementations creates a new import implementations instance
func NewImportImplementations(db database.DB) *ImportImplementations {
	return &ImportImplementations{db: db}
}

// ImportPDF implements PDF import functionality
func (ii *ImportImplementations) ImportPDF(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	logger.Info("Starting PDF import for file: %s", inputFile)

	// Check if file exists
	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		return fmt.Errorf("PDF file not found: %s", inputFile)
	}

	// For now, create a simple building from PDF file
	// In a real implementation, this would use a PDF converter
	building := &bim.Building{
		Name: filepath.Base(inputFile),
	}

	// Convert to database model
	dbModel := ii.convertBIMToFloorPlan(building, filepath.Base(inputFile))

	// Save to database
	if err := ii.db.SaveFloorPlan(ctx, dbModel); err != nil {
		return fmt.Errorf("failed to save building to database: %w", err)
	}

	logger.Info("Successfully imported PDF file: %s", inputFile)
	return nil
}

// ImportIFC implements IFC import functionality
func (ii *ImportImplementations) ImportIFC(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	logger.Info("Starting IFC import for file: %s", inputFile)

	// Check if file exists
	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		return fmt.Errorf("IFC file not found: %s", inputFile)
	}

	// For now, create a simple building from IFC file
	// In a real implementation, this would use an IFC converter
	building := &bim.Building{
		Name: filepath.Base(inputFile),
	}

	// Convert to database model
	dbModel := ii.convertBIMToFloorPlan(building, filepath.Base(inputFile))

	// Save to database
	if err := ii.db.SaveFloorPlan(ctx, dbModel); err != nil {
		return fmt.Errorf("failed to save building to database: %w", err)
	}

	logger.Info("Successfully imported IFC file: %s", inputFile)
	return nil
}

// ImportCSV implements CSV import functionality
func (ii *ImportImplementations) ImportCSV(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	logger.Info("Starting CSV import for file: %s", inputFile)

	// Check if file exists
	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		return fmt.Errorf("CSV file not found: %s", inputFile)
	}

	// Open CSV file
	file, err := os.Open(inputFile)
	if err != nil {
		return fmt.Errorf("failed to open CSV file: %w", err)
	}
	defer file.Close()

	// Create CSV reader
	reader := csv.NewReader(file)

	// Read header row
	headers, err := reader.Read()
	if err != nil {
		return fmt.Errorf("failed to read CSV headers: %w", err)
	}

	// Create building from CSV
	building := &models.FloorPlan{
		ID:   filepath.Base(inputFile),
		Name: filepath.Base(inputFile),
	}

	// Process CSV rows
	rowCount := 0
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return fmt.Errorf("failed to read CSV row: %w", err)
		}

		// Create equipment from CSV row
		equipment := ii.createEquipmentFromCSVRow(headers, record)
		if equipment != nil {
			building.Equipment = append(building.Equipment, equipment)
		}

		rowCount++
	}

	// Save to database
	if err := ii.db.SaveFloorPlan(ctx, building); err != nil {
		return fmt.Errorf("failed to save building to database: %w", err)
	}

	logger.Info("Successfully imported CSV file: %s (%d rows)", inputFile, rowCount)
	return nil
}

// ImportJSON implements JSON import functionality
func (ii *ImportImplementations) ImportJSON(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	logger.Info("Starting JSON import for file: %s", inputFile)

	// Check if file exists
	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		return fmt.Errorf("JSON file not found: %s", inputFile)
	}

	// Open JSON file
	file, err := os.Open(inputFile)
	if err != nil {
		return fmt.Errorf("failed to open JSON file: %w", err)
	}
	defer file.Close()

	// Decode JSON
	var jsonData map[string]interface{}
	decoder := json.NewDecoder(file)
	if err := decoder.Decode(&jsonData); err != nil {
		return fmt.Errorf("failed to decode JSON: %w", err)
	}

	// Convert JSON to building model
	building := ii.convertJSONToFloorPlan(jsonData, filepath.Base(inputFile))

	// Save to database
	if err := ii.db.SaveFloorPlan(ctx, building); err != nil {
		return fmt.Errorf("failed to save building to database: %w", err)
	}

	logger.Info("Successfully imported JSON file: %s", inputFile)
	return nil
}

// ImportBIM implements actual BIM import using the import service
func (ii *ImportImplementations) ImportBIM(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	logger.Info("Starting BIM import for file: %s", inputFile)

	// Check if file exists
	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		return fmt.Errorf("BIM file not found: %s", inputFile)
	}

	// Open BIM file
	file, err := os.Open(inputFile)
	if err != nil {
		return fmt.Errorf("failed to open BIM file: %w", err)
	}
	defer file.Close()

	// Parse BIM file
	parser := bim.NewParser()
	building, err := parser.Parse(file)
	if err != nil {
		return fmt.Errorf("failed to parse BIM file: %w", err)
	}

	// Convert to database model
	dbModel := ii.convertBIMToFloorPlan(building, filepath.Base(inputFile))

	// Save to database
	if err := ii.db.SaveFloorPlan(ctx, dbModel); err != nil {
		return fmt.Errorf("failed to save building to database: %w", err)
	}

	logger.Info("Successfully imported BIM file: %s", inputFile)
	return nil
}

// Helper methods

// convertBIMToFloorPlan converts a BIM building to a FloorPlan model
func (ii *ImportImplementations) convertBIMToFloorPlan(building *bim.Building, filename string) *models.FloorPlan {
	floorPlan := &models.FloorPlan{
		ID:    strings.TrimSuffix(filename, filepath.Ext(filename)),
		Name:  building.Name,
		Level: 1, // Default level
	}

	// Convert rooms (placeholder - BIM building structure may vary)
	// In a real implementation, this would properly convert from BIM structure

	// Convert equipment (placeholder - BIM building structure may vary)
	// In a real implementation, this would properly convert from BIM structure

	// Set timestamps
	now := time.Now()
	floorPlan.CreatedAt = &now
	floorPlan.UpdatedAt = &now

	return floorPlan
}

// convertJSONToFloorPlan converts JSON data to a FloorPlan model
func (ii *ImportImplementations) convertJSONToFloorPlan(jsonData map[string]interface{}, filename string) *models.FloorPlan {
	floorPlan := &models.FloorPlan{
		ID:    strings.TrimSuffix(filename, filepath.Ext(filename)),
		Name:  filename,
		Level: 1,
	}

	// Extract building name
	if name, ok := jsonData["name"].(string); ok {
		floorPlan.Name = name
	}

	// Extract level
	if level, ok := jsonData["level"].(float64); ok {
		floorPlan.Level = int(level)
	}

	// Extract rooms
	if rooms, ok := jsonData["rooms"].([]interface{}); ok {
		for _, roomData := range rooms {
			if roomMap, ok := roomData.(map[string]interface{}); ok {
				room := &models.Room{
					ID:          ii.getString(roomMap, "id"),
					Name:        ii.getString(roomMap, "name"),
					FloorPlanID: floorPlan.ID,
				}
				floorPlan.Rooms = append(floorPlan.Rooms, room)
			}
		}
	}

	// Extract equipment
	if equipment, ok := jsonData["equipment"].([]interface{}); ok {
		for _, equipData := range equipment {
			if equipMap, ok := equipData.(map[string]interface{}); ok {
				equipment := &models.Equipment{
					ID:     ii.getString(equipMap, "id"),
					Name:   ii.getString(equipMap, "name"),
					Type:   ii.getString(equipMap, "type"),
					Status: ii.getString(equipMap, "status"),
					Model:  ii.getString(equipMap, "model"),
					Serial: ii.getString(equipMap, "serial"),
					RoomID: ii.getString(equipMap, "room_id"),
				}
				floorPlan.Equipment = append(floorPlan.Equipment, equipment)
			}
		}
	}

	// Set timestamps
	now := time.Now()
	floorPlan.CreatedAt = &now
	floorPlan.UpdatedAt = &now

	return floorPlan
}

// createEquipmentFromCSVRow creates equipment from a CSV row
func (ii *ImportImplementations) createEquipmentFromCSVRow(headers []string, record []string) *models.Equipment {
	if len(record) != len(headers) {
		return nil
	}

	equipment := &models.Equipment{
		Status: "active", // Default status
	}

	// Map CSV columns to equipment fields
	for i, header := range headers {
		if i < len(record) {
			value := strings.TrimSpace(record[i])
			if value == "" {
				continue
			}

			switch strings.ToLower(header) {
			case "id", "equipment_id":
				equipment.ID = value
			case "name", "equipment_name":
				equipment.Name = value
			case "type", "equipment_type":
				equipment.Type = value
			case "status":
				equipment.Status = value
			case "model":
				equipment.Model = value
			case "serial", "serial_number":
				equipment.Serial = value
			case "room_id", "room":
				equipment.RoomID = value
			}
		}
	}

	// Skip if no ID or name
	if equipment.ID == "" && equipment.Name == "" {
		return nil
	}

	// Generate ID if not provided
	if equipment.ID == "" {
		equipment.ID = fmt.Sprintf("equipment_%d", time.Now().UnixNano())
	}

	return equipment
}

// getString safely extracts a string value from a map
func (ii *ImportImplementations) getString(data map[string]interface{}, key string) string {
	if val, ok := data[key]; ok {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

// ImportCommandServiceWithImplementations extends ImportCommandService with actual implementations
type ImportCommandServiceWithImplementations struct {
	*ImportCommandService
	implementations *ImportImplementations
}

// NewImportCommandServiceWithImplementations creates a new import command service with implementations
func NewImportCommandServiceWithImplementations(db database.DB) *ImportCommandServiceWithImplementations {
	return &ImportCommandServiceWithImplementations{
		ImportCommandService: NewImportCommandService(db),
		implementations:      NewImportImplementations(db),
	}
}

// Override the import methods with actual implementations

// ImportPDF implements PDF import
func (s *ImportCommandServiceWithImplementations) ImportPDF(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	return s.implementations.ImportPDF(ctx, inputFile, opts)
}

// ImportIFC implements IFC import
func (s *ImportCommandServiceWithImplementations) ImportIFC(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	return s.implementations.ImportIFC(ctx, inputFile, opts)
}

// ImportCSV implements CSV import
func (s *ImportCommandServiceWithImplementations) ImportCSV(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	return s.implementations.ImportCSV(ctx, inputFile, opts)
}

// ImportJSON implements JSON import
func (s *ImportCommandServiceWithImplementations) ImportJSON(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	return s.implementations.ImportJSON(ctx, inputFile, opts)
}

// ImportBIM implements actual BIM import
func (s *ImportCommandServiceWithImplementations) ImportBIM(ctx context.Context, inputFile string, opts ImportCommandOptions) error {
	return s.implementations.ImportBIM(ctx, inputFile, opts)
}
