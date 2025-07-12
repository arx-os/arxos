# Arxos Platform User Guides

## Overview

This document provides comprehensive user guides for the Arxos platform, covering version control, route management, floor comparison, and best practices. These guides are designed to help users effectively utilize all platform features.

## Table of Contents

1. [Version Control User Guide](#version-control-user-guide)
2. [Route Management Tutorial](#route-management-tutorial)
3. [Floor Comparison Guide](#floor-comparison-guide)
4. [Best Practices](#best-practices)
5. [Troubleshooting Guide](#troubleshooting-guide)

---

## Version Control User Guide

### Introduction to Version Control

Version control in Arxos allows you to track changes to building data over time, collaborate with team members, and maintain a complete history of modifications. This system is similar to Git but specifically designed for building information modeling (BIM) data.

### Key Concepts

#### Versions
- **Major Version**: Significant changes (e.g., new floor layout)
- **Minor Version**: Feature additions (e.g., new rooms)
- **Patch Version**: Bug fixes and small improvements

#### Branches
- **Main Branch**: Primary branch for stable data
- **Feature Branches**: For developing new features
- **Hotfix Branches**: For urgent fixes

#### Merge Requests
- **Pull Requests**: Propose changes from one branch to another
- **Code Review**: Team review process for changes
- **Conflict Resolution**: Handle conflicting changes

### Getting Started

#### 1. Creating Your First Version

```bash
# Create initial version of floor data
curl -X POST https://api.arxos.io/v1/version-control/versions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": "floor-001",
    "building_id": "building-001",
    "data": {
      "objects": [
        {
          "id": "room-001",
          "type": "room",
          "x": 100,
          "y": 100,
          "width": 50,
          "height": 50
        }
      ],
      "metadata": {
        "name": "Ground Floor",
        "level": 0
      }
    },
    "branch": "main",
    "message": "Initial floor layout",
    "version_type": "major"
  }'
```

#### 2. Creating a Feature Branch

```bash
# Create a new branch for feature development
curl -X POST https://api.arxos.io/v1/version-control/branches \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "branch_name": "feature-new-layout",
    "floor_id": "floor-001",
    "building_id": "building-001",
    "base_version_id": "v1.0.0-abc123",
    "description": "New layout design branch"
  }'
```

#### 3. Making Changes in a Branch

```bash
# Add new version to feature branch
curl -X POST https://api.arxos.io/v1/version-control/versions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": "floor-001",
    "building_id": "building-001",
    "data": {
      "objects": [
        {
          "id": "room-001",
          "type": "room",
          "x": 100,
          "y": 100,
          "width": 50,
          "height": 50
        },
        {
          "id": "room-002",
          "type": "room",
          "x": 200,
          "y": 200,
          "width": 60,
          "height": 40
        }
      ],
      "metadata": {
        "name": "Ground Floor",
        "level": 0
      }
    },
    "branch": "feature-new-layout",
    "message": "Added new room",
    "version_type": "minor"
  }'
```

#### 4. Creating a Merge Request

```bash
# Create merge request to merge feature branch into main
curl -X POST https://api.arxos.io/v1/version-control/merge-requests \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_version_id": "v1.0.1-def456",
    "target_version_id": "v1.0.0-abc123",
    "title": "Merge new layout changes",
    "description": "This merge request includes the new room layout design",
    "reviewers": ["user-002", "user-003"]
  }'
```

### Advanced Features

#### Annotations and Comments

Add annotations to specific objects or areas:

```bash
# Add annotation to a room
curl -X POST https://api.arxos.io/v1/version-control/versions/v1.0.0-abc123/annotations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This room needs additional lighting",
    "position": {
      "x": 150,
      "y": 200
    },
    "type": "note",
    "object_id": "room-001"
  }'
```

Add general comments to versions:

```bash
# Add comment to version
curl -X POST https://api.arxos.io/v1/version-control/versions/v1.0.0-abc123/comments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Great layout design! Consider adding more exits for safety."
  }'
```

#### Conflict Resolution

When merge conflicts occur:

1. **Identify Conflicts**: Review the conflict report
2. **Resolve Conflicts**: Choose which changes to keep
3. **Create Resolved Version**: Submit the resolved data
4. **Complete Merge**: Execute the merge request

```bash
# Resolve conflicts and create resolved version
curl -X POST https://api.arxos.io/v1/version-control/versions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": "floor-001",
    "building_id": "building-001",
    "data": {
      "objects": [
        // Resolved object data
      ]
    },
    "branch": "feature-new-layout",
    "message": "Resolved conflicts - combined both changes",
    "version_type": "minor"
  }'
```

### Best Practices

1. **Use Descriptive Messages**: Write clear, descriptive commit messages
2. **Create Feature Branches**: Use separate branches for different features
3. **Review Before Merging**: Always review changes before merging
4. **Keep Branches Updated**: Regularly sync feature branches with main
5. **Use Annotations**: Add annotations for important notes and feedback

---

## Route Management Tutorial

### Introduction to Route Management

Route management in Arxos allows you to create, optimize, and manage various types of routes within buildings, including evacuation routes, access routes, and maintenance paths.

### Route Types

#### Evacuation Routes
- **Purpose**: Safe exit paths during emergencies
- **Requirements**: Must be accessible, well-lit, and lead to exits
- **Optimization**: Shortest path to safety

#### Access Routes
- **Purpose**: Daily movement paths for occupants
- **Requirements**: Efficient, accessible, and logical flow
- **Optimization**: Balance between distance and convenience

#### Maintenance Routes
- **Purpose**: Paths for maintenance personnel
- **Requirements**: Access to equipment and utilities
- **Optimization**: Efficient access to maintenance points

### Creating Routes

#### 1. Basic Route Creation

```bash
# Create a simple evacuation route
curl -X POST https://api.arxos.io/v1/routes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": "floor-001",
    "building_id": "building-001",
    "name": "Primary Evacuation Route",
    "route_type": "evacuation",
    "waypoints": [
      {
        "x": 100,
        "y": 100,
        "type": "start"
      },
      {
        "x": 200,
        "y": 200,
        "type": "waypoint"
      },
      {
        "x": 300,
        "y": 300,
        "type": "end"
      }
    ],
    "properties": {
      "distance": 250.0,
      "estimated_time": 120,
      "accessibility": true,
      "capacity": 100
    }
  }'
```

#### 2. Route with Constraints

```bash
# Create route with specific constraints
curl -X POST https://api.arxos.io/v1/routes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": "floor-001",
    "building_id": "building-001",
    "name": "Accessible Evacuation Route",
    "route_type": "evacuation",
    "waypoints": [...],
    "properties": {
      "distance": 300.0,
      "estimated_time": 180,
      "accessibility": true,
      "capacity": 50,
      "constraints": {
        "max_slope": 5.0,
        "min_width": 1.2,
        "avoid_stairs": true
      }
    }
  }'
```

### Route Optimization

#### 1. Automatic Optimization

```bash
# Optimize existing route
curl -X POST https://api.arxos.io/v1/routes/route-001/optimize \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "optimization_type": "shortest_path",
    "constraints": {
      "avoid_obstacles": true,
      "prefer_accessible": true,
      "max_distance": 500.0
    }
  }'
```

#### 2. Manual Optimization

For complex scenarios, you can manually adjust waypoints:

```bash
# Update route with optimized waypoints
curl -X PUT https://api.arxos.io/v1/routes/route-001 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "waypoints": [
      {
        "x": 100,
        "y": 100,
        "type": "start"
      },
      {
        "x": 150,
        "y": 150,
        "type": "waypoint"
      },
      {
        "x": 250,
        "y": 250,
        "type": "waypoint"
      },
      {
        "x": 300,
        "y": 300,
        "type": "end"
      }
    ],
    "properties": {
      "distance": 220.0,
      "estimated_time": 110,
      "accessibility": true,
      "capacity": 100
    }
  }'
```

### Route Validation

#### 1. Validate Route Parameters

```bash
# Validate route before creation
curl -X POST https://api.arxos.io/v1/routes/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": "floor-001",
    "waypoints": [...],
    "route_type": "evacuation"
  }'
```

#### 2. Check Route Compliance

```bash
# Check if route meets safety requirements
curl -X GET https://api.arxos.io/v1/routes/route-001/compliance \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Route Management

#### 1. List All Routes

```bash
# Get all routes for a floor
curl -X GET "https://api.arxos.io/v1/floors/floor-001/routes?route_type=evacuation" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2. Update Route

```bash
# Update route properties
curl -X PUT https://api.arxos.io/v1/routes/route-001 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Evacuation Route",
    "properties": {
      "capacity": 120
    }
  }'
```

#### 3. Delete Route

```bash
# Delete a route
curl -X DELETE https://api.arxos.io/v1/routes/route-001 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Best Practices

1. **Plan Routes Carefully**: Consider all user types and requirements
2. **Test Routes**: Validate routes before implementation
3. **Optimize Regularly**: Review and optimize routes periodically
4. **Document Changes**: Keep records of route modifications
5. **Consider Accessibility**: Ensure routes are accessible to all users

---

## Floor Comparison Guide

### Introduction to Floor Comparison

Floor comparison in Arxos allows you to compare different versions of floors, identify changes, and analyze differences between floor layouts. This is essential for tracking modifications, reviewing changes, and ensuring consistency across building projects.

### Types of Comparisons

#### Version Comparison
- **Purpose**: Compare different versions of the same floor
- **Use Cases**: Review changes, track modifications, audit updates

#### Floor-to-Floor Comparison
- **Purpose**: Compare different floors within the same building
- **Use Cases**: Standardize layouts, identify inconsistencies

#### Cross-Building Comparison
- **Purpose**: Compare floors across different buildings
- **Use Cases**: Template creation, best practice identification

### Basic Comparison

#### 1. Compare Two Versions

```bash
# Compare two versions of the same floor
curl -X POST https://api.arxos.io/v1/floors/compare \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id_1": "floor-001",
    "floor_id_2": "floor-002",
    "comparison_type": "comprehensive"
  }'
```

#### 2. Compare Specific Aspects

```bash
# Compare only object changes
curl -X POST https://api.arxos.io/v1/floors/compare \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id_1": "floor-001",
    "floor_id_2": "floor-002",
    "comparison_type": "objects_only",
    "options": {
      "include_metadata": false,
      "include_routes": false
    }
  }'
```

### Advanced Comparison Features

#### 1. Detailed Object Comparison

```bash
# Get detailed object comparison
curl -X POST https://api.arxos.io/v1/floors/compare/detailed \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id_1": "floor-001",
    "floor_id_2": "floor-002",
    "comparison_type": "detailed",
    "options": {
      "include_properties": true,
      "include_positions": true,
      "include_relationships": true
    }
  }'
```

#### 2. Visual Comparison

```bash
# Generate visual comparison report
curl -X POST https://api.arxos.io/v1/floors/compare/visual \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id_1": "floor-001",
    "floor_id_2": "floor-002",
    "output_format": "svg",
    "highlight_changes": true
  }'
```

### Understanding Comparison Results

#### Similarity Score
- **0.0-0.3**: Very different (major changes)
- **0.3-0.7**: Moderately different (some changes)
- **0.7-1.0**: Very similar (minor changes)

#### Change Categories

1. **Added Objects**: New objects in the second floor
2. **Removed Objects**: Objects present in first floor but not in second
3. **Modified Objects**: Objects with changed properties
4. **Metadata Changes**: Changes to floor-level metadata

#### Example Response Analysis

```json
{
  "similarity_score": 0.85,
  "differences": {
    "added_objects": [
      {
        "id": "room-003",
        "type": "room",
        "properties": {
          "width": 60,
          "height": 40
        }
      }
    ],
    "modified_objects": [
      {
        "id": "room-001",
        "changes": {
          "width": {"from": 50, "to": 60},
          "height": {"from": 50, "to": 60}
        }
      }
    ],
    "removed_objects": [],
    "metadata_differences": {
      "area": {"from": 1000.0, "to": 1200.0}
    }
  }
}
```

### Comparison Workflows

#### 1. Review Changes Workflow

```bash
# 1. Compare versions
curl -X POST https://api.arxos.io/v1/floors/compare \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"floor_id_1": "v1.0.0", "floor_id_2": "v1.0.1"}'

# 2. Review changes
# Analyze the comparison results

# 3. Approve or reject changes
curl -X POST https://api.arxos.io/v1/version-control/merge-requests/mr-001/approve \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2. Template Creation Workflow

```bash
# 1. Compare multiple floors
curl -X POST https://api.arxos.io/v1/floors/compare/batch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "floor_ids": ["floor-001", "floor-002", "floor-003"],
    "comparison_type": "template_analysis"
  }'

# 2. Identify common patterns
# Analyze common elements across floors

# 3. Create template
curl -X POST https://api.arxos.io/v1/templates \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Standard Office Floor",
    "common_elements": [...]
  }'
```

### Best Practices

1. **Regular Comparisons**: Compare floors regularly to track changes
2. **Document Changes**: Keep records of significant changes
3. **Use Templates**: Create templates for consistent layouts
4. **Review Before Merging**: Always review changes before merging
5. **Validate Changes**: Ensure changes meet requirements

---

## Best Practices

### General Best Practices

#### 1. Data Management
- **Backup Regularly**: Create regular backups of important data
- **Version Control**: Use version control for all changes
- **Documentation**: Document all significant changes
- **Validation**: Validate data before committing changes

#### 2. Collaboration
- **Communication**: Communicate changes with team members
- **Review Process**: Implement review processes for changes
- **Access Control**: Use appropriate access controls
- **Audit Trails**: Maintain audit trails for all changes

#### 3. Performance
- **Optimization**: Optimize routes and layouts regularly
- **Caching**: Use caching for frequently accessed data
- **Batch Operations**: Use batch operations for multiple changes
- **Monitoring**: Monitor system performance

### Version Control Best Practices

#### 1. Branching Strategy
- **Main Branch**: Keep main branch stable
- **Feature Branches**: Use feature branches for development
- **Short-lived Branches**: Keep branches short-lived
- **Regular Merges**: Merge changes regularly

#### 2. Commit Messages
- **Clear Messages**: Write clear, descriptive commit messages
- **Conventional Format**: Use conventional commit format
- **Reference Issues**: Reference related issues in commits
- **Atomic Commits**: Make atomic, focused commits

#### 3. Review Process
- **Code Reviews**: Implement thorough review processes
- **Testing**: Test changes before merging
- **Documentation**: Update documentation with changes
- **Approval Process**: Require approval for significant changes

### Route Management Best Practices

#### 1. Route Planning
- **User Requirements**: Consider all user requirements
- **Safety First**: Prioritize safety in route design
- **Accessibility**: Ensure routes are accessible
- **Efficiency**: Optimize for efficiency and convenience

#### 2. Route Maintenance
- **Regular Reviews**: Review routes regularly
- **Updates**: Update routes when building changes
- **Validation**: Validate routes after changes
- **Documentation**: Document route changes

#### 3. Route Optimization
- **Performance**: Optimize for performance
- **User Experience**: Consider user experience
- **Constraints**: Respect physical and regulatory constraints
- **Testing**: Test routes in real-world conditions

### Floor Comparison Best Practices

#### 1. Comparison Strategy
- **Regular Comparisons**: Compare floors regularly
- **Meaningful Comparisons**: Compare relevant aspects
- **Documentation**: Document comparison results
- **Action Items**: Create action items from comparisons

#### 2. Change Management
- **Track Changes**: Track all significant changes
- **Review Process**: Review changes before implementation
- **Approval Process**: Require approval for major changes
- **Rollback Plan**: Have rollback plans ready

#### 3. Template Management
- **Create Templates**: Create templates for common layouts
- **Update Templates**: Update templates regularly
- **Version Templates**: Version control templates
- **Document Templates**: Document template usage

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Authentication Issues

**Problem**: 401 Unauthorized errors
**Symptoms**: 
- API calls return 401 status
- "Invalid token" error messages
- Token expiration warnings

**Solutions**:
1. Check token validity and expiration
2. Verify token format: `Authorization: Bearer <token>`
3. Regenerate token if expired
4. Check user permissions and role

**Prevention**:
- Implement token refresh mechanisms
- Monitor token expiration
- Use appropriate token storage

#### Rate Limiting Issues

**Problem**: 429 Too Many Requests errors
**Symptoms**:
- API calls return 429 status
- Rate limit exceeded messages
- Reduced API performance

**Solutions**:
1. Implement exponential backoff
2. Reduce request frequency
3. Use bulk operations
4. Contact support for rate limit increases

**Prevention**:
- Monitor API usage
- Implement request queuing
- Use caching strategies

#### Data Validation Issues

**Problem**: 422 Unprocessable Entity errors
**Symptoms**:
- Invalid data format errors
- Missing required field errors
- Data type mismatch errors

**Solutions**:
1. Validate data before submission
2. Check required fields
3. Verify data types
4. Review field constraints

**Prevention**:
- Implement client-side validation
- Use data validation libraries
- Test with sample data

#### Performance Issues

**Problem**: Slow response times
**Symptoms**:
- Long API response times
- Timeout errors
- Reduced system performance

**Solutions**:
1. Use pagination for large datasets
2. Implement caching
3. Optimize queries
4. Use async operations

**Prevention**:
- Monitor performance metrics
- Implement performance testing
- Use performance optimization techniques

#### Version Control Issues

**Problem**: Merge conflicts
**Symptoms**:
- Conflict error messages
- Inconsistent data
- Failed merge operations

**Solutions**:
1. Review conflict reports
2. Resolve conflicts manually
3. Create resolved versions
4. Test merged data

**Prevention**:
- Regular synchronization
- Clear change documentation
- Team communication

#### Route Management Issues

**Problem**: Invalid routes
**Symptoms**:
- Route validation errors
- Safety compliance issues
- Accessibility violations

**Solutions**:
1. Review route constraints
2. Validate route parameters
3. Check safety requirements
4. Update route design

**Prevention**:
- Regular route validation
- Safety compliance checks
- User requirement analysis

### Debugging Techniques

#### 1. Log Analysis
- Review application logs
- Check error messages
- Analyze performance metrics
- Monitor system resources

#### 2. API Testing
- Use API testing tools
- Test with sample data
- Verify response formats
- Check error handling

#### 3. Data Validation
- Validate input data
- Check data formats
- Verify field constraints
- Test edge cases

#### 4. Performance Monitoring
- Monitor response times
- Track resource usage
- Analyze bottlenecks
- Optimize performance

### Getting Help

#### 1. Documentation
- Review API documentation
- Check user guides
- Read troubleshooting guides
- Search knowledge base

#### 2. Community Support
- Join user forums
- Participate in discussions
- Share experiences
- Learn from others

#### 3. Technical Support
- Contact technical support
- Provide detailed information
- Include error logs
- Follow support procedures

#### 4. Training Resources
- Attend training sessions
- Watch tutorial videos
- Read best practice guides
- Practice with sample data 