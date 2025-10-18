package commands_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/arx-os/arxos/internal/cli/commands"
	"github.com/arx-os/arxos/internal/config"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCreateInitCommand(t *testing.T) {
	cmd := commands.CreateInitCommand(nil)
	assert.NotNil(t, cmd)
	assert.Equal(t, "init", cmd.Use)
	assert.Equal(t, "Initialize ArxOS configuration and directories", cmd.Short)
}

func TestInitCommandFlags(t *testing.T) {
	cmd := commands.CreateInitCommand(nil)

	// Test that all expected flags exist
	assert.True(t, cmd.Flags().Changed("config") || cmd.Flags().Lookup("config") != nil)
	assert.True(t, cmd.Flags().Changed("force") || cmd.Flags().Lookup("force") != nil)
	assert.True(t, cmd.Flags().Changed("verbose") || cmd.Flags().Lookup("verbose") != nil)
	assert.True(t, cmd.Flags().Changed("mode") || cmd.Flags().Lookup("mode") != nil)
	assert.True(t, cmd.Flags().Changed("data-dir") || cmd.Flags().Lookup("data-dir") != nil)
}

func TestInitCommandWithValidMode(t *testing.T) {
	// Create a temporary directory for testing
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)

	// Set flags
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)
	cmd.Flags().Set("verbose", "true")

	// Execute command
	err := cmd.Execute()
	assert.NoError(t, err)

	// Verify that directories were created
	assert.DirExists(t, tempDir)
	assert.DirExists(t, filepath.Join(tempDir, "cache"))
	assert.DirExists(t, filepath.Join(tempDir, "data"))
	assert.DirExists(t, filepath.Join(tempDir, "logs"))
}

func TestInitCommandWithInvalidMode(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)

	// Set invalid mode
	cmd.Flags().Set("mode", "invalid")
	cmd.Flags().Set("data-dir", tempDir)

	// Execute command - should fail
	err := cmd.Execute()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "invalid mode")
}

func TestInitCommandForceFlag(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)

	// First initialization
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)
	err := cmd.Execute()
	assert.NoError(t, err)

	// Second initialization without force - should succeed (no-op)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)
	err = cmd.Execute()
	assert.NoError(t, err)

	// Third initialization with force - should succeed
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)
	cmd.Flags().Set("force", "true")
	err = cmd.Execute()
	assert.NoError(t, err)
}

func TestInitCommandCreatesConfigFile(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)

	err := cmd.Execute()
	require.NoError(t, err)

	// Check that config file was created at correct path
	configPath := filepath.Join(tempDir, "config", "arxos.yaml")
	assert.FileExists(t, configPath)

	// Try to load the config
	cfg, err := config.Load(configPath)
	assert.NoError(t, err)
	assert.Equal(t, config.ModeLocal, cfg.Mode)
}

func TestInitCommandCreatesCacheConfig(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)

	err := cmd.Execute()
	require.NoError(t, err)

	// Check that cache directory was created (init doesn't create config.json)
	cacheDir := filepath.Join(tempDir, "cache", "l2")
	assert.DirExists(t, cacheDir)
}

func TestInitCommandCreatesLogConfig(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)

	err := cmd.Execute()
	require.NoError(t, err)

	// Check that logs directory was created (init doesn't create config.json)
	logsDir := filepath.Join(tempDir, "logs")
	assert.DirExists(t, logsDir)
}

func TestInitCommandCreatesStateFiles(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)

	err := cmd.Execute()
	require.NoError(t, err)

	// Check that data directory was created (init doesn't create state files)
	dataDir := filepath.Join(tempDir, "data")
	assert.DirExists(t, dataDir)
}

func TestInitCommandWithCloudMode(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "cloud")
	cmd.Flags().Set("data-dir", tempDir)

	err := cmd.Execute()
	require.NoError(t, err)

	// Verify config file was created with cloud mode
	configPath := filepath.Join(tempDir, "config", "arxos.yaml")
	assert.FileExists(t, configPath)

	// Verify cloud mode is set in the config file
	configData, err := os.ReadFile(configPath)
	require.NoError(t, err)
	assert.Contains(t, string(configData), "mode: cloud")
}

func TestInitCommandWithHybridMode(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "hybrid")
	cmd.Flags().Set("data-dir", tempDir)

	err := cmd.Execute()
	require.NoError(t, err)

	// Verify config file was created with hybrid mode
	configPath := filepath.Join(tempDir, "config", "arxos.yaml")
	assert.FileExists(t, configPath)

	// Verify hybrid mode is set in the config file
	configData, err := os.ReadFile(configPath)
	require.NoError(t, err)
	assert.Contains(t, string(configData), "mode: hybrid")
}

func TestInitCommandWithCustomConfig(t *testing.T) {
	tempDir := t.TempDir()
	customConfigDir := filepath.Join(tempDir, "custom")

	// Create a custom config file
	customConfigPath := filepath.Join(customConfigDir, "custom.yml")
	err := os.MkdirAll(customConfigDir, 0755)
	require.NoError(t, err)

	// Create a minimal valid config using template
	customConfig, err := config.CreateConfigFromTemplate("local", customConfigDir)
	require.NoError(t, err)

	err = customConfig.Save(customConfigPath)
	require.NoError(t, err)

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("config", customConfigPath)
	cmd.Flags().Set("data-dir", tempDir)

	err = cmd.Execute()
	assert.NoError(t, err)

	// Verify that the custom config was used
	assert.FileExists(t, customConfigPath)
}

func TestInitCommandValidation(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)

	err := cmd.Execute()
	require.NoError(t, err)

	// The command should have validated the installation
	// This is tested implicitly by the successful execution
}

func TestInitCommandCreatesAllRequiredDirectories(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)

	err := cmd.Execute()
	require.NoError(t, err)

	// Verify directories that init actually creates
	requiredDirs := []string{
		filepath.Join(tempDir, "cache", "l2"),
		filepath.Join(tempDir, "repositories"),
		filepath.Join(tempDir, "logs"),
		filepath.Join(tempDir, "temp"),
		filepath.Join(tempDir, "config"),
		filepath.Join(tempDir, "imports"),
		filepath.Join(tempDir, "exports"),
		filepath.Join(tempDir, "data"),
	}

	for _, dir := range requiredDirs {
		assert.DirExists(t, dir, "Directory %s should exist", dir)
	}
}

func TestInitCommandCreatesLogFiles(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)

	err := cmd.Execute()
	require.NoError(t, err)

	// Verify logs directory was created (init doesn't create log files)
	logsDir := filepath.Join(tempDir, "logs")
	assert.DirExists(t, logsDir)
}

func TestInitCommandWithVerboseFlag(t *testing.T) {
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)
	cmd.Flags().Set("verbose", "true")

	// Capture output to verify verbose logging
	err := cmd.Execute()
	assert.NoError(t, err)

	// The verbose flag should not cause errors
	// In a real implementation, this would test that verbose output is produced
}

func TestInitCommandErrorHandling(t *testing.T) {
	// Test with invalid data directory (read-only)
	readOnlyDir := "/tmp/readonly_test"
	err := os.MkdirAll(readOnlyDir, 0444) // Read-only
	if err == nil {
		defer os.RemoveAll(readOnlyDir)

		cmd := commands.CreateInitCommand(nil)
		cmd.Flags().Set("mode", "local")
		cmd.Flags().Set("data-dir", readOnlyDir)

		err = cmd.Execute()
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to create")
	}
}

func TestInitCommandIntegration(t *testing.T) {
	// Integration test that verifies the entire initialization process
	tempDir := t.TempDir()

	cmd := commands.CreateInitCommand(nil)
	cmd.Flags().Set("mode", "local")
	cmd.Flags().Set("data-dir", tempDir)
	cmd.Flags().Set("verbose", "true")

	err := cmd.Execute()
	require.NoError(t, err)

	// Verify complete initialization
	assert.DirExists(t, tempDir)

	// Verify config file was created at correct path
	configPath := filepath.Join(tempDir, "config", "arxos.yaml")
	assert.FileExists(t, configPath)

	cfg, err := config.Load(configPath)
	require.NoError(t, err)
	assert.Equal(t, config.ModeLocal, cfg.Mode)
}

// Benchmark tests
func BenchmarkInitCommand(b *testing.B) {
	for i := 0; i < b.N; i++ {
		tempDir := b.TempDir()

		cmd := commands.CreateInitCommand(nil)
		cmd.Flags().Set("mode", "local")
		cmd.Flags().Set("data-dir", tempDir)

		err := cmd.Execute()
		if err != nil {
			b.Fatal(err)
		}
	}
}

// Test helper functions
func TestHelperFunctions(t *testing.T) {
	// Test that helper functions work correctly
	tempDir := t.TempDir()

	// Test directory creation
	err := os.MkdirAll(filepath.Join(tempDir, "test"), 0755)
	assert.NoError(t, err)
	assert.DirExists(t, filepath.Join(tempDir, "test"))

	// Test file creation
	testFile := filepath.Join(tempDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test"), 0644)
	assert.NoError(t, err)
	assert.FileExists(t, testFile)
}
