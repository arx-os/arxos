// Package versioning provides API version management and routing
package versioning

import (
	"context"
	"fmt"
	"net/http"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Version represents an API version
type Version string

const (
	// V1 is API version 1.0 (current stable)
	V1 Version = "v1"
	// V2 is API version 2.0 (future)
	V2 Version = "v2"
	// V3 is API version 3.0 (future)
	V3 Version = "v3"
)

// contextKey for version in context
type contextKey string

const versionContextKey = contextKey("api_version")

// VersionInfo contains information about an API version
type VersionInfo struct {
	Version         string   `json:"version"`
	Status          string   `json:"status"` // stable, deprecated, sunset
	ReleaseDate     string   `json:"release_date"`
	SunsetDate      string   `json:"sunset_date,omitempty"`
	Features        []string `json:"features"`
	BreakingChanges []string `json:"breaking_changes,omitempty"`
}

// VersionRegistry manages available API versions
type VersionRegistry struct {
	versions       map[Version]*VersionInfo
	currentVersion Version
	defaultVersion Version
}

// NewRegistry creates a new version registry
func NewRegistry() *VersionRegistry {
	registry := &VersionRegistry{
		versions:       make(map[Version]*VersionInfo),
		currentVersion: V1,
		defaultVersion: V1,
	}

	// Register V1
	registry.Register(V1, &VersionInfo{
		Version:     "1.0.0",
		Status:      "stable",
		ReleaseDate: "2025-01-01",
		Features: []string{
			"Building management",
			"Equipment operations",
			"Spatial queries",
			"User authentication",
			"Organization management",
		},
	})

	return registry
}

// Register registers a new API version
func (vr *VersionRegistry) Register(version Version, info *VersionInfo) {
	vr.versions[version] = info
	logger.Info("Registered API version: %s (status: %s)", version, info.Status)
}

// Get returns version info for a specific version
func (vr *VersionRegistry) Get(version Version) (*VersionInfo, error) {
	info, exists := vr.versions[version]
	if !exists {
		return nil, fmt.Errorf("API version %s not found", version)
	}
	return info, nil
}

// GetAll returns all registered versions
func (vr *VersionRegistry) GetAll() map[Version]*VersionInfo {
	return vr.versions
}

// IsSupported checks if a version is supported
func (vr *VersionRegistry) IsSupported(version Version) bool {
	info, exists := vr.versions[version]
	if !exists {
		return false
	}
	// Version is supported if not sunset
	return info.Status != "sunset"
}

// GetCurrent returns the current stable version
func (vr *VersionRegistry) GetCurrent() Version {
	return vr.currentVersion
}

// GetDefault returns the default version for unversioned requests
func (vr *VersionRegistry) GetDefault() Version {
	return vr.defaultVersion
}

// Middleware provides version-aware request routing
type Middleware struct {
	registry *VersionRegistry
}

// NewMiddleware creates a new versioning middleware
func NewMiddleware(registry *VersionRegistry) *Middleware {
	return &Middleware{
		registry: registry,
	}
}

// ExtractVersion extracts API version from request
func (m *Middleware) ExtractVersion(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		version := m.getVersionFromRequest(r)

		// Validate version
		if !m.registry.IsSupported(version) {
			m.respondUnsupportedVersion(w, version)
			return
		}

		// Add version to context
		ctx := context.WithValue(r.Context(), versionContextKey, version)
		r = r.WithContext(ctx)

		// Add version header to response
		w.Header().Set("X-API-Version", string(version))

		logger.Debug("API request version: %s (path: %s)", version, r.URL.Path)

		next.ServeHTTP(w, r)
	})
}

// getVersionFromRequest extracts version from URL path, header, or query param
func (m *Middleware) getVersionFromRequest(r *http.Request) Version {
	// Priority 1: URL path (e.g., /api/v2/buildings)
	if version := m.extractVersionFromPath(r.URL.Path); version != "" {
		return version
	}

	// Priority 2: Accept header (e.g., application/vnd.arxos.v2+json)
	if version := m.extractVersionFromHeader(r.Header.Get("Accept")); version != "" {
		return version
	}

	// Priority 3: X-API-Version header
	if version := r.Header.Get("X-API-Version"); version != "" {
		return Version(version)
	}

	// Priority 4: Query parameter
	if version := r.URL.Query().Get("version"); version != "" {
		return Version(version)
	}

	// Default version
	return m.registry.GetDefault()
}

// extractVersionFromPath extracts version from URL path
func (m *Middleware) extractVersionFromPath(path string) Version {
	// Expected format: /api/v1/... or /api/v2/...
	parts := strings.Split(strings.TrimPrefix(path, "/"), "/")
	if len(parts) >= 2 && parts[0] == "api" {
		versionStr := parts[1]
		if strings.HasPrefix(versionStr, "v") {
			return Version(versionStr)
		}
	}
	return ""
}

// extractVersionFromHeader extracts version from Accept header
func (m *Middleware) extractVersionFromHeader(accept string) Version {
	// Expected format: application/vnd.arxos.v2+json
	if strings.Contains(accept, "vnd.arxos.") {
		parts := strings.Split(accept, ".")
		for _, part := range parts {
			if strings.HasPrefix(part, "v") && len(part) >= 2 {
				versionPart := strings.Split(part, "+")[0]
				return Version(versionPart)
			}
		}
	}
	return ""
}

// respondUnsupportedVersion sends an error response for unsupported versions
func (m *Middleware) respondUnsupportedVersion(w http.ResponseWriter, version Version) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)

	supportedVersions := m.getSupportedVersions()

	response := fmt.Sprintf(`{
		"error": "Unsupported API version",
		"code": "UNSUPPORTED_VERSION",
		"details": {
			"requested_version": "%s",
			"supported_versions": %s,
			"current_version": "%s"
		}
	}`, version, m.formatVersionList(supportedVersions), m.registry.GetCurrent())

	w.Write([]byte(response))
}

// getSupportedVersions returns list of supported versions
func (m *Middleware) getSupportedVersions() []Version {
	var supported []Version
	for version, info := range m.registry.GetAll() {
		if info.Status != "sunset" {
			supported = append(supported, version)
		}
	}
	return supported
}

// formatVersionList formats version list as JSON array
func (m *Middleware) formatVersionList(versions []Version) string {
	var strs []string
	for _, v := range versions {
		strs = append(strs, fmt.Sprintf(`"%s"`, v))
	}
	return "[" + strings.Join(strs, ", ") + "]"
}

// GetVersionFromContext retrieves version from context
func GetVersionFromContext(ctx context.Context) Version {
	if version, ok := ctx.Value(versionContextKey).(Version); ok {
		return version
	}
	return V1 // Default fallback
}

// DeprecationWarning adds a deprecation warning header
func DeprecationWarning(w http.ResponseWriter, version Version, sunsetDate string, upgradeVersion Version) {
	warning := fmt.Sprintf(`299 - "API version %s is deprecated. Please upgrade to %s. Sunset date: %s"`,
		version, upgradeVersion, sunsetDate)
	w.Header().Set("Warning", warning)
	w.Header().Set("Sunset", sunsetDate)
	w.Header().Set("Link", fmt.Sprintf(`</api/%s>; rel="successor-version"`, upgradeVersion))
}

// Global registry instance
var globalRegistry *VersionRegistry

// GetRegistry returns the global version registry
func GetRegistry() *VersionRegistry {
	if globalRegistry == nil {
		globalRegistry = NewRegistry()
	}
	return globalRegistry
}

// Initialize initializes the versioning system
func Initialize() *VersionRegistry {
	return GetRegistry()
}
