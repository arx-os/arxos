package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/ecosystem"
	"github.com/arx-os/arxos/internal/hardware"
)

// HardwareIntegrationService integrates the hardware platform with the ecosystem
type HardwareIntegrationService struct {
	db               *database.PostGISDB
	hardwarePlatform *hardware.Platform
}

// NewHardwareIntegrationService creates a new hardware integration service
func NewHardwareIntegrationService(db *database.PostGISDB) *HardwareIntegrationService {
	// Create hardware platform
	factory := NewHardwarePlatformFactory(db)
	hardwarePlatform := factory.CreatePlatform()

	return &HardwareIntegrationService{
		db:               db,
		hardwarePlatform: hardwarePlatform,
	}
}

// RegisterDevice registers a device through the ecosystem interface
func (his *HardwareIntegrationService) RegisterDevice(ctx context.Context, req ecosystem.RegisterDeviceRequest) (*ecosystem.Device, error) {
	// Convert ecosystem request to hardware request
	hardwareReq := hardware.RegisterDeviceRequest{
		Name:       req.Name,
		Type:       req.Type,
		TemplateID: req.TemplateID,
		Config:     req.Config,
		Location: hardware.DeviceLocation{
			BuildingID: "default",
			Floor:      "1",
			Room:       "101",
			Position:   make(map[string]interface{}),
			Path:       "/buildings/default/floors/1/rooms/101",
		},
	}

	// Register device through hardware platform
	hardwareDevice, err := his.hardwarePlatform.RegisterDevice(ctx, hardwareReq)
	if err != nil {
		return nil, fmt.Errorf("failed to register device: %w", err)
	}

	// Convert hardware device to ecosystem device
	ecosystemDevice := &ecosystem.Device{
		ID:         hardwareDevice.ID,
		Name:       hardwareDevice.Name,
		Type:       hardwareDevice.Type,
		TemplateID: hardwareDevice.TemplateID,
		Status:     hardwareDevice.Status,
		Config:     hardwareDevice.Config,
	}

	return ecosystemDevice, nil
}

// ListDevices lists devices through the ecosystem interface
func (his *HardwareIntegrationService) ListDevices(ctx context.Context, userID string) ([]*ecosystem.Device, error) {
	// List devices through hardware platform
	hardwareDevices, err := his.hardwarePlatform.ListDevices(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to list devices: %w", err)
	}

	// Convert hardware devices to ecosystem devices
	var ecosystemDevices []*ecosystem.Device
	for _, hardwareDevice := range hardwareDevices {
		ecosystemDevice := &ecosystem.Device{
			ID:         hardwareDevice.ID,
			Name:       hardwareDevice.Name,
			Type:       hardwareDevice.Type,
			TemplateID: hardwareDevice.TemplateID,
			Status:     hardwareDevice.Status,
			Config:     hardwareDevice.Config,
		}
		ecosystemDevices = append(ecosystemDevices, ecosystemDevice)
	}

	return ecosystemDevices, nil
}

// ConfigureGateway configures a gateway through the ecosystem interface
func (his *HardwareIntegrationService) ConfigureGateway(ctx context.Context, gatewayID string, config ecosystem.GatewayConfig) error {
	// Convert ecosystem config to hardware config
	hardwareConfig := hardware.GatewayConfig{
		Protocols: config.Protocols,
		Settings:  config.Settings,
		Security: hardware.SecurityConfig{
			Encryption:     "AES-256",
			Authentication: "OAuth2",
			Certificates:   []string{},
			AccessControl:  make(map[string]interface{}),
		},
		Network: hardware.NetworkConfig{
			Protocol:  "TCP",
			Port:      8080,
			Bandwidth: 1000,
			Latency:   50,
			Settings:  make(map[string]interface{}),
		},
		Monitoring: hardware.MonitoringConfig{
			Enabled:   true,
			Interval:  60,
			Metrics:   []string{"cpu", "memory", "network"},
			Retention: 30,
		},
	}

	// Configure gateway through hardware platform
	return his.hardwarePlatform.ConfigureGateway(ctx, gatewayID, hardwareConfig)
}

// GetHardwarePlatform returns the underlying hardware platform for direct access
func (his *HardwareIntegrationService) GetHardwarePlatform() *hardware.Platform {
	return his.hardwarePlatform
}

// InitializeHardwarePlatform initializes the hardware platform with default data
func (his *HardwareIntegrationService) InitializeHardwarePlatform(ctx context.Context) error {
	// Create some default device templates
	defaultTemplates := []hardware.CreateTemplateRequest{
		{
			Name:        "Temperature Sensor",
			Type:        "sensor",
			Description: "Basic temperature sensor for environmental monitoring",
			Schema: map[string]interface{}{
				"properties": map[string]interface{}{
					"temperature": map[string]interface{}{
						"type":        "number",
						"description": "Temperature in Celsius",
						"unit":        "°C",
					},
					"humidity": map[string]interface{}{
						"type":        "number",
						"description": "Humidity percentage",
						"unit":        "%",
					},
				},
			},
			Firmware: []byte("default_firmware"),
			SDK: hardware.SDKInfo{
				Version:       "1.0.0",
				Language:      "C++",
				Documentation: "https://docs.arxos.dev/sensors/temperature",
				Examples:      []string{"basic_reading", "calibration", "alerts"},
				ReleasedAt:    time.Now(),
			},
		},
		{
			Name:        "Smart Switch",
			Type:        "actuator",
			Description: "Smart switch for controlling electrical devices",
			Schema: map[string]interface{}{
				"properties": map[string]interface{}{
					"state": map[string]interface{}{
						"type":        "boolean",
						"description": "Switch state (on/off)",
					},
					"power_consumption": map[string]interface{}{
						"type":        "number",
						"description": "Current power consumption",
						"unit":        "W",
					},
				},
			},
			Firmware: []byte("default_firmware"),
			SDK: hardware.SDKInfo{
				Version:       "1.0.0",
				Language:      "C++",
				Documentation: "https://docs.arxos.dev/actuators/switch",
				Examples:      []string{"basic_control", "scheduling", "monitoring"},
				ReleasedAt:    time.Now(),
			},
		},
	}

	// Create templates
	for _, templateReq := range defaultTemplates {
		_, err := his.hardwarePlatform.CreateTemplate(ctx, templateReq)
		if err != nil {
			return fmt.Errorf("failed to create default template: %w", err)
		}
	}

	// Create some default certified devices for marketplace
	// This would typically be done through an admin interface
	// For now, we'll skip this as it requires more complex setup

	return nil
}
