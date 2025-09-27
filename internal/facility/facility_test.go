package facility

import (
	"fmt"
	"testing"
	"time"
)

func TestFacilityManager(t *testing.T) {
	fm := NewFacilityManager()

	// Test building creation
	building := &Building{
		ID:           "bldg-001",
		Name:         "Test Building",
		Address:      "123 Test St",
		City:         "Test City",
		State:        "TS",
		ZipCode:      "12345",
		Country:      "USA",
		BuildingType: "Office",
		Floors:       5,
		TotalArea:    50000.0,
		YearBuilt:    2020,
		Status:       BuildingStatusActive,
	}

	err := fm.CreateBuilding(building)
	if err != nil {
		t.Fatalf("Failed to create building: %v", err)
	}

	// Test building retrieval
	retrieved, err := fm.GetBuilding("bldg-001")
	if err != nil {
		t.Fatalf("Failed to get building: %v", err)
	}
	if retrieved.Name != "Test Building" {
		t.Errorf("Expected building name 'Test Building', got '%s'", retrieved.Name)
	}

	// Test space creation
	space := &Space{
		ID:         "space-001",
		BuildingID: "bldg-001",
		Name:       "Test Office",
		SpaceType:  "Office",
		Floor:      1,
		Area:       1000.0,
		Capacity:   10,
		Status:     SpaceStatusActive,
	}

	err = fm.CreateSpace(space)
	if err != nil {
		t.Fatalf("Failed to create space: %v", err)
	}

	// Test asset creation
	asset := &Asset{
		ID:           "asset-001",
		BuildingID:   "bldg-001",
		SpaceID:      "space-001",
		Name:         "Test HVAC Unit",
		AssetType:    "HVAC",
		Manufacturer: "Test Corp",
		Model:        "TC-1000",
		SerialNumber: "SN123456",
		InstallDate:  time.Now(),
		Status:       AssetStatusActive,
	}

	err = fm.CreateAsset(asset)
	if err != nil {
		t.Fatalf("Failed to create asset: %v", err)
	}

	// Test listing
	buildings := fm.ListBuildings()
	if len(buildings) != 1 {
		t.Errorf("Expected 1 building, got %d", len(buildings))
	}

	spaces := fm.ListSpaces()
	if len(spaces) != 1 {
		t.Errorf("Expected 1 space, got %d", len(spaces))
	}

	assets := fm.ListAssets()
	if len(assets) != 1 {
		t.Errorf("Expected 1 asset, got %d", len(assets))
	}

	// Test building update
	updates := map[string]interface{}{
		"name":   "Updated Building",
		"floors": 6,
	}
	err = fm.UpdateBuilding("bldg-001", updates)
	if err != nil {
		t.Fatalf("Failed to update building: %v", err)
	}

	updated, err := fm.GetBuilding("bldg-001")
	if err != nil {
		t.Fatalf("Failed to get updated building: %v", err)
	}
	if updated.Name != "Updated Building" {
		t.Errorf("Expected updated name 'Updated Building', got '%s'", updated.Name)
	}
	if updated.Floors != 6 {
		t.Errorf("Expected updated floors 6, got %d", updated.Floors)
	}

	// Test deletion
	err = fm.DeleteBuilding("bldg-001")
	if err != nil {
		t.Fatalf("Failed to delete building: %v", err)
	}

	_, err = fm.GetBuilding("bldg-001")
	if err == nil {
		t.Error("Expected error when getting deleted building")
	}
}

func TestWorkOrderManager(t *testing.T) {
	fm := NewFacilityManager()
	wom := NewWorkOrderManager(fm)

	// Test work order creation
	workOrder := &WorkOrder{
		ID:          "wo-001",
		Title:       "Test Work Order",
		Description: "Test work order description",
		Priority:    WorkOrderPriorityHigh,
		Status:      WorkOrderStatusOpen,
		AssetID:     "asset-001",
		SpaceID:     "space-001",
		BuildingID:  "bldg-001",
		CreatedBy:   "test-user",
	}

	err := wom.CreateWorkOrder(workOrder)
	if err != nil {
		t.Fatalf("Failed to create work order: %v", err)
	}

	// Test work order retrieval
	retrieved, err := wom.GetWorkOrder("wo-001")
	if err != nil {
		t.Fatalf("Failed to get work order: %v", err)
	}
	if retrieved.Title != "Test Work Order" {
		t.Errorf("Expected work order title 'Test Work Order', got '%s'", retrieved.Title)
	}

	// Test work order assignment
	err = wom.AssignWorkOrder("wo-001", "tech-001")
	if err != nil {
		t.Fatalf("Failed to assign work order: %v", err)
	}

	assigned, err := wom.GetWorkOrder("wo-001")
	if err != nil {
		t.Fatalf("Failed to get assigned work order: %v", err)
	}
	if assigned.AssignedTo != "tech-001" {
		t.Errorf("Expected assigned to 'tech-001', got '%s'", assigned.AssignedTo)
	}
	if assigned.Status != WorkOrderStatusAssigned {
		t.Errorf("Expected status 'assigned', got '%s'", assigned.Status)
	}

	// Test work order start
	err = wom.StartWorkOrder("wo-001")
	if err != nil {
		t.Fatalf("Failed to start work order: %v", err)
	}

	started, err := wom.GetWorkOrder("wo-001")
	if err != nil {
		t.Fatalf("Failed to get started work order: %v", err)
	}
	if started.Status != WorkOrderStatusInProgress {
		t.Errorf("Expected status 'in_progress', got '%s'", started.Status)
	}
	if started.StartedAt.IsZero() {
		t.Error("Expected StartedAt to be set")
	}

	// Test work order completion
	notes := []string{"Work completed successfully"}
	err = wom.CompleteWorkOrder("wo-001", notes)
	if err != nil {
		t.Fatalf("Failed to complete work order: %v", err)
	}

	completed, err := wom.GetWorkOrder("wo-001")
	if err != nil {
		t.Fatalf("Failed to get completed work order: %v", err)
	}
	if completed.Status != WorkOrderStatusCompleted {
		t.Errorf("Expected status 'completed', got '%s'", completed.Status)
	}
	if completed.CompletedAt.IsZero() {
		t.Error("Expected CompletedAt to be set")
	}
	if len(completed.Notes) != 1 {
		t.Errorf("Expected 1 note, got %d", len(completed.Notes))
	}

	// Test work order cancellation
	workOrder2 := &WorkOrder{
		ID:          "wo-002",
		Title:       "Test Work Order 2",
		Description: "Test work order description 2",
		Priority:    WorkOrderPriorityMedium,
		Status:      WorkOrderStatusOpen,
		AssetID:     "asset-002",
		SpaceID:     "space-002",
		BuildingID:  "bldg-002",
		CreatedBy:   "test-user",
	}

	err = wom.CreateWorkOrder(workOrder2)
	if err != nil {
		t.Fatalf("Failed to create work order 2: %v", err)
	}

	err = wom.CancelWorkOrder("wo-002", "Test cancellation")
	if err != nil {
		t.Fatalf("Failed to cancel work order: %v", err)
	}

	cancelled, err := wom.GetWorkOrder("wo-002")
	if err != nil {
		t.Fatalf("Failed to get cancelled work order: %v", err)
	}
	if cancelled.Status != WorkOrderStatusCancelled {
		t.Errorf("Expected status 'cancelled', got '%s'", cancelled.Status)
	}
	if cancelled.CancelledAt.IsZero() {
		t.Error("Expected CancelledAt to be set")
	}
	if cancelled.CancellationReason != "Test cancellation" {
		t.Errorf("Expected cancellation reason 'Test cancellation', got '%s'", cancelled.CancellationReason)
	}
}

func TestMaintenanceManager(t *testing.T) {
	fm := NewFacilityManager()
	wom := NewWorkOrderManager(fm)
	mm := NewMaintenanceManager(fm, wom)

	// Test maintenance schedule creation
	schedule := &MaintenanceSchedule{
		ID:          "ms-001",
		Name:        "Test Maintenance Schedule",
		Description: "Test maintenance schedule description",
		AssetID:     "asset-001",
		Frequency:   "monthly",
		Interval:    1,
		NextDue:     time.Now().Add(24 * time.Hour),
		Status:      MaintenanceStatusActive,
	}

	err := mm.CreateMaintenanceSchedule(schedule)
	if err != nil {
		t.Fatalf("Failed to create maintenance schedule: %v", err)
	}

	// Test maintenance schedule retrieval
	retrieved, err := mm.GetMaintenanceSchedule("ms-001")
	if err != nil {
		t.Fatalf("Failed to get maintenance schedule: %v", err)
	}
	if retrieved.Name != "Test Maintenance Schedule" {
		t.Errorf("Expected schedule name 'Test Maintenance Schedule', got '%s'", retrieved.Name)
	}

	// Test maintenance execution
	workOrder, err := mm.ExecuteMaintenanceSchedule("ms-001")
	if err != nil {
		t.Fatalf("Failed to execute maintenance schedule: %v", err)
	}
	if workOrder == nil {
		t.Error("Expected work order to be created")
	}
	if workOrder.Title != "Test Maintenance Schedule" {
		t.Errorf("Expected work order title 'Test Maintenance Schedule', got '%s'", workOrder.Title)
	}

	// Test maintenance schedule update
	updates := map[string]interface{}{
		"name":     "Updated Maintenance Schedule",
		"interval": 2,
	}
	err = mm.UpdateMaintenanceSchedule("ms-001", updates)
	if err != nil {
		t.Fatalf("Failed to update maintenance schedule: %v", err)
	}

	updated, err := mm.GetMaintenanceSchedule("ms-001")
	if err != nil {
		t.Fatalf("Failed to get updated maintenance schedule: %v", err)
	}
	if updated.Name != "Updated Maintenance Schedule" {
		t.Errorf("Expected updated name 'Updated Maintenance Schedule', got '%s'", updated.Name)
	}
	if updated.Interval != 2 {
		t.Errorf("Expected updated interval 2, got %d", updated.Interval)
	}

	// Test maintenance schedule deletion
	err = mm.DeleteMaintenanceSchedule("ms-001")
	if err != nil {
		t.Fatalf("Failed to delete maintenance schedule: %v", err)
	}

	_, err = mm.GetMaintenanceSchedule("ms-001")
	if err == nil {
		t.Error("Expected error when getting deleted maintenance schedule")
	}
}

func TestInspectionManager(t *testing.T) {
	fm := NewFacilityManager()
	wom := NewWorkOrderManager(fm)
	im := NewInspectionManager(fm, wom)

	// Test inspection creation
	inspection := &Inspection{
		ID:            "insp-001",
		Name:          "Test Inspection",
		Type:          "Safety",
		AssetID:       "asset-001",
		SpaceID:       "space-001",
		BuildingID:    "bldg-001",
		ScheduledDate: time.Now().Add(24 * time.Hour),
		Status:        InspectionStatusScheduled,
	}

	err := im.CreateInspection(inspection)
	if err != nil {
		t.Fatalf("Failed to create inspection: %v", err)
	}

	// Test inspection retrieval
	retrieved, err := im.GetInspection("insp-001")
	if err != nil {
		t.Fatalf("Failed to get inspection: %v", err)
	}
	if retrieved.Name != "Test Inspection" {
		t.Errorf("Expected inspection name 'Test Inspection', got '%s'", retrieved.Name)
	}

	// Test inspection start
	err = im.StartInspection("insp-001")
	if err != nil {
		t.Fatalf("Failed to start inspection: %v", err)
	}

	started, err := im.GetInspection("insp-001")
	if err != nil {
		t.Fatalf("Failed to get started inspection: %v", err)
	}
	if started.Status != InspectionStatusInProgress {
		t.Errorf("Expected status 'in_progress', got '%s'", started.Status)
	}
	if started.StartedAt.IsZero() {
		t.Error("Expected StartedAt to be set")
	}

	// Test inspection completion
	score := 85.5
	notes := "Inspection completed with minor issues"
	err = im.CompleteInspection("insp-001", score, notes)
	if err != nil {
		t.Fatalf("Failed to complete inspection: %v", err)
	}

	completed, err := im.GetInspection("insp-001")
	if err != nil {
		t.Fatalf("Failed to get completed inspection: %v", err)
	}
	if completed.Status != InspectionStatusCompleted {
		t.Errorf("Expected status 'completed', got '%s'", completed.Status)
	}
	if completed.CompletedAt.IsZero() {
		t.Error("Expected CompletedAt to be set")
	}
	if completed.Score != score {
		t.Errorf("Expected score %.1f, got %.1f", score, completed.Score)
	}
	if completed.Notes != notes {
		t.Errorf("Expected notes '%s', got '%s'", notes, completed.Notes)
	}

	// Test finding creation
	finding := &InspectionFinding{
		ID:           "finding-001",
		InspectionID: "insp-001",
		Title:        "Test Finding",
		Description:  "Test finding description",
		Severity:     FindingSeverityMedium,
		Status:       FindingStatusOpen,
		Category:     "Safety",
	}

	err = im.CreateFinding(finding)
	if err != nil {
		t.Fatalf("Failed to create finding: %v", err)
	}

	// Test finding retrieval
	retrievedFinding, err := im.GetFinding("finding-001")
	if err != nil {
		t.Fatalf("Failed to get finding: %v", err)
	}
	if retrievedFinding.Title != "Test Finding" {
		t.Errorf("Expected finding title 'Test Finding', got '%s'", retrievedFinding.Title)
	}

	// Test finding update
	updates := map[string]interface{}{
		"status":      "resolved",
		"resolution":  "Issue fixed",
		"resolved_at": time.Now(),
	}
	err = im.UpdateFinding("finding-001", updates)
	if err != nil {
		t.Fatalf("Failed to update finding: %v", err)
	}

	updatedFinding, err := im.GetFinding("finding-001")
	if err != nil {
		t.Fatalf("Failed to get updated finding: %v", err)
	}
	if updatedFinding.Status != FindingStatusResolved {
		t.Errorf("Expected status 'resolved', got '%s'", updatedFinding.Status)
	}
	if updatedFinding.Resolution != "Issue fixed" {
		t.Errorf("Expected resolution 'Issue fixed', got '%s'", updatedFinding.Resolution)
	}
}

func TestVendorManager(t *testing.T) {
	fm := NewFacilityManager()
	vm := NewVendorManager(fm)

	// Test vendor creation
	vendor := &Vendor{
		ID:          "vendor-001",
		Name:        "Test Vendor",
		ContactName: "John Doe",
		Email:       "john@testvendor.com",
		Phone:       "555-1234",
		Address:     "123 Vendor St",
		City:        "Vendor City",
		State:       "VS",
		ZipCode:     "54321",
		Country:     "USA",
		Status:      VendorStatusActive,
	}

	err := vm.CreateVendor(vendor)
	if err != nil {
		t.Fatalf("Failed to create vendor: %v", err)
	}

	// Test vendor retrieval
	retrieved, err := vm.GetVendor("vendor-001")
	if err != nil {
		t.Fatalf("Failed to get vendor: %v", err)
	}
	if retrieved.Name != "Test Vendor" {
		t.Errorf("Expected vendor name 'Test Vendor', got '%s'", retrieved.Name)
	}

	// Test contract creation
	contract := &Contract{
		ID:          "contract-001",
		VendorID:    "vendor-001",
		Name:        "Test Contract",
		Description: "Test contract description",
		StartDate:   time.Now(),
		EndDate:     time.Now().Add(365 * 24 * time.Hour),
		Value:       100000.0,
		Status:      ContractStatusActive,
	}

	err = vm.CreateContract(contract)
	if err != nil {
		t.Fatalf("Failed to create contract: %v", err)
	}

	// Test contract retrieval
	retrievedContract, err := vm.GetContract("contract-001")
	if err != nil {
		t.Fatalf("Failed to get contract: %v", err)
	}
	if retrievedContract.Name != "Test Contract" {
		t.Errorf("Expected contract name 'Test Contract', got '%s'", retrievedContract.Name)
	}

	// Test vendor update
	updates := map[string]interface{}{
		"name":         "Updated Vendor",
		"contact_name": "Jane Doe",
	}
	err = vm.UpdateVendor("vendor-001", updates)
	if err != nil {
		t.Fatalf("Failed to update vendor: %v", err)
	}

	updated, err := vm.GetVendor("vendor-001")
	if err != nil {
		t.Fatalf("Failed to get updated vendor: %v", err)
	}
	if updated.Name != "Updated Vendor" {
		t.Errorf("Expected updated name 'Updated Vendor', got '%s'", updated.Name)
	}
	if updated.ContactName != "Jane Doe" {
		t.Errorf("Expected updated contact name 'Jane Doe', got '%s'", updated.ContactName)
	}

	// Test contract update
	contractUpdates := map[string]interface{}{
		"name":  "Updated Contract",
		"value": 150000.0,
	}
	err = vm.UpdateContract("contract-001", contractUpdates)
	if err != nil {
		t.Fatalf("Failed to update contract: %v", err)
	}

	updatedContract, err := vm.GetContract("contract-001")
	if err != nil {
		t.Fatalf("Failed to get updated contract: %v", err)
	}
	if updatedContract.Name != "Updated Contract" {
		t.Errorf("Expected updated contract name 'Updated Contract', got '%s'", updatedContract.Name)
	}
	if updatedContract.Value != 150000.0 {
		t.Errorf("Expected updated value 150000.0, got %.2f", updatedContract.Value)
	}

	// Test vendor deletion
	err = vm.DeleteVendor("vendor-001")
	if err != nil {
		t.Fatalf("Failed to delete vendor: %v", err)
	}

	_, err = vm.GetVendor("vendor-001")
	if err == nil {
		t.Error("Expected error when getting deleted vendor")
	}
}

func TestMetrics(t *testing.T) {
	fm := NewFacilityManager()
	wom := NewWorkOrderManager(fm)
	mm := NewMaintenanceManager(fm, wom)
	im := NewInspectionManager(fm, wom)
	vm := NewVendorManager(fm)

	// Test facility metrics
	facilityMetrics := fm.GetMetrics()
	if facilityMetrics == nil {
		t.Error("Expected facility metrics to be non-nil")
	}

	// Test work order metrics
	workOrderMetrics := wom.GetWorkOrderMetrics()
	if workOrderMetrics == nil {
		t.Error("Expected work order metrics to be non-nil")
	}

	// Test maintenance metrics
	maintenanceMetrics := mm.GetMaintenanceMetrics()
	if maintenanceMetrics == nil {
		t.Error("Expected maintenance metrics to be non-nil")
	}

	// Test inspection metrics
	inspectionMetrics := im.GetInspectionMetrics()
	if inspectionMetrics == nil {
		t.Error("Expected inspection metrics to be non-nil")
	}

	// Test vendor metrics
	vendorMetrics := vm.GetVendorMetrics()
	if vendorMetrics == nil {
		t.Error("Expected vendor metrics to be non-nil")
	}
}

func TestConcurrentOperations(t *testing.T) {
	fm := NewFacilityManager()
	wom := NewWorkOrderManager(fm)

	// Test concurrent building creation
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(id int) {
			building := &Building{
				ID:           fmt.Sprintf("bldg-%d", id),
				Name:         fmt.Sprintf("Building %d", id),
				Address:      "123 Test St",
				City:         "Test City",
				State:        "TS",
				ZipCode:      "12345",
				Country:      "USA",
				BuildingType: "Office",
				Floors:       5,
				TotalArea:    50000.0,
				YearBuilt:    2020,
				Status:       BuildingStatusActive,
			}
			err := fm.CreateBuilding(building)
			if err != nil {
				t.Errorf("Failed to create building %d: %v", id, err)
			}
			done <- true
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}

	// Verify all buildings were created
	buildings := fm.ListBuildings()
	if len(buildings) != 10 {
		t.Errorf("Expected 10 buildings, got %d", len(buildings))
	}

	// Test concurrent work order creation
	done = make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(id int) {
			workOrder := &WorkOrder{
				ID:          fmt.Sprintf("wo-%d", id),
				Title:       fmt.Sprintf("Work Order %d", id),
				Description: fmt.Sprintf("Description %d", id),
				Priority:    WorkOrderPriorityMedium,
				Status:      WorkOrderStatusOpen,
				AssetID:     fmt.Sprintf("asset-%d", id),
				SpaceID:     fmt.Sprintf("space-%d", id),
				BuildingID:  fmt.Sprintf("bldg-%d", id),
				CreatedBy:   "test-user",
			}
			err := wom.CreateWorkOrder(workOrder)
			if err != nil {
				t.Errorf("Failed to create work order %d: %v", id, err)
			}
			done <- true
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}

	// Verify all work orders were created
	workOrders := wom.ListWorkOrders()
	if len(workOrders) != 10 {
		t.Errorf("Expected 10 work orders, got %d", len(workOrders))
	}
}

func TestErrorHandling(t *testing.T) {
	fm := NewFacilityManager()
	wom := NewWorkOrderManager(fm)

	// Test getting non-existent building
	_, err := fm.GetBuilding("non-existent")
	if err == nil {
		t.Error("Expected error when getting non-existent building")
	}

	// Test getting non-existent work order
	_, err = wom.GetWorkOrder("non-existent")
	if err == nil {
		t.Error("Expected error when getting non-existent work order")
	}

	// Test creating building with duplicate ID
	building1 := &Building{
		ID:           "duplicate-id",
		Name:         "Building 1",
		Address:      "123 Test St",
		City:         "Test City",
		State:        "TS",
		ZipCode:      "12345",
		Country:      "USA",
		BuildingType: "Office",
		Floors:       5,
		TotalArea:    50000.0,
		YearBuilt:    2020,
		Status:       BuildingStatusActive,
	}

	building2 := &Building{
		ID:           "duplicate-id",
		Name:         "Building 2",
		Address:      "456 Test St",
		City:         "Test City",
		State:        "TS",
		ZipCode:      "12345",
		Country:      "USA",
		BuildingType: "Office",
		Floors:       5,
		TotalArea:    50000.0,
		YearBuilt:    2020,
		Status:       BuildingStatusActive,
	}

	err = fm.CreateBuilding(building1)
	if err != nil {
		t.Fatalf("Failed to create first building: %v", err)
	}

	err = fm.CreateBuilding(building2)
	if err == nil {
		t.Error("Expected error when creating building with duplicate ID")
	}

	// Test updating non-existent building
	updates := map[string]interface{}{
		"name": "Updated Name",
	}
	err = fm.UpdateBuilding("non-existent", updates)
	if err == nil {
		t.Error("Expected error when updating non-existent building")
	}

	// Test deleting non-existent building
	err = fm.DeleteBuilding("non-existent")
	if err == nil {
		t.Error("Expected error when deleting non-existent building")
	}
}

func TestWorkOrderStatusTransitions(t *testing.T) {
	fm := NewFacilityManager()
	wom := NewWorkOrderManager(fm)

	workOrder := &WorkOrder{
		ID:          "wo-001",
		Title:       "Test Work Order",
		Description: "Test work order description",
		Priority:    WorkOrderPriorityHigh,
		Status:      WorkOrderStatusOpen,
		AssetID:     "asset-001",
		SpaceID:     "space-001",
		BuildingID:  "bldg-001",
		CreatedBy:   "test-user",
	}

	err := wom.CreateWorkOrder(workOrder)
	if err != nil {
		t.Fatalf("Failed to create work order: %v", err)
	}

	// Test invalid status transitions
	err = wom.StartWorkOrder("wo-001")
	if err == nil {
		t.Error("Expected error when starting unassigned work order")
	}

	err = wom.CompleteWorkOrder("wo-001", []string{"test"})
	if err == nil {
		t.Error("Expected error when completing unassigned work order")
	}

	// Test valid status transitions
	err = wom.AssignWorkOrder("wo-001", "tech-001")
	if err != nil {
		t.Fatalf("Failed to assign work order: %v", err)
	}

	err = wom.StartWorkOrder("wo-001")
	if err != nil {
		t.Fatalf("Failed to start work order: %v", err)
	}

	err = wom.CompleteWorkOrder("wo-001", []string{"test"})
	if err != nil {
		t.Fatalf("Failed to complete work order: %v", err)
	}

	// Test invalid transitions from completed state
	err = wom.AssignWorkOrder("wo-001", "tech-002")
	if err == nil {
		t.Error("Expected error when reassigning completed work order")
	}

	err = wom.StartWorkOrder("wo-001")
	if err == nil {
		t.Error("Expected error when starting completed work order")
	}
}

func TestMaintenanceScheduleExecution(t *testing.T) {
	fm := NewFacilityManager()
	wom := NewWorkOrderManager(fm)
	mm := NewMaintenanceManager(fm, wom)

	// Test executing non-existent schedule
	_, err := mm.ExecuteMaintenanceSchedule("non-existent")
	if err == nil {
		t.Error("Expected error when executing non-existent schedule")
	}

	// Test executing inactive schedule
	schedule := &MaintenanceSchedule{
		ID:          "ms-001",
		Name:        "Test Schedule",
		Description: "Test description",
		AssetID:     "asset-001",
		Frequency:   "monthly",
		Interval:    1,
		NextDue:     time.Now().Add(24 * time.Hour),
		Status:      MaintenanceStatusInactive,
	}

	err = mm.CreateMaintenanceSchedule(schedule)
	if err != nil {
		t.Fatalf("Failed to create maintenance schedule: %v", err)
	}

	_, err = mm.ExecuteMaintenanceSchedule("ms-001")
	if err == nil {
		t.Error("Expected error when executing inactive schedule")
	}

	// Test executing overdue schedule
	schedule.Status = MaintenanceStatusActive
	schedule.NextDue = time.Now().Add(-24 * time.Hour) // Overdue
	err = mm.UpdateMaintenanceSchedule("ms-001", map[string]interface{}{
		"status":   MaintenanceStatusActive,
		"next_due": schedule.NextDue,
	})
	if err != nil {
		t.Fatalf("Failed to update maintenance schedule: %v", err)
	}

	workOrder, err := mm.ExecuteMaintenanceSchedule("ms-001")
	if err != nil {
		t.Fatalf("Failed to execute overdue maintenance schedule: %v", err)
	}
	if workOrder == nil {
		t.Error("Expected work order to be created for overdue schedule")
	}
}

func TestInspectionFindingManagement(t *testing.T) {
	fm := NewFacilityManager()
	wom := NewWorkOrderManager(fm)
	im := NewInspectionManager(fm, wom)

	// Test creating finding for non-existent inspection
	finding := &InspectionFinding{
		ID:           "finding-001",
		InspectionID: "non-existent",
		Title:        "Test Finding",
		Description:  "Test description",
		Severity:     FindingSeverityHigh,
		Status:       FindingStatusOpen,
		Category:     "Safety",
	}

	err := im.CreateFinding(finding)
	if err == nil {
		t.Error("Expected error when creating finding for non-existent inspection")
	}

	// Test getting non-existent finding
	_, err = im.GetFinding("non-existent")
	if err == nil {
		t.Error("Expected error when getting non-existent finding")
	}

	// Test updating non-existent finding
	updates := map[string]interface{}{
		"status": "resolved",
	}
	err = im.UpdateFinding("non-existent", updates)
	if err == nil {
		t.Error("Expected error when updating non-existent finding")
	}
}

func TestVendorContractManagement(t *testing.T) {
	fm := NewFacilityManager()
	vm := NewVendorManager(fm)

	// Test creating contract for non-existent vendor
	contract := &Contract{
		ID:          "contract-001",
		VendorID:    "non-existent",
		Name:        "Test Contract",
		Description: "Test description",
		StartDate:   time.Now(),
		EndDate:     time.Now().Add(365 * 24 * time.Hour),
		Value:       100000.0,
		Status:      ContractStatusActive,
	}

	err := vm.CreateContract(contract)
	if err == nil {
		t.Error("Expected error when creating contract for non-existent vendor")
	}

	// Test getting non-existent contract
	_, err = vm.GetContract("non-existent")
	if err == nil {
		t.Error("Expected error when getting non-existent contract")
	}

	// Test updating non-existent contract
	updates := map[string]interface{}{
		"name": "Updated Contract",
	}
	err = vm.UpdateContract("non-existent", updates)
	if err == nil {
		t.Error("Expected error when updating non-existent contract")
	}
}
