package main

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/spf13/cobra"
)

var migrateCmd = &cobra.Command{
	Use:   "migrate",
	Short: "Database migration commands",
	Long:  "Commands for managing database migrations",
}

var migrateUpCmd = &cobra.Command{
	Use:   "up",
	Short: "Apply all pending migrations",
	Long:  "Apply all pending migrations to the database",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()

		logger.Info("Applying database migrations...")

		// Get database connection
		dbConn, err := getDatabaseConnection(ctx)
		if err != nil {
			logger.Error("Failed to connect to database: %v", err)
			os.Exit(1)
		}
		defer dbConn.Close()

		// Apply migrations
		if err := dbConn.Migrate(ctx); err != nil {
			logger.Error("Migration failed: %v", err)
			os.Exit(1)
		}

		fmt.Println("✅ Migrations applied successfully")
	},
}

var migrateDownCmd = &cobra.Command{
	Use:   "down",
	Short: "Rollback the last migration",
	Long:  "Rollback the most recently applied migration",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()

		logger.Info("Rolling back last migration...")

		// Get database connection
		dbConn, err := getDatabaseConnection(ctx)
		if err != nil {
			logger.Error("Failed to connect to database: %v", err)
			os.Exit(1)
		}
		defer dbConn.Close()

		// Get migrator
		migrationsDir := os.Getenv("ARXOS_MIGRATIONS_DIR")
		if migrationsDir == "" {
			migrationsDir = "migrations"
		}

		migrator := database.NewMigrator(dbConn.(*database.PostGISDB).GetDB(), migrationsDir)

		// Load migrations
		if err := migrator.LoadMigrations(); err != nil {
			logger.Error("Failed to load migrations: %v", err)
			os.Exit(1)
		}

		// Rollback
		if err := migrator.Rollback(ctx); err != nil {
			logger.Error("Rollback failed: %v", err)
			os.Exit(1)
		}

		fmt.Println("✅ Migration rolled back successfully")
	},
}

var migrateStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show migration status",
	Long:  "Show the status of all migrations",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()

		// Get database connection
		dbConn, err := getDatabaseConnection(ctx)
		if err != nil {
			logger.Error("Failed to connect to database: %v", err)
			os.Exit(1)
		}
		defer dbConn.Close()

		// Get migrator
		migrationsDir := os.Getenv("ARXOS_MIGRATIONS_DIR")
		if migrationsDir == "" {
			migrationsDir = "migrations"
		}

		migrator := database.NewMigrator(dbConn.(*database.PostGISDB).GetDB(), migrationsDir)

		// Load migrations
		if err := migrator.LoadMigrations(); err != nil {
			logger.Error("Failed to load migrations: %v", err)
			os.Exit(1)
		}

		// Get status
		status, err := migrator.GetMigrationStatus(ctx)
		if err != nil {
			logger.Error("Failed to get migration status: %v", err)
			os.Exit(1)
		}

		// Display status
		fmt.Println("Migration Status:")
		fmt.Println("=================")
		for _, s := range status {
			statusStr := "❌ Pending"
			if s.Applied {
				statusStr = "✅ Applied"
				if s.AppliedAt != nil {
					statusStr += fmt.Sprintf(" (%s)", s.AppliedAt.Format("2006-01-02 15:04:05"))
				}
			}
			fmt.Printf("%3d: %-50s %s\n", s.Version, s.Description, statusStr)
		}
	},
}

var migrateCreateCmd = &cobra.Command{
	Use:   "create [name]",
	Short: "Create a new migration",
	Long:  "Create a new migration file with the given name",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		name := args[0]

		// Get migrations directory
		migrationsDir := os.Getenv("ARXOS_MIGRATIONS_DIR")
		if migrationsDir == "" {
			migrationsDir = "migrations"
		}

		// Create migrations directory if it doesn't exist
		if err := os.MkdirAll(migrationsDir, 0755); err != nil {
			logger.Error("Failed to create migrations directory: %v", err)
			os.Exit(1)
		}

		// Get next version number
		files, err := os.ReadDir(migrationsDir)
		if err != nil {
			logger.Error("Failed to read migrations directory: %v", err)
			os.Exit(1)
		}

		nextVersion := 1
		for _, file := range files {
			if !file.IsDir() && (file.Name()[0] >= '0' && file.Name()[0] <= '9') {
				version, err := strconv.Atoi(file.Name()[:3])
				if err == nil && version >= nextVersion {
					nextVersion = version + 1
				}
			}
		}

		// Create migration files
		versionStr := fmt.Sprintf("%03d", nextVersion)
		upFile := fmt.Sprintf("%s/%s_%s.up.sql", migrationsDir, versionStr, name)
		downFile := fmt.Sprintf("%s/%s_%s.down.sql", migrationsDir, versionStr, name)

		// Create up migration
		upContent := fmt.Sprintf(`-- Migration: %s
-- Version: %s
-- Created: %s

-- Add your migration SQL here
`, name, versionStr, time.Now().Format("2006-01-02 15:04:05"))

		if err := os.WriteFile(upFile, []byte(upContent), 0644); err != nil {
			logger.Error("Failed to create up migration file: %v", err)
			os.Exit(1)
		}

		// Create down migration
		downContent := fmt.Sprintf(`-- Rollback: %s
-- Version: %s
-- Created: %s

-- Add your rollback SQL here
`, name, versionStr, time.Now().Format("2006-01-02 15:04:05"))

		if err := os.WriteFile(downFile, []byte(downContent), 0644); err != nil {
			logger.Error("Failed to create down migration file: %v", err)
			os.Exit(1)
		}

		fmt.Printf("✅ Created migration %s\n", versionStr)
		fmt.Printf("   Up:   %s\n", upFile)
		fmt.Printf("   Down: %s\n", downFile)
	},
}

// getDatabaseConnection creates a database connection
func getDatabaseConnection(ctx context.Context) (database.DB, error) {
	// Use the same database connection logic as main.go
	config := database.PostGISConfig{
		Host:     "localhost",
		Port:     5432,
		Database: "arxos",
		User:     "arxos",
		Password: "arxos",
		SSLMode:  "disable",
	}

	postgisDB := database.NewPostGISDB(config)
	if err := postgisDB.Connect(ctx, ""); err != nil {
		return nil, err
	}

	return postgisDB, nil
}

func init() {
	migrateCmd.AddCommand(migrateUpCmd)
	migrateCmd.AddCommand(migrateDownCmd)
	migrateCmd.AddCommand(migrateStatusCmd)
	migrateCmd.AddCommand(migrateCreateCmd)
}
