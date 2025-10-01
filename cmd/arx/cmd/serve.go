package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	// "github.com/arx-os/arxos/internal/api" // Will be implemented
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/spf13/cobra"
)

// serveCmd represents the serve command following Go Blueprint standards
var serveCmd = &cobra.Command{
	Use:   "serve",
	Short: "Start HTTP API server",
	Long:  "Start the ArxOS HTTP API server for web and mobile clients",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		port, _ := cmd.Flags().GetInt("port")

		logger.Info("Starting HTTP API server on port %d", port)

		// Start API server
		if err := startAPIServer(ctx, port); err != nil {
			logger.Error("Failed to start API server: %v", err)
			return err
		}

		fmt.Printf("✅ API server started on port %d\n", port)
		return nil
	},
}

// startAPIServer starts the HTTP API server
func startAPIServer(ctx context.Context, port int) error {
	// Get services from DI container (would be injected in real implementation)
	// services := app.GetServices()
	// if !services.Database.IsHealthy() {
	//     return fmt.Errorf("database not initialized")
	// }

	// Create web router (placeholder)
	// webRouter := api.NewWebRouter()
	logger.Info("Web router initialized")

	// Setup HTTP router
	router := chi.NewRouter()

	// Middleware
	router.Use(chimiddleware.Logger)
	router.Use(chimiddleware.Recoverer)
	router.Use(chimiddleware.RequestID)
	router.Use(chimiddleware.RealIP)
	router.Use(chimiddleware.Timeout(60 * time.Second))

	// CORS middleware for development
	router.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, HX-Request")
			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}
			next.ServeHTTP(w, r)
		})
	})

	// Register routes (placeholder)
	// webRouter.RegisterRoutes(router)
	logger.Info("Routes registered")

	// Create HTTP server
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: router,
	}

	// Start server in goroutine
	go func() {
		fmt.Printf("🌐 ArxOS Web Server starting on http://localhost:%d\n", port)
		fmt.Println()
		fmt.Println("Available endpoints:")
		fmt.Printf("  • Landing Page:    http://localhost:%d\n", port)
		fmt.Printf("  • Core Dashboard:  http://localhost:%d/core\n", port)
		fmt.Printf("  • Hardware:        http://localhost:%d/hardware\n", port)
		fmt.Printf("  • Workflow:        http://localhost:%d/workflow\n", port)
		fmt.Println()
		fmt.Println("Press Ctrl+C to stop the server")
		fmt.Println()

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Printf("❌ Server error: %v\n", err)
			os.Exit(1)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	fmt.Println("\n🛑 Shutting down server...")

	// Graceful shutdown
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		logger.Error("Server shutdown error: %v", err)
		return err
	}

	logger.Info("Server stopped gracefully")
	return nil
}

func init() {
	serveCmd.Flags().IntP("port", "p", 8080, "Port to run the server on")
}
