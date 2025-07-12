package cmms

import (
	"testing"
	"time"

	"arx-cmms/pkg/models"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

func setupTestDB(t *testing.T) *gorm.DB {
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if err != nil {
		t.Fatalf("Failed to connect to test database: %v", err)
	}

	// Auto-migrate the test database
	err = db.AutoMigrate(&models.CMMSConnection{}, &models.CMMSMapping{}, &models.CMMSSyncLog{})
	if err != nil {
		t.Fatalf("Failed to migrate test database: %v", err)
	}

	return db
}

func TestNewClient(t *testing.T) {
	db := setupTestDB(t)
	client := NewClient(db)

	if client == nil {
		t.Error("Expected client to be created, got nil")
	}

	if client.db == nil {
		t.Error("Expected database connection to be set, got nil")
	}
}

func TestCreateConnection(t *testing.T) {
	db := setupTestDB(t)
	client := NewClient(db)

	conn := &models.CMMSConnection{
		Name:     "Test CMMS",
		Type:     "test",
		BaseURL:  "http://localhost",
		IsActive: true,
	}

	err := client.CreateConnection(conn)
	if err != nil {
		t.Errorf("Failed to create connection: %v", err)
	}

	if conn.ID == 0 {
		t.Error("Expected connection ID to be set after creation")
	}

	if conn.CreatedAt.IsZero() {
		t.Error("Expected created_at to be set")
	}
}

func TestGetConnection(t *testing.T) {
	db := setupTestDB(t)
	client := NewClient(db)

	// Create a test connection
	conn := &models.CMMSConnection{
		Name:     "Test CMMS",
		Type:     "test",
		BaseURL:  "http://localhost",
		IsActive: true,
	}
	client.CreateConnection(conn)

	// Retrieve the connection
	retrieved, err := client.GetConnection(conn.ID)
	if err != nil {
		t.Errorf("Failed to get connection: %v", err)
	}

	if retrieved.ID != conn.ID {
		t.Errorf("Expected connection ID %d, got %d", conn.ID, retrieved.ID)
	}

	if retrieved.Name != conn.Name {
		t.Errorf("Expected connection name %s, got %s", conn.Name, retrieved.Name)
	}
}

func TestListConnections(t *testing.T) {
	db := setupTestDB(t)
	client := NewClient(db)

	// Create test connections
	conn1 := &models.CMMSConnection{
		Name:     "Test CMMS 1",
		Type:     "test",
		BaseURL:  "http://localhost1",
		IsActive: true,
	}
	conn2 := &models.CMMSConnection{
		Name:     "Test CMMS 2",
		Type:     "test",
		BaseURL:  "http://localhost2",
		IsActive: false,
	}

	client.CreateConnection(conn1)
	client.CreateConnection(conn2)

	// List connections
	connections, err := client.ListConnections()
	if err != nil {
		t.Errorf("Failed to list connections: %v", err)
	}

	if len(connections) != 2 {
		t.Errorf("Expected 2 connections, got %d", len(connections))
	}
}

func TestUpdateConnection(t *testing.T) {
	db := setupTestDB(t)
	client := NewClient(db)

	// Create a test connection
	conn := &models.CMMSConnection{
		Name:     "Test CMMS",
		Type:     "test",
		BaseURL:  "http://localhost",
		IsActive: true,
	}
	client.CreateConnection(conn)

	// Update the connection
	conn.Name = "Updated CMMS"
	conn.IsActive = false

	err := client.UpdateConnection(conn)
	if err != nil {
		t.Errorf("Failed to update connection: %v", err)
	}

	// Verify the update
	retrieved, err := client.GetConnection(conn.ID)
	if err != nil {
		t.Errorf("Failed to get updated connection: %v", err)
	}

	if retrieved.Name != "Updated CMMS" {
		t.Errorf("Expected updated name 'Updated CMMS', got %s", retrieved.Name)
	}

	if retrieved.IsActive {
		t.Error("Expected connection to be inactive after update")
	}
}

func TestDeleteConnection(t *testing.T) {
	db := setupTestDB(t)
	client := NewClient(db)

	// Create a test connection
	conn := &models.CMMSConnection{
		Name:     "Test CMMS",
		Type:     "test",
		BaseURL:  "http://localhost",
		IsActive: true,
	}
	client.CreateConnection(conn)

	// Delete the connection
	err := client.DeleteConnection(conn.ID)
	if err != nil {
		t.Errorf("Failed to delete connection: %v", err)
	}

	// Verify deletion
	_, err = client.GetConnection(conn.ID)
	if err == nil {
		t.Error("Expected error when getting deleted connection")
	}
}

func TestCreateMapping(t *testing.T) {
	db := setupTestDB(t)
	client := NewClient(db)

	// Create a test connection
	conn := &models.CMMSConnection{
		Name:     "Test CMMS",
		Type:     "test",
		BaseURL:  "http://localhost",
		IsActive: true,
	}
	client.CreateConnection(conn)

	// Create a mapping
	mapping := &models.CMMSMapping{
		CMMSConnectionID: conn.ID,
		ArxosField:       "asset_id",
		CMMSField:        "cmms_asset_id",
		DataType:         "string",
		IsRequired:       true,
	}

	err := client.CreateMapping(mapping)
	if err != nil {
		t.Errorf("Failed to create mapping: %v", err)
	}

	if mapping.ID == 0 {
		t.Error("Expected mapping ID to be set after creation")
	}
}

func TestGetMappings(t *testing.T) {
	db := setupTestDB(t)
	client := NewClient(db)

	// Create a test connection
	conn := &models.CMMSConnection{
		Name:     "Test CMMS",
		Type:     "test",
		BaseURL:  "http://localhost",
		IsActive: true,
	}
	client.CreateConnection(conn)

	// Create test mappings
	mapping1 := &models.CMMSMapping{
		CMMSConnectionID: conn.ID,
		ArxosField:       "asset_id",
		CMMSField:        "cmms_asset_id",
		DataType:         "string",
	}
	mapping2 := &models.CMMSMapping{
		CMMSConnectionID: conn.ID,
		ArxosField:       "asset_name",
		CMMSField:        "cmms_asset_name",
		DataType:         "string",
	}

	client.CreateMapping(mapping1)
	client.CreateMapping(mapping2)

	// Get mappings
	mappings, err := client.GetMappings(conn.ID)
	if err != nil {
		t.Errorf("Failed to get mappings: %v", err)
	}

	if len(mappings) != 2 {
		t.Errorf("Expected 2 mappings, got %d", len(mappings))
	}
}

func TestGetSyncLogs(t *testing.T) {
	db := setupTestDB(t)
	client := NewClient(db)

	// Create a test connection
	conn := &models.CMMSConnection{
		Name:     "Test CMMS",
		Type:     "test",
		BaseURL:  "http://localhost",
		IsActive: true,
	}
	client.CreateConnection(conn)

	// Create test sync logs
	log1 := &models.CMMSSyncLog{
		CMMSConnectionID: conn.ID,
		SyncType:         "schedules",
		Status:           "success",
		RecordsProcessed: 10,
		RecordsCreated:   5,
		RecordsUpdated:   3,
		RecordsFailed:    2,
		StartedAt:        time.Now(),
		CompletedAt:      time.Now(),
	}
	log2 := &models.CMMSSyncLog{
		CMMSConnectionID: conn.ID,
		SyncType:         "work_orders",
		Status:           "success",
		RecordsProcessed: 5,
		RecordsCreated:   2,
		RecordsUpdated:   1,
		RecordsFailed:    0,
		StartedAt:        time.Now(),
		CompletedAt:      time.Now(),
	}

	db.Create(log1)
	db.Create(log2)

	// Get sync logs
	logs, err := client.GetSyncLogs(conn.ID, 10)
	if err != nil {
		t.Errorf("Failed to get sync logs: %v", err)
	}

	if len(logs) != 2 {
		t.Errorf("Expected 2 sync logs, got %d", len(logs))
	}
} 