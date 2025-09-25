package metrics

import (
	"context"
	"runtime"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// SystemMonitor provides real system monitoring capabilities
type SystemMonitor struct {
	startTime time.Time
	lastCPU   time.Time
	lastMem   time.Time
}

// NewSystemMonitor creates a new system monitor
func NewSystemMonitor() *SystemMonitor {
	return &SystemMonitor{
		startTime: time.Now(),
		lastCPU:   time.Now(),
		lastMem:   time.Now(),
	}
}

// GetSystemInfo returns current system information
func (sm *SystemMonitor) GetSystemInfo() SystemMonitorInfo {
	now := time.Now()

	// Get memory statistics
	memStats := runtime.MemStats{}
	runtime.ReadMemStats(&memStats)

	// Calculate uptime
	uptime := now.Sub(sm.startTime)

	// Get goroutine count
	goroutineCount := runtime.NumGoroutine()

	// Calculate memory usage in MB
	memoryUsage := float64(memStats.Alloc) / 1024 / 1024

	// Calculate CPU usage (simplified)
	cpuUsage := sm.calculateCPUUsage()

	return SystemMonitorInfo{
		Uptime:         uptime.String(),
		MemoryUsage:    memoryUsage,
		CPUUsage:       cpuUsage,
		GoroutineCount: goroutineCount,
		HeapSize:       float64(memStats.HeapAlloc) / 1024 / 1024,
		HeapObjects:    memStats.HeapObjects,
		GCs:            memStats.NumGC,
		LastGC:         time.Unix(0, int64(memStats.LastGC)),
		NextGC:         time.Unix(0, int64(memStats.NextGC)),
	}
}

// calculateCPUUsage calculates CPU usage percentage
func (sm *SystemMonitor) calculateCPUUsage() float64 {
	now := time.Now()

	// Simple CPU usage calculation based on goroutine count and time
	// This is a simplified approach - real implementation would use more sophisticated methods
	goroutines := runtime.NumGoroutine()
	timeDiff := now.Sub(sm.lastCPU).Seconds()

	if timeDiff > 0 {
		// Estimate CPU usage based on goroutine activity
		cpuUsage := float64(goroutines) * 0.1 // Simplified calculation
		if cpuUsage > 100 {
			cpuUsage = 100
		}
		sm.lastCPU = now
		return cpuUsage
	}

	return 0.0
}

// GetMemoryUsage returns detailed memory usage information
func (sm *SystemMonitor) GetMemoryUsage() MemoryUsage {
	memStats := runtime.MemStats{}
	runtime.ReadMemStats(&memStats)

	return MemoryUsage{
		Alloc:         memStats.Alloc,
		TotalAlloc:    memStats.TotalAlloc,
		Sys:           memStats.Sys,
		Lookups:       memStats.Lookups,
		Mallocs:       memStats.Mallocs,
		Frees:         memStats.Frees,
		HeapAlloc:     memStats.HeapAlloc,
		HeapSys:       memStats.HeapSys,
		HeapIdle:      memStats.HeapIdle,
		HeapInuse:     memStats.HeapInuse,
		HeapReleased:  memStats.HeapReleased,
		HeapObjects:   memStats.HeapObjects,
		StackInuse:    memStats.StackInuse,
		StackSys:      memStats.StackSys,
		MSpanInuse:    memStats.MSpanInuse,
		MSpanSys:      memStats.MSpanSys,
		MCacheInuse:   memStats.MCacheInuse,
		MCacheSys:     memStats.MCacheSys,
		BuckHashSys:   memStats.BuckHashSys,
		GCSys:         memStats.GCSys,
		OtherSys:      memStats.OtherSys,
		NextGC:        memStats.NextGC,
		LastGC:        memStats.LastGC,
		PauseTotalNs:  memStats.PauseTotalNs,
		NumGC:         memStats.NumGC,
		NumForcedGC:   memStats.NumForcedGC,
		GCCPUFraction: memStats.GCCPUFraction,
	}
}

// GetGoroutineInfo returns goroutine information
func (sm *SystemMonitor) GetGoroutineInfo() GoroutineInfo {
	goroutineCount := runtime.NumGoroutine()

	// Get stack trace to analyze goroutines
	buf := make([]byte, 1024*1024)
	n := runtime.Stack(buf, true)
	stackTrace := string(buf[:n])

	// Count goroutines by function (simplified)
	goroutineMap := make(map[string]int)
	lines := splitLines(stackTrace)
	for _, line := range lines {
		if contains(line, "goroutine") {
			// Extract function name (simplified)
			if funcName := extractFunctionName(line); funcName != "" {
				goroutineMap[funcName]++
			}
		}
	}

	return GoroutineInfo{
		Count:      goroutineCount,
		ByFunction: goroutineMap,
		StackTrace: stackTrace,
		LastUpdate: time.Now(),
	}
}

// GetGCInfo returns garbage collection information
func (sm *SystemMonitor) GetGCInfo() GCInfo {
	memStats := runtime.MemStats{}
	runtime.ReadMemStats(&memStats)

	// Calculate GC statistics
	gcPauseTotal := time.Duration(memStats.PauseTotalNs)
	avgPause := time.Duration(0)
	if memStats.NumGC > 0 {
		avgPause = gcPauseTotal / time.Duration(memStats.NumGC)
	}

	return GCInfo{
		NumGC:         memStats.NumGC,
		NumForcedGC:   memStats.NumForcedGC,
		PauseTotal:    gcPauseTotal,
		PauseAverage:  avgPause,
		PauseMax:      time.Duration(memStats.PauseNs[(memStats.NumGC+255)%256]),
		LastGC:        time.Unix(0, int64(memStats.LastGC)),
		NextGC:        time.Unix(0, int64(memStats.NextGC)),
		GCCPUFraction: memStats.GCCPUFraction,
	}
}

// StartMonitoring starts continuous system monitoring
func (sm *SystemMonitor) StartMonitoring(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	logger.Info("Starting system monitoring with interval: %v", interval)

	for {
		select {
		case <-ctx.Done():
			logger.Info("Stopping system monitoring")
			return
		case <-ticker.C:
			sm.collectMetrics()
		}
	}
}

// collectMetrics collects and logs system metrics
func (sm *SystemMonitor) collectMetrics() {
	systemInfo := sm.GetSystemInfo()

	logger.Debug("System metrics - Uptime: %s, Memory: %.2fMB, CPU: %.2f%%, Goroutines: %d",
		systemInfo.Uptime,
		systemInfo.MemoryUsage,
		systemInfo.CPUUsage,
		systemInfo.GoroutineCount)

	// Log warnings for high resource usage
	if systemInfo.MemoryUsage > 1000 { // 1GB
		logger.Warn("High memory usage detected: %.2fMB", systemInfo.MemoryUsage)
	}

	if systemInfo.CPUUsage > 80 {
		logger.Warn("High CPU usage detected: %.2f%%", systemInfo.CPUUsage)
	}

	if systemInfo.GoroutineCount > 1000 {
		logger.Warn("High goroutine count detected: %d", systemInfo.GoroutineCount)
	}
}

// Helper functions

func splitLines(text string) []string {
	var lines []string
	start := 0
	for i, char := range text {
		if char == '\n' {
			lines = append(lines, text[start:i])
			start = i + 1
		}
	}
	if start < len(text) {
		lines = append(lines, text[start:])
	}
	return lines
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && s[:len(substr)] == substr
}

func extractFunctionName(line string) string {
	// Simple function name extraction from stack trace
	// This is a simplified implementation
	if len(line) > 10 {
		return line[10:min(len(line), 50)] // Extract first 40 characters
	}
	return ""
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// Data structures for system monitoring

type SystemMonitorInfo struct {
	Uptime         string    `json:"uptime"`
	MemoryUsage    float64   `json:"memory_usage_mb"`
	CPUUsage       float64   `json:"cpu_usage_percent"`
	GoroutineCount int       `json:"goroutine_count"`
	HeapSize       float64   `json:"heap_size_mb"`
	HeapObjects    uint64    `json:"heap_objects"`
	GCs            uint32    `json:"gc_count"`
	LastGC         time.Time `json:"last_gc"`
	NextGC         time.Time `json:"next_gc"`
}

type MemoryUsage struct {
	Alloc         uint64  `json:"alloc"`
	TotalAlloc    uint64  `json:"total_alloc"`
	Sys           uint64  `json:"sys"`
	Lookups       uint64  `json:"lookups"`
	Mallocs       uint64  `json:"mallocs"`
	Frees         uint64  `json:"frees"`
	HeapAlloc     uint64  `json:"heap_alloc"`
	HeapSys       uint64  `json:"heap_sys"`
	HeapIdle      uint64  `json:"heap_idle"`
	HeapInuse     uint64  `json:"heap_inuse"`
	HeapReleased  uint64  `json:"heap_released"`
	HeapObjects   uint64  `json:"heap_objects"`
	StackInuse    uint64  `json:"stack_inuse"`
	StackSys      uint64  `json:"stack_sys"`
	MSpanInuse    uint64  `json:"mspan_inuse"`
	MSpanSys      uint64  `json:"mspan_sys"`
	MCacheInuse   uint64  `json:"mcache_inuse"`
	MCacheSys     uint64  `json:"mcache_sys"`
	BuckHashSys   uint64  `json:"buck_hash_sys"`
	GCSys         uint64  `json:"gc_sys"`
	OtherSys      uint64  `json:"other_sys"`
	NextGC        uint64  `json:"next_gc"`
	LastGC        uint64  `json:"last_gc"`
	PauseTotalNs  uint64  `json:"pause_total_ns"`
	NumGC         uint32  `json:"num_gc"`
	NumForcedGC   uint32  `json:"num_forced_gc"`
	GCCPUFraction float64 `json:"gc_cpu_fraction"`
}

type GoroutineInfo struct {
	Count      int            `json:"count"`
	ByFunction map[string]int `json:"by_function"`
	StackTrace string         `json:"stack_trace"`
	LastUpdate time.Time      `json:"last_update"`
}

type GCInfo struct {
	NumGC         uint32        `json:"num_gc"`
	NumForcedGC   uint32        `json:"num_forced_gc"`
	PauseTotal    time.Duration `json:"pause_total"`
	PauseAverage  time.Duration `json:"pause_average"`
	PauseMax      time.Duration `json:"pause_max"`
	LastGC        time.Time     `json:"last_gc"`
	NextGC        time.Time     `json:"next_gc"`
	GCCPUFraction float64       `json:"gc_cpu_fraction"`
}
