package tui

import (
	"github.com/arx-os/arxos/internal/config"
)

// LoadFromConfig loads TUI configuration from the main ArxOS config
func LoadFromConfig(cfg *config.Config) *config.TUIConfig {
	if cfg == nil {
		// Return default config if main config is nil
		defaultCfg := config.Default()
		return &defaultCfg.TUI
	}
	return &cfg.TUI
}

// NewTUIConfig creates a TUI configuration from the main config
func NewTUIConfig(cfg *config.Config) *config.TUIConfig {
	return LoadFromConfig(cfg)
}
