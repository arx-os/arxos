// CMMS Service
//
// Required environment variable:
//   DATABASE_URL - PostgreSQL DSN, e.g. "postgres://user:password@host:port/dbname?sslmode=disable"
//
// Optionally, create a .env file with DATABASE_URL for local development.

package main

import (
	"arx-cmms/pkg/cmms"
	"log"
	"os"
	"os/signal"
	"syscall"

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

	// Start sync scheduler
	client.StartSyncScheduler()

	log.Println("🚀 CMMS Service started")

	// Wait for termination signal
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, os.Interrupt, syscall.SIGTERM)
	<-sig

	log.Println("Shutting down CMMS Service...")
}
