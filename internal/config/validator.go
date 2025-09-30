package config

import (
	"fmt"
	"net/url"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// ConfigValidator validates configuration values
type ConfigValidator struct {
	errors []ValidationError
}

// ValidationError represents a configuration validation error
type ValidationError struct {
	Field   string `json:"field"`
	Value   string `json:"value"`
	Message string `json:"message"`
	Code    string `json:"code"`
}

// NewConfigValidator creates a new configuration validator
func NewConfigValidator() *ConfigValidator {
	return &ConfigValidator{
		errors: make([]ValidationError, 0),
	}
}

// Validate validates a configuration
func (cv *ConfigValidator) Validate(config *Config) []ValidationError {
	cv.errors = make([]ValidationError, 0)

	// Validate basic structure
	cv.validateBasicStructure(config)

	// Validate environment-specific settings
	cv.validateEnvironmentSettings(config)

	// Validate database configuration
	cv.validateDatabaseConfig(config)

	// Validate API configuration
	cv.validateAPIConfig(config)

	// Validate security settings
	cv.validateSecurityConfig(config)

	// Validate feature flags
	cv.validateFeatureFlags(config)

	// Validate telemetry settings
	cv.validateTelemetryConfig(config)

	// Validate storage settings
	cv.validateStorageConfig(config)

	// Validate TUI settings
	cv.validateTUIConfig(config)

	return cv.errors
}

// ValidateTemplate validates a configuration template
func (cv *ConfigValidator) ValidateTemplate(template *ConfigTemplate) []ValidationError {
	cv.errors = make([]ValidationError, 0)

	// Validate template structure
	cv.validateTemplateStructure(template)

	// Validate template variables
	cv.validateTemplateVariables(template)

	// Validate template configuration
	cv.validateTemplateConfig(template)

	return cv.errors
}

// HasErrors returns true if there are validation errors
func (cv *ConfigValidator) HasErrors() bool {
	return len(cv.errors) > 0
}

// GetErrors returns all validation errors
func (cv *ConfigValidator) GetErrors() []ValidationError {
	return cv.errors
}

// Private validation methods

func (cv *ConfigValidator) validateBasicStructure(config *Config) {
	if config == nil {
		cv.addError("config", "", "Configuration cannot be nil", "CONFIG_NIL")
		return
	}

	if config.Mode == "" {
		cv.addError("mode", "", "Mode is required", "MODE_REQUIRED")
	}
}

func (cv *ConfigValidator) validateEnvironmentSettings(config *Config) {
	// Validate mode
	if !isValidMode(string(config.Mode)) {
		cv.addError("mode", string(config.Mode), "Invalid mode", "INVALID_MODE")
	}

	// Validate environment-specific settings
	envConfig := GetEnvironmentConfig()
	if envConfig == nil {
		cv.addError("environment", "", "Environment configuration not found", "ENVIRONMENT_CONFIG_NOT_FOUND")
		return
	}
}

func (cv *ConfigValidator) validateDatabaseConfig(config *Config) {
	// Validate host
	if config.PostGIS.Host == "" {
		cv.addError("postgis.host", "", "Database host is required", "DB_HOST_REQUIRED")
	}

	// Validate port
	if config.PostGIS.Port <= 0 || config.PostGIS.Port > 65535 {
		cv.addError("postgis.port", fmt.Sprintf("%d", config.PostGIS.Port), "Database port must be between 1 and 65535", "INVALID_DB_PORT")
	}

	// Validate database name
	if config.PostGIS.Database == "" {
		cv.addError("postgis.database", "", "Database name is required", "DB_NAME_REQUIRED")
	}

	// Validate user
	if config.PostGIS.User == "" {
		cv.addError("postgis.user", "", "Database user is required", "DB_USER_REQUIRED")
	}

	// Validate SSL mode
	if config.PostGIS.SSLMode != "" && !isValidSSLMode(config.PostGIS.SSLMode) {
		cv.addError("postgis.ssl_mode", config.PostGIS.SSLMode, "Invalid SSL mode", "INVALID_SSL_MODE")
	}

	// Validate SRID
	if config.PostGIS.SRID <= 0 {
		cv.addError("postgis.srid", fmt.Sprintf("%d", config.PostGIS.SRID), "SRID must be positive", "INVALID_SRID")
	}
}

func (cv *ConfigValidator) validateAPIConfig(config *Config) {
	// Validate timeout
	if config.API.Timeout < 1*time.Second {
		cv.addError("api.timeout", config.API.Timeout.String(), "API timeout must be at least 1 second", "INVALID_API_TIMEOUT")
	}

	// Validate retry attempts
	if config.API.RetryAttempts < 0 {
		cv.addError("api.retry_attempts", fmt.Sprintf("%d", config.API.RetryAttempts), "Retry attempts cannot be negative", "INVALID_RETRY_ATTEMPTS")
	}

	// Validate retry delay
	if config.API.RetryDelay < 0 {
		cv.addError("api.retry_delay", config.API.RetryDelay.String(), "Retry delay cannot be negative", "INVALID_RETRY_DELAY")
	}

	// Validate user agent
	if config.API.UserAgent == "" {
		cv.addError("api.user_agent", "", "User agent is required", "USER_AGENT_REQUIRED")
	}
}

func (cv *ConfigValidator) validateSecurityConfig(config *Config) {
	// Validate JWT expiry
	if config.Security.JWTExpiry < 1*time.Minute {
		cv.addError("security.jwt_expiry", config.Security.JWTExpiry.String(), "JWT expiry must be at least 1 minute", "INVALID_JWT_EXPIRY")
	}

	// Validate session timeout
	if config.Security.SessionTimeout < 1*time.Minute {
		cv.addError("security.session_timeout", config.Security.SessionTimeout.String(), "Session timeout must be at least 1 minute", "INVALID_SESSION_TIMEOUT")
	}

	// Validate API rate limit
	if config.Security.APIRateLimit < 0 {
		cv.addError("security.api_rate_limit", fmt.Sprintf("%d", config.Security.APIRateLimit), "API rate limit cannot be negative", "INVALID_API_RATE_LIMIT")
	}

	// Validate API rate limit window
	if config.Security.APIRateLimitWindow < 1*time.Second {
		cv.addError("security.api_rate_limit_window", config.Security.APIRateLimitWindow.String(), "API rate limit window must be at least 1 second", "INVALID_API_RATE_LIMIT_WINDOW")
	}

	// Validate TLS settings
	if config.Security.EnableTLS {
		if config.Security.TLSCertPath == "" {
			cv.addError("security.tls_cert_path", "", "TLS cert path is required when TLS is enabled", "TLS_CERT_PATH_REQUIRED")
		}
	}

	// Validate CORS settings
	if len(config.Security.AllowedOrigins) == 0 {
		cv.addError("security.allowed_origins", "", "At least one CORS origin must be specified", "CORS_ORIGINS_REQUIRED")
	}

	for i, origin := range config.Security.AllowedOrigins {
		if origin != "*" {
			if validationErr := cv.validateURL(origin, fmt.Sprintf("security.allowed_origins[%d]", i)); validationErr.Field != "" {
				cv.errors = append(cv.errors, validationErr)
			}
		}
	}

	// Validate bcrypt cost
	if config.Security.BcryptCost < 4 || config.Security.BcryptCost > 31 {
		cv.addError("security.bcrypt_cost", fmt.Sprintf("%d", config.Security.BcryptCost), "Bcrypt cost must be between 4 and 31", "INVALID_BCRYPT_COST")
	}
}

func (cv *ConfigValidator) validateFeatureFlags(config *Config) {
	// Feature flags validation is handled by the struct tags
	// No additional validation needed for boolean flags
}

func (cv *ConfigValidator) validateTelemetryConfig(config *Config) {
	// Validate telemetry endpoint if provided
	if config.Telemetry.Endpoint != "" {
		if validationErr := cv.validateURL(config.Telemetry.Endpoint, "telemetry.endpoint"); validationErr.Field != "" {
			cv.errors = append(cv.errors, validationErr)
		}
	}

	// Validate sample rate
	if config.Telemetry.SampleRate < 0.0 || config.Telemetry.SampleRate > 1.0 {
		cv.addError("telemetry.sample_rate", fmt.Sprintf("%f", config.Telemetry.SampleRate), "Sample rate must be between 0.0 and 1.0", "INVALID_SAMPLE_RATE")
	}

	// Validate anonymous ID
	if config.Telemetry.Enabled && config.Telemetry.AnonymousID == "" {
		cv.addError("telemetry.anonymous_id", "", "Anonymous ID is required when telemetry is enabled", "ANONYMOUS_ID_REQUIRED")
	}
}

func (cv *ConfigValidator) validateStorageConfig(config *Config) {
	// Validate storage backend
	if config.Storage.Backend == "" {
		cv.addError("storage.backend", "", "Storage backend is required", "STORAGE_BACKEND_REQUIRED")
	}

	// Validate local path if using local backend
	if config.Storage.Backend == "local" {
		if config.Storage.LocalPath == "" {
			cv.addError("storage.local_path", "", "Local path is required for local storage backend", "LOCAL_PATH_REQUIRED")
		} else if !filepath.IsAbs(config.Storage.LocalPath) {
			cv.addError("storage.local_path", config.Storage.LocalPath, "Local path must be absolute", "INVALID_LOCAL_PATH")
		}
	}

	// Validate cloud settings if using cloud backend
	if config.Storage.Backend != "local" {
		if config.Storage.CloudBucket == "" {
			cv.addError("storage.cloud_bucket", "", "Cloud bucket is required for cloud storage backend", "CLOUD_BUCKET_REQUIRED")
		}
		if config.Storage.CloudRegion == "" {
			cv.addError("storage.cloud_region", "", "Cloud region is required for cloud storage backend", "CLOUD_REGION_REQUIRED")
		}
	}
}

func (cv *ConfigValidator) validateTUIConfig(config *Config) {
	// Validate TUI theme
	if config.TUI.Theme != "" && !isValidTUITheme(config.TUI.Theme) {
		cv.addError("tui.theme", config.TUI.Theme, "Invalid TUI theme", "INVALID_TUI_THEME")
	}

	// Validate update interval
	if config.TUI.UpdateInterval != "" {
		if _, err := time.ParseDuration(config.TUI.UpdateInterval); err != nil {
			cv.addError("tui.update_interval", config.TUI.UpdateInterval, "Invalid update interval format", "INVALID_UPDATE_INTERVAL")
		}
	}

	// Validate max equipment display
	if config.TUI.MaxEquipmentDisplay <= 0 {
		cv.addError("tui.max_equipment_display", fmt.Sprintf("%d", config.TUI.MaxEquipmentDisplay), "Max equipment display must be positive", "INVALID_MAX_EQUIPMENT_DISPLAY")
	}

	// Validate spatial precision
	if config.TUI.SpatialPrecision != "" && !isValidSpatialPrecision(config.TUI.SpatialPrecision) {
		cv.addError("tui.spatial_precision", config.TUI.SpatialPrecision, "Invalid spatial precision", "INVALID_SPATIAL_PRECISION")
	}

	// Validate grid scale
	if config.TUI.GridScale != "" && !isValidGridScale(config.TUI.GridScale) {
		cv.addError("tui.grid_scale", config.TUI.GridScale, "Invalid grid scale", "INVALID_GRID_SCALE")
	}

	// Validate viewport size
	if config.TUI.ViewportSize <= 0 {
		cv.addError("tui.viewport_size", fmt.Sprintf("%d", config.TUI.ViewportSize), "Viewport size must be positive", "INVALID_VIEWPORT_SIZE")
	}

	// Validate refresh rate
	if config.TUI.RefreshRate <= 0 {
		cv.addError("tui.refresh_rate", fmt.Sprintf("%d", config.TUI.RefreshRate), "Refresh rate must be positive", "INVALID_REFRESH_RATE")
	}
}

func (cv *ConfigValidator) validateTemplateStructure(template *ConfigTemplate) {
	if template == nil {
		cv.addError("template", "", "Template cannot be nil", "TEMPLATE_NIL")
		return
	}

	if template.Name == "" {
		cv.addError("template.name", "", "Template name is required", "TEMPLATE_NAME_REQUIRED")
	}

	if template.Description == "" {
		cv.addError("template.description", "", "Template description is required", "TEMPLATE_DESCRIPTION_REQUIRED")
	}

	if template.Environment == "" {
		cv.addError("template.environment", "", "Template environment is required", "TEMPLATE_ENVIRONMENT_REQUIRED")
	}

	if template.Config == nil {
		cv.addError("template.config", "", "Template configuration is required", "TEMPLATE_CONFIG_REQUIRED")
	}
}

func (cv *ConfigValidator) validateTemplateVariables(template *ConfigTemplate) {
	if template.Variables == nil {
		return
	}

	for i, variable := range template.Variables {
		if variable.Name == "" {
			cv.addError(fmt.Sprintf("template.variables[%d].name", i), "", "Variable name is required", "VARIABLE_NAME_REQUIRED")
		}

		if variable.Description == "" {
			cv.addError(fmt.Sprintf("template.variables[%d].description", i), "", "Variable description is required", "VARIABLE_DESCRIPTION_REQUIRED")
		}

		if variable.Type != "" && !isValidVariableType(variable.Type) {
			cv.addError(fmt.Sprintf("template.variables[%d].type", i), variable.Type, "Invalid variable type", "INVALID_VARIABLE_TYPE")
		}
	}
}

func (cv *ConfigValidator) validateTemplateConfig(template *ConfigTemplate) {
	if template.Config == nil {
		return
	}

	// Validate that all template variables are used in the config
	usedVariables := make(map[string]bool)
	cv.findUsedVariables(template.Config, usedVariables)

	for _, variable := range template.Variables {
		if !usedVariables[variable.Name] {
			cv.addError("template.variables", variable.Name, fmt.Sprintf("Variable '%s' is defined but not used in configuration", variable.Name), "UNUSED_VARIABLE")
		}
	}
}

func (cv *ConfigValidator) findUsedVariables(config interface{}, usedVariables map[string]bool) {
	switch v := config.(type) {
	case string:
		// Find template variables in string values
		re := regexp.MustCompile(`\{\{([^}]+)\}\}`)
		matches := re.FindAllStringSubmatch(v, -1)
		for _, match := range matches {
			if len(match) > 1 {
				usedVariables[strings.TrimSpace(match[1])] = true
			}
		}
	case map[string]interface{}:
		for _, value := range v {
			cv.findUsedVariables(value, usedVariables)
		}
	case []interface{}:
		for _, value := range v {
			cv.findUsedVariables(value, usedVariables)
		}
	}
}

func (cv *ConfigValidator) validateURL(urlStr, field string) ValidationError {
	if urlStr == "" {
		return ValidationError{Field: field, Value: urlStr, Message: "URL cannot be empty", Code: "URL_EMPTY"}
	}

	// Add protocol if missing
	if !strings.HasPrefix(urlStr, "http://") && !strings.HasPrefix(urlStr, "https://") {
		urlStr = "https://" + urlStr
	}

	parsedURL, err := url.Parse(urlStr)
	if err != nil {
		return ValidationError{Field: field, Value: urlStr, Message: "Invalid URL format", Code: "INVALID_URL"}
	}

	if parsedURL.Host == "" {
		return ValidationError{Field: field, Value: urlStr, Message: "URL must have a host", Code: "URL_NO_HOST"}
	}

	return ValidationError{} // No error
}

func (cv *ConfigValidator) addError(field, value, message, code string) {
	cv.errors = append(cv.errors, ValidationError{
		Field:   field,
		Value:   value,
		Message: message,
		Code:    code,
	})
}

// Helper functions

func isValidEnvironment(env Environment) bool {
	switch env {
	case EnvDevelopment, EnvStaging, EnvInternal, EnvProduction:
		return true
	default:
		return false
	}
}

func isValidMode(mode string) bool {
	switch mode {
	case "local", "hybrid", "cloud":
		return true
	default:
		return false
	}
}

func isValidSSLMode(sslMode string) bool {
	switch sslMode {
	case "disable", "allow", "prefer", "require", "verify-ca", "verify-full":
		return true
	default:
		return false
	}
}

func isValidTUITheme(theme string) bool {
	switch theme {
	case "dark", "light", "auto":
		return true
	default:
		return false
	}
}

func isValidSpatialPrecision(precision string) bool {
	switch precision {
	case "1mm", "1cm", "10cm", "1m":
		return true
	default:
		return false
	}
}

func isValidGridScale(scale string) bool {
	switch scale {
	case "1:5", "1:10", "1:20", "1:50", "1:100":
		return true
	default:
		return false
	}
}

func isValidVariableType(varType string) bool {
	switch varType {
	case "string", "int", "float", "bool", "duration":
		return true
	default:
		return false
	}
}
