package it

import (
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ITWorkOrderManager manages IT work orders
type ITWorkOrderManager struct {
	workOrders      map[string]*ITWorkOrder
	maintenanceLogs map[string]*MaintenanceLog
	metrics         *ITWorkOrderMetrics
	mu              sync.RWMutex
}

// ITWorkOrderMetrics represents work order management metrics
type ITWorkOrderMetrics struct {
	TotalWorkOrders       int64            `json:"total_work_orders"`
	OpenWorkOrders        int64            `json:"open_work_orders"`
	InProgressWorkOrders  int64            `json:"in_progress_work_orders"`
	CompletedWorkOrders   int64            `json:"completed_work_orders"`
	CancelledWorkOrders   int64            `json:"cancelled_work_orders"`
	AverageResolutionTime float64          `json:"average_resolution_time"`
	PriorityDistribution  map[string]int64 `json:"priority_distribution"`
	TypeDistribution      map[string]int64 `json:"type_distribution"`
}

// NewITWorkOrderManager creates a new IT work order manager
func NewITWorkOrderManager() *ITWorkOrderManager {
	return &ITWorkOrderManager{
		workOrders:      make(map[string]*ITWorkOrder),
		maintenanceLogs: make(map[string]*MaintenanceLog),
		metrics:         &ITWorkOrderMetrics{},
	}
}

// CreateWorkOrder creates a new work order
func (wom *ITWorkOrderManager) CreateWorkOrder(workOrder *ITWorkOrder) error {
	wom.mu.Lock()
	defer wom.mu.Unlock()

	if workOrder.ID == "" {
		workOrder.ID = fmt.Sprintf("wo_%d", time.Now().UnixNano())
	}

	workOrder.CreatedAt = time.Now()
	workOrder.UpdatedAt = time.Now()
	wom.workOrders[workOrder.ID] = workOrder
	wom.metrics.TotalWorkOrders++

	if workOrder.Status == WorkOrderStatusOpen {
		wom.metrics.OpenWorkOrders++
	}

	logger.Info("Work order created: %s", workOrder.ID)
	return nil
}

// GetWorkOrder returns a specific work order
func (wom *ITWorkOrderManager) GetWorkOrder(workOrderID string) (*ITWorkOrder, error) {
	wom.mu.RLock()
	defer wom.mu.RUnlock()

	workOrder, exists := wom.workOrders[workOrderID]
	if !exists {
		return nil, fmt.Errorf("work order not found: %s", workOrderID)
	}

	return workOrder, nil
}

// UpdateWorkOrder updates an existing work order
func (wom *ITWorkOrderManager) UpdateWorkOrder(workOrderID string, workOrder *ITWorkOrder) error {
	wom.mu.Lock()
	defer wom.mu.Unlock()

	if _, exists := wom.workOrders[workOrderID]; !exists {
		return fmt.Errorf("work order not found: %s", workOrderID)
	}

	workOrder.ID = workOrderID
	workOrder.UpdatedAt = time.Now()
	wom.workOrders[workOrderID] = workOrder

	logger.Info("Work order updated: %s", workOrderID)
	return nil
}

// DeleteWorkOrder deletes a work order
func (wom *ITWorkOrderManager) DeleteWorkOrder(workOrderID string) error {
	wom.mu.Lock()
	defer wom.mu.Unlock()

	workOrder, exists := wom.workOrders[workOrderID]
	if !exists {
		return fmt.Errorf("work order not found: %s", workOrderID)
	}

	// Update metrics
	wom.metrics.TotalWorkOrders--
	switch workOrder.Status {
	case WorkOrderStatusOpen:
		wom.metrics.OpenWorkOrders--
	case WorkOrderStatusInProgress:
		wom.metrics.InProgressWorkOrders--
	case WorkOrderStatusCompleted:
		wom.metrics.CompletedWorkOrders--
	case WorkOrderStatusCancelled:
		wom.metrics.CancelledWorkOrders--
	}

	delete(wom.workOrders, workOrderID)
	logger.Info("Work order deleted: %s", workOrderID)
	return nil
}

// GetWorkOrders returns all work orders with optional filtering
func (wom *ITWorkOrderManager) GetWorkOrders(filter WorkOrderFilter) []*ITWorkOrder {
	wom.mu.RLock()
	defer wom.mu.RUnlock()

	var workOrders []*ITWorkOrder
	for _, workOrder := range wom.workOrders {
		if wom.matchesWorkOrderFilter(workOrder, filter) {
			workOrders = append(workOrders, workOrder)
		}
	}

	return workOrders
}

// WorkOrderFilter represents filtering criteria for work orders
type WorkOrderFilter struct {
	Status      WorkOrderStatus `json:"status,omitempty"`
	Type        WorkOrderType   `json:"type,omitempty"`
	Priority    Priority        `json:"priority,omitempty"`
	AssignedTo  string          `json:"assigned_to,omitempty"`
	RequestedBy string          `json:"requested_by,omitempty"`
	Building    string          `json:"building,omitempty"`
	Room        string          `json:"room,omitempty"`
}

// matchesWorkOrderFilter checks if a work order matches the filter criteria
func (wom *ITWorkOrderManager) matchesWorkOrderFilter(workOrder *ITWorkOrder, filter WorkOrderFilter) bool {
	if filter.Status != "" && workOrder.Status != filter.Status {
		return false
	}
	if filter.Type != "" && workOrder.Type != filter.Type {
		return false
	}
	if filter.Priority != "" && workOrder.Priority != filter.Priority {
		return false
	}
	if filter.AssignedTo != "" && workOrder.AssignedTo != filter.AssignedTo {
		return false
	}
	if filter.RequestedBy != "" && workOrder.RequestedBy != filter.RequestedBy {
		return false
	}
	if filter.Building != "" && workOrder.Location.Building != filter.Building {
		return false
	}
	if filter.Room != "" && workOrder.Location.Room != filter.Room {
		return false
	}
	return true
}

// GetWorkOrderMetrics returns work order management metrics
func (wom *ITWorkOrderManager) GetWorkOrderMetrics() *ITWorkOrderMetrics {
	wom.mu.RLock()
	defer wom.mu.RUnlock()

	return wom.metrics
}

// UpdateWorkOrderMetrics updates the work order metrics
func (wom *ITWorkOrderManager) UpdateWorkOrderMetrics() {
	wom.mu.Lock()
	defer wom.mu.Unlock()

	// Reset counters
	wom.metrics.OpenWorkOrders = 0
	wom.metrics.InProgressWorkOrders = 0
	wom.metrics.CompletedWorkOrders = 0
	wom.metrics.CancelledWorkOrders = 0
	wom.metrics.PriorityDistribution = make(map[string]int64)
	wom.metrics.TypeDistribution = make(map[string]int64)

	// Count work orders by status and type
	for _, workOrder := range wom.workOrders {
		switch workOrder.Status {
		case WorkOrderStatusOpen:
			wom.metrics.OpenWorkOrders++
		case WorkOrderStatusInProgress:
			wom.metrics.InProgressWorkOrders++
		case WorkOrderStatusCompleted:
			wom.metrics.CompletedWorkOrders++
		case WorkOrderStatusCancelled:
			wom.metrics.CancelledWorkOrders++
		}

		// Count by priority
		wom.metrics.PriorityDistribution[string(workOrder.Priority)]++

		// Count by type
		wom.metrics.TypeDistribution[string(workOrder.Type)]++
	}

	logger.Debug("Work order metrics updated")
}
