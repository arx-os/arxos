package cmms

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/google/uuid"
)

// CMMSConnection represents a connection to a CMMS system
type CMMSConnection struct {
	ID             uuid.UUID `json:"id"`
	CMMSType       string    `json:"cmms_type"`
	APIURL         string    `json:"api_url"`
	APIKey         string    `json:"api_key"`
	Username       *string   `json:"username,omitempty"`
	Password       *string   `json:"password,omitempty"`
	ConnectionName string    `json:"connection_name"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

// FieldMapping represents a field mapping for data transformation
type FieldMapping struct {
	ID                 uuid.UUID `json:"id"`
	CMMSConnectionID   uuid.UUID `json:"cmms_connection_id"`
	SourceField        string    `json:"source_field"`
	TargetField        string    `json:"target_field"`
	TransformationRule *string   `json:"transformation_rule,omitempty"`
	IsRequired         bool      `json:"is_required"`
	CreatedAt          time.Time `json:"created_at"`
}

// SyncResult represents the result of a data synchronization operation
type SyncResult struct {
	SyncedCount int      `json:"synced_count"`
	Errors      []string `json:"errors"`
	Message     string   `json:"message"`
}

// WorkOrder represents a work order
type WorkOrder struct {
	ID              uuid.UUID  `json:"id"`
	WorkOrderNumber string     `json:"work_order_number"`
	AssetID         string     `json:"asset_id"`
	Title           string     `json:"title"`
	Description     string     `json:"description"`
	Status          string     `json:"status"`
	Priority        string     `json:"priority"`
	EstimatedHours  float64    `json:"estimated_hours"`
	ActualHours     *float64   `json:"actual_hours,omitempty"`
	EstimatedCost   float64    `json:"estimated_cost"`
	ActualCost      *float64   `json:"actual_cost,omitempty"`
	AssignedTo      *string    `json:"assigned_to,omitempty"`
	ScheduledStart  *time.Time `json:"scheduled_start,omitempty"`
	ScheduledEnd    *time.Time `json:"scheduled_end,omitempty"`
	ActualStart     *time.Time `json:"actual_start,omitempty"`
	ActualEnd       *time.Time `json:"actual_end,omitempty"`
	CreatedAt       time.Time  `json:"created_at"`
	UpdatedAt       time.Time  `json:"updated_at"`
}

// MaintenanceSchedule represents a maintenance schedule
type MaintenanceSchedule struct {
	ID                uuid.UUID   `json:"id"`
	Name              string      `json:"name"`
	Description       string      `json:"description"`
	MaintenanceType   string      `json:"maintenance_type"`
	Priority          string      `json:"priority"`
	Frequency         string      `json:"frequency"`
	TriggerType       string      `json:"trigger_type"`
	TriggerValue      interface{} `json:"trigger_value"`
	EstimatedDuration int         `json:"estimated_duration"`
	EstimatedCost     float64     `json:"estimated_cost"`
	RequiredSkills    []string    `json:"required_skills"`
	RequiredTools     []string    `json:"required_tools"`
	RequiredParts     []string    `json:"required_parts"`
	IsActive          bool        `json:"is_active"`
	CreatedAt         time.Time   `json:"created_at"`
	UpdatedAt         time.Time   `json:"updated_at"`
	LastExecuted      *time.Time  `json:"last_executed,omitempty"`
	NextScheduled     *time.Time  `json:"next_scheduled,omitempty"`
}

// MaintenanceTask represents a maintenance task
type MaintenanceTask struct {
	ID                uuid.UUID  `json:"id"`
	ScheduleID        uuid.UUID  `json:"schedule_id"`
	AssetID           string     `json:"asset_id"`
	Status            string     `json:"status"`
	Priority          string     `json:"priority"`
	ScheduledStart    time.Time  `json:"scheduled_start"`
	ScheduledEnd      time.Time  `json:"scheduled_end"`
	ActualStart       *time.Time `json:"actual_start,omitempty"`
	ActualEnd         *time.Time `json:"actual_end,omitempty"`
	EstimatedDuration int        `json:"estimated_duration"`
	ActualDuration    *int       `json:"actual_duration,omitempty"`
	EstimatedCost     float64    `json:"estimated_cost"`
	ActualCost        *float64   `json:"actual_cost,omitempty"`
	AssignedTo        *string    `json:"assigned_to,omitempty"`
	AssignedTeam      *string    `json:"assigned_team,omitempty"`
	Location          *string    `json:"location,omitempty"`
	Notes             *string    `json:"notes,omitempty"`
	CreatedAt         time.Time  `json:"created_at"`
	UpdatedAt         time.Time  `json:"updated_at"`
}

// Asset represents an asset
type Asset struct {
	ID                  string                 `json:"id"`
	Name                string                 `json:"name"`
	Description         *string                `json:"description,omitempty"`
	AssetType           string                 `json:"asset_type"`
	Status              string                 `json:"status"`
	Manufacturer        *string                `json:"manufacturer,omitempty"`
	Model               *string                `json:"model,omitempty"`
	SerialNumber        *string                `json:"serial_number,omitempty"`
	InstallationDate    *time.Time             `json:"installation_date,omitempty"`
	WarrantyExpiry      *time.Time             `json:"warranty_expiry,omitempty"`
	ExpectedLifespan    *int                   `json:"expected_lifespan,omitempty"`
	CurrentLocation     *AssetLocation         `json:"current_location,omitempty"`
	CurrentCondition    *AssetCondition        `json:"current_condition,omitempty"`
	LastMaintenance     *time.Time             `json:"last_maintenance,omitempty"`
	NextMaintenance     *time.Time             `json:"next_maintenance,omitempty"`
	TotalOperatingHours *float64               `json:"total_operating_hours,omitempty"`
	TotalCost           *float64               `json:"total_cost,omitempty"`
	Department          *string                `json:"department,omitempty"`
	ResponsiblePerson   *string                `json:"responsible_person,omitempty"`
	Tags                []string               `json:"tags"`
	Specifications      map[string]interface{} `json:"specifications"`
	CreatedAt           time.Time              `json:"created_at"`
	UpdatedAt           time.Time              `json:"updated_at"`
}

// AssetLocation represents asset location information
type AssetLocation struct {
	ID           uuid.UUID   `json:"id"`
	AssetID      string      `json:"asset_id"`
	LocationName string      `json:"location_name"`
	Building     *string     `json:"building,omitempty"`
	Floor        *string     `json:"floor,omitempty"`
	Room         *string     `json:"room,omitempty"`
	Coordinates  *[2]float64 `json:"coordinates,omitempty"`
	Address      *string     `json:"address,omitempty"`
	Zone         *string     `json:"zone,omitempty"`
	Department   *string     `json:"department,omitempty"`
	Timestamp    time.Time   `json:"timestamp"`
	UpdatedBy    *string     `json:"updated_by,omitempty"`
}

// AssetCondition represents asset condition assessment
type AssetCondition struct {
	ID                 uuid.UUID              `json:"id"`
	AssetID            string                 `json:"asset_id"`
	Condition          string                 `json:"condition"`
	AssessmentDate     time.Time              `json:"assessment_date"`
	AssessedBy         string                 `json:"assessed_by"`
	Notes              *string                `json:"notes,omitempty"`
	VisualInspection   *string                `json:"visual_inspection,omitempty"`
	FunctionalTest     *string                `json:"functional_test,omitempty"`
	PerformanceMetrics map[string]interface{} `json:"performance_metrics"`
	Recommendations    *string                `json:"recommendations,omitempty"`
	NextAssessmentDate *time.Time             `json:"next_assessment_date,omitempty"`
}

// AssetPerformance represents asset performance metrics
type AssetPerformance struct {
	ID                uuid.UUID `json:"id"`
	AssetID           string    `json:"asset_id"`
	Timestamp         time.Time `json:"timestamp"`
	UptimePercentage  float64   `json:"uptime_percentage"`
	EfficiencyRating  float64   `json:"efficiency_rating"`
	Throughput        *float64  `json:"throughput,omitempty"`
	EnergyConsumption *float64  `json:"energy_consumption,omitempty"`
	Temperature       *float64  `json:"temperature,omitempty"`
	Vibration         *float64  `json:"vibration,omitempty"`
	Pressure          *float64  `json:"pressure,omitempty"`
	Speed             *float64  `json:"speed,omitempty"`
	LoadPercentage    *float64  `json:"load_percentage,omitempty"`
	ErrorCount        int       `json:"error_count"`
	WarningCount      int       `json:"warning_count"`
	MaintenanceHours  *float64  `json:"maintenance_hours,omitempty"`
	CostPerHour       *float64  `json:"cost_per_hour,omitempty"`
}

// AssetAlert represents an asset alert
type AssetAlert struct {
	ID              uuid.UUID  `json:"id"`
	AssetID         string     `json:"asset_id"`
	AlertType       string     `json:"alert_type"`
	Severity        string     `json:"severity"`
	Message         string     `json:"message"`
	Timestamp       time.Time  `json:"timestamp"`
	IsAcknowledged  bool       `json:"is_acknowledged"`
	AcknowledgedBy  *string    `json:"acknowledged_by,omitempty"`
	AcknowledgedAt  *time.Time `json:"acknowledged_at,omitempty"`
	IsResolved      bool       `json:"is_resolved"`
	ResolvedBy      *string    `json:"resolved_by,omitempty"`
	ResolvedAt      *time.Time `json:"resolved_at,omitempty"`
	ResolutionNotes *string    `json:"resolution_notes,omitempty"`
}

// CMMSService provides methods to interact with CMMS services
type CMMSService struct {
	baseURL    string
	httpClient *http.Client
}

// NewCMMSService creates a new CMMS service client
func NewCMMSService(baseURL string) *CMMSService {
	return &CMMSService{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// AddCMMSConnection adds a new CMMS connection
func (s *CMMSService) AddCMMSConnection(connection CMMSConnection) (*CMMSConnection, error) {
	jsonData, err := json.Marshal(connection)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal connection: %w", err)
	}

	resp, err := s.httpClient.Post(s.baseURL+"/cmms/connections", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to add CMMS connection: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to add CMMS connection: status %d", resp.StatusCode)
	}

	var result struct {
		Success      bool   `json:"success"`
		ConnectionID string `json:"connection_id"`
		Message      string `json:"message"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("failed to add CMMS connection: %s", result.Message)
	}

	connection.ID, _ = uuid.Parse(result.ConnectionID)
	return &connection, nil
}

// SyncWorkOrders synchronizes work orders from CMMS
func (s *CMMSService) SyncWorkOrders(connectionID uuid.UUID, forceSync bool) (*SyncResult, error) {
	request := struct {
		CMMSConnectionID uuid.UUID `json:"cmms_connection_id"`
		SyncType         string    `json:"sync_type"`
		ForceSync        bool      `json:"force_sync"`
	}{
		CMMSConnectionID: connectionID,
		SyncType:         "work_orders",
		ForceSync:        forceSync,
	}

	jsonData, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := s.httpClient.Post(s.baseURL+"/cmms/sync/work-orders", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to sync work orders: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to sync work orders: status %d", resp.StatusCode)
	}

	var result struct {
		Success     bool     `json:"success"`
		SyncedCount int      `json:"synced_count"`
		Errors      []string `json:"errors"`
		Message     string   `json:"message"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("failed to sync work orders: %s", result.Message)
	}

	return &SyncResult{
		SyncedCount: result.SyncedCount,
		Errors:      result.Errors,
		Message:     result.Message,
	}, nil
}

// CreateWorkOrder creates a new work order
func (s *CMMSService) CreateWorkOrder(workOrder WorkOrder) (*WorkOrder, error) {
	jsonData, err := json.Marshal(workOrder)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal work order: %w", err)
	}

	resp, err := s.httpClient.Post(s.baseURL+"/work-orders", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create work order: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to create work order: status %d", resp.StatusCode)
	}

	var result struct {
		Success         bool   `json:"success"`
		WorkOrderID     string `json:"work_order_id"`
		WorkOrderNumber string `json:"work_order_number"`
		Message         string `json:"message"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("failed to create work order: %s", result.Message)
	}

	workOrder.ID, _ = uuid.Parse(result.WorkOrderID)
	workOrder.WorkOrderNumber = result.WorkOrderNumber
	return &workOrder, nil
}

// GetWorkOrders retrieves work orders with optional filters
func (s *CMMSService) GetWorkOrders(status, assetID, assignedTo *string) ([]WorkOrder, error) {
	url := s.baseURL + "/work-orders"
	if status != nil || assetID != nil || assignedTo != nil {
		url += "?"
		params := make([]string, 0)
		if status != nil {
			params = append(params, fmt.Sprintf("status=%s", *status))
		}
		if assetID != nil {
			params = append(params, fmt.Sprintf("asset_id=%s", *assetID))
		}
		if assignedTo != nil {
			params = append(params, fmt.Sprintf("assigned_to=%s", *assignedTo))
		}
		url += fmt.Sprintf("%s", params[0])
		for i := 1; i < len(params); i++ {
			url += "&" + params[i]
		}
	}

	resp, err := s.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to get work orders: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get work orders: status %d", resp.StatusCode)
	}

	var result struct {
		Success    bool        `json:"success"`
		WorkOrders []WorkOrder `json:"work_orders"`
		Count      int         `json:"count"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("failed to get work orders")
	}

	return result.WorkOrders, nil
}

// CreateMaintenanceSchedule creates a new maintenance schedule
func (s *CMMSService) CreateMaintenanceSchedule(schedule MaintenanceSchedule) (*MaintenanceSchedule, error) {
	jsonData, err := json.Marshal(schedule)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal schedule: %w", err)
	}

	resp, err := s.httpClient.Post(s.baseURL+"/maintenance/schedules", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create maintenance schedule: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to create maintenance schedule: status %d", resp.StatusCode)
	}

	var result struct {
		Success    bool   `json:"success"`
		ScheduleID string `json:"schedule_id"`
		Message    string `json:"message"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("failed to create maintenance schedule: %s", result.Message)
	}

	schedule.ID, _ = uuid.Parse(result.ScheduleID)
	return &schedule, nil
}

// GetMaintenanceSchedules retrieves all maintenance schedules
func (s *CMMSService) GetMaintenanceSchedules() ([]MaintenanceSchedule, error) {
	resp, err := s.httpClient.Get(s.baseURL + "/maintenance/schedules")
	if err != nil {
		return nil, fmt.Errorf("failed to get maintenance schedules: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get maintenance schedules: status %d", resp.StatusCode)
	}

	var result struct {
		Success   bool                  `json:"success"`
		Schedules []MaintenanceSchedule `json:"schedules"`
		Count     int                   `json:"count"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("failed to get maintenance schedules")
	}

	return result.Schedules, nil
}

// RegisterAsset registers a new asset
func (s *CMMSService) RegisterAsset(asset Asset) (*Asset, error) {
	jsonData, err := json.Marshal(asset)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal asset: %w", err)
	}

	resp, err := s.httpClient.Post(s.baseURL+"/assets", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to register asset: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to register asset: status %d", resp.StatusCode)
	}

	var result struct {
		Success bool   `json:"success"`
		AssetID string `json:"asset_id"`
		Message string `json:"message"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("failed to register asset: %s", result.Message)
	}

	return &asset, nil
}

// GetAssets retrieves assets with optional filters
func (s *CMMSService) GetAssets(assetType, status, department *string) ([]Asset, error) {
	url := s.baseURL + "/assets"
	if assetType != nil || status != nil || department != nil {
		url += "?"
		params := make([]string, 0)
		if assetType != nil {
			params = append(params, fmt.Sprintf("asset_type=%s", *assetType))
		}
		if status != nil {
			params = append(params, fmt.Sprintf("status=%s", *status))
		}
		if department != nil {
			params = append(params, fmt.Sprintf("department=%s", *department))
		}
		url += fmt.Sprintf("%s", params[0])
		for i := 1; i < len(params); i++ {
			url += "&" + params[i]
		}
	}

	resp, err := s.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to get assets: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get assets: status %d", resp.StatusCode)
	}

	var result struct {
		Success bool    `json:"success"`
		Assets  []Asset `json:"assets"`
		Count   int     `json:"count"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("failed to get assets")
	}

	return result.Assets, nil
}

// RecordPerformanceData records performance data for an asset
func (s *CMMSService) RecordPerformanceData(assetID string, performance AssetPerformance) error {
	jsonData, err := json.Marshal(performance)
	if err != nil {
		return fmt.Errorf("failed to marshal performance data: %w", err)
	}

	resp, err := s.httpClient.Post(
		fmt.Sprintf("%s/assets/%s/performance", s.baseURL, assetID),
		"application/json",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		return fmt.Errorf("failed to record performance data: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to record performance data: status %d", resp.StatusCode)
	}

	var result struct {
		Success bool   `json:"success"`
		Message string `json:"message"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return fmt.Errorf("failed to record performance data: %s", result.Message)
	}

	return nil
}

// GetAssetStatistics retrieves asset statistics
func (s *CMMSService) GetAssetStatistics(assetID *string, startDate, endDate *time.Time) (map[string]interface{}, error) {
	url := s.baseURL + "/assets/statistics"
	if assetID != nil || startDate != nil || endDate != nil {
		url += "?"
		params := make([]string, 0)
		if assetID != nil {
			params = append(params, fmt.Sprintf("asset_id=%s", *assetID))
		}
		if startDate != nil {
			params = append(params, fmt.Sprintf("start_date=%s", startDate.Format(time.RFC3339)))
		}
		if endDate != nil {
			params = append(params, fmt.Sprintf("end_date=%s", endDate.Format(time.RFC3339)))
		}
		url += fmt.Sprintf("%s", params[0])
		for i := 1; i < len(params); i++ {
			url += "&" + params[i]
		}
	}

	resp, err := s.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to get asset statistics: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get asset statistics: status %d", resp.StatusCode)
	}

	var result struct {
		Success    bool                   `json:"success"`
		Statistics map[string]interface{} `json:"statistics"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("failed to get asset statistics")
	}

	return result.Statistics, nil
}
