package facility

import (
	"fmt"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// MaintenanceManager manages maintenance schedules and operations
type MaintenanceManager struct {
	facilityManager  *FacilityManager
	workOrderManager *WorkOrderManager
	schedules        map[string]*MaintenanceSchedule
	metrics          *MaintenanceMetrics
}

// MaintenanceMetrics tracks maintenance performance
type MaintenanceMetrics struct {
	TotalSchedules         int64   `json:"total_schedules"`
	ActiveSchedules        int64   `json:"active_schedules"`
	DueSchedules           int64   `json:"due_schedules"`
	OverdueSchedules       int64   `json:"overdue_schedules"`
	CompletedTasks         int64   `json:"completed_tasks"`
	UpcomingMaintenance    int64   `json:"upcoming_maintenance"`
	OverdueMaintenance     int64   `json:"overdue_maintenance"`
	CompletedMaintenance   int64   `json:"completed_maintenance"`
	PreventiveMaintenance  int64   `json:"preventive_maintenance"`
	PredictiveMaintenance  int64   `json:"predictive_maintenance"`
	CorrectiveMaintenance  int64   `json:"corrective_maintenance"`
	EmergencyMaintenance   int64   `json:"emergency_maintenance"`
	AverageInterval        float64 `json:"average_interval"`
	AvgCompletionTimeHours float64 `json:"avg_completion_time_hours"`
	ComplianceRate         float64 `json:"compliance_rate"`
	CostSavings            float64 `json:"cost_savings"`
}

// NewMaintenanceManager creates a new maintenance manager
func NewMaintenanceManager(facilityManager *FacilityManager, workOrderManager *WorkOrderManager) *MaintenanceManager {
	return &MaintenanceManager{
		facilityManager:  facilityManager,
		workOrderManager: workOrderManager,
		schedules:        make(map[string]*MaintenanceSchedule),
		metrics:          &MaintenanceMetrics{},
	}
}

// CreateMaintenanceSchedule creates a new maintenance schedule
func (mm *MaintenanceManager) CreateMaintenanceSchedule(schedule *MaintenanceSchedule) error {
	if schedule == nil {
		return fmt.Errorf("maintenance schedule cannot be nil")
	}

	if schedule.ID == "" {
		schedule.ID = fmt.Sprintf("maint_%d", time.Now().UnixNano())
	}

	if schedule.Name == "" {
		return fmt.Errorf("maintenance schedule name cannot be empty")
	}

	if schedule.AssetID == "" {
		return fmt.Errorf("asset ID cannot be empty")
	}

	// Validate asset exists
	if _, exists := mm.facilityManager.assets[schedule.AssetID]; !exists {
		return fmt.Errorf("asset %s not found", schedule.AssetID)
	}

	// Set timestamps
	now := time.Now()
	schedule.CreatedAt = now
	schedule.UpdatedAt = now

	// Set default status
	if schedule.Status == "" {
		schedule.Status = MaintenanceStatusActive
	}

	// Calculate next run date
	if schedule.NextRun.IsZero() {
		schedule.NextRun = mm.calculateNextRun(schedule)
	}

	// Store schedule
	mm.schedules[schedule.ID] = schedule
	mm.metrics.TotalSchedules++

	// Update facility manager
	mm.facilityManager.maintenance[schedule.ID] = schedule

	logger.Info("Maintenance schedule created: %s (%s)", schedule.ID, schedule.Name)
	return nil
}

// GetMaintenanceSchedule retrieves a maintenance schedule by ID
func (mm *MaintenanceManager) GetMaintenanceSchedule(scheduleID string) (*MaintenanceSchedule, error) {
	schedule, exists := mm.schedules[scheduleID]
	if !exists {
		return nil, fmt.Errorf("maintenance schedule %s not found", scheduleID)
	}
	return schedule, nil
}

// UpdateMaintenanceSchedule updates an existing maintenance schedule
func (mm *MaintenanceManager) UpdateMaintenanceSchedule(scheduleID string, updates map[string]interface{}) error {
	schedule, exists := mm.schedules[scheduleID]
	if !exists {
		return fmt.Errorf("maintenance schedule %s not found", scheduleID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "name":
			if name, ok := value.(string); ok {
				schedule.Name = name
			}
		case "description":
			if description, ok := value.(string); ok {
				schedule.Description = description
			}
		case "type":
			if maintType, ok := value.(string); ok {
				schedule.Type = MaintenanceType(maintType)
			}
		case "frequency":
			if frequency, ok := value.(string); ok {
				schedule.Frequency = frequency
			}
		case "interval":
			if interval, ok := value.(int); ok {
				schedule.Interval = interval
			}
		case "status":
			if status, ok := value.(string); ok {
				schedule.Status = MaintenanceStatus(status)
			}
		case "next_run":
			if nextRun, ok := value.(time.Time); ok {
				schedule.NextRun = nextRun
			}
		}
	}

	schedule.UpdatedAt = time.Now()
	logger.Info("Maintenance schedule updated: %s", scheduleID)
	return nil
}

// DeleteMaintenanceSchedule deletes a maintenance schedule
func (mm *MaintenanceManager) DeleteMaintenanceSchedule(scheduleID string) error {
	schedule, exists := mm.schedules[scheduleID]
	if !exists {
		return fmt.Errorf("maintenance schedule %s not found", scheduleID)
	}

	// Delete schedule
	delete(mm.schedules, scheduleID)
	delete(mm.facilityManager.maintenance, scheduleID)
	mm.metrics.TotalSchedules--

	logger.Info("Maintenance schedule deleted: %s (%s)", scheduleID, schedule.Name)
	return nil
}

// ListMaintenanceSchedules returns all maintenance schedules
func (mm *MaintenanceManager) ListMaintenanceSchedules() []*MaintenanceSchedule {
	schedules := make([]*MaintenanceSchedule, 0, len(mm.schedules))
	for _, schedule := range mm.schedules {
		schedules = append(schedules, schedule)
	}
	return schedules
}

// GetMaintenanceSchedulesByAsset returns maintenance schedules for a specific asset
func (mm *MaintenanceManager) GetMaintenanceSchedulesByAsset(assetID string) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		if schedule.AssetID == assetID {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetMaintenanceSchedulesByType returns maintenance schedules by type
func (mm *MaintenanceManager) GetMaintenanceSchedulesByType(maintType MaintenanceType) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		if schedule.Type == maintType {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetMaintenanceSchedulesByStatus returns maintenance schedules by status
func (mm *MaintenanceManager) GetMaintenanceSchedulesByStatus(status MaintenanceStatus) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		if schedule.Status == status {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetUpcomingMaintenance returns maintenance schedules due in the next specified days
func (mm *MaintenanceManager) GetUpcomingMaintenance(days int) []*MaintenanceSchedule {
	var upcomingSchedules []*MaintenanceSchedule
	now := time.Now()
	cutoff := now.AddDate(0, 0, days)

	for _, schedule := range mm.schedules {
		if schedule.Status == MaintenanceStatusActive &&
			schedule.NextRun.After(now) && schedule.NextRun.Before(cutoff) {
			upcomingSchedules = append(upcomingSchedules, schedule)
		}
	}

	return upcomingSchedules
}

// GetOverdueMaintenance returns overdue maintenance schedules
func (mm *MaintenanceManager) GetOverdueMaintenance() []*MaintenanceSchedule {
	var overdueSchedules []*MaintenanceSchedule
	now := time.Now()

	for _, schedule := range mm.schedules {
		if schedule.Status == MaintenanceStatusActive && schedule.NextRun.Before(now) {
			overdueSchedules = append(overdueSchedules, schedule)
		}
	}

	return overdueSchedules
}

// ExecuteMaintenanceSchedule executes a maintenance schedule and creates a work order
func (mm *MaintenanceManager) ExecuteMaintenanceSchedule(scheduleID string) (*WorkOrder, error) {
	schedule, exists := mm.schedules[scheduleID]
	if !exists {
		return nil, fmt.Errorf("maintenance schedule %s not found", scheduleID)
	}

	if schedule.Status != MaintenanceStatusActive {
		return nil, fmt.Errorf("maintenance schedule %s is not active", scheduleID)
	}

	// Get asset information
	asset, err := mm.facilityManager.GetAsset(schedule.AssetID)
	if err != nil {
		return nil, fmt.Errorf("failed to get asset: %w", err)
	}

	// Create work order
	workOrder := &WorkOrder{
		Title:       fmt.Sprintf("Maintenance: %s", schedule.Name),
		Description: schedule.Description,
		Type:        WorkOrderTypePreventive,
		Priority:    WorkOrderPriorityMedium,
		Status:      WorkOrderStatusOpen,
		BuildingID:  asset.BuildingID,
		SpaceID:     asset.SpaceID,
		AssetID:     asset.ID,
		RequestedBy: "system",
		Config: map[string]interface{}{
			"schedule_id":      schedule.ID,
			"maintenance_type": schedule.Type,
		},
	}

	// Create work order
	err = mm.workOrderManager.CreateWorkOrder(workOrder)
	if err != nil {
		return nil, fmt.Errorf("failed to create work order: %w", err)
	}

	// Update schedule
	now := time.Now()
	schedule.LastRun = &now
	schedule.NextRun = mm.calculateNextRun(schedule)
	schedule.UpdatedAt = now

	// Update asset
	asset.LastMaintenance = &now
	asset.NextMaintenance = &schedule.NextRun
	mm.facilityManager.UpdateAsset(asset.ID, map[string]interface{}{
		"last_maintenance": now,
		"next_maintenance": schedule.NextRun,
	})

	logger.Info("Maintenance schedule %s executed, work order %s created", scheduleID, workOrder.ID)
	return workOrder, nil
}

// ExecuteAllDueMaintenance executes all due maintenance schedules
func (mm *MaintenanceManager) ExecuteAllDueMaintenance() ([]*WorkOrder, error) {
	var workOrders []*WorkOrder
	now := time.Now()

	for _, schedule := range mm.schedules {
		if schedule.Status == MaintenanceStatusActive && schedule.NextRun.Before(now) {
			workOrder, err := mm.ExecuteMaintenanceSchedule(schedule.ID)
			if err != nil {
				logger.Error("Failed to execute maintenance schedule %s: %v", schedule.ID, err)
				continue
			}
			workOrders = append(workOrders, workOrder)
		}
	}

	logger.Info("Executed %d due maintenance schedules", len(workOrders))
	return workOrders, nil
}

// PauseMaintenanceSchedule pauses a maintenance schedule
func (mm *MaintenanceManager) PauseMaintenanceSchedule(scheduleID string) error {
	schedule, exists := mm.schedules[scheduleID]
	if !exists {
		return fmt.Errorf("maintenance schedule %s not found", scheduleID)
	}

	schedule.Status = MaintenanceStatusPaused
	schedule.UpdatedAt = time.Now()

	logger.Info("Maintenance schedule %s paused", scheduleID)
	return nil
}

// ResumeMaintenanceSchedule resumes a paused maintenance schedule
func (mm *MaintenanceManager) ResumeMaintenanceSchedule(scheduleID string) error {
	schedule, exists := mm.schedules[scheduleID]
	if !exists {
		return fmt.Errorf("maintenance schedule %s not found", scheduleID)
	}

	schedule.Status = MaintenanceStatusActive
	schedule.UpdatedAt = time.Now()

	logger.Info("Maintenance schedule %s resumed", scheduleID)
	return nil
}

// CompleteMaintenanceSchedule marks a maintenance schedule as completed
func (mm *MaintenanceManager) CompleteMaintenanceSchedule(scheduleID string) error {
	schedule, exists := mm.schedules[scheduleID]
	if !exists {
		return fmt.Errorf("maintenance schedule %s not found", scheduleID)
	}

	schedule.Status = MaintenanceStatusCompleted
	schedule.UpdatedAt = time.Now()

	logger.Info("Maintenance schedule %s completed", scheduleID)
	return nil
}

// GetMaintenanceStatistics returns maintenance statistics
func (mm *MaintenanceManager) GetMaintenanceStatistics() map[string]interface{} {
	stats := make(map[string]interface{})

	// Count by type
	typeCounts := make(map[MaintenanceType]int)
	for _, schedule := range mm.schedules {
		typeCounts[schedule.Type]++
	}
	stats["type_counts"] = typeCounts

	// Count by status
	statusCounts := make(map[MaintenanceStatus]int)
	for _, schedule := range mm.schedules {
		statusCounts[schedule.Status]++
	}
	stats["status_counts"] = statusCounts

	// Count by frequency
	frequencyCounts := make(map[MaintenanceFrequency]int)
	for _, schedule := range mm.schedules {
		frequencyCounts[MaintenanceFrequency(schedule.Frequency)]++
	}
	stats["frequency_counts"] = frequencyCounts

	// Calculate averages
	var totalInterval float64
	var intervalCount int

	for _, schedule := range mm.schedules {
		totalInterval += float64(schedule.Interval)
		intervalCount++
	}

	if intervalCount > 0 {
		stats["average_interval"] = totalInterval / float64(intervalCount)
	}

	// Count upcoming and overdue
	stats["upcoming_maintenance"] = len(mm.GetUpcomingMaintenance(30))
	stats["overdue_maintenance"] = len(mm.GetOverdueMaintenance())

	stats["total_schedules"] = len(mm.schedules)

	return stats
}

// GetMaintenanceMetrics returns maintenance metrics
func (mm *MaintenanceManager) GetMaintenanceMetrics() *MaintenanceMetrics {
	// Update metrics
	mm.metrics.TotalSchedules = int64(len(mm.schedules))

	// Count active schedules
	mm.metrics.ActiveSchedules = 0
	mm.metrics.UpcomingMaintenance = 0
	mm.metrics.OverdueMaintenance = 0
	mm.metrics.CompletedMaintenance = 0
	mm.metrics.PreventiveMaintenance = 0
	mm.metrics.PredictiveMaintenance = 0
	mm.metrics.CorrectiveMaintenance = 0
	mm.metrics.EmergencyMaintenance = 0

	now := time.Now()
	upcomingCutoff := now.AddDate(0, 0, 30)

	for _, schedule := range mm.schedules {
		switch schedule.Status {
		case MaintenanceStatusActive:
			mm.metrics.ActiveSchedules++
			if schedule.NextRun.Before(now) {
				mm.metrics.OverdueMaintenance++
			} else if schedule.NextRun.Before(upcomingCutoff) {
				mm.metrics.UpcomingMaintenance++
			}
		case MaintenanceStatusCompleted:
			mm.metrics.CompletedMaintenance++
		}

		switch schedule.Type {
		case MaintenanceTypePreventive:
			mm.metrics.PreventiveMaintenance++
		case MaintenanceTypePredictive:
			mm.metrics.PredictiveMaintenance++
		case MaintenanceTypeCorrective:
			mm.metrics.CorrectiveMaintenance++
		case MaintenanceTypeEmergency:
			mm.metrics.EmergencyMaintenance++
		}
	}

	// Calculate average interval
	var totalInterval float64
	var intervalCount int

	for _, schedule := range mm.schedules {
		totalInterval += float64(schedule.Interval)
		intervalCount++
	}

	if intervalCount > 0 {
		mm.metrics.AverageInterval = totalInterval / float64(intervalCount)
	}

	// Calculate compliance rate
	if mm.metrics.TotalSchedules > 0 {
		mm.metrics.ComplianceRate = float64(mm.metrics.CompletedMaintenance) / float64(mm.metrics.TotalSchedules) * 100
	}

	return mm.metrics
}

// Helper methods

func (mm *MaintenanceManager) calculateNextRun(schedule *MaintenanceSchedule) time.Time {
	now := time.Now()

	switch schedule.Frequency {
	case "daily":
		return now.AddDate(0, 0, schedule.Interval)
	case "weekly":
		return now.AddDate(0, 0, schedule.Interval*7)
	case "monthly":
		return now.AddDate(0, schedule.Interval, 0)
	case "quarterly":
		return now.AddDate(0, schedule.Interval*3, 0)
	case "annually":
		return now.AddDate(schedule.Interval, 0, 0)
	case "custom":
		return now.AddDate(0, 0, schedule.Interval)
	default:
		return now.AddDate(0, 0, schedule.Interval)
	}
}

// SortMaintenanceSchedulesByNextRun sorts maintenance schedules by next run date
func (mm *MaintenanceManager) SortMaintenanceSchedulesByNextRun(schedules []*MaintenanceSchedule) []*MaintenanceSchedule {
	sort.Slice(schedules, func(i, j int) bool {
		return schedules[i].NextRun.Before(schedules[j].NextRun)
	})
	return schedules
}

// SortMaintenanceSchedulesByType sorts maintenance schedules by type
func (mm *MaintenanceManager) SortMaintenanceSchedulesByType(schedules []*MaintenanceSchedule) []*MaintenanceSchedule {
	sort.Slice(schedules, func(i, j int) bool {
		return schedules[i].Type < schedules[j].Type
	})
	return schedules
}

// GetMaintenanceSchedulesByAssetType returns maintenance schedules for assets of a specific type
func (mm *MaintenanceManager) GetMaintenanceSchedulesByAssetType(assetType AssetType) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		asset, err := mm.facilityManager.GetAsset(schedule.AssetID)
		if err != nil {
			continue
		}
		if asset.AssetType == string(assetType) {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetMaintenanceSchedulesByBuilding returns maintenance schedules for assets in a specific building
func (mm *MaintenanceManager) GetMaintenanceSchedulesByBuilding(buildingID string) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		asset, err := mm.facilityManager.GetAsset(schedule.AssetID)
		if err != nil {
			continue
		}
		if asset.BuildingID == buildingID {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetMaintenanceSchedulesBySpace returns maintenance schedules for assets in a specific space
func (mm *MaintenanceManager) GetMaintenanceSchedulesBySpace(spaceID string) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		asset, err := mm.facilityManager.GetAsset(schedule.AssetID)
		if err != nil {
			continue
		}
		if asset.SpaceID == spaceID {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetMaintenanceSchedulesByDateRange returns maintenance schedules within a date range
func (mm *MaintenanceManager) GetMaintenanceSchedulesByDateRange(startDate, endDate time.Time) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		if schedule.NextRun.After(startDate) && schedule.NextRun.Before(endDate) {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetMaintenanceSchedulesByFrequency returns maintenance schedules by frequency
func (mm *MaintenanceManager) GetMaintenanceSchedulesByFrequency(frequency MaintenanceFrequency) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		if schedule.Frequency == string(frequency) {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetMaintenanceSchedulesByInterval returns maintenance schedules by interval
func (mm *MaintenanceManager) GetMaintenanceSchedulesByInterval(interval int) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		if schedule.Interval == interval {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetMaintenanceSchedulesByAssetCondition returns maintenance schedules for assets with specific condition
func (mm *MaintenanceManager) GetMaintenanceSchedulesByAssetCondition(condition AssetCondition) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		asset, err := mm.facilityManager.GetAsset(schedule.AssetID)
		if err != nil {
			continue
		}
		if asset.Condition == condition {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}

// GetMaintenanceSchedulesByAssetStatus returns maintenance schedules for assets with specific status
func (mm *MaintenanceManager) GetMaintenanceSchedulesByAssetStatus(status AssetStatus) []*MaintenanceSchedule {
	var schedules []*MaintenanceSchedule
	for _, schedule := range mm.schedules {
		asset, err := mm.facilityManager.GetAsset(schedule.AssetID)
		if err != nil {
			continue
		}
		if asset.Status == status {
			schedules = append(schedules, schedule)
		}
	}
	return schedules
}
