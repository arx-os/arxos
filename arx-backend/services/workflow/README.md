# Workflow Automation Services

This directory contains the Go implementation of workflow automation services, migrated from the Python implementation. The services provide comprehensive workflow orchestration, execution, monitoring, and analytics capabilities.

## Architecture

The workflow automation system consists of four main components:

### 1. WorkflowEngine (`workflow_engine.go`)
- **Purpose**: Core workflow orchestration and execution engine
- **Features**:
  - Workflow definition management
  - Execution scheduling and queuing
  - Step-by-step workflow execution
  - Condition evaluation and branching
  - Error handling and retry logic
  - Database persistence

### 2. WorkflowManager (`workflow_manager.go`)
- **Purpose**: Workflow lifecycle management and administration
- **Features**:
  - Template-based workflow creation
  - Scheduling and cron-based execution
  - Trigger management (file changes, API calls, etc.)
  - Workflow versioning and updates
  - Bulk operations

### 3. WorkflowExecutor (`workflow_executor.go`)
- **Purpose**: Individual step execution and processing
- **Features**:
  - Step type execution (validation, export, transform, etc.)
  - File operations (read, write, copy, move, delete)
  - API calls and external service integration
  - Parallel execution support
  - Retry logic with exponential backoff
  - Performance monitoring

### 4. WorkflowMonitor (`workflow_monitor.go`)
- **Purpose**: Monitoring, analytics, and alerting
- **Features**:
  - Real-time metrics collection
  - Performance analytics and reporting
  - Alert generation and management
  - Trend analysis and recommendations
  - Custom report generation

## Data Models

### Core Entities

#### WorkflowDefinition
```go
type WorkflowDefinition struct {
    WorkflowID    string                 `json:"workflow_id" gorm:"primaryKey"`
    Name          string                 `json:"name"`
    Description   string                 `json:"description"`
    WorkflowType  WorkflowType           `json:"workflow_type"`
    Steps         []WorkflowStep         `json:"steps" gorm:"type:json"`
    Triggers      []map[string]interface{} `json:"triggers" gorm:"type:json"`
    Schedule      *string                `json:"schedule"`
    Timeout       int                    `json:"timeout"`
    MaxRetries    int                    `json:"max_retries"`
    ErrorHandling map[string]interface{} `json:"error_handling" gorm:"type:json"`
    Metadata      map[string]interface{} `json:"metadata" gorm:"type:json"`
    CreatedAt     time.Time              `json:"created_at"`
    UpdatedAt     time.Time              `json:"updated_at"`
}
```

#### WorkflowExecution
```go
type WorkflowExecution struct {
    ExecutionID   string                 `json:"execution_id" gorm:"primaryKey"`
    WorkflowID    string                 `json:"workflow_id"`
    Status        WorkflowStatus         `json:"status"`
    StartTime     time.Time              `json:"start_time"`
    EndTime       *time.Time             `json:"end_time"`
    CurrentStep   *string                `json:"current_step"`
    Progress      float64                `json:"progress"`
    Result        map[string]interface{} `json:"result" gorm:"type:json"`
    Error         *string                `json:"error"`
    Context       map[string]interface{} `json:"context" gorm:"type:json"`
    Metadata      map[string]interface{} `json:"metadata" gorm:"type:json"`
}
```

#### WorkflowStep
```go
type WorkflowStep struct {
    StepID      string                 `json:"step_id"`
    Name        string                 `json:"name"`
    StepType    StepType               `json:"step_type"`
    Parameters  map[string]interface{} `json:"parameters"`
    Conditions  []map[string]interface{} `json:"conditions"`
    Timeout     int                    `json:"timeout"`
    RetryCount  int                    `json:"retry_count"`
    RetryDelay  int                    `json:"retry_delay"`
    Parallel    bool                   `json:"parallel"`
    Required    bool                   `json:"required"`
}
```

## Workflow Types

### Supported Workflow Types
- `validation` - Data validation workflows
- `export` - Data export and format conversion
- `reporting` - Report generation workflows
- `data_processing` - Data transformation and processing
- `integration` - System integration workflows
- `cleanup` - Maintenance and cleanup workflows

### Supported Step Types
- `validation` - Data validation steps
- `export` - Data export steps
- `transform` - Data transformation steps
- `notify` - Notification steps
- `condition` - Conditional logic steps
- `loop` - Loop execution steps
- `parallel` - Parallel execution steps
- `delay` - Time delay steps
- `api_call` - External API calls
- `file_operation` - File system operations

## Usage Examples

### Creating a Workflow

```go
// Create workflow definition
workflowData := map[string]interface{}{
    "workflow_id": "bim_validation_workflow",
    "name": "BIM Validation Workflow",
    "description": "Automated BIM validation with fix application",
    "workflow_type": "validation",
    "steps": []map[string]interface{}{
        {
            "step_id": "validate_floorplan",
            "name": "Validate Floorplan",
            "step_type": "validation",
            "parameters": map[string]interface{}{
                "service": "bim_health_checker",
                "auto_apply_fixes": true,
            },
            "timeout": 300,
            "retry_count": 2,
        },
        {
            "step_id": "apply_fixes",
            "name": "Apply Fixes",
            "step_type": "api_call",
            "parameters": map[string]interface{}{
                "endpoint": "/bim-health/apply-fixes",
                "method": "POST",
            },
            "conditions": []map[string]interface{}{
                {
                    "type": "greater_than",
                    "field": "issues_found",
                    "value": 0,
                },
            },
        },
    },
    "timeout": 900,
    "max_retries": 2,
}

workflow, err := engine.CreateWorkflow(workflowData)
```

### Executing a Workflow

```go
// Execute workflow with context
context := map[string]interface{}{
    "file_path": "/path/to/bim/file.json",
    "user_id": "user123",
}

executionID, err := engine.ExecuteWorkflow("bim_validation_workflow", context)
if err != nil {
    log.Printf("Failed to execute workflow: %v", err)
    return
}

// Check execution status
status, err := engine.GetWorkflowStatus(executionID)
if err != nil {
    log.Printf("Failed to get status: %v", err)
    return
}

fmt.Printf("Execution status: %s, Progress: %.2f%%\n", 
    status["status"], status["progress"])
```

### Scheduling a Workflow

```go
// Schedule workflow to run daily at 2 AM
schedule, err := manager.ScheduleWorkflow("bim_validation_workflow", "0 2 * * *")
if err != nil {
    log.Printf("Failed to schedule workflow: %v", err)
    return
}

fmt.Printf("Scheduled workflow: %s\n", schedule.ScheduleID)
```

### Monitoring and Analytics

```go
// Get current metrics
metrics := monitor.GetMetrics()
fmt.Printf("Total workflows: %d, Active executions: %d\n", 
    metrics.TotalWorkflows, metrics.ActiveWorkflows)

// Generate analytics report
startDate := time.Now().AddDate(0, 0, -30) // Last 30 days
endDate := time.Now()
report, err := monitor.GenerateReport(startDate, endDate)
if err != nil {
    log.Printf("Failed to generate report: %v", err)
    return
}

fmt.Printf("Report generated: %d executions, %.2f%% success rate\n",
    report["executions"].(map[string]interface{})["total"],
    report["executions"].(map[string]interface{})["success_rate"])
```

## Migration from Python

### Key Improvements

1. **Performance**: Go's compiled nature provides better performance for workflow execution
2. **Concurrency**: Native goroutine support for parallel step execution
3. **Type Safety**: Strong typing reduces runtime errors and improves maintainability
4. **Database Integration**: Direct GORM integration for better data persistence
5. **Memory Efficiency**: Lower memory footprint compared to Python
6. **Enterprise Features**: Enhanced monitoring, analytics, and alerting capabilities

### Migrated Features

- ✅ Workflow definition and execution
- ✅ Step-by-step workflow processing
- ✅ Conditional logic and branching
- ✅ Error handling and retry mechanisms
- ✅ Scheduling and cron-based execution
- ✅ Template-based workflow creation
- ✅ File operations and API calls
- ✅ Parallel execution support
- ✅ Performance monitoring and analytics
- ✅ Alert generation and management
- ✅ Database persistence with GORM

### New Features Added

- 🔄 Real-time execution monitoring
- 📊 Advanced analytics and reporting
- 🚨 Intelligent alerting system
- 📈 Performance trend analysis
- 💡 Optimization recommendations
- 🔧 Template management system
- ⚡ Enhanced parallel processing
- 🛡️ Improved error recovery

## Database Schema

The workflow services use the following database tables:

### workflow_definitions
- `workflow_id` (PK) - Unique workflow identifier
- `name` - Workflow name
- `description` - Workflow description
- `workflow_type` - Type of workflow
- `steps` (JSON) - Workflow steps configuration
- `triggers` (JSON) - Workflow triggers
- `schedule` - Cron schedule expression
- `timeout` - Execution timeout in seconds
- `max_retries` - Maximum retry attempts
- `error_handling` (JSON) - Error handling configuration
- `metadata` (JSON) - Additional metadata
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### workflow_executions
- `execution_id` (PK) - Unique execution identifier
- `workflow_id` - Associated workflow ID
- `status` - Execution status
- `start_time` - Execution start time
- `end_time` - Execution end time
- `current_step` - Currently executing step
- `progress` - Execution progress percentage
- `result` (JSON) - Execution results
- `error` - Error message if failed
- `context` (JSON) - Execution context
- `metadata` (JSON) - Execution metadata

### step_executions
- `step_execution_id` (PK) - Unique step execution identifier
- `workflow_execution_id` - Associated workflow execution
- `step_id` - Step identifier
- `status` - Step execution status
- `start_time` - Step start time
- `end_time` - Step end time
- `result` (JSON) - Step execution results
- `error` - Step error message
- `retry_count` - Number of retry attempts
- `duration` - Step execution duration

### workflow_schedules
- `schedule_id` (PK) - Unique schedule identifier
- `workflow_id` - Associated workflow ID
- `cron_expression` - Cron schedule expression
- `enabled` - Schedule enabled flag
- `last_run` - Last execution time
- `next_run` - Next scheduled execution time
- `created_at` - Creation timestamp

### workflow_triggers
- `trigger_id` (PK) - Unique trigger identifier
- `workflow_id` - Associated workflow ID
- `trigger_type` - Type of trigger
- `conditions` (JSON) - Trigger conditions
- `enabled` - Trigger enabled flag
- `created_at` - Creation timestamp

### workflow_templates
- `template_id` (PK) - Unique template identifier
- `name` - Template name
- `description` - Template description
- `category` - Template category
- `workflow_type` - Associated workflow type
- `steps` (JSON) - Template steps
- `parameters` (JSON) - Template parameters
- `tags` (JSON) - Template tags
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### workflow_alerts
- `alert_id` (PK) - Unique alert identifier
- `workflow_id` - Associated workflow ID
- `execution_id` - Associated execution ID
- `alert_type` - Type of alert
- `severity` - Alert severity level
- `message` - Alert message
- `details` (JSON) - Alert details
- `acknowledged` - Acknowledgment flag
- `created_at` - Creation timestamp
- `acknowledged_at` - Acknowledgment timestamp

### workflow_performance
- `workflow_id` (PK) - Workflow identifier
- `total_executions` - Total execution count
- `successful_executions` - Successful execution count
- `failed_executions` - Failed execution count
- `average_duration` - Average execution duration
- `min_duration` - Minimum execution duration
- `max_duration` - Maximum execution duration
- `last_executed` - Last execution time
- `success_rate` - Success rate percentage
- `updated_at` - Last update timestamp

## Configuration

The workflow services can be configured through environment variables:

```bash
# Database configuration
WORKFLOW_DB_HOST=localhost
WORKFLOW_DB_PORT=5432
WORKFLOW_DB_NAME=arxos_workflows
WORKFLOW_DB_USER=workflow_user
WORKFLOW_DB_PASSWORD=workflow_pass

# Execution configuration
WORKFLOW_MAX_CONCURRENT_EXECUTIONS=10
WORKFLOW_DEFAULT_TIMEOUT=1800
WORKFLOW_DEFAULT_RETRIES=3

# Monitoring configuration
WORKFLOW_METRICS_INTERVAL=60
WORKFLOW_ALERT_CHECK_INTERVAL=300
WORKFLOW_PERFORMANCE_UPDATE_INTERVAL=3600
```

## API Endpoints

The workflow services expose the following REST API endpoints:

### Workflow Management
- `POST /api/workflows` - Create workflow
- `GET /api/workflows` - List workflows
- `GET /api/workflows/{id}` - Get workflow details
- `PUT /api/workflows/{id}` - Update workflow
- `DELETE /api/workflows/{id}` - Delete workflow

### Workflow Execution
- `POST /api/workflows/{id}/execute` - Execute workflow
- `GET /api/executions/{id}` - Get execution status
- `DELETE /api/executions/{id}` - Cancel execution
- `GET /api/executions` - List executions

### Scheduling
- `POST /api/workflows/{id}/schedule` - Schedule workflow
- `GET /api/schedules` - List schedules
- `PUT /api/schedules/{id}/enable` - Enable schedule
- `PUT /api/schedules/{id}/disable` - Disable schedule
- `DELETE /api/schedules/{id}` - Delete schedule

### Monitoring
- `GET /api/metrics` - Get current metrics
- `GET /api/alerts` - List alerts
- `PUT /api/alerts/{id}/acknowledge` - Acknowledge alert
- `GET /api/performance` - Get performance data
- `GET /api/reports` - Generate analytics report
- `GET /api/trends` - Get execution trends
- `GET /api/recommendations` - Get optimization recommendations

## Testing

Run the workflow services tests:

```bash
cd arxos/arx-backend/services/workflow
go test -v ./...
```

## Performance Targets

- **Workflow Execution**: Complete within 10 minutes
- **Success Rate**: 95%+ workflow success rate
- **Error Recovery**: Automated recovery for 80%+ of failures
- **Real-time Monitoring**: Status updates every 30 seconds
- **Concurrent Executions**: Support for 100+ concurrent workflows
- **Database Performance**: Sub-second query response times

## Future Enhancements

1. **Advanced Scheduling**: Support for complex cron expressions and calendar-based scheduling
2. **Workflow Versioning**: Version control for workflow definitions
3. **Visual Workflow Builder**: Web-based workflow design interface
4. **Integration Hub**: Pre-built connectors for common services
5. **Machine Learning**: Predictive analytics for workflow optimization
6. **Distributed Execution**: Multi-node workflow execution
7. **Real-time Collaboration**: Multi-user workflow editing
8. **Advanced Analytics**: Custom dashboard and reporting tools

## Contributing

When contributing to the workflow services:

1. Follow Go best practices and coding standards
2. Add comprehensive unit tests for new features
3. Update documentation for API changes
4. Ensure database migrations are backward compatible
5. Test performance impact of changes
6. Follow the existing error handling patterns

## License

This workflow automation system is part of the Arxos project and follows the same licensing terms. 