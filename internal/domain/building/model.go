package building

import (
	"time"

	"github.com/arx-os/arxos/internal/domain/equipment"
	"github.com/google/uuid"
)

// BuildingModel represents the complete building model for import/export
type BuildingModel struct {
	// Core building information
	Building *Building `json:"building"`

	// Floors in the building
	Floors []Floor `json:"floors"`

	// All equipment across all floors
	Equipment []*equipment.Equipment `json:"equipment"`

	// Rooms across all floors
	Rooms []Room `json:"rooms"`

	// Import metadata
	ImportMetadata ImportMetadata `json:"import_metadata,omitempty"`

	// Validation results
	ValidationIssues []ValidationIssue `json:"validation_issues,omitempty"`
}

// Floor represents a single floor in the building
type Floor struct {
	ID          uuid.UUID              `json:"id"`
	BuildingID  uuid.UUID              `json:"building_id"`
	Level       int                    `json:"level"`
	Name        string                 `json:"name"`
	Description string                 `json:"description,omitempty"`
	Height      float64                `json:"height,omitempty"` // Floor height in meters
	Area        float64                `json:"area,omitempty"`   // Floor area in square meters
	Equipment   []*equipment.Equipment `json:"equipment,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Room represents a room in the building
type Room struct {
	ID         uuid.UUID              `json:"id"`
	FloorID    uuid.UUID              `json:"floor_id"`
	BuildingID uuid.UUID              `json:"building_id"`
	Name       string                 `json:"name"`
	Type       string                 `json:"type"` // office, conference, storage, etc.
	Area       float64                `json:"area,omitempty"`
	Capacity   int                    `json:"capacity,omitempty"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// ImportMetadata contains information about the import process
type ImportMetadata struct {
	Format          string                 `json:"format"`
	SourceFile      string                 `json:"source_file,omitempty"`
	ImportedAt      time.Time              `json:"imported_at"`
	ImporterVersion string                 `json:"importer_version,omitempty"`
	OriginalData    map[string]interface{} `json:"original_data,omitempty"`
}

// ValidationIssue represents a validation problem found in the model
type ValidationIssue struct {
	Level      ValidationLevel        `json:"level"`
	Type       string                 `json:"type"`
	EntityType string                 `json:"entity_type,omitempty"`
	EntityID   string                 `json:"entity_id,omitempty"`
	Field      string                 `json:"field,omitempty"`
	Message    string                 `json:"message"`
	Details    map[string]interface{} `json:"details,omitempty"`
}

// ValidationLevel represents the severity of a validation issue
type ValidationLevel string

const (
	ValidationLevelError   ValidationLevel = "error"
	ValidationLevelWarning ValidationLevel = "warning"
	ValidationLevelInfo    ValidationLevel = "info"
)

// NewBuildingModel creates a new building model
func NewBuildingModel(building *Building) *BuildingModel {
	return &BuildingModel{
		Building:         building,
		Floors:           []Floor{},
		Equipment:        []*equipment.Equipment{},
		Rooms:            []Room{},
		ValidationIssues: []ValidationIssue{},
	}
}

// AddFloor adds a floor to the building model
func (bm *BuildingModel) AddFloor(floor Floor) {
	floor.BuildingID = bm.Building.ID
	if floor.ID == uuid.Nil {
		floor.ID = uuid.New()
	}
	bm.Floors = append(bm.Floors, floor)
}

// AddRoom adds a room to the building model
func (bm *BuildingModel) AddRoom(room Room) {
	room.BuildingID = bm.Building.ID
	if room.ID == uuid.Nil {
		room.ID = uuid.New()
	}
	bm.Rooms = append(bm.Rooms, room)
}

// AddEquipment adds equipment to the building model
func (bm *BuildingModel) AddEquipment(eq *equipment.Equipment) {
	bm.Equipment = append(bm.Equipment, eq)
}

// AddValidationIssue adds a validation issue to the model
func (bm *BuildingModel) AddValidationIssue(issue ValidationIssue) {
	bm.ValidationIssues = append(bm.ValidationIssues, issue)
}

// HasValidationIssues returns true if there are any validation issues
func (bm *BuildingModel) HasValidationIssues() bool {
	return len(bm.ValidationIssues) > 0
}

// GetValidationIssuesByLevel returns validation issues filtered by level
func (bm *BuildingModel) GetValidationIssuesByLevel(level ValidationLevel) []ValidationIssue {
	var issues []ValidationIssue
	for _, issue := range bm.ValidationIssues {
		if issue.Level == level {
			issues = append(issues, issue)
		}
	}
	return issues
}

// Validate validates the building model
func (bm *BuildingModel) Validate() []ValidationIssue {
	var issues []ValidationIssue

	// Validate building
	if bm.Building == nil {
		issues = append(issues, ValidationIssue{
			Level:   ValidationLevelError,
			Type:    "missing_building",
			Message: "Building is required",
		})
	} else {
		if err := bm.Building.Validate(); err != nil {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelError,
				Type:       "building_validation",
				EntityType: "building",
				EntityID:   bm.Building.ID.String(),
				Message:    err.Error(),
			})
		}
	}

	// Validate floors
	for i, floor := range bm.Floors {
		if floor.Name == "" {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelWarning,
				Type:       "missing_floor_name",
				EntityType: "floor",
				EntityID:   floor.ID.String(),
				Message:    "Floor name is missing",
			})
		}
		if floor.Level < 0 {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelWarning,
				Type:       "invalid_floor_level",
				EntityType: "floor",
				EntityID:   floor.ID.String(),
				Message:    "Floor level should be non-negative",
			})
		}
		// Check for duplicate floor levels
		for j, otherFloor := range bm.Floors {
			if i != j && floor.Level == otherFloor.Level {
				issues = append(issues, ValidationIssue{
					Level:      ValidationLevelWarning,
					Type:       "duplicate_floor_level",
					EntityType: "floor",
					EntityID:   floor.ID.String(),
					Message:    "Duplicate floor level found",
				})
			}
		}
	}

	// Validate rooms
	for _, room := range bm.Rooms {
		if room.Name == "" {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelWarning,
				Type:       "missing_room_name",
				EntityType: "room",
				EntityID:   room.ID.String(),
				Message:    "Room name is missing",
			})
		}
		// Check if room's floor exists
		floorExists := false
		for _, floor := range bm.Floors {
			if floor.ID == room.FloorID {
				floorExists = true
				break
			}
		}
		if !floorExists {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelError,
				Type:       "orphaned_room",
				EntityType: "room",
				EntityID:   room.ID.String(),
				Message:    "Room references non-existent floor",
			})
		}
	}

	// Validate equipment
	for _, eq := range bm.Equipment {
		if eq.Name == "" {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelWarning,
				Type:       "missing_equipment_name",
				EntityType: "equipment",
				EntityID:   eq.ID.String(),
				Message:    "Equipment name is missing",
			})
		}
	}

	return issues
}

// GetTotalArea calculates the total area of all floors
func (bm *BuildingModel) GetTotalArea() float64 {
	total := 0.0
	for _, floor := range bm.Floors {
		total += floor.Area
	}
	return total
}

// GetFloorCount returns the number of floors
func (bm *BuildingModel) GetFloorCount() int {
	return len(bm.Floors)
}

// GetRoomCount returns the number of rooms
func (bm *BuildingModel) GetRoomCount() int {
	return len(bm.Rooms)
}

// GetEquipmentCount returns the number of equipment items
func (bm *BuildingModel) GetEquipmentCount() int {
	return len(bm.Equipment)
}

// GetFloorByLevel returns a floor by its level number
func (bm *BuildingModel) GetFloorByLevel(level int) *Floor {
	for _, floor := range bm.Floors {
		if floor.Level == level {
			return &floor
		}
	}
	return nil
}

// GetRoomsByFloor returns all rooms on a specific floor
func (bm *BuildingModel) GetRoomsByFloor(floorID uuid.UUID) []Room {
	var rooms []Room
	for _, room := range bm.Rooms {
		if room.FloorID == floorID {
			rooms = append(rooms, room)
		}
	}
	return rooms
}

// GetEquipmentByFloor returns all equipment on a specific floor
func (bm *BuildingModel) GetEquipmentByFloor(floorID uuid.UUID) []*equipment.Equipment {
	var equipment []*equipment.Equipment
	for _, eq := range bm.Equipment {
		// This would need to be implemented based on equipment location logic
		// For now, return all equipment
		equipment = append(equipment, eq)
	}
	return equipment
}
