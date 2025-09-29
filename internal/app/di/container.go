package di

import (
	"context"
	"fmt"
	"net/http"
	"sync"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/domain/analytics"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/equipment"
	"github.com/arx-os/arxos/internal/domain/spatial"
	"github.com/arx-os/arxos/internal/domain/workflow"
	"github.com/arx-os/arxos/internal/infra/cache"
	"github.com/arx-os/arxos/internal/infra/database"
	inframessaging "github.com/arx-os/arxos/internal/infra/messaging"
	"github.com/arx-os/arxos/internal/infra/storage"
)

// Container implements a comprehensive dependency injection container
// following Clean Architecture principles and Go best practices
type Container struct {
	// Configuration
	config *Config

	// Services registry
	services map[string]interface{}

	// Singletons registry
	singletons map[string]interface{}

	// Mutex for thread-safe operations
	mutex sync.RWMutex

	// Initialization state
	initialized bool

	// Cleanup functions
	cleanup []func() error
}

// Config holds container configuration
type Config struct {
	// Database configuration
	Database DatabaseConfig `json:"database"`

	// Cache configuration
	Cache CacheConfig `json:"cache"`

	// Storage configuration
	Storage StorageConfig `json:"storage"`

	// WebSocket configuration
	WebSocket WebSocketConfig `json:"websocket"`

	// Development mode
	Development bool `json:"development"`
}

// DatabaseConfig holds database configuration
type DatabaseConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Database string `json:"database"`
	Username string `json:"username"`
	Password string `json:"password"`
	SSLMode  string `json:"ssl_mode"`
}

// CacheConfig holds cache configuration
type CacheConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Password string `json:"password"`
	DB       int    `json:"db"`
}

// StorageConfig holds storage configuration
type StorageConfig struct {
	Type      string `json:"type"` // local, s3, gcs
	Path      string `json:"path"`
	Bucket    string `json:"bucket"`
	Region    string `json:"region"`
	AccessKey string `json:"access_key"`
	SecretKey string `json:"secret_key"`
}

// WebSocketConfig holds WebSocket configuration
type WebSocketConfig struct {
	ReadBufferSize  int `json:"read_buffer_size"`
	WriteBufferSize int `json:"write_buffer_size"`
	PingPeriod      int `json:"ping_period"`
	PongWait        int `json:"pong_wait"`
	WriteWait       int `json:"write_wait"`
	MaxMessageSize  int `json:"max_message_size"`
}

// NewContainer creates a new dependency injection container
func NewContainer(config *Config) *Container {
	if config == nil {
		config = DefaultConfig()
	}

	return &Container{
		config:     config,
		services:   make(map[string]interface{}),
		singletons: make(map[string]interface{}),
		cleanup:    make([]func() error, 0),
	}
}

// DefaultConfig returns default container configuration
func DefaultConfig() *Config {
	return &Config{
		Database: DatabaseConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos",
			Username: "arxos",
			Password: "arxos",
			SSLMode:  "disable",
		},
		Cache: CacheConfig{
			Host:     "localhost",
			Port:     6379,
			Password: "",
			DB:       0,
		},
		Storage: StorageConfig{
			Type: "local",
			Path: "./storage",
		},
		WebSocket: WebSocketConfig{
			ReadBufferSize:  1024,
			WriteBufferSize: 1024,
			PingPeriod:      54,
			PongWait:        60,
			WriteWait:       10,
			MaxMessageSize:  512,
		},
		Development: true,
	}
}

// Initialize initializes all dependencies with proper dependency injection
func (c *Container) Initialize(ctx context.Context) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if c.initialized {
		return fmt.Errorf("container already initialized")
	}

	// Initialize infrastructure layer first (external dependencies)
	if err := c.initializeInfrastructure(ctx); err != nil {
		return fmt.Errorf("failed to initialize infrastructure: %w", err)
	}

	// Initialize domain layer (business logic)
	if err := c.initializeDomain(ctx); err != nil {
		return fmt.Errorf("failed to initialize domain: %w", err)
	}

	// Initialize application layer
	if err := c.initializeApplication(ctx); err != nil {
		return fmt.Errorf("failed to initialize application: %w", err)
	}

	c.initialized = true
	return nil
}

// GetServices returns the services container
func (c *Container) GetServices() *types.Services {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	services, ok := c.singletons["services"].(*types.Services)
	if !ok {
		panic("services not properly initialized")
	}
	return services
}

// GetWebSocketHub returns the WebSocket hub
func (c *Container) GetWebSocketHub() *inframessaging.WebSocketHub {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	hub, ok := c.singletons["websocket_hub"].(*inframessaging.WebSocketHub)
	if !ok {
		panic("websocket hub not properly initialized")
	}
	return hub
}

// Register registers a service with the container
func (c *Container) Register(name string, service interface{}) {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	c.services[name] = service
}

// RegisterSingleton registers a singleton service with the container
func (c *Container) RegisterSingleton(name string, service interface{}) {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	c.singletons[name] = service
}

// Get retrieves a service from the container
func (c *Container) Get(name string) (interface{}, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	// Check singletons first
	if service, exists := c.singletons[name]; exists {
		return service, nil
	}

	// Check regular services
	if service, exists := c.services[name]; exists {
		return service, nil
	}

	return nil, fmt.Errorf("service %s not found", name)
}

// MustGet retrieves a service from the container, panicking if not found
func (c *Container) MustGet(name string) interface{} {
	service, err := c.Get(name)
	if err != nil {
		panic(fmt.Sprintf("service %s not found: %v", name, err))
	}
	return service
}

// Close gracefully shuts down the container and all its dependencies
func (c *Container) Close() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	var lastErr error
	for _, cleanup := range c.cleanup {
		if err := cleanup(); err != nil {
			lastErr = err
		}
	}

	c.initialized = false
	return lastErr
}

// IsInitialized returns whether the container has been initialized
func (c *Container) IsInitialized() bool {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	return c.initialized
}

// Infrastructure layer initialization
func (c *Container) initializeInfrastructure(ctx context.Context) error {
	// Initialize database
	db, err := c.initDatabase(ctx)
	if err != nil {
		return err
	}
	c.RegisterSingleton("database", db)

	// Initialize cache
	cache, err := c.initCache(ctx)
	if err != nil {
		return err
	}
	c.RegisterSingleton("cache", cache)

	// Initialize storage
	storage, err := c.initStorage(ctx)
	if err != nil {
		return err
	}
	c.RegisterSingleton("storage", storage)

	// Initialize WebSocket hub
	hub, err := c.initWebSocketHub(ctx)
	if err != nil {
		return err
	}
	c.RegisterSingleton("websocket_hub", hub)

	// Initialize messaging service
	messaging, err := c.initMessaging(ctx)
	if err != nil {
		return err
	}
	c.RegisterSingleton("messaging", messaging)

	return nil
}

// Domain layer initialization
func (c *Container) initializeDomain(ctx context.Context) error {
	// Get infrastructure dependencies
	db := c.MustGet("database").(database.Interface)
	cache := c.MustGet("cache").(cache.Interface)
	messaging := c.MustGet("messaging").(inframessaging.Interface)

	// Initialize building service
	building := c.initBuilding(db)
	c.RegisterSingleton("building_service", building)

	// Initialize equipment service
	equipment := c.initEquipment(db)
	c.RegisterSingleton("equipment_service", equipment)

	// Initialize spatial service
	spatial := c.initSpatial(db)
	c.RegisterSingleton("spatial_service", spatial)

	// Initialize analytics service
	analytics := c.initAnalytics(db, cache)
	c.RegisterSingleton("analytics_service", analytics)

	// Initialize workflow service
	workflow := c.initWorkflow(db, messaging)
	c.RegisterSingleton("workflow_service", workflow)

	return nil
}

// Application layer initialization
func (c *Container) initializeApplication(ctx context.Context) error {
	// Get all services
	building := c.MustGet("building_service").(building.Service)
	equipment := c.MustGet("equipment_service").(equipment.Service)
	spatial := c.MustGet("spatial_service").(spatial.Service)
	analytics := c.MustGet("analytics_service").(analytics.Service)
	workflow := c.MustGet("workflow_service").(workflow.Service)
	database := c.MustGet("database").(database.Interface)
	cache := c.MustGet("cache").(cache.Interface)
	storage := c.MustGet("storage").(storage.Interface)
	messaging := c.MustGet("messaging").(inframessaging.Interface)

	// Create services container
	services := types.NewServices(
		building,
		equipment,
		spatial,
		analytics,
		workflow,
		database,
		cache,
		storage,
		messaging,
	)

	c.RegisterSingleton("services", services)
	return nil
}

// Individual service initialization methods
func (c *Container) initDatabase(ctx context.Context) (database.Interface, error) {
	// Initialize PostGIS database service
	postgisService := database.NewPostGISService()

	// Build DSN
	dsn := fmt.Sprintf("postgres://%s:%s@%s:%d/%s?sslmode=%s",
		c.config.Database.Username,
		c.config.Database.Password,
		c.config.Database.Host,
		c.config.Database.Port,
		c.config.Database.Database,
		c.config.Database.SSLMode,
	)

	// Connect to database
	if err := postgisService.ConnectWithDSN(ctx, dsn); err != nil {
		return nil, fmt.Errorf("failed to connect to PostGIS: %w", err)
	}

	// Run migrations
	if err := postgisService.Migrate(ctx); err != nil {
		return nil, fmt.Errorf("failed to run migrations: %w", err)
	}

	return postgisService, nil
}

func (c *Container) initCache(ctx context.Context) (cache.Interface, error) {
	// Initialize Redis cache service
	redisService := cache.NewRedisService()

	// Connect to Redis
	if err := redisService.Connect(ctx,
		c.config.Cache.Host,
		c.config.Cache.Port,
		c.config.Cache.Password,
		c.config.Cache.DB,
	); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	return redisService, nil
}

func (c *Container) initStorage(ctx context.Context) (storage.Interface, error) {
	// Initialize local storage service
	localStorageService := storage.NewLocalStorageService()

	// Connect to local storage
	if err := localStorageService.Connect(ctx, c.config.Storage.Path); err != nil {
		return nil, fmt.Errorf("failed to connect to local storage: %w", err)
	}

	return localStorageService, nil
}

func (c *Container) initWebSocketHub(ctx context.Context) (*inframessaging.WebSocketHub, error) {
	config := inframessaging.DefaultWebSocketConfig()
	hub := inframessaging.NewWebSocketHub(config)

	// Start the hub in a goroutine
	go hub.Run()

	// Add cleanup function
	c.cleanup = append(c.cleanup, func() error {
		// WebSocket hub cleanup would go here
		return nil
	})

	return hub, nil
}

func (c *Container) initMessaging(ctx context.Context) (inframessaging.Interface, error) {
	hub := c.MustGet("websocket_hub").(*inframessaging.WebSocketHub)
	return &messagingInfraService{hub: hub}, nil
}

func (c *Container) initBuilding(db database.Interface) building.Service {
	// This would initialize the actual building repository and service
	// For now, return a placeholder
	return &buildingPlaceholder{}
}

func (c *Container) initEquipment(db database.Interface) equipment.Service {
	// This would initialize the actual equipment repository and service
	// For now, return a placeholder
	return &equipmentPlaceholder{}
}

func (c *Container) initSpatial(db database.Interface) spatial.Service {
	// This would initialize the actual spatial repository and service
	// For now, return a placeholder
	return &spatialPlaceholder{}
}

func (c *Container) initAnalytics(db database.Interface, cache cache.Interface) analytics.Service {
	// This would initialize the actual analytics repository and service
	// For now, return a placeholder
	return &analyticsPlaceholder{}
}

func (c *Container) initWorkflow(db database.Interface, messaging inframessaging.Interface) workflow.Service {
	// This would initialize the actual workflow repository and service
	// For now, return a placeholder
	return &workflowPlaceholder{}
}

// messagingInfraService implements the infrastructure messaging interface
type messagingInfraService struct {
	hub *inframessaging.WebSocketHub
}

func (m *messagingInfraService) HandleWebSocket(w http.ResponseWriter, r *http.Request) error {
	return m.hub.HandleWebSocket(w, r)
}

func (m *messagingInfraService) BroadcastToRoom(room string, message interface{}) error {
	return m.hub.BroadcastToRoom(room, message)
}

func (m *messagingInfraService) BroadcastToUser(userID string, message interface{}) error {
	return m.hub.BroadcastToUser(userID, message)
}

func (m *messagingInfraService) BroadcastToAll(message interface{}) error {
	return m.hub.BroadcastToAll(message)
}

func (m *messagingInfraService) JoinRoom(userID, room string) error {
	return m.hub.JoinRoom(userID, room)
}

func (m *messagingInfraService) LeaveRoom(userID, room string) error {
	return m.hub.LeaveRoom(userID, room)
}

func (m *messagingInfraService) GetRoomUsers(room string) ([]string, error) {
	return m.hub.GetRoomUsers(room)
}

func (m *messagingInfraService) SendNotification(ctx context.Context, userID string, notification *inframessaging.Notification) error {
	return m.hub.BroadcastToUser(userID, notification)
}

func (m *messagingInfraService) SendBulkNotification(ctx context.Context, userIDs []string, notification *inframessaging.Notification) error {
	var lastErr error
	for _, userID := range userIDs {
		if err := m.hub.BroadcastToUser(userID, notification); err != nil {
			lastErr = err
		}
	}
	return lastErr
}

func (m *messagingInfraService) IsHealthy() bool {
	return m.hub.IsHealthy()
}

func (m *messagingInfraService) GetStats() map[string]interface{} {
	return m.hub.GetStats()
}
