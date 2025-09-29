# ArxOS Workflow Automation Platform

The ArxOS Workflow Automation Platform provides comprehensive workflow automation capabilities with n8n integration, enabling users to create, manage, and execute complex workflows for building automation, IoT device management, and business process automation.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                ArxOS Workflow Platform                      │
├─────────────────────────────────────────────────────────────┤
│  Workflow Manager  │  Trigger Manager  │  Action Manager   │
├─────────────────────────────────────────────────────────────┤
│  n8n Integration   │  HTTP API         │  CLI Tools        │
├─────────────────────────────────────────────────────────────┤
│  Schedule Triggers │  Webhook Triggers │  Event Triggers   │
│  Email Actions     │  Database Actions │  API Actions      │
│  MQTT Actions      │  Modbus Actions   │  Custom Actions   │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
internal/workflow/
├── workflow.go      # Core workflow management
├── n8n_client.go    # n8n integration client
├── triggers.go      # Trigger management system
├── actions.go       # Action management system
├── api.go          # HTTP API endpoints
├── workflow_test.go # Comprehensive test suite
└── README.md       # This documentation
```

## 🚀 Features

### **Core Workflow Management**
- **Workflow Creation**: Create and manage workflow definitions
- **Node-based Design**: Visual workflow design with nodes and connections
- **Execution Engine**: Asynchronous workflow execution with real-time status
- **Version Control**: Workflow versioning and change tracking
- **Validation**: Comprehensive workflow validation and error checking

### **Trigger System**
- **Schedule Triggers**: Cron-based scheduled execution
- **Webhook Triggers**: HTTP webhook-based triggers
- **Event Triggers**: Custom event-driven triggers
- **Manual Triggers**: User-initiated workflow execution
- **File Triggers**: File system change monitoring
- **Email Triggers**: Email-based workflow activation
- **Database Triggers**: Database change monitoring
- **MQTT Triggers**: MQTT message-based triggers
- **Modbus Triggers**: Modbus device monitoring

### **Action System**
- **Email Actions**: Send emails with templates and attachments
- **SMS Actions**: Send SMS notifications
- **Webhook Actions**: Send HTTP requests to external services
- **Database Actions**: Execute database queries and operations
- **API Actions**: Make API calls to external services
- **File Actions**: File operations (read, write, copy, move, delete)
- **Transform Actions**: Data transformation and conversion
- **Condition Actions**: Conditional logic and branching
- **Delay Actions**: Time-based delays and scheduling
- **MQTT Actions**: Publish messages to MQTT brokers
- **Modbus Actions**: Communicate with Modbus devices

### **n8n Integration**
- **Bidirectional Sync**: Sync workflows between ArxOS and n8n
- **Format Conversion**: Automatic conversion between ArxOS and n8n formats
- **API Integration**: Full n8n API integration for workflow management
- **Webhook Support**: n8n webhook integration for external triggers
- **Execution Monitoring**: Monitor n8n workflow executions

### **API and CLI**
- **REST API**: Complete HTTP API for all workflow operations
- **CLI Tools**: Command-line interface for workflow management
- **Real-time Status**: Live execution status and monitoring
- **Metrics**: Comprehensive performance metrics and statistics

## 🔧 Getting Started

### **1. Basic Workflow Creation**

```go
package main

import (
    "context"
    "github.com/arx-os/arxos/internal/workflow"
)

func main() {
    // Create workflow manager
    manager := workflow.NewWorkflowManager()
    
    // Create a simple workflow
    workflow := &workflow.Workflow{
        Name:        "Building Temperature Control",
        Description: "Automated temperature control for building zones",
        Version:     "1.0.0",
        Status:      workflow.WorkflowStatusActive,
        Nodes: []*workflow.WorkflowNode{
            {
                ID:   "trigger_1",
                Type: workflow.NodeTypeTrigger,
                Name: "Temperature Sensor",
                Position: workflow.Position{X: 0, Y: 0},
            },
            {
                ID:   "condition_1",
                Type: workflow.NodeTypeCondition,
                Name: "Temperature Check",
                Position: workflow.Position{X: 200, Y: 0},
            },
            {
                ID:   "action_1",
                Type: workflow.NodeTypeAction,
                Name: "HVAC Control",
                Position: workflow.Position{X: 400, Y: 0},
            },
        },
        Connections: []*workflow.WorkflowConnection{
            {
                ID:       "conn_1",
                FromNode: "trigger_1",
                ToNode:   "condition_1",
                FromPort: "output",
                ToPort:   "input",
            },
            {
                ID:       "conn_2",
                FromNode: "condition_1",
                ToNode:   "action_1",
                FromPort: "output",
                ToPort:   "input",
            },
        },
        Config: make(map[string]interface{}),
    }
    
    // Create workflow
    err := manager.CreateWorkflow(workflow)
    if err != nil {
        log.Fatal(err)
    }
    
    // Execute workflow
    execution, err := manager.ExecuteWorkflow(context.Background(), workflow.ID, map[string]interface{}{
        "temperature": 25.5,
        "zone": "zone_1",
    })
    if err != nil {
        log.Fatal(err)
    }
    
    log.Printf("Workflow executed: %s", execution.ID)
}
```

### **2. Using Triggers**

```go
// Create trigger manager
triggerManager := workflow.NewTriggerManager()

// Create a schedule trigger
trigger := &workflow.Trigger{
    Name:       "Daily Report Trigger",
    Type:       workflow.TriggerTypeSchedule,
    WorkflowID: "daily_report_workflow",
    Config: map[string]interface{}{
        "schedule": "0 0 9 * * *", // Every day at 9 AM
    },
    Enabled: false,
}

// Register trigger
err := triggerManager.RegisterTrigger(trigger)
if err != nil {
    log.Fatal(err)
}

// Start trigger
err = triggerManager.StartTrigger(context.Background(), trigger.ID)
if err != nil {
    log.Fatal(err)
}
```

### **3. Using Actions**

```go
// Create action manager
actionManager := workflow.NewActionManager()

// Create an email action
action := &workflow.Action{
    Name:       "Send Alert Email",
    Type:       workflow.ActionTypeEmail,
    Parameters: map[string]interface{}{
        "to":      "admin@building.com",
        "subject": "Building Alert",
        "body":    "Temperature threshold exceeded in Zone 1",
    },
    Enabled: true,
}

// Register action
err := actionManager.RegisterAction(action)
if err != nil {
    log.Fatal(err)
}

// Execute action
output, err := actionManager.ExecuteAction(context.Background(), action.ID, map[string]interface{}{
    "temperature": 30.5,
    "zone": "zone_1",
})
if err != nil {
    log.Fatal(err)
}

log.Printf("Email sent: %v", output)
```

### **4. n8n Integration**

```go
// Create n8n client
n8nClient := workflow.NewN8NClient()
n8nClient.SetCredentials("http://localhost:5678", "your-api-key")

// Convert ArxOS workflow to n8n format
n8nWorkflow := n8nClient.ConvertToN8NWorkflow(workflow)

// Create workflow in n8n
createdWorkflow, err := n8nClient.CreateWorkflow(context.Background(), n8nWorkflow)
if err != nil {
    log.Fatal(err)
}

// Activate workflow in n8n
err = n8nClient.ActivateWorkflow(context.Background(), createdWorkflow.ID)
if err != nil {
    log.Fatal(err)
}
```

## 🧩 Workflow Components

### **Workflow Nodes**

#### **Trigger Nodes**
- **Manual Trigger**: User-initiated workflow execution
- **Schedule Trigger**: Time-based workflow execution
- **Webhook Trigger**: HTTP webhook-based execution
- **Event Trigger**: Custom event-driven execution
- **File Trigger**: File system change monitoring
- **Email Trigger**: Email-based workflow activation
- **Database Trigger**: Database change monitoring
- **MQTT Trigger**: MQTT message-based execution
- **Modbus Trigger**: Modbus device monitoring

#### **Action Nodes**
- **Email Action**: Send emails with templates
- **SMS Action**: Send SMS notifications
- **Webhook Action**: Send HTTP requests
- **Database Action**: Execute database operations
- **API Action**: Make API calls
- **File Action**: File system operations
- **Transform Action**: Data transformation
- **Condition Action**: Conditional logic
- **Delay Action**: Time-based delays
- **MQTT Action**: Publish MQTT messages
- **Modbus Action**: Modbus device communication

#### **Control Nodes**
- **Condition Node**: Conditional branching
- **Transform Node**: Data transformation
- **Delay Node**: Time delays
- **Custom Node**: User-defined functionality

### **Workflow Connections**
- **Node Connections**: Connect nodes in sequence
- **Port Mapping**: Define input/output port connections
- **Data Flow**: Control data flow between nodes
- **Conditional Flow**: Branch based on conditions

## 🔌 API Endpoints

### **Workflow Management**
- `GET /api/v1/workflows` - List all workflows
- `POST /api/v1/workflows` - Create new workflow
- `GET /api/v1/workflows/{id}` - Get workflow details
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow

### **Workflow Execution**
- `POST /api/v1/workflows/execute` - Execute workflow
- `GET /api/v1/executions/{id}` - Get execution status
- `DELETE /api/v1/executions/{id}` - Cancel execution

### **Trigger Management**
- `GET /api/v1/triggers` - List all triggers
- `POST /api/v1/triggers` - Create new trigger
- `GET /api/v1/triggers/{id}` - Get trigger details
- `PUT /api/v1/triggers/{id}` - Update trigger
- `DELETE /api/v1/triggers/{id}` - Delete trigger
- `POST /api/v1/triggers/start` - Start trigger
- `POST /api/v1/triggers/stop` - Stop trigger

### **Action Management**
- `GET /api/v1/actions` - List all actions
- `POST /api/v1/actions` - Create new action
- `GET /api/v1/actions/{id}` - Get action details
- `PUT /api/v1/actions/{id}` - Update action
- `DELETE /api/v1/actions/{id}` - Delete action
- `POST /api/v1/actions/execute` - Execute action

### **n8n Integration**
- `GET /api/v1/n8n/workflows` - List n8n workflows
- `POST /api/v1/n8n/workflows` - Create n8n workflow
- `GET /api/v1/n8n/workflows/{id}` - Get n8n workflow
- `PUT /api/v1/n8n/workflows/{id}` - Update n8n workflow
- `DELETE /api/v1/n8n/workflows/{id}` - Delete n8n workflow
- `POST /api/v1/n8n/sync` - Sync with n8n

### **Metrics and Statistics**
- `GET /api/v1/workflows/metrics` - Workflow metrics
- `GET /api/v1/triggers/metrics` - Trigger metrics
- `GET /api/v1/actions/metrics` - Action metrics

## 🖥️ CLI Commands

### **Workflow Management**
```bash
# Create workflow
arx workflow create "Building Control" --description "Automated building control"

# List workflows
arx workflow list

# Get workflow details
arx workflow get workflow_123

# Execute workflow
arx workflow execute workflow_123 --input input.json --wait

# Get execution status
arx workflow status execution_456

# Cancel execution
arx workflow cancel execution_456
```

### **Trigger Management**
```bash
# Create trigger
arx workflow trigger create "Daily Report" schedule daily_report_workflow --config trigger.json

# List triggers
arx workflow trigger list

# Start trigger
arx workflow trigger start trigger_123

# Stop trigger
arx workflow trigger stop trigger_123
```

### **Action Management**
```bash
# Create action
arx workflow action create "Send Email" email --config action.json

# List actions
arx workflow action list

# Execute action
arx workflow action execute action_123 --input input.json
```

### **n8n Integration**
```bash
# Sync with n8n
arx workflow n8n sync to_n8n

# List n8n workflows
arx workflow n8n list
```

### **Metrics and Monitoring**
```bash
# Show workflow metrics
arx workflow metrics
```

## 📊 Metrics and Monitoring

### **Workflow Metrics**
- Total workflows created
- Active workflows count
- Total executions
- Successful/failed executions
- Average execution duration
- Execution success rate

### **Trigger Metrics**
- Total triggers registered
- Active triggers count
- Trigger activation count
- Trigger error count
- Average trigger latency

### **Action Metrics**
- Total actions registered
- Actions executed count
- Successful/failed actions
- Average action duration
- Action success rate

## 🧪 Testing

### **Running Tests**
```bash
# Run all workflow tests
go test ./internal/workflow/...

# Run specific test
go test -run TestWorkflowManager ./internal/workflow/

# Run with verbose output
go test -v ./internal/workflow/

# Run with coverage
go test -cover ./internal/workflow/
```

### **Test Coverage**
The workflow system includes comprehensive test coverage:
- Unit tests for all components
- Integration tests for workflow execution
- Mock implementations for testing
- Performance benchmarks
- Error handling tests

## 📚 Examples

### **Building Automation Workflow**

```go
// Create building automation workflow
workflow := &workflow.Workflow{
    Name:        "Building Automation",
    Description: "Automated building control and monitoring",
    Version:     "1.0.0",
    Status:      workflow.WorkflowStatusActive,
    Nodes: []*workflow.WorkflowNode{
        // Temperature sensor trigger
        {
            ID:   "temp_sensor",
            Type: workflow.NodeTypeTrigger,
            Name: "Temperature Sensor",
            Position: workflow.Position{X: 0, Y: 0},
        },
        // Temperature condition check
        {
            ID:   "temp_check",
            Type: workflow.NodeTypeCondition,
            Name: "Temperature Check",
            Position: workflow.Position{X: 200, Y: 0},
        },
        // HVAC control action
        {
            ID:   "hvac_control",
            Type: workflow.NodeTypeAction,
            Name: "HVAC Control",
            Position: workflow.Position{X: 400, Y: 0},
        },
        // Email notification action
        {
            ID:   "email_notify",
            Type: workflow.NodeTypeAction,
            Name: "Email Notification",
            Position: workflow.Position{X: 400, Y: 100},
        },
    },
    Connections: []*workflow.WorkflowConnection{
        {
            ID:       "conn_1",
            FromNode: "temp_sensor",
            ToNode:   "temp_check",
            FromPort: "output",
            ToPort:   "input",
        },
        {
            ID:       "conn_2",
            FromNode: "temp_check",
            ToNode:   "hvac_control",
            FromPort: "output",
            ToPort:   "input",
        },
        {
            ID:       "conn_3",
            FromNode: "temp_check",
            ToNode:   "email_notify",
            FromPort: "output",
            ToPort:   "input",
        },
    },
}
```

### **IoT Device Management Workflow**

```go
// Create IoT device management workflow
workflow := &workflow.Workflow{
    Name:        "IoT Device Management",
    Description: "Manage IoT devices and sensors",
    Version:     "1.0.0",
    Status:      workflow.WorkflowStatusActive,
    Nodes: []*workflow.WorkflowNode{
        // MQTT trigger for device data
        {
            ID:   "mqtt_trigger",
            Type: workflow.NodeTypeTrigger,
            Name: "MQTT Device Data",
            Position: workflow.Position{X: 0, Y: 0},
        },
        // Data transformation
        {
            ID:   "data_transform",
            Type: workflow.NodeTypeTransform,
            Name: "Transform Data",
            Position: workflow.Position{X: 200, Y: 0},
        },
        // Database storage
        {
            ID:   "db_store",
            Type: workflow.NodeTypeAction,
            Name: "Store in Database",
            Position: workflow.Position{X: 400, Y: 0},
        },
        // Alert condition
        {
            ID:   "alert_check",
            Type: workflow.NodeTypeCondition,
            Name: "Alert Check",
            Position: workflow.Position{X: 200, Y: 100},
        },
        // Send alert
        {
            ID:   "send_alert",
            Type: workflow.NodeTypeAction,
            Name: "Send Alert",
            Position: workflow.Position{X: 400, Y: 100},
        },
    },
    Connections: []*workflow.WorkflowConnection{
        {
            ID:       "conn_1",
            FromNode: "mqtt_trigger",
            ToNode:   "data_transform",
            FromPort: "output",
            ToPort:   "input",
        },
        {
            ID:       "conn_2",
            FromNode: "data_transform",
            ToNode:   "db_store",
            FromPort: "output",
            ToPort:   "input",
        },
        {
            ID:       "conn_3",
            FromNode: "data_transform",
            ToNode:   "alert_check",
            FromPort: "output",
            ToPort:   "input",
        },
        {
            ID:       "conn_4",
            FromNode: "alert_check",
            ToNode:   "send_alert",
            FromPort: "output",
            ToPort:   "input",
        },
    },
}
```

## 🛠️ Development

1. Clone the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a merge request

## 📄 License

This project is proprietary - all rights reserved.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Join our Discord community
- Check the documentation wiki

---

**ArxOS Workflow Automation Platform** - Automating the future of building management! 🏗️✨
