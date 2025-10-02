package commands

import (
	"context"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/arx-os/arxos/internal/domain/component"
)

// ComponentServiceProvider provides access to component services
type ComponentServiceProvider interface {
	GetComponentService() component.ComponentService
}

// CreateComponentCommands creates component management commands
func CreateComponentCommands(serviceContext interface{}) *cobra.Command {
	componentCmd := &cobra.Command{
		Use:   "component",
		Short: "Manage building components",
		Long:  "Create, update, and manage universal building components",
	}

	componentCmd.AddCommand(createComponentCreateCommand(serviceContext))
	componentCmd.AddCommand(createComponentGetCommand(serviceContext))
	componentCmd.AddCommand(createComponentListCommand(serviceContext))

	return componentCmd
}

// createComponentCreateCommand creates the component create command
func createComponentCreateCommand(serviceContext interface{}) *cobra.Command {
	var (
		name     string
		compType string
		path     string
		building string
		floor    string
		room     string
		x        float64
		y        float64
		z        float64
		creator  string
	)

	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new building component",
		Long:  "Create a new universal building component with specified properties",
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			sc, ok := serviceContext.(ComponentServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			componentService := sc.GetComponentService()

			// Validate required fields
			if name == "" {
				return fmt.Errorf("component name is required")
			}
			if compType == "" {
				return fmt.Errorf("component type is required")
			}
			if path == "" {
				return fmt.Errorf("component path is required")
			}
			if creator == "" {
				return fmt.Errorf("creator is required")
			}

			// Create location
			location := component.Location{
				X:        x,
				Y:        y,
				Z:        z,
				Floor:    floor,
				Room:     room,
				Building: building,
			}

			// Create component request
			req := component.CreateComponentRequest{
				Name:      name,
				Type:      component.ComponentType(compType),
				Path:      path,
				Location:  location,
				CreatedBy: creator,
			}

			// Create component
			comp, err := componentService.CreateComponent(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to create component: %w", err)
			}

			fmt.Printf("✅ Component created successfully!\n")
			fmt.Printf("   ID: %s\n", comp.ID)
			fmt.Printf("   Name: %s\n", comp.Name)
			fmt.Printf("   Type: %s\n", comp.Type)
			fmt.Printf("   Path: %s\n", comp.Path)
			fmt.Printf("   Location: Building=%s, Floor=%s, Room=%s\n", comp.Location.Building, comp.Location.Floor, comp.Location.Room)
			fmt.Printf("   Created: %s\n", comp.CreatedAt.Format("2006-01-02 15:04:05"))

			return nil
		},
	}

	cmd.Flags().StringVar(&name, "name", "", "Component name (required)")
	cmd.Flags().StringVar(&compType, "type", "", "Component type (required)")
	cmd.Flags().StringVar(&path, "path", "", "Component path (required)")
	cmd.Flags().StringVar(&building, "building", "", "Building identifier")
	cmd.Flags().StringVar(&floor, "floor", "", "Floor identifier")
	cmd.Flags().StringVar(&room, "room", "", "Room identifier")
	cmd.Flags().Float64Var(&x, "x", 0, "X coordinate")
	cmd.Flags().Float64Var(&y, "y", 0, "Y coordinate")
	cmd.Flags().Float64Var(&z, "z", 0, "Z coordinate")
	cmd.Flags().StringVar(&creator, "creator", "", "Creator identifier (required)")

	cmd.MarkFlagRequired("name")
	cmd.MarkFlagRequired("type")
	cmd.MarkFlagRequired("path")
	cmd.MarkFlagRequired("creator")

	return cmd
}

// createComponentGetCommand creates the component get command
func createComponentGetCommand(serviceContext interface{}) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get <identifier>",
		Short: "Get a component by ID or path",
		Long:  "Retrieve a component by its ID (UUID) or path",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			sc, ok := serviceContext.(ComponentServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			componentService := sc.GetComponentService()

			identifier := args[0]

			// Get component
			comp, err := componentService.GetComponent(ctx, identifier)
			if err != nil {
				return fmt.Errorf("failed to get component: %w", err)
			}

			fmt.Printf("📋 Component Details:\n")
			fmt.Printf("   ID: %s\n", comp.ID)
			fmt.Printf("   Name: %s\n", comp.Name)
			fmt.Printf("   Type: %s\n", comp.Type)
			fmt.Printf("   Path: %s\n", comp.Path)
			fmt.Printf("   Status: %s\n", comp.Status)
			fmt.Printf("   Version: %s\n", comp.Version)
			fmt.Printf("   Location: Building=%s, Floor=%s, Room=%s\n", comp.Location.Building, comp.Location.Floor, comp.Location.Room)
			fmt.Printf("   Coordinates: (%.2f, %.2f, %.2f)\n", comp.Location.X, comp.Location.Y, comp.Location.Z)
			fmt.Printf("   Created: %s by %s\n", comp.CreatedAt.Format("2006-01-02 15:04:05"), comp.CreatedBy)
			fmt.Printf("   Updated: %s by %s\n", comp.UpdatedAt.Format("2006-01-02 15:04:05"), comp.UpdatedBy)

			if len(comp.Properties) > 0 {
				fmt.Printf("   Properties:\n")
				for key, value := range comp.Properties {
					fmt.Printf("     %s: %v\n", key, value)
				}
			}

			if len(comp.Relations) > 0 {
				fmt.Printf("   Relations:\n")
				for _, rel := range comp.Relations {
					fmt.Printf("     %s -> %s (%s)\n", rel.Type, rel.TargetPath, rel.TargetID)
				}
			}

			return nil
		},
	}

	return cmd
}

// createComponentListCommand creates the component list command
func createComponentListCommand(serviceContext interface{}) *cobra.Command {
	var (
		compType string
		status   string
		building string
		floor    string
		room     string
		limit    int
	)

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List components with optional filtering",
		Long:  "List building components with optional filtering by type, status, location, etc.",
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			sc, ok := serviceContext.(ComponentServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			componentService := sc.GetComponentService()

			// Create filter
			filter := component.ComponentFilter{
				Building: building,
				Floor:    floor,
				Room:     room,
				Limit:    limit,
			}

			// Add type filter if specified
			if compType != "" {
				compTypeEnum := component.ComponentType(compType)
				filter.Type = &compTypeEnum
			}

			// Add status filter if specified
			if status != "" {
				statusEnum := component.ComponentStatus(status)
				filter.Status = &statusEnum
			}

			// List components
			components, err := componentService.ListComponents(ctx, filter)
			if err != nil {
				return fmt.Errorf("failed to list components: %w", err)
			}

			if len(components) == 0 {
				fmt.Println("No components found matching the criteria.")
				return nil
			}

			fmt.Printf("📋 Found %d components:\n\n", len(components))
			for i, comp := range components {
				fmt.Printf("%d. %s (%s)\n", i+1, comp.Name, comp.Type)
				fmt.Printf("   ID: %s\n", comp.ID)
				fmt.Printf("   Path: %s\n", comp.Path)
				fmt.Printf("   Status: %s\n", comp.Status)
				if comp.Location.Building != "" || comp.Location.Floor != "" || comp.Location.Room != "" {
					fmt.Printf("   Location: Building=%s, Floor=%s, Room=%s\n", comp.Location.Building, comp.Location.Floor, comp.Location.Room)
				}
				fmt.Printf("   Created: %s\n", comp.CreatedAt.Format("2006-01-02 15:04:05"))
				fmt.Println()
			}

			return nil
		},
	}

	cmd.Flags().StringVar(&compType, "type", "", "Filter by component type")
	cmd.Flags().StringVar(&status, "status", "", "Filter by component status")
	cmd.Flags().StringVar(&building, "building", "", "Filter by building")
	cmd.Flags().StringVar(&floor, "floor", "", "Filter by floor")
	cmd.Flags().StringVar(&room, "room", "", "Filter by room")
	cmd.Flags().IntVar(&limit, "limit", 50, "Maximum number of components to return")

	return cmd
}
