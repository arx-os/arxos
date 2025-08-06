# MCP Service - Model Context Protocol

A high-performance building code validation service with real-time capabilities, professional reporting, and enterprise-grade features.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Redis
- PostgreSQL (optional)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd services/mcp

# Install dependencies
pip install -r requirements.txt

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run the service
python main.py
```

### API Documentation
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

## 🏗️ Architecture

### Core Components
- **WebSocket Server**: Real-time CAD integration
- **Redis Integration**: Advanced caching system
- **Authentication System**: JWT-based security with RBAC
- **Performance Monitoring**: Prometheus metrics
- **PDF Report Generation**: Professional compliance reports
- **Knowledge Base System**: Building codes database with search and jurisdiction management

### Technology Stack
- **Backend**: FastAPI (Python 3.11)
- **Caching**: Redis with advanced strategies
- **Authentication**: JWT with role-based access control
- **Monitoring**: Prometheus + Grafana
- **PDF Generation**: ReportLab with custom templates
- **Deployment**: Docker with health checks

## 🧠 Knowledge Base System

The MCP Service includes a comprehensive knowledge base system for building codes, standards, and compliance management.

### Features
- **Building Codes Database**: IBC, NEC, IFC, ADA, NFPA, ASHRAE
- **Advanced Search**: Semantic search with relevance scoring
- **Jurisdiction Management**: Local amendments and compliance
- **Version Control**: Code version tracking and rollback
- **Code References**: Cross-references and citations
- **REST API**: Complete API for all knowledge base operations

### API Endpoints
```
GET  /api/v1/knowledge/codes                    # Get supported codes
GET  /api/v1/knowledge/codes/{code}/{section}   # Get code section
POST /api/v1/knowledge/search                   # Search building codes
GET  /api/v1/knowledge/jurisdictions            # Get jurisdictions
GET  /api/v1/knowledge/versions                 # Get code versions
GET  /api/v1/knowledge/references/{code}/{section} # Get references
```

### Usage Examples
```python
# Search for occupant load requirements
search_request = {
    "query": "occupant load calculation",
    "code_standard": "IBC",
    "max_results": 5
}

# Check jurisdiction compliance
compliance = await jurisdiction_manager.check_jurisdiction_compliance(
    "California", "IBC", "1004.1.1"
)

# Get code references
references = await code_reference.get_cross_references("IBC", "1004.1.1")
```

### Testing and Demo
```bash
# Run tests
python test_knowledge_base.py

# Run demo
python demo_knowledge_base.py
```

## 🤖 ML Integration System

The MCP Service includes a comprehensive ML integration system for AI-powered building code validation and analysis.

### Features
- **AI-Powered Validation**: Machine learning models for building code compliance
- **Predictive Analytics**: Risk assessment, cost estimation, timeline prediction
- **Pattern Recognition**: Design patterns, violation patterns, optimization opportunities
- **Model Management**: Training, versioning, and lifecycle management
- **Real-time Processing**: Fast response times with confidence scoring
- **Comprehensive API**: Complete REST API for all ML capabilities

### AI Validation Types
- **Structural**: Building structure and foundation compliance
- **Electrical**: Electrical system and load requirements
- **Fire Protection**: Fire safety and suppression systems
- **Accessibility**: ADA compliance and accessibility features
- **Mechanical**: HVAC and mechanical system requirements
- **Plumbing**: Plumbing system and fixture requirements
- **Energy**: Energy efficiency and sustainability standards
- **General**: Overall building code compliance

### Prediction Types
- **Compliance Risk**: Likelihood of code violations
- **Cost Estimate**: Construction cost predictions
- **Construction Time**: Project timeline estimates
- **Maintenance Needs**: Future maintenance requirements
- **Energy Efficiency**: Energy performance predictions
- **Safety Risk**: Safety and risk assessments

### Pattern Types
- **Design Patterns**: Recognized architectural and design patterns
- **Violation Patterns**: Common code violation patterns
- **Optimization Patterns**: Efficiency and cost optimization opportunities
- **Cost Patterns**: Cost analysis and trending patterns
- **Time Patterns**: Project timeline and scheduling patterns

### API Endpoints

#### AI Validation
- `POST /api/v1/ml/validate` - Perform AI-powered validation
- `GET /api/v1/ml/validate/types` - Get available validation types
- `GET /api/v1/ml/validate/statistics` - Get validation statistics

#### Predictive Analytics
- `POST /api/v1/ml/predict` - Perform predictive analytics
- `GET /api/v1/ml/predict/types` - Get available prediction types
- `GET /api/v1/ml/predict/statistics` - Get prediction statistics

#### Pattern Recognition
- `POST /api/v1/ml/patterns` - Perform pattern recognition
- `GET /api/v1/ml/patterns/types` - Get available pattern types

#### Model Management
- `POST /api/v1/ml/models/train` - Train new model
- `GET /api/v1/ml/models` - List all models
- `GET /api/v1/ml/models/{model_id}` - Get model information
- `POST /api/v1/ml/models/{model_id}/activate` - Activate model
- `POST /api/v1/ml/models/{model_id}/deactivate` - Deactivate model
- `DELETE /api/v1/ml/models/{model_id}` - Delete model
- `GET /api/v1/ml/models/statistics` - Get model statistics

#### Service Status
- `GET /api/v1/ml/status` - Get ML service status
- `GET /api/v1/ml/statistics` - Get comprehensive statistics
- `GET /api/v1/ml/health` - Health check

### Usage Examples

#### AI Validation
```bash
curl -X POST "http://localhost:8001/api/v1/ml/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "building_data": {
      "area": 8000,
      "height": 25,
      "type": "commercial",
      "occupancy": "B",
      "floors": 3
    },
    "validation_type": "structural",
    "jurisdiction": "New York City",
    "include_suggestions": true,
    "confidence_threshold": 0.7
  }'
```

#### Predictive Analytics
```bash
curl -X POST "http://localhost:8001/api/v1/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "building_data": {
      "area": 12000,
      "height": 30,
      "type": "commercial",
      "occupancy": "B"
    },
    "prediction_type": "compliance_risk",
    "include_confidence": true
  }'
```

#### Pattern Recognition
```bash
curl -X POST "http://localhost:8001/api/v1/ml/patterns" \
  -H "Content-Type: application/json" \
  -d '{
    "building_data": {
      "area": 20000,
      "height": 35,
      "type": "commercial",
      "occupancy": "B"
    },
    "pattern_type": "design_pattern",
    "similarity_threshold": 0.8
  }'
```

### Testing and Demo
```bash
# Run tests
python test_ml_integration.py

# Run demo
python demo_ml_integration.py
```

## 📁 Project Structure

```
services/mcp/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── docker-compose.dev.yml # Development environment
├── setup.py              # Package configuration
├── README.md             # This file
│
├── auth/                 # Authentication system
│   ├── authentication.py # JWT and RBAC implementation
│   └── __init__.py
│
├── cache/                # Redis caching system
│   ├── redis_manager.py  # Advanced caching strategies
│   └── __init__.py
│
├── monitoring/           # Performance monitoring
│   ├── prometheus_metrics.py # Custom metrics collection
│   └── __init__.py
│
├── report/              # PDF report generation
│   ├── report_generator.py # Professional PDF generation
│   ├── report_service.py   # Email and cloud storage
│   ├── report_routes.py    # API endpoints
│   └── __init__.py
│
├── websocket/           # Real-time communication
│   ├── websocket_manager.py # Connection management
│   ├── websocket_routes.py  # WebSocket endpoints
│   └── __init__.py
│
├── validate/            # Rule engine and validation
│   ├── rule_engine.py   # MCP rule processing
│   └── __init__.py
│
├── knowledge/           # Knowledge base system
│   ├── knowledge_base.py      # Core knowledge base
│   ├── search_engine.py       # Advanced search capabilities
│   ├── jurisdiction_manager.py # Jurisdiction management
│   ├── version_control.py     # Version control system
│   ├── code_reference.py      # Code references and citations
│   ├── knowledge_routes.py    # API endpoints
│   └── __init__.py
│
├── models/              # Data models
│   ├── mcp_models.py    # Pydantic models
│   └── __init__.py
│
├── config/              # Configuration management
│   └── __init__.py
│
├── tests/               # Test suite
│   ├── test_integration.py
│   ├── test_report_generation.py
│   └── ...
│
├── examples/            # Usage examples and demos
│   ├── demo_report_generation.py
│   ├── jurisdiction_demo.py
│   └── ...
│
├── docs/                # Documentation
│   ├── README.md        # Documentation index
│   ├── PHASE1_COMPLETION.md
│   ├── PHASE2_COMPLETION.md
│   ├── DEVELOPMENT_PLANS.md
│   └── ...
│
└── reports/             # Generated PDF reports
    └── .gitkeep
```

## 🔧 Configuration

### Environment Variables
```bash
# Service Configuration
MCP_HOST=0.0.0.0
MCP_PORT=8001
MCP_RELOAD=true

# Redis Configuration
REDIS_URL=redis://redis:6379

# Database Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/mcp_db

# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration (for reports)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@arxos.com

# Cloud Storage (for reports)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_STORAGE_CONTAINER=your-container-name
```

## 🧪 Testing

### Run All Tests
```bash
# Run integration tests
python tests/test_integration.py

# Run report generation tests
python tests/test_report_generation.py

# Run performance tests
python tests/test_performance.py
```

### Run Examples
```bash
# Run report generation demo
python examples/demo_report_generation.py

# Run jurisdiction demo
python examples/jurisdiction_demo.py
```

## 📊 API Endpoints

### Core Endpoints
- `POST /api/v1/validate` - Validate building model
- `GET /api/v1/validate/{building_id}` - Get validation result
- `GET /api/v1/jurisdiction/{building_id}` - Get jurisdiction info

### Report Endpoints
- `POST /api/v1/reports/generate` - Generate PDF report
- `POST /api/v1/reports/email` - Send report via email
- `GET /api/v1/reports/download/{filename}` - Download report
- `GET /api/v1/reports/history` - Get report history

### Authentication Endpoints
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token

### WebSocket Endpoints
- `WS /api/v1/ws/validation/{building_id}` - Real-time validation updates

### Monitoring Endpoints
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /api/v1/monitoring/metrics` - Custom metrics

## 🚀 Deployment

### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Access services
# MCP Service: http://localhost:8001
# Redis Commander: http://localhost:8081
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# PgAdmin: http://localhost:8080 (admin@arxos.com/admin123)
```

### Production
```bash
# Build and deploy
docker build -t mcp-service .
docker run -p 8001:8001 mcp-service
```

## 📈 Monitoring

### Metrics Available
- **Validation Performance**: Response times, throughput
- **Cache Performance**: Hit ratios, memory usage
- **User Activity**: Login attempts, API usage
- **Report Generation**: Generation times, file sizes
- **System Health**: CPU, memory, disk usage

### Dashboards
- **Performance Dashboard**: Real-time system metrics
- **Business Intelligence**: User activity and trends
- **Compliance Analytics**: Validation statistics
- **System Health**: Infrastructure monitoring

## 🔒 Security

### Authentication
- JWT-based authentication
- Role-based access control (RBAC)
- Permission matrix system
- Token refresh mechanism

### Authorization
- API endpoint protection
- File access control
- Report generation permissions
- Admin-only operations

## 📚 Documentation

### Development Documentation
- [Phase 1 Completion](docs/PHASE1_COMPLETION.md) - Core infrastructure
- [Phase 2 Completion](docs/PHASE2_COMPLETION.md) - Enhanced features
- [Development Plans](docs/DEVELOPMENT_PLANS.md) - Roadmap
- [Engineering Assessment](docs/ENGINEERING_ASSESSMENT.md) - Technical decisions

### API Documentation
- [API Reference](docs/API_REFERENCE.md) - Complete endpoint documentation
- [Architecture Overview](docs/ARCHITECTURE.md) - System design
- [Deployment Guide](docs/DEPLOYMENT.md) - Production setup

## 🤝 Contributing

### Development Standards
- Follow PEP 8 coding standards
- Write comprehensive tests
- Update documentation for changes
- Use conventional commit messages

### Testing Requirements
- Unit tests for all new features
- Integration tests for API endpoints
- Performance tests for critical paths
- Security tests for authentication

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For technical support or questions:
- **Email**: support@arxos.com
- **Documentation**: [docs/](docs/)
- **Issues**: Create an issue in the repository

---

**MCP Service** - Professional building code validation with real-time capabilities and enterprise-grade features. 