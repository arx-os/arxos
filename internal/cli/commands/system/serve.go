package system

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
	"github.com/arx-os/arxos/internal/config"
	httppkg "github.com/arx-os/arxos/internal/interfaces/http"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
)

// CreateServeCommand creates the serve command
func CreateServeCommand(serviceContext any) *cobra.Command {
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

// runServer starts the HTTP server using Clean Architecture
func runServer(host string, port int, certFile, keyFile string) error {
	fmt.Printf("🚀 Starting ArxOS HTTP server on %s:%d\n", host, port)

	// Load configuration
	cfg, err := loadConfig()
	if err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	// Create DI container and initialize all services
	container := app.NewContainer()
	ctx := context.Background()

	if err := container.Initialize(ctx, cfg); err != nil {
		return fmt.Errorf("failed to initialize container: %w", err)
	}

	logger := container.GetLogger()

	// Create server configuration
	serverConfig := types.NewServer(fmt.Sprintf("%d", port), host)

	// Create router using Clean Architecture
	routerConfig := &httppkg.RouterConfig{
		Container: container,
		Server:    serverConfig,
	}

	httpRouter := httppkg.NewRouter(routerConfig)

	logger.Info("Clean Architecture router configured successfully")

	// Create HTTP server
	srv := &http.Server{
		Addr:         fmt.Sprintf("%s:%d", host, port),
		Handler:      httpRouter,
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

// loadConfig loads the ArxOS configuration
func loadConfig() (*config.Config, error) {
	// Try to load config from file
	cfg, err := config.Load("")
	if err != nil {
		// Fallback to default development config
		cfg = &config.Config{
			Mode: "development",
			PostGIS: config.PostGISConfig{
				Host:     "localhost",
				Port:     5432,
				Database: "arxos",
				User:     "arxos",
				Password: "",
				SSLMode:  "disable",
			},
		}
	}
	return cfg, nil
}
