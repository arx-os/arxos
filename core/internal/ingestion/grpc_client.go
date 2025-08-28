package ingestion

import (
	"context"
	"fmt"
	"io"
	"sync"
	"time"

	"github.com/arxos/arxos/core/proto/ingestion"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/connectivity"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/status"
)

// GRPCClient manages the connection to the Python AI service
type GRPCClient struct {
	conn            *grpc.ClientConn
	client          ingestion.IngestionServiceClient
	address         string
	maxRetries      int
	retryDelay      time.Duration
	timeout         time.Duration
	streamChunkSize int
	mu              sync.RWMutex
	connected       bool
	metrics         *ClientMetrics
}

// ClientMetrics tracks gRPC client performance
type ClientMetrics struct {
	mu                 sync.RWMutex
	TotalRequests      int64
	SuccessfulRequests int64
	FailedRequests     int64
	TotalLatency       time.Duration
	LastError          error
	LastErrorTime      time.Time
}

// GRPCClientConfig holds configuration for the gRPC client
type GRPCClientConfig struct {
	Address         string
	MaxRetries      int
	RetryDelay      time.Duration
	Timeout         time.Duration
	StreamChunkSize int
}

// DefaultGRPCConfig returns default configuration
func DefaultGRPCConfig() *GRPCClientConfig {
	return &GRPCClientConfig{
		Address:         "localhost:50051",
		MaxRetries:      3,
		RetryDelay:      time.Second * 2,
		Timeout:         time.Minute * 5,
		StreamChunkSize: 1024 * 1024, // 1MB chunks
	}
}

// NewGRPCClient creates a new gRPC client for the Python AI service
func NewGRPCClient(config *GRPCClientConfig) (*GRPCClient, error) {
	if config == nil {
		config = DefaultGRPCConfig()
	}

	client := &GRPCClient{
		address:         config.Address,
		maxRetries:      config.MaxRetries,
		retryDelay:      config.RetryDelay,
		timeout:         config.Timeout,
		streamChunkSize: config.StreamChunkSize,
		metrics:         &ClientMetrics{},
	}

	if err := client.connect(); err != nil {
		return nil, fmt.Errorf("failed to connect to gRPC server: %w", err)
	}

	// Start health check routine
	go client.healthCheck()

	return client, nil
}

// connect establishes the gRPC connection
func (c *GRPCClient) connect() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Close existing connection if any
	if c.conn != nil {
		c.conn.Close()
	}

	// Configure connection options
	opts := []grpc.DialOption{
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Time:                10 * time.Second,
			Timeout:             3 * time.Second,
			PermitWithoutStream: true,
		}),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(100*1024*1024), // 100MB
			grpc.MaxCallSendMsgSize(100*1024*1024), // 100MB
		),
	}

	// Establish connection
	conn, err := grpc.Dial(c.address, opts...)
	if err != nil {
		c.connected = false
		return fmt.Errorf("failed to dial gRPC server: %w", err)
	}

	c.conn = conn
	c.client = ingestion.NewIngestionServiceClient(conn)
	c.connected = true

	return nil
}

// healthCheck monitors connection health
func (c *GRPCClient) healthCheck() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		c.mu.RLock()
		if c.conn == nil {
			c.mu.RUnlock()
			continue
		}
		state := c.conn.GetState()
		c.mu.RUnlock()

		if state != connectivity.Ready {
			c.mu.Lock()
			c.connected = false
			c.mu.Unlock()

			// Attempt reconnection
			if err := c.connect(); err != nil {
				c.recordError(fmt.Errorf("health check reconnect failed: %w", err))
			}
		}
	}
}

// ExtractPDF extracts content from a PDF file
func (c *GRPCClient) ExtractPDF(ctx context.Context, pdfData []byte, options *PDFExtractionOptions) (*PDFExtractionResult, error) {
	// Record metrics
	start := time.Now()
	defer func() {
		c.recordMetrics(time.Since(start), nil)
	}()

	// Build request
	req := &ingestion.PDFExtractionRequest{
		PdfData: pdfData,
		Options: &ingestion.ExtractionOptions{
			ExtractText:      options.ExtractText,
			ExtractImages:    options.ExtractImages,
			ExtractTables:    options.ExtractTables,
			DetectFloorPlans: options.DetectFloorPlans,
			Dpi:              int32(options.DPI),
			OutputFormat:     options.OutputFormat,
		},
	}

	// Execute with retries
	var resp *ingestion.PDFExtractionResponse
	err := c.executeWithRetry(ctx, func() error {
		var callErr error
		resp, callErr = c.client.ExtractPDF(ctx, req)
		return callErr
	})

	if err != nil {
		c.recordError(err)
		return nil, fmt.Errorf("PDF extraction failed: %w", err)
	}

	// Convert response to internal format
	result := c.convertPDFResponse(resp)
	return result, nil
}

// DetectWalls detects walls and structural elements from images
func (c *GRPCClient) DetectWalls(ctx context.Context, imageData []byte, options *WallDetectionOptions) (*WallDetectionResult, error) {
	start := time.Now()
	defer func() {
		c.recordMetrics(time.Since(start), nil)
	}()

	req := &ingestion.WallDetectionRequest{
		ImageData:   imageData,
		ImageFormat: options.ImageFormat,
		Options: &ingestion.DetectionOptions{
			MinWallThickness: options.MinWallThickness,
			MaxWallThickness: options.MaxWallThickness,
			DetectDoors:      options.DetectDoors,
			DetectWindows:    options.DetectWindows,
			DetectColumns:    options.DetectColumns,
			Units:            options.Units,
		},
	}

	var resp *ingestion.WallDetectionResponse
	err := c.executeWithRetry(ctx, func() error {
		var callErr error
		resp, callErr = c.client.DetectWalls(ctx, req)
		return callErr
	})

	if err != nil {
		c.recordError(err)
		return nil, fmt.Errorf("wall detection failed: %w", err)
	}

	result := c.convertWallResponse(resp)
	return result, nil
}

// Generate3DBIM generates a 3D BIM model from 2D floor plans
func (c *GRPCClient) Generate3DBIM(ctx context.Context, request *BIMGenerationRequest) (*BIMGenerationResult, error) {
	start := time.Now()
	defer func() {
		c.recordMetrics(time.Since(start), nil)
	}()

	// Convert internal request to proto format
	req := c.buildBIMRequest(request)

	var resp *ingestion.BIMGenerationResponse
	err := c.executeWithRetry(ctx, func() error {
		var callErr error
		resp, callErr = c.client.Generate3DBIM(ctx, req)
		return callErr
	})

	if err != nil {
		c.recordError(err)
		return nil, fmt.Errorf("BIM generation failed: %w", err)
	}

	result := c.convertBIMResponse(resp)
	return result, nil
}

// ProcessLargeFile handles streaming for large file processing
func (c *GRPCClient) ProcessLargeFile(ctx context.Context, filePath string, fileData []byte) (<-chan *ProcessingStatus, error) {
	// Create status channel
	statusChan := make(chan *ProcessingStatus, 10)

	go func() {
		defer close(statusChan)

		// Create stream
		stream, err := c.client.ProcessLargeFile(ctx)
		if err != nil {
			statusChan <- &ProcessingStatus{
				Status:  "error",
				Message: fmt.Sprintf("Failed to create stream: %v", err),
			}
			return
		}
		defer stream.CloseSend()

		// Send file chunks
		sessionID := generateSessionID()
		totalChunks := (len(fileData) + c.streamChunkSize - 1) / c.streamChunkSize

		for i := 0; i < totalChunks; i++ {
			start := i * c.streamChunkSize
			end := start + c.streamChunkSize
			if end > len(fileData) {
				end = len(fileData)
			}

			chunk := &ingestion.FileChunk{
				SessionId:   sessionID,
				ChunkIndex:  int32(i),
				TotalChunks: int32(totalChunks),
				Data:        fileData[start:end],
				IsLast:      i == totalChunks-1,
			}

			if err := stream.Send(chunk); err != nil {
				statusChan <- &ProcessingStatus{
					Status:  "error",
					Message: fmt.Sprintf("Failed to send chunk %d: %v", i, err),
				}
				return
			}
		}

		// Receive status updates
		for {
			status, err := stream.Recv()
			if err == io.EOF {
				break
			}
			if err != nil {
				statusChan <- &ProcessingStatus{
					Status:  "error",
					Message: fmt.Sprintf("Failed to receive status: %v", err),
				}
				return
			}

			// Convert and send status
			statusChan <- c.convertProcessingStatus(status)
		}
	}()

	return statusChan, nil
}

// GetProcessingStatus retrieves the status of an ongoing processing session
func (c *GRPCClient) GetProcessingStatus(ctx context.Context, sessionID string) (*ProcessingStatus, error) {
	req := &ingestion.StatusRequest{
		SessionId: sessionID,
	}

	resp, err := c.client.GetStatus(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get status: %w", err)
	}

	return c.convertStatusResponse(resp), nil
}

// executeWithRetry executes a function with retry logic
func (c *GRPCClient) executeWithRetry(ctx context.Context, fn func() error) error {
	var lastErr error
	
	for i := 0; i < c.maxRetries; i++ {
		// Check connection
		if !c.isConnected() {
			if err := c.connect(); err != nil {
				lastErr = err
				time.Sleep(c.retryDelay)
				continue
			}
		}

		// Execute function
		err := fn()
		if err == nil {
			return nil
		}

		// Check if error is retryable
		if !isRetryableError(err) {
			return err
		}

		lastErr = err
		
		// Exponential backoff
		if i < c.maxRetries-1 {
			delay := c.retryDelay * time.Duration(1<<uint(i))
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(delay):
			}
		}
	}

	return fmt.Errorf("max retries exceeded: %w", lastErr)
}

// isRetryableError determines if an error should be retried
func isRetryableError(err error) bool {
	st, ok := status.FromError(err)
	if !ok {
		return false
	}

	switch st.Code() {
	case codes.Unavailable, codes.DeadlineExceeded, codes.ResourceExhausted:
		return true
	default:
		return false
	}
}

// isConnected checks if the client is connected
func (c *GRPCClient) isConnected() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.connected && c.conn != nil && c.conn.GetState() == connectivity.Ready
}

// Close closes the gRPC connection
func (c *GRPCClient) Close() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.conn != nil {
		err := c.conn.Close()
		c.conn = nil
		c.client = nil
		c.connected = false
		return err
	}

	return nil
}

// Metrics methods

func (c *GRPCClient) recordMetrics(latency time.Duration, err error) {
	c.metrics.mu.Lock()
	defer c.metrics.mu.Unlock()

	c.metrics.TotalRequests++
	if err != nil {
		c.metrics.FailedRequests++
	} else {
		c.metrics.SuccessfulRequests++
		c.metrics.TotalLatency += latency
	}
}

func (c *GRPCClient) recordError(err error) {
	c.metrics.mu.Lock()
	defer c.metrics.mu.Unlock()

	c.metrics.LastError = err
	c.metrics.LastErrorTime = time.Now()
}

// GetMetrics returns current metrics
func (c *GRPCClient) GetMetrics() ClientMetrics {
	c.metrics.mu.RLock()
	defer c.metrics.mu.RUnlock()
	return *c.metrics
}

// Conversion methods

func (c *GRPCClient) convertPDFResponse(resp *ingestion.PDFExtractionResponse) *PDFExtractionResult {
	result := &PDFExtractionResult{
		DocumentID: resp.DocumentId,
		Metadata: DocumentMetadata{
			Title:        resp.Metadata.Title,
			Author:       resp.Metadata.Author,
			CreationDate: resp.Metadata.CreationDate,
			PageCount:    int(resp.Metadata.PageCount),
			DocumentType: resp.Metadata.DocumentType,
		},
		Pages:      make([]Page, 0, len(resp.Pages)),
		FloorPlans: make([]FloorPlan, 0, len(resp.FloorPlans)),
		Confidence: resp.Confidence.Score,
		Warnings:   resp.Warnings,
	}

	// Convert pages
	for _, p := range resp.Pages {
		page := Page{
			PageNumber:   int(p.PageNumber),
			TextContent:  p.TextContent,
			TextBlocks:   make([]TextBlock, 0, len(p.TextBlocks)),
			Images:       make([]ExtractedImage, 0, len(p.Images)),
			Tables:       make([]Table, 0, len(p.Tables)),
		}

		// Convert text blocks
		for _, tb := range p.TextBlocks {
			page.TextBlocks = append(page.TextBlocks, TextBlock{
				Text:      tb.Text,
				Font:      tb.Font,
				FontSize:  tb.FontSize,
				BlockType: tb.BlockType,
			})
		}

		// Convert images
		for _, img := range p.Images {
			page.Images = append(page.Images, ExtractedImage{
				Data:      img.Data,
				Format:    img.Format,
				Caption:   img.Caption,
				ImageType: img.ImageType,
			})
		}

		result.Pages = append(result.Pages, page)
	}

	// Convert floor plans
	for _, fp := range resp.FloorPlans {
		result.FloorPlans = append(result.FloorPlans, FloorPlan{
			ID:          fp.Id,
			FloorName:   fp.FloorName,
			FloorNumber: int(fp.FloorNumber),
			Scale:       fp.Scale,
			Rotation:    fp.Rotation,
		})
	}

	return result
}

func (c *GRPCClient) convertWallResponse(resp *ingestion.WallDetectionResponse) *WallDetectionResult {
	result := &WallDetectionResult{
		Walls:      make([]Wall, 0, len(resp.Walls)),
		Doors:      make([]Door, 0, len(resp.Doors)),
		Windows:    make([]Window, 0, len(resp.Windows)),
		Columns:    make([]Column, 0, len(resp.Columns)),
		Rooms:      make([]Room, 0, len(resp.Rooms)),
		Confidence: resp.Confidence.Score,
	}

	// Convert walls
	for _, w := range resp.Walls {
		result.Walls = append(result.Walls, Wall{
			ID:        w.Id,
			StartX:    w.Start.X,
			StartY:    w.Start.Y,
			EndX:      w.End.X,
			EndY:      w.End.Y,
			Thickness: w.Thickness,
			Material:  w.Material,
			WallType:  w.WallType,
			Height:    w.Height,
		})
	}

	// Convert doors
	for _, d := range resp.Doors {
		result.Doors = append(result.Doors, Door{
			ID:              d.Id,
			X:               d.Position.X,
			Y:               d.Position.Y,
			Width:           d.Width,
			Height:          d.Height,
			SwingAngle:      d.SwingAngle,
			DoorType:        d.DoorType,
			ConnectedWallID: d.ConnectedWallId,
		})
	}

	// Convert rooms
	for _, r := range resp.Rooms {
		room := Room{
			ID:       r.Id,
			Name:     r.Name,
			RoomType: r.RoomType,
			Area:     r.Area,
			Height:   r.Height,
		}
		
		// Convert boundary points
		for _, pt := range r.Boundary {
			room.Boundary = append(room.Boundary, Point2D{
				X: pt.X,
				Y: pt.Y,
			})
		}
		
		result.Rooms = append(result.Rooms, room)
	}

	return result
}

func (c *GRPCClient) buildBIMRequest(request *BIMGenerationRequest) *ingestion.BIMGenerationRequest {
	req := &ingestion.BIMGenerationRequest{
		Options: &ingestion.BIMOptions{
			DefaultFloorHeight: request.Options.DefaultFloorHeight,
			DefaultWallHeight:  request.Options.DefaultWallHeight,
			GenerateCeiling:    request.Options.GenerateCeiling,
			GenerateRoof:       request.Options.GenerateRoof,
			CoordinateSystem:   request.Options.CoordinateSystem,
			LevelOfDetail:      int32(request.Options.LevelOfDetail),
		},
	}

	// Convert walls
	for _, w := range request.Walls {
		req.Walls = append(req.Walls, &ingestion.Wall{
			Id:        w.ID,
			Start:     &ingestion.Point2D{X: w.StartX, Y: w.StartY},
			End:       &ingestion.Point2D{X: w.EndX, Y: w.EndY},
			Thickness: w.Thickness,
			Material:  w.Material,
			WallType:  w.WallType,
			Height:    w.Height,
		})
	}

	// Convert doors
	for _, d := range request.Doors {
		req.Doors = append(req.Doors, &ingestion.Door{
			Id:              d.ID,
			Position:        &ingestion.Point2D{X: d.X, Y: d.Y},
			Width:           d.Width,
			Height:          d.Height,
			SwingAngle:      d.SwingAngle,
			DoorType:        d.DoorType,
			ConnectedWallId: d.ConnectedWallID,
		})
	}

	// Convert rooms
	for _, r := range request.Rooms {
		room := &ingestion.Room{
			Id:       r.ID,
			Name:     r.Name,
			RoomType: r.RoomType,
			Area:     r.Area,
			Height:   r.Height,
		}
		
		// Convert boundary
		for _, pt := range r.Boundary {
			room.Boundary = append(room.Boundary, &ingestion.Point2D{
				X: pt.X,
				Y: pt.Y,
			})
		}
		
		req.Rooms = append(req.Rooms, room)
	}

	return req
}

func (c *GRPCClient) convertBIMResponse(resp *ingestion.BIMGenerationResponse) *BIMGenerationResult {
	result := &BIMGenerationResult{
		ModelID:    resp.Model.Id,
		ModelName:  resp.Model.Name,
		IFCVersion: resp.Model.IfcVersion,
		IFCData:    resp.Model.IfcData,
		GLTFData:   resp.Model.GltfData,
		Elements:   make([]BIMElement, 0, len(resp.Elements)),
		Spaces:     make([]BIMSpace, 0, len(resp.Spaces)),
		Confidence: resp.Confidence.Score,
		Warnings:   resp.Warnings,
	}

	// Convert elements
	for _, e := range resp.Elements {
		result.Elements = append(result.Elements, BIMElement{
			ID:         e.Id,
			IFCClass:   e.IfcClass,
			Name:       e.Name,
			Properties: e.Properties,
			MaterialID: e.MaterialId,
		})
	}

	// Convert spaces
	for _, s := range resp.Spaces {
		result.Spaces = append(result.Spaces, BIMSpace{
			ID:        s.Id,
			Name:      s.Name,
			SpaceType: s.SpaceType,
			Area:      s.Area,
			Volume:    s.Volume,
		})
	}

	return result
}

func (c *GRPCClient) convertProcessingStatus(status *ingestion.ProcessingStatus) *ProcessingStatus {
	ps := &ProcessingStatus{
		SessionID:    status.SessionId,
		Status:       status.Status,
		Progress:     status.Progress,
		CurrentStage: status.CurrentStage,
		Message:      status.Message,
	}

	// Convert result based on type
	switch r := status.Result.(type) {
	case *ingestion.ProcessingStatus_PdfResult:
		ps.Result = c.convertPDFResponse(r.PdfResult)
	case *ingestion.ProcessingStatus_WallResult:
		ps.Result = c.convertWallResponse(r.WallResult)
	case *ingestion.ProcessingStatus_BimResult:
		ps.Result = c.convertBIMResponse(r.BimResult)
	}

	return ps
}

func (c *GRPCClient) convertStatusResponse(resp *ingestion.StatusResponse) *ProcessingStatus {
	return &ProcessingStatus{
		SessionID:        resp.SessionId,
		Status:           resp.Status,
		Progress:         resp.Progress,
		CurrentStage:     resp.CurrentStage,
		StartedAt:        time.Unix(resp.StartedAt, 0),
		UpdatedAt:        time.Unix(resp.UpdatedAt, 0),
		CompletedStages:  resp.CompletedStages,
		PendingStages:    resp.PendingStages,
	}
}

// generateSessionID creates a unique session identifier
func generateSessionID() string {
	return fmt.Sprintf("session-%d", time.Now().UnixNano())
}