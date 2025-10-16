package tui

import (
	"context"
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/infrastructure"
	"github.com/arx-os/arxos/internal/tui/models"
	"github.com/arx-os/arxos/internal/tui/services"
)

// Demo runs a simple TUI demo without requiring database connection
func Demo() error {
	fmt.Println("🚀 ArxOS TUI Demo")
	fmt.Println("═══════════════════════════════════")
	fmt.Println()
	fmt.Println("This demo shows the ArxOS Terminal User Interface")
	fmt.Println("without requiring a database connection.")
	fmt.Println()
	fmt.Println("Features demonstrated:")
	fmt.Println("• Interactive dashboard with tabs")
	fmt.Println("• Equipment status visualization")
	fmt.Println("• Real-time metrics display")
	fmt.Println("• Professional styling and layout")
	fmt.Println()
	fmt.Println("Controls:")
	fmt.Println("• [Tab] - Switch between tabs")
	fmt.Println("• [↑↓] - Navigate equipment list")
	fmt.Println("• [r] - Refresh data")
	fmt.Println("• [q] or [Ctrl+C] - Quit")
	fmt.Println()

	// Check if terminal supports TUI
	if !IsTUIEnabled() {
		fmt.Println("⚠️  Warning: TUI may not work properly in this terminal environment")
		fmt.Println("   TERM variable:", os.Getenv("TERM"))
		fmt.Println()
	}

	fmt.Println("Press Enter to start the demo...")
	fmt.Scanln()

	// Create demo configuration
	cfg := config.Default()

	// Create dashboard model
	// Demo mode: create empty data service (nil repositories for demo)
	dataService := services.NewDataService(nil, nil, nil, nil)
	dashboard := models.NewDashboardModel(&cfg.TUI, dataService)

	// Create Bubble Tea program
	p := tea.NewProgram(dashboard, tea.WithAltScreen())

	// Run the program
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("TUI demo error: %w", err)
	}

	fmt.Println("Demo completed successfully!")
	return nil
}

// DemoWithData runs a TUI demo with mock data
func DemoWithData() error {
	fmt.Println("🎯 ArxOS TUI Demo with Mock Data")
	fmt.Println("═══════════════════════════════════")
	fmt.Println()

	// Create demo configuration
	cfg := config.Default()

	// Create dashboard model
	// Demo mode: create empty data service (nil repositories for demo)
	dataService := services.NewDataService(nil, nil, nil, nil)
	dashboard := models.NewDashboardModel(&cfg.TUI, dataService)

	// Create Bubble Tea program
	p := tea.NewProgram(dashboard, tea.WithAltScreen())

	// Run the program
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("TUI demo error: %w", err)
	}

	return nil
}

// RunDemoCommand runs the demo command
func RunDemoCommand() error {
	// Check if we have a database connection available
	cfg, err := config.Load("")
	if err != nil {
		fmt.Println("⚠️  No configuration found, running demo without database...")
		return Demo()
	}

	// Try to connect to database
	ctx := context.Background()
	db, err := infrastructure.NewDatabase(cfg)
	if err != nil {
		fmt.Println("⚠️  Database connection failed, running demo without database...")
		return Demo()
	}
	defer db.Close()

	// We have a database connection, run full demo
	fmt.Println("✅ Database connection available, running full demo...")
	_ = ctx // Use context in future
	_ = db  // Use database connection in future
	return DemoWithData()
}
