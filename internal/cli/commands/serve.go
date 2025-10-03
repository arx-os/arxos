package commands

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/spf13/cobra"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/interfaces/http/handlers"
	httpmiddleware "github.com/arx-os/arxos/internal/interfaces/http/middleware"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/pkg/auth"
)

// CreateServeCommand creates the serve command
func CreateServeCommand(serviceContext interface{}) *cobra.Command {
	var (
		port     int
		host     string
		certFile string
		keyFile  string
	)

	cmd := &cobra.Command{
		Use:   "serve",
		Short: "Start the ArxOS HTTP server",
		Long:  "Start the ArxOS HTTP API server with all configured endpoints and middleware",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runServer(host, port, certFile, keyFile)
		},
	}

	cmd.Flags().IntVarP(&port, "port", "p", 8080, "Port to listen on")
	cmd.Flags().StringVar(&host, "host", "0.0.0.0", "Host to bind to")
	cmd.Flags().StringVar(&certFile, "cert", "", "TLS certificate file")
	cmd.Flags().StringVar(&keyFile, "key", "", "TLS private key file")

	return cmd
}

// runServer starts the HTTP server
func runServer(host string, port int, certFile, keyFile string) error {
	fmt.Printf("🚀 Starting ArxOS HTTP server on %s:%d\n", host, port)

	// Create DI container
	container := app.NewContainer()

	// Get dependencies from container
	buildingUC := container.GetBuildingUseCase()
	logger := container.GetLogger()

	// Create JWT manager
	jwtConfig := &auth.JWTConfig{
		SecretKey:          "dev_jwt_secret_key_change_in_production",
		AccessTokenExpiry:  15 * time.Minute,
		RefreshTokenExpiry: 7 * 24 * time.Hour,
		Issuer:             "arxos",
		Audience:           "arxos-clients",
		Algorithm:          "HS256",
	}

	jwtManager, err := auth.NewJWTManager(jwtConfig)
	if err != nil {
		return fmt.Errorf("failed to create JWT manager: %w", err)
	}

	// Create server configuration using existing types
	serverConfig := types.NewServer(fmt.Sprintf("%d", port), host)

	// Create handlers using existing architecture
	apiHandler := handlers.NewAPIHandler(serverConfig)
	buildingHandler := handlers.NewBuildingHandler(serverConfig, buildingUC, logger)

	// Create router and setup middleware
	router := chi.NewRouter()

	// Setup middleware
	router.Use(middleware.RequestID)
	router.Use(middleware.RealIP)
	router.Use(middleware.Logger)
	router.Use(middleware.Recoverer)
	router.Use(middleware.Timeout(60 * time.Second))
	router.Use(httpmiddleware.RateLimit(100, time.Minute))
	router.Use(httpmiddleware.AuthMiddleware(jwtManager))

	// Register routes
	router.Get("/health", apiHandler.HandleHealth)
	router.Route("/api/v1", func(r chi.Router) {
		r.Get("/health", apiHandler.HandleHealth)
		r.Route("/buildings", func(r chi.Router) {
			r.Get("/", buildingHandler.ListBuildings)
			r.Post("/", buildingHandler.CreateBuilding)
			r.Get("/{id}", buildingHandler.GetBuilding)
			r.Put("/{id}", buildingHandler.UpdateBuilding)
			r.Delete("/{id}", buildingHandler.DeleteBuilding)
			r.Post("/{id}/import", buildingHandler.ImportBuilding)
			r.Get("/{id}/export", buildingHandler.ExportBuilding)
		})
	})

	// Create HTTP server
	srv := &http.Server{
		Addr:         fmt.Sprintf("%s:%d", host, port),
		Handler:      router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	// Start server in goroutine
	go func() {
		var err error
		if certFile != "" && keyFile != "" {
			fmt.Printf("🔒 Starting HTTPS server with TLS\n")
			err = srv.ListenAndServeTLS(certFile, keyFile)
		} else {
			fmt.Printf("🌐 Starting HTTP server\n")
			err = srv.ListenAndServe()
		}

		if err != nil && err != http.ErrServerClosed {
			logger.Error("Server failed to start", "error", err)
			os.Exit(1)
		}
	}()

	fmt.Printf("✅ ArxOS HTTP server started successfully\n")
	fmt.Printf("📡 API available at: http://%s:%d/api/v1\n", host, port)
	fmt.Printf("🏥 Health check: http://%s:%d/health\n", host, port)
	fmt.Printf("📚 API docs: http://%s:%d/api/v1/docs\n", host, port)

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	fmt.Println("\n🛑 Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Error("Server forced to shutdown", "error", err)
		return err
	}

	fmt.Println("✅ Server shutdown complete")
	return nil
}
