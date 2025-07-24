package notifications

import (
	"fmt"
	"sync"
	"time"
)

// UnifiedNotificationService handles all notification channels
type UnifiedNotificationService struct {
	emailService   *EmailService
	slackService   *SlackService
	smsService     *SMSService
	webhookService *WebhookService
	config         *UnifiedConfig
	statistics     *NotificationStatistics
	mu             sync.RWMutex
}

// UnifiedConfig holds unified notification service configuration
type UnifiedConfig struct {
	DefaultChannels []string
	PriorityMapping map[string][]string
	RetryConfig     RetryConfig
	RateLimit       int
	Timeout         time.Duration
}

// RetryConfig holds retry configuration
type RetryConfig struct {
	MaxRetries        int
	RetryDelay        time.Duration
	BackoffMultiplier float64
}

// UnifiedNotification represents a unified notification message
type UnifiedNotification struct {
	ID           string
	Title        string
	Message      string
	Channels     []string
	Priority     string
	TemplateID   string
	TemplateData map[string]interface{}
	CreatedAt    time.Time
	Status       string
	Results      map[string]*NotificationResult
}

// NotificationResult represents the result of a notification send operation
type NotificationResult struct {
	Success      bool
	Channel      string
	MessageID    string
	SentAt       time.Time
	DeliveredAt  *time.Time
	Error        error
	RetryCount   int
	DeliveryTime time.Duration
	Cost         float64
}

// NotificationStatistics holds notification delivery statistics
type NotificationStatistics struct {
	TotalSent    int
	Successful   int
	Failed       int
	ChannelStats map[string]*ChannelStatistics
	LastUpdated  time.Time
	mu           sync.RWMutex
}

// ChannelStatistics holds statistics for a specific channel
type ChannelStatistics struct {
	TotalSent   int
	Successful  int
	Failed      int
	AverageTime float64
	SuccessRate float64
	TotalCost   float64
	LastSent    time.Time
}

// NewUnifiedNotificationService creates a new unified notification service
func NewUnifiedNotificationService(
	emailService *EmailService,
	slackService *SMSService,
	smsService *SMSService,
	webhookService *WebhookService,
	config *UnifiedConfig,
) (*UnifiedNotificationService, error) {
	if emailService == nil || slackService == nil || smsService == nil || webhookService == nil {
		return nil, fmt.Errorf("all notification services must be provided")
	}

	service := &UnifiedNotificationService{
		emailService:   emailService,
		slackService:   slackService,
		smsService:     smsService,
		webhookService: webhookService,
		config:         config,
		statistics: &NotificationStatistics{
			ChannelStats: make(map[string]*ChannelStatistics),
		},
	}

	// Initialize channel statistics
	channels := []string{"email", "slack", "sms", "webhook"}
	for _, channel := range channels {
		service.statistics.ChannelStats[channel] = &ChannelStatistics{}
	}

	return service, nil
}

// SendNotification sends a notification to multiple channels
func (uns *UnifiedNotificationService) SendNotification(notification *UnifiedNotification) map[string]*NotificationResult {
	results := make(map[string]*NotificationResult)
	var wg sync.WaitGroup
	var mu sync.Mutex

	// Determine channels to use
	channels := notification.Channels
	if len(channels) == 0 {
		channels = uns.config.DefaultChannels
	}

	// Send to each channel concurrently
	for _, channel := range channels {
		wg.Add(1)
		go func(ch string) {
			defer wg.Done()
			result := uns.sendToChannel(notification, ch)

			mu.Lock()
			results[ch] = result
			uns.updateStatistics(ch, result)
			mu.Unlock()
		}(channel)
	}

	wg.Wait()

	// Update notification status
	uns.updateNotificationStatus(notification, results)

	return results
}

// sendToChannel sends a notification to a specific channel
func (uns *UnifiedNotificationService) sendToChannel(notification *UnifiedNotification, channel string) *NotificationResult {
	startTime := time.Now()
	result := &NotificationResult{
		Success:    false,
		Channel:    channel,
		MessageID:  generateUnifiedMessageID(),
		SentAt:     startTime,
		RetryCount: 0,
	}

	// Send with retry logic
	for attempt := 0; attempt <= uns.config.RetryConfig.MaxRetries; attempt++ {
		var err error

		switch channel {
		case "email":
			err = uns.sendEmail(notification, result)
		case "slack":
			err = uns.sendSlack(notification, result)
		case "sms":
			err = uns.sendSMS(notification, result)
		case "webhook":
			err = uns.sendWebhook(notification, result)
		default:
			err = fmt.Errorf("unknown channel: %s", channel)
		}

		if err != nil {
			result.RetryCount = attempt
			if attempt == uns.config.RetryConfig.MaxRetries {
				result.Error = fmt.Errorf("failed to send %s notification after %d attempts: %w", channel, uns.config.RetryConfig.MaxRetries, err)
				return result
			}

			// Exponential backoff
			delay := time.Duration(float64(uns.config.RetryConfig.RetryDelay) *
				uns.config.RetryConfig.BackoffMultiplier * float64(attempt+1))
			time.Sleep(delay)
			continue
		}

		result.Success = true
		result.DeliveryTime = time.Since(startTime)
		now := time.Now()
		result.DeliveredAt = &now
		break
	}

	return result
}

// sendEmail sends an email notification
func (uns *UnifiedNotificationService) sendEmail(notification *UnifiedNotification, result *NotificationResult) error {
	emailMessage := &EmailMessage{
		To:           uns.getEmailRecipients(notification),
		Subject:      notification.Title,
		Body:         notification.Message,
		Priority:     notification.Priority,
		TemplateID:   notification.TemplateID,
		TemplateData: notification.TemplateData,
	}

	emailResult := uns.emailService.SendEmail(emailMessage)
	if !emailResult.Success {
		return emailResult.Error
	}

	result.MessageID = emailResult.MessageID
	result.Cost = 0.0 // Email is typically free
	return nil
}

// sendSlack sends a Slack notification
func (uns *UnifiedNotificationService) sendSlack(notification *UnifiedNotification, result *NotificationResult) error {
	slackMessage := &SlackMessage{
		Channel: uns.getSlackChannel(notification),
		Text:    notification.Message,
		Attachments: []SlackAttachment{
			{
				Color: uns.getPriorityColor(notification.Priority),
				Text:  notification.Message,
				Title: notification.Title,
			},
		},
	}

	slackResult := uns.slackService.SendMessage(slackMessage)
	if !slackResult.Success {
		return slackResult.Error
	}

	result.MessageID = slackResult.MessageID
	result.Cost = 0.0 // Slack is free
	return nil
}

// sendSMS sends an SMS notification
func (uns *UnifiedNotificationService) sendSMS(notification *UnifiedNotification, result *NotificationResult) error {
	smsMessage := &SMSMessage{
		To:         uns.getSMSRecipients(notification),
		Body:       notification.Message,
		Priority:   notification.Priority,
		TemplateID: notification.TemplateID,
	}

	smsResult := uns.smsService.SendMessage(smsMessage)
	if !smsResult.Success {
		return smsResult.Error
	}

	result.MessageID = smsResult.MessageID
	result.Cost = smsResult.Cost
	return nil
}

// sendWebhook sends a webhook notification
func (uns *UnifiedNotificationService) sendWebhook(notification *UnifiedNotification, result *NotificationResult) error {
	webhookMessage := &WebhookMessage{
		URL:        uns.getWebhookURL(notification),
		Method:     "POST",
		Headers:    notification.TemplateData,
		Payload:    uns.createWebhookPayload(notification),
		RetryCount: uns.config.RetryConfig.MaxRetries,
		Timeout:    uns.config.Timeout,
	}

	webhookResult := uns.webhookService.SendWebhook(webhookMessage)
	if !webhookResult.Success {
		return webhookResult.Error
	}

	result.MessageID = webhookResult.MessageID
	result.Cost = 0.0 // Webhooks are typically free
	return nil
}

// Helper methods for channel-specific data extraction

func (uns *UnifiedNotificationService) getEmailRecipients(notification *UnifiedNotification) []string {
	if recipients, ok := notification.TemplateData["email_recipients"].([]string); ok {
		return recipients
	}
	return []string{"default@arxos.com"}
}

func (uns *UnifiedNotificationService) getSlackChannel(notification *UnifiedNotification) string {
	if channel, ok := notification.TemplateData["slack_channel"].(string); ok {
		return channel
	}
	return "#general"
}

func (uns *UnifiedNotificationService) getSMSRecipients(notification *UnifiedNotification) string {
	if recipients, ok := notification.TemplateData["sms_recipients"].(string); ok {
		return recipients
	}
	return "+1234567890"
}

func (uns *UnifiedNotificationService) getWebhookURL(notification *UnifiedNotification) string {
	if url, ok := notification.TemplateData["webhook_url"].(string); ok {
		return url
	}
	return "https://api.arxos.com/webhooks/default"
}

func (uns *UnifiedNotificationService) getPriorityColor(priority string) string {
	switch priority {
	case "urgent":
		return "danger"
	case "high":
		return "warning"
	case "normal":
		return "good"
	default:
		return "good"
	}
}

func (uns *UnifiedNotificationService) createWebhookPayload(notification *UnifiedNotification) map[string]interface{} {
	return map[string]interface{}{
		"type":      "notification",
		"title":     notification.Title,
		"message":   notification.Message,
		"priority":  notification.Priority,
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"data":      notification.TemplateData,
	}
}

// updateNotificationStatus updates the notification status based on results
func (uns *UnifiedNotificationService) updateNotificationStatus(notification *UnifiedNotification, results map[string]*NotificationResult) {
	successCount := 0
	totalCount := len(results)

	for _, result := range results {
		if result.Success {
			successCount++
		}
	}

	if successCount == totalCount {
		notification.Status = "delivered"
	} else if successCount > 0 {
		notification.Status = "partially_delivered"
	} else {
		notification.Status = "failed"
	}

	notification.Results = results
}

// updateStatistics updates the notification statistics
func (uns *UnifiedNotificationService) updateStatistics(channel string, result *NotificationResult) {
	uns.statistics.mu.Lock()
	defer uns.statistics.mu.Unlock()

	// Update overall statistics
	uns.statistics.TotalSent++
	if result.Success {
		uns.statistics.Successful++
	} else {
		uns.statistics.Failed++
	}

	// Update channel statistics
	channelStats := uns.statistics.ChannelStats[channel]
	channelStats.TotalSent++
	if result.Success {
		channelStats.Successful++
	} else {
		channelStats.Failed++
	}

	// Update average delivery time
	if result.Success {
		channelStats.AverageTime = (channelStats.AverageTime*float64(channelStats.Successful-1) +
			result.DeliveryTime.Seconds()) / float64(channelStats.Successful)
	}

	// Update success rate
	channelStats.SuccessRate = float64(channelStats.Successful) / float64(channelStats.TotalSent) * 100

	// Update cost
	channelStats.TotalCost += result.Cost

	// Update last sent time
	channelStats.LastSent = time.Now()

	uns.statistics.LastUpdated = time.Now()
}

// GetStatistics returns notification delivery statistics
func (uns *UnifiedNotificationService) GetStatistics() *NotificationStatistics {
	uns.statistics.mu.RLock()
	defer uns.statistics.mu.RUnlock()

	// Create a copy to avoid race conditions
	stats := &NotificationStatistics{
		TotalSent:    uns.statistics.TotalSent,
		Successful:   uns.statistics.Successful,
		Failed:       uns.statistics.Failed,
		LastUpdated:  uns.statistics.LastUpdated,
		ChannelStats: make(map[string]*ChannelStatistics),
	}

	for channel, channelStats := range uns.statistics.ChannelStats {
		stats.ChannelStats[channel] = &ChannelStatistics{
			TotalSent:   channelStats.TotalSent,
			Successful:  channelStats.Successful,
			Failed:      channelStats.Failed,
			AverageTime: channelStats.AverageTime,
			SuccessRate: channelStats.SuccessRate,
			TotalCost:   channelStats.TotalCost,
			LastSent:    channelStats.LastSent,
		}
	}

	return stats
}

// CreateNotification creates a new unified notification
func (uns *UnifiedNotificationService) CreateNotification(title, message string, channels []string, priority string) *UnifiedNotification {
	return &UnifiedNotification{
		ID:           generateUnifiedMessageID(),
		Title:        title,
		Message:      message,
		Channels:     channels,
		Priority:     priority,
		CreatedAt:    time.Now(),
		Status:       "pending",
		Results:      make(map[string]*NotificationResult),
		TemplateData: make(map[string]interface{}),
	}
}

// CreateAlertNotification creates an alert notification
func (uns *UnifiedNotificationService) CreateAlertNotification(alertType, severity, message string, channels []string) *UnifiedNotification {
	notification := uns.CreateNotification(
		fmt.Sprintf("Alert: %s", alertType),
		message,
		channels,
		severity,
	)

	notification.TemplateData["alert_type"] = alertType
	notification.TemplateData["severity"] = severity

	return notification
}

// CreateSystemNotification creates a system notification
func (uns *UnifiedNotificationService) CreateSystemNotification(eventType, message string, channels []string) *UnifiedNotification {
	notification := uns.CreateNotification(
		fmt.Sprintf("System: %s", eventType),
		message,
		channels,
		"normal",
	)

	notification.TemplateData["event_type"] = eventType

	return notification
}

// Helper functions

func generateUnifiedMessageID() string {
	return fmt.Sprintf("unified_%d", time.Now().UnixNano())
}

// ValidateChannel validates a notification channel
func ValidateChannel(channel string) bool {
	validChannels := []string{"email", "slack", "sms", "webhook"}
	for _, validChannel := range validChannels {
		if channel == validChannel {
			return true
		}
	}
	return false
}

// ValidatePriority validates a notification priority
func ValidatePriority(priority string) bool {
	validPriorities := []string{"low", "normal", "high", "urgent"}
	for _, validPriority := range validPriorities {
		if priority == validPriority {
			return true
		}
	}
	return false
}
