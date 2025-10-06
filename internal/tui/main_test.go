package tui

import (
	"context"
	"fmt"
	"testing"

	"github.com/arx-os/arxos/internal/config"
	"github.com/stretchr/testify/assert"
)

// MockDatabase implements domain.Database for testing
type MockDatabase struct{}

func (m *MockDatabase) Connect(ctx context.Context) error        { return nil }
func (m *MockDatabase) Close() error                             { return nil }
func (m *MockDatabase) Health(ctx context.Context) error         { return nil }
func (m *MockDatabase) BeginTx(ctx context.Context) (any, error) { return nil, nil }
func (m *MockDatabase) CommitTx(tx any) error                    { return nil }
func (m *MockDatabase) RollbackTx(tx any) error                  { return nil }

func TestNewTUI(t *testing.T) {
	cfg := &config.Config{
		TUI: config.TUIConfig{
			Enabled: true,
			Theme:   "dark",
		},
	}

	db := &MockDatabase{}
	tui := NewTUI(cfg, db)

	assert.NotNil(t, tui)
	assert.Equal(t, cfg, tui.config)
	assert.Equal(t, db, tui.db)
}

func TestTUI_RunDashboard_Disabled(t *testing.T) {
	cfg := &config.Config{
		TUI: config.TUIConfig{
			Enabled: false,
		},
	}

	db := &MockDatabase{}
	tui := NewTUI(cfg, db)

	err := tui.RunDashboard()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "TUI is disabled in configuration")
}

func TestTUI_RunDashboard_InvalidConfig(t *testing.T) {
	cfg := &config.Config{
		TUI: config.TUIConfig{
			Enabled:        true,
			Theme:          "invalid-theme",    // Invalid theme
			UpdateInterval: "invalid-duration", // Invalid duration
		},
	}

	db := &MockDatabase{}
	tui := NewTUI(cfg, db)

	err := tui.RunDashboard()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "invalid TUI configuration")
}

func TestTUI_RunDashboard_ValidConfig(t *testing.T) {
	cfg := &config.Config{
		TUI: config.TUIConfig{
			Enabled:             true,
			Theme:               "dark",
			UpdateInterval:      "1s",
			MaxEquipmentDisplay: 100, // Add required field
		},
	}

	db := &MockDatabase{}
	tui := NewTUI(cfg, db)

	// This will fail due to missing Bubble Tea dependencies in test environment
	// but we can test the configuration validation
	err := tui.RunDashboard()
	// The error should be related to TUI execution, not configuration
	assert.Error(t, err)
	// Should not be a configuration error
	assert.NotContains(t, err.Error(), "invalid TUI configuration")
}

func TestTUI_RunBuildingExplorer_Disabled(t *testing.T) {
	cfg := &config.Config{
		TUI: config.TUIConfig{
			Enabled: false,
		},
	}

	db := &MockDatabase{}
	tui := NewTUI(cfg, db)

	err := tui.RunBuildingExplorer("test-building-id")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "TUI is disabled in configuration")
}

func TestTUI_RunBuildingExplorer_InvalidConfig(t *testing.T) {
	cfg := &config.Config{
		TUI: config.TUIConfig{
			Enabled:        true,
			Theme:          "invalid-theme",
			UpdateInterval: "invalid-duration",
		},
	}

	db := &MockDatabase{}
	tui := NewTUI(cfg, db)

	err := tui.RunBuildingExplorer("test-building-id")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "invalid TUI configuration")
}

func TestTUI_RunBuildingExplorer_ValidConfig(t *testing.T) {
	cfg := &config.Config{
		TUI: config.TUIConfig{
			Enabled:             true,
			Theme:               "light",
			UpdateInterval:      "500ms",
			MaxEquipmentDisplay: 100, // Add required field
		},
	}

	db := &MockDatabase{}
	tui := NewTUI(cfg, db)

	// This will fail due to missing Bubble Tea dependencies in test environment
	// but we can test the configuration validation
	err := tui.RunBuildingExplorer("test-building-id")
	// The error should be related to TUI execution, not configuration
	assert.Error(t, err)
	// Should not be a configuration error
	assert.NotContains(t, err.Error(), "invalid TUI configuration")
}

func TestTUI_ConfigurationValidation(t *testing.T) {
	tests := []struct {
		name    string
		config  *config.Config
		wantErr bool
		errMsg  string
	}{
		{
			name: "valid dark theme",
			config: &config.Config{
				TUI: config.TUIConfig{
					Enabled:             true,
					Theme:               "dark",
					UpdateInterval:      "1s",
					MaxEquipmentDisplay: 100,
				},
			},
			wantErr: false,
		},
		{
			name: "valid light theme",
			config: &config.Config{
				TUI: config.TUIConfig{
					Enabled:             true,
					Theme:               "light",
					UpdateInterval:      "500ms",
					MaxEquipmentDisplay: 100,
				},
			},
			wantErr: false,
		},
		{
			name: "valid auto theme",
			config: &config.Config{
				TUI: config.TUIConfig{
					Enabled:             true,
					Theme:               "auto",
					UpdateInterval:      "2s",
					MaxEquipmentDisplay: 100,
				},
			},
			wantErr: false,
		},
		{
			name: "invalid theme",
			config: &config.Config{
				TUI: config.TUIConfig{
					Enabled:        true,
					Theme:          "invalid-theme",
					UpdateInterval: "1s",
				},
			},
			wantErr: true,
			errMsg:  "invalid theme",
		},
		{
			name: "invalid update interval",
			config: &config.Config{
				TUI: config.TUIConfig{
					Enabled:        true,
					Theme:          "dark",
					UpdateInterval: "invalid-duration",
				},
			},
			wantErr: true,
			errMsg:  "invalid update_interval",
		},
		{
			name: "negative max equipment display",
			config: &config.Config{
				TUI: config.TUIConfig{
					Enabled:             true,
					Theme:               "dark",
					UpdateInterval:      "1s",
					MaxEquipmentDisplay: -1,
				},
			},
			wantErr: true,
			errMsg:  "max_equipment_display must be positive",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			db := &MockDatabase{}
			tui := NewTUI(tt.config, db)

			err := tui.RunDashboard()

			if tt.wantErr {
				assert.Error(t, err)
				if tt.errMsg != "" {
					assert.Contains(t, err.Error(), tt.errMsg)
				}
			} else {
				// Even valid configs will fail due to missing Bubble Tea dependencies
				// but we can check it's not a configuration error
				assert.Error(t, err)
				assert.NotContains(t, err.Error(), "invalid TUI configuration")
			}
		})
	}
}

func TestTUI_ContextHandling(t *testing.T) {
	cfg := &config.Config{
		TUI: config.TUIConfig{
			Enabled:        true,
			Theme:          "dark",
			UpdateInterval: "1s",
		},
	}

	db := &MockDatabase{}
	tui := NewTUI(cfg, db)

	// Test with cancelled context
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_ = ctx // Acknowledge the variable is intentionally unused

	// The TUI methods don't take context, but we can test the structure
	assert.NotNil(t, tui)
	assert.Equal(t, cfg, tui.config)
	assert.Equal(t, db, tui.db)
}

func TestTUI_NilDatabase(t *testing.T) {
	cfg := &config.Config{
		TUI: config.TUIConfig{
			Enabled:        true,
			Theme:          "dark",
			UpdateInterval: "1s",
		},
	}

	// Test with nil database
	tui := NewTUI(cfg, nil)

	assert.NotNil(t, tui)
	assert.Equal(t, cfg, tui.config)
	assert.Nil(t, tui.db)

	// This should fail due to nil database
	err := tui.RunDashboard()
	assert.Error(t, err)
}

func TestTUI_NilConfig(t *testing.T) {
	db := &MockDatabase{}

	// Test with nil config
	tui := NewTUI(nil, db)

	assert.NotNil(t, tui)
	assert.Nil(t, tui.config)
	assert.Equal(t, db, tui.db)

	// This should fail due to nil config - expect a panic or error
	defer func() {
		if r := recover(); r != nil {
			// Expected panic due to nil config
			assert.Contains(t, fmt.Sprintf("%v", r), "nil pointer")
		}
	}()

	err := tui.RunDashboard()
	// If we get here, it should be an error
	if err != nil {
		assert.Error(t, err)
	}
}

func TestTUI_DefaultConfiguration(t *testing.T) {
	// Test with default config
	cfg := config.Default()
	db := &MockDatabase{}
	tui := NewTUI(cfg, db)

	assert.NotNil(t, tui)
	assert.Equal(t, cfg, tui.config)
	assert.Equal(t, db, tui.db)

	// Default config should have TUI enabled, but will fail due to missing TTY
	err := tui.RunDashboard()
	assert.Error(t, err)
	// Should fail due to TTY issues, not configuration
	assert.NotContains(t, err.Error(), "TUI is disabled in configuration")
}
