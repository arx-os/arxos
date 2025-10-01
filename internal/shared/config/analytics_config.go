package config

import (
	"fmt"
	"time"
)

// AnalyticsConfig contains configuration for analytics services
type AnalyticsConfig struct {
	// Data processing settings
	BatchSize           int           `yaml:"batch_size" json:"batch_size"`
	ProcessingInterval  time.Duration `yaml:"processing_interval" json:"processing_interval"`
	DataRetentionPeriod time.Duration `yaml:"data_retention_period" json:"data_retention_period"`

	// Model settings
	ModelUpdateInterval    time.Duration `yaml:"model_update_interval" json:"model_update_interval"`
	MaxTrainingDataPoints  int           `yaml:"max_training_data_points" json:"max_training_data_points"`
	ModelAccuracyThreshold float64       `yaml:"model_accuracy_threshold" json:"model_accuracy_threshold"`

	// Alert settings
	AlertCooldownPeriod time.Duration `yaml:"alert_cooldown_period" json:"alert_cooldown_period"`
	MaxAlertsPerHour    int           `yaml:"max_alerts_per_hour" json:"max_alerts_per_hour"`

	// Report settings
	ReportGenerationTimeout time.Duration `yaml:"report_generation_timeout" json:"report_generation_timeout"`
	MaxReportSize           int64         `yaml:"max_report_size" json:"max_report_size"`
	ReportStoragePath       string        `yaml:"report_storage_path" json:"report_storage_path"`

	// Performance settings
	MaxConcurrentProcessing int           `yaml:"max_concurrent_processing" json:"max_concurrent_processing"`
	ProcessingTimeout       time.Duration `yaml:"processing_timeout" json:"processing_timeout"`

	// Feature flags
	EnablePredictiveAnalytics   bool `yaml:"enable_predictive_analytics" json:"enable_predictive_analytics"`
	EnableAnomalyDetection      bool `yaml:"enable_anomaly_detection" json:"enable_anomaly_detection"`
	EnableEnergyOptimization    bool `yaml:"enable_energy_optimization" json:"enable_energy_optimization"`
	EnablePerformanceMonitoring bool `yaml:"enable_performance_monitoring" json:"enable_performance_monitoring"`
}

// DefaultAnalyticsConfig returns default analytics configuration
func DefaultAnalyticsConfig() *AnalyticsConfig {
	return &AnalyticsConfig{
		BatchSize:                   1000,
		ProcessingInterval:          time.Minute * 5,
		DataRetentionPeriod:         time.Hour * 24 * 30, // 30 days
		ModelUpdateInterval:         time.Hour * 24,      // 24 hours
		MaxTrainingDataPoints:       10000,
		ModelAccuracyThreshold:      0.8,
		AlertCooldownPeriod:         time.Minute * 15,
		MaxAlertsPerHour:            100,
		ReportGenerationTimeout:     time.Minute * 10,
		MaxReportSize:               50 * 1024 * 1024, // 50MB
		ReportStoragePath:           "/tmp/reports",
		MaxConcurrentProcessing:     10,
		ProcessingTimeout:           time.Minute * 2,
		EnablePredictiveAnalytics:   true,
		EnableAnomalyDetection:      true,
		EnableEnergyOptimization:    true,
		EnablePerformanceMonitoring: true,
	}
}

// Validate validates the analytics configuration
func (c *AnalyticsConfig) Validate() error {
	if c.BatchSize <= 0 {
		return fmt.Errorf("batch_size must be positive")
	}

	if c.ProcessingInterval <= 0 {
		return fmt.Errorf("processing_interval must be positive")
	}

	if c.DataRetentionPeriod <= 0 {
		return fmt.Errorf("data_retention_period must be positive")
	}

	if c.ModelUpdateInterval <= 0 {
		return fmt.Errorf("model_update_interval must be positive")
	}

	if c.MaxTrainingDataPoints <= 0 {
		return fmt.Errorf("max_training_data_points must be positive")
	}

	if c.ModelAccuracyThreshold < 0 || c.ModelAccuracyThreshold > 1 {
		return fmt.Errorf("model_accuracy_threshold must be between 0 and 1")
	}

	if c.AlertCooldownPeriod <= 0 {
		return fmt.Errorf("alert_cooldown_period must be positive")
	}

	if c.MaxAlertsPerHour <= 0 {
		return fmt.Errorf("max_alerts_per_hour must be positive")
	}

	if c.ReportGenerationTimeout <= 0 {
		return fmt.Errorf("report_generation_timeout must be positive")
	}

	if c.MaxReportSize <= 0 {
		return fmt.Errorf("max_report_size must be positive")
	}

	if c.MaxConcurrentProcessing <= 0 {
		return fmt.Errorf("max_concurrent_processing must be positive")
	}

	if c.ProcessingTimeout <= 0 {
		return fmt.Errorf("processing_timeout must be positive")
	}

	return nil
}
