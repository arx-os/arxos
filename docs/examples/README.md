# Arxos Examples

This directory contains comprehensive examples demonstrating various aspects of the Arxos platform. Each example is organized by category and includes detailed documentation and working code.

## 📁 Directory Structure

```
docs/examples/
├── README.md                           # This file
├── arxfile/                            # Arxfile configuration examples
│   └── arxfile_example.yaml           # Complete building repository config
├── pipeline/                           # Pipeline integration examples
│   └── pipeline_demo.py               # System integration demonstrations
├── integration/                        # Service integration examples
│   └── building_service_integration_example.py  # HVAC system integration
└── validation/                         # Validation system examples
    └── precision_validation_example.py # CAD precision validation
```

## 🎯 Example Categories

### **📋 Arxfile Examples** (`arxfile/`)
Configuration examples for building repositories and the Arxfile format.

**Files:**
- `arxfile_example.yaml` - Complete commercial building repository configuration

**Features Demonstrated:**
- Building metadata and ownership
- Share distribution system for contributors
- Contract management and legal agreements
- License and revenue sharing
- Compliance requirements

### **🔄 Pipeline Examples** (`pipeline/`)
Demonstrations of the Arxos pipeline for system integration and automation.

**Files:**
- `pipeline_demo.py` - Interactive pipeline demonstrations

**Features Demonstrated:**
- Audiovisual system integration
- Electrical system extension
- Complete pipeline workflow
- Error handling and validation
- Step-by-step integration process

### **🔗 Integration Examples** (`integration/`)
Real-world service integration examples showing how to connect external systems.

**Files:**
- `building_service_integration_example.py` - HVAC system integration

**Features Demonstrated:**
- API endpoint definitions
- Data models and compliance requirements
- Performance specifications
- Real-time capabilities
- Authentication methods
- Multi-phase integration pipeline

### **✅ Validation Examples** (`validation/`)
Precision validation system examples for CAD applications.

**Files:**
- `precision_validation_example.py` - Comprehensive validation demonstrations

**Features Demonstrated:**
- Coordinate validation with sub-millimeter accuracy
- Geometric validation (distances, angles)
- Constraint validation
- Custom validation rules
- Batch validation processing
- Testing framework
- Error handling and reporting

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+
- Arxos platform installed
- Required dependencies (see individual examples)

### **Running Examples**

#### **1. Arxfile Configuration**
```bash
# Review the configuration
cat docs/examples/arxfile/arxfile_example.yaml
```

#### **2. Pipeline Integration**
```bash
# Run the pipeline demo
cd docs/examples/pipeline
python pipeline_demo.py
```

#### **3. Service Integration**
```bash
# Run the HVAC integration example
cd docs/examples/integration
python building_service_integration_example.py
```

#### **4. Validation System**
```bash
# Run the precision validation demo
cd docs/examples/validation
python precision_validation_example.py
```

## 📖 Example Details

### **Arxfile Example**
The `arxfile_example.yaml` demonstrates a complete commercial building repository configuration including:

- **Building Information**: Metadata, ownership, licensing
- **Share Distribution**: Revenue sharing for contributors
- **Contract Management**: Legal agreements and obligations
- **Compliance**: Regulatory and industry requirements

### **Pipeline Demo**
The `pipeline_demo.py` shows interactive demonstrations of:

- **System Integration**: Adding new building systems
- **Schema Validation**: Ensuring data consistency
- **Behavior Implementation**: Creating system behaviors
- **Compliance Checking**: Validating against standards
- **Error Handling**: Robust error management

### **Integration Example**
The `building_service_integration_example.py` demonstrates:

- **HVAC System Integration**: Complete HVAC system setup
- **API Design**: RESTful endpoint definitions
- **Data Models**: Structured data schemas
- **Performance Requirements**: Scalability specifications
- **Compliance**: Industry standards adherence

### **Validation Example**
The `precision_validation_example.py` showcases:

- **Coordinate Validation**: Sub-millimeter precision
- **Geometric Operations**: Distance and angle calculations
- **Constraint Validation**: Design rule enforcement
- **Custom Rules**: User-defined validation logic
- **Batch Processing**: High-throughput validation
- **Testing Framework**: Comprehensive test suites

## 🔧 Customization

### **Modifying Examples**
Each example can be customized for your specific needs:

1. **Update Configuration**: Modify YAML files for your building
2. **Adjust Parameters**: Change integration parameters
3. **Add Validation Rules**: Create custom validation logic
4. **Extend Pipelines**: Add new integration steps

### **Creating New Examples**
To create new examples:

1. **Choose Category**: Select appropriate subdirectory
2. **Follow Structure**: Use existing examples as templates
3. **Update Paths**: Ensure correct import paths
4. **Add Documentation**: Include comprehensive comments
5. **Test Thoroughly**: Verify functionality

## 🐛 Troubleshooting

### **Common Issues**

#### **Import Errors**
```bash
# Add parent directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
```

#### **Missing Dependencies**
```bash
# Install required packages
pip install -r requirements.txt
```

#### **Path Issues**
```bash
# Ensure correct working directory
cd docs/examples/[category]
python [example_file].py
```

### **Getting Help**
- Check individual example documentation
- Review error messages carefully
- Verify file paths and permissions
- Ensure all dependencies are installed

## 📚 Additional Resources

- **Documentation**: See `/docs/` for comprehensive guides
- **API Reference**: Check `/docs/api/` for endpoint documentation
- **Architecture**: Review `/docs/architecture/` for system design
- **Development**: Visit `/docs/development/` for developer guides

## 🤝 Contributing

When adding new examples:

1. **Follow Structure**: Use existing organization
2. **Update README**: Document new examples
3. **Test Thoroughly**: Ensure examples work
4. **Add Documentation**: Include comprehensive comments
5. **Update Paths**: Verify import statements

## 📄 License

These examples are part of the Arxos platform and follow the same licensing terms as the main project.

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
**Maintainer**: Arxos Engineering Team
