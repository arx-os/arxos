package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/pkg/models/building"
)

// DataService provides data access for TUI components
type DataService struct {
	db domain.Database
}

// NewDataService creates a new data service instance
func NewDataService(db domain.Database) *DataService {
	return &DataService{
		db: db,
	}
}

// BuildingData represents comprehensive building data for TUI
type BuildingData struct {
	Building  *building.BuildingModel
	Floors    []*building.Floor
	Equipment []*building.Equipment
	Alerts    []Alert
	Metrics   *BuildingMetrics
}

// Alert represents a building alert
type Alert struct {
	ID       string    `json:"id"`
	Severity string    `json:"severity"`
	Message  string    `json:"message"`
	Time     time.Time `json:"time"`
	Source   string    `json:"source"`
}

// BuildingMetrics represents building performance metrics
type BuildingMetrics struct {
	Uptime         float64       `json:"uptime"`
	EnergyPerSqM   float64       `json:"energy_per_sq_m"`
	ResponseTime   time.Duration `json:"response_time"`
	Coverage       float64       `json:"coverage"`
	TotalEquipment int           `json:"total_equipment"`
	Operational    int           `json:"operational"`
	Maintenance    int           `json:"maintenance"`
	Offline        int           `json:"offline"`
	LastUpdate     time.Time     `json:"last_update"`
}

// GetBuildingData retrieves comprehensive building data for the TUI
func (ds *DataService) GetBuildingData(ctx context.Context, buildingID string) (*BuildingData, error) {
	if buildingID == "" {
		buildingID = "default" // Use default building if none specified
	}

	buildingData := &BuildingData{}

	// Get building information
	building, err := ds.getBuilding(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get building: %w", err)
	}
	buildingData.Building = building

	// Get floors
	floors, err := ds.getFloors(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get floors: %w", err)
	}
	buildingData.Floors = floors

	// Get equipment
	equipment, err := ds.getEquipment(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}
	buildingData.Equipment = equipment

	// Get alerts
	alerts, err := ds.getAlerts(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get alerts: %w", err)
	}
	buildingData.Alerts = alerts

	// Calculate metrics
	metrics, err := ds.calculateMetrics(ctx, buildingID, equipment)
	if err != nil {
		return nil, fmt.Errorf("failed to calculate metrics: %w", err)
	}
	buildingData.Metrics = metrics

	return buildingData, nil
}

// getBuilding retrieves building information
func (ds *DataService) getBuilding(ctx context.Context, buildingID string) (*building.BuildingModel, error) {
	// For now, return a mock building until we have real data
	// TODO: Implement actual database query
	return &building.BuildingModel{
		ID:          buildingID,
		Name:        "ArxOS Demo Building",
		Address:     "123 Tech Street, Innovation City",
		Description: "Demo building for ArxOS TUI testing",
		ImportedAt:  time.Now().Add(-30 * 24 * time.Hour),
		UpdatedAt:   time.Now(),
	}, nil
}

// getFloors retrieves floor information for a building
func (ds *DataService) getFloors(ctx context.Context, buildingID string) ([]*building.Floor, error) {
	// For now, return mock floors
	// TODO: Implement actual database query using PostGIS
	floors := []*building.Floor{
		{
			ID:          fmt.Sprintf("%s-floor-1", buildingID),
			Number:      1,
			Name:        "Ground Floor",
			Description: "Main entrance and lobby",
			Height:      3.5,
			Elevation:   0.0,
			Confidence:  building.ConfidenceMedium,
		},
		{
			ID:          fmt.Sprintf("%s-floor-2", buildingID),
			Number:      2,
			Name:        "Second Floor",
			Description: "Office spaces",
			Height:      3.0,
			Elevation:   3.5,
			Confidence:  building.ConfidenceMedium,
		},
		{
			ID:          fmt.Sprintf("%s-floor-3", buildingID),
			Number:      3,
			Name:        "Third Floor",
			Description: "Meeting rooms and executive offices",
			Height:      3.0,
			Elevation:   6.5,
			Confidence:  building.ConfidenceMedium,
		},
	}

	return floors, nil
}

// getEquipment retrieves equipment information for a building
func (ds *DataService) getEquipment(ctx context.Context, buildingID string) ([]*building.Equipment, error) {
	// For now, return mock equipment data
	// TODO: Implement actual database query using PostGIS spatial data
	equipment := []*building.Equipment{
		{
			ID:       "HVAC-001",
			Name:     "Main HVAC Unit",
			Type:     "HVAC",
			Status:   "operational",
			RoomID:   fmt.Sprintf("%s-floor-1", buildingID),
			Position: &building.Point3D{X: 10.5, Y: 15.2, Z: 2.0},
		},
		{
			ID:       "ELEC-001",
			Name:     "Main Electrical Panel",
			Type:     "Electrical",
			Status:   "operational",
			RoomID:   fmt.Sprintf("%s-floor-1", buildingID),
			Position: &building.Point3D{X: 5.0, Y: 8.0, Z: 1.5},
		},
		{
			ID:       "LIGHT-001",
			Name:     "Conference Room Light",
			Type:     "Lighting",
			Status:   "maintenance",
			RoomID:   fmt.Sprintf("%s-floor-2", buildingID),
			Position: &building.Point3D{X: 12.0, Y: 10.0, Z: 2.8},
		},
		{
			ID:       "OUTLET-001",
			Name:     "Power Outlet A1",
			Type:     "Electrical",
			Status:   "operational",
			RoomID:   fmt.Sprintf("%s-floor-2", buildingID),
			Position: &building.Point3D{X: 8.5, Y: 6.0, Z: 1.2},
		},
		{
			ID:       "FIRE-001",
			Name:     "Fire Alarm Panel",
			Type:     "Fire Safety",
			Status:   "operational",
			RoomID:   fmt.Sprintf("%s-floor-1", buildingID),
			Position: &building.Point3D{X: 15.0, Y: 12.0, Z: 2.5},
		},
	}

	return equipment, nil
}

// getAlerts retrieves active alerts for a building
func (ds *DataService) getAlerts(ctx context.Context, buildingID string) ([]Alert, error) {
	// For now, return mock alerts
	// TODO: Implement actual database query
	alerts := []Alert{
		{
			ID:       "ALERT-001",
			Severity: "warning",
			Message:  "HVAC-001: Maintenance due in 7 days",
			Time:     time.Now().Add(-2 * time.Hour),
			Source:   "maintenance_scheduler",
		},
		{
			ID:       "ALERT-002",
			Severity: "info",
			Message:  "LIGHT-001: Scheduled maintenance completed",
			Time:     time.Now().Add(-1 * time.Hour),
			Source:   "maintenance_scheduler",
		},
	}

	return alerts, nil
}

// calculateMetrics calculates building performance metrics
func (ds *DataService) calculateMetrics(ctx context.Context, buildingID string, equipment []*building.Equipment) (*BuildingMetrics, error) {
	// Calculate metrics from equipment data
	totalEquipment := len(equipment)
	operational := 0
	maintenance := 0
	offline := 0

	for _, eq := range equipment {
		switch eq.Status {
		case "operational":
			operational++
		case "maintenance":
			maintenance++
		case "offline":
			offline++
		}
	}

	// Calculate coverage based on equipment distribution
	coverage := 92.3 // TODO: Calculate based on spatial coverage

	metrics := &BuildingMetrics{
		Uptime:         98.5,
		EnergyPerSqM:   125.0,
		ResponseTime:   4 * time.Minute,
		Coverage:       coverage,
		TotalEquipment: totalEquipment,
		Operational:    operational,
		Maintenance:    maintenance,
		Offline:        offline,
		LastUpdate:     time.Now(),
	}

	return metrics, nil
}

// GetEquipmentByFloor retrieves equipment for a specific floor
func (ds *DataService) GetEquipmentByFloor(ctx context.Context, buildingID string, floorNumber int) ([]*building.Equipment, error) {
	allEquipment, err := ds.getEquipment(ctx, buildingID)
	if err != nil {
		return nil, err
	}

	var floorEquipment []*building.Equipment
	floorID := fmt.Sprintf("%s-floor-%d", buildingID, floorNumber)

	for _, eq := range allEquipment {
		if eq.RoomID == floorID {
			floorEquipment = append(floorEquipment, eq)
		}
	}

	return floorEquipment, nil
}

// GetSpatialData retrieves spatial data for visualization
func (ds *DataService) GetSpatialData(ctx context.Context, buildingID string) (*SpatialData, error) {
	// TODO: Implement PostGIS spatial queries
	// This would query the equipment_positions table for 3D coordinates
	// and return spatial data for ASCII floor plan rendering

	spatialData := &SpatialData{
		BuildingID: buildingID,
		Floors: []FloorSpatialData{
			{
				FloorNumber: 1,
				Bounds:      Bounds{X: 0, Y: 0, Width: 20, Height: 15},
				Equipment: []EquipmentSpatialData{
					{ID: "HVAC-001", X: 10.5, Y: 15.2, Type: "HVAC"},
					{ID: "ELEC-001", X: 5.0, Y: 8.0, Type: "Electrical"},
				},
			},
		},
	}

	return spatialData, nil
}

// SpatialData represents spatial information for visualization
type SpatialData struct {
	BuildingID string             `json:"building_id"`
	Floors     []FloorSpatialData `json:"floors"`
}

// FloorSpatialData represents spatial data for a floor
type FloorSpatialData struct {
	FloorNumber int                    `json:"floor_number"`
	Bounds      Bounds                 `json:"bounds"`
	Equipment   []EquipmentSpatialData `json:"equipment"`
}

// EquipmentSpatialData represents spatial data for equipment
type EquipmentSpatialData struct {
	ID   string  `json:"id"`
	X    float64 `json:"x"`
	Y    float64 `json:"y"`
	Type string  `json:"type"`
}

// Bounds represents spatial bounds
type Bounds struct {
	X      float64 `json:"x"`
	Y      float64 `json:"y"`
	Width  float64 `json:"width"`
	Height float64 `json:"height"`
}

// GetDB returns the database instance
func (ds *DataService) GetDB() domain.Database {
	return ds.db
}

// Close closes the data service
func (ds *DataService) Close() error {
	if ds.db != nil {
		return ds.db.Close()
	}
	return nil
}
