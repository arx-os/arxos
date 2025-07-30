# Arxos Developer Onboarding Index

## Overview

Welcome to Arxos! This index provides quick access to onboarding documentation for each repository in the Arxos ecosystem. Each repository has its own `ONBOARDING.md` file with specific setup instructions, requirements, and testing procedures.

## 🏗️ **Core Infrastructure**

### **Backend Services**
- **[arx-backend](https://github.com/arxos/arxos/tree/main/arxos/arx-backend/ONBOARDING.md)** - Main Go backend service
  - **Language**: Go 1.23+
  - **Purpose**: Core API and business logic
  - **Key Features**: REST API, authentication, database operations

### **Database & Infrastructure**
- **[arx-database](https://github.com/arxos/arxos/tree/main/arxos/infrastructure/database/ONBOARDING.md)** - Database management and migrations
  - **Language**: SQL, Python 3.11+
  - **Purpose**: Schema management, migrations, performance monitoring
  - **Key Features**: PostgreSQL, Alembic, diagram generation

## 🔧 **Processing & Parsing**

### **SVG Processing**
- **[arx_svg_parser](https://github.com/arxos/arxos/tree/main/arxos/arx_svg_parser/ONBOARDING.md)** - SVG to BIM conversion system
  - **Language**: Python 3.11+
  - **Purpose**: SVG parsing, BIM object generation, symbol management
  - **Key Features**: FastAPI, PostGIS, validation, symbol catalog

## 🏢 **Business Services**

### **CMMS Integration**
- **[arx-cmms](https://github.com/arxos/arxos/tree/main/arxos/services/cmms/ONBOARDING.md)** - Computerized Maintenance Management System
  - **Language**: Go 1.21+
  - **Purpose**: Maintenance management, work orders, asset tracking
  - **Key Features**: GORM, PostgreSQL, maintenance workflows

### **IoT Services**
- **[arx-iot](https://github.com/arxos/arxos/tree/main/arxos/services/iot/ONBOARDING.md)** - Internet of Things integration
  - **Language**: Python 3.11+
  - **Purpose**: Device management, sensor data, firmware updates
  - **Key Features**: Device registry, protocol handling, firmware management

### **AI Services**
- **[arx-ai](https://github.com/arxos/arxos/tree/main/arxos/services/ai/ONBOARDING.md)** - Artificial Intelligence and ML services
  - **Language**: Python 3.11+
  - **Purpose**: Machine learning, NLP, predictive analytics
  - **Key Features**: TensorFlow, scikit-learn, natural language processing

### **Data Vendor Integration**
- **[arx-data-vendor](https://github.com/arxos/arxos/tree/main/arxos/services/data-vendor/ONBOARDING.md)** - Third-party data integration
  - **Language**: Go 1.21+
  - **Purpose**: External data sources, vendor APIs, data synchronization
  - **Key Features**: API integration, data transformation, caching

### **Partner Services**
- **[arx-partners](https://github.com/arxos/arxos/tree/main/arxos/services/partners/ONBOARDING.md)** - Partner integration and management
  - **Language**: Python 3.11+
  - **Purpose**: Partner API management, integration workflows
  - **Key Features**: Partner authentication, data exchange, webhooks

### **PlanarX Services**
- **[arx-planarx](https://github.com/arxos/arxos/tree/main/arxos/services/planarx/ONBOARDING.md)** - PlanarX platform integration
  - **Language**: Python 3.11+
  - **Purpose**: PlanarX community and funding platform integration
  - **Key Features**: Community management, funding workflows, API integration

## 🎨 **Frontend & User Interface**

### **Web Frontend**
- **[arx-frontend-web](https://github.com/arxos/arxos/tree/main/arxos/frontend/web/ONBOARDING.md)** - Web application frontend
  - **Language**: HTML, CSS, JavaScript
  - **Purpose**: User interface, dashboard, interactive components
  - **Key Features**: Responsive design, accessibility, modern UI

### **Mobile Applications**
- **[arx-frontend-mobile](https://github.com/arxos/arxos/tree/main/arxos/frontend/mobile/ONBOARDING.md)** - Mobile app development
  - **Language**: React Native, JavaScript
  - **Purpose**: Cross-platform mobile applications
  - **Key Features**: iOS/Android support, offline capabilities

## 🛠️ **Development Tools**

### **Common Libraries**
- **[arx-common](https://github.com/arxos/arxos/tree/main/arxos/arx_common/ONBOARDING.md)** - Shared utilities and libraries
  - **Language**: Python 3.11+
  - **Purpose**: Common utilities, shared components
  - **Key Features**: Date utilities, object utilities, error handling

### **CLI Tools**
- **[arx-cli](https://github.com/arxos/arxos/tree/main/arxos/tools/cli/ONBOARDING.md)** - Command-line interface tools
  - **Language**: Python 3.11+
  - **Purpose**: Development and deployment tools
  - **Key Features**: Database management, deployment automation

## 📚 **Documentation**

### **Documentation System**
- **[arx-docs](https://github.com/arxos/arxos/tree/main/arx-docs/ONBOARDING.md)** - Documentation and guides
  - **Language**: Markdown, AsciiDoc
  - **Purpose**: Technical documentation, user guides, API docs
  - **Key Features**: Sphinx, automated generation, version control

## 🚀 **Quick Start Guide**

### **1. Prerequisites**
- **Git**: Latest version
- **Docker**: 20.10+ (for containerized development)
- **Go**: 1.21+ (for Go services)
- **Python**: 3.11+ (for Python services)
- **Node.js**: 18+ (for frontend development)
- **PostgreSQL**: 15+ (for database development)

### **2. Repository Setup**
```bash
# Clone the main repository
git clone https://github.com/arxos/arxos.git
cd arxos

# Initialize submodules (if any)
git submodule update --init --recursive
```

### **3. Environment Setup**
```bash
# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Install dependencies for all services
make setup
```

### **4. Development Workflow**
```bash
# Start development environment
make dev

# Run tests
make test

# Run linting
make lint

# Run migrations
make migrate
```

## 🔧 **Development Environment**

### **Recommended Setup**
- **IDE**: ArxIDE with Arxos extensions
- **Database**: PostgreSQL with PostGIS extension
- **Cache**: Redis for session and data caching
- **Message Queue**: Celery with Redis backend
- **Monitoring**: Prometheus and Grafana

### **Dev Container Support**
All repositories support ArxIDE Dev Containers for consistent development environments. Look for `.devcontainer.json` files in each repository.

## 📋 **Onboarding Checklist**

### **For New Developers**
- [ ] Read this index and understand the repository structure
- [ ] Set up development environment (prerequisites installed)
- [ ] Clone the main repository
- [ ] Configure environment variables
- [ ] Run the onboarding test for your primary repository
- [ ] Review the specific `ONBOARDING.md` for your repository
- [ ] Complete the first contribution (documentation update or bug fix)

### **For Repository Maintainers**
- [ ] Ensure `ONBOARDING.md` is up to date
- [ ] Verify `.env.example` contains all required variables
- [ ] Test the onboarding process from scratch
- [ ] Update this index when adding new repositories
- [ ] Maintain consistent standards across all repositories

## 🆘 **Getting Help**

### **Documentation**
- **API Documentation**: [docs.arxos.com](https://docs.arxos.com)
- **Architecture Guide**: [arx-docs/architecture/](https://github.com/arxos/arxos/tree/main/arx-docs/architecture/)
- **Database Documentation**: [arx-docs/database/](https://github.com/arxos/arxos/tree/main/arx-docs/database/)

### **Support Channels**
- **GitHub Issues**: [github.com/arxos/arxos/issues](https://github.com/arxos/arxos/issues)
- **Discord**: [discord.gg/arxos](https://discord.gg/arxos)
- **Email**: dev@arxos.com

### **Community**
- **Contributing Guide**: [CONTRIBUTING.md](https://github.com/arxos/arxos/blob/main/CONTRIBUTING.md)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](https://github.com/arxos/arxos/blob/main/CODE_OF_CONDUCT.md)
- **Development Standards**: [arx-docs/standards/](https://github.com/arxos/arxos/tree/main/arx-docs/standards/)

---

## 📊 **Repository Status**

| Repository | Status | Language | Last Updated |
|------------|--------|----------|--------------|
| arx-backend | ✅ Active | Go 1.23+ | 2024-01-15 |
| arx_svg_parser | ✅ Active | Python 3.11+ | 2024-01-15 |
| arx-cmms | ✅ Active | Go 1.21+ | 2024-01-15 |
| arx-database | ✅ Active | SQL/Python | 2024-01-15 |
| arx-iot | 🔄 In Progress | Python 3.11+ | 2024-01-15 |
| arx-ai | 🔄 In Progress | Python 3.11+ | 2024-01-15 |
| arx-frontend-web | 🔄 In Progress | HTML/CSS/JS | 2024-01-15 |
| arx-docs | ✅ Active | Markdown | 2024-01-15 |

**Legend:**
- ✅ **Active**: Fully documented and maintained
- 🔄 **In Progress**: Documentation being updated
- ⚠️ **Needs Update**: Documentation requires attention

---

*This index is maintained by the Arxos development team. Last updated: 2024-01-15* 