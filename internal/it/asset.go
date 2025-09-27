package it

import (
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ITAssetManager manages IT assets and configurations
type ITAssetManager struct {
	assets           map[string]*ITAsset
	configurations   map[string]*Configuration
	roomSetups       map[string]*RoomSetup
	partsInventory   map[string]*Part
	workOrders       map[string]*ITWorkOrder
	maintenanceLogs  map[string]*MaintenanceLog
	metrics          *ITAssetMetrics
	mu               sync.RWMutex
}

// ITAsset represents an IT asset
type ITAsset struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Type            AssetType              `json:"type"`
	Category        string                 `json:"category"`
	Brand           string                 `json:"brand"`
	Model           string                 `json:"model"`
	SerialNumber    string                 `json:"serial_number"`
	AssetTag        string                 `json:"asset_tag"`
	Location        Location               `json:"location"`
	Status          AssetStatus            `json:"status"`
	Condition       AssetCondition         `json:"condition"`
	PurchaseDate    time.Time              `json:"purchase_date"`
	WarrantyExpiry  *time.Time             `json:"warranty_expiry"`
	PurchasePrice   float64                `json:"purchase_price"`
	CurrentValue    float64                `json:"current_value"`
	Supplier        string                 `json:"supplier"`
	Configuration   *Configuration         `json:"configuration,omitempty"`
	MaintenanceLogs []string               `json:"maintenance_logs"` // Log IDs
	WorkOrders      []string               `json:"work_orders"`      // Work order IDs
	Metadata        map[string]interface{} `json:"metadata"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
}

// AssetType represents the type of IT asset
type AssetType string

const (
	AssetTypeComputer        AssetType = "computer"
	AssetTypeLaptop          AssetType = "laptop"
	AssetTypeTablet          AssetType = "tablet"
	AssetTypeProjector       AssetType = "projector"
	AssetTypeInteractiveBoard AssetType = "interactive_board"
	AssetTypeDocCamera       AssetType = "doc_camera"
	AssetTypeDockingStation  AssetType = "docking_station"
	AssetTypePrinter         AssetType = "printer"
	AssetTypeScanner         AssetType = "scanner"
	AssetTypeNetworkDevice   AssetType = "network_device"
	AssetTypeServer          AssetType = "server"
	AssetTypeStorage         AssetType = "storage"
	AssetTypeAccessory       AssetType = "accessory"
	AssetTypeOther           AssetType = "other"
)

// AssetStatus represents the status of an asset
type AssetStatus string

const (
	AssetStatusActive      AssetStatus = "active"
	AssetStatusInactive    AssetStatus = "inactive"
	AssetStatusMaintenance AssetStatus = "maintenance"
	AssetStatusRetired     AssetStatus = "retired"
	AssetStatusLost        AssetStatus = "lost"
	AssetStatusStolen      AssetStatus = "stolen"
)

// AssetCondition represents the physical condition of an asset
type AssetCondition string

const (
	AssetConditionExcellent AssetCondition = "excellent"
	AssetConditionGood      AssetCondition = "good"
	AssetConditionFair      AssetCondition = "fair"
	AssetConditionPoor      AssetCondition = "poor"
	AssetConditionBroken    AssetCondition = "broken"
)

// Location represents a physical location
type Location struct {
	Building    string `json:"building"`
	Floor       string `json:"floor"`
	Room        string `json:"room"`
	RoomNumber  string `json:"room_number"`
	Department  string `json:"department"`
	Zone        string `json:"zone"`
	Coordinates *Coordinates `json:"coordinates,omitempty"`
}

// Coordinates represents GPS coordinates
type Coordinates struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Altitude  float64 `json:"altitude"`
}

// Configuration represents an asset configuration
type Configuration struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Description     string                 `json:"description"`
	AssetType       AssetType              `json:"asset_type"`
	Components      []Component            `json:"components"`
	Software        []Software             `json:"software"`
	NetworkSettings *NetworkSettings       `json:"network_settings,omitempty"`
	UserSettings    map[string]interface{} `json:"user_settings"`
	IsTemplate      bool                   `json:"is_template"`
	CreatedBy       string                 `json:"created_by"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
}

// Component represents a hardware component
type Component struct {
	Type        string                 `json:"type"`
	Brand       string                 `json:"brand"`
	Model       string                 `json:"model"`
	Specs       map[string]interface{} `json:"specs"`
	Quantity    int                    `json:"quantity"`
	Required    bool                   `json:"required"`
	Optional    bool                   `json:"optional"`
	Notes       string                 `json:"notes"`
}

// Software represents installed software
type Software struct {
	Name        string                 `json:"name"`
	Version     string                 `json:"version"`
	License     string                 `json:"license"`
	Type        string                 `json:"type"` // os, application, driver, etc.
	Required    bool                   `json:"required"`
	AutoUpdate  bool                   `json:"auto_update"`
	Settings    map[string]interface{} `json:"settings"`
}

// NetworkSettings represents network configuration
type NetworkSettings struct {
	IPAddress     string            `json:"ip_address"`
	SubnetMask    string            `json:"subnet_mask"`
	Gateway       string            `json:"gateway"`
	DNS           []string          `json:"dns"`
	VLAN          string            `json:"vlan"`
	Wireless      *WirelessSettings `json:"wireless,omitempty"`
	Ports         []PortConfig      `json:"ports"`
	FirewallRules []FirewallRule    `json:"firewall_rules"`
}

// WirelessSettings represents wireless network settings
type WirelessSettings struct {
	SSID           string `json:"ssid"`
	Security       string `json:"security"`
	Encryption     string `json:"encryption"`
	Password       string `json:"password"`
	Frequency      string `json:"frequency"`
	Channel        int    `json:"channel"`
	SignalStrength int    `json:"signal_strength"`
}

// PortConfig represents network port configuration
type PortConfig struct {
	Port        int    `json:"port"`
	Protocol    string `json:"protocol"`
	Service     string `json:"service"`
	Description string `json:"description"`
	Enabled     bool   `json:"enabled"`
}

// FirewallRule represents a firewall rule
type FirewallRule struct {
	ID          string `json:"id"`
	Direction   string `json:"direction"` // inbound, outbound
	Protocol    string `json:"protocol"`
	Port        int    `json:"port"`
	Source      string `json:"source"`
	Destination string `json:"destination"`
	Action      string `json:"action"` // allow, deny
	Enabled     bool   `json:"enabled"`
}

// RoomSetup represents a room's IT equipment configuration
type RoomSetup struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Description     string                 `json:"description"`
	Room            Location               `json:"room"`
	SetupType       SetupType              `json:"setup_type"`
	Assets          []RoomAsset            `json:"assets"`
	Connections     []Connection           `json:"connections"`
	UserPreferences map[string]interface{} `json:"user_preferences"`
	IsActive        bool                   `json:"is_active"`
	CreatedBy       string                 `json:"created_by"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
}

// SetupType represents the type of room setup
type SetupType string

const (
	SetupTypeTraditional     SetupType = "traditional"      // Projector + Doc Camera + Docking Station
	SetupTypeInteractive     SetupType = "interactive"      // Interactive Board + Computer
	SetupTypeHybrid          SetupType = "hybrid"           // Mix of traditional and interactive
	SetupTypeComputerLab     SetupType = "computer_lab"     // Multiple computers for students
	SetupTypeConference      SetupType = "conference"       // Video conferencing setup
	SetupTypePresentation    SetupType = "presentation"     // Large presentation setup
	SetupTypeMobile          SetupType = "mobile"           // Mobile cart setup
	SetupTypeCustom          SetupType = "custom"           // Custom configuration
)

// RoomAsset represents an asset in a room setup
type RoomAsset struct {
	AssetID       string                 `json:"asset_id"`
	Position      Position               `json:"position"`
	Connections   []string               `json:"connections"` // Connection IDs
	Settings      map[string]interface{} `json:"settings"`
	IsPrimary     bool                   `json:"is_primary"`
	IsRequired    bool                   `json:"is_required"`
	Notes         string                 `json:"notes"`
}

// Position represents the physical position of an asset in a room
type Position struct {
	X        float64 `json:"x"`        // Distance from left wall (feet)
	Y        float64 `json:"y"`        // Distance from front wall (feet)
	Z        float64 `json:"z"`        // Height from floor (feet)
	Rotation float64 `json:"rotation"` // Rotation in degrees
	MountType string `json:"mount_type"` // wall, ceiling, floor, desk, etc.
}

// Connection represents a connection between assets
type Connection struct {
	ID          string        `json:"id"`
	FromAsset   string        `json:"from_asset"`
	ToAsset     string        `json:"to_asset"`
	Type        ConnectionType `json:"type"`
	Port        string        `json:"port"`
	Description string        `json:"description"`
	IsActive    bool          `json:"is_active"`
}

// ConnectionType represents the type of connection
type ConnectionType string

const (
	ConnectionTypeHDMI        ConnectionType = "hdmi"
	ConnectionTypeVGA         ConnectionType = "vga"
	ConnectionTypeUSB         ConnectionType = "usb"
	ConnectionTypeUSB_C       ConnectionType = "usb_c"
	ConnectionTypeEthernet    ConnectionType = "ethernet"
	ConnectionTypeWireless    ConnectionType = "wireless"
	ConnectionTypeBluetooth   ConnectionType = "bluetooth"
	ConnectionTypeAudio       ConnectionType = "audio"
	ConnectionTypePower       ConnectionType = "power"
	ConnectionTypeOther       ConnectionType = "other"
)

// Part represents an inventory part
type Part struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Description     string                 `json:"description"`
	PartNumber      string                 `json:"part_number"`
	Category        string                 `json:"category"`
	Brand           string                 `json:"brand"`
	Model           string                 `json:"model"`
	Supplier        string                 `json:"supplier"`
	SupplierPartNum string                 `json:"supplier_part_number"`
	UnitPrice       float64                `json:"unit_price"`
	Quantity        int                    `json:"quantity"`
	MinQuantity     int                    `json:"min_quantity"`
	MaxQuantity     int                    `json:"max_quantity"`
	Location        string                 `json:"location"`
	Status          PartStatus             `json:"status"`
	CompatibleWith  []string               `json:"compatible_with"` // Asset types
	Metadata        map[string]interface{} `json:"metadata"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
}

// PartStatus represents the status of a part
type PartStatus string

const (
	PartStatusInStock    PartStatus = "in_stock"
	PartStatusLowStock   PartStatus = "low_stock"
	PartStatusOutOfStock PartStatus = "out_of_stock"
	PartStatusDiscontinued PartStatus = "discontinued"
	PartStatusOnOrder    PartStatus = "on_order"
)

// ITWorkOrder represents an IT work order
type ITWorkOrder struct {
	ID              string                 `json:"id"`
	Title           string                 `json:"title"`
	Description     string                 `json:"description"`
	Type            WorkOrderType          `json:"type"`
	Priority        Priority               `json:"priority"`
	Status          WorkOrderStatus        `json:"status"`
	Location        Location               `json:"location"`
	RequestedBy     string                 `json:"requested_by"`
	AssignedTo      string                 `json:"assigned_to"`
	Assets          []string               `json:"assets"` // Asset IDs
	Parts           []PartRequest          `json:"parts"`
	EstimatedTime   time.Duration          `json:"estimated_time"`
	ActualTime      time.Duration          `json:"actual_time"`
	Cost            float64                `json:"cost"`
	Notes           string                 `json:"notes"`
	Resolution      string                 `json:"resolution"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
	DueDate         *time.Time             `json:"due_date"`
	CompletedAt     *time.Time             `json:"completed_at"`
}

// WorkOrderType represents the type of work order
type WorkOrderType string

const (
	WorkOrderTypeInstallation WorkOrderType = "installation"
	WorkOrderTypeRepair       WorkOrderType = "repair"
	WorkOrderTypeMaintenance  WorkOrderType = "maintenance"
	WorkOrderTypeUpgrade      WorkOrderType = "upgrade"
	WorkOrderTypeConfiguration WorkOrderType = "configuration"
	WorkOrderTypeRemoval      WorkOrderType = "removal"
	WorkOrderTypeInspection   WorkOrderType = "inspection"
	WorkOrderTypeOther        WorkOrderType = "other"
)

// Priority represents the priority level
type Priority string

const (
	PriorityLow      Priority = "low"
	PriorityMedium   Priority = "medium"
	PriorityHigh     Priority = "high"
	PriorityCritical Priority = "critical"
	PriorityEmergency Priority = "emergency"
)

// WorkOrderStatus represents the status of a work order
type WorkOrderStatus string

const (
	WorkOrderStatusOpen       WorkOrderStatus = "open"
	WorkOrderStatusAssigned   WorkOrderStatus = "assigned"
	WorkOrderStatusInProgress WorkOrderStatus = "in_progress"
	WorkOrderStatusOnHold     WorkOrderStatus = "on_hold"
	WorkOrderStatusCompleted  WorkOrderStatus = "completed"
	WorkOrderStatusCancelled  WorkOrderStatus = "cancelled"
	WorkOrderStatusClosed     WorkOrderStatus = "closed"
)

// PartRequest represents a request for parts
type PartRequest struct {
	PartID     string `json:"part_id"`
	Quantity   int    `json:"quantity"`
	Reason     string `json:"reason"`
	Urgent     bool   `json:"urgent"`
	Ordered    bool   `json:"ordered"`
	Received   bool   `json:"received"`
	OrderDate  *time.Time `json:"order_date"`
	ReceiveDate *time.Time `json:"receive_date"`
}

// MaintenanceLog represents a maintenance log entry
type MaintenanceLog struct {
	ID              string                 `json:"id"`
	AssetID         string                 `json:"asset_id"`
	Type            MaintenanceType        `json:"type"`
	Description     string                 `json:"description"`
	PerformedBy     string                 `json:"performed_by"`
	Date            time.Time              `json:"date"`
	Duration        time.Duration          `json:"duration"`
	PartsUsed       []PartUsed             `json:"parts_used"`
	Cost            float64                `json:"cost"`
	Notes           string                 `json:"notes"`
	NextMaintenance *time.Time             `json:"next_maintenance"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// MaintenanceType represents the type of maintenance
type MaintenanceType string

const (
	MaintenanceTypePreventive MaintenanceType = "preventive"
	MaintenanceTypeCorrective MaintenanceType = "corrective"
	MaintenanceTypeEmergency  MaintenanceType = "emergency"
	MaintenanceTypeUpgrade    MaintenanceType = "upgrade"
	MaintenanceTypeInspection MaintenanceType = "inspection"
)

// PartUsed represents a part used in maintenance
type PartUsed struct {
	PartID   string  `json:"part_id"`
	Quantity int     `json:"quantity"`
	Cost     float64 `json:"cost"`
	Notes    string  `json:"notes"`
}

// ITAssetMetrics represents IT asset management metrics
type ITAssetMetrics struct {
	TotalAssets           int64   `json:"total_assets"`
	ActiveAssets          int64   `json:"active_assets"`
	AssetsInMaintenance   int64   `json:"assets_in_maintenance"`
	RetiredAssets         int64   `json:"retired_assets"`
	TotalConfigurations   int64   `json:"total_configurations"`
	ActiveConfigurations  int64   `json:"active_configurations"`
	TotalRoomSetups       int64   `json:"total_room_setups"`
	ActiveRoomSetups      int64   `json:"active_room_setups"`
	TotalWorkOrders       int64   `json:"total_work_orders"`
	OpenWorkOrders        int64   `json:"open_work_orders"`
	CompletedWorkOrders   int64   `json:"completed_work_orders"`
	TotalParts            int64   `json:"total_parts"`
	LowStockParts         int64   `json:"low_stock_parts"`
	OutOfStockParts       int64   `json:"out_of_stock_parts"`
	TotalValue            float64 `json:"total_value"`
	DepreciationValue     float64 `json:"depreciation_value"`
	MaintenanceCost       float64 `json:"maintenance_cost"`
	AverageWorkOrderTime  float64 `json:"average_work_order_time"`
	AssetUtilization      float64 `json:"asset_utilization"`
}

// NewITAssetManager creates a new IT asset manager
func NewITAssetManager() *ITAssetManager {
	return &ITAssetManager{
		assets:          make(map[string]*ITAsset),
		configurations:  make(map[string]*Configuration),
		roomSetups:      make(map[string]*RoomSetup),
		partsInventory:  make(map[string]*Part),
		workOrders:      make(map[string]*ITWorkOrder),
		maintenanceLogs: make(map[string]*MaintenanceLog),
		metrics:         &ITAssetMetrics{},
	}
}

// CreateAsset creates a new IT asset
func (iam *ITAssetManager) CreateAsset(asset *ITAsset) error {
	iam.mu.Lock()
	defer iam.mu.Unlock()

	if asset.ID == "" {
		asset.ID = fmt.Sprintf("asset_%d", time.Now().UnixNano())
	}

	asset.CreatedAt = time.Now()
	asset.UpdatedAt = time.Now()
	iam.assets[asset.ID] = asset
	iam.metrics.TotalAssets++

	if asset.Status == AssetStatusActive {
		iam.metrics.ActiveAssets++
	}

	logger.Info("IT asset created: %s", asset.ID)
	return nil
}

// GetAsset returns a specific asset
func (iam *ITAssetManager) GetAsset(assetID string) (*ITAsset, error) {
	iam.mu.RLock()
	defer iam.mu.RUnlock()

	asset, exists := iam.assets[assetID]
	if !exists {
		return nil, fmt.Errorf("asset not found: %s", assetID)
	}

	return asset, nil
}

// UpdateAsset updates an existing asset
func (iam *ITAssetManager) UpdateAsset(assetID string, asset *ITAsset) error {
	iam.mu.Lock()
	defer iam.mu.Unlock()

	if _, exists := iam.assets[assetID]; !exists {
		return fmt.Errorf("asset not found: %s", assetID)
	}

	asset.ID = assetID
	asset.UpdatedAt = time.Now()
	iam.assets[assetID] = asset

	logger.Info("IT asset updated: %s", assetID)
	return nil
}

// DeleteAsset deletes an asset
func (iam *ITAssetManager) DeleteAsset(assetID string) error {
	iam.mu.Lock()
	defer iam.mu.Unlock()

	asset, exists := iam.assets[assetID]
	if !exists {
		return fmt.Errorf("asset not found: %s", assetID)
	}

	// Update metrics
	iam.metrics.TotalAssets--
	if asset.Status == AssetStatusActive {
		iam.metrics.ActiveAssets--
	}

	delete(iam.assets, assetID)
	logger.Info("IT asset deleted: %s", assetID)
	return nil
}

// GetAssets returns all assets with optional filtering
func (iam *ITAssetManager) GetAssets(filter AssetFilter) []*ITAsset {
	iam.mu.RLock()
	defer iam.mu.RUnlock()

	var assets []*ITAsset
	for _, asset := range iam.assets {
		if iam.matchesFilter(asset, filter) {
			assets = append(assets, asset)
		}
	}

	return assets
}

// AssetFilter represents filtering criteria for assets
type AssetFilter struct {
	Type     AssetType     `json:"type,omitempty"`
	Status   AssetStatus   `json:"status,omitempty"`
	Location Location      `json:"location,omitempty"`
	Brand    string        `json:"brand,omitempty"`
	Model    string        `json:"model,omitempty"`
}

// matchesFilter checks if an asset matches the filter criteria
func (iam *ITAssetManager) matchesFilter(asset *ITAsset, filter AssetFilter) bool {
	if filter.Type != "" && asset.Type != filter.Type {
		return false
	}
	if filter.Status != "" && asset.Status != filter.Status {
		return false
	}
	if filter.Brand != "" && asset.Brand != filter.Brand {
		return false
	}
	if filter.Model != "" && asset.Model != filter.Model {
		return false
	}
	// Add more filter logic as needed
	return true
}

// GetMetrics returns IT asset management metrics
func (iam *ITAssetManager) GetMetrics() *ITAssetMetrics {
	iam.mu.RLock()
	defer iam.mu.RUnlock()

	return iam.metrics
}

// UpdateMetrics updates the metrics
func (iam *ITAssetManager) UpdateMetrics() {
	iam.mu.Lock()
	defer iam.mu.Unlock()

	// Reset counters
	iam.metrics.ActiveAssets = 0
	iam.metrics.AssetsInMaintenance = 0
	iam.metrics.RetiredAssets = 0
	iam.metrics.TotalValue = 0

	// Count assets by status
	for _, asset := range iam.assets {
		switch asset.Status {
		case AssetStatusActive:
			iam.metrics.ActiveAssets++
		case AssetStatusMaintenance:
			iam.metrics.AssetsInMaintenance++
		case AssetStatusRetired:
			iam.metrics.RetiredAssets++
		}
		iam.metrics.TotalValue += asset.CurrentValue
	}

	// Count configurations
	iam.metrics.TotalConfigurations = int64(len(iam.configurations))
	activeConfigs := 0
	for _, config := range iam.configurations {
		if !config.IsTemplate {
			activeConfigs++
		}
	}
	iam.metrics.ActiveConfigurations = int64(activeConfigs)

	// Count room setups
	iam.metrics.TotalRoomSetups = int64(len(iam.roomSetups))
	activeSetups := 0
	for _, setup := range iam.roomSetups {
		if setup.IsActive {
			activeSetups++
		}
	}
	iam.metrics.ActiveRoomSetups = int64(activeSetups)

	// Count work orders
	iam.metrics.TotalWorkOrders = int64(len(iam.workOrders))
	openWorkOrders := 0
	completedWorkOrders := 0
	for _, workOrder := range iam.workOrders {
		switch workOrder.Status {
		case WorkOrderStatusOpen, WorkOrderStatusAssigned, WorkOrderStatusInProgress:
			openWorkOrders++
		case WorkOrderStatusCompleted:
			completedWorkOrders++
		}
	}
	iam.metrics.OpenWorkOrders = int64(openWorkOrders)
	iam.metrics.CompletedWorkOrders = int64(completedWorkOrders)

	// Count parts
	iam.metrics.TotalParts = int64(len(iam.partsInventory))
	lowStockParts := 0
	outOfStockParts := 0
	for _, part := range iam.partsInventory {
		switch part.Status {
		case PartStatusLowStock:
			lowStockParts++
		case PartStatusOutOfStock:
			outOfStockParts++
		}
	}
	iam.metrics.LowStockParts = int64(lowStockParts)
	iam.metrics.OutOfStockParts = int64(outOfStockParts)

	logger.Debug("IT asset metrics updated")
}
