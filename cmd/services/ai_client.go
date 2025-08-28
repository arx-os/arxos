// AI Service Client for connecting to AI microservice
package services

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	
	// TODO: Replace with generated protobuf when available
	// ai "github.com/arxos/arxos/core/proto/ai"
)

// AIClient wraps the gRPC client for AI services
type AIClient struct {
	conn   *grpc.ClientConn
	// client ai.AIServiceClient // Will be enabled when protobuf is generated
	config AIClientConfig
}

// AIClientConfig holds configuration for the AI service client
type AIClientConfig struct {
	ServiceURL     string        `json:"service_url"`
	Timeout        time.Duration `json:"timeout"`
	MaxRetries     int           `json:"max_retries"`
	EnableTLS      bool          `json:"enable_tls"`
	APIKey         string        `json:"api_key"`
	MaxMessageSize int           `json:"max_message_size"`
}

// NewAIClient creates a new AI service client
func NewAIClient(config AIClientConfig) (*AIClient, error) {
	// Set defaults
	if config.ServiceURL == "" {
		config.ServiceURL = getEnvOrDefault("ARXOS_AI_SERVICE_URL", "localhost:9090")
	}
	if config.Timeout == 0 {
		config.Timeout = 30 * time.Second
	}
	if config.MaxRetries == 0 {
		config.MaxRetries = 3
	}
	if config.MaxMessageSize == 0 {
		config.MaxMessageSize = 100 * 1024 * 1024 // 100MB for large images/point clouds
	}

	// Set up gRPC connection options
	opts := []grpc.DialOption{
		grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(config.MaxMessageSize)),
	}

	// Configure TLS
	if config.EnableTLS {
		// In production, would use proper TLS credentials
		// For now, use insecure connection
		log.Println("⚠️  TLS requested but using insecure connection for development")
	}
	opts = append(opts, grpc.WithTransportCredentials(insecure.NewCredentials()))

	// Establish connection
	conn, err := grpc.Dial(config.ServiceURL, opts...)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to AI service: %w", err)
	}

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := testConnection(ctx, conn); err != nil {
		conn.Close()
		return nil, fmt.Errorf("AI service connection test failed: %w", err)
	}

	client := &AIClient{
		conn:   conn,
		config: config,
		// client: ai.NewAIServiceClient(conn), // Will be enabled when protobuf is generated
	}

	log.Printf("✅ Connected to AI service at %s", config.ServiceURL)
	return client, nil
}

// Close closes the connection to the AI service
func (c *AIClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// DetectSymbols detects architectural symbols in images
func (c *AIClient) DetectSymbols(ctx context.Context, imageData []byte, imageFormat string, symbolTypes []string, confidenceThreshold float32) (*SymbolDetectionResult, error) {
	// TODO: Implement once protobuf is generated
	// For now, return mock data for development
	
	log.Printf("🔍 Detecting symbols in %s image (%d bytes)", imageFormat, len(imageData))
	
	// Simulate processing time
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-time.After(100 * time.Millisecond):
		// Continue
	}
	
	// Mock response for development
	result := &SymbolDetectionResult{
		Symbols: []DetectedSymbol{
			{
				Type:       "door",
				Confidence: 0.92,
				BoundingBox: BoundingBox{
					X:      100,
					Y:      150,
					Width:  80,
					Height: 20,
				},
				Center: Point2D{X: 140, Y: 160},
				Attributes: map[string]string{
					"orientation": "horizontal",
					"style":       "single",
				},
			},
			{
				Type:       "window",
				Confidence: 0.88,
				BoundingBox: BoundingBox{
					X:      200,
					Y:      100,
					Width:  60,
					Height: 15,
				},
				Center: Point2D{X: 230, Y: 107},
				Attributes: map[string]string{
					"orientation": "horizontal",
					"panes":       "2",
				},
			},
		},
		ProcessingTime: 0.1,
		ModelVersion:   "yolo-architecture-v2.1",
		TotalDetections: 2,
	}
	
	return result, nil
}

// ClassifyRoom classifies the type of room based on image and context
func (c *AIClient) ClassifyRoom(ctx context.Context, imageData []byte, roomBBox BoundingBox, contextSymbols []DetectedSymbol) (*RoomClassificationResult, error) {
	// TODO: Implement once protobuf is generated
	
	log.Printf("🏠 Classifying room with %d context symbols", len(contextSymbols))
	
	// Simulate processing
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-time.After(80 * time.Millisecond):
		// Continue
	}
	
	// Mock classification based on context
	roomType := "office"
	confidence := float32(0.85)
	
	// Simple heuristic based on symbols
	for _, symbol := range contextSymbols {
		if symbol.Type == "bathtub" || symbol.Type == "toilet" {
			roomType = "bathroom"
			confidence = 0.95
			break
		} else if symbol.Type == "stove" || symbol.Type == "refrigerator" {
			roomType = "kitchen"
			confidence = 0.92
			break
		}
	}
	
	result := &RoomClassificationResult{
		RoomType:   roomType,
		Confidence: confidence,
		Alternatives: []RoomTypeCandidate{
			{Type: "conference_room", Confidence: 0.15},
			{Type: "break_room", Confidence: 0.10},
		},
		Features: map[string]float32{
			"has_windows":    0.8,
			"has_furniture":  0.6,
			"natural_light":  0.7,
		},
	}
	
	return result, nil
}

// ProcessPointCloud processes LiDAR point cloud data
func (c *AIClient) ProcessPointCloud(ctx context.Context, pointCloudData []byte, format string, processingType ProcessingType) (*PointCloudResult, error) {
	// TODO: Implement once protobuf is generated
	
	log.Printf("☁️ Processing point cloud: %s format (%d bytes)", format, len(pointCloudData))
	
	// Simulate longer processing for point clouds
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-time.After(500 * time.Millisecond):
		// Continue
	}
	
	// Mock result
	result := &PointCloudResult{
		Walls: []Wall{
			{
				StartPoint: Point3D{X: 0, Y: 0, Z: 0},
				EndPoint:   Point3D{X: 5, Y: 0, Z: 0},
				Thickness:  0.15,
				Height:     2.5,
				Material:   "drywall",
			},
		},
		Rooms: []Room{
			{
				ID:       "room_001",
				Type:     "office",
				Area:     25.5,
				Height:   2.5,
				Boundary: []Point3D{
					{X: 0, Y: 0, Z: 0},
					{X: 5, Y: 0, Z: 0},
					{X: 5, Y: 5, Z: 0},
					{X: 0, Y: 5, Z: 0},
				},
			},
		},
		Objects: []DetectedObject{
			{
				Type:       "desk",
				Position:   Point3D{X: 2, Y: 2, Z: 0},
				Dimensions: Point3D{X: 1.2, Y: 0.6, Z: 0.75},
				Confidence: 0.89,
			},
		},
		Stats: CloudStats{
			TotalPoints:           45000,
			ProcessedPoints:       42000,
			ProcessingTimeSeconds: 0.5,
		},
	}
	
	return result, nil
}

// GetModelInfo retrieves information about a specific model
func (c *AIClient) GetModelInfo(ctx context.Context, modelID string) (*ModelInfo, error) {
	// TODO: Implement once protobuf is generated
	
	log.Printf("ℹ️ Getting info for model: %s", modelID)
	
	// Mock model info
	info := &ModelInfo{
		ID:        modelID,
		Name:      "YOLOv8 Architecture Detection",
		Type:      "symbol_detection",
		Version:   "v2.1.0",
		SizeBytes: 125 * 1024 * 1024, // 125MB
		Metrics: ModelMetrics{
			Accuracy:        0.89,
			Precision:       0.92,
			Recall:          0.87,
			F1Score:         0.895,
			InferenceTimeMs: 45.2,
		},
		Metadata: map[string]string{
			"training_dataset": "arxos-symbols-v3",
			"framework":        "pytorch",
			"gpu_optimized":    "true",
		},
	}
	
	return info, nil
}

// ListModels lists available AI models
func (c *AIClient) ListModels(ctx context.Context, modelType string) ([]ModelInfo, error) {
	// TODO: Implement once protobuf is generated
	
	log.Printf("📋 Listing models of type: %s", modelType)
	
	// Mock model list
	models := []ModelInfo{
		{
			ID:      "yolo-arch-v2",
			Name:    "YOLOv8 Architecture Detection",
			Type:    "symbol_detection",
			Version: "v2.1.0",
			Metrics: ModelMetrics{
				Accuracy:        0.89,
				InferenceTimeMs: 45.2,
			},
		},
		{
			ID:      "resnet-rooms-v1",
			Name:    "ResNet Room Classification",
			Type:    "room_classification",
			Version: "v1.3.0",
			Metrics: ModelMetrics{
				Accuracy:        0.92,
				InferenceTimeMs: 28.1,
			},
		},
	}
	
	// Filter by type if specified
	if modelType != "" && modelType != "all" {
		var filtered []ModelInfo
		for _, model := range models {
			if model.Type == modelType {
				filtered = append(filtered, model)
			}
		}
		return filtered, nil
	}
	
	return models, nil
}

// Data structures (will be replaced by generated protobuf structs)

type SymbolDetectionResult struct {
	Symbols         []DetectedSymbol
	ProcessingTime  float32
	ModelVersion    string
	TotalDetections int
}

type DetectedSymbol struct {
	Type        string
	Confidence  float32
	BoundingBox BoundingBox
	Center      Point2D
	Attributes  map[string]string
	Rotation    float32
}

type BoundingBox struct {
	X, Y, Width, Height float32
}

type Point2D struct {
	X, Y float32
}

type Point3D struct {
	X, Y, Z float32
}

type RoomClassificationResult struct {
	RoomType     string
	Confidence   float32
	Alternatives []RoomTypeCandidate
	Features     map[string]float32
}

type RoomTypeCandidate struct {
	Type       string
	Confidence float32
}

type PointCloudResult struct {
	Walls   []Wall
	Rooms   []Room
	Objects []DetectedObject
	Stats   CloudStats
}

type Wall struct {
	StartPoint Point3D
	EndPoint   Point3D
	Thickness  float32
	Height     float32
	Material   string
}

type Room struct {
	ID       string
	Type     string
	Area     float32
	Height   float32
	Boundary []Point3D
}

type DetectedObject struct {
	Type       string
	Position   Point3D
	Dimensions Point3D
	Confidence float32
}

type CloudStats struct {
	TotalPoints           int
	ProcessedPoints       int
	ProcessingTimeSeconds float32
}

type ModelInfo struct {
	ID        string
	Name      string
	Type      string
	Version   string
	SizeBytes int64
	Metrics   ModelMetrics
	Metadata  map[string]string
}

type ModelMetrics struct {
	Accuracy        float32
	Precision       float32
	Recall          float32
	F1Score         float32
	InferenceTimeMs float32
}

type ProcessingType int

const (
	ProcessingTypeWallDetection ProcessingType = iota
	ProcessingTypeRoomSegmentation
	ProcessingTypeObjectDetection
	ProcessingTypeFullAnalysis
)

// Helper functions

func testConnection(ctx context.Context, conn *grpc.ClientConn) error {
	// Simple connection test - in production would ping the service
	state := conn.GetState()
	log.Printf("gRPC connection state: %v", state)
	return nil
}

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}