package ingestion

import (
	"fmt"
	"log"
)

// TestIngestionPipeline tests the complete ingestion pipeline
func TestIngestionPipeline() {
	fmt.Println("🏗️  Testing Arxos Ingestion Pipeline")
	fmt.Println("=====================================")
	
	// Create new ingestion pipeline
	pipeline := NewIngestionPipeline()
	
	// Display supported formats
	fmt.Println("\n📄 Supported File Formats:")
	formats := pipeline.GetSupportedFormats()
	for _, format := range formats {
		fmt.Printf("  • %s\n", format)
	}
	
	// Create test request
	request := PipelineRequest{
		Files: []string{
			"test_building.pdf",
			"mechanical_plans.dwg", 
			"building_model.ifc",
			"equipment_list.xlsx",
			"site_scan.las",
			"inspection_photos.jpg",
		},
		BuildingMetadata: BuildingMetadata{
			Name:         "Test Office Building",
			Address:      "123 Innovation Drive, Austin TX",
			BuildingType: "Office",
			YearBuilt:    2020,
			TotalArea:    45000.0,
			NumFloors:    3,
		},
		ProcessingOptions: ProcessingOptions{
			EnableMerging:     true,
			MinConfidence:     0.70,
			RequireValidation: true,
			CoordinateSystem:  "Building Grid",
			UnitsOfMeasure:    "Imperial",
		},
	}
	
	// Process the building
	fmt.Println("\n🔄 Processing Building Files...")
	result, err := pipeline.ProcessBuilding(request)
	if err != nil {
		log.Fatalf("Processing failed: %v", err)
	}
	
	// Display results
	fmt.Printf("\n✅ Processing Complete!")
	fmt.Printf("\n📊 Building ID: %s", result.BuildingID)
	fmt.Printf("\n⏱️  Processing Time: %v", result.ProcessingTime)
	fmt.Printf("\n🎯 Overall Confidence: %.2f", result.OverallConfidence)
	
	// Statistics
	stats := result.Statistics
	fmt.Printf("\n\n📈 Processing Statistics:")
	fmt.Printf("\n  Files Processed: %d/%d", stats.ProcessedFiles, stats.TotalFiles)
	fmt.Printf("\n  Total Objects: %d", stats.TotalObjects)
	fmt.Printf("\n  Objects by Type:")
	for objType, count := range stats.ObjectsByType {
		fmt.Printf("\n    %s: %d", objType, count)
	}
	fmt.Printf("\n  Objects by System:")
	for system, count := range stats.ObjectsBySystem {
		fmt.Printf("\n    %s: %d", system, count)
	}
	
	// Confidence statistics
	confStats := stats.ConfidenceStats
	fmt.Printf("\n\n🎯 Confidence Analysis:")
	fmt.Printf("\n  Average: %.3f", confStats.Average)
	fmt.Printf("\n  Range: %.3f - %.3f", confStats.Minimum, confStats.Maximum)
	fmt.Printf("\n  Distribution:")
	for range_, count := range confStats.Distribution {
		fmt.Printf("\n    %s: %d objects", range_, count)
	}
	
	// Validation queue
	fmt.Printf("\n\n🔍 Validation Queue: %d items", len(result.ValidationQueue))
	if len(result.ValidationQueue) > 0 {
		fmt.Printf("\n  Top Priority Items:")
		for i, item := range result.ValidationQueue {
			if i >= 3 { // Show top 3
				break
			}
			fmt.Printf("\n    • %s (%s) - Priority: %.2f", item.ObjectType, item.ObjectID, item.Priority)
		}
	}
	
	// Processing steps
	fmt.Printf("\n\n⚙️  Processing Steps:")
	for _, step := range result.ProcessingSteps {
		status := "✅"
		if !step.Success {
			status = "❌"
		}
		fmt.Printf("\n  %s %s: %s (%.2fs, %d objects)", 
			status, step.ProcessorType, step.FilePath, step.Duration.Seconds(), step.ObjectsFound)
		
		if step.Error != "" {
			fmt.Printf(" - Error: %s", step.Error)
		}
	}
	
	// Warnings
	if len(result.Warnings) > 0 {
		fmt.Printf("\n\n⚠️  Warnings:")
		for _, warning := range result.Warnings {
			fmt.Printf("\n  • %s", warning)
		}
	}
	
	// Errors  
	if len(result.Errors) > 0 {
		fmt.Printf("\n\n❌ Errors:")
		for _, error := range result.Errors {
			fmt.Printf("\n  • %s", error)
		}
	}
	
	fmt.Printf("\n\n🎉 Ingestion Pipeline Test Complete!\n")
}