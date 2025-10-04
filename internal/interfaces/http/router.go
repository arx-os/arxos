package http

import (
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/interfaces/http/handlers"
	httpmiddleware "github.com/arx-os/arxos/internal/interfaces/http/middleware"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/pkg/auth"
)

// RouterConfig holds configuration for HTTP routing
type RouterConfig struct {
	Server     *types.Server
	Container  *app.Container
	JWTManager *auth.JWTManager
}

// NewRouter creates a fully configured HTTP router with mobile endpoints
func NewRouter(config *RouterConfig) chi.Router {
	// Create Chi router
	router := chi.NewRouter()

	// Apply common middleware
	router.Use(middleware.RequestID)
	router.Use(middleware.RealIP)
	router.Use(middleware.Logger)
	router.Use(middleware.Recoverer)
	router.Use(middleware.Timeout(60 * time.Second))

	// Create handlers with dependencies
	mobileHandlers := createMobileHandlers(config)
	publicHandlers := createPublicHandlers(config)
	apiHandlers := createAPIHandlers(config)

	// Health and status endpoints (public)
	router.Get("/health", publicHandlers.apiHandler.HandleHealth)
	router.Get("/ready", publicHandlers.apiHandler.HandleHealth)

	// API v1 routes
	router.Route("/api/v1", func(r chi.Router) {
		// Public API routes (rate-limited but no auth required)
		r.Route("/public", func(r chi.Router) {
			r.Use(httpmiddleware.RateLimit(1000, time.Hour))
			r.Get("/info", publicHandlers.apiHandler.HandleAPIInfo)
		})

		// Core API routes (requires authentication)
		r.Route("/buildings", func(r chi.Router) {
			r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
			r.Use(httpmiddleware.RateLimit(100, time.Hour))
			r.Get("/", apiHandlers.buildingHandler.ListBuildings)
			r.Post("/", apiHandlers.buildingHandler.CreateBuilding)
			r.Get("/{id}", apiHandlers.buildingHandler.GetBuilding)
			r.Put("/{id}", apiHandlers.buildingHandler.UpdateBuilding)
		})

		// Mobile API routes (mobile-optimized with AR/spatial features)
		r.Route("/mobile", func(r chi.Router) {
			// Mobile authentication endpoints (public)
			r.Route("/auth", func(r chi.Router) {
				r.Use(httpmiddleware.RateLimit(100, time.Hour))
				r.Post("/login", mobileHandlers.authHandler.HandleMobileLogin)
				r.Post("/register", mobileHandlers.authHandler.HandleMobileRegister)
				r.Post("/refresh", mobileHandlers.authHandler.HandleMobileRefreshToken)

				// Protected profile endpoints
				r.Group(func(r chi.Router) {
					r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
					r.Get("/profile", mobileHandlers.authHandler.HandleMobileProfile)
					r.Post("/logout", mobileHandlers.authHandler.HandleMobileLogout)
				})
			})

			// Mobile equipment endpoints (spatial/AR enabled)
			r.Route("/equipment", func(r chi.Router) {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(200, time.Hour))
				r.Get("/building/{buildingId}", mobileHandlers.mobileHandler.HandleMobileEquipment)
				r.Get("/{equipmentId}", mobileHandlers.mobileHandler.HandleMobileEquipmentDetail)
			})

			// Mobile spatial/AR endpoints (ARKit/ARCore enabled)
			r.Route("/spatial", func(r chi.Router) {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(300, time.Hour))

				// AR anchors and spatial mapping - using available methods
				r.Route("/anchors", func(r chi.Router) {
					r.Post("/", mobileHandlers.spatialHandler.HandleCreateSpaticialAnchor)
					r.Get("/building/{buildingId}", mobileHandlers.spatialHandler.HandleGetSpatialAnchors)
				})

				// Spatial queries and nearby equipment
				r.Route("/nearby", func(r chi.Router) {
					r.Get("/equipment", mobileHandlers.spatialHandler.HandleNearbyEquipment)
				})

				// AR session and mapping data
				r.Post("/mapping", mobileHandlers.spatialHandler.HandleSpatialMapping)

				// Building spatial data
				r.Get("/buildings", mobileHandlers.spatialHandler.HandleBuildingsList)
			})
		})

		// Legacy equipment routes (maintained for backward compatibility)
		r.Route("/equipment", func(r chi.Router) {
			if apiHandlers.equipmentHandler != nil {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(100, time.Hour))
				r.Get("/", apiHandlers.equipmentHandler.ListEquipment)
				r.Post("/", apiHandlers.equipmentHandler.CreateEquipment)
				r.Get("/{id}", apiHandlers.equipmentHandler.GetEquipment)
			}
		})
	})

	return router
}

// mobileHandlers holds all mobile-specific handlers
type mobileHandlers struct {
	authHandler    *handlers.AuthHandler
	mobileHandler  *handlers.MobileHandler
	spatialHandler *handlers.SpatialHandler
}

// publicHandlers holds public handlers
type publicHandlers struct {
	apiHandler *handlers.APIHandler
}

// apiHandlers holds authenticated API handlers
type apiHandlers struct {
	buildingHandler  *handlers.BuildingHandler
	equipmentHandler *handlers.EquipmentHandler
	userHandler      *handlers.UserHandler
}

// NewRouterConfig creates a router configuration from existing dependencies
func NewRouterConfig(server *types.Server, container *app.Container, jwtConfig *auth.JWTConfig) (*RouterConfig, error) {
	jwtManager, err := auth.NewJWTManager(jwtConfig)
	if err != nil {
		return nil, err
	}

	return &RouterConfig{
		Server:     server,
		Container:  container,
		JWTManager: jwtManager,
	}, nil
}

// createMobileHandlers creates mobile-specific handlers with proper dependencies
func createMobileHandlers(config *RouterConfig) *mobileHandlers {
	logger := config.Container.GetLogger()
	userUC := config.Container.GetUserUseCase()
	buildingUC := config.Container.GetBuildingUseCase()
	equipmentUC := config.Container.GetEquipmentUseCase()
	spatialRepo := config.Container.GetSpatialRepository()

	return &mobileHandlers{
		authHandler:    handlers.NewAuthHandler(config.Server, userUC, logger),
		mobileHandler:  handlers.NewMobileHandler(config.Server, buildingUC, equipmentUC, logger),
		spatialHandler: handlers.NewSpatialHandler(config.Server, buildingUC, equipmentUC, spatialRepo, logger),
	}
}

// createPublicHandlers creates public handlers for unauthenticated endpoints
func createPublicHandlers(config *RouterConfig) *publicHandlers {
	return &publicHandlers{
		apiHandler: handlers.NewAPIHandler(config.Server),
	}
}

// createAPIHandlers creates authenticated API handlers
func createAPIHandlers(config *RouterConfig) *apiHandlers {
	logger := config.Container.GetLogger()
	userUC := config.Container.GetUserUseCase()
	buildingUC := config.Container.GetBuildingUseCase()
	equipmentUC := config.Container.GetEquipmentUseCase()

	return &apiHandlers{
		buildingHandler:  handlers.NewBuildingHandler(config.Server, buildingUC, logger),
		equipmentHandler: handlers.NewEquipmentHandler(config.Server, equipmentUC, logger),
		userHandler:      handlers.NewUserHandler(config.Server, userUC, logger),
	}
}
