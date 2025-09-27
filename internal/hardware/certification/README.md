# ArxOS Hardware Certification System

The ArxOS Hardware Certification System provides comprehensive testing, validation, and certification capabilities for hardware devices in the ArxOS ecosystem. It ensures devices meet safety, performance, compatibility, security, reliability, and interoperability standards.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                ArxOS Certification System                   │
├─────────────────────────────────────────────────────────────┤
│  Certification Manager  │  Test Runner  │  Report Generator │
├─────────────────────────────────────────────────────────────┤
│  Test Executors        │  API Layer    │  CLI Tools        │
├─────────────────────────────────────────────────────────────┤
│  Safety Tests          │  Performance  │  Compatibility    │
│  Security Tests        │  Reliability  │  Interoperability │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
internal/hardware/certification/
├── certification.go      # Core certification manager
├── test_runner.go        # Test execution engine
├── executors.go          # Test category executors
├── report_generator.go   # Report generation system
├── api.go               # HTTP API endpoints
├── certification_test.go # Comprehensive test suite
└── README.md            # This documentation
```

## 🚀 Features

### **Core Certification Management**
- **Test Registration**: Register and manage certification tests
- **Standard Management**: Define and manage certification standards
- **Result Tracking**: Track test results and certification status
- **Device Certification**: Determine device certification status
- **Metrics Collection**: Comprehensive performance metrics

### **Test Execution Engine**
- **Async Execution**: Non-blocking test execution
- **Test Suites**: Run multiple tests as a suite
- **Timeout Management**: Configurable test timeouts
- **Status Tracking**: Real-time execution status
- **Logging**: Detailed execution logs
- **Cancellation**: Cancel running tests

### **Test Categories**
- **Safety Tests**: Electrical, fire, mechanical safety compliance
- **Performance Tests**: Response time, throughput, resource usage
- **Compatibility Tests**: Protocol, firmware, hardware compatibility
- **Security Tests**: Encryption, authentication, vulnerability scanning
- **Reliability Tests**: Uptime, error rates, stress testing
- **Interoperability Tests**: Cross-platform, standard compliance

### **Report Generation**
- **Multiple Formats**: JSON, HTML, PDF reports
- **Comprehensive Analysis**: Detailed test results and recommendations
- **Certification Levels**: Platinum, Gold, Silver, Bronze, Not Certified
- **Compliance Tracking**: Standards and regulation compliance
- **Visual Reports**: Rich HTML reports with charts and graphs

### **API and CLI**
- **REST API**: Full HTTP API for integration
- **CLI Tools**: Command-line interface for certification management
- **Real-time Status**: Live execution status monitoring
- **Batch Operations**: Run multiple tests efficiently

## 🔧 Getting Started

### **1. Basic Usage**

```go
package main

import (
    "context"
    "github.com/arx-os/arxos/internal/hardware/certification"
)

func main() {
    // Create certification manager
    manager := certification.NewCertificationManager()
    
    // Register a test
    test := &certification.CertificationTest{
        ID:          "safety_basic",
        Name:        "Basic Safety Test",
        Description: "Basic electrical and fire safety compliance test",
        Category:    certification.TestCategorySafety,
        Standard:    "IEC 61010-1",
        Version:     "1.0",
    }
    
    err := manager.RegisterTest(test)
    if err != nil {
        log.Fatal(err)
    }
    
    // Run test on device
    result, err := manager.RunTest(context.Background(), "device_001", "safety_basic")
    if err != nil {
        log.Fatal(err)
    }
    
    // Check result
    if result.Status == certification.TestStatusPassed {
        log.Printf("Device certified! Score: %.2f", result.Score)
    }
}
```

### **2. Using Test Runner**

```go
// Create test runner
runner := certification.NewTestRunner(manager)

// Run single test
execution, err := runner.RunTest(ctx, "device_001", "safety_basic", config)
if err != nil {
    log.Fatal(err)
}

// Run test suite
testIDs := []string{"safety_basic", "performance_basic", "security_basic"}
execution, err = runner.RunTestSuite(ctx, "device_001", testIDs, config)
if err != nil {
    log.Fatal(err)
}

// Check execution status
execution, err = runner.GetExecution(execution.ID)
if err != nil {
    log.Fatal(err)
}

log.Printf("Status: %s", execution.Status)
log.Printf("Duration: %s", execution.Duration)
```

### **3. Generating Reports**

```go
// Create report generator
generator := certification.NewReportGenerator()

// Get device results
results, err := manager.GetDeviceCertification("device_001")
if err != nil {
    log.Fatal(err)
}

// Generate JSON report
jsonData, err := generator.GenerateJSONReport("device_001", results)
if err != nil {
    log.Fatal(err)
}

// Generate HTML report
htmlData, err := generator.GenerateHTMLReport("device_001", results)
if err != nil {
    log.Fatal(err)
}

// Generate PDF report
pdfData, err := generator.GeneratePDFReport("device_001", results)
if err != nil {
    log.Fatal(err)
}
```

## 🧪 Test Categories

### **Safety Tests**
- **Electrical Safety**: Insulation resistance, leakage current, ground fault protection
- **Fire Safety**: Flame retardancy, smoke generation, thermal protection
- **Mechanical Safety**: Structural integrity, sharp edges, moving parts
- **EMC Compliance**: Electromagnetic emissions and immunity

### **Performance Tests**
- **Response Time**: Command response latency
- **Throughput**: Messages per second, data processing rate
- **Memory Usage**: RAM consumption, memory leaks
- **CPU Usage**: Processor utilization, efficiency
- **Power Consumption**: Energy efficiency, battery life

### **Compatibility Tests**
- **Protocol Compatibility**: MQTT, Modbus, BACnet support
- **Firmware Compatibility**: Version compatibility, upgrade paths
- **Hardware Compatibility**: Pin compatibility, voltage levels
- **Software Compatibility**: API compatibility, data formats

### **Security Tests**
- **Encryption**: Data encryption, key management
- **Authentication**: User authentication, device identity
- **Authorization**: Access control, permission management
- **Vulnerability Scanning**: Security flaws, penetration testing

### **Reliability Tests**
- **Uptime**: Continuous operation, availability
- **Error Rates**: Failure rates, error handling
- **Recovery Time**: System recovery, fault tolerance
- **Stress Testing**: Load testing, endurance testing

### **Interoperability Tests**
- **Protocol Interop**: Cross-protocol communication
- **Data Interop**: Data format compatibility
- **API Interop**: API compatibility across platforms
- **Standard Compliance**: Industry standard adherence

## 📊 Certification Levels

### **Platinum Level** (95+ score, 0 critical issues, ≤2 warnings)
- Highest certification level
- Exceptional performance and reliability
- Minimal issues or warnings
- Premium device status

### **Gold Level** (90+ score, 0 critical issues, ≤5 warnings)
- High-quality certification
- Strong performance and reliability
- Few minor issues
- Professional device status

### **Silver Level** (80+ score, 0 critical issues)
- Standard certification
- Good performance and reliability
- No critical issues
- Commercial device status

### **Bronze Level** (70+ score)
- Basic certification
- Acceptable performance
- Some issues present
- Limited device status

### **Not Certified** (<70 score)
- Failed certification
- Significant issues present
- Not recommended for production
- Development/testing only

## 🔌 API Endpoints

### **Test Management**
- `GET /api/v1/certification/tests` - List all tests
- `POST /api/v1/certification/tests` - Create new test
- `GET /api/v1/certification/tests/{id}` - Get test details
- `PUT /api/v1/certification/tests/{id}` - Update test
- `DELETE /api/v1/certification/tests/{id}` - Delete test

### **Test Execution**
- `POST /api/v1/certification/execute` - Run single test
- `POST /api/v1/certification/execute/suite` - Run test suite
- `GET /api/v1/certification/executions/{id}` - Get execution status
- `DELETE /api/v1/certification/executions/{id}` - Cancel execution

### **Results and Reports**
- `GET /api/v1/certification/results/{device-id}` - Get device results
- `GET /api/v1/certification/reports/{device-id}` - Generate report
- `GET /api/v1/certification/reports/{device-id}?format=html` - HTML report
- `GET /api/v1/certification/reports/{device-id}?format=pdf` - PDF report

### **Standards and Compliance**
- `GET /api/v1/certification/standards` - List standards
- `POST /api/v1/certification/standards` - Create standard
- `GET /api/v1/certification/standards/{id}` - Get standard details

### **Metrics and Statistics**
- `GET /api/v1/certification/metrics` - Get certification metrics
- `GET /api/v1/certification/stats` - Get system statistics

## 🖥️ CLI Commands

### **Basic Commands**
```bash
# List available tests
arx certify list

# Run single test
arx certify run device_001 safety_basic

# Run test suite
arx certify suite device_001 safety_basic performance_basic security_basic

# Get device status
arx certify status device_001

# Generate report
arx certify report device_001

# Get execution status
arx certify exec execution_123

# Cancel execution
arx certify cancel execution_123
```

### **Advanced Commands**
```bash
# Run test with configuration
arx certify run device_001 safety_basic --config config.json

# Run test with timeout
arx certify run device_001 safety_basic --timeout 60m

# Wait for completion
arx certify run device_001 safety_basic --wait

# Generate HTML report
arx certify report device_001 --format html --output report.html

# Generate PDF report
arx certify report device_001 --format pdf --output report.pdf

# Show metrics
arx certify metrics

# List standards
arx certify standards
```

## 📈 Metrics and Monitoring

### **Certification Metrics**
- Total tests executed
- Passed/failed test counts
- Certified device count
- Average certification score
- Expired device count

### **Test Runner Metrics**
- Total executions
- Completed/failed executions
- Average execution duration
- Timeout executions
- Tests run per execution

### **Performance Metrics**
- Test execution times
- Resource utilization
- Error rates
- Success rates
- Throughput

## 🛠️ Custom Test Executors

### **Creating Custom Executors**

```go
type CustomTestExecutor struct {
    name         string
    version      string
    capabilities []string
}

func (e *CustomTestExecutor) Execute(ctx context.Context, test *CertificationTest, deviceID string) (*TestResult, error) {
    // Implement custom test logic
    result := &TestResult{
        ID:        fmt.Sprintf("custom_%d", time.Now().UnixNano()),
        TestID:    test.ID,
        DeviceID:  deviceID,
        Status:    TestStatusPassed,
        Score:     85.0,
        MaxScore:  100.0,
        Details:   map[string]interface{}{"custom": true},
        Errors:    []string{},
        Warnings:  []string{},
        StartTime: time.Now(),
        EndTime:   time.Now().Add(1 * time.Second),
        Duration:  1 * time.Second,
    }
    
    return result, nil
}

func (e *CustomTestExecutor) GetName() string {
    return e.name
}

func (e *CustomTestExecutor) GetVersion() string {
    return e.version
}

func (e *CustomTestExecutor) GetCapabilities() []string {
    return e.capabilities
}

// Register custom executor
runner.RegisterExecutor(TestCategoryCustom, &CustomTestExecutor{
    name:    "Custom Executor",
    version: "1.0.0",
    capabilities: []string{"custom_test"},
})
```

## 🧪 Testing

### **Running Tests**
```bash
# Run all certification tests
go test ./internal/hardware/certification/...

# Run specific test
go test -run TestCertificationManager ./internal/hardware/certification/

# Run with verbose output
go test -v ./internal/hardware/certification/

# Run with coverage
go test -cover ./internal/hardware/certification/
```

### **Test Coverage**
The certification system includes comprehensive test coverage:
- Unit tests for all components
- Integration tests for test execution
- Mock implementations for testing
- Performance benchmarks
- Error handling tests

## 📚 Examples

### **Complete Certification Workflow**

```go
package main

import (
    "context"
    "log"
    "time"
    
    "github.com/arx-os/arxos/internal/hardware/certification"
)

func main() {
    // Initialize certification system
    manager := certification.NewCertificationManager()
    runner := certification.NewTestRunner(manager)
    generator := certification.NewReportGenerator()
    
    deviceID := "ESP32_SENSOR_001"
    
    // Define test suite
    testIDs := []string{
        "safety_basic",
        "performance_basic", 
        "compatibility_mqtt",
        "security_basic",
        "reliability_basic",
    }
    
    // Run certification suite
    config := map[string]interface{}{
        "timeout": 30, // 30 minutes
        "environment": "production",
    }
    
    execution, err := runner.RunTestSuite(context.Background(), deviceID, testIDs, config)
    if err != nil {
        log.Fatal(err)
    }
    
    log.Printf("Certification started: %s", execution.ID)
    
    // Wait for completion
    for {
        execution, err = runner.GetExecution(execution.ID)
        if err != nil {
            log.Fatal(err)
        }
        
        if execution.Status == certification.TestExecutionStatusCompleted ||
           execution.Status == certification.TestExecutionStatusFailed {
            break
        }
        
        time.Sleep(5 * time.Second)
    }
    
    // Generate report
    results, err := manager.GetDeviceCertification(deviceID)
    if err != nil {
        log.Fatal(err)
    }
    
    // Generate HTML report
    htmlData, err := generator.GenerateHTMLReport(deviceID, results)
    if err != nil {
        log.Fatal(err)
    }
    
    // Save report
    err = os.WriteFile("certification_report.html", htmlData, 0644)
    if err != nil {
        log.Fatal(err)
    }
    
    log.Printf("Certification completed: %s", execution.Status)
    log.Printf("Report saved: certification_report.html")
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Join our Discord community
- Check the documentation wiki

---

**ArxOS Hardware Certification System** - Ensuring quality and reliability in IoT devices! 🏗️✨
