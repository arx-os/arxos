package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/hardware"
)

// HardwareService implements the hardware tier business logic (Layer 2 - FREEMIUM)
type HardwareService struct {
	db *database.PostGISDB
}

// NewHardwareService creates a new HardwareService
func NewHardwareService(db *database.PostGISDB) *HardwareService {
	return &HardwareService{db: db}
}

// Device Management

// RegisterDevice registers a new device in the hardware platform
func (hs *HardwareService) RegisterDevice(ctx context.Context, req hardware.RegisterDeviceRequest) (*hardware.Device, error) {
	// Validate request
	if req.Name == "" {
		return nil, fmt.Errorf("device name is required")
	}
	if req.Type == "" {
		return nil, fmt.Errorf("device type is required")
	}
	if req.TemplateID == "" {
		return nil, fmt.Errorf("template ID is required")
	}

	// Validate template exists
	var templateExists bool
	err := hs.db.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM device_templates WHERE id = $1)", req.TemplateID).Scan(&templateExists)
	if err != nil {
		return nil, fmt.Errorf("failed to validate template: %w", err)
	}
	if !templateExists {
		return nil, fmt.Errorf("device template not found: %s", req.TemplateID)
	}

	// Create device
	query := `
		INSERT INTO hardware_devices (id, name, type, template_id, status, config, firmware, location, user_id, tier, created_at, updated_at)
		VALUES ($1, $2, $3, $4, 'active', $5, $6, $7, $8, 'hardware', NOW(), NOW())
		RETURNING id, name, type, template_id, status, config, firmware, location, user_id, created_at, updated_at`

	var device hardware.Device
	deviceID := generateDeviceID()

	var configJSON, firmwareJSON, locationJSON []byte
	err = hs.db.QueryRow(ctx, query,
		deviceID,
		req.Name,
		req.Type,
		req.TemplateID,
		req.Config,
		json.RawMessage("{}"), // Default firmware
		req.Location,
		"default_user", // TODO: Get from context
	).Scan(
		&device.ID,
		&device.Name,
		&device.Type,
		&device.TemplateID,
		&device.Status,
		&configJSON,
		&firmwareJSON,
		&locationJSON,
		&device.UserID,
		&device.CreatedAt,
		&device.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to register device: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(configJSON, &device.Config); err != nil {
		device.Config = make(map[string]interface{})
	}
	if err := json.Unmarshal(firmwareJSON, &device.Firmware); err != nil {
		device.Firmware = hardware.FirmwareInfo{}
	}
	if err := json.Unmarshal(locationJSON, &device.Location); err != nil {
		device.Location = hardware.DeviceLocation{}
	}

	return &device, nil
}

// GetDevice retrieves a device by ID
func (hs *HardwareService) GetDevice(ctx context.Context, deviceID string) (*hardware.Device, error) {
	query := `
		SELECT id, name, type, template_id, status, config, firmware, location, user_id, created_at, updated_at
		FROM hardware_devices
		WHERE id = $1 AND tier = 'hardware'
	`

	var device hardware.Device
	var configJSON, firmwareJSON, locationJSON []byte
	err := hs.db.QueryRow(ctx, query, deviceID).Scan(
		&device.ID,
		&device.Name,
		&device.Type,
		&device.TemplateID,
		&device.Status,
		&configJSON,
		&firmwareJSON,
		&locationJSON,
		&device.UserID,
		&device.CreatedAt,
		&device.UpdatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("device not found")
		}
		return nil, fmt.Errorf("failed to get device: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(configJSON, &device.Config); err != nil {
		device.Config = make(map[string]interface{})
	}
	if err := json.Unmarshal(firmwareJSON, &device.Firmware); err != nil {
		device.Firmware = hardware.FirmwareInfo{}
	}
	if err := json.Unmarshal(locationJSON, &device.Location); err != nil {
		device.Location = hardware.DeviceLocation{}
	}

	return &device, nil
}

// ListDevices lists devices for a user
func (hs *HardwareService) ListDevices(ctx context.Context, userID string) ([]*hardware.Device, error) {
	query := `
		SELECT id, name, type, template_id, status, config, firmware, location, user_id, created_at, updated_at
		FROM hardware_devices
		WHERE tier = 'hardware'
		ORDER BY created_at DESC
	`

	rows, err := hs.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to list devices: %w", err)
	}
	defer rows.Close()

	var devices []*hardware.Device
	for rows.Next() {
		var device hardware.Device
		var configJSON, firmwareJSON, locationJSON []byte
		err := rows.Scan(
			&device.ID,
			&device.Name,
			&device.Type,
			&device.TemplateID,
			&device.Status,
			&configJSON,
			&firmwareJSON,
			&locationJSON,
			&device.UserID,
			&device.CreatedAt,
			&device.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan device: %w", err)
		}

		// Parse JSON fields
		if err := json.Unmarshal(configJSON, &device.Config); err != nil {
			device.Config = make(map[string]interface{})
		}
		if err := json.Unmarshal(firmwareJSON, &device.Firmware); err != nil {
			device.Firmware = hardware.FirmwareInfo{}
		}
		if err := json.Unmarshal(locationJSON, &device.Location); err != nil {
			device.Location = hardware.DeviceLocation{}
		}

		devices = append(devices, &device)
	}

	return devices, nil
}

// UpdateDevice updates device information
func (hs *HardwareService) UpdateDevice(ctx context.Context, deviceID string, updates hardware.DeviceUpdates) (*hardware.Device, error) {
	// Get existing device
	device, err := hs.GetDevice(ctx, deviceID)
	if err != nil {
		return nil, fmt.Errorf("failed to get existing device: %w", err)
	}

	// Update fields
	if updates.Name != nil {
		device.Name = *updates.Name
	}
	if updates.Status != nil {
		device.Status = *updates.Status
	}
	if updates.Config != nil {
		device.Config = updates.Config
	}
	if updates.Location != nil {
		device.Location = *updates.Location
	}

	// Update in database
	query := `
		UPDATE hardware_devices 
		SET name = $1, status = $2, config = $3, location = $4, updated_at = NOW()
		WHERE id = $5 AND tier = 'hardware'
	`

	_, err = hs.db.Exec(ctx, query,
		device.Name,
		device.Status,
		device.Config,
		device.Location,
		deviceID,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to update device: %w", err)
	}

	return device, nil
}

// DeleteDevice removes a device
func (hs *HardwareService) DeleteDevice(ctx context.Context, deviceID string) error {
	_, err := hs.db.Exec(ctx, "DELETE FROM hardware_devices WHERE id = $1 AND tier = 'hardware'", deviceID)
	if err != nil {
		return fmt.Errorf("failed to delete device: %w", err)
	}
	return nil
}

// UpdateDeviceFirmware updates device firmware
func (hs *HardwareService) UpdateDeviceFirmware(ctx context.Context, deviceID string, firmware []byte) error {
	// Validate device exists
	_, err := hs.GetDevice(ctx, deviceID)
	if err != nil {
		return fmt.Errorf("device not found: %w", err)
	}

	// Create firmware info
	firmwareInfo := hardware.FirmwareInfo{
		Version:    "1.0.0",
		Build:      fmt.Sprintf("build_%d", time.Now().Unix()),
		Checksum:   fmt.Sprintf("%x", firmware),
		Size:       int64(len(firmware)),
		ReleasedAt: time.Now(),
		Compatible: true,
	}

	// Update firmware in database
	query := `
		UPDATE hardware_devices 
		SET firmware = $1, updated_at = NOW()
		WHERE id = $2 AND tier = 'hardware'
	`

	_, err = hs.db.Exec(ctx, query, firmwareInfo, deviceID)
	if err != nil {
		return fmt.Errorf("failed to update device firmware: %w", err)
	}

	return nil
}

// GetDeviceStatus retrieves device status information
func (hs *HardwareService) GetDeviceStatus(ctx context.Context, deviceID string) (*hardware.DeviceStatus, error) {
	// Validate device exists
	device, err := hs.GetDevice(ctx, deviceID)
	if err != nil {
		return nil, fmt.Errorf("device not found: %w", err)
	}

	// Create device status
	status := &hardware.DeviceStatus{
		DeviceID:    device.ID,
		Status:      device.Status,
		LastSeen:    time.Now(),
		Health:      "healthy",
		Metrics:     make(map[string]interface{}),
		Errors:      []string{},
		LastUpdated: time.Now(),
	}

	// Add some sample metrics
	status.Metrics["uptime"] = "24h"
	status.Metrics["temperature"] = 25.5
	status.Metrics["humidity"] = 60.0
	status.Metrics["signal_strength"] = -45

	return status, nil
}

// Helper functions

func generateDeviceID() string {
	return fmt.Sprintf("dev_%d", time.Now().UnixNano())
}
