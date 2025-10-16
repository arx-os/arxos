/**
 * CLI Integration Tests
 * Comprehensive tests for CLI commands including execution, argument parsing, and output formatting
 */

package integration

import (
	"bytes"
	"context"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/test/helpers"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// CLIIntegrationTestSuite manages CLI integration tests
type CLIIntegrationTestSuite struct {
	app        *app.Container
	config     *config.Config
	cliPath    string
	testDir    string
	httpClient *http.Client
}

// NewCLIIntegrationTestSuite creates a new CLI integration test suite
func NewCLIIntegrationTestSuite(t *testing.T) *CLIIntegrationTestSuite {
	// Load test configuration
	cfg := helpers.LoadTestConfig(t)

	// Create application container
	container := app.NewContainer()
	ctx := context.Background()
	err := container.Initialize(ctx, cfg)
	if err != nil {
		t.Skipf("Cannot initialize container (database may not be available): %v", err)
		return nil
	}

	// Get CLI binary path
	cliPath := getCLIBinaryPath(t)

	// Create test directory
	testDir := t.TempDir()

	// Create HTTP client for API verification
	httpClient := &http.Client{
		Timeout: 30 * time.Second,
	}

	return &CLIIntegrationTestSuite{
		app:        container,
		config:     cfg,
		cliPath:    cliPath,
		testDir:    testDir,
		httpClient: httpClient,
	}
}

// getCLIBinaryPath finds the CLI binary for testing
func getCLIBinaryPath(t *testing.T) string {
	// Try to find the CLI binary in common locations
	possiblePaths := []string{
		"./arxos",
		"./bin/arxos",
		"./build/arxos",
		"../arxos",
		"../../arxos",
	}

	for _, path := range possiblePaths {
		if _, err := os.Stat(path); err == nil {
			return path
		}
	}

	// If not found, try to build it
	buildPath := buildCLIBinary(t)
	if buildPath != "" {
		return buildPath
	}

	t.Skip("CLI binary not found and could not be built")
	return ""
}

// buildCLIBinary attempts to build the CLI binary
func buildCLIBinary(t *testing.T) string {
	// Try to build the CLI
	cmd := exec.Command("go", "build", "-o", "arxos-test", "./cmd/arxos")
	cmd.Dir = "."

	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Logf("Failed to build CLI: %v, output: %s", err, string(output))
		return ""
	}

	// Check if binary was created
	if _, err := os.Stat("arxos-test"); err == nil {
		return "./arxos-test"
	}

	return ""
}

// runCLICommand executes a CLI command and returns the output
func (suite *CLIIntegrationTestSuite) runCLICommand(args []string) (string, string, error) {
	cmd := exec.Command(suite.cliPath, args...)
	cmd.Dir = suite.testDir

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	return stdout.String(), stderr.String(), err
}

// TestCLIBasicCommands tests basic CLI functionality
func TestCLIBasicCommands(t *testing.T) {
	suite := NewCLIIntegrationTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	t.Run("HelpCommand", func(t *testing.T) {
		stdout, stderr, err := suite.runCLICommand([]string{"--help"})

		// Help command should succeed
		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "ArxOS")
		assert.Contains(t, stdout, "Usage:")
		assert.Contains(t, stdout, "Commands:")
	})

	t.Run("VersionCommand", func(t *testing.T) {
		stdout, stderr, err := suite.runCLICommand([]string{"version"})

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "ArxOS")
		assert.Contains(t, stdout, "version")
	})

	t.Run("InvalidCommand", func(t *testing.T) {
		_, stderr, err := suite.runCLICommand([]string{"invalid-command"})

		// Invalid command should fail
		assert.Error(t, err)
		assert.Contains(t, stderr, "unknown command")
	})

	t.Run("InvalidFlag", func(t *testing.T) {
		_, stderr, err := suite.runCLICommand([]string{"--invalid-flag"})

		// Invalid flag should fail
		assert.Error(t, err)
		assert.Contains(t, stderr, "unknown flag")
	})
}

// TestBuildingCLICommands tests building-related CLI commands
func TestBuildingCLICommands(t *testing.T) {
	suite := NewCLIIntegrationTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	t.Run("CreateBuilding", func(t *testing.T) {
		// Create a building via CLI
		args := []string{
			"building", "create",
			"--name", "CLI Test Building",
			"--address", "123 CLI Street",
			"--city", "Test City",
			"--state", "TS",
			"--zip", "12345",
			"--country", "Test Country",
			"--type", "office",
		}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "Building created successfully")
		assert.Contains(t, stdout, "CLI Test Building")
	})

	t.Run("ListBuildings", func(t *testing.T) {
		// List buildings via CLI
		args := []string{"building", "list"}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "Buildings:")
	})

	t.Run("GetBuilding", func(t *testing.T) {
		// First create a building to get its ID
		createArgs := []string{
			"building", "create",
			"--name", "Get Test Building",
			"--address", "456 Get Street",
			"--city", "Test City",
			"--state", "TS",
			"--zip", "12345",
			"--country", "Test Country",
			"--type", "office",
		}

		createStdout, _, err := suite.runCLICommand(createArgs)
		require.NoError(t, err)

		// Extract building ID from output (assuming it's in the format "ID: <id>")
		lines := strings.Split(createStdout, "\n")
		var buildingID string
		for _, line := range lines {
			if strings.Contains(line, "ID:") {
				parts := strings.Split(line, "ID:")
				if len(parts) > 1 {
					buildingID = strings.TrimSpace(parts[1])
					break
				}
			}
		}

		if buildingID == "" {
			t.Skip("Could not extract building ID from create output")
			return
		}

		// Get the building
		args := []string{"building", "get", "--id", buildingID}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "Get Test Building")
		assert.Contains(t, stdout, buildingID)
	})

	t.Run("UpdateBuilding", func(t *testing.T) {
		// First create a building
		createArgs := []string{
			"building", "create",
			"--name", "Update Test Building",
			"--address", "789 Update Street",
			"--city", "Test City",
			"--state", "TS",
			"--zip", "12345",
			"--country", "Test Country",
			"--type", "office",
		}

		createStdout, _, err := suite.runCLICommand(createArgs)
		require.NoError(t, err)

		// Extract building ID
		lines := strings.Split(createStdout, "\n")
		var buildingID string
		for _, line := range lines {
			if strings.Contains(line, "ID:") {
				parts := strings.Split(line, "ID:")
				if len(parts) > 1 {
					buildingID = strings.TrimSpace(parts[1])
					break
				}
			}
		}

		if buildingID == "" {
			t.Skip("Could not extract building ID from create output")
			return
		}

		// Update the building
		args := []string{
			"building", "update",
			"--id", buildingID,
			"--name", "Updated CLI Building",
			"--address", "999 Updated Street",
		}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "Building updated successfully")
		assert.Contains(t, stdout, "Updated CLI Building")
	})

	t.Run("DeleteBuilding", func(t *testing.T) {
		// First create a building
		createArgs := []string{
			"building", "create",
			"--name", "Delete Test Building",
			"--address", "111 Delete Street",
			"--city", "Test City",
			"--state", "TS",
			"--zip", "12345",
			"--country", "Test Country",
			"--type", "office",
		}

		createStdout, _, err := suite.runCLICommand(createArgs)
		require.NoError(t, err)

		// Extract building ID
		lines := strings.Split(createStdout, "\n")
		var buildingID string
		for _, line := range lines {
			if strings.Contains(line, "ID:") {
				parts := strings.Split(line, "ID:")
				if len(parts) > 1 {
					buildingID = strings.TrimSpace(parts[1])
					break
				}
			}
		}

		if buildingID == "" {
			t.Skip("Could not extract building ID from create output")
			return
		}

		// Delete the building
		args := []string{"building", "delete", "--id", buildingID}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "Building deleted successfully")
	})
}

// TestEquipmentCLICommands tests equipment-related CLI commands
func TestEquipmentCLICommands(t *testing.T) {
	suite := NewCLIIntegrationTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	var buildingID string

	// Setup: Create a building first
	t.Run("SetupBuilding", func(t *testing.T) {
		createArgs := []string{
			"building", "create",
			"--name", "Equipment Test Building",
			"--address", "123 Equipment Street",
			"--city", "Test City",
			"--state", "TS",
			"--zip", "12345",
			"--country", "Test Country",
			"--type", "office",
		}

		createStdout, _, err := suite.runCLICommand(createArgs)
		require.NoError(t, err)

		// Extract building ID
		lines := strings.Split(createStdout, "\n")
		for _, line := range lines {
			if strings.Contains(line, "ID:") {
				parts := strings.Split(line, "ID:")
				if len(parts) > 1 {
					buildingID = strings.TrimSpace(parts[1])
					break
				}
			}
		}

		require.NotEmpty(t, buildingID, "Could not extract building ID")
	})

	t.Run("CreateEquipment", func(t *testing.T) {
		args := []string{
			"equipment", "create",
			"--building-id", buildingID,
			"--name", "CLI Test Equipment",
			"--type", "HVAC",
			"--model", "CLI Model 3000",
			"--location-x", "40.7128",
			"--location-y", "-74.0060",
			"--location-z", "5",
		}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "Equipment created successfully")
		assert.Contains(t, stdout, "CLI Test Equipment")
	})

	t.Run("ListEquipment", func(t *testing.T) {
		args := []string{"equipment", "list", "--building-id", buildingID}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "Equipment:")
	})

	t.Run("GetEquipmentByPath", func(t *testing.T) {
		path := "/B1/F1/R1/HVAC/EQUIP-01"
		args := []string{"equipment", "get", "--path", path}

		stdout, stderr, err := suite.runCLICommand(args)

		// Should either succeed with equipment data or show not found
		if err != nil {
			assert.Contains(t, stderr, "not found")
		} else {
			assert.Contains(t, stdout, "Equipment:")
		}
	})

	t.Run("FindEquipmentByPathPattern", func(t *testing.T) {
		pattern := "/B1/F1/*/HVAC/*"
		args := []string{"equipment", "find", "--pattern", pattern}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "Equipment found:")
	})
}

// TestPathQueryCLICommands tests path-based query CLI commands
func TestPathQueryCLICommands(t *testing.T) {
	suite := NewCLIIntegrationTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	t.Run("GetByExactPath", func(t *testing.T) {
		path := "/B1/F1/R1/HVAC/TEMP-01"
		args := []string{"get", path}

		stdout, stderr, err := suite.runCLICommand(args)

		// Should either succeed with equipment data or show not found
		if err != nil {
			assert.Contains(t, stderr, "not found")
		} else {
			assert.Contains(t, stdout, "Equipment:")
		}
	})

	t.Run("FindByPathPattern", func(t *testing.T) {
		pattern := "/B1/F1/*/HVAC/*"
		args := []string{"find", pattern}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "Equipment found:")
	})

	t.Run("InvalidPath", func(t *testing.T) {
		path := "invalid-path"
		args := []string{"get", path}

		_, stderr, err := suite.runCLICommand(args)

		assert.Error(t, err)
		assert.Contains(t, stderr, "invalid path")
	})

	t.Run("InvalidPattern", func(t *testing.T) {
		pattern := "invalid-pattern"
		args := []string{"find", pattern}

		_, stderr, err := suite.runCLICommand(args)

		assert.Error(t, err)
		assert.Contains(t, stderr, "invalid pattern")
	})
}

// TestCLIErrorHandling tests CLI error handling
func TestCLIErrorHandling(t *testing.T) {
	suite := NewCLIIntegrationTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	t.Run("MissingRequiredArguments", func(t *testing.T) {
		// Try to create building without required arguments
		args := []string{"building", "create"}

		_, stderr, err := suite.runCLICommand(args)

		assert.Error(t, err)
		assert.Contains(t, stderr, "required")
	})

	t.Run("InvalidArgumentValues", func(t *testing.T) {
		// Try to create building with invalid values
		args := []string{
			"building", "create",
			"--name", "", // Empty name
			"--address", "123 Test Street",
		}

		_, stderr, err := suite.runCLICommand(args)

		assert.Error(t, err)
		assert.Contains(t, stderr, "invalid")
	})

	t.Run("NonExistentResource", func(t *testing.T) {
		// Try to get non-existent building
		args := []string{"building", "get", "--id", "non-existent-id"}

		_, stderr, err := suite.runCLICommand(args)

		assert.Error(t, err)
		assert.Contains(t, stderr, "not found")
	})

	t.Run("InvalidResourceID", func(t *testing.T) {
		// Try to get building with invalid ID format
		args := []string{"building", "get", "--id", "invalid-id"}

		_, stderr, err := suite.runCLICommand(args)

		assert.Error(t, err)
		assert.Contains(t, stderr, "invalid")
	})
}

// TestCLIOutputFormatting tests CLI output formatting
func TestCLIOutputFormatting(t *testing.T) {
	suite := NewCLIIntegrationTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	t.Run("JSONOutput", func(t *testing.T) {
		// Test JSON output format
		args := []string{"building", "list", "--format", "json"}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)

		// Should be valid JSON
		assert.True(t, strings.HasPrefix(stdout, "{") || strings.HasPrefix(stdout, "["))
	})

	t.Run("TableOutput", func(t *testing.T) {
		// Test table output format (default)
		args := []string{"building", "list", "--format", "table"}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)

		// Should contain table headers
		assert.Contains(t, stdout, "ID")
		assert.Contains(t, stdout, "Name")
		assert.Contains(t, stdout, "Address")
	})

	t.Run("YAMLOutput", func(t *testing.T) {
		// Test YAML output format
		args := []string{"building", "list", "--format", "yaml"}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)

		// Should contain YAML structure
		assert.Contains(t, stdout, "buildings:")
	})

	t.Run("InvalidFormat", func(t *testing.T) {
		// Test invalid output format
		args := []string{"building", "list", "--format", "invalid"}

		_, stderr, err := suite.runCLICommand(args)

		assert.Error(t, err)
		assert.Contains(t, stderr, "invalid format")
	})
}

// TestCLIConfiguration tests CLI configuration handling
func TestCLIConfiguration(t *testing.T) {
	suite := NewCLIIntegrationTestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	t.Run("ConfigFile", func(t *testing.T) {
		// Create a test config file
		configFile := filepath.Join(suite.testDir, "test-config.yaml")
		configContent := `
server:
  host: "localhost"
  port: 8080
database:
  host: "localhost"
  port: 5432
  name: "arxos_test"
`

		err := os.WriteFile(configFile, []byte(configContent), 0644)
		require.NoError(t, err)

		// Use config file
		args := []string{"--config", configFile, "version"}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "ArxOS")
	})

	t.Run("EnvironmentVariables", func(t *testing.T) {
		// Set environment variables
		os.Setenv("ARXOS_DB_HOST", "localhost")
		os.Setenv("ARXOS_DB_PORT", "5432")
		defer os.Unsetenv("ARXOS_DB_HOST")
		defer os.Unsetenv("ARXOS_DB_PORT")

		args := []string{"version"}

		stdout, stderr, err := suite.runCLICommand(args)

		assert.NoError(t, err)
		assert.Empty(t, stderr)
		assert.Contains(t, stdout, "ArxOS")
	})

	t.Run("InvalidConfigFile", func(t *testing.T) {
		// Create invalid config file
		configFile := filepath.Join(suite.testDir, "invalid-config.yaml")
		configContent := "invalid: yaml: content: ["

		err := os.WriteFile(configFile, []byte(configContent), 0644)
		require.NoError(t, err)

		// Try to use invalid config file
		args := []string{"--config", configFile, "version"}

		_, stderr, err := suite.runCLICommand(args)

		assert.Error(t, err)
		assert.Contains(t, stderr, "invalid config")
	})
}
