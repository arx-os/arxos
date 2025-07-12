package models

import (
	"time"
)

// CMMSConnection represents a connection to an external CMMS system
type CMMSConnection struct {
	ID              int        `json:"id" db:"id"`
	Name            string     `json:"name" db:"name"`
	Type            string     `json:"type" db:"type"` // e.g. "upkeep", "fiix", "custom"
	BaseURL         string     `json:"base_url" db:"base_url"`
	APIKey          string     `json:"api_key" db:"api_key"`
	Username        string     `json:"username" db:"username"`
	Password        string     `json:"password" db:"password"`
	OAuth2ClientID  string     `json:"oauth2_client_id" db:"oauth2_client_id"`
	OAuth2Secret    string     `json:"oauth2_secret" db:"oauth2_secret"`
	OAuth2TokenURL  string     `json:"oauth2_token_url" db:"oauth2_token_url"`
	OAuth2Scope     string     `json:"oauth2_scope" db:"oauth2_scope"`
	SyncIntervalMin int        `json:"sync_interval_min" db:"sync_interval_min"` // minutes
	IsActive        bool       `json:"is_active" db:"is_active"`
	LastSync        *time.Time `json:"last_sync" db:"last_sync"`
	LastSyncStatus  string     `json:"last_sync_status" db:"last_sync_status"`
	LastSyncError   string     `json:"last_sync_error" db:"last_sync_error"`
	CreatedAt       time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt       time.Time  `json:"updated_at" db:"updated_at"`
}

// CMMSMapping represents field mappings between Arxos and CMMS systems
type CMMSMapping struct {
	ID               int    `json:"id" db:"id"`
	CMMSConnectionID int    `json:"cmms_connection_id" db:"cmms_connection_id"`
	ArxosField       string `json:"arxos_field" db:"arxos_field"`
	CMMSField        string `json:"cmms_field" db:"cmms_field"`
	DataType         string `json:"data_type" db:"data_type"` // string, number, date, boolean
	IsRequired       bool   `json:"is_required" db:"is_required"`
	DefaultValue     string `json:"default_value" db:"default_value"`
	TransformRule    string `json:"transform_rule" db:"transform_rule"` // JSON transformation rules
}

// MaintenanceSchedule represents a maintenance schedule from CMMS
type MaintenanceSchedule struct {
	ID               int        `json:"id" db:"id"`
	AssetID          int        `json:"asset_id" db:"asset_id"`
	CMMSConnectionID int        `json:"cmms_connection_id" db:"cmms_connection_id"`
	CMMSAssetID      string     `json:"cmms_asset_id" db:"cmms_asset_id"`
	ScheduleType     string     `json:"schedule_type" db:"schedule_type"` // preventive, predictive, etc.
	Frequency        string     `json:"frequency" db:"frequency"`         // daily, weekly, monthly, etc.
	Interval         int        `json:"interval" db:"interval"`           // every X frequency units
	Description      string     `json:"description" db:"description"`
	Instructions     string     `json:"instructions" db:"instructions"`
	EstimatedHours   float64    `json:"estimated_hours" db:"estimated_hours"`
	Priority         string     `json:"priority" db:"priority"` // low, medium, high, critical
	IsActive         bool       `json:"is_active" db:"is_active"`
	NextDueDate      time.Time  `json:"next_due_date" db:"next_due_date"`
	LastCompleted    *time.Time `json:"last_completed" db:"last_completed"`
	CreatedAt        time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time  `json:"updated_at" db:"updated_at"`
}

// WorkOrder represents a work order from CMMS
type WorkOrder struct {
	ID               int        `json:"id" db:"id"`
	AssetID          int        `json:"asset_id" db:"asset_id"`
	CMMSConnectionID int        `json:"cmms_connection_id" db:"cmms_connection_id"`
	CMMSWorkOrderID  string     `json:"cmms_work_order_id" db:"cmms_work_order_id"`
	WorkOrderNumber  string     `json:"work_order_number" db:"work_order_number"`
	Type             string     `json:"type" db:"type"`         // corrective, preventive, emergency
	Status           string     `json:"status" db:"status"`     // open, in_progress, completed, cancelled
	Priority         string     `json:"priority" db:"priority"` // low, medium, high, critical
	Description      string     `json:"description" db:"description"`
	Instructions     string     `json:"instructions" db:"instructions"`
	AssignedTo       string     `json:"assigned_to" db:"assigned_to"`
	EstimatedHours   float64    `json:"estimated_hours" db:"estimated_hours"`
	ActualHours      float64    `json:"actual_hours" db:"actual_hours"`
	Cost             float64    `json:"cost" db:"cost"`
	PartsUsed        string     `json:"parts_used" db:"parts_used"`
	CreatedDate      time.Time  `json:"created_date" db:"created_date"`
	ScheduledDate    time.Time  `json:"scheduled_date" db:"scheduled_date"`
	StartedDate      *time.Time `json:"started_date" db:"started_date"`
	CompletedDate    *time.Time `json:"completed_date" db:"completed_date"`
	CreatedAt        time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time  `json:"updated_at" db:"updated_at"`
}

// EquipmentSpecification represents equipment specifications from CMMS
type EquipmentSpecification struct {
	ID               int       `json:"id" db:"id"`
	AssetID          int       `json:"asset_id" db:"asset_id"`
	CMMSConnectionID int       `json:"cmms_connection_id" db:"cmms_connection_id"`
	CMMSAssetID      string    `json:"cmms_asset_id" db:"cmms_asset_id"`
	SpecType         string    `json:"spec_type" db:"spec_type"` // technical, operational, maintenance
	SpecName         string    `json:"spec_name" db:"spec_name"`
	SpecValue        string    `json:"spec_value" db:"spec_value"`
	Unit             string    `json:"unit" db:"unit"`
	MinValue         *float64  `json:"min_value" db:"min_value"`
	MaxValue         *float64  `json:"max_value" db:"max_value"`
	IsCritical       bool      `json:"is_critical" db:"is_critical"`
	CreatedAt        time.Time `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time `json:"updated_at" db:"updated_at"`
}

// CMMSSyncLog represents a sync operation log
type CMMSSyncLog struct {
	ID               int       `json:"id" db:"id"`
	CMMSConnectionID int       `json:"cmms_connection_id" db:"cmms_connection_id"`
	SyncType         string    `json:"sync_type" db:"sync_type"` // schedules, work_orders, specs
	Status           string    `json:"status" db:"status"`       // success, partial, failed
	RecordsProcessed int       `json:"records_processed" db:"records_processed"`
	RecordsCreated   int       `json:"records_created" db:"records_created"`
	RecordsUpdated   int       `json:"records_updated" db:"records_updated"`
	RecordsFailed    int       `json:"records_failed" db:"records_failed"`
	ErrorDetails     string    `json:"error_details" db:"error_details"`
	StartedAt        time.Time `json:"started_at" db:"started_at"`
	CompletedAt      time.Time `json:"completed_at" db:"completed_at"`
}
