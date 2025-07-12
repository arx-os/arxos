# Arxos Logging Standardization Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Components](#key-components)
4. [Usage Examples](#usage-examples)
5. [Log Format Standards](#log-format-standards)
6. [Configuration](#configuration)
7. [Performance Best Practices](#performance-best-practices)
8. [Monitoring](#monitoring)
9. [Best Practices](#best-practices)
10. [Migration Guide](#migration-guide)
11. [Troubleshooting](#troubleshooting)
12. [Future Enhancements](#future-enhancements)

## Overview

This guide provides comprehensive standards for logging across the Arxos platform, ensuring consistent, performant, and maintainable logging practices across all components.

## Architecture

The logging system follows a distributed architecture with centralized aggregation:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Python        │
│   (JavaScript)  │    │   (Go)          │    │   Microservice  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Log           │
                    │   Aggregation   │
                    │   Service       │
                    └─────────────────┘
```

## Key Components

### 1. Backend (Go) - LoggingService
- **Location**: `arx-backend/services/logging.go`
- **Features**: Structured logging, correlation tracking, business metrics, performance monitoring
- **Key Methods**:
  - `Log()` - Basic logging with context
  - `LogAPIRequest()` - API request logging
  - `LogBusinessEvent()` - Business event logging
  - `LogSecurityEvent()` - Security event logging

### 2. Python Microservice - ArxLogger
- **Location**: `arx_svg_parser/utils/logger.py`
- **Features**: JSON structured logging, log rotation, performance tracking
- **Key Methods**:
  - `info()`, `debug()`, `warning()`, `error()` - Basic logging
  - `performance()` - Performance metrics
  - `business_event()` - Business events
  - `api_request()` - API requests

### 3. Frontend (JavaScript) - ArxLogger
- **Location**: `arx-web-frontend/static/js/arx-logger.js`
- **Features**: Structured logging, batch processing, remote logging
- **Key Methods**:
  - `info()`, `warn()`, `error()` - Basic logging
  - `apiRequest()` - API request logging
  - `businessEvent()` - Business events
  - `performance()` - Performance tracking

### 4. Log Aggregation Service
- **Location**: `arx-backend/handlers/logging.go`
- **Features**: Centralized log collection, metrics aggregation, log retrieval
- **Endpoints**:
  - `POST /api/logs/aggregate` - Log aggregation
  - `GET /api/logs/retrieve` - Log retrieval
  - `GET /api/logs/metrics` - Business metrics
  - `GET /api/logs/performance` - Performance stats

## Usage Examples

### Backend (Go)
```go
// Basic logging
loggingService.Log(services.LogLevelInfo, "User logged in", ctx)

// API request logging
loggingService.LogAPIRequest(ctx, 200, time.Millisecond*150, 1024)

// Business event logging
loggingService.LogBusinessEvent(ctx, "user", "login", map[string]interface{}{
    "user_id": 123,
    "ip_address": "192.168.1.1",
})

// Security event logging
loggingService.LogSecurityEvent(ctx, "login_attempt", "info", map[string]interface{}{
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
})
```

### Python Microservice
```python
from utils.logger import logger, set_context

# Set context
set_context(correlation_id="corr_123", user_id=456)

# Basic logging
logger.info("Processing SVG file", {"file_size": 1024, "format": "svg"})

# Performance tracking
@logger.performance_tracker("svg_processing")
def process_svg(file_path):
    # Processing logic
    pass

# Business events
logger.business_event("file_upload", "svg_processed", {
    "file_size": 1024,
    "processing_time": 1.5
})
```

### Frontend (JavaScript)
```javascript
// Basic logging
arxLogger.info('User clicked button', { buttonId: 'submit', page: 'login' });

// API request logging
arxLogger.apiRequest('POST', '/api/login', 200, 150, 1024);

// Business events
arxLogger.businessEvent('user_action', 'login_attempt', {
    userId: 123,
    method: 'email'
});

// Performance tracking
arxLogger.performance('data_processing', 45.2, { recordCount: 1000 });
```

## Log Format Standards

### Standard Log Entry Structure
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "message": "User logged in successfully",
  "logger": "arx-backend",
  "correlation_id": "corr_123456",
  "request_id": "req_789012",
  "user_id": 123,
  "building_id": 456,
  "endpoint": "/api/auth/login",
  "method": "POST",
  "component": "auth",
  "service": "arx-backend",
  "version": "1.0.0",
  "environment": "production",
  "metadata": {
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "processing_time_ms": 150
  }
}
```

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARN**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical system failures

## Configuration

### Environment Variables
```bash
# Log Level
ARX_LOG_LEVEL=info

# Log Aggregation
ARX_LOG_AGGREGATION_ENABLED=true
ARX_LOG_AGGREGATION_ENDPOINT=http://localhost:8080/api/logs/aggregate

# Performance Settings
ARX_LOG_BUFFER_SIZE=1000
ARX_LOG_WORKER_COUNT=4
ARX_LOG_PROCESSING_TIMEOUT=1ms
ARX_LOG_ENTRY_SIZE_LIMIT=1024

# Retention Settings
ARX_LOG_INFO_RETENTION_DAYS=30
ARX_LOG_DEBUG_RETENTION_DAYS=7
ARX_LOG_COMPRESSION_ENABLED=true
ARX_LOG_DAILY_ROTATION=true
```

## Performance Best Practices

### 1. Log Entry Size Management
- **Target**: Keep log entries under 1KB average
- **Implementation**:
  - Truncate messages exceeding size limits
  - Use structured data instead of verbose text
  - Compress large payloads when necessary

```go
// Go Backend - Size checking
const LogEntrySizeLimit = 1024 // 1KB limit

if entry.Size > LogEntrySizeLimit {
    // Truncate message if too large
    if len(entry.Message) > LogEntrySizeLimit/2 {
        entry.Message = entry.Message[:LogEntrySizeLimit/2] + "... [truncated]"
    }
}
```

```python
# Python - Size checking
LOG_ENTRY_SIZE_LIMIT = 1024  # 1KB limit

def truncate_message(message, max_length=LOG_ENTRY_SIZE_LIMIT // 2):
    if len(message) > max_length:
        return message[:max_length] + '... [truncated]'
    return message
```

```javascript
// JavaScript - Size checking
const LOG_ENTRY_SIZE_LIMIT = 1024; // 1KB limit

truncateMessage(message, maxLength = LOG_ENTRY_SIZE_LIMIT / 2) {
    if (message.length > maxLength) {
        return message.substring(0, maxLength) + '... [truncated]';
    }
    return message;
}
```

### 2. Processing Time Optimization
- **Target**: Process log entries in under 1ms
- **Implementation**:
  - Asynchronous processing with worker pools
  - Buffered logging to reduce I/O overhead
  - Performance monitoring and alerting

```go
// Go Backend - Async processing
const ProcessingTimeTarget = time.Millisecond

func (ls *LoggingService) processLogEntry(entry LogEntry) {
    start := time.Now()
    
    // Process the log entry
    ls.logger.Log(entry.Level.toZapLevel(), entry.Message, entry.Fields...)
    
    // Track processing time
    duration := time.Since(start)
    if duration > ProcessingTimeTarget {
        ls.logger.Warn("Log entry processing exceeded target time",
            zap.Duration("processing_time", duration),
            zap.Duration("target_time", ProcessingTimeTarget),
        )
    }
}
```

```python
# Python - Async processing
PROCESSING_TIME_TARGET = 0.001  # 1ms target

def _process_log_entry(self, entry):
    start_time = time.time()
    
    // Process log entry
    self.logger.handle(record)
    
    // Track processing time
    processing_time = time.time() - start_time
    if processing_time > PROCESSING_TIME_TARGET:
        self.warning("Log entry processing exceeded target time", {
            'processing_time_ms': processing_time * 1000,
            'target_time_ms': PROCESSING_TIME_TARGET * 1000
        })
```

```javascript
// JavaScript - Performance tracking
const PROCESSING_TIME_TARGET = 1; // 1ms target

trackPerformance(processingTime, entrySize) {
    if (processingTime > PROCESSING_TIME_TARGET) {
        this.performanceMetrics.slowLogs++;
        this.warn('Log entry processing exceeded target time', {
            processingTimeMs: Math.round(processingTime * 100) / 100,
            targetTimeMs: PROCESSING_TIME_TARGET
        });
    }
}
```

### 3. Storage Optimization
- **Compression**: Enable gzip compression for log files
- **Rotation**: Daily log rotation with size limits
- **Implementation**:

```go
// Go Backend - Compression and rotation
type RetentionPolicy struct {
    InfoRetentionDays  int
    DebugRetentionDays int
    CompressionEnabled bool
    DailyRotation      bool
}

var DefaultRetentionPolicy = RetentionPolicy{
    InfoRetentionDays:  30,
    DebugRetentionDays: 7,
    CompressionEnabled: true,
    DailyRotation:      true,
}
```

```python
# Python - Log rotation and compression
MAX_LOG_FILE_SIZE = 100 * 1024 * 1024  # 100MB
LOG_RETENTION_DAYS = {
    'INFO': 30,
    'DEBUG': 7,
    'WARNING': 30,
    'ERROR': 30,
    'CRITICAL': 30
}

# Rotating file handler with compression
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=MAX_LOG_FILE_SIZE,
    backupCount=30,  # 30 days retention
    encoding='utf-8'
)
```

### 4. Retention Policies
- **INFO+ logs**: 30 days retention
- **DEBUG logs**: 7 days retention
- **Implementation**:

```go
// Go Backend - Retention enforcement
func (ls *LoggingService) cleanupOldLogsByLevel(now time.Time) {
    for _, file := range logFiles {
        age := now.Sub(info.ModTime())
        shouldDelete := false
        
        // Determine retention based on file type
        if strings.Contains(file, "debug") || strings.Contains(file, "DEBUG") {
            shouldDelete = age > time.Duration(ls.retentionPolicy.DebugRetentionDays)*24*time.Hour
        } else {
            shouldDelete = age > time.Duration(ls.retentionPolicy.InfoRetentionDays)*24*time.Hour
        }
        
        if shouldDelete {
            os.Remove(file)
        }
    }
}
```

```python
# Python - Retention cleanup
def _cleanup_old_logs(self):
    now = datetime.now()
    
    for log_file in self.log_dir.glob("*.log*"):
        file_age = now - datetime.fromtimestamp(log_file.stat().st_mtime)
        
        // Determine retention based on file type
        retention_days = LOG_RETENTION_DAYS.get('INFO', 30)  # Default
        
        if 'debug' in log_file.name.lower():
            retention_days = LOG_RETENTION_DAYS.get('DEBUG', 7)
        
        if file_age.days > retention_days:
            log_file.unlink()
```

### 5. Batch Processing
- **Frontend**: Batch log entries before sending to backend
- **Backend**: Process logs in worker pools
- **Implementation**:

```javascript
// JavaScript - Batch processing
const BATCH_SIZE = 10; // Number of logs to batch
const BATCH_TIMEOUT = 5000; // 5 seconds timeout

addToBatch(logEntry) {
    this.logBuffer.push(logEntry);
    
    // Process batch if it's full
    if (this.logBuffer.length >= BATCH_SIZE) {
        this.processBatch();
    }
    
    // Set timeout for batch processing
    if (!this.batchTimeout) {
        this.batchTimeout = setTimeout(() => {
            this.processBatch();
        }, BATCH_TIMEOUT);
    }
}
```

```go
// Go Backend - Worker pool processing
func (ls *LoggingService) startLogWorkers() {
    for i := 0; i < ls.workerCount; i++ {
        ls.workersWg.Add(1)
        go ls.logWorker(i)
    }
}

func (ls *LoggingService) logWorker(id int) {
    for {
        select {
        case entry := <-ls.logBuffer:
            ls.processLogEntry(entry)
        case <-ls.stopWorkers:
            return
        }
    }
}
```

### 6. Performance Monitoring
- **Metrics**: Track processing times, entry sizes, throughput
- **Alerting**: Alert on slow processing or large entries
- **Implementation**:

```go
// Go Backend - Performance metrics
type PerformanceStats struct {
    Count       int64         `json:"count"`
    TotalTime   time.Duration `json:"total_time"`
    MinTime     time.Duration `json:"min_time"`
    MaxTime     time.Duration `json:"max_time"`
    AvgTime     time.Duration `json:"avg_time"`
    LastUpdated time.Time     `json:"last_updated"`
}
```

```python
# Python - Performance metrics
self.performanceMetrics = {
    'total_logs': 0,
    'total_size': 0,
    'avg_processing_time': 0.0,
    'slow_logs': 0,
    'large_logs': 0,
    'errors': 0,
    'last_rotation': datetime.now(),
    'compressed_files': 0
}
```

```javascript
// JavaScript - Performance metrics
this.performanceMetrics = {
    totalLogs: 0,
    totalSize: 0,
    avgProcessingTime: 0,
    slowLogs: 0,
    largeLogs: 0,
    errors: 0,
    batchSends: 0,
    failedSends: 0
};
```

## Monitoring

### Key Metrics to Monitor
1. **Processing Performance**
   - Average log processing time
   - Number of slow log entries (>1ms)
   - Log entry size distribution

2. **Storage Metrics**
   - Log file sizes
   - Compression ratios
   - Storage usage trends

3. **Retention Compliance**
   - Files deleted by retention policy
   - Compression success rate
   - Storage cleanup efficiency

4. **System Health**
   - Buffer utilization
   - Worker pool health
   - Error rates

### Alerting Thresholds
- **Processing Time**: >1ms average over 5 minutes
- **Entry Size**: >1KB average over 5 minutes
- **Error Rate**: >1% of total logs
- **Storage Usage**: >80% of allocated space
- **Buffer Full**: >90% buffer utilization

## Best Practices

### 1. Log Message Guidelines
- Use structured data over verbose text
- Include relevant context (user ID, request ID, etc.)
- Avoid logging sensitive information
- Use appropriate log levels

### 2. Performance Guidelines
- Keep log entries under 1KB
- Use async processing where possible
- Implement proper buffering
- Monitor processing times

### 3. Storage Guidelines
- Enable compression for old logs
- Implement proper rotation policies
- Monitor storage usage
- Clean up old files regularly

### 4. Security Guidelines
- Never log passwords or tokens
- Sanitize user input in logs
- Use correlation IDs for tracing
- Implement proper access controls

## Migration Guide

### From Console.log to ArxLogger
```javascript
// Before
console.log('User logged in', { userId: 123 });

// After
arxLogger.info('User logged in', { userId: 123 });
```

### From Print Statements to ArxLogger (Python)
```python
# Before
print(f"Processing file: {file_path}")

# After
logger.info("Processing file", {"file_path": file_path})
```

### From Basic Logging to Structured Logging (Go)
```go
// Before
log.Printf("User %d logged in", userID)

// After
loggingService.Log(services.LogLevelInfo, "User logged in", ctx, 
    zap.Uint("user_id", userID))
```

## Troubleshooting

### Common Issues

1. **Slow Log Processing**
   - Check worker pool configuration
   - Monitor buffer utilization
   - Review log entry sizes

2. **High Storage Usage**
   - Verify retention policies
   - Check compression settings
   - Monitor log rotation

3. **Missing Logs**
   - Check log levels
   - Verify correlation IDs
   - Review aggregation endpoints

### Debug Commands
```bash
# Check log file sizes
find /var/log/arxos -name "*.log*" -exec ls -lh {} \;

# Monitor log processing
tail -f /var/log/arxos/application.log | grep "processing_time"

# Check retention cleanup
find /var/log/arxos -name "*.log*" -mtime +30 -ls
```

## Future Enhancements

### Planned Features
1. **Real-time Log Streaming**
   - WebSocket-based log streaming
   - Real-time dashboard updates
   - Live log filtering

2. **Advanced Analytics**
   - Log pattern recognition
   - Anomaly detection
   - Predictive analytics

3. **Enhanced Security**
   - Log encryption at rest
   - Digital signatures
   - Audit trail verification

4. **Integration Improvements**
   - ELK Stack integration
   - Prometheus metrics
   - Grafana dashboards

### Performance Targets
- **Processing Time**: <0.5ms per entry
- **Entry Size**: <512B average
- **Throughput**: >10,000 entries/second
- **Storage Efficiency**: >90% compression ratio

---

This guide ensures consistent, performant, and maintainable logging across the entire Arxos platform while meeting production requirements for performance and storage efficiency. 