package di

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/monitoring"
)

// MonitoringConfig holds configuration for monitoring components
type MonitoringConfig struct {
	Enabled          bool   `json:"enabled"`
	MetricsInterval  int    `json:"metrics_interval"` // seconds
	HealthInterval   int    `json:"health_interval"`  // seconds
	HealthTimeout    int    `json:"health_timeout"`   // seconds
	DashboardPort    int    `json:"dashboard_port"`
	DashboardEnabled bool   `json:"dashboard_enabled"`
	AlertingEnabled  bool   `json:"alerting_enabled"`
	LogLevel         string `json:"log_level"`
}

// MonitoringServices holds all monitoring-related services
type MonitoringServices struct {
	MetricsCollector *monitoring.MetricsCollector
	HealthMonitor    *monitoring.HealthMonitor
	AlertManager     *monitoring.AlertManager
	Tracer           *monitoring.Tracer
	Dashboard        *monitoring.Dashboard
}

// NewMonitoringServices creates monitoring services
func NewMonitoringServices(config *MonitoringConfig) *MonitoringServices {
	if !config.Enabled {
		return &MonitoringServices{}
	}

	// Create monitoring components
	metricsCollector := monitoring.NewMetricsCollector()
	healthMonitor := monitoring.NewHealthMonitor(
		time.Duration(config.HealthInterval)*time.Second,
		time.Duration(config.HealthTimeout)*time.Second,
	)
	alertManager := monitoring.NewAlertManager(time.Duration(config.HealthInterval) * time.Second)
	tracer := monitoring.NewTracer()

	// Create dashboard
	dashboard := monitoring.NewDashboard(metricsCollector, healthMonitor, alertManager, tracer)

	return &MonitoringServices{
		MetricsCollector: metricsCollector,
		HealthMonitor:    healthMonitor,
		AlertManager:     alertManager,
		Tracer:           tracer,
		Dashboard:        dashboard,
	}
}

// InitializeMonitoring initializes monitoring for the DI container
func (c *Container) InitializeMonitoring(ctx context.Context, config *MonitoringConfig) error {
	if !config.Enabled {
		return nil
	}

	// Create monitoring services
	monitoringServices := NewMonitoringServices(config)

	// Register monitoring services in container
	c.RegisterSingleton("metrics_collector", monitoringServices.MetricsCollector)
	c.RegisterSingleton("health_monitor", monitoringServices.HealthMonitor)
	c.RegisterSingleton("alert_manager", monitoringServices.AlertManager)
	c.RegisterSingleton("tracer", monitoringServices.Tracer)
	c.RegisterSingleton("dashboard", monitoringServices.Dashboard)

	// Start background monitoring
	go monitoringServices.MetricsCollector.StartMetricsCollection(ctx, time.Duration(config.MetricsInterval)*time.Second)
	go monitoringServices.HealthMonitor.StartHealthMonitoring(ctx)

	// Start dashboard if enabled
	if config.DashboardEnabled {
		go func() {
			addr := fmt.Sprintf(":%d", config.DashboardPort)
			if err := monitoringServices.Dashboard.StartDashboard(ctx, addr); err != nil {
				// Log error but don't fail initialization
				fmt.Printf("Failed to start monitoring dashboard: %v\n", err)
			}
		}()
	}

	// Register health checkers for infrastructure services
	c.registerHealthCheckers(ctx, monitoringServices.HealthMonitor)

	// Setup default alert rules
	c.setupDefaultAlertRules(monitoringServices.AlertManager)

	return nil
}

// registerHealthCheckers registers health checkers for infrastructure services
func (c *Container) registerHealthCheckers(ctx context.Context, healthMonitor *monitoring.HealthMonitor) {
	// Register database health checker
	if db, err := c.Get("database"); err == nil {
		if dbService, ok := db.(interface {
			IsHealthy() bool
			GetStats() map[string]interface{}
		}); ok {
			dbChecker := monitoring.NewDatabaseHealthChecker("postgis", dbService)
			healthMonitor.RegisterHealthChecker(dbChecker)
		}
	}

	// Register cache health checker
	if cache, err := c.Get("cache"); err == nil {
		if cacheService, ok := cache.(interface {
			IsHealthy() bool
			GetStats() map[string]interface{}
		}); ok {
			cacheChecker := monitoring.NewCacheHealthChecker("redis", cacheService)
			healthMonitor.RegisterHealthChecker(cacheChecker)
		}
	}

	// Register storage health checker
	if storage, err := c.Get("storage"); err == nil {
		if storageService, ok := storage.(interface {
			IsHealthy() bool
			GetStats() map[string]interface{}
		}); ok {
			storageChecker := monitoring.NewStorageHealthChecker("local", storageService)
			healthMonitor.RegisterHealthChecker(storageChecker)
		}
	}
}

// setupDefaultAlertRules sets up default alert rules
func (c *Container) setupDefaultAlertRules(alertManager *monitoring.AlertManager) {
	// High error rate alert
	alertManager.AddAlertRule(&monitoring.AlertRule{
		ID:          "high_error_rate",
		Name:        "High Error Rate",
		Description: "Error rate is above 5%",
		Level:       monitoring.AlertLevelWarning,
		Condition:   "error_rate > 0.05",
		Duration:    5 * time.Minute,
		Labels:      map[string]string{"service": "api"},
		Annotations: map[string]string{"summary": "High error rate detected"},
		Enabled:     true,
	})

	// High response time alert
	alertManager.AddAlertRule(&monitoring.AlertRule{
		ID:          "high_response_time",
		Name:        "High Response Time",
		Description: "Response time is above 1 second",
		Level:       monitoring.AlertLevelWarning,
		Condition:   "response_time > 1.0",
		Duration:    2 * time.Minute,
		Labels:      map[string]string{"service": "api"},
		Annotations: map[string]string{"summary": "High response time detected"},
		Enabled:     true,
	})

	// Service down alert
	alertManager.AddAlertRule(&monitoring.AlertRule{
		ID:          "service_down",
		Name:        "Service Down",
		Description: "Service is not responding",
		Level:       monitoring.AlertLevelCritical,
		Condition:   "health_status == 'unhealthy'",
		Duration:    1 * time.Minute,
		Labels:      map[string]string{"service": "all"},
		Annotations: map[string]string{"summary": "Service is down"},
		Enabled:     true,
	})

	// Database connection alert
	alertManager.AddAlertRule(&monitoring.AlertRule{
		ID:          "database_down",
		Name:        "Database Down",
		Description: "Database is not responding",
		Level:       monitoring.AlertLevelCritical,
		Condition:   "database_health == 'unhealthy'",
		Duration:    30 * time.Second,
		Labels:      map[string]string{"service": "database"},
		Annotations: map[string]string{"summary": "Database is down"},
		Enabled:     true,
	})

	// Cache connection alert
	alertManager.AddAlertRule(&monitoring.AlertRule{
		ID:          "cache_down",
		Name:        "Cache Down",
		Description: "Cache is not responding",
		Level:       monitoring.AlertLevelWarning,
		Condition:   "cache_health == 'unhealthy'",
		Duration:    1 * time.Minute,
		Labels:      map[string]string{"service": "cache"},
		Annotations: map[string]string{"summary": "Cache is down"},
		Enabled:     true,
	})

	// Storage alert
	alertManager.AddAlertRule(&monitoring.AlertRule{
		ID:          "storage_down",
		Name:        "Storage Down",
		Description: "Storage is not responding",
		Level:       monitoring.AlertLevelWarning,
		Condition:   "storage_health == 'unhealthy'",
		Duration:    1 * time.Minute,
		Labels:      map[string]string{"service": "storage"},
		Annotations: map[string]string{"summary": "Storage is down"},
		Enabled:     true,
	})
}

// GetMonitoringServices retrieves monitoring services from the container
func (c *Container) GetMonitoringServices() (*MonitoringServices, error) {
	metricsCollector, err := c.Get("metrics_collector")
	if err != nil {
		return nil, fmt.Errorf("metrics collector not found: %w", err)
	}

	healthMonitor, err := c.Get("health_monitor")
	if err != nil {
		return nil, fmt.Errorf("health monitor not found: %w", err)
	}

	alertManager, err := c.Get("alert_manager")
	if err != nil {
		return nil, fmt.Errorf("alert manager not found: %w", err)
	}

	tracer, err := c.Get("tracer")
	if err != nil {
		return nil, fmt.Errorf("tracer not found: %w", err)
	}

	dashboard, err := c.Get("dashboard")
	if err != nil {
		return nil, fmt.Errorf("dashboard not found: %w", err)
	}

	return &MonitoringServices{
		MetricsCollector: metricsCollector.(*monitoring.MetricsCollector),
		HealthMonitor:    healthMonitor.(*monitoring.HealthMonitor),
		AlertManager:     alertManager.(*monitoring.AlertManager),
		Tracer:           tracer.(*monitoring.Tracer),
		Dashboard:        dashboard.(*monitoring.Dashboard),
	}, nil
}

// DefaultMonitoringConfig returns default monitoring configuration
func DefaultMonitoringConfig() *MonitoringConfig {
	return &MonitoringConfig{
		Enabled:          true,
		MetricsInterval:  30,
		HealthInterval:   30,
		HealthTimeout:    5,
		DashboardPort:    8081,
		DashboardEnabled: true,
		AlertingEnabled:  true,
		LogLevel:         "info",
	}
}
