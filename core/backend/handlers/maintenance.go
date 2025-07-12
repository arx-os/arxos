package handlers

import (
	"arx/db"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
)

// Maintenance Task Handlers
func GetMaintenanceTasks(w http.ResponseWriter, r *http.Request) {
	assetID := r.URL.Query().Get("asset_id")
	status := r.URL.Query().Get("status")
	priority := r.URL.Query().Get("priority")

	query := `
		SELECT mt.id, mt.asset_id, mt.schedule_id, mt.task_type, mt.status, mt.priority,
		       mt.title, mt.description, mt.instructions, mt.assigned_to, mt.estimated_hours,
		       mt.actual_hours, mt.estimated_cost, mt.actual_cost, mt.parts_used, mt.notes,
		       mt.scheduled_date, mt.started_date, mt.completed_date, mt.due_date,
		       mt.created_at, mt.updated_at, a.asset_type as asset_name
		FROM maintenance_tasks mt
		JOIN assets a ON mt.asset_id = a.id
		WHERE 1=1
	`
	args := []interface{}{}
	argCount := 0

	if assetID != "" {
		argCount++
		query += fmt.Sprintf(" AND mt.asset_id = $%d", argCount)
		args = append(args, assetID)
	}

	if status != "" {
		argCount++
		query += fmt.Sprintf(" AND mt.status = $%d", argCount)
		args = append(args, status)
	}

	if priority != "" {
		argCount++
		query += fmt.Sprintf(" AND mt.priority = $%d", argCount)
		args = append(args, priority)
	}

	query += " ORDER BY mt.due_date"

	type MaintenanceTask struct {
		ID             int        `json:"id"`
		AssetID        int        `json:"asset_id"`
		ScheduleID     *int       `json:"schedule_id"`
		TaskType       string     `json:"task_type"`
		Status         string     `json:"status"`
		Priority       string     `json:"priority"`
		Title          string     `json:"title"`
		Description    string     `json:"description"`
		Instructions   string     `json:"instructions"`
		AssignedTo     string     `json:"assigned_to"`
		EstimatedHours float64    `json:"estimated_hours"`
		ActualHours    float64    `json:"actual_hours"`
		EstimatedCost  float64    `json:"estimated_cost"`
		ActualCost     float64    `json:"actual_cost"`
		PartsUsed      string     `json:"parts_used"`
		Notes          string     `json:"notes"`
		ScheduledDate  time.Time  `json:"scheduled_date"`
		StartedDate    *time.Time `json:"started_date"`
		CompletedDate  *time.Time `json:"completed_date"`
		DueDate        time.Time  `json:"due_date"`
		CreatedAt      time.Time  `json:"created_at"`
		UpdatedAt      time.Time  `json:"updated_at"`
		AssetName      string     `json:"asset_name"`
	}

	var tasks []MaintenanceTask
	err := db.DB.Raw(query, args...).Scan(&tasks).Error
	if err != nil {
		http.Error(w, "Failed to fetch maintenance tasks", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"tasks": tasks})
}

func CreateMaintenanceTask(w http.ResponseWriter, r *http.Request) {
	var task struct {
		AssetID        int       `json:"asset_id"`
		ScheduleID     *int      `json:"schedule_id"`
		TaskType       string    `json:"task_type"`
		Status         string    `json:"status"`
		Priority       string    `json:"priority"`
		Title          string    `json:"title"`
		Description    string    `json:"description"`
		Instructions   string    `json:"instructions"`
		AssignedTo     string    `json:"assigned_to"`
		EstimatedHours float64   `json:"estimated_hours"`
		EstimatedCost  float64   `json:"estimated_cost"`
		PartsUsed      string    `json:"parts_used"`
		Notes          string    `json:"notes"`
		ScheduledDate  time.Time `json:"scheduled_date"`
		DueDate        time.Time `json:"due_date"`
	}

	if err := json.NewDecoder(r.Body).Decode(&task); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if task.AssetID == 0 || task.TaskType == "" || task.Status == "" || task.Priority == "" {
		http.Error(w, "asset_id, task_type, status, and priority are required", http.StatusBadRequest)
		return
	}

	var id int
	err := db.DB.Raw(`
		INSERT INTO maintenance_tasks (asset_id, schedule_id, task_type, status, priority,
			title, description, instructions, assigned_to, estimated_hours, estimated_cost,
			parts_used, notes, scheduled_date, due_date)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
		RETURNING id
	`, task.AssetID, task.ScheduleID, task.TaskType, task.Status, task.Priority,
		task.Title, task.Description, task.Instructions, task.AssignedTo, task.EstimatedHours,
		task.EstimatedCost, task.PartsUsed, task.Notes, task.ScheduledDate, task.DueDate).Scan(&id).Error

	if err != nil {
		http.Error(w, "Failed to create maintenance task", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{"id": id, "message": "Maintenance task created successfully"})
}

func UpdateMaintenanceTask(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	idInt, err := strconv.Atoi(id)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	var task struct {
		Status        string     `json:"status"`
		Priority      string     `json:"priority"`
		Title         string     `json:"title"`
		Description   string     `json:"description"`
		Instructions  string     `json:"instructions"`
		AssignedTo    string     `json:"assigned_to"`
		ActualHours   float64    `json:"actual_hours"`
		ActualCost    float64    `json:"actual_cost"`
		PartsUsed     string     `json:"parts_used"`
		Notes         string     `json:"notes"`
		StartedDate   *time.Time `json:"started_date"`
		CompletedDate *time.Time `json:"completed_date"`
	}

	if err := json.NewDecoder(r.Body).Decode(&task); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Update the task
	err = db.DB.Exec(`
		UPDATE maintenance_tasks SET 
			status = $1, priority = $2, title = $3, description = $4, instructions = $5,
			assigned_to = $6, actual_hours = $7, actual_cost = $8, parts_used = $9,
			notes = $10, started_date = $11, completed_date = $12, updated_at = CURRENT_TIMESTAMP
		WHERE id = $13
	`, task.Status, task.Priority, task.Title, task.Description, task.Instructions,
		task.AssignedTo, task.ActualHours, task.ActualCost, task.PartsUsed, task.Notes,
		task.StartedDate, task.CompletedDate, idInt).Error

	if err != nil {
		http.Error(w, "Failed to update maintenance task", http.StatusInternalServerError)
		return
	}

	// If task is completed, update asset's last maintenance date and total cost
	if task.Status == "completed" && task.CompletedDate != nil {
		db.DB.Exec(`
			UPDATE assets SET last_maintenance_date = $1, 
				total_maintenance_cost = total_maintenance_cost + $2,
				updated_at = CURRENT_TIMESTAMP
			WHERE id = (SELECT asset_id FROM maintenance_tasks WHERE id = $3)
		`, task.CompletedDate, task.ActualCost, idInt)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"message": "Maintenance task updated successfully"})
}

// Asset Lifecycle Handlers
func GetAssetLifecycle(w http.ResponseWriter, r *http.Request) {
	assetID := chi.URLParam(r, "assetId")

	type Lifecycle struct {
		ID              int        `json:"id"`
		AssetID         int        `json:"asset_id"`
		InstallDate     time.Time  `json:"install_date"`
		ExpectedLife    int        `json:"expected_life"`
		EndOfLifeDate   time.Time  `json:"end_of_life_date"`
		ReplacementDate *time.Time `json:"replacement_date"`
		Status          string     `json:"status"`
		Condition       string     `json:"condition"`
		RiskLevel       string     `json:"risk_level"`
		Notes           string     `json:"notes"`
		CreatedAt       time.Time  `json:"created_at"`
		UpdatedAt       time.Time  `json:"updated_at"`
		AssetName       string     `json:"asset_name"`
	}

	var lifecycle Lifecycle
	err := db.DB.Raw(`
		SELECT al.id, al.asset_id, al.install_date, al.expected_life, al.end_of_life_date,
		       al.replacement_date, al.status, al.condition, al.risk_level, al.notes,
		       al.created_at, al.updated_at, a.asset_type as asset_name
		FROM asset_lifecycles al
		JOIN assets a ON al.asset_id = a.id
		WHERE al.asset_id = $1
	`, assetID).Scan(&lifecycle).Error

	if err != nil {
		http.Error(w, "Asset lifecycle not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(lifecycle)
}

func CreateAssetLifecycle(w http.ResponseWriter, r *http.Request) {
	var lifecycle struct {
		AssetID      int       `json:"asset_id"`
		InstallDate  time.Time `json:"install_date"`
		ExpectedLife int       `json:"expected_life"`
		Condition    string    `json:"condition"`
		RiskLevel    string    `json:"risk_level"`
		Notes        string    `json:"notes"`
	}

	if err := json.NewDecoder(r.Body).Decode(&lifecycle); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if lifecycle.AssetID == 0 || lifecycle.ExpectedLife == 0 {
		http.Error(w, "asset_id and expected_life are required", http.StatusBadRequest)
		return
	}

	// Calculate end of life date
	endOfLifeDate := lifecycle.InstallDate.AddDate(0, lifecycle.ExpectedLife, 0)

	var id int
	err := db.DB.Raw(`
		INSERT INTO asset_lifecycles (asset_id, install_date, expected_life, end_of_life_date,
			condition, risk_level, notes)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		RETURNING id
	`, lifecycle.AssetID, lifecycle.InstallDate, lifecycle.ExpectedLife, endOfLifeDate,
		lifecycle.Condition, lifecycle.RiskLevel, lifecycle.Notes).Scan(&id).Error

	if err != nil {
		http.Error(w, "Failed to create asset lifecycle", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{"id": id, "message": "Asset lifecycle created successfully"})
}

// Warranty Handlers
func GetAssetWarranties(w http.ResponseWriter, r *http.Request) {
	assetID := chi.URLParam(r, "assetId")

	type Warranty struct {
		ID             int       `json:"id"`
		AssetID        int       `json:"asset_id"`
		WarrantyType   string    `json:"warranty_type"`
		Provider       string    `json:"provider"`
		ContractNumber string    `json:"contract_number"`
		StartDate      time.Time `json:"start_date"`
		EndDate        time.Time `json:"end_date"`
		Coverage       string    `json:"coverage"`
		Terms          string    `json:"terms"`
		ContactInfo    string    `json:"contact_info"`
		IsActive       bool      `json:"is_active"`
		CreatedAt      time.Time `json:"created_at"`
		UpdatedAt      time.Time `json:"updated_at"`
	}

	var warranties []Warranty
	err := db.DB.Raw(`
		SELECT id, asset_id, warranty_type, provider, contract_number, start_date, end_date,
		       coverage, terms, contact_info, is_active, created_at, updated_at
		FROM warranties
		WHERE asset_id = $1
		ORDER BY end_date DESC
	`, assetID).Scan(&warranties).Error

	if err != nil {
		http.Error(w, "Failed to fetch warranties", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"warranties": warranties})
}

func CreateWarranty(w http.ResponseWriter, r *http.Request) {
	var warranty struct {
		AssetID        int       `json:"asset_id"`
		WarrantyType   string    `json:"warranty_type"`
		Provider       string    `json:"provider"`
		ContractNumber string    `json:"contract_number"`
		StartDate      time.Time `json:"start_date"`
		EndDate        time.Time `json:"end_date"`
		Coverage       string    `json:"coverage"`
		Terms          string    `json:"terms"`
		ContactInfo    string    `json:"contact_info"`
	}

	if err := json.NewDecoder(r.Body).Decode(&warranty); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if warranty.AssetID == 0 || warranty.WarrantyType == "" || warranty.Provider == "" || warranty.Coverage == "" {
		http.Error(w, "asset_id, warranty_type, provider, and coverage are required", http.StatusBadRequest)
		return
	}

	var id int
	err := db.DB.Raw(`
		INSERT INTO warranties (asset_id, warranty_type, provider, contract_number, start_date,
			end_date, coverage, terms, contact_info)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		RETURNING id
	`, warranty.AssetID, warranty.WarrantyType, warranty.Provider, warranty.ContractNumber,
		warranty.StartDate, warranty.EndDate, warranty.Coverage, warranty.Terms, warranty.ContactInfo).Scan(&id).Error

	if err != nil {
		http.Error(w, "Failed to create warranty", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{"id": id, "message": "Warranty created successfully"})
}

// Replacement Plan Handlers
func GetReplacementPlans(w http.ResponseWriter, r *http.Request) {
	assetID := r.URL.Query().Get("asset_id")
	status := r.URL.Query().Get("status")

	query := `
		SELECT rp.id, rp.asset_id, rp.plan_type, rp.reason, rp.priority, rp.estimated_cost,
		       rp.budgeted_amount, rp.planned_date, rp.actual_date, rp.status,
		       rp.replacement_asset_id, rp.notes, rp.created_at, rp.updated_at,
		       a.asset_type as asset_name
		FROM replacement_plans rp
		JOIN assets a ON rp.asset_id = a.id
		WHERE 1=1
	`
	args := []interface{}{}
	argCount := 0

	if assetID != "" {
		argCount++
		query += fmt.Sprintf(" AND rp.asset_id = $%d", argCount)
		args = append(args, assetID)
	}

	if status != "" {
		argCount++
		query += fmt.Sprintf(" AND rp.status = $%d", argCount)
		args = append(args, status)
	}

	query += " ORDER BY rp.planned_date"

	type ReplacementPlan struct {
		ID                 int        `json:"id"`
		AssetID            int        `json:"asset_id"`
		PlanType           string     `json:"plan_type"`
		Reason             string     `json:"reason"`
		Priority           string     `json:"priority"`
		EstimatedCost      float64    `json:"estimated_cost"`
		BudgetedAmount     float64    `json:"budgeted_amount"`
		PlannedDate        time.Time  `json:"planned_date"`
		ActualDate         *time.Time `json:"actual_date"`
		Status             string     `json:"status"`
		ReplacementAssetID *int       `json:"replacement_asset_id"`
		Notes              string     `json:"notes"`
		CreatedAt          time.Time  `json:"created_at"`
		UpdatedAt          time.Time  `json:"updated_at"`
		AssetName          string     `json:"asset_name"`
	}

	var plans []ReplacementPlan
	err := db.DB.Raw(query, args...).Scan(&plans).Error
	if err != nil {
		http.Error(w, "Failed to fetch replacement plans", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"plans": plans})
}

// Maintenance Cost Handlers
func GetMaintenanceCosts(w http.ResponseWriter, r *http.Request) {
	assetID := r.URL.Query().Get("asset_id")
	costType := r.URL.Query().Get("cost_type")
	startDate := r.URL.Query().Get("start_date")
	endDate := r.URL.Query().Get("end_date")

	query := `
		SELECT mc.id, mc.asset_id, mc.task_id, mc.cost_type, mc.description, mc.amount,
		       mc.currency, mc.date, mc.invoice_number, mc.vendor, mc.approved_by,
		       mc.created_at, mc.updated_at, a.asset_type as asset_name
		FROM maintenance_costs mc
		JOIN assets a ON mc.asset_id = a.id
		WHERE 1=1
	`
	args := []interface{}{}
	argCount := 0

	if assetID != "" {
		argCount++
		query += fmt.Sprintf(" AND mc.asset_id = $%d", argCount)
		args = append(args, assetID)
	}

	if costType != "" {
		argCount++
		query += fmt.Sprintf(" AND mc.cost_type = $%d", argCount)
		args = append(args, costType)
	}

	if startDate != "" {
		argCount++
		query += fmt.Sprintf(" AND mc.date >= $%d", argCount)
		args = append(args, startDate)
	}

	if endDate != "" {
		argCount++
		query += fmt.Sprintf(" AND mc.date <= $%d", argCount)
		args = append(args, endDate)
	}

	query += " ORDER BY mc.date DESC"

	type MaintenanceCost struct {
		ID            int       `json:"id"`
		AssetID       int       `json:"asset_id"`
		TaskID        *int      `json:"task_id"`
		CostType      string    `json:"cost_type"`
		Description   string    `json:"description"`
		Amount        float64   `json:"amount"`
		Currency      string    `json:"currency"`
		Date          time.Time `json:"date"`
		InvoiceNumber string    `json:"invoice_number"`
		Vendor        string    `json:"vendor"`
		ApprovedBy    string    `json:"approved_by"`
		CreatedAt     time.Time `json:"created_at"`
		UpdatedAt     time.Time `json:"updated_at"`
		AssetName     string    `json:"asset_name"`
	}

	var costs []MaintenanceCost
	err := db.DB.Raw(query, args...).Scan(&costs).Error
	if err != nil {
		http.Error(w, "Failed to fetch maintenance costs", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"costs": costs})
}

// Maintenance Notification Handlers
func GetMaintenanceNotifications(w http.ResponseWriter, r *http.Request) {
	assetID := r.URL.Query().Get("asset_id")
	isRead := r.URL.Query().Get("is_read")
	priority := r.URL.Query().Get("priority")

	query := `
		SELECT mn.id, mn.asset_id, mn.task_id, mn.notification_type, mn.title, mn.message,
		       mn.priority, mn.is_read, mn.read_by, mn.read_at, mn.created_at, mn.updated_at,
		       a.asset_type as asset_name
		FROM maintenance_notifications mn
		JOIN assets a ON mn.asset_id = a.id
		WHERE 1=1
	`
	args := []interface{}{}
	argCount := 0

	if assetID != "" {
		argCount++
		query += fmt.Sprintf(" AND mn.asset_id = $%d", argCount)
		args = append(args, assetID)
	}

	if isRead != "" {
		argCount++
		query += fmt.Sprintf(" AND mn.is_read = $%d", argCount)
		args = append(args, isRead == "true")
	}

	if priority != "" {
		argCount++
		query += fmt.Sprintf(" AND mn.priority = $%d", argCount)
		args = append(args, priority)
	}

	query += " ORDER BY mn.created_at DESC"

	type Notification struct {
		ID               int        `json:"id"`
		AssetID          int        `json:"asset_id"`
		TaskID           *int       `json:"task_id"`
		NotificationType string     `json:"notification_type"`
		Title            string     `json:"title"`
		Message          string     `json:"message"`
		Priority         string     `json:"priority"`
		IsRead           bool       `json:"is_read"`
		ReadBy           string     `json:"read_by"`
		ReadAt           *time.Time `json:"read_at"`
		CreatedAt        time.Time  `json:"created_at"`
		UpdatedAt        time.Time  `json:"updated_at"`
		AssetName        string     `json:"asset_name"`
	}

	var notifications []Notification
	err := db.DB.Raw(query, args...).Scan(&notifications).Error
	if err != nil {
		http.Error(w, "Failed to fetch notifications", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"notifications": notifications})
}

func MarkNotificationAsRead(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	readBy := r.URL.Query().Get("read_by")

	idInt, err := strconv.Atoi(id)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	err = db.DB.Exec(`
		UPDATE maintenance_notifications SET is_read = true, read_by = $1, read_at = CURRENT_TIMESTAMP
		WHERE id = $2
	`, readBy, idInt).Error

	if err != nil {
		http.Error(w, "Failed to mark notification as read", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"message": "Notification marked as read"})
}

// Maintenance Dashboard
func GetMaintenanceDashboard(w http.ResponseWriter, r *http.Request) {
	// Get summary statistics
	var stats struct {
		TotalTasks        int     `json:"total_tasks"`
		PendingTasks      int     `json:"pending_tasks"`
		OverdueTasks      int     `json:"overdue_tasks"`
		CompletedTasks    int     `json:"completed_tasks"`
		TotalCost         float64 `json:"total_cost"`
		AverageCompletion float64 `json:"average_completion_hours"`
	}

	// Get task counts
	db.DB.Raw("SELECT COUNT(*) FROM maintenance_tasks").Scan(&stats.TotalTasks)
	db.DB.Raw("SELECT COUNT(*) FROM maintenance_tasks WHERE status = 'pending'").Scan(&stats.PendingTasks)
	db.DB.Raw("SELECT COUNT(*) FROM maintenance_tasks WHERE due_date < CURRENT_DATE AND status != 'completed'").Scan(&stats.OverdueTasks)
	db.DB.Raw("SELECT COUNT(*) FROM maintenance_tasks WHERE status = 'completed'").Scan(&stats.CompletedTasks)

	// Get total cost
	db.DB.Raw("SELECT COALESCE(SUM(actual_cost), 0) FROM maintenance_tasks WHERE status = 'completed'").Scan(&stats.TotalCost)

	// Get average completion time
	db.DB.Raw(`
		SELECT COALESCE(AVG(actual_hours), 0) 
		FROM maintenance_tasks 
		WHERE status = 'completed' AND actual_hours > 0
	`).Scan(&stats.AverageCompletion)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"dashboard": stats})
}
