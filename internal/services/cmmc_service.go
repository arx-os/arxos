package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/ecosystem"
)

// CMMCService implements CMMS/CAFM features for the workflow tier (Layer 3 - PAID)
type CMMCService struct {
	db *database.PostGISDB
}

// NewCMMCService creates a new CMMS/CAFM service
func NewCMMCService(db *database.PostGISDB) *CMMCService {
	return &CMMCService{
		db: db,
	}
}

// Work Order Management

func (cs *CMMCService) CreateWorkOrder(ctx context.Context, req ecosystem.CreateWorkOrderRequest) (*ecosystem.WorkOrder, error) {
	// Validate request
	if req.Title == "" {
		return nil, fmt.Errorf("work order title is required")
	}
	if req.EquipmentID == "" {
		return nil, fmt.Errorf("equipment ID is required")
	}

	// Validate equipment exists
	var equipmentExists bool
	err := cs.db.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM equipment WHERE id = $1)", req.EquipmentID).Scan(&equipmentExists)
	if err != nil {
		return nil, fmt.Errorf("failed to validate equipment: %w", err)
	}
	if !equipmentExists {
		return nil, fmt.Errorf("equipment not found: %s", req.EquipmentID)
	}

	// Create work order
	query := `
		INSERT INTO work_orders (id, title, description, priority, status, equipment_id, metadata, tier, created_at, updated_at)
		VALUES ($1, $2, $3, $4, 'open', $5, $6, 'workflow', NOW(), NOW())
		RETURNING id, title, description, priority, status, equipment_id, metadata
	`

	var workOrder ecosystem.WorkOrder
	workOrderID := generateWorkOrderID()

	var metadataJSON []byte
	err = cs.db.QueryRow(ctx, query,
		workOrderID,
		req.Title,
		req.Description,
		req.Priority,
		req.EquipmentID,
		req.Metadata,
	).Scan(
		&workOrder.ID,
		&workOrder.Title,
		&workOrder.Description,
		&workOrder.Priority,
		&workOrder.Status,
		&workOrder.EquipmentID,
		&metadataJSON,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create work order: %w", err)
	}

	// Parse metadata
	if err := json.Unmarshal(metadataJSON, &workOrder.Metadata); err != nil {
		workOrder.Metadata = make(map[string]interface{})
	}

	return &workOrder, nil
}

func (cs *CMMCService) GetWorkOrder(ctx context.Context, workOrderID string) (*ecosystem.WorkOrder, error) {
	query := `
		SELECT id, title, description, priority, status, equipment_id, metadata
		FROM work_orders
		WHERE id = $1 AND tier = 'workflow'
	`

	var workOrder ecosystem.WorkOrder
	var metadataJSON []byte
	err := cs.db.QueryRow(ctx, query, workOrderID).Scan(
		&workOrder.ID,
		&workOrder.Title,
		&workOrder.Description,
		&workOrder.Priority,
		&workOrder.Status,
		&workOrder.EquipmentID,
		&metadataJSON,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("work order not found")
		}
		return nil, fmt.Errorf("failed to get work order: %w", err)
	}

	// Parse metadata
	if err := json.Unmarshal(metadataJSON, &workOrder.Metadata); err != nil {
		workOrder.Metadata = make(map[string]interface{})
	}

	return &workOrder, nil
}

func (cs *CMMCService) ListWorkOrders(ctx context.Context, userID string, filters ecosystem.WorkOrderFilters) ([]*ecosystem.WorkOrder, error) {
	query := `
		SELECT id, title, description, priority, status, equipment_id, metadata
		FROM work_orders
		WHERE tier = 'workflow'
	`

	args := []interface{}{}
	argIndex := 1

	// Add filters
	if filters.Status != "" {
		query += fmt.Sprintf(" AND status = $%d", argIndex)
		args = append(args, filters.Status)
		argIndex++
	}

	if filters.Priority != "" {
		query += fmt.Sprintf(" AND priority = $%d", argIndex)
		args = append(args, filters.Priority)
		argIndex++
	}

	if filters.EquipmentID != "" {
		query += fmt.Sprintf(" AND equipment_id = $%d", argIndex)
		args = append(args, filters.EquipmentID)
		argIndex++
	}

	query += " ORDER BY created_at DESC"

	rows, err := cs.db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list work orders: %w", err)
	}
	defer rows.Close()

	var workOrders []*ecosystem.WorkOrder
	for rows.Next() {
		var workOrder ecosystem.WorkOrder
		var metadataJSON []byte
		err := rows.Scan(
			&workOrder.ID,
			&workOrder.Title,
			&workOrder.Description,
			&workOrder.Priority,
			&workOrder.Status,
			&workOrder.EquipmentID,
			&metadataJSON,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan work order: %w", err)
		}

		// Parse metadata
		if err := json.Unmarshal(metadataJSON, &workOrder.Metadata); err != nil {
			workOrder.Metadata = make(map[string]interface{})
		}

		workOrders = append(workOrders, &workOrder)
	}

	return workOrders, nil
}

func (cs *CMMCService) UpdateWorkOrder(ctx context.Context, workOrderID string, updates map[string]interface{}) (*ecosystem.WorkOrder, error) {
	// Get existing work order
	workOrder, err := cs.GetWorkOrder(ctx, workOrderID)
	if err != nil {
		return nil, fmt.Errorf("failed to get existing work order: %w", err)
	}

	// Update fields
	if title, ok := updates["title"].(string); ok {
		workOrder.Title = title
	}
	if description, ok := updates["description"].(string); ok {
		workOrder.Description = description
	}
	if priority, ok := updates["priority"].(string); ok {
		workOrder.Priority = priority
	}
	if status, ok := updates["status"].(string); ok {
		workOrder.Status = status
	}
	if metadata, ok := updates["metadata"].(map[string]interface{}); ok {
		workOrder.Metadata = metadata
	}

	// Update in database
	query := `
		UPDATE work_orders 
		SET title = $1, description = $2, priority = $3, status = $4, metadata = $5, updated_at = NOW()
		WHERE id = $6 AND tier = 'workflow'
	`

	_, err = cs.db.Exec(ctx, query,
		workOrder.Title,
		workOrder.Description,
		workOrder.Priority,
		workOrder.Status,
		workOrder.Metadata,
		workOrderID,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to update work order: %w", err)
	}

	return workOrder, nil
}

func (cs *CMMCService) DeleteWorkOrder(ctx context.Context, workOrderID string) error {
	_, err := cs.db.Exec(ctx, "DELETE FROM work_orders WHERE id = $1", workOrderID)
	if err != nil {
		return fmt.Errorf("failed to delete work order: %w", err)
	}

	return nil
}

func (cs *CMMCService) AssignWorkOrder(ctx context.Context, workOrderID string, assigneeID string) error {
	_, err := cs.db.Exec(ctx,
		"UPDATE work_orders SET assigned_to = $1, updated_at = NOW() WHERE id = $2",
		assigneeID, workOrderID)
	if err != nil {
		return fmt.Errorf("failed to assign work order: %w", err)
	}

	return nil
}

func (cs *CMMCService) CompleteWorkOrder(ctx context.Context, workOrderID string, completion ecosystem.WorkOrderCompletion) error {
	query := `
		UPDATE work_orders 
		SET status = 'completed', completed_at = $1, updated_at = NOW()
		WHERE id = $2
	`

	_, err := cs.db.Exec(ctx, query, completion.CompletedAt, workOrderID)
	if err != nil {
		return fmt.Errorf("failed to complete work order: %w", err)
	}

	// Store completion details
	if completion.Notes != "" || completion.Results != nil {
		metadataQuery := `
			UPDATE work_orders 
			SET metadata = COALESCE(metadata, '{}'::jsonb) || $1::jsonb
			WHERE id = $2
		`

		completionData := map[string]interface{}{
			"completion_notes":   completion.Notes,
			"completion_results": completion.Results,
		}

		_, err = cs.db.Exec(ctx, metadataQuery, completionData, workOrderID)
		if err != nil {
			return fmt.Errorf("failed to store completion details: %w", err)
		}
	}

	return nil
}

// Maintenance Schedule Management

func (cs *CMMCService) CreateMaintenanceSchedule(ctx context.Context, req ecosystem.CreateMaintenanceScheduleRequest) (*ecosystem.MaintenanceSchedule, error) {
	// Validate request
	if req.Name == "" {
		return nil, fmt.Errorf("schedule name is required")
	}
	if len(req.EquipmentIDs) == 0 {
		return nil, fmt.Errorf("at least one equipment ID is required")
	}

	// Validate equipment exists
	for _, equipmentID := range req.EquipmentIDs {
		var equipmentExists bool
		err := cs.db.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM equipment WHERE id = $1)", equipmentID).Scan(&equipmentExists)
		if err != nil {
			return nil, fmt.Errorf("failed to validate equipment %s: %w", equipmentID, err)
		}
		if !equipmentExists {
			return nil, fmt.Errorf("equipment not found: %s", equipmentID)
		}
	}

	// Create maintenance schedule
	query := `
		INSERT INTO maintenance_schedules (id, name, type, schedule, tasks, status, user_id, tier, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
		RETURNING id, name, type, schedule, tasks, status, tier, created_at, updated_at
	`

	var schedule ecosystem.MaintenanceSchedule
	scheduleID := generateMaintenanceScheduleID()

	err := cs.db.QueryRow(ctx, query,
		scheduleID,
		req.Name,
		req.Type,
		req.Schedule,
		req.Tasks,
		"active",
		"default_user", // TODO: Get from context
		string(ecosystem.TierWorkflow),
	).Scan(
		&schedule.ID,
		&schedule.Name,
		&schedule.Type,
		&schedule.Schedule,
		&schedule.Tasks,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create maintenance schedule: %w", err)
	}

	// Create schedule-equipment relationships
	for _, equipmentID := range req.EquipmentIDs {
		_, err = cs.db.Exec(ctx, `
			INSERT INTO maintenance_schedule_equipment (schedule_id, equipment_id, created_at)
			VALUES ($1, $2, NOW())
		`, scheduleID, equipmentID)
		if err != nil {
			return nil, fmt.Errorf("failed to link schedule to equipment %s: %w", equipmentID, err)
		}
	}

	return &schedule, nil
}

func (cs *CMMCService) GetMaintenanceSchedule(ctx context.Context, scheduleID string) (*ecosystem.MaintenanceSchedule, error) {
	query := `
		SELECT id, name, type, schedule, tasks
		FROM maintenance_schedules
		WHERE id = $1 AND tier = 'workflow'
	`

	var schedule ecosystem.MaintenanceSchedule
	var tasksJSON []byte
	err := cs.db.QueryRow(ctx, query, scheduleID).Scan(
		&schedule.ID,
		&schedule.Name,
		&schedule.Type,
		&schedule.Schedule,
		&tasksJSON,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("maintenance schedule not found")
		}
		return nil, fmt.Errorf("failed to get maintenance schedule: %w", err)
	}

	// Parse tasks
	if err := json.Unmarshal(tasksJSON, &schedule.Tasks); err != nil {
		schedule.Tasks = []map[string]interface{}{}
	}

	return &schedule, nil
}

func (cs *CMMCService) ListMaintenanceSchedules(ctx context.Context, userID string) ([]*ecosystem.MaintenanceSchedule, error) {
	query := `
		SELECT id, name, type, schedule, tasks
		FROM maintenance_schedules
		WHERE tier = 'workflow'
		ORDER BY created_at DESC
	`

	rows, err := cs.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to list maintenance schedules: %w", err)
	}
	defer rows.Close()

	var schedules []*ecosystem.MaintenanceSchedule
	for rows.Next() {
		var schedule ecosystem.MaintenanceSchedule
		var tasksJSON []byte
		err := rows.Scan(
			&schedule.ID,
			&schedule.Name,
			&schedule.Type,
			&schedule.Schedule,
			&tasksJSON,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan maintenance schedule: %w", err)
		}

		// Parse tasks
		if err := json.Unmarshal(tasksJSON, &schedule.Tasks); err != nil {
			schedule.Tasks = []map[string]interface{}{}
		}

		schedules = append(schedules, &schedule)
	}

	return schedules, nil
}

func (cs *CMMCService) UpdateMaintenanceSchedule(ctx context.Context, scheduleID string, updates map[string]interface{}) (*ecosystem.MaintenanceSchedule, error) {
	// Get existing schedule
	schedule, err := cs.GetMaintenanceSchedule(ctx, scheduleID)
	if err != nil {
		return nil, fmt.Errorf("failed to get existing schedule: %w", err)
	}

	// Update fields
	if name, ok := updates["name"].(string); ok {
		schedule.Name = name
	}
	if scheduleType, ok := updates["type"].(string); ok {
		schedule.Type = scheduleType
	}
	if scheduleData, ok := updates["schedule"].(map[string]interface{}); ok {
		schedule.Schedule = scheduleData
	}
	if tasks, ok := updates["tasks"].([]map[string]interface{}); ok {
		schedule.Tasks = tasks
	}

	// Update in database
	query := `
		UPDATE maintenance_schedules 
		SET name = $1, type = $2, schedule = $3, tasks = $4, updated_at = NOW()
		WHERE id = $5 AND tier = 'workflow'
	`

	_, err = cs.db.Exec(ctx, query,
		schedule.Name,
		schedule.Type,
		schedule.Schedule,
		schedule.Tasks,
		scheduleID,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to update maintenance schedule: %w", err)
	}

	return schedule, nil
}

func (cs *CMMCService) DeleteMaintenanceSchedule(ctx context.Context, scheduleID string) error {
	// Delete schedule-equipment relationships
	_, err := cs.db.Exec(ctx, "DELETE FROM maintenance_schedule_equipment WHERE schedule_id = $1", scheduleID)
	if err != nil {
		return fmt.Errorf("failed to delete schedule-equipment relationships: %w", err)
	}

	// Delete schedule
	_, err = cs.db.Exec(ctx, "DELETE FROM maintenance_schedules WHERE id = $1", scheduleID)
	if err != nil {
		return fmt.Errorf("failed to delete maintenance schedule: %w", err)
	}

	return nil
}

func (cs *CMMCService) ExecuteMaintenanceSchedule(ctx context.Context, scheduleID string) (*ecosystem.MaintenanceExecution, error) {
	// Get schedule
	schedule, err := cs.GetMaintenanceSchedule(ctx, scheduleID)
	if err != nil {
		return nil, fmt.Errorf("failed to get schedule: %w", err)
	}

	// Create execution
	executionID := generateMaintenanceExecutionID()
	query := `
		INSERT INTO maintenance_executions (id, schedule_id, status, started_at, tasks, results, tier)
		VALUES ($1, $2, $3, NOW(), $4, $5, $6)
		RETURNING id, schedule_id, status, started_at, completed_at, tasks, results
	`

	var execution ecosystem.MaintenanceExecution
	var tasksJSON, resultsJSON []byte
	err = cs.db.QueryRow(ctx, query,
		executionID,
		scheduleID,
		"running",
		schedule.Tasks,
		map[string]interface{}{},
		string(ecosystem.TierWorkflow),
	).Scan(
		&execution.ID,
		&execution.ScheduleID,
		&execution.Status,
		&execution.StartedAt,
		&execution.CompletedAt,
		&tasksJSON,
		&resultsJSON,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create maintenance execution: %w", err)
	}

	// Parse tasks and results
	if err := json.Unmarshal(tasksJSON, &execution.Tasks); err != nil {
		execution.Tasks = []map[string]interface{}{}
	}
	if err := json.Unmarshal(resultsJSON, &execution.Results); err != nil {
		execution.Results = map[string]interface{}{}
	}

	return &execution, nil
}

// Report Generation

func (cs *CMMCService) GenerateReport(ctx context.Context, req ecosystem.GenerateReportRequest) (*ecosystem.Report, error) {
	// Validate request
	if req.Name == "" {
		return nil, fmt.Errorf("report name is required")
	}
	if req.Type == "" {
		return nil, fmt.Errorf("report type is required")
	}

	reportID := generateReportID()

	// Generate report based on type
	var reportData map[string]interface{}
	var err error

	switch req.Type {
	case "work_orders":
		reportData, err = cs.generateWorkOrdersReport(ctx, req)
	case "maintenance":
		reportData, err = cs.generateMaintenanceReport(ctx, req)
	case "equipment":
		reportData, err = cs.generateEquipmentReport(ctx, req)
	default:
		return nil, fmt.Errorf("unsupported report type: %s", req.Type)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to generate report data: %w", err)
	}

	// Create report record
	query := `
		INSERT INTO reports (id, name, type, data, format, generated_at, user_id, size_bytes, tier)
		VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7, $8)
		RETURNING id, name, type, data, format, generated_at, user_id, size_bytes
	`

	var report ecosystem.Report
	reportJSON, _ := json.Marshal(reportData)

	err = cs.db.QueryRow(ctx, query,
		reportID,
		req.Name,
		req.Type,
		reportData,
		req.Format,
		"default_user", // TODO: Get from context
		int64(len(reportJSON)),
		string(ecosystem.TierWorkflow),
	).Scan(
		&report.ID,
		&report.Name,
		&report.Type,
		&report.Data,
		&report.Format,
		&report.GeneratedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to store report: %w", err)
	}

	return &report, nil
}

func (cs *CMMCService) GetReport(ctx context.Context, reportID string) (*ecosystem.Report, error) {
	query := `
		SELECT id, name, type, data, format, generated_at
		FROM reports
		WHERE id = $1 AND tier = 'workflow'
	`

	var report ecosystem.Report
	var dataJSON []byte
	err := cs.db.QueryRow(ctx, query, reportID).Scan(
		&report.ID,
		&report.Name,
		&report.Type,
		&dataJSON,
		&report.Format,
		&report.GeneratedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("report not found")
		}
		return nil, fmt.Errorf("failed to get report: %w", err)
	}

	// Parse data
	if err := json.Unmarshal(dataJSON, &report.Data); err != nil {
		report.Data = make(map[string]interface{})
	}

	return &report, nil
}

func (cs *CMMCService) ListReports(ctx context.Context, userID string) ([]*ecosystem.Report, error) {
	query := `
		SELECT id, name, type, data, format, generated_at
		FROM reports
		WHERE tier = 'workflow'
		ORDER BY generated_at DESC
	`

	rows, err := cs.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to list reports: %w", err)
	}
	defer rows.Close()

	var reports []*ecosystem.Report
	for rows.Next() {
		var report ecosystem.Report
		var dataJSON []byte
		err := rows.Scan(
			&report.ID,
			&report.Name,
			&report.Type,
			&dataJSON,
			&report.Format,
			&report.GeneratedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan report: %w", err)
		}

		// Parse data
		if err := json.Unmarshal(dataJSON, &report.Data); err != nil {
			report.Data = make(map[string]interface{})
		}

		reports = append(reports, &report)
	}

	return reports, nil
}

func (cs *CMMCService) DeleteReport(ctx context.Context, reportID string) error {
	_, err := cs.db.Exec(ctx, "DELETE FROM reports WHERE id = $1", reportID)
	if err != nil {
		return fmt.Errorf("failed to delete report: %w", err)
	}

	return nil
}

// Report generation helpers

func (cs *CMMCService) generateWorkOrdersReport(ctx context.Context, req ecosystem.GenerateReportRequest) (map[string]interface{}, error) {
	// Generate work orders report
	query := `
		SELECT COUNT(*) as total,
		       COUNT(CASE WHEN status = 'open' THEN 1 END) as open,
		       COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress,
		       COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
		       COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled
		FROM work_orders
		WHERE user_id = $1
	`

	var stats struct {
		Total      int `json:"total"`
		Open       int `json:"open"`
		InProgress int `json:"in_progress"`
		Completed  int `json:"completed"`
		Cancelled  int `json:"cancelled"`
	}

	err := cs.db.QueryRow(ctx, query, "default_user").Scan(
		&stats.Total,
		&stats.Open,
		&stats.InProgress,
		&stats.Completed,
		&stats.Cancelled,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to generate work orders stats: %w", err)
	}

	return map[string]interface{}{
		"type":         "work_orders",
		"generated_at": time.Now(),
		"summary":      stats,
		"details":      "Work orders report data",
	}, nil
}

func (cs *CMMCService) generateMaintenanceReport(ctx context.Context, req ecosystem.GenerateReportRequest) (map[string]interface{}, error) {
	// Generate maintenance report
	return map[string]interface{}{
		"type":         "maintenance",
		"generated_at": time.Now(),
		"summary":      "Maintenance report data",
		"details":      "Maintenance schedules and executions",
	}, nil
}

func (cs *CMMCService) generateEquipmentReport(ctx context.Context, req ecosystem.GenerateReportRequest) (map[string]interface{}, error) {
	// Generate equipment report
	return map[string]interface{}{
		"type":         "equipment",
		"generated_at": time.Now(),
		"summary":      "Equipment report data",
		"details":      "Equipment status and maintenance history",
	}, nil
}

// Utility functions

func generateWorkOrderID() string {
	return fmt.Sprintf("workorder_%d", time.Now().UnixNano())
}

func generateMaintenanceScheduleID() string {
	return fmt.Sprintf("schedule_%d", time.Now().UnixNano())
}

func generateMaintenanceExecutionID() string {
	return fmt.Sprintf("execution_%d", time.Now().UnixNano())
}

func generateReportID() string {
	return fmt.Sprintf("report_%d", time.Now().UnixNano())
}
