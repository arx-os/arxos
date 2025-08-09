# User Training Guide - Viewport Manager

## Overview

This guide provides comprehensive training for users of the Arxos SVG-BIM viewport manager. Learn how to navigate, zoom, pan, and interact with 2D building models efficiently.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Navigation](#basic-navigation)
3. [Advanced Zoom Features](#advanced-zoom-features)
4. [Coordinate System](#coordinate-system)
5. [Symbol Interaction](#symbol-interaction)
6. [Keyboard Shortcuts](#keyboard-shortcuts)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Getting Started

### Prerequisites
- Modern web browser (Chrome, Edge, Firefox, Safari)
- Basic understanding of building systems
- Access to Arxos SVG-BIM system

### First Steps
1. **Open the Application**: Navigate to the Arxos SVG-BIM interface
2. **Load a Model**: Select or upload your building model
3. **Familiarize with Interface**: Identify the viewport area and controls

### Interface Overview
```
┌─────────────────────────────────────────────────────────┐
│ Toolbar: Zoom, Pan, Reset, Undo/Redo                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                    Viewport Area                        │
│                                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ Status Bar: Coordinates, Scale, Zoom Level              │
└─────────────────────────────────────────────────────────┘
```

## Basic Navigation

### Mouse Controls

#### Zoom Operations
- **Zoom In**:
  - Scroll wheel up
  - Double-click on area
  - Use zoom slider (+ button)
- **Zoom Out**:
  - Scroll wheel down
  - Use zoom slider (- button)
- **Zoom to Fit**:
  - Double-click empty space
  - Press 'F' key

#### Pan Operations
- **Pan View**:
  - Click and drag with left mouse button
  - Hold middle mouse button and drag
- **Pan to Center**:
  - Right-click on location
  - Select "Center View"

### Touch Controls (Mobile/Tablet)

#### Gesture Support
- **Pinch to Zoom**:
  - Two-finger pinch in/out
  - Smooth zoom with momentum
- **Pan**:
  - Single finger drag
  - Momentum scrolling
- **Double Tap**:
  - Zoom to fit
  - Reset view

## Advanced Zoom Features

### Zoom Constraints
The system enforces zoom limits for optimal performance:
- **Minimum Zoom**: 0.1x (10% of original size)
- **Maximum Zoom**: 5.0x (500% of original size)
- **Zoom Steps**: 0.1x increments for precise control

### Zoom History
- **Undo Zoom**: Ctrl+Z or toolbar button
- **Redo Zoom**: Ctrl+Y or toolbar button
- **History Limit**: Last 50 zoom operations stored
- **Clear History**: Reset button in toolbar

### Smart Zoom
- **Zoom to Selection**: Select objects and press 'Z'
- **Zoom to Symbol**: Right-click symbol → "Zoom to Symbol"
- **Zoom to Area**: Draw selection box and press 'Z'

## Coordinate System

### Understanding Coordinates
The system uses a real-world coordinate system:
- **Units**: Meters (configurable)
- **Origin**: Bottom-left corner of building
- **Precision**: 6 decimal places (millimeter accuracy)

### Coordinate Display
```
Status Bar: X: 123.456 Y: 789.012 Scale: 1:100 Zoom: 1.5x
```

### Coordinate Conversion
- **Screen to Real**: Click anywhere to see real-world coordinates
- **Real to Screen**: Enter coordinates in toolbar to navigate
- **Measurement Tool**: Use ruler tool for distance measurements

### Scale Factors
- **1:1**: Full scale (1 pixel = 1 meter)
- **1:50**: 50x reduction (1 pixel = 50 meters)
- **1:100**: 100x reduction (1 pixel = 100 meters)
- **Auto Scale**: Automatically adjusts based on building size

## Symbol Interaction

### Selecting Symbols
- **Single Click**: Select individual symbol
- **Shift+Click**: Add to selection
- **Ctrl+Click**: Toggle selection
- **Drag Selection**: Click and drag to select multiple symbols

### Symbol Information
- **Hover**: See symbol details in tooltip
- **Right-Click**: Context menu with options
- **Properties Panel**: Detailed symbol information
- **Layer Visibility**: Toggle symbol layers

### Symbol Placement
- **Snap to Grid**: Automatic alignment to grid
- **Snap to Symbols**: Align to existing symbols
- **Precise Placement**: Enter exact coordinates
- **Copy/Paste**: Duplicate symbols quickly

## Keyboard Shortcuts

### Navigation Shortcuts
| Shortcut | Action |
|----------|--------|
| `F` | Zoom to fit |
| `R` | Reset view |
| `Z` | Zoom to selection |
| `Space` | Toggle pan mode |
| `Esc` | Cancel current operation |

### Zoom Shortcuts
| Shortcut | Action |
|----------|--------|
| `+` | Zoom in |
| `-` | Zoom out |
| `Ctrl + +` | Zoom in (larger step) |
| `Ctrl + -` | Zoom out (larger step) |
| `Ctrl + 0` | Reset zoom to 100% |

### Selection Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl + A` | Select all symbols |
| `Ctrl + D` | Deselect all |
| `Delete` | Delete selected symbols |
| `Ctrl + C` | Copy selected symbols |
| `Ctrl + V` | Paste symbols |

### History Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl + Z` | Undo last action |
| `Ctrl + Y` | Redo last action |
| `Ctrl + Shift + Z` | Undo zoom |
| `Ctrl + Shift + Y` | Redo zoom |

## Troubleshooting

### Common Issues

#### Performance Problems
**Symptoms**: Slow zoom/pan, laggy interface
**Solutions**:
- Reduce zoom level (stay below 3x)
- Close other browser tabs
- Clear browser cache
- Use hardware acceleration

#### Coordinate Accuracy
**Symptoms**: Measurements seem incorrect
**Solutions**:
- Check scale factor settings
- Verify coordinate system units
- Calibrate measurement tools
- Contact support for model issues

#### Zoom Not Working
**Symptoms**: Can't zoom in/out
**Solutions**:
- Check zoom constraints (0.1x to 5.0x)
- Refresh the page
- Clear browser cache
- Try different browser

#### Touch Gestures Not Working
**Symptoms**: Pinch-to-zoom not responding
**Solutions**:
- Enable touch gestures in settings
- Use two-finger gestures
- Check device compatibility
- Update browser to latest version

### Error Messages

#### "Zoom Level Too High"
- Reduce zoom level below 5.0x
- Use "Zoom to Fit" to reset view

#### "Coordinate Out of Bounds"
- Check coordinate input format
- Verify coordinate system units
- Use "Center View" to reset

#### "Performance Warning"
- Reduce zoom level
- Close unnecessary browser tabs
- Wait for operation to complete

## Best Practices

### Navigation Efficiency
1. **Use Keyboard Shortcuts**: Learn and use keyboard shortcuts for faster navigation
2. **Zoom Strategically**: Start with overview, then zoom to details
3. **Use Zoom History**: Leverage undo/redo for efficient navigation
4. **Pan Efficiently**: Use middle mouse button for smooth panning

### Coordinate Management
1. **Verify Scale**: Always check scale factor before measurements
2. **Use Snap Features**: Enable snap to grid and symbols for accuracy
3. **Document Coordinates**: Keep notes of important coordinate locations
4. **Calibrate Regularly**: Verify coordinate system accuracy

### Performance Optimization
1. **Limit Zoom Level**: Stay within recommended zoom range (0.1x to 5.0x)
2. **Close Unused Tabs**: Free up browser resources
3. **Use Hardware Acceleration**: Enable in browser settings
4. **Regular Maintenance**: Clear cache and restart browser periodically

### Collaboration Tips
1. **Share Viewport State**: Export viewport settings for team members
2. **Use Consistent Scale**: Agree on standard scale factors
3. **Document Changes**: Note coordinate system changes
4. **Coordinate Measurements**: Use consistent measurement units

## Advanced Features

### Custom Zoom Levels
- **Set Custom Zoom**: Enter specific zoom level in toolbar
- **Save Zoom Presets**: Save frequently used zoom levels
- **Zoom to Percentage**: Use percentage-based zoom

### Coordinate Systems
- **Multiple Systems**: Support for different coordinate systems
- **System Conversion**: Automatic conversion between systems
- **Custom Origins**: Set custom coordinate origins

### Export Options
- **Viewport Screenshot**: Export current view as image
- **Coordinate Report**: Export coordinate data
- **Measurement Report**: Export measurement data

## Training Exercises

### Exercise 1: Basic Navigation
1. Open a building model
2. Practice zoom in/out with mouse wheel
3. Pan around the model
4. Use "Zoom to Fit" to reset view
5. Navigate to specific coordinates

### Exercise 2: Advanced Zoom
1. Use zoom history (undo/redo)
2. Practice zoom constraints
3. Use keyboard shortcuts for zoom
4. Zoom to specific symbols
5. Create custom zoom presets

### Exercise 3: Coordinate System
1. Identify coordinate display
2. Measure distances between points
3. Convert between coordinate systems
4. Use snap features for placement
5. Document coordinate locations

### Exercise 4: Symbol Interaction
1. Select individual symbols
2. Select multiple symbols
3. View symbol properties
4. Place symbols with precision
5. Use symbol layers

## Support Resources

### Documentation
- **API Reference**: Technical documentation
- **User Guide**: Detailed feature guide
- **Troubleshooting**: Common issues and solutions
- **Best Practices**: Optimization tips

### Training Materials
- **Video Tutorials**: Step-by-step video guides
- **Interactive Demos**: Hands-on learning
- **Practice Models**: Sample models for training
- **Certification**: User certification program

### Support Channels
- **Help Desk**: Technical support
- **User Forum**: Community support
- **Training Sessions**: Live training events
- **Documentation**: Self-service resources

---

**Last Updated**: [Current Date]
**Version**: 1.0.0
**Training Level**: Beginner to Advanced
