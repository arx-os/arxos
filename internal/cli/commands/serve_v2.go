package commands

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/spf13/cobra"

	"github.com/arx-os/arxos/internal/app"
	httppkg "github.com/arx-os/arxos/internal/interfaces/http"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/pkg/auth"
)

// CreateServeV2Command creates the enhanced serve command with mobile endpoints
func CreateServeV2Command(serviceContext interface{}) *cobra.Command {
	var (
		port     int
		host     string
		certFile string
		keyFile  string
	)

	cmd := &cobra.Command{
		Use:   "serve-v2",
		Short: "Start the ArxOS HTTP server with mobile API v2",
		Long:  "Start the enhanced ArxOS HTTP API server with mobile endpoints, spatial services, and ARKit/ARCore support",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runServerV2(host, port, certFile, keyFile)
		},
	}

	cmd.Flags().IntVarP(&port, "port", "p", 8080, "Port to listen on")
	cmd.Flags().StringVar(&host, "host", "0.0.0.0", "Host to bind to")
	cmd.Flags().StringVar(&certFile, "cert", "", "TLS certificate file")
	cmd.Flags().StringVar(&keyFile, "key", "", "TLS private key file")

	return cmd
}

// runServerV2 starts the enhanced HTTP server with mobile endpoints
func runServerV2(host string, port int, certFile, keyFile string) error {
	fmt.Printf("🚀 Starting ArxOS HTTP server v2 with Mobile API on %s:%d\n", host, port)

	// Create DI container
	container := app.NewContainer()

	// Create JWT manager configuration
	jwtConfig := &auth.JWTConfig{
		SecretKey:          "dev_jwt_secret_key_change_in_production",
		AccessTokenExpiry:  15 * time.Minute,
		RefreshTokenExpiry: 7 * 24 * time.Hour,
		Issuer:             "arxos",
		Audience:           "arxos-clients",
		Algorithm:          "HS256",
	}

	// Create server configuration
	serverConfig := types.NewServer(fmt.Sprintf("%d", port), host)

	// Create router configuration
	routerConfig, err := httppkg.NewRouterConfig(serverConfig, container, jwtConfig)
	if err != nil {
		return fmt.Errorf("failed to create router config: %w", err)
	}

	// Create enhanced router with mobile endpoints
	router := httppkg.NewRouter(routerConfig)

	// Create HTTP server
	srv := &http.Server{
		Addr:         fmt.Sprintf("%s:%d", host, port),
		Handler:      router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	// Setup graceful shutdown signal handling
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

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
			logger := container.GetLogger()
			logger.Error("Server failed to start", "error", err)
			os.Exit(1)
		}
	}()

	// Print server startup info
	fmt.Printf("✅ ArxOS HTTP server v2 started successfully\n")
	fmt.Printf("📡 API available at: http://%s:%d/api/v1\n", host, port)
	fmt.Printf("📱 Mobile API available at: http://%s:%d/api/v1/mobile\n", host, port)
	fmt.Printf("🗺️  Spatial API available at: http://%s:%d/api/v1/mobile/spatial\n", host, port)
	fmt.Printf("🏥 Health check: http://%s:%d/health\n", host, port)

	// Mobile-specific endpoints info
	fmt.Printf("\n📱 Mobile API Endpoints:\n")
	fmt.Printf("   🔐 Authentication: POST /api/v1/mobile/auth/login\n")
	fmt.Printf("   🔐 Registration:   POST /api/v1/mobile/auth/register\n")
	fmt.Printf("   ⚙️  Equipment:       GET /api/v1/mobile/equipment/building/{id}\n")
	fmt.Printf("   🗺️  Spatial:        POST /api/v1/mobile/spatial/anchors\n")

	fmt.Printf("\n🚀 ArxOS Server v2: Ready for Mobile & ARKit/ARCore Integration!\n")

	// Wait for interrupt signal
	<-quit

	fmt.Println("\n🛑 Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger := container.GetLogger()
		logger.Error("Server forced to shutdown", "error", err)
		return err
	}

	fmt.Println("✅ Server shutdown complete")
	return nil
}
