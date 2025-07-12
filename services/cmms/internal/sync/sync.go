package sync

import (
	"arx-cmms/pkg/models"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"gorm.io/gorm"
)

// SyncManager handles CMMS data synchronization
type SyncManager struct {
	db *gorm.DB
}

// NewSyncManager creates a new sync manager
func NewSyncManager(db *gorm.DB) *SyncManager {
	return &SyncManager{db: db}
}

// SyncResult represents the result of a sync operation
type SyncResult struct {
	RecordsProcessed int
	RecordsCreated   int
	RecordsUpdated   int
	RecordsFailed    int
	ErrorDetails     string
	Status           string
}

// SyncSchedules syncs maintenance schedules from CMMS
func (sm *SyncManager) SyncSchedules(ctx context.Context, conn *models.CMMSConnection, client *http.Client) (*SyncResult, error) {
	result := &SyncResult{Status: "success"}

	// Create sync log entry
	syncLog := &models.CMMSSyncLog{
		CMMSConnectionID: conn.ID,
		SyncType:         "schedules",
		Status:           "in_progress",
		StartedAt:        time.Now(),
		CompletedAt:      time.Now(),
	}
	sm.db.Create(syncLog)

	// Fetch schedules from CMMS API
	schedules, err := sm.fetchSchedulesFromAPI(ctx, conn, client)
	if err != nil {
		result.Status = "failed"
		result.ErrorDetails = err.Error()
		syncLog.Status = result.Status
		syncLog.ErrorDetails = result.ErrorDetails
		syncLog.CompletedAt = time.Now()
		sm.db.Save(syncLog)
		return result, err
	}

	// Get field mappings
	mappings, err := sm.GetMappings(conn.ID)
	if err != nil {
		result.Status = "failed"
		result.ErrorDetails = "Failed to get field mappings: " + err.Error()
		syncLog.Status = result.Status
		syncLog.ErrorDetails = result.ErrorDetails
		syncLog.CompletedAt = time.Now()
		sm.db.Save(syncLog)
		return result, err
	}

	// Process each schedule
	for _, scheduleData := range schedules {
		result.RecordsProcessed++

		// Transform data using mappings
		transformedData, err := sm.TransformData(scheduleData, mappings)
		if err != nil {
			result.RecordsFailed++
			log.Printf("Failed to transform schedule data: %v", err)
			continue
		}

		// Create or update maintenance schedule
		var schedule models.MaintenanceSchedule
		cmmsAssetID := transformedData["cmms_asset_id"].(string)

		// Try to find existing schedule by CMMS asset ID
		err = sm.db.Where("cmms_connection_id = ? AND cmms_asset_id = ?", conn.ID, cmmsAssetID).First(&schedule).Error

		if err != nil && err != gorm.ErrRecordNotFound {
			result.RecordsFailed++
			log.Printf("Database error for schedule: %v", err)
			continue
		}

		// Update schedule fields
		if assetID, ok := transformedData["asset_id"].(int); ok {
			schedule.AssetID = assetID
		}
		schedule.CMMSConnectionID = conn.ID
		schedule.CMMSAssetID = cmmsAssetID

		if scheduleType, ok := transformedData["schedule_type"].(string); ok {
			schedule.ScheduleType = scheduleType
		}
		if frequency, ok := transformedData["frequency"].(string); ok {
			schedule.Frequency = frequency
		}
		if interval, ok := transformedData["interval"].(int); ok {
			schedule.Interval = interval
		}
		if description, ok := transformedData["description"].(string); ok {
			schedule.Description = description
		}
		if instructions, ok := transformedData["instructions"].(string); ok {
			schedule.Instructions = instructions
		}
		if estimatedHours, ok := transformedData["estimated_hours"].(float64); ok {
			schedule.EstimatedHours = estimatedHours
		}
		if priority, ok := transformedData["priority"].(string); ok {
			schedule.Priority = priority
		}
		if isActive, ok := transformedData["is_active"].(bool); ok {
			schedule.IsActive = isActive
		}
		if nextDueDate, ok := transformedData["next_due_date"].(time.Time); ok {
			schedule.NextDueDate = nextDueDate
		}

		// Save to database
		if schedule.ID == 0 {
			schedule.CreatedAt = time.Now()
			err = sm.db.Create(&schedule).Error
			if err != nil {
				result.RecordsFailed++
				log.Printf("Failed to create schedule: %v", err)
			} else {
				result.RecordsCreated++
			}
		} else {
			schedule.UpdatedAt = time.Now()
			err = sm.db.Save(&schedule).Error
			if err != nil {
				result.RecordsFailed++
				log.Printf("Failed to update schedule: %v", err)
			} else {
				result.RecordsUpdated++
			}
		}
	}

	// Update sync log
	syncLog.Status = result.Status
	syncLog.RecordsProcessed = result.RecordsProcessed
	syncLog.RecordsCreated = result.RecordsCreated
	syncLog.RecordsUpdated = result.RecordsUpdated
	syncLog.RecordsFailed = result.RecordsFailed
	syncLog.ErrorDetails = result.ErrorDetails
	syncLog.CompletedAt = time.Now()
	sm.db.Save(syncLog)

	return result, nil
}

// SyncWorkOrders syncs work orders from CMMS
func (sm *SyncManager) SyncWorkOrders(ctx context.Context, conn *models.CMMSConnection, client *http.Client) (*SyncResult, error) {
	result := &SyncResult{Status: "success"}

	// Create sync log entry
	syncLog := &models.CMMSSyncLog{
		CMMSConnectionID: conn.ID,
		SyncType:         "work_orders",
		Status:           "in_progress",
		StartedAt:        time.Now(),
		CompletedAt:      time.Now(),
	}
	sm.db.Create(syncLog)

	// Fetch work orders from CMMS API
	workOrders, err := sm.fetchWorkOrdersFromAPI(ctx, conn, client)
	if err != nil {
		result.Status = "failed"
		result.ErrorDetails = err.Error()
		syncLog.Status = result.Status
		syncLog.ErrorDetails = result.ErrorDetails
		syncLog.CompletedAt = time.Now()
		sm.db.Save(syncLog)
		return result, err
	}

	// Get field mappings
	mappings, err := sm.GetMappings(conn.ID)
	if err != nil {
		result.Status = "failed"
		result.ErrorDetails = "Failed to get field mappings: " + err.Error()
		syncLog.Status = result.Status
		syncLog.ErrorDetails = result.ErrorDetails
		syncLog.CompletedAt = time.Now()
		sm.db.Save(syncLog)
		return result, err
	}

	// Process each work order
	for _, workOrderData := range workOrders {
		result.RecordsProcessed++

		// Transform data using mappings
		transformedData, err := sm.TransformData(workOrderData, mappings)
		if err != nil {
			result.RecordsFailed++
			log.Printf("Failed to transform work order data: %v", err)
			continue
		}

		// Create or update work order
		var workOrder models.WorkOrder
		cmmsWorkOrderID := transformedData["cmms_work_order_id"].(string)

		// Try to find existing work order by CMMS work order ID
		err = sm.db.Where("cmms_connection_id = ? AND cmms_work_order_id = ?", conn.ID, cmmsWorkOrderID).First(&workOrder).Error

		if err != nil && err != gorm.ErrRecordNotFound {
			result.RecordsFailed++
			log.Printf("Database error for work order: %v", err)
			continue
		}

		// Update work order fields
		if assetID, ok := transformedData["asset_id"].(int); ok {
			workOrder.AssetID = assetID
		}
		workOrder.CMMSConnectionID = conn.ID
		workOrder.CMMSWorkOrderID = cmmsWorkOrderID

		if workOrderNumber, ok := transformedData["work_order_number"].(string); ok {
			workOrder.WorkOrderNumber = workOrderNumber
		}
		if workOrderType, ok := transformedData["type"].(string); ok {
			workOrder.Type = workOrderType
		}
		if status, ok := transformedData["status"].(string); ok {
			workOrder.Status = status
		}
		if priority, ok := transformedData["priority"].(string); ok {
			workOrder.Priority = priority
		}
		if description, ok := transformedData["description"].(string); ok {
			workOrder.Description = description
		}
		if instructions, ok := transformedData["instructions"].(string); ok {
			workOrder.Instructions = instructions
		}
		if assignedTo, ok := transformedData["assigned_to"].(string); ok {
			workOrder.AssignedTo = assignedTo
		}
		if estimatedHours, ok := transformedData["estimated_hours"].(float64); ok {
			workOrder.EstimatedHours = estimatedHours
		}
		if actualHours, ok := transformedData["actual_hours"].(float64); ok {
			workOrder.ActualHours = actualHours
		}
		if cost, ok := transformedData["cost"].(float64); ok {
			workOrder.Cost = cost
		}
		if partsUsed, ok := transformedData["parts_used"].(string); ok {
			workOrder.PartsUsed = partsUsed
		}

		// Handle date fields
		if createdDate, ok := transformedData["created_date"].(time.Time); ok {
			workOrder.CreatedDate = createdDate
		}
		if scheduledDate, ok := transformedData["scheduled_date"].(time.Time); ok {
			workOrder.ScheduledDate = scheduledDate
		}
		if startedDate, ok := transformedData["started_date"].(*time.Time); ok {
			workOrder.StartedDate = startedDate
		}
		if completedDate, ok := transformedData["completed_date"].(*time.Time); ok {
			workOrder.CompletedDate = completedDate
		}

		// Save to database
		if workOrder.ID == 0 {
			workOrder.CreatedAt = time.Now()
			err = sm.db.Create(&workOrder).Error
			if err != nil {
				result.RecordsFailed++
				log.Printf("Failed to create work order: %v", err)
			} else {
				result.RecordsCreated++
			}
		} else {
			workOrder.UpdatedAt = time.Now()
			err = sm.db.Save(&workOrder).Error
			if err != nil {
				result.RecordsFailed++
				log.Printf("Failed to update work order: %v", err)
			} else {
				result.RecordsUpdated++
			}
		}
	}

	// Update sync log
	syncLog.Status = result.Status
	syncLog.RecordsProcessed = result.RecordsProcessed
	syncLog.RecordsCreated = result.RecordsCreated
	syncLog.RecordsUpdated = result.RecordsUpdated
	syncLog.RecordsFailed = result.RecordsFailed
	syncLog.ErrorDetails = result.ErrorDetails
	syncLog.CompletedAt = time.Now()
	sm.db.Save(syncLog)

	return result, nil
}

// SyncEquipmentSpecs syncs equipment specifications from CMMS
func (sm *SyncManager) SyncEquipmentSpecs(ctx context.Context, conn *models.CMMSConnection, client *http.Client) (*SyncResult, error) {
	result := &SyncResult{Status: "success"}

	// Create sync log entry
	syncLog := &models.CMMSSyncLog{
		CMMSConnectionID: conn.ID,
		SyncType:         "specs",
		Status:           "in_progress",
		StartedAt:        time.Now(),
		CompletedAt:      time.Now(),
	}
	sm.db.Create(syncLog)

	// Fetch equipment specs from CMMS API
	specs, err := sm.fetchEquipmentSpecsFromAPI(ctx, conn, client)
	if err != nil {
		result.Status = "failed"
		result.ErrorDetails = err.Error()
		syncLog.Status = result.Status
		syncLog.ErrorDetails = result.ErrorDetails
		syncLog.CompletedAt = time.Now()
		sm.db.Save(syncLog)
		return result, err
	}

	// Get field mappings
	mappings, err := sm.GetMappings(conn.ID)
	if err != nil {
		result.Status = "failed"
		result.ErrorDetails = "Failed to get field mappings: " + err.Error()
		syncLog.Status = result.Status
		syncLog.ErrorDetails = result.ErrorDetails
		syncLog.CompletedAt = time.Now()
		sm.db.Save(syncLog)
		return result, err
	}

	// Process each equipment spec
	for _, specData := range specs {
		result.RecordsProcessed++

		// Transform data using mappings
		transformedData, err := sm.TransformData(specData, mappings)
		if err != nil {
			result.RecordsFailed++
			log.Printf("Failed to transform equipment spec data: %v", err)
			continue
		}

		// Create or update equipment specification
		var spec models.EquipmentSpecification
		cmmsAssetID := transformedData["cmms_asset_id"].(string)
		specName := transformedData["spec_name"].(string)

		// Try to find existing spec by CMMS asset ID and spec name
		err = sm.db.Where("cmms_connection_id = ? AND cmms_asset_id = ? AND spec_name = ?",
			conn.ID, cmmsAssetID, specName).First(&spec).Error

		if err != nil && err != gorm.ErrRecordNotFound {
			result.RecordsFailed++
			log.Printf("Database error for equipment spec: %v", err)
			continue
		}

		// Update spec fields
		if assetID, ok := transformedData["asset_id"].(int); ok {
			spec.AssetID = assetID
		}
		spec.CMMSConnectionID = conn.ID
		spec.CMMSAssetID = cmmsAssetID

		if specType, ok := transformedData["spec_type"].(string); ok {
			spec.SpecType = specType
		}
		spec.SpecName = specName
		if specValue, ok := transformedData["spec_value"].(string); ok {
			spec.SpecValue = specValue
		}
		if unit, ok := transformedData["unit"].(string); ok {
			spec.Unit = unit
		}
		if minValue, ok := transformedData["min_value"].(*float64); ok {
			spec.MinValue = minValue
		}
		if maxValue, ok := transformedData["max_value"].(*float64); ok {
			spec.MaxValue = maxValue
		}
		if isCritical, ok := transformedData["is_critical"].(bool); ok {
			spec.IsCritical = isCritical
		}

		// Save to database
		if spec.ID == 0 {
			spec.CreatedAt = time.Now()
			err = sm.db.Create(&spec).Error
			if err != nil {
				result.RecordsFailed++
				log.Printf("Failed to create equipment spec: %v", err)
			} else {
				result.RecordsCreated++
			}
		} else {
			spec.UpdatedAt = time.Now()
			err = sm.db.Save(&spec).Error
			if err != nil {
				result.RecordsFailed++
				log.Printf("Failed to update equipment spec: %v", err)
			} else {
				result.RecordsUpdated++
			}
		}
	}

	// Update sync log
	syncLog.Status = result.Status
	syncLog.RecordsProcessed = result.RecordsProcessed
	syncLog.RecordsCreated = result.RecordsCreated
	syncLog.RecordsUpdated = result.RecordsUpdated
	syncLog.RecordsFailed = result.RecordsFailed
	syncLog.ErrorDetails = result.ErrorDetails
	syncLog.CompletedAt = time.Now()
	sm.db.Save(syncLog)

	return result, nil
}

// GetMappings retrieves field mappings for a CMMS connection
func (sm *SyncManager) GetMappings(connectionID int) ([]models.CMMSMapping, error) {
	var mappings []models.CMMSMapping
	err := sm.db.Where("cmms_connection_id = ?", connectionID).Find(&mappings).Error
	return mappings, err
}

// fetchSchedulesFromAPI fetches schedules from CMMS API
func (sm *SyncManager) fetchSchedulesFromAPI(ctx context.Context, conn *models.CMMSConnection, client *http.Client) ([]map[string]interface{}, error) {
	// Generic CMMS API endpoint for schedules
	endpoint := conn.BaseURL + "/api/schedules"
	if conn.Type == "upkeep" {
		endpoint = conn.BaseURL + "/api/v1/schedules"
	} else if conn.Type == "fiix" {
		endpoint = conn.BaseURL + "/api/v2/schedules"
	}

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add authentication headers based on connection type
	if conn.APIKey != "" {
		req.Header.Set("Authorization", "Bearer "+conn.APIKey)
	} else if conn.Username != "" && conn.Password != "" {
		req.SetBasicAuth(conn.Username, conn.Password)
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch schedules: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("schedules API returned status: %d", resp.StatusCode)
	}

	var schedules []map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&schedules); err != nil {
		return nil, fmt.Errorf("failed to decode schedules response: %w", err)
	}

	return schedules, nil
}

// fetchWorkOrdersFromAPI fetches work orders from CMMS API
func (sm *SyncManager) fetchWorkOrdersFromAPI(ctx context.Context, conn *models.CMMSConnection, client *http.Client) ([]map[string]interface{}, error) {
	// Generic CMMS API endpoint for work orders
	endpoint := conn.BaseURL + "/api/work-orders"
	if conn.Type == "upkeep" {
		endpoint = conn.BaseURL + "/api/v1/work-orders"
	} else if conn.Type == "fiix" {
		endpoint = conn.BaseURL + "/api/v2/work-orders"
	}

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add authentication headers based on connection type
	if conn.APIKey != "" {
		req.Header.Set("Authorization", "Bearer "+conn.APIKey)
	} else if conn.Username != "" && conn.Password != "" {
		req.SetBasicAuth(conn.Username, conn.Password)
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch work orders: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("work orders API returned status: %d", resp.StatusCode)
	}

	var workOrders []map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&workOrders); err != nil {
		return nil, fmt.Errorf("failed to decode work orders response: %w", err)
	}

	return workOrders, nil
}

// fetchEquipmentSpecsFromAPI fetches equipment specifications from CMMS API
func (sm *SyncManager) fetchEquipmentSpecsFromAPI(ctx context.Context, conn *models.CMMSConnection, client *http.Client) ([]map[string]interface{}, error) {
	// Generic CMMS API endpoint for equipment specifications
	endpoint := conn.BaseURL + "/api/equipment/specifications"
	if conn.Type == "upkeep" {
		endpoint = conn.BaseURL + "/api/v1/equipment/specifications"
	} else if conn.Type == "fiix" {
		endpoint = conn.BaseURL + "/api/v2/equipment/specifications"
	}

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add authentication headers based on connection type
	if conn.APIKey != "" {
		req.Header.Set("Authorization", "Bearer "+conn.APIKey)
	} else if conn.Username != "" && conn.Password != "" {
		req.SetBasicAuth(conn.Username, conn.Password)
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch equipment specs: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("equipment specs API returned status: %d", resp.StatusCode)
	}

	var specs []map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&specs); err != nil {
		return nil, fmt.Errorf("failed to decode equipment specs response: %w", err)
	}

	return specs, nil
}

// TransformData applies transformation rules to data
func (sm *SyncManager) TransformData(data map[string]interface{}, mappings []models.CMMSMapping) (map[string]interface{}, error) {
	transformed := make(map[string]interface{})

	for _, mapping := range mappings {
		if value, exists := data[mapping.CMMSField]; exists {
			// Apply transformation rules if specified
			if mapping.TransformRule != "" {
				transformedValue, err := sm.applyTransformRule(value, mapping.TransformRule)
				if err != nil {
					log.Printf("Transform error for field %s: %v", mapping.CMMSField, err)
					continue
				}
				transformed[mapping.ArxosField] = transformedValue
			} else {
				transformed[mapping.ArxosField] = value
			}
		} else if mapping.IsRequired {
			// Use default value for required fields that don't exist
			transformed[mapping.ArxosField] = mapping.DefaultValue
		}
	}

	return transformed, nil
}

// applyTransformRule applies a JSON transformation rule to data
func (sm *SyncManager) applyTransformRule(value interface{}, rule string) (interface{}, error) {
	// Parse the transformation rule
	var transformRule map[string]interface{}
	if err := json.Unmarshal([]byte(rule), &transformRule); err != nil {
		return value, fmt.Errorf("invalid transform rule JSON: %w", err)
	}

	// Apply transformation based on rule type
	if ruleType, ok := transformRule["type"].(string); ok {
		switch ruleType {
		case "type_conversion":
			return sm.applyTypeConversion(value, transformRule)
		case "date_format":
			return sm.applyDateFormat(value, transformRule)
		case "string_manipulation":
			return sm.applyStringManipulation(value, transformRule)
		case "conditional":
			return sm.applyConditionalLogic(value, transformRule)
		case "default":
			return sm.applyDefaultValue(value, transformRule)
		default:
			return value, fmt.Errorf("unknown transform rule type: %s", ruleType)
		}
	}

	return value, nil
}

// applyTypeConversion handles type conversions
func (sm *SyncManager) applyTypeConversion(value interface{}, rule map[string]interface{}) (interface{}, error) {
	targetType, ok := rule["target_type"].(string)
	if !ok {
		return value, fmt.Errorf("target_type not specified in type conversion rule")
	}

	switch targetType {
	case "string":
		return fmt.Sprintf("%v", value), nil
	case "int":
		switch v := value.(type) {
		case float64:
			return int(v), nil
		case string:
			if i, err := strconv.Atoi(v); err == nil {
				return i, nil
			}
		}
		return 0, fmt.Errorf("cannot convert %v to int", value)
	case "float64":
		switch v := value.(type) {
		case string:
			if f, err := strconv.ParseFloat(v, 64); err == nil {
				return f, nil
			}
		case int:
			return float64(v), nil
		}
		return 0.0, fmt.Errorf("cannot convert %v to float64", value)
	case "bool":
		switch v := value.(type) {
		case string:
			return strings.ToLower(v) == "true" || v == "1" || v == "yes", nil
		case int:
			return v != 0, nil
		case float64:
			return v != 0, nil
		}
		return false, fmt.Errorf("cannot convert %v to bool", value)
	default:
		return value, fmt.Errorf("unsupported target type: %s", targetType)
	}
}

// applyDateFormat handles date format transformations
func (sm *SyncManager) applyDateFormat(value interface{}, rule map[string]interface{}) (interface{}, error) {
	inputFormat, ok := rule["input_format"].(string)
	if !ok {
		inputFormat = "2006-01-02T15:04:05Z" // Default ISO format
	}

	// Convert value to string if it isn't already
	var dateStr string
	switch v := value.(type) {
	case string:
		dateStr = v
	case time.Time:
		return v, nil
	default:
		dateStr = fmt.Sprintf("%v", v)
	}

	// Parse the input date
	parsedTime, err := time.Parse(inputFormat, dateStr)
	if err != nil {
		return value, fmt.Errorf("failed to parse date '%s' with format '%s': %w", dateStr, inputFormat, err)
	}

	// Return the parsed time (output format is handled by the caller)
	return parsedTime, nil
}

// applyStringManipulation handles string transformations
func (sm *SyncManager) applyStringManipulation(value interface{}, rule map[string]interface{}) (interface{}, error) {
	operation, ok := rule["operation"].(string)
	if !ok {
		return value, fmt.Errorf("operation not specified in string manipulation rule")
	}

	// Convert value to string
	var str string
	switch v := value.(type) {
	case string:
		str = v
	default:
		str = fmt.Sprintf("%v", v)
	}

	switch operation {
	case "uppercase":
		return strings.ToUpper(str), nil
	case "lowercase":
		return strings.ToLower(str), nil
	case "trim":
		return strings.TrimSpace(str), nil
	case "replace":
		oldStr, ok := rule["old"].(string)
		if !ok {
			return str, fmt.Errorf("old string not specified in replace operation")
		}
		newStr, ok := rule["new"].(string)
		if !ok {
			return str, fmt.Errorf("new string not specified in replace operation")
		}
		return strings.ReplaceAll(str, oldStr, newStr), nil
	case "substring":
		start, ok := rule["start"].(float64)
		if !ok {
			return str, fmt.Errorf("start position not specified in substring operation")
		}
		end, ok := rule["end"].(float64)
		if !ok {
			return str, fmt.Errorf("end position not specified in substring operation")
		}
		if int(start) >= len(str) || int(end) > len(str) {
			return str, fmt.Errorf("substring indices out of bounds")
		}
		return str[int(start):int(end)], nil
	default:
		return str, fmt.Errorf("unknown string operation: %s", operation)
	}
}

// applyConditionalLogic handles conditional transformations
func (sm *SyncManager) applyConditionalLogic(value interface{}, rule map[string]interface{}) (interface{}, error) {
	condition, ok := rule["condition"].(map[string]interface{})
	if !ok {
		return value, fmt.Errorf("condition not specified in conditional rule")
	}

	operator, ok := condition["operator"].(string)
	if !ok {
		return value, fmt.Errorf("operator not specified in condition")
	}

	field, ok := condition["field"].(string)
	if !ok {
		return value, fmt.Errorf("field not specified in condition")
	}

	expectedValue, ok := condition["value"]
	if !ok {
		return value, fmt.Errorf("expected value not specified in condition")
	}

	// Get the field value from the current data context
	// For now, we'll use the current value as the field value
	// In a more advanced implementation, this could look up the field value from a data context
	fieldValue := value
	log.Printf("Applying conditional logic: field=%s, operator=%s, expected=%v, actual=%v", field, operator, expectedValue, fieldValue)

	// Apply the condition
	var conditionMet bool
	switch operator {
	case "equals":
		conditionMet = fmt.Sprintf("%v", fieldValue) == fmt.Sprintf("%v", expectedValue)
	case "not_equals":
		conditionMet = fmt.Sprintf("%v", fieldValue) != fmt.Sprintf("%v", expectedValue)
	case "contains":
		fieldStr := fmt.Sprintf("%v", fieldValue)
		expectedStr := fmt.Sprintf("%v", expectedValue)
		conditionMet = strings.Contains(fieldStr, expectedStr)
	case "greater_than":
		if f1, f2, err := sm.compareNumbers(fieldValue, expectedValue); err == nil {
			conditionMet = f1 > f2
		}
	case "less_than":
		if f1, f2, err := sm.compareNumbers(fieldValue, expectedValue); err == nil {
			conditionMet = f1 < f2
		}
	default:
		return value, fmt.Errorf("unknown condition operator: %s", operator)
	}

	// Return the appropriate value based on condition
	if conditionMet {
		if trueValue, ok := rule["true_value"]; ok {
			return trueValue, nil
		}
	} else {
		if falseValue, ok := rule["false_value"]; ok {
			return falseValue, nil
		}
	}

	return value, nil
}

// applyDefaultValue applies a default value if the current value is empty/null
func (sm *SyncManager) applyDefaultValue(value interface{}, rule map[string]interface{}) (interface{}, error) {
	defaultValue, ok := rule["default_value"]
	if !ok {
		return value, fmt.Errorf("default_value not specified in default rule")
	}

	// Check if current value is empty/null
	if value == nil || value == "" || value == 0 || value == false {
		return defaultValue, nil
	}

	return value, nil
}

// compareNumbers compares two values as numbers
func (sm *SyncManager) compareNumbers(a, b interface{}) (float64, float64, error) {
	var aFloat, bFloat float64

	switch v := a.(type) {
	case float64:
		aFloat = v
	case int:
		aFloat = float64(v)
	case string:
		if f, err := strconv.ParseFloat(v, 64); err == nil {
			aFloat = f
		} else {
			return 0, 0, fmt.Errorf("cannot convert %v to number", a)
		}
	default:
		return 0, 0, fmt.Errorf("cannot convert %v to number", a)
	}

	switch v := b.(type) {
	case float64:
		bFloat = v
	case int:
		bFloat = float64(v)
	case string:
		if f, err := strconv.ParseFloat(v, 64); err == nil {
			bFloat = f
		} else {
			return 0, 0, fmt.Errorf("cannot convert %v to number", b)
		}
	default:
		return 0, 0, fmt.Errorf("cannot convert %v to number", b)
	}

	return aFloat, bFloat, nil
}
