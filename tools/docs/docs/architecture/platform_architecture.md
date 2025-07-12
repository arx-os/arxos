# Platform Architecture

## Overview

The Arxos platform is a comprehensive building information modeling (BIM) system that integrates SVG processing, symbol management, and building code compliance.

## System Architecture

### Core Components
```
arxos/
├── arx_svg_parser/          # Python-based SVG processing
├── arx-symbol-library/      # JSON-based symbol definitions
├── arx-backend/            # Go-based backend services
├── arx-web-frontend/       # Web interface
├── arx-database/           # Database and migrations
├── arx-infra/              # Infrastructure configuration
└── arx-docs/               # Documentation
```

### Data Flow
1. **SVG Input**: Building plans in SVG format
2. **Symbol Recognition**: Automatic symbol identification
3. **BIM Assembly**: Conversion to BIM model
4. **Rule Validation**: Building code compliance checking
5. **Output Generation**: Reports and visualizations

## Component Details

### arx_svg_parser
- **Language**: Python 3.8+
- **Framework**: FastAPI
- **Purpose**: SVG processing and BIM assembly
- **Key Features**:
  - JSON-based symbol library
  - Rule engine for compliance
  - REST API for integration
  - CLI tools for automation

### arx-symbol-library
- **Format**: JSON symbol definitions
- **Organization**: System-based directory structure
- **Validation**: JSON schema validation
- **Features**:
  - Mechanical, electrical, security systems
  - Rich metadata and properties
  - Connection and relationship data
  - Version control and history

### arx-backend
- **Language**: Go 1.19+
- **Framework**: Gin or Echo
- **Purpose**: High-performance backend services
- **Features**:
  - Asset management
  - User authentication
  - Data persistence
  - Real-time updates

### arx-web-frontend
- **Language**: JavaScript/TypeScript
- **Framework**: React or Vue.js
- **Purpose**: Web-based user interface
- **Features**:
  - Interactive SVG viewer
  - Symbol library browser
  - Compliance reporting
  - User management

## Configuration Management

### Project Configuration
- **arxfile.json**: Project metadata, permissions, sync info
- **Environment Variables**: Runtime configuration
- **Database Configuration**: Connection and schema settings
- **API Configuration**: Endpoint and authentication settings

### Symbol Library Configuration
```json
{
  "library_path": "../arx-symbol-library",
  "validation_schema": "schemas/symbol.schema.json",
  "cache_enabled": true,
  "cache_ttl": 3600,
  "systems": ["mechanical", "electrical", "security", "network"]
}
```

### API Configuration
```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "debug": false,
  "cors_origins": ["http://localhost:3000"],
  "trusted_hosts": ["localhost", "arxos.example.com"],
  "rate_limit": {
    "requests_per_minute": 100,
    "burst_size": 10
  }
}
```

## Data Architecture

### Symbol Data Model
```json
{
  "id": "hvac_unit_001",
  "name": "HVAC Unit",
  "system": "mechanical",
  "category": "hvac",
  "description": "Air handling unit",
  "svg": {
    "content": "<g id=\"hvac\">...</g>",
    "viewBox": "0 0 100 100"
  },
  "properties": {
    "capacity": "5000 CFM",
    "voltage": "480V",
    "efficiency": "95%"
  },
  "connections": [
    {
      "type": "electrical",
      "position": {"x": 10, "y": 20},
      "properties": {"voltage": "480V"}
    }
  ],
  "metadata": {
    "version": "1.0",
    "created": "2024-01-01T00:00:00Z",
    "author": "system",
    "funding_source": "federal_grant_2024"
  }
}
```

### Database Schema
```sql
-- Symbols table
CREATE TABLE symbols (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    system TEXT NOT NULL,
    category TEXT,
    description TEXT,
    svg_content TEXT NOT NULL,
    properties JSON,
    connections JSON,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Architecture

### Authentication
- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: bcrypt for password security
- **Session Management**: Token expiration and refresh
- **Role-based Access**: User role management

### Authorization
- **Resource Protection**: Endpoint security
- **Permission Levels**: Read, write, admin permissions
- **API Security**: Rate limiting and input validation
- **Data Protection**: Sensitive data encryption

### Network Security
- **HTTPS**: SSL/TLS encryption
- **Firewall**: Network access control
- **VPN**: Secure remote access
- **Monitoring**: Security event monitoring

## Performance Architecture

### Caching Strategy
- **Memory Cache**: In-memory symbol caching
- **Disk Cache**: Persistent cache storage
- **CDN**: Static asset delivery
- **Database Cache**: Query result caching

### Load Balancing
- **Nginx**: Reverse proxy and load balancer
- **Health Checks**: Service health monitoring
- **Failover**: Automatic failover handling
- **Scaling**: Horizontal scaling support

### Database Optimization
- **Indexing**: Strategic database indexing
- **Connection Pooling**: Database connection management
- **Query Optimization**: Efficient query design
- **Partitioning**: Data partitioning for large datasets

## Integration Architecture

### External APIs
- **Building Code APIs**: Code compliance services
- **CAD Integration**: CAD software integration
- **BIM Services**: BIM model services
- **Analytics**: Usage analytics and reporting

### Data Exchange
- **IFC Format**: Industry Foundation Classes
- **SVG Format**: Scalable Vector Graphics
- **JSON APIs**: RESTful API interfaces
- **File Formats**: Import/export capabilities

### Third-party Services
- **Authentication**: OAuth and SAML integration
- **Storage**: Cloud storage integration
- **Monitoring**: Application monitoring services
- **Analytics**: Usage analytics services

## Deployment Architecture

### Containerization
- **Docker**: Application containerization
- **Docker Compose**: Multi-service orchestration
- **Kubernetes**: Container orchestration (optional)
- **Registry**: Container image registry

### Infrastructure
- **Cloud Providers**: AWS, Azure, GCP support
- **On-premises**: Traditional server deployment
- **Hybrid**: Mixed cloud and on-premises
- **Edge**: Edge computing deployment

### CI/CD Pipeline
- **Source Control**: Git-based version control
- **Build Automation**: Automated build processes
- **Testing**: Automated testing pipeline
- **Deployment**: Automated deployment processes

## Monitoring and Observability

### Application Monitoring
- **Health Checks**: Service health monitoring
- **Performance Metrics**: Response time and throughput
- **Error Tracking**: Error monitoring and alerting
- **Usage Analytics**: User behavior analytics

### Infrastructure Monitoring
- **System Metrics**: CPU, memory, disk usage
- **Network Metrics**: Network performance monitoring
- **Database Metrics**: Database performance monitoring
- **Security Monitoring**: Security event monitoring

### Logging
- **Structured Logging**: JSON format logs
- **Log Aggregation**: Centralized log collection
- **Log Analysis**: Log analysis and reporting
- **Alerting**: Automated alerting system

## Scalability Architecture

### Horizontal Scaling
- **Load Balancers**: Traffic distribution
- **Stateless Services**: Stateless application design
- **Database Sharding**: Database scaling
- **Microservices**: Service decomposition

### Vertical Scaling
- **Resource Allocation**: CPU and memory allocation
- **Performance Tuning**: Application optimization
- **Capacity Planning**: Resource planning
- **Monitoring**: Performance monitoring

### Auto-scaling
- **Cloud Auto-scaling**: Cloud provider auto-scaling
- **Custom Auto-scaling**: Custom scaling logic
- **Metrics-based**: Scaling based on metrics
- **Predictive Scaling**: Predictive scaling algorithms

## Disaster Recovery

### Backup Strategy
- **Database Backups**: Regular database backups
- **File Backups**: Symbol library and file backups
- **Configuration Backups**: Configuration backups
- **Version Control**: Code version control

### Recovery Procedures
- **Data Recovery**: Database and file recovery
- **Service Recovery**: Service restoration procedures
- **Rollback Procedures**: Version rollback procedures
- **Testing**: Regular recovery testing

### High Availability
- **Redundancy**: System redundancy design
- **Failover**: Automatic failover procedures
- **Monitoring**: Availability monitoring
- **Alerting**: Availability alerting
