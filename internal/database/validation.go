package database

import (
	"fmt"

	"github.com/arx-os/arxos/pkg/models"
)

// ValidateFloorPlan validates a floor plan before saving
func ValidateFloorPlan(plan *models.FloorPlan) error {
	if plan == nil {
		return fmt.Errorf("floor plan is nil")
	}

	if plan.ID == "" {
		return fmt.Errorf("floor plan ID is required")
	}

	if plan.Name == "" {
		return fmt.Errorf("floor plan name is required")
	}

	if plan.Building == "" {
		return fmt.Errorf("building name is required")
	}

	// Check for duplicate room IDs
	roomIDs := make(map[string]bool)
	for _, room := range plan.Rooms {
		if room.ID == "" {
			return fmt.Errorf("room ID is required")
		}
		if roomIDs[room.ID] {
			return fmt.Errorf("duplicate room ID: %s", room.ID)
		}
		roomIDs[room.ID] = true
	}

	// Check for duplicate equipment IDs
	equipmentIDs := make(map[string]bool)
	for _, equipment := range plan.Equipment {
		if equipment.ID == "" {
			return fmt.Errorf("equipment ID is required")
		}
		if equipmentIDs[equipment.ID] {
			return fmt.Errorf("duplicate equipment ID: %s", equipment.ID)
		}
		equipmentIDs[equipment.ID] = true

		// Check if equipment references a valid room
		if equipment.RoomID != "" {
			if !roomIDs[equipment.RoomID] {
				return fmt.Errorf("equipment %s references non-existent room: %s", equipment.ID, equipment.RoomID)
			}
		}
	}

	return nil
}
