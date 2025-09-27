package it

import (
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ConfigurationManager manages IT configurations and room setups
type ConfigurationManager struct {
	configurations map[string]*Configuration
	roomSetups     map[string]*RoomSetup
	templates      map[string]*Configuration
	setupTemplates map[string]*RoomSetup
	metrics        *ConfigurationMetrics
	mu             sync.RWMutex
}

// ConfigurationMetrics represents configuration management metrics
type ConfigurationMetrics struct {
	TotalConfigurations    int64         `json:"total_configurations"`
	ActiveConfigurations   int64         `json:"active_configurations"`
	TemplateConfigurations int64         `json:"template_configurations"`
	TotalRoomSetups        int64         `json:"total_room_setups"`
	ActiveRoomSetups       int64         `json:"active_room_setups"`
	TemplateRoomSetups     int64         `json:"template_room_setups"`
	MostUsedConfigs        []ConfigUsage `json:"most_used_configs"`
	MostUsedSetups         []SetupUsage  `json:"most_used_setups"`
	ConfigurationHealth    float64       `json:"configuration_health"`
	SetupCompliance        float64       `json:"setup_compliance"`
}

// ConfigUsage represents configuration usage statistics
type ConfigUsage struct {
	ConfigID   string    `json:"config_id"`
	ConfigName string    `json:"config_name"`
	UsageCount int64     `json:"usage_count"`
	LastUsed   time.Time `json:"last_used"`
}

// SetupUsage represents room setup usage statistics
type SetupUsage struct {
	SetupID    string    `json:"setup_id"`
	SetupName  string    `json:"setup_name"`
	UsageCount int64     `json:"usage_count"`
	LastUsed   time.Time `json:"last_used"`
}

// NewConfigurationManager creates a new configuration manager
func NewConfigurationManager() *ConfigurationManager {
	return &ConfigurationManager{
		configurations: make(map[string]*Configuration),
		roomSetups:     make(map[string]*RoomSetup),
		templates:      make(map[string]*Configuration),
		setupTemplates: make(map[string]*RoomSetup),
		metrics:        &ConfigurationMetrics{},
	}
}

// CreateConfiguration creates a new configuration
func (cm *ConfigurationManager) CreateConfiguration(config *Configuration) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if config.ID == "" {
		config.ID = fmt.Sprintf("config_%d", time.Now().UnixNano())
	}

	config.CreatedAt = time.Now()
	config.UpdatedAt = time.Now()

	if config.IsTemplate {
		cm.templates[config.ID] = config
		cm.metrics.TemplateConfigurations++
	} else {
		cm.configurations[config.ID] = config
		cm.metrics.ActiveConfigurations++
	}

	cm.metrics.TotalConfigurations++

	logger.Info("Configuration created: %s", config.ID)
	return nil
}

// GetConfiguration returns a specific configuration
func (cm *ConfigurationManager) GetConfiguration(configID string) (*Configuration, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	// Check regular configurations first
	if config, exists := cm.configurations[configID]; exists {
		return config, nil
	}

	// Check templates
	if config, exists := cm.templates[configID]; exists {
		return config, nil
	}

	return nil, fmt.Errorf("configuration not found: %s", configID)
}

// UpdateConfiguration updates an existing configuration
func (cm *ConfigurationManager) UpdateConfiguration(configID string, config *Configuration) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	config.ID = configID
	config.UpdatedAt = time.Now()

	// Check if it's a template
	if config.IsTemplate {
		if _, exists := cm.templates[configID]; !exists {
			return fmt.Errorf("template configuration not found: %s", configID)
		}
		cm.templates[configID] = config
	} else {
		if _, exists := cm.configurations[configID]; !exists {
			return fmt.Errorf("configuration not found: %s", configID)
		}
		cm.configurations[configID] = config
	}

	logger.Info("Configuration updated: %s", configID)
	return nil
}

// DeleteConfiguration deletes a configuration
func (cm *ConfigurationManager) DeleteConfiguration(configID string) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Check regular configurations first
	if _, exists := cm.configurations[configID]; exists {
		delete(cm.configurations, configID)
		cm.metrics.ActiveConfigurations--
		cm.metrics.TotalConfigurations--
		logger.Info("Configuration deleted: %s", configID)
		return nil
	}

	// Check templates
	if _, exists := cm.templates[configID]; exists {
		delete(cm.templates, configID)
		cm.metrics.TemplateConfigurations--
		cm.metrics.TotalConfigurations--
		logger.Info("Template configuration deleted: %s", configID)
		return nil
	}

	return fmt.Errorf("configuration not found: %s", configID)
}

// GetConfigurations returns all configurations with optional filtering
func (cm *ConfigurationManager) GetConfigurations(filter ConfigFilter) []*Configuration {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var configs []*Configuration

	// Add regular configurations
	for _, config := range cm.configurations {
		if cm.matchesConfigFilter(config, filter) {
			configs = append(configs, config)
		}
	}

	// Add templates if requested
	if filter.IncludeTemplates {
		for _, config := range cm.templates {
			if cm.matchesConfigFilter(config, filter) {
				configs = append(configs, config)
			}
		}
	}

	return configs
}

// ConfigFilter represents filtering criteria for configurations
type ConfigFilter struct {
	AssetType        AssetType `json:"asset_type,omitempty"`
	IsTemplate       *bool     `json:"is_template,omitempty"`
	CreatedBy        string    `json:"created_by,omitempty"`
	IncludeTemplates bool      `json:"include_templates"`
}

// matchesConfigFilter checks if a configuration matches the filter criteria
func (cm *ConfigurationManager) matchesConfigFilter(config *Configuration, filter ConfigFilter) bool {
	if filter.AssetType != "" && config.AssetType != filter.AssetType {
		return false
	}
	if filter.IsTemplate != nil && config.IsTemplate != *filter.IsTemplate {
		return false
	}
	if filter.CreatedBy != "" && config.CreatedBy != filter.CreatedBy {
		return false
	}
	return true
}

// CreateRoomSetup creates a new room setup
func (cm *ConfigurationManager) CreateRoomSetup(setup *RoomSetup) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if setup.ID == "" {
		setup.ID = fmt.Sprintf("setup_%d", time.Now().UnixNano())
	}

	setup.CreatedAt = time.Now()
	setup.UpdatedAt = time.Now()

	if setup.IsActive {
		cm.roomSetups[setup.ID] = setup
		cm.metrics.ActiveRoomSetups++
	} else {
		cm.setupTemplates[setup.ID] = setup
		cm.metrics.TemplateRoomSetups++
	}

	cm.metrics.TotalRoomSetups++

	logger.Info("Room setup created: %s", setup.ID)
	return nil
}

// GetRoomSetup returns a specific room setup
func (cm *ConfigurationManager) GetRoomSetup(setupID string) (*RoomSetup, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	// Check active setups first
	if setup, exists := cm.roomSetups[setupID]; exists {
		return setup, nil
	}

	// Check templates
	if setup, exists := cm.setupTemplates[setupID]; exists {
		return setup, nil
	}

	return nil, fmt.Errorf("room setup not found: %s", setupID)
}

// UpdateRoomSetup updates an existing room setup
func (cm *ConfigurationManager) UpdateRoomSetup(setupID string, setup *RoomSetup) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	setup.ID = setupID
	setup.UpdatedAt = time.Now()

	// Check if it's active
	if setup.IsActive {
		if _, exists := cm.roomSetups[setupID]; !exists {
			return fmt.Errorf("active room setup not found: %s", setupID)
		}
		cm.roomSetups[setupID] = setup
	} else {
		if _, exists := cm.setupTemplates[setupID]; !exists {
			return fmt.Errorf("room setup template not found: %s", setupID)
		}
		cm.setupTemplates[setupID] = setup
	}

	logger.Info("Room setup updated: %s", setupID)
	return nil
}

// DeleteRoomSetup deletes a room setup
func (cm *ConfigurationManager) DeleteRoomSetup(setupID string) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Check active setups first
	if _, exists := cm.roomSetups[setupID]; exists {
		delete(cm.roomSetups, setupID)
		cm.metrics.ActiveRoomSetups--
		cm.metrics.TotalRoomSetups--
		logger.Info("Room setup deleted: %s", setupID)
		return nil
	}

	// Check templates
	if _, exists := cm.setupTemplates[setupID]; exists {
		delete(cm.setupTemplates, setupID)
		cm.metrics.TemplateRoomSetups--
		cm.metrics.TotalRoomSetups--
		logger.Info("Room setup template deleted: %s", setupID)
		return nil
	}

	return fmt.Errorf("room setup not found: %s", setupID)
}

// GetRoomSetups returns all room setups with optional filtering
func (cm *ConfigurationManager) GetRoomSetups(filter SetupFilter) []*RoomSetup {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var setups []*RoomSetup

	// Add active setups
	for _, setup := range cm.roomSetups {
		if cm.matchesSetupFilter(setup, filter) {
			setups = append(setups, setup)
		}
	}

	// Add templates if requested
	if filter.IncludeTemplates {
		for _, setup := range cm.setupTemplates {
			if cm.matchesSetupFilter(setup, filter) {
				setups = append(setups, setup)
			}
		}
	}

	return setups
}

// SetupFilter represents filtering criteria for room setups
type SetupFilter struct {
	SetupType        SetupType `json:"setup_type,omitempty"`
	IsActive         *bool     `json:"is_active,omitempty"`
	CreatedBy        string    `json:"created_by,omitempty"`
	IncludeTemplates bool      `json:"include_templates"`
	Building         string    `json:"building,omitempty"`
	Room             string    `json:"room,omitempty"`
}

// matchesSetupFilter checks if a room setup matches the filter criteria
func (cm *ConfigurationManager) matchesSetupFilter(setup *RoomSetup, filter SetupFilter) bool {
	if filter.SetupType != "" && setup.SetupType != filter.SetupType {
		return false
	}
	if filter.IsActive != nil && setup.IsActive != *filter.IsActive {
		return false
	}
	if filter.CreatedBy != "" && setup.CreatedBy != filter.CreatedBy {
		return false
	}
	if filter.Building != "" && setup.Room.Building != filter.Building {
		return false
	}
	if filter.Room != "" && setup.Room.Room != filter.Room {
		return false
	}
	return true
}

// CloneConfiguration creates a copy of a configuration
func (cm *ConfigurationManager) CloneConfiguration(sourceConfigID string, newName string, createdBy string) (*Configuration, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	// Get source configuration
	sourceConfig, err := cm.GetConfiguration(sourceConfigID)
	if err != nil {
		return nil, err
	}

	// Create clone
	clone := &Configuration{
		Name:         newName,
		Description:  sourceConfig.Description + " (Clone)",
		AssetType:    sourceConfig.AssetType,
		Components:   make([]Component, len(sourceConfig.Components)),
		Software:     make([]Software, len(sourceConfig.Software)),
		UserSettings: make(map[string]interface{}),
		IsTemplate:   false,
		CreatedBy:    createdBy,
	}

	// Deep copy components
	copy(clone.Components, sourceConfig.Components)

	// Deep copy software
	copy(clone.Software, sourceConfig.Software)

	// Deep copy user settings
	for k, v := range sourceConfig.UserSettings {
		clone.UserSettings[k] = v
	}

	// Copy network settings if present
	if sourceConfig.NetworkSettings != nil {
		clone.NetworkSettings = &NetworkSettings{
			IPAddress:  sourceConfig.NetworkSettings.IPAddress,
			SubnetMask: sourceConfig.NetworkSettings.SubnetMask,
			Gateway:    sourceConfig.NetworkSettings.Gateway,
			DNS:        make([]string, len(sourceConfig.NetworkSettings.DNS)),
			VLAN:       sourceConfig.NetworkSettings.VLAN,
		}
		copy(clone.NetworkSettings.DNS, sourceConfig.NetworkSettings.DNS)

		// Copy wireless settings if present
		if sourceConfig.NetworkSettings.Wireless != nil {
			clone.NetworkSettings.Wireless = &WirelessSettings{
				SSID:           sourceConfig.NetworkSettings.Wireless.SSID,
				Security:       sourceConfig.NetworkSettings.Wireless.Security,
				Encryption:     sourceConfig.NetworkSettings.Wireless.Encryption,
				Password:       sourceConfig.NetworkSettings.Wireless.Password,
				Frequency:      sourceConfig.NetworkSettings.Wireless.Frequency,
				Channel:        sourceConfig.NetworkSettings.Wireless.Channel,
				SignalStrength: sourceConfig.NetworkSettings.Wireless.SignalStrength,
			}
		}

		// Copy ports
		clone.NetworkSettings.Ports = make([]PortConfig, len(sourceConfig.NetworkSettings.Ports))
		copy(clone.NetworkSettings.Ports, sourceConfig.NetworkSettings.Ports)

		// Copy firewall rules
		clone.NetworkSettings.FirewallRules = make([]FirewallRule, len(sourceConfig.NetworkSettings.FirewallRules))
		copy(clone.NetworkSettings.FirewallRules, sourceConfig.NetworkSettings.FirewallRules)
	}

	// Create the clone
	err = cm.CreateConfiguration(clone)
	if err != nil {
		return nil, err
	}

	logger.Info("Configuration cloned: %s -> %s", sourceConfigID, clone.ID)
	return clone, nil
}

// CloneRoomSetup creates a copy of a room setup
func (cm *ConfigurationManager) CloneRoomSetup(sourceSetupID string, newName string, newLocation Location, createdBy string) (*RoomSetup, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	// Get source setup
	sourceSetup, err := cm.GetRoomSetup(sourceSetupID)
	if err != nil {
		return nil, err
	}

	// Create clone
	clone := &RoomSetup{
		Name:            newName,
		Description:     sourceSetup.Description + " (Clone)",
		Room:            newLocation,
		SetupType:       sourceSetup.SetupType,
		Assets:          make([]RoomAsset, len(sourceSetup.Assets)),
		Connections:     make([]Connection, len(sourceSetup.Connections)),
		UserPreferences: make(map[string]interface{}),
		IsActive:        false, // Clone starts as inactive
		CreatedBy:       createdBy,
	}

	// Deep copy assets
	copy(clone.Assets, sourceSetup.Assets)

	// Deep copy connections
	copy(clone.Connections, sourceSetup.Connections)

	// Deep copy user preferences
	for k, v := range sourceSetup.UserPreferences {
		clone.UserPreferences[k] = v
	}

	// Create the clone
	err = cm.CreateRoomSetup(clone)
	if err != nil {
		return nil, err
	}

	logger.Info("Room setup cloned: %s -> %s", sourceSetupID, clone.ID)
	return clone, nil
}

// GetConfigurationTemplates returns all configuration templates
func (cm *ConfigurationManager) GetConfigurationTemplates() []*Configuration {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var templates []*Configuration
	for _, template := range cm.templates {
		templates = append(templates, template)
	}
	return templates
}

// GetRoomSetupTemplates returns all room setup templates
func (cm *ConfigurationManager) GetRoomSetupTemplates() []*RoomSetup {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var templates []*RoomSetup
	for _, template := range cm.setupTemplates {
		templates = append(templates, template)
	}
	return templates
}

// GetMetrics returns configuration management metrics
func (cm *ConfigurationManager) GetMetrics() *ConfigurationMetrics {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	return cm.metrics
}

// UpdateMetrics updates the configuration metrics
func (cm *ConfigurationManager) UpdateMetrics() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// Count configurations
	cm.metrics.TotalConfigurations = int64(len(cm.configurations) + len(cm.templates))
	cm.metrics.ActiveConfigurations = int64(len(cm.configurations))
	cm.metrics.TemplateConfigurations = int64(len(cm.templates))

	// Count room setups
	cm.metrics.TotalRoomSetups = int64(len(cm.roomSetups) + len(cm.setupTemplates))
	cm.metrics.ActiveRoomSetups = int64(len(cm.roomSetups))
	cm.metrics.TemplateRoomSetups = int64(len(cm.setupTemplates))

	// Calculate configuration health (simplified)
	cm.metrics.ConfigurationHealth = cm.calculateConfigurationHealth()

	// Calculate setup compliance (simplified)
	cm.metrics.SetupCompliance = cm.calculateSetupCompliance()

	logger.Debug("Configuration metrics updated")
}

// calculateConfigurationHealth calculates the health of configurations
func (cm *ConfigurationManager) calculateConfigurationHealth() float64 {
	if len(cm.configurations) == 0 {
		return 1.0
	}

	// Simplified health calculation
	// In a real implementation, this would check for:
	// - Missing required components
	// - Outdated software versions
	// - Configuration conflicts
	// - Security issues

	healthyConfigs := 0
	for range cm.configurations {
		// For now, assume all configs are healthy
		// This would be replaced with actual health checks
		healthyConfigs++
	}

	return float64(healthyConfigs) / float64(len(cm.configurations))
}

// calculateSetupCompliance calculates the compliance of room setups
func (cm *ConfigurationManager) calculateSetupCompliance() float64 {
	if len(cm.roomSetups) == 0 {
		return 1.0
	}

	// Simplified compliance calculation
	// In a real implementation, this would check for:
	// - Required assets present
	// - Proper connections
	// - Security compliance
	// - Accessibility compliance

	compliantSetups := 0
	for range cm.roomSetups {
		// For now, assume all setups are compliant
		// This would be replaced with actual compliance checks
		compliantSetups++
	}

	return float64(compliantSetups) / float64(len(cm.roomSetups))
}

// GetConfigurationByAssetType returns configurations for a specific asset type
func (cm *ConfigurationManager) GetConfigurationByAssetType(assetType AssetType) []*Configuration {
	filter := ConfigFilter{
		AssetType:        assetType,
		IncludeTemplates: true,
	}
	return cm.GetConfigurations(filter)
}

// GetRoomSetupByType returns room setups for a specific setup type
func (cm *ConfigurationManager) GetRoomSetupByType(setupType SetupType) []*RoomSetup {
	filter := SetupFilter{
		SetupType:        setupType,
		IncludeTemplates: true,
	}
	return cm.GetRoomSetups(filter)
}

// GetRoomSetupByLocation returns room setups for a specific location
func (cm *ConfigurationManager) GetRoomSetupByLocation(building, room string) []*RoomSetup {
	filter := SetupFilter{
		Building:         building,
		Room:             room,
		IncludeTemplates: false, // Only active setups
	}
	return cm.GetRoomSetups(filter)
}
