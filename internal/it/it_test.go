package it

import (
	"testing"
	"time"
)

func TestITManager(t *testing.T) {
	im := NewITManager()

	// Test manager creation
	if im == nil {
		t.Fatal("Expected IT manager, got nil")
	}

	// Test component managers
	if im.GetAssetManager() == nil {
		t.Fatal("Expected asset manager, got nil")
	}
	if im.GetConfigManager() == nil {
		t.Fatal("Expected config manager, got nil")
	}
	if im.GetInventoryManager() == nil {
		t.Fatal("Expected inventory manager, got nil")
	}
	if im.GetWorkOrderManager() == nil {
		t.Fatal("Expected work order manager, got nil")
	}
}

func TestRoomSetupFromPath(t *testing.T) {
	im := NewITManager()

	// Test valid building path
	roomPath := "/buildings/test-building/floors/1/rooms/classroom-101"
	setup, err := im.CreateRoomSetupFromPath(roomPath, SetupTypeTraditional, "test-user")
	if err != nil {
		t.Fatalf("Failed to create room setup: %v", err)
	}

	if setup.Room.Building != "test-building" {
		t.Errorf("Expected building 'test-building', got '%s'", setup.Room.Building)
	}
	if setup.Room.Floor != "1" {
		t.Errorf("Expected floor '1', got '%s'", setup.Room.Floor)
	}
	if setup.Room.Room != "classroom-101" {
		t.Errorf("Expected room 'classroom-101', got '%s'", setup.Room.Room)
	}
	if setup.SetupType != SetupTypeTraditional {
		t.Errorf("Expected setup type 'traditional', got '%s'", setup.SetupType)
	}
}

func TestPathValidation(t *testing.T) {
	im := NewITManager()

	// Test valid paths
	validPaths := []string{
		"/buildings/building1/floors/1/rooms/room1",
		"/buildings/test-building/floors/ground/rooms/classroom-101",
		"/buildings/main/floors/2/rooms/lab-205",
	}

	for _, path := range validPaths {
		err := im.ValidateBuildingPath(path)
		if err != nil {
			t.Errorf("Expected valid path, got error: %v", err)
		}

		building, floor, room, err := im.GetPathComponents(path)
		if err != nil {
			t.Errorf("Expected to parse path, got error: %v", err)
		}

		if building == "" || floor == "" || room == "" {
			t.Errorf("Expected non-empty components, got building='%s', floor='%s', room='%s'", building, floor, room)
		}
	}

	// Test invalid paths
	invalidPaths := []string{
		"/invalid/path",
		"/buildings/building1",
		"/buildings/building1/floors/1",
		"/buildings/building1/floors/1/rooms",
		"/wrong/building1/floors/1/rooms/room1",
		"buildings/building1/floors/1/rooms/room1", // Missing leading slash
	}

	for _, path := range invalidPaths {
		err := im.ValidateBuildingPath(path)
		if err == nil {
			t.Errorf("Expected invalid path error for '%s', got nil", path)
		}
	}
}

func TestAssetManagement(t *testing.T) {
	im := NewITManager()

	// Create test asset
	asset := &ITAsset{
		Name:         "Test Laptop",
		Type:         AssetTypeLaptop,
		Category:     "Computers",
		Brand:        "Dell",
		Model:        "Latitude 5520",
		SerialNumber: "ABC123",
		AssetTag:     "LAP-001",
		Status:       AssetStatusActive,
		Condition:    AssetConditionGood,
		Location: Location{
			Building: "test-building",
			Floor:    "1",
			Room:     "classroom-101",
		},
		PurchasePrice: 1200.0,
		CurrentValue:  1000.0,
		Supplier:      "Dell",
		Metadata:      make(map[string]interface{}),
	}

	// Create asset
	err := im.assetManager.CreateAsset(asset)
	if err != nil {
		t.Fatalf("Failed to create asset: %v", err)
	}

	// Test getting asset
	retrievedAsset, err := im.assetManager.GetAsset(asset.ID)
	if err != nil {
		t.Fatalf("Failed to get asset: %v", err)
	}

	if retrievedAsset.Name != asset.Name {
		t.Errorf("Expected asset name '%s', got '%s'", asset.Name, retrievedAsset.Name)
	}

	// Test filtering assets
	assets := im.assetManager.GetAssets(AssetFilter{
		Type: AssetTypeLaptop,
	})

	if len(assets) == 0 {
		t.Fatal("Expected to find laptop assets")
	}

	// Test updating asset
	asset.Name = "Updated Laptop"
	err = im.assetManager.UpdateAsset(asset.ID, asset)
	if err != nil {
		t.Fatalf("Failed to update asset: %v", err)
	}

	// Test deleting asset
	err = im.assetManager.DeleteAsset(asset.ID)
	if err != nil {
		t.Fatalf("Failed to delete asset: %v", err)
	}
}

func TestConfigurationManagement(t *testing.T) {
	im := NewITManager()

	// Create test configuration
	config := &Configuration{
		Name:        "Standard Laptop Config",
		Description: "Standard configuration for laptops",
		AssetType:   AssetTypeLaptop,
		Components: []Component{
			{
				Type:     "CPU",
				Brand:    "Intel",
				Model:    "i7-1165G7",
				Quantity: 1,
				Required: true,
			},
			{
				Type:     "RAM",
				Brand:    "Crucial",
				Model:    "16GB DDR4",
				Quantity: 1,
				Required: true,
			},
		},
		Software: []Software{
			{
				Name:     "Windows 11",
				Version:  "22H2",
				License:  "Volume",
				Type:     "os",
				Required: true,
			},
		},
		UserSettings: map[string]interface{}{
			"power_save":  true,
			"auto_update": true,
		},
		IsTemplate: true,
		CreatedBy:  "test-user",
	}

	// Create configuration
	err := im.configManager.CreateConfiguration(config)
	if err != nil {
		t.Fatalf("Failed to create configuration: %v", err)
	}

	// Test getting configuration
	retrievedConfig, err := im.configManager.GetConfiguration(config.ID)
	if err != nil {
		t.Fatalf("Failed to get configuration: %v", err)
	}

	if retrievedConfig.Name != config.Name {
		t.Errorf("Expected config name '%s', got '%s'", config.Name, retrievedConfig.Name)
	}

	// Test cloning configuration
	roomPath := "/buildings/test-building/floors/1/rooms/classroom-101"
	clone, err := im.CreateConfigurationFromTemplate(config.ID, AssetTypeLaptop, roomPath, "test-user")
	if err != nil {
		t.Fatalf("Failed to create configuration from template: %v", err)
	}

	if clone.IsTemplate {
		t.Error("Expected cloned configuration to not be a template")
	}

	// Test filtering configurations
	configs := im.configManager.GetConfigurations(ConfigFilter{
		AssetType: AssetTypeLaptop,
	})

	if len(configs) == 0 {
		t.Fatal("Expected to find laptop configurations")
	}
}

func TestRoomSetupManagement(t *testing.T) {
	im := NewITManager()

	// Create room setup
	roomPath := "/buildings/test-building/floors/1/rooms/classroom-101"
	setup, err := im.CreateRoomSetupFromPath(roomPath, SetupTypeTraditional, "test-user")
	if err != nil {
		t.Fatalf("Failed to create room setup: %v", err)
	}

	// Test getting room setup
	retrievedSetup, err := im.GetRoomSetupByPath(roomPath)
	if err != nil {
		t.Fatalf("Failed to get room setup: %v", err)
	}

	if retrievedSetup.ID != setup.ID {
		t.Errorf("Expected setup ID '%s', got '%s'", setup.ID, retrievedSetup.ID)
	}

	// Test adding asset to room
	asset := &ITAsset{
		Name:          "Test Projector",
		Type:          AssetTypeProjector,
		Brand:         "Epson",
		Model:         "PowerLite 1781W",
		SerialNumber:  "PROJ123",
		AssetTag:      "PROJ-001",
		Status:        AssetStatusActive,
		Condition:     AssetConditionGood,
		PurchasePrice: 500.0,
		CurrentValue:  400.0,
		Supplier:      "Epson",
		Metadata:      make(map[string]interface{}),
	}

	err = im.assetManager.CreateAsset(asset)
	if err != nil {
		t.Fatalf("Failed to create asset: %v", err)
	}

	position := Position{
		X:         10.0,
		Y:         5.0,
		Z:         8.0,
		Rotation:  0.0,
		MountType: "ceiling",
	}

	err = im.AddAssetToRoom(asset.ID, roomPath, position, true)
	if err != nil {
		t.Fatalf("Failed to add asset to room: %v", err)
	}

	// Test getting assets by room
	assets, err := im.GetAssetsByRoomPath(roomPath)
	if err != nil {
		t.Fatalf("Failed to get assets by room: %v", err)
	}

	if len(assets) == 0 {
		t.Fatal("Expected to find assets in room")
	}

	// Test room summary
	summary, err := im.GetRoomSetupSummary(roomPath)
	if err != nil {
		t.Fatalf("Failed to get room summary: %v", err)
	}

	if summary.TotalAssets == 0 {
		t.Error("Expected room to have assets")
	}

	if summary.SetupType != SetupTypeTraditional {
		t.Errorf("Expected setup type 'traditional', got '%s'", summary.SetupType)
	}
}

func TestWorkOrderManagement(t *testing.T) {
	im := NewITManager()

	// Create work order
	roomPath := "/buildings/test-building/floors/1/rooms/classroom-101"
	workOrder, err := im.CreateWorkOrderForRoom(
		roomPath,
		"Install New Projector",
		"Install and configure new Epson projector",
		WorkOrderTypeInstallation,
		PriorityHigh,
		"teacher@school.edu",
	)
	if err != nil {
		t.Fatalf("Failed to create work order: %v", err)
	}

	if workOrder.Title != "Install New Projector" {
		t.Errorf("Expected title 'Install New Projector', got '%s'", workOrder.Title)
	}

	if workOrder.Priority != PriorityHigh {
		t.Errorf("Expected priority 'high', got '%s'", workOrder.Priority)
	}

	if workOrder.Status != WorkOrderStatusOpen {
		t.Errorf("Expected status 'open', got '%s'", workOrder.Status)
	}

	// Test getting work orders by room
	workOrders, err := im.GetWorkOrdersByRoomPath(roomPath)
	if err != nil {
		t.Fatalf("Failed to get work orders by room: %v", err)
	}

	if len(workOrders) == 0 {
		t.Fatal("Expected to find work orders for room")
	}

	// Test updating work order
	workOrder.Status = WorkOrderStatusInProgress
	workOrder.AssignedTo = "tech@school.edu"
	workOrder.UpdatedAt = time.Now()

	err = im.workOrderManager.UpdateWorkOrder(workOrder.ID, workOrder)
	if err != nil {
		t.Fatalf("Failed to update work order: %v", err)
	}

	// Test filtering work orders
	filteredWorkOrders := im.workOrderManager.GetWorkOrders(WorkOrderFilter{
		Status: WorkOrderStatusInProgress,
	})

	if len(filteredWorkOrders) == 0 {
		t.Fatal("Expected to find in-progress work orders")
	}
}

func TestInventoryManagement(t *testing.T) {
	im := NewITManager()

	// Create test part
	part := &Part{
		Name:           "HDMI Cable",
		Description:    "6ft HDMI cable for projectors",
		PartNumber:     "HDMI-6FT-001",
		Category:       "Cables",
		Brand:          "Amazon Basics",
		Model:          "HDMI-6FT",
		Supplier:       "Amazon",
		UnitPrice:      15.99,
		Quantity:       10,
		MinQuantity:    5,
		MaxQuantity:    20,
		Location:       "Storage Room A",
		CompatibleWith: []string{"projector", "laptop", "tv"},
		Metadata:       make(map[string]interface{}),
	}

	// Create part
	err := im.inventoryManager.CreatePart(part)
	if err != nil {
		t.Fatalf("Failed to create part: %v", err)
	}

	// Test getting part
	retrievedPart, err := im.inventoryManager.GetPart(part.ID)
	if err != nil {
		t.Fatalf("Failed to get part: %v", err)
	}

	if retrievedPart.Name != part.Name {
		t.Errorf("Expected part name '%s', got '%s'", part.Name, retrievedPart.Name)
	}

	// Test filtering parts
	parts := im.inventoryManager.GetParts(PartFilter{
		Category: "Cables",
	})

	if len(parts) == 0 {
		t.Fatal("Expected to find cable parts")
	}

	// Test low stock parts
	lowStockParts := im.inventoryManager.GetLowStockParts()
	if len(lowStockParts) == 0 {
		t.Fatal("Expected to find low stock parts")
	}

	// Test reorder report
	reorderItems := im.inventoryManager.GenerateReorderReport()
	if len(reorderItems) == 0 {
		t.Fatal("Expected to find reorder items")
	}

	// Test part usage
	usage := &PartUsage{
		PartID:      part.ID,
		AssetID:     "asset-123",
		WorkOrderID: "wo-123",
		Quantity:    2,
		Date:        time.Now(),
		UsedBy:      "tech@school.edu",
		Reason:      "Projector installation",
		Cost:        31.98,
		Notes:       "Used for classroom setup",
		Metadata:    make(map[string]interface{}),
	}

	err = im.inventoryManager.RecordPartUsage(usage)
	if err != nil {
		t.Fatalf("Failed to record part usage: %v", err)
	}

	// Check updated quantity
	updatedPart, err := im.inventoryManager.GetPart(part.ID)
	if err != nil {
		t.Fatalf("Failed to get updated part: %v", err)
	}

	expectedQuantity := part.Quantity - usage.Quantity
	if updatedPart.Quantity != expectedQuantity {
		t.Errorf("Expected quantity %d, got %d", expectedQuantity, updatedPart.Quantity)
	}
}

func TestBuildingSummary(t *testing.T) {
	im := NewITManager()

	// Create room setups for building
	roomPaths := []string{
		"/buildings/test-building/floors/1/rooms/classroom-101",
		"/buildings/test-building/floors/1/rooms/classroom-102",
		"/buildings/test-building/floors/2/rooms/lab-201",
	}

	for _, roomPath := range roomPaths {
		_, err := im.CreateRoomSetupFromPath(roomPath, SetupTypeTraditional, "test-user")
		if err != nil {
			t.Fatalf("Failed to create room setup for %s: %v", roomPath, err)
		}
	}

	// Get building summary
	buildingPath := "/buildings/test-building"
	summary, err := im.GetBuildingITSummary(buildingPath)
	if err != nil {
		t.Fatalf("Failed to get building summary: %v", err)
	}

	if summary.TotalRooms != len(roomPaths) {
		t.Errorf("Expected %d rooms, got %d", len(roomPaths), summary.TotalRooms)
	}

	if summary.BuildingPath != buildingPath {
		t.Errorf("Expected building path '%s', got '%s'", buildingPath, summary.BuildingPath)
	}
}

func TestMetrics(t *testing.T) {
	im := NewITManager()

	// Update metrics
	im.UpdateMetrics()

	// Get metrics
	metrics := im.GetMetrics()

	if metrics == nil {
		t.Fatal("Expected metrics, got nil")
	}

	// Test individual component metrics
	assetMetrics := im.assetManager.GetMetrics()
	if assetMetrics == nil {
		t.Fatal("Expected asset metrics, got nil")
	}

	configMetrics := im.configManager.GetMetrics()
	if configMetrics == nil {
		t.Fatal("Expected config metrics, got nil")
	}

	inventoryMetrics := im.inventoryManager.GetInventoryMetrics()
	if inventoryMetrics == nil {
		t.Fatal("Expected inventory metrics, got nil")
	}

	workOrderMetrics := im.workOrderManager.GetWorkOrderMetrics()
	if workOrderMetrics == nil {
		t.Fatal("Expected work order metrics, got nil")
	}
}

func TestAssetTypes(t *testing.T) {
	// Test asset type constants
	expectedTypes := []AssetType{
		AssetTypeComputer,
		AssetTypeLaptop,
		AssetTypeTablet,
		AssetTypeProjector,
		AssetTypeInteractiveBoard,
		AssetTypeDocCamera,
		AssetTypeDockingStation,
		AssetTypePrinter,
		AssetTypeScanner,
		AssetTypeNetworkDevice,
		AssetTypeServer,
		AssetTypeStorage,
		AssetTypeAccessory,
		AssetTypeOther,
	}

	for _, assetType := range expectedTypes {
		if assetType == "" {
			t.Error("Expected non-empty asset type")
		}
	}
}

func TestSetupTypes(t *testing.T) {
	// Test setup type constants
	expectedTypes := []SetupType{
		SetupTypeTraditional,
		SetupTypeInteractive,
		SetupTypeHybrid,
		SetupTypeComputerLab,
		SetupTypeConference,
		SetupTypePresentation,
		SetupTypeMobile,
		SetupTypeCustom,
	}

	for _, setupType := range expectedTypes {
		if setupType == "" {
			t.Error("Expected non-empty setup type")
		}
	}
}

func TestConnectionTypes(t *testing.T) {
	// Test connection type constants
	expectedTypes := []ConnectionType{
		ConnectionTypeHDMI,
		ConnectionTypeVGA,
		ConnectionTypeUSB,
		ConnectionTypeUSB_C,
		ConnectionTypeEthernet,
		ConnectionTypeWireless,
		ConnectionTypeBluetooth,
		ConnectionTypeAudio,
		ConnectionTypePower,
		ConnectionTypeOther,
	}

	for _, connectionType := range expectedTypes {
		if connectionType == "" {
			t.Error("Expected non-empty connection type")
		}
	}
}

func TestWorkOrderTypes(t *testing.T) {
	// Test work order type constants
	expectedTypes := []WorkOrderType{
		WorkOrderTypeInstallation,
		WorkOrderTypeRepair,
		WorkOrderTypeMaintenance,
		WorkOrderTypeUpgrade,
		WorkOrderTypeConfiguration,
		WorkOrderTypeRemoval,
		WorkOrderTypeInspection,
		WorkOrderTypeOther,
	}

	for _, workOrderType := range expectedTypes {
		if workOrderType == "" {
			t.Error("Expected non-empty work order type")
		}
	}
}

func TestPriorityLevels(t *testing.T) {
	// Test priority constants
	expectedPriorities := []Priority{
		PriorityLow,
		PriorityMedium,
		PriorityHigh,
		PriorityCritical,
		PriorityEmergency,
	}

	for _, priority := range expectedPriorities {
		if priority == "" {
			t.Error("Expected non-empty priority")
		}
	}
}

func TestAssetStatuses(t *testing.T) {
	// Test asset status constants
	expectedStatuses := []AssetStatus{
		AssetStatusActive,
		AssetStatusInactive,
		AssetStatusMaintenance,
		AssetStatusRetired,
		AssetStatusLost,
		AssetStatusStolen,
	}

	for _, status := range expectedStatuses {
		if status == "" {
			t.Error("Expected non-empty asset status")
		}
	}
}

func TestAssetConditions(t *testing.T) {
	// Test asset condition constants
	expectedConditions := []AssetCondition{
		AssetConditionExcellent,
		AssetConditionGood,
		AssetConditionFair,
		AssetConditionPoor,
		AssetConditionBroken,
	}

	for _, condition := range expectedConditions {
		if condition == "" {
			t.Error("Expected non-empty asset condition")
		}
	}
}

func TestPartStatuses(t *testing.T) {
	// Test part status constants
	expectedStatuses := []PartStatus{
		PartStatusInStock,
		PartStatusLowStock,
		PartStatusOutOfStock,
		PartStatusDiscontinued,
		PartStatusOnOrder,
	}

	for _, status := range expectedStatuses {
		if status == "" {
			t.Error("Expected non-empty part status")
		}
	}
}

func TestWorkOrderStatuses(t *testing.T) {
	// Test work order status constants
	expectedStatuses := []WorkOrderStatus{
		WorkOrderStatusOpen,
		WorkOrderStatusAssigned,
		WorkOrderStatusInProgress,
		WorkOrderStatusOnHold,
		WorkOrderStatusCompleted,
		WorkOrderStatusCancelled,
		WorkOrderStatusClosed,
	}

	for _, status := range expectedStatuses {
		if status == "" {
			t.Error("Expected non-empty work order status")
		}
	}
}

func TestMaintenanceTypes(t *testing.T) {
	// Test maintenance type constants
	expectedTypes := []MaintenanceType{
		MaintenanceTypePreventive,
		MaintenanceTypeCorrective,
		MaintenanceTypeEmergency,
		MaintenanceTypeUpgrade,
		MaintenanceTypeInspection,
	}

	for _, maintenanceType := range expectedTypes {
		if maintenanceType == "" {
			t.Error("Expected non-empty maintenance type")
		}
	}
}
