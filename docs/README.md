# ARXOS Documentation

## 🎯 **Welcome to ARXOS**

ARXOS is a **Building Infrastructure-as-Code** platform that transforms buildings into programmable, navigable, version-controlled systems. Think of it as **"Git for Buildings"** - enabling infinite zoom from campus-level down to microchip internals, all through ASCII art and augmented reality.

## 🚀 **Core Innovation**

- **ASCII as Universal Language**: Buildings rendered in ASCII art that works everywhere from SSH terminals to AR headsets
- **Infinite Fractal Zoom**: Navigate from satellite view down to silicon chip level through the same interface
- **Building as Filesystem**: Navigate buildings with familiar commands: `cd`, `ls`, `find`, `tree`
- **Progressive Reality Construction**: Start with PDF plans, end with accurate 3D digital twins
- **Field-First Design**: Built for workers on the ground, not just office users

## 🏗️ **System Architecture**

ARXOS consists of three core components:

1. **ArxObject Runtime Engine (C)** - High-performance building component system (<1ms operations)
2. **ASCII-BIM Engine (C)** - Multi-resolution ASCII rendering (<10ms generation)
3. **CLI Tools (Go)** - Building navigation and version control
4. **AR Mobile Apps** - Field validation and real-time building interaction

## 📚 **Documentation Structure**

```
/docs
├── README.md                    # This file - main navigation
├── architecture/                # System architecture docs
│   ├── overview.md             # High-level system design
│   ├── arxobjects.md           # ArxObject data model (updated)
│   ├── ascii-bim.md            # ASCII rendering system
│   └── cli-architecture.md     # CLI design and structure
├── cli/                        # CLI documentation
│   ├── commands.md             # Complete command reference
│   ├── file-tree.md            # ArxObject file tree structure
│   └── examples.md             # Usage examples and workflows
├── development/                 # Developer documentation
│   ├── setup.md                # Development environment
│   ├── arxobject-dev.md        # ArxObject development guide
│   └── cli-dev.md              # CLI development guide
├── workflows/                   # User workflow guides
│   ├── field-validation.md     # AR field validation process
│   ├── building-iac.md         # Infrastructure as Code workflows
│   └── pdf-to-3d.md            # Progressive building construction
└── api/                        # API documentation (if needed)
    └── README.md               # API overview
```

## 🎯 **Getting Started**

### **For Field Workers & Users**
1. **CLI Navigation**: Learn building navigation with [CLI Commands](cli/commands.md)
2. **File Tree Structure**: Understand how buildings are organized in [File Tree Guide](cli/file-tree.md)
3. **Field Validation**: Learn AR validation workflows in [Field Validation Guide](workflows/field-validation.md)

### **For Developers & Engineers**
1. **Architecture**: Start with [System Overview](architecture/overview.md)
2. **ArxObject System**: Understand the core data model in [ArxObject Guide](architecture/arxobjects.md)
3. **Development Setup**: Get your environment ready with [Development Setup](development/setup.md)

### **For IT & Operations**
1. **Building IaC**: Learn infrastructure-as-code workflows in [Building IaC Guide](workflows/building-iac.md)
2. **CLI Operations**: Master building management commands in [CLI Examples](cli/examples.md)
3. **Version Control**: Understand building version control in [CLI Commands](cli/commands.md)

## 🔧 **Technology Stack**

- **Core Engine**: C (ArxObject runtime, ASCII-BIM rendering)
- **CLI Tools**: Go (building navigation, version control)
- **AI Services**: Python (progressive scaling, field validation)
- **Frontend**: Progressive Web App + AR mobile apps
- **Database**: PostgreSQL/PostGIS with spatial indexing

## 🎯 **Key Concepts**

### **ArxObject DNA**
Every building component is an ArxObject - intelligent, self-aware entities that understand their context, relationships, and confidence levels.

### **Infinite Zoom Architecture**
Seamless navigation from campus-level views down to microcontroller internals, with each level showing contextually appropriate detail.

### **Progressive Construction**
Start with PDF floor plans, add field measurements, fuse with LiDAR data, and progressively build accurate 3D models.

### **Building Infrastructure as Code**
Manage buildings through YAML configurations, Git-like version control, and automated operations - just like cloud infrastructure.

## 🚀 **What's Next?**

1. **Explore the CLI**: Try building navigation commands
2. **Understand ArxObjects**: Learn the core data model
3. **See ASCII Rendering**: Experience building visualization
4. **Try Field Validation**: Experience AR building interaction

---

**The future of buildings is not just smart - it's programmable.** 🏗️✨
