package workflow

import (
	"context"
	"time"
)

// Platform manages the workflow automation ecosystem (Layer 3 - PAID)
type Platform struct {
	workflowManager    WorkflowManager
	cmmcManager        CMMCManager
	automationManager  AutomationManager
	analyticsManager   AnalyticsManager
	integrationManager IntegrationManager
}

// WorkflowManager handles workflow creation and execution
type WorkflowManager interface {
	CreateWorkflow(ctx context.Context, req CreateWorkflowRequest) (*Workflow, error)
	GetWorkflow(ctx context.Context, workflowID string) (*Workflow, error)
	ListWorkflows(ctx context.Context, userID string) ([]*Workflow, error)
	UpdateWorkflow(ctx context.Context, workflowID string, updates WorkflowUpdates) (*Workflow, error)
	DeleteWorkflow(ctx context.Context, workflowID string) error
	ExecuteWorkflow(ctx context.Context, workflowID string, input map[string]interface{}) (*WorkflowResult, error)
	GetWorkflowStatus(ctx context.Context, executionID string) (*WorkflowStatus, error)
	PauseWorkflow(ctx context.Context, workflowID string) error
	ResumeWorkflow(ctx context.Context, workflowID string) error
}

// CMMCManager handles CMMS/CAFM features
type CMMCManager interface {
	CreateWorkOrder(ctx context.Context, req CreateWorkOrderRequest) (*WorkOrder, error)
	GetWorkOrder(ctx context.Context, workOrderID string) (*WorkOrder, error)
	ListWorkOrders(ctx context.Context, userID string, filters WorkOrderFilters) ([]*WorkOrder, error)
	UpdateWorkOrder(ctx context.Context, workOrderID string, updates WorkOrderUpdates) (*WorkOrder, error)
	DeleteWorkOrder(ctx context.Context, workOrderID string) error
	AssignWorkOrder(ctx context.Context, workOrderID string, assigneeID string) error
	CompleteWorkOrder(ctx context.Context, workOrderID string, completion WorkOrderCompletion) error

	CreateMaintenanceSchedule(ctx context.Context, req CreateMaintenanceScheduleRequest) (*MaintenanceSchedule, error)
	GetMaintenanceSchedule(ctx context.Context, scheduleID string) (*MaintenanceSchedule, error)
	ListMaintenanceSchedules(ctx context.Context, userID string) ([]*MaintenanceSchedule, error)
	UpdateMaintenanceSchedule(ctx context.Context, scheduleID string, updates MaintenanceScheduleUpdates) (*MaintenanceSchedule, error)
	DeleteMaintenanceSchedule(ctx context.Context, scheduleID string) error
	ExecuteMaintenanceSchedule(ctx context.Context, scheduleID string) (*MaintenanceExecution, error)

	GenerateReport(ctx context.Context, req GenerateReportRequest) (*Report, error)
	GetReport(ctx context.Context, reportID string) (*Report, error)
	ListReports(ctx context.Context, userID string) ([]*Report, error)
	DeleteReport(ctx context.Context, reportID string) error
}

// AutomationManager handles building automation
type AutomationManager interface {
	CreateAutomation(ctx context.Context, req CreateAutomationRequest) (*Automation, error)
	GetAutomation(ctx context.Context, automationID string) (*Automation, error)
	ListAutomations(ctx context.Context, userID string) ([]*Automation, error)
	UpdateAutomation(ctx context.Context, automationID string, updates AutomationUpdates) (*Automation, error)
	DeleteAutomation(ctx context.Context, automationID string) error
	TriggerAutomation(ctx context.Context, automationID string, trigger map[string]interface{}) error
	GetAutomationStatus(ctx context.Context, automationID string) (*AutomationStatus, error)
	EnableAutomation(ctx context.Context, automationID string) error
	DisableAutomation(ctx context.Context, automationID string) error
}

// AnalyticsManager handles analytics and insights
type AnalyticsManager interface {
	GetAnalytics(ctx context.Context, req AnalyticsRequest) (*AnalyticsResult, error)
	GetPredictiveInsights(ctx context.Context, buildingID string) (*PredictiveInsights, error)
	GetDashboard(ctx context.Context, userID string, dashboardType string) (*Dashboard, error)
	GetEnergyAnalytics(ctx context.Context, req EnergyAnalyticsRequest) (*EnergyAnalytics, error)
	GetMaintenanceAnalytics(ctx context.Context, req MaintenanceAnalyticsRequest) (*MaintenanceAnalytics, error)
	GetOccupancyAnalytics(ctx context.Context, req OccupancyAnalyticsRequest) (*OccupancyAnalytics, error)
	GetComplianceAnalytics(ctx context.Context, req ComplianceAnalyticsRequest) (*ComplianceAnalytics, error)
}

// IntegrationManager handles enterprise integrations
type IntegrationManager interface {
	CreateIntegration(ctx context.Context, req CreateIntegrationRequest) (*Integration, error)
	GetIntegration(ctx context.Context, integrationID string) (*Integration, error)
	ListIntegrations(ctx context.Context, userID string) ([]*Integration, error)
	UpdateIntegration(ctx context.Context, integrationID string, updates IntegrationUpdates) (*Integration, error)
	DeleteIntegration(ctx context.Context, integrationID string) error
	TestIntegration(ctx context.Context, integrationID string) (*IntegrationTest, error)
	SyncIntegration(ctx context.Context, integrationID string) (*IntegrationSync, error)
	GetIntegrationStatus(ctx context.Context, integrationID string) (*IntegrationStatus, error)
}

// NewPlatform creates a new workflow platform
func NewPlatform(
	workflowManager WorkflowManager,
	cmmcManager CMMCManager,
	automationManager AutomationManager,
	analyticsManager AnalyticsManager,
	integrationManager IntegrationManager,
) *Platform {
	return &Platform{
		workflowManager:    workflowManager,
		cmmcManager:        cmmcManager,
		automationManager:  automationManager,
		analyticsManager:   analyticsManager,
		integrationManager: integrationManager,
	}
}

// Workflow management methods
func (p *Platform) CreateWorkflow(ctx context.Context, req CreateWorkflowRequest) (*Workflow, error) {
	return p.workflowManager.CreateWorkflow(ctx, req)
}

func (p *Platform) GetWorkflow(ctx context.Context, workflowID string) (*Workflow, error) {
	return p.workflowManager.GetWorkflow(ctx, workflowID)
}

func (p *Platform) ListWorkflows(ctx context.Context, userID string) ([]*Workflow, error) {
	return p.workflowManager.ListWorkflows(ctx, userID)
}

func (p *Platform) UpdateWorkflow(ctx context.Context, workflowID string, updates WorkflowUpdates) (*Workflow, error) {
	return p.workflowManager.UpdateWorkflow(ctx, workflowID, updates)
}

func (p *Platform) DeleteWorkflow(ctx context.Context, workflowID string) error {
	return p.workflowManager.DeleteWorkflow(ctx, workflowID)
}

func (p *Platform) ExecuteWorkflow(ctx context.Context, workflowID string, input map[string]interface{}) (*WorkflowResult, error) {
	return p.workflowManager.ExecuteWorkflow(ctx, workflowID, input)
}

func (p *Platform) GetWorkflowStatus(ctx context.Context, executionID string) (*WorkflowStatus, error) {
	return p.workflowManager.GetWorkflowStatus(ctx, executionID)
}

func (p *Platform) PauseWorkflow(ctx context.Context, workflowID string) error {
	return p.workflowManager.PauseWorkflow(ctx, workflowID)
}

func (p *Platform) ResumeWorkflow(ctx context.Context, workflowID string) error {
	return p.workflowManager.ResumeWorkflow(ctx, workflowID)
}

// CMMC management methods
func (p *Platform) CreateWorkOrder(ctx context.Context, req CreateWorkOrderRequest) (*WorkOrder, error) {
	return p.cmmcManager.CreateWorkOrder(ctx, req)
}

func (p *Platform) GetWorkOrder(ctx context.Context, workOrderID string) (*WorkOrder, error) {
	return p.cmmcManager.GetWorkOrder(ctx, workOrderID)
}

func (p *Platform) ListWorkOrders(ctx context.Context, userID string, filters WorkOrderFilters) ([]*WorkOrder, error) {
	return p.cmmcManager.ListWorkOrders(ctx, userID, filters)
}

func (p *Platform) UpdateWorkOrder(ctx context.Context, workOrderID string, updates WorkOrderUpdates) (*WorkOrder, error) {
	return p.cmmcManager.UpdateWorkOrder(ctx, workOrderID, updates)
}

func (p *Platform) DeleteWorkOrder(ctx context.Context, workOrderID string) error {
	return p.cmmcManager.DeleteWorkOrder(ctx, workOrderID)
}

func (p *Platform) AssignWorkOrder(ctx context.Context, workOrderID string, assigneeID string) error {
	return p.cmmcManager.AssignWorkOrder(ctx, workOrderID, assigneeID)
}

func (p *Platform) CompleteWorkOrder(ctx context.Context, workOrderID string, completion WorkOrderCompletion) error {
	return p.cmmcManager.CompleteWorkOrder(ctx, workOrderID, completion)
}

func (p *Platform) CreateMaintenanceSchedule(ctx context.Context, req CreateMaintenanceScheduleRequest) (*MaintenanceSchedule, error) {
	return p.cmmcManager.CreateMaintenanceSchedule(ctx, req)
}

func (p *Platform) GetMaintenanceSchedule(ctx context.Context, scheduleID string) (*MaintenanceSchedule, error) {
	return p.cmmcManager.GetMaintenanceSchedule(ctx, scheduleID)
}

func (p *Platform) ListMaintenanceSchedules(ctx context.Context, userID string) ([]*MaintenanceSchedule, error) {
	return p.cmmcManager.ListMaintenanceSchedules(ctx, userID)
}

func (p *Platform) UpdateMaintenanceSchedule(ctx context.Context, scheduleID string, updates MaintenanceScheduleUpdates) (*MaintenanceSchedule, error) {
	return p.cmmcManager.UpdateMaintenanceSchedule(ctx, scheduleID, updates)
}

func (p *Platform) DeleteMaintenanceSchedule(ctx context.Context, scheduleID string) error {
	return p.cmmcManager.DeleteMaintenanceSchedule(ctx, scheduleID)
}

func (p *Platform) ExecuteMaintenanceSchedule(ctx context.Context, scheduleID string) (*MaintenanceExecution, error) {
	return p.cmmcManager.ExecuteMaintenanceSchedule(ctx, scheduleID)
}

func (p *Platform) GenerateReport(ctx context.Context, req GenerateReportRequest) (*Report, error) {
	return p.cmmcManager.GenerateReport(ctx, req)
}

func (p *Platform) GetReport(ctx context.Context, reportID string) (*Report, error) {
	return p.cmmcManager.GetReport(ctx, reportID)
}

func (p *Platform) ListReports(ctx context.Context, userID string) ([]*Report, error) {
	return p.cmmcManager.ListReports(ctx, userID)
}

func (p *Platform) DeleteReport(ctx context.Context, reportID string) error {
	return p.cmmcManager.DeleteReport(ctx, reportID)
}

// Automation management methods
func (p *Platform) CreateAutomation(ctx context.Context, req CreateAutomationRequest) (*Automation, error) {
	return p.automationManager.CreateAutomation(ctx, req)
}

func (p *Platform) GetAutomation(ctx context.Context, automationID string) (*Automation, error) {
	return p.automationManager.GetAutomation(ctx, automationID)
}

func (p *Platform) ListAutomations(ctx context.Context, userID string) ([]*Automation, error) {
	return p.automationManager.ListAutomations(ctx, userID)
}

func (p *Platform) UpdateAutomation(ctx context.Context, automationID string, updates AutomationUpdates) (*Automation, error) {
	return p.automationManager.UpdateAutomation(ctx, automationID, updates)
}

func (p *Platform) DeleteAutomation(ctx context.Context, automationID string) error {
	return p.automationManager.DeleteAutomation(ctx, automationID)
}

func (p *Platform) TriggerAutomation(ctx context.Context, automationID string, trigger map[string]interface{}) error {
	return p.automationManager.TriggerAutomation(ctx, automationID, trigger)
}

func (p *Platform) GetAutomationStatus(ctx context.Context, automationID string) (*AutomationStatus, error) {
	return p.automationManager.GetAutomationStatus(ctx, automationID)
}

func (p *Platform) EnableAutomation(ctx context.Context, automationID string) error {
	return p.automationManager.EnableAutomation(ctx, automationID)
}

func (p *Platform) DisableAutomation(ctx context.Context, automationID string) error {
	return p.automationManager.DisableAutomation(ctx, automationID)
}

// Analytics methods
func (p *Platform) GetAnalytics(ctx context.Context, req AnalyticsRequest) (*AnalyticsResult, error) {
	return p.analyticsManager.GetAnalytics(ctx, req)
}

func (p *Platform) GetPredictiveInsights(ctx context.Context, buildingID string) (*PredictiveInsights, error) {
	return p.analyticsManager.GetPredictiveInsights(ctx, buildingID)
}

func (p *Platform) GetDashboard(ctx context.Context, userID string, dashboardType string) (*Dashboard, error) {
	return p.analyticsManager.GetDashboard(ctx, userID, dashboardType)
}

func (p *Platform) GetEnergyAnalytics(ctx context.Context, req EnergyAnalyticsRequest) (*EnergyAnalytics, error) {
	return p.analyticsManager.GetEnergyAnalytics(ctx, req)
}

func (p *Platform) GetMaintenanceAnalytics(ctx context.Context, req MaintenanceAnalyticsRequest) (*MaintenanceAnalytics, error) {
	return p.analyticsManager.GetMaintenanceAnalytics(ctx, req)
}

func (p *Platform) GetOccupancyAnalytics(ctx context.Context, req OccupancyAnalyticsRequest) (*OccupancyAnalytics, error) {
	return p.analyticsManager.GetOccupancyAnalytics(ctx, req)
}

func (p *Platform) GetComplianceAnalytics(ctx context.Context, req ComplianceAnalyticsRequest) (*ComplianceAnalytics, error) {
	return p.analyticsManager.GetComplianceAnalytics(ctx, req)
}

// Integration methods
func (p *Platform) CreateIntegration(ctx context.Context, req CreateIntegrationRequest) (*Integration, error) {
	return p.integrationManager.CreateIntegration(ctx, req)
}

func (p *Platform) GetIntegration(ctx context.Context, integrationID string) (*Integration, error) {
	return p.integrationManager.GetIntegration(ctx, integrationID)
}

func (p *Platform) ListIntegrations(ctx context.Context, userID string) ([]*Integration, error) {
	return p.integrationManager.ListIntegrations(ctx, userID)
}

func (p *Platform) UpdateIntegration(ctx context.Context, integrationID string, updates IntegrationUpdates) (*Integration, error) {
	return p.integrationManager.UpdateIntegration(ctx, integrationID, updates)
}

func (p *Platform) DeleteIntegration(ctx context.Context, integrationID string) error {
	return p.integrationManager.DeleteIntegration(ctx, integrationID)
}

func (p *Platform) TestIntegration(ctx context.Context, integrationID string) (*IntegrationTest, error) {
	return p.integrationManager.TestIntegration(ctx, integrationID)
}

func (p *Platform) SyncIntegration(ctx context.Context, integrationID string) (*IntegrationSync, error) {
	return p.integrationManager.SyncIntegration(ctx, integrationID)
}

func (p *Platform) GetIntegrationStatus(ctx context.Context, integrationID string) (*IntegrationStatus, error) {
	return p.integrationManager.GetIntegrationStatus(ctx, integrationID)
}

// Data structures

type Workflow struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Definition  map[string]interface{} `json:"definition"`
	Status      string                 `json:"status"`
	Version     string                 `json:"version"`
	UserID      string                 `json:"user_id"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

type WorkflowResult struct {
	ID          string                 `json:"id"`
	WorkflowID  string                 `json:"workflow_id"`
	Status      string                 `json:"status"`
	Output      map[string]interface{} `json:"output"`
	Duration    int64                  `json:"duration_ms"`
	Error       string                 `json:"error,omitempty"`
	StartedAt   time.Time              `json:"started_at"`
	CompletedAt *time.Time             `json:"completed_at,omitempty"`
}

type WorkflowStatus struct {
	ExecutionID string                 `json:"execution_id"`
	Status      string                 `json:"status"`
	Progress    int                    `json:"progress"`
	CurrentStep string                 `json:"current_step"`
	Metrics     map[string]interface{} `json:"metrics"`
	LastUpdated time.Time              `json:"last_updated"`
}

type WorkOrder struct {
	ID          string                 `json:"id"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Priority    string                 `json:"priority"`
	Status      string                 `json:"status"`
	EquipmentID string                 `json:"equipment_id"`
	AssignedTo  string                 `json:"assigned_to"`
	DueDate     time.Time              `json:"due_date"`
	CompletedAt *time.Time             `json:"completed_at,omitempty"`
	Metadata    map[string]interface{} `json:"metadata"`
	UserID      string                 `json:"user_id"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

type MaintenanceSchedule struct {
	ID        string                 `json:"id"`
	Name      string                 `json:"name"`
	Type      string                 `json:"type"`
	Schedule  map[string]interface{} `json:"schedule"`
	Tasks     []MaintenanceTask      `json:"tasks"`
	Status    string                 `json:"status"`
	UserID    string                 `json:"user_id"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

type MaintenanceTask struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	Type         string                 `json:"type"`
	EquipmentID  string                 `json:"equipment_id"`
	Duration     int                    `json:"duration_minutes"`
	Frequency    string                 `json:"frequency"`
	Instructions []string               `json:"instructions"`
	Metadata     map[string]interface{} `json:"metadata"`
}

type MaintenanceExecution struct {
	ID          string                 `json:"id"`
	ScheduleID  string                 `json:"schedule_id"`
	Status      string                 `json:"status"`
	StartedAt   time.Time              `json:"started_at"`
	CompletedAt *time.Time             `json:"completed_at,omitempty"`
	Tasks       []TaskExecution        `json:"tasks"`
	Results     map[string]interface{} `json:"results"`
}

type TaskExecution struct {
	TaskID      string                 `json:"task_id"`
	Status      string                 `json:"status"`
	StartedAt   time.Time              `json:"started_at"`
	CompletedAt *time.Time             `json:"completed_at,omitempty"`
	Results     map[string]interface{} `json:"results"`
	Notes       string                 `json:"notes"`
}

type Report struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Data        map[string]interface{} `json:"data"`
	Format      string                 `json:"format"`
	GeneratedAt time.Time              `json:"generated_at"`
	UserID      string                 `json:"user_id"`
	Size        int64                  `json:"size"`
}

type Automation struct {
	ID         string                `json:"id"`
	Name       string                `json:"name"`
	Trigger    AutomationTrigger     `json:"trigger"`
	Actions    []AutomationAction    `json:"actions"`
	Conditions []AutomationCondition `json:"conditions"`
	Status     string                `json:"status"`
	UserID     string                `json:"user_id"`
	CreatedAt  time.Time             `json:"created_at"`
	UpdatedAt  time.Time             `json:"updated_at"`
}

type AutomationTrigger struct {
	Type       string                 `json:"type"`
	Event      string                 `json:"event"`
	Schedule   string                 `json:"schedule,omitempty"`
	Conditions map[string]interface{} `json:"conditions"`
}

type AutomationAction struct {
	Type       string                 `json:"type"`
	Target     string                 `json:"target"`
	Parameters map[string]interface{} `json:"parameters"`
}

type AutomationCondition struct {
	Field    string      `json:"field"`
	Operator string      `json:"operator"`
	Value    interface{} `json:"value"`
}

type AutomationStatus struct {
	AutomationID  string     `json:"automation_id"`
	Status        string     `json:"status"`
	LastTriggered time.Time  `json:"last_triggered"`
	TriggerCount  int        `json:"trigger_count"`
	SuccessCount  int        `json:"success_count"`
	ErrorCount    int        `json:"error_count"`
	LastError     string     `json:"last_error,omitempty"`
	NextSchedule  *time.Time `json:"next_schedule,omitempty"`
}

type AnalyticsResult struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Data        map[string]interface{} `json:"data"`
	Summary     map[string]interface{} `json:"summary"`
	GeneratedAt time.Time              `json:"generated_at"`
}

type PredictiveInsights struct {
	ID          string              `json:"id"`
	Type        string              `json:"type"`
	Insights    []PredictiveInsight `json:"insights"`
	Confidence  float64             `json:"confidence"`
	GeneratedAt time.Time           `json:"generated_at"`
}

type PredictiveInsight struct {
	Type           string                 `json:"type"`
	Description    string                 `json:"description"`
	Confidence     float64                `json:"confidence"`
	Impact         string                 `json:"impact"`
	Recommendation string                 `json:"recommendation"`
	Timeframe      string                 `json:"timeframe"`
	Metadata       map[string]interface{} `json:"metadata"`
}

type Dashboard struct {
	ID        string                 `json:"id"`
	Name      string                 `json:"name"`
	Type      string                 `json:"type"`
	Widgets   []DashboardWidget      `json:"widgets"`
	Layout    map[string]interface{} `json:"layout"`
	UserID    string                 `json:"user_id"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

type DashboardWidget struct {
	ID       string                 `json:"id"`
	Type     string                 `json:"type"`
	Title    string                 `json:"title"`
	Config   map[string]interface{} `json:"config"`
	Position map[string]interface{} `json:"position"`
	Size     map[string]interface{} `json:"size"`
}

type EnergyAnalytics struct {
	ID          string                 `json:"id"`
	BuildingID  string                 `json:"building_id"`
	Consumption map[string]interface{} `json:"consumption"`
	Efficiency  map[string]interface{} `json:"efficiency"`
	Costs       map[string]interface{} `json:"costs"`
	Trends      []TrendData            `json:"trends"`
	GeneratedAt time.Time              `json:"generated_at"`
}

type MaintenanceAnalytics struct {
	ID          string                 `json:"id"`
	BuildingID  string                 `json:"building_id"`
	WorkOrders  map[string]interface{} `json:"work_orders"`
	Schedules   map[string]interface{} `json:"schedules"`
	Efficiency  map[string]interface{} `json:"efficiency"`
	Costs       map[string]interface{} `json:"costs"`
	Trends      []TrendData            `json:"trends"`
	GeneratedAt time.Time              `json:"generated_at"`
}

type OccupancyAnalytics struct {
	ID          string                 `json:"id"`
	BuildingID  string                 `json:"building_id"`
	Occupancy   map[string]interface{} `json:"occupancy"`
	Patterns    map[string]interface{} `json:"patterns"`
	Efficiency  map[string]interface{} `json:"efficiency"`
	Trends      []TrendData            `json:"trends"`
	GeneratedAt time.Time              `json:"generated_at"`
}

type ComplianceAnalytics struct {
	ID          string                 `json:"id"`
	BuildingID  string                 `json:"building_id"`
	Compliance  map[string]interface{} `json:"compliance"`
	Violations  map[string]interface{} `json:"violations"`
	Remediation map[string]interface{} `json:"remediation"`
	Trends      []TrendData            `json:"trends"`
	GeneratedAt time.Time              `json:"generated_at"`
}

type TrendData struct {
	Date     time.Time              `json:"date"`
	Value    float64                `json:"value"`
	Unit     string                 `json:"unit"`
	Metadata map[string]interface{} `json:"metadata"`
}

type Integration struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Status      string                 `json:"status"`
	Config      map[string]interface{} `json:"config"`
	Credentials map[string]interface{} `json:"credentials"`
	UserID      string                 `json:"user_id"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

type IntegrationTest struct {
	ID            string                 `json:"id"`
	IntegrationID string                 `json:"integration_id"`
	Status        string                 `json:"status"`
	Results       map[string]interface{} `json:"results"`
	Error         string                 `json:"error,omitempty"`
	TestedAt      time.Time              `json:"tested_at"`
}

type IntegrationSync struct {
	ID            string                 `json:"id"`
	IntegrationID string                 `json:"integration_id"`
	Status        string                 `json:"status"`
	SyncedAt      time.Time              `json:"synced_at"`
	Records       map[string]interface{} `json:"records"`
	Error         string                 `json:"error,omitempty"`
}

type IntegrationStatus struct {
	IntegrationID string     `json:"integration_id"`
	Status        string     `json:"status"`
	LastSync      time.Time  `json:"last_sync"`
	SyncCount     int        `json:"sync_count"`
	ErrorCount    int        `json:"error_count"`
	LastError     string     `json:"last_error,omitempty"`
	NextSync      *time.Time `json:"next_sync,omitempty"`
}

// Request types

type CreateWorkflowRequest struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Definition  map[string]interface{} `json:"definition"`
}

type WorkflowUpdates struct {
	Name        *string                `json:"name,omitempty"`
	Description *string                `json:"description,omitempty"`
	Definition  map[string]interface{} `json:"definition,omitempty"`
	Status      *string                `json:"status,omitempty"`
}

type CreateWorkOrderRequest struct {
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Priority    string                 `json:"priority"`
	EquipmentID string                 `json:"equipment_id"`
	DueDate     time.Time              `json:"due_date"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type WorkOrderFilters struct {
	Status      string                 `json:"status,omitempty"`
	Priority    string                 `json:"priority,omitempty"`
	EquipmentID string                 `json:"equipment_id,omitempty"`
	AssignedTo  string                 `json:"assigned_to,omitempty"`
	DateRange   map[string]interface{} `json:"date_range,omitempty"`
}

type WorkOrderUpdates struct {
	Title       *string                `json:"title,omitempty"`
	Description *string                `json:"description,omitempty"`
	Priority    *string                `json:"priority,omitempty"`
	Status      *string                `json:"status,omitempty"`
	AssignedTo  *string                `json:"assigned_to,omitempty"`
	DueDate     *time.Time             `json:"due_date,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

type WorkOrderCompletion struct {
	Notes       string                 `json:"notes"`
	Results     map[string]interface{} `json:"results"`
	CompletedAt time.Time              `json:"completed_at"`
}

type CreateMaintenanceScheduleRequest struct {
	Name         string                 `json:"name"`
	Type         string                 `json:"type"`
	Schedule     map[string]interface{} `json:"schedule"`
	EquipmentIDs []string               `json:"equipment_ids"`
	Tasks        []MaintenanceTask      `json:"tasks"`
}

type MaintenanceScheduleUpdates struct {
	Name         *string                `json:"name,omitempty"`
	Type         *string                `json:"type,omitempty"`
	Schedule     map[string]interface{} `json:"schedule,omitempty"`
	EquipmentIDs []string               `json:"equipment_ids,omitempty"`
	Tasks        []MaintenanceTask      `json:"tasks,omitempty"`
	Status       *string                `json:"status,omitempty"`
}

type GenerateReportRequest struct {
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	BuildingID string                 `json:"building_id"`
	TimeRange  map[string]interface{} `json:"time_range"`
	Format     string                 `json:"format"`
	Parameters map[string]interface{} `json:"parameters"`
}

type CreateAutomationRequest struct {
	Name       string                `json:"name"`
	Trigger    AutomationTrigger     `json:"trigger"`
	Actions    []AutomationAction    `json:"actions"`
	Conditions []AutomationCondition `json:"conditions"`
}

type AutomationUpdates struct {
	Name       *string               `json:"name,omitempty"`
	Trigger    *AutomationTrigger    `json:"trigger,omitempty"`
	Actions    []AutomationAction    `json:"actions,omitempty"`
	Conditions []AutomationCondition `json:"conditions,omitempty"`
	Status     *string               `json:"status,omitempty"`
}

type AnalyticsRequest struct {
	BuildingID string                 `json:"building_id"`
	Type       string                 `json:"type"`
	TimeRange  map[string]interface{} `json:"time_range"`
	Metrics    []string               `json:"metrics"`
	Filters    map[string]interface{} `json:"filters"`
}

type EnergyAnalyticsRequest struct {
	BuildingID string                 `json:"building_id"`
	TimeRange  map[string]interface{} `json:"time_range"`
	Metrics    []string               `json:"metrics"`
	Filters    map[string]interface{} `json:"filters"`
}

type MaintenanceAnalyticsRequest struct {
	BuildingID string                 `json:"building_id"`
	TimeRange  map[string]interface{} `json:"time_range"`
	Metrics    []string               `json:"metrics"`
	Filters    map[string]interface{} `json:"filters"`
}

type OccupancyAnalyticsRequest struct {
	BuildingID string                 `json:"building_id"`
	TimeRange  map[string]interface{} `json:"time_range"`
	Metrics    []string               `json:"metrics"`
	Filters    map[string]interface{} `json:"filters"`
}

type ComplianceAnalyticsRequest struct {
	BuildingID string                 `json:"building_id"`
	TimeRange  map[string]interface{} `json:"time_range"`
	Standards  []string               `json:"standards"`
	Filters    map[string]interface{} `json:"filters"`
}

type CreateIntegrationRequest struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Config      map[string]interface{} `json:"config"`
	Credentials map[string]interface{} `json:"credentials"`
}

type IntegrationUpdates struct {
	Name        *string                `json:"name,omitempty"`
	Type        *string                `json:"type,omitempty"`
	Config      map[string]interface{} `json:"config,omitempty"`
	Credentials map[string]interface{} `json:"credentials,omitempty"`
	Status      *string                `json:"status,omitempty"`
}

// Workflow platform factory
type PlatformFactory struct {
	workflowManager    WorkflowManager
	cmmcManager        CMMCManager
	automationManager  AutomationManager
	analyticsManager   AnalyticsManager
	integrationManager IntegrationManager
}

// NewPlatformFactory creates a new workflow platform factory
func NewPlatformFactory(
	workflowManager WorkflowManager,
	cmmcManager CMMCManager,
	automationManager AutomationManager,
	analyticsManager AnalyticsManager,
	integrationManager IntegrationManager,
) *PlatformFactory {
	return &PlatformFactory{
		workflowManager:    workflowManager,
		cmmcManager:        cmmcManager,
		automationManager:  automationManager,
		analyticsManager:   analyticsManager,
		integrationManager: integrationManager,
	}
}

// CreatePlatform creates a new workflow platform instance
func (pf *PlatformFactory) CreatePlatform() *Platform {
	return NewPlatform(
		pf.workflowManager,
		pf.cmmcManager,
		pf.automationManager,
		pf.analyticsManager,
		pf.integrationManager,
	)
}
