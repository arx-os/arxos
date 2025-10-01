package buildingops

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/google/uuid"
)

// Building Operations

// CreateBuilding creates a new building
func (bom *BuildingOpsManager) CreateBuilding(ctx context.Context, req CreateBuildingRequest) (*Building, error) {
	bom.mu.Lock()
	defer bom.mu.Unlock()

	building := &Building{
		ID:           uuid.New().String(),
		Name:         req.Name,
		Address:      req.Address,
		City:         req.City,
		State:        req.State,
		ZipCode:      req.ZipCode,
		Country:      req.Country,
		BuildingType: req.BuildingType,
		Status:       BuildingStatusActive,
		Floors:       req.Floors,
		TotalArea:    req.TotalArea,
		YearBuilt:    req.YearBuilt,
		Owner:        req.Owner,
		Manager:      req.Manager,
		Spaces:       []string{},
		Assets:       []string{},
		Config:       req.Config,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	bom.buildings[building.ID] = building
	bom.UpdateMetrics()

	logger.Info("Building created", "building_id", building.ID, "name", building.Name)
	return building, nil
}

// GetBuilding retrieves a building by ID
func (bom *BuildingOpsManager) GetBuilding(ctx context.Context, id string) (*Building, error) {
	bom.mu.RLock()
	defer bom.mu.RUnlock()

	building, exists := bom.buildings[id]
	if !exists {
		return nil, fmt.Errorf("building not found: %s", id)
	}

	return building, nil
}

// ListBuildings lists all buildings
func (bom *BuildingOpsManager) ListBuildings(ctx context.Context, filter BuildingFilter) ([]*Building, error) {
	bom.mu.RLock()
	defer bom.mu.RUnlock()

	var buildings []*Building
	for _, building := range bom.buildings {
		if filter.Matches(building) {
			buildings = append(buildings, building)
		}
	}

	return buildings, nil
}

// Asset Operations (Unified Physical + IT)

// CreateAsset creates a new asset (physical or IT)
func (bom *BuildingOpsManager) CreateAsset(ctx context.Context, req CreateAssetRequest) (*Asset, error) {
	bom.mu.Lock()
	defer bom.mu.Unlock()

	asset := &Asset{
		ID:           uuid.New().String(),
		BuildingID:   req.BuildingID,
		SpaceID:      req.SpaceID,
		Name:         req.Name,
		AssetType:    req.AssetType,
		Category:     req.Category,
		SubCategory:  req.SubCategory,
		Manufacturer: req.Manufacturer,
		Model:        req.Model,
		SerialNumber: req.SerialNumber,
		Status:       AssetStatusActive,
		Condition:    req.Condition,
		Value:        req.Value,
		PurchaseDate: req.PurchaseDate,
		WarrantyExpiry: req.WarrantyExpiry,
		Location:     req.Location,
		Notes:        req.Notes,
		Config:       req.Config,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	bom.assets[asset.ID] = asset
	
	// Add asset to building
	if building, exists := bom.buildings[asset.BuildingID]; exists {
		building.Assets = append(building.Assets, asset.ID)
		building.UpdatedAt = time.Now()
	}

	// Add asset to space if specified
	if asset.SpaceID != "" {
		if space, exists := bom.spaces[asset.SpaceID]; exists {
			space.Assets = append(space.Assets, asset.ID)
			space.UpdatedAt = time.Now()
		}
	}

	bom.UpdateMetrics()

	logger.Info("Asset created", "asset_id", asset.ID, "name", asset.Name, "type", asset.AssetType)
	return asset, nil
}

// GetAsset retrieves an asset by ID
func (bom *BuildingOpsManager) GetAsset(ctx context.Context, id string) (*Asset, error) {
	bom.mu.RLock()
	defer bom.mu.RUnlock()

	asset, exists := bom.assets[id]
	if !exists {
		return nil, fmt.Errorf("asset not found: %s", id)
	}

	return asset, nil
}

// ListAssets lists all assets with optional filtering
func (bom *BuildingOpsManager) ListAssets(ctx context.Context, filter AssetFilter) ([]*Asset, error) {
	bom.mu.RLock()
	defer bom.mu.RUnlock()

	var assets []*Asset
	for _, asset := range bom.assets {
		if filter.Matches(asset) {
			assets = append(assets, asset)
		}
	}

	return assets, nil
}

// Work Order Operations (Unified Facility + IT)

// CreateWorkOrder creates a new work order (facility or IT)
func (bom *BuildingOpsManager) CreateWorkOrder(ctx context.Context, req CreateWorkOrderRequest) (*WorkOrder, error) {
	bom.mu.Lock()
	defer bom.mu.Unlock()

	workOrder := &WorkOrder{
		ID:          uuid.New().String(),
		BuildingID:  req.BuildingID,
		SpaceID:     req.SpaceID,
		AssetID:     req.AssetID,
		Title:       req.Title,
		Description: req.Description,
		Category:    req.Category,
		Priority:    req.Priority,
		Status:      WorkOrderStatusOpen,
		AssignedTo:  req.AssignedTo,
		RequestedBy: req.RequestedBy,
		DueDate:     req.DueDate,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	bom.workOrders[workOrder.ID] = workOrder
	bom.UpdateMetrics()

	logger.Info("Work order created", "work_order_id", workOrder.ID, "title", workOrder.Title, "category", workOrder.Category)
	return workOrder, nil
}

// GetWorkOrder retrieves a work order by ID
func (bom *BuildingOpsManager) GetWorkOrder(ctx context.Context, id string) (*WorkOrder, error) {
	bom.mu.RLock()
	defer bom.mu.RUnlock()

	workOrder, exists := bom.workOrders[id]
	if !exists {
		return nil, fmt.Errorf("work order not found: %s", id)
	}

	return workOrder, nil
}

// ListWorkOrders lists all work orders with optional filtering
func (bom *BuildingOpsManager) ListWorkOrders(ctx context.Context, filter WorkOrderFilter) ([]*WorkOrder, error) {
	bom.mu.RLock()
	defer bom.mu.RUnlock()

	var workOrders []*WorkOrder
	for _, workOrder := range bom.workOrders {
		if filter.Matches(workOrder) {
			workOrders = append(workOrders, workOrder)
		}
	}

	return workOrders, nil
}

// UpdateWorkOrderStatus updates a work order's status
func (bom *BuildingOpsManager) UpdateWorkOrderStatus(ctx context.Context, id string, status WorkOrderStatus) error {
	bom.mu.Lock()
	defer bom.mu.Unlock()

	workOrder, exists := bom.workOrders[id]
	if !exists {
		return fmt.Errorf("work order not found: %s", id)
	}

	workOrder.Status = status
	workOrder.UpdatedAt = time.Now()
	
	if status == WorkOrderStatusCompleted {
		workOrder.CompletedAt = time.Now()
	}

	bom.UpdateMetrics()

	logger.Info("Work order status updated", "work_order_id", id, "status", status)
	return nil
}

// IT-Specific Operations

// CreateConfiguration creates a new IT configuration
func (bom *BuildingOpsManager) CreateConfiguration(ctx context.Context, req CreateConfigurationRequest) (*Configuration, error) {
	bom.mu.Lock()
	defer bom.mu.Unlock()

	config := &Configuration{
		ID:         uuid.New().String(),
		BuildingID: req.BuildingID,
		SpaceID:    req.SpaceID,
		Name:       req.Name,
		ConfigType: req.ConfigType,
		Version:    req.Version,
		Status:     "active",
		Config:     req.Config,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	bom.configs[config.ID] = config
	bom.UpdateMetrics()

	logger.Info("Configuration created", "config_id", config.ID, "name", config.Name)
	return config, nil
}

// CreateInventoryItem creates a new inventory item
func (bom *BuildingOpsManager) CreateInventoryItem(ctx context.Context, req CreateInventoryItemRequest) (*InventoryItem, error) {
	bom.mu.Lock()
	defer bom.mu.Unlock()

	item := &InventoryItem{
		ID:         uuid.New().String(),
		Name:       req.Name,
		Category:   req.Category,
		Quantity:   req.Quantity,
		MinStock:   req.MinStock,
		UnitPrice:  req.UnitPrice,
		TotalValue: req.UnitPrice * float64(req.Quantity),
		Location:   req.Location,
		Supplier:   req.Supplier,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	bom.inventory[item.ID] = item
	bom.UpdateMetrics()

	logger.Info("Inventory item created", "item_id", item.ID, "name", item.Name)
	return item, nil
}

// Request Types

type CreateBuildingRequest struct {
	Name         string                 `json:"name"`
	Address      string                 `json:"address"`
	City         string                 `json:"city"`
	State        string                 `json:"state"`
	ZipCode      string                 `json:"zip_code"`
	Country      string                 `json:"country"`
	BuildingType string                 `json:"building_type"`
	Floors       int                    `json:"floors"`
	TotalArea    float64                `json:"total_area"`
	YearBuilt    int                    `json:"year_built"`
	Owner        string                 `json:"owner"`
	Manager      string                 `json:"manager"`
	Config       map[string]interface{} `json:"config"`
}

type CreateAssetRequest struct {
	BuildingID    string                 `json:"building_id"`
	SpaceID       string                 `json:"space_id"`
	Name          string                 `json:"name"`
	AssetType     AssetType              `json:"asset_type"`
	Category      string                 `json:"category"`
	SubCategory   string                 `json:"sub_category"`
	Manufacturer  string                 `json:"manufacturer"`
	Model         string                 `json:"model"`
	SerialNumber  string                 `json:"serial_number"`
	Condition     AssetCondition         `json:"condition"`
	Value         float64                `json:"value"`
	PurchaseDate  time.Time              `json:"purchase_date"`
	WarrantyExpiry time.Time             `json:"warranty_expiry"`
	Location      string                 `json:"location"`
	Notes         string                 `json:"notes"`
	Config        map[string]interface{} `json:"config"`
}

type CreateWorkOrderRequest struct {
	BuildingID  string             `json:"building_id"`
	SpaceID     string             `json:"space_id"`
	AssetID     string             `json:"asset_id"`
	Title       string             `json:"title"`
	Description string             `json:"description"`
	Category    WorkOrderCategory  `json:"category"`
	Priority    WorkOrderPriority  `json:"priority"`
	AssignedTo  string             `json:"assigned_to"`
	RequestedBy string             `json:"requested_by"`
	DueDate     time.Time          `json:"due_date"`
}

type CreateConfigurationRequest struct {
	BuildingID string                 `json:"building_id"`
	SpaceID    string                 `json:"space_id"`
	Name       string                 `json:"name"`
	ConfigType string                 `json:"config_type"`
	Version    string                 `json:"version"`
	Config     map[string]interface{} `json:"config"`
}

type CreateInventoryItemRequest struct {
	Name       string  `json:"name"`
	Category   string  `json:"category"`
	Quantity   int     `json:"quantity"`
	MinStock   int     `json:"min_stock"`
	UnitPrice  float64 `json:"unit_price"`
	Location   string  `json:"location"`
	Supplier   string  `json:"supplier"`
}

// Filter Types

type BuildingFilter struct {
	Status       *BuildingStatus `json:"status"`
	BuildingType *string         `json:"building_type"`
	City         *string         `json:"city"`
	State        *string         `json:"state"`
}

func (f BuildingFilter) Matches(building *Building) bool {
	if f.Status != nil && building.Status != *f.Status {
		return false
	}
	if f.BuildingType != nil && building.BuildingType != *f.BuildingType {
		return false
	}
	if f.City != nil && building.City != *f.City {
		return false
	}
	if f.State != nil && building.State != *f.State {
		return false
	}
	return true
}

type AssetFilter struct {
	AssetType *AssetType `json:"asset_type"`
	Category  *string    `json:"category"`
	Status    *AssetStatus `json:"status"`
	BuildingID *string   `json:"building_id"`
	SpaceID   *string    `json:"space_id"`
}

func (f AssetFilter) Matches(asset *Asset) bool {
	if f.AssetType != nil && asset.AssetType != *f.AssetType {
		return false
	}
	if f.Category != nil && asset.Category != *f.Category {
		return false
	}
	if f.Status != nil && asset.Status != *f.Status {
		return false
	}
	if f.BuildingID != nil && asset.BuildingID != *f.BuildingID {
		return false
	}
	if f.SpaceID != nil && asset.SpaceID != *f.SpaceID {
		return false
	}
	return true
}

type WorkOrderFilter struct {
	Category *WorkOrderCategory `json:"category"`
	Status   *WorkOrderStatus   `json:"status"`
	Priority *WorkOrderPriority `json:"priority"`
	BuildingID *string          `json:"building_id"`
	AssignedTo *string          `json:"assigned_to"`
}

func (f WorkOrderFilter) Matches(workOrder *WorkOrder) bool {
	if f.Category != nil && workOrder.Category != *f.Category {
		return false
	}
	if f.Status != nil && workOrder.Status != *f.Status {
		return false
	}
	if f.Priority != nil && workOrder.Priority != *f.Priority {
		return false
	}
	if f.BuildingID != nil && workOrder.BuildingID != *f.BuildingID {
		return false
	}
	if f.AssignedTo != nil && workOrder.AssignedTo != *f.AssignedTo {
		return false
	}
	return true
}
