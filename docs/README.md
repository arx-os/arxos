# ARXOS Documentation

## 🎯 **Welcome to ARXOS**

ARXOS is a building information and validation system with AR capabilities, designed for simplicity and direct deployment. Think of it as **"Google Maps for Buildings"** - enabling infinite zoom from campus-level down to individual circuit traces.

## 🚀 **Quick Navigation**

### **For New Developers**
- **[Quick Start](quick-start.md)** - Get up and running in 5 minutes
- **[Architecture Overview](architecture/overview.md)** - System design and technology stack
- **[Development Setup](development/setup.md)** - Local development environment

### **For Developers**
- **[API Reference](api/README.md)** - Complete API documentation
- **[Development Guide](development/guide.md)** - Coding standards and practices
- **[ArxObject System](architecture/arxobjects.md)** - Core data model documentation

### **For Users**
- **[User Guide](user-guide.md)** - How to use ARXOS features
- **[AR/3D Features](features/ar-3d.md)** - Augmented reality and 3D visualization

## 🏗️ **System Overview**

ARXOS consists of three main components:

1. **Go Backend** - Single binary REST API server with Chi router
2. **Python AI Service** - PDF/IFC/DWG ingestion and processing
3. **Vanilla JS Frontend** - HTML/CSS/JS with Three.js for 3D/AR

## 🔧 **Technology Stack**

- **Backend**: Go with Chi router, PostgreSQL/PostGIS, Redis
- **Frontend**: Vanilla JavaScript, HTML5, CSS3, HTMX, Three.js
- **AI Service**: Python with OpenAI API integration
- **AR**: 8th Wall web-based AR framework

## 📚 **Documentation Structure**

```
/docs
├── README.md                    # This file - main navigation
├── quick-start.md              # 5-minute setup guide
├── user-guide.md               # End user documentation
├── architecture/               # System architecture docs
│   ├── overview.md            # High-level system design
│   ├── arxobjects.md          # ArxObject data model
│   └── components.md          # System components
├── development/                # Developer documentation
│   ├── setup.md               # Development environment
│   ├── guide.md               # Coding standards & practices
│   └── deployment.md          # Production deployment
├── api/                        # API documentation
│   ├── README.md              # API overview
│   ├── endpoints.md           # REST endpoint reference
│   └── examples.md            # API usage examples
└── features/                   # Feature-specific docs
    ├── ar-3d.md               # AR and 3D features
    └── pdf-ingestion.md       # PDF processing features
```

## 🎯 **Getting Started**

1. **New to ARXOS?** Start with [Quick Start](quick-start.md)
2. **Want to understand the system?** Read [Architecture Overview](architecture/overview.md)
3. **Ready to develop?** Follow [Development Setup](development/setup.md)
4. **Need API info?** Check [API Reference](api/README.md)

---

**Need help?** Check the [Development Guide](development/guide.md) or review the [Architecture Overview](architecture/overview.md) for detailed information.
