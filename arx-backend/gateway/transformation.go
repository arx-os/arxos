package gateway

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strings"
	"text/template"
	"time"

	"sync"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"go.uber.org/zap"
)

// TransformationManager manages request and response transformations
type TransformationManager struct {
	config  TransformationConfig
	logger  *zap.Logger
	rules   map[string]*TransformationRule
	mu      sync.RWMutex
	metrics *TransformationMetrics
}

// TransformationConfig defines transformation configuration
type TransformationConfig struct {
	Enabled           bool                          `yaml:"enabled"`
	RequestTransform  bool                          `yaml:"request_transform"`
	ResponseTransform bool                          `yaml:"response_transform"`
	Rules             map[string]TransformationRule `yaml:"rules"`
	Templates         map[string]string             `yaml:"templates"`
	MaxBodySize       int64                         `yaml:"max_body_size"`
	Compression       bool                          `yaml:"compression"`
}

// TransformationRule defines a transformation rule
type TransformationRule struct {
	Name              string                    `yaml:"name"`
	Enabled           bool                      `yaml:"enabled"`
	Priority          int                       `yaml:"priority"`
	Conditions        []TransformationCondition `yaml:"conditions"`
	RequestTransform  *RequestTransform         `yaml:"request_transform"`
	ResponseTransform *ResponseTransform        `yaml:"response_transform"`
	ErrorHandling     ErrorHandling             `yaml:"error_handling"`
}

// TransformationCondition defines conditions for applying transformations
type TransformationCondition struct {
	Type     string `yaml:"type"` // path, method, header, query
	Field    string `yaml:"field"`
	Operator string `yaml:"operator"` // equals, contains, regex, exists
	Value    string `yaml:"value"`
	Negate   bool   `yaml:"negate"`
}

// RequestTransform defines request transformation
type RequestTransform struct {
	Headers     map[string]string          `yaml:"headers"`
	QueryParams map[string]string          `yaml:"query_params"`
	Body        *BodyTransform             `yaml:"body"`
	URL         *URLTransform              `yaml:"url"`
	Method      string                     `yaml:"method"`
	Custom      map[string]CustomTransform `yaml:"custom"`
}

// ResponseTransform defines response transformation
type ResponseTransform struct {
	Headers    map[string]string          `yaml:"headers"`
	Body       *BodyTransform             `yaml:"body"`
	StatusCode *StatusCodeTransform       `yaml:"status_code"`
	Custom     map[string]CustomTransform `yaml:"custom"`
}

// BodyTransform defines body transformation
type BodyTransform struct {
	Type        string            `yaml:"type"` // json, xml, text, binary
	Template    string            `yaml:"template"`
	Variables   map[string]string `yaml:"variables"`
	Validation  *ValidationRule   `yaml:"validation"`
	Compression bool              `yaml:"compression"`
}

// URLTransform defines URL transformation
type URLTransform struct {
	Path        string            `yaml:"path"`
	QueryParams map[string]string `yaml:"query_params"`
	Fragment    string            `yaml:"fragment"`
}

// StatusCodeTransform defines status code transformation
type StatusCodeTransform struct {
	Map        map[int]int           `yaml:"map"`
	Default    int                   `yaml:"default"`
	Conditions []StatusCodeCondition `yaml:"conditions"`
}

// StatusCodeCondition defines status code transformation conditions
type StatusCodeCondition struct {
	From       int    `yaml:"from"`
	To         int    `yaml:"to"`
	Condition  string `yaml:"condition"`
	Expression string `yaml:"expression"`
}

// CustomTransform defines custom transformation
type CustomTransform struct {
	Type       string            `yaml:"type"`
	Script     string            `yaml:"script"`
	Parameters map[string]string `yaml:"parameters"`
	Timeout    time.Duration     `yaml:"timeout"`
}

// ValidationRule defines validation rules
type ValidationRule struct {
	Required []string           `yaml:"required"`
	Format   map[string]string  `yaml:"format"`
	Size     *SizeValidation    `yaml:"size"`
	Content  *ContentValidation `yaml:"content"`
}

// SizeValidation defines size validation
type SizeValidation struct {
	Min       int64 `yaml:"min"`
	Max       int64 `yaml:"max"`
	MaxFields int   `yaml:"max_fields"`
	MaxDepth  int   `yaml:"max_depth"`
}

// ContentValidation defines content validation
type ContentValidation struct {
	AllowedTypes   []string `yaml:"allowed_types"`
	ForbiddenTypes []string `yaml:"forbidden_types"`
	MaxFileSize    int64    `yaml:"max_file_size"`
}

// ErrorHandling defines error handling for transformations
type ErrorHandling struct {
	OnError      string `yaml:"on_error"` // fail, skip, default
	DefaultValue string `yaml:"default_value"`
	LogErrors    bool   `yaml:"log_errors"`
	ReturnError  bool   `yaml:"return_error"`
}

// TransformationMetrics holds transformation metrics
type TransformationMetrics struct {
	transformationsTotal   *prometheus.CounterVec
	transformationErrors   *prometheus.CounterVec
	transformationDuration *prometheus.HistogramVec
	validationErrors       *prometheus.CounterVec
}

// NewTransformationManager creates a new transformation manager
func NewTransformationManager(config TransformationConfig) (*TransformationManager, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	tm := &TransformationManager{
		config: config,
		logger: logger,
		rules:  make(map[string]*TransformationRule),
	}

	// Initialize metrics
	tm.initializeMetrics()

	// Initialize rules
	tm.initializeRules()

	return tm, nil
}

// initializeMetrics initializes transformation metrics
func (tm *TransformationManager) initializeMetrics() {
	tm.metrics = &TransformationMetrics{
		transformationsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_transformations_total",
				Help: "Total transformations applied",
			},
			[]string{"rule", "type", "status"},
		),
		transformationErrors: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_transformation_errors_total",
				Help: "Total transformation errors",
			},
			[]string{"rule", "type", "error"},
		),
		transformationDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_transformation_duration_seconds",
				Help:    "Transformation duration",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"rule", "type"},
		),
		validationErrors: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_validation_errors_total",
				Help: "Total validation errors",
			},
			[]string{"rule", "field", "type"},
		),
	}
}

// initializeRules initializes transformation rules
func (tm *TransformationManager) initializeRules() {
	for name, rule := range tm.config.Rules {
		tm.rules[name] = &rule

		tm.logger.Info("Transformation rule initialized",
			zap.String("rule", name),
			zap.Bool("enabled", rule.Enabled),
			zap.Int("priority", rule.Priority),
		)
	}
}

// TransformRequest transforms a request based on applicable rules
func (tm *TransformationManager) TransformRequest(request *http.Request) (*http.Request, error) {
	if !tm.config.Enabled || !tm.config.RequestTransform {
		return request, nil
	}

	start := time.Now()
	transformedRequest := request.Clone(request.Context())

	// Find applicable rules
	applicableRules := tm.findApplicableRules(request, "request")
	if len(applicableRules) == 0 {
		return request, nil
	}

	// Sort rules by priority
	tm.sortRulesByPriority(applicableRules)

	// Apply transformations
	for _, rule := range applicableRules {
		if err := tm.applyRequestTransform(transformedRequest, rule); err != nil {
			tm.handleTransformationError(rule, "request", err)
			if rule.ErrorHandling.OnError == "fail" {
				return nil, err
			}
		}
	}

	// Update metrics
	duration := time.Since(start)
	tm.metrics.transformationDuration.WithLabelValues("request", "request").Observe(duration.Seconds())
	tm.metrics.transformationsTotal.WithLabelValues("request", "request", "success").Inc()

	return transformedRequest, nil
}

// TransformResponse transforms a response based on applicable rules
func (tm *TransformationManager) TransformResponse(response *http.Response) (*http.Response, error) {
	if !tm.config.Enabled || !tm.config.ResponseTransform {
		return response, nil
	}

	start := time.Now()
	transformedResponse := response

	// Find applicable rules
	applicableRules := tm.findApplicableRules(response.Request, "response")
	if len(applicableRules) == 0 {
		return response, nil
	}

	// Sort rules by priority
	tm.sortRulesByPriority(applicableRules)

	// Apply transformations
	for _, rule := range applicableRules {
		if err := tm.applyResponseTransform(transformedResponse, rule); err != nil {
			tm.handleTransformationError(rule, "response", err)
			if rule.ErrorHandling.OnError == "fail" {
				return nil, err
			}
		}
	}

	// Update metrics
	duration := time.Since(start)
	tm.metrics.transformationDuration.WithLabelValues("response", "response").Observe(duration.Seconds())
	tm.metrics.transformationsTotal.WithLabelValues("response", "response", "success").Inc()

	return transformedResponse, nil
}

// findApplicableRules finds rules that apply to the request
func (tm *TransformationManager) findApplicableRules(request *http.Request, transformType string) []*TransformationRule {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	var applicableRules []*TransformationRule

	for _, rule := range tm.rules {
		if !rule.Enabled {
			continue
		}

		// Check if rule applies to this transformation type
		if transformType == "request" && rule.RequestTransform == nil {
			continue
		}
		if transformType == "response" && rule.ResponseTransform == nil {
			continue
		}

		// Check conditions
		if tm.evaluateConditions(request, rule.Conditions) {
			applicableRules = append(applicableRules, rule)
		}
	}

	return applicableRules
}

// evaluateConditions evaluates transformation conditions
func (tm *TransformationManager) evaluateConditions(request *http.Request, conditions []TransformationCondition) bool {
	for _, condition := range conditions {
		if !tm.evaluateCondition(request, condition) {
			return false
		}
	}
	return true
}

// evaluateCondition evaluates a single condition
func (tm *TransformationManager) evaluateCondition(request *http.Request, condition TransformationCondition) bool {
	var value string
	var exists bool

	switch condition.Type {
	case "path":
		value = request.URL.Path
		exists = true
	case "method":
		value = request.Method
		exists = true
	case "header":
		value = request.Header.Get(condition.Field)
		exists = value != ""
	case "query":
		value = request.URL.Query().Get(condition.Field)
		exists = value != ""
	default:
		return false
	}

	result := tm.compareValues(value, condition.Operator, condition.Value, exists)
	if condition.Negate {
		result = !result
	}

	return result
}

// compareValues compares values based on operator
func (tm *TransformationManager) compareValues(value, operator, expected string, exists bool) bool {
	switch operator {
	case "equals":
		return value == expected
	case "contains":
		return strings.Contains(value, expected)
	case "regex":
		matched, _ := regexp.MatchString(expected, value)
		return matched
	case "exists":
		return exists
	case "starts_with":
		return strings.HasPrefix(value, expected)
	case "ends_with":
		return strings.HasSuffix(value, expected)
	default:
		return false
	}
}

// sortRulesByPriority sorts rules by priority (highest first)
func (tm *TransformationManager) sortRulesByPriority(rules []*TransformationRule) {
	// Simple bubble sort for small lists
	for i := 0; i < len(rules)-1; i++ {
		for j := 0; j < len(rules)-i-1; j++ {
			if rules[j].Priority < rules[j+1].Priority {
				rules[j], rules[j+1] = rules[j+1], rules[j]
			}
		}
	}
}

// applyRequestTransform applies request transformation
func (tm *TransformationManager) applyRequestTransform(request *http.Request, rule *TransformationRule) error {
	if rule.RequestTransform == nil {
		return nil
	}

	transform := rule.RequestTransform

	// Transform headers
	if transform.Headers != nil {
		for key, value := range transform.Headers {
			request.Header.Set(key, value)
		}
	}

	// Transform query parameters
	if transform.QueryParams != nil {
		q := request.URL.Query()
		for key, value := range transform.QueryParams {
			q.Set(key, value)
		}
		request.URL.RawQuery = q.Encode()
	}

	// Transform method
	if transform.Method != "" {
		request.Method = transform.Method
	}

	// Transform URL
	if transform.URL != nil {
		if transform.URL.Path != "" {
			request.URL.Path = transform.URL.Path
		}
		if transform.URL.QueryParams != nil {
			q := request.URL.Query()
			for key, value := range transform.URL.QueryParams {
				q.Set(key, value)
			}
			request.URL.RawQuery = q.Encode()
		}
		if transform.URL.Fragment != "" {
			request.URL.Fragment = transform.URL.Fragment
		}
	}

	// Transform body
	if transform.Body != nil {
		if err := tm.transformRequestBody(request, transform.Body); err != nil {
			return fmt.Errorf("failed to transform request body: %w", err)
		}
	}

	// Apply custom transformations
	if transform.Custom != nil {
		for name, custom := range transform.Custom {
			if err := tm.applyCustomTransform(request, name, custom); err != nil {
				return fmt.Errorf("failed to apply custom transform %s: %w", name, err)
			}
		}
	}

	return nil
}

// applyResponseTransform applies response transformation
func (tm *TransformationManager) applyResponseTransform(response *http.Response, rule *TransformationRule) error {
	if rule.ResponseTransform == nil {
		return nil
	}

	transform := rule.ResponseTransform

	// Transform headers
	if transform.Headers != nil {
		for key, value := range transform.Headers {
			response.Header.Set(key, value)
		}
	}

	// Transform status code
	if transform.StatusCode != nil {
		if err := tm.transformStatusCode(response, transform.StatusCode); err != nil {
			return fmt.Errorf("failed to transform status code: %w", err)
		}
	}

	// Transform body
	if transform.Body != nil {
		if err := tm.transformResponseBody(response, transform.Body); err != nil {
			return fmt.Errorf("failed to transform response body: %w", err)
		}
	}

	// Apply custom transformations
	if transform.Custom != nil {
		for name, custom := range transform.Custom {
			if err := tm.applyCustomTransform(response, name, custom); err != nil {
				return fmt.Errorf("failed to apply custom transform %s: %w", name, err)
			}
		}
	}

	return nil
}

// transformRequestBody transforms request body
func (tm *TransformationManager) transformRequestBody(request *http.Request, bodyTransform *BodyTransform) error {
	if request.Body == nil {
		return nil
	}

	// Read body
	bodyBytes, err := io.ReadAll(request.Body)
	if err != nil {
		return err
	}
	request.Body.Close()

	// Validate body size
	if tm.config.MaxBodySize > 0 && int64(len(bodyBytes)) > tm.config.MaxBodySize {
		return fmt.Errorf("request body too large: %d bytes", len(bodyBytes))
	}

	// Transform based on type
	var transformedBody []byte
	switch bodyTransform.Type {
	case "json":
		transformedBody, err = tm.transformJSONBody(bodyBytes, bodyTransform)
	case "xml":
		transformedBody, err = tm.transformXMLBody(bodyBytes, bodyTransform)
	case "text":
		transformedBody, err = tm.transformTextBody(bodyBytes, bodyTransform)
	case "binary":
		transformedBody = bodyBytes // No transformation for binary
	default:
		return fmt.Errorf("unsupported body type: %s", bodyTransform.Type)
	}

	if err != nil {
		return err
	}

	// Validate transformed body
	if bodyTransform.Validation != nil {
		if err := tm.validateBody(transformedBody, bodyTransform.Validation); err != nil {
			return fmt.Errorf("body validation failed: %w", err)
		}
	}

	// Set new body
	request.Body = io.NopCloser(bytes.NewReader(transformedBody))
	request.ContentLength = int64(len(transformedBody))

	return nil
}

// transformResponseBody transforms response body
func (tm *TransformationManager) transformResponseBody(response *http.Response, bodyTransform *BodyTransform) error {
	if response.Body == nil {
		return nil
	}

	// Read body
	bodyBytes, err := io.ReadAll(response.Body)
	if err != nil {
		return err
	}
	response.Body.Close()

	// Transform based on type
	var transformedBody []byte
	switch bodyTransform.Type {
	case "json":
		transformedBody, err = tm.transformJSONBody(bodyBytes, bodyTransform)
	case "xml":
		transformedBody, err = tm.transformXMLBody(bodyBytes, bodyTransform)
	case "text":
		transformedBody, err = tm.transformTextBody(bodyBytes, bodyTransform)
	case "binary":
		transformedBody = bodyBytes // No transformation for binary
	default:
		return fmt.Errorf("unsupported body type: %s", bodyTransform.Type)
	}

	if err != nil {
		return err
	}

	// Validate transformed body
	if bodyTransform.Validation != nil {
		if err := tm.validateBody(transformedBody, bodyTransform.Validation); err != nil {
			return fmt.Errorf("body validation failed: %w", err)
		}
	}

	// Set new body
	response.Body = io.NopCloser(bytes.NewReader(transformedBody))
	response.ContentLength = int64(len(transformedBody))

	return nil
}

// transformJSONBody transforms JSON body
func (tm *TransformationManager) transformJSONBody(bodyBytes []byte, bodyTransform *BodyTransform) ([]byte, error) {
	var data interface{}
	if err := json.Unmarshal(bodyBytes, &data); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}

	// Apply template if specified
	if bodyTransform.Template != "" {
		tmpl, err := template.New("body").Parse(bodyTransform.Template)
		if err != nil {
			return nil, fmt.Errorf("failed to parse template: %w", err)
		}

		var buf bytes.Buffer
		if err := tmpl.Execute(&buf, data); err != nil {
			return nil, fmt.Errorf("failed to execute template: %w", err)
		}

		return buf.Bytes(), nil
	}

	// Apply variables if specified
	if bodyTransform.Variables != nil {
		// This is a simplified implementation
		// In a real implementation, you would apply variable substitution
		return bodyBytes, nil
	}

	return bodyBytes, nil
}

// transformXMLBody transforms XML body
func (tm *TransformationManager) transformXMLBody(bodyBytes []byte, bodyTransform *BodyTransform) ([]byte, error) {
	// Simplified XML transformation
	// In a real implementation, you would parse and transform XML
	return bodyBytes, nil
}

// transformTextBody transforms text body
func (tm *TransformationManager) transformTextBody(bodyBytes []byte, bodyTransform *BodyTransform) ([]byte, error) {
	text := string(bodyBytes)

	// Apply template if specified
	if bodyTransform.Template != "" {
		tmpl, err := template.New("body").Parse(bodyTransform.Template)
		if err != nil {
			return nil, fmt.Errorf("failed to parse template: %w", err)
		}

		var buf bytes.Buffer
		if err := tmpl.Execute(&buf, text); err != nil {
			return nil, fmt.Errorf("failed to execute template: %w", err)
		}

		return buf.Bytes(), nil
	}

	// Apply variables if specified
	if bodyTransform.Variables != nil {
		// This is a simplified implementation
		// In a real implementation, you would apply variable substitution
		return bodyBytes, nil
	}

	return bodyBytes, nil
}

// transformStatusCode transforms status code
func (tm *TransformationManager) transformStatusCode(response *http.Response, statusTransform *StatusCodeTransform) error {
	originalStatus := response.StatusCode

	// Check mapping first
	if statusTransform.Map != nil {
		if newStatus, exists := statusTransform.Map[originalStatus]; exists {
			response.StatusCode = newStatus
			return nil
		}
	}

	// Check conditions
	if statusTransform.Conditions != nil {
		for _, condition := range statusTransform.Conditions {
			if condition.From == originalStatus {
				response.StatusCode = condition.To
				return nil
			}
		}
	}

	// Use default if specified
	if statusTransform.Default > 0 {
		response.StatusCode = statusTransform.Default
	}

	return nil
}

// applyCustomTransform applies custom transformation
func (tm *TransformationManager) applyCustomTransform(obj interface{}, name string, custom CustomTransform) error {
	// This is a simplified implementation
	// In a real implementation, you would execute custom scripts or transformations
	tm.logger.Debug("Applying custom transform",
		zap.String("name", name),
		zap.String("type", custom.Type),
	)
	return nil
}

// validateBody validates transformed body
func (tm *TransformationManager) validateBody(bodyBytes []byte, validation *ValidationRule) error {
	// Check size validation
	if validation.Size != nil {
		if validation.Size.Max > 0 && int64(len(bodyBytes)) > validation.Size.Max {
			return fmt.Errorf("body size exceeds maximum: %d bytes", len(bodyBytes))
		}
		if validation.Size.Min > 0 && int64(len(bodyBytes)) < validation.Size.Min {
			return fmt.Errorf("body size below minimum: %d bytes", len(bodyBytes))
		}
	}

	// Check content validation
	if validation.Content != nil {
		contentType := http.DetectContentType(bodyBytes)
		if len(validation.Content.AllowedTypes) > 0 {
			allowed := false
			for _, allowedType := range validation.Content.AllowedTypes {
				if strings.Contains(contentType, allowedType) {
					allowed = true
					break
				}
			}
			if !allowed {
				return fmt.Errorf("content type not allowed: %s", contentType)
			}
		}
		if len(validation.Content.ForbiddenTypes) > 0 {
			for _, forbiddenType := range validation.Content.ForbiddenTypes {
				if strings.Contains(contentType, forbiddenType) {
					return fmt.Errorf("content type forbidden: %s", contentType)
				}
			}
		}
	}

	return nil
}

// handleTransformationError handles transformation errors
func (tm *TransformationManager) handleTransformationError(rule *TransformationRule, transformType string, err error) {
	tm.metrics.transformationErrors.WithLabelValues(rule.Name, transformType, err.Error()).Inc()

	if rule.ErrorHandling.LogErrors {
		tm.logger.Error("Transformation error",
			zap.String("rule", rule.Name),
			zap.String("type", transformType),
			zap.Error(err),
		)
	}
}

// GetStats returns transformation statistics
func (tm *TransformationManager) GetStats() map[string]interface{} {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	stats := make(map[string]interface{})
	for name, rule := range tm.rules {
		ruleStats := map[string]interface{}{
			"name":     name,
			"enabled":  rule.Enabled,
			"priority": rule.Priority,
		}
		stats[name] = ruleStats
	}

	return stats
}

// UpdateConfig updates the transformation configuration
func (tm *TransformationManager) UpdateConfig(config TransformationConfig) error {
	tm.config = config
	tm.initializeRules()
	tm.logger.Info("Transformation configuration updated")
	return nil
}
