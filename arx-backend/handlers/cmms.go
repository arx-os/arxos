package handlers

import (
	"arx/db"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"time"

	"arx-cmms/pkg/cmms"
	"arx-cmms/pkg/models"

	"github.com/go-chi/chi/v5"
	"golang.org/x/crypto/bcrypt"
)

// Global CMMS client
var cmmsClient *cmms.Client

// InitCMMSClient initializes the CMMS client
func InitCMMSClient() {
	cmmsClient = cmms.NewClient(db.DB)
}

// CMMS Connection Handlers
func GetCMMSConnections(w http.ResponseWriter, r *http.Request) {
	connections, err := cmmsClient.ListConnections()
	if err != nil {
		http.Error(w, "Failed to fetch CMMS connections", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"connections": connections})
}

func GetCMMSConnection(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	idInt, err := strconv.Atoi(id)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	conn, err := cmmsClient.GetConnection(idInt)
	if err != nil {
		http.Error(w, "CMMS connection not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(conn)
}

func CreateCMMSConnection(w http.ResponseWriter, r *http.Request) {
	var conn models.CMMSConnection
	if err := json.NewDecoder(r.Body).Decode(&conn); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if conn.Name == "" || conn.Type == "" || conn.BaseURL == "" {
		http.Error(w, "Name, type, and base_url are required", http.StatusBadRequest)
		return
	}

	// Encrypt password if provided
	if conn.Password != "" {
		hashed, err := bcrypt.GenerateFromPassword([]byte(conn.Password), bcrypt.DefaultCost)
		if err != nil {
			http.Error(w, "Failed to encrypt password", http.StatusInternalServerError)
			return
		}
		conn.Password = string(hashed)
	}

	err := cmmsClient.CreateConnection(&conn)
	if err != nil {
		http.Error(w, "Failed to create CMMS connection", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{"id": conn.ID, "message": "CMMS connection created successfully"})
}

func UpdateCMMSConnection(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	idInt, err := strconv.Atoi(id)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	var conn models.CMMSConnection
	if err := json.NewDecoder(r.Body).Decode(&conn); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	conn.ID = idInt

	// Handle password update
	if conn.Password != "" {
		hashed, err := bcrypt.GenerateFromPassword([]byte(conn.Password), bcrypt.DefaultCost)
		if err != nil {
			http.Error(w, "Failed to encrypt password", http.StatusInternalServerError)
			return
		}
		conn.Password = string(hashed)
	}

	err = cmmsClient.UpdateConnection(&conn)
	if err != nil {
		http.Error(w, "Failed to update CMMS connection", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"message": "CMMS connection updated successfully"})
}

func DeleteCMMSConnection(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	idInt, err := strconv.Atoi(id)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	err = cmmsClient.DeleteConnection(idInt)
	if err != nil {
		http.Error(w, "Failed to delete CMMS connection", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"message": "CMMS connection deleted successfully"})
}

// CMMS Mapping Handlers
func GetCMMSMappings(w http.ResponseWriter, r *http.Request) {
	connectionID := chi.URLParam(r, "connectionId")
	connectionIDInt, err := strconv.Atoi(connectionID)
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}

	mappings, err := cmmsClient.GetMappings(connectionIDInt)
	if err != nil {
		http.Error(w, "Failed to fetch CMMS mappings", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"mappings": mappings})
}

func CreateCMMSMapping(w http.ResponseWriter, r *http.Request) {
	connectionID := chi.URLParam(r, "connectionId")
	connectionIDInt, err := strconv.Atoi(connectionID)
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}

	var mapping models.CMMSMapping
	if err := json.NewDecoder(r.Body).Decode(&mapping); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	mapping.CMMSConnectionID = connectionIDInt

	// Validate required fields
	if mapping.ArxosField == "" || mapping.CMMSField == "" || mapping.DataType == "" {
		http.Error(w, "arxos_field, cmms_field, and data_type are required", http.StatusBadRequest)
		return
	}

	err = cmmsClient.CreateMapping(&mapping)
	if err != nil {
		http.Error(w, "Failed to create CMMS mapping", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{"id": mapping.ID, "message": "CMMS mapping created successfully"})
}

// Maintenance Schedule Handlers
func GetMaintenanceSchedules(w http.ResponseWriter, r *http.Request) {
	assetID := r.URL.Query().Get("asset_id")
	connectionID := r.URL.Query().Get("connection_id")

	query := `
		SELECT ms.id, ms.asset_id, ms.cmms_connection_id, ms.cmms_asset_id, ms.schedule_type,
		       ms.frequency, ms.interval, ms.description, ms.instructions, ms.estimated_hours,
		       ms.priority, ms.is_active, ms.next_due_date, ms.last_completed, ms.created_at, ms.updated_at,
		       cc.name as connection_name, a.asset_type as asset_name
		FROM maintenance_schedules ms
		JOIN cmms_connections cc ON ms.cmms_connection_id = cc.id
		JOIN assets a ON ms.asset_id = a.id
		WHERE 1=1
	`
	args := []interface{}{}
	argCount := 0

	if assetID != "" {
		argCount++
		query += fmt.Sprintf(" AND ms.asset_id = $%d", argCount)
		args = append(args, assetID)
	}

	if connectionID != "" {
		argCount++
		query += fmt.Sprintf(" AND ms.cmms_connection_id = $%d", argCount)
		args = append(args, connectionID)
	}

	query += " ORDER BY ms.next_due_date"

	var schedules []struct {
		ID               int        `json:"id"`
		AssetID          int        `json:"asset_id"`
		CMMSConnectionID int        `json:"cmms_connection_id"`
		CMMSAssetID      string     `json:"cmms_asset_id"`
		ScheduleType     string     `json:"schedule_type"`
		Frequency        string     `json:"frequency"`
		Interval         int        `json:"interval"`
		Description      string     `json:"description"`
		Instructions     string     `json:"instructions"`
		EstimatedHours   float64    `json:"estimated_hours"`
		Priority         string     `json:"priority"`
		IsActive         bool       `json:"is_active"`
		NextDueDate      time.Time  `json:"next_due_date"`
		LastCompleted    *time.Time `json:"last_completed"`
		CreatedAt        time.Time  `json:"created_at"`
		UpdatedAt        time.Time  `json:"updated_at"`
		ConnectionName   string     `json:"connection_name"`
		AssetName        string     `json:"asset_name"`
	}

	err := db.DB.Raw(query, args...).Scan(&schedules).Error
	if err != nil {
		http.Error(w, "Failed to fetch maintenance schedules", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"schedules": schedules})
}

// Work Order Handlers
func GetWorkOrders(w http.ResponseWriter, r *http.Request) {
	assetID := r.URL.Query().Get("asset_id")
	status := r.URL.Query().Get("status")
	connectionID := r.URL.Query().Get("connection_id")

	query := `
		SELECT wo.id, wo.asset_id, wo.cmms_connection_id, wo.cmms_work_order_id, wo.work_order_number,
		       wo.type, wo.status, wo.priority, wo.description, wo.instructions, wo.assigned_to,
		       wo.estimated_hours, wo.actual_hours, wo.cost, wo.parts_used, wo.created_date,
		       wo.scheduled_date, wo.started_date, wo.completed_date, wo.created_at, wo.updated_at,
		       cc.name as connection_name, a.asset_type as asset_name
		FROM work_orders wo
		JOIN cmms_connections cc ON wo.cmms_connection_id = cc.id
		JOIN assets a ON wo.asset_id = a.id
		WHERE 1=1
	`
	args := []interface{}{}
	argCount := 0

	if assetID != "" {
		argCount++
		query += fmt.Sprintf(" AND wo.asset_id = $%d", argCount)
		args = append(args, assetID)
	}

	if status != "" {
		argCount++
		query += fmt.Sprintf(" AND wo.status = $%d", argCount)
		args = append(args, status)
	}

	if connectionID != "" {
		argCount++
		query += fmt.Sprintf(" AND wo.cmms_connection_id = $%d", argCount)
		args = append(args, connectionID)
	}

	query += " ORDER BY wo.scheduled_date DESC"

	var workOrders []struct {
		ID               int        `json:"id"`
		AssetID          int        `json:"asset_id"`
		CMMSConnectionID int        `json:"cmms_connection_id"`
		CMMSWorkOrderID  string     `json:"cmms_work_order_id"`
		WorkOrderNumber  string     `json:"work_order_number"`
		Type             string     `json:"type"`
		Status           string     `json:"status"`
		Priority         string     `json:"priority"`
		Description      string     `json:"description"`
		Instructions     string     `json:"instructions"`
		AssignedTo       string     `json:"assigned_to"`
		EstimatedHours   float64    `json:"estimated_hours"`
		ActualHours      float64    `json:"actual_hours"`
		Cost             float64    `json:"cost"`
		PartsUsed        string     `json:"parts_used"`
		CreatedDate      time.Time  `json:"created_date"`
		ScheduledDate    time.Time  `json:"scheduled_date"`
		StartedDate      *time.Time `json:"started_date"`
		CompletedDate    *time.Time `json:"completed_date"`
		CreatedAt        time.Time  `json:"created_at"`
		UpdatedAt        time.Time  `json:"updated_at"`
		ConnectionName   string     `json:"connection_name"`
		AssetName        string     `json:"asset_name"`
	}

	err := db.DB.Raw(query, args...).Scan(&workOrders).Error
	if err != nil {
		http.Error(w, "Failed to fetch work orders", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"work_orders": workOrders})
}

// Equipment Specification Handlers
func GetEquipmentSpecifications(w http.ResponseWriter, r *http.Request) {
	assetID := r.URL.Query().Get("asset_id")
	specType := r.URL.Query().Get("spec_type")
	connectionID := r.URL.Query().Get("connection_id")

	query := `
		SELECT es.id, es.asset_id, es.cmms_connection_id, es.cmms_asset_id, es.spec_type,
		       es.spec_name, es.spec_value, es.unit, es.min_value, es.max_value, es.is_critical,
		       es.created_at, es.updated_at, cc.name as connection_name, a.asset_type as asset_name
		FROM equipment_specifications es
		JOIN cmms_connections cc ON es.cmms_connection_id = cc.id
		JOIN assets a ON es.asset_id = a.id
		WHERE 1=1
	`
	args := []interface{}{}
	argCount := 0

	if assetID != "" {
		argCount++
		query += fmt.Sprintf(" AND es.asset_id = $%d", argCount)
		args = append(args, assetID)
	}

	if specType != "" {
		argCount++
		query += fmt.Sprintf(" AND es.spec_type = $%d", argCount)
		args = append(args, specType)
	}

	if connectionID != "" {
		argCount++
		query += fmt.Sprintf(" AND es.cmms_connection_id = $%d", argCount)
		args = append(args, connectionID)
	}

	query += " ORDER BY es.spec_type, es.spec_name"

	var specs []struct {
		ID               int       `json:"id"`
		AssetID          int       `json:"asset_id"`
		CMMSConnectionID int       `json:"cmms_connection_id"`
		CMMSAssetID      string    `json:"cmms_asset_id"`
		SpecType         string    `json:"spec_type"`
		SpecName         string    `json:"spec_name"`
		SpecValue        string    `json:"spec_value"`
		Unit             string    `json:"unit"`
		MinValue         *float64  `json:"min_value"`
		MaxValue         *float64  `json:"max_value"`
		IsCritical       bool      `json:"is_critical"`
		CreatedAt        time.Time `json:"created_at"`
		UpdatedAt        time.Time `json:"updated_at"`
		ConnectionName   string    `json:"connection_name"`
		AssetName        string    `json:"asset_name"`
	}

	err := db.DB.Raw(query, args...).Scan(&specs).Error
	if err != nil {
		http.Error(w, "Failed to fetch equipment specifications", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"specifications": specs})
}

// CMMS Sync Handlers
func SyncCMMSData(w http.ResponseWriter, r *http.Request) {
	connectionID := chi.URLParam(r, "connectionId")
	syncType := r.URL.Query().Get("type") // schedules, work_orders, specs

	// Validate sync type
	validTypes := map[string]bool{"schedules": true, "work_orders": true, "specs": true}
	if !validTypes[syncType] {
		http.Error(w, "Invalid sync type. Must be schedules, work_orders, or specs", http.StatusBadRequest)
		return
	}

	connectionIDInt, err := strconv.Atoi(connectionID)
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}

	// Start sync log
	var syncLogID int
	err = db.DB.Raw(`
		INSERT INTO cmms_sync_logs (cmms_connection_id, sync_type, status, started_at, completed_at)
		VALUES (?, ?, 'in_progress', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
		RETURNING id
	`, connectionIDInt, syncType).Scan(&syncLogID).Error

	if err != nil {
		http.Error(w, "Failed to start sync", http.StatusInternalServerError)
		return
	}

	// Implement actual CMMS data synchronization logic
	go func() {
		defer func() {
			// Update sync log with completion status
			db.DB.Exec(`
				UPDATE cmms_sync_logs 
				SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
				WHERE id = ?
			`, syncLogID)
		}()

		// 1. Fetch CMMS connection details
		var connection models.CMMSConnection
		err := db.DB.Where("id = ?", connectionIDInt).First(&connection).Error
		if err != nil {
			log.Printf("Failed to fetch CMMS connection: %v", err)
			return
		}

		// 2. Fetch field mappings for this connection
		var mappings []models.CMMSMapping
		err = db.DB.Where("cmms_connection_id = ?", connectionIDInt).Find(&mappings).Error
		if err != nil {
			log.Printf("Failed to fetch CMMS mappings: %v", err)
			return
		}

		// 3. Create mapping lookup
		fieldMappings := make(map[string]string)
		for _, mapping := range mappings {
			fieldMappings[mapping.CMMSField] = mapping.ArxosField
		}

		// 4. Fetch data from CMMS API based on sync type
		var cmmsData []map[string]interface{}
		switch syncType {
		case "work_orders":
			cmmsData, err = cmmsClient.FetchWorkOrders(connectionIDInt)
		case "maintenance_schedules":
			cmmsData, err = cmmsClient.FetchMaintenanceSchedules(connectionIDInt)
		case "equipment":
			cmmsData, err = cmmsClient.FetchEquipment(connectionIDInt)
		case "assets":
			cmmsData, err = cmmsClient.FetchAssets(connectionIDInt)
		default:
			log.Printf("Unknown sync type: %s", syncType)
			return
		}

		if err != nil {
			log.Printf("Failed to fetch CMMS data: %v", err)
			return
		}

		// 5. Transform and sync data
		syncedCount := 0
		errorCount := 0

		for _, data := range cmmsData {
			// Transform data using field mappings
			transformedData := transformCMMSData(data, fieldMappings)

			// Insert or update record based on sync type
			err = syncCMMSRecord(syncType, transformedData, connectionIDInt)
			if err != nil {
				log.Printf("Failed to sync record: %v", err)
				errorCount++
			} else {
				syncedCount++
			}
		}

		// 6. Update sync log with results
		db.DB.Exec(`
			UPDATE cmms_sync_logs 
			SET status = 'completed', 
				completed_at = CURRENT_TIMESTAMP,
				records_processed = ?,
				records_synced = ?,
				error_count = ?
			WHERE id = ?
		`, len(cmmsData), syncedCount, errorCount, syncLogID)

		log.Printf("CMMS sync completed: %d records processed, %d synced, %d errors",
			len(cmmsData), syncedCount, errorCount)
	}()

	// Return immediate response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message":     "CMMS sync initiated",
		"sync_log_id": syncLogID,
		"sync_type":   syncType,
		"status":      "in_progress",
	})
}

// transformCMMSData transforms CMMS data using field mappings
func transformCMMSData(data map[string]interface{}, fieldMappings map[string]string) map[string]interface{} {
	transformed := make(map[string]interface{})

	for cmmsField, arxosField := range fieldMappings {
		if value, exists := data[cmmsField]; exists {
			transformed[arxosField] = value
		}
	}

	return transformed
}

// syncCMMSRecord syncs a single CMMS record to the Arxos database
func syncCMMSRecord(syncType string, data map[string]interface{}, connectionID int) error {
	switch syncType {
	case "work_orders":
		return syncWorkOrder(data, connectionID)
	case "maintenance_schedules":
		return syncMaintenanceSchedule(data, connectionID)
	case "equipment":
		return syncEquipment(data, connectionID)
	case "assets":
		return syncAsset(data, connectionID)
	default:
		return fmt.Errorf("unknown sync type: %s", syncType)
	}
}

// syncWorkOrder syncs a work order record
func syncWorkOrder(data map[string]interface{}, connectionID int) error {
	// Extract work order data
	workOrderID, _ := data["work_order_id"].(string)
	description, _ := data["description"].(string)
	status, _ := data["status"].(string)
	priority, _ := data["priority"].(string)

	// Upsert work order
	return db.DB.Exec(`
		INSERT INTO work_orders (cmms_connection_id, work_order_id, description, status, priority, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
		ON CONFLICT (cmms_connection_id, work_order_id) 
		DO UPDATE SET 
			description = EXCLUDED.description,
			status = EXCLUDED.status,
			priority = EXCLUDED.priority,
			updated_at = CURRENT_TIMESTAMP
	`, connectionID, workOrderID, description, status, priority).Error
}

// syncMaintenanceSchedule syncs a maintenance schedule record
func syncMaintenanceSchedule(data map[string]interface{}, connectionID int) error {
	// Extract maintenance schedule data
	scheduleID, _ := data["schedule_id"].(string)
	equipmentID, _ := data["equipment_id"].(string)
	maintenanceType, _ := data["maintenance_type"].(string)
	frequency, _ := data["frequency"].(string)

	// Upsert maintenance schedule
	return db.DB.Exec(`
		INSERT INTO maintenance_schedules (cmms_connection_id, schedule_id, equipment_id, maintenance_type, frequency, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
		ON CONFLICT (cmms_connection_id, schedule_id) 
		DO UPDATE SET 
			equipment_id = EXCLUDED.equipment_id,
			maintenance_type = EXCLUDED.maintenance_type,
			frequency = EXCLUDED.frequency,
			updated_at = CURRENT_TIMESTAMP
	`, connectionID, scheduleID, equipmentID, maintenanceType, frequency).Error
}

// syncEquipment syncs an equipment record
func syncEquipment(data map[string]interface{}, connectionID int) error {
	// Extract equipment data
	equipmentID, _ := data["equipment_id"].(string)
	name, _ := data["name"].(string)
	type_, _ := data["type"].(string)
	location, _ := data["location"].(string)

	// Upsert equipment
	return db.DB.Exec(`
		INSERT INTO equipment (cmms_connection_id, equipment_id, name, type, location, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
		ON CONFLICT (cmms_connection_id, equipment_id) 
		DO UPDATE SET 
			name = EXCLUDED.name,
			type = EXCLUDED.type,
			location = EXCLUDED.location,
			updated_at = CURRENT_TIMESTAMP
	`, connectionID, equipmentID, name, type_, location).Error
}

// syncAsset syncs an asset record
func syncAsset(data map[string]interface{}, connectionID int) error {
	// Extract asset data
	assetID, _ := data["asset_id"].(string)
	name, _ := data["name"].(string)
	type_, _ := data["type"].(string)
	location, _ := data["location"].(string)

	// Upsert asset
	return db.DB.Exec(`
		INSERT INTO assets (cmms_connection_id, asset_id, name, type, location, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
		ON CONFLICT (cmms_connection_id, asset_id) 
		DO UPDATE SET 
			name = EXCLUDED.name,
			type = EXCLUDED.type,
			location = EXCLUDED.location,
			updated_at = CURRENT_TIMESTAMP
	`, connectionID, assetID, name, type_, location).Error
}

func GetCMMSSyncLogs(w http.ResponseWriter, r *http.Request) {
	connectionID := chi.URLParam(r, "connectionId")
	limit := r.URL.Query().Get("limit")
	if limit == "" {
		limit = "50"
	}

	limitInt, err := strconv.Atoi(limit)
	if err != nil {
		limitInt = 50
	}

	connectionIDInt, err := strconv.Atoi(connectionID)
	if err != nil {
		http.Error(w, "Invalid connection ID", http.StatusBadRequest)
		return
	}

	logs, err := cmmsClient.GetSyncLogs(connectionIDInt, limitInt)
	if err != nil {
		http.Error(w, "Failed to fetch sync logs", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"sync_logs": logs})
}

// POST /cmms/connections/{id}/test
func TestCMMSConnection(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	idInt, err := strconv.Atoi(id)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	err = cmmsClient.TestConnection(idInt)
	if err != nil {
		w.WriteHeader(http.StatusBadGateway)
		json.NewEncoder(w).Encode(map[string]interface{}{"success": false, "error": err.Error()})
		return
	}
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true})
}

// POST /cmms/connections/{id}/sync
func ManualCMMSSync(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	idInt, err := strconv.Atoi(id)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	err = cmmsClient.SyncConnection(ctx, idInt, "")
	if err != nil {
		w.WriteHeader(http.StatusBadGateway)
		json.NewEncoder(w).Encode(map[string]interface{}{"success": false, "error": err.Error()})
		return
	}
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true})
}
