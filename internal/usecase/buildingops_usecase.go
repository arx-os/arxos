package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// BuildingOpsUseCase implements building operations business logic following Clean Architecture
type BuildingOpsUseCase struct {
	buildingRepo  domain.BuildingRepository
	equipmentRepo domain.EquipmentRepository
	logger        domain.Logger
}

// NewBuildingOpsUseCase creates a new BuildingOpsUseCase
func NewBuildingOpsUseCase(buildingRepo domain.BuildingRepository, equipmentRepo domain.EquipmentRepository, logger domain.Logger) *BuildingOpsUseCase {
	return &BuildingOpsUseCase{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		logger:        logger,
	}
}

// ControlEquipment controls building equipment (HVAC, lighting, etc.)
func (uc *BuildingOpsUseCase) ControlEquipment(ctx context.Context, req *domain.ControlEquipmentRequest) error {
	uc.logger.Info("Controlling equipment", "equipment_id", req.EquipmentID, "action", req.Action)

	// Get equipment
	equipment, err := uc.equipmentRepo.GetByID(ctx, req.EquipmentID)
	if err != nil {
		return fmt.Errorf("equipment not found: %w", err)
	}

	// Validate control action
	if err := uc.validateControlAction(equipment, req.Action); err != nil {
		return fmt.Errorf("invalid control action: %w", err)
	}

	// Apply control action (business logic)
	if err := uc.applyControlAction(ctx, equipment, req.Action); err != nil {
		return fmt.Errorf("failed to control equipment: %w", err)
	}

	uc.logger.Info("Equipment controlled successfully", "equipment_id", req.EquipmentID)
	return nil
}

// SetBuildingMode sets the operating mode for a building or zone
func (uc *BuildingOpsUseCase) SetBuildingMode(ctx context.Context, req *domain.SetBuildingModeRequest) error {
	uc.logger.Info("Setting building mode", "building_id", req.BuildingID, "mode", req.Mode)

	// Get building
	_, err := uc.buildingRepo.GetByID(ctx, req.BuildingID)
	if err != nil {
		return fmt.Errorf("building not found: %w", err)
	}

	// Get all equipment in building
	equipment, err := uc.equipmentRepo.GetByBuilding(ctx, req.BuildingID)
	if err != nil {
		return fmt.Errorf("failed to get building equipment: %w", err)
	}

	// Apply mode to all equipment
	for _, eq := range equipment {
		if err := uc.applyBuildingMode(eq, req.Mode); err != nil {
			uc.logger.Warn("Failed to apply mode to equipment", "equipment_id", eq.ID, "error", err)
			continue
		}
	}

	uc.logger.Info("Building mode set successfully", "building_id", req.BuildingID)
	return nil
}

// MonitorBuildingHealth monitors the health of building systems
func (uc *BuildingOpsUseCase) MonitorBuildingHealth(ctx context.Context, buildingID string) (*domain.BuildingHealthReport, error) {
	uc.logger.Info("Monitoring building health", "building_id", buildingID)

	// Get building
	building, err := uc.buildingRepo.GetByID(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("building not found: %w", err)
	}

	// Get equipment
	equipment, err := uc.equipmentRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get building equipment: %w", err)
	}

	// Generate health report
	report := &domain.BuildingHealthReport{
		BuildingID:      buildingID,
		BuildingName:    building.Name,
		GeneratedAt:     time.Now(),
		EquipmentHealth: make(map[string]string),
		OverallHealth:   "healthy",
	}

	// Check equipment health
	failedCount := 0
	for _, eq := range equipment {
		health := uc.assessEquipmentHealth(eq)
		report.EquipmentHealth[eq.ID] = health
		if health == "failed" {
			failedCount++
		}
	}

	// Determine overall health
	if failedCount > 0 {
		report.OverallHealth = "degraded"
		if failedCount > len(equipment)/2 {
			report.OverallHealth = "critical"
		}
	}

	uc.logger.Info("Building health report generated", "building_id", buildingID, "overall_health", report.OverallHealth)
	return report, nil
}

// Private helper methods

func (uc *BuildingOpsUseCase) validateControlAction(equipment *domain.Equipment, action *domain.ControlAction) error {
	// Validate that the action is appropriate for the equipment type
	switch equipment.Type {
	case "hvac":
		return uc.validateHVACAction(action)
	case "lighting":
		return uc.validateLightingAction(action)
	case "security":
		return uc.validateSecurityAction(action)
	default:
		return fmt.Errorf("unsupported equipment type: %s", equipment.Type)
	}
}

func (uc *BuildingOpsUseCase) validateHVACAction(action *domain.ControlAction) error {
	validActions := []string{"on", "off", "heat", "cool", "fan", "auto"}
	for _, valid := range validActions {
		if action.Command == valid {
			return nil
		}
	}
	return fmt.Errorf("invalid HVAC action: %s", action.Command)
}

func (uc *BuildingOpsUseCase) validateLightingAction(action *domain.ControlAction) error {
	validActions := []string{"on", "off", "dim", "brighten"}
	for _, valid := range validActions {
		if action.Command == valid {
			return nil
		}
	}
	return fmt.Errorf("invalid lighting action: %s", action.Command)
}

func (uc *BuildingOpsUseCase) validateSecurityAction(action *domain.ControlAction) error {
	validActions := []string{"arm", "disarm", "lock", "unlock"}
	for _, valid := range validActions {
		if action.Command == valid {
			return nil
		}
	}
	return fmt.Errorf("invalid security action: %s", action.Command)
}

func (uc *BuildingOpsUseCase) applyControlAction(ctx context.Context, equipment *domain.Equipment, action *domain.ControlAction) error {
	// This would interface with hardware control systems
	// For now, just update the equipment status
	equipment.Status = fmt.Sprintf("controlled_%s", action.Command)
	equipment.UpdatedAt = time.Now()

	return uc.equipmentRepo.Update(ctx, equipment)
}

func (uc *BuildingOpsUseCase) applyBuildingMode(equipment *domain.Equipment, mode string) error {
	// Apply building mode to equipment
	// This is simplified - in reality, different equipment types would respond differently to modes
	equipment.Status = fmt.Sprintf("mode_%s", mode)
	equipment.UpdatedAt = time.Now()

	return nil
}

func (uc *BuildingOpsUseCase) assessEquipmentHealth(equipment *domain.Equipment) string {
	// Simple health assessment based on status
	switch equipment.Status {
	case "operational", "controlled_on", "mode_active":
		return "healthy"
	case "maintenance", "controlled_off":
		return "warning"
	case "failed", "error":
		return "failed"
	default:
		return "unknown"
	}
}
