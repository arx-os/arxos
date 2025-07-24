package notifications

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arxos/arx-backend/models"
	"gorm.io/gorm"
)

// EnhancedNotificationService provides enterprise-grade notification capabilities
type EnhancedNotificationService struct {
	db             *gorm.DB
	emailService   *EmailService
	slackService   *SlackService
	smsService     *SMSService
	webhookService *WebhookService
	unifiedService *UnifiedNotificationService
	config         *EnhancedNotificationConfig
	queue          *NotificationQueue
	statistics     *EnhancedNotificationStatistics
	mu             sync.RWMutex
	ctx            context.Context
	cancel         context.CancelFunc
}

// EnhancedNotificationConfig holds enhanced notification service configuration
type EnhancedNotificationConfig struct {
	DefaultChannels       []models.NotificationChannelType
	PriorityMapping       map[models.NotificationPriority][]models.NotificationChannelType
	RetryConfig           EnhancedRetryConfig
	RateLimit             int
	Timeout               time.Duration
	BatchSize             int
	QueueWorkers          int
	EnableAuditLogging    bool
	EnableStatistics      bool
	EnableUserPreferences bool
	TemplatePath          string
	MaxRetentionDays      int
}

// EnhancedRetryConfig holds enhanced retry configuration
type EnhancedRetryConfig struct {
	MaxRetries        int
	RetryDelay        time.Duration
	BackoffMultiplier float64
	MaxRetryDelay     time.Duration
	Jitter            bool
}

// EnhancedNotificationStatistics holds enhanced notification statistics
type EnhancedNotificationStatistics struct {
	TotalNotifications       int64
	SuccessfulNotifications  int64
	FailedNotifications      int64
	RateLimitedNotifications int64
	ChannelStats             map[models.NotificationChannelType]*EnhancedChannelStatistics
	PriorityStats            map[models.NotificationPriority]*EnhancedPriorityStatistics
	TypeStats                map[models.NotificationType]*EnhancedTypeStatistics
	UserStats                map[uint]*EnhancedUserStatistics
	LastUpdated              time.Time
	mu                       sync.RWMutex
}

// EnhancedChannelStatistics holds enhanced statistics for a specific channel
type EnhancedChannelStatistics struct {
	TotalSent         int64
	Successful        int64
	Failed            int64
	RateLimited       int64
	AverageTime       float64
	SuccessRate       float64
	TotalCost         float64
	LastSent          time.Time
	ErrorBreakdown    map[string]int64
	PerformanceTrends []PerformancePoint
}

// EnhancedPriorityStatistics holds enhanced statistics for a specific priority
type EnhancedPriorityStatistics struct {
	TotalSent        int64
	Successful       int64
	Failed           int64
	AverageTime      float64
	SuccessRate      float64
	LastSent         time.Time
	ChannelBreakdown map[models.NotificationChannelType]int64
}

// EnhancedTypeStatistics holds enhanced statistics for a specific notification type
type EnhancedTypeStatistics struct {
	TotalSent         int64
	Successful        int64
	Failed            int64
	AverageTime       float64
	SuccessRate       float64
	LastSent          time.Time
	PriorityBreakdown map[models.NotificationPriority]int64
}

// EnhancedUserStatistics holds enhanced statistics for a specific user
type EnhancedUserStatistics struct {
	TotalSent        int64
	Successful       int64
	Failed           int64
	AverageTime      float64
	SuccessRate      float64
	LastSent         time.Time
	ChannelBreakdown map[models.NotificationChannelType]int64
	TypeBreakdown    map[models.NotificationType]int64
}

// PerformancePoint represents a performance data point
type PerformancePoint struct {
	Timestamp time.Time
	Value     float64
	Metric    string
}

// NotificationQueue manages notification processing queue
type NotificationQueue struct {
	queue   chan *models.NotificationEnhanced
	workers int
	ctx     context.Context
	cancel  context.CancelFunc
	service *EnhancedNotificationService
	mu      sync.RWMutex
}

// NewEnhancedNotificationService creates a new enhanced notification service
func NewEnhancedNotificationService(
	db *gorm.DB,
	emailService *EmailService,
	slackService *SlackService,
	smsService *SMSService,
	webhookService *WebhookService,
	unifiedService *UnifiedNotificationService,
	config *EnhancedNotificationConfig,
) (*EnhancedNotificationService, error) {
	if db == nil {
		return nil, fmt.Errorf("database connection is required")
	}

	if config == nil {
		config = &EnhancedNotificationConfig{
			DefaultChannels: []models.NotificationChannelType{
				models.NotificationChannelTypeEmail,
				models.NotificationChannelTypeSlack,
			},
			PriorityMapping: map[models.NotificationPriority][]models.NotificationChannelType{
				models.NotificationPriorityLow:    {models.NotificationChannelTypeEmail},
				models.NotificationPriorityNormal: {models.NotificationChannelTypeEmail, models.NotificationChannelTypeSlack},
				models.NotificationPriorityHigh:   {models.NotificationChannelTypeEmail, models.NotificationChannelTypeSlack, models.NotificationChannelTypeSMS},
				models.NotificationPriorityUrgent: {models.NotificationChannelTypeEmail, models.NotificationChannelTypeSlack, models.NotificationChannelTypeSMS, models.NotificationChannelTypeWebhook},
			},
			RetryConfig: EnhancedRetryConfig{
				MaxRetries:        3,
				RetryDelay:        5 * time.Second,
				BackoffMultiplier: 2.0,
				MaxRetryDelay:     60 * time.Second,
				Jitter:            true,
			},
			RateLimit:             100,
			Timeout:               30 * time.Second,
			BatchSize:             50,
			QueueWorkers:          5,
			EnableAuditLogging:    true,
			EnableStatistics:      true,
			EnableUserPreferences: true,
			TemplatePath:          "./templates",
			MaxRetentionDays:      90,
		}
	}

	ctx, cancel := context.WithCancel(context.Background())

	service := &EnhancedNotificationService{
		db:             db,
		emailService:   emailService,
		slackService:   slackService,
		smsService:     smsService,
		webhookService: webhookService,
		unifiedService: unifiedService,
		config:         config,
		statistics: &EnhancedNotificationStatistics{
			ChannelStats:  make(map[models.NotificationChannelType]*EnhancedChannelStatistics),
			PriorityStats: make(map[models.NotificationPriority]*EnhancedPriorityStatistics),
			TypeStats:     make(map[models.NotificationType]*EnhancedTypeStatistics),
			UserStats:     make(map[uint]*EnhancedUserStatistics),
		},
		ctx:    ctx,
		cancel: cancel,
	}

	// Initialize queue
	service.queue = NewNotificationQueue(service, config.QueueWorkers, ctx)

	// Initialize statistics
	if err := service.initializeStatistics(); err != nil {
		return nil, fmt.Errorf("failed to initialize statistics: %w", err)
	}

	// Start background workers
	go service.startBackgroundWorkers()

	return service, nil
}

// CreateNotification creates a new notification using enhanced models
func (ens *EnhancedNotificationService) CreateNotification(
	title, message string,
	notificationType models.NotificationType,
	channels []models.NotificationChannelType,
	priority models.NotificationPriority,
	recipientID uint,
	senderID *uint,
	configID *uint,
	templateID *uint,
	templateData map[string]interface{},
	metadata map[string]interface{},
) (*models.NotificationEnhanced, error) {
	// Validate inputs
	if title == "" || message == "" {
		return nil, fmt.Errorf("title and message are required")
	}

	if !notificationType.IsValid() {
		return nil, fmt.Errorf("invalid notification type: %s", notificationType)
	}

	if !priority.IsValid() {
		return nil, fmt.Errorf("invalid priority: %s", priority)
	}

	// Validate channels
	for _, channel := range channels {
		if !channel.IsValid() {
			return nil, fmt.Errorf("invalid channel: %s", channel)
		}
	}

	// Check user preferences if enabled
	if ens.config.EnableUserPreferences {
		filteredChannels, err := ens.filterChannelsByUserPreferences(recipientID, channels, notificationType)
		if err != nil {
			return nil, fmt.Errorf("failed to filter channels by user preferences: %w", err)
		}
		channels = filteredChannels
	}

	// Create notification
	notification := &models.NotificationEnhanced{
		Title:       title,
		Message:     message,
		Type:        notificationType,
		Priority:    priority,
		Status:      models.NotificationStatusPending,
		RecipientID: recipientID,
		SenderID:    senderID,
		ConfigID:    configID,
		TemplateID:  templateID,
		RetryCount:  0,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Set channels
	if err := notification.SetChannels(channels); err != nil {
		return nil, fmt.Errorf("failed to set channels: %w", err)
	}

	// Set template data
	if templateData != nil {
		if err := notification.SetTemplateData(templateData); err != nil {
			return nil, fmt.Errorf("failed to set template data: %w", err)
		}
	}

	// Set metadata
	if metadata != nil {
		if err := notification.SetMetadata(metadata); err != nil {
			return nil, fmt.Errorf("failed to set metadata: %w", err)
		}
	}

	// Save to database
	if err := ens.db.Create(notification).Error; err != nil {
		return nil, fmt.Errorf("failed to create notification: %w", err)
	}

	// Log audit event if enabled
	if ens.config.EnableAuditLogging {
		if err := ens.logAuditEvent(notification, "created"); err != nil {
			// Log error but don't fail the operation
			fmt.Printf("Failed to log audit event: %v\n", err)
		}
	}

	// Update statistics
	if ens.config.EnableStatistics {
		ens.updateStatistics(notification, "created")
	}

	return notification, nil
}

// SendNotification sends a notification through all configured channels
func (ens *EnhancedNotificationService) SendNotification(notification *models.NotificationEnhanced) error {
	if notification == nil {
		return fmt.Errorf("notification is required")
	}

	// Update status to sending
	notification.Status = models.NotificationStatusSending
	notification.UpdatedAt = time.Now()

	if err := ens.db.Save(notification).Error; err != nil {
		return fmt.Errorf("failed to update notification status: %w", err)
	}

	// Get channels
	channels := notification.GetChannels()
	if len(channels) == 0 {
		channels = ens.config.DefaultChannels
	}

	// Send to each channel
	var deliveryResults []*models.NotificationDeliveryEnhanced
	for _, channel := range channels {
		delivery, err := ens.sendToChannel(notification, channel)
		if err != nil {
			// Log error but continue with other channels
			fmt.Printf("Failed to send to channel %s: %v\n", channel, err)
			continue
		}
		deliveryResults = append(deliveryResults, delivery)
	}

	// Update notification status based on results
	ens.updateNotificationStatus(notification, deliveryResults)

	// Save updated notification
	if err := ens.db.Save(notification).Error; err != nil {
		return fmt.Errorf("failed to save notification: %w", err)
	}

	// Log audit event if enabled
	if ens.config.EnableAuditLogging {
		if err := ens.logAuditEvent(notification, "sent"); err != nil {
			fmt.Printf("Failed to log audit event: %v\n", err)
		}
	}

	// Update statistics
	if ens.config.EnableStatistics {
		ens.updateStatistics(notification, "sent")
	}

	return nil
}

// sendToChannel sends notification to a specific channel
func (ens *EnhancedNotificationService) sendToChannel(
	notification *models.NotificationEnhanced,
	channel models.NotificationChannelType,
) (*models.NotificationDeliveryEnhanced, error) {
	// Create delivery record
	delivery := &models.NotificationDeliveryEnhanced{
		NotificationID: notification.ID,
		Channel:        channel,
		Status:         models.NotificationStatusPending,
		AttemptNumber:  1,
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}

	// Save delivery record
	if err := ens.db.Create(delivery).Error; err != nil {
		return nil, fmt.Errorf("failed to create delivery record: %w", err)
	}

	// Send based on channel type
	var err error
	switch channel {
	case models.NotificationChannelTypeEmail:
		err = ens.sendEmail(notification, delivery)
	case models.NotificationChannelTypeSlack:
		err = ens.sendSlack(notification, delivery)
	case models.NotificationChannelTypeSMS:
		err = ens.sendSMS(notification, delivery)
	case models.NotificationChannelTypeWebhook:
		err = ens.sendWebhook(notification, delivery)
	case models.NotificationChannelTypePush:
		err = ens.sendPush(notification, delivery)
	case models.NotificationChannelTypeInApp:
		err = ens.sendInApp(notification, delivery)
	default:
		err = fmt.Errorf("unsupported channel: %s", channel)
	}

	// Update delivery status
	if err != nil {
		delivery.Status = models.NotificationStatusFailed
		delivery.ErrorMessage = err.Error()
		delivery.FailedAt = &time.Time{}
		*delivery.FailedAt = time.Now()
	} else {
		delivery.Status = models.NotificationStatusDelivered
		delivery.DeliveredAt = &time.Now()
	}

	delivery.UpdatedAt = time.Now()

	// Save delivery record
	if err := ens.db.Save(delivery).Error; err != nil {
		return nil, fmt.Errorf("failed to save delivery record: %w", err)
	}

	return delivery, nil
}

// sendEmail sends notification via email
func (ens *EnhancedNotificationService) sendEmail(
	notification *models.NotificationEnhanced,
	delivery *models.NotificationDeliveryEnhanced,
) error {
	if ens.emailService == nil {
		return fmt.Errorf("email service not configured")
	}

	// Get email configuration
	config, err := ens.getEmailConfig(notification.ConfigID)
	if err != nil {
		return fmt.Errorf("failed to get email config: %w", err)
	}

	// Create email message
	message := &EmailMessage{
		To:         []string{}, // Will be populated from recipient
		Subject:    notification.Title,
		Body:       notification.Message,
		Priority:   string(notification.Priority),
		TemplateID: "", // Will be populated if template is used
	}

	// Add template data if available
	if notification.TemplateData != nil {
		templateData := notification.GetTemplateData()
		if templateData != nil {
			message.TemplateData = templateData
		}
	}

	// Send email
	result := ens.emailService.SendEmail(message)
	if !result.Success {
		return fmt.Errorf("email send failed: %v", result.Error)
	}

	// Update delivery with external ID
	delivery.ExternalID = result.MessageID
	delivery.SentAt = &result.SentAt

	return nil
}

// sendSlack sends notification via Slack
func (ens *EnhancedNotificationService) sendSlack(
	notification *models.NotificationEnhanced,
	delivery *models.NotificationDeliveryEnhanced,
) error {
	if ens.slackService == nil {
		return fmt.Errorf("slack service not configured")
	}

	// Create Slack message
	message := &SlackMessage{
		Text: notification.Message,
	}

	// Add priority color
	message.Attachments = []SlackAttachment{
		{
			Color: ens.getPriorityColor(notification.Priority),
			Title: notification.Title,
			Text:  notification.Message,
		},
	}

	// Send Slack message
	result := ens.slackService.SendMessage(message)
	if !result.Success {
		return fmt.Errorf("slack send failed: %v", result.Error)
	}

	// Update delivery with external ID
	delivery.ExternalID = result.MessageID
	delivery.SentAt = &result.SentAt

	return nil
}

// sendSMS sends notification via SMS
func (ens *EnhancedNotificationService) sendSMS(
	notification *models.NotificationEnhanced,
	delivery *models.NotificationDeliveryEnhanced,
) error {
	if ens.smsService == nil {
		return fmt.Errorf("SMS service not configured")
	}

	// Create SMS message
	message := &SMSMessage{
		To:   "", // Will be populated from recipient
		Body: notification.Message,
	}

	// Send SMS
	result := ens.smsService.SendSMS(message)
	if !result.Success {
		return fmt.Errorf("SMS send failed: %v", result.Error)
	}

	// Update delivery with external ID
	delivery.ExternalID = result.MessageID
	delivery.SentAt = &result.SentAt

	return nil
}

// sendWebhook sends notification via webhook
func (ens *EnhancedNotificationService) sendWebhook(
	notification *models.NotificationEnhanced,
	delivery *models.NotificationDeliveryEnhanced,
) error {
	if ens.webhookService == nil {
		return fmt.Errorf("webhook service not configured")
	}

	// Create webhook payload
	payload := map[string]interface{}{
		"title":     notification.Title,
		"message":   notification.Message,
		"type":      string(notification.Type),
		"priority":  string(notification.Priority),
		"timestamp": time.Now().Unix(),
	}

	// Add metadata if available
	if notification.Metadata != nil {
		metadata := notification.GetMetadata()
		if metadata != nil {
			payload["metadata"] = metadata
		}
	}

	// Create webhook request
	request := &WebhookNotificationRequest{
		URL:     "", // Will be populated from config
		Payload: payload,
		Method:  "POST",
	}

	// Send webhook
	result := ens.webhookService.SendWebhook(request)
	if !result.Success {
		return fmt.Errorf("webhook send failed: %v", result.Error)
	}

	// Update delivery with external ID
	delivery.ExternalID = result.MessageID
	delivery.SentAt = &result.SentAt

	return nil
}

// sendPush sends notification via push notification
func (ens *EnhancedNotificationService) sendPush(
	notification *models.NotificationEnhanced,
	delivery *models.NotificationDeliveryEnhanced,
) error {
	// TODO: Implement push notification service
	return fmt.Errorf("push notifications not yet implemented")
}

// sendInApp sends notification via in-app notification
func (ens *EnhancedNotificationService) sendInApp(
	notification *models.NotificationEnhanced,
	delivery *models.NotificationDeliveryEnhanced,
) error {
	// TODO: Implement in-app notification service
	return fmt.Errorf("in-app notifications not yet implemented")
}

// Helper methods

// filterChannelsByUserPreferences filters channels based on user preferences
func (ens *EnhancedNotificationService) filterChannelsByUserPreferences(
	userID uint,
	channels []models.NotificationChannelType,
	notificationType models.NotificationType,
) ([]models.NotificationChannelType, error) {
	var preferences []models.NotificationPreference
	if err := ens.db.Where("user_id = ? AND type = ? AND is_enabled = ?", userID, notificationType, true).Find(&preferences).Error; err != nil {
		return nil, fmt.Errorf("failed to get user preferences: %w", err)
	}

	// If no preferences found, return all channels
	if len(preferences) == 0 {
		return channels, nil
	}

	// Filter channels based on preferences
	enabledChannels := make(map[models.NotificationChannelType]bool)
	for _, pref := range preferences {
		enabledChannels[pref.Channel] = true
	}

	var filteredChannels []models.NotificationChannelType
	for _, channel := range channels {
		if enabledChannels[channel] {
			filteredChannels = append(filteredChannels, channel)
		}
	}

	return filteredChannels, nil
}

// getEmailConfig retrieves email configuration
func (ens *EnhancedNotificationService) getEmailConfig(configID *uint) (*models.NotificationConfigEnhanced, error) {
	if configID == nil {
		return nil, fmt.Errorf("no email config ID provided")
	}

	var config models.NotificationConfigEnhanced
	if err := ens.db.First(&config, *configID).Error; err != nil {
		return nil, fmt.Errorf("failed to get email config: %w", err)
	}

	return &config, nil
}

// getPriorityColor returns color for priority
func (ens *EnhancedNotificationService) getPriorityColor(priority models.NotificationPriority) string {
	switch priority {
	case models.NotificationPriorityLow:
		return "#36a64f" // Green
	case models.NotificationPriorityNormal:
		return "#3b82f6" // Blue
	case models.NotificationPriorityHigh:
		return "#f59e0b" // Orange
	case models.NotificationPriorityUrgent:
		return "#ef4444" // Red
	default:
		return "#6b7280" // Gray
	}
}

// updateNotificationStatus updates notification status based on delivery results
func (ens *EnhancedNotificationService) updateNotificationStatus(
	notification *models.NotificationEnhanced,
	deliveries []*models.NotificationDeliveryEnhanced,
) {
	if len(deliveries) == 0 {
		notification.Status = models.NotificationStatusFailed
		return
	}

	// Check if any delivery was successful
	hasSuccess := false
	hasFailure := false

	for _, delivery := range deliveries {
		switch delivery.Status {
		case models.NotificationStatusDelivered:
			hasSuccess = true
		case models.NotificationStatusFailed:
			hasFailure = true
		}
	}

	// Update status
	if hasSuccess && !hasFailure {
		notification.Status = models.NotificationStatusDelivered
	} else if hasSuccess && hasFailure {
		notification.Status = models.NotificationStatusSent
	} else {
		notification.Status = models.NotificationStatusFailed
	}
}

// logAuditEvent logs audit event
func (ens *EnhancedNotificationService) logAuditEvent(
	notification *models.NotificationEnhanced,
	action string,
) error {
	auditLog := &models.NotificationLog{
		NotificationID: notification.ID,
		Action:         action,
		Status:         notification.Status,
		Message:        fmt.Sprintf("Notification %s: %s", action, notification.Title),
		CreatedAt:      time.Now(),
	}

	return ens.db.Create(auditLog).Error
}

// updateStatistics updates notification statistics
func (ens *EnhancedNotificationService) updateStatistics(
	notification *models.NotificationEnhanced,
	action string,
) {
	ens.statistics.mu.Lock()
	defer ens.statistics.mu.Unlock()

	// Update total counts
	switch action {
	case "created":
		ens.statistics.TotalNotifications++
	case "sent":
		// Statistics updated in delivery methods
	}

	ens.statistics.LastUpdated = time.Now()
}

// initializeStatistics initializes notification statistics
func (ens *EnhancedNotificationService) initializeStatistics() error {
	// Load existing statistics from database
	var stats []models.NotificationStats
	if err := ens.db.Find(&stats).Error; err != nil {
		return fmt.Errorf("failed to load statistics: %w", err)
	}

	// Initialize statistics from database
	for _, stat := range stats {
		// Initialize channel statistics
		if ens.statistics.ChannelStats[stat.Channel] == nil {
			ens.statistics.ChannelStats[stat.Channel] = &EnhancedChannelStatistics{}
		}

		channelStat := ens.statistics.ChannelStats[stat.Channel]
		channelStat.TotalSent = int64(stat.TotalSent)
		channelStat.Successful = int64(stat.TotalDelivered)
		channelStat.Failed = int64(stat.TotalFailed)
		channelStat.RateLimited = int64(stat.TotalRateLimited)
		channelStat.AverageTime = stat.AvgDeliveryTime
		channelStat.SuccessRate = stat.SuccessRate
		channelStat.LastSent = stat.Date
	}

	return nil
}

// startBackgroundWorkers starts background workers for notification processing
func (ens *EnhancedNotificationService) startBackgroundWorkers() {
	// Start queue workers
	go ens.queue.Start()

	// Start statistics updater
	go ens.updateStatisticsPeriodically()

	// Start cleanup worker
	go ens.cleanupOldNotifications()
}

// updateStatisticsPeriodically updates statistics periodically
func (ens *EnhancedNotificationService) updateStatisticsPeriodically() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ens.ctx.Done():
			return
		case <-ticker.C:
			if err := ens.updateStatisticsFromDatabase(); err != nil {
				fmt.Printf("Failed to update statistics: %v\n", err)
			}
		}
	}
}

// updateStatisticsFromDatabase updates statistics from database
func (ens *EnhancedNotificationService) updateStatisticsFromDatabase() error {
	// Update channel statistics
	var channelStats []models.NotificationStats
	if err := ens.db.Where("date >= ?", time.Now().AddDate(0, 0, -7)).Find(&channelStats).Error; err != nil {
		return fmt.Errorf("failed to get channel statistics: %w", err)
	}

	ens.statistics.mu.Lock()
	defer ens.statistics.mu.Unlock()

	for _, stat := range channelStats {
		if ens.statistics.ChannelStats[stat.Channel] == nil {
			ens.statistics.ChannelStats[stat.Channel] = &EnhancedChannelStatistics{}
		}

		channelStat := ens.statistics.ChannelStats[stat.Channel]
		channelStat.TotalSent = int64(stat.TotalSent)
		channelStat.Successful = int64(stat.TotalDelivered)
		channelStat.Failed = int64(stat.TotalFailed)
		channelStat.RateLimited = int64(stat.TotalRateLimited)
		channelStat.AverageTime = stat.AvgDeliveryTime
		channelStat.SuccessRate = stat.SuccessRate
		channelStat.LastSent = stat.Date
	}

	return nil
}

// cleanupOldNotifications cleans up old notifications based on retention policy
func (ens *EnhancedNotificationService) cleanupOldNotifications() {
	ticker := time.NewTicker(24 * time.Hour)
	defer ticker.Stop()

	for {
		select {
		case <-ens.ctx.Done():
			return
		case <-ticker.C:
			if err := ens.performCleanup(); err != nil {
				fmt.Printf("Failed to cleanup old notifications: %v\n", err)
			}
		}
	}
}

// performCleanup performs cleanup of old notifications
func (ens *EnhancedNotificationService) performCleanup() error {
	retentionDate := time.Now().AddDate(0, 0, -ens.config.MaxRetentionDays)

	// Delete old notifications
	if err := ens.db.Where("created_at < ?", retentionDate).Delete(&models.NotificationEnhanced{}).Error; err != nil {
		return fmt.Errorf("failed to cleanup notifications: %w", err)
	}

	// Delete old delivery records
	if err := ens.db.Where("created_at < ?", retentionDate).Delete(&models.NotificationDeliveryEnhanced{}).Error; err != nil {
		return fmt.Errorf("failed to cleanup delivery records: %w", err)
	}

	// Delete old logs
	if err := ens.db.Where("created_at < ?", retentionDate).Delete(&models.NotificationLog{}).Error; err != nil {
		return fmt.Errorf("failed to cleanup logs: %w", err)
	}

	return nil
}

// GetStatistics returns enhanced notification statistics
func (ens *EnhancedNotificationService) GetStatistics() *EnhancedNotificationStatistics {
	ens.statistics.mu.RLock()
	defer ens.statistics.mu.RUnlock()

	// Create a copy to avoid race conditions
	stats := &EnhancedNotificationStatistics{
		TotalNotifications:       ens.statistics.TotalNotifications,
		SuccessfulNotifications:  ens.statistics.SuccessfulNotifications,
		FailedNotifications:      ens.statistics.FailedNotifications,
		RateLimitedNotifications: ens.statistics.RateLimitedNotifications,
		LastUpdated:              ens.statistics.LastUpdated,
		ChannelStats:             make(map[models.NotificationChannelType]*EnhancedChannelStatistics),
		PriorityStats:            make(map[models.NotificationPriority]*EnhancedPriorityStatistics),
		TypeStats:                make(map[models.NotificationType]*EnhancedTypeStatistics),
		UserStats:                make(map[uint]*EnhancedUserStatistics),
	}

	// Copy channel statistics
	for channel, stat := range ens.statistics.ChannelStats {
		stats.ChannelStats[channel] = &EnhancedChannelStatistics{
			TotalSent:   stat.TotalSent,
			Successful:  stat.Successful,
			Failed:      stat.Failed,
			RateLimited: stat.RateLimited,
			AverageTime: stat.AverageTime,
			SuccessRate: stat.SuccessRate,
			TotalCost:   stat.TotalCost,
			LastSent:    stat.LastSent,
		}
	}

	return stats
}

// Shutdown gracefully shuts down the enhanced notification service
func (ens *EnhancedNotificationService) Shutdown() error {
	// Cancel context to stop background workers
	ens.cancel()

	// Wait for background workers to finish
	time.Sleep(2 * time.Second)

	// Save final statistics
	if err := ens.saveStatistics(); err != nil {
		return fmt.Errorf("failed to save final statistics: %w", err)
	}

	return nil
}

// saveStatistics saves statistics to database
func (ens *EnhancedNotificationService) saveStatistics() error {
	stats := ens.GetStatistics()

	// Save channel statistics
	for channel, stat := range stats.ChannelStats {
		notificationStat := &models.NotificationStats{
			Date:             time.Now(),
			Channel:          channel,
			Type:             models.NotificationTypeSystem, // Default type
			TotalSent:        int(stat.TotalSent),
			TotalDelivered:   int(stat.Successful),
			TotalFailed:      int(stat.Failed),
			TotalRateLimited: int(stat.RateLimited),
			AvgDeliveryTime:  stat.AverageTime,
			SuccessRate:      stat.SuccessRate,
			CreatedAt:        time.Now(),
			UpdatedAt:        time.Now(),
		}

		if err := ens.db.Create(notificationStat).Error; err != nil {
			return fmt.Errorf("failed to save channel statistics: %w", err)
		}
	}

	return nil
}
