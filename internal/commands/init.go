package commands

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// ExecuteInit creates a new building in the database
func ExecuteInit(opts InitOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewSQLiteDBFromPath("arxos.db")
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create building
	now := time.Now()
	building := &models.FloorPlan{
		ID:        opts.UUID,
		UUID:      opts.UUID,
		Name:      opts.Name,
		Building:  opts.Name,
		Level:     1,
		CreatedAt: &now,
		UpdatedAt: &now,
		Rooms:     []*models.Room{},
		Equipment: []*models.Equipment{},
	}

	// Add template equipment if specified
	if opts.Template != "" {
		building.Equipment = createTemplateEquipment(opts.Template, opts.UUID)
		logger.Info("Applied template: %s", opts.Template)
	}

	// Save to database
	if err := db.SaveFloorPlan(ctx, building); err != nil {
		return fmt.Errorf("failed to save building: %w", err)
	}

	logger.Info("Created building: %s (%s)", opts.Name, opts.UUID)
	if len(building.Equipment) > 0 {
		logger.Info("Added %d equipment items", len(building.Equipment))
	}

	return nil
}

func createTemplateEquipment(template, buildingUUID string) []*models.Equipment {
	equipment := []*models.Equipment{}

	switch template {
	case "office":
		equipment = append(equipment, &models.Equipment{
			ID:     "HVAC_RTU_01",
			Name:   "Rooftop HVAC Unit",
			Type:   "HVAC.RTU",
			Path:   "N/R/HVAC/01",
			RoomID: "", // Ensure empty string for NULL
			Status: models.StatusOperational,
		})
		equipment = append(equipment, &models.Equipment{
			ID:     "ELEC_PANEL_01",
			Name:   "Main Electrical Panel",
			Type:   "Electrical.Panel",
			Path:   "N/1/B/ELEC/01",
			Status: models.StatusOperational,
		})
		equipment = append(equipment, &models.Equipment{
			ID:     "ELEVATOR_01",
			Name:   "Passenger Elevator 1",
			Type:   "Transport.Elevator",
			Path:   "N/L/CORE/01",
			Status: models.StatusOperational,
		})
		equipment = append(equipment, &models.Equipment{
			ID:     "FIRE_PANEL_01",
			Name:   "Fire Alarm Panel",
			Type:   "Safety.FirePanel",
			Path:   "N/1/LOBBY/01",
			Status: models.StatusOperational,
		})

	case "warehouse":
		equipment = append(equipment, &models.Equipment{
			ID:     "DOCK_DOOR_01",
			Name:   "Loading Dock Door 1",
			Type:   "Access.DockDoor",
			Path:   "N/1/DOCK/01",
			Status: models.StatusOperational,
		})
		equipment = append(equipment, &models.Equipment{
			ID:     "HVAC_UNIT_01",
			Name:   "Warehouse HVAC Unit",
			Type:   "HVAC.Industrial",
			Path:   "N/1/MECH/01",
			Status: models.StatusOperational,
		})
		equipment = append(equipment, &models.Equipment{
			ID:     "RACK_SYSTEM_01",
			Name:   "Automated Storage System",
			Type:   "Storage.Automated",
			Path:   "N/1/STORAGE/01",
			Status: models.StatusOperational,
		})

	case "school":
		equipment = append(equipment, &models.Equipment{
			ID:     "FIRE_PANEL_01",
			Name:   "Fire Alarm Panel",
			Type:   "Safety.FirePanel",
			Path:   "N/1/ADMIN/01",
			Status: models.StatusOperational,
		})
		equipment = append(equipment, &models.Equipment{
			ID:     "PA_SYSTEM_01",
			Name:   "Public Address System",
			Type:   "Audio.PA",
			Path:   "N/1/ADMIN/02",
			Status: models.StatusOperational,
		})
		equipment = append(equipment, &models.Equipment{
			ID:     "CAFETERIA_HVAC_01",
			Name:   "Cafeteria HVAC",
			Type:   "HVAC.Zone",
			Path:   "N/1/CAFE/01",
			Status: models.StatusOperational,
		})
		equipment = append(equipment, &models.Equipment{
			ID:     "GYM_HVAC_01",
			Name:   "Gymnasium HVAC",
			Type:   "HVAC.Zone",
			Path:   "N/1/GYM/01",
			Status: models.StatusOperational,
		})
	}

	return equipment
}
