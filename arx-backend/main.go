package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"arx/db"
	"arx/handlers"
	"arx/services"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-redis/redis/v8"
	"github.com/joho/godotenv"
	"github.com/rs/cors"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using system environment variables")
	}

	// Initialize database
	db.Connect()
	database := db.DB
	if database == nil {
		log.Fatalf("Failed to initialize database")
	}

	// Run database migrations
	db.Migrate()

	// Initialize Redis
	redisClient := redis.NewClient(&redis.Options{
		Addr:     getEnv("REDIS_ADDR", "localhost:6379"),
		Password: getEnv("REDIS_PASSWORD", ""),
		DB:       0,
	})

	// Test Redis connection
	ctx := context.Background()
	if err := redisClient.Ping(ctx).Err(); err != nil {
		log.Fatalf("Failed to connect to Redis: %v", err)
	}

	// Initialize service registry
	registry := services.GetServiceRegistry()
	if err := registry.Initialize(database, redisClient); err != nil {
		log.Fatalf("Failed to initialize service registry: %v", err)
	}

	// Initialize handlers
	notificationHandler := handlers.NewNotificationHandler()

	// Setup router
	r := chi.NewRouter()

	// Middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Timeout(60 * time.Second))

	// CORS
	corsMiddleware := cors.New(cors.Options{
		AllowedOrigins:   []string{"*"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: true,
		MaxAge:           300,
	})
	r.Use(corsMiddleware.Handler)

	// API routes
	r.Route("/api", func(r chi.Router) {
		// Notification routes
		r.Route("/notifications", func(r chi.Router) {
			r.Route("/email", func(r chi.Router) {
				r.Post("/send", notificationHandler.SendEmailNotification)
				r.Get("/", notificationHandler.GetEmailNotifications)
				r.Get("/{id}", notificationHandler.GetEmailNotification)
				r.Get("/{id}/delivery", notificationHandler.GetEmailDeliveryHistory)
				r.Get("/statistics", notificationHandler.GetEmailStatistics)
				r.Post("/config/test", notificationHandler.TestEmailConfig)

				// Template routes
				r.Route("/templates", func(r chi.Router) {
					r.Post("/", notificationHandler.CreateEmailTemplate)
					r.Get("/", notificationHandler.GetEmailTemplates)
					r.Put("/{id}", notificationHandler.UpdateEmailTemplate)
					r.Delete("/{id}", notificationHandler.DeleteEmailTemplate)
				})

				// Config routes
				r.Route("/config", func(r chi.Router) {
					r.Get("/", notificationHandler.GetEmailConfig)
					r.Put("/", notificationHandler.UpdateEmailConfig)
				})
			})
		})
	})

	// Health check
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"healthy","timestamp":"` + time.Now().Format(time.RFC3339) + `"}`))
	})

	// Start server
	port := getEnv("PORT", "8080")
	server := &http.Server{
		Addr:         ":" + port,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown
	go func() {
		log.Printf("Starting server on port %s", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	// Shutdown services
	if err := registry.Shutdown(); err != nil {
		log.Printf("Error during service shutdown: %v", err)
	}

	// Close database connection
	db.Close()

	log.Println("Server exited")
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
