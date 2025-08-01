# Arxos Building System Schemas

This directory contains comprehensive JSON schemas that define the data models for all building systems in the Arxos platform. These schemas serve as the foundation for building information modeling (BIM), system integration, and data exchange across the entire platform.

## Directory Structure

```
schemas/
├── audiovisual/
│   └── schema.json          # Audio/visual system components
├── electrical/
│   └── schema.json          # Electrical power and distribution
├── mechanical/
│   └── schema.json          # HVAC and mechanical systems
├── plumbing/
│   └── schema.json          # Water supply and drainage
├── fire_protection/
│   └── schema.json          # Fire alarm and suppression
├── security/
│   └── schema.json          # Access control and surveillance
├── lighting/
│   └── schema.json          # General and emergency lighting
├── structural/
│   └── schema.json          # Building structure and foundation
├── communications/
│   └── schema.json          # Data networks and voice systems
└── README.md                # This documentation
```

## System Coverage

The schemas cover **9 major building systems**:

### 1. **Electrical System** (`electrical/schema.json`)
- Power distribution panels and circuits
- Electrical outlets and fixtures
- Emergency power systems
- Lighting fixtures and controls
- Electrical monitoring and control

### 2. **Mechanical System** (`mechanical/schema.json`)
- Air handlers and VAV boxes
- Ductwork and diffusers
- Chillers, boilers, and cooling towers
- Thermostats and HVAC controls
- HVAC monitoring and optimization

### 3. **Plumbing System** (`plumbing/schema.json`)
- Water mains and distribution
- Hot water heaters and fixtures
- Drainage and sewer systems
- Water pumps and valves
- Plumbing monitoring and control

### 4. **Fire Protection System** (`fire_protection/schema.json`)
- Fire alarm panels and detectors
- Smoke and heat detectors
- Manual pull stations
- Fire sprinklers and piping
- Notification appliances and monitoring

### 5. **Security System** (`security/schema.json`)
- Security cameras and recorders
- Access control and card readers
- Intrusion detection systems
- Security servers and monitoring
- Video management and analytics

### 6. **Lighting System** (`lighting/schema.json`)
- General lighting fixtures
- Emergency lighting systems
- Lighting controls and sensors
- Occupancy and daylight sensors
- Lighting monitoring and energy management

### 7. **Structural System** (`structural/schema.json`)
- Foundations and footings
- Columns, beams, and walls
- Floors and roof systems
- Structural monitoring and sensors
- Load capacity and deflection tracking

### 8. **Communications System** (`communications/schema.json`)
- Network switches and wireless
- Voice systems and phones
- Conference and paging systems
- Communications servers
- Network monitoring and management

### 9. **Audiovisual System** (`audiovisual/schema.json`)
- Displays, projectors, and screens
- Audio systems and amplifiers
- Control systems and touch panels
- Media players and recording
- AV monitoring and management

## Schema Structure

Each schema follows a consistent structure:

```json
{
  "system": "system_name",
  "description": "System description",
  "version": "1.0.0",
  "created_by": "Arxos System",
  "created_at": "2024-12-19",
  "objects": {
    "component_name": {
      "properties": {
        // Technical specifications
      },
      "relationships": {
        // System connections and dependencies
      },
      "behavior_profile": "component_behavior",
      "metadata": {
        // Lifecycle and maintenance info
      }
    }
  },
  "system_requirements": {
    // System-level requirements
  },
  "compliance_standards": {
    // Applicable codes and standards
  },
  "maintenance_schedule": {
    // Maintenance intervals and tasks
  }
}
```

## Key Features

### **Comprehensive Object Definitions**
- **Properties**: Technical specifications, performance metrics, and operational parameters
- **Relationships**: System connections, dependencies, and data flow
- **Behavior Profiles**: Expected system behaviors and interactions
- **Metadata**: Lifecycle information, warranties, and maintenance schedules

### **System Integration**
- **Cross-System Relationships**: Objects reference components in other systems
- **Data Exchange**: Standardized communication protocols (BACnet, Modbus, SNMP)
- **Monitoring Integration**: Real-time monitoring and control capabilities

### **Compliance and Standards**
- **Building Codes**: IBC, NFPA, OSHA compliance
- **Industry Standards**: ASHRAE, IEEE, TIA, ANSI
- **Energy Standards**: LEED, ENERGY STAR, ASHRAE 90.1
- **Safety Standards**: NFPA, IBC, OSHA requirements

### **Maintenance and Lifecycle**
- **Preventive Maintenance**: Scheduled maintenance intervals
- **Warranty Tracking**: Component warranty periods
- **Lifecycle Management**: Operational status tracking
- **Performance Monitoring**: Real-time system performance

## Usage Guidelines

### **For Developers**
1. **System Integration**: Use schemas to define data models for new components
2. **API Development**: Reference schemas for API endpoint definitions
3. **Database Design**: Use schemas to design database schemas
4. **Validation**: Implement schema validation for data integrity

### **For System Integrators**
1. **Component Mapping**: Map existing systems to schema objects
2. **Data Migration**: Use schemas for data transformation
3. **System Testing**: Validate system behavior against schemas
4. **Documentation**: Generate system documentation from schemas

### **For Building Operators**
1. **System Monitoring**: Use schemas to configure monitoring systems
2. **Maintenance Planning**: Reference maintenance schedules
3. **Compliance Tracking**: Monitor compliance with standards
4. **Performance Analysis**: Analyze system performance metrics

## Integration with Arxos Platform

### **SVGX Engine Integration**
- Schemas define the data models for SVGX building elements
- Support for real-time behavior simulation
- Integration with physics engine for system modeling

### **Building Management System**
- Schemas provide the foundation for BMS data models
- Support for real-time monitoring and control
- Integration with alarm and event management

### **AI Agent Integration**
- Schemas enable AI agents to understand building systems
- Support for intelligent system optimization
- Integration with predictive maintenance algorithms

### **Mobile and Web Applications**
- Schemas provide consistent data models across applications
- Support for real-time system status display
- Integration with user interface components

## Version Control

- **Schema Versioning**: Each schema includes version information
- **Backward Compatibility**: Schema changes maintain backward compatibility
- **Migration Support**: Tools for schema migration and data transformation
- **Documentation**: Comprehensive documentation for schema changes

## Contributing

When adding new schemas or modifying existing ones:

1. **Follow the Structure**: Maintain consistent schema structure
2. **Include Relationships**: Define cross-system relationships
3. **Add Documentation**: Update this README with new systems
4. **Test Integration**: Verify integration with existing systems
5. **Update Version**: Increment schema version numbers

## Support

For questions about schemas or system integration:

- **Documentation**: Refer to individual schema files
- **Examples**: Check the SVGX Engine for usage examples
- **Testing**: Use the test suite for validation
- **Community**: Engage with the Arxos development community

---

**Last Updated**: December 19, 2024  
**Version**: 1.0.0  
**Maintained By**: Arxos Development Team 