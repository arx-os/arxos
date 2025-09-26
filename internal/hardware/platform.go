package hardware

import (
	"context"
	"time"
)

// Platform manages the hardware ecosystem (Layer 2 - FREEMIUM)
type Platform struct {
	deviceManager      DeviceManager
	templateManager    TemplateManager
	gatewayManager     GatewayManager
	marketplaceManager MarketplaceManager
}

// DeviceManager handles device lifecycle and management
type DeviceManager interface {
	RegisterDevice(ctx context.Context, req RegisterDeviceRequest) (*Device, error)
	ListDevices(ctx context.Context, userID string) ([]*Device, error)
	GetDevice(ctx context.Context, deviceID string) (*Device, error)
	UpdateDevice(ctx context.Context, deviceID string, updates DeviceUpdates) (*Device, error)
	DeleteDevice(ctx context.Context, deviceID string) error
	UpdateDeviceFirmware(ctx context.Context, deviceID string, firmware []byte) error
	GetDeviceStatus(ctx context.Context, deviceID string) (*DeviceStatus, error)
}

// TemplateManager handles device templates and SDK
type TemplateManager interface {
	GetTemplates(ctx context.Context) ([]*DeviceTemplate, error)
	GetTemplate(ctx context.Context, templateID string) (*DeviceTemplate, error)
	CreateTemplate(ctx context.Context, req CreateTemplateRequest) (*DeviceTemplate, error)
	CreateDeviceFromTemplate(ctx context.Context, templateID string, userID string) (*Device, error)
	ValidateTemplate(ctx context.Context, template *DeviceTemplate) error
}

// GatewayManager handles gateway deployment and management
type GatewayManager interface {
	DeployGateway(ctx context.Context, req DeployGatewayRequest) (*Gateway, error)
	ListGateways(ctx context.Context, userID string) ([]*Gateway, error)
	GetGateway(ctx context.Context, gatewayID string) (*Gateway, error)
	UpdateGateway(ctx context.Context, gatewayID string, config GatewayConfig) (*Gateway, error)
	DeleteGateway(ctx context.Context, gatewayID string) error
	ConfigureGateway(ctx context.Context, gatewayID string, config GatewayConfig) error
	GetGatewayStatus(ctx context.Context, gatewayID string) (*GatewayStatus, error)
}

// MarketplaceManager handles certified device marketplace
type MarketplaceManager interface {
	ListCertifiedDevices(ctx context.Context) ([]*CertifiedDevice, error)
	GetCertifiedDevice(ctx context.Context, deviceID string) (*CertifiedDevice, error)
	PurchaseDevice(ctx context.Context, req PurchaseDeviceRequest) (*PurchaseResult, error)
	ListOrders(ctx context.Context, userID string) ([]*Order, error)
	GetOrder(ctx context.Context, orderID string) (*Order, error)
	CancelOrder(ctx context.Context, orderID string) error
}

// NewPlatform creates a new hardware platform
func NewPlatform(
	deviceManager DeviceManager,
	templateManager TemplateManager,
	gatewayManager GatewayManager,
	marketplaceManager MarketplaceManager,
) *Platform {
	return &Platform{
		deviceManager:      deviceManager,
		templateManager:    templateManager,
		gatewayManager:     gatewayManager,
		marketplaceManager: marketplaceManager,
	}
}

// Device management methods
func (p *Platform) RegisterDevice(ctx context.Context, req RegisterDeviceRequest) (*Device, error) {
	return p.deviceManager.RegisterDevice(ctx, req)
}

func (p *Platform) ListDevices(ctx context.Context, userID string) ([]*Device, error) {
	return p.deviceManager.ListDevices(ctx, userID)
}

func (p *Platform) GetDevice(ctx context.Context, deviceID string) (*Device, error) {
	return p.deviceManager.GetDevice(ctx, deviceID)
}

func (p *Platform) UpdateDevice(ctx context.Context, deviceID string, updates DeviceUpdates) (*Device, error) {
	return p.deviceManager.UpdateDevice(ctx, deviceID, updates)
}

func (p *Platform) DeleteDevice(ctx context.Context, deviceID string) error {
	return p.deviceManager.DeleteDevice(ctx, deviceID)
}

func (p *Platform) UpdateDeviceFirmware(ctx context.Context, deviceID string, firmware []byte) error {
	return p.deviceManager.UpdateDeviceFirmware(ctx, deviceID, firmware)
}

func (p *Platform) GetDeviceStatus(ctx context.Context, deviceID string) (*DeviceStatus, error) {
	return p.deviceManager.GetDeviceStatus(ctx, deviceID)
}

// Template management methods
func (p *Platform) GetTemplates(ctx context.Context) ([]*DeviceTemplate, error) {
	return p.templateManager.GetTemplates(ctx)
}

func (p *Platform) GetTemplate(ctx context.Context, templateID string) (*DeviceTemplate, error) {
	return p.templateManager.GetTemplate(ctx, templateID)
}

func (p *Platform) CreateTemplate(ctx context.Context, req CreateTemplateRequest) (*DeviceTemplate, error) {
	return p.templateManager.CreateTemplate(ctx, req)
}

func (p *Platform) CreateDeviceFromTemplate(ctx context.Context, templateID string, userID string) (*Device, error) {
	return p.templateManager.CreateDeviceFromTemplate(ctx, templateID, userID)
}

func (p *Platform) ValidateTemplate(ctx context.Context, template *DeviceTemplate) error {
	return p.templateManager.ValidateTemplate(ctx, template)
}

// Gateway management methods
func (p *Platform) DeployGateway(ctx context.Context, req DeployGatewayRequest) (*Gateway, error) {
	return p.gatewayManager.DeployGateway(ctx, req)
}

func (p *Platform) ListGateways(ctx context.Context, userID string) ([]*Gateway, error) {
	return p.gatewayManager.ListGateways(ctx, userID)
}

func (p *Platform) GetGateway(ctx context.Context, gatewayID string) (*Gateway, error) {
	return p.gatewayManager.GetGateway(ctx, gatewayID)
}

func (p *Platform) UpdateGateway(ctx context.Context, gatewayID string, config GatewayConfig) (*Gateway, error) {
	return p.gatewayManager.UpdateGateway(ctx, gatewayID, config)
}

func (p *Platform) DeleteGateway(ctx context.Context, gatewayID string) error {
	return p.gatewayManager.DeleteGateway(ctx, gatewayID)
}

func (p *Platform) ConfigureGateway(ctx context.Context, gatewayID string, config GatewayConfig) error {
	return p.gatewayManager.ConfigureGateway(ctx, gatewayID, config)
}

func (p *Platform) GetGatewayStatus(ctx context.Context, gatewayID string) (*GatewayStatus, error) {
	return p.gatewayManager.GetGatewayStatus(ctx, gatewayID)
}

// Marketplace methods
func (p *Platform) ListCertifiedDevices(ctx context.Context) ([]*CertifiedDevice, error) {
	return p.marketplaceManager.ListCertifiedDevices(ctx)
}

func (p *Platform) GetCertifiedDevice(ctx context.Context, deviceID string) (*CertifiedDevice, error) {
	return p.marketplaceManager.GetCertifiedDevice(ctx, deviceID)
}

func (p *Platform) PurchaseDevice(ctx context.Context, req PurchaseDeviceRequest) (*PurchaseResult, error) {
	return p.marketplaceManager.PurchaseDevice(ctx, req)
}

func (p *Platform) ListOrders(ctx context.Context, userID string) ([]*Order, error) {
	return p.marketplaceManager.ListOrders(ctx, userID)
}

func (p *Platform) GetOrder(ctx context.Context, orderID string) (*Order, error) {
	return p.marketplaceManager.GetOrder(ctx, orderID)
}

func (p *Platform) CancelOrder(ctx context.Context, orderID string) error {
	return p.marketplaceManager.CancelOrder(ctx, orderID)
}

// Data structures

type Device struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	TemplateID string                 `json:"template_id"`
	Status     string                 `json:"status"`
	Config     map[string]interface{} `json:"config"`
	Firmware   FirmwareInfo           `json:"firmware"`
	Location   DeviceLocation         `json:"location"`
	UserID     string                 `json:"user_id"`
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
}

type DeviceTemplate struct {
	ID            string                 `json:"id"`
	Name          string                 `json:"name"`
	Type          string                 `json:"type"`
	Description   string                 `json:"description"`
	Schema        map[string]interface{} `json:"schema"`
	Firmware      []byte                 `json:"firmware"`
	SDK           SDKInfo                `json:"sdk"`
	Certification CertificationInfo      `json:"certification"`
	CreatedAt     time.Time              `json:"created_at"`
	UpdatedAt     time.Time              `json:"updated_at"`
}

type Gateway struct {
	ID        string         `json:"id"`
	Name      string         `json:"name"`
	Type      string         `json:"type"`
	Status    string         `json:"status"`
	Config    GatewayConfig  `json:"config"`
	Devices   []string       `json:"devices"`
	Location  DeviceLocation `json:"location"`
	UserID    string         `json:"user_id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}

type CertifiedDevice struct {
	ID             string                 `json:"id"`
	Name           string                 `json:"name"`
	Type           string                 `json:"type"`
	Price          float64                `json:"price"`
	Certification  string                 `json:"certification"`
	Description    string                 `json:"description"`
	Features       []string               `json:"features"`
	Specifications map[string]interface{} `json:"specifications"`
	Availability   string                 `json:"availability"`
	CreatedAt      time.Time              `json:"created_at"`
}

type DeviceStatus struct {
	DeviceID    string                 `json:"device_id"`
	Status      string                 `json:"status"`
	LastSeen    time.Time              `json:"last_seen"`
	Health      string                 `json:"health"`
	Metrics     map[string]interface{} `json:"metrics"`
	Errors      []string               `json:"errors"`
	LastUpdated time.Time              `json:"last_updated"`
}

type GatewayStatus struct {
	GatewayID        string                 `json:"gateway_id"`
	Status           string                 `json:"status"`
	LastSeen         time.Time              `json:"last_seen"`
	ConnectedDevices int                    `json:"connected_devices"`
	Health           string                 `json:"health"`
	Metrics          map[string]interface{} `json:"metrics"`
	Errors           []string               `json:"errors"`
	LastUpdated      time.Time              `json:"last_updated"`
}

type FirmwareInfo struct {
	Version    string    `json:"version"`
	Build      string    `json:"build"`
	Checksum   string    `json:"checksum"`
	Size       int64     `json:"size"`
	ReleasedAt time.Time `json:"released_at"`
	Compatible bool      `json:"compatible"`
}

type SDKInfo struct {
	Version       string    `json:"version"`
	Language      string    `json:"language"`
	Documentation string    `json:"documentation"`
	Examples      []string  `json:"examples"`
	ReleasedAt    time.Time `json:"released_at"`
}

type CertificationInfo struct {
	Standard    string    `json:"standard"`
	Level       string    `json:"level"`
	CertifiedAt time.Time `json:"certified_at"`
	ExpiresAt   time.Time `json:"expires_at"`
	Certifier   string    `json:"certifier"`
}

type DeviceLocation struct {
	BuildingID string                 `json:"building_id"`
	Floor      string                 `json:"floor"`
	Room       string                 `json:"room"`
	Position   map[string]interface{} `json:"position"`
	Path       string                 `json:"path"`
}

type GatewayConfig struct {
	Protocols  []string               `json:"protocols"`
	Settings   map[string]interface{} `json:"settings"`
	Security   SecurityConfig         `json:"security"`
	Network    NetworkConfig          `json:"network"`
	Monitoring MonitoringConfig       `json:"monitoring"`
}

type SecurityConfig struct {
	Encryption     string                 `json:"encryption"`
	Authentication string                 `json:"authentication"`
	Certificates   []string               `json:"certificates"`
	AccessControl  map[string]interface{} `json:"access_control"`
}

type NetworkConfig struct {
	Protocol  string                 `json:"protocol"`
	Port      int                    `json:"port"`
	Bandwidth int                    `json:"bandwidth"`
	Latency   int                    `json:"latency"`
	Settings  map[string]interface{} `json:"settings"`
}

type MonitoringConfig struct {
	Enabled   bool          `json:"enabled"`
	Interval  int           `json:"interval"`
	Metrics   []string      `json:"metrics"`
	Alerts    []AlertConfig `json:"alerts"`
	Retention int           `json:"retention"`
}

type AlertConfig struct {
	Type       string      `json:"type"`
	Condition  string      `json:"condition"`
	Threshold  interface{} `json:"threshold"`
	Action     string      `json:"action"`
	Recipients []string    `json:"recipients"`
}

type PurchaseResult struct {
	ID           string    `json:"id"`
	Status       string    `json:"status"`
	DeviceID     string    `json:"device_id"`
	OrderNumber  string    `json:"order_number"`
	TrackingInfo string    `json:"tracking_info"`
	TotalPrice   float64   `json:"total_price"`
	PurchasedAt  time.Time `json:"purchased_at"`
}

type Order struct {
	ID         string       `json:"id"`
	UserID     string       `json:"user_id"`
	DeviceID   string       `json:"device_id"`
	Quantity   int          `json:"quantity"`
	Status     string       `json:"status"`
	TotalPrice float64      `json:"total_price"`
	Shipping   ShippingInfo `json:"shipping"`
	Payment    PaymentInfo  `json:"payment"`
	CreatedAt  time.Time    `json:"created_at"`
	UpdatedAt  time.Time    `json:"updated_at"`
}

type ShippingInfo struct {
	Address           AddressInfo `json:"address"`
	Method            string      `json:"method"`
	Tracking          string      `json:"tracking"`
	EstimatedDelivery time.Time   `json:"estimated_delivery"`
}

type PaymentInfo struct {
	Method      string    `json:"method"`
	Status      string    `json:"status"`
	Amount      float64   `json:"amount"`
	Currency    string    `json:"currency"`
	ProcessedAt time.Time `json:"processed_at"`
}

type AddressInfo struct {
	Name    string `json:"name"`
	Street  string `json:"street"`
	City    string `json:"city"`
	State   string `json:"state"`
	ZipCode string `json:"zip_code"`
	Country string `json:"country"`
}

// Request types

type RegisterDeviceRequest struct {
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	TemplateID string                 `json:"template_id"`
	Config     map[string]interface{} `json:"config"`
	Location   DeviceLocation         `json:"location"`
}

type DeviceUpdates struct {
	Name     *string                `json:"name,omitempty"`
	Config   map[string]interface{} `json:"config,omitempty"`
	Location *DeviceLocation        `json:"location,omitempty"`
	Status   *string                `json:"status,omitempty"`
}

type CreateTemplateRequest struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Description string                 `json:"description"`
	Schema      map[string]interface{} `json:"schema"`
	Firmware    []byte                 `json:"firmware"`
	SDK         SDKInfo                `json:"sdk"`
}

type DeployGatewayRequest struct {
	Name     string         `json:"name"`
	Type     string         `json:"type"`
	Config   GatewayConfig  `json:"config"`
	Location DeviceLocation `json:"location"`
	Devices  []string       `json:"devices"`
}

type PurchaseDeviceRequest struct {
	DeviceID string       `json:"device_id"`
	Quantity int          `json:"quantity"`
	Shipping ShippingInfo `json:"shipping"`
	Payment  PaymentInfo  `json:"payment"`
}

// Hardware platform factory
type PlatformFactory struct {
	deviceManager      DeviceManager
	templateManager    TemplateManager
	gatewayManager     GatewayManager
	marketplaceManager MarketplaceManager
}

// NewPlatformFactory creates a new platform factory
func NewPlatformFactory(
	deviceManager DeviceManager,
	templateManager TemplateManager,
	gatewayManager GatewayManager,
	marketplaceManager MarketplaceManager,
) *PlatformFactory {
	return &PlatformFactory{
		deviceManager:      deviceManager,
		templateManager:    templateManager,
		gatewayManager:     gatewayManager,
		marketplaceManager: marketplaceManager,
	}
}

// CreatePlatform creates a new hardware platform instance
func (pf *PlatformFactory) CreatePlatform() *Platform {
	return NewPlatform(
		pf.deviceManager,
		pf.templateManager,
		pf.gatewayManager,
		pf.marketplaceManager,
	)
}
