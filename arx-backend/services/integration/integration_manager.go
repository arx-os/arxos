package integration

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// IntegrationType represents the type of integration
type IntegrationType string

const (
	IntegrationTypeSystem     IntegrationType = "system"
	IntegrationTypeEnterprise IntegrationType = "enterprise"
)

// IntegrationStatus represents the status of an integration
type IntegrationStatus string

const (
	IntegrationStatusActive      IntegrationStatus = "active"
	IntegrationStatusInactive    IntegrationStatus = "inactive"
	IntegrationStatusError       IntegrationStatus = "error"
	IntegrationStatusMaintenance IntegrationStatus = "maintenance"
)

// ManagerIntegrationConfig represents a unified integration configuration
type ManagerIntegrationConfig struct {
	ID            string            `json:"id" gorm:"primaryKey"`
	Name          string            `json:"name"`
	Type          IntegrationType   `json:"type"`
	Status        IntegrationStatus `json:"status"`
	SystemID      *string           `json:"system_id"`
	EnterpriseID  *string           `json:"enterprise_id"`
	Description   *string           `json:"description"`
	Configuration json.RawMessage   `json:"configuration"`
	Schedule      *string           `json:"schedule"`
	LastSync      *time.Time        `json:"last_sync"`
	NextSync      *time.Time        `json:"next_sync"`
	CreatedAt     time.Time         `json:"created_at"`
	UpdatedAt     time.Time         `json:"updated_at"`
}

// IntegrationEvent represents an integration event
type IntegrationEvent struct {
	ID            string          `json:"id" gorm:"primaryKey"`
	IntegrationID string          `json:"integration_id"`
	EventType     string          `json:"event_type"`
	EventData     json.RawMessage `json:"event_data"`
	Status        string          `json:"status"`
	ErrorMessage  *string         `json:"error_message"`
	Timestamp     time.Time       `json:"timestamp"`
}

// IntegrationMetrics represents integration performance metrics
type IntegrationMetrics struct {
	ID                     string     `json:"id" gorm:"primaryKey"`
	IntegrationID          string     `json:"integration_id"`
	TotalSyncs             int        `json:"total_syncs"`
	SuccessfulSyncs        int        `json:"successful_syncs"`
	FailedSyncs            int        `json:"failed_syncs"`
	AverageSyncDuration    float64    `json:"average_sync_duration"`
	LastSyncDuration       float64    `json:"last_sync_duration"`
	TotalRecordsProcessed  int        `json:"total_records_processed"`
	TotalRecordsSuccessful int        `json:"total_records_successful"`
	TotalRecordsFailed     int        `json:"total_records_failed"`
	LastSyncTimestamp      *time.Time `json:"last_sync_timestamp"`
	CreatedAt              time.Time  `json:"created_at"`
	UpdatedAt              time.Time  `json:"updated_at"`
}

// IntegrationManager manages all integration services
type IntegrationManager struct {
	db                    *gorm.DB
	mu                    sync.RWMutex
	systemIntegration     *SystemIntegration
	enterpriseIntegration *EnterpriseIntegration
	configs               map[string]*ManagerIntegrationConfig
	metrics               map[string]*IntegrationMetrics
	config                *ManagerConfig
}

// ManagerConfig holds configuration for the integration manager
type ManagerConfig struct {
	EnableAutoSync       bool          `json:"enable_auto_sync"`
	AutoSyncInterval     time.Duration `json:"auto_sync_interval"`
	EnableMonitoring     bool          `json:"enable_monitoring"`
	MonitoringInterval   time.Duration `json:"monitoring_interval"`
	EnableEventLogging   bool          `json:"enable_event_logging"`
	MaxRetryAttempts     int           `json:"max_retry_attempts"`
	RetryDelay           time.Duration `json:"retry_delay"`
	EnableMetrics        bool          `json:"enable_metrics"`
	MetricsRetentionDays int           `json:"metrics_retention_days"`
}

// NewIntegrationManager creates a new integration manager
func NewIntegrationManager(db *gorm.DB, systemIntegration *SystemIntegration, enterpriseIntegration *EnterpriseIntegration, config *ManagerConfig) *IntegrationManager {
	if config == nil {
		config = &ManagerConfig{
			EnableAutoSync:       true,
			AutoSyncInterval:     15 * time.Minute,
			EnableMonitoring:     true,
			MonitoringInterval:   5 * time.Minute,
			EnableEventLogging:   true,
			MaxRetryAttempts:     3,
			RetryDelay:           30 * time.Second,
			EnableMetrics:        true,
			MetricsRetentionDays: 90,
		}
	}

	return &IntegrationManager{
		db:                    db,
		systemIntegration:     systemIntegration,
		enterpriseIntegration: enterpriseIntegration,
		configs:               make(map[string]*ManagerIntegrationConfig),
		metrics:               make(map[string]*IntegrationMetrics),
		config:                config,
	}
}

// CreateIntegrationConfig creates a new integration configuration
func (im *IntegrationManager) CreateIntegrationConfig(ctx context.Context, config *ManagerIntegrationConfig) error {
	if err := im.validateIntegrationConfig(config); err != nil {
		return fmt.Errorf("invalid integration config: %w", err)
	}

	config.ID = generateManagerID()
	config.Status = IntegrationStatusInactive
	config.CreatedAt = time.Now()
	config.UpdatedAt = time.Now()

	if err := im.db.WithContext(ctx).Create(config).Error; err != nil {
		return fmt.Errorf("failed to create integration config: %w", err)
	}

	im.mu.Lock()
	im.configs[config.ID] = config
	im.mu.Unlock()

	return nil
}

// GetIntegrationConfig retrieves an integration configuration by ID
func (im *IntegrationManager) GetIntegrationConfig(ctx context.Context, id string) (*ManagerIntegrationConfig, error) {
	var config ManagerIntegrationConfig
	if err := im.db.WithContext(ctx).Where("id = ?", id).First(&config).Error; err != nil {
		return nil, fmt.Errorf("integration config not found: %w", err)
	}
	return &config, nil
}

// UpdateIntegrationConfig updates an integration configuration
func (im *IntegrationManager) UpdateIntegrationConfig(ctx context.Context, id string, updates map[string]interface{}) error {
	updates["updated_at"] = time.Now()

	if err := im.db.WithContext(ctx).Model(&IntegrationConfig{}).Where("id = ?", id).Updates(updates).Error; err != nil {
		return fmt.Errorf("failed to update integration config: %w", err)
	}

	// Update local cache
	im.mu.Lock()
	if config, exists := im.configs[id]; exists {
		config.UpdatedAt = time.Now()
	}
	im.mu.Unlock()

	return nil
}

// ListIntegrationConfigs retrieves all integration configurations
func (im *IntegrationManager) ListIntegrationConfigs(ctx context.Context, status *IntegrationStatus) ([]ManagerIntegrationConfig, error) {
	var configs []ManagerIntegrationConfig
	query := im.db.WithContext(ctx)

	if status != nil {
		query = query.Where("status = ?", *status)
	}

	if err := query.Order("created_at DESC").Find(&configs).Error; err != nil {
		return nil, fmt.Errorf("failed to list integration configs: %w", err)
	}

	return configs, nil
}

// ActivateIntegration activates an integration
func (im *IntegrationManager) ActivateIntegration(ctx context.Context, id string) error {
	config, err := im.GetIntegrationConfig(ctx, id)
	if err != nil {
		return err
	}

	// Test the integration before activating
	if err := im.testIntegration(config); err != nil {
		return fmt.Errorf("integration test failed: %w", err)
	}

	updates := map[string]interface{}{
		"status":     IntegrationStatusActive,
		"updated_at": time.Now(),
	}

	return im.UpdateIntegrationConfig(ctx, id, updates)
}

// DeactivateIntegration deactivates an integration
func (im *IntegrationManager) DeactivateIntegration(ctx context.Context, id string) error {
	updates := map[string]interface{}{
		"status":     IntegrationStatusInactive,
		"updated_at": time.Now(),
	}

	return im.UpdateIntegrationConfig(ctx, id, updates)
}

// SyncIntegration performs a manual sync for an integration
func (im *IntegrationManager) SyncIntegration(ctx context.Context, id string, direction SyncDirection, data []map[string]interface{}) (*map[string]interface{}, error) {
	config, err := im.GetIntegrationConfig(ctx, id)
	if err != nil {
		return nil, err
	}

	if config.Status != IntegrationStatusActive {
		return nil, fmt.Errorf("integration is not active")
	}

	startTime := time.Now()
	var result *map[string]interface{}
	var err2 error

	switch config.Type {
	case IntegrationTypeSystem:
		if config.SystemID == nil {
			return nil, fmt.Errorf("system_id not configured")
		}
		syncResult, err := im.systemIntegration.SyncData(ctx, *config.SystemID, direction, data, ConflictResolutionTimestampBased)
		if err != nil {
			err2 = err
		} else {
			result = &map[string]interface{}{
				"sync_result": syncResult,
				"duration":    time.Since(startTime).Seconds(),
			}
		}

	case IntegrationTypeEnterprise:
		if config.EnterpriseID == nil {
			return nil, fmt.Errorf("enterprise_id not configured")
		}
		syncResult, err := im.enterpriseIntegration.SyncEnterpriseData(ctx, *config.EnterpriseID, direction, data, ConflictResolutionTimestampBased)
		if err != nil {
			err2 = err
		} else {
			result = &map[string]interface{}{
				"sync_result": syncResult,
				"duration":    time.Since(startTime).Seconds(),
			}
		}

	default:
		return nil, fmt.Errorf("unsupported integration type: %s", config.Type)
	}

	// Update last sync time
	now := time.Now()
	updates := map[string]interface{}{
		"last_sync":  &now,
		"updated_at": now,
	}
	im.UpdateIntegrationConfig(ctx, id, updates)

	// Log integration event
	im.logIntegrationEvent(ctx, id, "manual_sync", map[string]interface{}{
		"direction": direction,
		"records":   len(data),
		"duration":  time.Since(startTime).Seconds(),
		"success":   err2 == nil,
		"error":     err2,
	})

	// Update metrics
	im.updateIntegrationMetrics(ctx, id, len(data), err2 == nil, time.Since(startTime).Seconds())

	return result, err2
}

// GetIntegrationStatus gets the status of an integration
func (im *IntegrationManager) GetIntegrationStatus(ctx context.Context, id string) (*map[string]interface{}, error) {
	config, err := im.GetIntegrationConfig(ctx, id)
	if err != nil {
		return nil, err
	}

	status := map[string]interface{}{
		"id":         config.ID,
		"name":       config.Name,
		"type":       config.Type,
		"status":     config.Status,
		"last_sync":  config.LastSync,
		"next_sync":  config.NextSync,
		"updated_at": config.UpdatedAt,
	}

	// Get specific integration status
	switch config.Type {
	case IntegrationTypeSystem:
		if config.SystemID != nil {
			if systemStatus, err := im.systemIntegration.GetConnectionStatus(ctx, *config.SystemID); err == nil {
				status["system_status"] = systemStatus
			}
		}

	case IntegrationTypeEnterprise:
		if config.EnterpriseID != nil {
			if enterpriseStatus, err := im.enterpriseIntegration.GetEnterpriseConnectionStatus(ctx, *config.EnterpriseID); err == nil {
				status["enterprise_status"] = enterpriseStatus
			}
		}
	}

	// Get metrics
	if metrics, err := im.getIntegrationMetrics(ctx, id); err == nil {
		status["metrics"] = metrics
	}

	return &status, nil
}

// GetIntegrationMetrics gets metrics for an integration
func (im *IntegrationManager) GetIntegrationMetrics(ctx context.Context, id string) (*IntegrationMetrics, error) {
	return im.getIntegrationMetrics(ctx, id)
}

// GetAllIntegrationMetrics gets metrics for all integrations
func (im *IntegrationManager) GetAllIntegrationMetrics(ctx context.Context) ([]IntegrationMetrics, error) {
	var metrics []IntegrationMetrics
	if err := im.db.WithContext(ctx).Find(&metrics).Error; err != nil {
		return nil, fmt.Errorf("failed to get integration metrics: %w", err)
	}
	return metrics, nil
}

// GetIntegrationEvents gets events for an integration
func (im *IntegrationManager) GetIntegrationEvents(ctx context.Context, id string, limit int) ([]IntegrationEvent, error) {
	var events []IntegrationEvent
	if err := im.db.WithContext(ctx).Where("integration_id = ?", id).Order("timestamp DESC").Limit(limit).Find(&events).Error; err != nil {
		return nil, fmt.Errorf("failed to get integration events: %w", err)
	}
	return events, nil
}

// validateIntegrationConfig validates integration configuration
func (im *IntegrationManager) validateIntegrationConfig(config *ManagerIntegrationConfig) error {
	if config.Name == "" {
		return fmt.Errorf("name is required")
	}
	if config.Type == "" {
		return fmt.Errorf("type is required")
	}

	switch config.Type {
	case IntegrationTypeSystem:
		if config.SystemID == nil || *config.SystemID == "" {
			return fmt.Errorf("system_id is required for system integration")
		}
	case IntegrationTypeEnterprise:
		if config.EnterpriseID == nil || *config.EnterpriseID == "" {
			return fmt.Errorf("enterprise_id is required for enterprise integration")
		}
	default:
		return fmt.Errorf("unsupported integration type: %s", config.Type)
	}

	return nil
}

// testIntegration tests an integration
func (im *IntegrationManager) testIntegration(config *ManagerIntegrationConfig) error {
	switch config.Type {
	case IntegrationTypeSystem:
		if config.SystemID == nil {
			return fmt.Errorf("system_id not configured")
		}
		_, err := im.systemIntegration.TestConnection(context.Background(), *config.SystemID)
		return err

	case IntegrationTypeEnterprise:
		if config.EnterpriseID == nil {
			return fmt.Errorf("enterprise_id not configured")
		}
		_, err := im.enterpriseIntegration.TestEnterpriseConnection(context.Background(), *config.EnterpriseID)
		return err

	default:
		return fmt.Errorf("unsupported integration type: %s", config.Type)
	}
}

// logIntegrationEvent logs an integration event
func (im *IntegrationManager) logIntegrationEvent(ctx context.Context, integrationID string, eventType string, eventData map[string]interface{}) {
	if !im.config.EnableEventLogging {
		return
	}

	data, _ := json.Marshal(eventData)
	event := &IntegrationEvent{
		ID:            generateManagerID(),
		IntegrationID: integrationID,
		EventType:     eventType,
		EventData:     data,
		Status:        "logged",
		Timestamp:     time.Now(),
	}

	im.db.WithContext(ctx).Create(event)
}

// updateIntegrationMetrics updates integration metrics
func (im *IntegrationManager) updateIntegrationMetrics(ctx context.Context, integrationID string, recordsProcessed int, success bool, duration float64) {
	if !im.config.EnableMetrics {
		return
	}

	var metrics IntegrationMetrics
	err := im.db.WithContext(ctx).Where("integration_id = ?", integrationID).First(&metrics).Error

	if err != nil {
		// Create new metrics record
		metrics = IntegrationMetrics{
			ID:                     generateManagerID(),
			IntegrationID:          integrationID,
			TotalSyncs:             0,
			SuccessfulSyncs:        0,
			FailedSyncs:            0,
			AverageSyncDuration:    0,
			TotalRecordsProcessed:  0,
			TotalRecordsSuccessful: 0,
			TotalRecordsFailed:     0,
			CreatedAt:              time.Now(),
			UpdatedAt:              time.Now(),
		}
	}

	// Update metrics
	metrics.TotalSyncs++
	if success {
		metrics.SuccessfulSyncs++
		metrics.TotalRecordsSuccessful += recordsProcessed
	} else {
		metrics.FailedSyncs++
		metrics.TotalRecordsFailed += recordsProcessed
	}

	metrics.TotalRecordsProcessed += recordsProcessed
	metrics.LastSyncDuration = duration
	metrics.AverageSyncDuration = (metrics.AverageSyncDuration*float64(metrics.TotalSyncs-1) + duration) / float64(metrics.TotalSyncs)
	metrics.LastSyncTimestamp = &time.Time{}
	*metrics.LastSyncTimestamp = time.Now()
	metrics.UpdatedAt = time.Now()

	if err != nil {
		im.db.WithContext(ctx).Create(&metrics)
	} else {
		im.db.WithContext(ctx).Save(&metrics)
	}
}

// getIntegrationMetrics gets metrics for an integration
func (im *IntegrationManager) getIntegrationMetrics(ctx context.Context, id string) (*IntegrationMetrics, error) {
	var metrics IntegrationMetrics
	if err := im.db.WithContext(ctx).Where("integration_id = ?", id).First(&metrics).Error; err != nil {
		return nil, fmt.Errorf("metrics not found: %w", err)
	}
	return &metrics, nil
}

// generateManagerID generates a unique ID for manager entities
func generateManagerID() string {
	return fmt.Sprintf("mgr_%d", time.Now().UnixNano())
}
