//go:build integration
// +build integration

package services

import (
	"context"
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

type ServicesIntegrationTestSuite struct {
	suite.Suite
	db       *database.PostGISDB
	registry *ServiceRegistry
	ctx      context.Context
}

func (s *ServicesIntegrationTestSuite) SetupSuite() {
	// Setup test database
	config := &database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos_test",
		User:     "test",
		Password: "test",
		SSLMode:  "disable",
		MaxConns: 10,
	}

	s.db = database.NewPostGISDB(*config)
	s.ctx = context.Background()

	err := s.db.Connect(s.ctx)
	s.Require().NoError(err, "Failed to connect to test database")

	err = s.db.InitializeSchema(s.ctx)
	s.Require().NoError(err, "Failed to initialize schema")

	// Initialize service registry
	s.registry = NewServiceRegistry(s.db)
	s.Require().NotNil(s.registry)
}

func (s *ServicesIntegrationTestSuite) TearDownSuite() {
	if s.db != nil {
		s.cleanupTestData()
		s.db.Close()
	}
}

func (s *ServicesIntegrationTestSuite) SetupTest() {
	s.cleanupTestData()
}

func (s *ServicesIntegrationTestSuite) cleanupTestData() {
	queries := []string{
		"DELETE FROM sync_status WHERE entity_id LIKE 'TEST_%'",
		"DELETE FROM equipment WHERE id LIKE 'TEST_%'",
		"DELETE FROM equipment_positions WHERE equipment_id LIKE 'TEST_%'",
		"DELETE FROM buildings WHERE id LIKE 'TEST_%' OR name LIKE 'TEST_%'",
		"DELETE FROM floors WHERE id LIKE 'TEST_%' OR name LIKE 'TEST_%'",
		"DELETE FROM spatial_indexes WHERE object_id LIKE 'TEST_%'",
	}

	for _, q := range queries {
		_, err := s.db.GetDB().ExecContext(s.ctx, q)
		if err != nil {
			s.T().Logf("Warning: cleanup query failed: %v", err)
		}
	}
}

func TestServicesIntegrationSuite(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test suite")
	}
	suite.Run(t, new(ServicesIntegrationTestSuite))
}

// TestBuildingService tests building service operations
func (s *ServicesIntegrationTestSuite) TestBuildingService() {
	buildingService := s.registry.BuildingService

	// Create building
	building := &models.Building{
		ID:          fmt.Sprintf("TEST_%s", uuid.New().String()),
		Name:        "TEST_Building_Service",
		Address:     "456 Service Street",
		Description: "Test building for service layer",
		Metadata: map[string]interface{}{
			"floors": 5,
			"area":   10000,
		},
	}

	err := buildingService.CreateBuilding(s.ctx, building)
	s.Require().NoError(err)

	// Get building
	retrieved, err := buildingService.GetBuilding(s.ctx, building.ID)
	s.Require().NoError(err)
	s.Equal(building.Name, retrieved.Name)
	s.Equal(building.Address, retrieved.Address)

	// Update building
	building.Description = "Updated description"
	err = buildingService.UpdateBuilding(s.ctx, building)
	s.Require().NoError(err)

	// List buildings
	buildings, err := buildingService.ListBuildings(s.ctx, 0, 10)
	s.Require().NoError(err)
	s.Greater(len(buildings), 0)

	// Create floors for building
	for i := 1; i <= 3; i++ {
		floor := &models.Floor{
			ID:         fmt.Sprintf("TEST_FLOOR_%d", i),
			BuildingID: building.ID,
			Name:       fmt.Sprintf("TEST_Floor_%d", i),
			Level:      i,
			Height:     3000,
		}
		err := buildingService.CreateFloor(s.ctx, floor)
		s.Require().NoError(err)
	}

	// Get building with floors
	buildingWithFloors, err := buildingService.GetBuildingWithFloors(s.ctx, building.ID)
	s.Require().NoError(err)
	s.Equal(3, len(buildingWithFloors.Floors))

	// Delete building (should cascade to floors)
	err = buildingService.DeleteBuilding(s.ctx, building.ID)
	s.Require().NoError(err)

	// Verify deletion
	_, err = buildingService.GetBuilding(s.ctx, building.ID)
	s.Error(err)
}

// TestEquipmentService tests equipment service operations
func (s *ServicesIntegrationTestSuite) TestEquipmentService() {
	equipmentService := s.registry.EquipmentService

	// Create multiple equipment items
	equipmentList := []models.Equipment{
		{
			ID:       "TEST_EQ_001",
			Name:     "Test HVAC Unit",
			Type:     "HVAC",
			Status:   "active",
			Metadata: map[string]interface{}{"power": "5kW"},
		},
		{
			ID:       "TEST_EQ_002",
			Name:     "Test Sensor",
			Type:     "sensor",
			Status:   "active",
			Metadata: map[string]interface{}{"range": "10m"},
		},
		{
			ID:       "TEST_EQ_003",
			Name:     "Test Light",
			Type:     "lighting",
			Status:   "inactive",
			Metadata: map[string]interface{}{"watts": 60},
		},
	}

	for _, eq := range equipmentList {
		err := equipmentService.CreateEquipment(s.ctx, &eq)
		s.Require().NoError(err)
	}

	// Get equipment by ID
	retrieved, err := equipmentService.GetEquipment(s.ctx, "TEST_EQ_001")
	s.Require().NoError(err)
	s.Equal("Test HVAC Unit", retrieved.Name)

	// List equipment by type
	hvacEquipment, err := equipmentService.ListEquipmentByType(s.ctx, "HVAC")
	s.Require().NoError(err)
	s.Equal(1, len(hvacEquipment))

	// List equipment by status
	activeEquipment, err := equipmentService.ListEquipmentByStatus(s.ctx, "active")
	s.Require().NoError(err)
	s.Equal(2, len(activeEquipment))

	// Update equipment status
	err = equipmentService.UpdateEquipmentStatus(s.ctx, "TEST_EQ_003", "active")
	s.Require().NoError(err)

	// Batch update equipment
	updates := []models.Equipment{
		{ID: "TEST_EQ_001", Status: "maintenance"},
		{ID: "TEST_EQ_002", Status: "maintenance"},
	}

	err = equipmentService.BatchUpdateEquipment(s.ctx, updates)
	s.Require().NoError(err)

	// Verify batch update
	maintenanceEquipment, err := equipmentService.ListEquipmentByStatus(s.ctx, "maintenance")
	s.Require().NoError(err)
	s.Equal(2, len(maintenanceEquipment))
}

// TestSpatialService tests spatial service operations
func (s *ServicesIntegrationTestSuite) TestSpatialService() {
	spatialService := s.registry.SpatialService
	equipmentService := s.registry.EquipmentService

	// Create equipment with positions
	equipment := []struct {
		id  string
		pos spatial.Point3D
	}{
		{"TEST_SPATIAL_001", spatial.Point3D{X: 0, Y: 0, Z: 0}},
		{"TEST_SPATIAL_002", spatial.Point3D{X: 1000, Y: 0, Z: 0}},
		{"TEST_SPATIAL_003", spatial.Point3D{X: 2000, Y: 0, Z: 0}},
		{"TEST_SPATIAL_004", spatial.Point3D{X: 500, Y: 500, Z: 0}},
		{"TEST_SPATIAL_005", spatial.Point3D{X: 1500, Y: 1500, Z: 0}},
	}

	for _, eq := range equipment {
		// Create equipment
		err := equipmentService.CreateEquipment(s.ctx, &models.Equipment{
			ID:     eq.id,
			Name:   fmt.Sprintf("Spatial Test %s", eq.id),
			Type:   "sensor",
			Status: "active",
		})
		s.Require().NoError(err)

		// Set position
		err = spatialService.UpdateEquipmentPosition(s.ctx, eq.id, eq.pos, spatial.ConfidenceHigh, "test")
		s.Require().NoError(err)
	}

	// Test proximity search
	nearbyEquipment, err := spatialService.FindEquipmentNearPoint(s.ctx, spatial.Point3D{X: 500, Y: 0, Z: 0}, 600)
	s.Require().NoError(err)
	s.Equal(2, len(nearbyEquipment), "Should find 2 equipment within 600mm of (500,0,0)")

	// Test bounding box search
	bbox := spatial.BoundingBox{
		Min: spatial.Point3D{X: -100, Y: -100, Z: -100},
		Max: spatial.Point3D{X: 1100, Y: 600, Z: 100},
	}
	inBox, err := spatialService.FindEquipmentInBoundingBox(s.ctx, bbox)
	s.Require().NoError(err)
	s.Equal(3, len(inBox), "Should find 3 equipment in bounding box")

	// Test path finding
	path, distance, err := spatialService.FindPath(s.ctx, "TEST_SPATIAL_001", "TEST_SPATIAL_005")
	s.Require().NoError(err)
	s.NotEmpty(path)
	s.Greater(distance, 0.0)

	// Test clustering
	clusters, err := spatialService.ClusterEquipment(s.ctx, 1500)
	s.Require().NoError(err)
	s.Greater(len(clusters), 0)
	s.T().Logf("Found %d clusters with radius 1500mm", len(clusters))

	// Test movement history
	newPos := spatial.Point3D{X: 100, Y: 100, Z: 0}
	err = spatialService.UpdateEquipmentPosition(s.ctx, "TEST_SPATIAL_001", newPos, spatial.ConfidenceMedium, "movement")
	s.Require().NoError(err)

	history, err := spatialService.GetEquipmentMovementHistory(s.ctx, "TEST_SPATIAL_001", 10)
	s.Require().NoError(err)
	s.GreaterOrEqual(len(history), 2, "Should have at least 2 position records")
}

// TestSyncService tests synchronization service
func (s *ServicesIntegrationTestSuite) TestSyncService() {
	syncService := s.registry.SyncService

	// Create sync status for multiple entities
	entities := []string{"TEST_SYNC_001", "TEST_SYNC_002", "TEST_SYNC_003"}

	for _, entityID := range entities {
		status := &models.SyncStatus{
			EntityID:   entityID,
			EntityType: "equipment",
			Status:     "pending",
			LastSync:   time.Now().Add(-1 * time.Hour),
		}
		err := syncService.UpdateSyncStatus(s.ctx, status)
		s.Require().NoError(err)
	}

	// Get pending syncs
	pending, err := syncService.GetPendingSyncs(s.ctx, "equipment", 10)
	s.Require().NoError(err)
	s.Equal(3, len(pending))

	// Process sync for one entity
	err = syncService.StartSync(s.ctx, "TEST_SYNC_001", "equipment")
	s.Require().NoError(err)

	// Simulate sync completion
	time.Sleep(100 * time.Millisecond)
	err = syncService.CompleteSync(s.ctx, "TEST_SYNC_001", "equipment", nil)
	s.Require().NoError(err)

	// Simulate sync failure
	err = syncService.StartSync(s.ctx, "TEST_SYNC_002", "equipment")
	s.Require().NoError(err)
	err = syncService.FailSync(s.ctx, "TEST_SYNC_002", "equipment", fmt.Errorf("test error"))
	s.Require().NoError(err)

	// Get sync statistics
	stats, err := syncService.GetSyncStatistics(s.ctx)
	s.Require().NoError(err)
	s.Contains(stats, "equipment")
	s.Equal(1, stats["equipment"]["completed"])
	s.Equal(1, stats["equipment"]["failed"])
	s.Equal(1, stats["equipment"]["pending"])

	// Test batch sync
	err = syncService.BatchSync(s.ctx, entities, "equipment")
	s.Require().NoError(err)

	// Test sync retry with exponential backoff
	for i := 0; i < 3; i++ {
		err = syncService.RetryFailedSyncs(s.ctx, "equipment", i+1)
		s.Require().NoError(err)
		time.Sleep(100 * time.Millisecond)
	}
}

// TestNotificationService tests notification service
func (s *ServicesIntegrationTestSuite) TestNotificationService() {
	notificationService := s.registry.NotificationService

	// Create notifications
	notifications := []models.Notification{
		{
			ID:        uuid.New().String(),
			Type:      "equipment_alert",
			Priority:  "high",
			Title:     "Equipment Failure",
			Message:   "TEST_EQ_001 has stopped responding",
			EntityID:  "TEST_EQ_001",
			CreatedAt: time.Now(),
		},
		{
			ID:        uuid.New().String(),
			Type:      "maintenance",
			Priority:  "medium",
			Title:     "Scheduled Maintenance",
			Message:   "TEST_EQ_002 requires maintenance",
			EntityID:  "TEST_EQ_002",
			CreatedAt: time.Now(),
		},
		{
			ID:        uuid.New().String(),
			Type:      "system",
			Priority:  "low",
			Title:     "System Update",
			Message:   "System will be updated tonight",
			CreatedAt: time.Now(),
		},
	}

	for _, notif := range notifications {
		err := notificationService.CreateNotification(s.ctx, &notif)
		s.Require().NoError(err)
	}

	// Get unread notifications
	unread, err := notificationService.GetUnreadNotifications(s.ctx, 10)
	s.Require().NoError(err)
	s.Equal(3, len(unread))

	// Get notifications by priority
	highPriority, err := notificationService.GetNotificationsByPriority(s.ctx, "high")
	s.Require().NoError(err)
	s.Equal(1, len(highPriority))

	// Mark notification as read
	err = notificationService.MarkAsRead(s.ctx, notifications[0].ID)
	s.Require().NoError(err)

	// Get unread count
	count, err := notificationService.GetUnreadCount(s.ctx)
	s.Require().NoError(err)
	s.Equal(2, count)

	// Batch mark as read
	ids := []string{notifications[1].ID, notifications[2].ID}
	err = notificationService.BatchMarkAsRead(s.ctx, ids)
	s.Require().NoError(err)

	// Test notification aggregation
	for i := 0; i < 5; i++ {
		notif := models.Notification{
			ID:        uuid.New().String(),
			Type:      "equipment_alert",
			Priority:  "high",
			Title:     fmt.Sprintf("Alert %d", i),
			Message:   "Multiple alerts",
			EntityID:  "TEST_EQ_003",
			CreatedAt: time.Now(),
		}
		err := notificationService.CreateNotification(s.ctx, &notif)
		s.Require().NoError(err)
	}

	// Get aggregated notifications
	aggregated, err := notificationService.GetAggregatedNotifications(s.ctx, "TEST_EQ_003", time.Hour)
	s.Require().NoError(err)
	s.Equal(5, len(aggregated))
}

// TestServiceOrchestration tests complex service interactions
func (s *ServicesIntegrationTestSuite) TestServiceOrchestration() {
	// This tests the interaction between multiple services
	buildingService := s.registry.BuildingService
	equipmentService := s.registry.EquipmentService
	spatialService := s.registry.SpatialService
	notificationService := s.registry.NotificationService

	// Create building and floors
	building := &models.Building{
		ID:   "TEST_ORCH_BUILDING",
		Name: "Orchestration Test Building",
	}
	err := buildingService.CreateBuilding(s.ctx, building)
	s.Require().NoError(err)

	floor := &models.Floor{
		ID:         "TEST_ORCH_FLOOR",
		BuildingID: building.ID,
		Name:       "Ground Floor",
		Level:      0,
		Height:     3000,
	}
	err = buildingService.CreateFloor(s.ctx, floor)
	s.Require().NoError(err)

	// Create equipment on floor
	var equipmentIDs []string
	for i := 0; i < 10; i++ {
		eq := models.Equipment{
			ID:      fmt.Sprintf("TEST_ORCH_EQ_%02d", i),
			Name:    fmt.Sprintf("Orchestration Equipment %d", i),
			Type:    "sensor",
			Status:  "active",
			FloorID: &floor.ID,
		}
		err := equipmentService.CreateEquipment(s.ctx, &eq)
		s.Require().NoError(err)
		equipmentIDs = append(equipmentIDs, eq.ID)

		// Set position
		pos := spatial.Point3D{
			X: float64(i%5) * 1000,
			Y: float64(i/5) * 1000,
			Z: 0,
		}
		err = spatialService.UpdateEquipmentPosition(s.ctx, eq.ID, pos, spatial.ConfidenceHigh, "orchestration")
		s.Require().NoError(err)
	}

	// Simulate equipment failure
	failedEquipmentID := equipmentIDs[0]
	err = equipmentService.UpdateEquipmentStatus(s.ctx, failedEquipmentID, "failed")
	s.Require().NoError(err)

	// Create notification for failure
	notification := &models.Notification{
		ID:        uuid.New().String(),
		Type:      "equipment_failure",
		Priority:  "high",
		Title:     "Equipment Failure Detected",
		Message:   fmt.Sprintf("Equipment %s has failed", failedEquipmentID),
		EntityID:  failedEquipmentID,
		CreatedAt: time.Now(),
	}
	err = notificationService.CreateNotification(s.ctx, notification)
	s.Require().NoError(err)

	// Find nearby equipment that might be affected
	failedPos, _, err := spatialService.GetEquipmentPosition(s.ctx, failedEquipmentID)
	s.Require().NoError(err)

	nearbyEquipment, err := spatialService.FindEquipmentNearPoint(s.ctx, failedPos, 1500)
	s.Require().NoError(err)

	// Create notifications for nearby equipment
	for _, nearbyID := range nearbyEquipment {
		if nearbyID != failedEquipmentID {
			notif := &models.Notification{
				ID:        uuid.New().String(),
				Type:      "equipment_warning",
				Priority:  "medium",
				Title:     "Nearby Equipment Failure",
				Message:   fmt.Sprintf("Equipment %s is near failed equipment %s", nearbyID, failedEquipmentID),
				EntityID:  nearbyID,
				CreatedAt: time.Now(),
			}
			err := notificationService.CreateNotification(s.ctx, notif)
			s.Require().NoError(err)
		}
	}

	// Verify orchestration results
	buildingWithDetails, err := buildingService.GetBuildingWithFloors(s.ctx, building.ID)
	s.Require().NoError(err)
	s.Equal(1, len(buildingWithDetails.Floors))

	floorEquipment, err := equipmentService.ListEquipmentByFloor(s.ctx, floor.ID)
	s.Require().NoError(err)
	s.Equal(10, len(floorEquipment))

	notifications, err := notificationService.GetNotificationsByPriority(s.ctx, "high")
	s.Require().NoError(err)
	s.GreaterOrEqual(len(notifications), 1)
}

// TestConcurrentServiceOperations tests services under concurrent load
func (s *ServicesIntegrationTestSuite) TestConcurrentServiceOperations() {
	const numWorkers = 20
	const opsPerWorker = 50

	var wg sync.WaitGroup
	errors := make(chan error, numWorkers*opsPerWorker)

	// Launch workers performing various service operations
	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()

			for op := 0; op < opsPerWorker; op++ {
				switch op % 4 {
				case 0: // Create equipment
					eq := models.Equipment{
						ID:     fmt.Sprintf("TEST_CONC_%d_%d", workerID, op),
						Name:   fmt.Sprintf("Concurrent Equipment %d-%d", workerID, op),
						Type:   "sensor",
						Status: "active",
					}
					if err := s.registry.EquipmentService.CreateEquipment(s.ctx, &eq); err != nil {
						errors <- fmt.Errorf("worker %d: create equipment failed: %w", workerID, err)
					}

				case 1: // Update position
					id := fmt.Sprintf("TEST_CONC_%d_%d", workerID, op-1)
					pos := spatial.Point3D{
						X: float64(workerID * 100),
						Y: float64(op * 100),
						Z: 0,
					}
					_ = s.registry.SpatialService.UpdateEquipmentPosition(s.ctx, id, pos, spatial.ConfidenceMedium, "concurrent")

				case 2: // Create notification
					notif := models.Notification{
						ID:       uuid.New().String(),
						Type:     "test",
						Priority: "low",
						Title:    fmt.Sprintf("Test %d-%d", workerID, op),
						Message:  "Concurrent test notification",
					}
					_ = s.registry.NotificationService.CreateNotification(s.ctx, &notif)

				case 3: // List operations
					_, _ = s.registry.EquipmentService.ListEquipmentByType(s.ctx, "sensor")
				}
			}
		}(w)
	}

	// Wait for completion
	done := make(chan bool)
	go func() {
		wg.Wait()
		close(errors)
		done <- true
	}()

	// Collect errors with timeout
	select {
	case <-done:
		errorCount := 0
		for err := range errors {
			errorCount++
			s.T().Logf("Concurrent operation error: %v", err)
		}
		s.Less(errorCount, numWorkers*5, "Too many errors during concurrent operations")
		s.T().Logf("Completed %d concurrent operations with %d errors", numWorkers*opsPerWorker, errorCount)

	case <-time.After(30 * time.Second):
		s.Fail("Concurrent operations timeout")
	}
}

// TestServiceRecovery tests service error recovery
func (s *ServicesIntegrationTestSuite) TestServiceRecovery() {
	equipmentService := s.registry.EquipmentService

	// Test transaction rollback on error
	eq := models.Equipment{
		ID:     "TEST_RECOVERY",
		Name:   "Recovery Test",
		Type:   "sensor",
		Status: "active",
	}

	err := equipmentService.CreateEquipment(s.ctx, &eq)
	s.Require().NoError(err)

	// Try to create duplicate (should fail)
	err = equipmentService.CreateEquipment(s.ctx, &eq)
	s.Error(err)

	// Original should still exist and be queryable
	retrieved, err := equipmentService.GetEquipment(s.ctx, eq.ID)
	s.Require().NoError(err)
	s.Equal(eq.Name, retrieved.Name)

	// Test service retry mechanism
	retryCount := 0
	maxRetries := 3

	operation := func() error {
		retryCount++
		if retryCount < maxRetries {
			return fmt.Errorf("temporary error")
		}
		return nil
	}

	err = s.registry.RetryOperation(operation, maxRetries, 100*time.Millisecond)
	s.NoError(err)
	s.Equal(maxRetries, retryCount)
}