package main

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"

	"github.com/joelpate/arxos/internal/ascii/colors"
	"github.com/joelpate/arxos/internal/output"
	"github.com/joelpate/arxos/pkg/models"
)

var colorsCmd = &cobra.Command{
	Use:   "colors",
	Short: "Enhanced 256-color terminal visualization",
	Long: `Display building floor plans with enhanced 256-color terminal support.

This command provides rich color visualization including:
- Equipment status with color coding
- Temperature heatmaps
- Energy flow visualization
- Multiple color palette modes
- Color-blind friendly options`,
}

var colorsViewCmd = &cobra.Command{
	Use:   "view [floor plan]",
	Short: "View floor plan with enhanced colors",
	Run: func(cmd *cobra.Command, args []string) {
		// Get flags
		mode, _ := cmd.Flags().GetString("mode")
		width, _ := cmd.Flags().GetInt("width")
		height, _ := cmd.Flags().GetInt("height")
		showTemp, _ := cmd.Flags().GetBool("temperature")
		showEnergy, _ := cmd.Flags().GetBool("energy")
		animate, _ := cmd.Flags().GetBool("animate")
		
		// Load floor plan
		var floorFile string
		if len(args) > 0 {
			floorFile = args[0]
			if !strings.HasSuffix(floorFile, ".json") {
				floorFile += ".json"
			}
		} else {
			plans, err := stateManager.ListFloorPlans()
			if err != nil || len(plans) == 0 {
				if jsonOutput {
					output.WriteError(jsonOutput, "colors view", fmt.Errorf("no floor plans found"))
				} else {
					fmt.Println("No floor plans found. Use 'arx import' to import a PDF first.")
				}
				os.Exit(1)
			}
			floorFile = plans[0]
		}
		
		if err := stateManager.LoadFloorPlan(floorFile); err != nil {
			if jsonOutput {
				output.WriteError(jsonOutput, "colors view", fmt.Errorf("error loading floor plan: %v", err))
			} else {
				fmt.Fprintf(os.Stderr, "Error loading floor plan: %v\n", err)
			}
			os.Exit(1)
		}
		
		plan := stateManager.GetFloorPlan()
		if plan == nil {
			if jsonOutput {
				output.WriteError(jsonOutput, "colors view", fmt.Errorf("no floor plan loaded"))
			} else {
				fmt.Println("No floor plan loaded")
			}
			os.Exit(1)
		}
		
		// Auto-detect terminal size if not specified
		if width == 0 {
			width = 120
		}
		if height == 0 {
			height = 40
		}
		
		// Create enhanced renderer
		paletteMode := colors.PaletteMode(mode)
		renderer := colors.NewEnhancedRenderer(width, height, paletteMode)
		
		if jsonOutput {
			// JSON output mode
			result := map[string]interface{}{
				"floor_plan": output.FloorPlanSummary{
					Name:      plan.Name,
					Building:  plan.Building,
					Level:     plan.Level,
					RoomCount: len(plan.Rooms),
					Equipment: len(plan.Equipment),
				},
				"color_mode": mode,
				"features": map[string]bool{
					"temperature": showTemp,
					"energy":      showEnergy,
					"animation":   animate,
				},
				"terminal_support": map[string]bool{
					"256_colors": colors.SupportsColor256(),
				},
			}
			output.WriteOutput(jsonOutput, "colors view", result)
		} else {
			// Terminal output mode
			if animate {
				runAnimatedColorView(renderer, plan, showTemp, showEnergy)
			} else {
				renderColoredView(renderer, plan, showTemp, showEnergy)
			}
		}
	},
}

var colorsPaletteCmd = &cobra.Command{
	Use:   "palette",
	Short: "Display available color palettes",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Available Color Palettes:")
		fmt.Println(strings.Repeat("─", 50))
		
		modes := []colors.PaletteMode{
			colors.ModeDefault,
			colors.ModeDark,
			colors.ModeLight,
			colors.ModeHighContrast,
			colors.ModeColorBlind,
			colors.ModeMonochrome,
		}
		
		for _, mode := range modes {
			palette := colors.NewPalette(mode)
			fmt.Printf("\n%s Mode:\n", mode)
			
			// Show sample colors
			samples := []struct {
				name  string
				color colors.Color256
			}{
				{"Background", palette.Background},
				{"Foreground", palette.Foreground},
				{"Outlet", colors.OutletOrange},
				{"Switch", colors.SwitchBlue},
				{"Panel", colors.PanelRed},
				{"Sensor", colors.SensorGreen},
				{"Normal", colors.StatusNormal},
				{"Warning", colors.StatusWarning},
				{"Failed", colors.StatusFailed},
			}
			
			for _, sample := range samples {
				// Adapt color for the palette mode
				displayColor := sample.color
				if mode == colors.ModeColorBlind && sample.name != "Background" && sample.name != "Foreground" {
					displayColor = palette.GetEquipmentColor(strings.ToLower(sample.name), "normal")
				}
				
				fmt.Printf("  %s %s\n", 
					displayColor.Format("███"),
					sample.name)
			}
		}
		
		fmt.Println("\n" + strings.Repeat("─", 50))
		fmt.Printf("Terminal supports 256 colors: %v\n", colors.SupportsColor256())
	},
}

var colorsTestCmd = &cobra.Command{
	Use:   "test",
	Short: "Test 256-color terminal support",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("256-Color Terminal Test")
		fmt.Println(strings.Repeat("═", 80))
		
		// Test system colors (0-15)
		fmt.Println("\nSystem Colors (0-15):")
		for i := 0; i < 16; i++ {
			color := colors.Color256(i)
			fmt.Print(color.Format("██"))
			if (i+1)%8 == 0 {
				fmt.Println()
			}
		}
		
		// Test color cube (16-231)
		fmt.Println("\n\n216-Color Cube (16-231):")
		for green := 0; green < 6; green++ {
			for red := 0; red < 6; red++ {
				for blue := 0; blue < 6; blue++ {
					idx := 16 + red*36 + green*6 + blue
					color := colors.Color256(idx)
					fmt.Print(color.Format("█"))
				}
				fmt.Print(" ")
			}
			fmt.Println()
		}
		
		// Test grayscale (232-255)
		fmt.Println("\nGrayscale (232-255):")
		for i := 232; i < 256; i++ {
			color := colors.Color256(i)
			fmt.Print(color.Format("██"))
		}
		fmt.Println()
		
		// Test gradients
		fmt.Println("\n\nColor Gradients:")
		
		// Energy gradient
		fmt.Print("Energy:      ")
		energyGradient := colors.Gradient(colors.EnergyLow, colors.EnergyOverload, 40)
		for _, color := range energyGradient {
			fmt.Print(color.Format("█"))
		}
		fmt.Println()
		
		// Temperature gradient
		fmt.Print("Temperature: ")
		tempGradient := colors.Gradient(colors.TempCold, colors.TempCritical, 40)
		for _, color := range tempGradient {
			fmt.Print(color.Format("█"))
		}
		fmt.Println()
		
		fmt.Println("\n" + strings.Repeat("═", 80))
	},
}

func renderColoredView(renderer *colors.EnhancedRenderer, plan *models.FloorPlan, showTemp, showEnergy bool) {
	// Clear screen
	fmt.Print("\033[H\033[2J")
	
	// Render the floor plan
	renderer.RenderFloorPlan(plan)
	
	// Add temperature overlay if requested
	if showTemp {
		// Generate mock temperature data for demo
		temps := generateMockTemperatureData(renderer.Width, renderer.Height)
		renderer.DrawTemperatureMap(temps)
	}
	
	// Add energy flow if requested
	if showEnergy {
		// Generate mock energy paths for demo
		for i, equip := range plan.Equipment {
			if equip.Type == "outlet" && i < len(plan.Equipment)-1 {
				path := []models.Point{
					equip.Location,
					plan.Equipment[i+1].Location,
				}
				renderer.DrawEnergyFlow(path, 0.7, 0)
			}
		}
	}
	
	// Output to terminal
	fmt.Print(renderer.Render())
	
	// Show info
	fmt.Println("\n" + strings.Repeat("─", 80))
	fmt.Printf("Enhanced Color View - %s\n", plan.Name)
	fmt.Printf("256-Color Support: %v\n", colors.SupportsColor256())
	fmt.Println("Features: Temperature=" + fmt.Sprint(showTemp) + " Energy=" + fmt.Sprint(showEnergy))
}

func runAnimatedColorView(renderer *colors.EnhancedRenderer, plan *models.FloorPlan, showTemp, showEnergy bool) {
	fmt.Println("Animated view not yet implemented. Showing static view instead.")
	renderColoredView(renderer, plan, showTemp, showEnergy)
}

func generateMockTemperatureData(width, height int) [][]float64 {
	temps := make([][]float64, height)
	for y := range temps {
		temps[y] = make([]float64, width)
		for x := range temps[y] {
			// Generate gradient from cold to hot
			temps[y][x] = 15.0 + float64(x+y)*0.3
		}
	}
	return temps
}

func init() {
	// View command flags
	colorsViewCmd.Flags().StringP("mode", "m", "default", "Color palette mode (default, dark, light, high_contrast, color_blind, monochrome)")
	colorsViewCmd.Flags().Int("width", 0, "Display width (auto-detect if 0)")
	colorsViewCmd.Flags().Int("height", 0, "Display height (auto-detect if 0)")
	colorsViewCmd.Flags().Bool("temperature", false, "Show temperature heatmap overlay")
	colorsViewCmd.Flags().Bool("energy", false, "Show energy flow visualization")
	colorsViewCmd.Flags().Bool("animate", false, "Enable animation effects")
	
	// Add subcommands
	colorsCmd.AddCommand(colorsViewCmd)
	colorsCmd.AddCommand(colorsPaletteCmd)
	colorsCmd.AddCommand(colorsTestCmd)
	
	// Add to root
	rootCmd.AddCommand(colorsCmd)
}