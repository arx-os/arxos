# ArxIDE User Guide

## 🚀 Getting Started

### Installation

#### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 2GB available disk space
- **Graphics**: OpenGL 3.3 compatible graphics card
- **Network**: Internet connection for updates and collaboration

#### Download & Install

1. **Download ArxIDE**
   - Visit the official Arxos website: https://arxos.com/arxide
   - Choose your operating system
   - Download the latest version

2. **Install ArxIDE**
   - **Windows**: Run the `.exe` installer and follow the setup wizard
   - **macOS**: Open the `.dmg` file and drag ArxIDE to Applications
   - **Linux**: Extract the `.tar.gz` file and run the install script

3. **First Launch**
   - Launch ArxIDE from your applications menu
   - Complete the initial setup wizard
   - Sign in with your Arxos account or create a new one

### Initial Setup

#### Account Creation
1. Click "Create Account" in the welcome screen
2. Enter your email address and choose a password
3. Verify your email address
4. Complete your profile information

#### Workspace Configuration
1. Choose your default workspace location
2. Select your preferred theme (Light/Dark/Auto)
3. Configure your preferred language
4. Set up your collaboration preferences

## 🏗️ Basic Usage

### Interface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ArxIDE Interface                            │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   Activity  │  │   Editor Area   │  │   Properties    │   │
│  │     Bar     │  │                 │  │     Panel       │   │
│  │             │  │  ┌─────────────┐ │  │                 │   │
│  │ 📁 Explorer │  │  │   Monaco    │ │  │  Object Info    │   │
│  │ 🔧 Extensions│  │  │   Editor    │ │  │                 │   │
│  │ 🏗️ Building │  │  │             │ │  │  Properties     │   │
│  │ 🤖 Agent    │  │  └─────────────┘ │  │                 │   │
│  │             │  │                 │  │  │  Commands      │   │
│  │             │  │  ┌─────────────┐ │  │                 │   │
│  │             │  │  │   Three.js  │ │  │  │  History      │   │
│  │             │  │  │    Canvas   │ │  │  │                 │   │
│  │             │  │  │             │ │  │  └─────────────────┘   │
│  └─────────────┘  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Creating Your First Building

#### 1. New Project
1. Click **File → New Project**
2. Choose a project template:
   - **Empty Building**: Start from scratch
   - **Residential Template**: Pre-configured residential building
   - **Commercial Template**: Pre-configured commercial building
   - **Industrial Template**: Pre-configured industrial building

#### 2. Basic Building Structure
```svgx
// Example: Simple residential building
building "My House" {
  floors: [
    floor "Ground Floor" {
      rooms: [
        room "Living Room" {
          dimensions: { width: 20, length: 15, height: 9 }
          systems: [
            electrical {
              outlets: 8
              lighting: 4
              switches: 2
            }
            hvac {
              vents: 3
              thermostat: 1
            }
          ]
        }
      ]
    }
  ]
}
```

#### 3. Natural Language Commands
Use the Arxos Agent to create building elements with natural language:

**Examples:**
- "Add a kitchen to the ground floor"
- "Create an electrical panel in the basement"
- "Add HVAC ductwork to the second floor"
- "Install security cameras around the perimeter"

### File Management

#### Opening Files
1. **Recent Files**: Click **File → Recent** to see recently opened files
2. **Open File**: Use **Ctrl+O** (Windows/Linux) or **Cmd+O** (macOS)
3. **File Browser**: Use the Explorer panel to navigate and open files

#### Saving Files
1. **Save**: **Ctrl+S** (Windows/Linux) or **Cmd+S** (macOS)
2. **Save As**: **Ctrl+Shift+S** (Windows/Linux) or **Cmd+Shift+S** (macOS)
3. **Auto-save**: Files are automatically saved every 30 seconds

#### File Formats
- **SVGX**: Native Arxos building format
- **DWG**: AutoCAD format (import/export)
- **DXF**: AutoCAD exchange format (import/export)
- **IFC**: Industry Foundation Classes (import/export)
- **JSON**: Data exchange format

## 🔧 Advanced Features

### 3D Building Visualization

#### Navigation
- **Pan**: Right-click and drag
- **Rotate**: Left-click and drag
- **Zoom**: Mouse wheel or pinch gesture
- **Focus**: Double-click on an object to focus the camera

#### View Modes
- **Wireframe**: Show building structure as wireframe
- **Solid**: Show solid building model
- **Textured**: Show building with materials and textures
- **X-Ray**: Show internal systems through walls

#### System Visualization
- **Electrical**: View electrical systems and circuits
- **HVAC**: View heating, ventilation, and air conditioning
- **Plumbing**: View water and waste systems
- **Security**: View security and access control systems

### Natural Language CAD Commands

#### Command Structure
```
[Action] [Object] [Location] [Properties]
```

#### Examples
```
"Add a 20-amp circuit to the kitchen"
"Install a 120V outlet 3 feet from the floor"
"Create a 3-ton HVAC unit on the roof"
"Add a fire sprinkler in the basement"
"Connect the main panel to the subpanel"
```

#### Context Awareness
The Arxos Agent understands context:
- **Location**: "in the kitchen" refers to the current room
- **System**: "electrical" automatically applies to electrical systems
- **Standards**: "NEC compliant" ensures code compliance
- **Materials**: "copper wire" specifies material requirements

### Extension System

#### Installing Extensions
1. Open the Extensions panel (🔧 icon)
2. Browse available extensions
3. Click "Install" on desired extensions
4. Restart ArxIDE if prompted

#### Popular Extensions
- **Electrical CAD Tools**: Advanced electrical design
- **HVAC Designer**: HVAC system design and analysis
- **Plumbing Pro**: Plumbing system design
- **Security Systems**: Security and access control
- **Energy Analysis**: Energy efficiency analysis
- **Code Compliance**: Building code checking

#### Creating Custom Extensions
1. Open **Extensions → Create Extension**
2. Choose extension template
3. Configure extension settings
4. Develop extension functionality
5. Test and package extension

### Collaboration Features

#### Real-time Collaboration
1. **Start Session**: Click **Collaborate → Start Session**
2. **Invite Users**: Share session link with team members
3. **Join Session**: Click session link to join
4. **View Participants**: See who's currently editing

#### Conflict Resolution
- **Auto-merge**: Simple conflicts are automatically resolved
- **Manual Resolution**: Complex conflicts require manual resolution
- **Version History**: View and restore previous versions
- **Comments**: Add comments to specific building elements

#### Sharing and Export
- **Export PDF**: Create 2D drawings for printing
- **Export 3D Model**: Export for other CAD software
- **Share Link**: Generate shareable links
- **Publish**: Publish to Arxos cloud for public access

## 🎨 Customization

### Themes and Appearance

#### Theme Selection
1. Go to **Settings → Appearance**
2. Choose from available themes:
   - **Light**: Clean, bright interface
   - **Dark**: Easy on the eyes
   - **Auto**: Follows system preference
   - **Custom**: Create your own theme

#### Custom Themes
1. Click **Create Custom Theme**
2. Configure colors for:
   - Background colors
   - Text colors
   - Accent colors
   - UI element colors
3. Save and apply your theme

### Keyboard Shortcuts

#### Default Shortcuts
```
File Operations:
Ctrl+N          New file
Ctrl+O          Open file
Ctrl+S          Save
Ctrl+Shift+S    Save as
Ctrl+W          Close file

Editing:
Ctrl+Z          Undo
Ctrl+Y          Redo
Ctrl+X          Cut
Ctrl+C          Copy
Ctrl+V          Paste
Ctrl+F          Find
Ctrl+H          Replace

Navigation:
Ctrl+Tab        Switch between files
Ctrl+1-9        Switch to specific panel
F11             Toggle fullscreen
Ctrl+B          Toggle sidebar

Building Commands:
Ctrl+Shift+A    Add object
Ctrl+Shift+D    Delete object
Ctrl+Shift+M    Move object
Ctrl+Shift+R    Rotate object
Ctrl+Shift+S    Scale object

Agent Commands:
Ctrl+Shift+G    Open agent chat
Ctrl+Shift+V    Voice command
Ctrl+Shift+H    Command history
```

#### Custom Shortcuts
1. Go to **Settings → Keyboard Shortcuts**
2. Search for the command you want to customize
3. Click on the command and press your desired key combination
4. Save your custom shortcuts

### Workspace Layout

#### Panel Management
- **Move Panels**: Drag panel headers to reposition
- **Resize Panels**: Drag panel borders to resize
- **Hide Panels**: Click the X button to hide panels
- **Show Panels**: Use **View → Panels** to show hidden panels

#### Layout Presets
- **Default**: Standard layout for general use
- **Code Focus**: Emphasizes code editing
- **3D Focus**: Emphasizes 3D visualization
- **Collaboration**: Optimized for team work
- **Custom**: Save your own layout

## 🔍 Troubleshooting

### Common Issues

#### Performance Issues
**Problem**: ArxIDE is running slowly
**Solutions**:
1. Close unnecessary files and panels
2. Reduce 3D model complexity
3. Update graphics drivers
4. Increase system RAM
5. Use wireframe mode for large models

#### File Loading Issues
**Problem**: Can't open a file
**Solutions**:
1. Check file format compatibility
2. Verify file isn't corrupted
3. Try opening in a different format
4. Check file permissions
5. Contact support for unsupported formats

#### Extension Problems
**Problem**: Extension not working
**Solutions**:
1. Check extension compatibility
2. Update extension to latest version
3. Disable conflicting extensions
4. Reinstall the extension
5. Check extension documentation

#### Collaboration Issues
**Problem**: Can't join collaboration session
**Solutions**:
1. Check internet connection
2. Verify session link is correct
3. Ensure you have permission to join
4. Try refreshing the page
5. Contact session owner

### Getting Help

#### Documentation
- **User Guide**: This comprehensive guide
- **API Reference**: Technical documentation
- **Video Tutorials**: Step-by-step video guides
- **Knowledge Base**: Searchable help articles

#### Community Support
- **Forums**: Community discussion boards
- **Discord**: Real-time chat support
- **GitHub**: Issue tracking and feature requests
- **Stack Overflow**: Technical Q&A

#### Professional Support
- **Email Support**: support@arxos.com
- **Live Chat**: Available during business hours
- **Phone Support**: Premium support option
- **Remote Assistance**: Screen sharing support

### System Information

#### View System Info
1. Go to **Help → About ArxIDE**
2. View version information
3. Check system requirements
4. View installed extensions
5. Access diagnostic information

#### Diagnostic Tools
- **Performance Monitor**: Real-time performance metrics
- **Memory Usage**: Monitor memory consumption
- **Network Status**: Check connection quality
- **Error Logs**: View detailed error information

## 📚 Advanced Topics

### Building Information Modeling (BIM)

#### BIM Concepts
- **3D Modeling**: Create detailed 3D building models
- **System Integration**: Integrate all building systems
- **Data Management**: Manage building data and metadata
- **Lifecycle Management**: Track building through its lifecycle

#### BIM Workflows
1. **Conceptual Design**: Initial building concept
2. **Schematic Design**: Basic building layout
3. **Design Development**: Detailed design
4. **Construction Documents**: Final construction plans
5. **Construction Administration**: Oversee construction
6. **Facility Management**: Ongoing building management

### Building Codes and Standards

#### Code Compliance
- **NEC**: National Electrical Code
- **IBC**: International Building Code
- **ASHRAE**: HVAC standards
- **NFPA**: Fire protection standards
- **Local Codes**: Jurisdiction-specific requirements

#### Code Checking
1. **Automatic Checking**: Real-time code compliance
2. **Manual Review**: Detailed code analysis
3. **Report Generation**: Compliance reports
4. **Recommendations**: Code improvement suggestions

### Energy Analysis

#### Energy Modeling
- **Load Calculations**: Heating and cooling loads
- **Energy Consumption**: Annual energy usage
- **Cost Analysis**: Energy cost projections
- **Efficiency Measures**: Energy-saving recommendations

#### Sustainability Features
- **LEED Compliance**: Green building certification
- **Energy Star**: Energy efficiency standards
- **Carbon Footprint**: Environmental impact analysis
- **Renewable Energy**: Solar and wind integration

This user guide provides comprehensive coverage of ArxIDE's features and capabilities. For additional help, consult the documentation, community forums, or contact Arxos support.
