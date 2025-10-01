package buildingops

import (
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// BuildingOpsManager manages all building operations - physical and IT infrastructure
type BuildingOpsManager struct {
	buildings   map[string]*Building
	spaces      map[string]*Space
	assets      map[string]*Asset     // Unified: physical + IT assets
	workOrders  map[string]*WorkOrder // Unified: facility + IT work orders
	maintenance map[string]*MaintenanceSchedule
	inspections map[string]*Inspection
	vendors     map[string]*Vendor
	contracts   map[string]*Contract
	configs     map[string]*Configuration // IT configurations
	inventory   map[string]*InventoryItem // IT inventory
	metrics     *BuildingOpsMetrics
	mu          sync.RWMutex
}

// BuildingOpsMetrics represents unified building operations metrics
type BuildingOpsMetrics struct {
	// Building metrics
	TotalBuildings  int64 `json:"total_buildings"`
	ActiveBuildings int64 `json:"active_buildings"`
	TotalSpaces     int64 `json:"total_spaces"`
	OccupiedSpaces  int64 `json:"occupied_spaces"`

	// Asset metrics (physical + IT)
	TotalAssets    int64 `json:"total_assets"`
	PhysicalAssets int64 `json:"physical_assets"`
	ITAssets       int64 `json:"it_assets"`
	ActiveAssets   int64 `json:"active_assets"`

	// Work order metrics (facility + IT)
	TotalWorkOrders    int64 `json:"total_work_orders"`
	FacilityWorkOrders int64 `json:"facility_work_orders"`
	ITWorkOrders       int64 `json:"it_work_orders"`
	OpenWorkOrders     int64 `json:"open_work_orders"`

	// IT-specific metrics
	TotalConfigurations int64 `json:"total_configurations"`
	TotalInventoryItems int64 `json:"total_inventory_items"`
	LowStockItems       int64 `json:"low_stock_items"`

	// Financial metrics
	TotalAssetValue    float64 `json:"total_asset_value"`
	PhysicalAssetValue float64 `json:"physical_asset_value"`
	ITAssetValue       float64 `json:"it_asset_value"`

	// Performance metrics
	AssetUtilization    float64 `json:"asset_utilization"`
	WorkOrderEfficiency float64 `json:"work_order_efficiency"`
	InventoryAccuracy   float64 `json:"inventory_accuracy"`
	BuildingOccupancy   float64 `json:"building_occupancy"`
}

// NewBuildingOpsManager creates a new unified building operations manager
func NewBuildingOpsManager() *BuildingOpsManager {
	return &BuildingOpsManager{
		buildings:   make(map[string]*Building),
		spaces:      make(map[string]*Space),
		assets:      make(map[string]*Asset),
		workOrders:  make(map[string]*WorkOrder),
		maintenance: make(map[string]*MaintenanceSchedule),
		inspections: make(map[string]*Inspection),
		vendors:     make(map[string]*Vendor),
		contracts:   make(map[string]*Contract),
		configs:     make(map[string]*Configuration),
		inventory:   make(map[string]*InventoryItem),
		metrics:     &BuildingOpsMetrics{},
	}
}

// GetMetrics returns unified building operations metrics
func (bom *BuildingOpsManager) GetMetrics() *BuildingOpsMetrics {
	bom.mu.RLock()
	defer bom.mu.RUnlock()
	return bom.metrics
}

// UpdateMetrics updates all building operations metrics
func (bom *BuildingOpsManager) UpdateMetrics() {
	bom.mu.Lock()
	defer bom.mu.Unlock()

	// Reset counters
	bom.metrics = &BuildingOpsMetrics{}

	// Count buildings and spaces
	for _, building := range bom.buildings {
		bom.metrics.TotalBuildings++
		if building.Status == BuildingStatusActive {
			bom.metrics.ActiveBuildings++
		}
	}

	for _, space := range bom.spaces {
		bom.metrics.TotalSpaces++
		if space.Occupancy > 0 {
			bom.metrics.OccupiedSpaces++
		}
	}

	// Count assets (physical + IT)
	for _, asset := range bom.assets {
		bom.metrics.TotalAssets++
		if asset.Status == AssetStatusActive {
			bom.metrics.ActiveAssets++
		}

		bom.metrics.TotalAssetValue += asset.Value

		switch asset.AssetType {
		case AssetTypePhysical:
			bom.metrics.PhysicalAssets++
			bom.metrics.PhysicalAssetValue += asset.Value
		case AssetTypeIT:
			bom.metrics.ITAssets++
			bom.metrics.ITAssetValue += asset.Value
		}
	}

	// Count work orders (facility + IT)
	for _, workOrder := range bom.workOrders {
		bom.metrics.TotalWorkOrders++
		if workOrder.Status == WorkOrderStatusOpen {
			bom.metrics.OpenWorkOrders++
		}

		switch workOrder.Category {
		case WorkOrderCategoryFacility:
			bom.metrics.FacilityWorkOrders++
		case WorkOrderCategoryIT:
			bom.metrics.ITWorkOrders++
		}
	}

	// Count IT-specific items
	for range bom.configs {
		bom.metrics.TotalConfigurations++
	}

	for _, item := range bom.inventory {
		bom.metrics.TotalInventoryItems++
		if item.Quantity <= item.MinStock {
			bom.metrics.LowStockItems++
		}
	}

	// Calculate performance metrics
	if bom.metrics.TotalAssets > 0 {
		bom.metrics.AssetUtilization = float64(bom.metrics.ActiveAssets) / float64(bom.metrics.TotalAssets) * 100
	}

	if bom.metrics.TotalSpaces > 0 {
		bom.metrics.BuildingOccupancy = float64(bom.metrics.OccupiedSpaces) / float64(bom.metrics.TotalSpaces) * 100
	}

	logger.Info("Building operations metrics updated",
		"total_buildings", bom.metrics.TotalBuildings,
		"total_assets", bom.metrics.TotalAssets,
		"total_work_orders", bom.metrics.TotalWorkOrders)
}

// Building represents a physical building
type Building struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Address      string                 `json:"address"`
	City         string                 `json:"city"`
	State        string                 `json:"state"`
	ZipCode      string                 `json:"zip_code"`
	Country      string                 `json:"country"`
	BuildingType string                 `json:"building_type"`
	Status       BuildingStatus         `json:"status"`
	Floors       int                    `json:"floors"`
	TotalArea    float64                `json:"total_area"` // Square feet
	YearBuilt    int                    `json:"year_built"`
	Owner        string                 `json:"owner"`
	Manager      string                 `json:"manager"`
	Spaces       []string               `json:"spaces"` // Space IDs
	Assets       []string               `json:"assets"` // Asset IDs (physical + IT)
	Config       map[string]interface{} `json:"config"`
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
}

// BuildingStatus represents the operational status of a building
type BuildingStatus string

const (
	BuildingStatusActive      = BuildingStatus("active")
	BuildingStatusInactive    = BuildingStatus("inactive")
	BuildingStatusMaintenance = BuildingStatus("maintenance")
	BuildingStatusRenovation  = BuildingStatus("renovation")
	BuildingStatusClosed      = BuildingStatus("closed")
)

// Space represents a space within a building
type Space struct {
	ID         string                 `json:"id"`
	BuildingID string                 `json:"building_id"`
	Name       string                 `json:"name"`
	SpaceType  string                 `json:"space_type"`
	Floor      int                    `json:"floor"`
	Area       float64                `json:"area"` // Square feet
	Capacity   int                    `json:"capacity"`
	Status     SpaceStatus            `json:"status"`
	Occupancy  int                    `json:"occupancy"`
	Assets     []string               `json:"assets"` // Asset IDs (physical + IT)
	Config     map[string]interface{} `json:"config"`
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
}

// SpaceStatus represents the status of a space
type SpaceStatus string

const (
	SpaceStatusAvailable   = SpaceStatus("available")
	SpaceStatusOccupied    = SpaceStatus("occupied")
	SpaceStatusMaintenance = SpaceStatus("maintenance")
	SpaceStatusClosed      = SpaceStatus("closed")
)

// Asset represents a unified asset (physical or IT)
type Asset struct {
	ID             string                 `json:"id"`
	BuildingID     string                 `json:"building_id"`
	SpaceID        string                 `json:"space_id"`
	Name           string                 `json:"name"`
	AssetType      AssetType              `json:"asset_type"` // Physical or IT
	Category       string                 `json:"category"`
	SubCategory    string                 `json:"sub_category"`
	Manufacturer   string                 `json:"manufacturer"`
	Model          string                 `json:"model"`
	SerialNumber   string                 `json:"serial_number"`
	Status         AssetStatus            `json:"status"`
	Condition      AssetCondition         `json:"condition"`
	Value          float64                `json:"value"`
	PurchaseDate   time.Time              `json:"purchase_date"`
	WarrantyExpiry time.Time              `json:"warranty_expiry"`
	Location       string                 `json:"location"`
	Notes          string                 `json:"notes"`
	Config         map[string]interface{} `json:"config"`
	CreatedAt      time.Time              `json:"created_at"`
	UpdatedAt      time.Time              `json:"updated_at"`
}

// AssetType represents the type of asset
type AssetType string

const (
	AssetTypePhysical = AssetType("physical") // HVAC, electrical, plumbing, etc.
	AssetTypeIT       = AssetType("it")       // servers, networking, security, etc.
)

// AssetStatus represents the operational status of an asset
type AssetStatus string

const (
	AssetStatusActive      = AssetStatus("active")
	AssetStatusInactive    = AssetStatus("inactive")
	AssetStatusMaintenance = AssetStatus("maintenance")
	AssetStatusRetired     = AssetStatus("retired")
)

// AssetCondition represents the physical condition of an asset
type AssetCondition string

const (
	AssetConditionExcellent = AssetCondition("excellent")
	AssetConditionGood      = AssetCondition("good")
	AssetConditionFair      = AssetCondition("fair")
	AssetConditionPoor      = AssetCondition("poor")
	AssetConditionCritical  = AssetCondition("critical")
)

// WorkOrder represents a unified work order (facility or IT)
type WorkOrder struct {
	ID          string            `json:"id"`
	BuildingID  string            `json:"building_id"`
	SpaceID     string            `json:"space_id"`
	AssetID     string            `json:"asset_id"` // Can be physical or IT asset
	Title       string            `json:"title"`
	Description string            `json:"description"`
	Category    WorkOrderCategory `json:"category"` // Facility or IT
	Priority    WorkOrderPriority `json:"priority"`
	Status      WorkOrderStatus   `json:"status"`
	AssignedTo  string            `json:"assigned_to"`
	RequestedBy string            `json:"requested_by"`
	DueDate     time.Time         `json:"due_date"`
	CompletedAt time.Time         `json:"completed_at"`
	CreatedAt   time.Time         `json:"created_at"`
	UpdatedAt   time.Time         `json:"updated_at"`
}

// WorkOrderCategory represents the category of work order
type WorkOrderCategory string

const (
	WorkOrderCategoryFacility = WorkOrderCategory("facility") // HVAC, electrical, plumbing, etc.
	WorkOrderCategoryIT       = WorkOrderCategory("it")       // servers, networking, security, etc.
)

// WorkOrderPriority represents the priority level of a work order
type WorkOrderPriority string

const (
	WorkOrderPriorityLow      = WorkOrderPriority("low")
	WorkOrderPriorityMedium   = WorkOrderPriority("medium")
	WorkOrderPriorityHigh     = WorkOrderPriority("high")
	WorkOrderPriorityCritical = WorkOrderPriority("critical")
)

// WorkOrderStatus represents the status of a work order
type WorkOrderStatus string

const (
	WorkOrderStatusOpen       = WorkOrderStatus("open")
	WorkOrderStatusInProgress = WorkOrderStatus("in_progress")
	WorkOrderStatusCompleted  = WorkOrderStatus("completed")
	WorkOrderStatusCancelled  = WorkOrderStatus("cancelled")
)

// Configuration represents IT configuration management
type Configuration struct {
	ID         string                 `json:"id"`
	BuildingID string                 `json:"building_id"`
	SpaceID    string                 `json:"space_id"`
	Name       string                 `json:"name"`
	ConfigType string                 `json:"config_type"`
	Version    string                 `json:"version"`
	Status     string                 `json:"status"`
	Config     map[string]interface{} `json:"config"`
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
}

// InventoryItem represents IT inventory management
type InventoryItem struct {
	ID         string    `json:"id"`
	Name       string    `json:"name"`
	Category   string    `json:"category"`
	Quantity   int       `json:"quantity"`
	MinStock   int       `json:"min_stock"`
	UnitPrice  float64   `json:"unit_price"`
	TotalValue float64   `json:"total_value"`
	Location   string    `json:"location"`
	Supplier   string    `json:"supplier"`
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
}

// MaintenanceSchedule, Inspection, Vendor, Contract types remain the same
// (keeping the existing facility management structures)

type MaintenanceSchedule struct {
	ID            string    `json:"id"`
	AssetID       string    `json:"asset_id"`
	Task          string    `json:"task"`
	Frequency     string    `json:"frequency"`
	LastPerformed time.Time `json:"last_performed"`
	NextDue       time.Time `json:"next_due"`
	AssignedTo    string    `json:"assigned_to"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`
}

type Inspection struct {
	ID          string    `json:"id"`
	BuildingID  string    `json:"building_id"`
	SpaceID     string    `json:"space_id"`
	Inspector   string    `json:"inspector"`
	Type        string    `json:"type"`
	Status      string    `json:"status"`
	Findings    string    `json:"findings"`
	DueDate     time.Time `json:"due_date"`
	CompletedAt time.Time `json:"completed_at"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type Vendor struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Contact   string    `json:"contact"`
	Email     string    `json:"email"`
	Phone     string    `json:"phone"`
	Services  []string  `json:"services"`
	Rating    float64   `json:"rating"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type Contract struct {
	ID         string    `json:"id"`
	VendorID   string    `json:"vendor_id"`
	BuildingID string    `json:"building_id"`
	Type       string    `json:"type"`
	StartDate  time.Time `json:"start_date"`
	EndDate    time.Time `json:"end_date"`
	Value      float64   `json:"value"`
	Status     string    `json:"status"`
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
}
