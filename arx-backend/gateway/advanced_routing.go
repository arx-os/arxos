package gateway

import (
	"fmt"
	"net/http"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"go.uber.org/zap"
)

// AdvancedRouter manages advanced routing capabilities
type AdvancedRouter struct {
	config  AdvancedRoutingConfig
	logger  *zap.Logger
	rules   map[string]*RoutingRule
	mu      sync.RWMutex
	metrics *RoutingMetrics
}

// AdvancedRoutingConfig defines advanced routing configuration
type AdvancedRoutingConfig struct {
	Enabled        bool                   `yaml:"enabled"`
	DefaultService string                 `yaml:"default_service"`
	Rules          map[string]RoutingRule `yaml:"rules"`
	PathRewriting  PathRewritingConfig    `yaml:"path_rewriting"`
	QueryRouting   QueryRoutingConfig     `yaml:"query_routing"`
	HeaderRouting  HeaderRoutingConfig    `yaml:"header_routing"`
	CustomRouting  CustomRoutingConfig    `yaml:"custom_routing"`
	FallbackPolicy FallbackPolicy         `yaml:"fallback_policy"`
}

// RoutingRule defines an advanced routing rule
type RoutingRule struct {
	Name          string               `yaml:"name"`
	Enabled       bool                 `yaml:"enabled"`
	Priority      int                  `yaml:"priority"`
	Type          RoutingType          `yaml:"type"`
	Conditions    []RoutingCondition   `yaml:"conditions"`
	Actions       []RoutingAction      `yaml:"actions"`
	Service       string               `yaml:"service"`
	URL           string               `yaml:"url"`
	Timeout       time.Duration        `yaml:"timeout"`
	Retries       int                  `yaml:"retries"`
	LoadBalancing *LoadBalancingConfig `yaml:"load_balancing"`
	Transform     *TransformConfig     `yaml:"transform"`
	ErrorHandling ErrorHandling        `yaml:"error_handling"`
}

// RoutingType represents the type of routing rule
type RoutingType string

const (
	RoutingTypePath     RoutingType = "path"
	RoutingTypeQuery    RoutingType = "query"
	RoutingTypeHeader   RoutingType = "header"
	RoutingTypeCustom   RoutingType = "custom"
	RoutingTypeRegex    RoutingType = "regex"
	RoutingTypeWeighted RoutingType = "weighted"
)

// RoutingCondition defines conditions for routing
type RoutingCondition struct {
	Type          string `yaml:"type"` // path, method, header, query, ip, time
	Field         string `yaml:"field"`
	Operator      string `yaml:"operator"` // equals, contains, regex, exists, range
	Value         string `yaml:"value"`
	Value2        string `yaml:"value2"` // For range operations
	Negate        bool   `yaml:"negate"`
	CaseSensitive bool   `yaml:"case_sensitive"`
}

// RoutingAction defines actions to take when routing
type RoutingAction struct {
	Type       string            `yaml:"type"` // rewrite, redirect, proxy, transform
	Path       string            `yaml:"path"`
	Query      map[string]string `yaml:"query"`
	Headers    map[string]string `yaml:"headers"`
	StatusCode int               `yaml:"status_code"`
	Service    string            `yaml:"service"`
	URL        string            `yaml:"url"`
	Timeout    time.Duration     `yaml:"timeout"`
	Retries    int               `yaml:"retries"`
}

// PathRewritingConfig defines path rewriting configuration
type PathRewritingConfig struct {
	Enabled       bool                `yaml:"enabled"`
	Rules         map[string]PathRule `yaml:"rules"`
	PreserveQuery bool                `yaml:"preserve_query"`
	StripPrefix   bool                `yaml:"strip_prefix"`
	AddPrefix     string              `yaml:"add_prefix"`
}

// PathRule defines a path rewriting rule
type PathRule struct {
	Pattern     string             `yaml:"pattern"`
	Replacement string             `yaml:"replacement"`
	Regex       bool               `yaml:"regex"`
	Variables   map[string]string  `yaml:"variables"`
	Conditions  []RoutingCondition `yaml:"conditions"`
}

// QueryRoutingConfig defines query parameter routing configuration
type QueryRoutingConfig struct {
	Enabled          bool                 `yaml:"enabled"`
	Rules            map[string]QueryRule `yaml:"rules"`
	DefaultService   string               `yaml:"default_service"`
	ParameterMapping map[string]string    `yaml:"parameter_mapping"`
}

// QueryRule defines a query parameter routing rule
type QueryRule struct {
	Parameter     string            `yaml:"parameter"`
	Values        map[string]string `yaml:"values"`
	Default       string            `yaml:"default"`
	Regex         bool              `yaml:"regex"`
	CaseSensitive bool              `yaml:"case_sensitive"`
}

// HeaderRoutingConfig defines header-based routing configuration
type HeaderRoutingConfig struct {
	Enabled        bool                  `yaml:"enabled"`
	Rules          map[string]HeaderRule `yaml:"rules"`
	DefaultService string                `yaml:"default_service"`
	HeaderMapping  map[string]string     `yaml:"header_mapping"`
}

// HeaderRule defines a header-based routing rule
type HeaderRule struct {
	Header        string            `yaml:"header"`
	Values        map[string]string `yaml:"values"`
	Default       string            `yaml:"default"`
	Regex         bool              `yaml:"regex"`
	CaseSensitive bool              `yaml:"case_sensitive"`
}

// CustomRoutingConfig defines custom routing configuration
type CustomRoutingConfig struct {
	Enabled    bool                    `yaml:"enabled"`
	Scripts    map[string]CustomScript `yaml:"scripts"`
	Timeout    time.Duration           `yaml:"timeout"`
	MaxRetries int                     `yaml:"max_retries"`
}

// CustomScript defines a custom routing script
type CustomScript struct {
	Language   string            `yaml:"language"` // javascript, python, lua
	Script     string            `yaml:"script"`
	Parameters map[string]string `yaml:"parameters"`
	Timeout    time.Duration     `yaml:"timeout"`
	Cache      bool              `yaml:"cache"`
}

// FallbackPolicy defines fallback routing policy
type FallbackPolicy struct {
	Enabled    bool   `yaml:"enabled"`
	Service    string `yaml:"service"`
	StatusCode int    `yaml:"status_code"`
	Message    string `yaml:"message"`
	LogErrors  bool   `yaml:"log_errors"`
}

// RoutingMetrics holds routing metrics
type RoutingMetrics struct {
	requestsTotal    *prometheus.CounterVec
	routingDecisions *prometheus.CounterVec
	routingErrors    *prometheus.CounterVec
	routingDuration  *prometheus.HistogramVec
	fallbacksTotal   *prometheus.CounterVec
}

// NewAdvancedRouter creates a new advanced router
func NewAdvancedRouter(config AdvancedRoutingConfig) (*AdvancedRouter, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	ar := &AdvancedRouter{
		config: config,
		logger: logger,
		rules:  make(map[string]*RoutingRule),
	}

	// Initialize metrics
	ar.initializeMetrics()

	// Initialize rules
	ar.initializeRules()

	return ar, nil
}

// initializeMetrics initializes routing metrics
func (ar *AdvancedRouter) initializeMetrics() {
	ar.metrics = &RoutingMetrics{
		requestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_routing_requests_total",
				Help: "Total routing requests",
			},
			[]string{"rule", "service", "status"},
		),
		routingDecisions: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_routing_decisions_total",
				Help: "Total routing decisions",
			},
			[]string{"rule", "decision", "type"},
		),
		routingErrors: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_routing_errors_total",
				Help: "Total routing errors",
			},
			[]string{"rule", "error_type"},
		),
		routingDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_routing_duration_seconds",
				Help:    "Routing decision duration",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"rule", "type"},
		),
		fallbacksTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_routing_fallbacks_total",
				Help: "Total routing fallbacks",
			},
			[]string{"rule", "fallback_type"},
		),
	}
}

// initializeRules initializes routing rules
func (ar *AdvancedRouter) initializeRules() {
	for name, rule := range ar.config.Rules {
		ar.rules[name] = &rule

		ar.logger.Info("Routing rule initialized",
			zap.String("rule", name),
			zap.Bool("enabled", rule.Enabled),
			zap.Int("priority", rule.Priority),
			zap.String("type", string(rule.Type)),
		)
	}
}

// RouteRequest routes a request using advanced routing rules
func (ar *AdvancedRouter) RouteRequest(request *http.Request) (*RoutingResult, error) {
	if !ar.config.Enabled {
		return &RoutingResult{
			Service: ar.config.DefaultService,
			URL:     request.URL.String(),
		}, nil
	}

	start := time.Now()

	// Find applicable rules
	applicableRules := ar.findApplicableRules(request)
	if len(applicableRules) == 0 {
		// Use fallback
		return ar.handleFallback(request)
	}

	// Sort rules by priority
	ar.sortRulesByPriority(applicableRules)

	// Apply first matching rule
	for _, rule := range applicableRules {
		result, err := ar.applyRoutingRule(request, rule)
		if err != nil {
			ar.handleRoutingError(rule, err)
			continue
		}

		// Update metrics
		duration := time.Since(start)
		ar.metrics.routingDuration.WithLabelValues(rule.Name, string(rule.Type)).Observe(duration.Seconds())
		ar.metrics.routingDecisions.WithLabelValues(rule.Name, "success", string(rule.Type)).Inc()

		return result, nil
	}

	// No rules matched, use fallback
	return ar.handleFallback(request)
}

// RoutingResult represents the result of routing
type RoutingResult struct {
	Service    string
	URL        string
	Path       string
	Query      map[string]string
	Headers    map[string]string
	StatusCode int
	Actions    []RoutingAction
	Transform  *TransformConfig
	Timeout    time.Duration
	Retries    int
}

// findApplicableRules finds rules that apply to the request
func (ar *AdvancedRouter) findApplicableRules(request *http.Request) []*RoutingRule {
	ar.mu.RLock()
	defer ar.mu.RUnlock()

	var applicableRules []*RoutingRule

	for _, rule := range ar.rules {
		if !rule.Enabled {
			continue
		}

		// Check conditions
		if ar.evaluateRoutingConditions(request, rule.Conditions) {
			applicableRules = append(applicableRules, rule)
		}
	}

	return applicableRules
}

// evaluateRoutingConditions evaluates routing conditions
func (ar *AdvancedRouter) evaluateRoutingConditions(request *http.Request, conditions []RoutingCondition) bool {
	for _, condition := range conditions {
		if !ar.evaluateRoutingCondition(request, condition) {
			return false
		}
	}
	return true
}

// evaluateRoutingCondition evaluates a single routing condition
func (ar *AdvancedRouter) evaluateRoutingCondition(request *http.Request, condition RoutingCondition) bool {
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
	case "ip":
		value = ar.getClientIP(request)
		exists = value != ""
	case "time":
		value = time.Now().Format("15:04")
		exists = true
	default:
		return false
	}

	result := ar.compareRoutingValues(value, condition.Operator, condition.Value, condition.Value2, exists, condition.CaseSensitive)
	if condition.Negate {
		result = !result
	}

	return result
}

// compareRoutingValues compares values based on operator
func (ar *AdvancedRouter) compareRoutingValues(value, operator, expected, expected2 string, exists, caseSensitive bool) bool {
	// Handle case sensitivity
	if !caseSensitive {
		value = strings.ToLower(value)
		expected = strings.ToLower(expected)
		if expected2 != "" {
			expected2 = strings.ToLower(expected2)
		}
	}

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
	case "range":
		if expected2 == "" {
			return false
		}
		return value >= expected && value <= expected2
	case "in":
		values := strings.Split(expected, ",")
		for _, v := range values {
			if strings.TrimSpace(v) == value {
				return true
			}
		}
		return false
	default:
		return false
	}
}

// getClientIP gets the client IP address
func (ar *AdvancedRouter) getClientIP(request *http.Request) string {
	// Check X-Forwarded-For header
	if forwardedFor := request.Header.Get("X-Forwarded-For"); forwardedFor != "" {
		ips := strings.Split(forwardedFor, ",")
		if len(ips) > 0 {
			return strings.TrimSpace(ips[0])
		}
	}

	// Check X-Real-IP header
	if realIP := request.Header.Get("X-Real-IP"); realIP != "" {
		return realIP
	}

	// Use remote address
	return request.RemoteAddr
}

// sortRulesByPriority sorts rules by priority (highest first)
func (ar *AdvancedRouter) sortRulesByPriority(rules []*RoutingRule) {
	// Simple bubble sort for small lists
	for i := 0; i < len(rules)-1; i++ {
		for j := 0; j < len(rules)-i-1; j++ {
			if rules[j].Priority < rules[j+1].Priority {
				rules[j], rules[j+1] = rules[j+1], rules[j]
			}
		}
	}
}

// applyRoutingRule applies a routing rule
func (ar *AdvancedRouter) applyRoutingRule(request *http.Request, rule *RoutingRule) (*RoutingResult, error) {
	result := &RoutingResult{
		Service:   rule.Service,
		URL:       rule.URL,
		Path:      request.URL.Path,
		Query:     make(map[string]string),
		Headers:   make(map[string]string),
		Actions:   rule.Actions,
		Transform: rule.Transform,
		Timeout:   rule.Timeout,
		Retries:   rule.Retries,
	}

	// Copy query parameters
	for key, values := range request.URL.Query() {
		if len(values) > 0 {
			result.Query[key] = values[0]
		}
	}

	// Copy headers
	for key, values := range request.Header {
		if len(values) > 0 {
			result.Headers[key] = values[0]
		}
	}

	// Apply actions
	for _, action := range rule.Actions {
		if err := ar.applyRoutingAction(result, action); err != nil {
			return nil, fmt.Errorf("failed to apply routing action: %w", err)
		}
	}

	// Apply path rewriting
	if ar.config.PathRewriting.Enabled {
		if err := ar.applyPathRewriting(result, request); err != nil {
			return nil, fmt.Errorf("failed to apply path rewriting: %w", err)
		}
	}

	// Apply query routing
	if ar.config.QueryRouting.Enabled {
		if err := ar.applyQueryRouting(result, request); err != nil {
			return nil, fmt.Errorf("failed to apply query routing: %w", err)
		}
	}

	// Apply header routing
	if ar.config.HeaderRouting.Enabled {
		if err := ar.applyHeaderRouting(result, request); err != nil {
			return nil, fmt.Errorf("failed to apply header routing: %w", err)
		}
	}

	// Apply custom routing
	if ar.config.CustomRouting.Enabled {
		if err := ar.applyCustomRouting(result, request, rule); err != nil {
			return nil, fmt.Errorf("failed to apply custom routing: %w", err)
		}
	}

	return result, nil
}

// applyRoutingAction applies a routing action
func (ar *AdvancedRouter) applyRoutingAction(result *RoutingResult, action RoutingAction) error {
	switch action.Type {
	case "rewrite":
		if action.Path != "" {
			result.Path = action.Path
		}
		if action.Query != nil {
			for key, value := range action.Query {
				result.Query[key] = value
			}
		}
		if action.Headers != nil {
			for key, value := range action.Headers {
				result.Headers[key] = value
			}
		}
	case "redirect":
		if action.StatusCode > 0 {
			result.StatusCode = action.StatusCode
		}
		if action.URL != "" {
			result.URL = action.URL
		}
	case "proxy":
		if action.Service != "" {
			result.Service = action.Service
		}
		if action.URL != "" {
			result.URL = action.URL
		}
		if action.Timeout > 0 {
			result.Timeout = action.Timeout
		}
		if action.Retries > 0 {
			result.Retries = action.Retries
		}
	case "transform":
		// Apply transformation
		if result.Transform == nil {
			result.Transform = &TransformConfig{}
		}
		// Merge transformation configs
		// This is a simplified implementation
	}

	return nil
}

// applyPathRewriting applies path rewriting
func (ar *AdvancedRouter) applyPathRewriting(result *RoutingResult, request *http.Request) error {
	config := ar.config.PathRewriting

	// Add prefix if specified
	if config.AddPrefix != "" {
		result.Path = config.AddPrefix + result.Path
	}

	// Strip prefix if specified
	if config.StripPrefix {
		// This is a simplified implementation
		// In a real implementation, you would strip the prefix based on configuration
	}

	// Apply path rules
	for _, rule := range config.Rules {
		if ar.evaluateRoutingConditions(request, rule.Conditions) {
			if rule.Regex {
				re, err := regexp.Compile(rule.Pattern)
				if err != nil {
					return fmt.Errorf("invalid regex pattern: %w", err)
				}
				result.Path = re.ReplaceAllString(result.Path, rule.Replacement)
			} else {
				result.Path = strings.ReplaceAll(result.Path, rule.Pattern, rule.Replacement)
			}
		}
	}

	return nil
}

// applyQueryRouting applies query parameter routing
func (ar *AdvancedRouter) applyQueryRouting(result *RoutingResult, request *http.Request) error {
	config := ar.config.QueryRouting

	for _, rule := range config.Rules {
		value := request.URL.Query().Get(rule.Parameter)
		if value == "" {
			continue
		}

		// Check if value matches any routing rule
		for queryValue, service := range rule.Values {
			if rule.Regex {
				matched, _ := regexp.MatchString(queryValue, value)
				if matched {
					result.Service = service
					return nil
				}
			} else {
				if rule.CaseSensitive {
					if value == queryValue {
						result.Service = service
						return nil
					}
				} else {
					if strings.EqualFold(value, queryValue) {
						result.Service = service
						return nil
					}
				}
			}
		}

		// Use default if specified
		if rule.Default != "" {
			result.Service = rule.Default
		}
	}

	return nil
}

// applyHeaderRouting applies header-based routing
func (ar *AdvancedRouter) applyHeaderRouting(result *RoutingResult, request *http.Request) error {
	config := ar.config.HeaderRouting

	for _, rule := range config.Rules {
		value := request.Header.Get(rule.Header)
		if value == "" {
			continue
		}

		// Check if value matches any routing rule
		for headerValue, service := range rule.Values {
			if rule.Regex {
				matched, _ := regexp.MatchString(headerValue, value)
				if matched {
					result.Service = service
					return nil
				}
			} else {
				if rule.CaseSensitive {
					if value == headerValue {
						result.Service = service
						return nil
					}
				} else {
					if strings.EqualFold(value, headerValue) {
						result.Service = service
						return nil
					}
				}
			}
		}

		// Use default if specified
		if rule.Default != "" {
			result.Service = rule.Default
		}
	}

	return nil
}

// applyCustomRouting applies custom routing
func (ar *AdvancedRouter) applyCustomRouting(result *RoutingResult, request *http.Request, rule *RoutingRule) error {
	if rule.Type != RoutingTypeCustom {
		return nil
	}

	// This is a simplified implementation
	// In a real implementation, you would execute custom scripts
	ar.logger.Debug("Applying custom routing",
		zap.String("rule", rule.Name),
		zap.String("service", result.Service),
	)

	return nil
}

// handleFallback handles routing fallback
func (ar *AdvancedRouter) handleFallback(request *http.Request) (*RoutingResult, error) {
	if !ar.config.FallbackPolicy.Enabled {
		return nil, fmt.Errorf("no routing rule matched and fallback disabled")
	}

	ar.metrics.fallbacksTotal.WithLabelValues("default", "no_rule_match").Inc()

	if ar.config.FallbackPolicy.LogErrors {
		ar.logger.Warn("No routing rule matched, using fallback",
			zap.String("path", request.URL.Path),
			zap.String("method", request.Method),
		)
	}

	return &RoutingResult{
		Service:    ar.config.FallbackPolicy.Service,
		URL:        request.URL.String(),
		Path:       request.URL.Path,
		StatusCode: ar.config.FallbackPolicy.StatusCode,
	}, nil
}

// handleRoutingError handles routing errors
func (ar *AdvancedRouter) handleRoutingError(rule *RoutingRule, err error) {
	ar.metrics.routingErrors.WithLabelValues(rule.Name, err.Error()).Inc()

	if rule.ErrorHandling.LogErrors {
		ar.logger.Error("Routing error",
			zap.String("rule", rule.Name),
			zap.Error(err),
		)
	}
}

// GetStats returns routing statistics
func (ar *AdvancedRouter) GetStats() map[string]interface{} {
	ar.mu.RLock()
	defer ar.mu.RUnlock()

	stats := make(map[string]interface{})
	for name, rule := range ar.rules {
		ruleStats := map[string]interface{}{
			"name":     name,
			"enabled":  rule.Enabled,
			"priority": rule.Priority,
			"type":     string(rule.Type),
			"service":  rule.Service,
		}
		stats[name] = ruleStats
	}

	return stats
}

// UpdateConfig updates the routing configuration
func (ar *AdvancedRouter) UpdateConfig(config AdvancedRoutingConfig) error {
	ar.config = config
	ar.initializeRules()
	ar.logger.Info("Advanced routing configuration updated")
	return nil
}
