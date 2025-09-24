package building

import (
	"time"

	"github.com/arx-os/arxos/internal/core/equipment"
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
	eq.BuildingID = bm.Building.ID
	bm.Equipment = append(bm.Equipment, eq)
}

// Validate validates the entire building model
func (bm *BuildingModel) Validate() []ValidationIssue {
	issues := []ValidationIssue{}

	// Validate building
	if bm.Building == nil {
		issues = append(issues, ValidationIssue{
			Level:   ValidationLevelError,
			Type:    "missing_building",
			Message: "Building information is required",
		})
		return issues
	}

	if err := bm.Building.Validate(); err != nil {
		issues = append(issues, ValidationIssue{
			Level:      ValidationLevelError,
			Type:       "invalid_building",
			EntityType: "building",
			EntityID:   bm.Building.ID.String(),
			Message:    err.Error(),
		})
	}

	// Validate floors
	if len(bm.Floors) == 0 {
		issues = append(issues, ValidationIssue{
			Level:   ValidationLevelWarning,
			Type:    "no_floors",
			Message: "Building has no floors defined",
		})
	}

	floorIDs := make(map[uuid.UUID]bool)
	for _, floor := range bm.Floors {
		if floor.ID == uuid.Nil {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelError,
				Type:       "invalid_floor_id",
				EntityType: "floor",
				Field:      "id",
				Message:    "Floor ID is required",
			})
		}
		if floorIDs[floor.ID] {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelError,
				Type:       "duplicate_floor_id",
				EntityType: "floor",
				EntityID:   floor.ID.String(),
				Message:    "Duplicate floor ID found",
			})
		}
		floorIDs[floor.ID] = true

		if floor.Name == "" {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelWarning,
				Type:       "missing_floor_name",
				EntityType: "floor",
				EntityID:   floor.ID.String(),
				Field:      "name",
				Message:    "Floor name is missing",
			})
		}
	}

	// Validate rooms
	roomIDs := make(map[uuid.UUID]bool)
	for _, room := range bm.Rooms {
		if room.ID == uuid.Nil {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelError,
				Type:       "invalid_room_id",
				EntityType: "room",
				Field:      "id",
				Message:    "Room ID is required",
			})
		}
		if roomIDs[room.ID] {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelError,
				Type:       "duplicate_room_id",
				EntityType: "room",
				EntityID:   room.ID.String(),
				Message:    "Duplicate room ID found",
			})
		}
		roomIDs[room.ID] = true

		// Check if room's floor exists
		if room.FloorID != uuid.Nil && !floorIDs[room.FloorID] {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelError,
				Type:       "invalid_floor_reference",
				EntityType: "room",
				EntityID:   room.ID.String(),
				Field:      "floor_id",
				Message:    "Room references non-existent floor",
				Details: map[string]interface{}{
					"floor_id": room.FloorID.String(),
				},
			})
		}
	}

	// Validate equipment
	for _, eq := range bm.Equipment {
		if err := eq.Validate(); err != nil {
			issues = append(issues, ValidationIssue{
				Level:      ValidationLevelError,
				Type:       "invalid_equipment",
				EntityType: "equipment",
				EntityID:   eq.ID.String(),
				Message:    err.Error(),
			})
		}
	}

	bm.ValidationIssues = issues
	return issues
}

// HasErrors returns true if the model has validation errors
func (bm *BuildingModel) HasErrors() bool {
	for _, issue := range bm.ValidationIssues {
		if issue.Level == ValidationLevelError {
			return true
		}
	}
	return false
}

// GetFloorByLevel returns a floor by its level number
func (bm *BuildingModel) GetFloorByLevel(level int) *Floor {
	for i := range bm.Floors {
		if bm.Floors[i].Level == level {
			return &bm.Floors[i]
		}
	}
	return nil
}

// GetRoomsByFloor returns all rooms on a specific floor
func (bm *BuildingModel) GetRoomsByFloor(floorID uuid.UUID) []Room {
	rooms := []Room{}
	for _, room := range bm.Rooms {
		if room.FloorID == floorID {
			rooms = append(rooms, room)
		}
	}
	return rooms
}

// GetEquipmentByRoom returns all equipment in a specific room
func (bm *BuildingModel) GetEquipmentByRoom(roomID string) []*equipment.Equipment {
	// Since equipment doesn't have direct RoomID, we would need to
	// determine room association through position or metadata
	equipment := []*equipment.Equipment{}
	for _, eq := range bm.Equipment {
		// Check if equipment metadata contains room information
		if eq.Metadata != nil {
			if rid, ok := eq.Metadata["room_id"].(string); ok && rid == roomID {
				equipment = append(equipment, eq)
			}
		}
	}
	return equipment
}

// GetAllEquipment returns all equipment in the building
func (bm *BuildingModel) GetAllEquipment() []*equipment.Equipment {
	return bm.Equipment
}
