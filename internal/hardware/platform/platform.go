package platform

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/hardware/certification"
	"github.com/arx-os/arxos/internal/hardware/devices"
	"github.com/arx-os/arxos/internal/hardware/protocols"
)

// Platform represents the hardware platform manager
type Platform struct {
	devices       map[string]*devices.Device
	protocols     map[string]protocols.Protocol
	gateways      map[string]*Gateway
	certification *certification.CertificationManager
	metrics       *PlatformMetrics
}

// Gateway represents a hardware gateway for protocol translation
type Gateway struct {
	ID        string                 `json:"id"`
	Name      string                 `json:"name"`
	Type      string                 `json:"type"`
	Location  string                 `json:"location"`
	Protocols []string               `json:"protocols"`
	Status    GatewayStatus          `json:"status"`
	LastSeen  time.Time              `json:"last_seen"`
	Config    map[string]interface{} `json:"config"`
	Devices   []string               `json:"devices"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

// GatewayStatus represents the operational status of a gateway
type GatewayStatus string

const (
	GatewayStatusOnline      GatewayStatus = "online"
	GatewayStatusOffline     GatewayStatus = "offline"
	GatewayStatusError       GatewayStatus = "error"
	GatewayStatusUpdating    GatewayStatus = "updating"
	GatewayStatusMaintenance GatewayStatus = "maintenance"
)

// DeviceTemplate represents a hardware device template
type DeviceTemplate struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Type         string                 `json:"type"`
	Platform     string                 `json:"platform"` // esp32, rp2040, etc.
	Version      string                 `json:"version"`
	Description  string                 `json:"description"`
	Capabilities []string               `json:"capabilities"`
	Config       map[string]interface{} `json:"config"`
	Firmware     *FirmwareInfo          `json:"firmware"`
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
}

// FirmwareInfo represents firmware information for a device template
type FirmwareInfo struct {
	Version       string    `json:"version"`
	Size          int64     `json:"size"`
	Checksum      string    `json:"checksum"`
	URL           string    `json:"url"`
	CompiledAt    time.Time `json:"compiled_at"`
	Features      []string  `json:"features"`
	Compatibility []string  `json:"compatibility"`
}

// PlatformMetrics tracks platform performance metrics
type PlatformMetrics struct {
	TotalDevices     int64         `json:"total_devices"`
	OnlineDevices    int64         `json:"online_devices"`
	TotalGateways    int64         `json:"total_gateways"`
	OnlineGateways   int64         `json:"online_gateways"`
	MessagesSent     int64         `json:"messages_sent"`
	MessagesReceived int64         `json:"messages_received"`
	Errors           int64         `json:"errors"`
	Uptime           time.Duration `json:"uptime"`
}

// NewPlatform creates a new hardware platform manager
func NewPlatform() *Platform {
	return &Platform{
		devices:       make(map[string]*devices.Device),
		protocols:     make(map[string]protocols.Protocol),
		gateways:      make(map[string]*Gateway),
		certification: certification.NewCertificationManager(),
		metrics:       &PlatformMetrics{},
	}
}

// RegisterDevice registers a new device with the platform
func (p *Platform) RegisterDevice(ctx context.Context, device *devices.Device) error {
	if device == nil {
		return fmt.Errorf("device cannot be nil")
	}

	if device.ID == "" {
		return fmt.Errorf("device ID cannot be empty")
	}

	// Validate device configuration
	if err := p.validateDevice(device); err != nil {
		return fmt.Errorf("device validation failed: %w", err)
	}

	// Register device
	p.devices[device.ID] = device
	p.metrics.TotalDevices++

	logger.Info("Device registered: %s (%s)", device.ID, device.Name)
	return nil
}

// UnregisterDevice removes a device from the platform
func (p *Platform) UnregisterDevice(ctx context.Context, deviceID string) error {
	device, exists := p.devices[deviceID]
	if !exists {
		return fmt.Errorf("device %s not found", deviceID)
	}

	// Remove from associated gateway
	if device.GatewayID != "" {
		if gateway, exists := p.gateways[device.GatewayID]; exists {
			p.removeDeviceFromGateway(gateway, deviceID)
		}
	}

	delete(p.devices, deviceID)
	p.metrics.TotalDevices--

	logger.Info("Device unregistered: %s", deviceID)
	return nil
}

// RegisterGateway registers a new gateway with the platform
func (p *Platform) RegisterGateway(ctx context.Context, gateway *Gateway) error {
	if gateway == nil {
		return fmt.Errorf("gateway cannot be nil")
	}

	if gateway.ID == "" {
		return fmt.Errorf("gateway ID cannot be empty")
	}

	// Validate gateway configuration
	if err := p.validateGateway(gateway); err != nil {
		return fmt.Errorf("gateway validation failed: %w", err)
	}

	// Set timestamps
	now := time.Now()
	if gateway.CreatedAt.IsZero() {
		gateway.CreatedAt = now
	}
	gateway.UpdatedAt = now
	gateway.LastSeen = now

	// Register gateway
	p.gateways[gateway.ID] = gateway
	p.metrics.TotalGateways++

	logger.Info("Gateway registered: %s (%s)", gateway.ID, gateway.Name)
	return nil
}

// GetDevice retrieves a device by ID
func (p *Platform) GetDevice(deviceID string) (*devices.Device, error) {
	device, exists := p.devices[deviceID]
	if !exists {
		return nil, fmt.Errorf("device %s not found", deviceID)
	}
	return device, nil
}

// GetGateway retrieves a gateway by ID
func (p *Platform) GetGateway(gatewayID string) (*Gateway, error) {
	gateway, exists := p.gateways[gatewayID]
	if !exists {
		return nil, fmt.Errorf("gateway %s not found", gatewayID)
	}
	return gateway, nil
}

// ListDevices returns all registered devices
func (p *Platform) ListDevices() []*devices.Device {
	devices := make([]*devices.Device, 0, len(p.devices))
	for _, device := range p.devices {
		devices = append(devices, device)
	}
	return devices
}

// ListGateways returns all registered gateways
func (p *Platform) ListGateways() []*Gateway {
	gateways := make([]*Gateway, 0, len(p.gateways))
	for _, gateway := range p.gateways {
		gateways = append(gateways, gateway)
	}
	return gateways
}

// UpdateDeviceStatus updates the status of a device
func (p *Platform) UpdateDeviceStatus(ctx context.Context, deviceID string, status devices.DeviceStatus) error {
	device, exists := p.devices[deviceID]
	if !exists {
		return fmt.Errorf("device %s not found", deviceID)
	}

	device.Status = status
	device.LastSeen = time.Now()

	// Update metrics
	if status == devices.DeviceStatusOnline {
		p.metrics.OnlineDevices++
	} else if device.Status == devices.DeviceStatusOnline {
		p.metrics.OnlineDevices--
	}

	logger.Debug("Device status updated: %s -> %s", deviceID, status)
	return nil
}

// UpdateGatewayStatus updates the status of a gateway
func (p *Platform) UpdateGatewayStatus(ctx context.Context, gatewayID string, status GatewayStatus) error {
	gateway, exists := p.gateways[gatewayID]
	if !exists {
		return fmt.Errorf("gateway %s not found", gatewayID)
	}

	gateway.Status = status
	gateway.LastSeen = time.Now()

	// Update metrics
	if status == GatewayStatusOnline {
		p.metrics.OnlineGateways++
	} else if gateway.Status == GatewayStatusOnline {
		p.metrics.OnlineGateways--
	}

	logger.Debug("Gateway status updated: %s -> %s", gatewayID, status)
	return nil
}

// SendMessage sends a message to a device
func (p *Platform) SendMessage(ctx context.Context, deviceID string, message interface{}) error {
	device, exists := p.devices[deviceID]
	if !exists {
		return fmt.Errorf("device %s not found", deviceID)
	}

	// Find the gateway for this device
	gateway, exists := p.gateways[device.GatewayID]
	if !exists {
		return fmt.Errorf("gateway %s not found for device %s", device.GatewayID, deviceID)
	}

	// Send message through gateway
	if err := p.sendMessageThroughGateway(ctx, gateway, device, message); err != nil {
		p.metrics.Errors++
		return fmt.Errorf("failed to send message: %w", err)
	}

	p.metrics.MessagesSent++
	logger.Debug("Message sent to device %s through gateway %s", deviceID, gateway.ID)
	return nil
}

// GetMetrics returns platform metrics
func (p *Platform) GetMetrics() *PlatformMetrics {
	return p.metrics
}

// validateDevice validates a device configuration
func (p *Platform) validateDevice(device *devices.Device) error {
	if device.Name == "" {
		return fmt.Errorf("device name cannot be empty")
	}

	if device.Type == "" {
		return fmt.Errorf("device type cannot be empty")
	}

	if device.GatewayID != "" {
		if _, exists := p.gateways[device.GatewayID]; !exists {
			return fmt.Errorf("gateway %s not found", device.GatewayID)
		}
	}

	return nil
}

// validateGateway validates a gateway configuration
func (p *Platform) validateGateway(gateway *Gateway) error {
	if gateway.Name == "" {
		return fmt.Errorf("gateway name cannot be empty")
	}

	if gateway.Type == "" {
		return fmt.Errorf("gateway type cannot be empty")
	}

	if len(gateway.Protocols) == 0 {
		return fmt.Errorf("gateway must support at least one protocol")
	}

	return nil
}

// removeDeviceFromGateway removes a device from a gateway's device list
func (p *Platform) removeDeviceFromGateway(gateway *Gateway, deviceID string) {
	for i, id := range gateway.Devices {
		if id == deviceID {
			gateway.Devices = append(gateway.Devices[:i], gateway.Devices[i+1:]...)
			break
		}
	}
}

// sendMessageThroughGateway sends a message through a gateway
func (p *Platform) sendMessageThroughGateway(ctx context.Context, gateway *Gateway, device *devices.Device, message interface{}) error {
	// This would integrate with the actual protocol implementation
	// For now, we'll just log the message
	messageData, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	logger.Debug("Sending message to device %s via gateway %s: %s",
		device.ID, gateway.ID, string(messageData))

	return nil
}
