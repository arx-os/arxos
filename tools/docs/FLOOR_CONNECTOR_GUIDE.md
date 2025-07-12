# Floor-Based Connector Management Guide

## Overview

The Arxos platform provides comprehensive floor-based connector management capabilities, allowing users to organize, filter, and manage connectors by building floors. This guide covers all aspects of working with connectors in a floor-based environment.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Connector Management Interface](#connector-management-interface)
3. [Floor-Based Filtering](#floor-based-filtering)
4. [Floor Grouping and Organization](#floor-grouping-and-organization)
5. [Creating Connectors with FloorID](#creating-connectors-with-floorid)
6. [Floor Validation and Consistency](#floor-validation-and-consistency)
7. [Bulk Operations](#bulk-operations)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Getting Started

### Prerequisites

- Access to a building with multiple floors
- Appropriate permissions for connector management
- Understanding of basic connector concepts

### Key Concepts

- **FloorID**: Every connector must be assigned to a specific floor
- **Floor Consistency**: Connected objects must be on the same floor
- **Floor Validation**: Connector placement is validated against floor boundaries
- **Floor Grouping**: Connectors are automatically grouped by floor in lists

## Connector Management Interface

### Main Connector Page

The connector management page (`/connector_management.html`) provides:

- **Floor Filter Dropdown**: Select specific floors to view
- **Floor Grouping**: Connectors grouped by floor with headers
- **Floor Badges**: Visual indicators showing floor information
- **Floor Statistics**: Count of connectors per floor

### Navigation

- Access from SVG viewer via "Connectors" link
- Direct URL: `/connector_management.html`
- Available in main navigation menu

## Floor-Based Filtering

### Filter Options

1. **Floor Filter**: Select specific floors from dropdown
2. **System Filter**: Filter by system (electrical, HVAC, etc.)
3. **Connector Type Filter**: Filter by connector type
4. **Status Filter**: Filter by connection status
5. **Search**: Search by connector name

### Filter Combinations

- Combine multiple filters for precise results
- Clear all filters with "Reset" button
- Save filter preferences for future sessions

## Floor Grouping and Organization

### Automatic Grouping

Connectors are automatically grouped by floor with:

- **Floor Headers**: Clear section headers with floor names
- **Connector Counts**: Number of connectors per floor
- **Collapsible Sections**: Expand/collapse floor groups
- **Visual Separation**: Clear visual distinction between floors

### Floor Indicators

Each connector displays:

- **Floor Badge**: Small badge next to connector name
- **Floor Information**: Floor name in connector details
- **Floor Tooltips**: Hover tooltips with floor information

## Creating Connectors with FloorID

### Step-by-Step Process

1. **Access Creation Modal**
   - Click "Create Connector" button
   - Modal opens with floor selection

2. **Select Floor**
   - Choose floor from dropdown
   - Floor selection is required
   - Available floors are filtered by building

3. **Fill Connector Details**
   - Enter connector name and type
   - Select system and category
   - Set connection type and status
   - Define capacity and load

4. **Set Geometry**
   - Place connector on floor plan
   - Coordinates validated against floor bounds
   - Visual feedback for placement

5. **Connect Objects**
   - Select connected devices/rooms
   - Floor consistency validation
   - Error messages for mismatched floors

### Floor Validation

- **Required Field**: FloorID is mandatory
- **Boundary Check**: Coordinates within floor bounds
- **Consistency Check**: Connected objects on same floor
- **Real-time Feedback**: Immediate validation messages

## Floor Validation and Consistency

### Validation Rules

1. **FloorID Required**
   - All connectors must have floor_id > 0
   - Error if floor not selected

2. **Floor Consistency**
   - Connected objects must be on same floor
   - Error if objects on different floors

3. **Geometry Validation**
   - Coordinates within floor boundaries
   - Warning for out-of-bounds placement

4. **Capacity Validation**
   - Current load ≤ max capacity
   - Error if capacity exceeded

### Error Handling

- **Clear Error Messages**: Specific error descriptions
- **Visual Indicators**: Red borders and icons
- **Suggestions**: Recommended fixes
- **Validation Summary**: List of all issues

## Bulk Operations

### Bulk Floor Assignment

1. **Select Connectors**
   - Check connectors to update
   - Multi-select with checkboxes

2. **Choose Floor**
   - Select target floor
   - Preview changes

3. **Apply Changes**
   - Confirm bulk update
   - Progress indicator
   - Success/error summary

### Bulk Updates

- **Status Updates**: Change status for multiple connectors
- **Type Updates**: Update connector types
- **Capacity Updates**: Modify capacity settings
- **Floor Reassignment**: Move connectors between floors

## Troubleshooting

### Common Issues

#### Floor Selection Not Available
- **Cause**: No floors configured for building
- **Solution**: Add floors in building settings

#### Floor Consistency Errors
- **Cause**: Connected objects on different floors
- **Solution**: Move objects to same floor or update connections

#### Geometry Validation Failures
- **Cause**: Coordinates outside floor bounds
- **Solution**: Adjust placement within floor boundaries

#### Capacity Exceeded
- **Cause**: Current load > max capacity
- **Solution**: Increase max capacity or reduce current load

### Error Messages

| Error | Description | Solution |
|-------|-------------|----------|
| "Floor ID is required" | No floor selected | Select a floor from dropdown |
| "Floor mismatch" | Connected objects on different floors | Move objects to same floor |
| "Coordinates out of bounds" | Placement outside floor area | Adjust placement within floor |
| "Capacity exceeded" | Load exceeds maximum capacity | Increase capacity or reduce load |

## Best Practices

### Floor Organization

1. **Consistent Naming**: Use clear floor names (e.g., "1st Floor", "Ground Floor")
2. **Logical Grouping**: Group related connectors on same floor
3. **Clear Documentation**: Document floor-specific requirements

### Connector Placement

1. **Accurate Coordinates**: Place connectors precisely on floor plans
2. **Logical Positioning**: Position near connected equipment
3. **Accessibility**: Ensure connectors are accessible for maintenance

### Data Management

1. **Regular Validation**: Periodically check floor consistency
2. **Capacity Monitoring**: Monitor load vs. capacity ratios
3. **Documentation**: Maintain detailed connector documentation

### Performance Optimization

1. **Efficient Filtering**: Use specific filters to reduce result sets
2. **Bulk Operations**: Use bulk updates for multiple changes
3. **Regular Cleanup**: Remove unused or obsolete connectors

## Advanced Features

### Floor-Based Analytics

- **Floor Statistics**: Connector counts and types per floor
- **Capacity Analysis**: Load distribution across floors
- **Trend Reporting**: Historical connector data by floor

### Integration Features

- **BIM Integration**: Connectors included in BIM model exports
- **Floor-Based Exports**: Export connectors by floor
- **API Access**: Programmatic access to floor-based connector data

### Customization

- **Floor Colors**: Customize floor indicators and badges
- **Filter Presets**: Save and reuse filter combinations
- **Display Options**: Customize connector list display

## Support and Resources

### Documentation

- [API Reference](../API_REFERENCE.md#bim-object-management)
- [Building Systems Library](../BUILDING_SYSTEMS_LIBRARY.md#connector-models)
- [Platform Architecture](../PLATFORM_ARCHITECTURE.md)

### Technical Support

- **Email**: support@arxos.io
- **Documentation**: https://docs.arxos.io
- **Community**: https://community.arxos.io

### Training Resources

- **Video Tutorials**: Available in help section
- **Interactive Demos**: Step-by-step guided tours
- **Webinars**: Regular training sessions

---

*Last updated: January 2024*
*Version: 1.0*
