package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// AnalyticsUseCase implements analytics business logic following Clean Architecture
type AnalyticsUseCase struct {
	buildingRepo  domain.BuildingRepository
	equipmentRepo domain.EquipmentRepository
	logger        domain.Logger
}

// NewAnalyticsUseCase creates a new AnalyticsUseCase
func NewAnalyticsUseCase(buildingRepo domain.BuildingRepository, equipmentRepo domain.EquipmentRepository, logger domain.Logger) *AnalyticsUseCase {
	return &AnalyticsUseCase{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		logger:        logger,
	}
}

// GetBuildingAnalytics retrieves analytics for a specific building
func (uc *AnalyticsUseCase) GetBuildingAnalytics(ctx context.Context, buildingID string) (*domain.BuildingAnalytics, error) {
	uc.logger.Info("Getting building analytics", "building_id", buildingID)

	if buildingID == "" {
		return nil, fmt.Errorf("building ID is required")
	}

	// Verify building exists
	building, err := uc.buildingRepo.GetByID(ctx, buildingID)
	if err != nil {
		uc.logger.Error("Failed to get building for analytics", "building_id", buildingID, "error", err)
		return nil, fmt.Errorf("building not found: %w", err)
	}

	// Get equipment for the building
	equipment, err := uc.equipmentRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		uc.logger.Error("Failed to get equipment for analytics", "building_id", buildingID, "error", err)
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	// Calculate analytics
	analytics := &domain.BuildingAnalytics{
		BuildingID:           buildingID,
		BuildingName:         building.Name,
		TotalEquipment:       len(equipment),
		OperationalEquipment: 0,
		MaintenanceEquipment: 0,
		FailedEquipment:      0,
		GeneratedAt:          time.Now(),
	}

	// Count equipment by status
	for _, eq := range equipment {
		switch eq.Status {
		case "operational":
			analytics.OperationalEquipment++
		case "maintenance":
			analytics.MaintenanceEquipment++
		case "failed":
			analytics.FailedEquipment++
		}
	}

	uc.logger.Info("Building analytics generated", "building_id", buildingID)
	return analytics, nil
}

// GetSystemAnalytics retrieves system-wide analytics
func (uc *AnalyticsUseCase) GetSystemAnalytics(ctx context.Context) (*domain.SystemAnalytics, error) {
	uc.logger.Info("Getting system analytics")

	// Get all buildings
	buildings, err := uc.buildingRepo.List(ctx, &domain.BuildingFilter{Limit: 1000})
	if err != nil {
		uc.logger.Error("Failed to get buildings for system analytics", "error", err)
		return nil, fmt.Errorf("failed to get buildings: %w", err)
	}

	// Get all equipment
	equipment, err := uc.equipmentRepo.List(ctx, &domain.EquipmentFilter{Limit: 10000})
	if err != nil {
		uc.logger.Error("Failed to get equipment for system analytics", "error", err)
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	// Calculate system analytics
	analytics := &domain.SystemAnalytics{
		TotalBuildings:       len(buildings),
		TotalEquipment:       len(equipment),
		OperationalEquipment: 0,
		MaintenanceEquipment: 0,
		FailedEquipment:      0,
		GeneratedAt:          time.Now(),
	}

	// Count equipment by status
	for _, eq := range equipment {
		switch eq.Status {
		case "operational":
			analytics.OperationalEquipment++
		case "maintenance":
			analytics.MaintenanceEquipment++
		case "failed":
			analytics.FailedEquipment++
		}
	}

	uc.logger.Info("System analytics generated")
	return analytics, nil
}

// GetEquipmentAnalytics retrieves analytics for equipment
func (uc *AnalyticsUseCase) GetEquipmentAnalytics(ctx context.Context, filter *domain.EquipmentFilter) (*domain.EquipmentAnalytics, error) {
	uc.logger.Info("Getting equipment analytics", "filter", filter)

	// Get equipment based on filter
	equipment, err := uc.equipmentRepo.List(ctx, filter)
	if err != nil {
		uc.logger.Error("Failed to get equipment for analytics", "error", err)
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	// Calculate equipment analytics
	analytics := &domain.EquipmentAnalytics{
		TotalEquipment: len(equipment),
		ByType:         make(map[string]int),
		ByStatus:       make(map[string]int),
		GeneratedAt:    time.Now(),
	}

	// Count equipment by type and status
	for _, eq := range equipment {
		analytics.ByType[eq.Type]++
		analytics.ByStatus[eq.Status]++
	}

	uc.logger.Info("Equipment analytics generated", "total", len(equipment))
	return analytics, nil
}
