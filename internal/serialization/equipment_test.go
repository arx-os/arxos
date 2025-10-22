package serialization

import (
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestPathToGitFile(t *testing.T) {
	tests := []struct {
		name          string
		universalPath string
		expected      string
	}{
		{
			name:          "simple path",
			universalPath: "/B1/3/301/HVAC/VAV-301",
			expected:      "equipment/B1/3/301/HVAC/VAV-301.yml",
		},
		{
			name:          "path without leading slash",
			universalPath: "B1/3/301/HVAC/VAV-301",
			expected:      "equipment/B1/3/301/HVAC/VAV-301.yml",
		},
		{
			name:          "minimal path",
			universalPath: "/B1/VAV-301",
			expected:      "equipment/B1/VAV-301.yml",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := PathToGitFile(tt.universalPath)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestGitFileToPath(t *testing.T) {
	tests := []struct {
		name        string
		gitFilePath string
		expected    string
	}{
		{
			name:        "simple file path",
			gitFilePath: "equipment/B1/3/301/HVAC/VAV-301.yml",
			expected:    "/B1/3/301/HVAC/VAV-301",
		},
		{
			name:        "minimal file path",
			gitFilePath: "equipment/B1/VAV-301.yml",
			expected:    "/B1/VAV-301",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := GitFileToPath(tt.gitFilePath)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestPathRoundTrip(t *testing.T) {
	originalPaths := []string{
		"/B1/3/301/HVAC/VAV-301",
		"/EMPIRE-STATE/ROOF/MER-NORTH/HVAC/AHU-01",
		"/CAMPUS-WEST/1/101/LIGHTS/ZONE-A",
		"/B1/VAV-301",
	}

	for _, originalPath := range originalPaths {
		t.Run(originalPath, func(t *testing.T) {
			gitFile := PathToGitFile(originalPath)
			convertedPath := GitFileToPath(gitFile)
			assert.Equal(t, originalPath, convertedPath)
		})
	}
}

func TestValidateUniversalPath(t *testing.T) {
	tests := []struct {
		name        string
		path        string
		expectError bool
	}{
		{
			name:        "valid path",
			path:        "/B1/3/301/HVAC/VAV-301",
			expectError: false,
		},
		{
			name:        "minimal valid path",
			path:        "/B1/VAV-301",
			expectError: false,
		},
		{
			name:        "empty path",
			path:        "",
			expectError: true,
		},
		{
			name:        "path without leading slash",
			path:        "B1/3/301/HVAC/VAV-301",
			expectError: true,
		},
		{
			name:        "path with empty part",
			path:        "/B1//301/HVAC/VAV-301",
			expectError: true,
		},
		{
			name:        "single part path",
			path:        "/B1",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateUniversalPath(tt.path)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestExtractPathComponents(t *testing.T) {
	tests := []struct {
		name              string
		path              string
		expectedBuilding  string
		expectedFloor     string
		expectedRoom      string
		expectedSystem    string
		expectedEquipment string
	}{
		{
			name:              "full path",
			path:              "/B1/3/301/HVAC/VAV-301",
			expectedBuilding:  "B1",
			expectedFloor:     "3",
			expectedRoom:      "301",
			expectedSystem:    "HVAC",
			expectedEquipment: "VAV-301",
		},
		{
			name:              "minimal path",
			path:              "/B1/VAV-301",
			expectedBuilding:  "B1",
			expectedFloor:     "VAV-301",
			expectedRoom:      "",
			expectedSystem:    "",
			expectedEquipment: "",
		},
		{
			name:              "building only",
			path:              "/B1",
			expectedBuilding:  "B1",
			expectedFloor:     "",
			expectedRoom:      "",
			expectedSystem:    "",
			expectedEquipment: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			building, floor, room, system, equipment := ExtractPathComponents(tt.path)
			assert.Equal(t, tt.expectedBuilding, building)
			assert.Equal(t, tt.expectedFloor, floor)
			assert.Equal(t, tt.expectedRoom, room)
			assert.Equal(t, tt.expectedSystem, system)
			assert.Equal(t, tt.expectedEquipment, equipment)
		})
	}
}

func TestBuildPathFromComponents(t *testing.T) {
	tests := []struct {
		name         string
		building     string
		floor        string
		room         string
		system       string
		equipment    string
		expectedPath string
	}{
		{
			name:         "full components",
			building:     "B1",
			floor:        "3",
			room:         "301",
			system:       "HVAC",
			equipment:    "VAV-301",
			expectedPath: "/B1/3/301/HVAC/VAV-301",
		},
		{
			name:         "minimal components",
			building:     "B1",
			equipment:    "VAV-301",
			expectedPath: "/B1/VAV-301",
		},
		{
			name:         "empty components",
			expectedPath: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := BuildPathFromComponents(tt.building, tt.floor, tt.room, tt.system, tt.equipment)
			assert.Equal(t, tt.expectedPath, result)
		})
	}
}

func TestEquipmentToYAML(t *testing.T) {
	// Create a test equipment
	eq := &domain.Equipment{
		ID:       types.FromString("eq_123"),
		Name:     "VAV-301",
		Path:     "/B1/3/301/HVAC/VAV-301",
		Type:     "hvac",
		Category: "vav",
		Subtype:  "variable_air_volume",
		Model:    "Trane VAV-500",
		Status:   "operational",
		Location: &domain.Location{
			X: 10.5,
			Y: 8.2,
			Z: 2.7,
		},
		CreatedAt: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		UpdatedAt: time.Date(2024, 10, 21, 10, 30, 0, 0, time.UTC),
	}

	yaml, err := EquipmentToYAML(eq)
	require.NoError(t, err)

	// Verify YAML structure
	assert.Equal(t, "arxos.io/v1", yaml.APIVersion)
	assert.Equal(t, "Equipment", yaml.Kind)
	assert.Equal(t, "VAV-301", yaml.Metadata.Name)
	assert.Equal(t, "/B1/3/301/HVAC/VAV-301", yaml.Metadata.Path)
	assert.Equal(t, "eq_123", yaml.Metadata.ID)

	// Verify labels
	assert.Equal(t, "hvac", yaml.Metadata.Labels["type"])
	assert.Equal(t, "vav", yaml.Metadata.Labels["category"])
	assert.Equal(t, "B1", yaml.Metadata.Labels["building"])
	assert.Equal(t, "3", yaml.Metadata.Labels["floor"])
	assert.Equal(t, "301", yaml.Metadata.Labels["room"])
	assert.Equal(t, "HVAC", yaml.Metadata.Labels["system"])

	// Verify spec
	assert.Equal(t, "Trane VAV-500", yaml.Spec.Model)
	assert.NotNil(t, yaml.Spec.Location)
	assert.Equal(t, 10.5, yaml.Spec.Location.X)
	assert.Equal(t, 8.2, yaml.Spec.Location.Y)
	assert.Equal(t, 2.7, yaml.Spec.Location.Z)

	// Verify status
	assert.Equal(t, "operational", yaml.Status.OperationalState)
	assert.Equal(t, "healthy", yaml.Status.Health)
	assert.Equal(t, eq.UpdatedAt, yaml.Status.LastUpdated)

	// Verify ArxOS metadata
	assert.Equal(t, "eq_123", yaml.ArxOS.PostGISID)
}

func TestYAMLToEquipment(t *testing.T) {
	yaml := &EquipmentYAML{
		APIVersion: "arxos.io/v1",
		Kind:       "Equipment",
		Metadata: EquipmentMetadata{
			Name: "VAV-301",
			Path: "/B1/3/301/HVAC/VAV-301",
			ID:   "eq_123",
			Labels: map[string]string{
				"type":     "hvac",
				"category": "vav",
			},
		},
		Spec: EquipmentSpec{
			Model: "Trane VAV-500",
			Location: &LocationYAML{
				X: 10.5,
				Y: 8.2,
				Z: 2.7,
			},
		},
		Status: EquipmentStatus{
			OperationalState: "operational",
			Health:           "healthy",
			LastUpdated:      time.Date(2024, 10, 21, 10, 30, 0, 0, time.UTC),
		},
		ArxOS: ArxOSMetadata{
			PostGISID: "eq_123",
		},
	}

	eq, err := YAMLToEquipment(yaml)
	require.NoError(t, err)

	// Verify equipment structure
	assert.Equal(t, "VAV-301", eq.Name)
	assert.Equal(t, "/B1/3/301/HVAC/VAV-301", eq.Path)
	assert.Equal(t, "hvac", eq.Type)
	assert.Equal(t, "vav", eq.Category)
	assert.Equal(t, "Trane VAV-500", eq.Model)
	assert.Equal(t, "operational", eq.Status)
	assert.Equal(t, yaml.Status.LastUpdated, eq.UpdatedAt)

	// Verify location
	assert.NotNil(t, eq.Location)
	assert.Equal(t, 10.5, eq.Location.X)
	assert.Equal(t, 8.2, eq.Location.Y)
	assert.Equal(t, 2.7, eq.Location.Z)

	// Verify ID
	assert.Equal(t, types.FromString("eq_123"), eq.ID)
}

func TestEquipmentRoundTrip(t *testing.T) {
	original := &domain.Equipment{
		ID:       types.FromString("eq_123"),
		Name:     "VAV-301",
		Path:     "/B1/3/301/HVAC/VAV-301",
		Type:     "hvac",
		Category: "vav",
		Subtype:  "variable_air_volume",
		Model:    "Trane VAV-500",
		Status:   "operational",
		Location: &domain.Location{
			X: 10.5,
			Y: 8.2,
			Z: 2.7,
		},
		CreatedAt: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		UpdatedAt: time.Date(2024, 10, 21, 10, 30, 0, 0, time.UTC),
	}

	// Convert to YAML
	yaml, err := EquipmentToYAML(original)
	require.NoError(t, err)

	// Convert back to Equipment
	converted, err := YAMLToEquipment(yaml)
	require.NoError(t, err)

	// Verify round trip
	assert.Equal(t, original.Name, converted.Name)
	assert.Equal(t, original.Path, converted.Path)
	assert.Equal(t, original.Type, converted.Type)
	assert.Equal(t, original.Category, converted.Category)
	assert.Equal(t, original.Model, converted.Model)
	assert.Equal(t, original.Status, converted.Status)
	assert.Equal(t, original.ID, converted.ID)
	assert.Equal(t, original.UpdatedAt, converted.UpdatedAt)

	// Verify location
	assert.NotNil(t, converted.Location)
	assert.Equal(t, original.Location.X, converted.Location.X)
	assert.Equal(t, original.Location.Y, converted.Location.Y)
	assert.Equal(t, original.Location.Z, converted.Location.Z)
}

func TestMarshalUnmarshalEquipment(t *testing.T) {
	eq := &domain.Equipment{
		ID:       types.FromString("eq_123"),
		Name:     "VAV-301",
		Path:     "/B1/3/301/HVAC/VAV-301",
		Type:     "hvac",
		Category: "vav",
		Model:    "Trane VAV-500",
		Status:   "operational",
		Location: &domain.Location{
			X: 10.5,
			Y: 8.2,
			Z: 2.7,
		},
		UpdatedAt: time.Date(2024, 10, 21, 10, 30, 0, 0, time.UTC),
	}

	// Marshal to YAML bytes
	yamlBytes, err := MarshalEquipmentToYAML(eq)
	require.NoError(t, err)
	assert.NotEmpty(t, yamlBytes)

	// Unmarshal back to Equipment
	converted, err := UnmarshalEquipmentFromYAML(yamlBytes)
	require.NoError(t, err)

	// Verify round trip
	assert.Equal(t, eq.Name, converted.Name)
	assert.Equal(t, eq.Path, converted.Path)
	assert.Equal(t, eq.Type, converted.Type)
	assert.Equal(t, eq.Category, converted.Category)
	assert.Equal(t, eq.Model, converted.Model)
	assert.Equal(t, eq.Status, converted.Status)
	assert.Equal(t, eq.ID, converted.ID)
	assert.Equal(t, eq.UpdatedAt, converted.UpdatedAt)
}
