package workflow

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ActionManager manages workflow actions
type ActionManager struct {
	actions  map[string]*Action
	handlers map[ActionType]ActionHandler
	metrics  *ActionMetrics
}

// ActionHandler defines the interface for action handlers
type ActionHandler interface {
	// Execute executes the action
	Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error)

	// GetName returns the handler name
	GetName() string

	// GetCapabilities returns the action capabilities
	GetCapabilities() []string
}

// ActionMetrics tracks action performance metrics
type ActionMetrics struct {
	TotalActions      int64         `json:"total_actions"`
	ExecutedActions   int64         `json:"executed_actions"`
	SuccessfulActions int64         `json:"successful_actions"`
	FailedActions     int64         `json:"failed_actions"`
	AverageDuration   time.Duration `json:"average_duration"`
}

// NewActionManager creates a new action manager
func NewActionManager() *ActionManager {
	am := &ActionManager{
		actions:  make(map[string]*Action),
		handlers: make(map[ActionType]ActionHandler),
		metrics:  &ActionMetrics{},
	}

	// Register default handlers
	am.registerDefaultHandlers()
	return am
}

// RegisterAction registers a new action
func (am *ActionManager) RegisterAction(action *Action) error {
	if action == nil {
		return fmt.Errorf("action cannot be nil")
	}

	if action.ID == "" {
		action.ID = fmt.Sprintf("action_%d", time.Now().UnixNano())
	}

	if action.Name == "" {
		return fmt.Errorf("action name cannot be empty")
	}

	if action.Type == "" {
		return fmt.Errorf("action type cannot be empty")
	}

	// Validate action
	if err := am.validateAction(action); err != nil {
		return fmt.Errorf("action validation failed: %w", err)
	}

	// Store action
	am.actions[action.ID] = action
	am.metrics.TotalActions++

	logger.Info("Action registered: %s (%s)", action.ID, action.Name)
	return nil
}

// ExecuteAction executes an action
func (am *ActionManager) ExecuteAction(ctx context.Context, actionID string, input map[string]interface{}) (map[string]interface{}, error) {
	action, exists := am.actions[actionID]
	if !exists {
		return nil, fmt.Errorf("action %s not found", actionID)
	}

	if !action.Enabled {
		return nil, fmt.Errorf("action %s is not enabled", actionID)
	}

	handler, exists := am.handlers[action.Type]
	if !exists {
		return nil, fmt.Errorf("no handler found for action type %s", action.Type)
	}

	start := time.Now()
	output, err := handler.Execute(ctx, action, input)
	duration := time.Since(start)

	am.metrics.ExecutedActions++
	am.updateAverageDuration(duration)

	if err != nil {
		am.metrics.FailedActions++
		return nil, fmt.Errorf("action execution failed: %w", err)
	}

	am.metrics.SuccessfulActions++
	logger.Info("Action executed: %s (duration: %s)", actionID, duration)
	return output, nil
}

// GetAction retrieves an action by ID
func (am *ActionManager) GetAction(actionID string) (*Action, error) {
	action, exists := am.actions[actionID]
	if !exists {
		return nil, fmt.Errorf("action %s not found", actionID)
	}
	return action, nil
}

// ListActions returns all actions
func (am *ActionManager) ListActions() []*Action {
	actions := make([]*Action, 0, len(am.actions))
	for _, action := range am.actions {
		actions = append(actions, action)
	}
	return actions
}

// GetMetrics returns action metrics
func (am *ActionManager) GetMetrics() *ActionMetrics {
	return am.metrics
}

// validateAction validates an action configuration
func (am *ActionManager) validateAction(action *Action) error {
	// Check if handler exists
	if _, exists := am.handlers[action.Type]; !exists {
		return fmt.Errorf("no handler found for action type %s", action.Type)
	}

	return nil
}

// registerDefaultHandlers registers default action handlers
func (am *ActionManager) registerDefaultHandlers() {
	am.RegisterHandler(ActionTypeEmail, NewEmailActionHandler())
	am.RegisterHandler(ActionTypeSMS, NewSMSActionHandler())
	am.RegisterHandler(ActionTypeWebhook, NewWebhookActionHandler())
	am.RegisterHandler(ActionTypeDatabase, NewDatabaseActionHandler())
	am.RegisterHandler(ActionTypeAPI, NewAPIActionHandler())
	am.RegisterHandler(ActionTypeFile, NewFileActionHandler())
	am.RegisterHandler(ActionTypeTransform, NewTransformActionHandler())
	am.RegisterHandler(ActionTypeCondition, NewConditionActionHandler())
	am.RegisterHandler(ActionTypeDelay, NewDelayActionHandler())
	am.RegisterHandler(ActionTypeMQTT, NewMQTTActionHandler())
	am.RegisterHandler(ActionTypeModbus, NewModbusActionHandler())
}

// RegisterHandler registers an action handler
func (am *ActionManager) RegisterHandler(actionType ActionType, handler ActionHandler) {
	am.handlers[actionType] = handler
	logger.Info("Action handler registered: %s", handler.GetName())
}

// updateAverageDuration updates the average execution duration
func (am *ActionManager) updateAverageDuration(duration time.Duration) {
	if am.metrics.ExecutedActions > 0 {
		totalDuration := am.metrics.AverageDuration * time.Duration(am.metrics.ExecutedActions-1)
		am.metrics.AverageDuration = (totalDuration + duration) / time.Duration(am.metrics.ExecutedActions)
	} else {
		am.metrics.AverageDuration = duration
	}
}

// EmailActionHandler handles email actions
type EmailActionHandler struct {
	httpClient *http.Client
}

// NewEmailActionHandler creates a new email action handler
func NewEmailActionHandler() *EmailActionHandler {
	return &EmailActionHandler{
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}
}

// Execute executes the email action
func (h *EmailActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract email parameters
	to, ok := action.Parameters["to"].(string)
	if !ok {
		return nil, fmt.Errorf("email 'to' parameter is required")
	}

	subject, ok := action.Parameters["subject"].(string)
	if !ok {
		subject = "ArxOS Workflow Notification"
	}

	_, ok = action.Parameters["body"].(string)
	if !ok {
		// body = "Workflow executed successfully"
	}

	// Simulate email sending
	logger.Info("Sending email to %s: %s", to, subject)

	// In a real implementation, would use an email service like SendGrid, SES, etc.
	time.Sleep(100 * time.Millisecond) // Simulate network delay

	return map[string]interface{}{
		"status":     "sent",
		"to":         to,
		"subject":    subject,
		"message_id": fmt.Sprintf("msg_%d", time.Now().UnixNano()),
		"timestamp":  time.Now(),
	}, nil
}

// GetName returns the handler name
func (h *EmailActionHandler) GetName() string {
	return "Email Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *EmailActionHandler) GetCapabilities() []string {
	return []string{"send_email", "html_email", "template_email", "attachment"}
}

// SMSActionHandler handles SMS actions
type SMSActionHandler struct {
	httpClient *http.Client
}

// NewSMSActionHandler creates a new SMS action handler
func NewSMSActionHandler() *SMSActionHandler {
	return &SMSActionHandler{
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}
}

// Execute executes the SMS action
func (h *SMSActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract SMS parameters
	to, ok := action.Parameters["to"].(string)
	if !ok {
		return nil, fmt.Errorf("SMS 'to' parameter is required")
	}

	message, ok := action.Parameters["message"].(string)
	if !ok {
		message = "ArxOS Workflow Notification"
	}

	// Simulate SMS sending
	logger.Info("Sending SMS to %s: %s", to, message)

	// In a real implementation, would use an SMS service like Twilio, AWS SNS, etc.
	time.Sleep(50 * time.Millisecond) // Simulate network delay

	return map[string]interface{}{
		"status":     "sent",
		"to":         to,
		"message":    message,
		"message_id": fmt.Sprintf("sms_%d", time.Now().UnixNano()),
		"timestamp":  time.Now(),
	}, nil
}

// GetName returns the handler name
func (h *SMSActionHandler) GetName() string {
	return "SMS Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *SMSActionHandler) GetCapabilities() []string {
	return []string{"send_sms", "bulk_sms", "unicode_sms"}
}

// WebhookActionHandler handles webhook actions
type WebhookActionHandler struct {
	httpClient *http.Client
}

// NewWebhookActionHandler creates a new webhook action handler
func NewWebhookActionHandler() *WebhookActionHandler {
	return &WebhookActionHandler{
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}
}

// Execute executes the webhook action
func (h *WebhookActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract webhook parameters
	url, ok := action.Parameters["url"].(string)
	if !ok {
		return nil, fmt.Errorf("webhook 'url' parameter is required")
	}

	method, ok := action.Parameters["method"].(string)
	if !ok {
		method = "POST"
	}

	// Prepare request data
	requestData := input
	if customData, ok := action.Parameters["data"].(map[string]interface{}); ok {
		requestData = customData
	}

	// Simulate webhook call
	logger.Info("Sending webhook to %s: %s", url, method)

	// In a real implementation, would make actual HTTP request
	time.Sleep(200 * time.Millisecond) // Simulate network delay

	return map[string]interface{}{
		"status":    "sent",
		"url":       url,
		"method":    method,
		"data":      requestData,
		"timestamp": time.Now(),
	}, nil
}

// GetName returns the handler name
func (h *WebhookActionHandler) GetName() string {
	return "Webhook Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *WebhookActionHandler) GetCapabilities() []string {
	return []string{"http_request", "custom_headers", "authentication", "retry_logic"}
}

// DatabaseActionHandler handles database actions
type DatabaseActionHandler struct{}

// NewDatabaseActionHandler creates a new database action handler
func NewDatabaseActionHandler() *DatabaseActionHandler {
	return &DatabaseActionHandler{}
}

// Execute executes the database action
func (h *DatabaseActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract database parameters
	query, ok := action.Parameters["query"].(string)
	if !ok {
		return nil, fmt.Errorf("database 'query' parameter is required")
	}

	operation, ok := action.Parameters["operation"].(string)
	if !ok {
		operation = "select"
	}

	// Simulate database operation
	logger.Info("Executing database %s operation: %s", operation, query)

	// In a real implementation, would execute actual database query
	time.Sleep(100 * time.Millisecond) // Simulate database delay

	result := map[string]interface{}{
		"status":        "completed",
		"operation":     operation,
		"query":         query,
		"rows_affected": 1,
		"timestamp":     time.Now(),
	}

	// Add query results based on operation
	switch operation {
	case "select":
		result["rows"] = []map[string]interface{}{
			{"id": 1, "name": "test", "value": "data"},
		}
	case "insert", "update", "delete":
		result["rows_affected"] = 1
	}

	return result, nil
}

// GetName returns the handler name
func (h *DatabaseActionHandler) GetName() string {
	return "Database Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *DatabaseActionHandler) GetCapabilities() []string {
	return []string{"select", "insert", "update", "delete", "stored_procedure", "transaction"}
}

// APIActionHandler handles API actions
type APIActionHandler struct {
	httpClient *http.Client
}

// NewAPIActionHandler creates a new API action handler
func NewAPIActionHandler() *APIActionHandler {
	return &APIActionHandler{
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}
}

// Execute executes the API action
func (h *APIActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract API parameters
	url, ok := action.Parameters["url"].(string)
	if !ok {
		return nil, fmt.Errorf("API 'url' parameter is required")
	}

	method, ok := action.Parameters["method"].(string)
	if !ok {
		method = "GET"
	}

	// Prepare request data
	requestData := input
	if customData, ok := action.Parameters["data"].(map[string]interface{}); ok {
		requestData = customData
	}

	// Simulate API call
	logger.Info("Making API call to %s: %s", url, method)

	// In a real implementation, would make actual HTTP request
	time.Sleep(300 * time.Millisecond) // Simulate network delay

	return map[string]interface{}{
		"status":    "completed",
		"url":       url,
		"method":    method,
		"data":      requestData,
		"response":  map[string]interface{}{"status": "success", "data": "response_data"},
		"timestamp": time.Now(),
	}, nil
}

// GetName returns the handler name
func (h *APIActionHandler) GetName() string {
	return "API Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *APIActionHandler) GetCapabilities() []string {
	return []string{"http_request", "authentication", "rate_limiting", "retry_logic", "response_parsing"}
}

// FileActionHandler handles file actions
type FileActionHandler struct{}

// NewFileActionHandler creates a new file action handler
func NewFileActionHandler() *FileActionHandler {
	return &FileActionHandler{}
}

// Execute executes the file action
func (h *FileActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract file parameters
	operation, ok := action.Parameters["operation"].(string)
	if !ok {
		return nil, fmt.Errorf("file 'operation' parameter is required")
	}

	filePath, ok := action.Parameters["file_path"].(string)
	if !ok {
		return nil, fmt.Errorf("file 'file_path' parameter is required")
	}

	// Simulate file operation
	logger.Info("Executing file %s operation on %s", operation, filePath)

	// In a real implementation, would perform actual file operations
	time.Sleep(50 * time.Millisecond) // Simulate file I/O delay

	result := map[string]interface{}{
		"status":    "completed",
		"operation": operation,
		"file_path": filePath,
		"timestamp": time.Now(),
	}

	// Add operation-specific results
	switch operation {
	case "read":
		result["content"] = "file content"
		result["size"] = 1024
	case "write":
		result["bytes_written"] = 1024
	case "delete":
		result["deleted"] = true
	case "copy":
		result["copied_to"] = filePath + ".copy"
	case "move":
		result["moved_to"] = filePath + ".moved"
	}

	return result, nil
}

// GetName returns the handler name
func (h *FileActionHandler) GetName() string {
	return "File Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *FileActionHandler) GetCapabilities() []string {
	return []string{"read", "write", "delete", "copy", "move", "compress", "extract"}
}

// TransformActionHandler handles data transformation actions
type TransformActionHandler struct{}

// NewTransformActionHandler creates a new transform action handler
func NewTransformActionHandler() *TransformActionHandler {
	return &TransformActionHandler{}
}

// Execute executes the transform action
func (h *TransformActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract transform parameters
	transformation, ok := action.Parameters["transformation"].(string)
	if !ok {
		return nil, fmt.Errorf("transform 'transformation' parameter is required")
	}

	// Simulate data transformation
	logger.Info("Executing data transformation: %s", transformation)

	// In a real implementation, would perform actual data transformation
	time.Sleep(100 * time.Millisecond) // Simulate processing delay

	// Apply transformation based on type
	var output map[string]interface{}
	switch transformation {
	case "json_to_xml":
		output = map[string]interface{}{
			"format": "xml",
			"data":   "<root><item>transformed data</item></root>",
		}
	case "xml_to_json":
		output = map[string]interface{}{
			"format": "json",
			"data":   map[string]interface{}{"root": map[string]interface{}{"item": "transformed data"}},
		}
	case "csv_to_json":
		output = map[string]interface{}{
			"format": "json",
			"data":   []map[string]interface{}{{"col1": "value1", "col2": "value2"}},
		}
	case "normalize":
		output = map[string]interface{}{
			"normalized": true,
			"data":       input,
		}
	default:
		output = map[string]interface{}{
			"transformed": true,
			"data":        input,
		}
	}

	return map[string]interface{}{
		"status":         "completed",
		"transformation": transformation,
		"output":         output,
		"timestamp":      time.Now(),
	}, nil
}

// GetName returns the handler name
func (h *TransformActionHandler) GetName() string {
	return "Transform Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *TransformActionHandler) GetCapabilities() []string {
	return []string{"json_to_xml", "xml_to_json", "csv_to_json", "normalize", "filter", "map", "aggregate"}
}

// ConditionActionHandler handles conditional actions
type ConditionActionHandler struct{}

// NewConditionActionHandler creates a new condition action handler
func NewConditionActionHandler() *ConditionActionHandler {
	return &ConditionActionHandler{}
}

// Execute executes the condition action
func (h *ConditionActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract condition parameters
	condition, ok := action.Parameters["condition"].(string)
	if !ok {
		return nil, fmt.Errorf("condition 'condition' parameter is required")
	}

	// Simulate condition evaluation
	logger.Info("Evaluating condition: %s", condition)

	// In a real implementation, would evaluate actual condition
	time.Sleep(50 * time.Millisecond) // Simulate evaluation delay

	// Simple condition evaluation (in real implementation would use expression evaluator)
	result := true
	if condition == "false" {
		result = false
	}

	return map[string]interface{}{
		"status":    "completed",
		"condition": condition,
		"result":    result,
		"timestamp": time.Now(),
	}, nil
}

// GetName returns the handler name
func (h *ConditionActionHandler) GetName() string {
	return "Condition Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *ConditionActionHandler) GetCapabilities() []string {
	return []string{"boolean_condition", "comparison", "logical_operators", "regex_match", "value_check"}
}

// DelayActionHandler handles delay actions
type DelayActionHandler struct{}

// NewDelayActionHandler creates a new delay action handler
func NewDelayActionHandler() *DelayActionHandler {
	return &DelayActionHandler{}
}

// Execute executes the delay action
func (h *DelayActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract delay parameters
	delay, ok := action.Parameters["delay"].(float64)
	if !ok {
		delay = 1.0 // Default 1 second
	}

	// Execute delay
	logger.Info("Executing delay: %.2f seconds", delay)

	time.Sleep(time.Duration(delay) * time.Second)

	return map[string]interface{}{
		"status":    "completed",
		"delay":     delay,
		"timestamp": time.Now(),
	}, nil
}

// GetName returns the handler name
func (h *DelayActionHandler) GetName() string {
	return "Delay Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *DelayActionHandler) GetCapabilities() []string {
	return []string{"fixed_delay", "random_delay", "conditional_delay"}
}

// MQTTActionHandler handles MQTT actions
type MQTTActionHandler struct{}

// NewMQTTActionHandler creates a new MQTT action handler
func NewMQTTActionHandler() *MQTTActionHandler {
	return &MQTTActionHandler{}
}

// Execute executes the MQTT action
func (h *MQTTActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract MQTT parameters
	topic, ok := action.Parameters["topic"].(string)
	if !ok {
		return nil, fmt.Errorf("MQTT 'topic' parameter is required")
	}

	message, ok := action.Parameters["message"].(string)
	if !ok {
		message = "ArxOS Workflow Message"
	}

	qos, ok := action.Parameters["qos"].(float64)
	if !ok {
		qos = 1
	}

	// Simulate MQTT publish
	logger.Info("Publishing MQTT message to %s: %s", topic, message)

	// In a real implementation, would publish to actual MQTT broker
	time.Sleep(100 * time.Millisecond) // Simulate network delay

	return map[string]interface{}{
		"status":    "published",
		"topic":     topic,
		"message":   message,
		"qos":       int(qos),
		"timestamp": time.Now(),
	}, nil
}

// GetName returns the handler name
func (h *MQTTActionHandler) GetName() string {
	return "MQTT Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *MQTTActionHandler) GetCapabilities() []string {
	return []string{"publish", "subscribe", "retain", "qos", "will_message"}
}

// ModbusActionHandler handles Modbus actions
type ModbusActionHandler struct{}

// NewModbusActionHandler creates a new Modbus action handler
func NewModbusActionHandler() *ModbusActionHandler {
	return &ModbusActionHandler{}
}

// Execute executes the Modbus action
func (h *ModbusActionHandler) Execute(ctx context.Context, action *Action, input map[string]interface{}) (map[string]interface{}, error) {
	// Extract Modbus parameters
	address, ok := action.Parameters["address"].(string)
	if !ok {
		return nil, fmt.Errorf("Modbus 'address' parameter is required")
	}

	function, ok := action.Parameters["function"].(string)
	if !ok {
		function = "read_holding_registers"
	}

	// Simulate Modbus operation
	logger.Info("Executing Modbus %s on %s", function, address)

	// In a real implementation, would perform actual Modbus operation
	time.Sleep(200 * time.Millisecond) // Simulate network delay

	return map[string]interface{}{
		"status":    "completed",
		"address":   address,
		"function":  function,
		"data":      []int{100, 200, 300},
		"timestamp": time.Now(),
	}, nil
}

// GetName returns the handler name
func (h *ModbusActionHandler) GetName() string {
	return "Modbus Action Handler"
}

// GetCapabilities returns the action capabilities
func (h *ModbusActionHandler) GetCapabilities() []string {
	return []string{"read_holding_registers", "write_holding_register", "read_coils", "write_coil", "read_input_registers"}
}
