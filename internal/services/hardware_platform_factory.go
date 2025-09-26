package services

import (
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/hardware"
)

// HardwarePlatformFactory creates and configures the hardware platform
type HardwarePlatformFactory struct {
	db *database.PostGISDB
}

// NewHardwarePlatformFactory creates a new hardware platform factory
func NewHardwarePlatformFactory(db *database.PostGISDB) *HardwarePlatformFactory {
	return &HardwarePlatformFactory{
		db: db,
	}
}

// CreatePlatform creates a fully configured hardware platform instance
func (hpf *HardwarePlatformFactory) CreatePlatform() *hardware.Platform {
	// Create service implementations
	deviceService := NewHardwareService(hpf.db)
	templateService := NewTemplateService(hpf.db)
	gatewayService := NewGatewayService(hpf.db)
	marketplaceService := NewMarketplaceService(hpf.db)

	// Create hardware platform
	return hardware.NewPlatform(
		deviceService,
		templateService,
		gatewayService,
		marketplaceService,
	)
}

// CreatePlatformFactory creates a platform factory using the hardware package's factory
func (hpf *HardwarePlatformFactory) CreatePlatformFactory() *hardware.PlatformFactory {
	// Create service implementations
	deviceService := NewHardwareService(hpf.db)
	templateService := NewTemplateService(hpf.db)
	gatewayService := NewGatewayService(hpf.db)
	marketplaceService := NewMarketplaceService(hpf.db)

	// Create hardware platform factory
	return hardware.NewPlatformFactory(
		deviceService,
		templateService,
		gatewayService,
		marketplaceService,
	)
}
