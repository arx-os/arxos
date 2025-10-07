package commands

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/arx-os/arxos/internal/config"
	"github.com/spf13/cobra"
)

// CreateConfigCommand creates the config command group
func CreateConfigCommand(serviceContext any) *cobra.Command {
	configCmd := &cobra.Command{
		Use:   "config",
		Short: "Configuration management commands",
		Long:  "Manage ArxOS configuration files, templates, and validation",
	}

	// Add subcommands
	configCmd.AddCommand(createConfigValidateCommand())
	configCmd.AddCommand(createConfigLoadCommand())
	configCmd.AddCommand(createConfigSaveCommand())
	configCmd.AddCommand(createConfigTemplateCommand())
	configCmd.AddCommand(createConfigMigrateCommand())
	configCmd.AddCommand(createConfigServicesCommand())

	return configCmd
}

// createConfigValidateCommand creates the config validate command
func createConfigValidateCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "validate [config-path]",
		Short: "Validate configuration file",
		Long: `Validate an ArxOS configuration file for correctness.

Examples:
  arx config validate                    # Validate default config
  arx config validate configs/environments/development.yml`,
		RunE: func(_ *cobra.Command, args []string) error {
			configPath := ""
			if len(args) > 0 {
				configPath = args[0]
			} else {
				configPath = config.GetConfigPath()
			}

			fmt.Printf("🔍 Validating configuration: %s\n", configPath)

			cfg, err := config.Load(configPath)
			if err != nil {
				return fmt.Errorf("failed to load config: %w", err)
			}

			if err := cfg.Validate(); err != nil {
				return fmt.Errorf("configuration validation failed: %w", err)
			}

			fmt.Println("✅ Configuration is valid!")
			return nil
		},
	}
}

// createConfigLoadCommand creates the config load command
func createConfigLoadCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "load [config-path]",
		Short: "Load and display configuration",
		Long: `Load an ArxOS configuration file and display its contents.

Examples:
  arx config load                        # Load default config
  arx config load configs/environments/production.yml`,
		RunE: func(_ *cobra.Command, args []string) error {
			configPath := ""
			if len(args) > 0 {
				configPath = args[0]
			} else {
				configPath = config.GetConfigPath()
			}

			fmt.Printf("📁 Loading configuration: %s\n", configPath)

			cfg, err := config.Load(configPath)
			if err != nil {
				return fmt.Errorf("failed to load config: %w", err)
			}

			// Display key configuration information
			fmt.Printf("Mode: %s\n", cfg.Mode)
			fmt.Printf("Version: %s\n", cfg.Version)
			fmt.Printf("State Directory: %s\n", cfg.StateDir)
			fmt.Printf("Cache Directory: %s\n", cfg.CacheDir)
			fmt.Printf("Database Type: %s\n", cfg.Database.Type)
			fmt.Printf("PostGIS Host: %s:%d\n", cfg.PostGIS.Host, cfg.PostGIS.Port)
			fmt.Printf("Cloud Enabled: %t\n", cfg.IsCloudEnabled())
			fmt.Printf("Offline Mode: %t\n", cfg.IsOfflineMode())

			return nil
		},
	}
}

// createConfigSaveCommand creates the config save command
func createConfigSaveCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "save [output-path]",
		Short: "Save current configuration to file",
		Long: `Save the current configuration (with defaults and environment overrides) to a file.

Examples:
  arx config save                        # Save to default location
  arx config save my-config.yml         # Save to specific file`,
		RunE: func(_ *cobra.Command, args []string) error {
			outputPath := ""
			if len(args) > 0 {
				outputPath = args[0]
			} else {
				outputPath = config.GetConfigPath()
			}

			fmt.Printf("💾 Saving configuration to: %s\n", outputPath)

			// Load current config with all overrides
			cfg, err := config.Load("")
			if err != nil {
				return fmt.Errorf("failed to load current config: %w", err)
			}

			if err := cfg.Save(outputPath); err != nil {
				return fmt.Errorf("failed to save config: %w", err)
			}

			fmt.Printf("✅ Configuration saved to %s\n", outputPath)
			return nil
		},
	}
}

// createConfigTemplateCommand creates the config template command
func createConfigTemplateCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "template [environment] [output-path]",
		Short: "Generate configuration template",
		Long: `Generate a configuration template for a specific environment.

Examples:
  arx config template development        # Generate development template
  arx config template production prod.yml # Generate production template to specific file`,
		RunE: func(_ *cobra.Command, args []string) error {
			if len(args) == 0 {
				return fmt.Errorf("environment is required (development, production, test)")
			}

			environment := args[0]
			outputPath := ""
			if len(args) > 1 {
				outputPath = args[1]
			} else {
				outputPath = fmt.Sprintf("configs/environments/%s.yml", environment)
			}

			// Check if template exists
			templatePath := fmt.Sprintf("configs/environments/%s.yml", environment)
			if _, err := os.Stat(templatePath); os.IsNotExist(err) {
				return fmt.Errorf("template not found: %s", templatePath)
			}

			// Create output directory if it doesn't exist
			if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
				return fmt.Errorf("failed to create output directory: %w", err)
			}

			// Copy template to output path
			if err := copyFile(templatePath, outputPath); err != nil {
				return fmt.Errorf("failed to copy template: %w", err)
			}

			fmt.Printf("✅ Generated %s template at %s\n", environment, outputPath)
			fmt.Printf("  cp %s configs/my-config.yml # Copy to use\n", templatePath)
			return nil
		},
	}
}

// createConfigMigrateCommand creates the config migrate command
func createConfigMigrateCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "migrate [old-path] [new-path]",
		Short: "Migrate legacy configuration files to new format",
		Long: `Migrate legacy configuration files to the new ArxOS configuration format.

Examples:
  arx config migrate                    # Migrate all config files
  arx config migrate old.yml new.yml   # Migrate specific file`,
		RunE: func(_ *cobra.Command, args []string) error {
			if len(args) == 0 {
				// Migrate all configurations
				fmt.Println("🔄 Migrating all configuration files...")
				migrator := config.NewConfigMigrator("configs")
				results, err := migrator.MigrateAllConfigs()
				if err != nil {
					return fmt.Errorf("failed to migrate configs: %w", err)
				}

				successCount := 0
				for _, result := range results {
					if result.Success {
						successCount++
						fmt.Printf("✅ Migrated: %s -> %s\n", result.SourcePath, result.TargetPath)
						for _, change := range result.Changes {
							fmt.Printf("   - %s\n", change)
						}
					} else {
						fmt.Printf("❌ Failed: %s - %v\n", result.SourcePath, result.Error)
					}
				}

				fmt.Printf("✅ Migration completed: %d/%d files migrated successfully\n", successCount, len(results))
				return nil
			}

			if len(args) != 2 {
				return fmt.Errorf("migrate requires either no arguments or exactly 2 arguments")
			}

			oldPath := args[0]
			newPath := args[1]

			fmt.Printf("🔄 Migrating %s to %s...\n", oldPath, newPath)
			migrator := config.NewConfigMigrator("configs")
			result, err := migrator.MigrateConfig(oldPath, newPath)
			if err != nil {
				return fmt.Errorf("failed to migrate config: %w", err)
			}

			if result.Success {
				fmt.Printf("✅ Successfully migrated %s to %s\n", oldPath, newPath)
				for _, change := range result.Changes {
					fmt.Printf("   - %s\n", change)
				}
			} else {
				return fmt.Errorf("migration failed: %v", result.Error)
			}

			return nil
		},
	}
}

// createConfigServicesCommand creates the config services command
func createConfigServicesCommand() *cobra.Command {
	servicesCmd := &cobra.Command{
		Use:   "services",
		Short: "Manage service configurations",
		Long:  "List, load, and manage service-specific configurations",
	}

	servicesCmd.AddCommand(createConfigServicesListCommand())
	servicesCmd.AddCommand(createConfigServicesLoadCommand())

	return servicesCmd
}

// createConfigServicesListCommand creates the config services list command
func createConfigServicesListCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List available service configurations",
		Long:  "List all available service configuration files",
		RunE: func(_ *cobra.Command, args []string) error {
			serviceLoader := config.NewServiceConfigLoader("configs")
			services, err := serviceLoader.ListAvailableServices()
			if err != nil {
				return fmt.Errorf("failed to list services: %w", err)
			}

			if len(services) == 0 {
				fmt.Println("No service configurations found in configs/services/")
				return nil
			}

			fmt.Println("Available service configurations:")
			for _, service := range services {
				fmt.Printf("  - %s\n", service)
			}

			return nil
		},
	}
}

// createConfigServicesLoadCommand creates the config services load command
func createConfigServicesLoadCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "load [service-name]",
		Short: "Load and display service configuration",
		Long:  "Load and display a specific service configuration",
		RunE: func(_ *cobra.Command, args []string) error {
			if len(args) == 0 {
				return fmt.Errorf("service name is required")
			}

			serviceName := args[0]
			serviceLoader := config.NewServiceConfigLoader("configs")

			serviceConfig, err := serviceLoader.LoadServiceConfig(serviceName)
			if err != nil {
				return fmt.Errorf("failed to load service config %s: %w", serviceName, err)
			}

			fmt.Printf("Service configuration for %s:\n", serviceName)
			for key, value := range serviceConfig {
				fmt.Printf("  %s: %v\n", key, value)
			}

			return nil
		},
	}
}

// copyFile copies a file from src to dst
func copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	destFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer destFile.Close()

	_, err = destFile.ReadFrom(sourceFile)
	return err
}
