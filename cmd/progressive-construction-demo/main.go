// Progressive Construction Pipeline Demo
// Demonstrates the complete PDF → Measurements → LiDAR → 3D workflow
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"
)

func main() {
	fmt.Println("ArxOS Progressive Construction Pipeline Demo")
	fmt.Println("==========================================")
	fmt.Println()

	// Demo configuration
	config := &PipelineConfig{
		EnableLiDARFusion:   true,
		RequiredAccuracy:    1.0, // 1mm accuracy requirement
		ConfidenceThreshold: 0.75,
		Generate3DMesh:      true,
		GenerateASCII:       true,
		ValidateAgainstCode: true,
		TempDirectory:       "./temp",
		OutputDirectory:     "./output",
	}

	// Create output directories
	if err := os.MkdirAll(config.TempDirectory, 0755); err != nil {
		log.Fatal("Failed to create temp directory:", err)
	}
	if err := os.MkdirAll(config.OutputDirectory, 0755); err != nil {
		log.Fatal("Failed to create output directory:", err)
	}

	// Initialize pipeline
	pipeline := NewProgressiveConstructionPipeline(config)
	
	// Set progress callback to show real-time progress
	pipeline.SetProgressCallback(func(stage string, progress float64, message string) {
		fmt.Printf("[%s] %.1f%% - %s\n", stage, progress*100, message)
	})

	// Demo parameters
	samplePDFPath := "./demo/sample-floorplan.pdf"
	buildingID := "demo-building-001"

	fmt.Printf("Processing: %s\n", samplePDFPath)
	fmt.Printf("Building ID: %s\n", buildingID)
	fmt.Println()

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	// Process PDF through the complete pipeline
	fmt.Println("Starting Progressive Construction Pipeline...")
	fmt.Println()

	result, err := pipeline.ProcessPDF(ctx, samplePDFPath, buildingID)
	if err != nil {
		log.Fatal("Pipeline processing failed:", err)
	}

	// Display results
	displayResults(result)

	// Save detailed results
	if err := saveResults(result, config.OutputDirectory); err != nil {
		log.Printf("Warning: Failed to save detailed results: %v", err)
	}

	fmt.Println()
	fmt.Println("Demo completed successfully!")
	fmt.Printf("Total processing time: %v\n", result.ProcessingTime)
	fmt.Printf("Generated files in: %s\n", config.OutputDirectory)
}

func displayResults(result *ProcessingResult) {
	fmt.Println()
	fmt.Println("Pipeline Results Summary")
	fmt.Println("========================")
	
	fmt.Printf("Processing Time: %v\n", result.ProcessingTime)
	fmt.Printf("Total Objects Created: %d\n", len(result.ArxObjects))
	fmt.Printf("Overall Confidence: %.2f\n", result.OverallConfidence)
	
	if result.MeshFile != "" {
		fmt.Printf("3D Mesh Generated: %s\n", result.MeshFile)
	}
	
	fmt.Println()
	fmt.Println("Stage Results:")
	fmt.Println("--------------")
	
	for stageName, stageResult := range result.StageResults {
		status := "✓"
		if !stageResult.Success {
			status = "✗"
		}
		
		fmt.Printf("%s %s: %d objects, %.2f confidence, %v processing time\n",
			status, stageName, stageResult.ObjectsCreated, stageResult.Confidence, stageResult.ProcessingTime)
	}
	
	if len(result.ValidationErrors) > 0 {
		fmt.Println()
		fmt.Println("Validation Issues:")
		fmt.Println("------------------")
		
		for _, valErr := range result.ValidationErrors {
			severity := "ℹ"
			switch valErr.Severity {
			case "error":
				severity = "✗"
			case "warning":
				severity = "⚠"
			}
			
			fmt.Printf("%s %s: %s\n", severity, valErr.Type, valErr.Description)
		}
	}
	
	fmt.Println()
	fmt.Println("Object Types Created:")
	fmt.Println("--------------------")
	
	objectCounts := make(map[string]int)
	for _, obj := range result.ArxObjects {
		objectCounts[string(obj.Type)]++
	}
	
	for objType, count := range objectCounts {
		fmt.Printf("  %s: %d\n", objType, count)
	}
	
	if result.ASCIIPreview != "" {
		fmt.Println()
		fmt.Println("ASCII Preview:")
		fmt.Println("--------------")
		fmt.Println(result.ASCIIPreview)
	}
}

func saveResults(result *ProcessingResult, outputDir string) error {
	// Save detailed JSON results
	jsonData, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal results: %w", err)
	}
	
	resultFile := filepath.Join(outputDir, "pipeline-results.json")
	if err := os.WriteFile(resultFile, jsonData, 0644); err != nil {
		return fmt.Errorf("failed to write results file: %w", err)
	}
	
	fmt.Printf("Detailed results saved to: %s\n", resultFile)
	
	// Save individual ArxObjects
	objectsDir := filepath.Join(outputDir, "arxobjects")
	if err := os.MkdirAll(objectsDir, 0755); err != nil {
		return fmt.Errorf("failed to create objects directory: %w", err)
	}
	
	for i, obj := range result.ArxObjects {
		objData, err := json.MarshalIndent(obj, "", "  ")
		if err != nil {
			continue
		}
		
		objFile := filepath.Join(objectsDir, fmt.Sprintf("object_%d_%s.json", i+1, obj.Type))
		os.WriteFile(objFile, objData, 0644)
	}
	
	fmt.Printf("Individual objects saved to: %s\n", objectsDir)
	
	return nil
}