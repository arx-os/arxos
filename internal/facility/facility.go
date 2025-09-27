package facility

import (
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// FacilityManager manages facility operations and maintenance
type FacilityManager struct {
	buildings   map[string]*Building
	spaces      map[string]*Space
	assets      map[string]*Asset
	workOrders  map[string]*WorkOrder
	maintenance map[string]*MaintenanceSchedule
	inspections map[string]*Inspection
	vendors     map[string]*Vendor
	contracts   map[string]*Contract
	metrics     *FacilityMetrics
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
	Assets       []string               `json:"assets"` // Asset IDs
	Config       map[string]interface{} `json:"config"`
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
}

// BuildingType represents the type of building
type BuildingType string

const (
	BuildingTypeOffice      = BuildingType("office")
	BuildingTypeResidential = BuildingType("residential")
	BuildingTypeCommercial  = BuildingType("commercial")
	BuildingTypeIndustrial  = BuildingType("industrial")
	BuildingTypeHealthcare  = BuildingType("healthcare")
	BuildingTypeEducational = BuildingType("educational")
	BuildingTypeRetail      = BuildingType("retail")
	BuildingTypeWarehouse   = BuildingType("warehouse")
	BuildingTypeMixed       = BuildingType("mixed")
)

// BuildingStatus represents the operational status of a building
type BuildingStatus string

const (
	BuildingStatusActive      = BuildingStatus("active")
	BuildingStatusInactive    = BuildingStatus("inactive")
	BuildingStatusMaintenance = BuildingStatus("maintenance")
	BuildingStatusRenovation  = BuildingStatus("renovation")
	BuildingStatusClosed      = BuildingStatus("closed")
)

// Address represents a physical address
type Address struct {
	Street     string  `json:"street"`
	City       string  `json:"city"`
	State      string  `json:"state"`
	PostalCode string  `json:"postal_code"`
	Country    string  `json:"country"`
	Latitude   float64 `json:"latitude"`
	Longitude  float64 `json:"longitude"`
}

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
	Assets     []string               `json:"assets"` // Asset IDs
	Config     map[string]interface{} `json:"config"`
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
}

// SpaceType represents the type of space
type SpaceType string

const (
	SpaceTypeOffice     = SpaceType("office")
	SpaceTypeConference = SpaceType("conference")
	SpaceTypeMeeting    = SpaceType("meeting")
	SpaceTypeReception  = SpaceType("reception")
	SpaceTypeBreak      = SpaceType("break")
	SpaceTypeStorage    = SpaceType("storage")
	SpaceTypeServer     = SpaceType("server")
	SpaceTypeMechanical = SpaceType("mechanical")
	SpaceTypeElectrical = SpaceType("electrical")
	SpaceTypeRestroom   = SpaceType("restroom")
	SpaceTypeKitchen    = SpaceType("kitchen")
	SpaceTypeLobby      = SpaceType("lobby")
	SpaceTypeParking    = SpaceType("parking")
	SpaceTypeOutdoor    = SpaceType("outdoor")
)

// SpaceStatus represents the operational status of a space
type SpaceStatus string

const (
	SpaceStatusActive      = SpaceStatus("active")
	SpaceStatusAvailable   = SpaceStatus("available")
	SpaceStatusOccupied    = SpaceStatus("occupied")
	SpaceStatusMaintenance = SpaceStatus("maintenance")
	SpaceStatusReserved    = SpaceStatus("reserved")
	SpaceStatusOutOfOrder  = SpaceStatus("out_of_order")
)

// Asset represents a physical asset within a building
type Asset struct {
	ID              string                 `json:"id"`
	BuildingID      string                 `json:"building_id"`
	SpaceID         string                 `json:"space_id"`
	Name            string                 `json:"name"`
	AssetType       string                 `json:"asset_type"`
	Category        string                 `json:"category"`
	Manufacturer    string                 `json:"manufacturer"`
	Model           string                 `json:"model"`
	SerialNumber    string                 `json:"serial_number"`
	Status          AssetStatus            `json:"status"`
	Condition       AssetCondition         `json:"condition"`
	InstallDate     time.Time              `json:"install_date"`
	WarrantyExpiry  *time.Time             `json:"warranty_expiry,omitempty"`
	LastMaintenance *time.Time             `json:"last_maintenance,omitempty"`
	NextMaintenance *time.Time             `json:"next_maintenance,omitempty"`
	Cost            float64                `json:"cost"`
	Depreciation    float64                `json:"depreciation"`
	Config          map[string]interface{} `json:"config"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
}

// AssetType represents the type of asset
type AssetType string

const (
	AssetTypeHVAC       = AssetType("hvac")
	AssetTypeElectrical = AssetType("electrical")
	AssetTypePlumbing   = AssetType("plumbing")
	AssetTypeSecurity   = AssetType("security")
	AssetTypeIT         = AssetType("it")
	AssetTypeFurniture  = AssetType("furniture")
	AssetTypeEquipment  = AssetType("equipment")
	AssetTypeVehicle    = AssetType("vehicle")
	AssetTypeTool       = AssetType("tool")
	AssetTypeSafety     = AssetType("safety")
)

// AssetStatus represents the operational status of an asset
type AssetStatus string

const (
	AssetStatusActive      = AssetStatus("active")
	AssetStatusOperational = AssetStatus("operational")
	AssetStatusMaintenance = AssetStatus("maintenance")
	AssetStatusRepair      = AssetStatus("repair")
	AssetStatusRetired     = AssetStatus("retired")
	AssetStatusMissing     = AssetStatus("missing")
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

// WorkOrder represents a maintenance work order
type WorkOrder struct {
	ID                 string                 `json:"id"`
	Title              string                 `json:"title"`
	Description        string                 `json:"description"`
	Type               WorkOrderType          `json:"type"`
	Priority           WorkOrderPriority      `json:"priority"`
	Status             WorkOrderStatus        `json:"status"`
	BuildingID         string                 `json:"building_id"`
	SpaceID            string                 `json:"space_id"`
	AssetID            string                 `json:"asset_id"`
	RequestedBy        string                 `json:"requested_by"`
	CreatedBy          string                 `json:"created_by"`
	AssignedTo         string                 `json:"assigned_to"`
	VendorID           string                 `json:"vendor_id,omitempty"`
	EstimatedCost      float64                `json:"estimated_cost"`
	ActualCost         float64                `json:"actual_cost"`
	EstimatedHours     float64                `json:"estimated_hours"`
	ActualHours        float64                `json:"actual_hours"`
	ScheduledDate      *time.Time             `json:"scheduled_date,omitempty"`
	StartDate          *time.Time             `json:"start_date,omitempty"`
	StartedAt          *time.Time             `json:"started_at,omitempty"`
	CompletionDate     *time.Time             `json:"completion_date,omitempty"`
	CompletedAt        *time.Time             `json:"completed_at,omitempty"`
	CancelledAt        *time.Time             `json:"cancelled_at,omitempty"`
	CancellationReason string                 `json:"cancellation_reason,omitempty"`
	DueDate            *time.Time             `json:"due_date,omitempty"`
	Notes              []string               `json:"notes"`
	Attachments        []string               `json:"attachments"`
	Config             map[string]interface{} `json:"config"`
	CreatedAt          time.Time              `json:"created_at"`
	UpdatedAt          time.Time              `json:"updated_at"`
}

// WorkOrderType represents the type of work order
type WorkOrderType string

const (
	WorkOrderTypePreventive   = WorkOrderType("preventive")
	WorkOrderTypeCorrective   = WorkOrderType("corrective")
	WorkOrderTypeEmergency    = WorkOrderType("emergency")
	WorkOrderTypeInspection   = WorkOrderType("inspection")
	WorkOrderTypeInstallation = WorkOrderType("installation")
	WorkOrderTypeUpgrade      = WorkOrderType("upgrade")
	WorkOrderTypeReplacement  = WorkOrderType("replacement")
)

// WorkOrderPriority represents the priority of a work order
type WorkOrderPriority string

const (
	WorkOrderPriorityLow       = WorkOrderPriority("low")
	WorkOrderPriorityMedium    = WorkOrderPriority("medium")
	WorkOrderPriorityHigh      = WorkOrderPriority("high")
	WorkOrderPriorityCritical  = WorkOrderPriority("critical")
	WorkOrderPriorityEmergency = WorkOrderPriority("emergency")
)

// WorkOrderStatus represents the status of a work order
type WorkOrderStatus string

const (
	WorkOrderStatusOpen       = WorkOrderStatus("open")
	WorkOrderStatusAssigned   = WorkOrderStatus("assigned")
	WorkOrderStatusInProgress = WorkOrderStatus("in_progress")
	WorkOrderStatusOnHold     = WorkOrderStatus("on_hold")
	WorkOrderStatusCompleted  = WorkOrderStatus("completed")
	WorkOrderStatusCancelled  = WorkOrderStatus("cancelled")
	WorkOrderStatusClosed     = WorkOrderStatus("closed")
)

// MaintenanceSchedule represents a scheduled maintenance task
type MaintenanceSchedule struct {
	ID          string                 `json:"id"`
	AssetID     string                 `json:"asset_id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Type        MaintenanceType        `json:"type"`
	Frequency   string                 `json:"frequency"`
	Interval    int                    `json:"interval"` // Days
	LastRun     *time.Time             `json:"last_run,omitempty"`
	NextRun     time.Time              `json:"next_run"`
	NextDue     time.Time              `json:"next_due"`
	Status      MaintenanceStatus      `json:"status"`
	Config      map[string]interface{} `json:"config"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// MaintenanceType represents the type of maintenance
type MaintenanceType string

const (
	MaintenanceTypePreventive = MaintenanceType("preventive")
	MaintenanceTypePredictive = MaintenanceType("predictive")
	MaintenanceTypeCorrective = MaintenanceType("corrective")
	MaintenanceTypeEmergency  = MaintenanceType("emergency")
)

// MaintenanceFrequency represents the frequency of maintenance
type MaintenanceFrequency string

const (
	MaintenanceFrequencyDaily     = MaintenanceFrequency("daily")
	MaintenanceFrequencyWeekly    = MaintenanceFrequency("weekly")
	MaintenanceFrequencyMonthly   = MaintenanceFrequency("monthly")
	MaintenanceFrequencyQuarterly = MaintenanceFrequency("quarterly")
	MaintenanceFrequencyAnnually  = MaintenanceFrequency("annually")
	MaintenanceFrequencyCustom    = MaintenanceFrequency("custom")
)

// MaintenanceStatus represents the status of maintenance
type MaintenanceStatus string

const (
	MaintenanceStatusActive    = MaintenanceStatus("active")
	MaintenanceStatusInactive  = MaintenanceStatus("inactive")
	MaintenanceStatusPaused    = MaintenanceStatus("paused")
	MaintenanceStatusCompleted = MaintenanceStatus("completed")
)

// Inspection represents a facility inspection
type Inspection struct {
	ID            string                 `json:"id"`
	Name          string                 `json:"name"`
	BuildingID    string                 `json:"building_id"`
	SpaceID       string                 `json:"space_id"`
	AssetID       string                 `json:"asset_id,omitempty"`
	Type          string                 `json:"type"`
	Status        InspectionStatus       `json:"status"`
	Inspector     string                 `json:"inspector"`
	ScheduledDate time.Time              `json:"scheduled_date"`
	StartDate     *time.Time             `json:"start_date,omitempty"`
	StartedAt     *time.Time             `json:"started_at,omitempty"`
	EndDate       *time.Time             `json:"end_date,omitempty"`
	CompletedAt   *time.Time             `json:"completed_at,omitempty"`
	Findings      []InspectionFinding    `json:"findings"`
	Score         float64                `json:"score"`
	Notes         string                 `json:"notes"`
	Config        map[string]interface{} `json:"config"`
	CreatedAt     time.Time              `json:"created_at"`
	UpdatedAt     time.Time              `json:"updated_at"`
}

// InspectionType represents the type of inspection
type InspectionType string

const (
	InspectionTypeSafety        = InspectionType("safety")
	InspectionTypeFire          = InspectionType("fire")
	InspectionTypeElectrical    = InspectionType("electrical")
	InspectionTypeHVAC          = InspectionType("hvac")
	InspectionTypePlumbing      = InspectionType("plumbing")
	InspectionTypeStructural    = InspectionType("structural")
	InspectionTypeEnvironmental = InspectionType("environmental")
	InspectionTypeSecurity      = InspectionType("security")
	InspectionTypeCompliance    = InspectionType("compliance")
)

// InspectionStatus represents the status of an inspection
type InspectionStatus string

const (
	InspectionStatusScheduled  = InspectionStatus("scheduled")
	InspectionStatusInProgress = InspectionStatus("in_progress")
	InspectionStatusCompleted  = InspectionStatus("completed")
	InspectionStatusFailed     = InspectionStatus("failed")
	InspectionStatusCancelled  = InspectionStatus("cancelled")
)

// InspectionFinding represents a finding from an inspection
type InspectionFinding struct {
	ID             string                 `json:"id"`
	InspectionID   string                 `json:"inspection_id"`
	Title          string                 `json:"title"`
	Description    string                 `json:"description"`
	Severity       FindingSeverity        `json:"severity"`
	Category       string                 `json:"category"`
	Location       string                 `json:"location"`
	Recommendation string                 `json:"recommendation"`
	Status         FindingStatus          `json:"status"`
	Resolution     string                 `json:"resolution"`
	ResolvedAt     *time.Time             `json:"resolved_at,omitempty"`
	DueDate        *time.Time             `json:"due_date,omitempty"`
	ResolvedDate   *time.Time             `json:"resolved_date,omitempty"`
	Config         map[string]interface{} `json:"config"`
	CreatedAt      time.Time              `json:"created_at"`
	UpdatedAt      time.Time              `json:"updated_at"`
}

// FindingSeverity represents the severity of a finding
type FindingSeverity string

const (
	FindingSeverityLow      = FindingSeverity("low")
	FindingSeverityMedium   = FindingSeverity("medium")
	FindingSeverityHigh     = FindingSeverity("high")
	FindingSeverityCritical = FindingSeverity("critical")
)

// FindingStatus represents the status of a finding
type FindingStatus string

const (
	FindingStatusOpen       = FindingStatus("open")
	FindingStatusInProgress = FindingStatus("in_progress")
	FindingStatusResolved   = FindingStatus("resolved")
	FindingStatusClosed     = FindingStatus("closed")
)

// Vendor represents a service vendor
type Vendor struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	ContactName string                 `json:"contact_name"`
	Email       string                 `json:"email"`
	Phone       string                 `json:"phone"`
	Address     string                 `json:"address"`
	City        string                 `json:"city"`
	State       string                 `json:"state"`
	ZipCode     string                 `json:"zip_code"`
	Country     string                 `json:"country"`
	Type        VendorType             `json:"type"`
	Contact     Contact                `json:"contact"`
	Services    []string               `json:"services"`
	Rating      float64                `json:"rating"`
	Status      VendorStatus           `json:"status"`
	Config      map[string]interface{} `json:"config"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// VendorType represents the type of vendor
type VendorType string

const (
	VendorTypeMaintenance = VendorType("maintenance")
	VendorTypeCleaning    = VendorType("cleaning")
	VendorTypeSecurity    = VendorType("security")
	VendorTypeIT          = VendorType("it")
	VendorTypeHVAC        = VendorType("hvac")
	VendorTypeElectrical  = VendorType("electrical")
	VendorTypePlumbing    = VendorType("plumbing")
	VendorTypeLandscaping = VendorType("landscaping")
	VendorTypeGeneral     = VendorType("general")
)

// VendorStatus represents the status of a vendor
type VendorStatus string

const (
	VendorStatusActive      = VendorStatus("active")
	VendorStatusInactive    = VendorStatus("inactive")
	VendorStatusSuspended   = VendorStatus("suspended")
	VendorStatusBlacklisted = VendorStatus("blacklisted")
)

// Contact represents contact information
type Contact struct {
	FirstName string  `json:"first_name"`
	LastName  string  `json:"last_name"`
	Email     string  `json:"email"`
	Phone     string  `json:"phone"`
	Mobile    string  `json:"mobile"`
	Address   Address `json:"address"`
	Company   string  `json:"company"`
	Title     string  `json:"title"`
}

// Contract represents a service contract
type Contract struct {
	ID          string                 `json:"id"`
	VendorID    string                 `json:"vendor_id"`
	BuildingID  string                 `json:"building_id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Type        ContractType           `json:"type"`
	Status      ContractStatus         `json:"status"`
	StartDate   time.Time              `json:"start_date"`
	EndDate     time.Time              `json:"end_date"`
	Value       float64                `json:"value"`
	Terms       string                 `json:"terms"`
	Config      map[string]interface{} `json:"config"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// ContractType represents the type of contract
type ContractType string

const (
	ContractTypeMaintenance = ContractType("maintenance")
	ContractTypeService     = ContractType("service")
	ContractTypeSupply      = ContractType("supply")
	ContractTypeLease       = ContractType("lease")
	ContractTypeConsulting  = ContractType("consulting")
)

// ContractStatus represents the status of a contract
type ContractStatus string

const (
	ContractStatusDraft      = ContractStatus("draft")
	ContractStatusActive     = ContractStatus("active")
	ContractStatusExpired    = ContractStatus("expired")
	ContractStatusTerminated = ContractStatus("terminated")
	ContractStatusRenewed    = ContractStatus("renewed")
)

// FacilityMetrics tracks facility management performance
type FacilityMetrics struct {
	TotalBuildings      int64   `json:"total_buildings"`
	TotalSpaces         int64   `json:"total_spaces"`
	TotalAssets         int64   `json:"total_assets"`
	ActiveBuildings     int64   `json:"active_buildings"`
	ActiveSpaces        int64   `json:"active_spaces"`
	ActiveAssets        int64   `json:"active_assets"`
	TotalWorkOrders     int64   `json:"total_work_orders"`
	OpenWorkOrders      int64   `json:"open_work_orders"`
	CompletedWorkOrders int64   `json:"completed_work_orders"`
	OverdueWorkOrders   int64   `json:"overdue_work_orders"`
	TotalMaintenance    int64   `json:"total_maintenance"`
	UpcomingMaintenance int64   `json:"upcoming_maintenance"`
	TotalInspections    int64   `json:"total_inspections"`
	OpenFindings        int64   `json:"open_findings"`
	TotalVendors        int64   `json:"total_vendors"`
	ActiveContracts     int64   `json:"active_contracts"`
	AverageResponseTime float64 `json:"average_response_time"`
	MaintenanceCost     float64 `json:"maintenance_cost"`
	AssetUtilization    float64 `json:"asset_utilization"`
}

// NewFacilityManager creates a new facility manager
func NewFacilityManager() *FacilityManager {
	return &FacilityManager{
		buildings:   make(map[string]*Building),
		spaces:      make(map[string]*Space),
		assets:      make(map[string]*Asset),
		workOrders:  make(map[string]*WorkOrder),
		maintenance: make(map[string]*MaintenanceSchedule),
		inspections: make(map[string]*Inspection),
		vendors:     make(map[string]*Vendor),
		contracts:   make(map[string]*Contract),
		metrics:     &FacilityMetrics{},
	}
}

// Building Management Methods

// CreateBuilding creates a new building
func (fm *FacilityManager) CreateBuilding(building *Building) error {
	if building == nil {
		return fmt.Errorf("building cannot be nil")
	}

	if building.ID == "" {
		building.ID = fmt.Sprintf("building_%d", time.Now().UnixNano())
	}

	if building.Name == "" {
		return fmt.Errorf("building name cannot be empty")
	}

	// Set timestamps
	now := time.Now()
	building.CreatedAt = now
	building.UpdatedAt = now

	// Set default status
	if building.Status == "" {
		building.Status = BuildingStatusActive
	}

	// Store building
	fm.buildings[building.ID] = building
	fm.metrics.TotalBuildings++

	logger.Info("Building created: %s (%s)", building.ID, building.Name)
	return nil
}

// GetBuilding retrieves a building by ID
func (fm *FacilityManager) GetBuilding(buildingID string) (*Building, error) {
	building, exists := fm.buildings[buildingID]
	if !exists {
		return nil, fmt.Errorf("building %s not found", buildingID)
	}
	return building, nil
}

// UpdateBuilding updates an existing building
func (fm *FacilityManager) UpdateBuilding(buildingID string, updates map[string]interface{}) error {
	building, exists := fm.buildings[buildingID]
	if !exists {
		return fmt.Errorf("building %s not found", buildingID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "name":
			if name, ok := value.(string); ok {
				building.Name = name
			}
		case "status":
			if status, ok := value.(string); ok {
				building.Status = BuildingStatus(status)
			}
		case "config":
			if config, ok := value.(map[string]interface{}); ok {
				building.Config = config
			}
		}
	}

	building.UpdatedAt = time.Now()
	logger.Info("Building updated: %s", buildingID)
	return nil
}

// DeleteBuilding deletes a building
func (fm *FacilityManager) DeleteBuilding(buildingID string) error {
	building, exists := fm.buildings[buildingID]
	if !exists {
		return fmt.Errorf("building %s not found", buildingID)
	}

	// Delete associated spaces
	for _, spaceID := range building.Spaces {
		delete(fm.spaces, spaceID)
	}

	// Delete associated assets
	for _, assetID := range building.Assets {
		delete(fm.assets, assetID)
	}

	// Delete building
	delete(fm.buildings, buildingID)
	fm.metrics.TotalBuildings--

	logger.Info("Building deleted: %s (%s)", buildingID, building.Name)
	return nil
}

// ListBuildings returns all buildings
func (fm *FacilityManager) ListBuildings() []*Building {
	buildings := make([]*Building, 0, len(fm.buildings))
	for _, building := range fm.buildings {
		buildings = append(buildings, building)
	}
	return buildings
}

// Space Management Methods

// CreateSpace creates a new space
func (fm *FacilityManager) CreateSpace(space *Space) error {
	if space == nil {
		return fmt.Errorf("space cannot be nil")
	}

	if space.ID == "" {
		space.ID = fmt.Sprintf("space_%d", time.Now().UnixNano())
	}

	if space.Name == "" {
		return fmt.Errorf("space name cannot be empty")
	}

	if space.BuildingID == "" {
		return fmt.Errorf("building ID cannot be empty")
	}

	// Verify building exists
	if _, exists := fm.buildings[space.BuildingID]; !exists {
		return fmt.Errorf("building %s not found", space.BuildingID)
	}

	// Set timestamps
	now := time.Now()
	space.CreatedAt = now
	space.UpdatedAt = now

	// Set default status
	if space.Status == "" {
		space.Status = SpaceStatusAvailable
	}

	// Store space
	fm.spaces[space.ID] = space
	fm.metrics.TotalSpaces++

	// Add to building
	building := fm.buildings[space.BuildingID]
	building.Spaces = append(building.Spaces, space.ID)

	logger.Info("Space created: %s (%s)", space.ID, space.Name)
	return nil
}

// GetSpace retrieves a space by ID
func (fm *FacilityManager) GetSpace(spaceID string) (*Space, error) {
	space, exists := fm.spaces[spaceID]
	if !exists {
		return nil, fmt.Errorf("space %s not found", spaceID)
	}
	return space, nil
}

// UpdateSpace updates an existing space
func (fm *FacilityManager) UpdateSpace(spaceID string, updates map[string]interface{}) error {
	space, exists := fm.spaces[spaceID]
	if !exists {
		return fmt.Errorf("space %s not found", spaceID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "name":
			if name, ok := value.(string); ok {
				space.Name = name
			}
		case "status":
			if status, ok := value.(string); ok {
				space.Status = SpaceStatus(status)
			}
		case "occupancy":
			if occupancy, ok := value.(int); ok {
				space.Occupancy = occupancy
			}
		}
	}

	space.UpdatedAt = time.Now()
	logger.Info("Space updated: %s", spaceID)
	return nil
}

// DeleteSpace deletes a space
func (fm *FacilityManager) DeleteSpace(spaceID string) error {
	space, exists := fm.spaces[spaceID]
	if !exists {
		return fmt.Errorf("space %s not found", spaceID)
	}

	// Remove from building
	building := fm.buildings[space.BuildingID]
	for i, id := range building.Spaces {
		if id == spaceID {
			building.Spaces = append(building.Spaces[:i], building.Spaces[i+1:]...)
			break
		}
	}

	// Delete space
	delete(fm.spaces, spaceID)
	fm.metrics.TotalSpaces--

	logger.Info("Space deleted: %s (%s)", spaceID, space.Name)
	return nil
}

// ListSpaces returns all spaces
func (fm *FacilityManager) ListSpaces() []*Space {
	spaces := make([]*Space, 0, len(fm.spaces))
	for _, space := range fm.spaces {
		spaces = append(spaces, space)
	}
	return spaces
}

// GetSpacesByBuilding returns spaces for a specific building
func (fm *FacilityManager) GetSpacesByBuilding(buildingID string) []*Space {
	var spaces []*Space
	for _, space := range fm.spaces {
		if space.BuildingID == buildingID {
			spaces = append(spaces, space)
		}
	}
	return spaces
}

// Asset Management Methods

// CreateAsset creates a new asset
func (fm *FacilityManager) CreateAsset(asset *Asset) error {
	if asset == nil {
		return fmt.Errorf("asset cannot be nil")
	}

	if asset.ID == "" {
		asset.ID = fmt.Sprintf("asset_%d", time.Now().UnixNano())
	}

	if asset.Name == "" {
		return fmt.Errorf("asset name cannot be empty")
	}

	if asset.BuildingID == "" {
		return fmt.Errorf("building ID cannot be empty")
	}

	// Verify building exists
	if _, exists := fm.buildings[asset.BuildingID]; !exists {
		return fmt.Errorf("building %s not found", asset.BuildingID)
	}

	// Verify space exists if provided
	if asset.SpaceID != "" {
		if _, exists := fm.spaces[asset.SpaceID]; !exists {
			return fmt.Errorf("space %s not found", asset.SpaceID)
		}
	}

	// Set timestamps
	now := time.Now()
	asset.CreatedAt = now
	asset.UpdatedAt = now

	// Set default status
	if asset.Status == "" {
		asset.Status = AssetStatusOperational
	}

	// Set default condition
	if asset.Condition == "" {
		asset.Condition = AssetConditionGood
	}

	// Store asset
	fm.assets[asset.ID] = asset
	fm.metrics.TotalAssets++

	// Add to building
	building := fm.buildings[asset.BuildingID]
	building.Assets = append(building.Assets, asset.ID)

	// Add to space if provided
	if asset.SpaceID != "" {
		space := fm.spaces[asset.SpaceID]
		space.Assets = append(space.Assets, asset.ID)
	}

	logger.Info("Asset created: %s (%s)", asset.ID, asset.Name)
	return nil
}

// GetAsset retrieves an asset by ID
func (fm *FacilityManager) GetAsset(assetID string) (*Asset, error) {
	asset, exists := fm.assets[assetID]
	if !exists {
		return nil, fmt.Errorf("asset %s not found", assetID)
	}
	return asset, nil
}

// UpdateAsset updates an existing asset
func (fm *FacilityManager) UpdateAsset(assetID string, updates map[string]interface{}) error {
	asset, exists := fm.assets[assetID]
	if !exists {
		return fmt.Errorf("asset %s not found", assetID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "name":
			if name, ok := value.(string); ok {
				asset.Name = name
			}
		case "status":
			if status, ok := value.(string); ok {
				asset.Status = AssetStatus(status)
			}
		case "condition":
			if condition, ok := value.(string); ok {
				asset.Condition = AssetCondition(condition)
			}
		case "last_maintenance":
			if lastMaintenance, ok := value.(time.Time); ok {
				asset.LastMaintenance = &lastMaintenance
			}
		case "next_maintenance":
			if nextMaintenance, ok := value.(time.Time); ok {
				asset.NextMaintenance = &nextMaintenance
			}
		}
	}

	asset.UpdatedAt = time.Now()
	logger.Info("Asset updated: %s", assetID)
	return nil
}

// DeleteAsset deletes an asset
func (fm *FacilityManager) DeleteAsset(assetID string) error {
	asset, exists := fm.assets[assetID]
	if !exists {
		return fmt.Errorf("asset %s not found", assetID)
	}

	// Remove from building
	building := fm.buildings[asset.BuildingID]
	for i, id := range building.Assets {
		if id == assetID {
			building.Assets = append(building.Assets[:i], building.Assets[i+1:]...)
			break
		}
	}

	// Remove from space if provided
	if asset.SpaceID != "" {
		space := fm.spaces[asset.SpaceID]
		for i, id := range space.Assets {
			if id == assetID {
				space.Assets = append(space.Assets[:i], space.Assets[i+1:]...)
				break
			}
		}
	}

	// Delete asset
	delete(fm.assets, assetID)
	fm.metrics.TotalAssets--

	logger.Info("Asset deleted: %s (%s)", assetID, asset.Name)
	return nil
}

// ListAssets returns all assets
func (fm *FacilityManager) ListAssets() []*Asset {
	assets := make([]*Asset, 0, len(fm.assets))
	for _, asset := range fm.assets {
		assets = append(assets, asset)
	}
	return assets
}

// GetAssetsByBuilding returns assets for a specific building
func (fm *FacilityManager) GetAssetsByBuilding(buildingID string) []*Asset {
	var assets []*Asset
	for _, asset := range fm.assets {
		if asset.BuildingID == buildingID {
			assets = append(assets, asset)
		}
	}
	return assets
}

// GetAssetsBySpace returns assets for a specific space
func (fm *FacilityManager) GetAssetsBySpace(spaceID string) []*Asset {
	var assets []*Asset
	for _, asset := range fm.assets {
		if asset.SpaceID == spaceID {
			assets = append(assets, asset)
		}
	}
	return assets
}

// GetMetrics returns facility metrics
func (fm *FacilityManager) GetMetrics() *FacilityMetrics {
	// Update metrics
	fm.metrics.TotalBuildings = int64(len(fm.buildings))
	fm.metrics.TotalSpaces = int64(len(fm.spaces))
	fm.metrics.TotalAssets = int64(len(fm.assets))
	fm.metrics.TotalWorkOrders = int64(len(fm.workOrders))
	fm.metrics.TotalVendors = int64(len(fm.vendors))
	fm.metrics.ActiveContracts = int64(len(fm.contracts))

	// Count open work orders
	fm.metrics.OpenWorkOrders = 0
	fm.metrics.CompletedWorkOrders = 0
	fm.metrics.OverdueWorkOrders = 0
	now := time.Now()

	for _, workOrder := range fm.workOrders {
		switch workOrder.Status {
		case WorkOrderStatusOpen, WorkOrderStatusAssigned, WorkOrderStatusInProgress:
			fm.metrics.OpenWorkOrders++
			if workOrder.DueDate != nil && workOrder.DueDate.Before(now) {
				fm.metrics.OverdueWorkOrders++
			}
		case WorkOrderStatusCompleted, WorkOrderStatusClosed:
			fm.metrics.CompletedWorkOrders++
		}
	}

	// Count upcoming maintenance
	fm.metrics.UpcomingMaintenance = 0
	for _, maintenance := range fm.maintenance {
		if maintenance.NextRun.Before(now.Add(7 * 24 * time.Hour)) {
			fm.metrics.UpcomingMaintenance++
		}
	}

	// Count open findings
	fm.metrics.OpenFindings = 0
	for _, inspection := range fm.inspections {
		for _, finding := range inspection.Findings {
			if finding.Status == FindingStatusOpen || finding.Status == FindingStatusInProgress {
				fm.metrics.OpenFindings++
			}
		}
	}

	return fm.metrics
}
