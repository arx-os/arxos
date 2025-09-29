package examples

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"

	"github.com/arx-os/arxos/internal/app/di"
	"github.com/arx-os/arxos/internal/domain/analytics"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/equipment"
	"github.com/arx-os/arxos/internal/domain/messaging"
	"github.com/arx-os/arxos/internal/domain/spatial"
	"github.com/arx-os/arxos/internal/domain/workflow"
)

// DIUsageExample demonstrates how to use the dependency injection system
// following Clean Architecture principles and Go best practices
type DIUsageExample struct{}

// NewDIUsageExample creates a new DI usage example
func NewDIUsageExample() *DIUsageExample {
	return &DIUsageExample{}
}

// DemonstrateBasicUsage shows basic dependency injection usage
func (d *DIUsageExample) DemonstrateBasicUsage(ctx context.Context) error {
	// Create configuration
	config := di.DefaultConfig()
	config.Database.Host = "localhost"
	config.Database.Port = 5432
	config.Database.Database = "arxos_dev"

	// Initialize service locator
	locator := di.GetServiceLocator()
	if err := locator.Initialize(ctx, config); err != nil {
		return fmt.Errorf("failed to initialize service locator: %w", err)
	}

	// Use services
	buildingService := locator.GetBuildingService()
	messagingService := locator.GetMessaging()

	// Example: Create a building
	building, err := buildingService.CreateBuilding(ctx, building.CreateBuildingRequest{
		ArxosID:  "ARXOS-001",
		Name:     "Office Building",
		Address:  "123 Main St",
		Rotation: 0.0,
	})
	if err != nil {
		return fmt.Errorf("failed to create building: %w", err)
	}

	// Example: Send notification
	notification := messaging.CreateNotification(
		"user-123",
		"info",
		"Building Created",
		fmt.Sprintf("Building %s has been created successfully", building.Name),
		map[string]interface{}{
			"building_id": building.ID,
			"arxos_id":    building.ArxosID,
		},
	)

	if err := messagingService.SendNotification(ctx, "user-123", notification); err != nil {
		return fmt.Errorf("failed to send notification: %w", err)
	}

	log.Printf("Successfully created building %s and sent notification", building.Name)
	return nil
}

// DemonstrateBuilderPattern shows how to use the service builder pattern
func (d *DIUsageExample) DemonstrateBuilderPattern(ctx context.Context) error {
	// Create configuration
	config := di.DefaultConfig()
	config.Development = true
	config.WebSocket.MaxMessageSize = 1024

	// Use service builder
	factory := di.NewFactory(nil)
	builder := di.NewServiceBuilder(factory, ctx, config)

	// Build services in order
	container, err := builder.
		WithDatabase().
		WithCache().
		WithStorage().
		WithWebSocket().
		WithMessaging().
		WithBuilding().
		WithEquipment().
		WithSpatial().
		WithAnalytics().
		WithWorkflow().
		Build()

	if err != nil {
		return fmt.Errorf("failed to build services: %w", err)
	}

	// Get services from container
	services := container.GetServices()
	webSocketHub := container.GetWebSocketHub()

	log.Printf("Successfully built services: Building=%t, Equipment=%t, Spatial=%t, Analytics=%t, Workflow=%t, Messaging=%t",
		services.Building != nil,
		services.Equipment != nil,
		services.Spatial != nil,
		services.Analytics != nil,
		services.Workflow != nil,
		services.Messaging != nil)
	log.Printf("WebSocket hub stats: %+v", webSocketHub.GetStats())

	return nil
}

// DemonstrateAdvancedUsage shows advanced dependency injection usage
func (d *DIUsageExample) DemonstrateAdvancedUsage(ctx context.Context) error {
	// Create custom configuration
	config := &di.Config{
		Database: di.DatabaseConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_prod",
			Username: "arxos_user",
			Password: "secure_password",
			SSLMode:  "require",
		},
		Cache: di.CacheConfig{
			Host:     "redis-cluster.example.com",
			Port:     6379,
			Password: "redis_password",
			DB:       0,
		},
		Storage: di.StorageConfig{
			Type:      "s3",
			Bucket:    "arxos-storage",
			Region:    "us-west-2",
			AccessKey: "AKIAIOSFODNN7EXAMPLE",
			SecretKey: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
		},
		WebSocket: di.WebSocketConfig{
			ReadBufferSize:  2048,
			WriteBufferSize: 2048,
			PingPeriod:      30,
			PongWait:        60,
			WriteWait:       10,
			MaxMessageSize:  1024,
		},
		Development: false,
	}

	// Initialize with builder
	locator := di.GetServiceLocator()
	if err := locator.InitializeWithBuilder(ctx, config); err != nil {
		return fmt.Errorf("failed to initialize with builder: %w", err)
	}

	// Demonstrate service usage
	services := locator.GetServices()

	// Building operations
	buildingService := services.Building
	building, err := buildingService.CreateBuilding(ctx, building.CreateBuildingRequest{
		ArxosID:  "ARXOS-002",
		Name:     "Warehouse",
		Address:  "456 Industrial Ave",
		Rotation: 0.0,
	})
	if err != nil {
		return fmt.Errorf("failed to create building: %w", err)
	}

	// Equipment operations
	equipmentService := services.Equipment
	equipment, err := equipmentService.CreateEquipment(ctx, equipment.CreateEquipmentRequest{
		Name:     "HVAC Unit 001",
		Type:     "hvac",
		Location: &equipment.Location{X: 10.5, Y: 20.3, Z: 0.0},
		Metadata: map[string]interface{}{
			"manufacturer": "Carrier",
			"model":        "42QHC018",
			"capacity":     "18 tons",
		},
	})
	if err != nil {
		return fmt.Errorf("failed to create equipment: %w", err)
	}

	// Spatial operations
	spatialService := services.Spatial
	nearby, err := spatialService.FindNearby(ctx, spatial.FindNearbyRequest{
		Center:   &spatial.Point{X: 10.5, Y: 20.3, Z: 0.0},
		Radius:   5.0,
		ItemType: "equipment",
		Limit:    10,
	})
	if err != nil {
		return fmt.Errorf("failed to find nearby equipment: %w", err)
	}

	// Analytics operations
	analyticsService := services.Analytics
	energyData, err := analyticsService.GetEnergyConsumption(ctx, analytics.EnergyConsumptionRequest{
		BuildingID: building.ID,
		StartDate:  time.Now().AddDate(0, 0, -30),
		EndDate:    time.Now(),
		Period:     "daily",
	})
	if err != nil {
		return fmt.Errorf("failed to get energy consumption: %w", err)
	}

	// Workflow operations
	workflowService := services.Workflow
	workflow, err := workflowService.CreateWorkflow(ctx, workflow.CreateWorkflowRequest{
		Name:        "Equipment Maintenance",
		Description: "Regular maintenance workflow for HVAC equipment",
		Definition: map[string]interface{}{
			"steps": []map[string]interface{}{
				{"name": "Inspect", "duration": "30m"},
				{"name": "Clean", "duration": "45m"},
				{"name": "Test", "duration": "15m"},
			},
		},
		Status: "active",
	})
	if err != nil {
		return fmt.Errorf("failed to create workflow: %w", err)
	}

	// Messaging operations
	// TODO: This should use domain messaging service, not infrastructure messaging service
	// For now, use placeholder implementation

	// Subscribe to building updates
	// TODO: This should use domain messaging service, not infrastructure messaging service
	// For now, use placeholder implementation
	log.Printf("Subscribing user-123 to building updates for building %s", building.ID.String())

	// Publish building update
	update := &messaging.BuildingUpdate{
		ID:         uuid.New().String(),
		BuildingID: building.ID.String(),
		Type:       "equipment_added",
		Data: map[string]interface{}{
			"equipment_id":   equipment.ID,
			"equipment_name": equipment.Name,
			"equipment_type": equipment.Type,
		},
		Timestamp: time.Now(),
		Source:    "equipment_service",
		Priority:  "normal",
	}

	// TODO: This should use domain messaging service, not infrastructure messaging service
	// For now, use placeholder implementation
	log.Printf("Publishing building update: %+v", update)

	log.Printf("Successfully created building %s with equipment %s", building.Name, equipment.Name)
	log.Printf("Found %d nearby equipment items", len(nearby))
	log.Printf("Energy consumption: %.2f kWh", energyData.TotalConsumption)
	log.Printf("Created workflow %s with %d steps", workflow.Name, len(workflow.Definition["steps"].([]map[string]interface{})))

	return nil
}

// DemonstrateErrorHandling shows proper error handling with dependency injection
func (d *DIUsageExample) DemonstrateErrorHandling(ctx context.Context) error {
	// Create invalid configuration
	config := &di.Config{
		Database: di.DatabaseConfig{
			Host:     "invalid-host",
			Port:     9999,
			Database: "nonexistent",
			Username: "invalid_user",
			Password: "wrong_password",
		},
	}

	// Try to initialize with invalid configuration
	locator := di.GetServiceLocator()
	err := locator.Initialize(ctx, config)
	if err != nil {
		log.Printf("Expected error with invalid configuration: %v", err)
	}

	// Try to use services before initialization
	defer func() {
		if r := recover(); r != nil {
			log.Printf("Expected panic when accessing uninitialized services: %v", r)
		}
	}()

	// This should panic
	_ = locator.GetBuildingService()

	return nil
}

// DemonstrateGracefulShutdown shows how to gracefully shutdown the DI container
func (d *DIUsageExample) DemonstrateGracefulShutdown(ctx context.Context) error {
	// Initialize services
	config := di.DefaultConfig()
	locator := di.GetServiceLocator()

	if err := locator.Initialize(ctx, config); err != nil {
		return fmt.Errorf("failed to initialize: %w", err)
	}

	// Use services
	services := locator.GetServices()
	log.Printf("Services initialized: Building=%t, Equipment=%t, Spatial=%t, Analytics=%t, Workflow=%t, Messaging=%t",
		services.Building != nil,
		services.Equipment != nil,
		services.Spatial != nil,
		services.Analytics != nil,
		services.Workflow != nil,
		services.Messaging != nil)

	// Simulate some work
	time.Sleep(100 * time.Millisecond)

	// Gracefully shutdown
	if err := locator.Close(); err != nil {
		return fmt.Errorf("failed to close services: %w", err)
	}

	log.Println("Services gracefully shutdown")
	return nil
}

// DemonstrateServiceStats shows how to get service statistics
func (d *DIUsageExample) DemonstrateServiceStats(ctx context.Context) error {
	// Initialize services
	config := di.DefaultConfig()
	locator := di.GetServiceLocator()

	if err := locator.Initialize(ctx, config); err != nil {
		return fmt.Errorf("failed to initialize: %w", err)
	}

	// Get service statistics
	stats := locator.GetStats()
	log.Printf("Service statistics: %+v", stats)

	// Get individual service stats
	database := locator.GetDatabase()
	cache := locator.GetCache()
	storage := locator.GetStorage()
	messaging := locator.GetMessaging()
	webSocket := locator.GetWebSocketHub()

	log.Printf("Database stats: %+v", database.GetStats())
	log.Printf("Cache stats: %+v", cache.GetStats())
	log.Printf("Storage stats: %+v", storage.GetStats())
	log.Printf("Messaging stats: %+v", messaging.GetStats())
	log.Printf("WebSocket stats: %+v", webSocket.GetStats())

	return nil
}
