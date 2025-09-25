package api

import (
	"context"
	"net/http"
	"strconv"
	"strings"

	"github.com/arx-os/arxos/internal/api/docs"
	_ "github.com/arx-os/arxos/internal/api/docs" // swagger docs
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	httpSwagger "github.com/swaggo/http-swagger"
)

// CreateAPIRouter creates the main API router with all endpoints including Swagger UI
func CreateAPIRouter(s *Server) chi.Router {
	r := chi.NewRouter()

	// Apply middleware
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Compress(5))

	// Health checks (no auth required)
	r.Get("/health", s.HandleHealth)
	r.Get("/ready", s.handleReady)

	// Swagger UI endpoint
	r.Get("/swagger/*", httpSwagger.Handler(
		httpSwagger.URL("/api/v1/swagger/doc.json"),
	))

	// Serve swagger.json
	r.Get("/api/v1/swagger/doc.json", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(docs.SwaggerInfo.ReadDoc()))
	})

	// API v1 routes
	r.Route("/api/v1", func(r chi.Router) {
		// Apply rate limiting and CORS to API routes
		r.Use(s.corsMiddleware)
		r.Use(s.rateLimitMiddleware)

		// Authentication endpoints (no auth required)
		r.Post("/auth/login", s.HandleLogin)
		r.Post("/auth/logout", s.HandleLogout)
		r.Post("/auth/refresh", s.HandleRefreshToken)
		r.Post("/auth/register", s.handleRegister)

		// Protected routes
		r.Group(func(r chi.Router) {
			// Apply authentication middleware
			r.Use(s.authMiddleware)

			// Building endpoints
			r.Route("/buildings", func(r chi.Router) {
				r.Get("/", s.HandleListBuildings)
				r.Post("/", s.HandleCreateBuilding)
				r.Route("/{id}", func(r chi.Router) {
					r.Get("/", s.HandleGetBuilding)
					r.Put("/", s.HandleUpdateBuilding)
					r.Delete("/", s.HandleDeleteBuilding)
				})
			})

			// Equipment endpoints
			r.Route("/equipment", func(r chi.Router) {
				r.Get("/", s.HandleListEquipment)
				r.Route("/{id}", func(r chi.Router) {
					r.Get("/", s.HandleGetEquipment)
				})
			})

			// User endpoints
			r.Route("/users", func(r chi.Router) {
				r.Get("/me", s.HandleGetCurrentUser)
				r.Put("/me", s.HandleUpdateCurrentUser)
				r.Post("/me/password", s.HandleChangePassword)
			})

			// Search endpoint
			r.Get("/search", s.HandleSearch)
		})
	})

	// Mount version info endpoint
	vm := NewVersionManager()
	r.Get("/api/versions", vm.VersionInfoHandler())

	return r
}

// authMiddleware validates JWT tokens
func (s *Server) authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token := extractToken(r)
		if token == "" {
			respondError(w, http.StatusUnauthorized, "Missing authentication token")
			return
		}

		// Validate token with auth service
		userID, err := s.services.Auth.ValidateToken(r.Context(), token)
		if err != nil {
			respondError(w, http.StatusUnauthorized, "Invalid token")
			return
		}

		// Add user ID to context
		ctx := context.WithValue(r.Context(), contextKey("user_id"), userID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// corsMiddleware handles CORS headers
func (s *Server) corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set CORS headers
		for _, origin := range s.config.CORS.AllowedOrigins {
			if origin == "*" || origin == r.Header.Get("Origin") {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				break
			}
		}

		w.Header().Set("Access-Control-Allow-Methods", strings.Join(s.config.CORS.AllowedMethods, ", "))
		w.Header().Set("Access-Control-Allow-Headers", strings.Join(s.config.CORS.AllowedHeaders, ", "))
		w.Header().Set("Access-Control-Max-Age", strconv.Itoa(s.config.CORS.MaxAge))

		// Handle preflight requests
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// rateLimitMiddleware is implemented in middleware.go
