package models

import (
	"encoding/json"
	"fmt"
	"time"

	"gorm.io/datatypes"
	"gorm.io/gorm"
)

// NotificationChannelType represents the type of notification channel
type NotificationChannelType string

const (
	NotificationChannelTypeEmail   NotificationChannelType = "email"
	NotificationChannelTypeSlack   NotificationChannelType = "slack"
	NotificationChannelTypeSMS     NotificationChannelType = "sms"
	NotificationChannelTypeWebhook NotificationChannelType = "webhook"
	NotificationChannelTypePush    NotificationChannelType = "push"
	NotificationChannelTypeInApp   NotificationChannelType = "in_app"
)

// NotificationPriority represents the priority level of a notification
type NotificationPriority string

const (
	NotificationPriorityLow    NotificationPriority = "low"
	NotificationPriorityNormal NotificationPriority = "normal"
	NotificationPriorityHigh   NotificationPriority = "high"
	NotificationPriorityUrgent NotificationPriority = "urgent"
)

// NotificationStatus represents the status of a notification
type NotificationStatus string

const (
	NotificationStatusPending     NotificationStatus = "pending"
	NotificationStatusSending     NotificationStatus = "sending"
	NotificationStatusSent        NotificationStatus = "sent"
	NotificationStatusDelivered   NotificationStatus = "delivered"
	NotificationStatusFailed      NotificationStatus = "failed"
	NotificationStatusRateLimited NotificationStatus = "rate_limited"
	NotificationStatusCancelled   NotificationStatus = "cancelled"
)

// NotificationType represents the type of notification
type NotificationType string

const (
	NotificationTypeSystem      NotificationType = "system"
	NotificationTypeUser        NotificationType = "user"
	NotificationTypeMaintenance NotificationType = "maintenance"
	NotificationTypeAlert       NotificationType = "alert"
	NotificationTypeReminder    NotificationType = "reminder"
	NotificationTypeUpdate      NotificationType = "update"
	NotificationTypeSecurity    NotificationType = "security"
)

// Enhanced NotificationTemplate with additional fields
type NotificationTemplateEnhanced struct {
	ID          uint             `gorm:"primaryKey" json:"id"`
	Name        string           `gorm:"uniqueIndex;not null" json:"name"`
	Description string           `gorm:"type:text" json:"description"`
	Type        NotificationType `gorm:"index;not null" json:"type"`
	Channels    datatypes.JSON   `json:"channels"` // Array of NotificationChannelType
	Subject     string           `gorm:"type:text" json:"subject"`
	Body        string           `gorm:"type:text" json:"body"`
	HTMLBody    string           `gorm:"type:text" json:"html_body"`
	Variables   datatypes.JSON   `json:"variables"` // Template variables
	IsActive    bool             `gorm:"default:true" json:"is_active"`
	CreatedBy   uint             `gorm:"index;not null" json:"created_by"`
	CreatedAt   time.Time        `json:"created_at"`
	UpdatedAt   time.Time        `json:"updated_at"`
	DeletedAt   gorm.DeletedAt   `gorm:"index" json:"-"`

	// Relationships
	User User `json:"user,omitempty"`
}

// Enhanced NotificationConfig with additional fields
type NotificationConfigEnhanced struct {
	ID            uint                 `gorm:"primaryKey" json:"id"`
	Name          string               `gorm:"uniqueIndex;not null" json:"name"`
	Description   string               `gorm:"type:text" json:"description"`
	Channels      datatypes.JSON       `json:"channels"` // Array of NotificationChannelType
	Priority      NotificationPriority `gorm:"default:'normal'" json:"priority"`
	RetryAttempts int                  `gorm:"default:3" json:"retry_attempts"`
	RetryDelay    int                  `gorm:"default:60" json:"retry_delay"` // seconds
	Timeout       int                  `gorm:"default:30" json:"timeout"`     // seconds
	TemplateID    *uint                `gorm:"index" json:"template_id"`
	TemplateData  datatypes.JSON       `json:"template_data"`
	IsActive      bool                 `gorm:"default:true" json:"is_active"`
	CreatedBy     uint                 `gorm:"index;not null" json:"created_by"`
	CreatedAt     time.Time            `json:"created_at"`
	UpdatedAt     time.Time            `json:"updated_at"`
	DeletedAt     gorm.DeletedAt       `gorm:"index" json:"-"`

	// Relationships
	Template NotificationTemplateEnhanced `json:"template,omitempty"`
	User     User                         `json:"user,omitempty"`
}

// Enhanced Notification with additional fields
type NotificationEnhanced struct {
	ID                uint                 `gorm:"primaryKey" json:"id"`
	Title             string               `gorm:"type:text;not null" json:"title"`
	Message           string               `gorm:"type:text;not null" json:"message"`
	Type              NotificationType     `gorm:"index;not null" json:"type"`
	Channels          datatypes.JSON       `json:"channels"` // Array of NotificationChannelType
	Priority          NotificationPriority `gorm:"default:'normal'" json:"priority"`
	Status            NotificationStatus   `gorm:"default:'pending'" json:"status"`
	ConfigID          *uint                `gorm:"index" json:"config_id"`
	TemplateID        *uint                `gorm:"index" json:"template_id"`
	TemplateData      datatypes.JSON       `json:"template_data"`
	RecipientID       uint                 `gorm:"index;not null" json:"recipient_id"`
	SenderID          *uint                `gorm:"index" json:"sender_id"`
	BuildingID        *uint                `gorm:"index" json:"building_id"`
	AssetID           *string              `gorm:"index" json:"asset_id"`
	RelatedObjectID   *string              `gorm:"index" json:"related_object_id"`
	RelatedObjectType string               `json:"related_object_type"`
	Metadata          datatypes.JSON       `json:"metadata"`
	ErrorMessage      string               `gorm:"type:text" json:"error_message"`
	RetryCount        int                  `gorm:"default:0" json:"retry_count"`
	CreatedAt         time.Time            `json:"created_at"`
	UpdatedAt         time.Time            `json:"updated_at"`
	DeletedAt         gorm.DeletedAt       `gorm:"index" json:"-"`

	// Relationships
	Config     NotificationConfigEnhanced     `json:"config,omitempty"`
	Template   NotificationTemplateEnhanced   `json:"template,omitempty"`
	Recipient  User                           `json:"recipient,omitempty"`
	Sender     User                           `gorm:"foreignKey:SenderID" json:"sender,omitempty"`
	Building   Building                       `json:"building,omitempty"`
	Deliveries []NotificationDeliveryEnhanced `json:"deliveries,omitempty"`
}

// Enhanced NotificationDelivery with additional fields
type NotificationDeliveryEnhanced struct {
	ID             uint                    `gorm:"primaryKey" json:"id"`
	NotificationID uint                    `gorm:"index;not null" json:"notification_id"`
	Channel        NotificationChannelType `gorm:"index;not null" json:"channel"`
	Status         NotificationStatus      `gorm:"default:'pending'" json:"status"`
	AttemptNumber  int                     `gorm:"default:1" json:"attempt_number"`
	SentAt         *time.Time              `json:"sent_at"`
	DeliveredAt    *time.Time              `json:"delivered_at"`
	FailedAt       *time.Time              `json:"failed_at"`
	ErrorMessage   string                  `gorm:"type:text" json:"error_message"`
	ResponseCode   int                     `json:"response_code"`
	ResponseBody   string                  `gorm:"type:text" json:"response_body"`
	ExternalID     string                  `gorm:"index" json:"external_id"` // External service ID
	Metadata       datatypes.JSON          `json:"metadata"`
	CreatedAt      time.Time               `json:"created_at"`
	UpdatedAt      time.Time               `json:"updated_at"`

	// Relationships
	Notification NotificationEnhanced `json:"notification,omitempty"`
}

// NotificationChannelConfig represents configuration for a specific notification channel
type NotificationChannelConfig struct {
	ID          uint                    `gorm:"primaryKey" json:"id"`
	Channel     NotificationChannelType `gorm:"uniqueIndex;not null" json:"channel"`
	Name        string                  `gorm:"not null" json:"name"`
	Description string                  `gorm:"type:text" json:"description"`
	IsEnabled   bool                    `gorm:"default:true" json:"is_enabled"`
	Config      datatypes.JSON          `json:"config"`                        // Channel-specific configuration
	RateLimit   int                     `gorm:"default:100" json:"rate_limit"` // messages per minute
	Timeout     int                     `gorm:"default:30" json:"timeout"`     // seconds
	RetryLimit  int                     `gorm:"default:3" json:"retry_limit"`
	CreatedAt   time.Time               `json:"created_at"`
	UpdatedAt   time.Time               `json:"updated_at"`
	DeletedAt   gorm.DeletedAt          `gorm:"index" json:"-"`
}

// NotificationPreference represents user notification preferences
type NotificationPreference struct {
	ID        uint                    `gorm:"primaryKey" json:"id"`
	UserID    uint                    `gorm:"uniqueIndex:idx_user_channel;not null" json:"user_id"`
	Channel   NotificationChannelType `gorm:"uniqueIndex:idx_user_channel;not null" json:"channel"`
	Type      NotificationType        `gorm:"index;not null" json:"type"`
	IsEnabled bool                    `gorm:"default:true" json:"is_enabled"`
	Priority  NotificationPriority    `gorm:"default:'normal'" json:"priority"`
	Frequency string                  `gorm:"default:'immediate'" json:"frequency"` // immediate, daily, weekly, never
	CreatedAt time.Time               `json:"created_at"`
	UpdatedAt time.Time               `json:"updated_at"`

	// Relationships
	User User `json:"user,omitempty"`
}

// NotificationLog represents notification activity logs
type NotificationLog struct {
	ID             uint               `gorm:"primaryKey" json:"id"`
	NotificationID uint               `gorm:"index;not null" json:"notification_id"`
	DeliveryID     *uint              `gorm:"index" json:"delivery_id"`
	Action         string             `gorm:"index;not null" json:"action"` // created, sent, delivered, failed, etc.
	Status         NotificationStatus `gorm:"index;not null" json:"status"`
	Message        string             `gorm:"type:text" json:"message"`
	Metadata       datatypes.JSON     `json:"metadata"`
	IPAddress      string             `json:"ip_address"`
	UserAgent      string             `gorm:"type:text" json:"user_agent"`
	CreatedAt      time.Time          `json:"created_at"`

	// Relationships
	Notification NotificationEnhanced         `json:"notification,omitempty"`
	Delivery     NotificationDeliveryEnhanced `json:"delivery,omitempty"`
}

// NotificationStats represents notification statistics
type NotificationStats struct {
	ID               uint                    `gorm:"primaryKey" json:"id"`
	Date             time.Time               `gorm:"index;not null" json:"date"`
	Channel          NotificationChannelType `gorm:"index;not null" json:"channel"`
	Type             NotificationType        `gorm:"index;not null" json:"type"`
	TotalSent        int                     `json:"total_sent"`
	TotalDelivered   int                     `json:"total_delivered"`
	TotalFailed      int                     `json:"total_failed"`
	TotalRateLimited int                     `json:"total_rate_limited"`
	AvgDeliveryTime  float64                 `json:"avg_delivery_time"` // in seconds
	SuccessRate      float64                 `json:"success_rate"`      // percentage
	CreatedAt        time.Time               `json:"created_at"`
	UpdatedAt        time.Time               `json:"updated_at"`
}

// NotificationQueue represents queued notifications for processing
type NotificationQueue struct {
	ID             uint                 `gorm:"primaryKey" json:"id"`
	NotificationID uint                 `gorm:"index;not null" json:"notification_id"`
	Priority       NotificationPriority `gorm:"index;not null" json:"priority"`
	Status         string               `gorm:"index;not null" json:"status"` // queued, processing, completed, failed
	AttemptCount   int                  `gorm:"default:0" json:"attempt_count"`
	MaxAttempts    int                  `gorm:"default:3" json:"max_attempts"`
	ScheduledAt    time.Time            `gorm:"index;not null" json:"scheduled_at"`
	ProcessedAt    *time.Time           `json:"processed_at"`
	ErrorMessage   string               `gorm:"type:text" json:"error_message"`
	CreatedAt      time.Time            `json:"created_at"`
	UpdatedAt      time.Time            `json:"updated_at"`

	// Relationships
	Notification NotificationEnhanced `json:"notification,omitempty"`
}

// Helper methods for NotificationEnhanced struct
func (n *NotificationEnhanced) GetChannels() []NotificationChannelType {
	var channels []NotificationChannelType
	if n.Channels != nil {
		json.Unmarshal(n.Channels, &channels)
	}
	return channels
}

func (n *NotificationEnhanced) SetChannels(channels []NotificationChannelType) error {
	data, err := json.Marshal(channels)
	if err != nil {
		return fmt.Errorf("failed to marshal channels: %w", err)
	}
	n.Channels = data
	return nil
}

func (n *NotificationEnhanced) GetMetadata() map[string]interface{} {
	var metadata map[string]interface{}
	if n.Metadata != nil {
		json.Unmarshal(n.Metadata, &metadata)
	}
	return metadata
}

func (n *NotificationEnhanced) SetMetadata(metadata map[string]interface{}) error {
	data, err := json.Marshal(metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}
	n.Metadata = data
	return nil
}

// Helper methods for NotificationTemplateEnhanced struct
func (nt *NotificationTemplateEnhanced) GetChannels() []NotificationChannelType {
	var channels []NotificationChannelType
	if nt.Channels != nil {
		json.Unmarshal(nt.Channels, &channels)
	}
	return channels
}

func (nt *NotificationTemplateEnhanced) SetChannels(channels []NotificationChannelType) error {
	data, err := json.Marshal(channels)
	if err != nil {
		return fmt.Errorf("failed to marshal channels: %w", err)
	}
	nt.Channels = data
	return nil
}

func (nt *NotificationTemplateEnhanced) GetVariables() map[string]interface{} {
	var variables map[string]interface{}
	if nt.Variables != nil {
		json.Unmarshal(nt.Variables, &variables)
	}
	return variables
}

func (nt *NotificationTemplateEnhanced) SetVariables(variables map[string]interface{}) error {
	data, err := json.Marshal(variables)
	if err != nil {
		return fmt.Errorf("failed to marshal variables: %w", err)
	}
	nt.Variables = data
	return nil
}

// Helper methods for NotificationConfigEnhanced struct
func (nc *NotificationConfigEnhanced) GetChannels() []NotificationChannelType {
	var channels []NotificationChannelType
	if nc.Channels != nil {
		json.Unmarshal(nc.Channels, &channels)
	}
	return channels
}

func (nc *NotificationConfigEnhanced) SetChannels(channels []NotificationChannelType) error {
	data, err := json.Marshal(channels)
	if err != nil {
		return fmt.Errorf("failed to marshal channels: %w", err)
	}
	nc.Channels = data
	return nil
}

func (nc *NotificationConfigEnhanced) GetTemplateData() map[string]interface{} {
	var templateData map[string]interface{}
	if nc.TemplateData != nil {
		json.Unmarshal(nc.TemplateData, &templateData)
	}
	return templateData
}

func (nc *NotificationConfigEnhanced) SetTemplateData(templateData map[string]interface{}) error {
	data, err := json.Marshal(templateData)
	if err != nil {
		return fmt.Errorf("failed to marshal template data: %w", err)
	}
	nc.TemplateData = data
	return nil
}

// Helper methods for NotificationChannelConfig struct
func (ncc *NotificationChannelConfig) GetConfig() map[string]interface{} {
	var config map[string]interface{}
	if ncc.Config != nil {
		json.Unmarshal(ncc.Config, &config)
	}
	return config
}

func (ncc *NotificationChannelConfig) SetConfig(config map[string]interface{}) error {
	data, err := json.Marshal(config)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}
	ncc.Config = data
	return nil
}

// Helper methods for NotificationDeliveryEnhanced struct
func (nd *NotificationDeliveryEnhanced) GetMetadata() map[string]interface{} {
	var metadata map[string]interface{}
	if nd.Metadata != nil {
		json.Unmarshal(nd.Metadata, &metadata)
	}
	return metadata
}

func (nd *NotificationDeliveryEnhanced) SetMetadata(metadata map[string]interface{}) error {
	data, err := json.Marshal(metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}
	nd.Metadata = data
	return nil
}

// Helper methods for NotificationLog struct
func (nl *NotificationLog) GetMetadata() map[string]interface{} {
	var metadata map[string]interface{}
	if nl.Metadata != nil {
		json.Unmarshal(nl.Metadata, &metadata)
	}
	return metadata
}

func (nl *NotificationLog) SetMetadata(metadata map[string]interface{}) error {
	data, err := json.Marshal(metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}
	nl.Metadata = data
	return nil
}

// Validation methods
func (nct NotificationChannelType) IsValid() bool {
	switch nct {
	case NotificationChannelTypeEmail, NotificationChannelTypeSlack, NotificationChannelTypeSMS,
		NotificationChannelTypeWebhook, NotificationChannelTypePush, NotificationChannelTypeInApp:
		return true
	default:
		return false
	}
}

func (np NotificationPriority) IsValid() bool {
	switch np {
	case NotificationPriorityLow, NotificationPriorityNormal, NotificationPriorityHigh, NotificationPriorityUrgent:
		return true
	default:
		return false
	}
}

func (ns NotificationStatus) IsValid() bool {
	switch ns {
	case NotificationStatusPending, NotificationStatusSending, NotificationStatusSent,
		NotificationStatusDelivered, NotificationStatusFailed, NotificationStatusRateLimited, NotificationStatusCancelled:
		return true
	default:
		return false
	}
}

func (nt NotificationType) IsValid() bool {
	switch nt {
	case NotificationTypeSystem, NotificationTypeUser, NotificationTypeMaintenance,
		NotificationTypeAlert, NotificationTypeReminder, NotificationTypeUpdate, NotificationTypeSecurity:
		return true
	default:
		return false
	}
}

// String methods for better logging
func (nct NotificationChannelType) String() string {
	return string(nct)
}

func (np NotificationPriority) String() string {
	return string(np)
}

func (ns NotificationStatus) String() string {
	return string(ns)
}

func (nt NotificationType) String() string {
	return string(nt)
}
