// PDF Parser CLI - extracts building layouts from architectural PDFs
package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/arxos/arxos/internal/types"
	"github.com/arxos/arxos/pkg/building"
	"github.com/arxos/arxos/pkg/idf"
	"github.com/arxos/arxos/pkg/image"
	"github.com/arxos/arxos/pkg/pdf"
)

func main() {
	// Command line flags
	var (
		inputFile  = flag.String("input", "", "Input PDF file path (required)")
		outputFormat = flag.String("format", "ascii", "Output format: ascii, json, stats")
		debug      = flag.Bool("debug", false, "Enable debug output")
		textMode   = flag.String("text-mode", "comprehensive", "Text extraction mode: comprehensive, basic, hybrid")
		edgeThresh = flag.Float64("edge-threshold", 25.0, "Edge detection threshold")
		minRoom    = flag.Int("min-room-size", 50, "Minimum room size")
		maxRoom    = flag.Int("max-room-size", 1000, "Maximum room size")
		scale      = flag.Float64("scale", 25.0, "Render scale factor")
	)
	
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [options]\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "\nExtracts building layouts from architectural PDF files.\n\n")
		fmt.Fprintf(os.Stderr, "Options:\n")
		flag.PrintDefaults()
		fmt.Fprintf(os.Stderr, "\nExamples:\n")
		fmt.Fprintf(os.Stderr, "  %s -input floorplan.pdf\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "  %s -input floorplan.pdf -format json -debug\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "  %s -input floorplan.pdf -text-mode basic -edge-threshold 30\n", os.Args[0])
	}
	
	flag.Parse()

	// Validate required arguments
	if *inputFile == "" {
		fmt.Fprintf(os.Stderr, "Error: -input flag is required\n\n")
		flag.Usage()
		os.Exit(1)
	}

	// Check if input file exists
	if _, err := os.Stat(*inputFile); os.IsNotExist(err) {
		log.Fatalf("Error: Input file does not exist: %s", *inputFile)
	}

	// Create configuration
	config := &types.ParseConfig{
		EdgeDetectionThreshold: *edgeThresh,
		MinRoomSize:           *minRoom,
		MaxRoomSize:           *maxRoom,
		TextExtractionMode:    *textMode,
		RenderScale:           *scale,
		Debug:                 *debug,
	}

	// Start timing
	startTime := time.Now()

	// Process the PDF
	result, err := processPDF(*inputFile, config)
	if err != nil {
		log.Fatalf("Error processing PDF: %v", err)
	}

	// Calculate processing time
	processingTime := time.Since(startTime)
	result.Stats.ProcessingTimeMS = processingTime.Milliseconds()

	// Output results based on format
	if err := outputResults(result, *outputFormat); err != nil {
		log.Fatalf("Error outputting results: %v", err)
	}

	// Print processing summary if debug enabled
	if *debug {
		printProcessingSummary(result, processingTime)
	}
}

// processPDF processes a PDF file and returns the complete parsing result
func processPDF(inputFile string, config *types.ParseConfig) (*types.ParseResult, error) {
	result := &types.ParseResult{
		Config:   config,
		Stats:    types.ParseStats{},
		Errors:   []error{},
		Warnings: []string{},
	}

	if config.Debug {
		fmt.Printf("Processing PDF: %s\n", inputFile)
		fmt.Printf("Configuration: %+v\n", config)
	}

	// Step 1: Parse PDF
	parser := pdf.NewParserWithConfig(config)
	doc, err := parser.ParseFile(inputFile)
	if err != nil {
		return nil, fmt.Errorf("failed to parse PDF: %w", err)
	}
	result.Document = doc
	result.Stats.ObjectsProcessed = len(doc.Objects)

	if config.Debug {
		fmt.Printf("Parsed %d PDF objects\n", len(doc.Objects))
	}

	// Step 2: Extract text
	textExtractor := pdf.NewTextExtractorWithConfig(config)
	text, err := textExtractor.ExtractText(doc)
	if err != nil {
		result.Warnings = append(result.Warnings, fmt.Sprintf("Text extraction warning: %v", err))
		text = "" // Continue with empty text
	}
	doc.Text = text
	result.Stats.TextCharacters = len(text)

	if config.Debug {
		fmt.Printf("Extracted %d characters of text\n", len(text))
	}

	// Step 3: Process images
	imageProcessor := image.NewProcessorWithConfig(config)
	processedImages := []*types.ProcessedImage{}
	
	for _, img := range doc.Images {
		processedImg, err := imageProcessor.ProcessImage(img)
		if err != nil {
			result.Warnings = append(result.Warnings, fmt.Sprintf("Image processing warning: %v", err))
			continue
		}
		processedImages = append(processedImages, processedImg)
		result.Stats.EdgesDetected += len(processedImg.Edges)
		result.Stats.LinesExtracted += len(processedImg.Lines)
	}
	result.Images = processedImages
	result.Stats.ImagesProcessed = len(processedImages)

	if config.Debug {
		fmt.Printf("Processed %d images, detected %d edges, extracted %d lines\n", 
			len(processedImages), result.Stats.EdgesDetected, result.Stats.LinesExtracted)
	}

	// Step 4: Build campus layout
	campusBuilder := building.NewBuilderWithConfig(config)
	campus, err := campusBuilder.ExtractCampus(doc, processedImages)
	if err != nil {
		return nil, fmt.Errorf("failed to extract campus: %w", err)
	}
	result.Campus = campus

	// Count rooms across all buildings
	for _, building := range campus.Buildings {
		result.Stats.RoomsDetected += len(building.Rooms)
	}

	if config.Debug {
		fmt.Printf("Extracted campus with %d buildings and %d rooms\n", 
			len(campus.Buildings), result.Stats.RoomsDetected)
	}

	// Step 5: Detect IDFs
	idfDetector := idf.NewDetectorWithConfig(config)
	
	// Extract rooms for IDF association
	allRooms := []types.Room{}
	for _, building := range campus.Buildings {
		allRooms = append(allRooms, building.Rooms...)
	}
	
	idfLocations, err := idfDetector.DetectIDFLocations(text, allRooms)
	if err != nil {
		result.Warnings = append(result.Warnings, fmt.Sprintf("IDF detection warning: %v", err))
	} else {
		campus.IDFRooms = idfLocations
		result.Stats.IDFsDetected = len(idfLocations)
	}

	if config.Debug {
		fmt.Printf("Detected %d IDF locations\n", len(idfLocations))
	}

	// Set campus name based on input file
	if campus.Name == "Extracted Campus" {
		campus.Name = fmt.Sprintf("Campus - %s", filepath.Base(inputFile))
	}

	return result, nil
}

// outputResults outputs the parsing results in the specified format
func outputResults(result *types.ParseResult, format string) error {
	renderer := building.NewRendererWithConfig(result.Config)

	switch format {
	case "ascii":
		output, err := renderer.RenderASCII(result.Campus)
		if err != nil {
			return fmt.Errorf("failed to render ASCII: %w", err)
		}
		fmt.Print(output)

	case "json":
		output, err := renderer.RenderJSON(result.Campus)
		if err != nil {
			return fmt.Errorf("failed to render JSON: %w", err)
		}
		fmt.Print(string(output))

	case "stats":
		output := renderer.RenderStats(result.Campus)
		fmt.Print(output)

	default:
		return fmt.Errorf("unsupported output format: %s (supported: ascii, json, stats)", format)
	}

	return nil
}

// printProcessingSummary prints detailed processing information
func printProcessingSummary(result *types.ParseResult, processingTime time.Duration) {
	fmt.Fprintf(os.Stderr, "\n=== PROCESSING SUMMARY ===\n")
	fmt.Fprintf(os.Stderr, "Processing Time: %v\n", processingTime)
	fmt.Fprintf(os.Stderr, "PDF Objects: %d\n", result.Stats.ObjectsProcessed)
	fmt.Fprintf(os.Stderr, "Images Processed: %d\n", result.Stats.ImagesProcessed)
	fmt.Fprintf(os.Stderr, "Text Characters: %d\n", result.Stats.TextCharacters)
	fmt.Fprintf(os.Stderr, "Edges Detected: %d\n", result.Stats.EdgesDetected)
	fmt.Fprintf(os.Stderr, "Lines Extracted: %d\n", result.Stats.LinesExtracted)
	fmt.Fprintf(os.Stderr, "Rooms Detected: %d\n", result.Stats.RoomsDetected)
	fmt.Fprintf(os.Stderr, "IDFs Detected: %d\n", result.Stats.IDFsDetected)

	if len(result.Errors) > 0 {
		fmt.Fprintf(os.Stderr, "\nErrors:\n")
		for _, err := range result.Errors {
			fmt.Fprintf(os.Stderr, "  - %v\n", err)
		}
	}

	if len(result.Warnings) > 0 {
		fmt.Fprintf(os.Stderr, "\nWarnings:\n")
		for _, warning := range result.Warnings {
			fmt.Fprintf(os.Stderr, "  - %s\n", warning)
		}
	}
}