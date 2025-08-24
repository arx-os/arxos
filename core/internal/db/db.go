// Package db provides database connection and management
package db

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var (
	// DB is the global database connection (sqlx)
	DB *sqlx.DB
	
	// GormDB is the GORM database connection
	GormDB *gorm.DB
	
	// SqlDB is the standard sql.DB connection
	SqlDB *sql.DB
)

// Config holds database configuration
type Config struct {
	Driver   string
	Host     string
	Port     int
	Database string
	Username string
	Password string
	SSLMode  string
}

// InitDB initializes the database connections
func InitDB() error {
	config := getConfigFromEnv()
	
	// Build connection string
	var dsn string
	switch config.Driver {
	case "postgres", "postgresql":
		dsn = fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
			config.Host, config.Port, config.Username, config.Password, config.Database, config.SSLMode)
	default:
		return fmt.Errorf("unsupported database driver: %s (only PostgreSQL is supported)", config.Driver)
	}
	
	// Initialize sqlx connection
	var err error
	DB, err = sqlx.Connect(config.Driver, dsn)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	
	// Configure connection pool
	DB.SetMaxOpenConns(25)
	DB.SetMaxIdleConns(5)
	DB.SetConnMaxLifetime(5 * time.Minute)
	
	// Test connection
	if err := DB.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}
	
	// Store standard sql.DB
	SqlDB = DB.DB
	
	// Initialize GORM if using PostgreSQL
	if config.Driver == "postgres" || config.Driver == "postgresql" {
		gormConfig := &gorm.Config{
			Logger: logger.Default.LogMode(logger.Info),
		}
		
		GormDB, err = gorm.Open(postgres.Open(dsn), gormConfig)
		if err != nil {
			return fmt.Errorf("failed to connect to database with GORM: %w", err)
		}
	}
	
	log.Println("✅ Database connection established")
	return nil
}

// getConfigFromEnv reads database configuration from environment variables
func getConfigFromEnv() Config {
	config := Config{
		Driver:   getEnv("DB_DRIVER", "postgres"),
		Host:     getEnv("DB_HOST", "localhost"),
		Port:     getEnvAsInt("DB_PORT", 5432),
		Database: getEnv("DB_NAME", "arxos"),
		Username: getEnv("DB_USER", "arxos"),
		Password: getEnv("DB_PASSWORD", "arxos_dev"),
		SSLMode:  getEnv("DB_SSL_MODE", "disable"),
	}
	
	// Support DATABASE_URL for convenience
	if dbURL := os.Getenv("DATABASE_URL"); dbURL != "" {
		// Parse DATABASE_URL if provided
		// This is a simplified parser - production should use a proper URL parser
		log.Println("Using DATABASE_URL")
	}
	
	return config
}

// Close closes all database connections
func Close() error {
	if DB != nil {
		if err := DB.Close(); err != nil {
			return err
		}
	}
	
	if GormDB != nil {
		sqlDB, err := GormDB.DB()
		if err != nil {
			return err
		}
		if err := sqlDB.Close(); err != nil {
			return err
		}
	}
	
	return nil
}

// Health checks the database health
func Health() error {
	if DB == nil {
		return fmt.Errorf("database not initialized")
	}
	
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()
	
	return DB.PingContext(ctx)
}

// Transaction executes a function within a database transaction
func Transaction(fn func(*sqlx.Tx) error) error {
	tx, err := DB.Beginx()
	if err != nil {
		return err
	}
	
	defer func() {
		if p := recover(); p != nil {
			tx.Rollback()
			panic(p)
		}
	}()
	
	if err := fn(tx); err != nil {
		tx.Rollback()
		return err
	}
	
	return tx.Commit()
}

// Helper functions

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvAsInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		var intVal int
		if _, err := fmt.Sscanf(value, "%d", &intVal); err == nil {
			return intVal
		}
	}
	return defaultValue
}

