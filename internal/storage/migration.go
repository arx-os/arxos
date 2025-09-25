package storage

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/common/logger"
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

	// Read the JSON file
	data, err := os.ReadFile(jsonPath)
	if err != nil {
		return fmt.Errorf("failed to read JSON file: %w", err)
	}

	// Parse the old JSON format
	var oldBuilding OldBuildingFormat
	if err := json.Unmarshal(data, &oldBuilding); err != nil {
		return fmt.Errorf("failed to parse JSON: %w", err)
	}

	// Convert to new BuildingData format
	buildingData, err := convertOldJSONToBuildingData(&oldBuilding)
	if err != nil {
		return fmt.Errorf("failed to convert JSON to BuildingData: %w", err)
	}

	// Save using the new coordinator
	return coordinator.SaveBuilding(ctx, buildingData, SourceTerminal)
}

// OldBuildingFormat represents the old JSON format for backward compatibility
type OldBuildingFormat struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description,omitempty"`
	Address     string                 `json:"address,omitempty"`
	Project     string                 `json:"project,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
	Floors      []OldFloorFormat       `json:"floors,omitempty"`
	Systems     []OldSystemFormat      `json:"systems,omitempty"`
	Documents   []OldDocumentFormat    `json:"documents,omitempty"`
}

type OldFloorFormat struct {
	ID        string            `json:"id"`
	GUID      string            `json:"guid,omitempty"`
	IFCId     string            `json:"ifc_id,omitempty"`
	Name      string            `json:"name"`
	Level     int               `json:"level"`
	Elevation float64           `json:"elevation,omitempty"`
	Area      float64           `json:"area,omitempty"`
	Height    float64           `json:"height,omitempty"`
	Rooms     []OldRoomFormat   `json:"rooms,omitempty"`
	Equipment []OldEquipmentFormat `json:"equipment,omitempty"`
}

type OldRoomFormat struct {
	ID        string            `json:"id"`
	GUID      string            `json:"guid,omitempty"`
	IFCId     string            `json:"ifc_id,omitempty"`
	Name      string            `json:"name"`
	Type      string            `json:"type,omitempty"`
	Area      float64           `json:"area,omitempty"`
	Capacity  int               `json:"capacity,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

type OldEquipmentFormat struct {
	ID          string            `json:"id"`
	GUID        string            `json:"guid,omitempty"`
	IFCId       string            `json:"ifc_id,omitempty"`
	Name        string            `json:"name"`
	Type        string            `json:"type,omitempty"`
	Description string            `json:"description,omitempty"`
	Location    *OldLocationFormat `json:"location,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

type OldLocationFormat struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

type OldSystemFormat struct {
	ID          string   `json:"id"`
	Type        string   `json:"type"`
	Name        string   `json:"name"`
	Description string   `json:"description,omitempty"`
	Equipment   []string `json:"equipment,omitempty"`
}

type OldDocumentFormat struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Type        string `json:"type,omitempty"`
	Path        string `json:"path,omitempty"`
	Description string `json:"description,omitempty"`
}

// convertOldJSONToBuildingData converts old JSON format to new BuildingData
func convertOldJSONToBuildingData(old *OldBuildingFormat) (*BuildingData, error) {
	// Create BIM building from old format
	bimBuilding := &bim.Building{
		ID:               old.ID,
		Name:             old.Name,
		FileVersion:      "1.0.0",
		Generated:        time.Now(),
		CoordinateSystem: bim.TopLeftOrigin,
		Units:            bim.Meters,
		Metadata: bim.Metadata{
			CreatedBy:    "migration",
			Organization: "ArxOS",
			Tags:         []string{"migrated", "json"},
			Notes:        old.Description,
			Location: struct {
				Address string `json:"address,omitempty"`
				City    string `json:"city,omitempty"`
				State   string `json:"state,omitempty"`
				Country string `json:"country,omitempty"`
			}{
				Address: old.Address,
			},
		},
	}

	// Convert floors
	for _, oldFloor := range old.Floors {
		floor := bim.Floor{
			Level:      oldFloor.Level,
			Name:       oldFloor.Name,
			Dimensions: bim.Dimensions{
				Width:  oldFloor.Area, // Using area as width for simplicity
				Height: oldFloor.Height,
			},
			GridScale: bim.GridScale{
				Ratio:       "1:1",
				Description: "1 char = 1 meter",
			},
			Legend:      make(map[rune]string),
			Layout:      []string{},
			Rooms:       []bim.Room{},
			Equipment:   []bim.Equipment{},
			Connections: make(map[bim.ConnectionType][]bim.Connection),
			Issues:      []bim.Issue{},
		}

		// Convert rooms
		for _, oldRoom := range oldFloor.Rooms {
			room := bim.Room{
				ID:         oldRoom.ID,
				Name:       oldRoom.Name,
				Type:       oldRoom.Type,
				Location:   bim.Location{X: 0, Y: 0, Room: oldRoom.ID},
				Dimensions: bim.Dimensions{Width: oldRoom.Area, Height: 0},
				Description: fmt.Sprintf("Capacity: %d", oldRoom.Capacity),
			}
			floor.Rooms = append(floor.Rooms, room)
		}

		// Convert equipment
		for _, oldEquip := range oldFloor.Equipment {
			equipment := bim.Equipment{
				ID:           oldEquip.ID,
				Type:         oldEquip.Type,
				Location:     bim.Location{X: 0, Y: 0, Room: ""},
				Status:       bim.StatusUnknown,
				Notes:        oldEquip.Description,
				CustomFields: convertMetadataToStringMap(oldEquip.Metadata),
			}
			if oldEquip.Location != nil {
				equipment.Location = bim.Location{
					X: oldEquip.Location.X,
					Y: oldEquip.Location.Y,
					Room: "",
				}
			}
			floor.Equipment = append(floor.Equipment, equipment)
		}

		bimBuilding.Floors = append(bimBuilding.Floors, floor)
	}

	return &BuildingData{
		BIMBuilding:  bimBuilding,
		DataSources:  []DataSource{SourceTerminal},
		LastModified: time.Now(),
	}, nil
}

// convertMetadataToStringMap converts map[string]interface{} to map[string]string
func convertMetadataToStringMap(metadata map[string]interface{}) map[string]string {
	result := make(map[string]string)
	for k, v := range metadata {
		if str, ok := v.(string); ok {
			result[k] = str
		} else {
			result[k] = fmt.Sprintf("%v", v)
		}
	}
	return result
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
