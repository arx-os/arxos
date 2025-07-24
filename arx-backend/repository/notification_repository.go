package repository

import (
	"time"

	"arx/models"

	"gorm.io/gorm"
)

// NotificationRepository handles database operations for notifications
type NotificationRepository struct {
	db *gorm.DB
}

// NewNotificationRepository creates a new notification repository
func NewNotificationRepository(db *gorm.DB) *NotificationRepository {
	return &NotificationRepository{
		db: db,
	}
}

// Notification CRUD Operations

// CreateNotification creates a new notification
func (r *NotificationRepository) CreateNotification(notification *models.NotificationEnhanced) error {
	return r.db.Create(notification).Error
}

// GetNotificationByID retrieves a notification by ID
func (r *NotificationRepository) GetNotificationByID(id uint) (*models.NotificationEnhanced, error) {
	var notification models.NotificationEnhanced
	err := r.db.Preload("Config").Preload("Template").Preload("Recipient").Preload("Sender").Preload("Building").Preload("Deliveries").
		First(&notification, id).Error
	if err != nil {
		return nil, err
	}
	return &notification, nil
}

// GetNotifications retrieves notifications with filtering and pagination
func (r *NotificationRepository) GetNotifications(filters map[string]interface{}, page, pageSize int) ([]models.NotificationEnhanced, int64, error) {
	var notifications []models.NotificationEnhanced
	var total int64

	query := r.db.Model(&models.NotificationEnhanced{})

	// Apply filters
	for key, value := range filters {
		if value != nil {
			query = query.Where(key+" = ?", value)
		}
	}

	// Get total count
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// Apply pagination
	offset := (page - 1) * pageSize
	err := query.Preload("Config").Preload("Template").Preload("Recipient").Preload("Sender").Preload("Building").Preload("Deliveries").
		Offset(offset).Limit(pageSize).Order("created_at DESC").Find(&notifications).Error

	return notifications, total, err
}

// UpdateNotification updates a notification
func (r *NotificationRepository) UpdateNotification(notification *models.NotificationEnhanced) error {
	return r.db.Save(notification).Error
}

// DeleteNotification deletes a notification
func (r *NotificationRepository) DeleteNotification(id uint) error {
	return r.db.Delete(&models.NotificationEnhanced{}, id).Error
}

// Notification Delivery Operations

// CreateDelivery creates a new notification delivery record
func (r *NotificationRepository) CreateDelivery(delivery *models.NotificationDeliveryEnhanced) error {
	return r.db.Create(delivery).Error
}

// GetDeliveryByID retrieves a delivery by ID
func (r *NotificationRepository) GetDeliveryByID(id uint) (*models.NotificationDeliveryEnhanced, error) {
	var delivery models.NotificationDeliveryEnhanced
	err := r.db.Preload("Notification").First(&delivery, id).Error
	if err != nil {
		return nil, err
	}
	return &delivery, nil
}

// GetDeliveriesByNotificationID retrieves all deliveries for a notification
func (r *NotificationRepository) GetDeliveriesByNotificationID(notificationID uint) ([]models.NotificationDeliveryEnhanced, error) {
	var deliveries []models.NotificationDeliveryEnhanced
	err := r.db.Where("notification_id = ?", notificationID).Find(&deliveries).Error
	return deliveries, err
}

// UpdateDelivery updates a delivery record
func (r *NotificationRepository) UpdateDelivery(delivery *models.NotificationDeliveryEnhanced) error {
	return r.db.Save(delivery).Error
}

// GetFailedDeliveries retrieves failed deliveries for retry
func (r *NotificationRepository) GetFailedDeliveries(limit int) ([]models.NotificationDeliveryEnhanced, error) {
	var deliveries []models.NotificationDeliveryEnhanced
	err := r.db.Where("status = ?", models.NotificationStatusFailed).
		Preload("Notification").
		Limit(limit).
		Find(&deliveries).Error
	return deliveries, err
}

// Template Management Operations

// CreateTemplate creates a new notification template
func (r *NotificationRepository) CreateTemplate(template *models.NotificationTemplateEnhanced) error {
	return r.db.Create(template).Error
}

// GetTemplateByID retrieves a template by ID
func (r *NotificationRepository) GetTemplateByID(id uint) (*models.NotificationTemplateEnhanced, error) {
	var template models.NotificationTemplateEnhanced
	err := r.db.Preload("User").First(&template, id).Error
	if err != nil {
		return nil, err
	}
	return &template, nil
}

// GetTemplates retrieves templates with filtering and pagination
func (r *NotificationRepository) GetTemplates(filters map[string]interface{}, page, pageSize int) ([]models.NotificationTemplateEnhanced, int64, error) {
	var templates []models.NotificationTemplateEnhanced
	var total int64

	query := r.db.Model(&models.NotificationTemplateEnhanced{})

	// Apply filters
	for key, value := range filters {
		if value != nil {
			query = query.Where(key+" = ?", value)
		}
	}

	// Get total count
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// Apply pagination
	offset := (page - 1) * pageSize
	err := query.Preload("User").Offset(offset).Limit(pageSize).Order("created_at DESC").Find(&templates).Error

	return templates, total, err
}

// UpdateTemplate updates a template
func (r *NotificationRepository) UpdateTemplate(template *models.NotificationTemplateEnhanced) error {
	return r.db.Save(template).Error
}

// DeleteTemplate deletes a template
func (r *NotificationRepository) DeleteTemplate(id uint) error {
	return r.db.Delete(&models.NotificationTemplateEnhanced{}, id).Error
}

// GetActiveTemplates retrieves active templates by type
func (r *NotificationRepository) GetActiveTemplates(notificationType models.NotificationType) ([]models.NotificationTemplateEnhanced, error) {
	var templates []models.NotificationTemplateEnhanced
	err := r.db.Where("type = ? AND is_active = ?", notificationType, true).Find(&templates).Error
	return templates, err
}

// Configuration Management Operations

// CreateConfig creates a new notification configuration
func (r *NotificationRepository) CreateConfig(config *models.NotificationConfigEnhanced) error {
	return r.db.Create(config).Error
}

// GetConfigByID retrieves a configuration by ID
func (r *NotificationRepository) GetConfigByID(id uint) (*models.NotificationConfigEnhanced, error) {
	var config models.NotificationConfigEnhanced
	err := r.db.Preload("Template").First(&config, id).Error
	if err != nil {
		return nil, err
	}
	return &config, nil
}

// GetConfigs retrieves configurations with filtering and pagination
func (r *NotificationRepository) GetConfigs(filters map[string]interface{}, page, pageSize int) ([]models.NotificationConfigEnhanced, int64, error) {
	var configs []models.NotificationConfigEnhanced
	var total int64

	query := r.db.Model(&models.NotificationConfigEnhanced{})

	// Apply filters
	for key, value := range filters {
		if value != nil {
			query = query.Where(key+" = ?", value)
		}
	}

	// Get total count
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// Apply pagination
	offset := (page - 1) * pageSize
	err := query.Preload("Template").Offset(offset).Limit(pageSize).Order("created_at DESC").Find(&configs).Error

	return configs, total, err
}

// UpdateConfig updates a configuration
func (r *NotificationRepository) UpdateConfig(config *models.NotificationConfigEnhanced) error {
	return r.db.Save(config).Error
}

// DeleteConfig deletes a configuration
func (r *NotificationRepository) DeleteConfig(id uint) error {
	return r.db.Delete(&models.NotificationConfigEnhanced{}, id).Error
}

// GetActiveConfigs retrieves active configurations
func (r *NotificationRepository) GetActiveConfigs() ([]models.NotificationConfigEnhanced, error) {
	var configs []models.NotificationConfigEnhanced
	err := r.db.Where("is_active = ?", true).Preload("Template").Find(&configs).Error
	return configs, err
}

// User Preference Operations

// CreatePreference creates a new user notification preference
func (r *NotificationRepository) CreatePreference(preference *models.NotificationPreference) error {
	return r.db.Create(preference).Error
}

// GetPreferenceByID retrieves a preference by ID
func (r *NotificationRepository) GetPreferenceByID(id uint) (*models.NotificationPreference, error) {
	var preference models.NotificationPreference
	err := r.db.Preload("User").First(&preference, id).Error
	if err != nil {
		return nil, err
	}
	return &preference, nil
}

// GetUserPreferences retrieves all preferences for a user
func (r *NotificationRepository) GetUserPreferences(userID uint) ([]models.NotificationPreference, error) {
	var preferences []models.NotificationPreference
	err := r.db.Where("user_id = ?", userID).Preload("User").Find(&preferences).Error
	return preferences, err
}

// GetUserPreference retrieves a specific preference for a user
func (r *NotificationRepository) GetUserPreference(userID uint, channel models.NotificationChannelType, notificationType models.NotificationType) (*models.NotificationPreference, error) {
	var preference models.NotificationPreference
	err := r.db.Where("user_id = ? AND channel = ? AND type = ?", userID, channel, notificationType).
		Preload("User").First(&preference).Error
	if err != nil {
		return nil, err
	}
	return &preference, nil
}

// UpdatePreference updates a user preference
func (r *NotificationRepository) UpdatePreference(preference *models.NotificationPreference) error {
	return r.db.Save(preference).Error
}

// DeletePreference deletes a user preference
func (r *NotificationRepository) DeletePreference(id uint) error {
	return r.db.Delete(&models.NotificationPreference{}, id).Error
}

// Channel Configuration Operations

// CreateChannelConfig creates a new channel configuration
func (r *NotificationRepository) CreateChannelConfig(config *models.NotificationChannelConfig) error {
	return r.db.Create(config).Error
}

// GetChannelConfig retrieves a channel configuration
func (r *NotificationRepository) GetChannelConfig(channel models.NotificationChannelType) (*models.NotificationChannelConfig, error) {
	var config models.NotificationChannelConfig
	err := r.db.Where("channel = ?", channel).First(&config).Error
	if err != nil {
		return nil, err
	}
	return &config, nil
}

// GetChannelConfigs retrieves all channel configurations
func (r *NotificationRepository) GetChannelConfigs() ([]models.NotificationChannelConfig, error) {
	var configs []models.NotificationChannelConfig
	err := r.db.Find(&configs).Error
	return configs, err
}

// UpdateChannelConfig updates a channel configuration
func (r *NotificationRepository) UpdateChannelConfig(config *models.NotificationChannelConfig) error {
	return r.db.Save(config).Error
}

// DeleteChannelConfig deletes a channel configuration
func (r *NotificationRepository) DeleteChannelConfig(channel models.NotificationChannelType) error {
	return r.db.Where("channel = ?", channel).Delete(&models.NotificationChannelConfig{}).Error
}

// Statistics and Analytics Operations

// CreateStats creates a new statistics record
func (r *NotificationRepository) CreateStats(stats *models.NotificationStats) error {
	return r.db.Create(stats).Error
}

// GetStats retrieves statistics for a specific date and channel
func (r *NotificationRepository) GetStats(date time.Time, channel models.NotificationChannelType, notificationType models.NotificationType) (*models.NotificationStats, error) {
	var stats models.NotificationStats
	err := r.db.Where("date = ? AND channel = ? AND type = ?", date, channel, notificationType).First(&stats).Error
	if err != nil {
		return nil, err
	}
	return &stats, nil
}

// GetStatsByDateRange retrieves statistics for a date range
func (r *NotificationRepository) GetStatsByDateRange(startDate, endDate time.Time, channel models.NotificationChannelType) ([]models.NotificationStats, error) {
	var stats []models.NotificationStats
	err := r.db.Where("date BETWEEN ? AND ? AND channel = ?", startDate, endDate, channel).Find(&stats).Error
	return stats, err
}

// UpdateStats updates statistics
func (r *NotificationRepository) UpdateStats(stats *models.NotificationStats) error {
	return r.db.Save(stats).Error
}

// GetDeliveryStatistics retrieves delivery statistics
func (r *NotificationRepository) GetDeliveryStatistics(days int) (map[string]interface{}, error) {
	var stats []struct {
		Channel     string  `json:"channel"`
		TotalSent   int     `json:"total_sent"`
		Delivered   int     `json:"delivered"`
		Failed      int     `json:"failed"`
		SuccessRate float64 `json:"success_rate"`
	}

	query := `
		SELECT 
			channel,
			COUNT(*) as total_sent,
			SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
			SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
			(SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as success_rate
		FROM notification_deliveries 
		WHERE created_at >= NOW() - INTERVAL '? days'
		GROUP BY channel
	`

	err := r.db.Raw(query, days).Scan(&stats).Error
	if err != nil {
		return nil, err
	}

	result := make(map[string]interface{})
	result["statistics"] = stats
	result["period_days"] = days
	result["generated_at"] = time.Now()

	return result, nil
}

// Queue Operations

// CreateQueueItem creates a new queue item
func (r *NotificationRepository) CreateQueueItem(queueItem *models.NotificationQueue) error {
	return r.db.Create(queueItem).Error
}

// GetQueueItems retrieves queued items for processing
func (r *NotificationRepository) GetQueueItems(limit int) ([]models.NotificationQueue, error) {
	var items []models.NotificationQueue
	err := r.db.Where("status = ? AND scheduled_at <= ?", "queued", time.Now()).
		Preload("Notification").
		Order("priority DESC, scheduled_at ASC").
		Limit(limit).
		Find(&items).Error
	return items, err
}

// UpdateQueueItem updates a queue item
func (r *NotificationRepository) UpdateQueueItem(item *models.NotificationQueue) error {
	return r.db.Save(item).Error
}

// DeleteQueueItem deletes a queue item
func (r *NotificationRepository) DeleteQueueItem(id uint) error {
	return r.db.Delete(&models.NotificationQueue{}, id).Error
}

// GetQueueStatistics retrieves queue statistics
func (r *NotificationRepository) GetQueueStatistics() (map[string]interface{}, error) {
	var stats struct {
		Queued     int64 `json:"queued"`
		Processing int64 `json:"processing"`
		Completed  int64 `json:"completed"`
		Failed     int64 `json:"failed"`
	}

	err := r.db.Model(&models.NotificationQueue{}).
		Select("COUNT(CASE WHEN status = 'queued' THEN 1 END) as queued, " +
			"COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing, " +
			"COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed, " +
			"COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed").
		Scan(&stats).Error

	if err != nil {
		return nil, err
	}

	result := make(map[string]interface{})
	result["queue_stats"] = stats
	result["generated_at"] = time.Now()

	return result, nil
}

// Logging Operations

// CreateLog creates a new notification log entry
func (r *NotificationRepository) CreateLog(log *models.NotificationLog) error {
	return r.db.Create(log).Error
}

// GetLogs retrieves logs for a notification
func (r *NotificationRepository) GetLogs(notificationID uint, limit int) ([]models.NotificationLog, error) {
	var logs []models.NotificationLog
	err := r.db.Where("notification_id = ?", notificationID).
		Preload("Notification").Preload("Delivery").
		Order("created_at DESC").
		Limit(limit).
		Find(&logs).Error
	return logs, err
}

// GetLogsByAction retrieves logs by action type
func (r *NotificationRepository) GetLogsByAction(action string, limit int) ([]models.NotificationLog, error) {
	var logs []models.NotificationLog
	err := r.db.Where("action = ?", action).
		Preload("Notification").Preload("Delivery").
		Order("created_at DESC").
		Limit(limit).
		Find(&logs).Error
	return logs, err
}

// Maintenance Notification Integration

// UpdateMaintenanceNotificationDelivery updates delivery tracking for maintenance notifications
func (r *NotificationRepository) UpdateMaintenanceNotificationDelivery(maintenanceNotification *models.MaintenanceNotification) error {
	return r.db.Save(maintenanceNotification).Error
}

// GetMaintenanceNotificationsWithDelivery retrieves maintenance notifications with delivery tracking
func (r *NotificationRepository) GetMaintenanceNotificationsWithDelivery(assetID int, limit int) ([]models.MaintenanceNotification, error) {
	var notifications []models.MaintenanceNotification
	err := r.db.Where("asset_id = ?", assetID).
		Preload("Notification").
		Order("created_at DESC").
		Limit(limit).
		Find(&notifications).Error
	return notifications, err
}

// Utility Operations

// CleanupOldNotifications removes old notification records
func (r *NotificationRepository) CleanupOldNotifications(daysToKeep int) error {
	cutoffDate := time.Now().AddDate(0, 0, -daysToKeep)
	return r.db.Where("created_at < ?", cutoffDate).Delete(&models.NotificationEnhanced{}).Error
}

// CleanupOldLogs removes old log records
func (r *NotificationRepository) CleanupOldLogs(daysToKeep int) error {
	cutoffDate := time.Now().AddDate(0, 0, -daysToKeep)
	return r.db.Where("created_at < ?", cutoffDate).Delete(&models.NotificationLog{}).Error
}

// GetNotificationCount retrieves notification count by status
func (r *NotificationRepository) GetNotificationCount(status models.NotificationStatus) (int64, error) {
	var count int64
	err := r.db.Model(&models.NotificationEnhanced{}).Where("status = ?", status).Count(&count).Error
	return count, err
}

// GetDeliveryCount retrieves delivery count by status
func (r *NotificationRepository) GetDeliveryCount(status models.NotificationStatus) (int64, error) {
	var count int64
	err := r.db.Model(&models.NotificationDeliveryEnhanced{}).Where("status = ?", status).Count(&count).Error
	return count, err
}

// GetUserNotificationCount retrieves notification count for a user
func (r *NotificationRepository) GetUserNotificationCount(userID uint, status models.NotificationStatus) (int64, error) {
	var count int64
	err := r.db.Model(&models.NotificationEnhanced{}).
		Where("recipient_id = ? AND status = ?", userID, status).
		Count(&count).Error
	return count, err
}

// GetNotificationSummary retrieves a summary of notifications
func (r *NotificationRepository) GetNotificationSummary(days int) (map[string]interface{}, error) {
	var summary struct {
		TotalNotifications int64 `json:"total_notifications"`
		PendingCount       int64 `json:"pending_count"`
		SentCount          int64 `json:"sent_count"`
		DeliveredCount     int64 `json:"delivered_count"`
		FailedCount        int64 `json:"failed_count"`
	}

	query := `
		SELECT 
			COUNT(*) as total_notifications,
			SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
			SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent_count,
			SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_count,
			SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
		FROM notifications 
		WHERE created_at >= NOW() - INTERVAL '? days'
	`

	err := r.db.Raw(query, days).Scan(&summary).Error
	if err != nil {
		return nil, err
	}

	result := make(map[string]interface{})
	result["summary"] = summary
	result["period_days"] = days
	result["generated_at"] = time.Now()

	return result, nil
}

// Transaction Support

// WithTransaction executes operations within a database transaction
func (r *NotificationRepository) WithTransaction(fn func(*NotificationRepository) error) error {
	return r.db.Transaction(func(tx *gorm.DB) error {
		txRepo := &NotificationRepository{db: tx}
		return fn(txRepo)
	})
}

// Health Check

// HealthCheck performs a health check on the notification repository
func (r *NotificationRepository) HealthCheck() (map[string]interface{}, error) {
	var result = make(map[string]interface{})

	// Check if we can query the database
	var count int64
	err := r.db.Model(&models.NotificationEnhanced{}).Count(&count).Error
	if err != nil {
		result["status"] = "unhealthy"
		result["error"] = err.Error()
		return result, err
	}

	result["status"] = "healthy"
	result["notification_count"] = count
	result["checked_at"] = time.Now()

	return result, nil
}
