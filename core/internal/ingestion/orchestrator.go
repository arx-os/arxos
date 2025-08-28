// Package ingestion orchestrates the ingestion pipeline
package ingestion

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync"
	"time"
	
	"github.com/arxos/arxos/cmd/models"
	"github.com/arxos/arxos/core/internal/pdf"
	"github.com/google/uuid"
)

// Orchestrator coordinates the entire ingestion pipeline
type Orchestrator struct {
	grpcClient    *GRPCClient
	db            *sql.DB
	stages        []PipelineStage
	config        *OrchestratorConfig
	metrics       *PipelineMetrics
	mu            sync.RWMutex
	activeSessions map[string]*Session
}

// OrchestratorConfig holds orchestrator configuration
type OrchestratorConfig struct {
	GRPCAddress      string        `json:"grpc_address"`
	MaxWorkers       int           `json:"max_workers"`
	Timeout          time.Duration `json:"timeout"`
	RetryAttempts    int           `json:"retry_attempts"`
	TempDir          string        `json:"temp_dir"`
	EnableCaching    bool          `json:"enable_caching"`
	MaxFileSize      int64         `json:"max_file_size"`
	EnableStreaming  bool          `json:"enable_streaming"`
}

// PipelineMetrics tracks pipeline performance
type PipelineMetrics struct {
	mu               sync.RWMutex
	TotalProcessed   int64
	TotalSuccess     int64
	TotalFailed      int64
	AverageLatency   time.Duration
	StageMetrics     map[string]*StageMetrics
}

// StageMetrics tracks individual stage performance
type StageMetrics struct {
	Executions     int64
	TotalDuration  time.Duration
	Failures       int64
	LastExecution  time.Time
}

// Session represents an active processing session
type Session struct {
	ID              string
	Type            string
	Status          string
	StartTime       time.Time
	LastUpdate      time.Time
	CurrentStage    string
	Progress        float32
	Results         map[string]interface{}
	Errors          []error
}

// PipelineStage represents a processing stage
type PipelineStage interface {
	Name() string
	Process(ctx context.Context, data interface{}) (interface{}, error)
	Validate(data interface{}) error
}

// DefaultOrchestratorConfig returns default configuration
func DefaultOrchestratorConfig() *OrchestratorConfig {
	return &OrchestratorConfig{
		GRPCAddress:     "localhost:50051",
		MaxWorkers:      4,
		Timeout:         5 * time.Minute,
		RetryAttempts:   3,
		TempDir:         "/tmp/arxos-ingestion",
		EnableCaching:   true,
		MaxFileSize:     100 * 1024 * 1024, // 100MB
		EnableStreaming: true,
	}
}

// NewOrchestrator creates a new pipeline orchestrator
func NewOrchestrator(config *OrchestratorConfig, db *sql.DB) (*Orchestrator, error) {
	if config == nil {
		config = DefaultOrchestratorConfig()
	}

	// Create gRPC client
	grpcConfig := &GRPCClientConfig{
		Address:    config.GRPCAddress,
		MaxRetries: config.RetryAttempts,
		Timeout:    config.Timeout,
	}
	
	grpcClient, err := NewGRPCClient(grpcConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create gRPC client: %w", err)
	}

	// Create temp directory
	if err := os.MkdirAll(config.TempDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create temp dir: %w", err)
	}

	o := &Orchestrator{
		grpcClient:     grpcClient,
		db:             db,
		config:         config,
		activeSessions: make(map[string]*Session),
		metrics: &PipelineMetrics{
			StageMetrics: make(map[string]*StageMetrics),
		},
	}

	// Initialize pipeline stages
	o.initializeStages()

	return o, nil
}

// initializeStages sets up the processing pipeline stages
func (o *Orchestrator) initializeStages() {
	o.stages = []PipelineStage{
		NewValidationStage(),
		NewExtractionStage(o.grpcClient),
		NewDetectionStage(o.grpcClient),
		NewMeasurementStage(o.grpcClient),
		NewBIMGenerationStage(o.grpcClient),
		NewPersistenceStage(o.db),
	}
}

// ProcessPDF orchestrates PDF ingestion pipeline
func (o *Orchestrator) ProcessPDF(ctx context.Context, pdfData []byte, filename string) (*PipelineResult, error) {
	// Create session
	sessionID := uuid.New().String()
	session := &Session{
		ID:           sessionID,
		Type:         "pdf",
		Status:       "processing",
		StartTime:    time.Now(),
		LastUpdate:   time.Now(),
		CurrentStage: "initialization",
		Progress:     0,
		Results:      make(map[string]interface{}),
		Errors:       []error{},
	}
	
	o.mu.Lock()
	o.activeSessions[sessionID] = session
	o.mu.Unlock()
	
	defer func() {
		o.mu.Lock()
		delete(o.activeSessions, sessionID)
		o.mu.Unlock()
	}()

	result := &PipelineResult{
		SessionID:  sessionID,
		StartTime:  time.Now(),
		Stages:     make(map[string]StageResult),
		Objects:    []models.ArxObject{},
		Confidence: 0.0,
	}

	// Validate file size
	if int64(len(pdfData)) > o.config.MaxFileSize {
		return nil, fmt.Errorf("file size exceeds maximum of %d bytes", o.config.MaxFileSize)
	}

	// Stage 1: PDF Extraction (Python via gRPC)
	o.updateSession(sessionID, "pdf_extraction", 0.1)
	extractionStart := time.Now()
	
	extractionOptions := &PDFExtractionOptions{
		ExtractText:      true,
		ExtractImages:    true,
		ExtractTables:    true,
		DetectFloorPlans: true,
		DPI:              150,
		OutputFormat:     "json",
	}
	
	extractionResult, err := o.grpcClient.ExtractPDF(ctx, pdfData, extractionOptions)
	if err != nil {
		o.recordStageError(result, "pdf_extraction", err)
		return result, fmt.Errorf("pdf extraction failed: %w", err)
	}
	
	result.Stages["pdf_extraction"] = StageResult{
		Success:  true,
		Duration: time.Since(extractionStart),
		Output:   extractionResult,
	}
	o.updateSession(sessionID, "pdf_extraction", 0.3)

	// Stage 2: Wall Detection (Python via gRPC)
	if len(extractionResult.FloorPlans) > 0 {
		o.updateSession(sessionID, "wall_detection", 0.4)
		detectionStart := time.Now()
		
		// Process each floor plan
		var allWalls []Wall
		var allRooms []Room
		
		for i, floorPlan := range extractionResult.FloorPlans {
			// Get the floor plan image
			if i < len(extractionResult.Pages) && len(extractionResult.Pages[i].Images) > 0 {
				imageData := extractionResult.Pages[i].Images[0].Data
				
				detectionOptions := &WallDetectionOptions{
					ImageFormat:      "png",
					MinWallThickness: 0.1,
					MaxWallThickness: 0.5,
					DetectDoors:      true,
					DetectWindows:    true,
					DetectColumns:    true,
					Units:            "meters",
				}
				
				detectionResult, err := o.grpcClient.DetectWalls(ctx, imageData, detectionOptions)
				if err != nil {
					o.recordStageError(result, "wall_detection", err)
					continue
				}
				
				allWalls = append(allWalls, detectionResult.Walls...)
				allRooms = append(allRooms, detectionResult.Rooms...)
				
				// Store intermediate results
				session.Results[fmt.Sprintf("floor_%d_walls", floorPlan.FloorNumber)] = detectionResult.Walls
				session.Results[fmt.Sprintf("floor_%d_rooms", floorPlan.FloorNumber)] = detectionResult.Rooms
			}
		}
		
		result.Stages["wall_detection"] = StageResult{
			Success:  true,
			Duration: time.Since(detectionStart),
			Output: map[string]interface{}{
				"walls": allWalls,
				"rooms": allRooms,
			},
		}
		o.updateSession(sessionID, "wall_detection", 0.6)
		
		// Stage 3: BIM Generation (Python via gRPC)
		o.updateSession(sessionID, "bim_generation", 0.7)
		bimStart := time.Now()
		
		bimRequest := &BIMGenerationRequest{
			Walls: allWalls,
			Rooms: allRooms,
			Options: BIMOptions{
				DefaultFloorHeight: 3.0,
				DefaultWallHeight:  3.0,
				GenerateCeiling:    true,
				GenerateRoof:       false,
				CoordinateSystem:   "local",
				LevelOfDetail:      300,
			},
		}
		
		bimResult, err := o.grpcClient.Generate3DBIM(ctx, bimRequest)
		if err != nil {
			o.recordStageError(result, "bim_generation", err)
		} else {
			result.Stages["bim_generation"] = StageResult{
				Success:  true,
				Duration: time.Since(bimStart),
				Output:   bimResult,
			}
			
			// Convert BIM elements to ArxObjects
			arxObjects := o.convertBIMToArxObjects(bimResult)
			result.Objects = arxObjects
		}
		o.updateSession(sessionID, "bim_generation", 0.9)
	}

	// Stage 4: Persistence
	o.updateSession(sessionID, "persistence", 0.95)
	persistStart := time.Now()
	
	if len(result.Objects) > 0 {
		err = o.persistObjects(ctx, result.Objects, sessionID)
		if err != nil {
			o.recordStageError(result, "persistence", err)
		} else {
			result.Stages["persistence"] = StageResult{
				Success:  true,
				Duration: time.Since(persistStart),
				Output:   map[string]int{"objects_saved": len(result.Objects)},
			}
		}
	}

	// Calculate overall confidence
	result.Confidence = o.calculateOverallConfidence(result)
	
	// Update metrics
	o.updateMetrics(result)
	
	// Final session update
	o.updateSession(sessionID, "complete", 1.0)
	session.Status = "completed"
	
	result.EndTime = time.Now()
	result.TotalDuration = result.EndTime.Sub(result.StartTime)
	
	return result, nil
}

// ProcessImage processes standalone images through the pipeline
func (o *Orchestrator) ProcessImage(ctx context.Context, imageData []byte, imageType string) (*PipelineResult, error) {
	sessionID := uuid.New().String()
	session := &Session{
		ID:           sessionID,
		Type:         "image",
		Status:       "processing",
		StartTime:    time.Now(),
		LastUpdate:   time.Now(),
		CurrentStage: "initialization",
		Progress:     0,
		Results:      make(map[string]interface{}),
		Errors:       []error{},
	}
	
	o.mu.Lock()
	o.activeSessions[sessionID] = session
	o.mu.Unlock()
	
	defer func() {
		o.mu.Lock()
		delete(o.activeSessions, sessionID)
		o.mu.Unlock()
	}()

	result := &PipelineResult{
		SessionID:  sessionID,
		StartTime:  time.Now(),
		Stages:     make(map[string]StageResult),
		Objects:    []models.ArxObject{},
		Confidence: 0.0,
	}

	// Direct wall detection for images
	detectionOptions := &WallDetectionOptions{
		ImageFormat:      imageType,
		MinWallThickness: 0.1,
		MaxWallThickness: 0.5,
		DetectDoors:      true,
		DetectWindows:    true,
		DetectColumns:    true,
		Units:            "meters",
	}
	
	detectionResult, err := o.grpcClient.DetectWalls(ctx, imageData, detectionOptions)
	if err != nil {
		return result, fmt.Errorf("wall detection failed: %w", err)
	}
	
	result.Stages["wall_detection"] = StageResult{
		Success:  true,
		Duration: time.Since(result.StartTime),
		Output:   detectionResult,
	}

	// Generate BIM if walls detected
	if len(detectionResult.Walls) > 0 {
		bimRequest := &BIMGenerationRequest{
			Walls: detectionResult.Walls,
			Rooms: detectionResult.Rooms,
			Options: BIMOptions{
				DefaultFloorHeight: 3.0,
				DefaultWallHeight:  3.0,
				GenerateCeiling:    true,
				GenerateRoof:       false,
				CoordinateSystem:   "local",
				LevelOfDetail:      300,
			},
		}
		
		bimResult, err := o.grpcClient.Generate3DBIM(ctx, bimRequest)
		if err == nil {
			result.Objects = o.convertBIMToArxObjects(bimResult)
			result.Confidence = bimResult.Confidence
		}
	}
	
	result.EndTime = time.Now()
	result.TotalDuration = result.EndTime.Sub(result.StartTime)
	
	return result, nil
}

// StreamLargeFile processes large files using streaming
func (o *Orchestrator) StreamLargeFile(ctx context.Context, filePath string) (<-chan *ProcessingStatus, error) {
	// Read file
	fileData, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}
	
	// Start streaming process
	return o.grpcClient.ProcessLargeFile(ctx, filePath, fileData)
}

// GetSessionStatus returns the current status of a processing session
func (o *Orchestrator) GetSessionStatus(sessionID string) (*Session, error) {
	o.mu.RLock()
	defer o.mu.RUnlock()
	
	session, exists := o.activeSessions[sessionID]
	if !exists {
		return nil, fmt.Errorf("session %s not found", sessionID)
	}
	
	return session, nil
}

// GetMetrics returns current pipeline metrics
func (o *Orchestrator) GetMetrics() PipelineMetrics {
	o.metrics.mu.RLock()
	defer o.metrics.mu.RUnlock()
	return *o.metrics
}

// Close gracefully shuts down the orchestrator
func (o *Orchestrator) Close() error {
	// Close gRPC connection
	if o.grpcClient != nil {
		return o.grpcClient.Close()
	}
	return nil
}

// Helper methods

func (o *Orchestrator) updateSession(sessionID, stage string, progress float32) {
	o.mu.Lock()
	defer o.mu.Unlock()
	
	if session, exists := o.activeSessions[sessionID]; exists {
		session.CurrentStage = stage
		session.Progress = progress
		session.LastUpdate = time.Now()
	}
}

func (o *Orchestrator) recordStageError(result *PipelineResult, stage string, err error) {
	result.Stages[stage] = StageResult{
		Success: false,
		Error:   err,
	}
	result.Errors = append(result.Errors, err)
}

func (o *Orchestrator) convertBIMToArxObjects(bimResult *BIMGenerationResult) []models.ArxObject {
	objects := make([]models.ArxObject, 0, len(bimResult.Elements))
	
	for _, element := range bimResult.Elements {
		obj := models.ArxObject{
			ID:         element.ID,
			Name:       element.Name,
			Type:       o.ifcClassToArxType(element.IFCClass),
			Properties: element.Properties,
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		objects = append(objects, obj)
	}
	
	return objects
}

func (o *Orchestrator) ifcClassToArxType(ifcClass string) string {
	// Map IFC classes to Arx object types
	mapping := map[string]string{
		"IfcWall":     "wall",
		"IfcDoor":     "door",
		"IfcWindow":   "window",
		"IfcSpace":    "room",
		"IfcColumn":   "column",
		"IfcRoof":     "roof",
		"IfcSlab":     "floor",
		"IfcBeam":     "beam",
	}
	
	if arxType, exists := mapping[ifcClass]; exists {
		return arxType
	}
	return "element"
}

func (o *Orchestrator) persistObjects(ctx context.Context, objects []models.ArxObject, sessionID string) error {
	// Begin transaction
	tx, err := o.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Insert objects
	for _, obj := range objects {
		query := `
			INSERT INTO arx_objects (id, name, type, properties, session_id, created_at, updated_at)
			VALUES ($1, $2, $3, $4, $5, $6, $7)
		`
		
		propertiesJSON, err := json.Marshal(obj.Properties)
		if err != nil {
			return fmt.Errorf("failed to marshal properties: %w", err)
		}
		
		_, err = tx.Exec(query, obj.ID, obj.Name, obj.Type, propertiesJSON, sessionID, obj.CreatedAt, obj.UpdatedAt)
		if err != nil {
			return fmt.Errorf("failed to insert object: %w", err)
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

func (o *Orchestrator) calculateOverallConfidence(result *PipelineResult) float32 {
	var totalConfidence float32
	var stageCount int
	
	for _, stage := range result.Stages {
		if stage.Success && stage.Output != nil {
			// Extract confidence from stage output if available
			switch output := stage.Output.(type) {
			case *PDFExtractionResult:
				totalConfidence += output.Confidence
				stageCount++
			case *WallDetectionResult:
				totalConfidence += output.Confidence
				stageCount++
			case *BIMGenerationResult:
				totalConfidence += output.Confidence
				stageCount++
			}
		}
	}
	
	if stageCount > 0 {
		return totalConfidence / float32(stageCount)
	}
	return 0.0
}

func (o *Orchestrator) updateMetrics(result *PipelineResult) {
	o.metrics.mu.Lock()
	defer o.metrics.mu.Unlock()
	
	o.metrics.TotalProcessed++
	
	if len(result.Errors) == 0 {
		o.metrics.TotalSuccess++
	} else {
		o.metrics.TotalFailed++
	}
	
	// Update stage metrics
	for stageName, stageResult := range result.Stages {
		if _, exists := o.metrics.StageMetrics[stageName]; !exists {
			o.metrics.StageMetrics[stageName] = &StageMetrics{}
		}
		
		metric := o.metrics.StageMetrics[stageName]
		metric.Executions++
		metric.TotalDuration += stageResult.Duration
		metric.LastExecution = time.Now()
		
		if !stageResult.Success {
			metric.Failures++
		}
	}
	
	// Update average latency
	if o.metrics.TotalProcessed > 0 {
		o.metrics.AverageLatency = time.Duration(
			int64(o.metrics.AverageLatency)*(o.metrics.TotalProcessed-1)/o.metrics.TotalProcessed +
			int64(result.TotalDuration)/o.metrics.TotalProcessed,
		)
	}
}

// PipelineResult contains the complete pipeline result
type PipelineResult struct {
	SessionID     string                   `json:"session_id"`
	StartTime     time.Time                `json:"start_time"`
	EndTime       time.Time                `json:"end_time"`
	TotalDuration time.Duration            `json:"total_duration"`
	Stages        map[string]StageResult   `json:"stages"`
	Objects       []models.ArxObject       `json:"objects,omitempty"`
	Confidence    float32                  `json:"confidence"`
	Errors        []error                  `json:"errors,omitempty"`
}

// StageResult contains a single stage result
type StageResult struct {
	Success  bool          `json:"success"`
	Duration time.Duration `json:"duration"`
	Output   interface{}   `json:"output,omitempty"`
	Error    error         `json:"error,omitempty"`
}