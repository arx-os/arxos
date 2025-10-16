package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/pkg/models/building"
)

// DataService provides spatial data access for TUI components
// Follows Clean Architecture by using repositories instead of raw DB queries
type DataService struct {
	buildingRepo  domain.BuildingRepository
	equipmentRepo domain.EquipmentRepository
	floorRepo     domain.FloorRepository
	roomRepo      domain.RoomRepository
}

// NewDataService creates a new data service instance
func NewDataService(buildingRepo domain.BuildingRepository, equipmentRepo domain.EquipmentRepository, floorRepo domain.FloorRepository, roomRepo domain.RoomRepository) *DataService {
	return &DataService{
		buildingRepo:  buildingRepo,
		equipmentRepo: equipmentRepo,
		floorRepo:     floorRepo,
		roomRepo:      roomRepo,
	}
}

// BuildingData represents comprehensive building data for TUI visualization
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

// BuildingMetrics represents building performance metrics with spatial coverage
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

	// Get building information using spatial queries
	building, err := ds.getBuilding(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get building: %w", err)
	}
	buildingData.Building = building

	// Get floors with spatial bounds
	floors, err := ds.getFloors(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get floors: %w", err)
	}
	buildingData.Floors = floors

	// Get equipment with positions using PostGIS spatial functions
	equipment, err := ds.getEquipment(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}
	buildingData.Equipment = equipment

	// Get alerts with spatial context
	alerts, err := ds.getAlerts(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get alerts: %w", err)
	}
	buildingData.Alerts = alerts

	// Calculate metrics including spatial coverage
	metrics, err := ds.calculateSpatialMetrics(ctx, buildingID, equipment)
	if err != nil {
		return nil, fmt.Errorf("failed to calculate spatial metrics: %w", err)
	}
	buildingData.Metrics = metrics

	return buildingData, nil
}

// getBuilding retrieves building information using repository
func (ds *DataService) getBuilding(ctx context.Context, buildingID string) (*building.BuildingModel, error) {
	// Use repository to get building data
	bldg, err := ds.buildingRepo.GetByID(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get building: %w", err)
	}

	// Convert domain.Building to building.BuildingModel for TUI
	return &building.BuildingModel{
		ID:          bldg.ID.String(),
		Name:        bldg.Name,
		Address:     bldg.Address,
		Description: "", // Could add description field to domain.Building
		ImportedAt:  bldg.CreatedAt,
		UpdatedAt:   bldg.UpdatedAt,
	}, nil
}

// getFloors retrieves floor information using repository
func (ds *DataService) getFloors(ctx context.Context, buildingID string) ([]*building.Floor, error) {
	// Use repository to get floors
	domainFloors, err := ds.floorRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get floors: %w", err)
	}

	// Convert domain.Floor to building.Floor for TUI
	var floors []*building.Floor
	for _, domainFloor := range domainFloors {
		// Get equipment count for this floor to determine confidence
		floorEquipment, _ := ds.floorRepo.GetEquipment(ctx, domainFloor.ID.String())
		equipCount := len(floorEquipment)

		// Determine confidence based on data quality
		confidence := building.ConfidenceLow
		if equipCount > 10 {
			confidence = building.ConfidenceHigh
		} else if equipCount > 0 {
			confidence = building.ConfidenceMedium
		}

		floors = append(floors, &building.Floor{
			ID:          domainFloor.ID.String(),
			Number:      domainFloor.Level,
			Name:        domainFloor.Name,
			Description: "Floor from database", // Could add description to domain.Floor
			Height:      3.0,                   // Default height - could add to domain.Floor
			Elevation:   float64(domainFloor.Level) * 3.0,
			Confidence:  confidence,
		})
	}

	return floors, nil
}

// getEquipment retrieves equipment information using repository
func (ds *DataService) getEquipment(ctx context.Context, buildingID string) ([]*building.Equipment, error) {
	// Use repository to get equipment
	domainEquipment, err := ds.equipmentRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get equipment: %w", err)
	}

	// Convert domain.Equipment to building.Equipment for TUI
	var equipment []*building.Equipment
	for _, domainEq := range domainEquipment {
		// Convert location to Point3D if available
		var position *building.Point3D
		if domainEq.Location != nil {
			position = &building.Point3D{
				X: domainEq.Location.X,
				Y: domainEq.Location.Y,
				Z: domainEq.Location.Z,
			}
		}

		equipment = append(equipment, &building.Equipment{
			ID:       domainEq.ID.String(),
			Name:     domainEq.Name,
			Type:     domainEq.Type,
			Status:   domainEq.Status,
			RoomID:   domainEq.RoomID.String(),
			Position: position,
		})
	}

	return equipment, nil
}

// getAlerts retrieves alerts based on equipment status
func (ds *DataService) getAlerts(ctx context.Context, buildingID string) ([]Alert, error) {
	// Get equipment to check for alert conditions
	equipment, err := ds.equipmentRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		// If we can't get equipment, return empty alerts instead of erroring
		return []Alert{}, nil
	}

	var alerts []Alert

	// Generate alerts based on equipment status
	for _, eq := range equipment {
		switch eq.Status {
		case "failed":
			alerts = append(alerts, Alert{
				ID:       fmt.Sprintf("ALERT-%s", eq.ID.String()[:8]),
				Severity: "error",
				Message:  fmt.Sprintf("%s: Equipment failed - immediate attention required", eq.Name),
				Time:     time.Now(),
				Source:   "equipment_monitor",
			})
		case "maintenance":
			alerts = append(alerts, Alert{
				ID:       fmt.Sprintf("ALERT-%s", eq.ID.String()[:8]),
				Severity: "warning",
				Message:  fmt.Sprintf("%s: In maintenance mode", eq.Name),
				Time:     time.Now(),
				Source:   "maintenance_scheduler",
			})
		}
	}

	// If no alerts, return a friendly info message
	if len(alerts) == 0 {
		alerts = append(alerts, Alert{
			ID:       "ALERT-INFO",
			Severity: "info",
			Message:  "All systems operational",
			Time:     time.Now(),
			Source:   "system_monitor",
		})
	}

	return alerts, nil
}

// calculateSpatialMetrics calculates building performance metrics from real data
func (ds *DataService) calculateSpatialMetrics(ctx context.Context, buildingID string, equipment []*building.Equipment) (*BuildingMetrics, error) {
	// Calculate metrics from actual equipment data
	totalEquipment := len(equipment)
	operational := 0
	maintenance := 0
	offline := 0
	withLocation := 0

	for _, eq := range equipment {
		switch eq.Status {
		case "operational":
			operational++
		case "maintenance":
			maintenance++
		case "offline":
			offline++
		}

		// Count equipment with location data for coverage calculation
		if eq.Position != nil {
			withLocation++
		}
	}

	// Calculate spatial coverage based on equipment with location data
	spatialCoverage := 0.0
	if totalEquipment > 0 {
		spatialCoverage = float64(withLocation) / float64(totalEquipment) * 100.0
	}

	// Calculate operational percentage
	uptime := 0.0
	if totalEquipment > 0 {
		uptime = float64(operational) / float64(totalEquipment) * 100.0
	}

	metrics := &BuildingMetrics{
		Uptime:         uptime,
		EnergyPerSqM:   0.0,             // NOTE: Energy via BAS point integration
		ResponseTime:   1 * time.Minute, // NOTE: Response time via audit logs
		Coverage:       spatialCoverage,
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
	// Get all floors for the building to find the matching floor
	floors, err := ds.floorRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get floors: %w", err)
	}

	// Find the floor with matching level
	var targetFloorID string
	for _, floor := range floors {
		if floor.Level == floorNumber {
			targetFloorID = floor.ID.String()
			break
		}
	}

	if targetFloorID == "" {
		return []*building.Equipment{}, nil // No floor found, return empty
	}

	// Get equipment for this floor
	domainEquipment, err := ds.floorRepo.GetEquipment(ctx, targetFloorID)
	if err != nil {
		return nil, fmt.Errorf("failed to get floor equipment: %w", err)
	}

	// Convert to TUI equipment format
	var equipment []*building.Equipment
	for _, domainEq := range domainEquipment {
		var position *building.Point3D
		if domainEq.Location != nil {
			position = &building.Point3D{
				X: domainEq.Location.X,
				Y: domainEq.Location.Y,
				Z: domainEq.Location.Z,
			}
		}

		equipment = append(equipment, &building.Equipment{
			ID:       domainEq.ID.String(),
			Name:     domainEq.Name,
			Type:     domainEq.Type,
			Status:   domainEq.Status,
			RoomID:   domainEq.RoomID.String(),
			Position: position,
		})
	}

	return equipment, nil
}

// GetSpatialData retrieves spatial data for ASCII floor plan visualization
func (ds *DataService) GetSpatialData(ctx context.Context, buildingID string) (*SpatialData, error) {
	// Get floors and equipment for the building
	floors, err := ds.floorRepo.GetByBuilding(ctx, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to get floors: %w", err)
	}

	spatialData := &SpatialData{
		BuildingID: buildingID,
		Floors:     []FloorSpatialData{},
	}

	// Build spatial data for each floor
	for _, floor := range floors {
		// Get rooms for this floor
		floorRooms, err := ds.roomRepo.GetByFloor(ctx, floor.ID.String())
		if err != nil {
			// Log error but continue - rooms are optional for visualization
			fmt.Printf("Warning: Failed to get rooms for floor %s: %v\n", floor.ID.String(), err)
		}

		// Get equipment for this floor
		floorEquipment, err := ds.floorRepo.GetEquipment(ctx, floor.ID.String())
		if err != nil {
			continue // Skip floors we can't get equipment for
		}

		// Calculate bounds from room and equipment positions
		minX, minY, maxX, maxY := 0.0, 0.0, 20.0, 15.0 // Defaults
		hasData := false

		// First, try to get bounds from rooms (more accurate)
		if len(floorRooms) > 0 {
			hasData = true
			firstRoom := floorRooms[0]
			if firstRoom.Location != nil {
				minX = firstRoom.Location.X - firstRoom.Width/2
				minY = firstRoom.Location.Y - firstRoom.Height/2
				maxX = firstRoom.Location.X + firstRoom.Width/2
				maxY = firstRoom.Location.Y + firstRoom.Height/2
			}

			// Expand bounds to include all rooms
			for _, room := range floorRooms {
				if room.Location != nil {
					roomMinX := room.Location.X - room.Width/2
					roomMinY := room.Location.Y - room.Height/2
					roomMaxX := room.Location.X + room.Width/2
					roomMaxY := room.Location.Y + room.Height/2

					if roomMinX < minX {
						minX = roomMinX
					}
					if roomMinY < minY {
						minY = roomMinY
					}
					if roomMaxX > maxX {
						maxX = roomMaxX
					}
					if roomMaxY > maxY {
						maxY = roomMaxY
					}
				}
			}
		}

		// If no room data, fall back to equipment positions
		if !hasData && len(floorEquipment) > 0 {
			hasData = true
			minX, minY = floorEquipment[0].Location.X, floorEquipment[0].Location.Y
			maxX, maxY = minX, minY

			for _, eq := range floorEquipment {
				if eq.Location == nil {
					continue
				}
				if eq.Location.X < minX {
					minX = eq.Location.X
				}
				if eq.Location.Y < minY {
					minY = eq.Location.Y
				}
				if eq.Location.X > maxX {
					maxX = eq.Location.X
				}
				if eq.Location.Y > maxY {
					maxY = eq.Location.Y
				}
			}
		}

		// Build room spatial data
		var roomData []RoomSpatialData
		for _, room := range floorRooms {
			if room.Location != nil {
				roomData = append(roomData, RoomSpatialData{
					ID:     room.ID.String(),
					Name:   room.Name,
					Number: room.Number,
					X:      room.Location.X,
					Y:      room.Location.Y,
					Width:  room.Width,
					Height: room.Height,
					Area:   room.Width * room.Height, // Calculate area
				})
			}
		}

		// Build equipment spatial data
		var equipmentData []EquipmentSpatialData
		for _, eq := range floorEquipment {
			if eq.Location != nil {
				equipmentData = append(equipmentData, EquipmentSpatialData{
					ID:   eq.ID.String(),
					X:    eq.Location.X,
					Y:    eq.Location.Y,
					Type: eq.Type,
				})
			}
		}

		spatialData.Floors = append(spatialData.Floors, FloorSpatialData{
			FloorNumber: floor.Level,
			Bounds: Bounds{
				X:      minX,
				Y:      minY,
				Width:  maxX - minX,
				Height: maxY - minY,
			},
			Rooms:     roomData,
			Equipment: equipmentData,
		})
	}

	return spatialData, nil
}

// SpatialData represents spatial information for TUI visualization
type SpatialData struct {
	BuildingID string             `json:"building_id"`
	Floors     []FloorSpatialData `json:"floors"`
}

// FloorSpatialData represents spatial data for a floor
type FloorSpatialData struct {
	FloorNumber int                    `json:"floor_number"`
	Bounds      Bounds                 `json:"bounds"`
	Rooms       []RoomSpatialData      `json:"rooms"`
	Equipment   []EquipmentSpatialData `json:"equipment"`
}

// RoomSpatialData represents spatial data for a room
type RoomSpatialData struct {
	ID     string  `json:"id"`
	Name   string  `json:"name"`
	Number string  `json:"number"`
	X      float64 `json:"x"`      // Center X coordinate
	Y      float64 `json:"y"`      // Center Y coordinate
	Width  float64 `json:"width"`  // Room width in meters
	Height float64 `json:"height"` // Room height in meters
	Area   float64 `json:"area"`   // Room area in square meters
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

// Close closes the data service (repositories don't need explicit closing)
func (ds *DataService) Close() error {
	// Repositories are stateless and don't need closing
	return nil
}
