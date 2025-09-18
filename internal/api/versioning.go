package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/go-chi/chi/v5"
)

// APIVersion represents an API version
type APIVersion struct {
	Version     string     `json:"version"`
	Status      string     `json:"status"` // "stable", "beta", "deprecated", "sunset"
	Released    time.Time  `json:"released"`
	Deprecated  *time.Time `json:"deprecated,omitempty"`
	Sunset      *time.Time `json:"sunset,omitempty"`
	Description string     `json:"description"`
	ChangesURL  string     `json:"changes_url,omitempty"`
}

// VersionInfo contains version metadata
type VersionInfo struct {
	Current      string        `json:"current"`
	Supported    []APIVersion  `json:"supported"`
	Latest       string        `json:"latest"`
	Deprecations []Deprecation `json:"deprecations,omitempty"`
}

// Deprecation represents a deprecated API feature
type Deprecation struct {
	Feature     string    `json:"feature"`
	Version     string    `json:"version"`
	Deprecated  time.Time `json:"deprecated"`
	Sunset      time.Time `json:"sunset"`
	Replacement string    `json:"replacement,omitempty"`
	Reason      string    `json:"reason"`
}

// VersionManager manages API versioning
type VersionManager struct {
	versions       map[string]APIVersion
	deprecations   []Deprecation
	defaultVersion string
}

// NewVersionManager creates a new version manager
func NewVersionManager() *VersionManager {
	now := time.Now()

	versions := map[string]APIVersion{
		"v1": {
			Version:     "v1",
			Status:      "stable",
			Released:    now.AddDate(-1, 0, 0), // Released 1 year ago
			Description: "Initial stable release of ArxOS API",
			ChangesURL:  "/docs/changelog/v1",
		},
		"v2": {
			Version:     "v2",
			Status:      "beta",
			Released:    now.AddDate(0, -3, 0), // Released 3 months ago
			Description: "Enhanced API with improved AR features and performance",
			ChangesURL:  "/docs/changelog/v2",
		},
	}

	deprecations := []Deprecation{
		{
			Feature:     "/api/v1/buildings/{id}/rooms",
			Version:     "v1",
			Deprecated:  now.AddDate(0, -6, 0),
			Sunset:      now.AddDate(0, 6, 0),
			Replacement: "/api/v2/buildings/{id}?include=rooms",
			Reason:      "Consolidated into building endpoint for better performance",
		},
	}

	return &VersionManager{
		versions:       versions,
		deprecations:   deprecations,
		defaultVersion: "v1",
	}
}

// GetVersion returns version information
func (vm *VersionManager) GetVersion(version string) (APIVersion, bool) {
	v, exists := vm.versions[version]
	return v, exists
}

// GetSupportedVersions returns all supported versions
func (vm *VersionManager) GetSupportedVersions() []APIVersion {
	var versions []APIVersion
	for _, v := range vm.versions {
		if v.Status != "sunset" {
			versions = append(versions, v)
		}
	}
	return versions
}

// GetVersionInfo returns comprehensive version information
func (vm *VersionManager) GetVersionInfo() VersionInfo {
	supported := vm.GetSupportedVersions()

	// Find latest stable version
	latest := vm.defaultVersion
	for _, v := range supported {
		if v.Status == "stable" && v.Version > latest {
			latest = v.Version
		}
	}

	return VersionInfo{
		Current:      vm.defaultVersion,
		Supported:    supported,
		Latest:       latest,
		Deprecations: vm.deprecations,
	}
}

// VersionMiddleware adds version handling to requests
func (vm *VersionManager) VersionMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		version := vm.extractVersion(r)

		// Validate version
		apiVersion, exists := vm.GetVersion(version)
		if !exists {
			vm.respondError(w, http.StatusBadRequest,
				fmt.Sprintf("Unsupported API version: %s", version))
			return
		}

		// Check if version is sunset
		if apiVersion.Status == "sunset" {
			vm.respondError(w, http.StatusGone,
				fmt.Sprintf("API version %s has been sunset", version))
			return
		}

		// Add deprecation headers if applicable
		if apiVersion.Status == "deprecated" && apiVersion.Sunset != nil {
			w.Header().Set("Deprecation", apiVersion.Deprecated.Format(time.RFC1123))
			w.Header().Set("Sunset", apiVersion.Sunset.Format(time.RFC1123))
			w.Header().Set("Link", fmt.Sprintf("<%s>; rel=\"successor-version\"", vm.getSuccessorVersion(version)))
		}

		// Add version to response headers
		w.Header().Set("API-Version", version)
		w.Header().Set("API-Supported-Versions", vm.getSupportedVersionsHeader())

		// Check for deprecated features in this request
		vm.checkDeprecatedFeatures(w, r, version)

		next.ServeHTTP(w, r)
	})
}

// extractVersion extracts API version from request
func (vm *VersionManager) extractVersion(r *http.Request) string {
	// 1. Check Accept header (preferred)
	accept := r.Header.Get("Accept")
	if strings.Contains(accept, "application/vnd.arxos") {
		parts := strings.Split(accept, "+")
		for _, part := range parts {
			if strings.HasPrefix(part, "version=") {
				return strings.TrimPrefix(part, "version=")
			}
		}
	}

	// 2. Check custom header
	if version := r.Header.Get("API-Version"); version != "" {
		return version
	}

	// 3. Check query parameter
	if version := r.URL.Query().Get("version"); version != "" {
		return version
	}

	// 4. Extract from URL path
	path := r.URL.Path
	if strings.HasPrefix(path, "/api/") {
		parts := strings.Split(path, "/")
		if len(parts) >= 3 && strings.HasPrefix(parts[2], "v") {
			return parts[2]
		}
	}

	// 5. Default version
	return vm.defaultVersion
}

// checkDeprecatedFeatures checks if the request uses deprecated features
func (vm *VersionManager) checkDeprecatedFeatures(w http.ResponseWriter, r *http.Request, version string) {
	for _, dep := range vm.deprecations {
		if dep.Version == version && vm.matchesPattern(r.URL.Path, dep.Feature) {
			w.Header().Set("Warning", fmt.Sprintf("299 - \"Deprecated feature: %s. %s\"", dep.Feature, dep.Reason))
			if dep.Replacement != "" {
				w.Header().Set("Link", fmt.Sprintf("<%s>; rel=\"alternate\"", dep.Replacement))
			}

			// Log deprecation usage for metrics
			logger.Warn("Deprecated API feature used: %s by %s", dep.Feature, r.RemoteAddr)
			break
		}
	}
}

// matchesPattern checks if a path matches a pattern with wildcards
func (vm *VersionManager) matchesPattern(path, pattern string) bool {
	// Simple pattern matching - could be enhanced with regex
	pathParts := strings.Split(path, "/")
	patternParts := strings.Split(pattern, "/")

	if len(pathParts) != len(patternParts) {
		return false
	}

	for i, part := range patternParts {
		if strings.HasPrefix(part, "{") && strings.HasSuffix(part, "}") {
			// Wildcard part - matches anything
			continue
		}
		if part != pathParts[i] {
			return false
		}
	}

	return true
}

// getSuccessorVersion returns the successor version for a deprecated version
func (vm *VersionManager) getSuccessorVersion(version string) string {
	// Simple logic - could be enhanced
	if version == "v1" {
		return "/api/v2"
	}
	return "/api/v1"
}

// getSupportedVersionsHeader returns supported versions as header value
func (vm *VersionManager) getSupportedVersionsHeader() string {
	versions := vm.GetSupportedVersions()
	var versionStrings []string
	for _, v := range versions {
		versionStrings = append(versionStrings, v.Version)
	}
	return strings.Join(versionStrings, ", ")
}

// respondError sends an error response
func (vm *VersionManager) respondError(w http.ResponseWriter, status int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"error":              message,
		"supported_versions": vm.GetSupportedVersions(),
	})
}

// VersionInfoHandler returns version information
func (vm *VersionManager) VersionInfoHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(vm.GetVersionInfo())
	}
}

// CreateVersionedRouter creates a router with version-specific routes
func CreateVersionedRouter(vm *VersionManager) chi.Router {
	r := chi.NewRouter()

	// Add version middleware
	r.Use(vm.VersionMiddleware)

	// Version info endpoint
	r.Get("/versions", vm.VersionInfoHandler())

	// Version-specific route groups
	r.Route("/api", func(r chi.Router) {
		// v1 routes
		r.Route("/v1", func(r chi.Router) {
			r.Get("/", func(w http.ResponseWriter, r *http.Request) {
				json.NewEncoder(w).Encode(map[string]string{
					"version": "v1",
					"status":  "stable",
				})
			})
		})

		// v2 routes
		r.Route("/v2", func(r chi.Router) {
			r.Get("/", func(w http.ResponseWriter, r *http.Request) {
				json.NewEncoder(w).Encode(map[string]string{
					"version": "v2",
					"status":  "beta",
				})
			})
		})
	})

	return r
}

// GetRateLimitForVersion returns rate limit configuration for a version
func (vm *VersionManager) GetRateLimitForVersion(version string) RateLimitConfig {
	switch version {
	case "v1":
		return RateLimitConfig{
			RequestsPerMinute: 100,
			BurstSize:         200,
		}
	case "v2":
		return RateLimitConfig{
			RequestsPerMinute: 150, // Higher limits for newer version
			BurstSize:         300,
		}
	default:
		return RateLimitConfig{
			RequestsPerMinute: 60, // Conservative for unknown versions
			BurstSize:         100,
		}
	}
}
