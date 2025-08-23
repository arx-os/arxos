package wall_composition

import (
	"fmt"
	"log"
	"strings"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/wall_composition/engine"
	"github.com/arxos/arxos/core/wall_composition/integration"
	"github.com/arxos/arxos/core/wall_composition/renderer"
)

// Phase2TestRunner tests the complete Phase 2 wall composition system
func Phase2TestRunner() {
	fmt.Println("🚀 Starting Phase 2 Wall Composition System Tests")
	fmt.Println(strings.Repeat("=", 60))

	// Test 1: Engine Configuration
	testEngineConfiguration()

	// Test 2: SVG Renderer Configuration
	testSVGRendererConfiguration()

	// Test 3: Integration Adapter
	testIntegrationAdapter()

	// Test 4: End-to-End Wall Composition
	testEndToEndComposition()

	// Test 5: Performance and Statistics
	testPerformanceAndStats()

	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("✅ Phase 2 Wall Composition System Tests Completed")
}

func testEngineConfiguration() {
	fmt.Println("\n🔧 Testing Engine Configuration...")

	// Test default configuration
	config := engine.DefaultCompositionConfig()

	if config.MaxGapDistance != 50.0 {
		log.Printf("❌ Expected MaxGapDistance 50.0, got %f", config.MaxGapDistance)
	} else {
		fmt.Println("✅ Default MaxGapDistance: 50.0mm")
	}

	if config.ParallelThreshold != 5.0 {
		log.Printf("❌ Expected ParallelThreshold 5.0, got %f", config.ParallelThreshold)
	} else {
		fmt.Println("✅ Default ParallelThreshold: 5.0 degrees")
	}

	if config.ConfidenceThreshold != 0.6 {
		log.Printf("❌ Expected ConfidenceThreshold 0.6, got %f", config.ConfidenceThreshold)
	} else {
		fmt.Println("✅ Default ConfidenceThreshold: 60%")
	}

	// Test custom configuration
	customConfig := engine.CompositionConfig{
		MaxGapDistance:      100.0,
		ParallelThreshold:   10.0,
		MinWallLength:       200.0,
		MaxWallLength:       100000.0,
		ConfidenceThreshold: 0.7,
	}

	engine := engine.NewWallCompositionEngine(customConfig)
	if engine == nil {
		log.Println("❌ Failed to create engine with custom configuration")
	} else {
		fmt.Println("✅ Custom engine configuration created successfully")
	}
}

func testSVGRendererConfiguration() {
	fmt.Println("\n🎨 Testing SVG Renderer Configuration...")

	// Test default configuration
	config := renderer.DefaultRenderConfig()

	if config.Width != 297.0 {
		log.Printf("❌ Expected Width 297.0, got %f", config.Width)
	} else {
		fmt.Println("✅ Default Width: 297.0mm (A4)")
	}

	if config.Height != 210.0 {
		log.Printf("❌ Expected Height 210.0, got %f", config.Height)
	} else {
		fmt.Println("✅ Default Height: 210.0mm (A4)")
	}

	if config.Scale != 1.0 {
		log.Printf("❌ Expected Scale 1.0, got %f", config.Scale)
	} else {
		fmt.Println("✅ Default Scale: 1:1 (1 SVG unit = 1mm)")
	}

	// Test custom configuration
	customConfig := renderer.RenderConfig{
		Width:          500.0,
		Height:         300.0,
		Scale:          2.0,
		ShowConfidence: true,
		ShowDimensions: true,
		ShowMetadata:   true,
	}

	renderer := renderer.NewSVGRenderer(customConfig)
	if renderer == nil {
		log.Println("❌ Failed to create renderer with custom configuration")
	} else {
		fmt.Println("✅ Custom renderer configuration created successfully")
	}
}

func testIntegrationAdapter() {
	fmt.Println("\n🔗 Testing Integration Adapter...")

	// Test default adapter creation
	adapter := integration.NewArxObjectAdapter()
	if adapter == nil {
		log.Println("❌ Failed to create default adapter")
		return
	}
	fmt.Println("✅ Default adapter created successfully")

	// Test custom configuration adapter
	compConfig := engine.DefaultCompositionConfig()
	renderConfig := renderer.DefaultRenderConfig()

	customAdapter := integration.NewArxObjectAdapterWithConfig(compConfig, renderConfig)
	if customAdapter == nil {
		log.Println("❌ Failed to create custom configuration adapter")
	} else {
		fmt.Println("✅ Custom configuration adapter created successfully")
	}

	// Test empty ArxObject processing
	structures, err := adapter.ProcessArxObjects([]*arxobject.ArxObject{})
	if err != nil {
		log.Printf("❌ Error processing empty ArxObjects: %v", err)
	} else if len(structures) != 0 {
		log.Printf("❌ Expected 0 structures, got %d", len(structures))
	} else {
		fmt.Println("✅ Empty ArxObject processing works correctly")
	}
}

func testEndToEndComposition() {
	fmt.Println("\n🔄 Testing End-to-End Wall Composition...")

	// Create test ArxObjects
	arxObjects := createTestArxObjects()

	// Create adapter
	adapter := integration.NewArxObjectAdapter()

	// Process ArxObjects into wall structures
	structures, err := adapter.ProcessArxObjects(arxObjects)
	if err != nil {
		log.Printf("❌ Error processing ArxObjects: %v", err)
		return
	}

	fmt.Printf("✅ Created %d wall structures from %d ArxObjects\n", len(structures), len(arxObjects))

	// Render wall structures to SVG
	svg, err := adapter.RenderWallStructures(structures)
	if err != nil {
		log.Printf("❌ Error rendering wall structures: %v", err)
		return
	}

	if len(svg) == 0 {
		log.Println("❌ Generated SVG is empty")
	} else {
		fmt.Printf("✅ Generated SVG with %d characters\n", len(svg))
	}

	// Test combined process and render
	combinedSVG, err := adapter.ProcessAndRender(arxObjects)
	if err != nil {
		log.Printf("❌ Error in combined process and render: %v", err)
		return
	}

	if len(combinedSVG) == 0 {
		log.Println("❌ Combined process and render generated empty SVG")
	} else {
		fmt.Printf("✅ Combined process and render generated SVG with %d characters\n", len(combinedSVG))
	}
}

func testPerformanceAndStats() {
	fmt.Println("\n📊 Testing Performance and Statistics...")

	// Create adapter
	adapter := integration.NewArxObjectAdapter()

	// Get composition stats
	compStats := adapter.GetCompositionStats()
	fmt.Printf("✅ Composition Stats: %+v\n", compStats)

	// Get render stats
	renderStats := adapter.GetRenderStats()
	fmt.Printf("✅ Render Stats: %+v\n", renderStats)

	// Test configuration updates
	adapter.UpdateCompositionConfig(engine.CompositionConfig{
		MaxGapDistance:      75.0,
		ParallelThreshold:   7.5,
		ConfidenceThreshold: 0.65,
	})
	fmt.Println("✅ Composition configuration updated successfully")

	adapter.UpdateRenderConfig(renderer.RenderConfig{
		Width:          400.0,
		Height:         300.0,
		ShowConfidence: false,
		ShowDimensions: true,
	})
	fmt.Println("✅ Render configuration updated successfully")
}

func createTestArxObjects() []*arxobject.ArxObject {
	// Create a simple rectangular room with 4 walls
	arxObjects := []*arxobject.ArxObject{
		// North wall (horizontal)
		{
			ID:     1,
			Type:   arxobject.StructuralWall,
			X:      0,
			Y:      0,
			Z:      0,
			Length: 5000000000, // 5m
			Width:  200000000,  // 200mm
			Height: 3000000000, // 3m
		},
		// East wall (vertical)
		{
			ID:     2,
			Type:   arxobject.StructuralWall,
			X:      5000000000, // 5m
			Y:      0,
			Z:      0,
			Length: 4000000000, // 4m
			Width:  200000000,  // 200mm
			Height: 3000000000, // 3m
		},
		// South wall (horizontal)
		{
			ID:     3,
			Type:   arxobject.StructuralWall,
			X:      0,
			Y:      4000000000, // 4m
			Z:      0,
			Length: 5000000000, // 5m
			Width:  200000000,  // 200mm
			Height: 3000000000, // 3m
		},
		// West wall (vertical)
		{
			ID:     4,
			Type:   arxobject.StructuralWall,
			X:      0,
			Y:      0,
			Z:      0,
			Length: 4000000000, // 4m
			Width:  200000000,  // 200mm
			Height: 3000000000, // 3m
		},
	}

	return arxObjects
}

// RunPhase2Tests is the main entry point for running Phase 2 tests
func RunPhase2Tests() {
	Phase2TestRunner()
}
