package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"gopkg.in/yaml.v2"

	"github.com/arxos/arx-backend/gateway"
)

// Config represents the main application configuration
type Config struct {
	Gateway gateway.Config `yaml:"gateway"`
}

// loadConfig loads configuration from file
func loadConfig(configPath string) (*Config, error) {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var config Config
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config file: %w", err)
	}

	return &config, nil
}

// validateConfig validates the configuration
func validateConfig(config *Config) error {
	if config.Gateway.Port <= 0 || config.Gateway.Port > 65535 {
		return fmt.Errorf("invalid port: %d", config.Gateway.Port)
	}

	if config.Gateway.Host == "" {
		return fmt.Errorf("host cannot be empty")
	}

	if len(config.Gateway.Services) == 0 {
		return fmt.Errorf("no services configured")
	}

	return nil
}

// setupGracefulShutdown sets up graceful shutdown handling
func setupGracefulShutdown(gateway *gateway.Gateway) {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		log.Printf("Received signal: %v", sig)

		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()

		if err := gateway.Stop(ctx); err != nil {
			log.Printf("Error stopping gateway: %v", err)
		}

		os.Exit(0)
	}()
}

func main() {
	// Parse command line flags
	configPath := flag.String("config", "config/gateway.yaml", "Path to configuration file")
	flag.Parse()

	// Load configuration
	config, err := loadConfig(*configPath)
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Validate configuration
	if err := validateConfig(config); err != nil {
		log.Fatalf("Invalid configuration: %v", err)
	}

	// Create gateway
	gw, err := gateway.NewGateway(&config.Gateway)
	if err != nil {
		log.Fatalf("Failed to create gateway: %v", err)
	}

	// Setup graceful shutdown
	setupGracefulShutdown(gw)

	// Start gateway
	log.Printf("Starting API Gateway on %s:%d", config.Gateway.Host, config.Gateway.Port)
	if err := gw.Start(); err != nil {
		log.Fatalf("Failed to start gateway: %v", err)
	}

	// Keep the main goroutine alive
	select {}
}
