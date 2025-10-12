package services

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// FileProcessor provides file processing functionality
type FileProcessor struct {
	logger    domain.Logger
	workers   int
	queueSize int
	jobQueue  chan *ProcessingJob
	ctx       context.Context
	cancel    context.CancelFunc
	wg        sync.WaitGroup
}

// ProcessingJob represents a file processing job
type ProcessingJob struct {
	ID       string
	FilePath string
	Format   string
	Priority int
	Created  time.Time
}

// NewFileProcessor creates a new file processor
func NewFileProcessor(logger domain.Logger) *FileProcessor {
	return &FileProcessor{
		logger: logger,
	}
}

// Start starts the file processor
func (fp *FileProcessor) Start(ctx context.Context, workers, queueSize int) error {
	fp.workers = workers
	fp.queueSize = queueSize
	fp.jobQueue = make(chan *ProcessingJob, queueSize)
	fp.ctx, fp.cancel = context.WithCancel(ctx)

	fp.logger.Info("Starting file processor", "workers", workers, "queue_size", queueSize)

	// Start worker goroutines
	for i := 0; i < workers; i++ {
		fp.wg.Add(1)
		go fp.worker(i)
	}

	return nil
}

// Stop stops the file processor
func (fp *FileProcessor) Stop() error {
	fp.logger.Info("Stopping file processor")

	if fp.cancel != nil {
		fp.cancel()
	}

	close(fp.jobQueue)
	fp.wg.Wait()

	fp.logger.Info("File processor stopped")
	return nil
}

// Health returns the health of the file processor
func (fp *FileProcessor) Health() (map[string]any, error) {
	return map[string]any{
		"status":     "healthy",
		"workers":    fp.workers,
		"queue_size": len(fp.jobQueue),
		"capacity":   fp.queueSize,
	}, nil
}

// ReadFile reads a file and returns its contents
func (fp *FileProcessor) ReadFile(filePath string) ([]byte, error) {
	fp.logger.Debug("Reading file", "path", filePath)

	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	fp.logger.Debug("File read successfully", "path", filePath, "size", len(data))
	return data, nil
}

// WriteFile writes data to a file
func (fp *FileProcessor) WriteFile(filePath string, data []byte) error {
	fp.logger.Debug("Writing file", "path", filePath, "size", len(data))

	// Ensure directory exists
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	file, err := os.Create(filePath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	_, err = file.Write(data)
	if err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	fp.logger.Debug("File written successfully", "path", filePath)
	return nil
}

// ProcessFile queues a file for processing
func (fp *FileProcessor) ProcessFile(filePath, format string) error {
	job := &ProcessingJob{
		ID:       fmt.Sprintf("%d", time.Now().UnixNano()),
		FilePath: filePath,
		Format:   format,
		Priority: 1,
		Created:  time.Now(),
	}

	select {
	case fp.jobQueue <- job:
		fp.logger.Debug("File queued for processing", "path", filePath, "format", format)
		return nil
	default:
		return fmt.Errorf("processing queue is full")
	}
}

// worker processes jobs from the queue
func (fp *FileProcessor) worker(workerID int) {
	defer fp.wg.Done()

	fp.logger.Debug("Worker started", "worker_id", workerID)

	for {
		select {
		case <-fp.ctx.Done():
			fp.logger.Debug("Worker stopping", "worker_id", workerID)
			return

		case job := <-fp.jobQueue:
			fp.logger.Debug("Processing job", "worker_id", workerID, "job_id", job.ID, "path", job.FilePath)

			if err := fp.processJob(job); err != nil {
				fp.logger.Error("Job processing failed", "worker_id", workerID, "job_id", job.ID, "error", err)
			} else {
				fp.logger.Debug("Job completed successfully", "worker_id", workerID, "job_id", job.ID)
			}
		}
	}
}

// processJob processes a single job
func (fp *FileProcessor) processJob(job *ProcessingJob) error {
	fp.logger.Debug("Processing file", "path", job.FilePath, "format", job.Format)

	// Read file
	data, err := fp.ReadFile(job.FilePath)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	// Process based on format
	switch job.Format {
	case "ifc":
		return fp.processIFCFile(job, data)
	case "bas_csv":
		return fp.processBASCSVFile(job, data)
	default:
		return fmt.Errorf("unsupported file format: %s", job.Format)
	}
}

// processIFCFile processes an IFC file
func (fp *FileProcessor) processIFCFile(job *ProcessingJob, data []byte) error {
	fp.logger.Info("Processing IFC file", "path", job.FilePath, "size", len(data))

	// IFC processing logic would go here
	// For now, just validate that it's a valid IFC file
	if len(data) < 100 {
		return fmt.Errorf("file too small to be a valid IFC file")
	}

	// Check for IFC header
	if !fp.isIFCFile(data) {
		return fmt.Errorf("file does not appear to be a valid IFC file")
	}

	fp.logger.Info("IFC file validated successfully", "path", job.FilePath)
	return nil
}

// isIFCFile checks if data represents an IFC file
func (fp *FileProcessor) isIFCFile(data []byte) bool {
	// Simple IFC file detection
	ifcHeader := "ISO-10303-21"
	return len(data) > len(ifcHeader) && string(data[:len(ifcHeader)]) == ifcHeader
}

// processBASCSVFile processes a BAS CSV export file
func (fp *FileProcessor) processBASCSVFile(job *ProcessingJob, data []byte) error {
	fp.logger.Info("Processing BAS CSV file", "path", job.FilePath, "size", len(data))

	// Validate CSV file structure
	if len(data) < 10 {
		return fmt.Errorf("file too small to be a valid CSV file")
	}

	// Check for CSV-like content (has commas or headers)
	if !fp.isCSVFile(data) {
		return fmt.Errorf("file does not appear to be a valid CSV file")
	}

	fp.logger.Info("BAS CSV file validated successfully", "path", job.FilePath)

	// NOTE: BAS import should be performed via CLI command or API endpoint
	// File processor validates file is ready, actual import happens via:
	// - CLI: arx bas import <file> --building <id>
	// - API: POST /api/v1/bas/import
	// This allows user control over building/system mapping

	return nil
}

// isCSVFile checks if data represents a CSV file
func (fp *FileProcessor) isCSVFile(data []byte) bool {
	// Simple CSV detection - check for comma-separated values in first line
	firstLine := ""
	for i, b := range data {
		if b == '\n' || i > 500 {
			break
		}
		firstLine += string(b)
	}

	// CSV should have at least one comma in header
	return len(firstLine) > 0 && (data[0] != '#') && containsComma(firstLine)
}

// containsComma checks if a string contains a comma
func containsComma(s string) bool {
	for _, c := range s {
		if c == ',' {
			return true
		}
	}
	return false
}
