package middleware

import (
	"bytes"
	"compress/gzip"
	"compress/zlib"
	"io"
	"net/http"
	"strings"
	"sync"

	"go.uber.org/zap"
)

// CompressionMiddleware handles request and response compression
type CompressionMiddleware struct {
	config CompressionConfig
	logger *zap.Logger
	pool   *CompressionPool
}

// CompressionConfig defines compression configuration
type CompressionConfig struct {
	Enabled             bool     `yaml:"enabled"`
	MinSize             int      `yaml:"min_size"`
	CompressionLevel    int      `yaml:"compression_level"`
	SupportedEncodings  []string `yaml:"supported_encodings"`
	ContentTypes        []string `yaml:"content_types"`
	ExcludePaths        []string `yaml:"exclude_paths"`
	RequestCompression  bool     `yaml:"request_compression"`
	ResponseCompression bool     `yaml:"response_compression"`
}

// CompressionPool manages compression buffers and writers
type CompressionPool struct {
	gzipWriters sync.Pool
	zlibWriters sync.Pool
	gzipReaders sync.Pool
	zlibReaders sync.Pool
	buffers     sync.Pool
}

// CompressedResponse wraps a compressed response
type CompressedResponse struct {
	http.ResponseWriter
	writer     io.Writer
	buffer     *bytes.Buffer
	encoding   string
	compressed bool
	written    bool
}

// NewCompressionMiddleware creates a new compression middleware
func NewCompressionMiddleware(config CompressionConfig) *CompressionMiddleware {
	logger, err := zap.NewProduction()
	if err != nil {
		logger = zap.NewNop()
	}

	cm := &CompressionMiddleware{
		config: config,
		logger: logger,
		pool:   &CompressionPool{},
	}

	// Initialize pools
	cm.initializePools()

	return cm
}

// initializePools initializes compression pools
func (cm *CompressionMiddleware) initializePools() {
	// Gzip writers pool
	cm.pool.gzipWriters.New = func() interface{} {
		buffer := &bytes.Buffer{}
		writer, err := gzip.NewWriterLevel(buffer, cm.config.CompressionLevel)
		if err != nil {
			writer, _ = gzip.NewWriter(buffer)
		}
		return &gzipWriter{buffer: buffer, writer: writer}
	}

	// Zlib writers pool
	cm.pool.zlibWriters.New = func() interface{} {
		buffer := &bytes.Buffer{}
		writer, err := zlib.NewWriterLevel(buffer, cm.config.CompressionLevel)
		if err != nil {
			writer, _ = zlib.NewWriter(buffer)
		}
		return &zlibWriter{buffer: buffer, writer: writer}
	}

	// Buffer pool
	cm.pool.buffers.New = func() interface{} {
		return &bytes.Buffer{}
	}
}

// gzipWriter wraps gzip writer with buffer
type gzipWriter struct {
	buffer *bytes.Buffer
	writer *gzip.Writer
}

// zlibWriter wraps zlib writer with buffer
type zlibWriter struct {
	buffer *bytes.Buffer
	writer *zlib.Writer
}

// Handle handles compression middleware
func (cm *CompressionMiddleware) Handle(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !cm.config.Enabled {
			next.ServeHTTP(w, r)
			return
		}

		// Check if path should be excluded
		if cm.isPathExcluded(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}

		// Handle request compression
		if cm.config.RequestCompression {
			r = cm.handleRequestCompression(r)
		}

		// Handle response compression
		if cm.config.ResponseCompression {
			w = cm.handleResponseCompression(w, r)
		}

		next.ServeHTTP(w, r)
	})
}

// handleRequestCompression handles request decompression
func (cm *CompressionMiddleware) handleRequestCompression(r *http.Request) *http.Request {
	contentEncoding := r.Header.Get("Content-Encoding")
	if contentEncoding == "" {
		return r
	}

	// Check if we support this encoding
	if !cm.isEncodingSupported(contentEncoding) {
		cm.logger.Warn("Unsupported content encoding",
			zap.String("encoding", contentEncoding),
			zap.String("url", r.URL.String()),
		)
		return r
	}

	// Decompress request body
	originalBody := r.Body
	if originalBody == nil {
		return r
	}

	var reader io.Reader
	var err error

	switch contentEncoding {
	case "gzip":
		reader, err = gzip.NewReader(originalBody)
	case "deflate":
		reader, err = zlib.NewReader(originalBody)
	default:
		cm.logger.Warn("Unknown content encoding",
			zap.String("encoding", contentEncoding),
		)
		return r
	}

	if err != nil {
		cm.logger.Error("Failed to create decompression reader",
			zap.String("encoding", contentEncoding),
			zap.Error(err),
		)
		return r
	}

	// Read decompressed body
	decompressedBody, err := io.ReadAll(reader)
	if err != nil {
		cm.logger.Error("Failed to decompress request body",
			zap.String("encoding", contentEncoding),
			zap.Error(err),
		)
		return r
	}

	// Create new request with decompressed body
	newBody := io.NopCloser(bytes.NewReader(decompressedBody))
	r.Body = newBody
	r.ContentLength = int64(len(decompressedBody))
	r.Header.Del("Content-Encoding")

	cm.logger.Debug("Request decompressed",
		zap.String("encoding", contentEncoding),
		zap.Int("original_size", int(r.ContentLength)),
		zap.Int("decompressed_size", len(decompressedBody)),
	)

	return r
}

// handleResponseCompression handles response compression
func (cm *CompressionMiddleware) handleResponseCompression(w http.ResponseWriter, r *http.Request) http.ResponseWriter {
	// Check if client accepts compression
	acceptEncoding := r.Header.Get("Accept-Encoding")
	if acceptEncoding == "" {
		return w
	}

	// Determine best encoding
	encoding := cm.selectEncoding(acceptEncoding)
	if encoding == "" {
		return w
	}

	// Create compressed response writer
	compressedWriter := &CompressedResponse{
		ResponseWriter: w,
		encoding:       encoding,
		buffer:         cm.pool.buffers.Get().(*bytes.Buffer),
	}

	return compressedWriter
}

// selectEncoding selects the best compression encoding
func (cm *CompressionMiddleware) selectEncoding(acceptEncoding string) string {
	encodings := strings.Split(acceptEncoding, ",")

	for _, encoding := range encodings {
		encoding = strings.TrimSpace(encoding)
		if strings.Contains(encoding, ";") {
			encoding = strings.Split(encoding, ";")[0]
		}

		if cm.isEncodingSupported(encoding) {
			return encoding
		}
	}

	return ""
}

// isEncodingSupported checks if encoding is supported
func (cm *CompressionMiddleware) isEncodingSupported(encoding string) bool {
	for _, supported := range cm.config.SupportedEncodings {
		if strings.EqualFold(encoding, supported) {
			return true
		}
	}
	return false
}

// isPathExcluded checks if path should be excluded from compression
func (cm *CompressionMiddleware) isPathExcluded(path string) bool {
	for _, excludedPath := range cm.config.ExcludePaths {
		if strings.HasPrefix(path, excludedPath) {
			return true
		}
	}
	return false
}

// isContentTypeCompressible checks if content type should be compressed
func (cm *CompressionMiddleware) isContentTypeCompressible(contentType string) bool {
	for _, compressibleType := range cm.config.ContentTypes {
		if strings.Contains(contentType, compressibleType) {
			return true
		}
	}
	return false
}

// Write writes compressed response data
func (cr *CompressedResponse) Write(data []byte) (int, error) {
	if !cr.written {
		// Check if content should be compressed
		contentType := cr.Header().Get("Content-Type")
		if !cr.isContentTypeCompressible(contentType) {
			// Don't compress, write directly
			cr.Header().Set("Content-Encoding", "")
			return cr.ResponseWriter.Write(data)
		}

		// Check minimum size
		if len(data) < cr.config.MinSize {
			// Don't compress small responses
			cr.Header().Set("Content-Encoding", "")
			return cr.ResponseWriter.Write(data)
		}

		// Set up compression
		cr.setupCompression()
		cr.written = true
	}

	// Write to compression buffer
	return cr.writer.Write(data)
}

// setupCompression sets up response compression
func (cr *CompressedResponse) setupCompression() {
	// Set content encoding header
	cr.Header().Set("Content-Encoding", cr.encoding)
	cr.Header().Set("Vary", "Accept-Encoding")

	// Create compression writer
	switch cr.encoding {
	case "gzip":
		gzipWriter := cr.pool.gzipWriters.Get().(*gzipWriter)
		gzipWriter.buffer.Reset()
		gzipWriter.writer.Reset(gzipWriter.buffer)
		cr.writer = gzipWriter.writer
		cr.compressed = true
	case "deflate":
		zlibWriter := cr.pool.zlibWriters.Get().(*zlibWriter)
		zlibWriter.buffer.Reset()
		zlibWriter.writer.Reset(zlibWriter.buffer)
		cr.writer = zlibWriter.writer
		cr.compressed = true
	}
}

// Close closes the compressed response
func (cr *CompressedResponse) Close() error {
	if cr.compressed {
		// Close compression writer
		if closer, ok := cr.writer.(io.Closer); ok {
			closer.Close()
		}

		// Get compressed data
		var compressedData []byte
		switch cr.encoding {
		case "gzip":
			gzipWriter := cr.writer.(*gzip.Writer)
			compressedData = gzipWriter.buffer.Bytes()
		case "deflate":
			zlibWriter := cr.writer.(*zlib.Writer)
			compressedData = zlibWriter.buffer.Bytes()
		}

		// Write compressed data
		cr.ResponseWriter.Write(compressedData)

		// Return writers to pool
		switch cr.encoding {
		case "gzip":
			cr.pool.gzipWriters.Put(cr.writer)
		case "deflate":
			cr.pool.zlibWriters.Put(cr.writer)
		}
	}

	// Return buffer to pool
	cr.pool.buffers.Put(cr.buffer)

	return nil
}

// WriteHeader writes response headers
func (cr *CompressedResponse) WriteHeader(statusCode int) {
	if !cr.written {
		// Check if we should compress based on status code
		if statusCode >= 300 {
			// Don't compress error responses
			cr.Header().Set("Content-Encoding", "")
		}
	}

	cr.ResponseWriter.WriteHeader(statusCode)
}

// GetStats returns compression statistics
func (cm *CompressionMiddleware) GetStats() map[string]interface{} {
	return map[string]interface{}{
		"enabled":              cm.config.Enabled,
		"min_size":             cm.config.MinSize,
		"compression_level":    cm.config.CompressionLevel,
		"supported_encodings":  cm.config.SupportedEncodings,
		"content_types":        cm.config.ContentTypes,
		"exclude_paths":        cm.config.ExcludePaths,
		"request_compression":  cm.config.RequestCompression,
		"response_compression": cm.config.ResponseCompression,
	}
}

// UpdateConfig updates the compression configuration
func (cm *CompressionMiddleware) UpdateConfig(config CompressionConfig) error {
	cm.config = config
	cm.logger.Info("Compression configuration updated")
	return nil
}
