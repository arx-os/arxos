# Viewport Manager Complete Guide

## Overview

The Viewport Manager is a comprehensive tool for navigating and interacting with 2D SVG-BIM models. This guide combines the API reference, user guide, and troubleshooting information into a single comprehensive resource.

## Table of Contents

1. [User Guide](#user-guide)
   - [Getting Started](#getting-started)
   - [Basic Navigation](#basic-navigation)
   - [Advanced Features](#advanced-features)
   - [Coordinate Systems](#coordinate-systems)
   - [Real-World Measurements](#real-world-measurements)
   - [History and Undo/Redo](#history-and-undoredo)
   - [Keyboard Shortcuts](#keyboard-shortcuts)

2. [API Reference](#api-reference)
   - [Authentication](#authentication)
   - [Viewport State Management](#viewport-state-management)
   - [Zoom Operations](#zoom-operations)
   - [Pan Operations](#pan-operations)
   - [Coordinate Conversion](#coordinate-conversion)
   - [Real-World Coordinates](#real-world-coordinates)
   - [Viewport History](#viewport-history)
   - [Event Handling](#event-handling)
   - [Error Codes](#error-codes)

3. [Troubleshooting](#troubleshooting)
   - [Quick Diagnosis](#quick-diagnosis)
   - [Zoom Issues](#zoom-issues)
   - [Pan Issues](#pan-issues)
   - [Coordinate Problems](#coordinate-problems)
   - [Performance Issues](#performance-issues)
   - [Integration Problems](#integration-problems)
   - [Browser-Specific Issues](#browser-specific-issues)
   - [API Errors](#api-errors)
   - [Debugging Tools](#debugging-tools)

---

## User Guide

### Getting Started

#### Opening the Viewport Manager

1. Navigate to the SVG view page (`/svg_view.html`)
2. The viewport manager is automatically initialized
3. You'll see zoom controls and coordinate display in the interface

#### Initial View

- **Default Zoom**: 100% (1.0x magnification)
- **Default Pan**: Centered on the SVG content
- **Coordinate Display**: Shows current mouse position in SVG coordinates

### Basic Navigation

#### Zoom Controls

**Using Zoom Buttons**
- **Zoom In (+)** : Increases magnification by 10%
- **Zoom Out (-)** : Decreases magnification by 10%
- **Zoom to Fit** : Automatically adjusts zoom to show entire SVG
- **Zoom to 100%** : Returns to default zoom level

**Using Mouse Wheel**
- **Scroll Up** : Zoom in
- **Scroll Down** : Zoom out
- **Ctrl + Scroll** : Faster zoom changes
- **Shift + Scroll** : Slower zoom changes

**Using Touch Gestures (Mobile)**
- **Pinch Out** : Zoom in
- **Pinch In** : Zoom out
- **Double Tap** : Zoom to fit

#### Pan Controls

**Using Mouse**
- **Click and Drag** : Pan the view
- **Middle Mouse Button** : Pan without selecting objects
- **Arrow Keys** : Pan in small increments

**Using Touch (Mobile)**
- **Swipe** : Pan the view
- **Two-finger Swipe** : Pan without zooming

### Advanced Features

#### Zoom Constraints

The viewport manager enforces zoom limits to ensure optimal performance:

- **Minimum Zoom**: 10% (0.1x) - Prevents zooming out too far
- **Maximum Zoom**: 500% (5.0x) - Prevents excessive zooming in
- **Zoom Steps**: 10% increments for smooth transitions

#### Zoom to Specific Areas

1. **Zoom to Selection**:
   - Select objects on the SVG
   - Click "Zoom to Selection" button
   - Viewport adjusts to show selected area

2. **Zoom to Point**:
   - Right-click on any point
   - Select "Zoom to Point"
   - Viewport centers and zooms to that location

3. **Zoom to Object**:
   - Click on any object
   - Use "Zoom to Object" from context menu
   - Viewport focuses on the selected object

### Coordinate Systems

#### Understanding Coordinates

The viewport manager works with multiple coordinate systems:

**Screen Coordinates**
- **Origin**: Top-left corner of the viewport
- **Units**: Pixels
- **Use**: Mouse position, UI elements

**SVG Coordinates**
- **Origin**: Defined by SVG viewBox
- **Units**: SVG units (typically pixels)
- **Use**: Object positioning, measurements

**Real-World Coordinates**
- **Origin**: Building reference point
- **Units**: Feet, meters, inches, etc.
- **Use**: Actual building measurements

#### Coordinate Display

The interface shows coordinates in real-time:

```
Mouse Position: SVG (150.5, 200.3) | Screen (300, 400) | Real-World (75.25 ft, 100.15 ft)
```

### Real-World Measurements

#### Setting Up Real-World Coordinates

1. **Define Scale Factors**:
   ```
   Scale: 1 SVG unit = 0.5 feet
   ```

2. **Set Coordinate System**:
   ```
   Origin: (0, 0) at building corner
   Units: Feet
   Rotation: 0 degrees
   ```

3. **Configure Display**:
   ```
   Precision: 2 decimal places
   Units: Feet and inches
   ```

### History and Undo/Redo

#### Zoom History

- **Automatic Tracking**: All zoom operations are automatically tracked
- **History Size**: Configurable (default: 50 operations)
- **Undo/Redo**: Navigate through zoom history
- **Clear History**: Option to clear history for performance

#### History Controls

- **Undo (Ctrl+Z)**: Revert to previous zoom state
- **Redo (Ctrl+Y)**: Restore next zoom state
- **Clear History**: Remove all history entries
- **History Display**: Show current position in history

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `+` | Zoom in |
| `-` | Zoom out |
| `0` | Zoom to 100% |
| `F` | Zoom to fit |
| `Ctrl + Z` | Undo zoom |
| `Ctrl + Y` | Redo zoom |
| `Arrow Keys` | Pan view |
| `Home` | Center view |
| `End` | Zoom to fit |

---

## API Reference

**Base URL:** `https://api.arxos.io/v1/viewport`

### Authentication

All viewport manager endpoints require JWT authentication:

```
Authorization: Bearer <your-jwt-token>
```

### Viewport State Management

#### GET /api/viewport/state

Get current viewport state including zoom level, pan position, and coordinate system information.

**Headers:** `Authorization: Bearer <jwt-token>`

**Query Parameters:**
- `session_id` (optional): Session identifier for multi-session support

**Response:**
```json
{
  "success": true,
  "viewport_state": {
    "current_zoom": 1.0,
    "pan_x": 0.0,
    "pan_y": 0.0,
    "min_zoom": 0.1,
    "max_zoom": 5.0,
    "zoom_step": 0.1,
    "scale_factors": {
      "x": 1.0,
      "y": 1.0
    },
    "coordinate_system": {
      "units": "feet",
      "origin_x": 0.0,
      "origin_y": 0.0,
      "rotation": 0.0
    },
    "viewport_bounds": {
      "x_min": -1000.0,
      "y_min": -1000.0,
      "x_max": 1000.0,
      "y_max": 1000.0
    },
    "session_id": "session-123",
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

#### PUT /api/viewport/state

Update viewport state with new zoom, pan, or coordinate system settings.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "current_zoom": 2.0,
  "pan_x": 100.0,
  "pan_y": 200.0,
  "scale_factors": {
    "x": 0.5,
    "y": 0.5
  },
  "coordinate_system": {
    "units": "meters",
    "origin_x": 50.0,
    "origin_y": 50.0,
    "rotation": 0.785398
  },
  "session_id": "session-123"
}
```

### Zoom Operations

#### POST /api/viewport/zoom

Perform zoom operations with various methods.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "operation": "zoom_in",  // "zoom_in", "zoom_out", "zoom_to", "zoom_fit"
  "zoom_level": 2.0,       // Required for "zoom_to"
  "center_x": 150.0,       // Optional: zoom center point
  "center_y": 200.0,       // Optional: zoom center point
  "session_id": "session-123"
}
```

**Response:**
```json
{
  "success": true,
  "viewport_state": {
    "current_zoom": 2.0,
    "pan_x": 0.0,
    "pan_y": 0.0,
    "min_zoom": 0.1,
    "max_zoom": 5.0,
    "zoom_step": 0.1
  },
  "zoom_history": {
    "can_undo": true,
    "can_redo": false,
    "history_size": 5
  }
}
```

#### GET /api/viewport/zoom/history

Get zoom history for undo/redo operations.

**Headers:** `Authorization: Bearer <jwt-token>`

**Query Parameters:**
- `session_id` (optional): Session identifier
- `limit` (optional): Number of history entries (default: 50, max: 100)

**Response:**
```json
{
  "success": true,
  "zoom_history": [
    {
      "zoom": 1.0,
      "pan_x": 0.0,
      "pan_y": 0.0,
      "timestamp": "2024-01-15T10:30:00Z",
      "operation": "zoom_in"
    },
    {
      "zoom": 0.5,
      "pan_x": 0.0,
      "pan_y": 0.0,
      "timestamp": "2024-01-15T10:29:00Z",
      "operation": "zoom_out"
    }
  ],
  "current_index": 0,
  "can_undo": false,
  "can_redo": true
}
```

### Pan Operations

#### POST /api/viewport/pan

Perform pan operations.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "operation": "pan_to",     // "pan_to", "pan_by", "center_on"
  "x": 100.0,               // Target X coordinate
  "y": 200.0,               // Target Y coordinate
  "delta_x": 50.0,          // For "pan_by" operations
  "delta_y": 25.0,          // For "pan_by" operations
  "session_id": "session-123"
}
```

### Coordinate Conversion

#### POST /api/viewport/convert-coordinates

Convert between different coordinate systems.

**Headers:** `Authorization: Bearer <jwt-token>`

**Request Body:**
```json
{
  "conversion_type": "screen_to_svg",  // "screen_to_svg", "svg_to_screen", "svg_to_real_world", "real_world_to_svg"
  "x": 300.0,
  "y": 400.0,
  "session_id": "session-123"
}
```

**Response:**
```json
{
  "success": true,
  "converted_coordinates": {
    "x": 150.5,
    "y": 200.3,
    "units": "svg_units"
  },
  "conversion_info": {
    "scale_factor_x": 0.5,
    "scale_factor_y": 0.5,
    "offset_x": 0.0,
    "offset_y": 0.0
  }
}
```

### Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `VM001` | Invalid zoom level | Ensure zoom is within min/max bounds |
| `VM002` | Invalid pan coordinates | Check coordinate system and bounds |
| `VM003` | Session not found | Reinitialize session or login |
| `VM004` | SVG not loaded | Ensure SVG is properly loaded |
| `VM005` | Coordinate conversion failed | Verify coordinate system setup |
| `VM006` | History operation failed | Clear history or restart session |

---

## Troubleshooting

### Quick Diagnosis

#### Before Troubleshooting

1. **Check Browser Console**:
   - Open Developer Tools (F12)
   - Look for JavaScript errors
   - Check for network request failures

2. **Verify SVG Loading**:
   - Ensure SVG file is accessible
   - Check SVG file size and complexity
   - Verify SVG format is valid

3. **Check Viewport Manager Status**:
   - Look for initialization messages
   - Verify viewport controls are visible
   - Check coordinate display is working

#### Common Symptoms and Solutions

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Zoom buttons don't work | JavaScript error or SVG not loaded | Refresh page, check console |
| Pan doesn't respond | Event listeners not attached | Reinitialize viewport manager |
| Coordinates show NaN | Invalid coordinate system | Reset coordinate system |
| Slow performance | Large SVG or high zoom | Reduce zoom level, optimize SVG |
| Undo/Redo disabled | No history or session issue | Clear history, restart session |

### Zoom Issues

#### Zoom Buttons Not Responding

**Symptoms**:
- Clicking zoom buttons has no effect
- Zoom level display doesn't change
- No visual feedback from buttons

**Solutions**:

1. **Check JavaScript Console**:
   ```javascript
   // In browser console, check for errors
   console.log('Viewport manager:', window.viewportManager);
   console.log('Zoom buttons:', document.querySelectorAll('[id*="zoom"]'));
   ```

2. **Verify SVG Loading**:
   ```javascript
   // Check if SVG is loaded
   const svg = document.querySelector('svg');
   console.log('SVG loaded:', svg !== null);
   console.log('SVG size:', svg?.getBoundingClientRect());
   ```

3. **Reinitialize Viewport Manager**:
   ```javascript
   // Force reinitialization
   if (window.viewportManager) {
       window.viewportManager.destroy();
   }
   // Reinitialize (implementation specific)
   ```

#### Zoom Level Stuck

**Symptoms**:
- Zoom level doesn't change despite button clicks
- Zoom level shows incorrect value
- Zoom constraints not working

**Solutions**:

1. **Reset Zoom Level**:
   ```javascript
   // Force reset zoom
   viewportManager.setZoom(1.0);
   viewportManager.updateDisplay();
   ```

2. **Check Zoom Constraints**:
   ```javascript
   // Verify zoom limits
   console.log('Min zoom:', viewportManager.minZoom);
   console.log('Max zoom:', viewportManager.maxZoom);
   console.log('Current zoom:', viewportManager.currentZoom);
   ```

### Pan Issues

#### Pan Not Working

**Symptoms**:
- Mouse drag doesn't move the view
- Touch gestures don't work
- Arrow keys don't pan

**Solutions**:

1. **Check Event Listeners**:
   ```javascript
   // Verify mouse events are attached
   const svg = document.querySelector('svg');
   console.log('Mouse events:', svg.onmousedown, svg.onmousemove);
   ```

2. **Enable Pan Mode**:
   ```javascript
   // Ensure pan is enabled
   viewportManager.enablePan = true;
   viewportManager.updatePanHandlers();
   ```

3. **Check SVG Size**:
   ```javascript
   // SVG must be larger than viewport for panning
   const svgRect = svg.getBoundingClientRect();
   const viewportRect = viewport.getBoundingClientRect();
   console.log('SVG larger than viewport:',
       svgRect.width > viewportRect.width ||
       svgRect.height > viewportRect.height);
   ```

### Coordinate Problems

#### Invalid Coordinates

**Symptoms**:
- Coordinates show NaN or undefined
- Coordinate conversion fails
- Real-world measurements incorrect

**Solutions**:

1. **Reset Coordinate System**:
   ```javascript
   // Reset to default coordinate system
   viewportManager.setCoordinateSystem({
       units: 'pixels',
       origin_x: 0,
       origin_y: 0,
       rotation: 0
   });
   ```

2. **Verify Scale Factors**:
   ```javascript
   // Check scale factors
   console.log('Scale factors:', viewportManager.scaleFactors);
   console.log('Coordinate system:', viewportManager.coordinateSystem);
   ```

3. **Update Scale Factors**:
   ```javascript
   // Set proper scale factors
   viewportManager.setScaleFactors({
       x: 0.5,  // 1 SVG unit = 0.5 feet
       y: 0.5
   });
   ```

### Performance Issues

#### Slow Zoom/Pan Response

**Symptoms**:
- Lag during zoom operations
- Slow pan response
- Browser becomes unresponsive

**Solutions**:

1. **Optimize SVG**:
   ```javascript
   // Reduce SVG complexity
   const svg = document.querySelector('svg');
   // Remove unnecessary elements
   const elementsToRemove = svg.querySelectorAll('.debug, .temp');
   elementsToRemove.forEach(el => el.remove());
   ```

2. **Use Throttled Operations**:
   ```javascript
   // Implement throttling for smooth performance
   let operationTimeout;
   function throttledOperation(operation) {
       clearTimeout(operationTimeout);
       operationTimeout = setTimeout(() => {
           // Perform operation
       }, 16); // ~60fps
   }
   ```

3. **Reduce Zoom Range**:
   ```javascript
   // Limit zoom range for better performance
   viewportManager.minZoom = 0.25; // 25% minimum
   viewportManager.maxZoom = 3.0;  // 300% maximum
   ```

### Debugging Tools

#### Browser Developer Tools

1. **Console Logging**:
   ```javascript
   // Enable debug logging
   viewportManager.debug = true;
   viewportManager.logLevel = 'debug';
   ```

2. **Performance Monitoring**:
   ```javascript
   // Monitor performance metrics
   console.log('Memory usage:', performance.memory);
   console.log('Frame rate:', 1000 / (Date.now() - lastFrameTime));
   ```

3. **Event Monitoring**:
   ```javascript
   // Monitor viewport events
   viewportManager.addEventListener('zoomChanged', (data) => {
       console.log('Zoom changed:', data);
   });
   ```

#### API Debugging

1. **Request/Response Logging**:
   ```javascript
   // Log API calls
   console.log('API Request:', requestData);
   console.log('API Response:', responseData);
   ```

2. **Error Tracking**:
   ```javascript
   // Track errors
   viewportManager.onError = (error) => {
       console.error('Viewport error:', error);
       // Send to error tracking service
   };
   ```

### Getting Help

If you're still experiencing issues after trying the troubleshooting steps:

1. **Check the Console**: Look for specific error messages
2. **Review Logs**: Check application logs for detailed error information
3. **Contact Support**: Provide error codes and console output
4. **Submit Bug Report**: Include steps to reproduce the issue

## Best Practices

### Performance Optimization

1. **Optimize SVG Files**: Remove unnecessary elements and attributes
2. **Use Appropriate Zoom Levels**: Avoid extreme zoom levels for large models
3. **Implement Caching**: Cache coordinate conversions and calculations
4. **Throttle Operations**: Limit the frequency of zoom/pan operations

### User Experience

1. **Provide Visual Feedback**: Show loading states and operation progress
2. **Maintain Context**: Keep important UI elements visible during operations
3. **Support Multiple Input Methods**: Mouse, touch, and keyboard controls
4. **Clear Error Messages**: Provide helpful error messages and recovery options

### Integration

1. **Event-Driven Architecture**: Use events for loose coupling
2. **Configuration Management**: Allow easy customization of settings
3. **Session Management**: Support multiple user sessions
4. **Error Handling**: Implement comprehensive error handling and recovery
