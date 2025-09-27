# ArxOS System Architecture

## Overview

ArxOS is a comprehensive "Building Operating System" that treats buildings as code repositories, providing a unified platform for building management, automation, and optimization. The system is built on a three-tier ecosystem model with clean architecture principles and production-ready infrastructure.

## Core Philosophy

- **Buildings as Code**: Every building component is version-controlled and trackable
- **Buildings as Repositories**: Room configurations are treated like Git repositories with branching, commits, and pull requests
- **Path-Based Addressing**: Universal addressing system for all building elements
- **Git + GitHub Business Model**: Three-tier ecosystem (Core, Hardware, Workflow)
- **PostGIS Spatial Intelligence**: Millimeter-precision location awareness
- **Clean Architecture**: Separation of concerns with clear boundaries

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ArxOS Core Platform                     │
├─────────────────────────────────────────────────────────────────┤
│  CLI Interface (arx)  │  REST API  │  Web UI  │  Mobile App    │
├─────────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   Analytics │ │     IT      │ │  Workflow   │ │    CMMS     ││
│  │   Engine    │ │ Management  │ │ Automation  │ │   Features  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │  Hardware   │ │  Protocol   │ │ Hardware    │ │  Facility   ││
│  │  Platform   │ │ Translation │ │Certification│ │ Management  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                      Data Access Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   PostGIS   │ │   SQLite    │ │    Redis    │ │   File      ││
│  │  Database   │ │  Database   │ │    Cache    │ │   System    ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   Docker    │ │Kubernetes   │ │   GitHub    │ │   n8n       ││
│  │ Containers  │ │Orchestration│ │   Actions   │ │ Integration ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. Building Infrastructure (`internal/core/`)
- **Path Management**: Universal addressing system for building components
- **Spatial Queries**: PostGIS-based spatial operations and queries
- **Git Integration**: Version control for building data
- **Configuration Management**: YAML-based configuration system

### 2. Analytics Engine (`internal/analytics/`)
- **Energy Optimization**: Real-time energy consumption analysis and optimization
- **Predictive Analytics**: Machine learning models for forecasting and trends
- **Performance Monitoring**: KPI tracking and threshold-based alerting
- **Anomaly Detection**: Statistical analysis for identifying unusual patterns
- **Report Generation**: Multi-format reports with templates and scheduling

### 3. IT Asset Management (`internal/it/`)
- **Asset Lifecycle**: Complete IT asset management from procurement to disposal
- **Configuration Management**: Template-based hardware/software configurations
- **Room Setup Management**: Room-specific IT equipment layouts and connections
- **Inventory Management**: Parts and supplies tracking with supplier integration
- **Work Order Management**: IT work order creation, tracking, and resolution

### 4. Workflow Automation (`internal/workflow/`)
- **n8n Integration**: Seamless integration with n8n workflow automation platform
- **Trigger Management**: Multiple trigger types (schedule, webhook, event, manual)
- **Action Management**: Comprehensive action library for building operations
- **Workflow Execution**: Asynchronous workflow execution with monitoring
- **API Integration**: RESTful API for workflow management

### 5. CMMS/CAFM Features (`internal/facility/`)
- **Facility Management**: Building, space, and asset management
- **Work Order Management**: Maintenance work order lifecycle
- **Maintenance Scheduling**: Preventive and reactive maintenance planning
- **Inspection Management**: Inspection workflows and compliance tracking
- **Vendor Management**: External service provider and contract management

### 6. Hardware Platform (`internal/hardware/`)
- **Device Management**: IoT device registration, configuration, and monitoring
- **Protocol Translation**: BACnet, Modbus, MQTT protocol support
- **Certification Program**: Hardware testing and quality assurance
- **Edge Computing**: TinyGo-based edge device templates
- **Gateway Management**: Protocol gateway configuration and monitoring

### 7. Building as Repository (`internal/it/version_control.go`)
- **Version Control**: Git-like operations for room configurations
- **Branch Management**: Create, merge, and manage configuration branches
- **Commit History**: Track all changes to room configurations
- **Pull Requests**: Review and approve configuration changes
- **Rollback Capability**: Revert to previous configurations
- **Feature Requests**: User-driven configuration improvements
- **Emergency Fixes**: Rapid response to critical issues

## Data Architecture

### Primary Database: PostGIS
- **Spatial Data**: Building geometry, equipment locations, spatial relationships
- **Building Data**: Rooms, floors, equipment, systems, and their properties
- **Time Series**: Sensor data, energy consumption, performance metrics
- **Relationships**: Hierarchical building structure and equipment dependencies

### Secondary Storage
- **SQLite**: Local development and fallback database
- **Redis**: Caching layer for performance optimization
- **File System**: Configuration files, templates, and static assets
- **Git Repository**: Version-controlled building data and configurations

## API Architecture

### REST API Design
- **Resource-Based URLs**: `/api/{module}/{resource}/{id}`
- **HTTP Methods**: GET, POST, PUT, DELETE for CRUD operations
- **Status Codes**: Standard HTTP status codes for responses
- **Content Types**: JSON for data exchange, with support for other formats

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication for API access
- **Role-Based Access Control**: Granular permissions for different user types
- **API Keys**: Service-to-service authentication
- **Rate Limiting**: Protection against abuse and DoS attacks

## Integration Points

### External Systems
- **n8n Workflows**: Bidirectional integration for automation
- **Hardware Devices**: MQTT, Modbus, BACnet protocol support
- **GitHub**: Version control and CI/CD integration
- **Monitoring Systems**: Prometheus, Grafana integration
- **Notification Services**: Email, SMS, webhook notifications

### Internal Integrations
- **Analytics ↔ IT Management**: Asset performance and utilization tracking
- **Workflow ↔ CMMS**: Automated maintenance scheduling and work orders
- **Hardware ↔ Analytics**: Real-time data collection and analysis
- **IT Management ↔ Workflow**: Automated IT operations and provisioning

## Security Architecture

### Data Protection
- **Encryption**: At-rest and in-transit data encryption
- **Input Validation**: Comprehensive input sanitization and validation
- **SQL Injection Prevention**: Parameterized queries and query sanitization
- **XSS Protection**: Content Security Policy and input filtering

### Access Control
- **Authentication**: Multi-factor authentication support
- **Authorization**: Role-based access control with fine-grained permissions
- **Audit Logging**: Comprehensive activity logging and monitoring
- **Session Management**: Secure session handling and timeout

## Deployment Architecture

### Containerization
- **Docker**: Application containerization for consistent deployment
- **Docker Compose**: Multi-service orchestration for development
- **Kubernetes**: Production orchestration and scaling
- **Health Checks**: Application health monitoring and recovery

### CI/CD Pipeline
- **GitHub Actions**: Automated testing, building, and deployment
- **Multi-Environment**: Development, staging, and production environments
- **Automated Testing**: Unit, integration, and end-to-end testing
- **Rollback Capability**: Safe deployment rollback mechanisms

## Performance Architecture

### Caching Strategy
- **Redis Cache**: High-performance caching layer
- **Query Optimization**: Database query optimization and indexing
- **CDN Integration**: Static asset delivery optimization
- **Connection Pooling**: Database connection management

### Scalability
- **Horizontal Scaling**: Multi-instance deployment capability
- **Load Balancing**: Request distribution across instances
- **Database Sharding**: Data partitioning for large-scale deployments
- **Microservices**: Modular architecture for independent scaling

## Monitoring & Observability

### Metrics Collection
- **Prometheus**: Metrics collection and storage
- **Custom Metrics**: Application-specific performance metrics
- **System Metrics**: Infrastructure and resource utilization
- **Business Metrics**: KPI tracking and reporting

### Logging
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Log Levels**: Debug, Info, Warn, Error, Fatal
- **Centralized Logging**: Aggregated log collection and analysis
- **Audit Trails**: Security and compliance logging

### Alerting
- **Threshold-Based**: Automated alerts for performance issues
- **Anomaly Detection**: Machine learning-based anomaly alerts
- **Escalation Policies**: Multi-level alert escalation
- **Integration**: Email, SMS, and webhook notifications

## Development Workflow

### Code Organization
- **Clean Architecture**: Clear separation of concerns
- **Module Structure**: Self-contained modules with defined interfaces
- **Dependency Injection**: Loose coupling and testability
- **Interface Segregation**: Small, focused interfaces

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: Module interaction testing
- **End-to-End Tests**: Complete workflow testing
- **Performance Tests**: Load and stress testing

### Documentation
- **API Documentation**: OpenAPI/Swagger specifications
- **Code Documentation**: Inline code comments and examples
- **Architecture Documentation**: System design and decision records
- **User Guides**: End-user documentation and tutorials

## Future Extensibility

### Plugin Architecture
- **Module System**: Pluggable module architecture
- **API Extensions**: Custom API endpoint registration
- **Workflow Extensions**: Custom workflow actions and triggers
- **UI Extensions**: Custom dashboard and interface components

### Integration Framework
- **Webhook Support**: External system integration points
- **Event System**: Publish-subscribe event architecture
- **Message Queues**: Asynchronous processing and integration
- **API Gateway**: Centralized API management and routing

This architecture provides a solid foundation for building management while maintaining flexibility for future enhancements and integrations.
