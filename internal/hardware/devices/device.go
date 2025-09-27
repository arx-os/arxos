package devices

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Device represents a hardware device in the ArxOS ecosystem
type Device struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Type         DeviceType             `json:"type"`
	Platform     string                 `json:"platform"` // esp32, rp2040, etc.
	GatewayID    string                 `json:"gateway_id"`
	Location     string                 `json:"location"` // Building path
	Status       DeviceStatus           `json:"status"`
	Capabilities []string               `json:"capabilities"`
	Config       map[string]interface{} `json:"config"`
	Firmware     *FirmwareInfo          `json:"firmware"`
	LastSeen     time.Time              `json:"last_seen"`
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
}

// DeviceType represents the type of hardware device
type DeviceType string

const (
	DeviceTypeSensor     DeviceType = "sensor"
	DeviceTypeActuator   DeviceType = "actuator"
	DeviceTypeGateway    DeviceType = "gateway"
	DeviceTypeController DeviceType = "controller"
	DeviceTypeDisplay    DeviceType = "display"
	DeviceTypeCamera     DeviceType = "camera"
	DeviceTypeSpeaker    DeviceType = "speaker"
	DeviceTypeLight      DeviceType = "light"
	DeviceTypeThermostat DeviceType = "thermostat"
	DeviceTypeSwitch     DeviceType = "switch"
	DeviceTypeOutlet     DeviceType = "outlet"
	DeviceTypePanel      DeviceType = "panel"
)

// DeviceStatus represents the operational status of a device
type DeviceStatus string

const (
	DeviceStatusOnline      DeviceStatus = "online"
	DeviceStatusOffline     DeviceStatus = "offline"
	DeviceStatusError       DeviceStatus = "error"
	DeviceStatusUpdating    DeviceStatus = "updating"
	DeviceStatusMaintenance DeviceStatus = "maintenance"
	DeviceStatusSleeping    DeviceStatus = "sleeping"
	DeviceStatusUnknown     DeviceStatus = "unknown"
)

// FirmwareInfo represents firmware information for a device
type FirmwareInfo struct {
	Version       string    `json:"version"`
	BuildDate     time.Time `json:"build_date"`
	Size          int64     `json:"size"`
	Checksum      string    `json:"checksum"`
	Features      []string  `json:"features"`
	Compatibility []string  `json:"compatibility"`
}

// DeviceMessage represents a message from or to a device
type DeviceMessage struct {
	ID        string                 `json:"id"`
	DeviceID  string                 `json:"device_id"`
	Type      MessageType            `json:"type"`
	Payload   map[string]interface{} `json:"payload"`
	Timestamp time.Time              `json:"timestamp"`
	Priority  MessagePriority        `json:"priority"`
}

// MessageType represents the type of device message
type MessageType string

const (
	MessageTypeData      MessageType = "data"
	MessageTypeCommand   MessageType = "command"
	MessageTypeStatus    MessageType = "status"
	MessageTypeError     MessageType = "error"
	MessageTypeHeartbeat MessageType = "heartbeat"
	MessageTypeConfig    MessageType = "config"
	MessageTypeUpdate    MessageType = "update"
)

// MessagePriority represents the priority of a device message
type MessagePriority string

const (
	MessagePriorityLow      MessagePriority = "low"
	MessagePriorityNormal   MessagePriority = "normal"
	MessagePriorityHigh     MessagePriority = "high"
	MessagePriorityCritical MessagePriority = "critical"
)

// DeviceCapability represents a capability of a device
type DeviceCapability struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Description string                 `json:"description"`
	Parameters  map[string]interface{} `json:"parameters"`
	ReadOnly    bool                   `json:"read_only"`
}

// DeviceManager manages hardware devices
type DeviceManager struct {
	devices map[string]*Device
	metrics *DeviceMetrics
}

// DeviceMetrics tracks device performance metrics
type DeviceMetrics struct {
	TotalDevices     int64 `json:"total_devices"`
	OnlineDevices    int64 `json:"online_devices"`
	OfflineDevices   int64 `json:"offline_devices"`
	ErrorDevices     int64 `json:"error_devices"`
	MessagesReceived int64 `json:"messages_received"`
	MessagesSent     int64 `json:"messages_sent"`
	Errors           int64 `json:"errors"`
}

// NewDeviceManager creates a new device manager
func NewDeviceManager() *DeviceManager {
	return &DeviceManager{
		devices: make(map[string]*Device),
		metrics: &DeviceMetrics{},
	}
}

// CreateDevice creates a new device
func (dm *DeviceManager) CreateDevice(ctx context.Context, device *Device) error {
	if device == nil {
		return fmt.Errorf("device cannot be nil")
	}

	if device.ID == "" {
		return fmt.Errorf("device ID cannot be empty")
	}

	// Validate device
	if err := dm.validateDevice(device); err != nil {
		return fmt.Errorf("device validation failed: %w", err)
	}

	// Set timestamps
	now := time.Now()
	device.CreatedAt = now
	device.UpdatedAt = now
	device.LastSeen = now

	// Set default status if not set
	if device.Status == "" {
		device.Status = DeviceStatusOffline
	}

	// Register device
	dm.devices[device.ID] = device
	dm.metrics.TotalDevices++

	logger.Info("Device created: %s (%s)", device.ID, device.Name)
	return nil
}

// GetDevice retrieves a device by ID
func (dm *DeviceManager) GetDevice(deviceID string) (*Device, error) {
	device, exists := dm.devices[deviceID]
	if !exists {
		return nil, fmt.Errorf("device %s not found", deviceID)
	}
	return device, nil
}

// UpdateDevice updates an existing device
func (dm *DeviceManager) UpdateDevice(ctx context.Context, deviceID string, updates map[string]interface{}) error {
	device, exists := dm.devices[deviceID]
	if !exists {
		return fmt.Errorf("device %s not found", deviceID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "name":
			if name, ok := value.(string); ok {
				device.Name = name
			}
		case "location":
			if location, ok := value.(string); ok {
				device.Location = location
			}
		case "config":
			if config, ok := value.(map[string]interface{}); ok {
				device.Config = config
			}
		case "capabilities":
			if capabilities, ok := value.([]string); ok {
				device.Capabilities = capabilities
			}
		}
	}

	device.UpdatedAt = time.Now()

	logger.Debug("Device updated: %s", deviceID)
	return nil
}

// DeleteDevice removes a device
func (dm *DeviceManager) DeleteDevice(ctx context.Context, deviceID string) error {
	device, exists := dm.devices[deviceID]
	if !exists {
		return fmt.Errorf("device %s not found", deviceID)
	}

	delete(dm.devices, deviceID)
	dm.metrics.TotalDevices--

	logger.Info("Device deleted: %s (%s)", deviceID, device.Name)
	return nil
}

// ListDevices returns all devices
func (dm *DeviceManager) ListDevices() []*Device {
	devices := make([]*Device, 0, len(dm.devices))
	for _, device := range dm.devices {
		devices = append(devices, device)
	}
	return devices
}

// ListDevicesByType returns devices filtered by type
func (dm *DeviceManager) ListDevicesByType(deviceType DeviceType) []*Device {
	var devices []*Device
	for _, device := range dm.devices {
		if device.Type == deviceType {
			devices = append(devices, device)
		}
	}
	return devices
}

// ListDevicesByGateway returns devices for a specific gateway
func (dm *DeviceManager) ListDevicesByGateway(gatewayID string) []*Device {
	var devices []*Device
	for _, device := range dm.devices {
		if device.GatewayID == gatewayID {
			devices = append(devices, device)
		}
	}
	return devices
}

// UpdateDeviceStatus updates the status of a device
func (dm *DeviceManager) UpdateDeviceStatus(ctx context.Context, deviceID string, status DeviceStatus) error {
	device, exists := dm.devices[deviceID]
	if !exists {
		return fmt.Errorf("device %s not found", deviceID)
	}

	oldStatus := device.Status
	device.Status = status
	device.LastSeen = time.Now()
	device.UpdatedAt = time.Now()

	// Update metrics
	dm.updateStatusMetrics(oldStatus, status)

	logger.Debug("Device status updated: %s -> %s", deviceID, status)
	return nil
}

// SendCommand sends a command to a device
func (dm *DeviceManager) SendCommand(ctx context.Context, deviceID string, command map[string]interface{}) error {
	device, exists := dm.devices[deviceID]
	if !exists {
		return fmt.Errorf("device %s not found", deviceID)
	}

	if device.Status != DeviceStatusOnline {
		return fmt.Errorf("device %s is not online (status: %s)", deviceID, device.Status)
	}

	// Create command message
	message := &DeviceMessage{
		ID:        fmt.Sprintf("cmd_%d", time.Now().UnixNano()),
		DeviceID:  deviceID,
		Type:      MessageTypeCommand,
		Payload:   command,
		Timestamp: time.Now(),
		Priority:  MessagePriorityNormal,
	}

	// Send command (this would integrate with the actual communication layer)
	if err := dm.sendMessage(device, message); err != nil {
		dm.metrics.Errors++
		return fmt.Errorf("failed to send command: %w", err)
	}

	dm.metrics.MessagesSent++
	logger.Debug("Command sent to device %s: %v", deviceID, command)
	return nil
}

// ProcessMessage processes a message from a device
func (dm *DeviceManager) ProcessMessage(ctx context.Context, message *DeviceMessage) error {
	if message == nil {
		return fmt.Errorf("message cannot be nil")
	}

	device, exists := dm.devices[message.DeviceID]
	if !exists {
		return fmt.Errorf("device %s not found", message.DeviceID)
	}

	// Update device last seen
	device.LastSeen = time.Now()

	// Process message based on type
	switch message.Type {
	case MessageTypeData:
		return dm.processDataMessage(device, message)
	case MessageTypeStatus:
		return dm.processStatusMessage(device, message)
	case MessageTypeError:
		return dm.processErrorMessage(device, message)
	case MessageTypeHeartbeat:
		return dm.processHeartbeatMessage(device, message)
	default:
		logger.Warn("Unknown message type: %s", message.Type)
	}

	dm.metrics.MessagesReceived++
	return nil
}

// GetMetrics returns device metrics
func (dm *DeviceManager) GetMetrics() *DeviceMetrics {
	return dm.metrics
}

// validateDevice validates a device configuration
func (dm *DeviceManager) validateDevice(device *Device) error {
	if device.Name == "" {
		return fmt.Errorf("device name cannot be empty")
	}

	if device.Type == "" {
		return fmt.Errorf("device type cannot be empty")
	}

	if device.Platform == "" {
		return fmt.Errorf("device platform cannot be empty")
	}

	return nil
}

// updateStatusMetrics updates metrics based on status changes
func (dm *DeviceManager) updateStatusMetrics(oldStatus, newStatus DeviceStatus) {
	// Decrement old status
	switch oldStatus {
	case DeviceStatusOnline:
		dm.metrics.OnlineDevices--
	case DeviceStatusOffline:
		dm.metrics.OfflineDevices--
	case DeviceStatusError:
		dm.metrics.ErrorDevices--
	}

	// Increment new status
	switch newStatus {
	case DeviceStatusOnline:
		dm.metrics.OnlineDevices++
	case DeviceStatusOffline:
		dm.metrics.OfflineDevices++
	case DeviceStatusError:
		dm.metrics.ErrorDevices++
	}
}

// sendMessage sends a message to a device
func (dm *DeviceManager) sendMessage(device *Device, message *DeviceMessage) error {
	// This would integrate with the actual communication layer
	// For now, we'll just log the message
	messageData, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	logger.Debug("Sending message to device %s: %s", device.ID, string(messageData))
	return nil
}

// processDataMessage processes a data message from a device
func (dm *DeviceManager) processDataMessage(device *Device, message *DeviceMessage) error {
	logger.Debug("Processing data message from device %s: %v", device.ID, message.Payload)
	// Process sensor data, telemetry, etc.
	return nil
}

// processStatusMessage processes a status message from a device
func (dm *DeviceManager) processStatusMessage(device *Device, message *DeviceMessage) error {
	if status, ok := message.Payload["status"].(string); ok {
		if err := dm.UpdateDeviceStatus(context.Background(), device.ID, DeviceStatus(status)); err != nil {
			return fmt.Errorf("failed to update device status: %w", err)
		}
	}
	return nil
}

// processErrorMessage processes an error message from a device
func (dm *DeviceManager) processErrorMessage(device *Device, message *DeviceMessage) error {
	logger.Warn("Error message from device %s: %v", device.ID, message.Payload)
	dm.metrics.Errors++
	return nil
}

// processHeartbeatMessage processes a heartbeat message from a device
func (dm *DeviceManager) processHeartbeatMessage(device *Device, message *DeviceMessage) error {
	logger.Debug("Heartbeat from device %s", device.ID)
	// Update device status to online if it was offline
	if device.Status == DeviceStatusOffline {
		dm.UpdateDeviceStatus(context.Background(), device.ID, DeviceStatusOnline)
	}
	return nil
}
