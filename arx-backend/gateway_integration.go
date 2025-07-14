package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"arx/db"
	"arx/handlers"
	securityMiddleware "arx/middleware"
	"arx/middleware/auth"
	"arx/models"
	"arx/services"

	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/joho/godotenv"
	"github.com/rs/cors"
	"go.uber.org/zap"

	"arx/gateway"
)

// GatewayIntegration integrates the API Gateway with the existing backend
type GatewayIntegration struct {
	gateway *gateway.Gateway
	backend *BackendServer
	logger  *zap.Logger
	config  *IntegrationConfig
}

// BackendServer represents the existing backend server
type BackendServer struct {
	router *chi.Mux
	port   int
	host   string
}

// IntegrationConfig holds integration configuration
type IntegrationConfig struct {
	GatewayEnabled bool   `yaml:"gateway_enabled"`
	GatewayPort    int    `yaml:"gateway_port"`
	BackendPort    int    `yaml:"backend_port"`
	Host           string `yaml:"host"`
}

// NewGatewayIntegration creates a new gateway integration
func NewGatewayIntegration(config *IntegrationConfig) (*GatewayIntegration, error) {
	logger, err := zap.NewProduction()
	if err != nil {
		return nil, err
	}

	integration := &GatewayIntegration{
		logger: logger,
		config: config,
	}

	// Initialize backend server
	if err := integration.initializeBackend(); err != nil {
		return nil, err
	}

	// Initialize gateway if enabled
	if config.GatewayEnabled {
		if err := integration.initializeGateway(); err != nil {
			return nil, err
		}
	}

	return integration, nil
}

// initializeBackend initializes the existing backend server
func (gi *GatewayIntegration) initializeBackend() error {
	// Load environment variables
	godotenv.Load()

	// Initialize database
	db.Connect()
	db.Migrate()
	models.SeedCategories(db.DB)

	// Initialize services
	loggingService, err := services.NewLoggingService(db.DB, "./logs")
	if err != nil {
		return err
	}

	// Initialize Redis service
	redisService, err := services.NewRedisService(nil, gi.logger)
	if err != nil {
		gi.logger.Warn("Failed to initialize Redis service", zap.Error(err))
	}

	// Initialize cache service
	var cacheService *services.CacheService
	if redisService != nil {
		cacheService = services.NewCacheService(redisService, nil, gi.logger)
		handlers.SetCacheService(cacheService)
	}

	// Initialize handlers
	handlers.InitCMMSClient()

	// Set up router
	router := chi.NewRouter()
	router.Use(chimiddleware.Logger)
	router.Use(cors.AllowAll().Handler)

	// Apply security middleware
	router.Use(securityMiddleware.SecurityHeadersMiddleware)
	router.Use(securityMiddleware.AuditLoggingMiddleware)
	router.Use(securityMiddleware.RateLimitMiddleware(100, 200))

	// Add request logging middleware
	router.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			next.ServeHTTP(w, r)
			duration := time.Since(start)

			ctx := &services.LogContext{
				RequestID: r.Header.Get("X-Request-ID"),
				IPAddress: r.RemoteAddr,
				Endpoint:  r.URL.Path,
				Method:    r.Method,
				UserAgent: r.UserAgent(),
			}
			loggingService.LogAPIRequest(ctx, 200, duration, 0)
		})
	})

	// Set up routes
	gi.setupBackendRoutes(router)

	gi.backend = &BackendServer{
		router: router,
		port:   gi.config.BackendPort,
		host:   gi.config.Host,
	}

	return nil
}

// setupBackendRoutes sets up the existing backend routes
func (gi *GatewayIntegration) setupBackendRoutes(router *chi.Mux) {
	router.Route("/api", func(r chi.Router) {
		r.Post("/register", handlers.Register)
		r.Post("/login", handlers.Login)
		r.Get("/health", handlers.HealthCheck)

		r.Group(func(r chi.Router) {
			r.Use(auth.RequireAuth)
			r.Use(securityMiddleware.RateLimitMiddleware(50, 100))

			// Existing routes
			r.Get("/floor/svg", handlers.ServeFloorSVG)
			r.Get("/object/{objectId}/info", handlers.ServeObjectInfo)
			r.Post("/object/{objectId}/comment", handlers.PostObjectComment)

			r.Get("/projects", handlers.ListProjects)
			r.Post("/projects", handlers.CreateProject)
			r.Get("/projects/{id}", handlers.GetProject)

			// Building routes
			r.Get("/buildings", handlers.ListBuildings)
			r.Post("/buildings", handlers.CreateBuilding)
			r.Get("/buildings/{id}", handlers.GetBuilding)
			r.Put("/buildings/{id}", handlers.UpdateBuilding)
			r.Get("/buildings/{id}/floors", handlers.ListFloors)

			// Markup routes
			r.Post("/markup", handlers.SubmitMarkup)
			r.Get("/markups", handlers.ListMarkups)
			r.Delete("/markup/{id}", handlers.DeleteMarkup)

			// Drawing routes
			r.Post("/drawings", handlers.CreateDrawing)
			r.Get("/drawings/{drawingID}/last_modified", handlers.GetDrawingLastModified)

			// Comment routes
			r.Put("/comment/{id}", handlers.EditComment)
			r.Delete("/comment/{id}", handlers.DeleteComment)

			// Logs routes
			r.Get("/logs/{building_id}", handlers.GetLogs)

			// User routes
			r.Get("/me", handlers.Me)

			// HTMX routes
			r.Get("/buildings", handlers.HTMXListBuildings)
			r.Get("/buildings/{id}/floors", handlers.HTMXListFloors)

			// Admin routes
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "editor"))

				// BIM Object routes
				gi.setupBIMObjectRoutes(r)
			})
		})
	})
}

// setupBIMObjectRoutes sets up BIM object routes
func (gi *GatewayIntegration) setupBIMObjectRoutes(r chi.Router) {
	// Wall routes
	r.Post("/walls", handlers.CreateWall)
	r.Get("/walls/{id}", handlers.GetWall)
	r.Patch("/wall/{id}", handlers.UpdateWall)
	r.Delete("/walls/{id}", handlers.DeleteWall)
	r.Post("/wall/{id}/lock", handlers.LockWall)
	r.Post("/wall/{id}/unlock", handlers.UnlockWall)
	r.Post("/wall/{id}/assign", handlers.AssignWall)
	r.Post("/wall/{id}/status", handlers.UpdateWallStatus)

	// Door routes
	r.Post("/doors", handlers.CreateDoor)
	r.Get("/doors/{id}", handlers.GetDoor)
	r.Patch("/doors/{id}", handlers.UpdateDoor)
	r.Delete("/doors/{id}", handlers.DeleteDoor)

	// Window routes
	r.Post("/windows", handlers.CreateWindow)
	r.Get("/windows/{id}", handlers.GetWindow)
	r.Patch("/windows/{id}", handlers.UpdateWindow)
	r.Delete("/windows/{id}", handlers.DeleteWindow)

	// Room routes
	r.Post("/rooms", handlers.CreateRoom)
	r.Get("/rooms/{id}", handlers.GetRoom)
	r.Patch("/room/{id}", handlers.UpdateRoom)
	r.Delete("/rooms/{id}", handlers.DeleteRoom)
	r.Post("/room/{id}/lock", handlers.LockRoom)
	r.Post("/room/{id}/unlock", handlers.UnlockRoom)
	r.Post("/room/{id}/assign", handlers.AssignRoom)
	r.Post("/room/{id}/status", handlers.UpdateRoomStatus)

	// Device routes
	r.Post("/devices", handlers.CreateDevice)
	r.Get("/devices/{id}", handlers.GetDevice)
	r.Patch("/device/{id}", handlers.UpdateDeviceDetails)
	r.Delete("/devices/{id}", handlers.DeleteDevice)
}

// initializeGateway initializes the API Gateway
func (gi *GatewayIntegration) initializeGateway() error {
	// Create gateway configuration
	gatewayConfig := &gateway.Config{
		Port:         gi.config.GatewayPort,
		Host:         gi.config.Host,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
		Services: map[string]gateway.ServiceConfig{
			"arx-backend": {
				Name:   "arx-backend",
				URL:    fmt.Sprintf("http://%s:%d", gi.config.Host, gi.config.BackendPort),
				Health: fmt.Sprintf("http://%s:%d/api/health", gi.config.Host, gi.config.BackendPort),
				Routes: []gateway.Route{
					{
						Path:    "/api/*",
						Service: "arx-backend",
						Methods: []string{"GET", "POST", "PUT", "DELETE", "PATCH"},
						Auth:    true,
					},
				},
			},
		},
		Auth: gateway.AuthConfig{
			JWTSecret:   os.Getenv("JWT_SECRET"),
			TokenExpiry: 24 * time.Hour,
			Roles:       []string{"admin", "user", "guest"},
		},
		RateLimit: gateway.RateLimitConfig{
			RequestsPerSecond: 100,
			Burst:             200,
		},
		Monitoring: gateway.MonitoringConfig{
			HealthCheckInterval: 30 * time.Second,
		},
	}

	// Create gateway
	gw, err := gateway.NewGateway(gatewayConfig)
	if err != nil {
		return err
	}

	gi.gateway = gw
	return nil
}

// Start starts both the gateway and backend servers
func (gi *GatewayIntegration) Start() error {
	// Start backend server
	go func() {
		gi.logger.Info("Starting backend server",
			zap.String("host", gi.config.Host),
			zap.Int("port", gi.config.BackendPort),
		)

		server := &http.Server{
			Addr:    fmt.Sprintf("%s:%d", gi.config.Host, gi.config.BackendPort),
			Handler: gi.backend.router,
		}

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			gi.logger.Error("Backend server failed", zap.Error(err))
		}
	}()

	// Start gateway if enabled
	if gi.config.GatewayEnabled && gi.gateway != nil {
		go func() {
			gi.logger.Info("Starting API Gateway",
				zap.String("host", gi.config.Host),
				zap.Int("port", gi.config.GatewayPort),
			)

			if err := gi.gateway.Start(); err != nil {
				gi.logger.Error("Gateway failed", zap.Error(err))
			}
		}()
	}

	return nil
}

// Stop gracefully shuts down both servers
func (gi *GatewayIntegration) Stop(ctx context.Context) error {
	gi.logger.Info("Shutting down integration")

	if gi.gateway != nil {
		if err := gi.gateway.Stop(ctx); err != nil {
			gi.logger.Error("Failed to stop gateway", zap.Error(err))
		}
	}

	return nil
}

func runGatewayIntegration() {
	// Parse command line flags
	gatewayEnabled := flag.Bool("gateway", false, "Enable API Gateway")
	gatewayPort := flag.Int("gateway-port", 8080, "Gateway port")
	backendPort := flag.Int("backend-port", 8081, "Backend port")
	host := flag.String("host", "localhost", "Host address")
	flag.Parse()

	// Create integration configuration
	config := &IntegrationConfig{
		GatewayEnabled: *gatewayEnabled,
		GatewayPort:    *gatewayPort,
		BackendPort:    *backendPort,
		Host:           *host,
	}

	// Create integration
	integration, err := NewGatewayIntegration(config)
	if err != nil {
		log.Fatalf("Failed to create integration: %v", err)
	}

	// Setup graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Start integration
	if err := integration.Start(); err != nil {
		log.Fatalf("Failed to start integration: %v", err)
	}

	// Wait for shutdown signal
	sig := <-sigChan
	log.Printf("Received signal: %v", sig)

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := integration.Stop(ctx); err != nil {
		log.Printf("Error stopping integration: %v", err)
	}
}
