package main

import (
	"os"

	"github.com/arx-os/arxos/internal/cli"
	"github.com/arx-os/arxos/internal/config"
)

var (
	// Version information (set during build)
	Version   = "dev"
	BuildTime = "unknown"
	Commit    = "unknown"
)

func main() {
	// Load configuration
	cfg, err := config.Load("")
	if err != nil {
		// Fallback to default config if loading fails
		cfg = &config.Config{
			Mode: "development",
			PostGIS: config.PostGISConfig{
				Host:     "localhost",
				Port:     5432,
				Database: "arxos_db",
				User:     "arxos_user",
				Password: "arxos_password",
				SSLMode:  "disable",
			},
		}
	}

	// Create CLI application
	app := cli.NewApp(cfg)

	// Execute root command
	if err := app.Execute(); err != nil {
		os.Exit(1)
	}
}
