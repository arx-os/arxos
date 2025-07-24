package models

import (
	"time"
)

// NotificationChannel represents a notification channel
type NotificationChannel struct {
	ID        string    `json:"id" gorm:"primaryKey"`
	Name      string    `json:"name" gorm:"not null"`
	Type      string    `json:"type" gorm:"not null"`    // email, slack, sms, webhook
	Config    string    `json:"config" gorm:"type:text"` // JSON configuration
	Enabled   bool      `json:"enabled" gorm:"default:true"`
	Priority  int       `json:"priority" gorm:"default:1"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// NotificationTemplate represents a notification template
type NotificationTemplate struct {
	ID          string    `json:"id" gorm:"primaryKey"`
	Name        string    `json:"name" gorm:"not null"`
	Description string    `json:"description"`
	Type        string    `json:"type" gorm:"not null"` // email, slack, sms, webhook
	Subject     string    `json:"subject"`
	Body        string    `json:"body" gorm:"type:text"`
	Variables   string    `json:"variables" gorm:"type:text"` // JSON array of variable names
	Enabled     bool      `json:"enabled" gorm:"default:true"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// NotificationDelivery represents a notification delivery record
type NotificationDelivery struct {
	ID                string     `json:"id" gorm:"primaryKey"`
	NotificationID    string     `json:"notification_id" gorm:"not null"`
	Channel           string     `json:"channel" gorm:"not null"`
	Recipient         string     `json:"recipient"`
	Message           string     `json:"message" gorm:"type:text"`
	Status            string     `json:"status" gorm:"not null"` // pending, sent, delivered, failed
	ProviderMessageID string     `json:"provider_message_id"`
	SentAt            time.Time  `json:"sent_at"`
	DeliveredAt       *time.Time `json:"delivered_at"`
	Error             string     `json:"error"`
	RetryCount        int        `json:"retry_count" gorm:"default:0"`
	DeliveryTime      float64    `json:"delivery_time"` // in seconds
	Cost              float64    `json:"cost"`
	CreatedAt         time.Time  `json:"created_at"`
	UpdatedAt         time.Time  `json:"updated_at"`
}

// NotificationConfig represents notification system configuration
type NotificationConfig struct {
	ID          string    `json:"id" gorm:"primaryKey"`
	Key         string    `json:"key" gorm:"uniqueIndex;not null"`
	Value       string    `json:"value" gorm:"type:text"`
	Description string    `json:"description"`
	Category    string    `json:"category"` // system, email, slack, sms, webhook
	Enabled     bool      `json:"enabled" gorm:"default:true"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// NotificationStatistics represents aggregated notification statistics
type NotificationStatistics struct {
	ID          string    `json:"id" gorm:"primaryKey"`
	Channel     string    `json:"channel" gorm:"not null"`
	Period      string    `json:"period" gorm:"not null"` // daily, weekly, monthly
	Date        time.Time `json:"date" gorm:"not null"`
	TotalSent   int       `json:"total_sent" gorm:"default:0"`
	Successful  int       `json:"successful" gorm:"default:0"`
	Failed      int       `json:"failed" gorm:"default:0"`
	AverageTime float64   `json:"average_time" gorm:"default:0"`
	SuccessRate float64   `json:"success_rate" gorm:"default:0"`
	TotalCost   float64   `json:"total_cost" gorm:"default:0"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// EmailDeliveryStatus represents email delivery status
type EmailDeliveryStatus struct {
	MessageID   string     `json:"message_id"`
	Status      string     `json:"status"`
	DeliveredAt *time.Time `json:"delivered_at"`
	Error       string     `json:"error,omitempty"`
}

// EmailStatistics represents email delivery statistics
type EmailStatistics struct {
	TotalSent   int       `json:"total_sent"`
	Delivered   int       `json:"delivered"`
	Failed      int       `json:"failed"`
	AverageTime float64   `json:"average_time"`
	SuccessRate float64   `json:"success_rate"`
	LastUpdated time.Time `json:"last_updated"`
}

// SlackStatistics represents Slack delivery statistics
type SlackStatistics struct {
	TotalSent   int       `json:"total_sent"`
	Delivered   int       `json:"delivered"`
	Failed      int       `json:"failed"`
	AverageTime float64   `json:"average_time"`
	SuccessRate float64   `json:"success_rate"`
	LastUpdated time.Time `json:"last_updated"`
}

// SMSStatistics represents SMS delivery statistics
type SMSStatistics struct {
	TotalSent   int       `json:"total_sent"`
	Delivered   int       `json:"delivered"`
	Failed      int       `json:"failed"`
	AverageTime float64   `json:"average_time"`
	SuccessRate float64   `json:"success_rate"`
	TotalCost   float64   `json:"total_cost"`
	LastUpdated time.Time `json:"last_updated"`
}

// WebhookStatistics represents webhook delivery statistics
type WebhookStatistics struct {
	TotalSent   int       `json:"total_sent"`
	Delivered   int       `json:"delivered"`
	Failed      int       `json:"failed"`
	AverageTime float64   `json:"average_time"`
	SuccessRate float64   `json:"success_rate"`
	LastUpdated time.Time `json:"last_updated"`
}

// NotificationRequest represents a notification send request
type NotificationRequest struct {
	ID           string                 `json:"id"`
	Title        string                 `json:"title" binding:"required"`
	Message      string                 `json:"message" binding:"required"`
	Channels     []string               `json:"channels" binding:"required"`
	Priority     string                 `json:"priority"`
	TemplateID   string                 `json:"template_id"`
	TemplateData map[string]interface{} `json:"template_data"`
	Recipients   map[string][]string    `json:"recipients"`
	CreatedAt    time.Time              `json:"created_at"`
}

// NotificationResponse represents a notification send response
type NotificationResponse struct {
	ID          string                         `json:"id"`
	Status      string                         `json:"status"`
	Results     map[string]*NotificationResult `json:"results"`
	CreatedAt   time.Time                      `json:"created_at"`
	CompletedAt *time.Time                     `json:"completed_at"`
}

// NotificationResult represents the result of a single notification send
type NotificationResult struct {
	Success           bool       `json:"success"`
	Channel           string     `json:"channel"`
	MessageID         string     `json:"message_id"`
	SentAt            time.Time  `json:"sent_at"`
	DeliveredAt       *time.Time `json:"delivered_at"`
	Error             string     `json:"error,omitempty"`
	RetryCount        int        `json:"retry_count"`
	DeliveryTime      float64    `json:"delivery_time"`
	Cost              float64    `json:"cost"`
	ProviderMessageID string     `json:"provider_message_id,omitempty"`
}

// NotificationHistory represents notification delivery history
type NotificationHistory struct {
	ID                string     `json:"id"`
	NotificationID    string     `json:"notification_id"`
	Channel           string     `json:"channel"`
	Recipient         string     `json:"recipient"`
	Message           string     `json:"message"`
	Status            string     `json:"status"`
	ProviderMessageID string     `json:"provider_message_id"`
	SentAt            time.Time  `json:"sent_at"`
	DeliveredAt       *time.Time `json:"delivered_at"`
	Error             string     `json:"error,omitempty"`
	RetryCount        int        `json:"retry_count"`
	DeliveryTime      float64    `json:"delivery_time"`
	Cost              float64    `json:"cost"`
	CreatedAt         time.Time  `json:"created_at"`
}

// NotificationTemplateRequest represents a template creation request
type NotificationTemplateRequest struct {
	Name        string   `json:"name" binding:"required"`
	Description string   `json:"description"`
	Type        string   `json:"type" binding:"required"`
	Subject     string   `json:"subject"`
	Body        string   `json:"body" binding:"required"`
	Variables   []string `json:"variables"`
	Enabled     bool     `json:"enabled"`
}

// NotificationChannelRequest represents a channel creation request
type NotificationChannelRequest struct {
	Name     string                 `json:"name" binding:"required"`
	Type     string                 `json:"type" binding:"required"`
	Config   map[string]interface{} `json:"config" binding:"required"`
	Enabled  bool                   `json:"enabled"`
	Priority int                    `json:"priority"`
}

// NotificationConfigRequest represents a configuration update request
type NotificationConfigRequest struct {
	Key         string `json:"key" binding:"required"`
	Value       string `json:"value" binding:"required"`
	Description string `json:"description"`
	Category    string `json:"category"`
	Enabled     bool   `json:"enabled"`
}

// NotificationStatisticsRequest represents a statistics query request
type NotificationStatisticsRequest struct {
	Channel   string    `json:"channel"`
	Period    string    `json:"period"`
	StartDate time.Time `json:"start_date"`
	EndDate   time.Time `json:"end_date"`
}

// NotificationStatisticsResponse represents a statistics query response
type NotificationStatisticsResponse struct {
	Channel     string    `json:"channel"`
	Period      string    `json:"period"`
	Date        time.Time `json:"date"`
	TotalSent   int       `json:"total_sent"`
	Successful  int       `json:"successful"`
	Failed      int       `json:"failed"`
	AverageTime float64   `json:"average_time"`
	SuccessRate float64   `json:"success_rate"`
	TotalCost   float64   `json:"total_cost"`
}

// NotificationStatus represents notification status constants
const (
	NotificationStatusPending   = "pending"
	NotificationStatusSent      = "sent"
	NotificationStatusDelivered = "delivered"
	NotificationStatusFailed    = "failed"
	NotificationStatusCancelled = "cancelled"
)

// NotificationPriority represents notification priority constants
const (
	NotificationPriorityLow    = "low"
	NotificationPriorityNormal = "normal"
	NotificationPriorityHigh   = "high"
	NotificationPriorityUrgent = "urgent"
)

// NotificationChannelType represents notification channel type constants
const (
	NotificationChannelEmail   = "email"
	NotificationChannelSlack   = "slack"
	NotificationChannelSMS     = "sms"
	NotificationChannelWebhook = "webhook"
)

// NotificationPeriod represents statistics period constants
const (
	NotificationPeriodDaily   = "daily"
	NotificationPeriodWeekly  = "weekly"
	NotificationPeriodMonthly = "monthly"
)
