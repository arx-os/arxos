// CMMS Service
//
// Required environment variable:
//   DATABASE_URL - PostgreSQL DSN, e.g. "postgres://user:password@host:port/dbname?sslmode=disable"
//
// Optionally, create a .env file with DATABASE_URL for local development.

package main

import (
	"arx-cmms/internal/server"
	"arx-cmms/pkg/cmms"
	"context"
	"log"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	// Load environment variables from .env if present
	_ = godotenv.Load()

	// Database connection
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		log.Fatal("DATABASE_URL environment variable is not set. Please set it to your PostgreSQL DSN.")
	}

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	// Create CMMS client
	client := cmms.NewClient(db)

	// Start sync scheduler (commented out for testing to avoid external API calls)
	// client.StartSyncScheduler()

	// Get port from environment or use default
	port := 8080
	if portStr := os.Getenv("PORT"); portStr != "" {
		if p, err := strconv.Atoi(portStr); err == nil {
			port = p
		}
	}

	// Create and start HTTP server
	httpServer := server.NewServer(client, port)
	
	// Start server in a goroutine
	go func() {
		if err := httpServer.Start(); err != nil {
			log.Fatalf("Failed to start HTTP server: %v", err)
		}
	}()

	log.Println("🚀 CMMS Service started")

	// Wait for termination signal
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, os.Interrupt, syscall.SIGTERM)
	<-sig

	log.Println("Shutting down CMMS Service...")
	
	// Gracefully shutdown the server
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	
	if err := httpServer.Shutdown(ctx); err != nil {
		log.Printf("Error shutting down server: %v", err)
	}
}
