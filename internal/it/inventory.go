package it

import (
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// InventoryManager manages parts and inventory
type InventoryManager struct {
	parts     map[string]*Part
	suppliers map[string]*Supplier
	orders    map[string]*Order
	receipts  map[string]*Receipt
	usage     map[string]*PartUsage
	metrics   *InventoryMetrics
	mu        sync.RWMutex
}

// Supplier represents a parts supplier
type Supplier struct {
	ID            string                 `json:"id"`
	Name          string                 `json:"name"`
	ContactName   string                 `json:"contact_name"`
	Email         string                 `json:"email"`
	Phone         string                 `json:"phone"`
	Address       string                 `json:"address"`
	City          string                 `json:"city"`
	State         string                 `json:"state"`
	ZipCode       string                 `json:"zip_code"`
	Country       string                 `json:"country"`
	Website       string                 `json:"website"`
	PaymentTerms  string                 `json:"payment_terms"`
	ShippingTerms string                 `json:"shipping_terms"`
	Rating        float64                `json:"rating"`
	IsPreferred   bool                   `json:"is_preferred"`
	IsActive      bool                   `json:"is_active"`
	Metadata      map[string]interface{} `json:"metadata"`
	CreatedAt     time.Time              `json:"created_at"`
	UpdatedAt     time.Time              `json:"updated_at"`
}

// Order represents a parts order
type Order struct {
	ID           string                 `json:"id"`
	OrderNumber  string                 `json:"order_number"`
	SupplierID   string                 `json:"supplier_id"`
	Status       OrderStatus            `json:"status"`
	OrderDate    time.Time              `json:"order_date"`
	ExpectedDate *time.Time             `json:"expected_date"`
	ReceivedDate *time.Time             `json:"received_date"`
	Items        []OrderItem            `json:"items"`
	Subtotal     float64                `json:"subtotal"`
	Tax          float64                `json:"tax"`
	Shipping     float64                `json:"shipping"`
	Total        float64                `json:"total"`
	Notes        string                 `json:"notes"`
	CreatedBy    string                 `json:"created_by"`
	ApprovedBy   string                 `json:"approved_by"`
	ApprovedAt   *time.Time             `json:"approved_at"`
	Metadata     map[string]interface{} `json:"metadata"`
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
}

// OrderStatus represents the status of an order
type OrderStatus string

const (
	OrderStatusDraft     OrderStatus = "draft"
	OrderStatusPending   OrderStatus = "pending"
	OrderStatusApproved  OrderStatus = "approved"
	OrderStatusOrdered   OrderStatus = "ordered"
	OrderStatusShipped   OrderStatus = "shipped"
	OrderStatusReceived  OrderStatus = "received"
	OrderStatusCancelled OrderStatus = "cancelled"
	OrderStatusReturned  OrderStatus = "returned"
)

// OrderItem represents an item in an order
type OrderItem struct {
	PartID      string  `json:"part_id"`
	PartNumber  string  `json:"part_number"`
	Description string  `json:"description"`
	Quantity    int     `json:"quantity"`
	UnitPrice   float64 `json:"unit_price"`
	TotalPrice  float64 `json:"total_price"`
	ReceivedQty int     `json:"received_qty"`
	Notes       string  `json:"notes"`
}

// Receipt represents a parts receipt
type Receipt struct {
	ID            string                 `json:"id"`
	OrderID       string                 `json:"order_id"`
	ReceiptNumber string                 `json:"receipt_number"`
	ReceivedDate  time.Time              `json:"received_date"`
	ReceivedBy    string                 `json:"received_by"`
	Items         []ReceiptItem          `json:"items"`
	Condition     string                 `json:"condition"`
	Notes         string                 `json:"notes"`
	Metadata      map[string]interface{} `json:"metadata"`
	CreatedAt     time.Time              `json:"created_at"`
}

// ReceiptItem represents an item in a receipt
type ReceiptItem struct {
	PartID        string   `json:"part_id"`
	PartNumber    string   `json:"part_number"`
	Description   string   `json:"description"`
	OrderedQty    int      `json:"ordered_qty"`
	ReceivedQty   int      `json:"received_qty"`
	UnitPrice     float64  `json:"unit_price"`
	TotalPrice    float64  `json:"total_price"`
	Condition     string   `json:"condition"`
	SerialNumbers []string `json:"serial_numbers"`
	Notes         string   `json:"notes"`
}

// PartUsage represents usage of a part
type PartUsage struct {
	ID          string                 `json:"id"`
	PartID      string                 `json:"part_id"`
	AssetID     string                 `json:"asset_id"`
	WorkOrderID string                 `json:"work_order_id"`
	Quantity    int                    `json:"quantity"`
	Date        time.Time              `json:"date"`
	UsedBy      string                 `json:"used_by"`
	Reason      string                 `json:"reason"`
	Cost        float64                `json:"cost"`
	Notes       string                 `json:"notes"`
	Metadata    map[string]interface{} `json:"metadata"`
	CreatedAt   time.Time              `json:"created_at"`
}

// InventoryMetrics represents inventory management metrics
type InventoryMetrics struct {
	TotalParts        int64   `json:"total_parts"`
	InStockParts      int64   `json:"in_stock_parts"`
	LowStockParts     int64   `json:"low_stock_parts"`
	OutOfStockParts   int64   `json:"out_of_stock_parts"`
	TotalValue        float64 `json:"total_value"`
	TotalSuppliers    int64   `json:"total_suppliers"`
	ActiveSuppliers   int64   `json:"active_suppliers"`
	TotalOrders       int64   `json:"total_orders"`
	PendingOrders     int64   `json:"pending_orders"`
	CompletedOrders   int64   `json:"completed_orders"`
	TotalReceipts     int64   `json:"total_receipts"`
	AverageOrderTime  float64 `json:"average_order_time"`
	InventoryTurnover float64 `json:"inventory_turnover"`
	StockAccuracy     float64 `json:"stock_accuracy"`
}

// NewInventoryManager creates a new inventory manager
func NewInventoryManager() *InventoryManager {
	return &InventoryManager{
		parts:     make(map[string]*Part),
		suppliers: make(map[string]*Supplier),
		orders:    make(map[string]*Order),
		receipts:  make(map[string]*Receipt),
		usage:     make(map[string]*PartUsage),
		metrics:   &InventoryMetrics{},
	}
}

// CreatePart creates a new part
func (im *InventoryManager) CreatePart(part *Part) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if part.ID == "" {
		part.ID = fmt.Sprintf("part_%d", time.Now().UnixNano())
	}

	part.CreatedAt = time.Now()
	part.UpdatedAt = time.Now()

	// Set initial status based on quantity
	if part.Quantity > part.MinQuantity {
		part.Status = PartStatusInStock
	} else if part.Quantity > 0 {
		part.Status = PartStatusLowStock
	} else {
		part.Status = PartStatusOutOfStock
	}

	im.parts[part.ID] = part
	im.metrics.TotalParts++

	logger.Info("Part created: %s", part.ID)
	return nil
}

// GetPart returns a specific part
func (im *InventoryManager) GetPart(partID string) (*Part, error) {
	im.mu.RLock()
	defer im.mu.RUnlock()

	part, exists := im.parts[partID]
	if !exists {
		return nil, fmt.Errorf("part not found: %s", partID)
	}

	return part, nil
}

// UpdatePart updates an existing part
func (im *InventoryManager) UpdatePart(partID string, part *Part) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if _, exists := im.parts[partID]; !exists {
		return fmt.Errorf("part not found: %s", partID)
	}

	part.ID = partID
	part.UpdatedAt = time.Now()

	// Update status based on quantity
	if part.Quantity > part.MinQuantity {
		part.Status = PartStatusInStock
	} else if part.Quantity > 0 {
		part.Status = PartStatusLowStock
	} else {
		part.Status = PartStatusOutOfStock
	}

	im.parts[partID] = part

	logger.Info("Part updated: %s", partID)
	return nil
}

// DeletePart deletes a part
func (im *InventoryManager) DeletePart(partID string) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if _, exists := im.parts[partID]; !exists {
		return fmt.Errorf("part not found: %s", partID)
	}

	delete(im.parts, partID)
	im.metrics.TotalParts--

	logger.Info("Part deleted: %s", partID)
	return nil
}

// GetParts returns all parts with optional filtering
func (im *InventoryManager) GetParts(filter PartFilter) []*Part {
	im.mu.RLock()
	defer im.mu.RUnlock()

	var parts []*Part
	for _, part := range im.parts {
		if im.matchesPartFilter(part, filter) {
			parts = append(parts, part)
		}
	}

	return parts
}

// PartFilter represents filtering criteria for parts
type PartFilter struct {
	Category   string     `json:"category,omitempty"`
	Brand      string     `json:"brand,omitempty"`
	Status     PartStatus `json:"status,omitempty"`
	Supplier   string     `json:"supplier,omitempty"`
	LowStock   bool       `json:"low_stock"`
	OutOfStock bool       `json:"out_of_stock"`
}

// matchesPartFilter checks if a part matches the filter criteria
func (im *InventoryManager) matchesPartFilter(part *Part, filter PartFilter) bool {
	if filter.Category != "" && part.Category != filter.Category {
		return false
	}
	if filter.Brand != "" && part.Brand != filter.Brand {
		return false
	}
	if filter.Status != "" && part.Status != filter.Status {
		return false
	}
	if filter.Supplier != "" && part.Supplier != filter.Supplier {
		return false
	}
	if filter.LowStock && part.Status != PartStatusLowStock {
		return false
	}
	if filter.OutOfStock && part.Status != PartStatusOutOfStock {
		return false
	}
	return true
}

// CreateSupplier creates a new supplier
func (im *InventoryManager) CreateSupplier(supplier *Supplier) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if supplier.ID == "" {
		supplier.ID = fmt.Sprintf("supplier_%d", time.Now().UnixNano())
	}

	supplier.CreatedAt = time.Now()
	supplier.UpdatedAt = time.Now()
	im.suppliers[supplier.ID] = supplier
	im.metrics.TotalSuppliers++

	if supplier.IsActive {
		im.metrics.ActiveSuppliers++
	}

	logger.Info("Supplier created: %s", supplier.ID)
	return nil
}

// GetSupplier returns a specific supplier
func (im *InventoryManager) GetSupplier(supplierID string) (*Supplier, error) {
	im.mu.RLock()
	defer im.mu.RUnlock()

	supplier, exists := im.suppliers[supplierID]
	if !exists {
		return nil, fmt.Errorf("supplier not found: %s", supplierID)
	}

	return supplier, nil
}

// UpdateSupplier updates an existing supplier
func (im *InventoryManager) UpdateSupplier(supplierID string, supplier *Supplier) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if _, exists := im.suppliers[supplierID]; !exists {
		return fmt.Errorf("supplier not found: %s", supplierID)
	}

	supplier.ID = supplierID
	supplier.UpdatedAt = time.Now()
	im.suppliers[supplierID] = supplier

	logger.Info("Supplier updated: %s", supplierID)
	return nil
}

// DeleteSupplier deletes a supplier
func (im *InventoryManager) DeleteSupplier(supplierID string) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	supplier, exists := im.suppliers[supplierID]
	if !exists {
		return fmt.Errorf("supplier not found: %s", supplierID)
	}

	// Update metrics
	im.metrics.TotalSuppliers--
	if supplier.IsActive {
		im.metrics.ActiveSuppliers--
	}

	delete(im.suppliers, supplierID)
	logger.Info("Supplier deleted: %s", supplierID)
	return nil
}

// GetSuppliers returns all suppliers
func (im *InventoryManager) GetSuppliers() []*Supplier {
	im.mu.RLock()
	defer im.mu.RUnlock()

	var suppliers []*Supplier
	for _, supplier := range im.suppliers {
		suppliers = append(suppliers, supplier)
	}

	return suppliers
}

// CreateOrder creates a new order
func (im *InventoryManager) CreateOrder(order *Order) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if order.ID == "" {
		order.ID = fmt.Sprintf("order_%d", time.Now().UnixNano())
	}

	order.CreatedAt = time.Now()
	order.UpdatedAt = time.Now()
	im.orders[order.ID] = order
	im.metrics.TotalOrders++

	if order.Status == OrderStatusPending || order.Status == OrderStatusApproved {
		im.metrics.PendingOrders++
	}

	logger.Info("Order created: %s", order.ID)
	return nil
}

// GetOrder returns a specific order
func (im *InventoryManager) GetOrder(orderID string) (*Order, error) {
	im.mu.RLock()
	defer im.mu.RUnlock()

	order, exists := im.orders[orderID]
	if !exists {
		return nil, fmt.Errorf("order not found: %s", orderID)
	}

	return order, nil
}

// UpdateOrder updates an existing order
func (im *InventoryManager) UpdateOrder(orderID string, order *Order) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if _, exists := im.orders[orderID]; !exists {
		return fmt.Errorf("order not found: %s", orderID)
	}

	order.ID = orderID
	order.UpdatedAt = time.Now()
	im.orders[orderID] = order

	logger.Info("Order updated: %s", orderID)
	return nil
}

// DeleteOrder deletes an order
func (im *InventoryManager) DeleteOrder(orderID string) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	order, exists := im.orders[orderID]
	if !exists {
		return fmt.Errorf("order not found: %s", orderID)
	}

	// Update metrics
	im.metrics.TotalOrders--
	if order.Status == OrderStatusPending || order.Status == OrderStatusApproved {
		im.metrics.PendingOrders--
	}

	delete(im.orders, orderID)
	logger.Info("Order deleted: %s", orderID)
	return nil
}

// GetOrders returns all orders
func (im *InventoryManager) GetOrders() []*Order {
	im.mu.RLock()
	defer im.mu.RUnlock()

	var orders []*Order
	for _, order := range im.orders {
		orders = append(orders, order)
	}

	return orders
}

// CreateReceipt creates a new receipt
func (im *InventoryManager) CreateReceipt(receipt *Receipt) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if receipt.ID == "" {
		receipt.ID = fmt.Sprintf("receipt_%d", time.Now().UnixNano())
	}

	receipt.CreatedAt = time.Now()
	im.receipts[receipt.ID] = receipt
	im.metrics.TotalReceipts++

	// Update part quantities
	for _, item := range receipt.Items {
		if part, exists := im.parts[item.PartID]; exists {
			part.Quantity += item.ReceivedQty
			part.UpdatedAt = time.Now()

			// Update status based on new quantity
			if part.Quantity > part.MinQuantity {
				part.Status = PartStatusInStock
			} else if part.Quantity > 0 {
				part.Status = PartStatusLowStock
			} else {
				part.Status = PartStatusOutOfStock
			}

			im.parts[item.PartID] = part
		}
	}

	logger.Info("Receipt created: %s", receipt.ID)
	return nil
}

// GetReceipt returns a specific receipt
func (im *InventoryManager) GetReceipt(receiptID string) (*Receipt, error) {
	im.mu.RLock()
	defer im.mu.RUnlock()

	receipt, exists := im.receipts[receiptID]
	if !exists {
		return nil, fmt.Errorf("receipt not found: %s", receiptID)
	}

	return receipt, nil
}

// GetReceipts returns all receipts
func (im *InventoryManager) GetReceipts() []*Receipt {
	im.mu.RLock()
	defer im.mu.RUnlock()

	var receipts []*Receipt
	for _, receipt := range im.receipts {
		receipts = append(receipts, receipt)
	}

	return receipts
}

// RecordPartUsage records usage of a part
func (im *InventoryManager) RecordPartUsage(usage *PartUsage) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	if usage.ID == "" {
		usage.ID = fmt.Sprintf("usage_%d", time.Now().UnixNano())
	}

	usage.CreatedAt = time.Now()
	im.usage[usage.ID] = usage

	// Update part quantity
	if part, exists := im.parts[usage.PartID]; exists {
		part.Quantity -= usage.Quantity
		part.UpdatedAt = time.Now()

		// Update status based on new quantity
		if part.Quantity > part.MinQuantity {
			part.Status = PartStatusInStock
		} else if part.Quantity > 0 {
			part.Status = PartStatusLowStock
		} else {
			part.Status = PartStatusOutOfStock
		}

		im.parts[usage.PartID] = part
	}

	logger.Info("Part usage recorded: %s", usage.ID)
	return nil
}

// GetPartUsage returns usage records for a part
func (im *InventoryManager) GetPartUsage(partID string) []*PartUsage {
	im.mu.RLock()
	defer im.mu.RUnlock()

	var usage []*PartUsage
	for _, u := range im.usage {
		if u.PartID == partID {
			usage = append(usage, u)
		}
	}

	return usage
}

// GetLowStockParts returns parts that are low in stock
func (im *InventoryManager) GetLowStockParts() []*Part {
	filter := PartFilter{
		LowStock: true,
	}
	return im.GetParts(filter)
}

// GetOutOfStockParts returns parts that are out of stock
func (im *InventoryManager) GetOutOfStockParts() []*Part {
	filter := PartFilter{
		OutOfStock: true,
	}
	return im.GetParts(filter)
}

// GetInventoryMetrics returns inventory management metrics
func (im *InventoryManager) GetInventoryMetrics() *InventoryMetrics {
	im.mu.RLock()
	defer im.mu.RUnlock()

	return im.metrics
}

// UpdateInventoryMetrics updates the inventory metrics
func (im *InventoryManager) UpdateInventoryMetrics() {
	im.mu.Lock()
	defer im.mu.Unlock()

	// Reset counters
	im.metrics.InStockParts = 0
	im.metrics.LowStockParts = 0
	im.metrics.OutOfStockParts = 0
	im.metrics.TotalValue = 0
	im.metrics.PendingOrders = 0
	im.metrics.CompletedOrders = 0

	// Count parts by status
	for _, part := range im.parts {
		switch part.Status {
		case PartStatusInStock:
			im.metrics.InStockParts++
		case PartStatusLowStock:
			im.metrics.LowStockParts++
		case PartStatusOutOfStock:
			im.metrics.OutOfStockParts++
		}
		im.metrics.TotalValue += float64(part.Quantity) * part.UnitPrice
	}

	// Count orders by status
	for _, order := range im.orders {
		switch order.Status {
		case OrderStatusPending, OrderStatusApproved:
			im.metrics.PendingOrders++
		case OrderStatusReceived:
			im.metrics.CompletedOrders++
		}
	}

	// Count active suppliers
	im.metrics.ActiveSuppliers = 0
	for _, supplier := range im.suppliers {
		if supplier.IsActive {
			im.metrics.ActiveSuppliers++
		}
	}

	logger.Debug("Inventory metrics updated")
}

// GenerateReorderReport generates a report of parts that need reordering
func (im *InventoryManager) GenerateReorderReport() []ReorderItem {
	im.mu.RLock()
	defer im.mu.RUnlock()

	var reorderItems []ReorderItem

	for _, part := range im.parts {
		if part.Quantity <= part.MinQuantity && part.Status != PartStatusDiscontinued {
			reorderItems = append(reorderItems, ReorderItem{
				PartID:          part.ID,
				PartNumber:      part.PartNumber,
				Name:            part.Name,
				CurrentQuantity: part.Quantity,
				MinQuantity:     part.MinQuantity,
				MaxQuantity:     part.MaxQuantity,
				SuggestedOrder:  part.MaxQuantity - part.Quantity,
				UnitPrice:       part.UnitPrice,
				TotalCost:       float64(part.MaxQuantity-part.Quantity) * part.UnitPrice,
				Supplier:        part.Supplier,
				LastOrdered:     im.getLastOrderDate(part.ID),
			})
		}
	}

	return reorderItems
}

// ReorderItem represents an item that needs reordering
type ReorderItem struct {
	PartID          string     `json:"part_id"`
	PartNumber      string     `json:"part_number"`
	Name            string     `json:"name"`
	CurrentQuantity int        `json:"current_quantity"`
	MinQuantity     int        `json:"min_quantity"`
	MaxQuantity     int        `json:"max_quantity"`
	SuggestedOrder  int        `json:"suggested_order"`
	UnitPrice       float64    `json:"unit_price"`
	TotalCost       float64    `json:"total_cost"`
	Supplier        string     `json:"supplier"`
	LastOrdered     *time.Time `json:"last_ordered"`
}

// getLastOrderDate gets the last order date for a part
func (im *InventoryManager) getLastOrderDate(partID string) *time.Time {
	var lastOrdered *time.Time

	for _, order := range im.orders {
		for _, item := range order.Items {
			if item.PartID == partID {
				if lastOrdered == nil || order.OrderDate.After(*lastOrdered) {
					lastOrdered = &order.OrderDate
				}
			}
		}
	}

	return lastOrdered
}
