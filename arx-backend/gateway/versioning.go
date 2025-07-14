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

// VersionManager manages API versioning and routing
type VersionManager struct {
	config   VersionConfig
	logger   *zap.Logger
	versions map[string]*APIVersion
	mu       sync.RWMutex
	metrics  *VersionMetrics
}

// VersionConfig defines versioning configuration
type VersionConfig struct {
	Enabled           bool                   `yaml:"enabled"`
	DefaultVersion    string                 `yaml:"default_version"`
	VersionHeader     string                 `yaml:"version_header"`
	URLPattern        string                 `yaml:"url_pattern"`
	Versions          map[string]VersionInfo `yaml:"versions"`
	DeprecationPolicy DeprecationPolicy      `yaml:"deprecation_policy"`
	MigrationPolicy   MigrationPolicy        `yaml:"migration_policy"`
}

// VersionInfo defines information about an API version
type VersionInfo struct {
	Version         string           `yaml:"version"`
	Status          VersionStatus    `yaml:"status"`
	ReleaseDate     time.Time        `yaml:"release_date"`
	DeprecationDate *time.Time       `yaml:"deprecation_date"`
	EndOfLifeDate   *time.Time       `yaml:"end_of_life_date"`
	Service         string           `yaml:"service"`
	URL             string           `yaml:"url"`
	Routes          []VersionRoute   `yaml:"routes"`
	Documentation   string           `yaml:"documentation"`
	BreakingChanges []BreakingChange `yaml:"breaking_changes"`
}

// VersionStatus represents the status of an API version
type VersionStatus string

const (
	VersionStatusAlpha      VersionStatus = "alpha"
	VersionStatusBeta       VersionStatus = "beta"
	VersionStatusStable     VersionStatus = "stable"
	VersionStatusDeprecated VersionStatus = "deprecated"
	VersionStatusEOL        VersionStatus = "end_of_life"
)

// VersionRoute defines a route for a specific version
type VersionRoute struct {
	Path        string           `yaml:"path"`
	Methods     []string         `yaml:"methods"`
	Auth        bool             `yaml:"auth"`
	RateLimit   *RateLimitConfig `yaml:"rate_limit"`
	Transform   *TransformConfig `yaml:"transform"`
	Deprecated  bool             `yaml:"deprecated"`
	Replacement string           `yaml:"replacement"`
}

// BreakingChange represents a breaking change in an API version
type BreakingChange struct {
	Type        string    `yaml:"type"`
	Description string    `yaml:"description"`
	Date        time.Time `yaml:"date"`
	Migration   string    `yaml:"migration"`
}

// DeprecationPolicy defines how deprecation is handled
type DeprecationPolicy struct {
	Enabled           bool          `yaml:"enabled"`
	WarningHeader     string        `yaml:"warning_header"`
	WarningMessage    string        `yaml:"warning_message"`
	GracePeriod       time.Duration `yaml:"grace_period"`
	DeprecationHeader string        `yaml:"deprecation_header"`
	LogDeprecation    bool          `yaml:"log_deprecation"`
}

// MigrationPolicy defines how version migration is handled
type MigrationPolicy struct {
	Enabled          bool          `yaml:"enabled"`
	AutoMigration    bool          `yaml:"auto_migration"`
	MigrationHeader  string        `yaml:"migration_header"`
	MigrationMessage string        `yaml:"migration_message"`
	MigrationTimeout time.Duration `yaml:"migration_timeout"`
	RollbackEnabled  bool          `yaml:"rollback_enabled"`
}

// APIVersion represents an API version instance
type APIVersion struct {
	Info      VersionInfo
	Service   string
	URL       string
	Routes    map[string]*VersionRoute
	Status    VersionStatus
	CreatedAt time.Time
	UpdatedAt time.Time
	mu        sync.RWMutex
}

// VersionMetrics holds versioning metrics
type VersionMetrics struct {
	requestsTotal       *prometheus.CounterVec
	deprecationWarnings *prometheus.CounterVec
	migrationsTotal     *prometheus.CounterVec
	versionUsage        *prometheus.GaugeVec
}

// NewVersionManager creates a new version manager
func NewVersionManager(config VersionConfig) (*VersionManager, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	vm := &VersionManager{
		config:   config,
		logger:   logger,
		versions: make(map[string]*APIVersion),
	}

	// Initialize metrics
	vm.initializeMetrics()

	// Initialize versions
	vm.initializeVersions()

	return vm, nil
}

// initializeMetrics initializes versioning metrics
func (vm *VersionManager) initializeMetrics() {
	vm.metrics = &VersionMetrics{
		requestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_version_requests_total",
				Help: "Total requests by API version",
			},
			[]string{"version", "status", "route"},
		),
		deprecationWarnings: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_version_deprecation_warnings_total",
				Help: "Total deprecation warnings",
			},
			[]string{"version", "route"},
		),
		migrationsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_version_migrations_total",
				Help: "Total version migrations",
			},
			[]string{"from_version", "to_version"},
		),
		versionUsage: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_version_usage",
				Help: "API version usage",
			},
			[]string{"version", "status"},
		),
	}
}

// initializeVersions initializes API versions from configuration
func (vm *VersionManager) initializeVersions() {
	for version, info := range vm.config.Versions {
		apiVersion := &APIVersion{
			Info:      info,
			Service:   info.Service,
			URL:       info.URL,
			Routes:    make(map[string]*VersionRoute),
			Status:    info.Status,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		// Initialize routes
		for _, route := range info.Routes {
			apiVersion.Routes[route.Path] = &route
		}

		vm.versions[version] = apiVersion

		vm.logger.Info("API version initialized",
			zap.String("version", version),
			zap.String("status", string(info.Status)),
			zap.String("service", info.Service),
		)
	}
}

// GetVersion extracts version from request
func (vm *VersionManager) GetVersion(request *http.Request) (string, error) {
	if !vm.config.Enabled {
		return vm.config.DefaultVersion, nil
	}

	// Try header first
	if vm.config.VersionHeader != "" {
		if version := request.Header.Get(vm.config.VersionHeader); version != "" {
			return vm.normalizeVersion(version), nil
		}
	}

	// Try URL pattern
	if vm.config.URLPattern != "" {
		if version := vm.extractVersionFromURL(request.URL.Path); version != "" {
			return version, nil
		}
	}

	// Try Accept header
	if accept := request.Header.Get("Accept"); accept != "" {
		if version := vm.extractVersionFromAccept(accept); version != "" {
			return version, nil
		}
	}

	// Return default version
	return vm.config.DefaultVersion, nil
}

// normalizeVersion normalizes version string
func (vm *VersionManager) normalizeVersion(version string) string {
	// Remove 'v' prefix if present
	if strings.HasPrefix(version, "v") {
		version = version[1:]
	}
	return version
}

// extractVersionFromURL extracts version from URL path
func (vm *VersionManager) extractVersionFromURL(path string) string {
	// Pattern: /api/v1/users -> v1
	pattern := regexp.MustCompile(`/api/v(\d+)/`)
	matches := pattern.FindStringSubmatch(path)
	if len(matches) > 1 {
		return matches[1]
	}
	return ""
}

// extractVersionFromAccept extracts version from Accept header
func (vm *VersionManager) extractVersionFromAccept(accept string) string {
	// Pattern: application/vnd.api+json;version=1.0
	pattern := regexp.MustCompile(`version=(\d+(?:\.\d+)?)`)
	matches := pattern.FindStringSubmatch(accept)
	if len(matches) > 1 {
		return matches[1]
	}
	return ""
}

// GetVersionInfo gets information about a specific version
func (vm *VersionManager) GetVersionInfo(version string) (*APIVersion, error) {
	vm.mu.RLock()
	defer vm.mu.RUnlock()

	apiVersion, exists := vm.versions[version]
	if !exists {
		return nil, fmt.Errorf("version %s not found", version)
	}

	return apiVersion, nil
}

// IsVersionDeprecated checks if a version is deprecated
func (vm *VersionManager) IsVersionDeprecated(version string) bool {
	apiVersion, err := vm.GetVersionInfo(version)
	if err != nil {
		return false
	}

	return apiVersion.Status == VersionStatusDeprecated || apiVersion.Status == VersionStatusEOL
}

// IsVersionEOL checks if a version is end-of-life
func (vm *VersionManager) IsVersionEOL(version string) bool {
	apiVersion, err := vm.GetVersionInfo(version)
	if err != nil {
		return false
	}

	return apiVersion.Status == VersionStatusEOL
}

// GetDeprecationWarning gets deprecation warning for a version
func (vm *VersionManager) GetDeprecationWarning(version string) string {
	apiVersion, err := vm.GetVersionInfo(version)
	if err != nil {
		return ""
	}

	if apiVersion.Status != VersionStatusDeprecated {
		return ""
	}

	if vm.config.DeprecationPolicy.WarningMessage != "" {
		return vm.config.DeprecationPolicy.WarningMessage
	}

	return fmt.Sprintf("API version %s is deprecated. Please upgrade to a newer version.", version)
}

// GetMigrationInfo gets migration information for a version
func (vm *VersionManager) GetMigrationInfo(version string) (string, error) {
	apiVersion, err := vm.GetVersionInfo(version)
	if err != nil {
		return "", err
	}

	// Find the next stable version
	nextVersion := vm.findNextStableVersion(version)
	if nextVersion == "" {
		return "", fmt.Errorf("no migration path available for version %s", version)
	}

	return fmt.Sprintf("Migrate from version %s to version %s", version, nextVersion), nil
}

// findNextStableVersion finds the next stable version
func (vm *VersionManager) findNextStableVersion(currentVersion string) string {
	vm.mu.RLock()
	defer vm.mu.RUnlock()

	var nextVersion string
	var currentMajor int

	// Parse current version major number
	if _, err := fmt.Sscanf(currentVersion, "%d", &currentMajor); err != nil {
		return ""
	}

	// Find the next stable version
	for version, apiVersion := range vm.versions {
		if apiVersion.Status != VersionStatusStable {
			continue
		}

		var major int
		if _, err := fmt.Sscanf(version, "%d", &major); err != nil {
			continue
		}

		if major > currentMajor {
			if nextVersion == "" || major < func() int {
				var nextMajor int
				fmt.Sscanf(nextVersion, "%d", &nextMajor)
				return nextMajor
			}() {
				nextVersion = version
			}
		}
	}

	return nextVersion
}

// AddDeprecationHeaders adds deprecation headers to response
func (vm *VersionManager) AddDeprecationHeaders(w http.ResponseWriter, version string) {
	if !vm.config.DeprecationPolicy.Enabled {
		return
	}

	if vm.IsVersionDeprecated(version) {
		warning := vm.GetDeprecationWarning(version)
		if warning != "" {
			w.Header().Set(vm.config.DeprecationPolicy.WarningHeader, warning)
		}

		// Add deprecation date if available
		apiVersion, err := vm.GetVersionInfo(version)
		if err == nil && apiVersion.Info.DeprecationDate != nil {
			w.Header().Set("Sunset", apiVersion.Info.DeprecationDate.Format(time.RFC3339))
		}

		// Log deprecation warning
		if vm.config.DeprecationPolicy.LogDeprecation {
			vm.logger.Warn("Deprecated API version used",
				zap.String("version", version),
				zap.String("warning", warning),
			)
		}

		// Update metrics
		vm.metrics.deprecationWarnings.WithLabelValues(version, "").Inc()
	}
}

// AddMigrationHeaders adds migration headers to response
func (vm *VersionManager) AddMigrationHeaders(w http.ResponseWriter, version string) {
	if !vm.config.MigrationPolicy.Enabled {
		return
	}

	if vm.IsVersionDeprecated(version) {
		migrationInfo, err := vm.GetMigrationInfo(version)
		if err == nil {
			w.Header().Set(vm.config.MigrationPolicy.MigrationHeader, migrationInfo)
		}
	}
}

// TransformRequest transforms request for version-specific handling
func (vm *VersionManager) TransformRequest(request *http.Request, version string) (*http.Request, error) {
	apiVersion, err := vm.GetVersionInfo(version)
	if err != nil {
		return request, err
	}

	// Apply version-specific transformations
	transformedRequest := request.Clone(request.Context())

	// Transform headers
	for _, route := range apiVersion.Routes {
		if vm.matchesRoute(request.URL.Path, route.Path) {
			if route.Transform != nil {
				transformedRequest = vm.applyRequestTransform(transformedRequest, route.Transform)
			}
		}
	}

	return transformedRequest, nil
}

// TransformResponse transforms response for version-specific handling
func (vm *VersionManager) TransformResponse(response *http.Response, version string) (*http.Response, error) {
	apiVersion, err := vm.GetVersionInfo(version)
	if err != nil {
		return response, err
	}

	// Apply version-specific transformations
	// This is a simplified implementation
	// In a real implementation, you would transform the response body

	return response, nil
}

// matchesRoute checks if request path matches route pattern
func (vm *VersionManager) matchesRoute(requestPath, routePath string) bool {
	// Simple pattern matching
	// In a real implementation, you would use proper path matching
	return strings.HasPrefix(requestPath, routePath)
}

// applyRequestTransform applies request transformations
func (vm *VersionManager) applyRequestTransform(request *http.Request, transform *TransformConfig) *http.Request {
	// Apply header transformations
	if transform.Headers != nil {
		for key, value := range transform.Headers {
			request.Header.Set(key, value)
		}
	}

	// Apply query parameter transformations
	if transform.QueryParams != nil {
		q := request.URL.Query()
		for key, value := range transform.QueryParams {
			q.Set(key, value)
		}
		request.URL.RawQuery = q.Encode()
	}

	return request
}

// GetVersionRoute gets route information for a specific version and path
func (vm *VersionManager) GetVersionRoute(version, path string) (*VersionRoute, error) {
	apiVersion, err := vm.GetVersionInfo(version)
	if err != nil {
		return nil, err
	}

	apiVersion.mu.RLock()
	defer apiVersion.mu.RUnlock()

	route, exists := apiVersion.Routes[path]
	if !exists {
		return nil, fmt.Errorf("route %s not found in version %s", path, version)
	}

	return route, nil
}

// GetVersionStats returns version usage statistics
func (vm *VersionManager) GetVersionStats() map[string]interface{} {
	vm.mu.RLock()
	defer vm.mu.RUnlock()

	stats := make(map[string]interface{})
	for version, apiVersion := range vm.versions {
		apiVersion.mu.RLock()
		versionStats := map[string]interface{}{
			"version":      version,
			"status":       apiVersion.Status,
			"service":      apiVersion.Service,
			"url":          apiVersion.URL,
			"routes_count": len(apiVersion.Routes),
			"created_at":   apiVersion.CreatedAt,
			"updated_at":   apiVersion.UpdatedAt,
			"deprecated":   apiVersion.Status == VersionStatusDeprecated,
			"end_of_life":  apiVersion.Status == VersionStatusEOL,
		}

		if apiVersion.Info.DeprecationDate != nil {
			versionStats["deprecation_date"] = apiVersion.Info.DeprecationDate
		}
		if apiVersion.Info.EndOfLifeDate != nil {
			versionStats["end_of_life_date"] = apiVersion.Info.EndOfLifeDate
		}

		apiVersion.mu.RUnlock()
		stats[version] = versionStats
	}

	return stats
}

// UpdateVersionStatus updates the status of a version
func (vm *VersionManager) UpdateVersionStatus(version string, status VersionStatus) error {
	vm.mu.Lock()
	defer vm.mu.Unlock()

	apiVersion, exists := vm.versions[version]
	if !exists {
		return fmt.Errorf("version %s not found", version)
	}

	apiVersion.mu.Lock()
	apiVersion.Status = status
	apiVersion.UpdatedAt = time.Now()
	apiVersion.mu.Unlock()

	vm.logger.Info("Version status updated",
		zap.String("version", version),
		zap.String("status", string(status)),
	)

	return nil
}

// AddVersion adds a new API version
func (vm *VersionManager) AddVersion(version string, info VersionInfo) error {
	vm.mu.Lock()
	defer vm.mu.Unlock()

	if _, exists := vm.versions[version]; exists {
		return fmt.Errorf("version %s already exists", version)
	}

	apiVersion := &APIVersion{
		Info:      info,
		Service:   info.Service,
		URL:       info.URL,
		Routes:    make(map[string]*VersionRoute),
		Status:    info.Status,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Initialize routes
	for _, route := range info.Routes {
		apiVersion.Routes[route.Path] = &route
	}

	vm.versions[version] = apiVersion

	vm.logger.Info("API version added",
		zap.String("version", version),
		zap.String("status", string(info.Status)),
		zap.String("service", info.Service),
	)

	return nil
}

// RemoveVersion removes an API version
func (vm *VersionManager) RemoveVersion(version string) error {
	vm.mu.Lock()
	defer vm.mu.Unlock()

	if _, exists := vm.versions[version]; !exists {
		return fmt.Errorf("version %s not found", version)
	}

	delete(vm.versions, version)

	vm.logger.Info("API version removed",
		zap.String("version", version),
	)

	return nil
}

// UpdateConfig updates the versioning configuration
func (vm *VersionManager) UpdateConfig(config VersionConfig) error {
	vm.config = config
	vm.logger.Info("Versioning configuration updated")
	return nil
}
