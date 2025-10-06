/**
 * Test Data Builder - Helper for creating test data in integration tests
 */

package helpers

import (
	"context"
	"fmt"
	"math"
	"math/rand"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase"
)

// TestDataBuilder helps create test data for integration tests
type TestDataBuilder struct {
	buildingUC     *usecase.BuildingUseCase
	equipmentUC    *usecase.EquipmentUseCase
	userUC         *usecase.UserUseCase
	organizationUC *usecase.OrganizationUseCase
	componentUC    *usecase.ComponentUseCase
	ifcUC          *usecase.IFCUseCase
}

// NewTestDataBuilder creates a new test data builder
func NewTestDataBuilder(
	buildingUC *usecase.BuildingUseCase,
	equipmentUC *usecase.EquipmentUseCase,
	userUC *usecase.UserUseCase,
	organizationUC *usecase.OrganizationUseCase,
	componentUC *usecase.ComponentUseCase,
	ifcUC *usecase.IFCUseCase,
) *TestDataBuilder {
	return &TestDataBuilder{
		buildingUC:     buildingUC,
		equipmentUC:    equipmentUC,
		userUC:         userUC,
		organizationUC: organizationUC,
		componentUC:    componentUC,
		ifcUC:          ifcUC,
	}
}

// BuildTestOrganization creates a test organization
func (tdb *TestDataBuilder) BuildTestOrganization(ctx context.Context) (*domain.Organization, error) {
	orgReq := &domain.CreateOrganizationRequest{
		Name:        fmt.Sprintf("Test Organization %d", rand.Intn(1000)),
		Description: "Test organization for integration tests",
		Plan:        "premium",
	}

	return tdb.organizationUC.CreateOrganization(ctx, orgReq)
}

// BuildTestUser creates a test user
func (tdb *TestDataBuilder) BuildTestUser(ctx context.Context, orgID string) (*domain.User, error) {
	userReq := &domain.CreateUserRequest{
		Email: fmt.Sprintf("testuser%d@example.com", rand.Intn(1000)),
		Name:  fmt.Sprintf("Test User %d", rand.Intn(1000)),
		Role:  "user",
	}

	return tdb.userUC.CreateUser(ctx, userReq)
}

// BuildTestBuilding creates a test building
func (tdb *TestDataBuilder) BuildTestBuilding(ctx context.Context) (*domain.Building, error) {
	buildingReq := &domain.CreateBuildingRequest{
		Name:    fmt.Sprintf("Test Building %d", rand.Intn(1000)),
		Address: fmt.Sprintf("%d Test Street, Test City", rand.Intn(1000)),
		Coordinates: &domain.Location{
			X: 40.7128 + (rand.Float64()-0.5)*0.1,
			Y: -74.0060 + (rand.Float64()-0.5)*0.1,
			Z: 0,
		},
	}

	return tdb.buildingUC.CreateBuilding(ctx, buildingReq)
}

// BuildTestEquipment creates test equipment for a building
func (tdb *TestDataBuilder) BuildTestEquipment(ctx context.Context, buildingID string) (*domain.Equipment, error) {
	equipmentTypes := []string{"HVAC", "Electrical", "Plumbing", "FireSafety", "Security"}
	// Note: equipmentStatuses and criticalityLevels would be used for status updates
	// but are not part of the initial equipment creation

	equipmentReq := &domain.CreateEquipmentRequest{
		BuildingID: types.FromString(buildingID),
		Name:       fmt.Sprintf("Test Equipment %d", rand.Intn(1000)),
		Type:       equipmentTypes[rand.Intn(len(equipmentTypes))],
		Model:      fmt.Sprintf("Test Model %d", rand.Intn(1000)),
		Location: &domain.Location{
			X: float64(rand.Intn(100)),
			Y: float64(rand.Intn(100)),
			Z: float64(rand.Intn(20)),
		},
		// Note: Status and Criticality are not part of CreateEquipmentRequest
		// They would be set through update operations
	}

	return tdb.equipmentUC.CreateEquipment(ctx, equipmentReq)
}

// BuildTestBuildingsWithEquipment creates multiple buildings with equipment
func (tdb *TestDataBuilder) BuildTestBuildingsWithEquipment(ctx context.Context, count int, equipmentPerBuilding int) ([]*domain.Building, error) {
	var buildings []*domain.Building

	for i := 0; i < count; i++ {
		// Create building
		building, err := tdb.BuildTestBuilding(ctx)
		if err != nil {
			return nil, fmt.Errorf("failed to create building %d: %w", i, err)
		}
		buildings = append(buildings, building)

		// Create equipment for building
		for j := 0; j < equipmentPerBuilding; j++ {
			_, err := tdb.BuildTestEquipment(ctx, building.ID.String())
			if err != nil {
				return nil, fmt.Errorf("failed to create equipment %d for building %d: %w", j, i, err)
			}
		}
	}

	return buildings, nil
}

// BuildTestIFCData creates test IFC data
func (tdb *TestDataBuilder) BuildTestIFCData(ctx context.Context, repositoryID string) (*domain.IFCImportResult, error) {
	// Create mock IFC data (placeholder for future use)
	_ = []byte(fmt.Sprintf(`
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('IFC4'),'2;1');
FILE_NAME('test_building_%d.ifc','%s',('Test User'),('Test Organization'),'Test Software','Test Software Version','Test Identifier');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1=IFCPROJECT('%s','Test Project %d','Test Project Description',$,$,$,$,$,#2);
#2=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,0.01,$,$);
ENDSEC;

END-ISO-10303-21;
`, rand.Intn(1000), time.Now().Format("2006-01-02T15:04:05"), repositoryID, rand.Intn(1000)))

	// Import the IFC data (this would call the actual IFC use case)
	// For now, return a mock successful result
	result := &domain.IFCImportResult{
		Success:            true,
		RepositoryID:       repositoryID,
		ComponentsImported: 50 + rand.Intn(50), // Random between 50-100
		ComponentsSkipped:  rand.Intn(10),      // Random between 0-10
		Errors:             []string{},
		Warnings:           []string{"Some materials could not be resolved"},
		ProcessingTime:     float64(10 + rand.Intn(30)), // Random between 10-40 seconds
		FileName:           fmt.Sprintf("test_building_%d.ifc", rand.Intn(1000)),
		FileSize:           int64(500000 + rand.Intn(500000)), // Random between 0.5-1MB
		ImportDate:         time.Now(),
		IFCVersion:         "IFC4",
		SchemaURL:          "https://standards.buildingsmart.org/IFC/RELEASE/IFC4",
	}

	return result, nil
}

// BuildTestSpatialData creates test spatial data
func (tdb *TestDataBuilder) BuildTestSpatialData(ctx context.Context, equipmentID string) (*domain.SpatialAnchor, error) {
	// Create spatial anchor with realistic test data
	position := &domain.SpatialLocation{
		X: float64(rand.Intn(100)),
		Y: float64(rand.Intn(100)),
		Z: float64(rand.Intn(20)),
	}

	rotation := &domain.Quaternion{
		W: 1.0,
		X: 0,
		Y: 0,
		Z: 0,
	}

	anchor := &domain.SpatialAnchor{
		ID:               fmt.Sprintf("test-anchor-%d", rand.Intn(1000)),
		Position:         position,
		Rotation:         rotation,
		Confidence:       0.8 + rand.Float64()*0.2, // Random between 0.8-1.0
		Timestamp:        time.Now(),
		BuildingID:       "test-building",
		FloorID:          "test-floor",
		RoomID:           "test-room",
		EquipmentID:      equipmentID,
		ValidationStatus: "pending",
		LastUpdated:      time.Now(),
		Platform:         "ARKit",
		Stability:        0.9,
		Range:            10.0, // 10 meters
		Metadata:         map[string]any{"source": "test", "quality": "high"},
	}

	return anchor, nil
}

// BuildTestARData creates test AR data
func (tdb *TestDataBuilder) BuildTestARData(ctx context.Context, equipmentID string) (*domain.EquipmentAROverlay, error) {
	// Create AR overlay with realistic test data
	position := &domain.SpatialLocation{
		X: float64(rand.Intn(100)),
		Y: float64(rand.Intn(100)),
		Z: float64(rand.Intn(20)),
	}

	rotation := &domain.Quaternion{
		W: 1.0,
		X: 0,
		Y: 0,
		Z: 0,
	}

	scale := &domain.SpatialLocation{
		X: 1.0,
		Y: 1.0,
		Z: 1.0,
	}

	arVisibility := domain.ARVisibility{
		IsVisible:           true,
		Distance:            float64(rand.Intn(50)),        // Random distance 0-50 meters
		OcclusionLevel:      float64(rand.Intn(100)) / 100, // Random 0-1
		LightingCondition:   "good",
		Contrast:            0.8 + rand.Float64()*0.2, // Random between 0.8-1.0
		Brightness:          0.7 + rand.Float64()*0.3, // Random between 0.7-1.0
		LastVisibilityCheck: time.Now(),
	}

	metadata := domain.EquipmentARMetadata{
		Name:         fmt.Sprintf("Test AR Equipment %d", rand.Intn(1000)),
		Type:         "HVAC",
		Model:        fmt.Sprintf("AR Model %d", rand.Intn(1000)),
		Manufacturer: "TestAR Corp",
		Criticality:  "medium",
		Color:        "#00ff00",
		Tags:         []string{"equipment", "ar", "test"},
		Attrs:        map[string]any{"test": true, "generated": true},
	}

	overlay := &domain.EquipmentAROverlay{
		EquipmentID:  equipmentID,
		Position:     position,
		Rotation:     rotation,
		Scale:        scale,
		Status:       "operational",
		LastUpdated:  time.Now(),
		ARVisibility: arVisibility,
		ModelType:    "3D",
		ModelPath:    "/models/hvac_unit.glb",
		MaterialPath: "/materials/hvac_material.gltf",
		LOD:          1,
		Metadata:     metadata,
	}

	return overlay, nil
}

// BuildTestNavigationData creates test navigation data
func (tdb *TestDataBuilder) BuildTestNavigationData(ctx context.Context, from, to *domain.SpatialLocation) (*domain.ARNavigationPath, error) {
	// Create waypoints between from and to
	numWaypoints := 5

	waypoints := make([]*domain.SpatialLocation, 0, numWaypoints+1)

	for i := 0; i <= numWaypoints; i++ {
		t := float64(i) / float64(numWaypoints)
		waypoint := &domain.SpatialLocation{
			X: from.X + (to.X-from.X)*t,
			Y: from.Y + (to.Y-from.Y)*t,
			Z: from.Z + (to.Z-from.Z)*t,
		}
		waypoints = append(waypoints, waypoint)
	}

	// Calculate distance
	totalDistance := 0.0
	for i := 0; i < len(waypoints)-1; i++ {
		dx := waypoints[i+1].X - waypoints[i].X
		dy := waypoints[i+1].Y - waypoints[i].Y
		dz := waypoints[i+1].Z - waypoints[i].Z
		totalDistance += math.Sqrt(dx*dx + dy*dy + dz*dz)
	}

	// Create AR instructions for each waypoint
	var instructions []domain.ARInstruction
	for i, waypoint := range waypoints {
		instructionType := "move"
		if i == len(waypoints)-1 {
			instructionType = "stop"
		}

		instructions = append(instructions, domain.ARInstruction{
			ID:                fmt.Sprintf("instruction-%d", i),
			Type:              instructionType,
			Position:          waypoint,
			Description:       fmt.Sprintf("Move to waypoint %d", i+1),
			EstimatedDuration: 5.0, // 5 seconds per instruction
			Priority:          "medium",
			ARVisualization: domain.ARVisualization{
				Type:      "arrow",
				Color:     "#00ff00",
				Size:      1.0,
				Animation: "pulse",
				Opacity:   0.8,
				Intensity: 1.0,
			},
		})
	}

	path := &domain.ARNavigationPath{
		ID:             fmt.Sprintf("nav-path-%d", rand.Intn(1000)),
		Waypoints:      waypoints,
		Distance:       totalDistance,
		EstimatedTime:  totalDistance / 1.4,         // Walking speed in mm/s
		Obstacles:      []*domain.SpatialLocation{}, // No obstacles for simplicity
		ARInstructions: instructions,
		Difficulty:     "easy",
		Accessibility:  true,
		Hazardous:      false,
		CreatedAt:      time.Now(),
	}

	return path, nil
}

// BuildTestPerformanceData creates test performance data
func (tdb *TestDataBuilder) BuildTestPerformanceData(ctx context.Context, sessionID string) (*domain.ARSessionMetrics, error) {
	// Create performance metrics with realistic test data
	startTime := time.Now().Add(-time.Hour)
	endTime := time.Now()

	metrics := &domain.ARSessionMetrics{
		SessionID:                 sessionID,
		StartTime:                 startTime,
		EndTime:                   endTime,
		Duration:                  time.Hour.Seconds(),
		AnchorsDetected:           rand.Intn(100),
		AnchorsCreated:            rand.Intn(50),
		AnchorsUpdated:            rand.Intn(30),
		AnchorsRemoved:            rand.Intn(10),
		EquipmentOverlaysRendered: rand.Intn(200),
		NavigationPathsCalculated: rand.Intn(20),
		ErrorsEncountered:         rand.Intn(5),
		AverageFrameRate:          float64(30 + rand.Intn(30)),     // Random between 30-60 FPS
		AverageTrackingQuality:    float64(80+rand.Intn(20)) / 100, // Random between 0.8-1.0
		BatteryUsage:              float64(20 + rand.Intn(60)),     // Random between 20-80%
		MemoryUsage:               float64(100 + rand.Intn(200)),   // Random between 100-300 MB
		ThermalState:              "normal",                        // Could be randomized: normal, slight, intermediate, critical
	}

	return metrics, nil
}

// CleanupTestData removes all test data
func (tdb *TestDataBuilder) CleanupTestData(ctx context.Context) error {
	// This would clean up all test data
	// Implementation would depend on the specific cleanup requirements
	return nil
}

// Helper function to create random string
func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[rand.Intn(len(charset))]
	}
	return string(b)
}

// Helper function to create random email
func randomEmail() string {
	return fmt.Sprintf("test%s@example.com", randomString(8))
}

// Helper function to create random phone number
func randomPhone() string {
	return fmt.Sprintf("+1-%d-%d-%d", rand.Intn(900)+100, rand.Intn(900)+100, rand.Intn(9000)+1000)
}
