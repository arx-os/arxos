package facility

import (
	"fmt"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// WorkOrderManager manages work orders and maintenance operations
type WorkOrderManager struct {
	facilityManager *FacilityManager
	workOrders      map[string]*WorkOrder
	assignments     map[string][]string // technician -> work order IDs
	priorities      map[WorkOrderPriority]int
	metrics         *WorkOrderMetrics
}

// WorkOrderMetrics tracks work order performance
type WorkOrderMetrics struct {
	TotalWorkOrders        int64   `json:"total_work_orders"`
	OpenWorkOrders         int64   `json:"open_work_orders"`
	InProgressWorkOrders   int64   `json:"in_progress_work_orders"`
	CompletedWorkOrders    int64   `json:"completed_work_orders"`
	CancelledWorkOrders    int64   `json:"cancelled_work_orders"`
	OverdueWorkOrders      int64   `json:"overdue_work_orders"`
	AverageResponseTime    float64 `json:"average_response_time"`
	AvgResolutionTimeHours float64 `json:"avg_resolution_time_hours"`
	AverageCompletionTime  float64 `json:"average_completion_time"`
	CostSavings            float64 `json:"cost_savings"`
	Efficiency             float64 `json:"efficiency"`
}

// NewWorkOrderManager creates a new work order manager
func NewWorkOrderManager(facilityManager *FacilityManager) *WorkOrderManager {
	return &WorkOrderManager{
		facilityManager: facilityManager,
		workOrders:      make(map[string]*WorkOrder),
		assignments:     make(map[string][]string),
		priorities: map[WorkOrderPriority]int{
			WorkOrderPriorityEmergency: 5,
			WorkOrderPriorityCritical:  4,
			WorkOrderPriorityHigh:      3,
			WorkOrderPriorityMedium:    2,
			WorkOrderPriorityLow:       1,
		},
		metrics: &WorkOrderMetrics{},
	}
}

// CreateWorkOrder creates a new work order
func (wom *WorkOrderManager) CreateWorkOrder(workOrder *WorkOrder) error {
	if workOrder == nil {
		return fmt.Errorf("work order cannot be nil")
	}

	if workOrder.ID == "" {
		workOrder.ID = fmt.Sprintf("wo_%d", time.Now().UnixNano())
	}

	if workOrder.Title == "" {
		return fmt.Errorf("work order title cannot be empty")
	}

	// Validate building exists
	if workOrder.BuildingID != "" {
		if _, exists := wom.facilityManager.buildings[workOrder.BuildingID]; !exists {
			return fmt.Errorf("building %s not found", workOrder.BuildingID)
		}
	}

	// Validate space exists
	if workOrder.SpaceID != "" {
		if _, exists := wom.facilityManager.spaces[workOrder.SpaceID]; !exists {
			return fmt.Errorf("space %s not found", workOrder.SpaceID)
		}
	}

	// Validate asset exists
	if workOrder.AssetID != "" {
		if _, exists := wom.facilityManager.assets[workOrder.AssetID]; !exists {
			return fmt.Errorf("asset %s not found", workOrder.AssetID)
		}
	}

	// Set timestamps
	now := time.Now()
	workOrder.CreatedAt = now
	workOrder.UpdatedAt = now

	// Set default status
	if workOrder.Status == "" {
		workOrder.Status = WorkOrderStatusOpen
	}

	// Set default priority
	if workOrder.Priority == "" {
		workOrder.Priority = WorkOrderPriorityMedium
	}

	// Store work order
	wom.workOrders[workOrder.ID] = workOrder
	wom.metrics.TotalWorkOrders++

	// Update facility manager
	wom.facilityManager.workOrders[workOrder.ID] = workOrder

	logger.Info("Work order created: %s (%s)", workOrder.ID, workOrder.Title)
	return nil
}

// GetWorkOrder retrieves a work order by ID
func (wom *WorkOrderManager) GetWorkOrder(workOrderID string) (*WorkOrder, error) {
	workOrder, exists := wom.workOrders[workOrderID]
	if !exists {
		return nil, fmt.Errorf("work order %s not found", workOrderID)
	}
	return workOrder, nil
}

// UpdateWorkOrder updates an existing work order
func (wom *WorkOrderManager) UpdateWorkOrder(workOrderID string, updates map[string]interface{}) error {
	workOrder, exists := wom.workOrders[workOrderID]
	if !exists {
		return fmt.Errorf("work order %s not found", workOrderID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "title":
			if title, ok := value.(string); ok {
				workOrder.Title = title
			}
		case "description":
			if description, ok := value.(string); ok {
				workOrder.Description = description
			}
		case "status":
			if status, ok := value.(string); ok {
				workOrder.Status = WorkOrderStatus(status)
			}
		case "priority":
			if priority, ok := value.(string); ok {
				workOrder.Priority = WorkOrderPriority(priority)
			}
		case "assigned_to":
			if assignedTo, ok := value.(string); ok {
				// Remove from old assignment
				if workOrder.AssignedTo != "" {
					wom.removeAssignment(workOrder.AssignedTo, workOrderID)
				}
				// Add to new assignment
				workOrder.AssignedTo = assignedTo
				wom.addAssignment(assignedTo, workOrderID)
			}
		case "estimated_cost":
			if cost, ok := value.(float64); ok {
				workOrder.EstimatedCost = cost
			}
		case "actual_cost":
			if cost, ok := value.(float64); ok {
				workOrder.ActualCost = cost
			}
		case "estimated_hours":
			if hours, ok := value.(float64); ok {
				workOrder.EstimatedHours = hours
			}
		case "actual_hours":
			if hours, ok := value.(float64); ok {
				workOrder.ActualHours = hours
			}
		case "scheduled_date":
			if date, ok := value.(time.Time); ok {
				workOrder.ScheduledDate = &date
			}
		case "start_date":
			if date, ok := value.(time.Time); ok {
				workOrder.StartDate = &date
			}
		case "completion_date":
			if date, ok := value.(time.Time); ok {
				workOrder.CompletionDate = &date
			}
		case "due_date":
			if date, ok := value.(time.Time); ok {
				workOrder.DueDate = &date
			}
		case "notes":
			if notes, ok := value.([]string); ok {
				workOrder.Notes = notes
			}
		}
	}

	workOrder.UpdatedAt = time.Now()
	logger.Info("Work order updated: %s", workOrderID)
	return nil
}

// DeleteWorkOrder deletes a work order
func (wom *WorkOrderManager) DeleteWorkOrder(workOrderID string) error {
	workOrder, exists := wom.workOrders[workOrderID]
	if !exists {
		return fmt.Errorf("work order %s not found", workOrderID)
	}

	// Remove from assignments
	if workOrder.AssignedTo != "" {
		wom.removeAssignment(workOrder.AssignedTo, workOrderID)
	}

	// Delete work order
	delete(wom.workOrders, workOrderID)
	delete(wom.facilityManager.workOrders, workOrderID)
	wom.metrics.TotalWorkOrders--

	logger.Info("Work order deleted: %s (%s)", workOrderID, workOrder.Title)
	return nil
}

// ListWorkOrders returns all work orders
func (wom *WorkOrderManager) ListWorkOrders() []*WorkOrder {
	workOrders := make([]*WorkOrder, 0, len(wom.workOrders))
	for _, workOrder := range wom.workOrders {
		workOrders = append(workOrders, workOrder)
	}
	return workOrders
}

// GetWorkOrdersByStatus returns work orders by status
func (wom *WorkOrderManager) GetWorkOrdersByStatus(status WorkOrderStatus) []*WorkOrder {
	var workOrders []*WorkOrder
	for _, workOrder := range wom.workOrders {
		if workOrder.Status == status {
			workOrders = append(workOrders, workOrder)
		}
	}
	return workOrders
}

// GetWorkOrdersByPriority returns work orders by priority
func (wom *WorkOrderManager) GetWorkOrdersByPriority(priority WorkOrderPriority) []*WorkOrder {
	var workOrders []*WorkOrder
	for _, workOrder := range wom.workOrders {
		if workOrder.Priority == priority {
			workOrders = append(workOrders, workOrder)
		}
	}
	return workOrders
}

// GetWorkOrdersByBuilding returns work orders for a specific building
func (wom *WorkOrderManager) GetWorkOrdersByBuilding(buildingID string) []*WorkOrder {
	var workOrders []*WorkOrder
	for _, workOrder := range wom.workOrders {
		if workOrder.BuildingID == buildingID {
			workOrders = append(workOrders, workOrder)
		}
	}
	return workOrders
}

// GetWorkOrdersBySpace returns work orders for a specific space
func (wom *WorkOrderManager) GetWorkOrdersBySpace(spaceID string) []*WorkOrder {
	var workOrders []*WorkOrder
	for _, workOrder := range wom.workOrders {
		if workOrder.SpaceID == spaceID {
			workOrders = append(workOrders, workOrder)
		}
	}
	return workOrders
}

// GetWorkOrdersByAsset returns work orders for a specific asset
func (wom *WorkOrderManager) GetWorkOrdersByAsset(assetID string) []*WorkOrder {
	var workOrders []*WorkOrder
	for _, workOrder := range wom.workOrders {
		if workOrder.AssetID == assetID {
			workOrders = append(workOrders, workOrder)
		}
	}
	return workOrders
}

// GetWorkOrdersByTechnician returns work orders assigned to a specific technician
func (wom *WorkOrderManager) GetWorkOrdersByTechnician(technicianID string) []*WorkOrder {
	var workOrders []*WorkOrder
	for _, workOrder := range wom.workOrders {
		if workOrder.AssignedTo == technicianID {
			workOrders = append(workOrders, workOrder)
		}
	}
	return workOrders
}

// AssignWorkOrder assigns a work order to a technician
func (wom *WorkOrderManager) AssignWorkOrder(workOrderID, technicianID string) error {
	workOrder, exists := wom.workOrders[workOrderID]
	if !exists {
		return fmt.Errorf("work order %s not found", workOrderID)
	}

	// Remove from old assignment
	if workOrder.AssignedTo != "" {
		wom.removeAssignment(workOrder.AssignedTo, workOrderID)
	}

	// Assign to new technician
	workOrder.AssignedTo = technicianID
	workOrder.Status = WorkOrderStatusAssigned
	workOrder.UpdatedAt = time.Now()

	// Add to new assignment
	wom.addAssignment(technicianID, workOrderID)

	logger.Info("Work order %s assigned to technician %s", workOrderID, technicianID)
	return nil
}

// StartWorkOrder starts a work order
func (wom *WorkOrderManager) StartWorkOrder(workOrderID string) error {
	workOrder, exists := wom.workOrders[workOrderID]
	if !exists {
		return fmt.Errorf("work order %s not found", workOrderID)
	}

	if workOrder.Status != WorkOrderStatusAssigned {
		return fmt.Errorf("work order must be assigned before starting")
	}

	now := time.Now()
	workOrder.Status = WorkOrderStatusInProgress
	workOrder.StartDate = &now
	workOrder.UpdatedAt = now

	logger.Info("Work order %s started", workOrderID)
	return nil
}

// CompleteWorkOrder completes a work order
func (wom *WorkOrderManager) CompleteWorkOrder(workOrderID string, notes []string) error {
	workOrder, exists := wom.workOrders[workOrderID]
	if !exists {
		return fmt.Errorf("work order %s not found", workOrderID)
	}

	if workOrder.Status != WorkOrderStatusInProgress {
		return fmt.Errorf("work order must be in progress to complete")
	}

	now := time.Now()
	workOrder.Status = WorkOrderStatusCompleted
	workOrder.CompletionDate = &now
	workOrder.Notes = append(workOrder.Notes, notes...)
	workOrder.UpdatedAt = now

	// Remove from assignments
	if workOrder.AssignedTo != "" {
		wom.removeAssignment(workOrder.AssignedTo, workOrderID)
	}

	logger.Info("Work order %s completed", workOrderID)
	return nil
}

// CancelWorkOrder cancels a work order
func (wom *WorkOrderManager) CancelWorkOrder(workOrderID string, reason string) error {
	workOrder, exists := wom.workOrders[workOrderID]
	if !exists {
		return fmt.Errorf("work order %s not found", workOrderID)
	}

	workOrder.Status = WorkOrderStatusCancelled
	workOrder.Notes = append(workOrder.Notes, fmt.Sprintf("Cancelled: %s", reason))
	workOrder.UpdatedAt = time.Now()

	// Remove from assignments
	if workOrder.AssignedTo != "" {
		wom.removeAssignment(workOrder.AssignedTo, workOrderID)
	}

	logger.Info("Work order %s cancelled: %s", workOrderID, reason)
	return nil
}

// GetOverdueWorkOrders returns overdue work orders
func (wom *WorkOrderManager) GetOverdueWorkOrders() []*WorkOrder {
	var overdueWorkOrders []*WorkOrder
	now := time.Now()

	for _, workOrder := range wom.workOrders {
		if workOrder.DueDate != nil && workOrder.DueDate.Before(now) &&
			(workOrder.Status == WorkOrderStatusOpen || workOrder.Status == WorkOrderStatusAssigned || workOrder.Status == WorkOrderStatusInProgress) {
			overdueWorkOrders = append(overdueWorkOrders, workOrder)
		}
	}

	return overdueWorkOrders
}

// GetUpcomingWorkOrders returns work orders due in the next specified days
func (wom *WorkOrderManager) GetUpcomingWorkOrders(days int) []*WorkOrder {
	var upcomingWorkOrders []*WorkOrder
	now := time.Now()
	cutoff := now.AddDate(0, 0, days)

	for _, workOrder := range wom.workOrders {
		if workOrder.DueDate != nil && workOrder.DueDate.After(now) && workOrder.DueDate.Before(cutoff) &&
			(workOrder.Status == WorkOrderStatusOpen || workOrder.Status == WorkOrderStatusAssigned) {
			upcomingWorkOrders = append(upcomingWorkOrders, workOrder)
		}
	}

	return upcomingWorkOrders
}

// GetWorkOrdersByDateRange returns work orders within a date range
func (wom *WorkOrderManager) GetWorkOrdersByDateRange(startDate, endDate time.Time) []*WorkOrder {
	var workOrders []*WorkOrder

	for _, workOrder := range wom.workOrders {
		if workOrder.CreatedAt.After(startDate) && workOrder.CreatedAt.Before(endDate) {
			workOrders = append(workOrders, workOrder)
		}
	}

	return workOrders
}

// GetWorkOrderStatistics returns work order statistics
func (wom *WorkOrderManager) GetWorkOrderStatistics() map[string]interface{} {
	stats := make(map[string]interface{})

	// Count by status
	statusCounts := make(map[WorkOrderStatus]int)
	for _, workOrder := range wom.workOrders {
		statusCounts[workOrder.Status]++
	}
	stats["status_counts"] = statusCounts

	// Count by priority
	priorityCounts := make(map[WorkOrderPriority]int)
	for _, workOrder := range wom.workOrders {
		priorityCounts[workOrder.Priority]++
	}
	stats["priority_counts"] = priorityCounts

	// Count by type
	typeCounts := make(map[WorkOrderType]int)
	for _, workOrder := range wom.workOrders {
		typeCounts[workOrder.Type]++
	}
	stats["type_counts"] = typeCounts

	// Calculate averages
	var totalCost, totalHours float64
	var completedCount int

	for _, workOrder := range wom.workOrders {
		totalCost += workOrder.ActualCost
		totalHours += workOrder.ActualHours
		if workOrder.Status == WorkOrderStatusCompleted {
			completedCount++
		}
	}

	if completedCount > 0 {
		stats["average_cost"] = totalCost / float64(completedCount)
		stats["average_hours"] = totalHours / float64(completedCount)
	}

	stats["total_work_orders"] = len(wom.workOrders)
	stats["completed_work_orders"] = completedCount
	stats["overdue_work_orders"] = len(wom.GetOverdueWorkOrders())

	return stats
}

// GetTechnicianWorkload returns workload for a technician
func (wom *WorkOrderManager) GetTechnicianWorkload(technicianID string) map[string]interface{} {
	workload := make(map[string]interface{})

	workOrders := wom.GetWorkOrdersByTechnician(technicianID)

	// Count by status
	statusCounts := make(map[WorkOrderStatus]int)
	for _, workOrder := range workOrders {
		statusCounts[workOrder.Status]++
	}
	workload["status_counts"] = statusCounts

	// Count by priority
	priorityCounts := make(map[WorkOrderPriority]int)
	for _, workOrder := range workOrders {
		priorityCounts[workOrder.Priority]++
	}
	workload["priority_counts"] = priorityCounts

	// Calculate total hours
	var totalHours float64
	for _, workOrder := range workOrders {
		totalHours += workOrder.ActualHours
	}
	workload["total_hours"] = totalHours

	workload["total_work_orders"] = len(workOrders)
	workload["overdue_work_orders"] = len(wom.getOverdueWorkOrdersForTechnician(technicianID))

	return workload
}

// GetWorkOrderMetrics returns work order metrics
func (wom *WorkOrderManager) GetWorkOrderMetrics() *WorkOrderMetrics {
	// Update metrics
	wom.metrics.TotalWorkOrders = int64(len(wom.workOrders))

	// Count open work orders
	wom.metrics.OpenWorkOrders = 0
	wom.metrics.CompletedWorkOrders = 0
	wom.metrics.OverdueWorkOrders = 0
	now := time.Now()

	for _, workOrder := range wom.workOrders {
		switch workOrder.Status {
		case WorkOrderStatusOpen, WorkOrderStatusAssigned, WorkOrderStatusInProgress:
			wom.metrics.OpenWorkOrders++
			if workOrder.DueDate != nil && workOrder.DueDate.Before(now) {
				wom.metrics.OverdueWorkOrders++
			}
		case WorkOrderStatusCompleted, WorkOrderStatusClosed:
			wom.metrics.CompletedWorkOrders++
		}
	}

	// Calculate average response time
	var totalResponseTime time.Duration
	var responseCount int

	for _, workOrder := range wom.workOrders {
		if workOrder.StartDate != nil && workOrder.CreatedAt.Before(*workOrder.StartDate) {
			responseTime := workOrder.StartDate.Sub(workOrder.CreatedAt)
			totalResponseTime += responseTime
			responseCount++
		}
	}

	if responseCount > 0 {
		wom.metrics.AverageResponseTime = totalResponseTime.Seconds() / float64(responseCount)
	}

	// Calculate average completion time
	var totalCompletionTime time.Duration
	var completionCount int

	for _, workOrder := range wom.workOrders {
		if workOrder.CompletionDate != nil && workOrder.StartDate != nil {
			completionTime := workOrder.CompletionDate.Sub(*workOrder.StartDate)
			totalCompletionTime += completionTime
			completionCount++
		}
	}

	if completionCount > 0 {
		wom.metrics.AverageCompletionTime = totalCompletionTime.Seconds() / float64(completionCount)
	}

	// Calculate efficiency (completed vs total)
	if wom.metrics.TotalWorkOrders > 0 {
		wom.metrics.Efficiency = float64(wom.metrics.CompletedWorkOrders) / float64(wom.metrics.TotalWorkOrders) * 100
	}

	return wom.metrics
}

// Helper methods

func (wom *WorkOrderManager) addAssignment(technicianID, workOrderID string) {
	if wom.assignments[technicianID] == nil {
		wom.assignments[technicianID] = make([]string, 0)
	}
	wom.assignments[technicianID] = append(wom.assignments[technicianID], workOrderID)
}

func (wom *WorkOrderManager) removeAssignment(technicianID, workOrderID string) {
	if assignments, exists := wom.assignments[technicianID]; exists {
		for i, id := range assignments {
			if id == workOrderID {
				wom.assignments[technicianID] = append(assignments[:i], assignments[i+1:]...)
				break
			}
		}
	}
}

func (wom *WorkOrderManager) getOverdueWorkOrdersForTechnician(technicianID string) []*WorkOrder {
	var overdueWorkOrders []*WorkOrder
	now := time.Now()

	for _, workOrder := range wom.workOrders {
		if workOrder.AssignedTo == technicianID &&
			workOrder.DueDate != nil && workOrder.DueDate.Before(now) &&
			(workOrder.Status == WorkOrderStatusOpen || workOrder.Status == WorkOrderStatusAssigned || workOrder.Status == WorkOrderStatusInProgress) {
			overdueWorkOrders = append(overdueWorkOrders, workOrder)
		}
	}

	return overdueWorkOrders
}

// SortWorkOrdersByPriority sorts work orders by priority
func (wom *WorkOrderManager) SortWorkOrdersByPriority(workOrders []*WorkOrder) []*WorkOrder {
	sort.Slice(workOrders, func(i, j int) bool {
		return wom.priorities[workOrders[i].Priority] > wom.priorities[workOrders[j].Priority]
	})
	return workOrders
}

// SortWorkOrdersByDueDate sorts work orders by due date
func (wom *WorkOrderManager) SortWorkOrdersByDueDate(workOrders []*WorkOrder) []*WorkOrder {
	sort.Slice(workOrders, func(i, j int) bool {
		if workOrders[i].DueDate == nil {
			return false
		}
		if workOrders[j].DueDate == nil {
			return true
		}
		return workOrders[i].DueDate.Before(*workOrders[j].DueDate)
	})
	return workOrders
}
