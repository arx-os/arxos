package gateway

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestVersionManager_NewVersionManager(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		VersionHeader:  "X-API-Version",
		URLPattern:     "/api/v{version}/",
		Versions: map[string]VersionInfo{
			"v1": {
				Version:     "v1",
				Status:      VersionStatusStable,
				ReleaseDate: time.Now(),
				Service:     "arx-svg-parser",
				URL:         "http://localhost:8000",
			},
			"v2": {
				Version:     "v2",
				Status:      VersionStatusBeta,
				ReleaseDate: time.Now(),
				Service:     "arx-svg-parser-v2",
				URL:         "http://localhost:8001",
			},
		},
		DeprecationPolicy: DeprecationPolicy{
			Enabled:        true,
			WarningHeader:  "X-API-Deprecation",
			WarningMessage: "API version is deprecated",
			GracePeriod:    30 * 24 * time.Hour,
			LogDeprecation: true,
		},
		MigrationPolicy: MigrationPolicy{
			Enabled:          true,
			AutoMigration:    false,
			MigrationHeader:  "X-API-Migration",
			MigrationMessage: "Migrate to newer version",
			MigrationTimeout: 30 * time.Second,
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)
	assert.NotNil(t, vm)
	assert.Equal(t, config, vm.config)
}

func TestVersionManager_GetVersion_Header(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		VersionHeader:  "X-API-Version",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusBeta},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	request := httptest.NewRequest("GET", "/api/test", nil)
	request.Header.Set("X-API-Version", "v2")

	version, err := vm.GetVersion(request)
	require.NoError(t, err)
	assert.Equal(t, "2", version)
}

func TestVersionManager_GetVersion_URL(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		URLPattern:     "/api/v{version}/",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusBeta},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	request := httptest.NewRequest("GET", "/api/v2/users", nil)

	version, err := vm.GetVersion(request)
	require.NoError(t, err)
	assert.Equal(t, "2", version)
}

func TestVersionManager_GetVersion_Accept(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusBeta},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	request := httptest.NewRequest("GET", "/api/test", nil)
	request.Header.Set("Accept", "application/vnd.api+json;version=2.0")

	version, err := vm.GetVersion(request)
	require.NoError(t, err)
	assert.Equal(t, "2.0", version)
}

func TestVersionManager_GetVersion_Default(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusBeta},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	request := httptest.NewRequest("GET", "/api/test", nil)

	version, err := vm.GetVersion(request)
	require.NoError(t, err)
	assert.Equal(t, "v1", version)
}

func TestVersionManager_GetVersionInfo(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {
				Version:     "v1",
				Status:      VersionStatusStable,
				ReleaseDate: time.Now(),
				Service:     "arx-svg-parser",
				URL:         "http://localhost:8000",
			},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	versionInfo, err := vm.GetVersionInfo("v1")
	require.NoError(t, err)
	assert.Equal(t, "v1", versionInfo.Info.Version)
	assert.Equal(t, VersionStatusStable, versionInfo.Status)
	assert.Equal(t, "arx-svg-parser", versionInfo.Service)
}

func TestVersionManager_GetVersionInfo_NotFound(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	_, err = vm.GetVersionInfo("v999")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "version v999 not found")
}

func TestVersionManager_IsVersionDeprecated(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusDeprecated},
			"v3": {Version: "v3", Status: VersionStatusEOL},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	assert.False(t, vm.IsVersionDeprecated("v1"))
	assert.True(t, vm.IsVersionDeprecated("v2"))
	assert.True(t, vm.IsVersionDeprecated("v3"))
}

func TestVersionManager_IsVersionEOL(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusDeprecated},
			"v3": {Version: "v3", Status: VersionStatusEOL},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	assert.False(t, vm.IsVersionEOL("v1"))
	assert.False(t, vm.IsVersionEOL("v2"))
	assert.True(t, vm.IsVersionEOL("v3"))
}

func TestVersionManager_GetDeprecationWarning(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		DeprecationPolicy: DeprecationPolicy{
			Enabled:        true,
			WarningMessage: "API version is deprecated",
		},
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusDeprecated},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	// No warning for stable version
	warning := vm.GetDeprecationWarning("v1")
	assert.Empty(t, warning)

	// Warning for deprecated version
	warning = vm.GetDeprecationWarning("v2")
	assert.Contains(t, warning, "deprecated")
}

func TestVersionManager_GetMigrationInfo(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusStable},
			"v3": {Version: "v3", Status: VersionStatusDeprecated},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	// Migration info for deprecated version
	migrationInfo, err := vm.GetMigrationInfo("v3")
	require.NoError(t, err)
	assert.Contains(t, migrationInfo, "Migrate from version v3")
}

func TestVersionManager_AddDeprecationHeaders(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		DeprecationPolicy: DeprecationPolicy{
			Enabled:        true,
			WarningHeader:  "X-API-Deprecation",
			WarningMessage: "API version is deprecated",
			LogDeprecation: true,
		},
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusDeprecated},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	w := httptest.NewRecorder()
	vm.AddDeprecationHeaders(w, "v2")

	assert.Equal(t, "API version is deprecated", w.Header().Get("X-API-Deprecation"))
}

func TestVersionManager_AddMigrationHeaders(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		MigrationPolicy: MigrationPolicy{
			Enabled:         true,
			MigrationHeader: "X-API-Migration",
		},
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusStable},
			"v3": {Version: "v3", Status: VersionStatusDeprecated},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	w := httptest.NewRecorder()
	vm.AddMigrationHeaders(w, "v3")

	// Should have migration header for deprecated version
	assert.NotEmpty(t, w.Header().Get("X-API-Migration"))
}

func TestVersionManager_TransformRequest(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {
				Version: "v1",
				Status:  VersionStatusStable,
				Routes: []VersionRoute{
					{
						Path:    "/api/v1/users",
						Methods: []string{"GET"},
						Transform: &TransformConfig{
							Headers: map[string]string{"X-Version": "v1"},
						},
					},
				},
			},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	request := httptest.NewRequest("GET", "/api/v1/users", nil)
	transformedRequest, err := vm.TransformRequest(request, "v1")
	require.NoError(t, err)

	assert.Equal(t, "v1", transformedRequest.Header.Get("X-Version"))
}

func TestVersionManager_TransformResponse(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {
				Version: "v1",
				Status:  VersionStatusStable,
			},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	response := &http.Response{
		StatusCode: 200,
		Header:     make(http.Header),
	}
	response.Header.Set("Content-Type", "application/json")

	transformedResponse, err := vm.TransformResponse(response, "v1")
	require.NoError(t, err)

	assert.Equal(t, 200, transformedResponse.StatusCode)
}

func TestVersionManager_GetVersionRoute(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {
				Version: "v1",
				Status:  VersionStatusStable,
				Routes: []VersionRoute{
					{
						Path:       "/api/v1/users",
						Methods:    []string{"GET"},
						Auth:       true,
						Deprecated: false,
					},
				},
			},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	route, err := vm.GetVersionRoute("v1", "/api/v1/users")
	require.NoError(t, err)
	assert.Equal(t, "/api/v1/users", route.Path)
	assert.True(t, route.Auth)
	assert.False(t, route.Deprecated)
}

func TestVersionManager_GetVersionRoute_NotFound(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {
				Version: "v1",
				Status:  VersionStatusStable,
				Routes: []VersionRoute{
					{
						Path:    "/api/v1/users",
						Methods: []string{"GET"},
					},
				},
			},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	_, err = vm.GetVersionRoute("v1", "/api/v1/nonexistent")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "route /api/v1/nonexistent not found")
}

func TestVersionManager_GetVersionStats(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {
				Version:     "v1",
				Status:      VersionStatusStable,
				ReleaseDate: time.Now(),
				Service:     "arx-svg-parser",
				URL:         "http://localhost:8000",
			},
			"v2": {
				Version:     "v2",
				Status:      VersionStatusDeprecated,
				ReleaseDate: time.Now(),
				Service:     "arx-svg-parser-v2",
				URL:         "http://localhost:8001",
			},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	stats := vm.GetVersionStats()

	v1Stats, exists := stats["v1"].(map[string]interface{})
	assert.True(t, exists)
	assert.Equal(t, "v1", v1Stats["version"])
	assert.Equal(t, string(VersionStatusStable), v1Stats["status"])
	assert.Equal(t, "arx-svg-parser", v1Stats["service"])

	v2Stats, exists := stats["v2"].(map[string]interface{})
	assert.True(t, exists)
	assert.Equal(t, "v2", v2Stats["version"])
	assert.Equal(t, string(VersionStatusDeprecated), v2Stats["status"])
	assert.True(t, v2Stats["deprecated"].(bool))
}

func TestVersionManager_UpdateVersionStatus(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	// Update status to deprecated
	err = vm.UpdateVersionStatus("v1", VersionStatusDeprecated)
	require.NoError(t, err)

	versionInfo, err := vm.GetVersionInfo("v1")
	require.NoError(t, err)
	assert.Equal(t, VersionStatusDeprecated, versionInfo.Status)
}

func TestVersionManager_AddVersion(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	newVersion := VersionInfo{
		Version:     "v3",
		Status:      VersionStatusBeta,
		ReleaseDate: time.Now(),
		Service:     "arx-svg-parser-v3",
		URL:         "http://localhost:8002",
	}

	err = vm.AddVersion("v3", newVersion)
	require.NoError(t, err)

	versionInfo, err := vm.GetVersionInfo("v3")
	require.NoError(t, err)
	assert.Equal(t, "v3", versionInfo.Info.Version)
	assert.Equal(t, VersionStatusBeta, versionInfo.Status)
	assert.Equal(t, "arx-svg-parser-v3", versionInfo.Service)
}

func TestVersionManager_AddVersion_AlreadyExists(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	newVersion := VersionInfo{
		Version: "v1",
		Status:  VersionStatusBeta,
	}

	err = vm.AddVersion("v1", newVersion)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "version v1 already exists")
}

func TestVersionManager_RemoveVersion(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
			"v2": {Version: "v2", Status: VersionStatusBeta},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	err = vm.RemoveVersion("v2")
	require.NoError(t, err)

	// Should not find removed version
	_, err = vm.GetVersionInfo("v2")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "version v2 not found")

	// Should still find other version
	versionInfo, err := vm.GetVersionInfo("v1")
	require.NoError(t, err)
	assert.Equal(t, "v1", versionInfo.Info.Version)
}

func TestVersionManager_RemoveVersion_NotFound(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	err = vm.RemoveVersion("v999")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "version v999 not found")
}

func TestVersionManager_UpdateConfig(t *testing.T) {
	config := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v1",
		Versions: map[string]VersionInfo{
			"v1": {Version: "v1", Status: VersionStatusStable},
		},
	}

	vm, err := NewVersionManager(config)
	require.NoError(t, err)

	newConfig := VersionConfig{
		Enabled:        true,
		DefaultVersion: "v2",
		Versions: map[string]VersionInfo{
			"v2": {Version: "v2", Status: VersionStatusStable},
		},
	}

	err = vm.UpdateConfig(newConfig)
	require.NoError(t, err)
	assert.Equal(t, newConfig, vm.config)
}
