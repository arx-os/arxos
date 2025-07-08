package middleware

import (
	"time"

	"github.com/go-chi/chi/v5"
	"go.uber.org/zap"
)

// ExampleCacheIntegration demonstrates how to integrate cache middleware
// This is an example file showing different cache configurations
func ExampleCacheIntegration() {
	// Example logger
	logger, _ := zap.NewProduction()

	// Create router
	r := chi.NewRouter()

	// Example 1: Global cache middleware with default configuration
	r.Use(CacheMiddleware(nil))

	// Example 2: Global cache middleware with custom TTL
	r.Use(CacheMiddlewareWithTTL(10 * time.Minute))

	// Example 3: Path-specific caching
	r.Group(func(r chi.Router) {
		// Cache building endpoints with 15-minute TTL
		config := &CacheConfig{
			TTL:            15 * time.Minute,
			KeyPrefix:      "buildings:cache:",
			IncludeQuery:   true,
			IncludeHeaders: []string{"Authorization"},
			Logger:         logger,
		}
		r.Use(CacheMiddleware(config))

		// Building routes
		r.Get("/api/buildings", nil)             // handlers.ListBuildings
		r.Get("/api/buildings/{id}", nil)        // handlers.GetBuilding
		r.Get("/api/buildings/{id}/floors", nil) // handlers.ListFloors
	})

	// Example 4: Asset endpoints with different TTL
	r.Group(func(r chi.Router) {
		// Short TTL for asset list (frequently changing)
		r.Use(CacheMiddlewareWithTTL(5 * time.Minute))
		r.Get("/api/buildings/{id}/assets", nil) // handlers.GetBuildingAssets

		// Longer TTL for individual assets
		r.Use(CacheMiddlewareWithTTL(15 * time.Minute))
		r.Get("/api/assets/{id}", nil) // handlers.GetBuildingAsset
	})

	// Example 5: Version control with very short TTL
	r.Group(func(r chi.Router) {
		// Very short TTL for version history (changes frequently)
		r.Use(CacheMiddlewareWithTTL(2 * time.Minute))
		r.Get("/api/floor/{id}/history", nil) // handlers.GetVersionHistory

		// Short TTL for version diffs
		r.Use(CacheMiddlewareWithTTL(5 * time.Minute))
		r.Get("/api/floor/{id}/diff", nil) // handlers.GetVersionDiff

		// Longer TTL for branch information
		r.Use(CacheMiddlewareWithTTL(10 * time.Minute))
		r.Get("/api/floor/{id}/branch", nil) // handlers.GetBranchInformation
	})

	// Example 6: Symbol library with long TTL (static data)
	r.Group(func(r chi.Router) {
		// Long TTL for symbol library (rarely changes)
		r.Use(CacheMiddlewareWithTTL(1 * time.Hour))
		r.Get("/api/symbols", nil)            // handlers.ListSymbols
		r.Get("/api/symbols/{id}", nil)       // handlers.GetSymbol
		r.Get("/api/symbols/categories", nil) // handlers.GetSymbolCategories
	})

	// Example 7: Cache invalidation for write operations
	r.Group(func(r chi.Router) {
		// Invalidate building caches on building operations
		r.Use(CacheInvalidationMiddleware([]string{"/api/buildings"}, nil))
		r.Post("/api/buildings", nil)        // handlers.CreateBuilding
		r.Put("/api/buildings/{id}", nil)    // handlers.UpdateBuilding
		r.Delete("/api/buildings/{id}", nil) // handlers.DeleteBuilding
	})

	r.Group(func(r chi.Router) {
		// Invalidate asset caches on asset operations
		r.Use(CacheInvalidationMiddleware([]string{"/api/assets"}, nil))
		r.Post("/api/buildings/{id}/assets", nil) // handlers.CreateBuildingAsset
		r.Put("/api/assets/{id}", nil)            // handlers.UpdateBuildingAsset
		r.Delete("/api/assets/{id}", nil)         // handlers.DeleteBuildingAsset
	})

	// Example 8: Exclude sensitive endpoints from caching
	r.Group(func(r chi.Router) {
		// Exclude admin and health endpoints from caching
		exclusions := []string{"/api/admin", "/api/health", "/api/metrics"}
		r.Use(CacheMiddlewareWithExclusions(exclusions, nil))

		// These endpoints won't be cached
		r.Get("/api/admin/users", nil) // handlers.ListUsers
		r.Get("/api/health", nil)      // handlers.HealthCheck
		r.Get("/api/metrics", nil)     // handlers.GetMetrics
	})

	// Example 9: Cache statistics middleware
	r.Use(CacheStatsMiddleware(nil))

	// Example 10: Custom configuration for specific use case
	r.Group(func(r chi.Router) {
		config := &CacheConfig{
			TTL:            30 * time.Minute,
			KeyPrefix:      "export:cache:",
			IncludeQuery:   true,
			IncludeBody:    true, // Include body for export requests
			IncludeHeaders: []string{"Authorization", "X-Export-Format"},
			MaxBodySize:    2 * 1024 * 1024, // 2MB
			Logger:         logger,
		}
		r.Use(CacheMiddleware(config))

		r.Get("/api/export/buildings", nil) // handlers.ExportBuildings
		r.Get("/api/export/assets", nil)    // handlers.ExportAssets
	})

	_ = r // Use router
}

// ExampleMainIntegration shows how to integrate in main.go
func ExampleMainIntegration() {
	// This would be in main.go
	/*
		func main() {
			// Initialize logger
			logger, _ := zap.NewProduction()
			defer logger.Sync()

			// Initialize Redis service
			redisService, err := services.NewRedisService(nil, logger)
			if err != nil {
				log.Printf("Warning: Failed to initialize Redis service: %v", err)
				redisService = nil
			}

			// Initialize cache service
			var cacheService *services.CacheService
			if redisService != nil {
				cacheService = services.NewCacheService(redisService, nil, logger)
				log.Println("✅ Cache service initialized successfully")
			} else {
				log.Println("⚠️  Cache service disabled - Redis not available")
			}

			// Make cache service available to handlers
			handlers.SetCacheService(cacheService)

			// Set up router
			r := chi.NewRouter()

			// Apply security middleware globally
			r.Use(securityMiddleware.SecurityHeadersMiddleware)
			r.Use(securityMiddleware.AuditLoggingMiddleware)
			r.Use(securityMiddleware.RateLimitMiddleware(100, 200))

			// Apply cache middleware globally with default settings
			r.Use(CacheMiddlewareWithTTL(5 * time.Minute))

			// API routes with authentication
			r.Route("/api", func(r chi.Router) {
				r.Post("/register", handlers.Register)
				r.Post("/login", handlers.Login)

				r.Group(func(r chi.Router) {
					r.Use(auth.RequireAuth)

					// Building endpoints with custom cache configuration
					r.Group(func(r chi.Router) {
						config := &CacheConfig{
							TTL:           15 * time.Minute,
							KeyPrefix:     "buildings:cache:",
							IncludeQuery:  true,
							IncludeHeaders: []string{"Authorization"},
							Logger:        logger,
						}
						r.Use(CacheMiddleware(config))

						r.Get("/buildings", handlers.ListBuildings)
						r.Get("/buildings/{id}", handlers.GetBuilding)
						r.Get("/buildings/{id}/floors", handlers.ListFloors)
					})

					// Asset endpoints with different TTL
					r.Group(func(r chi.Router) {
						r.Use(CacheMiddlewareWithTTL(5 * time.Minute))
						r.Get("/buildings/{id}/assets", handlers.GetBuildingAssets)
						r.Get("/assets/{id}", handlers.GetBuildingAsset)
					})

					// Version control endpoints
					r.Group(func(r chi.Router) {
						r.Use(CacheMiddlewareWithTTL(2 * time.Minute))
						r.Get("/floor/{id}/history", handlers.GetVersionHistory)
						r.Get("/floor/{id}/diff", handlers.GetVersionDiff)
						r.Get("/floor/{id}/branch", handlers.GetBranchInformation)
					})

					// Write operations with cache invalidation
					r.Group(func(r chi.Router) {
						r.Use(CacheInvalidationMiddleware([]string{"/api/buildings", "/api/assets"}, nil))

						r.Post("/buildings", handlers.CreateBuilding)
						r.Put("/buildings/{id}", handlers.UpdateBuilding)
						r.Post("/buildings/{id}/assets", handlers.CreateBuildingAsset)
						r.Put("/assets/{id}", handlers.UpdateBuildingAsset)
					})

					// Symbol library with long TTL
					r.Group(func(r chi.Router) {
						r.Use(CacheMiddlewareWithTTL(1 * time.Hour))
						r.Get("/symbols", handlers.ListSymbols)
						r.Get("/symbols/{id}", handlers.GetSymbol)
					})
				})
			})

			// Start server
			log.Println("🚀 Server running on :8080")
			if err := http.ListenAndServe(":8080", r); err != nil {
				log.Fatalf("Server failed: %v", err)
			}
		}
	*/
}
