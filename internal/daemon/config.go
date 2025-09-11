package daemon

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"time"

	"gopkg.in/yaml.v2"
)

// DefaultConfig returns default daemon configuration
func DefaultConfig() *Config {
	return &Config{
		WatchDirs: []string{
			".arxos",
		},
		StateDir:     ".arxos",
		DatabasePath: filepath.Join(".arxos", "arxos.db"),
		SocketPath:   "/tmp/arxos.sock",
		
		AutoImport:   true,
		AutoExport:   false,
		SyncInterval: 5 * time.Minute,
		
		WatchPatterns: []string{
			"*.pdf",
			"*.ifc",
		},
		IgnorePatterns: []string{
			".*",
			"~*",
			"*.tmp",
			"*.bak",
		},
		
		MaxWorkers: 4,
		QueueSize:  100,
	}
}

// LoadConfig loads configuration from file
func LoadConfig(path string) (*Config, error) {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}
	
	config := DefaultConfig()
	
	// Try YAML first
	if err := yaml.Unmarshal(data, config); err != nil {
		// Try JSON
		if err := json.Unmarshal(data, config); err != nil {
			return nil, fmt.Errorf("failed to parse config (tried YAML and JSON): %w", err)
		}
	}
	
	// Validate and normalize paths
	if err := config.Validate(); err != nil {
		return nil, err
	}
	
	return config, nil
}

// SaveConfig saves configuration to file
func SaveConfig(config *Config, path string) error {
	// Determine format from extension
	ext := filepath.Ext(path)
	
	var data []byte
	var err error
	
	switch ext {
	case ".yaml", ".yml":
		data, err = yaml.Marshal(config)
	default:
		data, err = json.MarshalIndent(config, "", "  ")
	}
	
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}
	
	// Create directory if needed
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}
	
	// Write file
	if err := ioutil.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}
	
	return nil
}

// Validate validates the configuration
func (c *Config) Validate() error {
	// Ensure at least one watch directory
	if len(c.WatchDirs) == 0 {
		return fmt.Errorf("no watch directories specified")
	}
	
	// Validate watch directories exist
	for _, dir := range c.WatchDirs {
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			// Create directory if it doesn't exist
			if err := os.MkdirAll(dir, 0755); err != nil {
				return fmt.Errorf("watch directory %s does not exist and could not be created: %w", dir, err)
			}
		}
	}
	
	// Ensure state directory exists
	if c.StateDir != "" {
		if err := os.MkdirAll(c.StateDir, 0755); err != nil {
			return fmt.Errorf("failed to create state directory: %w", err)
		}
	}
	
	// Validate database path directory
	if c.DatabasePath != "" {
		dbDir := filepath.Dir(c.DatabasePath)
		if err := os.MkdirAll(dbDir, 0755); err != nil {
			return fmt.Errorf("failed to create database directory: %w", err)
		}
	}
	
	// Validate socket path directory
	if c.SocketPath != "" {
		socketDir := filepath.Dir(c.SocketPath)
		if err := os.MkdirAll(socketDir, 0755); err != nil {
			return fmt.Errorf("failed to create socket directory: %w", err)
		}
	}
	
	// Validate numeric values
	if c.MaxWorkers <= 0 {
		c.MaxWorkers = 4
	}
	if c.QueueSize <= 0 {
		c.QueueSize = 100
	}
	if c.SyncInterval <= 0 {
		c.SyncInterval = 5 * time.Minute
	}
	
	return nil
}

// MarshalJSON implements json.Marshaler
func (c *Config) MarshalJSON() ([]byte, error) {
	type Alias Config
	return json.Marshal(&struct {
		SyncInterval string `json:"sync_interval"`
		*Alias
	}{
		SyncInterval: c.SyncInterval.String(),
		Alias:        (*Alias)(c),
	})
}

// UnmarshalJSON implements json.Unmarshaler
func (c *Config) UnmarshalJSON(data []byte) error {
	type Alias Config
	aux := &struct {
		SyncInterval string `json:"sync_interval"`
		*Alias
	}{
		Alias: (*Alias)(c),
	}
	
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}
	
	if aux.SyncInterval != "" {
		duration, err := time.ParseDuration(aux.SyncInterval)
		if err != nil {
			return fmt.Errorf("invalid sync_interval: %w", err)
		}
		c.SyncInterval = duration
	}
	
	return nil
}

// MarshalYAML implements yaml.Marshaler
func (c *Config) MarshalYAML() (interface{}, error) {
	return map[string]interface{}{
		"watch_dirs":      c.WatchDirs,
		"state_dir":       c.StateDir,
		"database_path":   c.DatabasePath,
		"socket_path":     c.SocketPath,
		"auto_import":     c.AutoImport,
		"auto_export":     c.AutoExport,
		"sync_interval":   c.SyncInterval.String(),
		"watch_patterns":  c.WatchPatterns,
		"ignore_patterns": c.IgnorePatterns,
		"max_workers":     c.MaxWorkers,
		"queue_size":      c.QueueSize,
	}, nil
}

// UnmarshalYAML implements yaml.Unmarshaler
func (c *Config) UnmarshalYAML(unmarshal func(interface{}) error) error {
	var raw map[string]interface{}
	if err := unmarshal(&raw); err != nil {
		return err
	}
	
	// Parse each field
	if v, ok := raw["watch_dirs"].([]interface{}); ok {
		c.WatchDirs = make([]string, len(v))
		for i, dir := range v {
			c.WatchDirs[i] = fmt.Sprintf("%v", dir)
		}
	}
	
	if v, ok := raw["state_dir"].(string); ok {
		c.StateDir = v
	}
	
	if v, ok := raw["database_path"].(string); ok {
		c.DatabasePath = v
	}
	
	if v, ok := raw["socket_path"].(string); ok {
		c.SocketPath = v
	}
	
	if v, ok := raw["auto_import"].(bool); ok {
		c.AutoImport = v
	}
	
	if v, ok := raw["auto_export"].(bool); ok {
		c.AutoExport = v
	}
	
	if v, ok := raw["sync_interval"].(string); ok {
		duration, err := time.ParseDuration(v)
		if err != nil {
			return fmt.Errorf("invalid sync_interval: %w", err)
		}
		c.SyncInterval = duration
	}
	
	if v, ok := raw["watch_patterns"].([]interface{}); ok {
		c.WatchPatterns = make([]string, len(v))
		for i, pat := range v {
			c.WatchPatterns[i] = fmt.Sprintf("%v", pat)
		}
	}
	
	if v, ok := raw["ignore_patterns"].([]interface{}); ok {
		c.IgnorePatterns = make([]string, len(v))
		for i, pat := range v {
			c.IgnorePatterns[i] = fmt.Sprintf("%v", pat)
		}
	}
	
	if v, ok := raw["max_workers"].(int); ok {
		c.MaxWorkers = v
	}
	
	if v, ok := raw["queue_size"].(int); ok {
		c.QueueSize = v
	}
	
	return nil
}