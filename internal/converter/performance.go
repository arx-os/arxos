package converter

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
)

// PerformanceConfig holds performance tuning parameters
type PerformanceConfig struct {
	// MaxMemoryMB limits memory usage during conversion
	MaxMemoryMB int

	// BufferSize for streaming operations
	BufferSize int

	// MaxGoroutines limits concurrent processing
	MaxGoroutines int

	// EnableProfiling enables memory and CPU profiling
	EnableProfiling bool
}

// DefaultPerformanceConfig returns sensible defaults
func DefaultPerformanceConfig() *PerformanceConfig {
	return &PerformanceConfig{
		MaxMemoryMB:     500, // 500MB limit
		BufferSize:      64 * 1024, // 64KB buffer
		MaxGoroutines:   runtime.NumCPU(),
		EnableProfiling: false,
	}
}

// PerformanceMetrics tracks conversion performance
type PerformanceMetrics struct {
	StartTime         time.Time
	EndTime           time.Time
	Duration          time.Duration
	MemoryUsageBytes  int64
	PeakMemoryBytes   int64
	LinesProcessed    int
	RoomsExtracted    int
	EquipmentExtracted int
	ErrorsEncountered int
}

// String returns a formatted performance report
func (pm *PerformanceMetrics) String() string {
	return fmt.Sprintf(`Performance Metrics:
  Duration: %v
  Lines Processed: %d
  Rooms Extracted: %d
  Equipment Extracted: %d
  Memory Usage: %.2f MB
  Peak Memory: %.2f MB
  Processing Rate: %.0f lines/sec`,
		pm.Duration,
		pm.LinesProcessed,
		pm.RoomsExtracted,
		pm.EquipmentExtracted,
		float64(pm.MemoryUsageBytes)/(1024*1024),
		float64(pm.PeakMemoryBytes)/(1024*1024),
		float64(pm.LinesProcessed)/pm.Duration.Seconds())
}

// StreamingPDFConverter provides memory-efficient PDF processing
type StreamingPDFConverter struct {
	*RealPDFConverter
	config  *PerformanceConfig
	metrics *PerformanceMetrics
	mu      sync.RWMutex
}

// NewStreamingPDFConverter creates an optimized PDF converter
func NewStreamingPDFConverter(config *PerformanceConfig) *StreamingPDFConverter {
	if config == nil {
		config = DefaultPerformanceConfig()
	}

	return &StreamingPDFConverter{
		RealPDFConverter: NewRealPDFConverter(),
		config:          config,
		metrics:         &PerformanceMetrics{},
	}
}

// ConvertToBIMStreaming provides memory-efficient conversion
func (c *StreamingPDFConverter) ConvertToBIMStreaming(ctx context.Context, input io.Reader, output io.Writer) error {
	c.metrics.StartTime = time.Now()
	defer func() {
		c.metrics.EndTime = time.Now()
		c.metrics.Duration = c.metrics.EndTime.Sub(c.metrics.StartTime)

		if c.config.EnableProfiling {
			logger.Info("Conversion completed: %s", c.metrics.String())
		}
	}()

	// Monitor memory usage
	memMonitor := c.startMemoryMonitoring(ctx)
	defer memMonitor()

	// Use streaming scanner instead of loading entire file
	scanner := bufio.NewScanner(input)
	scanner.Buffer(make([]byte, c.config.BufferSize), c.config.BufferSize)

	building := &Building{
		Metadata: Metadata{
			Source: "PDF Import (Streaming)",
			Format: "PDF",
			Properties: map[string]string{
				"processing_mode": "streaming",
			},
		},
	}

	// Process in chunks to control memory usage
	var textChunks []string
	currentChunk := make([]string, 0, 100) // Process 100 lines at a time

	for scanner.Scan() {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		line := scanner.Text()
		c.metrics.LinesProcessed++

		currentChunk = append(currentChunk, line)

		// Process chunk when full
		if len(currentChunk) >= 100 {
			textChunks = append(textChunks, strings.Join(currentChunk, "\n"))
			currentChunk = currentChunk[:0] // Reset slice

			// Check memory usage
			if err := c.checkMemoryLimit(); err != nil {
				return err
			}
		}
	}

	// Process remaining lines
	if len(currentChunk) > 0 {
		textChunks = append(textChunks, strings.Join(currentChunk, "\n"))
	}

	if err := scanner.Err(); err != nil {
		c.metrics.ErrorsEncountered++
		return fmt.Errorf("scanning error: %w", err)
	}

	// Process chunks concurrently
	rooms, equipment := c.processChunksConcurrently(ctx, textChunks)

	c.metrics.RoomsExtracted = len(rooms)
	c.metrics.EquipmentExtracted = len(equipment)

	// Build final structure
	floor := Floor{
		ID:    "1",
		Name:  "Extracted Floor",
		Rooms: make([]Room, 0, len(rooms)),
	}

	// Process rooms
	for _, roomData := range rooms {
		room := Room{
			Number: roomData["number"],
			Name:   roomData["name"],
			Type:   c.inferRoomType(roomData["name"]),
		}

		// Parse area if available
		if areaStr, ok := roomData["area"]; ok {
			if area, err := strconv.ParseFloat(areaStr, 64); err == nil {
				room.Area = area
			}
		}

		// Add equipment to rooms
		for _, eq := range equipment {
			if eq["room"] == room.Number {
				room.Equipment = append(room.Equipment, Equipment{
					Tag:    eq["tag"],
					Name:   eq["name"],
					Type:   eq["type"],
					Status: "operational",
				})
			}
		}

		floor.Rooms = append(floor.Rooms, room)
	}

	building.Floors = append(building.Floors, floor)

	// Validate and output
	if issues := building.Validate(); len(issues) > 0 {
		logger.Warn("Data quality issues found (%d issues):", len(issues))
		for _, issue := range issues {
			logger.Warn("  - %s", issue)
		}
	}

	// Stream output
	return c.streamBIMOutput(building, output)
}

// processChunksConcurrently processes text chunks in parallel
func (c *StreamingPDFConverter) processChunksConcurrently(ctx context.Context, chunks []string) ([]map[string]string, []map[string]string) {
	type result struct {
		rooms     []map[string]string
		equipment []map[string]string
	}

	// Limit concurrent goroutines
	semaphore := make(chan struct{}, c.config.MaxGoroutines)
	results := make(chan result, len(chunks))

	var wg sync.WaitGroup

	for _, chunk := range chunks {
		wg.Add(1)
		go func(text string) {
			defer wg.Done()

			select {
			case semaphore <- struct{}{}:
				defer func() { <-semaphore }()
			case <-ctx.Done():
				return
			}

			rooms := c.extractRooms(text)
			equipment := c.extractEquipment(text)

			results <- result{rooms: rooms, equipment: equipment}
		}(chunk)
	}

	go func() {
		wg.Wait()
		close(results)
	}()

	// Collect results
	var allRooms []map[string]string
	var allEquipment []map[string]string

	for result := range results {
		allRooms = append(allRooms, result.rooms...)
		allEquipment = append(allEquipment, result.equipment...)
	}

	return allRooms, allEquipment
}

// startMemoryMonitoring monitors memory usage during conversion
func (c *StreamingPDFConverter) startMemoryMonitoring(ctx context.Context) func() {
	done := make(chan struct{})

	go func() {
		ticker := time.NewTicker(1 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-done:
				return
			case <-ticker.C:
				var m runtime.MemStats
				runtime.GC() // Force GC for accurate measurement
				runtime.ReadMemStats(&m)

				c.mu.Lock()
				c.metrics.MemoryUsageBytes = int64(m.Alloc)
				if int64(m.Alloc) > c.metrics.PeakMemoryBytes {
					c.metrics.PeakMemoryBytes = int64(m.Alloc)
				}
				c.mu.Unlock()
			}
		}
	}()

	return func() {
		close(done)
	}
}

// checkMemoryLimit ensures we don't exceed memory limits
func (c *StreamingPDFConverter) checkMemoryLimit() error {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	currentMB := m.Alloc / (1024 * 1024)
	if int(currentMB) > c.config.MaxMemoryMB {
		runtime.GC() // Try to free memory
		runtime.ReadMemStats(&m)

		currentMB = m.Alloc / (1024 * 1024)
		if int(currentMB) > c.config.MaxMemoryMB {
			return fmt.Errorf("memory limit exceeded: %d MB > %d MB limit", currentMB, c.config.MaxMemoryMB)
		}
	}

	return nil
}

// streamBIMOutput writes BIM data efficiently to output
func (c *StreamingPDFConverter) streamBIMOutput(building *Building, output io.Writer) error {
	writer := bufio.NewWriter(output)
	defer writer.Flush()

	// Stream header
	fmt.Fprintf(writer, "# ArxOS Building Information Model\n")
	if building.Name != "" {
		fmt.Fprintf(writer, "# Name: %s\n", building.Name)
	}
	fmt.Fprintf(writer, "# Source: %s (%s)\n", building.Metadata.Source, building.Metadata.Format)
	fmt.Fprintf(writer, "\n")

	// Stream floors
	if len(building.Floors) > 0 {
		fmt.Fprintf(writer, "## FLOORS\n")
		for _, floor := range building.Floors {
			fmt.Fprintf(writer, "FLOOR %s \"%s\" %.1f\n", floor.ID, floor.Name, floor.Elevation)
		}
		fmt.Fprintf(writer, "\n")
	}

	// Stream rooms
	if hasRooms(building) {
		fmt.Fprintf(writer, "## ROOMS\n")
		for _, floor := range building.Floors {
			for _, room := range floor.Rooms {
				fmt.Fprintf(writer, "ROOM %s/%s \"%s\" %s %.1f\n",
					floor.ID, room.Number, room.Name, room.Type, room.Area)
			}
		}
		fmt.Fprintf(writer, "\n")
	}

	// Stream equipment
	if hasEquipment(building) {
		fmt.Fprintf(writer, "## EQUIPMENT\n")
		for _, floor := range building.Floors {
			for _, room := range floor.Rooms {
				for _, eq := range room.Equipment {
					fmt.Fprintf(writer, "EQUIPMENT %s/%s/%s \"%s\" %s %s\n",
						floor.ID, room.Number, eq.Tag, eq.Name, eq.Type, eq.Status)
				}
			}
		}
	}

	return writer.Flush()
}

// MemoryPool provides reusable buffer management
type MemoryPool struct {
	pool sync.Pool
	size int
}

// NewMemoryPool creates a new memory pool for buffers
func NewMemoryPool(size int) *MemoryPool {
	return &MemoryPool{
		size: size,
		pool: sync.Pool{
			New: func() interface{} {
				return make([]byte, size)
			},
		},
	}
}

// Get retrieves a buffer from the pool
func (mp *MemoryPool) Get() []byte {
	return mp.pool.Get().([]byte)
}

// Put returns a buffer to the pool
func (mp *MemoryPool) Put(buf []byte) {
	if len(buf) == mp.size {
		mp.pool.Put(buf)
	}
}

// GetMetrics returns current performance metrics
func (c *StreamingPDFConverter) GetMetrics() *PerformanceMetrics {
	c.mu.RLock()
	defer c.mu.RUnlock()

	// Return a copy
	metrics := *c.metrics
	return &metrics
}