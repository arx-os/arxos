package it

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/security"
)

// ITManager manages all IT operations and integrates with building infrastructure
type ITManager struct {
	assetManager     *ITAssetManager
	configManager    *ConfigurationManager
	inventoryManager *InventoryManager
	workOrderManager *ITWorkOrderManager
	versionControl   *VersionControlManager
	securityManager  *security.VersionControlSecurity // Added for security
	metrics          *ITMetrics
	mu               sync.RWMutex
}

// ITMetrics represents overall IT management metrics
type ITMetrics struct {
	TotalAssets         int64   `json:"total_assets"`
	ActiveAssets        int64   `json:"active_assets"`
	TotalConfigurations int64   `json:"total_configurations"`
	TotalRoomSetups     int64   `json:"total_room_setups"`
	TotalWorkOrders     int64   `json:"total_work_orders"`
	OpenWorkOrders      int64   `json:"open_work_orders"`
	TotalParts          int64   `json:"total_parts"`
	LowStockParts       int64   `json:"low_stock_parts"`
	TotalValue          float64 `json:"total_value"`
	AssetUtilization    float64 `json:"asset_utilization"`
	WorkOrderEfficiency float64 `json:"work_order_efficiency"`
	InventoryAccuracy   float64 `json:"inventory_accuracy"`
}

// NewITManager creates a new IT manager
func NewITManager() *ITManager {
	versionControl := NewVersionControlManager()
	return &ITManager{
		assetManager:     NewITAssetManager(),
		configManager:    NewConfigurationManager(),
		inventoryManager: NewInventoryManager(),
		workOrderManager: NewITWorkOrderManager(),
		versionControl:   versionControl,
		securityManager:  versionControl.GetSecurityManager(), // Get security from version control
		metrics:          &ITMetrics{},
	}
}

// GetAssetManager returns the asset manager
func (im *ITManager) GetAssetManager() *ITAssetManager {
	return im.assetManager
}

// GetConfigManager returns the configuration manager
func (im *ITManager) GetConfigManager() *ConfigurationManager {
	return im.configManager
}

// GetInventoryManager returns the inventory manager
func (im *ITManager) GetInventoryManager() *InventoryManager {
	return im.inventoryManager
}

// GetWorkOrderManager returns the work order manager
func (im *ITManager) GetWorkOrderManager() *ITWorkOrderManager {
	return im.workOrderManager
}

// GetVersionControlManager returns the version control manager
func (im *ITManager) GetVersionControlManager() *VersionControlManager {
	return im.versionControl
}

// GetSecurityManager returns the security manager
func (im *ITManager) GetSecurityManager() *security.VersionControlSecurity {
	return im.securityManager
}

// GetMetrics returns overall IT metrics
func (im *ITManager) GetMetrics() *ITMetrics {
	im.mu.RLock()
	defer im.mu.RUnlock()

	return im.metrics
}

// UpdateMetrics updates all IT metrics
func (im *ITManager) UpdateMetrics() {
	im.mu.Lock()
	defer im.mu.Unlock()

	// Update individual component metrics
	im.assetManager.UpdateMetrics()
	im.configManager.UpdateMetrics()
	im.inventoryManager.UpdateInventoryMetrics()
	im.workOrderManager.UpdateWorkOrderMetrics()

	// Aggregate metrics
	assetMetrics := im.assetManager.GetMetrics()
	configMetrics := im.configManager.GetMetrics()
	inventoryMetrics := im.inventoryManager.GetInventoryMetrics()
	workOrderMetrics := im.workOrderManager.GetWorkOrderMetrics()

	im.metrics.TotalAssets = assetMetrics.TotalAssets
	im.metrics.ActiveAssets = assetMetrics.ActiveAssets
	im.metrics.TotalConfigurations = configMetrics.TotalConfigurations
	im.metrics.TotalRoomSetups = configMetrics.TotalRoomSetups
	im.metrics.TotalWorkOrders = workOrderMetrics.TotalWorkOrders
	im.metrics.OpenWorkOrders = workOrderMetrics.OpenWorkOrders
	im.metrics.TotalParts = inventoryMetrics.TotalParts
	im.metrics.LowStockParts = inventoryMetrics.LowStockParts
	im.metrics.TotalValue = assetMetrics.TotalValue

	logger.Debug("IT metrics updated")
}

// CreateRoomSetupFromPath creates a room setup from an ArxOS building path
func (im *ITManager) CreateRoomSetupFromPath(buildingPath string, setupType SetupType, createdBy string) (*RoomSetup, error) {
	// Parse building path: /buildings/{building}/floors/{floor}/rooms/{room}
	pathParts := strings.Split(strings.Trim(buildingPath, "/"), "/")
	if len(pathParts) < 6 {
		return nil, fmt.Errorf("invalid building path format: %s", buildingPath)
	}

	// Extract building, floor, and room from path
	building := pathParts[1]
	floor := pathParts[3]
	room := pathParts[5]

	// Create location from path
	location := Location{
		Building:   building,
		Floor:      floor,
		Room:       room,
		RoomNumber: room, // Use room as room number for now
	}

	// Create room setup
	setup := &RoomSetup{
		Name:            fmt.Sprintf("%s - %s", room, setupType),
		Description:     fmt.Sprintf("IT setup for %s in %s", room, building),
		Room:            location,
		SetupType:       setupType,
		Assets:          []RoomAsset{},
		Connections:     []Connection{},
		UserPreferences: make(map[string]interface{}),
		IsActive:        true,
		CreatedBy:       createdBy,
	}

	// Create the setup
	err := im.configManager.CreateRoomSetup(setup)
	if err != nil {
		return nil, fmt.Errorf("failed to create room setup: %w", err)
	}

	logger.Info("Room setup created from path %s: %s", buildingPath, setup.ID)
	return setup, nil
}

// GetRoomSetupByPath gets a room setup by building path
func (im *ITManager) GetRoomSetupByPath(buildingPath string) (*RoomSetup, error) {
	// Parse building path
	pathParts := strings.Split(strings.Trim(buildingPath, "/"), "/")
	if len(pathParts) < 6 {
		return nil, fmt.Errorf("invalid building path format: %s", buildingPath)
	}

	building := pathParts[1]
	room := pathParts[5]

	// Find room setup by location
	filter := SetupFilter{
		Building: building,
		Room:     room,
		IsActive: &[]bool{true}[0], // Only active setups
	}

	setups := im.configManager.GetRoomSetups(filter)
	if len(setups) == 0 {
		return nil, fmt.Errorf("no active room setup found for path: %s", buildingPath)
	}

	return setups[0], nil
}

// AddAssetToRoom adds an asset to a room setup
func (im *ITManager) AddAssetToRoom(assetID string, roomPath string, position Position, isPrimary bool) error {
	// Get the room setup
	setup, err := im.GetRoomSetupByPath(roomPath)
	if err != nil {
		return fmt.Errorf("failed to get room setup: %w", err)
	}

	// Get the asset
	asset, err := im.assetManager.GetAsset(assetID)
	if err != nil {
		return fmt.Errorf("failed to get asset: %w", err)
	}

	// Create room asset
	roomAsset := RoomAsset{
		AssetID:     assetID,
		Position:    position,
		Connections: []string{},
		Settings:    make(map[string]interface{}),
		IsPrimary:   isPrimary,
		IsRequired:  true,
		Notes:       fmt.Sprintf("Added to %s", roomPath),
	}

	// Add to room setup
	setup.Assets = append(setup.Assets, roomAsset)

	// Update asset location
	asset.Location = setup.Room
	asset.UpdatedAt = time.Now()

	// Update both
	err = im.configManager.UpdateRoomSetup(setup.ID, setup)
	if err != nil {
		return fmt.Errorf("failed to update room setup: %w", err)
	}

	err = im.assetManager.UpdateAsset(assetID, asset)
	if err != nil {
		return fmt.Errorf("failed to update asset: %w", err)
	}

	logger.Info("Asset %s added to room %s", assetID, roomPath)
	return nil
}

// RemoveAssetFromRoom removes an asset from a room setup
func (im *ITManager) RemoveAssetFromRoom(assetID string, roomPath string) error {
	// Get the room setup
	setup, err := im.GetRoomSetupByPath(roomPath)
	if err != nil {
		return fmt.Errorf("failed to get room setup: %w", err)
	}

	// Find and remove the asset
	for i, roomAsset := range setup.Assets {
		if roomAsset.AssetID == assetID {
			setup.Assets = append(setup.Assets[:i], setup.Assets[i+1:]...)
			break
		}
	}

	// Update room setup
	err = im.configManager.UpdateRoomSetup(setup.ID, setup)
	if err != nil {
		return fmt.Errorf("failed to update room setup: %w", err)
	}

	logger.Info("Asset %s removed from room %s", assetID, roomPath)
	return nil
}

// GetAssetsByRoomPath gets all assets in a room
func (im *ITManager) GetAssetsByRoomPath(roomPath string) ([]*ITAsset, error) {
	// Get the room setup
	setup, err := im.GetRoomSetupByPath(roomPath)
	if err != nil {
		return nil, fmt.Errorf("failed to get room setup: %w", err)
	}

	// Get all assets in the room
	var assets []*ITAsset
	for _, roomAsset := range setup.Assets {
		asset, err := im.assetManager.GetAsset(roomAsset.AssetID)
		if err != nil {
			logger.Warn("Failed to get asset %s: %v", roomAsset.AssetID, err)
			continue
		}
		assets = append(assets, asset)
	}

	return assets, nil
}

// CreateWorkOrderForRoom creates a work order for a specific room
func (im *ITManager) CreateWorkOrderForRoom(roomPath string, title string, description string, workOrderType WorkOrderType, priority Priority, requestedBy string) (*ITWorkOrder, error) {
	// Parse room path to get location
	pathParts := strings.Split(strings.Trim(roomPath, "/"), "/")
	if len(pathParts) < 6 {
		return nil, fmt.Errorf("invalid building path format: %s", roomPath)
	}

	building := pathParts[1]
	floor := pathParts[3]
	room := pathParts[5]

	location := Location{
		Building:   building,
		Floor:      floor,
		Room:       room,
		RoomNumber: room,
	}

	// Create work order
	workOrder := &ITWorkOrder{
		Title:       title,
		Description: description,
		Type:        workOrderType,
		Priority:    priority,
		Status:      WorkOrderStatusOpen,
		Location:    location,
		RequestedBy: requestedBy,
		Assets:      []string{},
		Parts:       []PartRequest{},
		Notes:       fmt.Sprintf("Work order for room: %s", roomPath),
	}

	// Create the work order
	err := im.workOrderManager.CreateWorkOrder(workOrder)
	if err != nil {
		return nil, fmt.Errorf("failed to create work order: %w", err)
	}

	logger.Info("Work order created for room %s: %s", roomPath, workOrder.ID)
	return workOrder, nil
}

// GetWorkOrdersByRoomPath gets all work orders for a specific room
func (im *ITManager) GetWorkOrdersByRoomPath(roomPath string) ([]*ITWorkOrder, error) {
	// Parse room path
	pathParts := strings.Split(strings.Trim(roomPath, "/"), "/")
	if len(pathParts) < 6 {
		return nil, fmt.Errorf("invalid building path format: %s", roomPath)
	}

	building := pathParts[1]
	room := pathParts[5]

	// Filter work orders by location
	filter := WorkOrderFilter{
		Building: building,
		Room:     room,
	}

	workOrders := im.workOrderManager.GetWorkOrders(filter)
	return workOrders, nil
}

// CreateConfigurationFromTemplate creates a configuration from a template
func (im *ITManager) CreateConfigurationFromTemplate(templateID string, assetType AssetType, roomPath string, createdBy string) (*Configuration, error) {
	// Get the template
	template, err := im.configManager.GetConfiguration(templateID)
	if err != nil {
		return nil, fmt.Errorf("failed to get template: %w", err)
	}

	if !template.IsTemplate {
		return nil, fmt.Errorf("configuration %s is not a template", templateID)
	}

	// Create new configuration from template
	config := &Configuration{
		Name:         fmt.Sprintf("%s - %s", template.Name, assetType),
		Description:  fmt.Sprintf("Configuration for %s based on template %s", assetType, template.Name),
		AssetType:    assetType,
		Components:   make([]Component, len(template.Components)),
		Software:     make([]Software, len(template.Software)),
		UserSettings: make(map[string]interface{}),
		IsTemplate:   false,
		CreatedBy:    createdBy,
	}

	// Deep copy components
	copy(config.Components, template.Components)

	// Deep copy software
	copy(config.Software, template.Software)

	// Deep copy user settings
	for k, v := range template.UserSettings {
		config.UserSettings[k] = v
	}

	// Copy network settings if present
	if template.NetworkSettings != nil {
		config.NetworkSettings = &NetworkSettings{
			IPAddress:  template.NetworkSettings.IPAddress,
			SubnetMask: template.NetworkSettings.SubnetMask,
			Gateway:    template.NetworkSettings.Gateway,
			DNS:        make([]string, len(template.NetworkSettings.DNS)),
			VLAN:       template.NetworkSettings.VLAN,
		}
		copy(config.NetworkSettings.DNS, template.NetworkSettings.DNS)

		// Copy wireless settings if present
		if template.NetworkSettings.Wireless != nil {
			config.NetworkSettings.Wireless = &WirelessSettings{
				SSID:           template.NetworkSettings.Wireless.SSID,
				Security:       template.NetworkSettings.Wireless.Security,
				Encryption:     template.NetworkSettings.Wireless.Encryption,
				Password:       template.NetworkSettings.Wireless.Password,
				Frequency:      template.NetworkSettings.Wireless.Frequency,
				Channel:        template.NetworkSettings.Wireless.Channel,
				SignalStrength: template.NetworkSettings.Wireless.SignalStrength,
			}
		}

		// Copy ports
		config.NetworkSettings.Ports = make([]PortConfig, len(template.NetworkSettings.Ports))
		copy(config.NetworkSettings.Ports, template.NetworkSettings.Ports)

		// Copy firewall rules
		config.NetworkSettings.FirewallRules = make([]FirewallRule, len(template.NetworkSettings.FirewallRules))
		copy(config.NetworkSettings.FirewallRules, template.NetworkSettings.FirewallRules)
	}

	// Create the configuration
	err = im.configManager.CreateConfiguration(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create configuration: %w", err)
	}

	logger.Info("Configuration created from template %s: %s", templateID, config.ID)
	return config, nil
}

// GetRoomSetupSummary returns a summary of a room's IT setup
func (im *ITManager) GetRoomSetupSummary(roomPath string) (*RoomSetupSummary, error) {
	// Get the room setup
	setup, err := im.GetRoomSetupByPath(roomPath)
	if err != nil {
		return nil, fmt.Errorf("failed to get room setup: %w", err)
	}

	// Get all assets in the room
	assets, err := im.GetAssetsByRoomPath(roomPath)
	if err != nil {
		return nil, fmt.Errorf("failed to get assets: %w", err)
	}

	// Get work orders for the room
	workOrders, err := im.GetWorkOrdersByRoomPath(roomPath)
	if err != nil {
		return nil, fmt.Errorf("failed to get work orders: %w", err)
	}

	// Create summary
	summary := &RoomSetupSummary{
		RoomPath:       roomPath,
		SetupType:      setup.SetupType,
		IsActive:       setup.IsActive,
		TotalAssets:    len(assets),
		AssetTypes:     make(map[string]int),
		WorkOrders:     len(workOrders),
		OpenWorkOrders: 0,
		Assets:         assets,
		LastUpdated:    setup.UpdatedAt,
	}

	// Count asset types
	for _, asset := range assets {
		summary.AssetTypes[string(asset.Type)]++
	}

	// Count open work orders
	for _, workOrder := range workOrders {
		if workOrder.Status == WorkOrderStatusOpen || workOrder.Status == WorkOrderStatusInProgress {
			summary.OpenWorkOrders++
		}
	}

	return summary, nil
}

// RoomSetupSummary represents a summary of a room's IT setup
type RoomSetupSummary struct {
	RoomPath       string         `json:"room_path"`
	SetupType      SetupType      `json:"setup_type"`
	IsActive       bool           `json:"is_active"`
	TotalAssets    int            `json:"total_assets"`
	AssetTypes     map[string]int `json:"asset_types"`
	WorkOrders     int            `json:"work_orders"`
	OpenWorkOrders int            `json:"open_work_orders"`
	Assets         []*ITAsset     `json:"assets"`
	LastUpdated    time.Time      `json:"last_updated"`
}

// GetBuildingITSummary returns a summary of IT assets for an entire building
func (im *ITManager) GetBuildingITSummary(buildingPath string) (*BuildingITSummary, error) {
	// Parse building path
	pathParts := strings.Split(strings.Trim(buildingPath, "/"), "/")
	if len(pathParts) < 2 {
		return nil, fmt.Errorf("invalid building path format: %s", buildingPath)
	}

	building := pathParts[1]

	// Get all room setups for the building
	filter := SetupFilter{
		Building: building,
		IsActive: &[]bool{true}[0],
	}

	setups := im.configManager.GetRoomSetups(filter)

	// Create summary
	summary := &BuildingITSummary{
		BuildingPath:    buildingPath,
		TotalRooms:      len(setups),
		TotalAssets:     0,
		AssetTypes:      make(map[string]int),
		SetupTypes:      make(map[string]int),
		TotalWorkOrders: 0,
		OpenWorkOrders:  0,
		Rooms:           make([]RoomSetupSummary, 0),
	}

	// Process each room
	for _, setup := range setups {
		roomPath := fmt.Sprintf("/buildings/%s/floors/%s/rooms/%s", setup.Room.Building, setup.Room.Floor, setup.Room.Room)

		roomSummary, err := im.GetRoomSetupSummary(roomPath)
		if err != nil {
			logger.Warn("Failed to get room summary for %s: %v", roomPath, err)
			continue
		}

		summary.Rooms = append(summary.Rooms, *roomSummary)
		summary.TotalAssets += roomSummary.TotalAssets
		summary.TotalWorkOrders += roomSummary.WorkOrders
		summary.OpenWorkOrders += roomSummary.OpenWorkOrders

		// Count asset types
		for assetType, count := range roomSummary.AssetTypes {
			summary.AssetTypes[assetType] += count
		}

		// Count setup types
		summary.SetupTypes[string(setup.SetupType)]++
	}

	return summary, nil
}

// BuildingITSummary represents a summary of IT assets for a building
type BuildingITSummary struct {
	BuildingPath    string             `json:"building_path"`
	TotalRooms      int                `json:"total_rooms"`
	TotalAssets     int                `json:"total_assets"`
	AssetTypes      map[string]int     `json:"asset_types"`
	SetupTypes      map[string]int     `json:"setup_types"`
	TotalWorkOrders int                `json:"total_work_orders"`
	OpenWorkOrders  int                `json:"open_work_orders"`
	Rooms           []RoomSetupSummary `json:"rooms"`
}

// ValidateBuildingPath validates an ArxOS building path
func (im *ITManager) ValidateBuildingPath(path string) error {
	// Expected format: /buildings/{building}/floors/{floor}/rooms/{room}
	pathParts := strings.Split(strings.Trim(path, "/"), "/")

	if len(pathParts) != 6 {
		return fmt.Errorf("invalid path format: expected /buildings/{building}/floors/{floor}/rooms/{room}, got %s", path)
	}

	if pathParts[0] != "buildings" {
		return fmt.Errorf("path must start with 'buildings', got %s", pathParts[0])
	}

	if pathParts[2] != "floors" {
		return fmt.Errorf("path must contain 'floors', got %s", pathParts[2])
	}

	if pathParts[4] != "rooms" {
		return fmt.Errorf("path must contain 'rooms', got %s", pathParts[4])
	}

	return nil
}

// GetPathComponents extracts components from a building path
func (im *ITManager) GetPathComponents(path string) (building, floor, room string, err error) {
	err = im.ValidateBuildingPath(path)
	if err != nil {
		return "", "", "", err
	}

	pathParts := strings.Split(strings.Trim(path, "/"), "/")
	building = pathParts[1]
	floor = pathParts[3]
	room = pathParts[5]

	return building, floor, room, nil
}

// Version Control Methods (Git-like operations for room configurations)

// CreateBranch creates a new branch for a room configuration
func (im *ITManager) CreateBranch(roomPath, branchName, template string) error {
	return im.versionControl.CreateBranch(roomPath, branchName, template)
}

// CommitChanges commits changes to a room configuration
func (im *ITManager) CommitChanges(roomPath, branch, message, author string, changes []*HardwareChange) (*RoomCommit, error) {
	return im.versionControl.CommitChanges(roomPath, branch, message, author, changes)
}

// PushChanges pushes changes to the remote repository (syncs with physical reality)
func (im *ITManager) PushChanges(roomPath, branch string) error {
	return im.versionControl.PushChanges(roomPath, branch)
}

// PullChanges pulls the latest changes from the remote repository
func (im *ITManager) PullChanges(roomPath, branch string) error {
	return im.versionControl.PullChanges(roomPath, branch)
}

// GetRoomHistory returns the commit history for a room
func (im *ITManager) GetRoomHistory(roomPath, branch string) ([]*RoomCommit, error) {
	return im.versionControl.GetRoomHistory(roomPath, branch)
}

// RollbackRoom rolls back a room to a specific commit
func (im *ITManager) RollbackRoom(roomPath, branch, commitID string) error {
	return im.versionControl.RollbackRoom(roomPath, branch, commitID)
}

// CreatePullRequest creates a pull request for room configuration changes
func (im *ITManager) CreatePullRequest(roomPath, title, description, createdBy, baseBranch, headBranch string) (*PullRequest, error) {
	return im.versionControl.CreatePullRequest(roomPath, title, description, createdBy, baseBranch, headBranch)
}

// ReviewPullRequest reviews a pull request
func (im *ITManager) ReviewPullRequest(prID string, approved bool, reviewer string) error {
	return im.versionControl.ReviewPullRequest(prID, approved, reviewer)
}

// MergePullRequest merges a pull request
func (im *ITManager) MergePullRequest(prID string, deploy bool) error {
	return im.versionControl.MergePullRequest(prID, deploy)
}

// GetPullRequest gets a pull request by ID
func (im *ITManager) GetPullRequest(prID string) (*PullRequest, error) {
	im.versionControl.mu.RLock()
	defer im.versionControl.mu.RUnlock()

	pr, exists := im.versionControl.pullRequests[prID]
	if !exists {
		return nil, fmt.Errorf("pull request %s not found", prID)
	}

	return pr, nil
}

// ListPullRequests lists all pull requests for a room
func (im *ITManager) ListPullRequests(roomPath string) ([]*PullRequest, error) {
	im.versionControl.mu.RLock()
	defer im.versionControl.mu.RUnlock()

	var prs []*PullRequest
	for _, pr := range im.versionControl.pullRequests {
		if pr.RoomPath == roomPath {
			prs = append(prs, pr)
		}
	}

	return prs, nil
}

// CreateFeatureRequest creates a feature request for room configuration changes
func (im *ITManager) CreateFeatureRequest(roomPath, title, description, priority, requestedBy string) (*PullRequest, error) {
	// Create a feature branch
	featureBranch := fmt.Sprintf("feature-%s-%d", strings.ReplaceAll(title, " ", "-"), time.Now().Unix())

	err := im.CreateBranch(roomPath, featureBranch, "main")
	if err != nil {
		return nil, fmt.Errorf("failed to create feature branch: %w", err)
	}

	// Create pull request
	pr, err := im.CreatePullRequest(roomPath, title, description, requestedBy, "main", featureBranch)
	if err != nil {
		return nil, fmt.Errorf("failed to create pull request: %w", err)
	}

	// Add priority to metadata
	pr.Metadata["priority"] = priority
	pr.Metadata["type"] = "feature_request"

	return pr, nil
}

// CreateBulkUpdate creates a bulk update for multiple rooms
func (im *ITManager) CreateBulkUpdate(pattern, template, title, description, createdBy string) ([]*PullRequest, error) {
	// This would parse the pattern and create pull requests for each matching room
	// For now, we'll return an error indicating this needs to be implemented
	return nil, fmt.Errorf("bulk update not yet implemented")
}

// CreateEmergencyFix creates an emergency fix for a room
func (im *ITManager) CreateEmergencyFix(roomPath, issue, priority, reportedBy string) (*PullRequest, error) {
	// Create emergency branch
	emergencyBranch := fmt.Sprintf("emergency-%s-%d", strings.ReplaceAll(issue, " ", "-"), time.Now().Unix())

	err := im.CreateBranch(roomPath, emergencyBranch, "main")
	if err != nil {
		return nil, fmt.Errorf("failed to create emergency branch: %w", err)
	}

	// Create pull request
	pr, err := im.CreatePullRequest(roomPath, fmt.Sprintf("Emergency Fix: %s", issue),
		fmt.Sprintf("Emergency fix for issue: %s", issue), reportedBy, "main", emergencyBranch)
	if err != nil {
		return nil, fmt.Errorf("failed to create emergency pull request: %w", err)
	}

	// Add emergency metadata
	pr.Metadata["priority"] = priority
	pr.Metadata["type"] = "emergency_fix"
	pr.Metadata["issue"] = issue

	return pr, nil
}
