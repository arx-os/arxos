# Arxos User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Features](#core-features)
3. [Security Features](#security-features)
4. [Advanced Features](#advanced-features)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

---

## Getting Started

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arxos/arx-svg-parser.git
   cd arx-svg-parser
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   python setup_env.py
   ```

4. **Start the API server:**
   ```bash
   python main.py
   ```

### Quick Start

1. **Upload an SVG file:**
   ```bash
   curl -X POST http://localhost:8000/upload/svg \
     -F "file=@building_plan.svg"
   ```

2. **Convert to BIM:**
   ```bash
   curl -X POST http://localhost:8000/assemble/bim \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "svg_content=<svg>...</svg>&format=json"
   ```

3. **Export BIM data:**
   ```bash
   curl -X GET "http://localhost:8000/export/bim/svg_150_12345?format=json"
   ```

---

## Core Features

### SVG Upload and Parsing

The platform accepts SVG files and automatically parses them into structured data.

**Supported SVG Features:**
- Basic shapes (rect, circle, ellipse, line, polyline, polygon)
- Path elements with complex curves
- Groups and nested structures
- Text elements with fonts
- Gradients and patterns
- Transformations and animations

**Example:**
```python
from services.svg_parser import SVGParser

parser = SVGParser()
result = parser.parse_svg_file("building_plan.svg")
print(f"Parsed {result.element_count} elements")
```

### BIM Assembly

Convert SVG content into Building Information Modeling (BIM) format.

**Supported Formats:**
- JSON (default)
- XML
- IFC-lite
- glTF
- ASCII-BIM

**Example:**
```python
from services.bim_assembler import BIMAssembler

assembler = BIMAssembler()
bim_data = assembler.assemble_from_svg(svg_content, format="json")
```

### Symbol Management

Manage building system symbols and their properties.

**Features:**
- Symbol library with 100+ pre-built symbols
- Custom symbol creation
- Symbol categorization (electrical, plumbing, HVAC, etc.)
- Property management
- Version control

**Example:**
```python
from services.symbol_manager import SymbolManager

manager = SymbolManager()
symbols = manager.get_symbols_by_category("electrical")
```

### Export and Interoperability

Export BIM data in multiple formats for different applications.

**Supported Export Formats:**
- IFC-lite (Industry Foundation Classes)
- glTF (3D graphics)
- ASCII-BIM (Text-based)
- Excel (Spreadsheets)
- GeoJSON (Geospatial)
- JSON (Web applications)
- XML (Enterprise systems)
- CSV (Data analysis)
- PDF (Documentation)

**Example:**
```python
from services.export_service import ExportService

export_service = ExportService()
job = export_service.create_export_job(
    data_id="building_001",
    format="ifc-lite",
    options={"include_metadata": True}
)
```

---

## Security Features

### Privacy Controls

Automatically classify and protect sensitive data.

**Data Classification Levels:**
- **Public**: No restrictions
- **Internal**: Company use only
- **Confidential**: Limited access
- **Restricted**: Authorized personnel only

**Example:**
```python
from services.privacy_controls import PrivacyControls

controls = PrivacyControls()
classification = controls.classify_data("building_data", building_info)
protected_data = controls.apply_privacy_controls(data, classification)
```

### Encryption

Multi-layer encryption for data protection.

**Encryption Layers:**
- **Transport**: TLS 1.3 for data in transit
- **Storage**: AES-256 for data at rest
- **Application**: Custom encryption for sensitive fields

**Example:**
```python
from services.encryption_service import EncryptionService

encryption = EncryptionService()
encrypted_data = encryption.encrypt_data("sensitive data", "storage")
decrypted_data = encryption.decrypt_data(encrypted_data, "storage")
```

### Audit Trail

Comprehensive logging of all data access and modifications.

**Audit Events:**
- Data access (read, write, delete)
- User authentication
- Permission changes
- Encryption operations
- Export activities

**Example:**
```python
from services.audit_trail import AuditTrail

audit = AuditTrail()
audit.log_event(
    event_type="data_access",
    user_id="user123",
    resource_id="building_001",
    action="read"
)
```

### Role-Based Access Control (RBAC)

Manage user permissions and access levels.

**Predefined Roles:**
- **Administrator**: Full system access
- **Building Manager**: Building management
- **Inspector**: Inspection and compliance
- **Viewer**: Read-only access
- **Analyst**: Data analysis and reporting

**Example:**
```python
from services.rbac_service import RBACService

rbac = RBACService()
has_permission = rbac.check_permission("user123", "building", "read")
```

### AHJ API Integration

Integrate with Authority Having Jurisdiction (AHJ) systems for compliance.

**Features:**
- Inspection layer creation
- Code violation tracking
- Compliance reporting
- Jurisdiction management

**Example:**
```python
from services.ahj_service import AHJService

ahj = AHJService()
inspection = ahj.create_inspection_layer(
    building_id="building_001",
    ahj_id="ahj_001",
    inspector_id="inspector_123"
)
```

### Data Retention

Automated data lifecycle management.

**Retention Policies:**
- **Building Data**: 5 years
- **User Data**: 2 years
- **Audit Logs**: 7 years
- **Temporary Data**: 30 days

**Example:**
```python
from services.data_retention import DataRetentionService

retention = DataRetentionService()
retention.apply_policy("building_001", "building_data")
```

---

## Advanced Features

### Advanced SVG Features

Enhanced SVG processing capabilities.

**Features:**
- Complex path analysis
- Gradient and pattern extraction
- Animation support
- Custom element handling
- Performance optimization

**Example:**
```python
from services.advanced_svg_features import AdvancedSVGFeatures

features = AdvancedSVGFeatures()
result = features.process_complex_svg(svg_content)
```

### Advanced Symbol Management

Comprehensive symbol library management.

**Features:**
- Symbol versioning
- Custom property definitions
- Symbol relationships
- Bulk operations
- Import/export functionality

**Example:**
```python
from services.advanced_symbol_management import AdvancedSymbolManager

manager = AdvancedSymbolManager()
symbols = manager.search_symbols("fire_alarm", include_relationships=True)
```

### Logic Engine

Rule-based processing and validation.

**Features:**
- Custom rule creation
- Rule validation
- Automated processing
- Error detection
- Compliance checking

**Example:**
```python
from services.logic_engine import LogicEngine

engine = LogicEngine()
result = engine.process_with_rules(bim_data, rule_set="building_codes")
```

### Real-time Features

Live data processing and updates.

**Features:**
- Real-time telemetry
- Live monitoring
- WebSocket connections
- Event streaming
- Performance metrics

**Example:**
```python
from services.realtime_telemetry import RealtimeTelemetry

telemetry = RealtimeTelemetry()
telemetry.start_monitoring("building_001")
```

### Advanced Infrastructure

High-performance processing capabilities.

**Features:**
- Hierarchical SVG grouping
- Multi-layer caching
- Distributed processing
- Task queuing
- Performance optimization

**Example:**
```python
from services.hierarchical_grouping import HierarchicalGroupingService

grouping = HierarchicalGroupingService()
result = grouping.create_hierarchy(svg_elements)
```

---

## Troubleshooting

### Common Issues

#### 1. SVG Parsing Errors

**Problem:** SVG file fails to parse
**Solution:**
```python
# Check SVG validity
from services.svg_validator import SVGValidator

validator = SVGValidator()
is_valid = validator.validate_svg(svg_content)
```

#### 2. Memory Issues

**Problem:** Large SVG files cause memory errors
**Solution:**
```python
# Use streaming parser
from services.streaming_parser import StreamingParser

parser = StreamingParser()
result = parser.parse_large_svg("large_building.svg")
```

#### 3. Export Failures

**Problem:** Export jobs fail
**Solution:**
```python
# Check job status
from services.export_service import ExportService

export_service = ExportService()
status = export_service.get_job_status(job_id)
```

#### 4. Authentication Errors

**Problem:** API authentication fails
**Solution:**
```python
# Verify token
from services.auth_service import AuthService

auth = AuthService()
is_valid = auth.verify_token(token)
```

### Performance Optimization

#### 1. Caching

Enable caching for better performance:
```python
from services.cache_service import CacheService

cache = CacheService()
cache.enable_caching("svg_parsing", ttl=3600)
```

#### 2. Parallel Processing

Use parallel processing for large files:
```python
from services.distributed_processing import DistributedProcessingService

processor = DistributedProcessingService()
result = processor.process_parallel(svg_files, strategy="map_reduce")
```

#### 3. Memory Management

Optimize memory usage:
```python
from services.memory_manager import MemoryManager

memory = MemoryManager()
memory.set_limits(max_memory_gb=8, cleanup_threshold=0.8)
```

---

## Best Practices

### SVG Preparation

1. **Optimize SVG files:**
   - Remove unnecessary elements
   - Use appropriate precision
   - Compress when possible

2. **Use consistent naming:**
   - Meaningful element IDs
   - Descriptive group names
   - Standardized attributes

3. **Validate before processing:**
   - Check SVG validity
   - Verify element structure
   - Test with sample data

### Security Best Practices

1. **Data Classification:**
   - Classify all data appropriately
   - Apply privacy controls consistently
   - Review classifications regularly

2. **Access Control:**
   - Use principle of least privilege
   - Regular permission reviews
   - Monitor access patterns

3. **Audit Compliance:**
   - Enable comprehensive logging
   - Regular audit reviews
   - Maintain audit trails

### Performance Best Practices

1. **Caching Strategy:**
   - Cache frequently accessed data
   - Use appropriate TTL values
   - Monitor cache hit rates

2. **Resource Management:**
   - Monitor memory usage
   - Clean up temporary files
   - Use connection pooling

3. **Error Handling:**
   - Implement proper error handling
   - Log errors appropriately
   - Provide meaningful error messages

### Integration Best Practices

1. **API Usage:**
   - Use appropriate rate limits
   - Handle errors gracefully
   - Implement retry logic

2. **Data Export:**
   - Choose appropriate formats
   - Validate exported data
   - Monitor export performance

3. **Third-party Integrations:**
   - Secure API credentials
   - Validate input data
   - Monitor integration health

---

## Support and Resources

### Documentation
- [API Documentation](./API_DOCUMENTATION.md)
- [Admin Guide](./ADMIN_GUIDE.md)
- [Integration Guide](./INTEGRATION_GUIDE.md)

### Examples
- [Basic Usage Examples](../examples/)
- [Advanced Features Demo](../examples/advanced_features_demo.py)
- [Security Features Demo](../examples/security_features_demo.py)

### Community
- GitHub Issues: [Report bugs](https://github.com/arxos/arx-svg-parser/issues)
- Discussions: [Community forum](https://github.com/arxos/arx-svg-parser/discussions)
- Documentation: [Wiki](https://github.com/arxos/arx-svg-parser/wiki)

### Support
- Email: support@arxos.com
- Documentation: https://docs.arxos.com
- Training: https://training.arxos.com

---

**Version**: 1.0.0  
**Last Updated**: December 19, 2024  
**Contact**: support@arxos.com 