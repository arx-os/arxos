package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestValidateBuildingID(t *testing.T) {
	tests := []struct {
		name       string
		buildingID string
		wantErr    bool
	}{
		{"valid building ID", "building:main", false},
		{"valid with numbers", "building:hq_2024", false},
		{"valid with hyphens", "building:main-office", false},
		{"missing building prefix", "main", true},
		{"empty name", "building:", true},
		{"invalid characters", "building:main@office", true},
		{"spaces not allowed", "building:main office", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validateBuildingID(tt.buildingID)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateBuildingID() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestValidateInitOptions(t *testing.T) {
	tests := []struct {
		name    string
		options *InitOptions
		wantErr bool
	}{
		{
			name: "valid office building",
			options: &InitOptions{
				BuildingType: "office",
				Floors:       3,
				Area:         "15,000 sq ft",
			},
			wantErr: false,
		},
		{
			name: "invalid building type",
			options: &InitOptions{
				BuildingType: "invalid_type",
				Floors:       1,
			},
			wantErr: true,
		},
		{
			name: "too many floors",
			options: &InitOptions{
				BuildingType: "office",
				Floors:       250,
			},
			wantErr: true,
		},
		{
			name: "zero floors",
			options: &InitOptions{
				BuildingType: "office",
				Floors:       0,
			},
			wantErr: true,
		},
		{
			name: "both PDF and IFC specified",
			options: &InitOptions{
				BuildingType: "office",
				Floors:       1,
				FromPDF:      "plan.pdf",
				FromIFC:      "model.ifc",
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validateInitOptions(tt.options)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateInitOptions() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestIsValidAreaFormat(t *testing.T) {
	tests := []struct {
		name string
		area string
		want bool
	}{
		{"valid sq ft", "25,000 sq ft", true},
		{"valid m2", "5000 m2", true},
		{"valid ft2", "25000 ft2", true},
		{"empty area", "", false},
		{"no units", "25000", false},
		{"no numbers", "sq ft", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := isValidAreaFormat(tt.area)
			if got != tt.want {
				t.Errorf("isValidAreaFormat() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestCreateBuildingFilesystem(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Change to temp directory
	originalDir, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get current directory: %v", err)
	}
	defer os.Chdir(originalDir)

	if err := os.Chdir(tempDir); err != nil {
		t.Fatalf("Failed to change to temp directory: %v", err)
	}

	// Test building creation
	buildingID := "building:test"
	if err := createBuildingFilesystem(buildingID); err != nil {
		t.Fatalf("createBuildingFilesystem() failed: %v", err)
	}

	// Verify essential directories were created
	essentialDirs := []string{
		"building:test/.arxos",
		"building:test/.arxos/config",
		"building:test/.arxos/objects",
		"building:test/.arxos/vcs",
		"building:test/systems",
		"building:test/schemas",
	}

	for _, dir := range essentialDirs {
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			t.Errorf("Essential directory not created: %s", dir)
		}
	}
}

func TestCreateInitialConfiguration(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Change to temp directory
	originalDir, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get current directory: %v", err)
	}
	defer os.Chdir(originalDir)

	if err := os.Chdir(tempDir); err != nil {
		t.Fatalf("Failed to change to temp directory: %v", err)
	}

	// Test configuration creation
	buildingID := "building:test"
	options := &InitOptions{
		BuildingType: "office",
		Floors:       2,
		Area:         "10,000 sq ft",
		Location:     "123 Test St",
	}

	if err := createInitialConfiguration(buildingID, options); err != nil {
		t.Fatalf("createInitialConfiguration() failed: %v", err)
	}

	// Verify configuration files were created
	configFiles := []string{
		"building:test/arxos.yml",
		"building:test/floor:1/arxos.yml",
		"building:test/floor:2/arxos.yml",
		"building:test/systems/electrical/arxos.yml",
		"building:test/systems/hvac/arxos.yml",
	}

	for _, file := range configFiles {
		if _, err := os.Stat(file); os.IsNotExist(err) {
			t.Errorf("Configuration file not created: %s", file)
		}
	}
}

func TestValidateBuildingStructure(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Change to temp directory
	originalDir, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get current directory: %v", err)
	}
	defer os.Chdir(originalDir)

	if err := os.Chdir(tempDir); err != nil {
		t.Fatalf("Failed to change to temp directory: %v", err)
	}

	// Create a minimal building structure
	buildingID := "building:test"
	if err := createBuildingFilesystem(buildingID); err != nil {
		t.Fatalf("Failed to create building filesystem: %v", err)
	}

	// Create a basic configuration file
	config := BuildingConfig{
		BuildingID: buildingID,
		Type:       "office",
		Floors:     1,
		Version:    "1.0.0",
	}

	configPath := filepath.Join(buildingID, "arxos.yml")
	if err := writeYAML(configPath, config); err != nil {
		t.Fatalf("Failed to write config: %v", err)
	}

	// Test validation
	if err := validateBuildingStructure(buildingID); err != nil {
		t.Errorf("validateBuildingStructure() failed: %v", err)
	}
}
