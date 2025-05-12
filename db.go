// db/db.go
package db

import (
	"log"
	"os"
	"time"

	"arxline/models"

	"github.com/spf13/viper"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var DB *gorm.DB

// Connect initializes the database connection.
func Connect() {
	// Load environment variables
	viper.AutomaticEnv()
	dsn := viper.GetString("DATABASE_URL")
	if dsn == "" {
		log.Fatal("DATABASE_URL is not set")
	}

	// Configure GORM logger for better debugging
	newLogger := logger.New(
		log.New(os.Stdout, "\r\n", log.LstdFlags), // Output to stdout
		logger.Config{
			SlowThreshold:             time.Second, // Log queries slower than 1 second
			LogLevel:                  logger.Info, // Log all queries
			IgnoreRecordNotFoundError: true,        // Ignore "record not found" errors
			Colorful:                  true,        // Enable colorful logs
		},
	)

	// Open database connection
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: newLogger,
	})
	if err != nil {
		log.Fatalf("Failed to connect to DB: %v", err)
	}

	// Configure connection pooling
	sqlDB, err := db.DB()
	if err != nil {
		log.Fatalf("Failed to get SQL DB instance: %v", err)
	}
	sqlDB.SetMaxOpenConns(25)                 // Maximum number of open connections
	sqlDB.SetMaxIdleConns(10)                 // Maximum number of idle connections
	sqlDB.SetConnMaxLifetime(5 * time.Minute) // Maximum lifetime of a connection

	DB = db
	log.Println("✅ Database connected successfully")
}

// Migrate runs database migrations.
func Migrate() {
	if DB == nil {
		log.Fatal("Database connection is not initialized")
	}

	err := DB.AutoMigrate(
		&models.User{},
		&models.Project{},
		&models.Drawing{},
	)
	if err != nil {
		log.Fatalf("Failed to run migrations: %v", err)
	}

	log.Println("✅ Database migrations completed successfully")
}

// Close gracefully shuts down the database connection.
func Close() {
	if DB == nil {
		return
	}

	sqlDB, err := DB.DB()
	if err != nil {
		log.Printf("Failed to get SQL DB instance for closing: %v", err)
		return
	}

	err = sqlDB.Close()
	if err != nil {
		log.Printf("Failed to close database connection: %v", err)
	} else {
		log.Println("✅ Database connection closed successfully")
	}
}
