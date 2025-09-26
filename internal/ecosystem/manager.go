package ecosystem

import (
	"context"
	"fmt"
	"time"
)

// Manager handles the three-tier ecosystem coordination
type Manager struct {
	coreService     CoreService
	hardwareService HardwareService
	workflowService WorkflowService
}

// CoreService handles Layer 1 (FREE) functionality
type CoreService interface {
	// Building management
	CreateBuilding(ctx context.Context, req CreateBuildingRequest) (*Building, error)
	GetBuilding(ctx context.Context, id string) (*Building, error)
	ListBuildings(ctx context.Context, userID string) ([]*Building, error)

	// Equipment management
	CreateEquipment(ctx context.Context, req CreateEquipmentRequest) (*Equipment, error)
	GetEquipment(ctx context.Context, id string) (*Equipment, error)
	QueryEquipment(ctx context.Context, query EquipmentQuery) ([]*Equipment, error)

	// Spatial operations
	SpatialQuery(ctx context.Context, query SpatialQuery) ([]*Equipment, error)

	// Import/Export
	ImportData(ctx context.Context, req ImportRequest) (*ImportResult, error)
	ExportData(ctx context.Context, req ExportRequest) (*ExportResult, error)
}

// HardwareService handles Layer 2 (FREEMIUM) functionality
type HardwareService interface {
	// Device management
	RegisterDevice(ctx context.Context, req RegisterDeviceRequest) (*Device, error)
	ListDevices(ctx context.Context, userID string) ([]*Device, error)
	UpdateDeviceFirmware(ctx context.Context, deviceID string, firmware []byte) error

	// Templates
	GetDeviceTemplates(ctx context.Context) ([]*DeviceTemplate, error)
	CreateDeviceFromTemplate(ctx context.Context, templateID string) (*Device, error)

	// Gateway
	DeployGateway(ctx context.Context, req DeployGatewayRequest) (*Gateway, error)
	ConfigureGateway(ctx context.Context, gatewayID string, config GatewayConfig) error

	// Marketplace
	ListCertifiedDevices(ctx context.Context) ([]*CertifiedDevice, error)
	PurchaseDevice(ctx context.Context, req PurchaseDeviceRequest) (*PurchaseResult, error)
}

// WorkflowService handles Layer 3 (PAID) functionality
type WorkflowService interface {
	// Workflow management
	CreateWorkflow(ctx context.Context, req CreateWorkflowRequest) (*Workflow, error)
	ExecuteWorkflow(ctx context.Context, workflowID string, input map[string]interface{}) (*WorkflowResult, error)
	ListWorkflows(ctx context.Context, userID string) ([]*Workflow, error)

	// CMMS/CAFM
	CreateWorkOrder(ctx context.Context, req CreateWorkOrderRequest) (*WorkOrder, error)
	ScheduleMaintenance(ctx context.Context, req ScheduleMaintenanceRequest) (*MaintenanceSchedule, error)
	GenerateReport(ctx context.Context, req GenerateReportRequest) (*Report, error)

	// Automation
	CreateAutomation(ctx context.Context, req CreateAutomationRequest) (*Automation, error)
	TriggerAutomation(ctx context.Context, automationID string, trigger map[string]interface{}) error

	// Analytics
	GetAnalytics(ctx context.Context, req AnalyticsRequest) (*AnalyticsResult, error)
	GetPredictiveInsights(ctx context.Context, buildingID string) (*PredictiveInsights, error)
}

// NewManager creates a new ecosystem manager
func NewManager(core CoreService, hardware HardwareService, workflow WorkflowService) *Manager {
	return &Manager{
		coreService:     core,
		hardwareService: hardware,
		workflowService: workflow,
	}
}

// GetTierCapabilities returns capabilities for a specific tier
func (m *Manager) GetTierCapabilities(tier Tier) map[string]interface{} {
	capabilities := make(map[string]interface{})

	switch tier {
	case TierCore:
		capabilities["core_services"] = m.coreService != nil
		capabilities["building_management"] = true
		capabilities["equipment_management"] = true
		capabilities["spatial_queries"] = true
		capabilities["import_export"] = true

	case TierHardware:
		capabilities["hardware_services"] = m.hardwareService != nil
		capabilities["device_management"] = true
		capabilities["gateway_deployment"] = true
		capabilities["marketplace"] = true
		capabilities["device_templates"] = true

	case TierWorkflow:
		capabilities["workflow_services"] = m.workflowService != nil
		capabilities["workflow_automation"] = true
		capabilities["cmmc_features"] = true
		capabilities["analytics"] = true
		capabilities["enterprise_integrations"] = true
	}

	return capabilities
}

// ValidateTierAccess validates if a user has access to a specific tier
func (m *Manager) ValidateTierAccess(userID string, tier Tier, feature string) error {
	// TODO: Implement user tier validation logic
	// This would check user's subscription, organization tier, etc.

	switch tier {
	case TierCore:
		// Core tier is always available
		return nil

	case TierHardware:
		// Check if user has hardware tier access
		// This could be based on organization plan, individual subscription, etc.
		return nil

	case TierWorkflow:
		// Check if user has workflow tier access
		// This requires paid subscription
		return nil

	default:
		return fmt.Errorf("unknown tier: %s", tier)
	}
}

// Data structures for ecosystem services

type Building struct {
	ID        string                 `json:"id"`
	Name      string                 `json:"name"`
	Path      string                 `json:"path"`
	Tier      Tier                   `json:"tier"`
	Metadata  map[string]interface{} `json:"metadata"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

type Equipment struct {
	ID        string                 `json:"id"`
	Name      string                 `json:"name"`
	Path      string                 `json:"path"`
	Type      string                 `json:"type"`
	Position  map[string]interface{} `json:"position"`
	Metadata  map[string]interface{} `json:"metadata"`
	Tier      Tier                   `json:"tier"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

type Device struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	TemplateID string                 `json:"template_id"`
	Status     string                 `json:"status"`
	Config     map[string]interface{} `json:"config"`
}

type Workflow struct {
	ID            string                 `json:"id"`
	Name          string                 `json:"name"`
	Description   string                 `json:"description"`
	Definition    map[string]interface{} `json:"definition"`
	Status        string                 `json:"status"`
	Tier          Tier                   `json:"tier"`
	N8nWorkflowID string                 `json:"n8n_workflow_id"`
	CreatedAt     time.Time              `json:"created_at"`
	UpdatedAt     time.Time              `json:"updated_at"`
}

// Request/Response types

type CreateBuildingRequest struct {
	Name     string                 `json:"name"`
	Path     string                 `json:"path"`
	Metadata map[string]interface{} `json:"metadata"`
}

type CreateEquipmentRequest struct {
	Name     string                 `json:"name"`
	Path     string                 `json:"path"`
	Type     string                 `json:"type"`
	Position map[string]interface{} `json:"position"`
	Metadata map[string]interface{} `json:"metadata"`
}

type EquipmentQuery struct {
	BuildingID string                 `json:"building_id"`
	Type       string                 `json:"type"`
	Filters    map[string]interface{} `json:"filters"`
	Limit      int                    `json:"limit"`
	Offset     int                    `json:"offset"`
}

type SpatialQuery struct {
	Center map[string]interface{} `json:"center"`
	Radius float64                `json:"radius"`
	Type   string                 `json:"type"`
}

type ImportRequest struct {
	Format     string                 `json:"format"`
	Data       []byte                 `json:"data"`
	BuildingID string                 `json:"building_id"`
	Options    map[string]interface{} `json:"options"`
}

type ExportRequest struct {
	Format     string                 `json:"format"`
	BuildingID string                 `json:"building_id"`
	Options    map[string]interface{} `json:"options"`
}

type RegisterDeviceRequest struct {
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	TemplateID string                 `json:"template_id"`
	Config     map[string]interface{} `json:"config"`
}

type DeployGatewayRequest struct {
	Name    string                 `json:"name"`
	Type    string                 `json:"type"`
	Config  map[string]interface{} `json:"config"`
	Devices []string               `json:"devices"`
}

type CreateWorkflowRequest struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Definition  map[string]interface{} `json:"definition"`
}

type CreateWorkOrderRequest struct {
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Priority    string                 `json:"priority"`
	EquipmentID string                 `json:"equipment_id"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type WorkOrderFilters struct {
	Status      string `json:"status"`
	Priority    string `json:"priority"`
	EquipmentID string `json:"equipment_id"`
	AssignedTo  string `json:"assigned_to"`
}

type WorkOrderCompletion struct {
	WorkOrderID string                 `json:"work_order_id"`
	Status      string                 `json:"status"`
	CompletedBy string                 `json:"completed_by"`
	CompletedAt string                 `json:"completed_at"`
	Notes       string                 `json:"notes"`
	Results     map[string]interface{} `json:"results"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type CreateMaintenanceScheduleRequest struct {
	Name         string                   `json:"name"`
	Description  string                   `json:"description"`
	Type         string                   `json:"type"`
	Schedule     map[string]interface{}   `json:"schedule"`
	EquipmentIDs []string                 `json:"equipment_ids"`
	Tasks        []map[string]interface{} `json:"tasks"`
	Metadata     map[string]interface{}   `json:"metadata"`
}

type MaintenanceExecution struct {
	ID          string                   `json:"id"`
	ScheduleID  string                   `json:"schedule_id"`
	Status      string                   `json:"status"`
	StartedAt   string                   `json:"started_at"`
	CompletedAt string                   `json:"completed_at"`
	Tasks       []map[string]interface{} `json:"tasks"`
	Results     map[string]interface{}   `json:"results"`
}

type CreateAutomationRequest struct {
	Name       string                   `json:"name"`
	Trigger    map[string]interface{}   `json:"trigger"`
	Actions    []map[string]interface{} `json:"actions"`
	Conditions map[string]interface{}   `json:"conditions"`
}

type AnalyticsRequest struct {
	BuildingID string                 `json:"building_id"`
	Type       string                 `json:"type"`
	TimeRange  map[string]interface{} `json:"time_range"`
	Metrics    []string               `json:"metrics"`
}

// WorkflowExecutionStatus represents the status of a workflow execution
type WorkflowExecutionStatus struct {
	ExecutionID string                 `json:"execution_id"`
	Status      WorkflowStatus         `json:"status"`
	Progress    float64                `json:"progress"`
	CurrentStep string                 `json:"current_step"`
	LastUpdated time.Time              `json:"last_updated"`
	Metrics     map[string]interface{} `json:"metrics,omitempty"`
	Error       string                 `json:"error,omitempty"`
}

// WorkflowStatus represents the status of a workflow execution
type WorkflowStatus string

const (
	WorkflowStatusPending   WorkflowStatus = "pending"
	WorkflowStatusRunning   WorkflowStatus = "running"
	WorkflowStatusCompleted WorkflowStatus = "completed"
	WorkflowStatusFailed    WorkflowStatus = "failed"
	WorkflowStatusCancelled WorkflowStatus = "cancelled"
)

// Result types

type ImportResult struct {
	ID       string `json:"id"`
	Status   string `json:"status"`
	Message  string `json:"message"`
	Imported int    `json:"imported"`
	Errors   int    `json:"errors"`
}

type ExportResult struct {
	ID     string `json:"id"`
	Status string `json:"status"`
	Data   []byte `json:"data"`
	Format string `json:"format"`
	Size   int64  `json:"size"`
}

type WorkflowResult struct {
	ID         string                 `json:"id"`
	WorkflowID string                 `json:"workflow_id"`
	Status     string                 `json:"status"`
	Output     map[string]interface{} `json:"output"`
	Metadata   map[string]interface{} `json:"metadata"`
	Duration   int64                  `json:"duration_ms"`
	Error      string                 `json:"error,omitempty"`
}

type PurchaseResult struct {
	ID           string `json:"id"`
	Status       string `json:"status"`
	DeviceID     string `json:"device_id"`
	OrderNumber  string `json:"order_number"`
	TrackingInfo string `json:"tracking_info"`
}

type AnalyticsResult struct {
	ID      string                 `json:"id"`
	Type    string                 `json:"type"`
	Data    map[string]interface{} `json:"data"`
	Summary map[string]interface{} `json:"summary"`
}

type PredictiveInsights struct {
	ID         string                   `json:"id"`
	Type       string                   `json:"type"`
	Insights   []map[string]interface{} `json:"insights"`
	Confidence float64                  `json:"confidence"`
}

// Additional types

type DeviceTemplate struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Description string                 `json:"description"`
	Schema      map[string]interface{} `json:"schema"`
	Firmware    []byte                 `json:"firmware"`
}

type Gateway struct {
	ID      string                 `json:"id"`
	Name    string                 `json:"name"`
	Type    string                 `json:"type"`
	Status  string                 `json:"status"`
	Config  map[string]interface{} `json:"config"`
	Devices []string               `json:"devices"`
}

type GatewayConfig struct {
	Protocols []string               `json:"protocols"`
	Settings  map[string]interface{} `json:"settings"`
	Security  map[string]interface{} `json:"security"`
}

type CertifiedDevice struct {
	ID            string  `json:"id"`
	Name          string  `json:"name"`
	Type          string  `json:"type"`
	Price         float64 `json:"price"`
	Certification string  `json:"certification"`
	Description   string  `json:"description"`
}

type PurchaseDeviceRequest struct {
	DeviceID string                 `json:"device_id"`
	Quantity int                    `json:"quantity"`
	Shipping map[string]interface{} `json:"shipping"`
	Payment  map[string]interface{} `json:"payment"`
}

type WorkOrder struct {
	ID          string                 `json:"id"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Priority    string                 `json:"priority"`
	Status      string                 `json:"status"`
	EquipmentID string                 `json:"equipment_id"`
	AssignedTo  string                 `json:"assigned_to"`
	DueDate     string                 `json:"due_date"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type MaintenanceSchedule struct {
	ID       string                   `json:"id"`
	Name     string                   `json:"name"`
	Type     string                   `json:"type"`
	Schedule map[string]interface{}   `json:"schedule"`
	Tasks    []map[string]interface{} `json:"tasks"`
}

type Report struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Data        map[string]interface{} `json:"data"`
	Format      string                 `json:"format"`
	GeneratedAt string                 `json:"generated_at"`
}

type Automation struct {
	ID         string                   `json:"id"`
	Name       string                   `json:"name"`
	Trigger    map[string]interface{}   `json:"trigger"`
	Actions    []map[string]interface{} `json:"actions"`
	Conditions map[string]interface{}   `json:"conditions"`
	Status     string                   `json:"status"`
}

type ScheduleMaintenanceRequest struct {
	Name         string                   `json:"name"`
	Type         string                   `json:"type"`
	Schedule     map[string]interface{}   `json:"schedule"`
	EquipmentIDs []string                 `json:"equipment_ids"`
	Tasks        []map[string]interface{} `json:"tasks"`
}

type GenerateReportRequest struct {
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	BuildingID string                 `json:"building_id"`
	TimeRange  map[string]interface{} `json:"time_range"`
	Format     string                 `json:"format"`
}
