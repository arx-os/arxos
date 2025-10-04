package middleware

import (
	"compress/gzip"
	"io"
	"net/http"
	"strings"
	"sync"
)

// CompressionMiddleware provides response compression
func CompressionMiddleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if client accepts gzip encoding
			if !strings.Contains(r.Header.Get("Accept-Encoding"), "gzip") {
				next.ServeHTTP(w, r)
				return
			}

			// Skip compression for certain content types
			if shouldSkipCompression(r) {
				next.ServeHTTP(w, r)
				return
			}

			// Create gzip writer
			gz := gzipWriterPool.Get().(*gzip.Writer)
			defer gzipWriterPool.Put(gz)

			gz.Reset(w)
			defer gz.Close()

			// Set headers
			w.Header().Set("Content-Encoding", "gzip")
			w.Header().Set("Vary", "Accept-Encoding")

			// Wrap response writer
			gzw := &gzipResponseWriter{
				ResponseWriter: w,
				Writer:         gz,
			}

			next.ServeHTTP(gzw, r)
		})
	}
}

// gzipResponseWriter wraps http.ResponseWriter with gzip compression
type gzipResponseWriter struct {
	http.ResponseWriter
	Writer io.Writer
}

// Write writes data to the gzip writer
func (gzw *gzipResponseWriter) Write(b []byte) (int, error) {
	return gzw.Writer.Write(b)
}

// WriteHeader writes the HTTP header
func (gzw *gzipResponseWriter) WriteHeader(code int) {
	gzw.ResponseWriter.WriteHeader(code)
}

// Flush flushes the gzip writer
func (gzw *gzipResponseWriter) Flush() {
	if flusher, ok := gzw.Writer.(http.Flusher); ok {
		flusher.Flush()
	}
}

// gzipWriterPool is a pool of gzip writers for reuse
var gzipWriterPool = sync.Pool{
	New: func() interface{} {
		return gzip.NewWriter(nil)
	},
}

// shouldSkipCompression determines if compression should be skipped
func shouldSkipCompression(r *http.Request) bool {
	// Skip compression for certain content types
	contentType := r.Header.Get("Content-Type")
	skipTypes := []string{
		"image/",
		"video/",
		"audio/",
		"application/zip",
		"application/gzip",
		"application/x-gzip",
		"application/x-compress",
		"application/x-compressed",
	}

	for _, skipType := range skipTypes {
		if strings.Contains(contentType, skipType) {
			return true
		}
	}

	// Skip compression for very small responses
	if r.ContentLength > 0 && r.ContentLength < 1024 {
		return true
	}

	// Skip compression for WebSocket upgrades
	if r.Header.Get("Upgrade") == "websocket" {
		return true
	}

	return false
}

// CompressionLevelMiddleware provides configurable compression levels
func CompressionLevelMiddleware(level int) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if client accepts gzip encoding
			if !strings.Contains(r.Header.Get("Accept-Encoding"), "gzip") {
				next.ServeHTTP(w, r)
				return
			}

			// Skip compression for certain content types
			if shouldSkipCompression(r) {
				next.ServeHTTP(w, r)
				return
			}

			// Create gzip writer with specified level
			gz, err := gzip.NewWriterLevel(w, level)
			if err != nil {
				// Fallback to default compression
				next.ServeHTTP(w, r)
				return
			}
			defer gz.Close()

			// Set headers
			w.Header().Set("Content-Encoding", "gzip")
			w.Header().Set("Vary", "Accept-Encoding")

			// Wrap response writer
			gzw := &gzipResponseWriter{
				ResponseWriter: w,
				Writer:         gz,
			}

			next.ServeHTTP(gzw, r)
		})
	}
}

// BrotliCompressionMiddleware provides Brotli compression (if available)
func BrotliCompressionMiddleware() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if client accepts brotli encoding
			acceptEncoding := r.Header.Get("Accept-Encoding")
			if !strings.Contains(acceptEncoding, "br") {
				next.ServeHTTP(w, r)
				return
			}

			// Skip compression for certain content types
			if shouldSkipCompression(r) {
				next.ServeHTTP(w, r)
				return
			}

			// For now, fallback to gzip since we don't have brotli implementation
			// In a real implementation, you would use a brotli library
			CompressionMiddleware()(next).ServeHTTP(w, r)
		})
	}
}

// CompressionStats tracks compression statistics
type CompressionStats struct {
	RequestsCompressed int64   `json:"requests_compressed"`
	BytesSaved         int64   `json:"bytes_saved"`
	CompressionRatio   float64 `json:"compression_ratio"`
	AverageSavings     float64 `json:"average_savings"`
}

// CompressionMetricsMiddleware provides compression metrics
func CompressionMetricsMiddleware() func(http.Handler) http.Handler {
	stats := &CompressionStats{}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Wrap response writer to track metrics
			mw := &metricsResponseWriter{
				ResponseWriter: w,
				stats:          stats,
			}

			next.ServeHTTP(mw, r)
		})
	}
}

// metricsResponseWriter wraps http.ResponseWriter to track compression metrics
type metricsResponseWriter struct {
	http.ResponseWriter
	stats *CompressionStats
}

// Write tracks the number of bytes written
func (mrw *metricsResponseWriter) Write(b []byte) (int, error) {
	n, err := mrw.ResponseWriter.Write(b)

	// Track metrics (simplified - in real implementation you'd track original vs compressed size)
	mrw.stats.RequestsCompressed++

	return n, err
}

// GetCompressionStats returns current compression statistics
func GetCompressionStats() *CompressionStats {
	// This would be implemented with proper metrics collection
	return &CompressionStats{}
}
